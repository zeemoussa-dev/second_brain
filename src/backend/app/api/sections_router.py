"""Sections CRUD (2026-08-22, operator-directed: "Sections Part has
Nothing to do with Hermes So You can Restore it") -- restored from
app/_archive/api/sections_router.py. Genuinely independent of the
Hermes-mirror work (ADR-003): a Section is Second Brain's own real,
user-mutable grouping concept (ADR-014), never data Hermes owns or
reports. PATCH extended 2026-08-23 (operator: "the Hub can be
clicked and has its own Settings... Section Color and Icon, Description
and Name") from a name-only rename into a general update covering all
four fields. The real cross-manager composition (Section<->Agent) and
delete-blocking rule live in business/logic/section_agents.py, not here
(2026-08-28, API layer holds no business logic)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business.core.sections.section import Section
from app.business.core.sections.section_manager import SectionManager
from app.business.logic import section_agents

router = APIRouter(prefix="/sections")
_section_manager = SectionManager()


class SectionCreateBody(BaseModel):
    name: str


class SectionUpdateBody(BaseModel):
    # Each field: omitted (key absent from the JSON body, the default
    # None) = leave unchanged; for icon/color/subtitle, "" (explicit
    # empty string) = clear the value back to unset. Mirrors
    # AgentUpdateBody's own convention (agents_router.py). `folders`
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


@router.get("")
def list_sections() -> list[Section]:
    return section_agents.list_sections_with_agent_ids()


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
    try:
        return section_agents.delete_section(section_id)
    except section_agents.SectionNotFoundError:
        raise HTTPException(status_code=404, detail="Unknown section")
    except section_agents.SectionBlockedError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
