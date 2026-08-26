"""Chat request and response DTOs."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    """POST /chat/* body — message, optional conversation_id, RAG flag."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    use_rag: bool = True

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank.")
        return value.strip()


class ChatCompleteResponse(BaseModel):
    """Non-streaming chat reply with conversation id and LLM label."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    content: str
    llm: str
