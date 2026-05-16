from fastapi import APIRouter
from app.api.v1 import predictions, matches, stats

router = APIRouter(prefix="/v1")
router.include_router(predictions.router)
router.include_router(matches.router)
router.include_router(stats.router)
