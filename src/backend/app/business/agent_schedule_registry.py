"""Per-agent recurring schedule: a new, persisted, user-mutable concern
(REQ-SB-47-US-01), built together with REQ-SB-45's shared serialization
guarantee, per ADR-037 points 1-4. The single canonical home for:

1. Persisted per-(agent_id, capability_id) schedule CRUD, keyed by the
   composite string "<agent_id>::<capability_id>" — this project's
   structural guarantee that at most one active schedule exists per
   (agent, capability) pair.
2. The live AsyncIOScheduler reference — capture_scheduler.lifespan() calls
   set_live_scheduler(scheduler) once, at startup, so create_or_update_
   schedule/remove_schedule can mutate the live process's own scheduler
   directly (Scenario 4/5's "no restart required"), WITHOUT app/business/
   ever importing app.scheduling — the object stored here is a plain
   third-party apscheduler.schedulers.asyncio.AsyncIOScheduler instance,
   not app.scheduling-owned code (ADR-005 point 5's one-directional
   scheduling -> business edge stays intact).
3. The shared, in-process Outlook-COM dispatch lock — one module-level
   asyncio.Lock(), the ONE function (dispatch_with_shared_lock) every real
   scheduled/on-demand trigger source now passes through, generalizing
   capture_scheduler.py's own former private _capture_run_lock (ADR-005
   point 3's "one concurrency guard spans both trigger sources," one step
   further). Explicitly in-process only — see ADR-037's Context/
   Alternatives Considered for the disclosed cross-process scope decision.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

from apscheduler.triggers.interval import IntervalTrigger

from app.business import skill_registry, skill_tools
from app.data_access import vault_writer

_dispatch_lock = asyncio.Lock()
# REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- a SECOND, dedicated
# asyncio.Lock, scoped to email processing alone -- never the shared
# Outlook-COM lock above. This is the structural mechanism that makes
# pull_email and process_staged_email share NO lock: one being stuck can
# never block the other's own dispatch, regardless of which one is slow.
_processing_lock = asyncio.Lock()
_live_scheduler = None


class ScheduleRefusedError(Exception):
    """Raised by create_or_update_schedule when capability_id is not
    granted to agent_id, or is granted but not classified as mutating
    (Scenario 9 / AC-09). A clean, catchable outcome — the router (T04)
    catches this and turns it into an HTTP 400 with `.reason` as the
    message, never an unhandled exception/500."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _schedule_key(agent_id: str, capability_id: str) -> str:
    return f"{agent_id}::{capability_id}"


# The structural gate every run-state function below uses -- these three
# ids are the only ones this project tracks run-state for today:
# "run_capture_now" (the id shared by exactly the three covered capture
# agents -- email-capture-pipeline/meeting-capture/todo-capture, per
# skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]), plus
# "pull_email"/"process_staged_email" (REQ-SB-69-US-01-T04, ADR-046
# Decision 4 -- both granted to email-capture-pipeline alone, per
# skill_registry._MIGRATION_GRANT_SEED). Never a hardcoded agent-id list
# -- the SAME gate T01's own _invoke_capability dispatch-routing branch
# already uses for "run_capture_now", kept in exact lockstep here rather
# than re-derived a second way. A plain tuple (not a set) -- iteration
# order matters for get_job_run_states()'s own output below, and three
# ids is far too small a collection for set-membership speed to matter.
_RUN_STATE_TRACKED_CAPABILITY_IDS = ("run_capture_now", "pull_email", "process_staged_email")


def _job_run_state_key(agent_id: str, capability_id: str) -> str:
    return f"{agent_id}::{capability_id}"


def _load_job_run_state() -> dict:
    state = vault_writer.load_job_run_state()
    if state is None:
        state = {"runs": {}}
        vault_writer.save_job_run_state(state)
    return state


def _mark_run_started(agent_id: str, capability_id: str) -> None:
    if capability_id not in _RUN_STATE_TRACKED_CAPABILITY_IDS:
        return
    state = _load_job_run_state()
    key = _job_run_state_key(agent_id, capability_id)
    state["runs"][key] = {
        "agent_id": agent_id,
        "capability_id": capability_id,
        "running": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "last_outcome": None,
        "last_error_message": None,
        "last_duration_seconds": None,
    }
    vault_writer.save_job_run_state(state)


def _classify_run_outcome(result: dict) -> tuple[str, str | None]:
    """Maps invoke_skill's varying result shapes (as returned from
    inside dispatch_with_shared_lock's own asyncio.to_thread call) onto
    this record's {"last_outcome", "last_error_message"} pair.
    "skipped" covers the two genuinely-not-a-failure non-dispatch
    outcomes the working-mode gate can still return from inside the
    lock-held branch (Supervised-deferred "pending",
    Manual-dormant "skipped_manual") -- neither is a capture-pipeline
    failure, so neither should paint the job "error" on the Scheduling
    view. Everything else that did not genuinely, positively dispatch
    (unknown_skill, refused, available: False) is an honest "error",
    carrying the real message/reason text -- never fabricated."""
    status = result.get("status")
    if status in ("pending", "skipped_manual"):
        return "skipped", None
    if status in ("unknown_skill", "refused"):
        return "error", result.get("reason") or result.get("message")
    if result.get("available") is False:
        return "error", result.get("message")
    return "success", None


def _mark_run_finished(agent_id: str, capability_id: str, result: dict) -> None:
    if capability_id not in _RUN_STATE_TRACKED_CAPABILITY_IDS:
        return
    state = _load_job_run_state()
    key = _job_run_state_key(agent_id, capability_id)
    existing = state["runs"].get(key)
    started_at_iso = existing["started_at"] if existing else None
    finished_at = datetime.now(timezone.utc)
    duration_seconds = None
    if started_at_iso:
        duration_seconds = (finished_at - datetime.fromisoformat(started_at_iso)).total_seconds()
    outcome, error_message = _classify_run_outcome(result)
    state["runs"][key] = {
        "agent_id": agent_id,
        "capability_id": capability_id,
        "running": False,
        "started_at": started_at_iso,
        "finished_at": finished_at.isoformat(),
        "last_outcome": outcome,
        "last_error_message": error_message,
        "last_duration_seconds": duration_seconds,
    }
    vault_writer.save_job_run_state(state)


def get_job_run_states() -> list[dict]:
    """Read accessor for the Scheduling view (T03). One entry per
    (covered agent, covered capability_id) pair, for every id in
    _RUN_STATE_TRACKED_CAPABILITY_IDS -- covered agent ids for each id
    are read from skill_registry._MIGRATION_GRANT_SEED[capability_id]
    (the SAME real, already-existing source), never a second,
    independently-hardcoded id list -- so the frontend (T04) never needs
    its own copy of this list either.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 4): extended from a single
    hardcoded id to iterate all three tracked ids -- "pull_email"/
    "process_staged_email" add two more real entries here (both scoped
    to email-capture-pipeline alone, per skill_registry.
    _MIGRATION_GRANT_SEED), purely for internal observability parity;
    no new Scheduling-view frontend row is built for either (the parent
    story's own Non-Goal) -- GET /system-health's response shape is
    unaffected by this addition on its own (T04's own Files to Modify
    does not touch that router or its response assembly).

    A covered agent with no persisted record yet gets an honest
    "has_run": False placeholder (Scenario 5) -- never a fabricated
    running/duration/outcome value. An in-flight run's
    elapsed_seconds is computed fresh at read time (now -
    started_at) -- never persisted incrementally, mirroring
    REQ-SB-31-US-01's own established recompute-fresh-on-refresh
    convention for this exact page. An uncovered agent/capability
    (e.g. compass-expert/build_knowledge) is never iterated here at
    all, regardless of whatever job_run_state.json happens to
    contain (Scenario 7)."""
    state = _load_job_run_state()
    now = datetime.now(timezone.utc)
    records = []
    for capability_id in _RUN_STATE_TRACKED_CAPABILITY_IDS:
        covered_agent_ids = skill_registry._MIGRATION_GRANT_SEED.get(capability_id, [])
        for agent_id in covered_agent_ids:
            key = _job_run_state_key(agent_id, capability_id)
            record = state["runs"].get(key)
            if record is None:
                records.append({
                    "agent_id": agent_id,
                    "capability_id": capability_id,
                    "has_run": False,
                    "running": False,
                    "started_at": None,
                    "finished_at": None,
                    "last_outcome": None,
                    "last_error_message": None,
                    "last_duration_seconds": None,
                    "elapsed_seconds": None,
                })
                continue
            entry = dict(record)
            entry["has_run"] = True
            if entry["running"] and entry["started_at"]:
                entry["elapsed_seconds"] = (now - datetime.fromisoformat(entry["started_at"])).total_seconds()
            else:
                entry["elapsed_seconds"] = None
            records.append(entry)
    return records


def _job_id(agent_id: str, capability_id: str) -> str:
    return f"schedule:{agent_id}:{capability_id}"


def _load_state() -> dict:
    state = vault_writer.load_agent_schedules_state()
    if state is None:
        state = {"schedules": {}}
        vault_writer.save_agent_schedules_state(state)
    return state


def list_schedules(agent_id: str | None = None) -> list[dict]:
    state = _load_state()
    records = list(state["schedules"].values())
    if agent_id is not None:
        records = [record for record in records if record["agent_id"] == agent_id]
    return records


def _is_schedulable(agent_id: str, capability_id: str) -> bool:
    granted_ids = {skill["id"] for skill in skill_registry.list_agent_skills(agent_id)}
    return (
        capability_id in granted_ids
        and skill_tools.SKILLS.get(capability_id, {}).get("mutates") is True
    )


def create_or_update_schedule(
    agent_id: str, capability_id: str, interval_value: int, interval_unit: str,
) -> dict:
    """Refuses (raises ScheduleRefusedError, Scenario 9) unless
    capability_id is both granted to agent_id and classified as mutating.
    Replaces an existing entry for the same (agent_id, capability_id) pair
    in place — never duplicates (the composite-key dict shape makes this
    true by construction). Also mutates the live scheduler's own job
    registry, if one has been published via set_live_scheduler — a no-op
    (persist-JSON-only) otherwise, so this module stays safely importable/
    testable in isolation before T03 wires the real scheduler in."""
    if not _is_schedulable(agent_id, capability_id):
        raise ScheduleRefusedError(
            f"'{capability_id}' is not a granted, mutating capability for "
            f"agent '{agent_id}' — only an agent's own granted, mutating "
            "capabilities can be scheduled."
        )
    state = _load_state()
    key = _schedule_key(agent_id, capability_id)
    existing = state["schedules"].get(key)
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "agent_id": agent_id,
        "capability_id": capability_id,
        "interval_value": interval_value,
        "interval_unit": interval_unit,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
    state["schedules"][key] = record
    vault_writer.save_agent_schedules_state(state)
    _register_live_job(record)
    return record


def remove_schedule(agent_id: str, capability_id: str) -> bool:
    state = _load_state()
    key = _schedule_key(agent_id, capability_id)
    if key not in state["schedules"]:
        return False
    del state["schedules"][key]
    vault_writer.save_agent_schedules_state(state)
    _remove_live_job(agent_id, capability_id)
    return True


def set_live_scheduler(scheduler) -> None:
    global _live_scheduler
    _live_scheduler = scheduler


def _register_live_job(record: dict) -> None:
    if _live_scheduler is None:
        return
    agent_id, capability_id = record["agent_id"], record["capability_id"]
    _live_scheduler.add_job(
        _make_scheduled_tick_callback(agent_id, capability_id),
        trigger=IntervalTrigger(**{record["interval_unit"]: record["interval_value"]}),
        id=_job_id(agent_id, capability_id),
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=None,
        max_instances=1,
    )


def _remove_live_job(agent_id: str, capability_id: str) -> None:
    if _live_scheduler is None:
        return
    try:
        _live_scheduler.remove_job(_job_id(agent_id, capability_id))
    except Exception:  # noqa: BLE001 -- job may never have been registered against a live scheduler (e.g. created before any process had one yet); removal is still honestly idempotent from the caller's point of view
        pass


def _make_scheduled_tick_callback(agent_id: str, capability_id: str):
    """A bound-argument closure per job, avoiding the classic late-binding-
    closure-in-a-loop bug (ADR-037 point 2's own explicit callout) — each
    call to this factory captures its own agent_id/capability_id pair via
    the function's own parameters, not a shared loop variable.

    REQ-SB-69-US-01-T04 (ADR-046 Decision 4): a user-created custom
    schedule (agent_schedules_router.py) for "process_staged_email"
    specifically must route through the new dedicated processing lock,
    never the shared Outlook-COM one -- otherwise a custom recurring
    schedule for this one capability would silently reintroduce the exact
    lock-sharing this task exists to eliminate. Every other capability_id
    (including "pull_email") is unaffected -- still the same
    dispatch_with_shared_lock call as before this task."""
    dispatch = (
        dispatch_with_dedicated_processing_lock
        if capability_id == "process_staged_email"
        else dispatch_with_shared_lock
    )

    async def _tick() -> None:
        await dispatch(agent_id, capability_id, trigger="scheduled")

    return _tick


def get_shared_dispatch_lock() -> asyncio.Lock:
    return _dispatch_lock


async def dispatch_with_shared_lock(
    agent_id: str, capability_id: str, trigger: Literal["scheduled", "direct", "chat"],
) -> dict:
    """The ONE function every real scheduled/on-demand trigger source
    passes through (mirrors ADR-005 point 3's "one concurrency guard spans
    both trigger sources," generalized). Skips — never queues — if the
    lock is already held, returning an honest "skipped" result; otherwise
    acquires it and drives the real dispatch off the event loop thread
    (mirrors run_capture_if_idle's own exact blocking-call shape)."""
    lock = get_shared_dispatch_lock()
    history_len_before = len(vault_writer.load_agent_history(agent_id))
    if lock.locked():
        result = {"status": "skipped", "message": "skipped — another run is already in progress"}
    else:
        async with lock:
            _mark_run_started(agent_id, capability_id)
            result = await asyncio.to_thread(
                skill_registry.invoke_skill, agent_id, capability_id, None, trigger,
            )
            _mark_run_finished(agent_id, capability_id, result)
    _record_outcome(agent_id, capability_id, trigger, result, history_len_before)
    return result


def get_dedicated_processing_lock() -> asyncio.Lock:
    return _processing_lock


async def dispatch_with_dedicated_processing_lock(
    agent_id: str, capability_id: str, trigger: Literal["scheduled", "direct", "chat"],
) -> dict:
    """REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- dispatch_with_shared_
    lock's own sibling, mirroring its exact shape (skip-not-queue on
    contention, asyncio.to_thread dispatch, run-state marking, outcome
    recording), but acquiring the NEW, dedicated _processing_lock instead
    of the shared Outlook-COM one. Called ONLY for capability_id ==
    "process_staged_email" -- pull_email and every other real Outlook
    caller (meeting-capture/todo-capture) continue through
    dispatch_with_shared_lock, unchanged, exactly as before this task.

    This is the concrete mechanism that makes Scenario 2 (a stalled
    pull_email can't block already-staged mail) and Scenario 3 (stalled
    processing can't block the next pull_email) true BY CONSTRUCTION: the
    two capabilities share no lock, so one being stuck structurally
    cannot block the other's own dispatch, regardless of which one is
    slow. dispatch_with_shared_lock's own body/signature is left
    completely untouched by this addition -- this is a new, standalone
    sibling function, not a rewrite of that one."""
    lock = get_dedicated_processing_lock()
    history_len_before = len(vault_writer.load_agent_history(agent_id))
    if lock.locked():
        result = {"status": "skipped", "message": "skipped — another run is already in progress"}
    else:
        async with lock:
            _mark_run_started(agent_id, capability_id)
            result = await asyncio.to_thread(
                skill_registry.invoke_skill, agent_id, capability_id, None, trigger,
            )
            _mark_run_finished(agent_id, capability_id, result)
    _record_outcome(agent_id, capability_id, trigger, result, history_len_before)
    return result


def _record_outcome(
    agent_id: str, capability_id: str, trigger: str, result: dict, history_len_before: int,
) -> None:
    """Records every outcome to run history EXCEPT two cases where an
    entry already, genuinely exists — recording either a second time here
    would be a real duplicate, not an honest new record:
      - "skipped_manual" (T01) — the gate itself records ZERO history by
        design (dormant Manual ticks stay invisible); never append here,
        regardless of the length check below.
      - Any outcome that already grew agent_id's own history during the
        real dispatch this function itself just awaited — detected
        generically via a before/after length comparison, not a
        hardcoded capability_id or a "history_recorded" flag some
        handlers set and others don't. Reconciled against 2 REAL,
        live-discovered self-recording paths this task found by actually
        running them (not trusted from ADR-037's own illustrative "every
        other status is recorded" text alone — see this task's own
        Implementation Log): invoke_skill's own Supervised+mutates
        "pending" branch (writes a "proposal" entry itself), and
        run_capture_now's real email-capture dispatch (its own
        email_classification.run_capture_and_record_completion call
        already writes email-capture's own run_event/run_error entry
        internally, with no "history_recorded" flag on its return value
        unlike build_knowledge — a real, pre-existing inconsistency in
        skill_tools.py, out of this story's own scope to fix there; the
        length-check catches it anyway, generically, for any current or
        future self-recording handler, flagged or not)."""
    if result.get("status") == "skipped_manual":
        return
    if len(vault_writer.load_agent_history(agent_id)) > history_len_before:
        return
    capability_name = skill_tools.SKILLS.get(capability_id, {}).get("name", capability_id)
    trigger_label = "Scheduled run" if trigger == "scheduled" else "Run now"
    status = result.get("status")
    outcome_text = result.get("message") or result.get("reason") or status or "completed"
    is_failure = status in ("error", "refused", "unknown_skill") or result.get("available") is False
    kind = "run_error" if is_failure else "run_event"
    vault_writer.append_agent_history_entry(
        agent_id, kind, f"{trigger_label} — {capability_name} — {outcome_text}",
    )
