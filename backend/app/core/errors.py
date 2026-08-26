"""Application errors and the stable JSON error envelope for clients."""

from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError


class AppError(Exception):
    """Base domain error mapped to a stable JSON envelope and HTTP status."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
        fields: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.fields = fields or []


class UnauthorizedError(AppError):
    """Missing or invalid JWT / credentials (HTTP 401)."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class NotFoundError(AppError):
    """Requested resource does not exist for this user (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ConflictError(AppError):
    """Create conflict such as duplicate email (HTTP 409)."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="CONFLICT", status_code=409)


class RateLimitError(AppError):
    """Too many requests in the current window (HTTP 429)."""

    def __init__(self, message: str = "Rate limit exceeded. Try again in a minute.") -> None:
        super().__init__(message, code="RATE_LIMITED", status_code=429)


class LLMError(AppError):
    """Upstream language model failure (HTTP 502)."""

    def __init__(self, message: str = "The language model failed. Try again.") -> None:
        super().__init__(message, code="LLM_ERROR", status_code=502)


# ---------------------------------------------------------------------------
# Envelope — one shape for AppError, validation, and unexpected failures.
# Never put stack traces or SQL in the response body.
# ---------------------------------------------------------------------------
def error_body(
    *,
    code: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or [],
        }
    }


def field_errors_from_validation(
    exc: RequestValidationError | PydanticValidationError,
) -> list[dict[str, str]]:
    """Turn Pydantic loc/msg into per-field errors (missing, type, extra)."""
    fields: list[dict[str, str]] = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", []) if part not in {"body", "query", "path", "header"}]
        field = ".".join(loc) if loc else "body"
        error_type = str(err.get("type", "value_error"))
        msg = str(err.get("msg", "Invalid value"))
        if error_type == "missing":
            msg = "This field is required."
        elif error_type == "extra_forbidden":
            msg = "Unknown field is not allowed."
        fields.append({"field": field, "message": msg, "type": error_type})
    return fields
