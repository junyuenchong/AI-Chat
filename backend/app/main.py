"""
Application entrypoint.

FastAPI app factory and lifespan management.

Request path:
  uvicorn app.main:app
    → create_app()
    → api/v1/router.py
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions.register import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.infrastructure.database.session import init_db


# ────────────────────────────────────────────────────────
# lifespan
# Path: main.py
# Use: boot-time setup — logging, DB tables, shared app state.
# ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Boot and shutdown shared resources."""
    # Step 1 — configure logging and read settings.
    setup_logging()
    settings = get_settings()
    app.state.llm_enabled = settings.llm_enabled
    # Step 2 — ensure Postgres tables and indexes exist.
    await init_db()
    yield


# ────────────────────────────────────────────────────────
# create_app
# Path: main.py
# Use: build the FastAPI app with middleware, errors, and /api/v1 routes.
# ────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Q2 streaming LLM chat — FastAPI + Postgres + LangChain.",
        version="1.0.0",
        lifespan=lifespan,
    )
    register_exception_handlers(application)
    setup_middleware(application, settings)
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "api": "/api/v1",
            "frontend": "http://localhost:3000",
        }

    return application


app = create_app()
