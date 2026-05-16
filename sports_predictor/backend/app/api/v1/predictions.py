from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime, timedelta
from typing import List
from app.services.predictor import generate_daily_tickets
from app.schemas.prediction import DailyTicketsOut, TicketOut
from app.utils.cache import cache_get, cache_set, cache_key

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/daily", response_model=DailyTicketsOut, summary="Get today's prediction tickets")
async def get_daily_predictions(
    target_date: date = Query(default=None, description="Date (YYYY-MM-DD), defaults to tomorrow"),
    force_refresh: bool = Query(default=False, description="Bypass cache and regenerate"),
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
        raise HTTPException(status_code=404, detail=f"No predictions available for {target_date}")

    result = DailyTicketsOut(
        date=str(target_date),
        generated_at=datetime.utcnow().isoformat(),
        tickets=tickets,
        total_tickets=len(tickets),
    )

    await cache_set(ck, result.model_dump(), ttl=3600 * 4)
    return result


@router.get("/trigger", summary="Manually trigger daily generation (admin)")
async def trigger_generation(target_date: date = Query(default=None)):
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    tickets = await generate_daily_tickets(target_date)
    return {"message": f"Generated {len(tickets)} tickets for {target_date}", "tickets_count": len(tickets)}


@router.get("/history", summary="Get historical prediction tickets")
async def get_history(limit: int = Query(default=50, le=200)):
    ck = cache_key("history_tickets")
    cached = await cache_get(ck)
    if cached:
        return cached

    result = {"tickets": [], "total": 0}
    await cache_set(ck, result, ttl=600)
    return result


@router.get("/matches/upcoming", summary="Get upcoming matches")
async def get_upcoming_matches(league_id: int = Query(default=None)):
    from app.services.data_fetcher import DataFetcher
    async with DataFetcher() as fetcher:
        tomorrow = date.today() + timedelta(days=1)
        fixtures = await fetcher.get_fixtures(league_id or 39, tomorrow.year, str(tomorrow))
    matches = []
    for f in fixtures[:30]:
        fix = f.get("fixture", {})
        teams = f.get("teams", {})
        league = f.get("league", {})
        odds_data = f.get("odds", [{}])
        home_odds = draw_odds = away_odds = None
        if odds_data:
            vals = odds_data[0].get("values", [])
            if len(vals) >= 3:
                home_odds = float(vals[0].get("odd", 0)) or None
                draw_odds = float(vals[1].get("odd", 0)) or None
                away_odds = float(vals[2].get("odd", 0)) or None
        matches.append({
            "fixture_id": fix.get("id", 0),
            "home_team": teams.get("home", {}).get("name", ""),
            "away_team": teams.get("away", {}).get("name", ""),
            "league": league.get("name", ""),
            "match_time": fix.get("date", ""),
            "venue": fix.get("venue", {}).get("name") if isinstance(fix.get("venue"), dict) else None,
            "home_odds": home_odds,
            "draw_odds": draw_odds,
            "away_odds": away_odds,
        })
    return matches
