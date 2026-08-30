"""
User repository.

Persistence for user accounts.
"""

from app.infrastructure.database.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """Persist and look up users by id or email."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — database
    # Stores the async SQLAlchemy session for repository queries.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # get_by_id
    # Internal — database
    # Loads a user by primary key.
    # ────────────────────────────────────────────────────────
    async def get_by_id(self, user_id: str) -> User | None:
        # Primary-key lookup via the session identity map.
        return await self.db.get(User, user_id)

    # ────────────────────────────────────────────────────────
    # get_by_email
    # Internal — database
    # Looks up a user by normalized email address.
    # ────────────────────────────────────────────────────────
    async def get_by_email(self, email: str) -> User | None:
        # Always store/query lowercased email so Login and Register agree.
        return await self.db.scalar(select(User).where(User.email == email.lower()))

    # ────────────────────────────────────────────────────────
    # create
    # Internal — database
    # Persists a new user row and returns the flushed entity.
    # ────────────────────────────────────────────────────────
    async def create(self, user: User) -> User:
        self.db.add(user)
        # Flush so the row gets an id before the caller commits.
        await self.db.flush()
        return user
