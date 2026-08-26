"""User persistence — email lookup is case-insensitive to avoid duplicates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Persist and look up users by id or email."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        # Always store/query lowercased email so Login and Register agree.
        return await self.db.scalar(select(User).where(User.email == email.lower()))

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user
