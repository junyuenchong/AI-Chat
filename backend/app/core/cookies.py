"""
Session cookie helpers.

HttpOnly cookie read/write for browser-based authentication.
"""

from app.core.config import Settings
from fastapi import Request, Response


# ────────────────────────────────────────────────────────
# session_cookie_name
# Internal — resolve configured session cookie name.
# Returns the cookie key used for browser session authentication.
# ────────────────────────────────────────────────────────
def session_cookie_name(settings: Settings) -> str:
    """Return the configured session cookie name."""
    return settings.session_cookie_name


# ────────────────────────────────────────────────────────
# read_session_id
# Internal — read session id from request cookie.
# Returns a trimmed session id or None when the cookie is absent.
# ────────────────────────────────────────────────────────
def read_session_id(request: Request, settings: Settings) -> str | None:
    """Read and normalize the session id from the request cookie."""
    value = request.cookies.get(session_cookie_name(settings))
    # Strip whitespace so empty-looking cookies are treated as absent.
    return value.strip() if value else None


# ────────────────────────────────────────────────────────
# set_session_cookie
# Internal — write HttpOnly session cookie on response.
# Sets secure, SameSite, and max-age from application settings.
# ────────────────────────────────────────────────────────
def set_session_cookie(response: Response, settings: Settings, session_id: str) -> None:
    """Set an HttpOnly session cookie on the response."""
    response.set_cookie(
        key=session_cookie_name(settings),
        value=session_id,
        httponly=True,  # JavaScript cannot read the session id (XSS mitigation).
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes
        * 60,  # Align cookie lifetime with JWT expiry.
        secure=settings.cookie_secure,  # HTTPS-only in production.
        path="/",
    )


# ────────────────────────────────────────────────────────
# clear_session_cookie
# Internal — remove session cookie on logout.
# Deletes the HttpOnly session cookie with matching path and flags.
# ────────────────────────────────────────────────────────
def clear_session_cookie(response: Response, settings: Settings) -> None:
    """Clear the session cookie on logout."""
    # Flags must match set_session_cookie so the browser actually deletes it.
    response.delete_cookie(
        key=session_cookie_name(settings),
        path="/",
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
