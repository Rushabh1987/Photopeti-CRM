"""APScheduler wiring."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.db import SessionLocal
from app.services.reminders import evaluate

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


def _run_reminders() -> None:
    db = SessionLocal()
    try:
        evaluate(db)
    except Exception as exc:
        logger.error("Reminder job error: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    _scheduler.add_job(
        _run_reminders,
        "interval",
        minutes=settings.reminder_interval_minutes,
        id="reminders",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — interval=%d min", settings.reminder_interval_minutes)


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
