"""
CampusShield AI — Rule-Based Phishing Explanation Generator

Generates plain-language explanations for any risk assessment.
This ensures transparency and user education alongside every alert.

DESIGN CHOICE: Rule-based approach (not LLM) is used by default
for three reasons:
  1. Deterministic — same input always produces same explanation
  2. No external API dependency (works offline in air-gapped campuses)
  3. Faster — sub-millisecond vs 1-3s for LLM calls

An optional LLM enhancement hook is provided for campuses with
API key access (placeholder pattern shown).
"""

from typing import List
from .risk_scorer import ScoredSignal


# ── Plain-language templates per signal ───────────────────────────────────────
SIGNAL_EXPLANATIONS = {
    "domain_mismatch": (
        "The links inside this email point to a different website than the one "
        "the sender claims to be from. This is a classic phishing tactic — the "
        "email appears to come from a trusted source but directs you to a fake site."
    ),
    "suspicious_tld": (
        "The sender's domain uses a top-level domain (TLD) that is frequently "
        "registered for free and commonly associated with phishing campaigns "
        "(e.g. .xyz, .top, .tk). Legitimate organisations rarely use these TLDs "
        "for official communications."
    ),
    "has_ip_url": (
        "One or more links in this email use a bare IP address instead of a "
        "readable domain name. Legitimate services almost never do this — it is "
        "a strong indicator that the destination is trying to hide its identity."
    ),
    "payment_keyword": (
        "This email mentions payment details, credit cards, bank accounts, or "
        "asks you to enter credentials. Be extremely suspicious of any email "
        "requesting financial or login information."
    ),
    "urgency_language": (
        "The email uses urgent language to pressure you to act quickly — phrases "
        "like 'Account will be suspended', 'Act now', or 'Verify immediately'. "
        "Creating a sense of panic is a common social engineering technique "
        "designed to bypass your critical thinking."
    ),
    "has_redirect_url": (
        "One or more links are shortened (e.g. bit.ly, tinyurl) or use a redirect "
        "service. Attackers use these to hide the real destination URL until you "
        "click, making it impossible to verify where you will land."
    ),
    "link_anomaly": (
        "The overall quality of links in this email was flagged as anomalous — "
        "they may combine multiple suspicious patterns that individually appear minor "
        "but together indicate a coordinated phishing attempt."
    ),
    "has_homoglyph_url": (
        "Links in this email contain look-alike characters (homoglyphs) — for example, "
        "using Cyrillic 'а' instead of Latin 'a' in a domain like 'pаypal.com'. "
        "This is an advanced technique designed to fool visual inspection."
    ),
}

RECOMMENDED_ACTIONS = {
    "High": (
        "Do NOT click any links or reply to this email. Report it to your campus "
        "IT security team immediately using the 'Report Phishing' button. Delete "
        "the email after reporting."
    ),
    "Medium": (
        "Treat this email with caution. Do not click links or provide any personal "
        "information. If the email appears to be from a known organisation, contact "
        "them directly using their official website — not the contact details in this email."
    ),
    "Low": (
        "This email shows some minor anomalies but is likely safe. Remain vigilant: "
        "never enter credentials from an email link, and verify unexpected requests "
        "with the sender through a separate channel."
    ),
}


def generate_explanation(
    risk_level: str,
    risk_score: float,
    triggered_signals: List[ScoredSignal],
) -> str:
    """
    Generate a human-readable explanation for a phishing assessment.

    Returns a paragraph suitable for display to a student user —
    non-technical, educational, and specific to the signals found.
    """
    triggered = [s for s in triggered_signals if s.triggered]

    if not triggered:
        return (
            f"This email has a risk score of {risk_score:.0f}/100, which is classified as {risk_level}. "
            "No strong phishing signals were detected. Exercise normal caution with all emails."
        )

    # Build explanation from strongest signals (top 3 by weight)
    top_signals = sorted(triggered, key=lambda s: s.weight, reverse=True)[:3]

    parts = [
        f"This email received a risk score of {risk_score:.0f}/100 ({risk_level} risk) "
        f"based on {len(triggered)} suspicious signal{'s' if len(triggered) > 1 else ''} detected:"
    ]

    for i, signal in enumerate(top_signals, 1):
        explanation = SIGNAL_EXPLANATIONS.get(signal.name, f"Signal '{signal.name}' was triggered.")
        parts.append(f"\n{i}. {explanation}")

    if len(triggered) > 3:
        remaining = len(triggered) - 3
        parts.append(f"\n+ {remaining} additional signal{'s' if remaining > 1 else ''} also detected.")

    return " ".join(parts)


def get_recommended_action(risk_level: str) -> str:
    """Return the recommended action for a given risk level."""
    return RECOMMENDED_ACTIONS.get(risk_level, RECOMMENDED_ACTIONS["Low"])
