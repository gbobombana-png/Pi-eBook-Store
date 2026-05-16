from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.predictor import generate_daily_tickets, LEAGUES
from app.services.data_fetcher import get_fixtures
from app.services.persistence import save_tickets, get_history
from app.schemas.prediction import DailyTicketsOut
from app.utils.cache import cache_get, cache_set, cache_key, cache_delete
from app.utils.auth import require_admin

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/daily", response_model=DailyTicketsOut, summary="Tickets de prédictions du jour")
async def get_daily_predictions(
    target_date: date = Query(default=None),
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
    await cache_set(ck, result.model_dump(), ttl=3600 * 4)
    return result


@router.get("/trigger", summary="Générer les tickets (admin)")
async def trigger_generation(
    target_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    ck = cache_key("daily_tickets", str(target_date))
    await cache_delete(ck)

    tickets = await generate_daily_tickets(target_date)
    if tickets:
        await save_tickets(tickets, target_date, db)

    return {
        "message": f"{len(tickets)} tickets générés pour {target_date}",
        "tickets_count": len(tickets),
    }


@router.get("/history", summary="Historique des tickets depuis la DB")
async def get_history_endpoint(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    tickets = await get_history(db, limit=limit)
    return {"tickets": tickets, "total": len(tickets)}


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
