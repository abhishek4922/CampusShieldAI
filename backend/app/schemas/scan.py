"""
CampusShield AI — Pydantic Schemas for Scans & Alerts

All input schemas use strict validation to prevent injection attacks.
Outputs never echo back raw email content — only derived signals.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


# ── Input: Phishing Email Analysis Request ────────────────────────────────────
class EmailAnalysisRequest(BaseModel):
    """
    POST /v1/scans/analyze-email

    Note: email_subject and email_body are NEVER persisted.
    They are processed in-memory, features extracted, then discarded.
    """
    email_subject: str = Field(..., max_length=998, description="Email subject line")
    email_body:    str = Field(..., max_length=100_000, description="Email body text (plain or HTML stripped)")
    sender_domain: str = Field(..., max_length=253, description="Sender's domain (e.g. paypal-security.xyz)")
    links:         List[str] = Field(default_factory=list, max_length=500, description="Extracted URLs from email")

    @field_validator("sender_domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        # Basic domain format check — not a substitute for DKIM/SPF
        if not re.match(r"^[a-zA-Z0-9._\-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid sender domain format")
        return v.lower()

    @field_validator("links")
    @classmethod
    def validate_links(cls, v: List[str]) -> List[str]:
        if len(v) > 500:
            raise ValueError("Too many links — maximum 500 per email")
        return v


# ── Signal: individual risk signal ───────────────────────────────────────────
class RiskSignal(BaseModel):
    name:        str
    triggered:   bool
    weight:      float  # Contribution to overall score (0.0–1.0)
    value:       Optional[str] = None   # Human-readable value (domain name, score, etc.)
    description: str


# ── Output: Phishing Analysis Result ─────────────────────────────────────────
class EmailAnalysisResponse(BaseModel):
    scan_id:           UUID
    risk_score:        float = Field(..., ge=0, le=100)
    risk_level:        str   = Field(..., pattern="^(Low|Medium|High)$")
    signals_triggered: List[RiskSignal]
    plain_explanation: str
    recommended_action: str
    confidence:        float = Field(..., ge=0, le=1)
    processing_ms:     int


# ── Scan Record ───────────────────────────────────────────────────────────────
class ScanRecord(BaseModel):
    id:            UUID
    risk_score:    float
    risk_level:    str
    confidence:    float
    scanned_at:    datetime
    sender_domain: Optional[str]

    class Config:
        from_attributes = True


# ── Alert Schemas ─────────────────────────────────────────────────────────────
class AlertResponse(BaseModel):
    id:         UUID
    severity:   str
    status:     str
    scan_id:    UUID
    created_at: datetime
    notes:      Optional[str]

    class Config:
        from_attributes = True


class AlertUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(acknowledged|resolved)$")
    notes:  Optional[str] = Field(None, max_length=2000)
