"""
API v1 router.

Mounts feature routers under /api/v1. No business logic here.
"""

from app.api.v1.auth.router import router as auth_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.health.router import router as health_router
from app.api.v1.knowledge.router import router as knowledge_router
from fastapi import APIRouter

api_router = APIRouter()

# Health is mounted first — load balancers and probes hit it without auth.
api_router.include_router(health_router)
# Auth routes — register, login, logout, profile.
api_router.include_router(auth_router)
# Chat — SSE stream and JSON complete endpoints.
api_router.include_router(chat_router)
# Sidebar thread list and message history.
api_router.include_router(conversations_router)
# RAG document upload and listing (HTTP path: /documents).
api_router.include_router(knowledge_router)
