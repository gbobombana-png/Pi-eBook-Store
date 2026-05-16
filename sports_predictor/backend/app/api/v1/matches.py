from fastapi import APIRouter, Query
from datetime import date, timedelta
from app.services.data_fetcher import get_fixtures
from app.services.predictor import LEAGUES

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/upcoming", summary="List upcoming matches")
async def upcoming_matches(
    days_ahead: int = Query(default=1, ge=1, le=7),
):
    target = date.today() + timedelta(days=days_ahead)
    from_date = target.strftime("%Y-%m-%d")
    all_fixtures = []
    for league_id, season in LEAGUES:
        fixtures = await get_fixtures(league_id, season, from_date, from_date)
        for f in fixtures:
            all_fixtures.append({
                "id": f["fixture"]["id"],
                "date": f["fixture"]["date"],
                "home": f["teams"]["home"]["name"],
                "away": f["teams"]["away"]["name"],
                "league": f["league"]["name"],
                "round": f["league"].get("round", ""),
                "venue": f["fixture"].get("venue", {}).get("name", ""),
            })
    all_fixtures.sort(key=lambda x: x["date"])
    return {"date": from_date, "count": len(all_fixtures), "matches": all_fixtures}
