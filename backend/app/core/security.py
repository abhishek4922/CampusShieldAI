"""
CampusShield AI — Core Security Utilities

Handles:
  - bcrypt password hashing (cost 12)
  - JWT access + refresh token creation/decoding
  - CSRF token generation
  - Secure cookie helpers

SECURITY NOTE: JWT secret and bcrypt rounds are not configurable at
runtime to prevent downgrade attacks.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# bcrypt with cost factor 12 — slow enough to resist brute-force,
# fast enough for interactive login (~300ms on modern CPU)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ── Password Hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time bcrypt verification."""
    return pwd_context.verify(plain, hashed)


# ── Email Anonymisation ──────────────────────────────────────────────────────

def hash_email(email: str) -> str:
    """
    One-way SHA-256 hash of the lowercase email address.
    Used as the user identifier — the raw email is NEVER stored.
    """
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()


# ── JWT Token Management ─────────────────────────────────────────────────────

def _build_claims(subject: str, role: str, campus_id: str, token_type: str, expires_delta: timedelta) -> dict:
    """Construct JWT claims payload."""
    now = datetime.now(timezone.utc)
    return {
        "sub": subject,          # user UUID
        "role": role,
        "campus_id": campus_id,
        "type": token_type,      # "access" or "refresh"
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_hex(16),  # unique token ID (for revocation tracking)
    }


def create_access_token(user_id: str, role: str, campus_id: str) -> str:
    """Create a short-lived access token (15 min by default)."""
    claims = _build_claims(
        subject=user_id,
        role=role,
        campus_id=campus_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, role: str, campus_id: str) -> str:
    """Create a long-lived refresh token (7 days by default)."""
    claims = _build_claims(
        subject=user_id,
        role=role,
        campus_id=campus_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises JWTError if expired, tampered, or malformed.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise exc


# ── CSRF Protection ──────────────────────────────────────────────────────────

def generate_csrf_token() -> str:
    """Generate a cryptographically-secure CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(request_token: str, session_token: str) -> bool:
    """Constant-time comparison for CSRF double-submit cookie pattern."""
    return hmac.compare_digest(request_token, session_token)
