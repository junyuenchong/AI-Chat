"""
Knowledge request DTOs.

Pydantic models for POST /documents.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ────────────────────────────────────────────────────────
# CreateDocumentRequest
# Internal — POST /documents request body.
# Validates filename and raw text content for knowledge upload.
# ────────────────────────────────────────────────────────
class CreateDocumentRequest(BaseModel):
    """POST /documents body — filename and raw text content."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=100_000)

    # ────────────────────────────────────────────────────────
    # filename_not_blank
    # Internal — CreateDocumentRequest field validator.
    # Rejects blank filenames and trims whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("filename")
    @classmethod
    def filename_not_blank(cls, value: str) -> str:
        # Reject filenames that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Filename cannot be blank.")
        # Normalize leading and trailing whitespace in the filename.
        return value.strip()

    # ────────────────────────────────────────────────────────
    # content_not_blank
    # Internal — CreateDocumentRequest field validator.
    # Rejects blank document content and trims whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        # Reject document bodies that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Content cannot be blank.")
        # Normalize leading and trailing whitespace in the uploaded text.
        return value.strip()
