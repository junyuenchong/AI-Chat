"""
HTTP cross-cutting middleware.

Belongs here (global, affects every route):
  - Request ID
  - Security headers
  - CORS
  - Per-IP rate limiting

Does NOT belong here:
  - Authentication / authorization business rules
  - Per-user rate limits tied to chat use-cases

Request flow:
  Middleware → Router → Depends(get_current_user) → Application Service
"""

from __future__ import annotations

import logging
import uuid

from app.core.config import Settings, get_settings
from app.core.exceptions import RateLimitError, error_body
from app.infrastructure.cache.redis import get_redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {"/api/v1/health", "/health", "/", "/docs", "/openapi.json", "/redoc"}


# ────────────────────────────────────────────────────────
# RequestIdMiddleware
# Internal — HTTP middleware
# Assigns X-Request-ID to every request for log correlation.
# ────────────────────────────────────────────────────────
class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request id to request.state and the response headers."""

    # ────────────────────────────────────────────────────────
    # dispatch
    # Internal — HTTP middleware
    # Reuses incoming X-Request-ID or generates a new UUID.
    # ────────────────────────────────────────────────────────
    async def dispatch(self, request: Request, call_next) -> Response:
        # Reuse client-provided id or generate a new one for log correlation.
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Store on request state so handlers and loggers can read it.
        request.state.request_id = request_id
        response = await call_next(request)
        # Echo the id back so clients can reference it in support requests.
        response.headers["X-Request-ID"] = request_id
        return response


# ────────────────────────────────────────────────────────
# SecurityHeadersMiddleware
# Internal — HTTP middleware
# Adds baseline security headers to every response.
# ────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set common security headers (nosniff, frame deny, referrer policy)."""

    # ────────────────────────────────────────────────────────
    # dispatch
    # Internal — HTTP middleware
    # Applies headers after the route handler runs.
    # ────────────────────────────────────────────────────────
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # Prevent MIME-type sniffing attacks on JSON/HTML responses.
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Block embedding this app in iframes on other origins.
        response.headers["X-Frame-Options"] = "DENY"
        # Limit referrer leakage on cross-origin navigation.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ────────────────────────────────────────────────────────
# RateLimitMiddleware
# Internal — HTTP middleware
# Global per-IP request throttling before handlers run.
# ────────────────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global per-IP window; chat service adds per-user limits on top."""

    # ────────────────────────────────────────────────────────
    # dispatch
    # Internal — HTTP middleware
    # Increments per-IP counter in Redis and returns 429 when over limit.
    # ────────────────────────────────────────────────────────
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        # Skip throttling for health checks, docs, and the root landing page.
        if (
            path in _EXEMPT_PATHS
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return await call_next(request)

        redis = get_redis()
        # When Redis is down, allow traffic rather than blocking every request.
        if redis is None:
            return await call_next(request)

        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:ip:{client_ip}"

        try:
            # Increment the per-IP counter for the current 60-second window.
            current = await redis.incr(key)
            if current == 1:
                # First hit in the window must set TTL or the counter never resets.
                await redis.expire(key, 60)
            if current > settings.rate_limit_ip_per_minute:
                # Over limit — return 429 without invoking the route handler.
                return JSONResponse(
                    status_code=429,
                    content=error_body(
                        code="RATE_LIMITED",
                        message=(
                            "Too many requests from this address. "
                            "Try again in a minute."
                        ),
                    ),
                )
        except RateLimitError:
            raise  # Propagate explicit rate-limit errors from nested checks.
        except Exception:
            logger.warning("IP rate limit skipped; Redis error.")

        return await call_next(request)


# ────────────────────────────────────────────────────────
# setup_middleware
# Internal — HTTP middleware
# Registers CORS and all global middleware on the FastAPI app.
# ────────────────────────────────────────────────────────
def setup_middleware(app: FastAPI, settings: Settings | None = None) -> None:
    """Register global HTTP middleware (order: last added runs first on request)."""
    cfg = settings or get_settings()

    # Last added runs first on the way in — rate limit before route handlers.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    # CORS is outermost so preflight OPTIONS requests are handled first.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
