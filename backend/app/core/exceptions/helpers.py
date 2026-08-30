"""
Exception helpers.

Application-layer helpers that raise domain exceptions.
"""

from app.core.exceptions.base import AppException
from app.core.exceptions.domain import NotFoundError
from sqlalchemy.exc import SQLAlchemyError


# ────────────────────────────────────────────────────────
# database_error
# Internal — map SQLAlchemy failures to AppException.
# Returns a stable 503 envelope for database unavailability.
# ────────────────────────────────────────────────────────
def database_error(message: str, exc: SQLAlchemyError) -> AppException:
    """Map SQLAlchemy failures to a stable 503 envelope."""
    # Wrap the DB error in a typed exception the global handler understands.
    return AppException(message, code="DATABASE_ERROR", status_code=503)


# ────────────────────────────────────────────────────────
# require_found
# Internal — guard clause for optional repository lookups.
# Raises a domain exception when a scoped lookup returns None.
# ────────────────────────────────────────────────────────
def require_found[T](
    resource: T | None,
    *,
    exc: type[AppException] = NotFoundError,
    message: str | None = None,
) -> T:
    """Guard clause — raise a domain exception when a scoped lookup returns None."""
    if resource is None:
        # Use the caller's custom message when provided, otherwise the default.
        raise exc(message) if message is not None else exc()
    return resource
