"""Auth entity ↔ DTO mapping — keep hashed_password out of HTTP responses."""

from app.api.v1.auth.dto import RegisterRequest, TokenResponse, UserResponse
from app.core.security import create_access_token, hash_password
from app.models.user import User


class AuthMapper:
    """Map auth request DTOs → User and User → response DTOs."""

    # ---------------------------------------------------------------------------
    # Register — hash once here; never store plaintext password.
    # ---------------------------------------------------------------------------
    @staticmethod
    def to_entity(request: RegisterRequest) -> User:
        return User(
            email=request.email.lower(),
            name=request.name,
            hashed_password=hash_password(request.password),
        )

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        return UserResponse(id=user.id, email=user.email, name=user.name)

    @staticmethod
    def to_token_response(user: User) -> TokenResponse:
        # JWT subject is user.id — never put email in the token.
        return TokenResponse(
            access_token=create_access_token(user.id),
            user_id=user.id,
            email=user.email,
            name=user.name,
        )
