"""
Redis cache client and session store.

Single shared connection for rate limits, sessions, and other cache use.
Queue workers use a separate ARQ pool under messaging/.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import get_settings
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_redis: Redis | None = None
_SESSION_PREFIX = "session:"


# ────────────────────────────────────────────────────────
# init_redis
# Internal — cache
# Connects to Redis and verifies connectivity on application boot.
# ────────────────────────────────────────────────────────
async def init_redis() -> Redis:
    """
    Connect to Redis and verify connectivity on boot.

    Chat still works if Redis is down (fail soft).
    """
    global _redis
    settings = get_settings()
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()
    return _redis


# ────────────────────────────────────────────────────────
# close_redis
# Internal — cache
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
        pass
    _redis = None


# ────────────────────────────────────────────────────────
# get_redis
# Internal — cache
# Returns the shared Redis client, or None if not initialized.
# ────────────────────────────────────────────────────────
def get_redis() -> Redis | None:
    """Return the shared Redis client, or None if not initialized."""
    return _redis


def _session_key(session_id: str) -> str:
    return f"{_SESSION_PREFIX}{session_id}"


def _ttl_seconds() -> int:
    return get_settings().jwt_expire_minutes * 60


# ────────────────────────────────────────────────────────
# create_session
# Internal — session store
# Stores a new session in Redis and returns its session_id.
# ────────────────────────────────────────────────────────
async def create_session(user_id: str, redis: Redis | None = None) -> str | None:
    """Store session in Redis; return session_id or None if Redis is down."""
    client = redis or get_redis()
    if client is None:
        return None
    session_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        await client.setex(
            _session_key(session_id), _ttl_seconds(), json.dumps(payload)
        )
        return session_id
    except Exception:
        logger.warning("Could not create Redis session for user %s", user_id)
        return None


# ────────────────────────────────────────────────────────
# get_session_user_id
# Internal — session store
# Resolves a session_id to user_id and refreshes the session TTL.
# ────────────────────────────────────────────────────────
async def get_session_user_id(
    session_id: str, redis: Redis | None = None
) -> str | None:
    """Resolve session_id to user_id; refresh TTL on hit."""
    if not session_id:
        return None
    client = redis or get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(_session_key(session_id))
        if not raw:
            return None
        data = json.loads(raw)
        user_id = data.get("user_id")
        if not user_id:
            return None
        await client.expire(_session_key(session_id), _ttl_seconds())
        return str(user_id)
    except Exception:
        logger.warning("Session lookup failed")
        return None


# ────────────────────────────────────────────────────────
# delete_session
# Internal — session store
# Removes a session record from Redis on logout.
# ────────────────────────────────────────────────────────
async def delete_session(session_id: str, redis: Redis | None = None) -> None:
    client = redis or get_redis()
    if client is None or not session_id:
        return
    try:
        await client.delete(_session_key(session_id))
    except Exception:
        logger.warning("Could not delete session %s", session_id)
