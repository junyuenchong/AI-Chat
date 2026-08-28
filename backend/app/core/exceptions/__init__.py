"""
Exception package.

Centralized exception types, envelope helpers, and FastAPI registration.
"""

from app.core.exceptions.base import AppError, AppException
from app.core.exceptions.domain import (
    ConflictError,
    ConversationNotFound,
    DocumentNotFound,
    LLMError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
)
from app.core.exceptions.envelope import (
    HTTP_STATUS_ERROR_CODES,
    error_body,
    field_errors_from_validation,
    http_error_message,
)
from app.core.exceptions.helpers import database_error, require_found
from app.core.exceptions.register import register_exception_handlers

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
    "register_exception_handlers",
    "require_found",
]
