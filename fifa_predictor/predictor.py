import math
from team_data import TEAM_RATINGS, get_team

# Moyenne de buts par match en virtuel EA FC (calibrée sur données historiques)
BASE_GOALS = 2.7   # buts/match en moyenne
HOME_ADV   = 0.15  # léger avantage domicile dans les tournois


def _attack_strength(team_stats, base_avg=75):
    """Force d'attaque relative"""
    return team_stats["att"] / base_avg


def _defense_weakness(team_stats, base_avg=75):
    """Faiblesse défensive (inverse de la défense)"""
    return (150 - team_stats["def"]) / base_avg


def expected_goals(team_a, team_b, home_a=False):
    """
    Calcule les expected goals (xG) de chaque équipe
    Méthode Dixon-Coles adaptée pour EA FC virtuel
    """
    _, stats_a = get_team(team_a) if isinstance(team_a, str) else (None, team_a)
    _, stats_b = get_team(team_b) if isinstance(team_b, str) else (None, team_b)

    if not stats_a or not stats_b:
        return None, None

    # xG = base * force_attaque_A * faiblesse_défense_B
    xg_a = BASE_GOALS * _attack_strength(stats_a) * _defense_weakness(stats_b)
    xg_b = BASE_GOALS * _attack_strength(stats_b) * _defense_weakness(stats_a)

    if home_a:
        xg_a *= (1 + HOME_ADV)
        xg_b *= (1 - HOME_ADV * 0.5)

    # Ajustement pour les matchs virtuels (légèrement plus de buts)
    xg_a = round(xg_a, 3)
    xg_b = round(xg_b, 3)

    return xg_a, xg_b


def poisson_prob(lam, k):
    """P(X=k) pour une loi de Poisson de paramètre lambda"""
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def score_matrix(xg_a, xg_b, max_goals=7):
    """Matrice de probabilité pour chaque score (0-0 à max-max)"""
    matrix = {}
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            matrix[(i, j)] = poisson_prob(xg_a, i) * poisson_prob(xg_b, j)
    return matrix


def predict_match(team_a, team_b, mode="normal", home_a=False):
    """
    Prédit le résultat d'un match virtuel EA FC

    Modes:
    - normal  : match standard 90min (11v11)
    - 5x5     : match Rush 5v5 (plus de buts)
    - penalty : tirs au but
    """
    name_a, stats_a = get_team(team_a) if isinstance(team_a, str) else (team_a, team_a)
    name_b, stats_b = get_team(team_b) if isinstance(team_b, str) else (team_b, team_b)

    if not stats_a:
        return {"error": f"Équipe '{team_a}' non trouvée. Utilise --list pour voir les équipes disponibles."}
    if not stats_b:
        return {"error": f"Équipe '{team_b}' non trouvée."}

    # Ajustement selon le mode
    global BASE_GOALS
    original = BASE_GOALS
    if mode == "5x5":
        BASE_GOALS = 4.5   # 5v5 = beaucoup plus de buts
    elif mode == "penalty":
        return _predict_penalty(stats_a, stats_b, name_a, name_b)

    xg_a, xg_b = expected_goals(stats_a, stats_b, home_a)
    BASE_GOALS = original

    matrix = score_matrix(xg_a, xg_b)

    # Probabilités victoire/nul/défaite
    prob_a = sum(v for (i, j), v in matrix.items() if i > j)
    prob_b = sum(v for (i, j), v in matrix.items() if j > i)
    prob_d = sum(v for (i, j), v in matrix.items() if i == j)

    # Top 10 scores les plus probables
    top_scores = sorted(matrix.items(), key=lambda x: -x[1])[:10]

    # Score le plus probable
    best_score = top_scores[0][0]
    best_prob  = top_scores[0][1]

    # Score le plus probable parmi les scores "réalistes" (max 5 buts par équipe)
    realistic = [(s, p) for s, p in top_scores if s[0] <= 5 and s[1] <= 5]

    result = {
        "team_a":        name_a or team_a,
        "team_b":        name_b or team_b,
        "mode":          mode,
        "xg_a":          round(xg_a, 2),
        "xg_b":          round(xg_b, 2),
        "rating_a":      stats_a["ovr"],
        "rating_b":      stats_b["ovr"],
        "prob_a_wins":   round(prob_a * 100, 1),
        "prob_draw":     round(prob_d * 100, 1),
        "prob_b_wins":   round(prob_b * 100, 1),
        "predicted_score": f"{best_score[0]}-{best_score[1]}",
        "score_probability": round(best_prob * 100, 1),
        "top_5_scores":  [(f"{s[0]}-{s[1]}", round(p * 100, 1)) for s, p in realistic[:5]],
        "recommendation": _recommend(prob_a, prob_b, prob_d, name_a or team_a, name_b or team_b),
        "confidence":    _confidence_level(prob_a, prob_b, stats_a, stats_b),
    }
    return result


def _predict_penalty(stats_a, stats_b, name_a, name_b):
    """Prédiction tirs au but basée sur les stats globales"""
    # En penalty, l'avantage est basé sur l'overall et légèrement sur l'attaque
    score_a = stats_a["ovr"] * 0.4 + stats_a["att"] * 0.6
    score_b = stats_b["ovr"] * 0.4 + stats_b["att"] * 0.6
    total = score_a + score_b
    prob_a = score_a / total
    prob_b = score_b / total

    return {
        "team_a":        name_a,
        "team_b":        name_b,
        "mode":          "penalty",
        "rating_a":      stats_a["ovr"],
        "rating_b":      stats_b["ovr"],
        "prob_a_wins":   round(prob_a * 100, 1),
        "prob_b_wins":   round(prob_b * 100, 1),
        "prob_draw":     0.0,
        "predicted_score": "Pas applicable",
        "top_5_scores":  [],
        "recommendation": f"{name_a} favori" if prob_a > prob_b else f"{name_b} favori",
        "confidence":    "MEDIUM",
    }


def _recommend(prob_a, prob_b, prob_d, name_a, name_b):
    max_p = max(prob_a, prob_b, prob_d)
    if max_p == prob_a:
        return f"Victoire {name_a} ({prob_a*100:.0f}%)"
    elif max_p == prob_b:
        return f"Victoire {name_b} ({prob_b*100:.0f}%)"
    else:
        return f"Match nul ({prob_d*100:.0f}%)"


def _confidence_level(prob_a, prob_b, stats_a, stats_b):
    diff = abs(stats_a["ovr"] - stats_b["ovr"])
    max_prob = max(prob_a, prob_b)
    if diff >= 5 and max_prob > 0.55:
        return "HAUTE"
    elif diff >= 3 and max_prob > 0.45:
        return "MOYENNE"
    else:
        return "FAIBLE"
