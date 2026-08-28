"""
Chat response DTOs.

Pydantic models for non-streaming chat replies.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ────────────────────────────────────────────────────────
# ChatCompleteResponse
# Internal — POST /chat/complete response body.
# Returns the full AI reply with conversation id and LLM label.
# ────────────────────────────────────────────────────────
class ChatCompleteResponse(BaseModel):
    """Non-streaming chat reply with conversation id and LLM label."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    content: str
    llm: str
