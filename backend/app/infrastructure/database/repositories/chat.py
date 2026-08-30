"""Message persistence for chat turns."""

from app.infrastructure.database.models import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:
    """Load and store chat messages."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        value = await self.db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        return int(value or 0)
