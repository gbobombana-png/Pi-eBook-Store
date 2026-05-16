"""
APScheduler — runs prediction generation daily at configured time.
"""
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
    scheduler.start()
    logger.info(
        f"Scheduler started — daily generation at "
        f"{settings.DAILY_GENERATION_HOUR:02d}:{settings.DAILY_GENERATION_MINUTE:02d} UTC"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


async def _daily_job():
    logger.info("Running daily prediction generation...")
    try:
        tickets = await generate_daily_tickets()
        logger.info(f"Daily job complete — {len(tickets)} tickets generated")
    except Exception as e:
        logger.error(f"Daily job failed: {e}", exc_info=True)
