"""Blueprints HTTP surface — the Settings > Blueprints card.

A Blueprint is a RECIPE for a Section: its identity, the Agents in it, and
which Skills each Agent should have. Pull one onto a fresh install and that
Section comes up running.

Three endpoints, and the split matters: `preflight` never creates anything,
so the UI can show exactly what would happen — and what would stop it —
before the operator commits. `install` re-runs preflight itself and refuses
on failure; it does not trust a preview the client may be holding from
before someone changed the install underneath it.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business.core.blueprints.blueprint import Blueprint
from app.business.core.blueprints.blueprint_manager import BlueprintManager

router = APIRouter(prefix="/blueprints")
_manager = BlueprintManager()


@router.get("")
def list_blueprints() -> list[Blueprint]:
    """Every shipped Blueprint. A malformed one is listed carrying `error`
    rather than dropped — a broken Blueprint the operator cannot see is worse
    than one that fails loudly."""
    return _manager.get_all()


@router.get("/{blueprint_id}/preflight")
def preflight(blueprint_id: str, section_id: str | None = None) -> dict:
    """What would happen, and what would stop it. Creates nothing.

    404 only when the id is unknown; an id that exists but cannot be
    installed is a 200 carrying `ok: false` and its `problems` — that is a
    real answer about a real Blueprint, not a missing resource.
    """
    result = _manager.preflight(blueprint_id, section_id)
    if _manager.get_by_id(blueprint_id) is None:
        raise HTTPException(status_code=404, detail=f"no Blueprint {blueprint_id!r}")
    return result


@router.post("/{blueprint_id}/install")
def install(blueprint_id: str, section_id: str | None = None, wire_peers: bool = True) -> dict:
    """Installs the Section, its Agents and their Skills.

    Refuses with 409 when preconditions fail, and creates NOTHING in that
    case — a refusal never leaves a half-built Section behind. `wire_peers`
    appends each peer Agent's routing snippet to this machine's Primary
    SOUL.md, which is what makes Primary relay to it at all; without it the
    Agent exists, runs, and is never reached.

    `section_id` chooses which Section the Agents join. Omitted, the
    Blueprint's own suggestion is used -- a suggestion, never an imposition,
    so an operator with existing Sections is not forced into a new one.
    """
    if _manager.get_by_id(blueprint_id) is None:
        raise HTTPException(status_code=404, detail=f"no Blueprint {blueprint_id!r}")
    result = _manager.install(blueprint_id, section_id=section_id, wire_peers=wire_peers)
    if not result["installed"]:
        raise HTTPException(status_code=409, detail=result)
    return result
