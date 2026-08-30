"""Conversation persistence."""

from app.infrastructure.database.models import Conversation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ConversationRepository:
    """Load, create, and delete conversations scoped by user."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(
        self, user_id: str, *, limit: int = 100
    ) -> list[Conversation]:
        rows = await self.db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(rows.all())

    async def get_for_user(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        return await self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    async def get_with_messages(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        return await self.db.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )

    async def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
