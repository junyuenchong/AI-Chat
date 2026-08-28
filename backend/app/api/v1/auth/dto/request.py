"""
Auth request DTOs.

Pydantic models for POST /auth/register and POST /auth/login.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ────────────────────────────────────────────────────────
# RegisterRequest
# Internal — POST /auth/register request body.
# Validates email, password, and display name for sign-up.
# ────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """POST /auth/register body."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    # ────────────────────────────────────────────────────────
    # password_not_blank
    # Internal — RegisterRequest field validator.
    # Rejects passwords that are only whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        # Reject passwords that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Password cannot be blank.")
        return value

    # ────────────────────────────────────────────────────────
    # name_not_blank
    # Internal — RegisterRequest field validator.
    # Rejects display names that are only whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        # Reject display names that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Name cannot be blank.")
        return value


# ────────────────────────────────────────────────────────
# LoginRequest
# Internal — POST /auth/login request body.
# Validates email and password for sign-in.
# ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    """POST /auth/login body."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    # ────────────────────────────────────────────────────────
    # password_not_blank
    # Internal — LoginRequest field validator.
    # Rejects passwords that are only whitespace.
    # ────────────────────────────────────────────────────────
    @field_validator("password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        # Reject login passwords that contain only whitespace characters.
        if not value.strip():
            raise ValueError("Password cannot be blank.")
        return value
