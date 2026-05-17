"""
Analyse des cotes et des marchés bookmakers.
Détecte les sharp moves, inversions, divergences inter-bookmakers et volumes anormaux.
"""
from dataclasses import dataclass
from ..schemas.schemas import OddsAnalysisResult
from ..ml.anomaly_detector import detect_odds_anomalies, AnomalySignal


@dataclass
class OddsMovement:
    opening_home: float
    opening_draw: float
    opening_away: float
    current_home: float
    current_draw: float
    current_away: float
    bookmaker: str


def normalize_implied_prob(h: float, d: float, a: float) -> tuple[float, float, float]:
    """Retire la marge bookmaker et retourne les proba vraies."""
    overround = 1/h + 1/d + 1/a
    return 1/h/overround, 1/d/overround, 1/a/overround


def implied_margin(h: float, d: float, a: float) -> float:
    """Marge bookmaker en % (overround - 1)."""
    return (1/h + 1/d + 1/a - 1) * 100


def analyze(
    odds_snapshots: list[dict],         # historique trié par timestamp
    volumes: list[dict] | None = None,
    bookmaker_lines: list[dict] | None = None,  # [{"bk": str, "home": f, ...}]
) -> tuple[OddsAnalysisResult, list[AnomalySignal]]:

    if not odds_snapshots:
        return _empty_result(), []

    opening = odds_snapshots[0]
    current = odds_snapshots[-1]

    o_h = opening.get("home", 2.0);  o_d = opening.get("draw", 3.2); o_a = opening.get("away", 2.5)
    c_h = current.get("home", 2.0);  c_d = current.get("draw", 3.2); c_a = current.get("away", 2.5)

    ip_h0, _d0, ip_a0 = normalize_implied_prob(o_h, o_d, o_a)
    ip_hc, _dc, ip_ac = normalize_implied_prob(c_h, c_d, c_a)

    move_h = ip_hc - ip_h0
    move_a = ip_ac - ip_a0

    is_sharp = abs(move_h) >= 0.08 or abs(move_a) >= 0.08
    sharp_dir = None
    if is_sharp:
        sharp_dir = "home" if move_h > 0 else "away"

    is_inversion = (ip_h0 > ip_a0) != (ip_hc > ip_ac)

    # Volume
    vol_multiplier = 1.0
    vol_anomaly = False
    if volumes and len(volumes) >= 2:
        avg = sum(v.get("total", 0) for v in volumes[:-1]) / max(len(volumes) - 1, 1)
        last = volumes[-1].get("total", 0)
        if avg > 0:
            vol_multiplier = last / avg
            vol_anomaly = vol_multiplier >= 3.0

    # Consensus bookmakers
    consensus_pct = 100.0
    if bookmaker_lines and len(bookmaker_lines) >= 2:
        home_probs = []
        for bk in bookmaker_lines:
            try:
                ph, _, _ = normalize_implied_prob(bk["home"], bk.get("draw", 3.2), bk["away"])
                home_probs.append(ph)
            except (KeyError, ZeroDivisionError):
                pass
        if len(home_probs) >= 2:
            spread = max(home_probs) - min(home_probs)
            consensus_pct = max(0.0, 100.0 - spread * 200)

    # Score suspicion issu des cotes (max 25 pts)
    susp_contrib = 0.0
    if is_sharp:       susp_contrib += min(15, abs(move_h) * 100)
    if is_inversion:   susp_contrib += 25
    if vol_anomaly:    susp_contrib += min(15, vol_multiplier * 3)
    if consensus_pct < 80: susp_contrib += (80 - consensus_pct) / 4
    susp_contrib = min(25.0, susp_contrib)

    # Signaux anomalie détaillés
    signals = detect_odds_anomalies(odds_snapshots, volumes)

    result = OddsAnalysisResult(
        opening_home=round(o_h, 3),
        opening_away=round(o_a, 3),
        current_home=round(c_h, 3),
        current_away=round(c_a, 3),
        movement_home_pct=round(move_h * 100, 2),
        movement_away_pct=round(move_a * 100, 2),
        is_sharp_move=is_sharp,
        sharp_direction=sharp_dir,
        volume_anomaly=vol_anomaly,
        volume_multiplier=round(vol_multiplier, 2),
        market_inversion=is_inversion,
        bookmaker_consensus_pct=round(consensus_pct, 1),
        suspicion_contribution=round(susp_contrib, 2),
    )

    return result, signals


def _empty_result() -> OddsAnalysisResult:
    return OddsAnalysisResult(
        opening_home=None, opening_away=None,
        current_home=2.0, current_away=2.0,
        movement_home_pct=0.0, movement_away_pct=0.0,
        is_sharp_move=False, sharp_direction=None,
        volume_anomaly=False, volume_multiplier=1.0,
        market_inversion=False, bookmaker_consensus_pct=100.0,
        suspicion_contribution=0.0,
    )
