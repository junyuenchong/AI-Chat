"""
Health API routes.

HTTP layer for dependency probes used by the UI status pills.
"""

from app.api.v1.health.dto.response import HealthLayersResponse, HealthResponse
from app.core.config import get_settings
from app.core.database import get_db
from app.infrastructure.cache.redis import get_redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


# ────────────────────────────────────────────────────────
# health
# Endpoint: GET /health
# Checks Postgres, Redis, and LLM config for the status pills.
# ────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Public health check (no authentication required)."""
    # Load app metadata for the response payload.
    settings = get_settings()
    postgres_ok = False
    redis_ok = False

    # Probe Postgres with a lightweight query.
    try:
        await db.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        postgres_ok = False

    # Probe Redis only when a client is configured (optional dependency).
    redis = get_redis()
    if redis is not None:
        try:
            redis_ok = bool(await redis.ping())
        except Exception:
            redis_ok = False

    # Degrade gracefully when Postgres is down; Redis is optional.
    return HealthResponse(
        status="ok" if postgres_ok else "degraded",
        app=settings.app_name,
        llm=settings.llm_provider,
        postgres=postgres_ok,
        redis=redis_ok,
        layers=HealthLayersResponse(
            langchain="AI components (LLM, prompts, embeddings)",
            rag="Retriever + Knowledge chunks + LLM",
        ),
    )
