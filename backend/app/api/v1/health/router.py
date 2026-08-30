"""
Health API routes.

Public status check for Postgres and LLM provider.

Request path:
  frontend/features/health/api.ts
    → api/v1/health/router.py  (this file)
"""

from app.core.config import get_settings
from app.infrastructure.database.session import get_db
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    app: str
    llm: str
    postgres: bool


# ────────────────────────────────────────────────────────
# health
# Path: api/v1/health/router.py
# Endpoint: GET /health
# Use: report API status, LLM provider, and Postgres connectivity.
# ────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Public health check (no authentication required)."""
    settings = get_settings()
    postgres_ok = False
    try:
        # Step 1 — simple query proves Postgres is reachable.
        await db.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        postgres_ok = False

    # Step 2 — degraded when DB is down; llm shows demo/gemini/openai.
    return HealthResponse(
        status="ok" if postgres_ok else "degraded",
        app=settings.app_name,
        llm=settings.llm_provider,
        postgres=postgres_ok,
    )
