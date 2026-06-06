"""APScheduler wiring (Phase 4). A BackgroundScheduler runs reminders.evaluate()
every settings.reminder_interval_minutes. start_scheduler()/stop_scheduler()
are called from app.main's lifespan."""
# TODO(Phase 4): start_scheduler() / stop_scheduler()
