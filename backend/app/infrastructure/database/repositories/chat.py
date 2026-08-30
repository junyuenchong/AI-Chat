"""
Message persistence for chat turns.

Request path:
  application/chat/service.py
    → infrastructure/database/repositories/chat.py  (this file)
    → infrastructure/database/models.py (Message)
"""

from app.infrastructure.database.models import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:
    """Load and store chat messages."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Path: repositories/chat.py
    # Use: store the async SQLAlchemy session for this request.
    # ────────────────────────────────────────────────────────
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ────────────────────────────────────────────────────────
    # list_history
    # Path: repositories/chat.py
    # Use: load (role, content) pairs for LangChain context window.
    # ────────────────────────────────────────────────────────
    async def list_history(self, conversation_id: str) -> list[tuple[str, str]]:
        # Step 1 — ordered by created_at so history reads chronologically.
        rows = (
            await self.db.execute(
                select(Message.role, Message.content)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
        ).all()
        return [(row.role, row.content) for row in rows]

    # ────────────────────────────────────────────────────────
    # add
    # Path: repositories/chat.py
    # Use: insert one user or assistant message row.
    # ────────────────────────────────────────────────────────
    async def add(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        await self.db.flush()  # Flush so id is available before commit.
        return message

    # ────────────────────────────────────────────────────────
    # count
    # Path: repositories/chat.py
    # Use: count messages in a thread (tests / future features).
    # ────────────────────────────────────────────────────────
    async def count(self, conversation_id: str) -> int:
        value = await self.db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        return int(value or 0)
