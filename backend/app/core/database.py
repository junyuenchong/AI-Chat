"""
Database engine and sessions.

Postgres connectivity for request-scoped and standalone sessions.
"""

import sys
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.infrastructure.database.models import Base, load_models

settings = get_settings()

# NullPool under pytest — avoids asyncpg pool cancel warnings between tests.
_engine_kwargs: dict = {"pool_pre_ping": True}
if "pytest" in sys.modules:
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ────────────────────────────────────────────────────────
# get_db
# Internal — FastAPI dependency for request-scoped sessions.
# Yields a session per request; SSE streams must open SessionLocal directly.
# ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a request-scoped database session.

    SSE streams must open SessionLocal() themselves instead.
    """
    async with SessionLocal() as session:
        try:
            yield session  # Hand the open session to the route handler.
        except Exception:
            await session.rollback()  # Undo partial writes before re-raising.
            raise


# ────────────────────────────────────────────────────────
# init_db
# Internal — boot-time database setup.
# Creates extensions, tables, and performance indexes at application start.
# ────────────────────────────────────────────────────────
async def init_db() -> None:
    """
    Boot-time database setup: extensions, tables, and performance indexes.

    create_all does not migrate columns — use Alembic after schema changes.
    """
    load_models()  # Register all ORM models before create_all runs.
    async with engine.begin() as conn:
        # pgvector powers embedding similarity search in the knowledge base.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        # pg_trgm enables fuzzy text matching for hybrid retrieval.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        # Create any tables that do not yet exist (idempotent on restart).
        await conn.run_sync(Base.metadata.create_all)
        # Composite indexes for hot query paths — safe to re-run via IF NOT EXISTS.
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_messages_conversation_created "
                "ON messages (conversation_id, created_at)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_conversations_user_updated "
                "ON conversations (user_id, updated_at DESC)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_document_chunks_doc_index "
                "ON document_chunks (document_id, chunk_index)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_documents_user_created "
                "ON documents (user_id, created_at DESC)"
            )
        )
