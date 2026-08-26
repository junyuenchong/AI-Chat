"""Auth use-cases: register, login, profile."""

from sqlalchemy.exc import IntegrityError

from app.api.v1.auth.dto import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.api.v1.auth.mapping import AuthMapper
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import verify_password
from app.db.user import UserRepository
from app.models.user import User


class AuthService:
    """Register, login, and expose the current user profile."""

    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        # ---------------------------------------------------------------------------
        # Create user — hash password in mapper; never return hashed_password.
        # ---------------------------------------------------------------------------
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email already registered")
        user = AuthMapper.to_entity(payload)
        try:
            await self.users.create(user)
            await self.users.db.commit()
        except IntegrityError as exc:
            await self.users.db.rollback()
            raise ConflictError("Email already registered") from exc
        return AuthMapper.to_token_response(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        # ---------------------------------------------------------------------------
        # Same 401 for unknown email and bad password (no user enumeration).
        # ---------------------------------------------------------------------------
        user = await self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return AuthMapper.to_token_response(user)

    async def get_profile(self, user: User) -> UserResponse:
        return AuthMapper.to_user_response(user)
