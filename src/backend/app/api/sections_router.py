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

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.sections.section import Section
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes import agents_map_adapter

router = APIRouter(prefix="/sections")
_section_manager = SectionManager()
_agent_manager = AgentManager()


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


def _agent_ids_by_section() -> dict[str, list[str]]:
    """Real cross-manager composition (operator: "cross managers work is
    the business logic") -- SectionManager itself never reaches into
    Agent data (the ownership split), so this lives here, at the
    caller. Fixes GET /sections' own long-standing `agent_ids: []`
    bug: the field existed, but nothing ever filled it in from the
    real, live Registry-backed section_id AgentManager already
    resolves for every agent."""
    by_section: dict[str, list[str]] = {}
    for agent in _agent_manager.get_all():
        by_section.setdefault(agent.section_id, []).append(agent.id)
    return by_section


@router.get("")
def list_sections() -> list[Section]:
    agent_ids_by_section = _agent_ids_by_section()
    sections = _section_manager.get_all()
    for section in sections:
        section.agent_ids = agent_ids_by_section.get(section.id, [])
    return sections


@router.post("")
def create_section(body: SectionCreateBody) -> Section:
    return _section_manager.create(body.name)


@router.patch("/{section_id}")
def update_section(section_id: str, body: SectionUpdateBody) -> Section:
    section = _section_manager.update(
        section_id, name=body.name, icon=body.icon, color=body.color,
        subtitle=body.subtitle, description=body.description, folders=body.folders,
        fallback_agent_id=body.fallback_agent_id,
    )
    if section is None:
        raise HTTPException(status_code=404, detail="Unknown section")
    return section


@router.delete("/{section_id}")
def delete_section(section_id: str) -> dict:
    section = _section_manager.get_by_id(section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Unknown section")
    # AgentManager's own picture is fuller than SectionManager.delete()'s
    # internal Registry-only check -- it also resolves an agent not yet
    # migrated into the data/ tree (falls through to its real default
    # Section rather than being invisible to a Registry-only scan).
    # Checked here, at the cross-manager caller, not inside SectionManager
    # itself. SectionManager.delete()'s own Registry check still runs
    # underneath as a real, independent safety net either way.
    blocked_by_agent_ids = _agent_ids_by_section().get(section_id, [])
    if blocked_by_agent_ids:
        raise HTTPException(
            status_code=409,
            detail=_blocked_delete_message(section.name, blocked_by_agent_ids),
        )
    result = _section_manager.delete(section_id)
    if not result["deleted"]:
        raise HTTPException(
            status_code=409,
            detail=_blocked_delete_message(section.name, result["blocked_by_agent_ids"]),
        )
    return {"deleted": True}
