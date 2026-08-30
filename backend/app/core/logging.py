"""
Logging and rate limiting.

Process-wide logging setup and per-user request throttling.
"""

import logging

from app.core.config import get_settings
from app.core.exceptions import RateLimitError
from redis.asyncio import Redis


# ────────────────────────────────────────────────────────
# setup_logging
# Internal — process-wide logging configuration.
# Sets DEBUG in development and INFO in all other environments.
# ────────────────────────────────────────────────────────
def setup_logging() -> None:
    """Configure process-wide logging based on app_env."""
    settings = get_settings()
    # Verbose DEBUG in development; quieter INFO everywhere else.
    level = logging.DEBUG if settings.app_env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


# ────────────────────────────────────────────────────────
# enforce_rate_limit
# Internal — per-user Redis rate limit check.
# Skips enforcement when Redis is unavailable (availability over strict limits).
# ────────────────────────────────────────────────────────
async def enforce_rate_limit(redis: Redis | None, user_id: str) -> None:
    """
    Enforce per-user rate limit via Redis INCR window.

    If Redis is down, skip limit (availability over strict enforcement).
    """
    if redis is None:
        return  # No Redis — skip per-user limits rather than blocking chat.

    try:
        settings = get_settings()
        key = f"rate:{user_id}"
        current = await redis.incr(key)
        if current == 1:
            # First hit in the window must set TTL or the counter never resets.
            await redis.expire(key, 60)
        if current > settings.rate_limit_per_minute:
            raise RateLimitError()  # Caller maps this to HTTP 429.
    except RateLimitError:
        raise  # Propagate explicit rate-limit errors to the route handler.
    except Exception:
        logging.getLogger(__name__).warning("Rate limit check skipped; Redis error.")
