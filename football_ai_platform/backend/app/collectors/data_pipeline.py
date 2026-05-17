"""
Pipeline de collecte de données.
Orchestre football-data.org + The Odds API → base de données.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from .football_data import FootballDataClient, COMPETITIONS
from .odds_api import OddsAPIClient, SPORT_SOCCER_KEYS
from ..core.config import get_settings

logger = logging.getLogger("data_pipeline")
settings = get_settings()


class DataPipeline:
    def __init__(self, fd_key: str, odds_key: str):
        self.fd    = FootballDataClient(fd_key)
        self.odds  = OddsAPIClient(odds_key)

    # ── Collecte matchs ───────────────────────────────────────────────────────

    async def fetch_upcoming_matches(
        self,
        competitions: list[str] | None = None,
        days_ahead: int = 3,
    ) -> list[dict]:
        """
        Récupère tous les matchs à venir pour les compétitions sélectionnées.
        """
        comps = competitions or ["PL", "BL1", "FL1", "PD", "SA"]
        today = datetime.utcnow().date()
        date_to = (today + timedelta(days=days_ahead)).isoformat()
        all_matches = []

        for comp in comps:
            try:
                raw = await self.fd.get_matches(
                    competition=comp,
                    date_from=today.isoformat(),
                    date_to=date_to,
                    status="SCHEDULED",
                )
                normalized = [self.fd.normalize_match(m) for m in raw]
                all_matches.extend(normalized)
                logger.info(f"  ✅ {COMPETITIONS.get(comp, comp)}: {len(normalized)} matchs")
            except Exception as e:
                logger.warning(f"  ⚠ {comp}: {e}")
            await asyncio.sleep(6.5)   # respect rate limit 10 req/min

        logger.info(f"Total matchs collectés: {len(all_matches)}")
        return all_matches

    async def fetch_live_matches(self, competitions: list[str] | None = None) -> list[dict]:
        comps = competitions or ["PL", "BL1", "FL1", "PD", "SA"]
        live = []
        for comp in comps:
            try:
                raw = await self.fd.get_matches(competition=comp, status="IN_PLAY")
                live.extend([self.fd.normalize_match(m) for m in raw])
            except Exception as e:
                logger.warning(f"  ⚠ live {comp}: {e}")
            await asyncio.sleep(6.5)
        return live

    # ── Collecte cotes ────────────────────────────────────────────────────────

    async def fetch_odds_for_sport(self, sport_key: str) -> list[dict]:
        """Récupère et normalise les cotes pour un sport donné."""
        try:
            raw = await self.odds.get_odds(
                sport=sport_key,
                regions="eu",
                markets="h2h,totals",
            )
            normalized = [self.odds.normalize_event(e) for e in raw]
            remaining = self.odds.remaining_requests()
            logger.info(
                f"  ✅ {SPORT_SOCCER_KEYS.get(sport_key, sport_key)}: "
                f"{len(normalized)} matchs | {remaining} req restantes"
            )
            return normalized
        except Exception as e:
            logger.error(f"  ⚠ Odds API {sport_key}: {e}")
            return []

    async def fetch_all_odds(self, sport_keys: list[str] | None = None) -> list[dict]:
        keys = sport_keys or list(SPORT_SOCCER_KEYS.keys())
        all_odds = []
        for k in keys:
            events = await self.fetch_odds_for_sport(k)
            all_odds.extend(events)
            await asyncio.sleep(1)
        return all_odds

    # ── Enrichissement team profile ───────────────────────────────────────────

    async def build_team_profile(self, team_id: int, team_name: str) -> dict:
        """
        Construit un profil complet d'équipe depuis l'historique récent.
        """
        try:
            recent = await self.fd.get_team_matches(team_id, last_n=10, status="FINISHED")
            form = self.fd.extract_team_form(recent, team_id)

            goals_scored = []
            goals_conceded = []
            for m in recent:
                s = m.get("score", {}).get("fullTime", {})
                h_id = m.get("homeTeam", {}).get("id")
                gf = s.get("home", 0) if h_id == team_id else s.get("away", 0)
                ga = s.get("away", 0) if h_id == team_id else s.get("home", 0)
                if gf is not None: goals_scored.append(gf)
                if ga is not None: goals_conceded.append(ga)

            avg_scored   = sum(goals_scored) / len(goals_scored)   if goals_scored   else 1.4
            avg_conceded = sum(goals_conceded) / len(goals_conceded) if goals_conceded else 1.4

            return {
                "name": team_name,
                "team_id": team_id,
                "avg_goals_scored": round(avg_scored, 2),
                "avg_goals_conceded": round(avg_conceded, 2),
                "avg_xg_for": round(avg_scored * 0.92, 2),
                "avg_xg_against": round(avg_conceded * 0.92, 2),
                "home_avg_scored": round(avg_scored * 1.15, 2),
                "home_avg_conceded": round(avg_conceded * 0.85, 2),
                "away_avg_scored": round(avg_scored * 0.85, 2),
                "away_avg_conceded": round(avg_conceded * 1.15, 2),
                "form": form,
                "games": len(recent),
                "injuries": [],
            }
        except Exception as e:
            logger.warning(f"  ⚠ build_team_profile {team_name}: {e}")
            return {"name": team_name, "avg_goals_scored": 1.4, "avg_goals_conceded": 1.4,
                    "avg_xg_for": 1.3, "avg_xg_against": 1.3, "form": "DDDDD",
                    "home_avg_scored": 1.6, "home_avg_conceded": 1.2,
                    "away_avg_scored": 1.2, "away_avg_conceded": 1.6,
                    "games": 0, "injuries": []}

    async def build_h2h(self, match_id_fd: int) -> dict:
        """Construit le record H2H depuis football-data.org."""
        try:
            data = await self.fd.get_head_to_head(match_id_fd, limit=15)
            matches = data.get("matches", [])
            agg = data.get("aggregates", {})
            home_wins = agg.get("homeTeam", {}).get("wins", 0)
            away_wins = agg.get("awayTeam", {}).get("wins", 0)
            draws = len(matches) - home_wins - away_wins

            total_goals = sum(
                (m.get("score", {}).get("fullTime", {}).get("home", 0) or 0) +
                (m.get("score", {}).get("fullTime", {}).get("away", 0) or 0)
                for m in matches
            )
            avg_goals = total_goals / len(matches) if matches else 2.5

            return {
                "home_wins": home_wins,
                "draws": max(0, draws),
                "away_wins": away_wins,
                "avg_goals": round(avg_goals, 2),
            }
        except Exception as e:
            logger.warning(f"  ⚠ H2H {match_id_fd}: {e}")
            return {"home_wins": 0, "draws": 0, "away_wins": 0, "avg_goals": 2.5}

    # ── Pipeline complet ──────────────────────────────────────────────────────

    async def run_full_collection(
        self,
        competitions: list[str] | None = None,
        sport_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Lance la collecte complète:
        1. Matchs à venir (football-data.org)
        2. Cotes (The Odds API)
        3. Corrèle les matchs avec leurs cotes
        """
        logger.info("=== Démarrage collecte de données ===")

        # 1. Matchs
        logger.info("📅 Collecte des matchs...")
        matches = await self.fetch_upcoming_matches(competitions)

        # 2. Cotes
        logger.info("💰 Collecte des cotes...")
        all_odds = await self.fetch_all_odds(sport_keys)

        # 3. Corrélation matchs ↔ cotes (par nom d'équipe, fuzzy)
        enriched = []
        for match in matches:
            odds = self._find_odds_for_match(match, all_odds)
            enriched.append({**match, "odds": odds})

        logger.info(f"✅ Collection terminée: {len(enriched)} matchs enrichis")
        logger.info(f"   Quota Odds API restant: {self.odds.remaining_requests()} req")
        return {
            "collected_at": datetime.utcnow().isoformat(),
            "matches": enriched,
            "total": len(enriched),
        }

    def _find_odds_for_match(self, match: dict, odds_events: list[dict]) -> dict | None:
        """Corrèle un match football-data avec un event Odds API (matching par nom)."""
        home = match["home_team"].lower()
        away = match["away_team"].lower()

        best_score = 0
        best_event = None

        for ev in odds_events:
            h2 = ev["home_team"].lower()
            a2 = ev["away_team"].lower()
            score = (
                self._fuzzy_score(home, h2) +
                self._fuzzy_score(away, a2)
            )
            if score > best_score:
                best_score = score
                best_event = ev

        if best_score >= 1.5:
            return best_event
        return None

    @staticmethod
    def _fuzzy_score(a: str, b: str) -> float:
        """Score de similarité simplifié entre deux noms d'équipes."""
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return 0.0
        inter = a_words & b_words
        return len(inter) / max(len(a_words), len(b_words))
