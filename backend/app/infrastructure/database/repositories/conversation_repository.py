"""
Conversation repository.

Persistence for conversations and messages.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.message import Message


class ConversationRepository:
    """Load, create, and delete conversations scoped by user_id."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — database
    # Stores the async SQLAlchemy session for repository queries.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # list_for_user
    # Internal — database
    # Returns recent conversations owned by the given user.
    # ────────────────────────────────────────────────────────
    async def list_for_user(
        self, user_id: str, *, limit: int = 100
    ) -> list[Conversation]:
        # Most recently updated conversations first.
        rows = await self.db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(rows.all())

    # ────────────────────────────────────────────────────────
    # get_for_user
    # Internal — database
    # Loads one conversation scoped to the owning user.
    # ────────────────────────────────────────────────────────
    async def get_for_user(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        # Always filter by user_id — never trust conversation_id alone.
        return await self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    # ────────────────────────────────────────────────────────
    # get_with_messages
    # Internal — database
    # Loads a conversation and eagerly fetches its message history.
    # ────────────────────────────────────────────────────────
    async def get_with_messages(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        # Eager-load messages in one round trip via selectinload.
        return await self.db.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )

    # ────────────────────────────────────────────────────────
    # create
    # Internal — database
    # Persists a new conversation row and returns the flushed entity.
    # ────────────────────────────────────────────────────────
    async def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    # ────────────────────────────────────────────────────────
    # delete
    # Internal — database
    # Deletes a conversation and its related messages via ORM cascade.
    # ────────────────────────────────────────────────────────
    async def delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)


class MessageRepository:
    """Persist messages and load (role, content) history for the LLM."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — database
    # Stores the async SQLAlchemy session for repository queries.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # list_history
    # Internal — database
    # Returns ordered (role, content) tuples for LLM prompt building.
    # ────────────────────────────────────────────────────────
    async def list_history(self, conversation_id: str) -> list[tuple[str, str]]:
        """Tuples keep the LLM path free of ORM objects."""
        rows = (
            await self.db.execute(
                select(Message.role, Message.content)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
        ).all()
        # Project ORM rows into plain (role, content) tuples.
        return [(row.role, row.content) for row in rows]

    # ────────────────────────────────────────────────────────
    # add
    # Internal — database
    # Inserts one message into a conversation and flushes the row.
    # ────────────────────────────────────────────────────────
    async def add(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        await self.db.flush()
        return message

    # ────────────────────────────────────────────────────────
    # count
    # Internal — database
    # Counts messages in a conversation for summarize-job scheduling.
    # ────────────────────────────────────────────────────────
    async def count(self, conversation_id: str) -> int:
        # Used to decide when to enqueue the summarize ARQ job.
        value = await self.db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        return int(value or 0)
