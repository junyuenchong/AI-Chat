"""
Base exception.

Framework-agnostic application error mapped to HTTP by handlers.
"""


# ────────────────────────────────────────────────────────
# AppException
# Internal — base application error with code and HTTP status.
# Framework-agnostic error mapped to stable JSON by FastAPI handlers.
# ────────────────────────────────────────────────────────
class AppException(Exception):
    """Domain / application error with a stable client-facing code and HTTP status."""

    # ────────────────────────────────────────────────────────
    # __init__
    # Internal — set message, client code, status, and field errors.
    # All domain exceptions inherit these envelope fields.
    # ────────────────────────────────────────────────────────
    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
        fields: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        # These fields are read by exception handlers to build the JSON envelope.
        self.message = message
        self.code = code
        self.status_code = status_code
        self.fields = fields or []


# Backward-compatible alias used across services and tests.
AppError = AppException
