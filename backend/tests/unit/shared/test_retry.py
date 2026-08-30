"""Unit tests for async retry helpers."""

from unittest.mock import AsyncMock, patch

import pytest

from app.shared.retry import backoff_delay, is_retryable_error, retry_async


def test_is_retryable_error_detects_transient_failures():
    assert is_retryable_error(Exception("HTTP 503 Service Unavailable"))
    assert is_retryable_error(Exception("rate limit exceeded"))
    assert is_retryable_error(TimeoutError("connection timed out"))


def test_is_retryable_error_rejects_permanent_failures():
    assert not is_retryable_error(Exception("permission_denied for project"))
    assert not is_retryable_error(Exception("model not_found"))
    assert not is_retryable_error(Exception("401 unauthorized"))


def test_backoff_delay_grows_with_attempt():
    first = backoff_delay(0, base=0.5, max_delay=8.0)
    second = backoff_delay(1, base=0.5, max_delay=8.0)
    assert 0.35 <= first <= 0.5
    assert second > first


@pytest.mark.asyncio
async def test_retry_async_succeeds_after_transient_failure():
    operation = AsyncMock(side_effect=[Exception("HTTP 503"), "ok"])

    with patch("app.shared.retry.asyncio.sleep", new_callable=AsyncMock):
        result = await retry_async(
            operation,
            max_attempts=3,
            base_delay=0.01,
            max_delay=0.05,
            label="test op",
        )

    assert result == "ok"
    assert operation.await_count == 2


@pytest.mark.asyncio
async def test_retry_async_does_not_retry_permanent_failure():
    operation = AsyncMock(side_effect=Exception("permission_denied"))

    with pytest.raises(Exception, match="permission_denied"):
        await retry_async(
            operation,
            max_attempts=3,
            base_delay=0.01,
            max_delay=0.05,
        )

    assert operation.await_count == 1
