"""Health HTTP route — dependency checks for UI status pills."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.health.dto import HealthLayersResponse, HealthResponse
from app.clients.redis import get_redis
from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


# ---------------------------------------------------------------------------
# Public (no JWT) — Postgres + Redis + LLM provider; fail soft per check.
# ---------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    postgres_ok = False
    redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        postgres_ok = False

    redis = get_redis()
    if redis is not None:
        try:
            redis_ok = bool(await redis.ping())
        except Exception:
            redis_ok = False

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
