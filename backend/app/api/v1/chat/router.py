"""
Chat API routes.

HTTP layer for chat operations (SSE stream and JSON complete).
Business logic is handled by ChatService.
"""

from app.api.v1.chat.dto.request import ChatRequest
from app.api.v1.chat.dto.response import ChatCompleteResponse
from app.application.chat.mapper import ChatMapper
from app.application.chat.service import ChatService
from app.core.dependencies import get_chat_service, get_current_user
from app.infrastructure.database.models.user import User
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])


# ────────────────────────────────────────────────────────
# chat_stream
# Endpoint: POST /chat/stream
# Streams AI reply tokens in real time via Server-Sent Events.
# ────────────────────────────────────────────────────────
@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Stream a chat reply as Server-Sent Events."""
    # Map HTTP body to application command with the authenticated user id.
    command = ChatMapper.request_to_command(payload, user.id)

    # Delegate streaming to ChatService — router only wraps SSE.
    return EventSourceResponse(
        chat_service.stream_chat(command, request),
        ping=15,
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ────────────────────────────────────────────────────────
# chat_complete
# Endpoint: POST /chat/complete
# Sends a message and returns the full AI reply as JSON.
# ────────────────────────────────────────────────────────
@router.post("/complete", response_model=ChatCompleteResponse)
async def chat_complete(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Send a message and receive the full AI reply as JSON."""
    # Map HTTP body to application command with the authenticated user id.
    command = ChatMapper.request_to_command(payload, user.id)
    # Run the full chat pipeline and return the complete reply as JSON.
    return await chat_service.complete_chat(command)
