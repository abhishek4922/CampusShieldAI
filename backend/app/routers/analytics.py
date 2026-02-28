"""
CampusShield AI — Analytics Router

Endpoints:
  GET /v1/analytics/dashboard   - Campus-level threat dashboard (admin/security only)
  GET /v1/analytics/heatmap     - Risk heatmap data
  GET /v1/analytics/trend       - Weekly trend data

All analytics are derived from DP-noised snapshots — no individual
scan data is returned to admin users.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from app.database import get_db
from app.models import User, PhishingScan, AnalyticsSnapshot
from app.dependencies import require_role
from app.core.privacy import privatise_analytics

router = APIRouter()


class DashboardResponse(BaseModel):
    campus_id:           str
    period_start:        datetime
    period_end:          datetime
    total_scans:         int
    high_risk_count:     int
    medium_risk_count:   int
    low_risk_count:      int
    vulnerability_score: Optional[float]
    top_signals:         dict
    epsilon_budget_used: float


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    days: int = Query(default=7, ge=1, le=90, description="Lookback period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "security")),
) -> DashboardResponse:
    """
    Returns campus-level threat dashboard for the specified period.
    Data is sourced from DP-noised analytics snapshots — not raw scans.
    If no snapshot exists for the period, one is computed and cached.
    """
    campus_id = current_user.campus_id
    now       = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    # Check for cached snapshot
    snap = await db.execute(
        select(AnalyticsSnapshot)
        .where(
            AnalyticsSnapshot.campus_id   == campus_id,
            AnalyticsSnapshot.period_start >= period_start,
        )
        .order_by(desc(AnalyticsSnapshot.created_at))
        .limit(1)
    )
    snapshot = snap.scalar_one_or_none()

    if not snapshot:
        # Compute aggregate from raw scans, then apply DP noise before persisting
        counts = await db.execute(
            select(
                PhishingScan.risk_level,
                func.count(PhishingScan.id).label("count"),
            )
            .where(
                PhishingScan.campus_id  == campus_id,
                PhishingScan.scanned_at >= period_start,
            )
            .group_by(PhishingScan.risk_level)
        )
        raw_counts = {row.risk_level: row.count for row in counts}

        raw = {
            "total_scans":       sum(raw_counts.values()),
            "high_risk_count":   raw_counts.get("High", 0),
            "medium_risk_count": raw_counts.get("Medium", 0),
            "low_risk_count":    raw_counts.get("Low", 0),
        }

        # Apply Laplace differential privacy noise
        dp = privatise_analytics(raw)
        noised = dp["noised_counts"]

        total = max(noised["total_scans"], 1)
        vuln_score = round((noised["high_risk_count"] / total) * 100, 1)

        snapshot = AnalyticsSnapshot(
            campus_id           = campus_id,
            period_start        = period_start,
            period_end          = now,
            total_scans         = noised["total_scans"],
            high_risk_count     = noised["high_risk_count"],
            medium_risk_count   = noised["medium_risk_count"],
            low_risk_count      = noised["low_risk_count"],
            top_signal_categories = {},
            vulnerability_score = vuln_score,
            epsilon_budget_used = dp["epsilon_consumed"],
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

    return DashboardResponse(
        campus_id           = str(snapshot.campus_id),
        period_start        = snapshot.period_start,
        period_end          = snapshot.period_end,
        total_scans         = snapshot.total_scans,
        high_risk_count     = snapshot.high_risk_count,
        medium_risk_count   = snapshot.medium_risk_count,
        low_risk_count      = snapshot.low_risk_count,
        vulnerability_score = snapshot.vulnerability_score,
        top_signals         = snapshot.top_signal_categories,
        epsilon_budget_used = snapshot.epsilon_budget_used,
    )
