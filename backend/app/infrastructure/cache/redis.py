"""
Redis client.

Optional sidecar for rate limits and short-lived session state.
"""

from redis.asyncio import Redis

from app.core.config import get_settings

_redis: Redis | None = None


# ────────────────────────────────────────────────────────
# init_redis
# Internal — Redis
# Connects to Redis and verifies connectivity on application boot.
# ────────────────────────────────────────────────────────
async def init_redis() -> Redis:
    """
    Connect to Redis and verify connectivity on boot.

    Chat still works if Redis is down (fail soft).
    """
    global _redis
    settings = get_settings()
    # Create the async client with decoded string responses.
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    # Ping to confirm the connection is reachable before serving traffic.
    await _redis.ping()
    return _redis


# ────────────────────────────────────────────────────────
# close_redis
# Internal — Redis
# Closes the shared Redis connection on application shutdown.
# ────────────────────────────────────────────────────────
async def close_redis() -> None:
    """Close the shared Redis connection on shutdown."""
    global _redis
    if _redis is None:
        return
    try:
        await _redis.aclose()
    except Exception:
        # Ignore errors during shutdown cleanup.
        pass
    _redis = None


# ────────────────────────────────────────────────────────
# get_redis
# Internal — Redis
# Returns the shared Redis client, or None if not initialized.
# ────────────────────────────────────────────────────────
def get_redis() -> Redis | None:
    """Return the shared Redis client, or None if not initialized."""
    # May be None if init_redis was never called (e.g. Redis down on boot).
    return _redis
