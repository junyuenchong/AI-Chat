"""Message queries for chat history and persistence."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    """Persist messages and load (role, content) history for the LLM."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---------------------------------------------------------------------------
    # History — tuples keep the LLM path free of ORM objects.
    # ---------------------------------------------------------------------------
    async def list_history(self, conversation_id: str) -> list[tuple[str, str]]:
        rows = (
            await self.db.execute(
                select(Message.role, Message.content)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
        ).all()
        return [(row.role, row.content) for row in rows]

    async def add(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        await self.db.flush()
        return message

    async def count(self, conversation_id: str) -> int:
        # Used to decide when to enqueue the summarize ARQ job.
        value = await self.db.scalar(
            select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
        )
        return int(value or 0)
