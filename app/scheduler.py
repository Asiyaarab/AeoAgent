"""
APScheduler setup — runs the AEO analysis on the 1st, 15th, and 30th
of every month at 02:00 UTC.

The target URL is whatever the user most recently submitted through
``/api/analyze`` (held in a single-element list, not a true queue).
"""
from __future__ import annotations

import atexit
from threading import RLock
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import analyzer
from .config import (
    SCHEDULER_DAY,
    SCHEDULER_HOUR,
    SCHEDULER_MINUTE,
    SCHEDULER_TIMEZONE,
    get_logger,
)

logger = get_logger(__name__)

# Module-level state
scheduler: BackgroundScheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)
scheduled_url: List[str] = []
_url_lock = RLock()

JOB_ID = "monthly_aeo_analysis"


def scheduled_run() -> None:
    """Job callback — runs the full pipeline against the configured URL."""
    with _url_lock:
        url = scheduled_url[0] if scheduled_url else None
    if url:
        logger.info("Scheduled run triggered for %s", url)
        analyzer.run_full_analysis(url)
    else:
        logger.warning("Scheduled run fired but no URL configured yet")


def init_scheduler() -> None:
    """Start the scheduler exactly once (idempotent)."""
    if scheduler.running:
        return

    scheduler.add_job(
        func=scheduled_run,
        trigger=CronTrigger(
            day=SCHEDULER_DAY,
            hour=SCHEDULER_HOUR,
            minute=SCHEDULER_MINUTE,
        ),
        id=JOB_ID,
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    logger.info(
        "Scheduler started: day=%s hour=%d minute=%d tz=%s",
        SCHEDULER_DAY, SCHEDULER_HOUR, SCHEDULER_MINUTE, SCHEDULER_TIMEZONE,
    )


def set_scheduled_url(url: str) -> None:
    """Replace the currently configured URL (or push one if empty)."""
    with _url_lock:
        if not scheduled_url:
            scheduled_url.append(url)
        else:
            scheduled_url[0] = url


def get_scheduled_url() -> str | None:
    with _url_lock:
        return scheduled_url[0] if scheduled_url else None


def get_next_run() -> str | None:
    job = scheduler.get_job(JOB_ID)
    return job.next_run_time.isoformat() if job else None
