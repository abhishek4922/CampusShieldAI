"""
CampusShield AI — Health & Readiness Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from app.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe — for Docker/k8s health checks."""
    return {"status": "ok", "service": "campusshield-backend"}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe — checks DB and Redis connectivity."""
    checks = {}

    # DB check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"ready": all_ok, "checks": checks}
