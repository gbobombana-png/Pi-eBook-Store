from fastapi import APIRouter
router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/health")
async def health():
    return {"status": "ok", "service": "SportPredictor Pro"}
