from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .base import Base
from .models import User

_DB_DIR = Path(__file__).resolve().parent / "data"
_DB_PATH = _DB_DIR / "lifeink.db"
_DEFAULT_USER = "amlei"

engine = create_async_engine(
    f"sqlite+aiosqlite:///{_DB_PATH}",
    echo=False,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_default_user(db: AsyncSession) -> User:
    stmt = select(User).where(User.username == _DEFAULT_USER)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(username=_DEFAULT_USER)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def init_db() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await get_default_user(session)
