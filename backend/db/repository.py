from __future__ import annotations

import json
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.community.douban.models import Book, Game, Movie, Note, Profile, Review

from .models import (
    BookRow,
    CommunityMeta,
    GameRow,
    MovieRow,
    NoteRow,
    ReviewRow,
)


class CommunityMetaRepo:
    @staticmethod
    async def get_binding(
        db: AsyncSession, user_id: int, platform: str
    ) -> CommunityMeta | None:
        stmt = select(CommunityMeta).where(
            CommunityMeta.user_id == user_id,
            CommunityMeta.platform == platform,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def save_binding(
        db: AsyncSession,
        user_id: int,
        platform: str,
        community_user_id: str,
        profile: Profile,
    ) -> CommunityMeta:
        existing = await CommunityMetaRepo.get_binding(db, user_id, platform)
        if existing is not None:
            existing.bound = 1
            existing.community_user_id = community_user_id
            existing.profile_json = profile.model_dump_json()
            await db.flush()
            return existing

        row = CommunityMeta(
            user_id=user_id,
            platform=platform,
            bound=1,
            community_user_id=community_user_id,
            profile_json=profile.model_dump_json(),
        )
        db.add(row)
        await db.flush()
        return row

    @staticmethod
    async def delete_binding(
        db: AsyncSession, user_id: int, platform: str
    ) -> None:
        row = await CommunityMetaRepo.get_binding(db, user_id, platform)
        if row is not None:
            await db.delete(row)
            await db.flush()

    @staticmethod
    async def save_session_state(
        db: AsyncSession,
        user_id: int,
        platform: str,
        state_json: str,
        expires_at: str | None,
    ) -> None:
        row = await CommunityMetaRepo.get_binding(db, user_id, platform)
        if row is not None:
            row.session_state_json = state_json
            row.session_expires_at = expires_at
            await db.flush()

    @staticmethod
    async def get_session_state(
        db: AsyncSession, user_id: int, platform: str
    ) -> tuple[str | None, str | None]:
        row = await CommunityMetaRepo.get_binding(db, user_id, platform)
        if row is None:
            return None, None
        return row.session_state_json, row.session_expires_at


class DataRepo:
    @staticmethod
    async def upsert_books(
        db: AsyncSession, user_id: int, items: list[Book]
    ) -> int:
        count = 0
        for item in items:
            tags_json = json.dumps(item.tags) if item.tags else None
            stmt = insert(BookRow).values(
                user_id=user_id,
                title=item.title,
                url=item.url,
                cover=item.cover,
                author=item.author,
                country=item.country,
                translator=item.translator,
                publisher=item.publisher,
                pub_date=item.pub_date,
                price=item.price,
                rating=item.rating,
                read_date=item.read_date,
                status=item.status,
                tags=tags_json,
                comment=item.comment,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "url"],
                set_={
                    "title": stmt.excluded.title,
                    "cover": stmt.excluded.cover,
                    "author": stmt.excluded.author,
                    "country": stmt.excluded.country,
                    "translator": stmt.excluded.translator,
                    "publisher": stmt.excluded.publisher,
                    "pub_date": stmt.excluded.pub_date,
                    "price": stmt.excluded.price,
                    "rating": stmt.excluded.rating,
                    "read_date": stmt.excluded.read_date,
                    "status": stmt.excluded.status,
                    "tags": stmt.excluded.tags,
                    "comment": stmt.excluded.comment,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def upsert_movies(
        db: AsyncSession, user_id: int, items: list[Movie]
    ) -> int:
        count = 0
        for item in items:
            tags_json = json.dumps(item.tags) if item.tags else None
            stmt = insert(MovieRow).values(
                user_id=user_id,
                title=item.title,
                url=item.url,
                cover=item.cover,
                release_date=item.release_date,
                rating=item.rating,
                watch_date=item.watch_date,
                tags=tags_json,
                comment=item.comment,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "url"],
                set_={
                    "title": stmt.excluded.title,
                    "cover": stmt.excluded.cover,
                    "release_date": stmt.excluded.release_date,
                    "rating": stmt.excluded.rating,
                    "watch_date": stmt.excluded.watch_date,
                    "tags": stmt.excluded.tags,
                    "comment": stmt.excluded.comment,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def upsert_games(
        db: AsyncSession, user_id: int, items: list[Game]
    ) -> int:
        count = 0
        for item in items:
            tags_json = json.dumps(item.tags) if item.tags else None
            stmt = insert(GameRow).values(
                user_id=user_id,
                title=item.title,
                url=item.url,
                cover=item.cover,
                desc=item.desc,
                rating=item.rating,
                release_date=item.release_date,
                play_date=item.play_date,
                tags=tags_json,
                comment=item.comment,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "url"],
                set_={
                    "title": stmt.excluded.title,
                    "cover": stmt.excluded.cover,
                    "desc": stmt.excluded.desc,
                    "rating": stmt.excluded.rating,
                    "release_date": stmt.excluded.release_date,
                    "play_date": stmt.excluded.play_date,
                    "tags": stmt.excluded.tags,
                    "comment": stmt.excluded.comment,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def upsert_reviews(
        db: AsyncSession, user_id: int, items: list[Review]
    ) -> int:
        count = 0
        for item in items:
            stmt = insert(ReviewRow).values(
                user_id=user_id,
                subject_title=item.subject_title,
                subject_url=item.subject_url,
                subject_img_url=item.subject_img_url,
                review_title=item.review_title,
                review_url=item.review_url,
                date=item.date,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "review_url"],
                set_={
                    "subject_title": stmt.excluded.subject_title,
                    "subject_url": stmt.excluded.subject_url,
                    "subject_img_url": stmt.excluded.subject_img_url,
                    "review_title": stmt.excluded.review_title,
                    "date": stmt.excluded.date,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def upsert_notes(
        db: AsyncSession, user_id: int, items: list[Note]
    ) -> int:
        count = 0
        for item in items:
            stmt = insert(NoteRow).values(
                user_id=user_id,
                title=item.title,
                url=item.url,
                date=item.date,
                location=item.location,
                body=item.body,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "url"],
                set_={
                    "title": stmt.excluded.title,
                    "date": stmt.excluded.date,
                    "location": stmt.excluded.location,
                    "body": stmt.excluded.body,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def get_books(db: AsyncSession, user_id: int) -> Sequence[BookRow]:
        stmt = select(BookRow).where(BookRow.user_id == user_id)
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_movies(db: AsyncSession, user_id: int) -> Sequence[MovieRow]:
        stmt = select(MovieRow).where(MovieRow.user_id == user_id)
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_games(db: AsyncSession, user_id: int) -> Sequence[GameRow]:
        stmt = select(GameRow).where(GameRow.user_id == user_id)
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_reviews(db: AsyncSession, user_id: int) -> Sequence[ReviewRow]:
        stmt = select(ReviewRow).where(ReviewRow.user_id == user_id)
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def get_notes(db: AsyncSession, user_id: int) -> Sequence[NoteRow]:
        stmt = select(NoteRow).where(NoteRow.user_id == user_id)
        return (await db.execute(stmt)).scalars().all()
