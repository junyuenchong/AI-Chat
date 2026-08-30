"""
Auth application service.

Handles sign-up, login, and loading the current user's profile.
"""

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import verify_password
from app.infrastructure.database.models import User
from app.infrastructure.database.repositories.user import UserRepository
from sqlalchemy.exc import IntegrityError


class AuthService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — created by dependency injection.
    # Stores the user repository used for all auth database calls.
    # ────────────────────────────────────────────────────────
    def __init__(self, users: UserRepository) -> None:
        """Receive the user repository from FastAPI dependencies."""
        self.users = users

    # ────────────────────────────────────────────────────────
    # register_user
    # Endpoint: POST /auth/register
    # Creates a new account and returns the persisted User row.
    # ────────────────────────────────────────────────────────
    async def register_user(self, user: User) -> User:
        """Sign up a new user and return the saved User entity."""
        # Reject duplicate email before hitting the database.
        existing = await self.users.get_by_email(user.email)
        if existing:
            raise ConflictError("Email already registered")

        try:
            await self.users.create(user)
            await self.users.db.commit()
        except IntegrityError as exc:
            await self.users.db.rollback()
            raise ConflictError("Email already registered") from exc

        return user

    # ────────────────────────────────────────────────────────
    # login_user
    # Endpoint: POST /auth/login
    # Checks email and password, then returns the User row.
    # ────────────────────────────────────────────────────────
    async def login_user(self, email: str, password: str) -> User:
        """Log in with email and password and return the User entity."""
        user = await self.users.get_by_email(email)
        # Same error for bad email and bad password (no account enumeration).
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return user
