"""Auth request and response DTOs — extra=forbid so unknown fields fail clearly."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """POST /auth/register body."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be blank.")
        return value

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be blank.")
        return value


class LoginRequest(BaseModel):
    """POST /auth/login body."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be blank.")
        return value


class TokenResponse(BaseModel):
    """JWT access token plus basic user fields after register/login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    name: str


class UserResponse(BaseModel):
    """Public user profile returned by GET /auth/me (no hashed_password)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    email: str
    name: str
