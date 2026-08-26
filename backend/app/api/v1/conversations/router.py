"""Conversation HTTP routes — chat history threads (not the AI call)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.conversations.dto import ConversationDetailResponse, ConversationResponse
from app.core.dependencies import get_current_user
from app.db.conversation import ConversationRepository
from app.db.session import get_db
from app.models.user import User
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(ConversationRepository(db))


# ---------------------------------------------------------------------------
# List — sidebar; scoped to JWT user only.
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return await conversation_service.list_conversations(user)


# ---------------------------------------------------------------------------
# Detail — one thread with full Message history.
# ---------------------------------------------------------------------------
@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return await conversation_service.get_conversation(user, str(conversation_id))


# ---------------------------------------------------------------------------
# Delete — cascade removes messages via ORM relationship.
# ---------------------------------------------------------------------------
@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    await conversation_service.delete_conversation(user, str(conversation_id))
