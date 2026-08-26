"""Postgres engine and sessions."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Base, load_models

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # ---------------------------------------------------------------------------
    # Request-scoped session — FastAPI closes it when the handler returns.
    # SSE streams must open SessionLocal() themselves instead.
    # ---------------------------------------------------------------------------
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    # ---------------------------------------------------------------------------
    # Boot: load ORM models, enable extensions, create tables if missing.
    # create_all does not migrate columns — use Alembic or down -v after changes.
    # ---------------------------------------------------------------------------
    load_models()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)
