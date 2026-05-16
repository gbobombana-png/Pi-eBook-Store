"""
Admin endpoints — API keys, data collection, ML retraining.
All routes require admin JWT.
"""
import os
import pickle
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.match import Match, MatchStatus
from app.models.team import Team
from app.utils.auth import require_admin
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Schémas ────────────────────────────────────────────────────────────────

class ApiKeysUpdate(BaseModel):
    api_football_key: str = ""
    odds_api_key: str = ""


class ApiTestResult(BaseModel):
    api_football: dict
    odds_api: dict


# ─── Clés API ────────────────────────────────────────────────────────────────

@router.post("/api-keys", summary="Mettre à jour les clés API")
async def update_api_keys(
    data: ApiKeysUpdate,
    _admin: dict = Depends(require_admin),
):
    env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
    env_path = os.path.normpath(env_path)

    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()

    def _set(lines: list, key: str, value: str) -> list:
        found = False
        result = []
        for line in lines:
            if line.startswith(f"{key}="):
                result.append(f"{key}={value}\n")
                found = True
            else:
                result.append(line)
        if not found:
            result.append(f"{key}={value}\n")
        return result

    if data.api_football_key:
        lines = _set(lines, "API_FOOTBALL_KEY", data.api_football_key)
        settings.API_FOOTBALL_KEY = data.api_football_key

    if data.odds_api_key:
        lines = _set(lines, "ODDS_API_KEY", data.odds_api_key)
        settings.ODDS_API_KEY = data.odds_api_key

    with open(env_path, "w") as f:
        f.writelines(lines)

    return {
        "message": "Clés API mises à jour",
        "api_football_set": bool(settings.API_FOOTBALL_KEY),
        "odds_api_set": bool(settings.ODDS_API_KEY),
    }


@router.get("/api-keys/test", summary="Tester les connexions API")
async def test_api_connections(_admin: dict = Depends(require_admin)):
    import httpx

    results = {}

    # Test API-Football
    if settings.API_FOOTBALL_KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "https://api-football-v1.p.rapidapi.com/v3/status",
                    headers={
                        "X-RapidAPI-Key": settings.API_FOOTBALL_KEY,
                        "X-RapidAPI-Host": settings.API_FOOTBALL_HOST,
                    },
                )
                data = r.json()
                sub = data.get("response", {}).get("subscription", {})
                results["api_football"] = {
                    "status": "ok" if r.status_code == 200 else "error",
                    "http_code": r.status_code,
                    "plan": sub.get("plan", "unknown"),
                    "requests_remaining": sub.get("requests", {}).get("current", "?"),
                    "requests_limit": sub.get("requests", {}).get("limit_day", "?"),
                }
        except Exception as e:
            results["api_football"] = {"status": "error", "detail": str(e)}
    else:
        results["api_football"] = {"status": "not_configured", "detail": "Clé API non définie"}

    # Test TheOddsAPI
    if settings.ODDS_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    f"{settings.ODDS_API_BASE}/sports",
                    params={"apiKey": settings.ODDS_API_KEY},
                )
                results["odds_api"] = {
                    "status": "ok" if r.status_code == 200 else "error",
                    "http_code": r.status_code,
                    "remaining": r.headers.get("x-requests-remaining", "?"),
                    "used": r.headers.get("x-requests-used", "?"),
                }
        except Exception as e:
            results["odds_api"] = {"status": "error", "detail": str(e)}
    else:
        results["odds_api"] = {"status": "not_configured", "detail": "Clé API non définie"}

    return results


# ─── Collecte historique ─────────────────────────────────────────────────────

@router.post("/collect", summary="Collecter les données historiques en arrière-plan")
async def collect_historical(
    background_tasks: BackgroundTasks,
    season: int = None,
    max_per_league: int = 200,
    _admin: dict = Depends(require_admin),
):
    from app.services.historical_collector import collect_historical as _collect

    async def _run():
        logger.info("Collecte historique démarrée...")
        result = await _collect(season_only=season, max_per_league=max_per_league)
        logger.info(f"Collecte terminée: {result}")

    background_tasks.add_task(_run)
    return {
        "message": "Collecte démarrée en arrière-plan",
        "season_filter": season,
        "max_per_league": max_per_league,
    }


@router.get("/collect/status", summary="Statut des données collectées")
async def collection_status(
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    n_total = (await db.execute(select(func.count()).select_from(Match))).scalar_one()
    n_finished = (await db.execute(
        select(func.count()).select_from(Match).where(Match.status == MatchStatus.FINISHED)
    )).scalar_one()
    n_teams = (await db.execute(select(func.count()).select_from(Team))).scalar_one()

    return {
        "matches_total": n_total,
        "matches_finished": n_finished,
        "teams_total": n_teams,
        "ml_ready": n_finished >= 100,
        "recommended_threshold": 100,
    }


# ─── ML retraining ───────────────────────────────────────────────────────────

@router.post("/train", summary="Entraîner / réentraîner le modèle ML")
async def train_model(
    background_tasks: BackgroundTasks,
    force_synthetic: bool = False,
    _admin: dict = Depends(require_admin),
):
    from app.ml.trainer import main as train_main
    from app.ml.model import load_model

    async def _run():
        logger.info("Entraînement ML démarré...")
        await train_main(force_synthetic=force_synthetic)
        load_model()
        logger.info("Modèle rechargé en mémoire")

    background_tasks.add_task(_run)
    return {
        "message": "Entraînement démarré en arrière-plan",
        "force_synthetic": force_synthetic,
        "model_path": settings.MODEL_PATH,
    }


@router.get("/model/stats", summary="Statistiques du modèle ML actuel")
async def model_stats(
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    model_exists = os.path.exists(settings.MODEL_PATH)
    model_size = None
    model_modified = None
    n_features = None

    if model_exists:
        stat = os.stat(settings.MODEL_PATH)
        model_size = f"{stat.st_size / 1024 / 1024:.1f} Mo"
        model_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        try:
            with open(settings.MODEL_PATH, "rb") as f:
                m = pickle.load(f)
            steps = dict(m.steps)
            clf = steps.get("clf")
            if clf and hasattr(clf, "estimator"):
                est = clf.estimator
                n_features = getattr(est, "n_features_in_", None)
        except Exception:
            pass

    n_finished = (await db.execute(
        select(func.count()).select_from(Match).where(Match.status == MatchStatus.FINISHED)
    )).scalar_one()

    return {
        "model_exists": model_exists,
        "model_path": settings.MODEL_PATH,
        "model_size": model_size,
        "model_last_trained": model_modified,
        "n_features": n_features,
        "training_samples_available": n_finished,
        "using_ml": model_exists,
        "mode": "Gradient Boosting (calibré)" if model_exists else "Fallback statistique (Poisson)",
    }
