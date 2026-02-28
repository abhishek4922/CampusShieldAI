"""
CampusShield AI — ML Microservice Entry Point

This service runs independently of the main backend, communicating
solely via internal REST. There is no direct DB access — it processes
email features and returns risk assessments.

AMD Optimization: uvicorn with multiple workers leverages all CPU cores.
AMD EPYC provides excellent many-core parallelism for concurrent inference.
"""

from fastapi import FastAPI, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings
from app.routers import analyze
from app.core.exceptions import register_exception_handlers

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

app = FastAPI(
    title="CampusShield AI — ML Service",
    description="Phishing detection, risk scoring, and explainability microservice",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

register_exception_handlers(app)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(analyze.router, tags=["analysis"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "campusshield-ml"}
