"""
Knowledge response DTOs.

Pydantic models for document list and create responses.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ────────────────────────────────────────────────────────
# DocumentResponse
# Internal — GET /documents and POST /documents response item.
# Returns document metadata without the full text content.
# ────────────────────────────────────────────────────────
class DocumentResponse(BaseModel):
    """Document metadata returned by list/create (no full content)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    filename: str
    created_at: datetime
