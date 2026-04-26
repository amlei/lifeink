from __future__ import annotations

import json

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    avatar: Mapped[str | None] = mapped_column(default=None)
    bio: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="active")
    email_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=lambda: _now())
    updated_at: Mapped[str] = mapped_column(default=lambda: _now(), onupdate=lambda: _now())

    def to_api_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "avatar": self.avatar,
            "bio": self.bio,
            "email_verified": self.email_verified,
            "created_at": self.created_at,
        }


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(nullable=False, index=True)
    code: Mapped[str] = mapped_column(nullable=False)
    expires_at: Mapped[str] = mapped_column(nullable=False)
    used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=lambda: _now())


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
        UniqueConstraint("user_id", "url", "source", name="uq_books_user_url_source"),
        Index("ix_books_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(default="douban")  # "douban" or "weread"
    title: Mapped[str]
    url: Mapped[str]  # Douban URL or WeRead bookId
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
    # WeRead-specific fields (nullable for Douban rows)
    isbn: Mapped[str | None]
    category: Mapped[str | None]
    intro: Mapped[str | None]
    total_words: Mapped[int | None]
    rating_detail: Mapped[str | None]  # e.g. "好评如潮"
    finished: Mapped[int | None]  # 0/1
    finish_reading: Mapped[int | None]  # 0/1
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

    def to_api_dict(self) -> dict:
        d = {
            "source": self.source,
            "title": self.title, "url": self.url, "cover": self.cover,
            "author": self.author, "translator": self.translator,
            "publisher": self.publisher, "price": self.price,
            "rating": self.rating,
        }
        if self.source == "weread":
            d.update({
                "book_id": self.url,
                "isbn": self.isbn, "category": self.category,
                "intro": self.intro, "total_words": self.total_words,
                "rating_detail": self.rating_detail,
                "finished": bool(self.finished) if self.finished is not None else None,
                "finish_reading": bool(self.finish_reading) if self.finish_reading is not None else None,
            })
        else:
            tags = json.loads(self.tags) if self.tags else None
            d.update({
                "country": self.country, "pub_date": self.pub_date,
                "read_date": self.read_date, "status": self.status,
                "tags": tags, "comment": self.comment,
            })
        return d


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

    def to_api_dict(self) -> dict:
        tags = json.loads(self.tags) if self.tags else None
        return {
            "title": self.title, "url": self.url, "cover": self.cover,
            "release_date": self.release_date, "rating": self.rating,
            "watch_date": self.watch_date, "tags": tags, "comment": self.comment,
        }


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
    date: Mapped[str | None]
    location: Mapped[str | None]
    body: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_pydantic(self) -> "community_models.Note":
        from src.community.douban.models import Note
        return Note(title=self.title, url=self.url, date=self.date, location=self.location, body=self.body)

    def to_api_dict(self) -> dict:
        return {
            "title": self.title, "url": self.url,
            "date": self.date, "location": self.location, "body": self.body,
        }


class BookmarkRow(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "book_id", "bookmark_id", name="uq_bookmarks_user_src_book_bm"),
        Index("ix_bookmarks_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(default="weread")  # "weread", etc.
    book_id: Mapped[str]
    book_title: Mapped[str | None]
    mark_text: Mapped[str]
    chapter_name: Mapped[str | None]
    chapter_idx: Mapped[int | None]
    style: Mapped[int | None]
    create_time: Mapped[int | None]
    bookmark_id: Mapped[str | None]
    scraped_at: Mapped[str] = mapped_column(default=lambda: _now())

    def to_api_dict(self) -> dict:
        return {
            "source": self.source,
            "book_id": self.book_id, "book_title": self.book_title,
            "mark_text": self.mark_text, "chapter_name": self.chapter_name,
            "chapter_idx": self.chapter_idx, "style": self.style,
            "create_time": self.create_time, "bookmark_id": self.bookmark_id,
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
