"""
Errors (deprecated).

Backward-compatible re-exports — prefer app.core.exceptions.
"""

from app.core.exceptions import (
    HTTP_STATUS_ERROR_CODES,
    AppError,
    AppException,
    ConflictError,
    ConversationNotFound,
    DocumentNotFound,
    LLMError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    database_error,
    error_body,
    field_errors_from_validation,
    http_error_message,
    require_found,
)

__all__ = [
    "AppError",
    "AppException",
    "ConflictError",
    "ConversationNotFound",
    "DocumentNotFound",
    "HTTP_STATUS_ERROR_CODES",
    "LLMError",
    "NotFoundError",
    "RateLimitError",
    "UnauthorizedError",
    "database_error",
    "error_body",
    "field_errors_from_validation",
    "http_error_message",
    "require_found",
]
