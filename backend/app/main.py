"""
Application entrypoint.

FastAPI app factory and lifespan management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions.register import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.infrastructure.cache.redis import close_redis, init_redis
from app.infrastructure.database.session import init_db
from app.infrastructure.messaging.queue import close_queue, init_queue


# ────────────────────────────────────────────────────────
# lifespan
# Internal — application entrypoint
# Boots shared resources on startup and tears them down on shutdown.
# ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Boot and shutdown shared resources."""
    # Configure logging before any other startup work runs.
    setup_logging()
    # Load settings once and expose LLM availability on app state for handlers.
    settings = get_settings()
    app.state.llm_enabled = settings.llm_enabled
    # Ensure extensions, tables, and indexes exist before serving traffic.
    await init_db()

    # Redis and ARQ are optional — chat degrades gracefully when sidecars are down.
    try:
        await init_redis()
    except Exception:
        pass  # Continue without Redis when the sidecar is unavailable.
    try:
        await init_queue()
    except Exception:
        pass  # Continue without the job queue when ARQ is unavailable.

    yield  # Hand control to the running application until shutdown.

    # Tear down optional resources in reverse startup order.
    await close_queue()
    await close_redis()


# ────────────────────────────────────────────────────────
# create_app
# Internal — application entrypoint
# Builds and configures the FastAPI application (middleware, routes, handlers).
# ────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    # Create the FastAPI instance with metadata and startup/shutdown hooks.
    application = FastAPI(
        title=settings.app_name,
        description=(
            "AI chat backend. "
            "LangChain = AI components. "
            "RAG = retriever + knowledge + LLM."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    # Wire global handlers so every error returns the same JSON envelope.
    register_exception_handlers(application)
    # Add CORS, request IDs, security headers, and IP rate limiting.
    setup_middleware(application, settings)
    # Versioned surface lets v2 evolve without breaking existing clients.
    application.include_router(api_router, prefix="/api/v1")

    # ────────────────────────────────────────────────────────
    # root
    # Internal — application entrypoint
    # Returns basic service links for the browser root URL (not in OpenAPI).
    # ────────────────────────────────────────────────────────
    @application.get("/", include_in_schema=False)
    async def root() -> dict:
        # Return quick links for humans hitting the root URL in a browser.
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "api": "/api/v1",
            "frontend": "http://localhost:3000",
        }

    return application


app = create_app()
