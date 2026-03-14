import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler(scrape_job_fn) -> None:
    """
    Start the APScheduler with a weekly Monday 09:00 UTC cron job.
    scrape_job_fn must be an async callable that runs the full scrape + DB upsert.
    """
    _scheduler.add_job(
        scrape_job_fn,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0, timezone="UTC"),
        id="weekly_scrape",
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1 hour late if server was down
    )
    _scheduler.start()
    logger.info("Scheduler started — weekly scrape scheduled for Monday 09:00 UTC")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
