from __future__ import annotations

import asyncio
import base64
import uuid
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.community.weread.client import WeReadClient
from src.community.weread.models.profile import Profile
from src.community.weread.session import SessionManager
from db.repository import CommunityMetaRepo, DataRepo, BookmarkRepo
from db.engine import async_session_factory


@dataclass
class WereadBindTask:
    task_id: str
    platform: str = "weread"
    status: Literal["pending", "scanned", "logged_in", "fetching_profile", "scraping", "bound", "failed"] = "pending"
    qr_base64: str | None = None
    user_id: str | None = None
    profile: Profile | None = None
    error: str | None = None
    scrape_phase: str | None = None
    scrape_counts: dict = field(default_factory=dict)
    event: asyncio.Event = field(default_factory=asyncio.Event)
    _loop: asyncio.AbstractEventLoop | None = field(default=None, repr=False)

    def bind_loop(self) -> None:
        self._loop = asyncio.get_running_loop()

    def _notify(self) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._set_and_clear)

    def _set_and_clear(self) -> None:
        self.event.set()
        self.event.clear()


class WereadBindManager:
    """Manages WeRead platform binding lifecycle with database-backed storage."""

    _tasks_by_user: dict[int, dict[str, WereadBindTask]] = {}

    def __init__(self, db: AsyncSession, user_id: int) -> None:
        self._db = db
        self._user_id = user_id
        if user_id not in WereadBindManager._tasks_by_user:
            WereadBindManager._tasks_by_user[user_id] = {}
        self._tasks = WereadBindManager._tasks_by_user[user_id]

    async def status(self) -> dict:
        for task in self._tasks.values():
            if task.status in ("pending", "scraping", "bound", "failed"):
                result: dict = {"status": task.status}
                if task.qr_base64:
                    result["qr_base64"] = task.qr_base64
                if task.status == "scraping":
                    result["scrape_phase"] = task.scrape_phase
                    result["scrape_counts"] = task.scrape_counts
                if task.status == "bound":
                    result["user_id"] = task.user_id
                    if task.profile:
                        result["profile"] = task.profile.model_dump()
                    result["scrape_counts"] = task.scrape_counts
                if task.status == "failed":
                    result["error"] = task.error
                return result
        row = await CommunityMetaRepo.get_binding(self._db, self._user_id, "weread")
        if row is not None and row.bound:
            return {"status": "bound", **row.to_api_dict()}
        return {"status": "idle"}

    async def refresh(self) -> dict:
        row = await CommunityMetaRepo.get_binding(self._db, self._user_id, "weread")
        if row is None or not row.bound:
            return {"error": "Not bound"}
        if not row.community_user_id:
            return {"error": "No user_id in meta"}
        try:
            state_json, _ = await CommunityMetaRepo.get_session_state(
                self._db, self._user_id, "weread"
            )
            client = WeReadClient(
                headless=True,
                state_json=state_json,
            )
            client.__enter__()
            client.ensure_ready()
            profile = client.scrape_profile()
            client.__exit__(None, None, None)
        except Exception as e:
            return {"error": str(e)}
        await CommunityMetaRepo.save_binding(
            self._db, self._user_id, "weread", row.community_user_id, profile
        )
        await self._db.commit()
        return {
            "bound": True,
            "platform": "weread",
            "user_id": row.community_user_id,
            "profile": profile.model_dump(),
        }

    async def unbind(self) -> dict:
        await CommunityMetaRepo.delete_binding(self._db, self._user_id, "weread")
        await self._db.commit()
        self._tasks.clear()
        return {"bound": False}

    def start_sync(self, community_user_id: str) -> WereadBindTask:
        self._tasks.clear()
        task_id = uuid.uuid4().hex[:12]
        task = WereadBindTask(task_id=task_id, status="scraping")
        task.bind_loop()
        self._tasks[task_id] = task

        user_id = self._user_id
        loop = asyncio.get_running_loop()

        def _run() -> None:
            try:
                _run_sync(task, loop, user_id, community_user_id)
                task.status = "bound"
                task._notify()
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                task._notify()

        loop.run_in_executor(None, _run)
        task._notify()
        return task

    def start_bind(self, channel: str = "msedge") -> WereadBindTask:
        self._tasks.clear()
        task_id = uuid.uuid4().hex[:12]
        task = WereadBindTask(task_id=task_id)
        task.bind_loop()
        self._tasks[task_id] = task

        db = self._db
        user_id = self._user_id
        loop = asyncio.get_running_loop()

        def _run() -> None:
            try:
                client = WeReadClient(
                    headless=False,
                    channel=channel,
                    on_progress=lambda s: (
                        setattr(task, "status", s) or task._notify()
                    ),
                    on_qr=lambda qr_bytes: (
                        setattr(task, "qr_base64", base64.b64encode(qr_bytes).decode())
                    ),
                )

                client.__enter__()
                client.ensure_ready()

                task.user_id = client.vid
                task.status = "fetching_profile"
                task._notify()

                task.profile = client.scrape_profile()

                # Save binding + session state to DB
                state_json = client._session._state_json
                future = asyncio.run_coroutine_threadsafe(
                    _save_binding(db, user_id, client.vid, task.profile, state_json),
                    loop,
                )
                future.result(timeout=10)

                # Auto-scrape shelf + bookmarks via sync
                _run_sync(task, loop, user_id, client.vid, client)

                task.status = "bound"
                task._notify()
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                task._notify()
            finally:
                try:
                    client.__exit__(None, None, None)
                except Exception:
                    pass

        asyncio.get_event_loop().run_in_executor(None, _run)
        return task


async def _save_binding(
    db: AsyncSession,
    user_id: int,
    vid: str,
    profile: Profile,
    state_json: str | None,
) -> None:
    await CommunityMetaRepo.save_binding(
        db, user_id, "weread", vid, profile
    )
    if state_json:
        await CommunityMetaRepo.save_session_state(db, user_id, "weread", state_json, None)
    await db.commit()


def _run_sync(
    task: WereadBindTask,
    loop: asyncio.AbstractEventLoop,
    user_id: int,
    vid: str,
    existing_client: WeReadClient | None = None,
) -> None:
    async def _do_scrape() -> None:
        async with async_session_factory() as db:
            state_json, _ = await CommunityMetaRepo.get_session_state(db, user_id, "weread")
            if not state_json:
                return

            client = existing_client
            should_close = False
            if client is None:
                client = WeReadClient(headless=True, state_json=state_json)
                client.__enter__()
                client.ensure_ready()
                should_close = True

            try:
                from src.community.weread.scrapers.shelf import scrape_shelf
                from src.community.weread.scrapers.bookmarks import scrape_bookmarks

                task.scrape_phase = "books"
                task._notify()
                try:
                    books = scrape_shelf(client._page, vid)
                    await DataRepo.upsert_weread_books(db, user_id, books)
                    await db.commit()
                    task.scrape_counts["books"] = len(books)
                    task._notify()
                except Exception:
                    pass

                # Fetch bookmarks for each book (limit to avoid excessive API calls)
                task.scrape_phase = "bookmarks"
                task._notify()
                try:
                    book_ids = [b.book_id for b in books] if "books" in task.scrape_counts else []
                    all_bookmarks = []
                    for book_id in book_ids[:50]:  # limit to first 50 books
                        bms = scrape_bookmarks(client._page, book_id)
                        all_bookmarks.extend(bms)
                    if all_bookmarks:
                        await BookmarkRepo.upsert_bookmarks(db, user_id, all_bookmarks)
                        await db.commit()
                    task.scrape_counts["bookmarks"] = len(all_bookmarks)
                    task._notify()
                except Exception:
                    pass
            finally:
                if should_close:
                    client.__exit__(None, None, None)

    future = asyncio.run_coroutine_threadsafe(_do_scrape(), loop)
    future.result(timeout=600)
