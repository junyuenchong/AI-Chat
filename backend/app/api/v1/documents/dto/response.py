"""
Documents response DTOs.

HTTP response bodies for knowledge-base list and upload.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Document metadata returned by list/create."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    filename: str
    created_at: datetime
