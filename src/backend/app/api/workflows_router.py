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

The run routes -- start a run, fetch the one next step, report its
outcome (`ADR-034`) -- are NOT here and are not stubbed. They are
`T05`'s, over their own `WorkflowRuns/` store: a route that existed and
did nothing would read, to the agent reading the catalogue, exactly
like a run engine that silently loses steps.
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
