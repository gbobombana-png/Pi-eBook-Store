"""
Generate realistic synthetic training data for the ML model.
Used when no historical DB data is available.
"""
import numpy as np
from app.services.analyzer import MatchContext
from app.ml.features import build_feature_vector


def _random_ctx(rng: np.random.Generator) -> MatchContext:
    """Sample a random match context with realistic distributions."""
    home_att = rng.gamma(shape=2.5, scale=0.7)   # ~1.75 avg
    away_att = rng.gamma(shape=2.0, scale=0.7)   # ~1.40 avg
    home_def = rng.gamma(shape=1.5, scale=0.8)   # ~1.20 avg
    away_def = rng.gamma(shape=2.0, scale=0.8)   # ~1.60 avg

    return MatchContext(
        home_name="HomeTeam",
        away_name="AwayTeam",
        home_goals_scored_avg=float(np.clip(home_att, 0.5, 4.0)),
        home_goals_conceded_avg=float(np.clip(home_def, 0.5, 3.5)),
        away_goals_scored_avg=float(np.clip(away_att, 0.4, 3.5)),
        away_goals_conceded_avg=float(np.clip(away_def, 0.5, 3.5)),
        home_xg_avg=float(np.clip(home_att * rng.uniform(0.8, 1.1), 0.4, 3.5)),
        away_xg_avg=float(np.clip(away_att * rng.uniform(0.8, 1.1), 0.4, 3.0)),
        home_xga_avg=float(np.clip(home_def * rng.uniform(0.85, 1.1), 0.3, 3.0)),
        away_xga_avg=float(np.clip(away_def * rng.uniform(0.85, 1.1), 0.4, 3.5)),
        home_shots_on_avg=float(rng.uniform(2.5, 8.0)),
        away_shots_on_avg=float(rng.uniform(2.0, 7.0)),
        home_possession_avg=float(rng.uniform(35.0, 70.0)),
        away_possession_avg=float(rng.uniform(30.0, 65.0)),
        home_corners_avg=float(rng.uniform(3.0, 9.0)),
        away_corners_avg=float(rng.uniform(2.5, 8.0)),
        home_btts_pct=float(rng.uniform(30.0, 75.0)),
        away_btts_pct=float(rng.uniform(30.0, 75.0)),
        home_over25_pct=float(rng.uniform(30.0, 80.0)),
        away_over25_pct=float(rng.uniform(30.0, 80.0)),
        home_rank=int(rng.integers(1, 20)),
        away_rank=int(rng.integers(1, 20)),
        home_points=int(rng.integers(10, 80)),
        away_points=int(rng.integers(10, 80)),
        h2h_home_wins=int(rng.integers(0, 8)),
        h2h_draws=int(rng.integers(0, 5)),
        h2h_away_wins=int(rng.integers(0, 8)),
        h2h_avg_goals=float(rng.uniform(1.5, 4.0)),
        home_key_players_missing=int(rng.integers(0, 4)),
        away_key_players_missing=int(rng.integers(0, 4)),
        home_days_rest=int(rng.integers(2, 14)),
        away_days_rest=int(rng.integers(2, 14)),
        odds_home=float(rng.uniform(1.3, 5.5)),
        odds_draw=float(rng.uniform(2.8, 4.5)),
        odds_away=float(rng.uniform(1.5, 8.0)),
        ml_prob_home=float(rng.uniform(0.20, 0.65)),
        ml_prob_draw=float(rng.uniform(0.15, 0.35)),
    )


def _outcome_label(ctx: MatchContext, rng: np.random.Generator) -> int:
    """Simulate realistic outcome using Poisson + home advantage."""
    import math
    lam_h = ctx.home_goals_scored_avg / max(ctx.away_goals_conceded_avg, 0.5) * 1.12
    lam_a = ctx.away_goals_scored_avg / max(ctx.home_goals_conceded_avg, 0.5)
    lam_h = max(0.3, min(lam_h, 5.0))
    lam_a = max(0.3, min(lam_a, 5.0))

    h_goals = rng.poisson(lam_h)
    a_goals = rng.poisson(lam_a)

    if h_goals > a_goals:  return 2  # home
    if h_goals == a_goals: return 1  # draw
    return 0  # away


def generate_synthetic_dataset(n_samples: int = 4000, seed: int = 42):
    """Return (X, y) numpy arrays of synthetic training data."""
    rng = np.random.default_rng(seed)
    X, y = [], []
    for _ in range(n_samples):
        ctx = _random_ctx(rng)
        try:
            feat = build_feature_vector(ctx)
            label = _outcome_label(ctx, rng)
            X.append(feat)
            y.append(label)
        except Exception:
            continue
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)
