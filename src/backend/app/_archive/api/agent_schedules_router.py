"""New API surface (ADR-037 point 7) — thin HTTP wrappers over
app/business/agent_schedule_registry.py's schedule CRUD + shared-lock
dispatch. Mirrors pending_approvals_router.py's/skills_router.py's own
"new dedicated router for a new dedicated concern" shape — no business
logic here; every real decision (refusal, persistence, live-job mutation,
the shared dispatch lock) stays in agent_schedule_registry.py."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import agent_registry, agent_schedule_registry

router = APIRouter(prefix="/agents/{agent_id}/schedules")


class CreateScheduleBody(BaseModel):
    capability_id: str
    interval_value: int
    interval_unit: str


class UpdateScheduleBody(BaseModel):
    interval_value: int | None = None
    interval_unit: str | None = None
    new_capability_id: str | None = None


def _require_known_agent(agent_id: str) -> None:
    if agent_registry.get_agent(agent_id) is None:
        raise HTTPException(status_code=404, detail="Unknown agent")


@router.get("")
def list_schedules(agent_id: str) -> list[dict]:
    _require_known_agent(agent_id)
    return agent_schedule_registry.list_schedules(agent_id)


@router.post("")
def create_schedule(agent_id: str, body: CreateScheduleBody) -> dict:
    _require_known_agent(agent_id)
    try:
        return agent_schedule_registry.create_or_update_schedule(
            agent_id, body.capability_id, body.interval_value, body.interval_unit,
        )
    except agent_schedule_registry.ScheduleRefusedError as exc:
        raise HTTPException(status_code=400, detail=exc.reason) from exc


@router.patch("/{capability_id}")
def update_schedule(agent_id: str, capability_id: str, body: UpdateScheduleBody) -> dict:
    _require_known_agent(agent_id)
    existing = next(
        (s for s in agent_schedule_registry.list_schedules(agent_id) if s["capability_id"] == capability_id),
        None,
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Unknown schedule")
    target_capability_id = body.new_capability_id or capability_id
    interval_value = body.interval_value if body.interval_value is not None else existing["interval_value"]
    interval_unit = body.interval_unit if body.interval_unit is not None else existing["interval_unit"]
    try:
        updated = agent_schedule_registry.create_or_update_schedule(
            agent_id, target_capability_id, interval_value, interval_unit,
        )
    except agent_schedule_registry.ScheduleRefusedError as exc:
        raise HTTPException(status_code=400, detail=exc.reason) from exc
    # Retargeting to a different capability_id leaves the prior key's own
    # record behind (composite-key dict, a different key) -- remove it so
    # "edit" genuinely replaces in place rather than leaving a stale entry.
    if target_capability_id != capability_id:
        agent_schedule_registry.remove_schedule(agent_id, capability_id)
    return updated


@router.delete("/{capability_id}")
def delete_schedule(agent_id: str, capability_id: str) -> dict:
    _require_known_agent(agent_id)
    removed = agent_schedule_registry.remove_schedule(agent_id, capability_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Unknown schedule")
    return {"removed": True}


@router.post("/{capability_id}/run-now")
async def run_now(agent_id: str, capability_id: str) -> dict:
    """On-demand dispatch — reuses the existing "direct" trigger literal,
    unchanged (T01 already lets it through regardless of working mode).
    Works whether or not a recurring schedule currently exists for this
    pair. Every outcome shape (real success, honest-unavailable, honest-
    skipped) is returned as-is, 200 — never translated into an HTTP
    error, mirroring skills_router.py::invoke_skill's own existing
    convention.

    ESC-045 (REQ-SB-69-US-01-T04 follow-up, ADR-046 Decision 4): a manual
    run-now for "process_staged_email" must route through the dedicated
    processing lock, never the shared Outlook-COM one — otherwise a
    human manually running Process from this endpoint would reintroduce
    the exact lock-sharing T04 exists to eliminate, for this one manual
    trigger path. Mirrors agent_schedule_registry._make_scheduled_tick_
    callback's/capture_scheduler._build_scheduled_tick's own identical
    dispatch-selection shape. Every other capability_id (including
    "pull_email") is unaffected — still the same dispatch_with_shared_
    lock call as before this fix."""
    _require_known_agent(agent_id)
    dispatch = (
        agent_schedule_registry.dispatch_with_dedicated_processing_lock
        if capability_id == "process_staged_email"
        else agent_schedule_registry.dispatch_with_shared_lock
    )
    return await dispatch(agent_id, capability_id, trigger="direct")
