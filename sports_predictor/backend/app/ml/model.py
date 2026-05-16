"""
Hybrid ML model: Gradient Boosting + Calibrated probabilities.
Falls back to statistical estimates when no trained model exists.
"""
import os
import pickle
import numpy as np
from typing import Optional, Tuple
from app.ml.features import build_feature_vector, N_FEATURES
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_model = None


def load_model():
    global _model
    if os.path.exists(settings.MODEL_PATH):
        with open(settings.MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        logger.info(f"ML model loaded from {settings.MODEL_PATH}")
    else:
        logger.warning("No trained ML model found — using statistical fallback")
        _model = None


def predict_probabilities(ctx) -> Tuple[float, float, float]:
    """Returns (prob_home, prob_draw, prob_away)."""
    if _model is None:
        return _statistical_fallback(ctx)
    try:
        features = build_feature_vector(ctx).reshape(1, -1)
        probs = _model.predict_proba(features)[0]
        # Model outputs [away, draw, home] — ensure correct ordering
        if hasattr(_model, "classes_"):
            idx = {c: i for i, c in enumerate(_model.classes_)}
            ph = probs[idx.get(2, 2)]
            pd = probs[idx.get(1, 1)]
            pa = probs[idx.get(0, 0)]
        else:
            ph, pd, pa = probs[2], probs[1], probs[0]
        total = ph + pd + pa
        return round(ph/total, 3), round(pd/total, 3), round(pa/total, 3)
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return _statistical_fallback(ctx)


def _statistical_fallback(ctx) -> Tuple[float, float, float]:
    """Simple Dixon-Coles inspired estimate when no ML model is available."""
    import math
    home_attack = ctx.home_xg_avg / max(ctx.away_xga_avg, 0.5)
    away_attack = ctx.away_xg_avg / max(ctx.home_xga_avg, 0.5)
    lam_h = max(0.3, home_attack * 1.15)  # home advantage
    lam_a = max(0.3, away_attack)

    prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
    for h in range(8):
        for a in range(8):
            p = (math.exp(-lam_h) * lam_h**h / math.factorial(h)
                 * math.exp(-lam_a) * lam_a**a / math.factorial(a))
            if h > a:   prob_home += p
            elif h == a: prob_draw += p
            else:        prob_away += p

    total = prob_home + prob_draw + prob_away
    return round(prob_home/total, 3), round(prob_draw/total, 3), round(prob_away/total, 3)
