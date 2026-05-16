"""
Feature engineering for the ML model.
Converts raw match data into a fixed-length feature vector.
"""
import numpy as np
from typing import Optional


FEATURE_NAMES = [
    # Form
    "home_form5_pts", "away_form5_pts", "home_form10_pts", "away_form10_pts",
    "form_delta",
    # Goals
    "home_goals_scored_avg", "home_goals_conceded_avg",
    "away_goals_scored_avg", "away_goals_conceded_avg",
    "home_goal_diff", "away_goal_diff",
    # xG
    "home_xg_avg", "away_xg_avg", "home_xga_avg", "away_xga_avg",
    "xg_delta", "xga_delta",
    # Shooting & possession
    "home_shots_on_avg", "away_shots_on_avg",
    "home_possession_avg", "away_possession_avg",
    # H2H
    "h2h_home_win_rate", "h2h_draw_rate", "h2h_avg_goals",
    # Standings
    "home_rank_norm", "away_rank_norm", "rank_delta",
    "home_points_norm", "away_points_norm",
    # Squad
    "home_injuries_penalty", "away_injuries_penalty",
    "home_suspension_penalty", "away_suspension_penalty",
    # Fatigue
    "home_fatigue", "away_fatigue",
    # Motivation flags
    "home_title_race", "home_relegation", "home_euro",
    "away_title_race", "away_relegation", "away_euro",
    "is_derby",
    # Odds (market signal)
    "odds_home_norm", "odds_draw_norm", "odds_away_norm",
    # Weather
    "rain_flag", "wind_norm",
]

N_FEATURES = len(FEATURE_NAMES)


def _form_pts(form: str) -> float:
    pts = {"W": 3, "D": 1, "L": 0}
    total = sum(pts.get(c, 0) for c in form.upper())
    return total / max(len(form) * 3, 1)


def build_feature_vector(ctx) -> np.ndarray:
    """Build feature vector from a MatchContext object."""
    h5 = _form_pts(ctx.home_form5)
    a5 = _form_pts(ctx.away_form5)
    h10 = _form_pts(ctx.home_form10)
    a10 = _form_pts(ctx.away_form10)

    h2h_total = max(ctx.h2h_home_wins + ctx.h2h_draws + ctx.h2h_away_wins, 1)

    oh = ctx.odds_home or 2.0
    od = ctx.odds_draw or 3.4
    oa = ctx.odds_away or 3.5
    implied_total = (1/oh + 1/od + 1/oa)

    feat = [
        h5, a5, h10, a10, h5 - a5,
        ctx.home_goals_scored_avg, ctx.home_goals_conceded_avg,
        ctx.away_goals_scored_avg, ctx.away_goals_conceded_avg,
        ctx.home_goals_scored_avg - ctx.home_goals_conceded_avg,
        ctx.away_goals_scored_avg - ctx.away_goals_conceded_avg,
        ctx.home_xg_avg, ctx.away_xg_avg, ctx.home_xga_avg, ctx.away_xga_avg,
        ctx.home_xg_avg - ctx.away_xg_avg,
        ctx.home_xga_avg - ctx.away_xga_avg,
        ctx.home_shots_on_avg, ctx.away_shots_on_avg,
        ctx.home_possession_avg / 100, ctx.away_possession_avg / 100,
        ctx.h2h_home_wins / h2h_total,
        ctx.h2h_draws / h2h_total,
        ctx.h2h_avg_goals,
        ctx.home_rank / max(ctx.total_teams, 1),
        ctx.away_rank / max(ctx.total_teams, 1),
        (ctx.away_rank - ctx.home_rank) / max(ctx.total_teams, 1),
        ctx.home_points / max(ctx.home_points + ctx.away_points, 1),
        ctx.away_points / max(ctx.home_points + ctx.away_points, 1),
        ctx.home_key_players_missing * 0.15 + ctx.home_total_injured * 0.05,
        ctx.away_key_players_missing * 0.15 + ctx.away_total_injured * 0.05,
        ctx.home_suspended * 0.1,
        ctx.away_suspended * 0.1,
        max(0, (7 - ctx.home_days_rest) / 7),
        max(0, (7 - ctx.away_days_rest) / 7),
        float(ctx.home_title_race), float(ctx.home_relegation_fight), float(ctx.home_european_race),
        float(ctx.away_title_race), float(ctx.away_relegation_fight), float(ctx.away_european_race),
        float(ctx.is_derby),
        (1/oh) / implied_total,
        (1/od) / implied_total,
        (1/oa) / implied_total,
        float(ctx.rain),
        min(ctx.wind_kmh / 100, 1.0),
    ]

    assert len(feat) == N_FEATURES, f"Feature count mismatch: {len(feat)} vs {N_FEATURES}"
    return np.array(feat, dtype=np.float32)
