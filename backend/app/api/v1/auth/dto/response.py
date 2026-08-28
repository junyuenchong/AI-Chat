"""
Auth response DTOs.

Pydantic models for token and profile responses.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ────────────────────────────────────────────────────────
# TokenResponse
# Internal — POST /auth/register and /auth/login response body.
# Returns a JWT token and basic user fields after sign-up or sign-in.
# ────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    """JWT access token plus basic user fields after register/login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    name: str


# ────────────────────────────────────────────────────────
# UserResponse
# Internal — GET /auth/me response body.
# Returns the public user profile without the hashed password.
# ────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Public user profile returned by GET /auth/me (no hashed_password)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    email: str
    name: str
