"""
Pipeline principal de prédiction.
Orchestre: football_analyzer → ML models → ensemble → suspicion_engine → résultat final.
"""
from datetime import datetime
from ..schemas.schemas import FullAnalysisResponse, MatchOut
from ..services import football_analyzer as fa
from ..services import odds_analyzer as oa
from ..services import suspicion_engine as se
from ..ml import poisson_model, xgboost_model, neural_network, ensemble
from ..ml.anomaly_detector import detect_statistical_anomalies, detect_pattern_similarities


def run_full_analysis(
    match: MatchOut,
    home_profile: fa.TeamProfile,
    away_profile: fa.TeamProfile,
    h2h: fa.H2HRecord,
    odds_snapshots: list[dict] | None = None,
    volumes: list[dict] | None = None,
    bookmaker_lines: list[dict] | None = None,
    is_home_fixture: bool = True,
) -> FullAnalysisResponse:

    # ── 1. Analyse des cotes ─────────────────────────────────────────────────
    snaps = odds_snapshots or []
    odds_result, odds_signals = oa.analyze(snaps, volumes, bookmaker_lines)

    # Probabilités implicites actuelles pour les features ML
    if snaps:
        cur = snaps[-1]
        h, d, a = cur.get("home", 2.5), cur.get("draw", 3.2), cur.get("away", 2.5)
        tot = 1/h + 1/d + 1/a
        impl_h, impl_d, impl_a = 1/h/tot, 1/d/tot, 1/a/tot
    else:
        impl_h, impl_d, impl_a = 0.45, 0.25, 0.30

    # ── 2. Analyse footballistique ───────────────────────────────────────────
    fb_result, lambda_h, lambda_a = fa.analyze(home_profile, away_profile, h2h, is_home_fixture)

    # ── 3. Modèles ML ────────────────────────────────────────────────────────
    # Poisson
    poisson_pred = poisson_model.predict(
        home_attack=home_profile.attack_strength_home if is_home_fixture else home_profile.attack_strength_away,
        home_defense=home_profile.defense_strength_home if is_home_fixture else home_profile.defense_strength_away,
        away_attack=away_profile.attack_strength_away,
        away_defense=away_profile.defense_strength_away,
        league_avg_home=fa.LEAGUE_HOME_AVG,
        league_avg_away=fa.LEAGUE_AWAY_AVG,
    )
    poisson_dict = poisson_model.to_dict(poisson_pred)

    # XGBoost
    xgb_features = fa.build_xgb_features(
        home_profile, away_profile, h2h,
        impl_h, impl_d, impl_a, is_home_fixture
    )
    xgb_dict = xgboost_model.predict(xgb_features)

    # Neural Network
    feature_vec = xgboost_model.features_to_vector(xgb_features)
    nn_dict = neural_network.predict(feature_vec)

    # ── 4. Ensemble ──────────────────────────────────────────────────────────
    ens_input = ensemble.EnsembleInput(
        poisson=poisson_dict,
        xgboost=xgb_dict,
        neural=nn_dict,
        has_odds=bool(snaps),
    )
    ens_result = ensemble.fuse(ens_input)

    # ── 5. Anomalies statistiques ────────────────────────────────────────────
    match_stats_dict = {
        "home_xg": match.home_xg,
        "away_xg": match.away_xg,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "home_possession": match.home_possession,
        "home_shots": match.home_shots,
        "home_form_score": home_profile.form_score,
    }
    stat_signals = detect_statistical_anomalies(match_stats_dict)

    # Patterns historiques
    pattern_features = {
        "odds_implied_home": impl_h,
        "odds_move_home": odds_result.movement_home_pct / 100,
        "volume_spike": odds_result.volume_multiplier,
        "home_xg": lambda_h,
        "home_score": match.home_score or 0,
        "away_score": match.away_score or 0,
        "h2h_home_win_rate": h2h.home_win_rate,
        "home_form": home_profile.form_score,
    }
    pat_signals, similar_matches = detect_pattern_similarities(pattern_features)

    # ── 6. Score de suspicion final ──────────────────────────────────────────
    suspicion = se.compute(
        odds_signals=odds_signals,
        stats_signals=stat_signals,
        pattern_signals=pat_signals,
        similar_matches=similar_matches,
        odds_contribution=odds_result.suspicion_contribution,
        stats_contribution=fb_result.suspicion_contribution,
    )

    # ── 7. Vainqueur + marchés ───────────────────────────────────────────────
    if ens_result.prob_home > ens_result.prob_away and ens_result.prob_home > ens_result.prob_draw:
        winner = match.home_team
    elif ens_result.prob_away > ens_result.prob_home and ens_result.prob_away > ens_result.prob_draw:
        winner = match.away_team
    else:
        winner = "Nul"

    markets = {
        "winner":      {"team": winner, "prob": max(ens_result.prob_home, ens_result.prob_draw, ens_result.prob_away)},
        "exact_score": {
            "score": f"{ens_result.predicted_home_score}:{ens_result.predicted_away_score}",
            "prob": ens_result.exact_score_probability,
        },
        "over_2_5":    {"prob": ens_result.prob_over25},
        "under_2_5":   {"prob": 1 - ens_result.prob_over25},
        "btts":        {"prob": ens_result.prob_btts},
        "btts_no":     {"prob": 1 - ens_result.prob_btts},
        "ht_home_lead":{"prob": ens_result.prob_ht_home_lead},
        "late_goal":   {"prob": ens_result.prob_late_goal},
        "home_win":    {"prob": ens_result.prob_home},
        "draw":        {"prob": ens_result.prob_draw},
        "away_win":    {"prob": ens_result.prob_away},
        "top_5_scores": poisson_dict.get("top_5_scores", []),
    }

    confidence = (
        max(ens_result.prob_home, ens_result.prob_draw, ens_result.prob_away) * 0.6
        + ens_result.model_agreement * 0.4
    ) * 100

    return FullAnalysisResponse(
        match=match,
        odds_analysis=odds_result,
        football_stats=fb_result,
        prediction=ens_result,
        suspicion=suspicion,
        predicted_winner=winner,
        prediction_confidence=round(confidence, 1),
        analysis_timestamp=datetime.utcnow(),
        markets=markets,
    )
