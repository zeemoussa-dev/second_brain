"""Sections CRUD (2026-08-22, operator-directed: "Sections Part has
Nothing to do with Hermes So You can Restore it") -- restored from
app/_archive/api/sections_router.py. Genuinely independent of the
Hermes-mirror work (ADR-003): a Section is Second Brain's own real,
user-mutable grouping concept (ADR-014), never data Hermes owns or
reports. PATCH extended 2026-08-23 (operator: "the Hub can be
clicked and has its own Settings... Section Color and Icon, Description
and Name") from a name-only rename into a general update covering all
four fields."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import section_registry
from app.business.hermes import agents_map_adapter

router = APIRouter(prefix="/sections")


class SectionCreateBody(BaseModel):
    name: str


class SectionUpdateBody(BaseModel):
    # Each field: omitted (key absent from the JSON body, the default
    # None) = leave unchanged; for icon/color/subtitle, "" (explicit
    # empty string) = clear the value back to unset. Mirrors
    # AgentVisualUpdateBody's own convention (agents_router.py). `folders`
    # is a list, not a string -- omitted (None) = leave unchanged, any
    # real list (including []) replaces it wholesale, no empty-string
    # sentinel needed.
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    subtitle: str | None = None
    description: str | None = None
    folders: list[str] | None = None
    fallback_agent_id: str | None = None


def _blocked_delete_message(name: str, blocked_by_agent_ids: list[str]) -> str:
    # `agent_registry` (the now-fully-retired pre-Hermes agent model) is
    # deliberately NOT used here -- it's empty and knows nothing about a
    # real Hermes agent id, which `delete_section`'s own blocking check
    # now also detects (REQ-SB-80). Resolved via the SAME adapter the
    # rest of the app uses for a real agent's friendly display name;
    # falls back to the bare id in the genuinely-impossible case a
    # blocking id resolves to neither a Pipeline nor a real Hermes agent.
    names = [
        (agents_map_adapter.get_agent_detail(aid) or {}).get("name", aid)
        for aid in blocked_by_agent_ids
    ]
    count = len(names)
    joined = ", ".join(names)
    return (
        f'Can\'t delete "{name}" — {count} agent{"s" if count != 1 else ""} '
        f'({joined}) {"are" if count != 1 else "is"} still assigned to this '
        "section. Move them to a different section first, then try again."
    )


@router.get("")
def list_sections() -> list[dict]:
    return section_registry.list_sections()


@router.post("")
def create_section(body: SectionCreateBody) -> dict:
    section = section_registry.create_section(body.name)
    return {**section, "agent_ids": []}


@router.patch("/{section_id}")
def update_section(section_id: str, body: SectionUpdateBody) -> dict:
    section = section_registry.update_section(
        section_id, name=body.name, icon=body.icon, color=body.color,
        subtitle=body.subtitle, description=body.description, folders=body.folders,
        fallback_agent_id=body.fallback_agent_id,
    )
    if section is None:
        raise HTTPException(status_code=404, detail="Unknown section")
    return section


@router.delete("/{section_id}")
def delete_section(section_id: str) -> dict:
    sections_by_id = {s["id"]: s for s in section_registry.list_sections()}
    section = sections_by_id.get(section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Unknown section")
    result = section_registry.delete_section(section_id)
    if not result["deleted"]:
        raise HTTPException(
            status_code=409,
            detail=_blocked_delete_message(section["name"], result["blocked_by_agent_ids"]),
        )
    return {"deleted": True}
