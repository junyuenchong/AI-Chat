"""Conversation use-cases: list, get, create, delete chat history threads."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.conversations.dto import ConversationDetailResponse, ConversationResponse
from app.api.v1.conversations.mapping import ConversationMapper
from app.core.errors import AppError, NotFoundError
from app.db.conversation import ConversationRepository
from app.models.conversation import Conversation
from app.models.user import User


class ConversationService:
    """List, get, create, and delete conversations for the current user."""

    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def list_conversations(self, user: User) -> list[ConversationResponse]:
        # ---------------------------------------------------------------------------
        # Always scoped by user_id — never leak another account's threads.
        # ---------------------------------------------------------------------------
        try:
            rows = await self.conversations.list_for_user(user.id)
        except SQLAlchemyError as exc:
            raise AppError(
                "Could not load conversations.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        return [ConversationMapper.to_response(row) for row in rows]

    async def get_conversation(self, user: User, conversation_id: str) -> ConversationDetailResponse:
        try:
            conversation = await self.conversations.get_with_messages(conversation_id, user.id)
        except SQLAlchemyError as exc:
            raise AppError(
                "Could not load conversation.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        if conversation is None:
            raise NotFoundError("Conversation not found")
        return ConversationMapper.to_detail_response(conversation)

    async def delete_conversation(self, user: User, conversation_id: str) -> None:
        try:
            conversation = await self.conversations.get_for_user(conversation_id, user.id)
        except SQLAlchemyError as exc:
            raise AppError(
                "Could not delete conversation.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc
        if conversation is None:
            raise NotFoundError("Conversation not found")
        try:
            await self.conversations.delete(conversation)
            await self.conversations.db.commit()
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise AppError(
                "Could not delete conversation.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc

    async def get_or_create(
        self,
        user_id: str,
        conversation_id: str | None,
        title: str,
    ) -> tuple[Conversation, bool]:
        # ---------------------------------------------------------------------------
        # Chat entry: resume existing thread or create a new Conversation.
        # ---------------------------------------------------------------------------
        try:
            if conversation_id:
                conversation = await self.conversations.get_for_user(conversation_id, user_id)
                if conversation is None:
                    raise NotFoundError("Conversation not found")
                return conversation, False
            conversation = Conversation(
                id=str(uuid4()),
                user_id=user_id,
                title=title[:80] or "New conversation",
            )
            await self.conversations.create(conversation)
            return conversation, True
        except AppError:
            raise
        except SQLAlchemyError as exc:
            await self.conversations.db.rollback()
            raise AppError(
                "Could not create conversation.",
                code="DATABASE_ERROR",
                status_code=503,
            ) from exc

    async def touch(self, conversation: Conversation) -> None:
        conversation.updated_at = datetime.now(timezone.utc)
