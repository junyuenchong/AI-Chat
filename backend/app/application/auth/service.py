"""
Auth application service.

Handles sign-up, login, and loading the current user's profile.

Request path:
  api/v1/auth/router.py
    → application/auth/mapper.py
    → application/auth/service.py  (this file)
    → infrastructure/database/repositories/user.py
"""

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import verify_password
from app.infrastructure.database.models import User
from app.infrastructure.database.repositories.user import UserRepository
from sqlalchemy.exc import IntegrityError


class AuthService:
    # ────────────────────────────────────────────────────────
    # __init__
    # Path: application/auth/service.py
    # Internal — created by dependency injection.
    # Use: stores the user repository used for all auth database calls.
    # ────────────────────────────────────────────────────────
    def __init__(self, users: UserRepository) -> None:
        """Receive the user repository from FastAPI dependencies."""
        self.users = users

    # ────────────────────────────────────────────────────────
    # register_user
    # Path: application/auth/service.py
    # Endpoint: POST /auth/register
    # Use: create a new account and return the persisted User row.
    # ────────────────────────────────────────────────────────
    async def register_user(self, user: User) -> User:
        """Sign up a new user and return the saved User entity."""
        # Step 1 — reject duplicate email before insert (fast path).
        existing = await self.users.get_by_email(user.email)
        if existing:
            raise ConflictError("Email already registered")

        try:
            # Step 2 — insert the new user row.
            await self.users.create(user)
            # Step 3 — commit so the account is visible to login immediately.
            await self.users.db.commit()
        except IntegrityError as exc:
            # Step 4 — race: another request registered the same email first.
            await self.users.db.rollback()
            raise ConflictError("Email already registered") from exc

        # Step 5 — return the saved entity to the router/mapper for JWT creation.
        return user

    # ────────────────────────────────────────────────────────
    # login_user
    # Path: application/auth/service.py
    # Endpoint: POST /auth/login
    # Use: verify email and password, then return the User row.
    # ────────────────────────────────────────────────────────
    async def login_user(self, email: str, password: str) -> User:
        """Log in with email and password and return the User entity."""
        # Step 1 — load the account by email.
        user = await self.users.get_by_email(email)

        # Step 2 — verify password; same error for unknown email or wrong password.
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        # Step 3 — return the user so the router can issue a JWT.
        return user
