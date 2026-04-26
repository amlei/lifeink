from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, VerificationCode
from src.core.auth.auth import generate_user_id, hash_password


class AuthRepo:
    @staticmethod
    async def get_active_user_by_email(db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.status == "active")
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_deleted_user_by_email(db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.status == "deleted")
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_user_by_pk(db: AsyncSession, pk: int) -> User | None:
        return await db.get(User, pk)

    @staticmethod
    async def create_user(
        db: AsyncSession, email: str, password: str
    ) -> User:
        uid = generate_user_id()
        name = f"星迹 {uid}"
        deleted = await AuthRepo.get_deleted_user_by_email(db, email)
        if deleted is not None:
            deleted.user_id = uid
            deleted.password_hash = hash_password(password)
            deleted.name = name
            deleted.status = "active"
            deleted.email_verified = True
            deleted.updated_at = datetime.now(timezone.utc).isoformat()
            await db.flush()
            return deleted
        user = User(
            user_id=uid,
            email=email,
            password_hash=hash_password(password),
            name=name,
            email_verified=True,
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession, user: User, name: str | None, avatar: str | None, bio: str | None
    ) -> User:
        if name is not None:
            user.name = name
        if avatar is not None:
            user.avatar = avatar
        if bio is not None:
            user.bio = bio
        await db.flush()
        return user

    @staticmethod
    async def update_password(db: AsyncSession, user: User, new_password: str) -> None:
        user.password_hash = hash_password(new_password)
        await db.flush()

    @staticmethod
    async def soft_delete(db: AsyncSession, user: User) -> None:
        user.status = "deleted"
        await db.flush()

    @staticmethod
    async def store_code(db: AsyncSession, email: str, code: str) -> None:
        expires = datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=10)
        row = VerificationCode(email=email, code=code, expires_at=expires.isoformat())
        db.add(row)
        await db.flush()

    @staticmethod
    async def verify_code(db: AsyncSession, email: str, code: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.code == code,
                VerificationCode.used == False,  # noqa: E712
                VerificationCode.expires_at > now,
            )
            .order_by(VerificationCode.id.desc())
            .limit(1)
        )
        row = (await db.execute(stmt)).scalar_one_or_none()
        if row is None:
            return False
        row.used = True
        await db.flush()
        return True
