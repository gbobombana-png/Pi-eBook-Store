"""
Système Elo dynamique — se met à jour avec les vrais résultats
Plus l'écart d'Elo est grand, moins de points gagnés si le favori gagne
"""
import json, os

ELO_FILE = os.path.join(os.path.dirname(__file__), "elo_ratings.json")
K = 32        # Facteur K standard
K_BIG = 40   # Facteur K pour les grosses différences de score
BASE = 1500   # Elo de départ


def _load():
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE) as f:
            return json.load(f)
    return {}


def _save(ratings):
    with open(ELO_FILE, "w") as f:
        json.dump(ratings, f, indent=2)


def get_elo(team):
    ratings = _load()
    return ratings.get(team, BASE)


def get_all():
    return _load()


def expected_score(elo_a, elo_b):
    """Probabilité de victoire de A selon l'Elo"""
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def update(team_a, score_a, team_b, score_b):
    """
    Met à jour l'Elo après un vrai résultat
    Appelle cette fonction après chaque match observé
    """
    ratings = _load()
    elo_a = ratings.get(team_a, BASE)
    elo_b = ratings.get(team_b, BASE)

    exp_a = expected_score(elo_a, elo_b)
    exp_b = 1 - exp_a

    # Résultat réel (1=victoire, 0.5=nul, 0=défaite)
    if score_a > score_b:
        result_a, result_b = 1.0, 0.0
    elif score_a < score_b:
        result_a, result_b = 0.0, 1.0
    else:
        result_a, result_b = 0.5, 0.5

    # K plus grand si la différence de buts est importante
    goal_diff = abs(score_a - score_b)
    k = K_BIG if goal_diff >= 3 else K

    new_elo_a = round(elo_a + k * (result_a - exp_a), 1)
    new_elo_b = round(elo_b + k * (result_b - exp_b), 1)

    ratings[team_a] = new_elo_a
    ratings[team_b] = new_elo_b
    _save(ratings)

    return {
        "team_a": team_a, "old_a": elo_a, "new_a": new_elo_a,
        "team_b": team_b, "old_b": elo_b, "new_b": new_elo_b,
    }


def elo_win_probability(team_a, team_b):
    """Probabilité de victoire basée sur Elo"""
    elo_a = get_elo(team_a)
    elo_b = get_elo(team_b)
    p_a = expected_score(elo_a, elo_b)
    return p_a, 1 - p_a
