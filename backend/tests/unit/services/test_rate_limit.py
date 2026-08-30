"""Unit tests for chat rate limiting.

Uses a fake Redis client — same path as POST /chat/stream and POST /chat/complete.
"""

import pytest
from app.core.exceptions import RateLimitError
from app.core.logging import enforce_rate_limit
from tests.helpers import FakeRedis

# ────────────────────────────────────────────────────────────
# test_rate_limit_skipped_when_redis_none
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: when Redis is unavailable, chat is not blocked by rate limiting.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_skipped_when_redis_none():
    await enforce_rate_limit(None, "user-1")


# ────────────────────────────────────────────────────────────
# test_rate_limit_raises_after_threshold
# Endpoint: POST /chat/stream, POST /chat/complete (internal)
# Use: exceeding the per-minute limit raises 429 RATE_LIMITED.
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_raises_after_threshold(monkeypatch):
    redis = FakeRedis()
    settings = type("S", (), {"rate_limit_per_minute": 2})()
    monkeypatch.setattr("app.core.logging.get_settings", lambda: settings)

    await enforce_rate_limit(redis, "user-1")
    await enforce_rate_limit(redis, "user-1")

    with pytest.raises(RateLimitError):
        await enforce_rate_limit(redis, "user-1")
