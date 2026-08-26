"""Shared FastAPI dependencies (JWT + service wiring)."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.db.user import UserRepository
from app.models.user import User
from app.services.auth import AuthService

# auto_error=False → missing Bearer becomes our JSON 401, not FastAPI 403.
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # ---------------------------------------------------------------------------
    # Decode JWT → load User — one place so all routers share 401 behavior.
    # ---------------------------------------------------------------------------
    if creds is None:
        raise UnauthorizedError("Not authenticated")
    try:
        user_id = decode_access_token(creds.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Unknown user")
    return user


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))
