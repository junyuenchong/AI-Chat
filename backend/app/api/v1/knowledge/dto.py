"""Knowledge request and response DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateDocumentRequest(BaseModel):
    """POST /documents body — filename and raw text content."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=100_000)

    @field_validator("filename")
    @classmethod
    def filename_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Filename cannot be blank.")
        return value.strip()

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Content cannot be blank.")
        return value.strip()


class DocumentResponse(BaseModel):
    """Document metadata returned by list/create (no full content)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    filename: str
    created_at: datetime
