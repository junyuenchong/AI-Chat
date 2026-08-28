"""
Exception handlers.

FastAPI handlers that always return JSON, never HTML or traceback.
"""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions.base import AppException
from app.core.exceptions.envelope import (
    HTTP_STATUS_ERROR_CODES,
    error_body,
    field_errors_from_validation,
    http_error_message,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# app_exception_handler
# Internal — handle AppException and return stable JSON envelope.
# Maps domain error code, message, and field errors to the response body.
# ────────────────────────────────────────────────────────
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    # Map the domain exception directly to the stable JSON error envelope.
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code=exc.code, message=exc.message, fields=exc.fields),
    )


# ────────────────────────────────────────────────────────
# validation_error_handler
# Internal — handle Pydantic/FastAPI validation errors.
# Returns HTTP 422 with per-field error details in the envelope.
# ────────────────────────────────────────────────────────
async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Convert Pydantic loc/msg tuples into per-field client errors.
    fields = field_errors_from_validation(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_body(
            code="VALIDATION_ERROR",
            message="One or more fields are invalid.",
            fields=fields,
        ),
    )


# ────────────────────────────────────────────────────────
# http_error_handler
# Internal — handle Starlette HTTPException responses.
# Normalizes HTTP error details into the stable JSON envelope.
# ────────────────────────────────────────────────────────
async def http_error_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(
            # Map well-known HTTP codes to stable client error codes.
            code=HTTP_STATUS_ERROR_CODES.get(exc.status_code, "HTTP_ERROR"),
            message=http_error_message(exc.detail),
        ),
    )


# ────────────────────────────────────────────────────────
# integrity_error_handler
# Internal — handle database integrity constraint violations.
# Returns HTTP 409 when a record conflicts with a unique constraint.
# ────────────────────────────────────────────────────────
async def integrity_error_handler(
    _request: Request, exc: IntegrityError
) -> JSONResponse:
    logger.warning("Database integrity error: %s", exc)
    # Unique constraint or FK violation — tell the client the record conflicts.
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_body(
            code="CONFLICT",
            message="This record already exists or violates a constraint.",
        ),
    )


# ────────────────────────────────────────────────────────
# database_error_handler
# Internal — handle unexpected SQLAlchemy database errors.
# Returns HTTP 503 and logs the full exception for operators.
# ────────────────────────────────────────────────────────
async def database_error_handler(
    _request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.exception("Database error: %s", exc)
    # Generic DB failure — do not leak internal SQL details to the client.
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_body(
            code="DATABASE_ERROR", message="Database is unavailable. Try again."
        ),
    )


# ────────────────────────────────────────────────────────
# unhandled_error_handler
# Internal — catch-all handler for unexpected exceptions.
# Returns HTTP 500; includes exception class name in development only.
# ────────────────────────────────────────────────────────
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    settings = get_settings()
    message = "An unexpected error occurred."
    if settings.app_env == "development":
        # Surface the exception class name locally to speed up debugging.
        message = f"An unexpected error occurred: {exc.__class__.__name__}"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body(code="INTERNAL_ERROR", message=message),
    )
