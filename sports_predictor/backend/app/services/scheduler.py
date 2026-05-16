"""
APScheduler — runs prediction generation daily at configured time.
"""
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.predictor import generate_daily_tickets
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler():
    scheduler.add_job(
        _daily_job,
        trigger=CronTrigger(
            hour=settings.DAILY_GENERATION_HOUR,
            minute=settings.DAILY_GENERATION_MINUTE,
        ),
        id="daily_prediction",
        replace_existing=True,
        misfire_grace_time=300,
    )
    # Collecte + réentraînement chaque lundi à 03:00 UTC
    scheduler.add_job(
        _weekly_retrain_job,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="weekly_retrain",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(
        f"Scheduler démarré — génération quotidienne à "
        f"{settings.DAILY_GENERATION_HOUR:02d}:{settings.DAILY_GENERATION_MINUTE:02d} UTC"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")


async def _weekly_retrain_job():
    logger.info("Réentraînement hebdomadaire démarré...")
    try:
        from app.services.historical_collector import collect_historical
        from app.ml.trainer import main as train_main
        from app.ml.model import load_model

        collect_result = await collect_historical(max_per_league=300)
        logger.info(f"Collecte: {collect_result}")

        await train_main(force_synthetic=False)
        load_model()
        logger.info("Modèle ML rechargé après réentraînement")
    except Exception as e:
        logger.error(f"Réentraînement hebdomadaire échoué: {e}", exc_info=True)


async def _daily_job():
    logger.info("Génération quotidienne en cours...")
    try:
        from app.database import AsyncSessionLocal
        from app.services.persistence import save_tickets
        from app.utils.cache import cache_key, cache_set

        target = date.today() + timedelta(days=1)
        tickets = await generate_daily_tickets(target)

        if tickets:
            async with AsyncSessionLocal() as db:
                await save_tickets(tickets, target, db)

            from datetime import datetime
            from app.schemas.prediction import DailyTicketsOut
            result = DailyTicketsOut(
                date=str(target),
                generated_at=datetime.utcnow().isoformat(),
                tickets=tickets,
                total_tickets=len(tickets),
            )
            ck = cache_key("daily_tickets", str(target))
            await cache_set(ck, result.model_dump(), ttl=3600 * 4)

        logger.info(f"Génération terminée — {len(tickets)} tickets créés et sauvegardés")
    except Exception as e:
        logger.error(f"Échec de la génération quotidienne: {e}", exc_info=True)
