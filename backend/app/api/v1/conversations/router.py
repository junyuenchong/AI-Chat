"""
Conversation API routes.

HTTP layer for chat history threads (not the AI call itself).
Business logic is handled by ConversationService.
"""

from uuid import UUID

from app.api.v1.conversations.dto.response import (
    ConversationDetailResponse,
    ConversationResponse,
)
from app.application.conversations.mapper import ConversationMapper
from app.application.conversations.service import ConversationService
from app.core.dependencies import get_conversation_service, get_current_user
from app.infrastructure.database.models import User
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ────────────────────────────────────────────────────────
# list_conversations
# Endpoint: GET /conversations
# Lists all chat threads for the current user in the sidebar.
# ────────────────────────────────────────────────────────
@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """List all conversations for the authenticated user."""
    rows = await conversation_service.list_conversations(user)
    return [ConversationMapper.conversation_to_list_item(row) for row in rows]


# ────────────────────────────────────────────────────────
# get_conversation
# Endpoint: GET /conversations/{conversation_id}
# Loads a single thread with its full message history.
# ────────────────────────────────────────────────────────
@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get a single conversation with its full message history."""
    conversation = await conversation_service.get_conversation(
        user, str(conversation_id)
    )
    return ConversationMapper.conversation_with_messages(conversation)


# ────────────────────────────────────────────────────────
# delete_conversation
# Endpoint: DELETE /conversations/{conversation_id}
# Removes a thread and all of its messages.
# ────────────────────────────────────────────────────────
@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation and its messages."""
    await conversation_service.delete_conversation(user, str(conversation_id))
