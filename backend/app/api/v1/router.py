"""
API v1 router.

Mounts feature routers under /api/v1.
"""

from app.api.v1.auth.router import router as auth_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.documents.router import router as documents_router
from app.api.v1.health.router import router as health_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(conversations_router)
api_router.include_router(documents_router)
