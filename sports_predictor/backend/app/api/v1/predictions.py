from fastapi import APIRouter, Query, HTTPException, Header
from datetime import date, datetime, timedelta
import uuid
from app.services.predictor import generate_daily_tickets, LEAGUES
from app.services.data_fetcher import get_fixtures
from app.schemas.prediction import DailyTicketsOut
from app.utils.cache import cache_get, cache_set, cache_key, cache_delete
from app.config import settings

router = APIRouter(prefix="/predictions", tags=["Predictions"])

_ticket_store: list[dict] = []


@router.get("/daily", response_model=DailyTicketsOut, summary="Get today's prediction tickets")
async def get_daily_predictions(
    target_date: date = Query(default=None, description="Date YYYY-MM-DD, défaut demain"),
    force_refresh: bool = Query(default=False),
):
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    ck = cache_key("daily_tickets", str(target_date))

    if not force_refresh:
        cached = await cache_get(ck)
        if cached:
            return cached

    tickets = await generate_daily_tickets(target_date)

    if not tickets:
        raise HTTPException(status_code=404, detail=f"Aucune prédiction disponible pour {target_date}")

    result = DailyTicketsOut(
        date=str(target_date),
        generated_at=datetime.utcnow().isoformat(),
        tickets=tickets,
        total_tickets=len(tickets),
    )

    payload = result.model_dump()
    await cache_set(ck, payload, ttl=3600 * 4)

    # Persist to in-memory store for history
    for t in tickets:
        entry = {**t, "date": str(target_date), "generated_at": payload["generated_at"]}
        if not any(e.get("ticket_number") == t["ticket_number"] and e.get("date") == str(target_date)
                   for e in _ticket_store):
            _ticket_store.append(entry)

    return result


@router.get("/trigger", summary="Déclencher la génération manuellement")
async def trigger_generation(
    target_date: date = Query(default=None),
    x_admin_key: str = Header(default=""),
):
    if settings.SECRET_KEY != "change-me-in-production" and x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Clé admin invalide")

    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    ck = cache_key("daily_tickets", str(target_date))
    await cache_delete(ck)

    tickets = await generate_daily_tickets(target_date)

    for t in tickets:
        entry = {**t, "date": str(target_date), "generated_at": datetime.utcnow().isoformat()}
        _ticket_store.append(entry)

    return {
        "message": f"{len(tickets)} tickets générés pour {target_date}",
        "tickets_count": len(tickets),
    }


@router.get("/history", summary="Historique des tickets")
async def get_history(limit: int = Query(default=50, le=200)):
    recent = list(reversed(_ticket_store))[:limit]
    return {"tickets": recent, "total": len(_ticket_store)}


@router.get("/matches/upcoming", summary="Prochains matchs")
async def get_upcoming_matches(days_ahead: int = Query(default=1, ge=1, le=7)):
    tomorrow = date.today() + timedelta(days=days_ahead)
    from_date = str(tomorrow)
    all_fixtures = []
    for league_id, season in LEAGUES:
        fixtures = await get_fixtures(league_id, season, from_date, from_date)
        all_fixtures.extend(fixtures)
    all_fixtures.sort(key=lambda x: x.get("fixture", {}).get("date", ""))
    matches = []
    for f in all_fixtures[:40]:
        fix = f.get("fixture", {})
        teams = f.get("teams", {})
        league = f.get("league", {})
        matches.append({
            "fixture_id": fix.get("id", 0),
            "home_team": teams.get("home", {}).get("name", ""),
            "away_team": teams.get("away", {}).get("name", ""),
            "league": league.get("name", ""),
            "match_time": fix.get("date", ""),
            "venue": fix.get("venue", {}).get("name", "") if isinstance(fix.get("venue"), dict) else "",
        })
    return matches
