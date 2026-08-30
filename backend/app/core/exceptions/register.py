"""
Exception registration.

Wire global exception handlers onto the FastAPI application.
"""

from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import (
    app_exception_handler,
    database_error_handler,
    http_error_handler,
    integrity_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ────────────────────────────────────────────────────────
# register_exception_handlers
# Internal — wire global exception handlers onto FastAPI app.
# Ensures domain and infrastructure errors always return stable JSON.
# ────────────────────────────────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers so domain exceptions become stable JSON responses."""
    # Application-layer errors with explicit codes and HTTP status.
    app.add_exception_handler(AppException, app_exception_handler)
    # Pydantic request body/query validation failures.
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    # Starlette/FastAPI HTTPException (404, 403, etc.).
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    # Unique constraint and foreign-key violations.
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    # Connection failures and other unexpected SQLAlchemy errors.
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    # Catch-all for anything not handled above.
    app.add_exception_handler(Exception, unhandled_error_handler)
