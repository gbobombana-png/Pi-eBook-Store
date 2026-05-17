"""
Réseau de neurones pour la prédiction footballistique.
Architecture: MLP multi-têtes (outcome + score + marchés).
En fallback (PyTorch non disponible), utilise un perceptron analytique.
"""
import os
import numpy as np
from typing import Any

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

MODEL_PATH = os.path.join(os.path.dirname(__file__), "weights", "nn_football.pt")

# ── Architecture réseau ───────────────────────────────────────────────────────

if TORCH_AVAILABLE:
    class FootballNet(nn.Module):
        """
        Réseau multi-têtes:
          - head_outcome: [p_home, p_draw, p_away]
          - head_goals_home: λ_home (Poisson)
          - head_goals_away: λ_away
          - head_markets: [p_over25, p_btts]
        """
        def __init__(self, input_dim: int = 26):
            super().__init__()
            self.backbone = nn.Sequential(
                nn.Linear(input_dim, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, 256),
                nn.BatchNorm1d(256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, 64),
                nn.ReLU(),
            )
            self.head_outcome = nn.Sequential(nn.Linear(64, 3), nn.Softmax(dim=1))
            self.head_goals_home = nn.Sequential(nn.Linear(64, 1), nn.Softplus())
            self.head_goals_away = nn.Sequential(nn.Linear(64, 1), nn.Softplus())
            self.head_markets   = nn.Sequential(nn.Linear(64, 2), nn.Sigmoid())

        def forward(self, x):
            feat = self.backbone(x)
            return {
                "outcome": self.head_outcome(feat),
                "goals_home": self.head_goals_home(feat).squeeze(1),
                "goals_away": self.head_goals_away(feat).squeeze(1),
                "markets": self.head_markets(feat),
            }


def _softmax(v: list[float]) -> list[float]:
    e = [2.718281828 ** x for x in v]
    s = sum(e)
    return [x / s for x in e]


def _analytical_nn_fallback(vec: np.ndarray) -> dict[str, Any]:
    """
    Perceptron simplifié: simule le comportement attendu du réseau.
    Poids calibrés sur des données footballistiques synthétiques.
    """
    # Indices correspondant à features_to_vector de xgboost_model.py
    home_goals  = vec[0]; away_goals  = vec[1]
    home_conc   = vec[2]; away_conc   = vec[3]
    home_xg     = vec[4]; away_xg     = vec[5]
    home_form   = vec[8]; away_form   = vec[9]
    h2h_hw_rate = vec[11]
    odds_h      = vec[14]; odds_d = vec[15]; odds_a = vec[16]
    home_adv    = vec[18]
    xg_h_rec    = vec[21]; xg_a_rec = vec[22]

    # Couche cachée simplifiée (3 neurones)
    h1 = max(0, 0.3*(home_goals - away_conc) + 0.2*home_form + 0.25*odds_h + 0.15*home_adv + 0.1*h2h_hw_rate)
    h2 = max(0, 0.3*(away_goals - home_conc) + 0.2*away_form + 0.25*odds_a + 0.15*(1-home_adv))
    h3 = max(0, 0.4*odds_d + 0.3*(1 - abs(h1 - h2)) + 0.3*0.28)

    raw = [h1, h3, h2]
    p_home, p_draw, p_away = _softmax(raw)

    # Prédiction buts via xG ajusté
    pred_h = max(0, round(xg_h_rec * (0.5 + p_home * 0.5)))
    pred_a = max(0, round(xg_a_rec * (0.5 + p_away * 0.5)))

    # Marchés
    p_over25 = 1 - np.exp(-(xg_h_rec + xg_a_rec) / 1.8)
    p_btts = (1 - np.exp(-xg_h_rec)) * (1 - np.exp(-xg_a_rec))

    return {
        "model": "neural_analytical",
        "prob_home_win": round(p_home, 4),
        "prob_draw": round(p_draw, 4),
        "prob_away_win": round(p_away, 4),
        "predicted_home_score": pred_h,
        "predicted_away_score": pred_a,
        "prob_over25": round(float(p_over25), 4),
        "prob_btts": round(float(p_btts), 4),
        "confidence": round(max(p_home, p_draw, p_away), 4),
    }


def predict(feature_vector: np.ndarray) -> dict[str, Any]:
    """
    feature_vector: vecteur numpy 26-dim généré par xgboost_model.features_to_vector()
    """
    if TORCH_AVAILABLE and os.path.exists(MODEL_PATH):
        try:
            model = FootballNet(input_dim=len(feature_vector))
            model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
            model.eval()
            with torch.no_grad():
                t = torch.tensor(feature_vector, dtype=torch.float32).unsqueeze(0)
                out = model(t)
                outcome  = out["outcome"].squeeze().numpy()
                goals_h  = float(out["goals_home"][0])
                goals_a  = float(out["goals_away"][0])
                markets  = out["markets"].squeeze().numpy()

            return {
                "model": "neural_network",
                "prob_home_win": round(float(outcome[0]), 4),
                "prob_draw":     round(float(outcome[1]), 4),
                "prob_away_win": round(float(outcome[2]), 4),
                "predicted_home_score": max(0, round(goals_h)),
                "predicted_away_score": max(0, round(goals_a)),
                "prob_over25": round(float(markets[0]), 4),
                "prob_btts":   round(float(markets[1]), 4),
                "confidence":  round(float(max(outcome)), 4),
            }
        except Exception:
            pass

    return _analytical_nn_fallback(feature_vector)
