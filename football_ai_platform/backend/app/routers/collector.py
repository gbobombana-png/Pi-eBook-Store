"""
Endpoints pour déclencher la collecte de données depuis l'UI ou un cron.
"""
from fastapi import APIRouter, HTTPException, Query
from ..collectors.scheduler import CollectionScheduler
from ..core.config import get_settings
import os

router = APIRouter(prefix="/collector", tags=["collector"])
settings = get_settings()


def _get_scheduler() -> CollectionScheduler:
    fd_key   = os.getenv("FOOTBALL_DATA_API_KEY", "")
    odds_key = os.getenv("ODDS_API_KEY", "")
    if not fd_key or not odds_key:
        raise HTTPException(
            400,
            "Clés API manquantes. Définir FOOTBALL_DATA_API_KEY et ODDS_API_KEY dans .env"
        )
    return CollectionScheduler(fd_key, odds_key)


@router.post("/run")
async def run_collection(
    competitions: list[str] = Query(default=["PL", "FL1", "BL1"]),
):
    """
    Lance une collecte manuelle immédiate.
    Récupère matchs + cotes + analyse IA pour toutes les compétitions.
    """
    scheduler = _get_scheduler()
    result = await scheduler.run_once(competitions=competitions)
    return {
        "status": "ok",
        "collected_at": result["collected_at"],
        "total_matches": result["total"],
        "analyses": result["analyses"],
        "odds_remaining": scheduler.pipeline.odds.remaining_requests(),
    }


@router.get("/quota")
async def check_quota():
    """Vérifie le quota restant The Odds API."""
    odds_key = os.getenv("ODDS_API_KEY", "")
    if not odds_key:
        raise HTTPException(400, "ODDS_API_KEY manquant")
    from ..collectors.odds_api import OddsAPIClient
    client = OddsAPIClient(odds_key)
    try:
        await client.get_sports()
        return {"remaining_requests": client.remaining_requests(), "status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/test-fd")
async def test_football_data(competition: str = Query(default="FL1")):
    """Test la connexion football-data.org (1 requête)."""
    fd_key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    if not fd_key:
        raise HTTPException(400, "FOOTBALL_DATA_API_KEY manquant")
    from ..collectors.football_data import FootballDataClient
    client = FootballDataClient(fd_key)
    try:
        matches = await client.get_matches(competition=competition)
        return {
            "status": "ok",
            "competition": competition,
            "matches_found": len(matches),
            "sample": [
                {
                    "home": m.get("homeTeam", {}).get("name"),
                    "away": m.get("awayTeam", {}).get("name"),
                    "date": m.get("utcDate"),
                }
                for m in matches[:3]
            ],
        }
    except Exception as e:
        raise HTTPException(500, str(e))
