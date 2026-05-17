"""
Analyse live minute par minute.
Recalcule les probabilités en temps réel selon les événements du match.
Détecte les retournements improbables et les pics de paris live.
"""
import math
import asyncio
from datetime import datetime
from ..core.websocket_manager import ws_manager
from ..schemas.schemas import LiveUpdatePayload


# Table de probabilités pré-calculée (minute, score_diff) → prob_home
# Inspiré des modèles Dixon-Robinson (1998) et travaux Bundesliga
# Format: {(minute_bucket, score_diff): p_home_win}
# score_diff: home_score - away_score

def _in_play_win_prob(
    minute: int,
    home_score: int,
    away_score: int,
    pre_match_home_prob: float,
    lambda_h: float = 1.5,
    lambda_a: float = 1.2,
) -> tuple[float, float, float]:
    """
    Calcule les probabilités live en tenant compte du temps restant
    et du score actuel (modèle Poisson dynamique sur le temps restant).
    """
    time_remaining = max(0, 90 - minute) / 90
    score_diff = home_score - away_score

    # Intensité ajustée: les équipes tirent plus en fin de match si elles perdent
    urgency_home = 1.0 + 0.3 * max(0, -score_diff) * (1 - time_remaining)
    urgency_away = 1.0 + 0.3 * max(0, score_diff) * (1 - time_remaining)

    adj_lam_h = lambda_h * time_remaining * urgency_home
    adj_lam_a = lambda_a * time_remaining * urgency_away

    # Score possible via Poisson sur le temps restant
    max_g = 6
    p_home = 0.0; p_draw = 0.0; p_away = 0.0

    for dh in range(max_g):
        for da in range(max_g):
            p_dh = (adj_lam_h ** dh) * math.exp(-adj_lam_h) / math.factorial(dh)
            p_da = (adj_lam_a ** da) * math.exp(-adj_lam_a) / math.factorial(da)
            p = p_dh * p_da
            final_h = home_score + dh
            final_a = away_score + da
            if final_h > final_a:   p_home += p
            elif final_h == final_a: p_draw += p
            else:                    p_away += p

    # Normalisation
    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total; p_draw /= total; p_away /= total

    # Blend avec pré-match (diminue à mesure que le match avance)
    pre_blend = max(0, time_remaining * 0.3)
    p_home = (1 - pre_blend) * p_home + pre_blend * pre_match_home_prob
    p_away_blend = (1 - pre_blend) * p_away + pre_blend * (1 - pre_match_home_prob - 0.28)
    p_draw = max(0, 1 - p_home - p_away_blend)

    # Normalisation finale
    total = p_home + p_draw + p_away_blend
    return p_home/total, p_draw/total, p_away_blend/total


def detect_live_anomaly(
    minute: int,
    home_score: int,
    away_score: int,
    pre_match_fav: str,  # "home" | "away"
    pre_match_fav_prob: float,
    live_volume_spike: float = 1.0,
) -> tuple[float, str | None]:
    """
    Détecte les retournements improbables et les anomalies live.
    Retourne (suspicion_delta, alert_message | None).
    """
    delta = 0.0
    alert = None

    # Favori qui perd de 2+ buts après la 60e minute
    if minute >= 60 and live_volume_spike >= 3.0:
        delta += 15.0
        alert = f"⚠️ Pic de volume live (×{live_volume_spike:.1f}) à la {minute}'"

    # Retournement très improbable
    if pre_match_fav == "home" and away_score > home_score + 1 and minute >= 50:
        reversal_prob = 1 - pre_match_fav_prob
        if reversal_prob < 0.15:
            delta += 20.0
            alert = f"🚨 Retournement improbable (favori domicile perd {home_score}-{away_score} à {minute}')"

    if pre_match_fav == "away" and home_score > away_score + 1 and minute >= 50:
        reversal_prob = pre_match_fav_prob  # prob adverse gagne
        if reversal_prob < 0.15:
            delta += 20.0
            alert = f"🚨 Retournement improbable (favori extérieur perd {home_score}-{away_score} à {minute}')"

    # But tardif suspect (90+)
    if minute > 88 and live_volume_spike >= 5.0:
        delta += 25.0
        alert = f"🚨 Volume massif sur but tardif ({minute}') — comportement très suspect"

    return min(30.0, delta), alert


async def process_live_event(
    match_id: int,
    minute: int,
    home_score: int,
    away_score: int,
    event_type: str,
    pre_match_home_prob: float,
    lambda_h: float,
    lambda_a: float,
    live_volume_spike: float,
    pre_match_fav: str,
    pre_match_fav_prob: float,
    current_suspicion: float,
) -> LiveUpdatePayload:
    """
    Traite un événement live et diffuse la mise à jour via WebSocket.
    """
    p_home, p_draw, p_away = _in_play_win_prob(
        minute, home_score, away_score, pre_match_home_prob, lambda_h, lambda_a
    )

    susp_delta, alert = detect_live_anomaly(
        minute, home_score, away_score,
        pre_match_fav, pre_match_fav_prob, live_volume_spike
    )

    payload = LiveUpdatePayload(
        match_id=match_id,
        minute=minute,
        home_score=home_score,
        away_score=away_score,
        event=event_type,
        prob_home=round(p_home, 4),
        prob_draw=round(p_draw, 4),
        prob_away=round(p_away, 4),
        suspicion_delta=round(susp_delta, 2),
        alert=alert,
    )

    # Diffusion WebSocket
    await ws_manager.send_to_match(str(match_id), payload.dict())

    # Si alerte critique → broadcast global dashboard
    if alert and susp_delta >= 20:
        await ws_manager.broadcast({
            "type": "LIVE_ALERT",
            "match_id": match_id,
            "alert": alert,
            "new_suspicion": min(100, current_suspicion + susp_delta),
        })

    return payload
