"""HTTP v1 — wire feature routers only (no business logic)."""

from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.health.router import router as health_router
from app.api.v1.knowledge.router import router as knowledge_router

api_router = APIRouter()

# ---------------------------------------------------------------------------
# Mount features under /api/v1 (matching order does not matter).
# ---------------------------------------------------------------------------
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(conversations_router)
api_router.include_router(knowledge_router)
