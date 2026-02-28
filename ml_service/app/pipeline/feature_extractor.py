"""
CampusShield AI — Feature Extraction Module

Extracts structured risk signals from raw email content.
This is the ONLY module that touches the raw email text.
All other modules work with extracted feature vectors.

PRIVACY NOTE: This module runs in the ML microservice only.
Raw email content never persists to any storage layer.

AMD OPTIMIZATION: Pure Python/regex operations that benefit
from multi-core scheduling in parallel inference scenarios.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse


# ── Known suspicious TLDs frequently used in phishing ────────────────────────
SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".click", ".link", ".loan", ".work", ".gq",
    ".ml", ".ga", ".cf", ".tk", ".pw", ".cc", ".su", ".ws",
    ".info", ".biz", ".cam", ".date", ".download",
}

# ── Urgency language patterns (common in phishing) ────────────────────────────
URGENCY_PATTERNS = [
    r"urgent[\s!]*action",
    r"act[\s]+now",
    r"immediate[\s]+action",
    r"account[\s]+(will[\s]+be[\s]+)?(suspended|closed|blocked|terminated)",
    r"verify[\s]+immediately",
    r"confirm[\s]+within[\s]+\d+[\s]+hours",
    r"limited[\s]+time",
    r"expire[sd]?",
    r"update[\s]+your[\s]+information",
    r"reactivat",
    r"suspicious[\s]+(activity|login|access)",
    r"unauthorized[\s]+(access|login|transaction)",
]

# ── Payment / credential harvesting keywords ──────────────────────────────────
PAYMENT_KEYWORDS = [
    r"credit[\s]*card", r"debit[\s]*card", r"bank[\s]*account",
    r"ssn|social[\s]*security", r"routing[\s]*number",
    r"password", r"login[\s]*credential", r"wire[\s]*transfer",
    r"paypal[\s]*account", r"bitcoin|crypto[\s]*wallet",
    r"enter[\s]+your[\s]+(details|information|card)",
]

# ── Link anomaly patterns ─────────────────────────────────────────────────────
HOMOGLYPH_CHARS = re.compile(r"[а-яА-Я\u0370-\u03ff\u0400-\u04ff]")  # Cyrillic/Greek in URLs
REDIRECT_PATTERNS = re.compile(r"(bit\.ly|tinyurl|t\.co|ow\.ly|goo\.gl|is\.gd|cli\.gs|rebrand\.ly)")
IP_IN_URL = re.compile(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


@dataclass
class EmailFeatures:
    """
    Structured feature vector extracted from one email.
    Becomes the sole input to risk scoring — raw text is discarded.
    """
    # Domain-level features
    sender_domain:     str
    sender_tld:        str
    domain_mismatch:   bool     # sender domain ≠ majority of link domains
    suspicious_tld:    bool     # TLD in known-bad list

    # Content features
    urgency_score:     float    # 0.0–1.0 — proportion of urgency patterns matched
    payment_keyword:   bool     # any payment/credential keyword present
    link_count:        int

    # Link-level features
    link_anomaly_score: float   # 0.0–1.0 composite anomaly score
    has_ip_url:         bool
    has_redirect_url:   bool
    has_homoglyph_url:  bool

    # Per-link domains (for domain mismatch calculation)
    link_domains:      List[str] = field(default_factory=list)


class FeatureExtractor:
    """
    Stateless feature extractor. Instantiated once at startup;
    all methods are pure functions of their inputs.
    """

    def extract(
        self,
        email_subject: str,
        email_body:    str,
        sender_domain: str,
        links:         List[str],
    ) -> EmailFeatures:
        """
        Main extraction entry point. Returns EmailFeatures.
        Called per request — does NOT mutate any state.
        """
        combined_text = f"{email_subject} {email_body}".lower()
        sender_domain = sender_domain.lower().strip()
        sender_tld    = f".{sender_domain.rsplit('.', 1)[-1]}" if "." in sender_domain else ""

        link_domains       = self._extract_link_domains(links)
        domain_mismatch    = self._check_domain_mismatch(sender_domain, link_domains)
        suspicious_tld     = sender_tld in SUSPICIOUS_TLDS
        urgency_score      = self._urgency_score(combined_text)
        payment_keyword    = self._has_payment_keywords(combined_text)
        link_anomaly, has_ip, has_redirect, has_homoglyph = self._link_anomaly(links)

        return EmailFeatures(
            sender_domain      = sender_domain,
            sender_tld         = sender_tld,
            domain_mismatch    = domain_mismatch,
            suspicious_tld     = suspicious_tld,
            urgency_score      = urgency_score,
            payment_keyword    = payment_keyword,
            link_count         = len(links),
            link_anomaly_score = link_anomaly,
            has_ip_url         = has_ip,
            has_redirect_url   = has_redirect,
            has_homoglyph_url  = has_homoglyph,
            link_domains       = link_domains,
        )

    def _extract_link_domains(self, links: List[str]) -> List[str]:
        domains = []
        for link in links:
            try:
                parsed = urlparse(link if link.startswith("http") else f"http://{link}")
                if parsed.hostname:
                    domains.append(parsed.hostname.lower())
            except Exception:
                pass
        return domains

    def _check_domain_mismatch(self, sender_domain: str, link_domains: List[str]) -> bool:
        """True if the majority of link domains differ from the sender domain."""
        if not link_domains:
            return False
        # Strip www. prefix from sender for comparison
        base_sender = sender_domain.lstrip("www.")
        mismatches = sum(1 for d in link_domains if base_sender not in d)
        return (mismatches / len(link_domains)) > 0.5

    def _urgency_score(self, text: str) -> float:
        """Proportion of urgency patterns matched — 0.0 to 1.0."""
        matched = sum(1 for pattern in URGENCY_PATTERNS if re.search(pattern, text))
        return round(min(matched / len(URGENCY_PATTERNS), 1.0), 4)

    def _has_payment_keywords(self, text: str) -> bool:
        return any(re.search(p, text) for p in PAYMENT_KEYWORDS)

    def _link_anomaly(self, links: List[str]):
        """Compute composite link anomaly score and individual flags."""
        if not links:
            return 0.0, False, False, False

        has_ip       = any(IP_IN_URL.search(l) for l in links)
        has_redirect = any(REDIRECT_PATTERNS.search(l) for l in links)
        has_homoglyph = any(HOMOGLYPH_CHARS.search(l) for l in links)

        score = (
            (0.4 if has_ip else 0.0) +
            (0.3 if has_redirect else 0.0) +
            (0.3 if has_homoglyph else 0.0)
        )
        return round(score, 4), has_ip, has_redirect, has_homoglyph
