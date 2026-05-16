"""
Multi-dimensional match analysis engine.
Produces a score (0-100) for each dimension and a final weighted total.
"""
from dataclasses import dataclass, field
from typing import Optional
import math

WEIGHTS = {
    "form":        0.22,
    "psychology":  0.13,
    "squad":       0.18,
    "tactics":     0.15,
    "advanced":    0.12,
    "odds":        0.10,
    "ml":          0.10,
}


@dataclass
class MatchContext:
    # Team basic info
    home_name: str
    away_name: str

    # Form — last 5/10 (e.g. "WWDWL")
    home_form5: str = "WWWWD"
    away_form5: str = "WDLWL"
    home_form10: str = "WWWWDWWDWL"
    away_form10: str = "WDLWLWDLWW"

    # Goals stats
    home_goals_scored_avg: float = 1.8
    home_goals_conceded_avg: float = 1.1
    away_goals_scored_avg: float = 1.4
    away_goals_conceded_avg: float = 1.5

    # xG
    home_xg_avg: float = 1.9
    away_xg_avg: float = 1.3
    home_xga_avg: float = 1.0
    away_xga_avg: float = 1.6

    # Shooting
    home_shots_on_avg: float = 5.2
    away_shots_on_avg: float = 3.8

    # Possession
    home_possession_avg: float = 58.0
    away_possession_avg: float = 48.0

    # Corners
    home_corners_avg: float = 6.1
    away_corners_avg: float = 4.2

    # BTTS / Over history
    home_btts_pct: float = 55.0
    away_btts_pct: float = 60.0
    home_over25_pct: float = 62.0
    away_over25_pct: float = 58.0

    # Standings context
    home_rank: int = 3
    away_rank: int = 8
    home_points: int = 65
    away_points: int = 48
    total_teams: int = 20
    rounds_remaining: int = 5

    # H2H (last 10)
    h2h_home_wins: int = 5
    h2h_draws: int = 2
    h2h_away_wins: int = 3
    h2h_avg_goals: float = 2.8
    h2h_btts_pct: float = 60.0

    # Squad
    home_key_players_missing: int = 0
    away_key_players_missing: int = 1
    home_total_injured: int = 1
    away_total_injured: int = 3
    home_suspended: int = 0
    away_suspended: int = 1

    # Fatigue (days since last match)
    home_days_rest: int = 7
    away_days_rest: int = 4

    # Motivation
    home_title_race: bool = False
    home_relegation_fight: bool = False
    home_european_race: bool = True
    away_title_race: bool = False
    away_relegation_fight: bool = True
    away_european_race: bool = False
    is_derby: bool = False
    is_cup: bool = False

    # Weather
    temperature: float = 15.0
    rain: bool = False
    wind_kmh: float = 20.0

    # Odds
    odds_home: Optional[float] = None
    odds_draw: Optional[float] = None
    odds_away: Optional[float] = None
    odds_over25: Optional[float] = None
    odds_btts_yes: Optional[float] = None

    # ML probability (set externally)
    ml_prob_home: float = 0.45
    ml_prob_draw: float = 0.27
    ml_prob_away: float = 0.28


@dataclass
class AnalysisResult:
    score_form: float = 0.0
    score_psychology: float = 0.0
    score_squad: float = 0.0
    score_tactics: float = 0.0
    score_advanced: float = 0.0
    score_odds: float = 0.0
    score_ml: float = 0.0
    score_total: float = 0.0

    prob_home: float = 0.0
    prob_draw: float = 0.0
    prob_away: float = 0.0
    prob_btts: float = 0.0
    prob_over25: float = 0.0

    best_bet: str = ""
    best_odds: float = 0.0
    confidence: int = 0
    value_edge: float = 0.0
    reasoning: str = ""
    risks: str = ""
    key_stats: dict = field(default_factory=dict)


def _form_points(form: str) -> float:
    pts = {"W": 3, "D": 1, "L": 0}
    total = sum(pts.get(c, 0) for c in form.upper())
    max_pts = len(form) * 3
    return total / max_pts if max_pts > 0 else 0.5


def analyze(ctx: MatchContext) -> AnalysisResult:
    r = AnalysisResult()

    # ── 1. FORM ──────────────────────────────────────────────────────────────
    home_f5 = _form_points(ctx.home_form5)
    away_f5 = _form_points(ctx.away_form5)
    home_f10 = _form_points(ctx.home_form10)
    away_f10 = _form_points(ctx.away_form10)

    home_form_score = (home_f5 * 0.6 + home_f10 * 0.4) * 100
    away_form_score = (away_f5 * 0.6 + away_f10 * 0.4) * 100
    r.score_form = (home_form_score - away_form_score + 100) / 2  # 0-100, 50=equal

    # xG dominance
    xg_ratio = ctx.home_xg_avg / max(ctx.away_xg_avg, 0.1)
    xg_score = min(100, max(0, 50 + (xg_ratio - 1) * 30))
    r.score_form = r.score_form * 0.6 + xg_score * 0.4

    # ── 2. PSYCHOLOGY ────────────────────────────────────────────────────────
    home_motive = 50.0
    away_motive = 50.0

    if ctx.home_title_race:       home_motive += 20
    if ctx.home_european_race:    home_motive += 10
    if ctx.home_relegation_fight: home_motive += 15
    if ctx.away_title_race:       away_motive += 20
    if ctx.away_relegation_fight: away_motive += 20
    if ctx.away_european_race:    away_motive += 10
    if ctx.is_derby:
        home_motive += 5
        away_motive += 5

    # Ranking pressure
    rank_delta = (ctx.away_rank - ctx.home_rank) / ctx.total_teams * 20
    home_motive += rank_delta

    r.score_psychology = min(100, max(0, (home_motive - away_motive + 100) / 2))

    # ── 3. SQUAD ─────────────────────────────────────────────────────────────
    home_squad = 100 - (ctx.home_key_players_missing * 15 + ctx.home_total_injured * 5 + ctx.home_suspended * 10)
    away_squad = 100 - (ctx.away_key_players_missing * 15 + ctx.away_total_injured * 5 + ctx.away_suspended * 10)
    home_squad = max(0, home_squad)
    away_squad = max(0, away_squad)
    r.score_squad = (home_squad - away_squad + 100) / 2

    # Fatigue
    home_fatigue = max(0, (7 - ctx.home_days_rest) * 5)
    away_fatigue = max(0, (7 - ctx.away_days_rest) * 5)
    r.score_squad = max(0, r.score_squad - home_fatigue * 0.3 + away_fatigue * 0.3)

    # ── 4. TACTICS ───────────────────────────────────────────────────────────
    home_dominance = (
        (ctx.home_possession_avg - 50) * 0.3
        + (ctx.home_shots_on_avg - ctx.away_shots_on_avg) * 3
        + (ctx.home_corners_avg - ctx.away_corners_avg) * 2
    )
    r.score_tactics = min(100, max(0, 50 + home_dominance))

    # ── 5. ADVANCED ──────────────────────────────────────────────────────────
    h2h_score = (ctx.h2h_home_wins / max(ctx.h2h_home_wins + ctx.h2h_draws + ctx.h2h_away_wins, 1)) * 100
    weather_penalty = 5 if ctx.rain else 0
    weather_penalty += max(0, (ctx.wind_kmh - 40) * 0.5)
    r.score_advanced = min(100, max(0, h2h_score * 0.5 + (100 - weather_penalty) * 0.5))

    # ── 6. ODDS ANALYSIS ─────────────────────────────────────────────────────
    if ctx.odds_home and ctx.odds_draw and ctx.odds_away:
        implied_home = 1 / ctx.odds_home
        implied_draw = 1 / ctx.odds_draw
        implied_away = 1 / ctx.odds_away
        total_implied = implied_home + implied_draw + implied_away
        norm_home = implied_home / total_implied
        norm_away = implied_away / total_implied
        market_home_score = norm_home * 100
        r.score_odds = min(100, max(0, market_home_score))
    else:
        r.score_odds = 50.0

    # ── 7. ML ────────────────────────────────────────────────────────────────
    r.score_ml = ctx.ml_prob_home * 100

    # ── TOTAL WEIGHTED SCORE ─────────────────────────────────────────────────
    r.score_total = (
        r.score_form       * WEIGHTS["form"]
        + r.score_psychology * WEIGHTS["psychology"]
        + r.score_squad      * WEIGHTS["squad"]
        + r.score_tactics    * WEIGHTS["tactics"]
        + r.score_advanced   * WEIGHTS["advanced"]
        + r.score_odds       * WEIGHTS["odds"]
        + r.score_ml         * WEIGHTS["ml"]
    )

    # ── PROBABILITIES ────────────────────────────────────────────────────────
    # Blend ML probs + stats
    stat_prob_home = r.score_total / 100
    stat_prob_away = (100 - r.score_total) / 100 * 0.7
    stat_prob_draw = 1 - stat_prob_home - stat_prob_away

    r.prob_home = round(ctx.ml_prob_home * 0.5 + stat_prob_home * 0.5, 3)
    r.prob_draw = round(ctx.ml_prob_draw * 0.5 + max(0, stat_prob_draw) * 0.5, 3)
    r.prob_away = round(1 - r.prob_home - r.prob_draw, 3)

    # BTTS probability
    home_scoring_prob = 1 - math.exp(-ctx.home_goals_scored_avg)
    away_scoring_prob = 1 - math.exp(-ctx.away_goals_scored_avg)
    r.prob_btts = round(home_scoring_prob * away_scoring_prob, 3)

    # Over 2.5 probability (Poisson)
    lam = ctx.home_goals_scored_avg + ctx.away_goals_scored_avg
    r.prob_over25 = round(1 - sum(
        (math.exp(-lam) * lam**k) / math.factorial(k) for k in range(3)
    ), 3)

    # ── BEST BET SELECTION ───────────────────────────────────────────────────
    candidates = [
        ("home", r.prob_home, ctx.odds_home or _fair_odds(r.prob_home)),
        ("draw", r.prob_draw, ctx.odds_draw or _fair_odds(r.prob_draw)),
        ("away", r.prob_away, ctx.odds_away or _fair_odds(r.prob_away)),
        ("btts_yes", r.prob_btts, ctx.odds_btts_yes or _fair_odds(r.prob_btts)),
        ("over25", r.prob_over25, ctx.odds_over25 or _fair_odds(r.prob_over25)),
    ]

    best_value = -999
    for bet_name, prob, odds in candidates:
        if odds is None or odds <= 1.0:
            continue
        implied = 1 / odds
        edge = prob - implied
        if edge > best_value:
            best_value = edge
            r.best_bet = bet_name
            r.best_odds = odds
            r.value_edge = round(edge * 100, 1)

    # ── CONFIDENCE ───────────────────────────────────────────────────────────
    base_conf = r.score_total
    if r.value_edge > 5:  base_conf = min(100, base_conf + 5)
    if r.value_edge < 0:  base_conf = max(0,   base_conf - 10)
    r.confidence = int(round(base_conf))

    # ── TEXT GENERATION ──────────────────────────────────────────────────────
    r.reasoning = _build_reasoning(ctx, r)
    r.risks = _build_risks(ctx, r)
    r.key_stats = _build_key_stats(ctx, r)

    return r


def _fair_odds(prob: float) -> float:
    return round(1 / max(prob, 0.01), 2)


def _build_reasoning(ctx: MatchContext, r: AnalysisResult) -> str:
    lines = []
    lines.append(f"Forme : {ctx.home_name} {ctx.home_form5} vs {ctx.away_name} {ctx.away_form5}.")
    lines.append(f"xG moyen — Domicile: {ctx.home_xg_avg:.2f} | Extérieur: {ctx.away_xg_avg:.2f}.")
    if ctx.home_key_players_missing > 0:
        lines.append(f"⚠ {ctx.away_key_players_missing} joueur(s) clé(s) absent(s) chez {ctx.away_name}.")
    if ctx.away_days_rest < 4:
        lines.append(f"⚠ {ctx.away_name} en situation de fatigue ({ctx.away_days_rest} jours de repos).")
    h2h_total = ctx.h2h_home_wins + ctx.h2h_draws + ctx.h2h_away_wins
    lines.append(f"H2H (10 derniers) : {ctx.h2h_home_wins}V {ctx.h2h_draws}N {ctx.h2h_away_wins}D — moy. {ctx.h2h_avg_goals:.1f} buts/match.")
    lines.append(f"Score d'analyse total : {r.score_total:.1f}/100 → Confiance {r.confidence}%.")
    return " ".join(lines)


def _build_risks(ctx: MatchContext, r: AnalysisResult) -> str:
    risks = []
    if ctx.is_derby:
        risks.append("Match de derby — résultat imprévisible malgré les statistiques.")
    if r.prob_draw > 0.27:
        risks.append(f"Probabilité de match nul élevée ({r.prob_draw*100:.0f}%) — double chance conseillée.")
    if ctx.away_relegation_fight:
        risks.append(f"{ctx.away_name} se bat pour sa survie — motivation extrême possible.")
    if ctx.rain:
        risks.append("Conditions météo défavorables (pluie) — jeu plus fermé probable.")
    if not risks:
        risks.append("Aucun facteur de risque majeur identifié.")
    return " ".join(risks)


def _build_key_stats(ctx: MatchContext, r: AnalysisResult) -> dict:
    return {
        "home_xg_avg": ctx.home_xg_avg,
        "away_xg_avg": ctx.away_xg_avg,
        "home_form5": ctx.home_form5,
        "away_form5": ctx.away_form5,
        "h2h_home_wins": ctx.h2h_home_wins,
        "h2h_draws": ctx.h2h_draws,
        "h2h_away_wins": ctx.h2h_away_wins,
        "prob_home": r.prob_home,
        "prob_draw": r.prob_draw,
        "prob_away": r.prob_away,
        "prob_btts": r.prob_btts,
        "prob_over25": r.prob_over25,
        "value_edge_pct": r.value_edge,
        "scores": {
            "form": round(r.score_form, 1),
            "psychology": round(r.score_psychology, 1),
            "squad": round(r.score_squad, 1),
            "tactics": round(r.score_tactics, 1),
            "advanced": round(r.score_advanced, 1),
            "odds": round(r.score_odds, 1),
            "ml": round(r.score_ml, 1),
            "total": round(r.score_total, 1),
        },
    }
