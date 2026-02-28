"""
CampusShield AI — Alerts Router

Endpoints:
  GET    /v1/alerts/            - List campus alerts (admin/security)
  GET    /v1/alerts/{alert_id}  - Get alert detail with scan context
  PATCH  /v1/alerts/{alert_id}  - Acknowledge or resolve an alert
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, Alert, AuditLog
from app.schemas.scan import AlertResponse, AlertUpdateRequest
from app.dependencies import require_role

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    status: str = "open",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "security")),
) -> List[AlertResponse]:
    """List alerts for the current campus, filtered by status."""
    result = await db.execute(
        select(Alert)
        .where(Alert.campus_id == current_user.campus_id, Alert.status == status)
        .order_by(desc(Alert.created_at))
        .limit(min(limit, 500))
    )
    return result.scalars().all()


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "security")),
) -> AlertResponse:
    """Get a single alert — tenant-scoped."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.campus_id == current_user.campus_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "security")),
) -> AlertResponse:
    """Acknowledge or resolve an alert. Only security/admin can do this."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.campus_id == current_user.campus_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    alert.notes  = payload.notes
    if payload.status == "resolved":
        alert.resolved_by = current_user.id
        alert.resolved_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        campus_id=current_user.campus_id, user_id=current_user.id,
        action=f"alert.{payload.status}", resource="alert", resource_id=alert.id,
        metadata={"notes": payload.notes},
    ))
    await db.commit()
    await db.refresh(alert)
    return alert
