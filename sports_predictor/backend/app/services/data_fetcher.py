"""
API-Football data fetcher.
When API_FOOTBALL_KEY is not set, returns realistic mock data for development.
"""
import httpx
from datetime import date, datetime, timedelta
from typing import Any, Optional
from app.config import settings
from app.utils.logger import get_logger
from app.utils.cache import cache_get, cache_set, cache_key

logger = get_logger(__name__)

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": settings.API_FOOTBALL_KEY or "",
    "X-RapidAPI-Host": settings.API_FOOTBALL_HOST,
}


async def _request(endpoint: str, params: dict) -> Optional[dict]:
    ck = cache_key("api", endpoint, str(sorted(params.items())))
    cached = await cache_get(ck)
    if cached:
        return cached

    if not settings.API_FOOTBALL_KEY:
        logger.warning("API_FOOTBALL_KEY not set — returning mock data")
        return _mock_response(endpoint, params)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params)
            resp.raise_for_status()
            data = resp.json()
            await cache_set(ck, data)
            return data
    except httpx.HTTPError as e:
        logger.error(f"API-Football HTTP error: {e}")
        return None


async def get_fixtures(league_id: int, season: int, from_date: str, to_date: str) -> list[dict]:
    data = await _request("fixtures", {
        "league": league_id, "season": season,
        "from": from_date, "to": to_date, "status": "NS",
    })
    return data.get("response", []) if data else []


async def get_team_statistics(team_id: int, league_id: int, season: int) -> Optional[dict]:
    data = await _request("teams/statistics", {
        "team": team_id, "league": league_id, "season": season,
    })
    return data.get("response") if data else None


async def get_head_to_head(team1_id: int, team2_id: int, last: int = 10) -> list[dict]:
    data = await _request("fixtures/headtohead", {
        "h2h": f"{team1_id}-{team2_id}", "last": last,
    })
    return data.get("response", []) if data else []


async def get_team_injuries(team_id: int, fixture_id: int) -> list[dict]:
    data = await _request("injuries", {"team": team_id, "fixture": fixture_id})
    return data.get("response", []) if data else []


async def get_standings(league_id: int, season: int) -> list[dict]:
    data = await _request("standings", {"league": league_id, "season": season})
    try:
        return data["response"][0]["league"]["standings"][0]
    except (KeyError, IndexError, TypeError):
        return []


async def get_fixture_odds(fixture_id: int) -> list[dict]:
    data = await _request("odds", {"fixture": fixture_id, "bookmaker": 6})  # 6 = Bet365
    return data.get("response", []) if data else []


async def get_fixture_predictions(fixture_id: int) -> Optional[dict]:
    data = await _request("predictions", {"fixture": fixture_id})
    resp = data.get("response", [])
    return resp[0] if resp else None


# ---------------------------------------------------------------------------
# Mock data for development (no API key needed)
# ---------------------------------------------------------------------------

def _mock_response(endpoint: str, params: dict) -> dict:
    if endpoint == "fixtures":
        return {"response": _mock_fixtures()}
    if endpoint == "teams/statistics":
        return {"response": _mock_team_stats()}
    if endpoint == "fixtures/headtohead":
        return {"response": _mock_h2h()}
    if endpoint == "standings":
        return {"response": [{"league": {"standings": [_mock_standings()]}}]}
    if endpoint == "odds":
        return {"response": _mock_odds()}
    return {"response": []}


def _mock_fixtures() -> list[dict]:
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return [
        {
            "fixture": {"id": 1001, "date": tomorrow, "venue": {"name": "Anfield", "city": "Liverpool"}},
            "league": {"id": 39, "name": "Premier League", "country": "England", "round": "Round 35"},
            "teams": {
                "home": {"id": 40, "name": "Liverpool", "logo": ""},
                "away": {"id": 33, "name": "Manchester United", "logo": ""},
            },
            "goals": {"home": None, "away": None},
            "score": {"halftime": {"home": None, "away": None}},
        },
        {
            "fixture": {"id": 1002, "date": tomorrow, "venue": {"name": "Santiago Bernabeu", "city": "Madrid"}},
            "league": {"id": 140, "name": "La Liga", "country": "Spain", "round": "Round 35"},
            "teams": {
                "home": {"id": 541, "name": "Real Madrid", "logo": ""},
                "away": {"id": 529, "name": "Barcelona", "logo": ""},
            },
            "goals": {"home": None, "away": None},
            "score": {"halftime": {"home": None, "away": None}},
        },
    ]


def _mock_team_stats() -> dict:
    return {
        "team": {"id": 40, "name": "Liverpool"},
        "fixtures": {
            "played": {"home": 17, "away": 17, "total": 34},
            "wins": {"home": 12, "away": 9, "total": 21},
            "draws": {"home": 3, "away": 4, "total": 7},
            "loses": {"home": 2, "away": 4, "total": 6},
        },
        "goals": {
            "for": {"average": {"home": "2.4", "away": "1.8", "total": "2.1"},
                    "total": {"home": 41, "away": 31}},
            "against": {"average": {"home": "0.9", "away": "1.3", "total": "1.1"},
                        "total": {"home": 15, "away": 22}},
        },
        "biggest": {"streak": {"wins": 7, "draws": 2, "loses": 2}},
        "clean_sheet": {"home": 9, "away": 6, "total": 15},
        "failed_to_score": {"home": 1, "away": 3, "total": 4},
    }


def _mock_h2h() -> list[dict]:
    return [
        {
            "fixture": {"id": 900 + i, "date": f"2024-0{i+1}-15T15:00:00+00:00"},
            "teams": {
                "home": {"id": 40, "name": "Liverpool", "winner": i % 2 == 0},
                "away": {"id": 33, "name": "Manchester United", "winner": i % 2 != 0},
            },
            "goals": {"home": 2 + (i % 2), "away": 1 + ((i + 1) % 2)},
        }
        for i in range(5)
    ]


def _mock_standings() -> list[dict]:
    teams = [
        (40, "Liverpool", 72, 21, 9, 4, 68, 37),
        (50, "Manchester City", 70, 20, 10, 4, 65, 40),
        (42, "Arsenal", 68, 20, 8, 6, 62, 35),
    ]
    return [
        {
            "rank": i + 1,
            "team": {"id": t[0], "name": t[1]},
            "points": t[2],
            "goalsDiff": t[4] - t[5],
            "all": {"played": sum(t[3:6]), "win": t[3], "draw": t[4], "lose": t[5],
                    "goals": {"for": t[6], "against": t[7]}},
        }
        for i, t in enumerate(teams)
    ]


def _mock_odds() -> list[dict]:
    return [
        {
            "bookmakers": [
                {
                    "id": 6, "name": "Bet365",
                    "bets": [
                        {"id": 1, "name": "Match Winner",
                         "values": [
                             {"value": "Home", "odd": "1.85"},
                             {"value": "Draw", "odd": "3.50"},
                             {"value": "Away", "odd": "4.20"},
                         ]},
                        {"id": 5, "name": "Goals Over/Under",
                         "values": [
                             {"value": "Over 2.5", "odd": "1.75"},
                             {"value": "Under 2.5", "odd": "2.05"},
                         ]},
                        {"id": 8, "name": "Both Teams Score",
                         "values": [
                             {"value": "Yes", "odd": "1.70"},
                             {"value": "No", "odd": "2.10"},
                         ]},
                    ],
                }
            ]
        }
    ]
