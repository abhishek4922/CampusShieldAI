"""
CampusShield AI — Tenant Isolation Middleware

Extracts campus_id from JWT token claims and injects it into the
request state. All downstream handlers use request.state.campus_id
to enforce row-level tenant isolation.

SECURITY: campus_id comes exclusively from the validated JWT — never
from request headers or query params, preventing tenant spoofing.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from jose import JWTError

from app.core.security import decode_token


# Paths that don't require tenant context (public routes)
_PUBLIC_PATHS = {
    "/health", "/metrics", "/docs", "/redoc",
    "/openapi.json", "/v1/auth/login", "/v1/auth/oauth",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that reads the JWT and populates request.state with:
      - campus_id: str | None
      - user_id:   str | None
      - user_role: str | None
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Initialise state defaults (public routes or missing token)
        request.state.campus_id = None
        request.state.user_id   = None
        request.state.user_role = None

        # Skip tenant extraction for public paths
        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/v1/auth/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    request.state.campus_id = payload.get("campus_id")
                    request.state.user_id   = payload.get("sub")
                    request.state.user_role = payload.get("role")
            except JWTError:
                pass  # Let the route handler return 401 via dependency

        return await call_next(request)
