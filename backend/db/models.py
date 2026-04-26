from __future__ import annotations

import json

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[str] = mapped_column(default=lambda: _now())

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r})"


class CommunityMeta(Base):
    __tablename__ = "community_meta"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_user_platform"),
        Index("ix_community_meta_user_platform", "user_id", "platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str]
    bound: Mapped[int] = mapped_column(default=0)
    community_user_id: Mapped[str | None]
    profile_json: Mapped[str | None]
    session_state_json: Mapped[str | None]
    session_expires_at: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(default=lambda: _now())
    updated_at: Mapped[str] = mapped_column(default=lambda: _now(), onupdate=lambda: _now())

    def to_api_dict(self) -> dict:
        profile = json.loads(self.profile_json) if self.profile_json else None
        return {
            "bound": bool(self.bound),
            "platform": self.platform,
            "user_id": self.community_user_id,
            "profile": profile,
        }


class BookRow(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_books_user_url"),
        Index("ix_books_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[str]
    cover: Mapped[str | None]
    author: Mapped[str | None]
    country: Mapped[str | None]
    translator: Mapped[str | None]
    publisher: Mapped[str | None]
    pub_date: Mapped[str | None]
    price: Mapped[str | None]
    rating: Mapped[int | None]
    read_date: Mapped[str | None]
    status: Mapped[str | None]
    tags: Mapped[str | None]  # JSON array
    comment: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Book":
        from src.community.douban.models import Book
        tags = json.loads(self.tags) if self.tags else None
        return Book(
            title=self.title, url=self.url, cover=self.cover,
            author=self.author, country=self.country, translator=self.translator,
            publisher=self.publisher, pub_date=self.pub_date, price=self.price,
            rating=self.rating, read_date=self.read_date, status=self.status,
            tags=tags, comment=self.comment,
        )


class MovieRow(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_movies_user_url"),
        Index("ix_movies_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[str]
    cover: Mapped[str | None]
    release_date: Mapped[str | None]
    rating: Mapped[int | None]
    watch_date: Mapped[str | None]
    tags: Mapped[str | None]  # JSON array
    comment: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Movie":
        from src.community.douban.models import Movie
        tags = json.loads(self.tags) if self.tags else None
        return Movie(
            title=self.title, url=self.url, cover=self.cover,
            release_date=self.release_date, rating=self.rating,
            watch_date=self.watch_date, tags=tags, comment=self.comment,
        )


class GameRow(Base):
    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_games_user_url"),
        Index("ix_games_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[str]
    cover: Mapped[str | None]
    desc: Mapped[str | None]
    rating: Mapped[int | None]
    release_date: Mapped[str | None]
    play_date: Mapped[str | None]
    tags: Mapped[str | None]  # JSON array
    comment: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Game":
        from src.community.douban.models import Game
        tags = json.loads(self.tags) if self.tags else None
        return Game(
            title=self.title, url=self.url, cover=self.cover,
            desc=self.desc, rating=self.rating, release_date=self.release_date,
            play_date=self.play_date, tags=tags, comment=self.comment,
        )


class ReviewRow(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "review_url", name="uq_reviews_user_url"),
        Index("ix_reviews_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_title: Mapped[str]
    subject_url: Mapped[str | None]
    subject_img_url: Mapped[str | None]
    review_title: Mapped[str | None]
    review_url: Mapped[str | None]
    date: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Review":
        from src.community.douban.models import Review
        return Review(
            subject_title=self.subject_title, subject_url=self.subject_url,
            subject_img_url=self.subject_img_url, review_title=self.review_title,
            review_url=self.review_url, date=self.date,
        )


class NoteRow(Base):
    __tablename__ = "notes"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_notes_user_url"),
        Index("ix_notes_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Note":
        from src.community.douban.models import Note
        return Note(title=self.title, url=self.url)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
