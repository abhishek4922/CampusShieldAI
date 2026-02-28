"""
CampusShield AI — Scans Router

Endpoints:
  POST /v1/scans/analyze-email  - Analyze email for phishing signals
  GET  /v1/scans/               - List user's scan history
  GET  /v1/scans/{scan_id}      - Get specific scan detail

The raw email body is NEVER stored. Only extracted features + results.
"""

import time
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import httpx

from app.database import get_db
from app.models import User, PhishingScan, AuditLog, Alert
from app.schemas.scan import EmailAnalysisRequest, EmailAnalysisResponse, ScanRecord
from app.dependencies import get_current_user, require_consent
from app.config import settings

router = APIRouter()


@router.post("/analyze-email", response_model=EmailAnalysisResponse)
async def analyze_email(
    payload: EmailAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_consent),  # Consent required
) -> EmailAnalysisResponse:
    """
    Phishing email analysis pipeline:
    1. Forward sanitised request to ML microservice
    2. ML service extracts features & returns risk JSON (never stores email)
    3. Backend persists features + result (not the email body)
    4. If High risk → auto-create alert
    5. Return full explainability result to caller
    """
    start_ms = time.perf_counter()

    # ── Forward to ML Microservice ─────────────────────────────
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            ml_response = await client.post(
                f"{settings.ML_SERVICE_URL}/analyze",
                json=payload.model_dump(),
                headers={"X-API-Key": settings.ML_SERVICE_API_KEY},
            )
            ml_response.raise_for_status()
            ml_result = ml_response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ML service timeout")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ML service error")

    # ── Persist extracted features + result (NO raw email) ─────
    scan = PhishingScan(
        campus_id          = current_user.campus_id,
        user_id            = current_user.id,
        sender_domain      = payload.sender_domain,
        sender_tld         = payload.sender_domain.rsplit(".", 1)[-1] if "." in payload.sender_domain else None,
        link_count         = len(payload.links),
        domain_mismatch    = ml_result["features"].get("domain_mismatch"),
        suspicious_tld     = ml_result["features"].get("suspicious_tld"),
        urgency_score      = ml_result["features"].get("urgency_score"),
        payment_keyword    = ml_result["features"].get("payment_keyword"),
        link_anomaly_score = ml_result["features"].get("link_anomaly_score"),
        risk_score         = ml_result["risk_score"],
        risk_level         = ml_result["risk_level"],
        confidence         = ml_result["confidence"],
        signals_triggered  = ml_result["signals_triggered"],
        plain_explanation  = ml_result["plain_explanation"],
        recommended_action = ml_result["recommended_action"],
    )
    db.add(scan)
    await db.flush()  # Get scan.id before commit

    # ── Auto-create alert for High-risk scans ──────────────────
    if ml_result["risk_level"] in ("High",):
        alert = Alert(
            campus_id = current_user.campus_id,
            scan_id   = scan.id,
            user_id   = current_user.id,
            severity  = "High" if ml_result["risk_score"] < 90 else "Critical",
            status    = "open",
        )
        db.add(alert)

    # ── Audit log ──────────────────────────────────────────────
    db.add(AuditLog(
        campus_id   = current_user.campus_id,
        user_id     = current_user.id,
        action      = "scan.analyze",
        resource    = "phishing_scan",
        resource_id = scan.id,
        metadata    = {"risk_level": ml_result["risk_level"], "risk_score": ml_result["risk_score"]},
    ))

    await db.commit()

    duration_ms = int((time.perf_counter() - start_ms) * 1000)

    return EmailAnalysisResponse(
        scan_id           = scan.id,
        risk_score        = ml_result["risk_score"],
        risk_level        = ml_result["risk_level"],
        signals_triggered = ml_result["signals_triggered"],
        plain_explanation = ml_result["plain_explanation"],
        recommended_action = ml_result["recommended_action"],
        confidence        = ml_result["confidence"],
        processing_ms     = duration_ms,
    )


@router.get("/", response_model=List[ScanRecord])
async def list_scans(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ScanRecord]:
    """List the current user's scan history (newest first)."""
    result = await db.execute(
        select(PhishingScan)
        .where(PhishingScan.user_id == current_user.id, PhishingScan.campus_id == current_user.campus_id)
        .order_by(desc(PhishingScan.scanned_at))
        .limit(min(limit, 200))
    )
    return result.scalars().all()


@router.get("/{scan_id}", response_model=ScanRecord)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanRecord:
    """Get a single scan by ID — must belong to user's campus."""
    result = await db.execute(
        select(PhishingScan).where(
            PhishingScan.id == scan_id,
            PhishingScan.campus_id == current_user.campus_id,  # Tenant enforced
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
