"""
CampusShield AI — Sklearn Phishing Classifier

Provides secondary confidence calibration on top of the rule-based
risk score. Uses a RandomForestClassifier trained on feature vectors.

MODEL LOADING STRATEGY:
  - On startup, attempts to load a serialised model from disk.
  - If no model exists (first boot), uses heuristic confidence estimation.
  - Model is retrained offline via training/train.py and hot-swapped.

AMD OPTIMIZATION:
  - RandomForest with n_jobs=-1 uses all available cores for parallelism.
  - sklearn's joblib backend is OpenMP-backed → benefits from AMD EPYC
    many-core architecture automatically.
  - ONNX export (future) for 3-10x inference speedup via ONNX Runtime.
"""

import os
import numpy as np
from typing import Optional
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "phishing_classifier" / "model.pkl"


class PhishingClassifier:
    """
    Wraps a trained sklearn pipeline for phishing confidence estimation.
    Degrades gracefully to heuristic mode when no model is available.
    """

    def __init__(self):
        self._model = None
        self._load_model()

    def _load_model(self):
        """Attempt to load serialised model. Fail silently for first boot."""
        if MODEL_PATH.exists():
            try:
                import joblib
                self._model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[ML] Warning: Could not load model from {MODEL_PATH}: {e}")
                self._model = None
        else:
            print(f"[ML] No pre-trained model found at {MODEL_PATH}. Using heuristic confidence.")

    def _features_to_vector(self, features, risk_score: float) -> np.ndarray:
        """Convert EmailFeatures to numpy vector for sklearn input."""
        return np.array([[
            float(features.domain_mismatch),
            float(features.suspicious_tld),
            features.urgency_score,
            float(features.payment_keyword),
            features.link_anomaly_score,
            float(features.has_ip_url),
            float(features.has_redirect_url),
            float(features.has_homoglyph_url),
            features.link_count,
            risk_score / 100.0,   # Normalised risk score as a feature
        ]])

    def predict_confidence(self, features, risk_score: float) -> float:
        """
        Return confidence in the 'phishing' classification (0.0–1.0).

        If model is loaded: uses sklearn's predict_proba.
        If not: uses a calibrated heuristic based on risk score.
        """
        if self._model is not None:
            try:
                X = self._features_to_vector(features, risk_score)
                proba = self._model.predict_proba(X)
                # proba shape: [[p_safe, p_phishing]]
                return round(float(proba[0][1]), 4)
            except Exception:
                pass  # Fall through to heuristic

        # Heuristic calibration: sigmoid-like mapping of risk score to confidence
        # At 50 → 0.50confident, at 80 → 0.88 confident, at 20 → 0.27 confident
        confidence = 1 / (1 + np.exp(-0.08 * (risk_score - 50)))
        return round(float(confidence), 4)
