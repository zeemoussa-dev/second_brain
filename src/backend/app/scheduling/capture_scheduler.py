"""Coordinates trigger sources (app-start, hourly interval — wired in T04)
for the email capture pipeline. A single shared concurrency guard covers
both trigger sources (ADR-005, point 3) so an app-start run and an
hourly-boundary run can never overlap each other, not just overlap
themselves.

Structurally parallel to app/api/ (ADR-005, point 5): translates a
timer/lifecycle event into a call against business/, never reaches into
data_access/ directly.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.business import email_classification

logger = logging.getLogger(__name__)

_capture_run_lock = asyncio.Lock()

_HOURLY_CAPTURE_JOB_ID = "hourly_capture"


async def run_capture_if_idle() -> None:
    """Runs one capture pass if no other capture is currently running;
    otherwise logs and returns immediately without waiting for the
    in-progress run to finish (Scenario 4 / AC-04: skip, not queue, not
    overlap). The underlying pipeline makes blocking Outlook COM calls, so
    it runs off the event loop thread via asyncio.to_thread."""
    if _capture_run_lock.locked():
        logger.info(
            "Capture run already in progress — skipping this trigger "
            "rather than starting an overlapping run."
        )
        return
    async with _capture_run_lock:
        await asyncio.to_thread(
            email_classification.run_capture_and_record_completion
        )


def build_scheduler() -> AsyncIOScheduler:
    """One hourly job; coalesce=True + misfire_grace_time=None together
    give 'a missed run fires once on the next opportunity, however late,
    not once per missed slot' (ADR-005 point 1 / AC-03's live-but-
    suspended-process case). max_instances=1 gives library-level
    skip-not-overlap for this trigger source alone; the cross-trigger-
    source guard (AC-04's app-start-vs-hourly case) is run_capture_if_idle
    itself, which this job also goes through."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_capture_if_idle,
        trigger=IntervalTrigger(hours=1),
        id=_HOURLY_CAPTURE_JOB_ID,
        coalesce=True,
        misfire_grace_time=None,
        max_instances=1,
    )
    return scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = build_scheduler()
    scheduler.start()
    # Unconditional app-start trigger (ADR-005 point 2 / AC-02, AC-05):
    # always fires once, regardless of how recently the last run
    # completed — this is also the full-restart catch-up path for AC-03.
    await run_capture_if_idle()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
