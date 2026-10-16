from __future__ import annotations

from dataclasses import dataclass, field

# The three implementation kinds ADR-032 allows, and nothing else. An
# Action carries exactly ONE of them (ActionManager enforces that).
IMPLEMENTATION_KINDS = ("skill", "http", "ui")


@dataclass
class ActionInput:
    name: str
    # The declared input type, as the catalogue publishes it to a caller
    # ("string", "boolean", ...). Not validated here -- an Action
    # describes its inputs; checking a real call's values against them
    # is the call gate's job (REQ-SB-95-US-03).
    type: str = "string"
    # Required means "ask rather than guess" at call time (ADR-032), so
    # it has to survive a round-trip exactly as saved -- the default is
    # the permissive one, never a silently-required input.
    required: bool = False
    description: str = ""


@dataclass
class ActionImplementation:
    """The one thing this Action runs. `kind` says which of the three
    shapes below is populated; the other two stay empty.

    Field shapes are fixed by ADR-033: a `skill` names the DEPLOYED
    Skill by the same bare slug SkillManager.deploy(skill_id, profile_id)
    itself takes, an `http` names a route on this app's own route table,
    and a `ui` names a registered front-end feature key -- the one kind
    the app points at and never performs.
    """
    kind: str
    skill_id: str = ""
    method: str = ""
    path: str = ""
    feature_key: str = ""


@dataclass
class Action:
    """One invocable operation this app can perform (ADR-032's sixth
    artifact kind). Instance data: it lives in the App Database Folder
    at data/Actions/<id>/Action.json, never in the repository."""
    id: str
    description: str = ""
    inputs: list[ActionInput] = field(default_factory=list)
    # Which agents may call it -- a list of agent ids, which ARE Hermes
    # profile ids everywhere in this codebase, or the single wildcard
    # entry ["*"] (ADR-033). Empty means nobody, and that is a real,
    # saveable state: a catalogued Action nothing may call yet.
    allowed_callers: list[str] = field(default_factory=list)
    # Stored here, honoured at the call by US-03's own Action-call
    # ledger (ADR-033). This story stores the flag and nothing more.
    needs_confirmation: bool = False
    implementation: ActionImplementation | None = None
    created_at: str = ""
    updated_at: str | None = None
