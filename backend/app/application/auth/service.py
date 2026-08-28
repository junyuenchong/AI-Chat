"""
Auth application service.

Handles sign-up, login, and loading the current user's profile.
"""

from sqlalchemy.exc import IntegrityError

from app.api.v1.auth.dto.request import LoginRequest, RegisterRequest
from app.api.v1.auth.dto.response import TokenResponse, UserResponse
from app.application.auth.mapper import AuthMapper
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import verify_password
from app.infrastructure.database.models.user import User
from app.infrastructure.database.repositories.user_repository import UserRepository


class AuthService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the user repository used for all auth database calls.
    # ────────────────────────────────────────────────────────
    def __init__(self, users: UserRepository) -> None:
        """Receive the user repository from FastAPI dependencies."""
        # Keep the repository on the service for all auth database calls.
        self.users = users

    # ────────────────────────────────────────────────────────
    # register_user
    # Endpoint: POST /auth/register
    # Creates a new account and returns a login token.
    # ────────────────────────────────────────────────────────
    async def register_user(self, payload: RegisterRequest) -> TokenResponse:
        """Sign up a new user and return a JWT token."""
        # Reject duplicate email before hitting the database.
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email already registered")

        # Build a new user row with a hashed password.
        user = AuthMapper.register_request_to_user(payload)
        try:
            # Persist the user and commit the transaction.
            await self.users.create(user)
            await self.users.db.commit()
        except IntegrityError as exc:
            # Roll back if two sign-ups race on the same email.
            await self.users.db.rollback()
            raise ConflictError(
                "Email already registered"
            ) from exc  # Two sign-ups at the same time.

        # Return a JWT and basic profile info for the new account.
        return AuthMapper.user_to_login_response(user)

    # ────────────────────────────────────────────────────────
    # login_user
    # Endpoint: POST /auth/login
    # Checks email and password, then returns a login token.
    # ────────────────────────────────────────────────────────
    async def login_user(self, payload: LoginRequest) -> TokenResponse:
        """Log in with email and password and return a JWT token."""
        # Look up the account by email.
        user = await self.users.get_by_email(payload.email)

        # Same error for bad email and bad password (no account enumeration).
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        # Issue a token for the authenticated user.
        return AuthMapper.user_to_login_response(user)

    # ────────────────────────────────────────────────────────
    # get_user_profile
    # Endpoint: GET /auth/me
    # Returns the logged-in user's name and email for the app header.
    # ────────────────────────────────────────────────────────
    async def get_user_profile(self, user: User) -> UserResponse:
        """Return profile JSON for the user who is already authenticated."""
        # Map the database user to a safe profile response (no password).
        return AuthMapper.user_to_profile_response(user)
