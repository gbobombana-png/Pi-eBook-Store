"""
Data fetcher — API-Football (primary) → football-data.org (free fallback) → rich demo data.
"""
import httpx
import random
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

# ---------------------------------------------------------------------------
# football-data.org free API
# ---------------------------------------------------------------------------
FD_BASE = "https://api.football-data.org/v4"
FD_LEAGUE_MAP = {
    39: "PL",    # Premier League
    140: "PD",   # La Liga
    61: "FL1",   # Ligue 1
    78: "BL1",   # Bundesliga
    135: "SA",   # Serie A
    2: "CL",     # Champions League
}


async def _fd_get_fixtures(league_id: int, from_date: str, to_date: str) -> list[dict]:
    token = getattr(settings, "FOOTBALL_DATA_TOKEN", None)
    if not token:
        return []
    competition = FD_LEAGUE_MAP.get(league_id)
    if not competition:
        return []
    ck = cache_key("fd", competition, from_date, to_date)
    cached = await cache_get(ck)
    if cached:
        return cached
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{FD_BASE}/competitions/{competition}/matches",
                headers={"X-Auth-Token": token},
                params={"dateFrom": from_date, "dateTo": to_date, "status": "SCHEDULED"},
            )
            resp.raise_for_status()
            matches = resp.json().get("matches", [])
            fixtures = [_fd_to_apifootball(m, league_id) for m in matches]
            await cache_set(ck, fixtures)
            return fixtures
    except Exception as e:
        logger.warning(f"football-data.org error for {competition}: {e}")
        return []


def _fd_to_apifootball(m: dict, league_id: int) -> dict:
    """Convert football-data.org match format to API-Football format."""
    utc_date = m.get("utcDate", "")
    home = m.get("homeTeam", {})
    away = m.get("awayTeam", {})
    comp = m.get("competition", {})
    return {
        "fixture": {
            "id": m.get("id", 0),
            "date": utc_date,
            "venue": {"name": "", "city": ""},
        },
        "league": {
            "id": league_id,
            "name": comp.get("name", ""),
            "country": "",
            "round": m.get("matchday", ""),
        },
        "teams": {
            "home": {"id": home.get("id", 0), "name": home.get("name", ""), "logo": ""},
            "away": {"id": away.get("id", 0), "name": away.get("name", ""), "logo": ""},
        },
        "goals": {"home": None, "away": None},
        "score": {"halftime": {"home": None, "away": None}},
    }


# ---------------------------------------------------------------------------
# API-Football primary fetcher
# ---------------------------------------------------------------------------

async def _request(endpoint: str, params: dict) -> Optional[dict]:
    ck = cache_key("api", endpoint, str(sorted(params.items())))
    cached = await cache_get(ck)
    if cached:
        return cached

    if not settings.API_FOOTBALL_KEY:
        return None  # caller will decide fallback

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
    # 1) Try API-Football
    data = await _request("fixtures", {
        "league": league_id, "season": season,
        "from": from_date, "to": to_date, "status": "NS",
    })
    if data:
        return data.get("response", [])

    # 2) Try football-data.org (free)
    fd_fixtures = await _fd_get_fixtures(league_id, from_date, to_date)
    if fd_fixtures:
        return fd_fixtures

    # 3) Rich demo data
    return _demo_fixtures(league_id, from_date, to_date)


async def get_team_statistics(team_id: int, league_id: int, season: int) -> Optional[dict]:
    data = await _request("teams/statistics", {
        "team": team_id, "league": league_id, "season": season,
    })
    return data.get("response") if data else _demo_team_stats(team_id)


async def get_head_to_head(team1_id: int, team2_id: int, last: int = 10) -> list[dict]:
    data = await _request("fixtures/headtohead", {
        "h2h": f"{team1_id}-{team2_id}", "last": last,
    })
    return data.get("response", []) if data else _demo_h2h(team1_id, team2_id)


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
    data = await _request("odds", {"fixture": fixture_id, "bookmaker": 6})
    return data.get("response", []) if data else _demo_odds()


async def get_fixture_predictions(fixture_id: int) -> Optional[dict]:
    data = await _request("predictions", {"fixture": fixture_id})
    resp = data.get("response", [])
    return resp[0] if resp else None


# ---------------------------------------------------------------------------
# Rich demo data — realistic teams, venues, varied matches
# ---------------------------------------------------------------------------

_LEAGUE_TEAMS: dict[int, list[dict]] = {
    39: [  # Premier League
        {"id": 40, "name": "Liverpool", "venue": "Anfield"},
        {"id": 33, "name": "Manchester United", "venue": "Old Trafford"},
        {"id": 50, "name": "Manchester City", "venue": "Etihad Stadium"},
        {"id": 42, "name": "Arsenal", "venue": "Emirates Stadium"},
        {"id": 47, "name": "Tottenham", "venue": "Tottenham Hotspur Stadium"},
        {"id": 49, "name": "Chelsea", "venue": "Stamford Bridge"},
        {"id": 66, "name": "Aston Villa", "venue": "Villa Park"},
        {"id": 34, "name": "Newcastle", "venue": "St. James' Park"},
        {"id": 51, "name": "Brighton", "venue": "Amex Stadium"},
        {"id": 45, "name": "Everton", "venue": "Goodison Park"},
    ],
    140: [  # La Liga
        {"id": 541, "name": "Real Madrid", "venue": "Santiago Bernabéu"},
        {"id": 529, "name": "Barcelona", "venue": "Spotify Camp Nou"},
        {"id": 530, "name": "Atlético Madrid", "venue": "Civitas Metropolitano"},
        {"id": 532, "name": "Sevilla", "venue": "Ramón Sánchez-Pizjuán"},
        {"id": 533, "name": "Villarreal", "venue": "Estadio de la Cerámica"},
        {"id": 548, "name": "Real Sociedad", "venue": "Reale Arena"},
        {"id": 543, "name": "Real Betis", "venue": "Benito Villamarín"},
        {"id": 546, "name": "Athletic Club", "venue": "San Mamés"},
    ],
    61: [  # Ligue 1
        {"id": 85, "name": "Paris Saint-Germain", "venue": "Parc des Princes"},
        {"id": 91, "name": "Monaco", "venue": "Stade Louis II"},
        {"id": 80, "name": "Lyon", "venue": "Groupama Stadium"},
        {"id": 81, "name": "Marseille", "venue": "Stade Vélodrome"},
        {"id": 84, "name": "Nice", "venue": "Allianz Riviera"},
        {"id": 94, "name": "Rennes", "venue": "Roazhon Park"},
        {"id": 93, "name": "Lens", "venue": "Stade Bollaert-Delelis"},
        {"id": 79, "name": "Lille", "venue": "Stade Pierre-Mauroy"},
    ],
    78: [  # Bundesliga
        {"id": 157, "name": "Bayern München", "venue": "Allianz Arena"},
        {"id": 165, "name": "Borussia Dortmund", "venue": "Signal Iduna Park"},
        {"id": 168, "name": "Bayer Leverkusen", "venue": "BayArena"},
        {"id": 173, "name": "RB Leipzig", "venue": "Red Bull Arena"},
        {"id": 169, "name": "Eintracht Frankfurt", "venue": "Deutsche Bank Park"},
        {"id": 161, "name": "VfB Stuttgart", "venue": "MHPArena"},
        {"id": 163, "name": "Borussia M'gladbach", "venue": "Borussia-Park"},
        {"id": 172, "name": "Union Berlin", "venue": "Stadion An der Alten Försterei"},
    ],
    135: [  # Serie A
        {"id": 489, "name": "AC Milan", "venue": "San Siro"},
        {"id": 505, "name": "Inter Milan", "venue": "San Siro"},
        {"id": 496, "name": "Juventus", "venue": "Allianz Stadium"},
        {"id": 497, "name": "AS Roma", "venue": "Stadio Olimpico"},
        {"id": 492, "name": "Napoli", "venue": "Diego Armando Maradona"},
        {"id": 487, "name": "Lazio", "venue": "Stadio Olimpico"},
        {"id": 500, "name": "Fiorentina", "venue": "Stadio Artemio Franchi"},
        {"id": 488, "name": "Atalanta", "venue": "Gewiss Stadium"},
    ],
    2: [  # Champions League (use some top clubs)
        {"id": 541, "name": "Real Madrid", "venue": "Santiago Bernabéu"},
        {"id": 50, "name": "Manchester City", "venue": "Etihad Stadium"},
        {"id": 157, "name": "Bayern München", "venue": "Allianz Arena"},
        {"id": 529, "name": "Barcelona", "venue": "Spotify Camp Nou"},
        {"id": 505, "name": "Inter Milan", "venue": "San Siro"},
        {"id": 40, "name": "Liverpool", "venue": "Anfield"},
        {"id": 168, "name": "Bayer Leverkusen", "venue": "BayArena"},
        {"id": 85, "name": "Paris Saint-Germain", "venue": "Parc des Princes"},
    ],
}

_LEAGUE_NAMES = {
    39: ("Premier League", "England"),
    140: ("La Liga", "Spain"),
    61: ("Ligue 1", "France"),
    78: ("Bundesliga", "Germany"),
    135: ("Serie A", "Italy"),
    2: ("Champions League", "Europe"),
}

_MATCH_HOURS = [13, 15, 16, 18, 20, 21]


def _demo_fixtures(league_id: int, from_date: str, to_date: str) -> list[dict]:
    teams = _LEAGUE_TEAMS.get(league_id, [])
    if len(teams) < 2:
        return []

    league_name, country = _LEAGUE_NAMES.get(league_id, ("Unknown", ""))
    start = datetime.strptime(from_date, "%Y-%m-%d").date()
    end = datetime.strptime(to_date, "%Y-%m-%d").date()
    days = (end - start).days + 1

    rng = random.Random(league_id + start.toordinal())
    shuffled = teams[:]
    rng.shuffle(shuffled)

    fixtures = []
    fix_id = league_id * 10000 + start.toordinal()
    pairs_per_day = max(1, len(shuffled) // (2 * max(days, 1)))

    for day_offset in range(days):
        match_date = start + timedelta(days=day_offset)
        day_teams = shuffled[:]
        rng.shuffle(day_teams)
        for i in range(0, min(len(day_teams) - 1, pairs_per_day * 2), 2):
            home = day_teams[i]
            away = day_teams[i + 1]
            hour = _MATCH_HOURS[rng.randint(0, len(_MATCH_HOURS) - 1)]
            kickoff = f"{match_date}T{hour:02d}:00:00+00:00"
            fixtures.append({
                "fixture": {
                    "id": fix_id,
                    "date": kickoff,
                    "venue": {"name": home["venue"], "city": ""},
                },
                "league": {
                    "id": league_id,
                    "name": league_name,
                    "country": country,
                    "round": f"Round {rng.randint(30, 38)}",
                },
                "teams": {
                    "home": {"id": home["id"], "name": home["name"], "logo": ""},
                    "away": {"id": away["id"], "name": away["name"], "logo": ""},
                },
                "goals": {"home": None, "away": None},
                "score": {"halftime": {"home": None, "away": None}},
            })
            fix_id += 1

    return fixtures


def _demo_team_stats(team_id: int) -> dict:
    rng = random.Random(team_id)
    wins = rng.randint(10, 22)
    draws = rng.randint(4, 10)
    losses = rng.randint(2, 10)
    played = wins + draws + losses
    gf = rng.randint(30, 70)
    ga = rng.randint(20, 55)
    return {
        "team": {"id": team_id, "name": "Team"},
        "fixtures": {
            "played": {"home": played // 2, "away": played // 2, "total": played},
            "wins": {"home": wins // 2, "away": wins - wins // 2, "total": wins},
            "draws": {"home": draws // 2, "away": draws - draws // 2, "total": draws},
            "loses": {"home": losses // 2, "away": losses - losses // 2, "total": losses},
        },
        "goals": {
            "for": {
                "average": {"home": f"{gf/played*1.2:.1f}", "away": f"{gf/played*0.8:.1f}", "total": f"{gf/played:.1f}"},
                "total": {"home": int(gf * 0.6), "away": int(gf * 0.4)},
            },
            "against": {
                "average": {"home": f"{ga/played*0.8:.1f}", "away": f"{ga/played*1.2:.1f}", "total": f"{ga/played:.1f}"},
                "total": {"home": int(ga * 0.4), "away": int(ga * 0.6)},
            },
        },
        "biggest": {"streak": {"wins": rng.randint(3, 8), "draws": rng.randint(1, 3), "loses": rng.randint(1, 3)}},
        "clean_sheet": {"home": rng.randint(4, 12), "away": rng.randint(2, 8), "total": rng.randint(6, 18)},
        "failed_to_score": {"home": rng.randint(1, 5), "away": rng.randint(2, 7), "total": rng.randint(3, 10)},
    }


def _demo_h2h(team1_id: int, team2_id: int) -> list[dict]:
    rng = random.Random(team1_id + team2_id)
    results = []
    for i in range(5):
        past = (datetime.utcnow() - timedelta(days=60 * (i + 1))).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        h_goals = rng.randint(0, 3)
        a_goals = rng.randint(0, 3)
        results.append({
            "fixture": {"id": 8000 + i, "date": past},
            "teams": {
                "home": {"id": team1_id, "name": "Home", "winner": h_goals > a_goals},
                "away": {"id": team2_id, "name": "Away", "winner": a_goals > h_goals},
            },
            "goals": {"home": h_goals, "away": a_goals},
        })
    return results


def _demo_odds() -> list[dict]:
    return [{
        "bookmakers": [{
            "id": 6, "name": "Bet365",
            "bets": [
                {"id": 1, "name": "Match Winner", "values": [
                    {"value": "Home", "odd": "1.85"},
                    {"value": "Draw", "odd": "3.50"},
                    {"value": "Away", "odd": "4.20"},
                ]},
                {"id": 5, "name": "Goals Over/Under", "values": [
                    {"value": "Over 2.5", "odd": "1.75"},
                    {"value": "Under 2.5", "odd": "2.05"},
                ]},
                {"id": 8, "name": "Both Teams Score", "values": [
                    {"value": "Yes", "odd": "1.70"},
                    {"value": "No", "odd": "2.10"},
                ]},
            ],
        }],
    }]
