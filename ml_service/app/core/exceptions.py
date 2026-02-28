"""
CampusShield AI — ML Service Exception Handlers
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

logger = structlog.get_logger("campusshield.ml.errors")


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Invalid request", "errors": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("ml_unhandled_error", path=request.url.path, exc=str(exc))
        return JSONResponse(status_code=500, content={"detail": "ML service error. Please try again."})
