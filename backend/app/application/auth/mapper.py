"""
Auth mapper.

Converts between API DTOs, domain objects, and database models.
"""

from uuid import uuid4

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.core.security import create_access_token, hash_password
from app.infrastructure.database.models import User


class AuthMapper:
    """Convert auth data between HTTP, application, and database layers."""

    # ────────────────────────────────────────────────────────
    # register_request_to_user
    # Endpoint: POST /auth/register (internal)
    # Converts sign-up form fields into a User row ready to save.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def register_request_to_user(request: RegisterRequest) -> User:
        """Build a new User from the sign-up form. Password is hashed here."""
        return User(
            id=str(uuid4()),
            email=request.email.lower(),
            name=request.name,
            hashed_password=hash_password(request.password),
        )

    # ────────────────────────────────────────────────────────
    # user_to_profile_response
    # Endpoint: GET /auth/me (internal)
    # Converts a User row into safe profile JSON (no password).
    # ────────────────────────────────────────────────────────
    @staticmethod
    def user_to_profile_response(user: User) -> UserResponse:
        """Return id, email, and name only — never the hashed password."""
        return UserResponse(id=user.id, email=user.email, name=user.name)

    # ────────────────────────────────────────────────────────
    # user_to_token_response
    # Endpoint: POST /auth/register, POST /auth/login (internal)
    # Converts a User row into a JWT token plus user info.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def user_to_token_response(user: User) -> TokenResponse:
        """Return access token and user details after successful auth."""
        return TokenResponse(
            access_token=create_access_token(user.id),
            user_id=user.id,
            email=user.email,
            name=user.name,
        )

    # ────────────────────────────────────────────────────────
    # login_credentials
    # Endpoint: POST /auth/login (internal)
    # Extracts email and password from the login request body.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def login_credentials(request: LoginRequest) -> tuple[str, str]:
        """Return (email, password) for the auth service."""
        return request.email, request.password
