"""Process logging and per-user rate limiting."""

import logging

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.errors import RateLimitError


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.app_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


async def enforce_rate_limit(redis: Redis | None, user_id: str) -> None:
    # ---------------------------------------------------------------------------
    # Redis INCR window — if Redis is down, skip limit (availability over strict).
    # ---------------------------------------------------------------------------
    if redis is None:
        return

    try:
        settings = get_settings()
        key = f"rate:{user_id}"
        current = await redis.incr(key)
        if current == 1:
            # First hit in the window must set TTL or the counter never resets.
            await redis.expire(key, 60)
        if current > settings.rate_limit_per_minute:
            raise RateLimitError()
    except RateLimitError:
        raise
    except Exception:
        logging.getLogger(__name__).warning("Rate limit check skipped; Redis error.")
