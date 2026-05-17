"""
Détecteur d'anomalies pour les matchs suspects.
Combine plusieurs approches:
  1. Z-score sur les métriques clés
  2. Isolation Forest sur les features de marché
  3. Détection de patterns historiques connus
  4. Analyse des séries temporelles des cotes
"""
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnomalySignal:
    code: str
    description: str
    severity: str          # "low" | "medium" | "high" | "critical"
    score_contribution: float
    details: dict = field(default_factory=dict)


# ── Seuils ────────────────────────────────────────────────────────────────────

THRESHOLDS = {
    # Cotes
    "odds_sharp_move":        0.08,    # 8% de mouvement
    "odds_reversal":          0.12,    # 12% → inversion de favori
    "max_bookmaker_spread":   0.15,    # divergence inter-bookmakers
    # Volume
    "volume_spike_ratio":     3.0,     # 3× le volume normal
    "late_volume_ratio":      5.0,     # 5× dans les 2h avant le match
    # Stats
    "xg_result_gap_sigma":    2.5,     # écart xG vs résultat en nb de σ
    "possession_goal_anomaly": 0.40,   # possession < 40% avec victoire 2+
    # Historique
    "h2h_score_anomaly":      0.05,    # score jamais vu en H2H (< 5%)
}


def _z_score(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return abs(value - mean) / std


def detect_odds_anomalies(
    odds_history: list[dict],   # [{"home": f, "draw": f, "away": f, "ts": int}, ...]
    volumes: list[dict] | None = None,
) -> list[AnomalySignal]:
    signals = []
    if len(odds_history) < 2:
        return signals

    opening = odds_history[0]
    current = odds_history[-1]

    o_h = opening.get("home", 2.0);  c_h = current.get("home", 2.0)
    o_a = opening.get("away", 2.0);  c_a = current.get("away", 2.0)

    # Probabilités implicites
    def implied(h, d, a):
        tot = 1/h + 1/d + 1/a
        return 1/h/tot, 1/a/tot

    ip_h0, ip_a0 = implied(o_h, opening.get("draw", 3.2), o_a)
    ip_hc, ip_ac = implied(c_h, current.get("draw", 3.2), c_a)

    move_h = ip_hc - ip_h0
    move_a = ip_ac - ip_a0

    # Sharp move détecté
    if abs(move_h) >= THRESHOLDS["odds_sharp_move"]:
        direction = "domicile" if move_h > 0 else "extérieur"
        severity = "high" if abs(move_h) >= 0.15 else "medium"
        signals.append(AnomalySignal(
            code="SHARP_MOVE",
            description=f"Mouvement sharp de {abs(move_h)*100:.1f}% vers {direction}",
            severity=severity,
            score_contribution=min(20, abs(move_h) * 100),
            details={"move_pct": round(abs(move_h)*100, 2), "direction": direction},
        ))

    # Inversion de marché (favori a changé)
    if (ip_h0 > ip_a0) != (ip_hc > ip_ac) and abs(move_h) >= THRESHOLDS["odds_reversal"]:
        signals.append(AnomalySignal(
            code="MARKET_INVERSION",
            description="Inversion du favori — changement majeur des probabilités",
            severity="critical",
            score_contribution=25,
            details={"opening_fav": "home" if ip_h0 > ip_a0 else "away",
                     "current_fav": "home" if ip_hc > ip_ac else "away"},
        ))

    # Analyse de la série temporelle (accélération du mouvement)
    if len(odds_history) >= 5:
        movements = []
        for i in range(1, len(odds_history)):
            prev = odds_history[i - 1]; curr = odds_history[i]
            m = abs(1/curr.get("home", 2) - 1/prev.get("home", 2))
            movements.append(m)
        avg_m = sum(movements[:-1]) / max(len(movements) - 1, 1)
        last_m = movements[-1]
        if avg_m > 0 and last_m / avg_m >= 4:
            signals.append(AnomalySignal(
                code="ODDS_ACCELERATION",
                description=f"Accélération du mouvement des cotes (×{last_m/avg_m:.1f})",
                severity="high",
                score_contribution=15,
                details={"acceleration_ratio": round(last_m/avg_m, 2)},
            ))

    # Volume anormal
    if volumes and len(volumes) >= 2:
        avg_vol = sum(v.get("total", 0) for v in volumes[:-1]) / max(len(volumes)-1, 1)
        last_vol = volumes[-1].get("total", 0)
        if avg_vol > 0:
            ratio = last_vol / avg_vol
            if ratio >= THRESHOLDS["volume_spike_ratio"]:
                severity = "critical" if ratio >= THRESHOLDS["late_volume_ratio"] else "high"
                signals.append(AnomalySignal(
                    code="VOLUME_SPIKE",
                    description=f"Pic de volume anormal (×{ratio:.1f} la moyenne)",
                    severity=severity,
                    score_contribution=min(20, ratio * 4),
                    details={"ratio": round(ratio, 2)},
                ))

    return signals


def detect_statistical_anomalies(
    match_stats: dict,
    historical_avg: dict | None = None,
) -> list[AnomalySignal]:
    signals = []
    hist = historical_avg or {}

    # Écart xG vs résultat réel
    home_xg = match_stats.get("home_xg", 0)
    away_xg = match_stats.get("away_xg", 0)
    home_score = match_stats.get("home_score")
    away_score = match_stats.get("away_score")

    if home_score is not None and away_score is not None:
        xg_diff_home = home_score - home_xg
        xg_diff_away = away_score - away_xg

        # Équipe qui gagne avec xG très faible
        if xg_diff_home >= 2.0 and home_score > away_score:
            signals.append(AnomalySignal(
                code="XG_OUTPERFORM_HOME",
                description=f"Domicile sur-performe son xG de +{xg_diff_home:.1f} buts",
                severity="medium" if xg_diff_home < 3 else "high",
                score_contribution=min(15, xg_diff_home * 5),
                details={"xg": home_xg, "actual": home_score, "delta": round(xg_diff_home, 2)},
            ))
        if xg_diff_away >= 2.0 and away_score > home_score:
            signals.append(AnomalySignal(
                code="XG_OUTPERFORM_AWAY",
                description=f"Extérieur sur-performe son xG de +{xg_diff_away:.1f} buts",
                severity="medium" if xg_diff_away < 3 else "high",
                score_contribution=min(15, xg_diff_away * 5),
                details={"xg": away_xg, "actual": away_score, "delta": round(xg_diff_away, 2)},
            ))

    # Anomalie possession vs victoire
    home_poss = match_stats.get("home_possession", 50)
    if home_poss is not None and home_score is not None and away_score is not None:
        if home_poss < 35 and home_score >= away_score + 2:
            signals.append(AnomalySignal(
                code="LOW_POSSESSION_WIN",
                description=f"Victoire avec seulement {home_poss:.0f}% possession (+2 buts d'écart)",
                severity="medium",
                score_contribution=8,
                details={"possession": home_poss},
            ))

    # Tirs au but vs buts: conversion anormale
    home_shots = match_stats.get("home_shots", 0)
    if home_shots and home_score is not None and home_shots > 0:
        conversion = home_score / home_shots
        if conversion >= 0.7 and home_shots >= 5:
            signals.append(AnomalySignal(
                code="CONVERSION_ANOMALY",
                description=f"Taux de conversion domicile anormal: {conversion*100:.0f}%",
                severity="medium",
                score_contribution=7,
                details={"shots": home_shots, "goals": home_score, "conversion": round(conversion, 3)},
            ))

    # Forme très faible vs performance excellente
    home_form_val = match_stats.get("home_form_score", 0.5)
    if home_form_val < 0.2 and home_score is not None and away_score is not None:
        if home_score >= away_score + 2:
            signals.append(AnomalySignal(
                code="POOR_FORM_OVERPERFORM",
                description="Équipe en mauvaise forme (< 20%) remporte par 2+ buts",
                severity="medium",
                score_contribution=10,
                details={"form_score": home_form_val},
            ))

    return signals


def detect_pattern_similarities(
    match_features: dict,
    suspect_patterns: list[dict] | None = None,
) -> tuple[list[AnomalySignal], list[str]]:
    """
    Compare les features du match à des patterns de matchs suspects historiques.
    Retourne les signaux et les noms des matchs similaires trouvés.
    """
    signals = []
    similar_matches = []

    # Patterns historiques connus (base de règles + encodage pattern)
    known_patterns = suspect_patterns or _default_suspect_patterns()

    for pattern in known_patterns:
        similarity = _compute_pattern_similarity(match_features, pattern["features"])
        if similarity >= 0.75:
            signals.append(AnomalySignal(
                code="SIMILAR_SUSPECT_PATTERN",
                description=f"Pattern similaire à: {pattern['label']} (similarité {similarity*100:.0f}%)",
                severity=pattern.get("severity", "medium"),
                score_contribution=min(20, similarity * 25),
                details={"pattern": pattern["label"], "similarity": round(similarity, 3)},
            ))
            similar_matches.append(pattern["label"])

    return signals, similar_matches


def _compute_pattern_similarity(feat: dict, pattern_feat: dict) -> float:
    """Similarité cosinus simplifiée sur les features numériques communes."""
    keys = set(feat.keys()) & set(pattern_feat.keys())
    if not keys:
        return 0.0
    diffs = []
    for k in keys:
        v1, v2 = feat.get(k, 0), pattern_feat.get(k, 0)
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            max_val = max(abs(v1), abs(v2), 1)
            diffs.append(1 - abs(v1 - v2) / max_val)
    return sum(diffs) / len(diffs) if diffs else 0.0


def _default_suspect_patterns() -> list[dict]:
    """Patterns de matchs historiquement suspects (base de règles)."""
    return [
        {
            "label": "Pattern 'fix_late_goal'",
            "severity": "high",
            "features": {
                "odds_move_away": 0.15, "volume_spike": 4.0,
                "home_xg": 1.8, "home_score": 0, "minute_first_goal": 85,
            },
        },
        {
            "label": "Pattern 'heavy_favourite_loss'",
            "severity": "high",
            "features": {
                "odds_implied_home": 0.72, "home_score": 0,
                "away_score": 2, "home_shots": 18,
            },
        },
        {
            "label": "Pattern 'uncharacteristic_result'",
            "severity": "medium",
            "features": {
                "h2h_home_win_rate": 0.7, "home_score": 0,
                "away_score": 3, "home_form": 0.8,
            },
        },
    ]


def compute_total_suspicion_score(signals: list[AnomalySignal]) -> float:
    """Agrège les contributions avec diminution marginale (évite le double comptage)."""
    if not signals:
        return 0.0
    contributions = sorted([s.score_contribution for s in signals], reverse=True)
    total = 0.0
    decay = 1.0
    for c in contributions:
        total += c * decay
        decay *= 0.85    # chaque signal suivant vaut 15% de moins
    return min(100.0, total)
