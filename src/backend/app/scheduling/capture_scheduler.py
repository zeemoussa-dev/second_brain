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

from app.business import agent_schedule_registry, email_classification

logger = logging.getLogger(__name__)

_HOURLY_CAPTURE_JOB_ID = "hourly_capture"


async def run_capture_if_idle() -> None:
    """Runs one capture pass if no other capture is currently running;
    otherwise logs and returns immediately without waiting for the
    in-progress run to finish (Scenario 4 / AC-04: skip, not queue, not
    overlap). The underlying pipeline makes blocking Outlook COM calls, so
    it runs off the event loop thread via asyncio.to_thread.

    Acquires agent_schedule_registry's own shared dispatch lock (ADR-037
    point 1) rather than a private one — this is what makes this hourly
    blob tick and any newly-configured per-agent schedule targeting one of
    the same three capture agents correctly serialize against each other,
    with neither mechanism's own internal logic rewritten.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 4): restructured into two
    separate steps. Step 1 (under the shared lock, unchanged) bundles
    Email's own Pull leg with Meeting-capture's and Todo-capture's own
    still-unchanged, still-Outlook-touching legs, via run_capture_and_
    record_completion(trigger="scheduled") -- Email's own leg stages ONLY
    for this trigger (email_classification.py's own docstring), never
    processes. Step 2, AFTER the shared lock is released, separately
    dispatches process_staged_email through the NEW, dedicated processing
    lock -- never the shared one above. This is what makes a stalled Pull
    unable to block already-staged mail, and a stalled Process unable to
    block the next Pull, true by construction for this one real,
    reachable trigger path (the hourly/app-start scheduled tick)."""
    lock = agent_schedule_registry.get_shared_dispatch_lock()
    if lock.locked():
        logger.info(
            "Capture run already in progress — skipping this trigger "
            "rather than starting an overlapping run."
        )
        return
    async with lock:
        await asyncio.to_thread(
            email_classification.run_capture_and_record_completion,
            trigger="scheduled",
        )
    await agent_schedule_registry.dispatch_with_dedicated_processing_lock(
        "email-capture-pipeline", "process_staged_email", trigger="scheduled",
    )


def build_scheduler() -> AsyncIOScheduler:
    """One hourly job; coalesce=True + misfire_grace_time=None together
    give 'a missed run fires once on the next opportunity, however late,
    not once per missed slot' (ADR-005 point 1 / AC-03's live-but-
    suspended-process case). max_instances=1 gives library-level
    skip-not-overlap for this trigger source alone; the cross-trigger-
    source guard (AC-04's app-start-vs-hourly case) is run_capture_if_idle
    itself, which this job also goes through.

    Also registers one job per persisted per-agent-capability schedule
    (ADR-037 point 2) — read fresh from agent_schedule_registry at build
    time, alongside the existing hardcoded hourly_capture job, unchanged."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_capture_if_idle,
        trigger=IntervalTrigger(hours=1),
        id=_HOURLY_CAPTURE_JOB_ID,
        coalesce=True,
        misfire_grace_time=None,
        max_instances=1,
    )
    for schedule in agent_schedule_registry.list_schedules():
        scheduler.add_job(
            _build_scheduled_tick(schedule["agent_id"], schedule["capability_id"]),
            trigger=IntervalTrigger(**{schedule["interval_unit"]: schedule["interval_value"]}),
            id=f"schedule:{schedule['agent_id']}:{schedule['capability_id']}",
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=None,
            max_instances=1,
        )
    return scheduler


def _build_scheduled_tick(agent_id: str, capability_id: str):
    """A dedicated closure per (agent_id, capability_id) pair, avoiding
    the classic late-binding-closure-in-a-loop bug — each call captures
    its own pair via this function's own parameters, not a shared loop
    variable a lambda referencing the loop's names directly would.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 4): a persisted per-agent
    schedule for "process_staged_email" specifically must route through
    the new dedicated processing lock at cold-start job registration too
    (mirrors agent_schedule_registry._make_scheduled_tick_callback's own
    identical fix for the LIVE-mutation path) -- otherwise a custom
    recurring schedule for this one capability would silently reintroduce
    the exact lock-sharing this task exists to eliminate, on process
    restart. Every other capability_id (including "pull_email") is
    unaffected — still the same dispatch_with_shared_lock call as before
    this task."""
    dispatch = (
        agent_schedule_registry.dispatch_with_dedicated_processing_lock
        if capability_id == "process_staged_email"
        else agent_schedule_registry.dispatch_with_shared_lock
    )

    async def _tick() -> None:
        await dispatch(agent_id, capability_id, trigger="scheduled")

    return _tick


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = build_scheduler()
    # Published BEFORE scheduler.start() (ADR-037 point 2) -- this is what
    # lets agent_schedule_registry.create_or_update_schedule/remove_schedule
    # mutate this process's own live job registry directly (Scenario 4/5's
    # "no restart required"), without app/business/ ever importing
    # app.scheduling (the object stored there is a plain third-party
    # AsyncIOScheduler instance, not app.scheduling-owned code).
    agent_schedule_registry.set_live_scheduler(scheduler)
    scheduler.start()
    # Unconditional app-start trigger (ADR-005 point 2 / AC-02, AC-05):
    # always fires once, regardless of how recently the last run
    # completed — this is also the full-restart catch-up path for AC-03.
    # Scheduled as a background task, never awaited here (BUGFIX, found
    # live 2026-08-14): awaiting it directly blocked FastAPI's own
    # "application startup complete" — and therefore ALL HTTP traffic,
    # not just capture-related endpoints — on the entire catch-up run
    # finishing first. A real backlog made this a genuine multi-minute,
    # many-real-API-call wait before the server would answer any request
    # at all. Nothing in REQ-SB-07's own spec requires the API to be
    # unusable while capture runs — see BUGS.md.
    asyncio.create_task(run_capture_if_idle())
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
