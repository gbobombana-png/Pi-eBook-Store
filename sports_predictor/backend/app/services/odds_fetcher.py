"""
TheOddsAPI integration — fetches live odds from multiple bookmakers.
Falls back to mock data when ODDS_API_KEY is not set.
"""
import httpx
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger
from app.utils.cache import cache_get, cache_set, cache_key

logger = get_logger(__name__)


async def get_live_odds(sport: str = "soccer", region: str = "eu") -> list[dict]:
    ck = cache_key("odds", sport, region)
    cached = await cache_get(ck)
    if cached:
        return cached

    if not settings.ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set — returning mock odds")
        return _mock_live_odds()

    url = f"{settings.ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        "apiKey": settings.ODDS_API_KEY,
        "regions": region,
        "markets": "h2h,totals,btts",
        "oddsFormat": "decimal",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            await cache_set(ck, data, ttl=300)  # 5-min cache for live odds
            return data
    except httpx.HTTPError as e:
        logger.error(f"TheOddsAPI error: {e}")
        return _mock_live_odds()


def extract_odds(raw: dict) -> dict:
    """Normalize raw odds into a unified format."""
    result = {"home": None, "draw": None, "away": None, "over25": None, "under25": None, "btts_yes": None, "btts_no": None}
    for bm in raw.get("bookmakers", []):
        for market in bm.get("markets", []):
            key = market.get("key")
            outcomes = {o["name"]: float(o["price"]) for o in market.get("outcomes", [])}
            if key == "h2h":
                teams = list(outcomes.keys())
                if len(teams) >= 2:
                    result["home"] = result["home"] or outcomes.get(teams[0])
                    result["draw"] = result["draw"] or outcomes.get("Draw")
                    result["away"] = result["away"] or outcomes.get(teams[1])
            elif key == "totals":
                result["over25"] = result["over25"] or outcomes.get("Over")
                result["under25"] = result["under25"] or outcomes.get("Under")
            elif key == "btts":
                result["btts_yes"] = result["btts_yes"] or outcomes.get("Yes")
                result["btts_no"] = result["btts_no"] or outcomes.get("No")
        if all(v is not None for v in [result["home"], result["draw"], result["away"]]):
            break
    return result


def implied_probability(odds: float) -> float:
    """Convert decimal odds to implied probability."""
    if not odds or odds <= 1.0:
        return 0.0
    return round(1 / odds, 4)


def _mock_live_odds() -> list[dict]:
    return [
        {
            "id": "mock_1001",
            "sport_key": "soccer_epl",
            "home_team": "Liverpool",
            "away_team": "Manchester United",
            "bookmakers": [
                {
                    "key": "bet365",
                    "markets": [
                        {"key": "h2h", "outcomes": [
                            {"name": "Liverpool", "price": 1.85},
                            {"name": "Draw", "price": 3.50},
                            {"name": "Manchester United", "price": 4.20},
                        ]},
                        {"key": "totals", "outcomes": [
                            {"name": "Over", "price": 1.75},
                            {"name": "Under", "price": 2.05},
                        ]},
                        {"key": "btts", "outcomes": [
                            {"name": "Yes", "price": 1.70},
                            {"name": "No", "price": 2.10},
                        ]},
                    ],
                }
            ],
        }
    ]
