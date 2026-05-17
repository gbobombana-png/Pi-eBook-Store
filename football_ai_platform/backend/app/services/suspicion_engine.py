"""
Moteur de suspicion: agrège tous les signaux d'anomalie et produit
un score final 0-100 avec niveau et rapport complet.
"""
from ..schemas.schemas import SuspicionResult, SuspicionFlag
from ..ml.anomaly_detector import (
    AnomalySignal,
    detect_statistical_anomalies,
    detect_pattern_similarities,
    compute_total_suspicion_score,
)
from ..core.config import get_settings

settings = get_settings()

# Mapping sévérité → contribution maximale
SEVERITY_WEIGHT = {
    "low": 5,
    "medium": 12,
    "high": 20,
    "critical": 30,
}

RISK_LABELS = {
    "low":      "Risque faible — aucun comportement suspect détecté.",
    "medium":   "Risque modéré — quelques anomalies détectées, à surveiller.",
    "high":     "Risque élevé — multiples signaux suspects concordants.",
    "critical": "ALERTE CRITIQUE — Patterns fortement associés à la manipulation de matchs.",
}


def _signals_to_flags(signals: list[AnomalySignal]) -> list[SuspicionFlag]:
    return [
        SuspicionFlag(
            code=s.code,
            description=s.description,
            severity=s.severity,
            score_contribution=round(s.score_contribution, 2),
        )
        for s in signals
    ]


def _level_from_score(score: float) -> str:
    if score >= settings.suspicion_high_threshold:
        return "critical" if score >= 85 else "high"
    if score >= settings.suspicion_medium_threshold:
        return "medium"
    return "low"


def compute(
    odds_signals: list[AnomalySignal],
    stats_signals: list[AnomalySignal] | None = None,
    pattern_signals: list[AnomalySignal] | None = None,
    similar_matches: list[str] | None = None,
    odds_contribution: float = 0.0,
    stats_contribution: float = 0.0,
) -> SuspicionResult:
    """
    Calcule le score de suspicion final en fusionnant tous les signaux.

    Architecture du score (max 100):
      - Anomalies cotes & volume:   max 35 pts
      - Anomalies statistiques:     max 25 pts
      - Patterns historiques:       max 25 pts
      - Indicateurs contextuels:    max 15 pts
    """
    all_signals: list[AnomalySignal] = list(odds_signals)
    if stats_signals:
        all_signals.extend(stats_signals)
    if pattern_signals:
        all_signals.extend(pattern_signals)

    # Score brut via diminution marginale
    raw_score = compute_total_suspicion_score(all_signals)

    # Ajouter les contributions directes (cotes + stats)
    direct_contrib = min(20, odds_contribution * 0.5 + stats_contribution * 0.3)
    final_score = min(100.0, raw_score + direct_contrib)

    level = _level_from_score(final_score)
    flags = _signals_to_flags(all_signals)
    similar = similar_matches or []

    return SuspicionResult(
        score=round(final_score, 1),
        level=level,
        flags=flags,
        similar_suspect_matches=similar,
        risk_assessment=RISK_LABELS[level],
    )


def quick_alert(score: float, level: str, home_team: str, away_team: str) -> dict:
    """Génère un payload d'alerte rapide pour WebSocket broadcast."""
    if level in ("high", "critical"):
        return {
            "type": "SUSPICION_ALERT",
            "match": f"{home_team} vs {away_team}",
            "score": score,
            "level": level,
            "message": f"⚠️ Score suspicion {score:.0f}/100 — {RISK_LABELS[level]}",
        }
    return {}
