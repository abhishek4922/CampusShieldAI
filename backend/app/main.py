"""
CampusShield AI — FastAPI Application Entry Point

This module bootstraps the FastAPI app, registers all routers,
attaches middleware (CORS, rate limiting, tenant extraction, logging),
mounts Prometheus metrics, and exposes the health endpoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.database import init_db, close_db
from app.middleware.logging import StructuredLoggingMiddleware
from app.middleware.tenant import TenantMiddleware
from app.routers import auth, scans, alerts, analytics, hygiene, campus, health
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: initialise DB connection pool on startup,
    gracefully close on shutdown.
    """
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="CampusShield AI API",
    description="Privacy-first, explainable AI campus security platform",
    version="1.0.0",
    docs_url="/docs" if settings.APP_DEBUG else None,   # Disable Swagger in prod
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

# ── Security: Trusted Hosts ──────────────────────────────────────────────────
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# ── CORS (restrict to frontend origin in production) ────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Campus-ID", "X-CSRF-Token"],
    expose_headers=["X-Request-ID"],
)

# ── Structured request logging ───────────────────────────────────────────────
app.add_middleware(StructuredLoggingMiddleware)

# ── Multi-tenant campus isolation ───────────────────────────────────────────
app.add_middleware(TenantMiddleware)

# ── Prometheus metrics (/metrics endpoint) ───────────────────────────────────
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["monitoring"])

# ── Exception handlers ───────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ──────────────────────────────────────────────────────────────────
API_V1 = "/v1"

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=f"{API_V1}/auth", tags=["auth"])
app.include_router(scans.router, prefix=f"{API_V1}/scans", tags=["scans"])
app.include_router(alerts.router, prefix=f"{API_V1}/alerts", tags=["alerts"])
app.include_router(analytics.router, prefix=f"{API_V1}/analytics", tags=["analytics"])
app.include_router(hygiene.router, prefix=f"{API_V1}/hygiene", tags=["hygiene"])
app.include_router(campus.router, prefix=f"{API_V1}/campus", tags=["campus"])
