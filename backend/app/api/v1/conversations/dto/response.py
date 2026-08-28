"""
Conversation response DTOs.

Pydantic models for conversation list and detail endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ────────────────────────────────────────────────────────
# MessageResponse
# Internal — GET /conversations/{id} message item.
# Represents one message in a conversation detail response.
# ────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    """One message in a conversation detail response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


# ────────────────────────────────────────────────────────
# ConversationResponse
# Internal — GET /conversations list item.
# Returns conversation metadata without message bodies.
# ────────────────────────────────────────────────────────
class ConversationResponse(BaseModel):
    """Conversation list item without message bodies."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime


# ────────────────────────────────────────────────────────
# ConversationDetailResponse
# Internal — GET /conversations/{id} response body.
# Returns a conversation with its full message history.
# ────────────────────────────────────────────────────────
class ConversationDetailResponse(ConversationResponse):
    """Conversation plus full message history."""

    messages: list[MessageResponse] = []
