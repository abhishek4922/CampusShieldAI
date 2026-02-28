"""
CampusShield AI — Structured Request Logging Middleware

Logs every request with: method, path, status_code, duration_ms,
request_id, and campus_id. Uses structlog for JSON output compatible
with ELK / Loki log aggregation.

PII PROTECTION: IP addresses are intentionally excluded from logs.
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger("campusshield.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Attach request-id to response for client correlation
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            campus_id=getattr(request.state, "campus_id", None),
        )
        return response
