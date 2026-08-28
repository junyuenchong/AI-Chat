"""
Auth mapper.

Converts sign-up/login data between API requests, database rows, and JSON responses.
"""

from uuid import uuid4

from app.api.v1.auth.dto.request import RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.core.security import create_access_token, hash_password
from app.infrastructure.database.models.user import User


class AuthMapper:
    """Convert auth data between HTTP requests, User rows, and API responses."""

    # ────────────────────────────────────────────────────────
    # register_request_to_user
    # Endpoint: POST /auth/register (internal)
    # Converts sign-up form fields into a User row ready to save.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def register_request_to_user(request: RegisterRequest) -> User:
        """Build a new User from the sign-up form. Password is hashed here."""
        # Create a new user row with a fresh id and hashed password.
        return User(
            id=str(uuid4()),
            # Lowercase email so login is case-insensitive.
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
        # Expose only public profile fields to the client.
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
        )

    # ────────────────────────────────────────────────────────
    # user_to_login_response
    # Endpoint: POST /auth/register, POST /auth/login (internal)
    # Converts a User row into a JWT token plus user info.
    # ────────────────────────────────────────────────────────
    @staticmethod
    def user_to_login_response(user: User) -> TokenResponse:
        """Return access token and user details after successful auth."""
        # Mint a JWT and include basic user info for the client.
        return TokenResponse(
            access_token=create_access_token(user.id),
            user_id=user.id,
            email=user.email,
            name=user.name,
        )
