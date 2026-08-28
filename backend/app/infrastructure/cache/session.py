"""
Redis session store.

Server-side sessions — cookie holds session_id, Redis holds user_id.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

from redis.asyncio import Redis

from app.core.config import get_settings
from app.infrastructure.cache.redis import get_redis

logger = logging.getLogger(__name__)

_SESSION_PREFIX = "session:"


# ────────────────────────────────────────────────────────
# _session_key
# Internal — session store
# Builds the Redis key for a server-side session record.
# ────────────────────────────────────────────────────────
def _session_key(session_id: str) -> str:
    # Prefix keeps session keys namespaced in Redis.
    return f"{_SESSION_PREFIX}{session_id}"


# ────────────────────────────────────────────────────────
# _ttl_seconds
# Internal — session store
# Derives session TTL from JWT expiry settings.
# ────────────────────────────────────────────────────────
def _ttl_seconds() -> int:
    # Align session lifetime with configured JWT expiry.
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
    # Generate an opaque session id for the browser cookie.
    session_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        # Store JSON payload with TTL matching JWT expiry.
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
        # Sliding expiration — extend TTL on each authenticated request.
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
        # Remove the session key so the cookie can no longer authenticate.
        await client.delete(_session_key(session_id))
    except Exception:
        logger.warning("Could not delete session %s", session_id)
