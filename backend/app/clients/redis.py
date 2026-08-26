"""Redis client for rate limits and short-lived state (optional sidecar)."""

from redis.asyncio import Redis

from app.core.config import get_settings

_redis: Redis | None = None


# ---------------------------------------------------------------------------
# Lifecycle — ping on boot; chat still works if Redis is down (fail soft).
# ---------------------------------------------------------------------------
async def init_redis() -> Redis:
    global _redis
    settings = get_settings()
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is None:
        return
    try:
        await _redis.aclose()
    except Exception:
        pass
    _redis = None


def get_redis() -> Redis | None:
    return _redis
