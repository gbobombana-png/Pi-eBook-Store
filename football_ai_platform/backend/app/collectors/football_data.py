"""
Client football-data.org (API gratuite)
Docs: https://www.football-data.org/documentation/quickstart

Clé gratuite: https://www.football-data.org/client/register
Limite: 10 req/min | Ligues: PL, Bundesliga, Ligue 1, Liga, Serie A, UCL...
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from ..core.config import get_settings

BASE_URL = "https://api.football-data.org/v4"

# Codes des compétitions disponibles en gratuit
COMPETITIONS = {
    "PL":  "Premier League",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "PD":  "La Liga",
    "SA":  "Serie A",
    "CL":  "Champions League",
    "EC":  "Euro",
    "WC":  "Coupe du Monde",
}


class FootballDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
        self._last_request = 0.0
        self._min_interval = 6.5  # 10 req/min → 1 req / 6s

    async def _get(self, path: str, params: dict | None = None) -> dict:
        # Respect rate limit (10 req/min)
        now = asyncio.get_event_loop().time()
        wait = self._min_interval - (now - self._last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = asyncio.get_event_loop().time()

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{BASE_URL}{path}",
                headers=self.headers,
                params=params or {},
            )
            r.raise_for_status()
            return r.json()

    async def get_matches(
        self,
        competition: str = "PL",
        date_from: str | None = None,
        date_to: str | None = None,
        status: str = "SCHEDULED",
    ) -> list[dict]:
        """
        Récupère les matchs d'une compétition.
        status: SCHEDULED | LIVE | IN_PLAY | PAUSED | FINISHED
        """
        today = datetime.utcnow().date()
        params = {
            "status": status,
            "dateFrom": date_from or today.isoformat(),
            "dateTo": date_to or (today + timedelta(days=7)).isoformat(),
        }
        data = await self._get(f"/competitions/{competition}/matches", params)
        return data.get("matches", [])

    async def get_match(self, match_id: int) -> dict:
        return await self._get(f"/matches/{match_id}")

    async def get_standings(self, competition: str = "PL") -> list[dict]:
        data = await self._get(f"/competitions/{competition}/standings")
        return data.get("standings", [])

    async def get_team_matches(
        self,
        team_id: int,
        last_n: int = 10,
        status: str = "FINISHED",
    ) -> list[dict]:
        params = {"status": status, "limit": last_n}
        data = await self._get(f"/teams/{team_id}/matches", params)
        return data.get("matches", [])

    async def get_head_to_head(self, match_id: int, limit: int = 10) -> dict:
        params = {"limit": limit}
        data = await self._get(f"/matches/{match_id}/head2head", params)
        return data

    # ── Transformations → format interne ─────────────────────────────────────

    def normalize_match(self, raw: dict) -> dict:
        """Convertit un match football-data.org → format MatchCreate interne."""
        home = raw.get("homeTeam", {})
        away = raw.get("awayTeam", {})
        score = raw.get("score", {})
        full = score.get("fullTime", {})
        competition = raw.get("competition", {})

        status_map = {
            "SCHEDULED": "scheduled",
            "LIVE": "live",
            "IN_PLAY": "live",
            "PAUSED": "live",
            "FINISHED": "finished",
            "CANCELLED": "cancelled",
            "POSTPONED": "cancelled",
        }

        return {
            "external_id": f"fd_{raw['id']}",
            "competition": competition.get("name", "Unknown"),
            "season": str(raw.get("season", {}).get("id", "2024")),
            "match_date": raw.get("utcDate", datetime.utcnow().isoformat()),
            "status": status_map.get(raw.get("status", "SCHEDULED"), "scheduled"),
            "home_team": home.get("name", "Unknown"),
            "away_team": away.get("name", "Unknown"),
            "home_team_id": home.get("id"),
            "away_team_id": away.get("id"),
            "home_score": full.get("home"),
            "away_score": full.get("away"),
            "fd_match_id": raw["id"],
        }

    def extract_team_form(self, matches: list[dict], team_id: int) -> str:
        """Extrait la forme récente (ex: 'WWDLL') depuis les derniers matchs."""
        form = []
        for m in sorted(matches, key=lambda x: x.get("utcDate", ""), reverse=True)[:5]:
            score = m.get("score", {}).get("fullTime", {})
            home_id = m.get("homeTeam", {}).get("id")
            h = score.get("home", 0) or 0
            a = score.get("away", 0) or 0
            if home_id == team_id:
                form.append("W" if h > a else "D" if h == a else "L")
            else:
                form.append("W" if a > h else "D" if h == a else "L")
        return "".join(reversed(form)) or "DDDDD"
