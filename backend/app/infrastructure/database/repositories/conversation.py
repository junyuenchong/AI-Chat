"""
Conversation persistence.

Request path:
  application/conversations/service.py
    → infrastructure/database/repositories/conversation.py  (this file)
    → infrastructure/database/models.py (Conversation)
"""

from app.infrastructure.database.models import Conversation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ConversationRepository:
    """Load, create, and delete conversations scoped by user."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Path: repositories/conversation.py
    # Use: store the async SQLAlchemy session for this request.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # list_for_user
    # Path: repositories/conversation.py
    # Endpoint: GET /conversations (internal)
    # Use: sidebar list sorted by most recent activity.
    # ────────────────────────────────────────────────────────
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

    # ────────────────────────────────────────────────────────
    # get_for_user
    # Path: repositories/conversation.py
    # Use: load one thread row scoped to the owning user.
    # ────────────────────────────────────────────────────────
    async def get_for_user(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        return await self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    # ────────────────────────────────────────────────────────
    # get_with_messages
    # Path: repositories/conversation.py
    # Endpoint: GET /conversations/{id} (internal)
    # Use: eager-load messages for the chat pane.
    # ────────────────────────────────────────────────────────
    async def get_with_messages(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        return await self.db.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )

    # ────────────────────────────────────────────────────────
    # create
    # Path: repositories/conversation.py
    # Use: insert a new thread row on first chat message.
    # ────────────────────────────────────────────────────────
    async def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    # ────────────────────────────────────────────────────────
    # delete
    # Path: repositories/conversation.py
    # Endpoint: DELETE /conversations/{id} (internal)
    # Use: remove thread and cascade-delete messages.
    # ────────────────────────────────────────────────────────
    async def delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
