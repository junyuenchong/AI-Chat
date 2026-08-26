"""Application entrypoint: FastAPI app factory + lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.clients.queue import close_queue, init_queue
from app.clients.redis import close_redis, init_redis
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------------------------------------------------------------------
    # Boot: logging → Postgres → optional Redis/ARQ (fail soft if sidecar down).
    # ---------------------------------------------------------------------------
    setup_logging()
    settings = get_settings()
    app.state.llm_enabled = settings.llm_enabled
    await init_db()
    try:
        await init_redis()
    except Exception:
        pass
    try:
        await init_queue()
    except Exception:
        pass
    yield
    await close_queue()
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
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
    register_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Versioned HTTP surface — clients keep /api/v1 while v2 can evolve.
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
