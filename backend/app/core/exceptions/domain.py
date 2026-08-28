"""
Domain exceptions.

Raise these from application/domain layers, not HTTPException.
"""

from app.core.exceptions.base import AppException


# ────────────────────────────────────────────────────────
# UnauthorizedError
# Internal — domain exception for missing or invalid credentials.
# Raised when authentication fails; maps to HTTP 401.
# ────────────────────────────────────────────────────────
class UnauthorizedError(AppException):
    """Missing or invalid credentials (HTTP 401)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to "Not authenticated" when no message is given.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "Not authenticated") -> None:
        # Stable client code + HTTP 401 for auth failures.
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


# ────────────────────────────────────────────────────────
# NotFoundError
# Internal — generic resource-not-found domain exception.
# Raised when a scoped lookup returns nothing; maps to HTTP 404.
# ────────────────────────────────────────────────────────
class NotFoundError(AppException):
    """Generic resource not found (HTTP 404)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to "Resource not found" when no message is given.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404)


# ────────────────────────────────────────────────────────
# ConversationNotFound
# Internal — conversation missing or not owned by user.
# Raised from chat/conversation services; maps to HTTP 404.
# ────────────────────────────────────────────────────────
class ConversationNotFound(AppException):
    """Conversation does not exist or is not owned by the current user (HTTP 404)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to "Conversation not found" when no message is given.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "Conversation not found") -> None:
        super().__init__(message, code="CONVERSATION_NOT_FOUND", status_code=404)


# ────────────────────────────────────────────────────────
# DocumentNotFound
# Internal — document missing or not owned by user.
# Raised from knowledge services; maps to HTTP 404.
# ────────────────────────────────────────────────────────
class DocumentNotFound(AppException):
    """Document does not exist or is not owned by the current user (HTTP 404)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to "Document not found" when no message is given.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "Document not found") -> None:
        super().__init__(message, code="DOCUMENT_NOT_FOUND", status_code=404)


# ────────────────────────────────────────────────────────
# ConflictError
# Internal — create/update conflict domain exception.
# Raised for duplicate email and similar constraints; maps to HTTP 409.
# ────────────────────────────────────────────────────────
class ConflictError(AppException):
    """Create conflict such as duplicate email (HTTP 409)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to "Resource already exists" when no message is given.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="CONFLICT", status_code=409)


# ────────────────────────────────────────────────────────
# RateLimitError
# Internal — too-many-requests domain exception.
# Raised when per-user or per-IP limits are exceeded; maps to HTTP 429.
# ────────────────────────────────────────────────────────
class RateLimitError(AppException):
    """Too many requests in the current window (HTTP 429)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to a retry-friendly rate-limit message.
    # ────────────────────────────────────────────────────────
    def __init__(
        self, message: str = "Rate limit exceeded. Try again in a minute."
    ) -> None:
        super().__init__(message, code="RATE_LIMITED", status_code=429)


# ────────────────────────────────────────────────────────
# LLMError
# Internal — upstream language-model failure domain exception.
# Raised when the LLM provider fails; maps to HTTP 502.
# ────────────────────────────────────────────────────────
class LLMError(AppException):
    """Upstream language model failure (HTTP 502)."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — construct with an optional custom message.
    # Defaults to a user-friendly LLM failure message.
    # ────────────────────────────────────────────────────────
    def __init__(self, message: str = "The language model failed. Try again.") -> None:
        super().__init__(message, code="LLM_ERROR", status_code=502)
