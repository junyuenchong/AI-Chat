"""
Async retry helpers with exponential backoff.

Used for transient LLM API failures (429, 503, timeouts).
Permanent errors (auth, model not found) are not retried.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_NON_RETRYABLE = (
    "permission_denied",
    "denied access",
    "invalid_api_key",
    "api key not valid",
    "not_found",
    "no longer available",
    "model_not_found",
    "authentication",
    "unauthorized",
    "401",
    "403",
)

_RETRYABLE = (
    "429",
    "503",
    "502",
    "504",
    "timeout",
    "timed out",
    "rate limit",
    "rate_limit",
    "overloaded",
    "capacity",
    "connection reset",
    "connection error",
    "temporarily",
    "unavailable",
    "resource_exhausted",
    "deadline exceeded",
    "internal error",
    "server error",
)


def is_retryable_error(exc: Exception) -> bool:
    """Return True when the error is likely transient and worth retrying."""
    text = str(exc).lower()
    if any(marker in text for marker in _NON_RETRYABLE):
        return False
    if any(marker in text for marker in _RETRYABLE):
        return True
    name = exc.__class__.__name__.lower()
    return "timeout" in name or "connection" in name


def backoff_delay(attempt: int, *, base: float, max_delay: float) -> float:
    """Exponential backoff with jitter (attempt is 0-based)."""
    delay = min(max_delay, base * (2**attempt))
    return delay * (0.75 + random.random() * 0.25)


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    label: str = "operation",
) -> T:
    """Run an async operation with retries on transient failures."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as exc:
            last_exc = exc
            is_last = attempt >= max_attempts - 1
            if is_last or not is_retryable_error(exc):
                raise
            delay = backoff_delay(attempt, base=base_delay, max_delay=max_delay)
            logger.warning(
                "%s failed (attempt %s/%s), retrying in %.2fs: %s",
                label,
                attempt + 1,
                max_attempts,
                delay,
                exc,
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
