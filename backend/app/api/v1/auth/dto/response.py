"""
Auth response DTOs.

HTTP response bodies for registration, login, and profile.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """JWT access token plus basic user fields after register/login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    name: str


class UserResponse(BaseModel):
    """Public user profile returned by GET /auth/me."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    email: str
    name: str
