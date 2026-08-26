"""FastAPI exception handlers — always return JSON, never HTML / traceback."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.errors import AppError, error_body, field_errors_from_validation

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    # ---------------------------------------------------------------------------
    # Domain / validation / HTTP / DB — map to the shared error envelope.
    # ---------------------------------------------------------------------------

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code=exc.code, message=exc.message, fields=exc.fields),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = field_errors_from_validation(exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_body(
                code="VALIDATION_ERROR",
                message="One or more fields are invalid.",
                fields=fields,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            429: "RATE_LIMITED",
        }
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=code_map.get(exc.status_code, "HTTP_ERROR"),
                message=message,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database integrity error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_body(code="CONFLICT", message="This record already exists or violates a constraint."),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_body(code="DATABASE_ERROR", message="Database is unavailable. Try again."),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        # Catch-all so the client always gets JSON, never a stack page.
        logger.exception("Unhandled error: %s", exc)
        settings = get_settings()
        message = "An unexpected error occurred."
        if settings.app_env == "development":
            message = f"An unexpected error occurred: {exc.__class__.__name__}"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body(code="INTERNAL_ERROR", message=message),
        )
