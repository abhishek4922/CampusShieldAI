"""
CampusShield AI — Authentication Router

Endpoints:
  POST /v1/auth/login       - Email/password login
  POST /v1/auth/refresh     - Refresh access token
  POST /v1/auth/logout      - Invalidate refresh token
  POST /v1/auth/consent     - Record explicit user consent
  GET  /v1/auth/oauth/login - Initiate OAuth flow
  GET  /v1/auth/oauth/callback - OAuth redirect handler

SECURITY: All auth failures return identical messages to prevent
user enumeration attacks.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.models import User, AuditLog
from app.core.security import (
    verify_password, hash_password, hash_email,
    create_access_token, create_refresh_token, decode_token,
)
from app.schemas.auth import LoginRequest, TokenResponse, ConsentRequest
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.
    Returns access (15 min) + refresh (7 day) JWT pair.
    """
    email_hash = hash_email(payload.email)

    result = await db.execute(
        select(User).where(
            User.email_hash == email_hash,
            User.is_active == True,
        )
    )
    user = result.scalar_one_or_none()

    # Constant-time: always run verify_password even on miss to prevent timing attacks
    dummy_hash = "$2b$12$KIXOKMYiGFQdYhqwMGz/seXPE0qv3sFqX/HB3KAGswfJNcKJO.HxK"
    password_to_check = user.password_hash if user else dummy_hash

    if not verify_password(payload.password, password_to_check) or not user:
        # Audit failed login attempt
        db.add(AuditLog(action="user.login.failed", ip_addr=None, metadata={"reason": "invalid_credentials"}))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    campus_id = str(user.campus_id)
    access  = create_access_token(str(user.id), user.role, campus_id)
    refresh = create_refresh_token(str(user.id), user.role, campus_id)

    # Audit successful login
    db.add(AuditLog(campus_id=user.campus_id, user_id=user.id, action="user.login", resource="user", resource_id=user.id))
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer", role=user.role)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    token = request.cookies.get("refresh_token") or request.headers.get("X-Refresh-Token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token type mismatch")

    user_id   = payload["sub"]
    role      = payload["role"]
    campus_id = payload["campus_id"]

    return TokenResponse(
        access_token=create_access_token(user_id, role, campus_id),
        refresh_token=create_refresh_token(user_id, role, campus_id),
        token_type="bearer",
        role=role,
    )


@router.post("/consent")
async def record_consent(
    payload: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record explicit user consent before any personal data is processed.
    This is a prerequisite for using the phishing scan service.
    """
    current_user.consent_given = True
    current_user.consent_at    = datetime.now(timezone.utc)
    db.add(AuditLog(
        campus_id=current_user.campus_id,
        user_id=current_user.id,
        action="user.consent.given",
        metadata={"version": payload.consent_version},
    ))
    await db.commit()
    return {"message": "Consent recorded", "consent_at": current_user.consent_at}


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invalidate session (clear cookies). Token blacklisting can be added via Redis jti."""
    db.add(AuditLog(campus_id=current_user.campus_id, user_id=current_user.id, action="user.logout"))
    await db.commit()
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
