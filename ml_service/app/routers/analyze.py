"""
CampusShield AI — ML Analyze Router (POST /analyze)

Orchestrates the full phishing detection pipeline:
  1. Feature extraction (FeatureExtractor)
  2. Risk scoring (compute_risk)
  3. Confidence estimation (sklearn classifier)
  4. Explanation generation (explainer)

API key authentication via X-API-Key header prevents external access.
This endpoint is ONLY called by the backend service.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
import re

from app.pipeline.feature_extractor import FeatureExtractor
from app.pipeline.risk_scorer import compute_risk
from app.pipeline.explainer import generate_explanation, get_recommended_action
from app.pipeline.classifier import PhishingClassifier
from app.config import settings

router = APIRouter()
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

# Singletons — loaded once at startup
_extractor   = FeatureExtractor()
_classifier  = PhishingClassifier()


def _verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> None:
    if api_key != settings.ML_SERVICE_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


class AnalyzeRequest(BaseModel):
    email_subject: str = Field(..., max_length=998)
    email_body:    str = Field(..., max_length=100_000)
    sender_domain: str = Field(..., max_length=253)
    links:         List[str] = Field(default_factory=list)


class SignalOut(BaseModel):
    name:        str
    triggered:   bool
    weight:      float
    value:       str
    description: str


class AnalyzeResponse(BaseModel):
    risk_score:        float
    risk_level:        str
    signals_triggered: List[SignalOut]
    plain_explanation: str
    recommended_action: str
    confidence:        float
    features:          dict   # Raw feature values for backend to persist
    processing_ms:     int


@router.post("/analyze", response_model=AnalyzeResponse, dependencies=[Security(_verify_api_key)])
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    Full phishing analysis pipeline. Called only from the backend.
    Raw email body is processed here and never stored.
    """
    t0 = time.perf_counter()

    # Step 1: Extract features (the only place raw text is touched)
    features = _extractor.extract(
        email_subject = payload.email_subject,
        email_body    = payload.email_body,
        sender_domain = payload.sender_domain,
        links         = payload.links,
    )

    # Step 2: Score risk (rule-based weighted signals)
    risk_score, risk_level, scored_signals = compute_risk(features)

    # Step 3: Get sklearn confidence calibration
    confidence = _classifier.predict_confidence(features, risk_score)

    # Step 4: Generate human-readable explanation
    explanation = generate_explanation(risk_level, risk_score, scored_signals)
    action      = get_recommended_action(risk_level)

    processing_ms = int((time.perf_counter() - t0) * 1000)

    # Convert signals to output format
    signals_out = [
        SignalOut(
            name        = s.name,
            triggered   = s.triggered,
            weight      = s.weight,
            value       = s.value,
            description = s.description,
        )
        for s in scored_signals if s.triggered  # Return only triggered signals
    ]

    # Raw feature dict for backend persistence (no raw email content)
    feature_dict = {
        "domain_mismatch":    features.domain_mismatch,
        "suspicious_tld":     features.suspicious_tld,
        "urgency_score":      features.urgency_score,
        "payment_keyword":    features.payment_keyword,
        "link_anomaly_score": features.link_anomaly_score,
    }

    return AnalyzeResponse(
        risk_score         = risk_score,
        risk_level         = risk_level,
        signals_triggered  = signals_out,
        plain_explanation  = explanation,
        recommended_action = action,
        confidence         = confidence,
        features           = feature_dict,
        processing_ms      = processing_ms,
    )
