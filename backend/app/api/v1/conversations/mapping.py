"""Conversation entity → response DTO."""

from app.api.v1.conversations.dto import (
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationMapper:
    """Map Conversation / Message ORM rows to public response DTOs."""

    @staticmethod
    def to_response(conversation: Conversation) -> ConversationResponse:
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    @staticmethod
    def to_message_response(message: Message) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )

    @staticmethod
    def to_detail_response(conversation: Conversation) -> ConversationDetailResponse:
        return ConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[ConversationMapper.to_message_response(m) for m in conversation.messages],
        )
