from __future__ import annotations

import asyncio
import base64
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from community.douban.client import DoubanClient
from community.douban.models.profile import Profile
from community.douban.session import _resolve_project_root

_META_FILENAME = "douban-meta.json"
_QR_DIR = _resolve_project_root() / "tmp"


@dataclass
class BindTask:
    task_id: str
    platform: str
    status: Literal["pending", "scanned", "logged_in", "fetching_profile", "bound", "failed"] = "pending"
    qr_base64: str | None = None
    user_id: str | None = None
    profile: Profile | None = None
    error: str | None = None
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


class BindManager:
    """Manages Douban account binding lifecycle."""

    def __init__(self) -> None:
        self._tasks: dict[str, BindTask] = {}

    @property
    def meta_path(self) -> Path:
        return _resolve_project_root() / ".playwright" / _META_FILENAME

    def load_meta(self) -> dict | None:
        if not self.meta_path.is_file():
            return None
        try:
            return json.loads(self.meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    @property
    def is_bound(self) -> bool:
        meta = self.load_meta()
        if not meta or not meta.get("bound"):
            return False
        from community.douban.session import SessionManager
        return SessionManager().has_valid_session

    def save_meta(self, user_id: str, profile: Profile) -> None:
        data = {
            "bound": True,
            "platform": "douban",
            "user_id": user_id,
            "profile": profile.model_dump(),
        }
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def delete_meta(self) -> None:
        if self.meta_path.is_file():
            self.meta_path.unlink()
        from community.douban.session import SessionManager
        state = SessionManager().state_path
        if state.is_file():
            state.unlink()
        self._tasks.clear()

    def start_bind(self, channel: str = "msedge") -> BindTask:
        self._tasks.clear()
        task_id = uuid.uuid4().hex[:12]
        task = BindTask(task_id=task_id, platform="douban")
        task.bind_loop()
        self._tasks[task_id] = task

        def _run() -> None:
            try:
                client = DoubanClient(
                    headless=False,
                    channel=channel,
                    on_progress=lambda s: (
                        setattr(task, "status", s) or task._notify()
                    ) if s != "qr_ready" else _handle_qr(),
                )

                def _handle_qr() -> None:
                    qr_path = _QR_DIR / "douban-login-qr.png"
                    if qr_path.is_file():
                        task.qr_base64 = base64.b64encode(qr_path.read_bytes()).decode()
                    task._notify()

                client.__enter__()
                client.ensure_ready(qr_output_dir=_QR_DIR)

                task.user_id = client.user_id
                task.status = "fetching_profile"
                task._notify()

                task.profile = client.scrape_profile()
                self.save_meta(client.user_id, task.profile)

                task.status = "bound"
                task._notify()

                client.__exit__(None, None, None)
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                task._notify()

        asyncio.get_event_loop().run_in_executor(None, _run)
        return task


# Platform registry
_managers: dict[str, BindManager] = {}


def get_manager(platform: str) -> BindManager | None:
    if platform == "douban":
        if platform not in _managers:
            _managers[platform] = BindManager()
        return _managers[platform]
    return None


def supported_platforms() -> list[str]:
    return ["douban"]
