"""APScheduler setup and lifecycle helpers.

The scheduler is created once at import time so ``main.py`` can reference it
during the FastAPI lifespan. Jobs are registered here; the lifespan handler
starts and stops the scheduler around the server's lifetime.

All times are expressed in UTC. 17:00 PKT = 12:00 UTC (PKT is UTC+5).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.price_sync import run_price_sync

logger = logging.getLogger(__name__)

# Job configuration — kept as module-level constants so they can be
# inspected in tests without relying on the scheduler's runtime state.
PRICE_SYNC_JOB_ID = "daily_price_sync"
PRICE_SYNC_JOB_NAME = "Daily PSX price sync (17:00 PKT)"
PRICE_SYNC_HOUR_UTC = 12  # 17:00 PKT = 12:00 UTC (PKT is UTC+5)
PRICE_SYNC_MINUTE_UTC = 0


def _make_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(
        run_price_sync,
        trigger=CronTrigger(hour=PRICE_SYNC_HOUR_UTC, minute=PRICE_SYNC_MINUTE_UTC, timezone="UTC"),
        id=PRICE_SYNC_JOB_ID,
        name=PRICE_SYNC_JOB_NAME,
        replace_existing=True,
        misfire_grace_time=3600,  # tolerate up to 1 h late start (e.g. server restart)
    )
    return sched


scheduler = _make_scheduler()
