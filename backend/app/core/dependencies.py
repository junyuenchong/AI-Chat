"""
FastAPI dependencies.

Auth and service wiring for routers — not middleware.

  Middleware  → request id, CORS, security headers, IP rate limit
  Depends()   → get_current_user, get_chat_service, …
  Application → use-cases (register, stream chat, upload document)
"""

from app.application.auth.service import AuthService
from app.application.chat.service import ChatService
from app.application.conversations.service import ConversationService
from app.application.documents.service import DocumentsService
from app.core.config import get_settings
from app.core.cookies import read_session_id
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.infrastructure.ai import build_chat_engine
from app.infrastructure.cache.redis import get_session_user_id
from app.infrastructure.database.models import User
from app.infrastructure.database.repositories.chat import MessageRepository
from app.infrastructure.database.repositories.conversation import ConversationRepository
from app.infrastructure.database.repositories.document import DocumentRepository
from app.infrastructure.database.repositories.user import UserRepository
from app.infrastructure.database.session import get_db
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Kept for OpenAPI, tests, and programmatic clients.
bearer_scheme = HTTPBearer(auto_error=False)


# ────────────────────────────────────────────────────────
# _resolve_user_id
# Internal — resolve authenticated user id from cookie or JWT.
# Checks session cookie first, then falls back to Bearer token.
# ────────────────────────────────────────────────────────
async def _resolve_user_id(
    request: Request, creds: HTTPAuthorizationCredentials | None
) -> str:
    """Resolve the authenticated user id from session cookie or Bearer JWT."""
    settings = get_settings()
    # Prefer browser session cookie over Bearer token when both are present.
    session_id = read_session_id(request, settings)
    if session_id:
        user_id = await get_session_user_id(session_id)
        if user_id:
            return user_id

    # No valid session — require a Bearer token for API clients.
    if creds is None:
        raise UnauthorizedError("Not authenticated")

    try:
        return decode_access_token(creds.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


# ────────────────────────────────────────────────────────
# get_current_user
# Internal — FastAPI dependency for authenticated User.
# Loads the user row after resolving id from session or Bearer JWT.
# ────────────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Load the authenticated user from session cookie or Bearer JWT."""
    user_id = await _resolve_user_id(request, creds)
    # Load the full user row — token alone does not prove the account still exists.
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Unknown user")
    return user


_chat_engine = build_chat_engine()


# ────────────────────────────────────────────────────────
# get_auth_service
# Internal — FastAPI dependency for AuthService.
# Builds AuthService with a request-scoped user repository.
# ────────────────────────────────────────────────────────
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Build AuthService with its required dependencies."""
    return AuthService(UserRepository(db))


# ────────────────────────────────────────────────────────
# get_chat_service
# Internal — FastAPI dependency for ChatService.
# Wires chat engine and conversation repositories.
# ────────────────────────────────────────────────────────
def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Build ChatService with its required dependencies."""
    return ChatService(
        chat_engine=_chat_engine,
        conversations=ConversationRepository(db),
        messages=MessageRepository(db),
    )


# ────────────────────────────────────────────────────────
# get_conversation_service
# Internal — FastAPI dependency for ConversationService.
# Builds ConversationService with a request-scoped repository.
# ────────────────────────────────────────────────────────
def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Build ConversationService with its required dependencies."""
    return ConversationService(ConversationRepository(db))


# ────────────────────────────────────────────────────────
# get_documents_service
# Internal — FastAPI dependency for DocumentsService.
# Builds DocumentsService with a request-scoped document repository.
# ────────────────────────────────────────────────────────
def get_documents_service(db: AsyncSession = Depends(get_db)) -> DocumentsService:
    """Build DocumentsService with its required dependencies."""
    return DocumentsService(DocumentRepository(db))
