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

**No silent fallback.** A missing required input is named, never
defaulted, inferred or substituted -- including by this module's own
record of the call, so the ledger shows exactly what the caller sent.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

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

# What the not-yet-implemented dispatch seam reports today
# (REQ-SB-95-US-03-T03 fills it). Deliberately not one of `ADR-033`'s
# four outcome values: a validated call whose dispatch does not exist
# yet is neither performed nor refused, and recording it as either
# would be the claimed-success failure this whole gate exists to
# prevent.
OUTCOME_NOT_DISPATCHED = "not_dispatched"


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
    # What dispatch reported about an accepted call. Today that is the
    # sentence saying nothing ran -- an accepted call must say so in
    # words the agent can relay, not only in an outcome token.
    detail: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)


def dispatch_validated_action_call(
    action: Action, caller_agent_id: str, validated_inputs: Mapping[str, Any],
) -> dict:
    """The seam REQ-SB-95-US-03-T03 fills with dispatch by
    implementation kind -- `http` performed, `ui` pointed at, `skill`
    authorised by single-use grant (`ADR-033`).

    It exists already, unimplemented, rather than being inlined later:
    the gate's contract is that validation finishes before dispatch
    begins, and that is only checkable if there is a single named place
    dispatch begins at.

    Returns the outcome the ledger records. Today that outcome says, in
    one word, that nothing ran -- a successful validation must never
    read as a performed operation.
    """
    return {
        "outcome": OUTCOME_NOT_DISPATCHED,
        "detail": (
            f"action {action.id!r} passed every validation; dispatching a "
            f"{action.implementation.kind if action.implementation else 'missing'} "
            "implementation is not implemented yet (REQ-SB-95-US-03-T03), so nothing was performed"
        ),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_call(
    call_id: str, action_id: str, caller_agent_id: str,
    inputs: Mapping[str, Any], outcome: str, refusal: str | None,
) -> None:
    """One ledger file per call, rewritten in place as the call
    progresses -- there is exactly one record per `call_id`, so
    confirmation (T04) turns a record into a grant rather than opening
    a second row about the same call.

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
            "recorded_at": _now(),
        })
    except OSError:
        _logger.warning(
            "action call %s on %r by %r ended %s but could not be written to the ledger",
            call_id, action_id, caller_agent_id, outcome, exc_info=True,
        )


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
    _record_call(call_id, action_id, caller_agent_id, validated_inputs, outcome, None)

    return ActionCallVerdict(
        call_id=call_id, action_id=action_id, caller_agent_id=caller_agent_id,
        accepted=True, outcome=outcome, refusal=None,
        detail=dispatched.get("detail"), inputs=validated_inputs,
    )
