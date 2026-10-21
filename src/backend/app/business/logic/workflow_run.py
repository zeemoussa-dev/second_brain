"""The Workflow run engine (`ADR-034`, REQ-SB-95-US-04-T05).

A run is a record that outlives the request that started it. The
framework hands back exactly ONE next step at a time and refuses to
advance until the current step's outcome is recorded, so "in order",
"no skipped step", "no invented step" and "reports what the Workflow
says is reported" are properties of
`<DATA_PATH>/data/WorkflowRuns/<run_id>.json` rather than promises by a
model.

**Four step states that nothing infers.** `not_reached`, `running`,
`done` and `refused` -- plus `awaiting_confirmation` and `failed` --
are written into the record as literal words, for every step, from the
moment the run starts. A step that has not run yet is NOT a step that
succeeded with no output, and the difference has to be in the stored
bytes: a record whose unreached steps were simply absent, or whose
status was derived from "has an outcome been written", could not tell
"nobody got there" from "it ran and produced nothing". Every documented
step is in the file from the first write, carrying `not_reached`.

**Every step goes through the `ADR-033` Action gate, unchanged.** There
is no second validation path and no second dispatch mechanism here:
`action_invocation.call_action()` is called with the step's own stored
inputs, and whatever it answers -- performed, pointed at, authorised,
refused, awaiting the operator -- is what the step records. A `skill`
step is therefore authorised and not performed, a `ui` step is pointed
at and not performed, and an `http` step is performed by the app,
because that is what the gate already does.

**Handing a step out is what dispatches it, and it happens once.** Ask
for the next step twice without recording an outcome and the SAME step
comes back out of the record, not a second call: re-dispatching an
`http` step would perform the operation twice, and re-dispatching a
confirmation-marked one would leave the operator a pile of identical
pending decisions.

**Per-step confirmation reuses `ADR-033`'s mechanism unchanged** -- the
gate opens the `awaiting_confirmation` call record, the operator answers
on the existing `/actions/calls/{call_id}/confirm|decline` surface, and
the re-call spends the single-use grant. One consequence is deliberate
and is this task's one scope-internal judgement call: a step marked
`needs_confirmation` whose Action does not itself require confirmation
is REFUSED, naming the step and why, rather than performed. The gate
decides confirmation from the Action's own flag and takes no override
(`REQ-SB-95-US-03-T04`: "an Action's confirmation flag, not the
caller's say-so"), so the only two things this engine could do with such
a step are refuse it or perform something the operator asked to be
asked about first. Refusing is the safe one, and performing it is the
exact failure this requirement exists to close.

**The report is composed, never stored.** `compose_report()` reads the
recorded step outcomes at the moment it is asked, so a failed step
cannot be reported as done -- there is no second copy of the answer to
drift from the statuses it was derived from.

**A run is never deleted and never silently ends.** Its status is
`running`, `awaiting_confirmation`, `blocked` or `complete`, and
`complete` is written only when every documented step is `done`. An
abandoned run stays open and visible (`ADR-034`).

Nothing here touches the Workflow definition store beyond reading it,
and the run snapshots the steps it is going to run AT START: editing a
Workflow must not change the order, inputs or confirmation flags of a
run that is already in flight.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from app.business.core.actions.action_manager import ActionManager
from app.business.core.workflows.workflow import Workflow, WorkflowStep
from app.business.core.workflows.workflow_manager import WorkflowManager
from app.business.logic import action_invocation, step_references
from app.data_access import action_calls as action_calls_data
from app.data_access import workflow_runs as workflow_runs_data

_logger = logging.getLogger(__name__)

# The six states one step of a run can be in, written literally into
# the record. They are six rather than "has an outcome / has not"
# because the operator, the agent and a later audit have to tell apart
# six genuinely different situations, and collapsing any pair of them
# would make at least one unreadable:
#
# - `not_reached`           -- the run has not got here. Written for
#                              every step at start, so "nobody got
#                              there" is a stored fact and not an
#                              absence to be interpreted;
# - `running`               -- handed out and dispatched through the
#                              gate; nothing has reported what came of
#                              it yet;
# - `awaiting_confirmation` -- dispatched, and the gate opened an
#                              awaiting_confirmation call record. The
#                              run pauses here, visibly;
# - `done`                  -- an outcome was reported and it succeeded;
# - `failed`                -- an outcome was reported, or the gate's
#                              own dispatch reported, that it did not;
# - `refused`               -- the gate refused it, or the operator
#                              declined it. Nothing was performed.
STEP_NOT_REACHED = "not_reached"
STEP_RUNNING = "running"
STEP_AWAITING_CONFIRMATION = "awaiting_confirmation"
STEP_DONE = "done"
STEP_FAILED = "failed"
STEP_REFUSED = "refused"

# The only two words a caller may report. `not_reached`, `running` and
# `awaiting_confirmation` are the framework's own and are deliberately
# unreportable: they describe where the run is, which is not something
# the caller is entitled to assert.
REPORTABLE_OUTCOMES = (STEP_DONE, STEP_FAILED)

# A step is reportable only while it is `running`. Every other state is
# either not yet reached, not yet answered by the operator, or already
# settled -- and an already-settled outcome is not retaken.
_REPORTABLE_STEP_STATUSES = (STEP_RUNNING,)

# The states a step is finished in, for better or worse.
_SETTLED_STEP_STATUSES = (STEP_DONE, STEP_FAILED, STEP_REFUSED)

# The four states a run can be in. `complete` is written only when
# every documented step is `done`; a run that stops for any other
# reason is `blocked` and stays open and visible, which is `ADR-034`'s
# own "an abandoned run must never look complete".
RUN_RUNNING = "running"
RUN_AWAITING_CONFIRMATION = "awaiting_confirmation"
RUN_BLOCKED = "blocked"
RUN_COMPLETE = "complete"


class WorkflowRunNotFoundError(Exception):
    """A run id, or a workflow id, this install does not have. Carries
    the sentence the caller reads; the router turns it into a 404
    without rewording it."""


class WorkflowRunRefusedError(Exception):
    """The run refuses to do what was asked -- an outcome for a step
    that is not the current one, for a step this run does not hold, for
    a step nothing has handed out yet, or a start that cannot happen.

    Carries the sentence the operator and the agent read, the same way
    `WorkflowStepActionNotFoundError` does, so the router turns it into
    a 409 with the words intact (`MEMORY.md`, 2026-10-17). A refusal
    whose reason is flattened to "Bad Request" throws away the only
    part either of them can act on.
    """


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot_step(position: int, step: WorkflowStep) -> dict:
    """One documented step, as the run will run it.

    Snapshotted at start rather than re-read from the Workflow on every
    hand-out: the operator may edit the Workflow while a run is in
    flight, and a run whose remaining steps, inputs or confirmation
    flags changed underneath it would be running handling nobody
    authorised -- and could not honestly claim afterwards to have run
    the documented steps in the documented order.

    `position` is stored for the operator to read and is NEVER what a
    step is addressed by (`MEMORY.md`, 2026-10-18): `step_id` is.
    """
    return {
        "step_id": step.id,
        "position": position,
        "action_id": step.action_id,
        "description": step.description,
        "needs_confirmation": bool(step.needs_confirmation),
        "inputs": dict(step.inputs or {}),
        # Filled at dispatch, once references are resolved.
        "resolved_inputs": None,
        "status": STEP_NOT_REACHED,
        # The gate's own word for what it did, kept verbatim and never
        # overwritten by what a caller later reports: a step reported
        # `done` whose dispatch was `pointed_at` is the operator having
        # done it themselves, and the record should still say so.
        "dispatch_outcome": None,
        "detail": None,
        "result": None,
        "refusal": None,
        # Every Action call this step produced, in order. A
        # confirmation-marked step produces two -- the operator's
        # decision and the re-call that spends it -- which is
        # `ADR-033`'s own two-row shape, not an anomaly.
        "call_ids": [],
        "awaiting_call_id": None,
        "handed_out_at": None,
        "recorded_at": None,
    }


def _new_run_record(
    run_id: str, workflow: Workflow, caller_agent_id: str,
    request: dict | None = None,
) -> dict:
    return {
        "run_id": run_id,
        "workflow_id": workflow.id,
        "request_kind": workflow.request_kind,
        "caller_agent_id": caller_agent_id,
        "status": RUN_RUNNING,
        "started_at": _now(),
        "updated_at": _now(),
        # What the ask was about -- "which customer" (`REQ-SB-103`).
        # Supplied by the agent that recognised the request, because only
        # a model can take it out of natural language. Recorded as given
        # and NOT verified: the app has no way to check that the agent
        # read the ask correctly, and a record that implied otherwise
        # would be the fabricated certainty this whole family of
        # requirements exists to avoid.
        "request": dict(request or {}),
        # Every documented step, in the documented order, from the very
        # first write -- "the run record holds every documented step and
        # no step that is not in the Workflow" is then a property of the
        # file rather than of whatever happened to be appended later.
        "steps": [
            _snapshot_step(position, step)
            for position, step in enumerate(workflow.steps, start=1)
        ],
        # The report DEFINITION, snapshotted for the same reason the
        # steps are. What is reported is composed from the recorded
        # outcomes at the moment it is asked for.
        "report": {
            "description": workflow.report.description,
            "include_step_ids": list(workflow.report.include_step_ids),
        },
    }


def _read_run(run_id: str) -> dict:
    try:
        return workflow_runs_data.read_run_json(run_id)
    except FileNotFoundError:
        raise WorkflowRunNotFoundError(
            f"there is no workflow run {run_id!r} on this install"
        )
    except (OSError, ValueError) as exc:
        raise WorkflowRunNotFoundError(
            f"the record for workflow run {run_id!r} could not be read: {exc}"
        )


def _save_run(run: dict) -> None:
    run["updated_at"] = _now()
    workflow_runs_data.write_run_json(run["run_id"], run)


def _current_step(run: Mapping[str, Any]) -> dict | None:
    """The one step this run is on: the first that is not `done`.

    Scanning for the first not-done step, rather than keeping a cursor
    the engine increments, is what makes "no skipped step" structural --
    there is no index that could be advanced past a step whose outcome
    was never recorded.
    """
    for step in run.get("steps") or []:
        if step.get("status") != STEP_DONE:
            return step
    return None


def _step_by_id(run: Mapping[str, Any], step_id: str) -> dict | None:
    for step in run.get("steps") or []:
        if step.get("step_id") == step_id:
            return step
    return None


def _run_status_for(run: Mapping[str, Any]) -> str:
    current = _current_step(run)
    if current is None:
        return RUN_COMPLETE
    if current.get("status") == STEP_AWAITING_CONFIRMATION:
        return RUN_AWAITING_CONFIRMATION
    if current.get("status") in (STEP_FAILED, STEP_REFUSED):
        return RUN_BLOCKED
    return RUN_RUNNING


def _apply_verdict(step: dict, verdict: action_invocation.ActionCallVerdict) -> None:
    """What the gate answered, written onto the step -- and nothing
    else written anywhere. The gate has already recorded the call in its
    own ledger; this records which step the call belongs to and what
    state that leaves the step in.

    The mapping is deliberately total and has no default-to-success
    branch: an outcome word this engine has never heard of lands on
    `failed`, because a dispatch nobody here can interpret is not
    evidence that anything worked.
    """
    step["call_ids"] = [*(step.get("call_ids") or []), verdict.call_id]
    step["dispatch_outcome"] = verdict.outcome
    step["detail"] = verdict.detail or verdict.refusal
    step["result"] = verdict.result
    step["handed_out_at"] = _now()

    if verdict.outcome == action_invocation.OUTCOME_AWAITING_CONFIRMATION:
        step["status"] = STEP_AWAITING_CONFIRMATION
        step["awaiting_call_id"] = verdict.call_id
        step["refusal"] = None
        return

    step["awaiting_call_id"] = None
    if not verdict.accepted:
        step["status"] = STEP_REFUSED
        step["refusal"] = verdict.refusal
        step["recorded_at"] = _now()
        return
    if verdict.outcome in (
        action_invocation.OUTCOME_PERFORMED,
        action_invocation.OUTCOME_POINTED_AT,
        action_invocation.OUTCOME_AUTHORISED,
    ):
        step["status"] = STEP_RUNNING
        step["refusal"] = None
        return

    # `failed`, `not_dispatched`, and anything a later task teaches the
    # gate to say. The app itself observed this one, so it is settled
    # here and not left for a caller to report over: a step the gate
    # says did not run must never be reportable as done.
    step["status"] = STEP_FAILED
    step["refusal"] = None
    step["recorded_at"] = _now()


def _dispatch(run: dict, step: dict, confirmed_call_id: str | None = None) -> None:
    """Resolves this step's inputs against the run, then calls the gate.

    A reference that cannot be resolved refuses the step HERE, before
    the Action is called at all -- the whole point is that the Action
    never sees a literal `{{steps.x.result}}`, and calling it to find
    out would be exactly the send this guards against.
    """
    try:
        inputs = step_references.resolve_inputs(step.get("inputs") or {}, run)
    except step_references.ReferenceError as exc:
        step["status"] = STEP_REFUSED
        step["dispatch_outcome"] = None
        step["awaiting_call_id"] = None
        step["refusal"] = (
            f"step {step.get('step_id')!r} was not run: {exc}"
        )
        step["resolved_inputs"] = None
        return
    # Kept beside the authored inputs, never replacing them: an operator
    # debugging a run needs to see BOTH what the step was written to
    # send and what it actually sent.
    step["resolved_inputs"] = inputs
    verdict = action_invocation.call_action(
        step["action_id"], run["caller_agent_id"], inputs, confirmed_call_id,
    )
    _apply_verdict(step, verdict)


def _refuse_unconfirmable_step(step: dict) -> None:
    """A step the operator marked for confirmation, naming an Action
    the gate will not pause for.

    Not performed, and not quietly performed either: the operator asked
    to be in the loop here, the gate takes confirmation from the
    Action's own flag and from nothing else, and the only honest answer
    left is to say which step and why. Recorded on the step rather than
    raised, so the run blocks visibly at the step the operator can fix
    instead of the whole call failing with no record of where.
    """
    step["status"] = STEP_REFUSED
    step["dispatch_outcome"] = None
    step["awaiting_call_id"] = None
    step["refusal"] = (
        f"step {step['step_id']!r} (position {step['position']}) is marked as needing your "
        f"confirmation, but action {step['action_id']!r} is not a confirmation-required action, "
        "so the framework has no confirmation to pause at and will not perform it unasked. "
        "Mark that action as needing confirmation, or clear the step's flag; nothing was "
        "performed."
    )
    step["detail"] = step["refusal"]
    step["recorded_at"] = _now()


def _action_needs_confirmation(action_id: str) -> bool:
    """Read from the LIVE catalogue, the same source the gate itself
    reads -- asking anything else could disagree with what the gate is
    about to do."""
    action = ActionManager().get_by_id(action_id)
    return bool(action is not None and action.needs_confirmation)


def _advance_awaiting_step(run: dict, step: dict) -> None:
    """What the operator decided about the call this step is paused on.

    Read from the Action-call ledger rather than kept as a second copy
    on the run: the ledger record IS the confirmation (`ADR-033`), and a
    run that remembered "confirmed" separately could say so about a
    decision the operator had meanwhile declined.
    """
    awaiting_call_id = step.get("awaiting_call_id")
    try:
        call_record = action_calls_data.read_call_json(awaiting_call_id or "")
    except (OSError, ValueError):
        _logger.warning(
            "workflow run %s is paused on action call %r, whose ledger record could not be read",
            run.get("run_id"), awaiting_call_id,
        )
        return

    outcome = call_record.get("outcome")
    if outcome == action_invocation.OUTCOME_DECLINED:
        step["status"] = STEP_REFUSED
        step["refusal"] = call_record.get("refusal") or (
            f"the operator declined action call {awaiting_call_id!r}, so step "
            f"{step['step_id']!r} was not run and nothing was performed"
        )
        step["detail"] = step["refusal"]
        step["awaiting_call_id"] = None
        step["recorded_at"] = _now()
        return

    if outcome == action_invocation.OUTCOME_CONFIRMED:
        # The re-call spends the single-use grant through the gate's own
        # mechanism -- this engine never consumes one itself.
        _dispatch(run, step, confirmed_call_id=awaiting_call_id)
        return

    # Still `awaiting_confirmation`: the operator has not answered. The
    # step is returned unchanged and NO second call is opened -- a run
    # polled every few seconds would otherwise bury the operator in
    # identical pending decisions about one step.


def start_run(
    workflow_id: str, caller_agent_id: str, request: dict | None = None,
) -> dict:
    """Open a run of one Workflow. Nothing is dispatched and nothing is
    performed here: a run starts as a record of what is to be done, with
    every documented step at `not_reached`.

    Separating "a run exists" from "a step has been handed out" is what
    lets the very first hand-out be the same operation as every later
    one, so there is no first-step path that could differ from the rest.
    """
    workflow = WorkflowManager().get_by_id(workflow_id)
    if workflow is None:
        raise WorkflowRunNotFoundError(
            f"there is no workflow {workflow_id!r} in this install's catalogue, so no run of it "
            "was started"
        )
    if not (caller_agent_id or "").strip():
        raise WorkflowRunRefusedError(
            f"a run of workflow {workflow_id!r} names the agent running it, and this one named "
            "none; no run was started"
        )
    if not workflow.steps:
        raise WorkflowRunRefusedError(
            f"workflow {workflow_id!r} documents no steps, so there is nothing to run and no run "
            "was started"
        )

    run = _new_run_record(uuid4().hex, workflow, caller_agent_id, request)
    workflow_runs_data.write_run_json(run["run_id"], run)
    return run


def next_step(run_id: str) -> dict:
    """The ONE step this run is on, dispatched through the Action gate
    if it has not been already.

    Asked again before the current step's outcome is recorded, this
    returns the SAME step out of the record and dispatches nothing a
    second time.

    When there is no next step -- every documented step `done`, or the
    run blocked at one that failed, was refused or was declined -- the
    answer is the composed report rather than a refusal: "there is no
    next step, and here is exactly what happened" is an honest answer to
    an honest question, and a 409 would make the report of a blocked run
    unreachable to the caller that most needs it.
    """
    run = _read_run(run_id)
    step = _current_step(run)

    if step is not None:
        if step.get("status") == STEP_AWAITING_CONFIRMATION:
            _advance_awaiting_step(run, step)
        elif step.get("status") == STEP_NOT_REACHED:
            if step.get("needs_confirmation") and not _action_needs_confirmation(
                step.get("action_id") or ""
            ):
                _refuse_unconfirmable_step(step)
            else:
                _dispatch(run, step)
        # `running`: handed out already, outcome not yet recorded. The
        # same step comes back untouched.

    run["status"] = _run_status_for(run)
    _save_run(run)

    current = _current_step(run)
    handed_out = (
        current if current is not None
        and current.get("status") not in _SETTLED_STEP_STATUSES
        else None
    )
    return {
        "run_id": run["run_id"],
        "workflow_id": run["workflow_id"],
        "status": run["status"],
        "step": handed_out,
        # The latest ledger record for the step that was handed out --
        # where the single-use grant of an `authorised` step and the
        # real result of a `performed` one live. Served from the ledger
        # rather than copied into the run record, so there is one owner
        # of what a call granted.
        "call": _latest_call_record(handed_out),
        "report": None if handed_out is not None else compose_report(run),
        "detail": _where_this_run_stands(run, handed_out),
    }


def _latest_call_record(step: Mapping[str, Any] | None) -> dict | None:
    call_ids = (step or {}).get("call_ids") or []
    if not call_ids:
        return None
    try:
        return action_calls_data.read_call_json(call_ids[-1])
    except (OSError, ValueError):
        return None


def _where_this_run_stands(run: Mapping[str, Any], handed_out: Mapping[str, Any] | None) -> str:
    """One sentence, for the agent to relay to the operator. It never
    says "done" for anything that is not `done`."""
    workflow_id = run.get("workflow_id")
    if handed_out is not None:
        if handed_out.get("status") == STEP_AWAITING_CONFIRMATION:
            return (
                f"run {run['run_id']!r} of workflow {workflow_id!r} is paused at step "
                f"{handed_out['step_id']!r} (position {handed_out['position']}) until the "
                f"operator confirms action call {handed_out.get('awaiting_call_id')!r}. Nothing "
                "beyond this step has been run."
            )
        return (
            f"run {run['run_id']!r} of workflow {workflow_id!r} is on step "
            f"{handed_out['step_id']!r} (position {handed_out['position']}), which runs action "
            f"{handed_out['action_id']!r}. Report its outcome before asking for the next step."
        )
    blocked_at = _current_step(run)
    if blocked_at is not None:
        return (
            f"run {run['run_id']!r} of workflow {workflow_id!r} is blocked at step "
            f"{blocked_at['step_id']!r} (position {blocked_at['position']}), which is "
            f"{blocked_at['status']!r}: {blocked_at.get('refusal') or blocked_at.get('detail')}. "
            "The steps after it were not run."
        )
    return (
        f"run {run['run_id']!r} of workflow {workflow_id!r} has run every documented step and is "
        "complete."
    )


def record_step_outcome(
    run_id: str, step_id: str, outcome: str, detail: str = "", result: Any | None = None,
) -> dict:
    """Record what came of the step this run is on -- and refuse
    anything else.

    Four refusals, each naming its own cause, and all of them before
    anything is written:

    1. a step id this run does not hold (no invented step);
    2. a step that is not the one the run is on (no skipped step);
    3. a step nothing has handed out yet, or one already settled -- a
       step that has not run is not a step that succeeded with no
       output, and an outcome already recorded is not retaken;
    4. an outcome word that is neither `done` nor `failed`.

    The gate's own `dispatch_outcome` is left exactly as it was: what
    the app did and what the caller reports are two different facts
    about one step, and overwriting the first with the second is how a
    `pointed_at` step comes to read as though the app performed it.
    """
    run = _read_run(run_id)

    step = _step_by_id(run, step_id)
    if step is None:
        documented = ", ".join(repr(entry["step_id"]) for entry in run.get("steps") or [])
        raise WorkflowRunRefusedError(
            f"run {run_id!r} of workflow {run.get('workflow_id')!r} holds no step {step_id!r} -- "
            f"its documented steps are {documented}. Nothing was recorded, and no step was added."
        )

    current = _current_step(run)
    if current is None or current.get("step_id") != step_id:
        if current is None:
            raise WorkflowRunRefusedError(
                f"run {run_id!r} has already run every documented step, so there is no outcome "
                f"left to record for step {step_id!r}"
            )
        raise WorkflowRunRefusedError(
            f"run {run_id!r} is on step {current['step_id']!r} (position {current['position']}), "
            f"not step {step_id!r} (position {step['position']}); steps are run in the documented "
            "order and none is skipped, so nothing was recorded"
        )

    if step.get("status") not in _REPORTABLE_STEP_STATUSES:
        raise WorkflowRunRefusedError(_why_this_step_takes_no_outcome(run_id, step))

    if outcome not in REPORTABLE_OUTCOMES:
        raise WorkflowRunRefusedError(
            f"{outcome!r} is not an outcome a step can be reported with; a step is reported "
            f"{STEP_DONE!r} or {STEP_FAILED!r}, and nothing was recorded for step {step_id!r}"
        )

    step["status"] = outcome
    step["recorded_at"] = _now()
    if detail:
        step["detail"] = detail
    if result is not None:
        step["result"] = result
    if outcome == STEP_FAILED:
        step["refusal"] = None

    run["status"] = _run_status_for(run)
    _save_run(run)
    return run


def _why_this_step_takes_no_outcome(run_id: str, step: Mapping[str, Any]) -> str:
    status = step.get("status")
    step_id = step.get("step_id")
    if status == STEP_NOT_REACHED:
        return (
            f"step {step_id!r} of run {run_id!r} has not been handed out yet, so there is nothing "
            "to report about it -- ask for the next step first. A step that has not run is not a "
            "step that succeeded."
        )
    if status == STEP_AWAITING_CONFIRMATION:
        return (
            f"step {step_id!r} of run {run_id!r} is waiting for the operator to confirm action "
            f"call {step.get('awaiting_call_id')!r}; its outcome is not yours to record until "
            "they answer, and nothing was recorded"
        )
    return (
        f"step {step_id!r} of run {run_id!r} is already {status!r}; an outcome that is recorded "
        "is not retaken, and nothing was changed"
    )


def compose_report(run: Mapping[str, Any]) -> dict:
    """What the Workflow said should come back, composed from the
    RECORDED step outcomes at the moment it is asked.

    Never stored on the run: a second copy of a derived answer can
    disagree with the outcomes it was derived from, and the whole point
    of composing it is that a failed step cannot be reported as done.

    `include_step_ids` filters which steps are described; it never
    changes the order, which is always the documented one, and it never
    changes `every_documented_step_done`, which is computed over EVERY
    step -- a report that listed only the two steps the operator asked
    about could otherwise read as complete while a third had failed.

    An id the definition names and the run does not hold is reported,
    not dropped: it means the Workflow's report definition and its steps
    have drifted apart, and silently reporting on fewer steps than were
    asked for is how that stays invisible.
    """
    steps = list(run.get("steps") or [])
    included_ids = set((run.get("report") or {}).get("include_step_ids") or [])
    described = [step for step in steps if not included_ids or step["step_id"] in included_ids]
    held_ids = {step["step_id"] for step in steps}
    return {
        "run_id": run.get("run_id"),
        "workflow_id": run.get("workflow_id"),
        "request_kind": run.get("request_kind"),
        "status": run.get("status"),
        "description": (run.get("report") or {}).get("description", ""),
        "every_documented_step_done": bool(steps) and all(
            step.get("status") == STEP_DONE for step in steps
        ),
        "steps": [
            {
                "step_id": step["step_id"],
                "position": step["position"],
                "action_id": step["action_id"],
                "description": step.get("description", ""),
                "status": step.get("status"),
                "dispatch_outcome": step.get("dispatch_outcome"),
                "detail": step.get("detail"),
                "result": step.get("result"),
                "refusal": step.get("refusal"),
                "call_ids": list(step.get("call_ids") or []),
            }
            for step in described
        ],
        "steps_named_by_the_report_that_this_run_has_no_step_for": sorted(
            included_ids - held_ids
        ),
    }
