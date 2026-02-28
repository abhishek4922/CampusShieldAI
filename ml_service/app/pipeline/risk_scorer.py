"""
CampusShield AI — Risk Scoring Engine

Converts raw extracted features into a 0-100 risk score,
a Low/Medium/High classification, and a structured list of
triggered signals with their weights and human-readable values.

DESIGN: The weighted rule-based scorer is the primary model.
The sklearn classifier provides a secondary confidence calibration.
This hybrid approach ensures explainability (rule-based) with
statistical calibration (ML model).

Signal weights are tuned based on real phishing campaign analysis.
Domain mismatch and suspicious TLD are the strongest single indicators.
"""

from dataclasses import dataclass
from typing import List, Tuple
from .feature_extractor import EmailFeatures


@dataclass
class ScoredSignal:
    name:        str
    triggered:   bool
    weight:      float    # Raw weight (0.0–1.0)
    contribution: float   # Actual score contribution
    value:       str
    description: str


# ── Signal Definitions ─────────────────────────────────────────────────────
# Each signal: (name, weight, description_template)
# Weights sum to 1.0 for a fully-triggered worst-case email
SIGNALS = [
    # High-weight signals (very strong phishing indicators)
    ("domain_mismatch",    0.25, "Sender domain differs from link domains"),
    ("suspicious_tld",     0.15, "Sender uses a suspicious top-level domain"),
    ("has_ip_url",         0.15, "Email contains links with bare IP addresses"),
    ("payment_keyword",    0.15, "Email references payment or credential information"),
    # Medium-weight signals
    ("urgency_language",   0.12, "Email uses urgency-inducing language patterns"),
    ("has_redirect_url",   0.08, "Email uses URL shorteners or redirect services"),
    ("link_anomaly",       0.05, "Composite link quality score is low"),
    # Low-weight signals (weak alone, significant in combination)
    ("has_homoglyph_url",  0.05, "Email contains links with look-alike Unicode characters"),
]

# Risk level thresholds
_HIGH_THRESHOLD   = 65
_MEDIUM_THRESHOLD = 35


def compute_risk(features: EmailFeatures) -> Tuple[float, str, List[ScoredSignal]]:
    """
    Compute risk score from extracted features.

    Returns:
        (risk_score: 0-100, risk_level: str, signals: List[ScoredSignal])

    Algorithm:
        weighted_sum = Σ (signal_weight × triggered)
        base_score   = weighted_sum × 100
        boost        = link_anomaly_score × 5  (continuous signal)
        urgency_boost= urgency_score × 12      (continuous signal)
        risk_score   = clamp(base_score + boost + urgency_boost, 0, 100)
    """
    triggered_vals = {
        "domain_mismatch":  (features.domain_mismatch, str(features.domain_mismatch)),
        "suspicious_tld":   (features.suspicious_tld, features.sender_tld or "N/A"),
        "has_ip_url":       (features.has_ip_url, "IP-based URL detected"),
        "payment_keyword":  (features.payment_keyword, "Payment/credential term present"),
        "urgency_language": (features.urgency_score > 0.2, f"score={features.urgency_score:.2f}"),
        "has_redirect_url": (features.has_redirect_url, "Redirect/shortener URL detected"),
        "link_anomaly":     (features.link_anomaly_score > 0.3, f"score={features.link_anomaly_score:.2f}"),
        "has_homoglyph_url":(features.has_homoglyph_url, "Homoglyph character detected"),
    }

    scored = []
    weighted_sum = 0.0

    for name, weight, description in SIGNALS:
        triggered, value = triggered_vals.get(name, (False, "N/A"))
        contribution = weight if triggered else 0.0
        weighted_sum += contribution
        scored.append(ScoredSignal(
            name         = name,
            triggered    = triggered,
            weight       = weight,
            contribution = round(contribution, 4),
            value        = value,
            description  = description,
        ))

    # Base score from binary signals
    base_score = weighted_sum * 100

    # Continuous signal boosts (scale-calibrated)
    urgency_boost = features.urgency_score * 12
    link_boost    = features.link_anomaly_score * 5

    risk_score = min(100.0, base_score + urgency_boost + link_boost)
    risk_score = round(risk_score, 2)

    if risk_score >= _HIGH_THRESHOLD:
        risk_level = "High"
    elif risk_score >= _MEDIUM_THRESHOLD:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return risk_score, risk_level, scored
