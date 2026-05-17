"""
Moteur d'ensemble: fusionne Poisson, XGBoost et Neural Network.
Pondération adaptative selon la disponibilité des features.
"""
from dataclasses import dataclass
from typing import Any

from .poisson_model import PoissonPrediction
from ..schemas.schemas import ModelPrediction, EnsembleResult


# Poids par défaut (optimisés empiriquement)
DEFAULT_WEIGHTS = {
    "poisson":  0.30,
    "xgboost":  0.40,
    "neural":   0.30,
}

# Si cotes bookmaker disponibles → augmenter le poids des modèles qui les utilisent
ODDS_ADJUSTED_WEIGHTS = {
    "poisson":  0.25,
    "xgboost":  0.45,
    "neural":   0.30,
}


@dataclass
class EnsembleInput:
    poisson:  dict[str, Any]
    xgboost:  dict[str, Any]
    neural:   dict[str, Any]
    has_odds: bool = False


def fuse(inputs: EnsembleInput) -> EnsembleResult:
    weights = ODDS_ADJUSTED_WEIGHTS if inputs.has_odds else DEFAULT_WEIGHTS

    models = [
        ("poisson",  inputs.poisson,  weights["poisson"]),
        ("xgboost",  inputs.xgboost,  weights["xgboost"]),
        ("neural",   inputs.neural,   weights["neural"]),
    ]

    # ── Probabilités d'issue ────────────────────────────────────────────────
    p_home = sum(m["prob_home_win"] * w for _, m, w in models)
    p_draw = sum(m["prob_draw"] * w for _, m, w in models)
    p_away = sum(m["prob_away_win"] * w for _, m, w in models)

    # Normalisation (somme = 1)
    total = p_home + p_draw + p_away
    p_home /= total; p_draw /= total; p_away /= total

    # ── Score prédit (vote majoritaire pondéré) ──────────────────────────────
    score_votes: dict[tuple[int, int], float] = {}
    for _, m, w in models:
        s = (m.get("predicted_home_score", 1), m.get("predicted_away_score", 1))
        score_votes[s] = score_votes.get(s, 0) + w
    predicted_score = max(score_votes, key=score_votes.get)
    exact_score_prob = score_votes[predicted_score]

    # ── Marchés ──────────────────────────────────────────────────────────────
    # Over 2.5: moyenne pondérée si disponible
    over25_vals = []
    btts_vals   = []
    for _, m, w in models:
        if "prob_over25" in m: over25_vals.append((m["prob_over25"], w))
        if "prob_btts"   in m: btts_vals.append((m["prob_btts"],    w))

    if over25_vals:
        tw = sum(w for _, w in over25_vals)
        p_over25 = sum(v * w for v, w in over25_vals) / tw
    else:
        # Fallback: estimation via les λ Poisson
        p_over25 = inputs.poisson.get("prob_over25", 0.50)

    if btts_vals:
        tw = sum(w for _, w in btts_vals)
        p_btts = sum(v * w for v, w in btts_vals) / tw
    else:
        p_btts = inputs.poisson.get("prob_btts", 0.50)

    # ── Marchés secondaires ──────────────────────────────────────────────────
    # HT home lead: approximation via Poisson (λ_home / 2 sur 45 min)
    lam_h = inputs.poisson.get("lambda_home", 1.5) / 2
    lam_a = inputs.poisson.get("lambda_away", 1.2) / 2
    import math
    p_ht_home = sum(
        (lam_h ** h) * math.exp(-lam_h) / math.factorial(h) *
        (lam_a ** a) * math.exp(-lam_a) / math.factorial(a)
        for h in range(6) for a in range(6) if h > a
    )

    # But tardif (>75 min): corrélation positive avec Over 2.5 et proche score
    p_late_goal = 0.35 + 0.30 * p_over25 + 0.15 * (1 - abs(p_home - p_away))

    # ── Accord entre modèles ─────────────────────────────────────────────────
    # = 1 - variance normalisée des proba_home_win
    ph_vals = [m["prob_home_win"] for _, m, _ in models]
    variance = sum((v - p_home) ** 2 for v in ph_vals) / len(ph_vals)
    model_agreement = max(0.0, 1.0 - variance * 10)

    # ── Confiance globale ────────────────────────────────────────────────────
    base_conf = sum(m.get("confidence", max(m["prob_home_win"], m["prob_draw"], m["prob_away_win"])) * w
                    for _, m, w in models)
    final_confidence = round((base_conf * 0.7 + model_agreement * 0.3) * 100, 1)

    # ── Détail des modèles pour affichage ────────────────────────────────────
    model_preds = []
    for name, m, w in models:
        ph = m.get("prob_home_win", 0)
        pd = m.get("prob_draw", 0)
        pa = m.get("prob_away_win", 0)
        model_preds.append(ModelPrediction(
            model_name=name,
            prob_home=round(ph, 4),
            prob_draw=round(pd, 4),
            prob_away=round(pa, 4),
            predicted_home_score=m.get("predicted_home_score", predicted_score[0]),
            predicted_away_score=m.get("predicted_away_score", predicted_score[1]),
            exact_score_prob=round(score_votes.get(
                (m.get("predicted_home_score", 0), m.get("predicted_away_score", 0)), 0.0
            ), 4),
            confidence=round(m.get("confidence", max(ph, pd, pa)), 4),
        ))

    return EnsembleResult(
        prob_home=round(p_home, 4),
        prob_draw=round(p_draw, 4),
        prob_away=round(p_away, 4),
        predicted_home_score=predicted_score[0],
        predicted_away_score=predicted_score[1],
        exact_score_probability=round(exact_score_prob, 4),
        prob_over25=round(p_over25, 4),
        prob_btts=round(p_btts, 4),
        prob_ht_home_lead=round(p_ht_home, 4),
        prob_late_goal=round(min(0.95, p_late_goal), 4),
        model_agreement=round(model_agreement, 4),
        predictions=model_preds,
    )
