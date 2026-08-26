"""ARQ job pool — summaries and embeddings must not block SSE chat."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings

_pool: ArqRedis | None = None


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


# ---------------------------------------------------------------------------
# Lifecycle — jobs no-op safely if the worker is stopped; chat still works.
# ---------------------------------------------------------------------------
async def init_queue() -> ArqRedis:
    global _pool
    _pool = await create_pool(redis_settings())
    return _pool


async def close_queue() -> None:
    global _pool
    if _pool is None:
        return
    try:
        await _pool.aclose()
    except Exception:
        pass
    _pool = None


def get_queue() -> ArqRedis | None:
    return _pool
