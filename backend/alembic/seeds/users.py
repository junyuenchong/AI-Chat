"""
User seeds.

Creates the demo account and a starter conversation thread.
"""

from __future__ import annotations

from uuid import uuid4

from app.core.security import hash_password
from app.infrastructure.database.models import Conversation, Message, User
from app.infrastructure.database.repositories.user import UserRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Demo credentials — local development only.
DEMO_USER_EMAIL = "demo@example.com"
DEMO_USER_PASSWORD = "demo123"
DEMO_USER_NAME = "Demo User"

DEMO_CONVERSATION_TITLE = "Getting started"
DEMO_MESSAGES: tuple[tuple[str, str], ...] = (
    ("user", "What is our annual leave policy?"),
    (
        "assistant",
        "Full-time employees receive 14 days of annual leave per calendar year.",
    ),
)


# ────────────────────────────────────────────────────────
# seed_users
# Internal — alembic/seeds
# Ensures the demo account exists and returns whether it was newly created.
# ────────────────────────────────────────────────────────
async def seed_users(db: AsyncSession) -> tuple[User, bool]:
    """Return the demo user, creating the row when missing."""
    users = UserRepository(db)
    existing = await users.get_by_email(DEMO_USER_EMAIL)
    if existing is not None:
        return existing, False

    user = User(
        id=str(uuid4()),
        email=DEMO_USER_EMAIL.lower(),
        name=DEMO_USER_NAME,
        hashed_password=hash_password(DEMO_USER_PASSWORD),
    )
    await users.create(user)
    return user, True


# ────────────────────────────────────────────────────────
# seed_conversations
# Internal — alembic/seeds
# Adds one starter thread so the sidebar is not empty on first login.
# ────────────────────────────────────────────────────────
async def seed_conversations(db: AsyncSession, user_id: str) -> bool:
    """Create a sample conversation when the demo user has none yet."""
    existing = await db.scalar(
        select(Conversation.id).where(Conversation.user_id == user_id).limit(1)
    )
    if existing is not None:
        return False

    conversation = Conversation(
        user_id=user_id,
        title=DEMO_CONVERSATION_TITLE,
        summary="Sample thread about HR policy.",
    )
    db.add(conversation)
    await db.flush()

    for role, content in DEMO_MESSAGES:
        db.add(
            Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
            )
        )

    return True
