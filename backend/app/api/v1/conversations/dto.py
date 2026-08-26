"""Conversation response DTOs — no internal-only fields."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """One message in a conversation detail response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    """Conversation list item without message bodies."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    """Conversation plus full message history."""

    messages: list[MessageResponse] = []
