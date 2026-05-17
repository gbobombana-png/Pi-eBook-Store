from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.websocket_manager import ws_manager
from ..services.live_analyzer import process_live_event
from ..models.db_models import Match, LiveEvent

router = APIRouter(prefix="/live", tags=["live"])


@router.websocket("/ws/{match_id}")
async def match_websocket(websocket: WebSocket, match_id: str):
    """
    WebSocket pour recevoir les mises à jour live d'un match.
    Le client s'abonne à un match_id spécifique.
    """
    await ws_manager.connect(websocket, match_id)
    try:
        while True:
            # Maintenir la connexion ouverte; le serveur pousse les updates
            data = await websocket.receive_text()
            # Optionnel: traiter les pings client
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, match_id)


@router.websocket("/ws/dashboard/global")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket global pour les alertes dashboard."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.post("/event/{match_id}")
async def push_live_event(
    match_id: int,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint appelé par le collecteur de données pour pousser un événement live.
    Body:
    {
      "minute": 67,
      "home_score": 1,
      "away_score": 0,
      "event_type": "goal",
      "team": "home",
      "player": "Mbappé",
      "pre_match_home_prob": 0.52,
      "lambda_h": 1.6,
      "lambda_a": 1.1,
      "live_volume_spike": 2.5,
      "pre_match_fav": "home",
      "pre_match_fav_prob": 0.52,
      "current_suspicion": 15.0
    }
    """
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(404, "Match not found")

    minute     = body.get("minute", 0)
    home_score = body.get("home_score", 0)
    away_score = body.get("away_score", 0)

    payload = await process_live_event(
        match_id=match_id,
        minute=minute,
        home_score=home_score,
        away_score=away_score,
        event_type=body.get("event_type", "update"),
        pre_match_home_prob=body.get("pre_match_home_prob", 0.5),
        lambda_h=body.get("lambda_h", 1.5),
        lambda_a=body.get("lambda_a", 1.2),
        live_volume_spike=body.get("live_volume_spike", 1.0),
        pre_match_fav=body.get("pre_match_fav", "home"),
        pre_match_fav_prob=body.get("pre_match_fav_prob", 0.5),
        current_suspicion=body.get("current_suspicion", 0.0),
    )

    # Persister l'event en DB
    event = LiveEvent(
        match_id=match_id,
        minute=minute,
        event_type=body.get("event_type", "update"),
        team=body.get("team", ""),
        player=body.get("player"),
        description=body.get("description"),
        prob_home_win_after=payload.prob_home,
        prob_draw_after=payload.prob_draw,
        prob_away_win_after=payload.prob_away,
        suspicion_delta=payload.suspicion_delta,
    )
    db.add(event)

    # Mettre à jour le score en DB
    match.home_score = home_score
    match.away_score = away_score

    await db.commit()
    return payload.dict()


@router.get("/status")
async def ws_status():
    return {
        "active_connections": ws_manager.active_connections(),
        "status": "operational",
    }
