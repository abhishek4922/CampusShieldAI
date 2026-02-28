"""
CampusShield AI — Standardised HTTP Exception Handlers

Registers handlers for:
  - Validation errors (422) — sanitised, no internal stack traces
  - Generic HTTP exceptions
  - Unhandled exceptions (500) — logged, safe message returned

SECURITY: Stack traces are never returned in error responses.
All errors are logged with structlog for ELK ingestion.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

logger = structlog.get_logger("campusshield.errors")


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        logger.warning("validation_error", path=request.url.path, errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Invalid request data", "errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        logger.info("http_error", path=request.url.path, status_code=exc.status_code)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        # Log full exception for dev debugging but never expose to clients
        logger.exception("unhandled_error", path=request.url.path, exc=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again."},
        )
