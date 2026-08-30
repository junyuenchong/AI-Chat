"""
Chat response DTOs.

HTTP response bodies for non-streaming chat.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatCompleteResponse(BaseModel):
    """Non-streaming chat reply with conversation id and LLM label."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    content: str
    llm: str
