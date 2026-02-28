"""
CampusShield AI — Campus Management Router (Admin)

Endpoints:
  GET   /v1/campus/settings       - Get campus security policy config
  PATCH /v1/campus/settings       - Update campus security policies
  GET   /v1/campus/users          - List campus users (paginated)
  POST  /v1/campus/users          - Invite/create a new user
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User, Campus
from app.dependencies import require_role
from app.core.security import hash_email, hash_password

router = APIRouter()


class CampusSettingsUpdate(BaseModel):
    min_risk_alert_threshold: int = 65       # Risk score to auto-create alert
    phishing_policy_version:  str = "1.0"
    enforce_mfa:              bool = False
    allow_anonymous_scans:    bool = False


class InviteUserRequest(BaseModel):
    email:   EmailStr
    role:    str = "student"


@router.get("/settings")
async def get_campus_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Return the current campus security policy configuration."""
    result = await db.execute(select(Campus).where(Campus.id == current_user.campus_id))
    campus = result.scalar_one_or_none()
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    return {"campus_id": str(campus.id), "name": campus.name, "plan": campus.plan, "settings": campus.settings}


@router.patch("/settings")
async def update_campus_settings(
    payload: CampusSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update configurable security policies for this campus."""
    result = await db.execute(select(Campus).where(Campus.id == current_user.campus_id))
    campus = result.scalar_one_or_none()
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    campus.settings = {**campus.settings, **payload.model_dump()}
    await db.commit()
    return {"message": "Settings updated", "settings": campus.settings}


@router.get("/users", response_model=List[dict])
async def list_users(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "security")),
):
    """List users for this campus. Returns anonymised identifiers, never raw emails."""
    result = await db.execute(
        select(User.id, User.display_name, User.role, User.hygiene_score, User.created_at)
        .where(User.campus_id == current_user.campus_id, User.is_active == True)
        .limit(min(limit, 500))
    )
    rows = result.all()
    return [{"id": str(r.id), "display_name": r.display_name, "role": r.role, "hygiene_score": r.hygiene_score} for r in rows]


@router.post("/users")
async def invite_user(
    payload: InviteUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new user for this campus. Email is hashed — not stored raw."""
    email_hash = hash_email(payload.email)
    existing = await db.execute(
        select(User).where(User.email_hash == email_hash, User.campus_id == current_user.campus_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(
        campus_id  = current_user.campus_id,
        email_hash = email_hash,
        role       = payload.role,
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User created", "user_id": str(new_user.id)}
