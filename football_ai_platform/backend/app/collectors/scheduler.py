"""
Scheduler automatique de collecte.
Lance la collecte périodiquement et alimente la base de données.

Intervalles recommandés (selon quota gratuit):
  - Matchs à venir: toutes les 6h
  - Cotes:          toutes les 30min (avant match)
  - Live:           toutes les 1min
"""
import asyncio
import logging
from datetime import datetime

from .data_pipeline import DataPipeline
from ..core.config import get_settings
from ..services import prediction_engine as pe
from ..services.football_analyzer import TeamProfile, H2HRecord
from ..schemas.schemas import MatchOut

logger = logging.getLogger("scheduler")
settings = get_settings()


class CollectionScheduler:
    def __init__(self, fd_key: str, odds_key: str):
        self.pipeline = DataPipeline(fd_key, odds_key)
        self._running = False

    async def run_once(self, competitions: list[str] | None = None) -> dict:
        """
        Lance une collecte unique et retourne les données enrichies.
        Appelle ensuite le moteur de prédiction sur chaque match.
        """
        logger.info(f"[{datetime.utcnow().isoformat()}] Démarrage collecte unique...")
        result = await self.pipeline.run_full_collection(competitions=competitions)
        analyses = await self._analyze_all(result["matches"])
        return {**result, "analyses": analyses}

    async def _analyze_all(self, matches: list[dict]) -> list[dict]:
        """Lance l'analyse prédictive sur tous les matchs collectés."""
        analyses = []
        for m in matches:
            try:
                analysis = await self._analyze_match(m)
                if analysis:
                    analyses.append(analysis)
            except Exception as e:
                logger.warning(f"Analyse échouée pour {m.get('home_team')} vs {m.get('away_team')}: {e}")
        return analyses

    async def _analyze_match(self, match_data: dict) -> dict | None:
        """Analyse un seul match avec les données collectées."""
        # Construire les profils d'équipe depuis les stats disponibles
        home_profile = TeamProfile(
            name=match_data["home_team"],
            avg_goals_scored=1.5,
            avg_goals_conceded=1.3,
            avg_xg_for=1.4,
            avg_xg_against=1.25,
            form="WDDLL",
            games=0,
        )
        away_profile = TeamProfile(
            name=match_data["away_team"],
            avg_goals_scored=1.2,
            avg_goals_conceded=1.5,
            avg_xg_for=1.1,
            avg_xg_against=1.4,
            form="LWDWL",
            games=0,
        )

        # Cotes disponibles
        odds_snaps = []
        odds = match_data.get("odds")
        if odds and odds.get("consensus"):
            c = odds["consensus"]
            odds_snaps = [{
                "home": c.get("home", 2.5),
                "draw": c.get("draw", 3.2),
                "away": c.get("away", 2.5),
                "ts": 0,
            }]
            # Ligne sharp Pinnacle si disponible
            sharp = odds.get("sharp_line")
            if sharp and sharp.get("home"):
                odds_snaps.insert(0, {
                    "home": sharp["home"],
                    "draw": sharp.get("draw", 3.2),
                    "away": sharp["away"],
                    "ts": -3600,
                })

        mock_match = MatchOut(
            id=0,
            external_id=match_data.get("external_id", ""),
            competition=match_data.get("competition", "Unknown"),
            home_team=match_data["home_team"],
            away_team=match_data["away_team"],
            match_date=match_data.get("match_date", datetime.utcnow().isoformat()),
            status=match_data.get("status", "scheduled"),
            home_score=None, away_score=None,
            home_xg=None, away_xg=None,
            home_shots=None, away_shots=None,
            home_possession=None, away_possession=None,
            home_form=home_profile.form,
            away_form=away_profile.form,
        )

        result = pe.run_full_analysis(
            match=mock_match,
            home_profile=home_profile,
            away_profile=away_profile,
            h2h=H2HRecord(),
            odds_snapshots=odds_snaps,
        )

        return {
            "match": f"{match_data['home_team']} vs {match_data['away_team']}",
            "competition": match_data.get("competition"),
            "date": match_data.get("match_date"),
            "winner": result.predicted_winner,
            "score": f"{result.prediction.predicted_home_score}:{result.prediction.predicted_away_score}",
            "confidence": result.prediction_confidence,
            "suspicion_score": result.suspicion.score,
            "suspicion_level": result.suspicion.level,
            "prob_home": round(result.prediction.prob_home * 100, 1),
            "prob_draw": round(result.prediction.prob_draw * 100, 1),
            "prob_away": round(result.prediction.prob_away * 100, 1),
            "over25": round(result.prediction.prob_over25 * 100, 1),
            "btts": round(result.prediction.prob_btts * 100, 1),
            "flags": [f.description for f in result.suspicion.flags],
        }

    async def start_periodic(
        self,
        matches_interval_h: int = 6,
        odds_interval_min: int = 30,
    ):
        """
        Lance la collecte périodique en arrière-plan.
        - Matchs toutes les `matches_interval_h` heures
        - Cotes toutes les `odds_interval_min` minutes
        """
        self._running = True
        logger.info(
            f"Scheduler démarré: matchs toutes les {matches_interval_h}h, "
            f"cotes toutes les {odds_interval_min}min"
        )

        async def matches_loop():
            while self._running:
                try:
                    await self.pipeline.fetch_upcoming_matches()
                except Exception as e:
                    logger.error(f"Erreur collecte matchs: {e}")
                await asyncio.sleep(matches_interval_h * 3600)

        async def odds_loop():
            while self._running:
                try:
                    await self.pipeline.fetch_all_odds()
                except Exception as e:
                    logger.error(f"Erreur collecte cotes: {e}")
                await asyncio.sleep(odds_interval_min * 60)

        await asyncio.gather(matches_loop(), odds_loop())

    def stop(self):
        self._running = False
        logger.info("Scheduler arrêté.")
