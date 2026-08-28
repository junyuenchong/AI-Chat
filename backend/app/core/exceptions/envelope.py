"""
Error envelope.

Stable JSON error shape shared by all exception handlers.
"""

from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError


# ────────────────────────────────────────────────────────
# error_body
# Internal — build stable JSON error envelope.
# Returns code, message, and optional per-field errors for all handlers.
# ────────────────────────────────────────────────────────
def error_body(
    *,
    code: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    # Never return blank code/message — clients always get a usable envelope.
    safe_message = (message or "An error occurred.").strip() or "An error occurred."
    safe_code = (code or "APP_ERROR").strip() or "APP_ERROR"
    return {
        "error": {
            "code": safe_code,
            "message": safe_message,
            "fields": fields or [],
        }
    }


# ────────────────────────────────────────────────────────
# field_errors_from_validation
# Internal — convert Pydantic validation errors to field list.
# Maps loc/msg pairs into client-friendly per-field error objects.
# ────────────────────────────────────────────────────────
def field_errors_from_validation(
    exc: RequestValidationError | PydanticValidationError,
) -> list[dict[str, str]]:
    """Turn Pydantic loc/msg into per-field errors (missing, type, extra)."""
    validation_messages = {
        "missing": "This field is required.",
        "extra_forbidden": "Unknown field is not allowed.",
    }
    fields: list[dict[str, str]] = []
    for err in exc.errors():
        # Strip body/query/path prefix — clients see "email", not "body.email".
        loc = [
            str(part)
            for part in err.get("loc", [])
            if part not in {"body", "query", "path", "header"}
        ]
        field = ".".join(loc) if loc else "body"
        error_type = str(err.get("type", "value_error"))
        # Prefer friendly copy for common validation types; fall back to Pydantic msg.
        msg = validation_messages.get(error_type, str(err.get("msg", "Invalid value")))
        fields.append({"field": field, "message": msg, "type": error_type})
    return fields


HTTP_STATUS_ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    429: "RATE_LIMITED",
}


# ────────────────────────────────────────────────────────
# http_error_message
# Internal — extract client-safe message from HTTPException detail.
# Handles string, dict, and fallback shapes from Starlette errors.
# ────────────────────────────────────────────────────────
def http_error_message(detail: object) -> str:
    """Extract a client-safe message from Starlette HTTPException.detail."""
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, dict):
        # Some routes pass {"message": "..."} instead of a plain string.
        return str(detail.get("message") or detail.get("msg") or "Request failed.")
    return "Request failed."  # Fallback when detail shape is unknown.
