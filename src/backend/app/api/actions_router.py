"""The Action catalogue's HTTP surface (REQ-SB-95-US-02-T03) -- flat and
single-purpose, the same one-router-per-entity convention
skills_router.py / index_router.py / pipelines_router.py already use.

This router composes; it does not decide. Cardinality (exactly one
implementation), save-time resolution and the per-Action broken status
are all ActionManager's own rules (ADR-032), so the only thing that
happens here is turning the Manager's refusal into an HTTP status --
never into a different message. A refused save reaches the client
carrying the Manager's sentence verbatim, because that sentence names
the skill / route / feature key that did not resolve and the operator
cannot act on "400 Bad Request".

409 for a refusal, not 422: FastAPI already owns 422 for its own
request-validation errors, whose `detail` is a LIST of error objects. A
Manager refusal sent under the same code would force the catalogue
screen to tell two different `detail` shapes apart before it could show
the operator anything. 409 is also what sections_router.py and
blueprints_router.py already return when a Manager refuses a write.

`POST /actions/{action_id}/call` is deliberately absent rather than
stubbed -- it lands here in REQ-SB-95-US-03-T02 with the invocation
gate that gives it meaning.

**Read and write shape the implementation differently, and a client has
to map between them.** A write sends the kind as a KEY --
`{"implementation": {"skill": {"skill_id": "..."}}}` -- because which
keys are present is what "exactly one" is counted over, and that is
also the shape stored in Action.json. A read returns the Action entity,
whose implementation is FLAT -- `{"kind": "skill", "skill_id": "...",
"method": "", "path": "", "feature_key": ""}`. Putting a GET body
straight back therefore refuses with the exactly-one message (it names
no kind key), loudly rather than silently. The entity shape is kept on
the read because every other detail route here returns the real
dataclass, and the rest of the backend already speaks it.

Three other fields are read-only and are NOT accepted on a write: `id`
after creation, `created_at` and `updated_at` (the Manager owns both
timestamps). An editor must render them as facts, never as inputs.

**A whole Action can be read-only too.** The list carries `plugin_id`
on an entry a loaded plugin contributed and omits the key entirely on
one this install stored -- the only thing a client has to tell them
apart by. Every write path on a contributed one refuses with the same
409 a Manager refusal gets, carrying the Manager's own sentence naming
the plugin (REQ-SB-95-US-02-T06, against ESC-069).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business.core.actions.action import Action
from app.business.core.actions.action_manager import (
    ActionImplementationCardinalityError,
    ActionImplementationUnresolvedError,
    ActionManager,
    PluginContributedActionIsReadOnlyError,
)

router = APIRouter(prefix="/actions")
_action_manager = ActionManager()


class ActionImplementationBody(BaseModel):
    """The three kind keys are typed because which keys are present IS
    the cardinality question; each kind's own spec is passed through as
    the client sent it, because what the fields inside mean belongs to
    the entity and the Manager. Typing the inner specs here would make
    this router silently drop any field it had not been taught about --
    a write path quietly accepting less than it appears to.
    """
    skill: dict[str, Any] | None = None
    http: dict[str, Any] | None = None
    ui: dict[str, Any] | None = None


class ActionInputBody(BaseModel):
    name: str
    type: str = "string"
    required: bool = False
    description: str = ""


class ActionCreateBody(BaseModel):
    id: str
    description: str = ""
    inputs: list[ActionInputBody] = []
    allowed_callers: list[str] = []
    needs_confirmation: bool = False
    # Omitted entirely is a real case, and NOT one this router answers:
    # it goes to the Manager as None and comes back as the exactly-one
    # refusal, so "no implementation" and "two implementations" are
    # refused by one rule in one place with one message.
    implementation: ActionImplementationBody | None = None


class ActionUpdateBody(BaseModel):
    """Omitted (None) = leave unchanged, for every field -- the update
    convention SectionUpdateBody and AgentUpdateBody already set. An
    omitted implementation keeps the stored one and is not re-resolved
    (ActionManager.update's own documented rule), so editing a
    description cannot be refused because something else on the install
    broke in the meantime."""
    description: str | None = None
    inputs: list[ActionInputBody] | None = None
    allowed_callers: list[str] | None = None
    needs_confirmation: bool | None = None
    implementation: ActionImplementationBody | None = None


def _implementation_payload(body: ActionImplementationBody | None) -> dict[str, Any] | None:
    """`exclude_none` so an unnamed kind is absent from the stored
    definition rather than present-and-null -- the Manager keys
    cardinality off `is not None`, and a file full of explicit nulls
    would still read correctly but would travel through export/import
    carrying kinds the Action does not have."""
    if body is None:
        return None
    return body.model_dump(exclude_none=True)


def _refusal(exc: Exception) -> HTTPException:
    return HTTPException(status_code=409, detail=str(exc))


@router.get("")
def list_actions() -> list[dict]:
    """Every catalogued Action with its live resolution status attached
    (AC-07). The status is recomputed by the Manager on every call and
    is never stored, so this list tells the operator what is broken
    right now without anything having had to call an Action."""
    status_by_action_id = {
        entry["action_id"]: entry for entry in _action_manager.resolution_report()
    }
    catalogue = []
    for action in _action_manager.get_all():
        status = status_by_action_id.get(action.id)
        entry = {
            "id": action.id,
            "description": action.description,
            "implementation_kind": action.implementation.kind if action.implementation else None,
            # An Action the report did not cover is shown as broken, not
            # as fine and not dropped: an unchecked entry resolving to
            # "healthy" is the exact failure ADR-032 exists to prevent.
            "status": status["status"] if status else "broken",
            "reason": status["reason"] if status else "this Action's implementation was not checked",
        }
        # Present only on a contributed entry, absent (not null) on a stored
        # one -- the wire shape then says exactly what ActionManager says:
        # a stored Action has no `plugin_id` attribute at all, rather than
        # an empty one. getattr for the same reason: reading the field
        # directly would raise on every Action the operator saved.
        plugin_id = getattr(action, "plugin_id", "")
        if plugin_id:
            entry["plugin_id"] = plugin_id
        catalogue.append(entry)
    return catalogue


@router.get("/{action_id}")
def get_action(action_id: str) -> Action:
    action = _action_manager.get_by_id(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id!r}")
    return action


@router.post("")
def create_action(body: ActionCreateBody) -> Action:
    try:
        return _action_manager.create(
            body.id,
            description=body.description,
            inputs=[entry.model_dump() for entry in body.inputs],
            allowed_callers=body.allowed_callers,
            needs_confirmation=body.needs_confirmation,
            implementation=_implementation_payload(body.implementation),
        )
    except (ActionImplementationCardinalityError, ActionImplementationUnresolvedError) as exc:
        raise _refusal(exc)


@router.put("/{action_id}")
def update_action(action_id: str, body: ActionUpdateBody) -> Action:
    try:
        action = _action_manager.update(
            action_id,
            description=body.description,
            inputs=None if body.inputs is None else [entry.model_dump() for entry in body.inputs],
            allowed_callers=body.allowed_callers,
            needs_confirmation=body.needs_confirmation,
            implementation=_implementation_payload(body.implementation),
        )
    except (
        ActionImplementationCardinalityError,
        ActionImplementationUnresolvedError,
        PluginContributedActionIsReadOnlyError,
    ) as exc:
        raise _refusal(exc)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id!r}")
    return action


@router.delete("/{action_id}")
def delete_action(action_id: str) -> dict:
    """Unguarded on purpose: the Workflow reverse-lookup guard arrives
    with the Workflow kind itself (REQ-SB-95-US-04-T02), and no Workflow
    can reference an Action today. Deleting an unknown id is
    {"deleted": False}, never a 404 -- ADR-014's result-dict convention,
    which ActionManager.delete already follows. A plugin-contributed
    Action is the one id that refuses rather than reporting a result:
    there is nothing stored to delete, and both {"deleted": true} and
    {"deleted": false} would be a lie about a row the operator is
    looking at."""
    try:
        return _action_manager.delete(action_id)
    except PluginContributedActionIsReadOnlyError as exc:
        raise _refusal(exc)
