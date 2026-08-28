"""
Conversation mapper.

Converts conversation and message database rows into API JSON responses.
"""

from app.api.v1.conversations.dto.response import (
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.message import Message


class ConversationMapper:
    """Convert conversation database rows into API responses."""

    # ────────────────────────────────────────────────────────
    # conversation_to_list_item
    # Endpoint: GET /conversations (internal)
    # Maps one conversation row to sidebar list JSON (no messages).
    # ────────────────────────────────────────────────────────
    @staticmethod
    def conversation_to_list_item(conversation: Conversation) -> ConversationResponse:
        """Return title and dates for the sidebar — messages are loaded separately."""
        # Expose metadata only — messages are fetched on thread open.
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    # ────────────────────────────────────────────────────────
    # message_to_response
    # Endpoint: GET /conversations/{id} (internal)
    # Maps one message row to chat history JSON.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def message_to_response(message: Message) -> MessageResponse:
        """Return role (user/assistant), content, and timestamp for one message."""
        # Map one stored message into the chat history item shape.
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )

    # ────────────────────────────────────────────────────────
    # conversation_with_messages
    # Endpoint: GET /conversations/{id} (internal)
    # Maps a conversation plus all its messages to full thread JSON.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def conversation_with_messages(
        conversation: Conversation,
    ) -> ConversationDetailResponse:
        """Return conversation metadata and every message in the thread."""
        # Combine thread metadata with the full message list.
        return ConversationDetailResponse(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                ConversationMapper.message_to_response(m) for m in conversation.messages
            ],
        )
