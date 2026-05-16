from fastapi import APIRouter, Query, HTTPException
from datetime import date, datetime, timedelta
from app.services.predictor import generate_daily_tickets
from app.schemas.prediction import DailyTicketsOut
from app.utils.cache import cache_get, cache_set, cache_key

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/daily", response_model=DailyTicketsOut, summary="Get today's prediction tickets")
async def get_daily_predictions(
    target_date: date = Query(default=None, description="Date (YYYY-MM-DD), defaults to tomorrow"),
    force_refresh: bool = Query(default=False, description="Bypass cache and regenerate"),
):
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    ck = cache_key("daily_tickets", str(target_date))

    if not force_refresh:
        cached = await cache_get(ck)
        if cached:
            return cached

    tickets = await generate_daily_tickets(target_date)

    if not tickets:
        raise HTTPException(status_code=404, detail=f"No predictions available for {target_date}")

    result = DailyTicketsOut(
        date=str(target_date),
        generated_at=datetime.utcnow().isoformat(),
        tickets=tickets,
        total_tickets=len(tickets),
    )

    await cache_set(ck, result.model_dump(), ttl=3600 * 4)
    return result


@router.get("/trigger", summary="Manually trigger daily generation (admin)")
async def trigger_generation(target_date: date = Query(default=None)):
    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    tickets = await generate_daily_tickets(target_date)
    return {"message": f"Generated {len(tickets)} tickets for {target_date}", "tickets_count": len(tickets)}
