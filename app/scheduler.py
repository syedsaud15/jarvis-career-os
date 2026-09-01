"""Optional scheduler runner. External messages are never sent without a configured bridge."""
from apscheduler.schedulers.blocking import BlockingScheduler
from app.config import get_settings


def daily_digest() -> None:
    # Intentionally a safe extension point: compose summary then require send approval.
    print("JARVIS daily digest is ready for delivery approval.")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=get_settings().timezone)
    scheduler.add_job(daily_digest, "cron", hour=8, minute=0, id="daily_digest")
    scheduler.start()

