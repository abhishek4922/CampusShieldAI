"""
CampusShield AI — SQLAlchemy ORM Models

All models include campus_id for multi-tenant isolation.
No raw PII is stored anywhere in this schema.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Float,
    Integer, SmallInteger, ForeignKey, JSON, BigInteger,
    CheckConstraint, UniqueConstraint, event, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ── Campus (SaaS Tenant) ─────────────────────────────────────────────────────
class Campus(Base):
    __tablename__ = "campuses"
    __table_args__ = {"schema": "campusshield"}

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(255), nullable=False)
    domain     = Column(String(255), nullable=False, unique=True)   # e.g. "mit.edu"
    plan       = Column(String(50), nullable=False, default="free") # free|pro|enterprise
    settings   = Column(JSON, nullable=False, default=dict)          # configurable policies
    is_active  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users      = relationship("User", back_populates="campus", cascade="all, delete-orphan")
    scans      = relationship("PhishingScan", back_populates="campus")


# ── User (hashed identity, no raw PII) ──────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("campus_id", "email_hash", name="uq_user_campus_email"),
        CheckConstraint("role IN ('student','admin','security')", name="ck_user_role"),
        {"schema": "campusshield"},
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id      = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="CASCADE"), nullable=False)
    # SHA-256 of lowercase email - never the raw email address
    email_hash     = Column(Text, nullable=False, index=True)
    display_name   = Column(String(120))                             # user-controlled, optional
    role           = Column(String(20), nullable=False, default="student")
    password_hash  = Column(Text)                                    # bcrypt; NULL for OAuth users
    oauth_provider = Column(String(50))                              # 'google' | 'microsoft'
    oauth_subject  = Column(Text)                                    # provider opaque ID
    consent_given  = Column(Boolean, nullable=False, default=False)
    consent_at     = Column(DateTime(timezone=True))
    is_active      = Column(Boolean, nullable=False, default=True)
    hygiene_score  = Column(SmallInteger, nullable=False, default=0) # gamified score 0-1000
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    campus = relationship("Campus", back_populates="users")
    scans  = relationship("PhishingScan", back_populates="user")


# ── Phishing Scan (features + results only, never raw email content) ─────────
class PhishingScan(Base):
    __tablename__ = "phishing_scans"
    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_risk_score_range"),
        CheckConstraint("risk_level IN ('Low','Medium','High')", name="ck_risk_level"),
        Index("idx_scans_campus_risk", "campus_id", "risk_level", "scanned_at"),
        {"schema": "campusshield"},
    )

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id           = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="CASCADE"), nullable=False)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("campusshield.users.id", ondelete="SET NULL"))

    # ── Extracted features (the ML pipeline populates these) ─
    sender_domain       = Column(String(255))          # domain only, not full address
    sender_tld          = Column(String(20))
    link_count          = Column(SmallInteger)
    domain_mismatch     = Column(Boolean)              # sender domain ≠ link domains
    suspicious_tld      = Column(Boolean)              # .xyz, .top, .click, etc.
    urgency_score       = Column(Float)                # 0.0–1.0 urgency keyword density
    payment_keyword     = Column(Boolean)              # presence of payment-related terms
    link_anomaly_score  = Column(Float)                # 0.0–1.0 (homoglyphs, redirects)

    # ── Risk output ───────────────────────────────────────────
    risk_score          = Column(Float, nullable=False)
    risk_level          = Column(String(10), nullable=False)         # Low | Medium | High
    confidence          = Column(Float, nullable=False)
    signals_triggered   = Column(JSON, nullable=False, default=list) # [{name, weight, value}]
    plain_explanation   = Column(Text)
    recommended_action  = Column(Text)

    scanned_at          = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    campus = relationship("Campus", back_populates="scans")
    user   = relationship("User", back_populates="scans")
    alert  = relationship("Alert", back_populates="scan", uselist=False)


# ── Alert (generated from High/Critical risk scans) ──────────────────────────
class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("severity IN ('Low','Medium','High','Critical')", name="ck_alert_severity"),
        CheckConstraint("status IN ('open','acknowledged','resolved')", name="ck_alert_status"),
        {"schema": "campusshield"},
    )

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id   = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id     = Column(UUID(as_uuid=True), ForeignKey("campusshield.phishing_scans.id", ondelete="CASCADE"), nullable=False)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("campusshield.users.id", ondelete="SET NULL"))
    severity    = Column(String(10), nullable=False)
    status      = Column(String(20), nullable=False, default="open")
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("campusshield.users.id"))
    resolved_at = Column(DateTime(timezone=True))
    notes       = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("PhishingScan", back_populates="alert")


# ── Analytics Snapshot (DP-noised aggregates, never raw events) ──────────────
class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("campus_id", "period_start", "period_end", name="uq_analytics_period"),
        {"schema": "campusshield"},
    )

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id             = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start          = Column(DateTime(timezone=True), nullable=False)
    period_end            = Column(DateTime(timezone=True), nullable=False)
    total_scans           = Column(Integer, nullable=False)      # DP-noised count
    high_risk_count       = Column(Integer, nullable=False)
    medium_risk_count     = Column(Integer, nullable=False)
    low_risk_count        = Column(Integer, nullable=False)
    top_signal_categories = Column(JSON, nullable=False, default=dict)  # {signal: noised_count}
    vulnerability_score   = Column(Float)                               # 0-100 campus score
    epsilon_budget_used   = Column(Float)                               # DP ε consumed this period
    created_at            = Column(DateTime(timezone=True), server_default=func.now())


# ── Digital Hygiene Session (anonymized learning progress) ───────────────────
class HygieneSession(Base):
    __tablename__ = "hygiene_sessions"
    __table_args__ = {"schema": "campusshield"}

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id    = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="CASCADE"), nullable=False)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("campusshield.users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id    = Column(String(100), nullable=False)
    completed    = Column(Boolean, nullable=False, default=False)
    score        = Column(SmallInteger)                          # 0-100 per lesson
    difficulty   = Column(String(20))                            # beginner | intermediate | advanced
    completed_at = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


# ── Audit Log (append-only enforced at app layer) ────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "campusshield"}

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    campus_id   = Column(UUID(as_uuid=True), ForeignKey("campusshield.campuses.id", ondelete="SET NULL"))
    user_id     = Column(UUID(as_uuid=True), ForeignKey("campusshield.users.id", ondelete="SET NULL"))
    action      = Column(String(100), nullable=False, index=True)  # e.g. 'user.login', 'scan.analyze'
    resource    = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    ip_addr     = Column(String(45))                               # IPv4/IPv6; rotated every 90 days
    user_agent  = Column(Text)
    metadata    = Column(JSON)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)
