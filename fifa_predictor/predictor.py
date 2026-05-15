"""
Moteur de prédiction expert — EA FC Virtual Matches
Combine: Poisson + Dixon-Coles + Monte Carlo + Elo + Attributs par mode
"""
import math
import random
from team_data import TEAM_RATINGS, get_team
from elo import get_elo, expected_score, elo_win_probability

# ─── Paramètres de base ─────────────────────────────────────────────
BASE_GOALS_NORMAL = 2.65   # buts/match moyen en virtuel 11v11
BASE_GOALS_5X5    = 4.80   # buts/match moyen en virtuel 5v5 Rush
HOME_ADV          = 0.12   # léger avantage organisateur
ELO_WEIGHT        = 0.25   # poids de l'Elo dans le calcul final (25%)
STATS_WEIGHT      = 0.75   # poids des stats EA FC (75%)

# ─── Poids des attributs selon le mode ──────────────────────────────
MODE_WEIGHTS = {
    "normal": {
        "sho": 0.28, "pas": 0.22, "dri": 0.20,
        "pac": 0.15, "phy": 0.10, "def_opp": 0.05
    },
    "5x5": {
        "pac": 0.32, "dri": 0.30, "sho": 0.22,
        "pas": 0.10, "phy": 0.06, "def_opp": 0.00
    },
    "rush": {  # alias 5x5
        "pac": 0.32, "dri": 0.30, "sho": 0.22,
        "pas": 0.10, "phy": 0.06, "def_opp": 0.00
    },
}

# ─── Correction Dixon-Coles ──────────────────────────────────────────
# Ajuste les probabilités des scores faibles (0-0, 1-0, 0-1, 1-1)
DC_RHO = -0.13   # corrélation négative entre buts domicile et extérieur


def _dc_correction(i, j, mu_a, mu_b, rho=DC_RHO):
    if i == 0 and j == 0:
        return 1 - mu_a * mu_b * rho
    elif i == 1 and j == 0:
        return 1 + mu_b * rho
    elif i == 0 and j == 1:
        return 1 + mu_a * rho
    elif i == 1 and j == 1:
        return 1 - rho
    return 1.0


def _poisson(lam, k):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(min(k, 20))


# ─── Calcul des xG ──────────────────────────────────────────────────

def _attack_index(stats, mode):
    """Score d'attaque normalisé selon les attributs importants pour ce mode"""
    w = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["normal"])
    score = (
        stats["sho"] * w["sho"] +
        stats["pas"] * w["pas"] +
        stats["dri"] * w["dri"] +
        stats["pac"] * w["pac"] +
        stats["phy"] * w["phy"]
    )
    return score / 75.0  # normaliser autour de 1.0


def _defense_index(stats, mode):
    """Résistance défensive — inverse de la faiblesse"""
    # En 5v5, la défense compte moins (peu de défenseurs)
    def_w = 0.60 if mode == "normal" else 0.35
    gk_w  = 0.40 if mode == "normal" else 0.65  # gardien plus crucial en 5v5
    defense = stats["def"] * def_w + stats["gk"] * gk_w
    return defense / 75.0


def _star_player_bonus(stats, mode):
    """Bonus si l'équipe a un joueur star exceptionnel (>90 rating)"""
    star = stats.get("star", 80)
    if star >= 92:
        return 0.08 if mode == "normal" else 0.12  # plus d'impact en 5v5
    elif star >= 89:
        return 0.05 if mode == "normal" else 0.08
    elif star >= 87:
        return 0.02
    return 0.0


def expected_goals(stats_a, stats_b, mode="normal", home_a=False):
    base = BASE_GOALS_5X5 if mode in ("5x5", "rush") else BASE_GOALS_NORMAL

    att_a = _attack_index(stats_a, mode)
    att_b = _attack_index(stats_b, mode)
    def_a = _defense_index(stats_a, mode)
    def_b = _defense_index(stats_b, mode)
    star_bonus_a = _star_player_bonus(stats_a, mode)
    star_bonus_b = _star_player_bonus(stats_b, mode)

    # xG = base × force_attaque × faiblesse_adverse
    # faiblesse_adverse = 2.0 - defense_index (plus c'est bas = plus faible)
    xg_a = base * att_a * (2.0 - def_b) * (1 + star_bonus_a)
    xg_b = base * att_b * (2.0 - def_a) * (1 + star_bonus_b)

    if home_a:
        xg_a *= (1 + HOME_ADV)
        xg_b *= (1 - HOME_ADV * 0.6)

    return round(max(xg_a, 0.3), 3), round(max(xg_b, 0.3), 3)


# ─── Matrice de scores ───────────────────────────────────────────────

def score_matrix(xg_a, xg_b, max_goals=8):
    matrix = {}
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = _poisson(xg_a, i) * _poisson(xg_b, j)
            p *= _dc_correction(i, j, xg_a, xg_b)
            matrix[(i, j)] = max(p, 0.0)
    # Renormaliser
    total = sum(matrix.values())
    return {k: v / total for k, v in matrix.items()}


# ─── Monte Carlo ─────────────────────────────────────────────────────

def monte_carlo(xg_a, xg_b, n=50000):
    """Simule N matchs, retourne probas victoire/nul/défaite + scores fréquents"""
    wins_a = wins_b = draws = 0
    score_counts = {}

    for _ in range(n):
        g_a = 0
        g_b = 0
        # Simuler but par but avec distribution de Poisson
        lam_a, lam_b = xg_a, xg_b
        # Méthode Knuth pour Poisson
        L_a = math.exp(-lam_a)
        L_b = math.exp(-lam_b)
        p, k = 1.0, 0
        while p > L_a:
            p *= random.random()
            k += 1
        g_a = k - 1

        p, k = 1.0, 0
        while p > L_b:
            p *= random.random()
            k += 1
        g_b = k - 1

        if g_a > g_b:
            wins_a += 1
        elif g_b > g_a:
            wins_b += 1
        else:
            draws += 1

        score_counts[(g_a, g_b)] = score_counts.get((g_a, g_b), 0) + 1

    top = sorted(score_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "prob_a": wins_a / n,
        "prob_b": wins_b / n,
        "prob_d": draws  / n,
        "top_scores": [(s, c / n) for s, c in top],
    }


# ─── Fusion Elo + Stats ──────────────────────────────────────────────

def _blend_probabilities(prob_stats, prob_elo):
    """Combine les probabilités stats EA FC et Elo avec pondération"""
    return (
        prob_stats * STATS_WEIGHT + prob_elo * ELO_WEIGHT,
    )[0]


# ─── Prédiction principale ───────────────────────────────────────────

def predict_match(team_a, team_b, mode="normal", home_a=False):
    name_a, stats_a = get_team(team_a)
    name_b, stats_b = get_team(team_b)

    if not stats_a:
        return {"error": f"Équipe '{team_a}' introuvable. Lance --list pour voir les équipes."}
    if not stats_b:
        return {"error": f"Équipe '{team_b}' introuvable."}

    mode = mode.lower()
    if mode == "penalty":
        return _predict_penalty(stats_a, stats_b, name_a, name_b)

    # 1. Expected Goals
    xg_a, xg_b = expected_goals(stats_a, stats_b, mode, home_a)

    # 2. Matrice de scores (Poisson + Dixon-Coles)
    matrix = score_matrix(xg_a, xg_b)

    # 3. Monte Carlo (50 000 simulations)
    mc = monte_carlo(xg_a, xg_b, n=50000)

    # 4. Elo
    elo_a = get_elo(name_a)
    elo_b = get_elo(name_b)
    elo_p_a = expected_score(elo_a, elo_b)
    elo_p_b = 1 - elo_p_a

    # 5. Fusion stats + Elo pour les probas finales
    raw_prob_a = sum(v for (i, j), v in matrix.items() if i > j)
    raw_prob_b = sum(v for (i, j), v in matrix.items() if j > i)
    raw_prob_d = sum(v for (i, j), v in matrix.items() if i == j)

    final_prob_a = raw_prob_a * STATS_WEIGHT + elo_p_a * ELO_WEIGHT
    final_prob_b = raw_prob_b * STATS_WEIGHT + elo_p_b * ELO_WEIGHT
    # Renormaliser en incluant le nul
    total = final_prob_a + final_prob_b + raw_prob_d
    final_prob_a /= total
    final_prob_b /= total
    final_prob_d  = raw_prob_d / total

    # 6. Top scores (combiner matrice + Monte Carlo)
    combined_scores = {}
    for (s, p) in mc["top_scores"]:
        mp = matrix.get(s, 0)
        combined_scores[s] = p * 0.6 + mp * 0.4  # MC 60%, Poisson 40%

    top_scores = sorted(combined_scores.items(), key=lambda x: -x[1])[:8]
    best_score = top_scores[0][0] if top_scores else (1, 1)
    best_prob  = top_scores[0][1] if top_scores else 0

    return {
        "team_a":        name_a,
        "team_b":        name_b,
        "mode":          mode,
        "rating_a":      stats_a["ovr"],
        "rating_b":      stats_b["ovr"],
        "star_a":        f"{stats_a['star_name']} ({stats_a['star']})",
        "star_b":        f"{stats_b['star_name']} ({stats_b['star']})",
        "xg_a":          round(xg_a, 2),
        "xg_b":          round(xg_b, 2),
        "elo_a":         elo_a,
        "elo_b":         elo_b,
        "prob_a_wins":   round(final_prob_a * 100, 1),
        "prob_draw":     round(final_prob_d  * 100, 1),
        "prob_b_wins":   round(final_prob_b * 100, 1),
        "mc_prob_a":     round(mc["prob_a"] * 100, 1),
        "mc_prob_b":     round(mc["prob_b"] * 100, 1),
        "predicted_score": f"{best_score[0]}-{best_score[1]}",
        "score_probability": round(best_prob * 100, 1),
        "top_scores":    [(f"{s[0]}-{s[1]}", round(p * 100, 1)) for s, p in top_scores[:6]],
        "recommendation": _recommend(final_prob_a, final_prob_b, final_prob_d, name_a, name_b),
        "confidence":    _confidence(final_prob_a, final_prob_b, final_prob_d, stats_a, stats_b, elo_a, elo_b),
        "analysis":      _analysis(stats_a, stats_b, name_a, name_b, mode, xg_a, xg_b),
    }


def _predict_penalty(stats_a, stats_b, name_a, name_b):
    # Probabilité de marquer un penalty : sho/110 modifié par gk adverse
    p_score_a = (stats_a["sho"] / 110) * (1 - (stats_b["gk"] - 75) / 200)
    p_score_b = (stats_b["sho"] / 110) * (1 - (stats_a["gk"] - 75) / 200)
    p_score_a = max(0.55, min(0.92, p_score_a))
    p_score_b = max(0.55, min(0.92, p_score_b))

    # Intégrer l'Elo dans les probabilités de tir
    elo_a = get_elo(name_a)
    elo_b = get_elo(name_b)
    elo_factor = expected_score(elo_a, elo_b)  # 0..1
    p_score_a = p_score_a * 0.80 + elo_factor * 0.20
    p_score_b = p_score_b * 0.80 + (1 - elo_factor) * 0.20

    N = 50000
    wins_a = wins_b = 0
    score_counts = {}

    for _ in range(N):
        # Phase 5 tirs chacun
        sa = sum(1 for _ in range(5) if random.random() < p_score_a)
        sb = sum(1 for _ in range(5) if random.random() < p_score_b)

        # Sudden death si égalité (rounds infinis comme dans FC25)
        extra = 0
        while sa == sb:
            extra += 1
            if random.random() < p_score_a:
                sa += 1
            if random.random() < p_score_b:
                sb += 1
            # Si encore égalité après ce round, continuer (déjà géré par while)
            if sa != sb:
                break

        key = (sa, sb)
        score_counts[key] = score_counts.get(key, 0) + 1

        if sa > sb:
            wins_a += 1
        else:
            wins_b += 1

    final_pa = wins_a / N
    final_pb = wins_b / N

    # Top scores probables
    top_raw = sorted(score_counts.items(), key=lambda x: -x[1])[:8]
    top_scores = [(f"{s[0]}-{s[1]}", round(c / N * 100, 1)) for s, c in top_raw]

    winner = name_a if final_pa > final_pb else name_b
    confidence = "HAUTE" if abs(final_pa - final_pb) > 0.10 else \
                 "MOYENNE" if abs(final_pa - final_pb) > 0.04 else "FAIBLE — très serré"

    return {
        "team_a": name_a, "team_b": name_b, "mode": "penalty",
        "rating_a": stats_a["ovr"], "rating_b": stats_b["ovr"],
        "star_a": f"{stats_a['star_name']} ({stats_a['star']})",
        "star_b": f"{stats_b['star_name']} ({stats_b['star']})",
        "xg_a": "-", "xg_b": "-",
        "elo_a": elo_a, "elo_b": elo_b,
        "prob_a_wins": round(final_pa * 100, 1),
        "prob_draw": 0.0,
        "prob_b_wins": round(final_pb * 100, 1),
        "mc_prob_a": round(final_pa * 100, 1),
        "mc_prob_b": round(final_pb * 100, 1),
        "predicted_score": top_scores[0][0] if top_scores else "5-4",
        "score_probability": top_scores[0][1] if top_scores else 0,
        "top_scores": [(s, p) for s, p in top_scores],
        "recommendation": f"Victoire {winner} aux tirs au but",
        "confidence": confidence,
        "analysis": [
            f"Prob. marquer: {name_a} {p_score_a*100:.0f}% | {name_b} {p_score_b*100:.0f}% par penalty",
            f"Shooting {name_a}: {stats_a['sho']} | {name_b}: {stats_b['sho']}",
            f"Gardien {name_a}: {stats_a['gk']} | {name_b}: {stats_b['gk']}",
            f"Elo {name_a}: {elo_a:.0f} | {name_b}: {elo_b:.0f}",
        ],
    }


def _recommend(pa, pb, pd, na, nb):
    if pa > pb and pa > pd:
        return f"Victoire {na} ({pa*100:.0f}%)"
    elif pb > pa and pb > pd:
        return f"Victoire {nb} ({pb*100:.0f}%)"
    else:
        return f"Match nul ({pd*100:.0f}%) ou {na} ({pa*100:.0f}%)"


def _confidence(pa, pb, pd, sa, sb, elo_a, elo_b):
    ovr_diff = abs(sa["ovr"] - sb["ovr"])
    elo_diff = abs(elo_a - elo_b)
    max_p = max(pa, pb)
    if ovr_diff >= 5 and max_p > 0.55 and elo_diff > 50:
        return "HAUTE"
    elif ovr_diff >= 3 and max_p > 0.48:
        return "MOYENNE"
    else:
        return "FAIBLE — match équilibré"


def _analysis(sa, sb, na, nb, mode, xg_a, xg_b):
    lines = []
    # Avantage par attribut
    attrs = [("pac","Vitesse"),("sho","Tir"),("pas","Passe"),("dri","Dribble"),("phy","Physique"),("gk","Gardien")]
    for attr, label in attrs:
        diff = sa[attr] - sb[attr]
        if diff >= 3:
            lines.append(f"{label}: {na} +{diff} ({sa[attr]} vs {sb[attr]})")
        elif diff <= -3:
            lines.append(f"{label}: {nb} +{abs(diff)} ({sb[attr]} vs {sa[attr]})")

    if mode in ("5x5", "rush"):
        if sa["pac"] > sb["pac"]:
            lines.append(f"Avantage vitesse en 5v5: {na} (PAC {sa['pac']} vs {sb['pac']})")
        if sa["dri"] > sb["dri"]:
            lines.append(f"Avantage dribble en 5v5: {na} (DRI {sa['dri']} vs {sb['dri']})")

    if abs(xg_a - xg_b) < 0.3:
        lines.append("Match très équilibré selon les xG")
    return lines[:5]
