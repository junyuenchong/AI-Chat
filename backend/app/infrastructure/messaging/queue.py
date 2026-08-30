"""
ARQ job queue.

Background pool for summaries and embeddings that must not block SSE chat.
"""

from app.core.config import get_settings
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

_pool: ArqRedis | None = None


# ────────────────────────────────────────────────────────
# redis_settings
# Internal — messaging
# Builds ARQ Redis settings from application configuration.
# ────────────────────────────────────────────────────────
def redis_settings() -> RedisSettings:
    """Build ARQ Redis settings from application config."""
    return RedisSettings.from_dsn(get_settings().redis_url)


# ────────────────────────────────────────────────────────
# init_queue
# Internal — messaging
# Creates the shared ARQ job pool on application boot.
# ────────────────────────────────────────────────────────
async def init_queue() -> ArqRedis:
    """
    Create the ARQ job pool on boot.

    Jobs no-op safely if the worker is stopped; chat still works.
    """
    global _pool
    _pool = await create_pool(redis_settings())
    return _pool


# ────────────────────────────────────────────────────────
# close_queue
# Internal — messaging
# Closes the shared ARQ pool on application shutdown.
# ────────────────────────────────────────────────────────
async def close_queue() -> None:
    """Close the shared ARQ pool on shutdown."""
    global _pool
    if _pool is None:
        return
    try:
        await _pool.aclose()
    except Exception:
        pass
    _pool = None


# ────────────────────────────────────────────────────────
# get_queue
# Internal — messaging
# Returns the shared ARQ pool, or None if not initialized.
# ────────────────────────────────────────────────────────
def get_queue() -> ArqRedis | None:
    """Return the shared ARQ pool, or None if not initialized."""
    return _pool
