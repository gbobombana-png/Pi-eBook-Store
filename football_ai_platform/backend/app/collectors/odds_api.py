"""
Client The Odds API (gratuit: 500 req/mois)
Docs: https://the-odds-api.com/lol-odds-api/

Clé gratuite: https://the-odds-api.com/#get-access
Fonctionnalités gratuites: cotes H2H (1X2), spreads, totals
40+ bookmakers: bet365, Pinnacle, William Hill, Unibet, etc.
"""
import httpx
from datetime import datetime

BASE_URL = "https://api.the-odds-api.com/v4"

# Sports supportés
SPORT_SOCCER_KEYS = {
    "soccer_france_ligue_one":     "Ligue 1",
    "soccer_epl":                  "Premier League",
    "soccer_germany_bundesliga":   "Bundesliga",
    "soccer_spain_la_liga":        "La Liga",
    "soccer_italy_serie_a":        "Serie A",
    "soccer_uefa_champs_league":   "Champions League",
    "soccer_uefa_europa_league":   "Europa League",
}

# Bookmakers de référence (pour détection sharp money)
SHARP_BOOKMAKERS = {"pinnacle", "betfair", "betfair_ex_eu", "matchbook"}
SOFT_BOOKMAKERS  = {"bet365", "williamhill", "unibet", "bwin", "1xbet"}


class OddsAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._remaining_requests: int | None = None

    async def _get(self, path: str, params: dict | None = None) -> tuple[dict | list, dict]:
        p = {"apiKey": self.api_key, **(params or {})}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BASE_URL}{path}", params=p)
            r.raise_for_status()
            # Suivre les quotas restants
            self._remaining_requests = int(r.headers.get("x-requests-remaining", -1))
            return r.json(), dict(r.headers)

    async def get_sports(self) -> list[dict]:
        """Liste tous les sports disponibles."""
        data, _ = await self._get("/sports")
        return [s for s in data if "soccer" in s.get("key", "")]

    async def get_odds(
        self,
        sport: str = "soccer_france_ligue_one",
        regions: str = "eu",
        markets: str = "h2h,totals",
        bookmakers: str | None = None,
    ) -> list[dict]:
        """
        Récupère les cotes pour tous les matchs à venir d'un sport.
        markets: h2h (1X2) | totals (over/under) | spreads
        regions: eu | uk | us | au
        """
        params = {"regions": regions, "markets": markets, "oddsFormat": "decimal"}
        if bookmakers:
            params["bookmakers"] = bookmakers
        data, _ = await self._get(f"/sports/{sport}/odds", params)
        return data if isinstance(data, list) else []

    async def get_event_odds(
        self,
        sport: str,
        event_id: str,
        markets: str = "h2h,totals,btts",
    ) -> dict:
        """Cotes détaillées pour un événement spécifique."""
        params = {"regions": "eu", "markets": markets, "oddsFormat": "decimal"}
        data, _ = await self._get(f"/sports/{sport}/events/{event_id}/odds", params)
        return data if isinstance(data, dict) else {}

    async def get_scores(self, sport: str = "soccer_france_ligue_one", days_from: int = 1) -> list[dict]:
        """Scores récents (utile pour vérifier les prédictions)."""
        params = {"daysFrom": days_from}
        data, _ = await self._get(f"/sports/{sport}/scores", params)
        return data if isinstance(data, list) else []

    def remaining_requests(self) -> int | None:
        return self._remaining_requests

    # ── Analyse & normalisation ──────────────────────────────────────────────

    def normalize_event(self, event: dict) -> dict:
        """Extrait les cotes clés d'un événement Odds API."""
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        bookmakers = event.get("bookmakers", [])

        # Aggréger les cotes par marché sur tous les bookmakers
        h2h_lines: list[dict] = []          # {bk, home, draw, away}
        totals_lines: list[dict] = []        # {bk, over, under, point}
        btts_lines: list[dict] = []          # {bk, yes, no}

        for bk in bookmakers:
            bk_key = bk.get("key", "")
            for market in bk.get("markets", []):
                key = market.get("key", "")
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

                if key == "h2h":
                    h2h_lines.append({
                        "bookmaker": bk_key,
                        "is_sharp": bk_key in SHARP_BOOKMAKERS,
                        "home": outcomes.get(home),
                        "draw": outcomes.get("Draw"),
                        "away": outcomes.get(away),
                    })
                elif key == "totals":
                    h = outcomes.get("Over"); u = outcomes.get("Under")
                    pt = next((o.get("point") for o in market.get("outcomes", []) if o.get("name") == "Over"), 2.5)
                    if h and u:
                        totals_lines.append({"bookmaker": bk_key, "over": h, "under": u, "point": pt})
                elif key == "btts":
                    y = outcomes.get("Yes"); n = outcomes.get("No")
                    if y and n:
                        btts_lines.append({"bookmaker": bk_key, "yes": y, "no": n})

        # Consensus (moyenne sur tous les BK)
        best = self._best_odds(h2h_lines, home, away)

        # Pinnacle comme référence (sharp)
        sharp = next((l for l in h2h_lines if l["bookmaker"] == "pinnacle"), None)

        return {
            "event_id":    event.get("id"),
            "sport_key":   event.get("sport_key"),
            "home_team":   home,
            "away_team":   away,
            "commence_time": event.get("commence_time"),
            "consensus": best,
            "sharp_line": sharp,
            "bookmaker_lines": h2h_lines,
            "totals": totals_lines,
            "btts": btts_lines,
            "num_bookmakers": len(bookmakers),
        }

    def _best_odds(self, lines: list[dict], home: str, away: str) -> dict:
        """Calcule la cote consensuelle (médiane) sur tous les bookmakers."""
        if not lines:
            return {"home": 2.5, "draw": 3.2, "away": 2.5}
        homes = [l["home"] for l in lines if l.get("home")]
        draws = [l["draw"] for l in lines if l.get("draw")]
        aways = [l["away"] for l in lines if l.get("away")]
        def median(lst):
            s = sorted(lst)
            n = len(s)
            return s[n // 2] if n else 2.5
        return {"home": median(homes), "draw": median(draws), "away": median(aways)}

    def detect_sharp_move(
        self,
        history: list[dict],   # snapshots triés par timestamp
        threshold: float = 0.08,
    ) -> dict:
        """
        Compare la cote d'ouverture vs actuelle.
        Retourne la direction du mouvement sharp et son amplitude.
        """
        if len(history) < 2:
            return {"sharp": False, "direction": None, "magnitude": 0.0}

        def implied(h, d, a):
            tot = 1/h + 1/d + 1/a
            return 1/h/tot, 1/a/tot

        op = history[0]; cur = history[-1]
        oh, oa = implied(op["home"], op.get("draw", 3.2), op["away"])
        ch, ca = implied(cur["home"], cur.get("draw", 3.2), cur["away"])
        move = ch - oh
        is_sharp = abs(move) >= threshold
        direction = "home" if move > 0 else "away" if move < 0 else None
        return {"sharp": is_sharp, "direction": direction, "magnitude": abs(move)}
