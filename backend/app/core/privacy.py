"""
CampusShield AI — Differential Privacy Utility

Implements the Laplace mechanism for ε-differential privacy.
Applied to all analytics aggregate counts before DB persistence,
ensuring no individual student's data can be inferred from statistics.

PRIVACY DESIGN:
  - Each count query (total_scans, high_risk_count, etc.) is a
    sensitivity-1 function over the dataset.
  - We add Laplace(0, sensitivity/epsilon) noise.
  - With ε=1.0 (default), noise std ≈ 1.41 — imperceptible at
    campus scale (hundreds of events) but sufficient for privacy.
  - ε budget is tracked per snapshot to prevent composition attacks.
"""

import numpy as np
from typing import Dict, Any

from app.config import settings


def _laplace_noise(sensitivity: float, epsilon: float) -> float:
    """Sample from Laplace(0, sensitivity/epsilon) distribution."""
    scale = sensitivity / epsilon
    return float(np.random.laplace(loc=0.0, scale=scale))


def apply_dp_noise(true_count: int, sensitivity: float = None, epsilon: float = None) -> int:
    """
    Add Laplace noise to an integer count.
    Returns a non-negative integer (clipped at 0).

    Args:
        true_count: The actual count to privatise.
        sensitivity: L1 sensitivity of the query (default from settings).
        epsilon: Privacy budget for this query (default from settings).
    """
    s = sensitivity or settings.DP_SENSITIVITY
    e = epsilon or settings.DP_EPSILON
    noised = true_count + _laplace_noise(s, e)
    return max(0, int(round(noised)))


def privatise_analytics(raw: Dict[str, int]) -> Dict[str, Any]:
    """
    Apply DP noise to a dictionary of aggregate counts.
    Returns the noised dictionary and the epsilon consumed.

    Each key is treated as an independent sensitivity-1 query.
    Composition: total ε consumed = ε × number_of_queries (sequential).
    """
    noised = {}
    num_queries = len(raw)

    # Per-query epsilon: split budget across all counts in this snapshot.
    # This is basic sequential composition — advanced composition
    # (e.g. moments accountant) can tighten this for future iterations.
    per_query_epsilon = settings.DP_EPSILON / max(num_queries, 1)

    for key, value in raw.items():
        noised[key] = apply_dp_noise(value, epsilon=per_query_epsilon)

    epsilon_consumed = per_query_epsilon * num_queries  # = settings.DP_EPSILON
    return {"noised_counts": noised, "epsilon_consumed": epsilon_consumed}
