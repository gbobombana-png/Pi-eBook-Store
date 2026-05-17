"""
Modèle de Poisson pour la prédiction footballistique.
Chaque équipe marque selon une loi de Poisson paramètrée par ses forces
d'attaque/défense relatives à la ligue.
"""
import math
from itertools import product
from dataclasses import dataclass


MAX_GOALS = 10    # on ne calcule pas au-delà
HOME_ADV = 1.25   # facteur avantage domicile par défaut


@dataclass
class PoissonPrediction:
    lambda_home: float
    lambda_away: float
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    prob_over25: float
    prob_btts: float
    score_matrix: dict[tuple[int, int], float]  # (home, away) → prob
    most_likely_score: tuple[int, int]
    most_likely_score_prob: float
    confidence: float


def poisson_prob(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def compute_score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = MAX_GOALS,
) -> dict[tuple[int, int], float]:
    matrix = {}
    for h, a in product(range(max_goals + 1), repeat=2):
        matrix[(h, a)] = poisson_prob(h, lambda_home) * poisson_prob(a, lambda_away)
    return matrix


def predict(
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    league_avg_home: float = 1.5,
    league_avg_away: float = 1.2,
    home_advantage: float = HOME_ADV,
) -> PoissonPrediction:
    """
    Calcule les probabilités Poisson.

    Formule Dixon-Coles:
      λ_home = attack_home × defense_away × league_avg_home × home_adv
      λ_away = attack_away × defense_home × league_avg_away
    """
    lambda_home = max(0.1, home_attack * away_defense * league_avg_home * home_advantage)
    lambda_away = max(0.1, away_attack * home_defense * league_avg_away)

    matrix = compute_score_matrix(lambda_home, lambda_away)

    p_home = sum(p for (h, a), p in matrix.items() if h > a)
    p_draw = sum(p for (h, a), p in matrix.items() if h == a)
    p_away = sum(p for (h, a), p in matrix.items() if h < a)

    p_over25 = sum(p for (h, a), p in matrix.items() if h + a > 2.5)
    p_btts   = sum(p for (h, a), p in matrix.items() if h >= 1 and a >= 1)

    best_score = max(matrix, key=matrix.get)
    best_prob  = matrix[best_score]

    # Confiance ≈ max(p_home, p_draw, p_away) normalisé
    conf = max(p_home, p_draw, p_away)

    return PoissonPrediction(
        lambda_home=round(lambda_home, 3),
        lambda_away=round(lambda_away, 3),
        prob_home_win=round(p_home, 4),
        prob_draw=round(p_draw, 4),
        prob_away_win=round(p_away, 4),
        prob_over25=round(p_over25, 4),
        prob_btts=round(p_btts, 4),
        score_matrix=matrix,
        most_likely_score=best_score,
        most_likely_score_prob=round(best_prob, 4),
        confidence=round(conf, 4),
    )


def to_dict(pred: PoissonPrediction) -> dict:
    return {
        "model": "poisson",
        "lambda_home": pred.lambda_home,
        "lambda_away": pred.lambda_away,
        "prob_home_win": pred.prob_home_win,
        "prob_draw": pred.prob_draw,
        "prob_away_win": pred.prob_away_win,
        "prob_over25": pred.prob_over25,
        "prob_btts": pred.prob_btts,
        "most_likely_score": f"{pred.most_likely_score[0]}:{pred.most_likely_score[1]}",
        "most_likely_score_prob": pred.most_likely_score_prob,
        "confidence": pred.confidence,
        "top_5_scores": sorted(
            [(f"{h}:{a}", round(p * 100, 2)) for (h, a), p in pred.score_matrix.items()],
            key=lambda x: -x[1],
        )[:5],
    }
