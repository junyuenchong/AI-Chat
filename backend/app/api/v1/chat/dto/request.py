"""
Chat request DTOs.

Pydantic models for POST /chat/* endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ────────────────────────────────────────────────────────
# ChatRequest
# Internal — POST /chat/stream and /chat/complete request body.
# Validates the user message, optional conversation id, and RAG flag.
# ────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """POST /chat/* body — message, optional conversation_id, RAG flag."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    use_rag: bool = True

    # ────────────────────────────────────────────────────────
    # message_not_blank
    # Internal — ChatRequest field validator.
    # Rejects empty messages and trims leading and trailing whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        # Reject messages that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Message cannot be blank.")
        # Normalize leading and trailing whitespace before passing to the service.
        return value.strip()
