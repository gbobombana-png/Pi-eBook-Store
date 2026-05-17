"""
Modèle XGBoost pour la prédiction footballistique.
Utilise un vecteur de features riche (stats, forme, H2H, cotes).
En production, le modèle est chargé depuis un fichier .ubj sauvegardé.
En fallback (pas de modèle entraîné), on utilise un modèle analytique calibré.
"""
import os
import numpy as np
from dataclasses import dataclass
from typing import Any

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

MODEL_PATH = os.path.join(os.path.dirname(__file__), "weights", "xgb_football.ubj")


@dataclass
class XGBFeatures:
    # Statistiques offensives
    home_avg_goals_scored: float
    away_avg_goals_scored: float
    home_avg_goals_conceded: float
    away_avg_goals_conceded: float
    home_xg_for: float
    away_xg_for: float
    home_xg_against: float
    away_xg_against: float

    # Forme (0-1, moyenne des 5 derniers matchs: 1=V, 0.5=N, 0=D)
    home_form: float
    away_form: float

    # H2H
    h2h_home_win_rate: float
    h2h_avg_goals: float
    h2h_matches: int

    # Cotes (probabilités implicites normalisées)
    odds_implied_home: float
    odds_implied_draw: float
    odds_implied_away: float

    # Contexte
    home_advantage: float = 1.0     # 1=domicile, 0.5=neutre, 0=extérieur
    home_injured_key: int = 0       # nb joueurs clés blessés
    away_injured_key: int = 0

    # Forme xG récente
    home_xg_last5: float = 1.4
    away_xg_last5: float = 1.2


def features_to_vector(f: XGBFeatures) -> np.ndarray:
    return np.array([
        f.home_avg_goals_scored,
        f.away_avg_goals_scored,
        f.home_avg_goals_conceded,
        f.away_avg_goals_conceded,
        f.home_xg_for,
        f.away_xg_for,
        f.home_xg_against,
        f.away_xg_against,
        f.home_form,
        f.away_form,
        f.home_form - f.away_form,          # différentiel de forme
        f.h2h_home_win_rate,
        f.h2h_avg_goals,
        min(f.h2h_matches, 20) / 20,        # normalisé
        f.odds_implied_home,
        f.odds_implied_draw,
        f.odds_implied_away,
        f.odds_implied_home - f.odds_implied_away,
        f.home_advantage,
        f.home_injured_key / 3.0,           # normalisé (max 3 joueurs clés)
        f.away_injured_key / 3.0,
        f.home_xg_last5,
        f.away_xg_last5,
        f.home_xg_last5 - f.away_xg_last5,
        f.home_avg_goals_scored - f.away_avg_goals_conceded,  # net attaque A
        f.away_avg_goals_scored - f.home_avg_goals_conceded,  # net attaque B
    ], dtype=np.float32)


def _analytical_fallback(f: XGBFeatures) -> dict[str, Any]:
    """
    Prédiction analytique calibrée quand le modèle XGBoost n'est pas disponible.
    Utilise un ensemble de règles heuristiques basées sur les features.
    """
    # Score composite domicile
    home_score = (
        0.25 * f.home_avg_goals_scored / max(f.away_avg_goals_conceded, 0.5)
        + 0.20 * f.home_form
        + 0.15 * f.h2h_home_win_rate
        + 0.25 * f.odds_implied_home
        + 0.10 * f.home_advantage
        + 0.05 * max(0, (f.away_injured_key - f.home_injured_key) / 3)
    )
    away_score = (
        0.25 * f.away_avg_goals_scored / max(f.home_avg_goals_conceded, 0.5)
        + 0.20 * f.away_form
        + 0.15 * (1 - f.h2h_home_win_rate)
        + 0.25 * f.odds_implied_away
        + 0.10 * (1 - f.home_advantage)
        + 0.05 * max(0, (f.home_injured_key - f.away_injured_key) / 3)
    )
    draw_score = 0.28 * f.odds_implied_draw + 0.72 * (1 - abs(home_score - away_score))

    total = home_score + draw_score + away_score
    p_home = home_score / total
    p_draw = draw_score / total
    p_away = away_score / total

    # Score prédit (arrondi aux valeurs réalistes)
    exp_home = f.home_xg_last5 * (0.5 + p_home)
    exp_away = f.away_xg_last5 * (0.5 + p_away)
    pred_h = max(0, round(exp_home))
    pred_a = max(0, round(exp_away))

    return {
        "model": "xgboost_analytical",
        "prob_home_win": round(p_home, 4),
        "prob_draw": round(p_draw, 4),
        "prob_away_win": round(p_away, 4),
        "predicted_home_score": pred_h,
        "predicted_away_score": pred_a,
        "confidence": round(max(p_home, p_draw, p_away), 4),
    }


def predict(features: XGBFeatures) -> dict[str, Any]:
    vec = features_to_vector(features).reshape(1, -1)

    if XGBOOST_AVAILABLE and os.path.exists(MODEL_PATH):
        try:
            model = xgb.Booster()
            model.load_model(MODEL_PATH)
            dmatrix = xgb.DMatrix(vec)
            proba = model.predict(dmatrix)[0]  # [p_home, p_draw, p_away]
            p_home, p_draw, p_away = float(proba[0]), float(proba[1]), float(proba[2])
            pred_h = max(0, round(features.home_xg_last5 * (0.6 + p_home * 0.4)))
            pred_a = max(0, round(features.away_xg_last5 * (0.6 + p_away * 0.4)))
            return {
                "model": "xgboost",
                "prob_home_win": round(p_home, 4),
                "prob_draw": round(p_draw, 4),
                "prob_away_win": round(p_away, 4),
                "predicted_home_score": pred_h,
                "predicted_away_score": pred_a,
                "confidence": round(max(p_home, p_draw, p_away), 4),
            }
        except Exception:
            pass

    return _analytical_fallback(features)
