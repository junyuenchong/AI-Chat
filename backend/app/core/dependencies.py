"""
FastAPI dependencies.

Auth and service wiring for routers.

Request path:
  api/v1/*/router.py
    → core/dependencies.py  (this file)
    → application/*/service.py
"""

from app.application.auth.service import AuthService
from app.application.chat.service import ChatService
from app.application.conversations.service import ConversationService
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.infrastructure.ai import build_chat_engine
from app.infrastructure.database.models import User
from app.infrastructure.database.repositories.chat import MessageRepository
from app.infrastructure.database.repositories.conversation import ConversationRepository
from app.infrastructure.database.repositories.user import UserRepository
from app.infrastructure.database.session import get_db
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)


# ────────────────────────────────────────────────────────
# get_current_user
# Path: core/dependencies.py
# Endpoint: all protected routes
# Use: decode JWT Bearer token and load the User row.
# ────────────────────────────────────────────────────────
async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Load the authenticated user from Bearer JWT."""
    # Step 1 — require Authorization header.
    if creds is None:
        raise UnauthorizedError("Not authenticated")
    try:
        # Step 2 — decode JWT to user id.
        user_id = decode_access_token(creds.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    # Step 3 — load user from Postgres.
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Unknown user")
    return user


# Built once at startup — ChatChain + LLM port (demo or Gemini/OpenAI).
_chat_engine = build_chat_engine()


# ────────────────────────────────────────────────────────
# get_auth_service
# Path: core/dependencies.py
# Use: inject AuthService into auth routes.
# ────────────────────────────────────────────────────────
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


# ────────────────────────────────────────────────────────
# get_chat_service
# Path: core/dependencies.py
# Use: inject ChatService into chat routes.
# ────────────────────────────────────────────────────────
def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(
        chat_engine=_chat_engine,
        conversations=ConversationRepository(db),
        messages=MessageRepository(db),
    )


# ────────────────────────────────────────────────────────
# get_conversation_service
# Path: core/dependencies.py
# Use: inject ConversationService into conversation routes.
# ────────────────────────────────────────────────────────
def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(ConversationRepository(db))
