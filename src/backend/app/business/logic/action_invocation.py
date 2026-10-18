"""The one validating door onto the Action catalogue (`ADR-033`,
REQ-SB-95-US-03-T02).

Every Action call -- from the shipped runner Skill over loopback, from
the in-app UI, later from a Workflow step -- arrives here, and here is
where it is refused. The refusal therefore comes from the framework and
no prompt text can route around it, which is the whole of `ADR-032`'s
"publishing the catalogue makes the agent likely to be right;
validating the call is what makes it true".

**It reads the LIVE catalogue, never the published SOUL block.** A
block left stale by a failed publication can mislead an agent about what
exists; it can never let a call through (`ADR-033`).

Four failure classes, checked in this order, each naming its own cause:

1. the action id is not in the live catalogue;
2. the caller is not in `allowed_callers` (`ActionManager.is_callable_by`
   answers it, so publication and the gate cannot drift about what
   `["*"]` means);
3. an input is required and missing, or passed and not declared;
4. the implementation no longer resolves -- the second line behind
   `ActionManager`'s save-time check (REQ-SB-95-US-02-T02), because what
   an Action points at is undeployed or unmounted by events the
   catalogue never sees.

Cheapest-and-most-fundamental first is not an optimisation: a call
naming an action that does not exist has no `allowed_callers` to check
and no inputs to validate, so any other order would have to invent an
answer to a question the data cannot answer.

**Nothing is half-performed.** Validation completes in full before the
dispatch seam is entered even once, and a refusal returns before it is
entered at all.

**Then dispatch by kind, and the app does not perform what it does not
own** (`ADR-033`, REQ-SB-95-US-03-T03). An `http` implementation is
performed, in process, against this app's own route, and only a 2xx is
`performed` -- built and proved in `_perform_http_implementation()`,
but deliberately not yet wired into the seam, for the reason
`dispatch_validated_action_call()` records (`ESC-073`). A `ui`
implementation is never performed -- the answer names the screen the
operator does it on. A `skill` implementation is
`authorised`, not performed: the answer carries a single-use grant the
runner spends once and performs in the profile where Skills already
run, because `ADR-019` keeps `skills/catalog/` as payload this app
never imports and this app is not a second executor of it.

The ledger is written TWICE for an accepted call -- `validated` before
dispatch is entered, then whatever dispatch really reported. A call
that crashes mid-dispatch therefore leaves a record saying only that it
was allowed to proceed, never one claiming an operation happened.

**No silent fallback.** A missing required input is named, never
defaulted, inferred or substituted -- including by this module's own
record of the call, so the ledger shows exactly what the caller sent.
"""
from __future__ import annotations

import asyncio
import logging
import urllib.parse
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

import httpx

from app.business.core.actions.action import Action
from app.business.core.actions.action_manager import ActionManager
from app.data_access import action_calls as action_calls_data

_logger = logging.getLogger(__name__)

# The reason tokens that appear in a `refused:<reason>` ledger outcome.
# Stable strings, not prose: the sentence beside them is for the
# operator and may be reworded, while a caller (and a later
# capability-gap review over this ledger) counts these.
REFUSED_UNKNOWN_ACTION = "unknown_action"
REFUSED_CALLER_NOT_PERMITTED = "caller_not_permitted"
REFUSED_MISSING_REQUIRED_INPUT = "missing_required_input"
REFUSED_UNKNOWN_INPUT = "unknown_input"
REFUSED_IMPLEMENTATION_DOES_NOT_RESOLVE = "implementation_does_not_resolve"

# Written the moment validation passes and BEFORE the dispatch seam is
# entered. A call that crashes or never returns therefore leaves a
# record saying only that it was allowed to proceed -- never one
# claiming an operation happened. `performed` and its siblings are
# written over this by whatever dispatch reports (`ADR-033`).
OUTCOME_VALIDATED = "validated"

# What a dispatch path that does not exist reports. Deliberately not
# one of `ADR-033`'s outcome values: a validated call nothing dispatched
# is neither performed nor refused, and recording it as either would be
# the claimed-success failure this whole gate exists to prevent.
OUTCOME_NOT_DISPATCHED = "not_dispatched"

# The three things dispatch can honestly report about an accepted call
# (`ADR-033`, REQ-SB-95-US-03-T03). They are three words rather than one
# because the app does three DIFFERENT things, and collapsing them would
# let "the operator still has to do this themselves" read as "done":
#
# - `performed`  -- an `http` implementation the app owns and really ran;
# - `pointed_at` -- a `ui` implementation, never performed by the app;
# - `authorised` -- a `skill` implementation, granted to the runner that
#                   performs it in the profile where Skills already run.
OUTCOME_PERFORMED = "performed"
OUTCOME_POINTED_AT = "pointed_at"
OUTCOME_AUTHORISED = "authorised"

# A dispatch that was entered and did not succeed. Written over the
# `validated` record exactly like a success would be, so a failure is
# never left looking like a call still in flight -- and never, under any
# circumstance, like `performed`.
OUTCOME_FAILED = "failed"

# Methods whose validated inputs travel as a JSON body; every other
# method sends them as query parameters. A convention, declared in one
# place: an Action's inputs are named values, and nothing in the
# catalogue says where on the wire each one belongs.
_HTTP_METHODS_WITH_A_BODY = ("POST", "PUT", "PATCH")

# Long enough for this app's own slowest route (a full vault re-index),
# short enough that a wedged route cannot hold the caller forever.
_HTTP_DISPATCH_TIMEOUT_SECONDS = 180.0

# `actions_router.py`'s own call route, named here as a literal rather
# than imported (api -> business is the only allowed direction,
# `ADR-003`). It is on the live route table, so an `http` Action may
# legally be saved pointing AT THE GATE ITSELF -- which would then
# dispatch into the gate, which would dispatch into the gate, each
# level on a fresh event loop and a fresh worker thread, until the
# process ran out of either. Refused by name instead.
_THE_CALL_GATES_OWN_ROUTE = ("POST", "/actions/{action_id}/call")


@dataclass
class ActionCallVerdict:
    """What the gate decided, and the ledger id it decided it under.

    `accepted` is the one field a caller must branch on. It is separate
    from `outcome` on purpose: `outcome` grows new values with every
    task in this story (`performed`, `awaiting_confirmation`,
    `declined`, a dispatch failure), and a runner that had to enumerate
    them to find out whether it was refused would silently treat each
    new one as success.
    """
    call_id: str
    action_id: str
    caller_agent_id: str
    accepted: bool
    outcome: str
    refusal: str | None = None
    # What dispatch reported about an accepted call, in words the agent
    # can relay -- an accepted call must say what happened, not only
    # carry an outcome token.
    detail: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    # What the app's own route really returned, on an `http`
    # implementation it performed. None on every other kind, because
    # nothing ran: `ADR-032`'s "the operator sees the result of the real
    # operation, not a description of it" is this field or nothing.
    result: Any | None = None
    # The single-use grant a `skill` implementation is authorised by --
    # the deployed skill id, the validated inputs and the call id it is
    # spent under. None on every other kind. The app does NOT perform
    # it (`ADR-019`, `ADR-033`): the runner does, in its own profile.
    grant: dict[str, Any] | None = None
    # Where the operator performs a `ui` implementation themselves --
    # the front-end feature key, which IS that screen's route. Named in
    # full rather than left inside the sentence so a screen can link to
    # it without parsing prose.
    where_the_operator_does_it: str | None = None


def _bind_path_parameters(path: str, inputs: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Substitutes the inputs the route declares as path parameters and
    hands back the path plus the ones still to place.

    An input consumed here must NOT also travel as a query parameter or
    in the body -- the route would then see the same name twice and
    FastAPI would answer about the wrong one. Quoted, because an input
    is operator data: a stem containing `/` or `?` must reach the route
    as one segment, not as a different route.
    """
    bound_path = path
    unplaced = dict(inputs)
    for name in list(unplaced):
        placeholder = "{" + name + "}"
        if placeholder in bound_path:
            bound_path = bound_path.replace(
                placeholder, urllib.parse.quote(str(unplaced.pop(name)), safe=""),
            )
    return bound_path, unplaced


async def _request_this_apps_own_route(
    method: str, path: str, inputs: Mapping[str, Any],
) -> httpx.Response:
    """One request into this very app, in process -- no socket, no port,
    no loopback hop.

    `ASGITransport` hands the request straight to the ASGI application
    object, so the real route, its real dependencies and the real
    middleware stack all run, while a test (and an install whose port
    moved, or which is reached through a reverse proxy) cannot
    accidentally reach a DIFFERENT backend that happens to be listening
    on 8001. "Performed by the app" means by THIS app.

    Imported inside the function for the reason `app_route_table()`
    already documents: `app.main` imports the API layer, which imports
    this module, so a module-level import would be a cycle and would
    invert `ADR-003`'s api -> business direction.
    """
    from app.main import app

    bound_path, unplaced_inputs = _bind_path_parameters(path, inputs)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://action-dispatch.localhost",
        timeout=_HTTP_DISPATCH_TIMEOUT_SECONDS,
    ) as in_process_client:
        if method in _HTTP_METHODS_WITH_A_BODY:
            return await in_process_client.request(method, bound_path, json=unplaced_inputs)
        return await in_process_client.request(method, bound_path, params=unplaced_inputs)


def _body_of(response: httpx.Response) -> Any:
    """The route's real answer. JSON when the route produced JSON, the
    raw text otherwise -- never a summary of it, and never an exception
    swallowing a body the operator is owed."""
    try:
        return response.json()
    except ValueError:
        return response.text


def _perform_http_implementation(
    action: Action, method: str, path: str, validated_inputs: Mapping[str, Any],
) -> dict:
    """The one kind the app owns and really runs (`ADR-033`).

    **Complete, tested, and not yet reached from
    `dispatch_validated_action_call()`** -- see the reason recorded
    there and in `ESC-073`. It is exercised directly by
    `tests/test_action_dispatch.py`, so what it does is proved rather
    than promised; only the one line that routes the `http` branch to
    it is outstanding.

    **Only 2xx is `performed`.** A route answering 4xx or 5xx did not do
    the thing, and reporting it as done -- with its own error body
    attached as if it were a result -- is precisely the fabricated
    outcome `REQ-SB-95` exists to make impossible. The real status and
    the real body travel back either way, so the operator sees what
    happened rather than a description of it.
    """
    if (method, path) == _THE_CALL_GATES_OWN_ROUTE:
        return {
            "outcome": OUTCOME_FAILED,
            "detail": (
                f"action {action.id!r} names this app's own Action-call route as its http "
                "implementation, which would call the gate from inside the gate without end; "
                "it was refused rather than dispatched, and nothing was performed"
            ),
        }
    try:
        response = asyncio.run(_request_this_apps_own_route(method, path, validated_inputs))
    except Exception as exc:
        # Deliberately broad: whatever a route can raise through the ASGI
        # stack (a timeout, a transport error, an unhandled bug) means the
        # same thing to the caller -- the operation did not happen -- and
        # an exception escaping here would reach the agent as a backend
        # fault indistinguishable from a refusal.
        _logger.warning(
            "action %r dispatched %s %s and it raised", action.id, method, path, exc_info=True,
        )
        return {
            "outcome": OUTCOME_FAILED,
            "detail": (
                f"action {action.id!r} was dispatched to this app's own {method} {path} and it "
                f"failed with {type(exc).__name__}: {exc}. Nothing was performed."
            ),
        }

    body = _body_of(response)
    if response.is_success:
        return {
            "outcome": OUTCOME_PERFORMED,
            "detail": (
                f"this app performed action {action.id!r} by running its own {method} {path}, "
                f"which answered HTTP {response.status_code}"
            ),
            "result": body,
        }
    return {
        "outcome": OUTCOME_FAILED,
        "detail": (
            f"action {action.id!r} was dispatched to this app's own {method} {path} and it "
            f"answered HTTP {response.status_code}, so the operation did NOT happen"
        ),
        "result": body,
    }


def _point_at_ui_implementation(action: Action, feature_key: str) -> dict:
    """Never performed, by decision and not by omission (`ADR-032`'s
    "point to but not perform", `ADR-033`). The app has no way to click
    a screen on the operator's behalf, and an agent that reported a `ui`
    Action as done would be describing something nobody did.

    The feature key IS the front-end route, so naming it is a usable
    instruction rather than a label.
    """
    return {
        "outcome": OUTCOME_POINTED_AT,
        "detail": (
            f"action {action.id!r} is something only the operator can do, on this app's "
            f"{feature_key!r} screen. Nothing was performed -- tell the operator to go there."
        ),
        "where_the_operator_does_it": feature_key,
    }


def _authorise_skill_implementation(
    action: Action, skill_id: str, caller_agent_id: str, validated_inputs: Mapping[str, Any],
) -> dict:
    """Authorised, not performed (`ADR-033`). The app does not become a
    second executor of Skill payload: `ADR-019` keeps
    `skills/catalog/` as payload this app never imports, and the
    deployed copy that actually runs lives in a Hermes profile this
    process does not own.

    So what comes back is a grant -- the deployed skill id, the
    validated inputs, and the profile it is granted to -- which the
    runner spends exactly once (`consume_single_use_grant`) and performs
    in its own profile.

    The `call_id` is stamped on by `call_action`, not minted here: the
    grant is spent against the ledger record of THIS call, and the seam
    is deliberately not told the call id (the gate owns it, and `T02`'s
    contract is that this seam's signature is the whole of dispatch's
    input).
    """
    return {
        "outcome": OUTCOME_AUTHORISED,
        "detail": (
            f"action {action.id!r} is performed by the deployed skill {skill_id!r} in agent "
            f"{caller_agent_id!r}'s own profile, not by this app. This call is AUTHORISED: run "
            "that skill with the granted inputs, once. Nothing has been performed yet."
        ),
        "grant": {
            "skill_id": skill_id,
            "caller_agent_id": caller_agent_id,
            "inputs": dict(validated_inputs),
            "granted_at": _now(),
        },
    }


def dispatch_validated_action_call(
    action: Action, caller_agent_id: str, validated_inputs: Mapping[str, Any],
) -> dict:
    """Dispatch by implementation kind, and the app does not perform
    what it does not own (`ADR-033`, REQ-SB-95-US-03-T03).

    The single named place dispatch begins at, so "validation finishes
    before dispatch begins" stays checkable (`T02`). Returns what the
    ledger records and what the verdict carries: an outcome, a sentence,
    and -- depending on the kind -- the real result, the grant, or the
    screen the operator does it on.

    An Action reaching here with no implementation, or with a kind
    nothing dispatches, is reported as a failure rather than quietly
    returning success. It should be unreachable (`ActionManager` refuses
    to save either, and the gate re-checks resolution immediately
    before this), which is exactly why it must not be silent if it ever
    happens.

    **`http` is built and proved but deliberately NOT wired here yet
    (`ESC-073`).** `_perform_http_implementation()` below is complete and
    tested directly; routing this branch to it is a one-line change. It
    waits because wiring it makes two tests in
    `tests/test_action_invocation_gate.py` -- a file outside this task's
    `## Files to Modify` -- stop telling the truth: one pins the
    transitional `not_dispatched` outcome `T02` wrote for exactly this
    moment, and the other points a test Action at the REAL
    `POST /vault-index/refresh`, which live dispatch turns into a full
    re-read of the operator's vault on every run of the suite (measured:
    1s to 8.6s). Reporting `not_dispatched` meanwhile is what `T02`
    already shipped for every kind, so nothing regresses and nothing
    claims to have run.
    """
    implementation = action.implementation
    if implementation is None:
        return {
            "outcome": OUTCOME_FAILED,
            "detail": (
                f"action {action.id!r} passed validation but names no implementation, so there "
                "was nothing to dispatch and nothing was performed"
            ),
        }
    if implementation.kind == "http":
        return {
            "outcome": OUTCOME_NOT_DISPATCHED,
            "detail": (
                f"action {action.id!r} passed every validation; dispatching an http "
                "implementation is not implemented yet in this gate (REQ-SB-95-US-03-T03 "
                "built and proved the performer; ESC-073 holds the wiring), so nothing "
                "was performed"
            ),
        }
    if implementation.kind == "ui":
        return _point_at_ui_implementation(action, implementation.feature_key)
    if implementation.kind == "skill":
        return _authorise_skill_implementation(
            action, implementation.skill_id, caller_agent_id, validated_inputs,
        )
    return {
        "outcome": OUTCOME_NOT_DISPATCHED,
        "detail": (
            f"action {action.id!r} names a {implementation.kind!r} implementation, which this "
            "app has no way to dispatch; nothing was performed"
        ),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_call(
    call_id: str, action_id: str, caller_agent_id: str,
    inputs: Mapping[str, Any], outcome: str, refusal: str | None,
    detail: str | None = None, result: Any | None = None,
    grant: Mapping[str, Any] | None = None,
) -> None:
    """One ledger file per call, rewritten in place as the call
    progresses -- there is exactly one record per `call_id`, so
    confirmation (T04) turns a record into a grant rather than opening
    a second row about the same call.

    `detail`, `result` and `grant` are what dispatch reported
    (REQ-SB-95-US-03-T03). The grant is written here, into the record
    itself, because the record IS the grant: spending it is a claim
    against this call id, so a grant that lived only in the response
    could be spent by anyone who had the response and by nobody who had
    the ledger.

    A ledger write that fails must not turn a correct refusal into a
    500: the caller still has to be told it was refused, and a lost
    audit row is a smaller harm than a refusal the agent never hears.
    Logged loudly rather than swallowed.
    """
    try:
        action_calls_data.write_call_json(call_id, {
            "call_id": call_id,
            "action_id": action_id,
            "caller_agent_id": caller_agent_id,
            "inputs": dict(inputs),
            "outcome": outcome,
            "refusal": refusal,
            "detail": detail,
            "result": result,
            "grant": dict(grant) if grant is not None else None,
            "recorded_at": _now(),
        })
    except OSError:
        _logger.warning(
            "action call %s on %r by %r ended %s but could not be written to the ledger",
            call_id, action_id, caller_agent_id, outcome, exc_info=True,
        )


@dataclass
class GrantConsumption:
    """Whether one single-use grant was spent by THIS caller, and what
    it granted. `consumed` is the one field to branch on, for the same
    reason `ActionCallVerdict.accepted` is: a second spender must be
    refused in a way it cannot mistake for success."""
    call_id: str
    consumed: bool
    refusal: str | None = None
    grant: dict[str, Any] | None = None


def consume_single_use_grant(
    call_id: str, reported_outcome: str | None = None, reported_detail: str | None = None,
) -> GrantConsumption:
    """Spend one grant, exactly once, ever.

    **One mechanism, not two.** A `skill` dispatch's grant
    (REQ-SB-95-US-03-T03) and a confirmation grant (`T04`) are the same
    object spent the same way: a claim on the call id, taken through
    `action_calls.claim_call_once()`, whose exclusivity is the
    filesystem's rather than a read-then-write this module could lose a
    race on.

    The claim is taken BEFORE the record is updated, and the record
    update is allowed to fail: a grant whose bookkeeping failed is
    already spent, which is the safe direction. The opposite order
    could mark it spent, fail, and leave it spendable again.

    `reported_outcome` is for the consumer that already knows what
    happened -- the runner coming back to say the Skill really ran.
    Left out, the record keeps the outcome dispatch gave it and only
    gains the fact that its grant is now spent.
    """
    try:
        record = action_calls_data.read_call_json(call_id)
    except (OSError, ValueError):
        return GrantConsumption(
            call_id=call_id, consumed=False,
            refusal=f"there is no action call {call_id!r} in this install's ledger, so it grants nothing",
        )

    grant = record.get("grant")
    if not grant:
        return GrantConsumption(
            call_id=call_id, consumed=False,
            refusal=(
                f"action call {call_id!r} carries no grant to consume -- it ended "
                f"{record.get('outcome')!r}, and nothing about it authorises anything"
            ),
        )

    if not action_calls_data.claim_call_once(call_id, {
        "call_id": call_id,
        "consumed_at": _now(),
        "reported_outcome": reported_outcome,
    }):
        return GrantConsumption(
            call_id=call_id, consumed=False,
            refusal=(
                f"the grant on action call {call_id!r} has already been consumed; a grant is "
                "single-use, so nothing was performed this time -- call the action again to "
                "be granted afresh"
            ),
        )

    record["grant"] = {**grant, "consumed_at": _now()}
    if reported_outcome is not None:
        record["outcome"] = reported_outcome
        record["detail"] = reported_detail
    record["recorded_at"] = _now()
    try:
        action_calls_data.write_call_json(call_id, record)
    except OSError:
        _logger.warning(
            "the grant on action call %s was consumed but the ledger record could not be "
            "updated to say so; the grant is spent and cannot be spent again",
            call_id, exc_info=True,
        )
    return GrantConsumption(call_id=call_id, consumed=True, grant=dict(grant))


def _missing_required_input_names(action: Action, inputs: Mapping[str, Any]) -> list[str]:
    """An input is supplied when the caller sent a value for it. An
    explicit `null` counts as NOT supplied: passing it on would hand
    dispatch a value the caller never had, which is the substitution
    `ADR-032` forbids. An empty string is a real value and is left
    alone -- the gate refuses what was not asked for, it does not judge
    what was.

    Declaration order, not alphabetical: the operator is about to be
    asked for these by name, in the order the Action lists them.
    """
    return [
        declared.name for declared in action.inputs
        if declared.required and inputs.get(declared.name) is None
    ]


def _undeclared_input_names(action: Action, inputs: Mapping[str, Any]) -> list[str]:
    declared_names = {declared.name for declared in action.inputs}
    return [name for name in inputs if name not in declared_names]


def _unresolved_reason(action_id: str) -> str | None:
    """Asked of `ActionManager.resolution_report()` rather than of the
    resolution internals: it is the Manager's own public, never-cached
    read of the live sources, so the gate cannot drift from what the
    catalogue screen shows the operator about the same Action.

    An Action the report does not cover is treated as broken, never as
    fine -- the same stance actions_router.py's list takes, and the
    silent-success failure `ADR-032` exists to prevent.
    """
    for entry in ActionManager().resolution_report():
        if entry["action_id"] == action_id:
            return entry["reason"] if entry["status"] != "resolves" else None
    return "this Action's implementation was not checked"


def _names(names: list[str]) -> str:
    return ", ".join(repr(name) for name in names)


def call_action(
    action_id: str, caller_agent_id: str, inputs: Mapping[str, Any] | None = None,
) -> ActionCallVerdict:
    """Validate one call against the live catalogue and, only if every
    check passes, enter dispatch exactly once.

    Never raises for a refused call: a refusal is a first-class answer
    (`ADR-033`), carries a ledger id, and has to reach the agent as
    words it can relay to the operator. An exception would make the
    four failure classes indistinguishable from a backend fault.
    """
    call_id = uuid.uuid4().hex
    supplied_inputs = dict(inputs or {})

    def refuse(reason: str, sentence: str) -> ActionCallVerdict:
        outcome = f"refused:{reason}"
        _record_call(call_id, action_id, caller_agent_id, supplied_inputs, outcome, sentence)
        return ActionCallVerdict(
            call_id=call_id, action_id=action_id, caller_agent_id=caller_agent_id,
            accepted=False, outcome=outcome, refusal=sentence, inputs=supplied_inputs,
        )

    action = ActionManager().get_by_id(action_id)
    if action is None:
        return refuse(
            REFUSED_UNKNOWN_ACTION,
            f"there is no action {action_id!r} in this install's catalogue, so it cannot be called",
        )

    # A caller that named nothing is refused here rather than being let
    # through by a wildcard: `["*"]` means every agent, and an empty
    # string is not an agent (`ADR-033` -- the caller names its own
    # Hermes profile id and the app believes it; believing a blank one
    # would record a call nobody made).
    if not caller_agent_id.strip():
        return refuse(
            REFUSED_CALLER_NOT_PERMITTED,
            f"this call named no caller agent id, so it may not run action {action_id!r}",
        )
    if not ActionManager.is_callable_by(action, caller_agent_id):
        return refuse(
            REFUSED_CALLER_NOT_PERMITTED,
            f"agent {caller_agent_id!r} may not run action {action_id!r}",
        )

    missing = _missing_required_input_names(action, supplied_inputs)
    if missing:
        return refuse(
            REFUSED_MISSING_REQUIRED_INPUT,
            f"action {action_id!r} requires {_names(missing)}, which this call did not supply; "
            "ask for it by name -- nothing is guessed or defaulted in its place",
        )
    undeclared = _undeclared_input_names(action, supplied_inputs)
    if undeclared:
        return refuse(
            REFUSED_UNKNOWN_INPUT,
            f"action {action_id!r} declares no input named {_names(undeclared)}; "
            "it was not dropped and nothing was run with it",
        )

    unresolved = _unresolved_reason(action_id)
    if unresolved is not None:
        return refuse(
            REFUSED_IMPLEMENTATION_DOES_NOT_RESOLVE,
            f"action {action_id!r} can no longer run on this install: {unresolved}",
        )

    # Built from the DECLARED inputs rather than handed the payload
    # through, so "only declared inputs reach dispatch" is true by
    # construction and not merely because the undeclared check above
    # ran first. Absent optional inputs stay absent -- an optional
    # input filled in here would be the guess this gate refuses.
    validated_inputs = {
        declared.name: supplied_inputs[declared.name]
        for declared in action.inputs if declared.name in supplied_inputs
    }

    # Recorded BEFORE dispatch. Confirmation (T04) inserts here, between
    # a complete validation and the first thing that could perform
    # anything.
    _record_call(call_id, action_id, caller_agent_id, validated_inputs, OUTCOME_VALIDATED, None)

    dispatched = dispatch_validated_action_call(action, caller_agent_id, validated_inputs)
    outcome = dispatched.get("outcome") or OUTCOME_NOT_DISPATCHED

    # The call id is stamped onto the grant HERE rather than inside the
    # seam: the grant is spent against this call's own ledger record, and
    # the gate is what owns the id. It also keeps the seam's signature
    # exactly as `T02` fixed it.
    granted = dispatched.get("grant")
    grant = None if granted is None else {**granted, "call_id": call_id, "single_use": True}

    _record_call(
        call_id, action_id, caller_agent_id, validated_inputs, outcome, None,
        detail=dispatched.get("detail"), result=dispatched.get("result"), grant=grant,
    )

    return ActionCallVerdict(
        call_id=call_id, action_id=action_id, caller_agent_id=caller_agent_id,
        accepted=True, outcome=outcome, refusal=None,
        detail=dispatched.get("detail"), inputs=validated_inputs,
        result=dispatched.get("result"), grant=grant,
        where_the_operator_does_it=dispatched.get("where_the_operator_does_it"),
    )
