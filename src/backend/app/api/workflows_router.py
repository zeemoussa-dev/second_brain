"""The Workflow catalogue's HTTP surface (REQ-SB-95-US-04-T03) -- flat
and single-purpose, the same one-router-per-entity convention
actions_router.py / index_router.py / pipelines_router.py already use.

This router composes; it does not decide. Step order, step identity and
save-time referential integrity with the Action catalogue are all
`WorkflowManager`'s own rules (`ADR-032`, `ADR-034`), so the only thing
that happens here is turning the Manager's refusal into an HTTP status
-- never into a different message.

**409 carrying the Manager's sentence verbatim, not a generic 400.** A
refused save names WHICH step (by position, as the operator's ordered
editor shows it) and WHICH unknown action id; flattening that to "Bad
Request" throws away the only part the operator can act on, and they
cannot fix a step they have not been told about. 422 is equally wrong:
FastAPI owns it for its own request-validation errors, whose `detail`
is a LIST of error objects, so a Manager refusal sent under the same
code would force the Workflows screen to tell two `detail` shapes apart
before it could show anything. 409 is what sections_router.py,
blueprints_router.py and actions_router.py already return when a
Manager refuses a write.

**A step's `action_id` is deliberately optional on the wire** -- same
reason actions_router.py accepts an omitted `implementation`. A step
naming nothing is a real case and NOT one this router answers: it goes
to the Manager and comes back as the Manager's own refusal, so "no
action id" and "an action id the catalogue does not have" are refused
by one rule, in one place, under one status, with one body shape.

Read and write shape the same way here, unlike the Action surface: a
`GET` body posted straight back is a valid write, because a stored step
carries exactly the five fields a written one does. The one asymmetry
is that `created_at`/`updated_at` are read-only facts the Manager owns
and are not accepted on a write, and `id` is settable only at creation.

**The run routes are at the bottom of this file** (`ADR-034`,
`REQ-SB-95-US-04-T05`): start a run, take the one next step, report that
step's outcome. There are three and there is deliberately no fourth --
no "get the run", no "list the runs", no separate "get the report". A
run is read by asking for its next step, which answers with the step or,
when there is none, with the composed report; adding a read-only view of
the same record would be a second answer to one question, and the two
could disagree. Nothing here decides anything about a run either: the
engine owns the order, the pause and the refusals, and this file maps
them onto statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business.core.workflows.workflow import Workflow
from app.business.core.workflows.workflow_manager import (
    WorkflowManager,
    WorkflowStepActionNotFoundError,
)
from app.business.logic import workflow_run

router = APIRouter(prefix="/workflows")
_workflow_manager = WorkflowManager()


class WorkflowStepBody(BaseModel):
    """One documented step on the wire.

    `id` is optional and empty means "mint one": a step the operator has
    just added in the editor has no id yet, while an existing step must
    send the id it already has or a reorder would re-key every step it
    moved (`ADR-034` -- a run addresses steps by id, never by position).

    `inputs` is an open dict and is NOT typed per Action: which inputs
    an Action declares is catalogue data that changes without a deploy,
    and the call gate validates them at the moment the step is
    dispatched (`ADR-033`). Typing them here would duplicate that rule
    in a place that cannot see the Action, and would silently drop any
    field it had not been taught about.
    """
    id: str = ""
    action_id: str = ""
    inputs: dict[str, Any] = {}
    needs_confirmation: bool = False
    description: str = ""


class WorkflowReportBody(BaseModel):
    """An empty `include_step_ids` means every step, in documented order
    -- the entity's own default, restated here so a client that sends
    nothing and a client that sends an empty list mean the same thing.
    """
    description: str = ""
    include_step_ids: list[str] = []


class WorkflowCreateBody(BaseModel):
    id: str
    request_kind: str = ""
    description: str = ""
    steps: list[WorkflowStepBody] = []
    report: WorkflowReportBody | None = None


class WorkflowUpdateBody(BaseModel):
    """Omitted (None) = leave unchanged, for every field -- the update
    convention ActionUpdateBody and SectionUpdateBody already set.

    A supplied `steps` REPLACES the stored list in the order given,
    which is what a reorder is; there is no merge by step id, because a
    merge cannot tell "the operator deleted this step" from "the client
    only sent the ones it changed" (WorkflowManager.update's own rule).
    """
    request_kind: str | None = None
    description: str | None = None
    steps: list[WorkflowStepBody] | None = None
    report: WorkflowReportBody | None = None


def _step_payloads(steps: list[WorkflowStepBody] | None) -> list[dict] | None:
    if steps is None:
        return None
    return [step.model_dump() for step in steps]


def _report_payload(report: WorkflowReportBody | None) -> dict | None:
    if report is None:
        return None
    return report.model_dump()


def _refusal(exc: Exception) -> HTTPException:
    return HTTPException(status_code=409, detail=str(exc))


@router.get("")
def list_workflows() -> list[Workflow]:
    """The whole catalogue as real Workflows, steps included -- the same
    "thin wrapper, one business call, return the real dataclass list"
    convention GET /indexes and GET /sections use. Nothing is summarised
    away: a Workflow IS its ordered steps, and a list row that had to
    fetch each one to say how many steps it has would make the
    catalogue screen N+1 requests deep."""
    return _workflow_manager.get_all()


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str) -> Workflow:
    workflow = _workflow_manager.get_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Unknown workflow: {workflow_id!r}")
    return workflow


@router.post("")
def create_workflow(body: WorkflowCreateBody) -> Workflow:
    """200 with the created Workflow, not 201 -- no route in app/api/
    returns 201, and a create that answered differently from every other
    one here would be the odd case every client has to learn."""
    try:
        return _workflow_manager.create(
            body.id,
            request_kind=body.request_kind,
            description=body.description,
            steps=_step_payloads(body.steps),
            report=_report_payload(body.report),
        )
    except WorkflowStepActionNotFoundError as exc:
        raise _refusal(exc)


@router.put("/{workflow_id}")
def update_workflow(workflow_id: str, body: WorkflowUpdateBody) -> Workflow:
    """A refused edit leaves the stored Workflow exactly as it was: the
    Manager validates every supplied step against the live catalogue
    BEFORE it writes, so there is nothing to roll back here and no
    partially-updated definition to read back."""
    try:
        workflow = _workflow_manager.update(
            workflow_id,
            request_kind=body.request_kind,
            description=body.description,
            steps=_step_payloads(body.steps),
            report=_report_payload(body.report),
        )
    except WorkflowStepActionNotFoundError as exc:
        raise _refusal(exc)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Unknown workflow: {workflow_id!r}")
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str) -> dict:
    """Deleting an unknown id is {"deleted": False}, never a 404 --
    `ADR-014`'s result-dict convention, which WorkflowManager.delete
    already follows. Deleting a Workflow removes its definition only:
    the Actions its steps named belong to the catalogue and outlive
    it."""
    return _workflow_manager.delete(workflow_id)


# The run surface (`ADR-034`, REQ-SB-95-US-04-T05). Runs live under
# `/workflows/runs/...` rather than a top-level `/workflow-runs/...` so
# a run stays visibly part of the Workflows surface -- the same choice
# actions_router.py made for `/actions/calls/...`.
#
# No path here can collide with the catalogue routes above: those are
# one segment after the prefix, `POST /workflows/{workflow_id}/run` is
# two, and the two run routes are three and four. A Workflow whose id
# were literally `runs` would still be reachable at `GET
# /workflows/runs`, because that route is one segment and these are not.


class WorkflowRunStartBody(BaseModel):
    """`caller_agent_id` is required and is the agent every step of this
    run is dispatched as -- the Action gate refuses a call that names no
    caller (`ADR-033`), and defaulting one here would record a run
    nobody started.
    There is no `inputs` field, and `request` is NOT one. A step's
    inputs are the operator's, part of the documented handling, and
    stored on the step; letting the starter of a run supply or override
    them would make the Workflow a suggestion rather than the handling
    that was decided on. `request` is a different thing: what the ask
    was ABOUT -- "which customer" -- which a step may reference but
    cannot be overridden by, because the reference is written in the
    Workflow and only the value comes from here (`REQ-SB-103`).
    """
    caller_agent_id: str
    # Supplied by the agent that recognised the request, because only a
    # model can take it out of natural language. An open dict, not a
    # typed model: which values a Workflow references is authoring data
    # that changes without a deploy, and typing it here would silently
    # drop a key the Workflow was written to use.
    request: dict[str, Any] = {}


class WorkflowStepOutcomeBody(BaseModel):
    """`done` or `failed`, and nothing else -- the engine refuses any
    other word by name. `not_reached`, `running` and
    `awaiting_confirmation` describe where the run is, which is the
    framework's to say and not the caller's.

    `detail` is what the caller saw, in words, and goes into the report
    the operator reads. `result` is open and untyped for the same reason
    a step's inputs are: what a `skill` step's runner comes back with is
    that Skill's business, not this router's.
    """
    outcome: str
    detail: str = ""
    result: Any = None


def _run_refusal(exc: Exception) -> HTTPException:
    """409 carrying the engine's own sentence as a plain string, never
    reworded (`MEMORY.md`, 2026-10-17). The sentence names which step,
    which position and why -- an agent relays it to the operator and the
    operator acts on it, and "Conflict" alone is actionable by
    neither."""
    return HTTPException(status_code=409, detail=str(exc))


@router.post("/{workflow_id}/run")
def start_workflow_run(workflow_id: str, body: WorkflowRunStartBody) -> dict:
    """Open a run of this Workflow. Nothing is dispatched and nothing is
    performed: the answer is a record whose every documented step reads
    `not_reached`, which is what makes "the run holds every documented
    step and no step that is not in the Workflow" checkable from the
    first byte written.

    The caller then asks for the next step, which is where the first
    step -- like every later one -- goes through the Action gate."""
    try:
        return workflow_run.start_run(workflow_id, body.caller_agent_id, body.request)
    except workflow_run.WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except workflow_run.WorkflowRunRefusedError as exc:
        raise _run_refusal(exc)


@router.post("/runs/{run_id}/next-step")
def take_the_next_workflow_run_step(run_id: str) -> dict:
    """The ONE step this run is on, dispatched through the Action gate
    if it has not been already.

    `POST`, not `GET`, and the name says `take` rather than `get`:
    handing a step out is what dispatches it, so this really performs an
    `http` step, really authorises a `skill` one, and really opens the
    `awaiting_confirmation` record a confirmation-marked step pauses at.
    A `GET` that did any of those would be a lie to every cache, proxy
    and retry that treats `GET` as safe.

    Asked again before the current step's outcome is recorded, it
    returns the SAME step and dispatches nothing a second time.

    `step` is `null` when there is no next step, and `status` says which
    kind of "no": `complete` when every documented step is `done`, or
    `blocked` when the run stopped at one that failed, was refused or
    was declined. `report` is then the report composed from the recorded
    outcomes. A blocked run answers 200 with that report rather than a
    409, because "there is no next step and here is exactly what
    happened" is the honest answer to the question that was asked -- and
    the caller that most needs the report is the one whose run broke.
    """
    try:
        return workflow_run.next_step(run_id)
    except workflow_run.WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/runs/{run_id}/steps/{step_id}/outcome")
def report_workflow_run_step_outcome(
    run_id: str, step_id: str, body: WorkflowStepOutcomeBody,
) -> dict:
    """Record what came of the step this run is on, and nothing else.

    An outcome for a step this run does not hold, for a step that is not
    the one the run is on, for a step nothing has handed out yet, or for
    one already settled, is a 409 carrying the engine's sentence --
    which is what "no skipped step" and "no invented step" look like
    from the wire."""
    try:
        return workflow_run.record_step_outcome(
            run_id, step_id, body.outcome, body.detail, body.result,
        )
    except workflow_run.WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except workflow_run.WorkflowRunRefusedError as exc:
        raise _run_refusal(exc)
