"""Chat HTTP routes: SSE stream + JSON complete."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.v1.chat.dto import ChatCompleteResponse, ChatRequest
from app.core.dependencies import get_current_user
from app.db.conversation import ConversationRepository
from app.db.message import MessageRepository
from app.db.session import get_db
from app.models.user import User
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(ConversationRepository(db), MessageRepository(db))


# ---------------------------------------------------------------------------
# Stream — main UI path (POST + SSE; browsers' EventSource is GET-only).
# ---------------------------------------------------------------------------
@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    # Disable nginx buffering so tokens flush immediately.
    return EventSourceResponse(
        chat_service.stream_chat(user, payload, request),
        ping=15,
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Complete — same RAG/LLM path as stream, one JSON body.
# ---------------------------------------------------------------------------
@router.post("/complete", response_model=ChatCompleteResponse)
async def chat_complete(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.complete_chat(user, payload)
