from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime
from app.config import settings
from app.utils.cache import cache_get
from app.utils.auth import require_admin

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/health", summary="Health check")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/config", summary="Configuration publique")
async def get_config():
    return {
        "tickets_per_day": settings.TICKETS_PER_DAY,
        "target_odds": settings.TARGET_ODDS,
        "min_confidence": settings.MIN_CONFIDENCE,
        "generation_time": f"{settings.DAILY_GENERATION_HOUR:02d}:{settings.DAILY_GENERATION_MINUTE:02d} UTC",
        "api_football_connected": bool(settings.API_FOOTBALL_KEY),
        "odds_api_connected": bool(settings.ODDS_API_KEY),
    }


@router.get("/cache", summary="Diagnostics cache")
async def cache_diagnostics():
    keys_to_check = ["daily_tickets", "history_tickets"]
    result = {}
    for k in keys_to_check:
        val = await cache_get(k)
        result[k] = "hit" if val else "miss"
    return {"cache_status": result}


@router.post("/admin/train", summary="Entraîner le modèle ML (admin)")
async def train_model(
    background_tasks: BackgroundTasks,
    force_synthetic: bool = False,
    _admin: dict = Depends(require_admin),
):
    from app.ml.trainer import main as train_main
    from app.ml.model import load_model

    async def _run():
        await train_main(force_synthetic=force_synthetic)
        load_model()

    background_tasks.add_task(_run)
    return {
        "message": "Entraînement démarré en arrière-plan",
        "force_synthetic": force_synthetic,
    }
