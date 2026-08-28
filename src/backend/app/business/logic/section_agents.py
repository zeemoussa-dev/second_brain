"""Real cross-manager composition between Sections and Agents (operator:
"cross managers work is the business logic") -- SectionManager itself
never reaches into Agent data (the ownership split), so this lives here,
not inside either Manager, and not inside sections_router.py (2026-08-28,
API layer holds no business logic).
"""
from __future__ import annotations

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.sections.section import Section
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes import agents_map_adapter

_section_manager = SectionManager()
_agent_manager = AgentManager()


class SectionNotFoundError(Exception):
    pass


class SectionBlockedError(Exception):
    """A Section can't be deleted while real agents are still assigned
    to it. Carries the ready-to-display message, not just the raw
    blocking ids -- building it needs the SAME agent-name resolution
    this module already owns."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def agent_ids_by_section() -> dict[str, list[str]]:
    """Fixes `Section.agent_ids`'s own long-standing `[]` bug: the field
    existed, but nothing ever filled it in from the real, live
    Registry-backed section_id AgentManager already resolves for every
    agent."""
    by_section: dict[str, list[str]] = {}
    for agent in _agent_manager.get_all():
        by_section.setdefault(agent.section_id, []).append(agent.id)
    return by_section


def list_sections_with_agent_ids() -> list[Section]:
    ids_by_section = agent_ids_by_section()
    sections = _section_manager.get_all()
    for section in sections:
        section.agent_ids = ids_by_section.get(section.id, [])
    return sections


def _blocked_delete_message(name: str, blocked_by_agent_ids: list[str]) -> str:
    # `agent_registry` (the now-fully-retired pre-Hermes agent model) is
    # deliberately NOT used here -- it's empty and knows nothing about a
    # real Hermes agent id, which this module's own blocking check now
    # also detects (REQ-SB-80). Resolved via the SAME adapter the rest
    # of the app uses for a real agent's friendly display name; falls
    # back to the bare id in the genuinely-impossible case a blocking id
    # resolves to neither a Pipeline nor a real Hermes agent.
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


def delete_section(section_id: str) -> dict:
    """{"deleted": True}, or raises SectionNotFoundError /
    SectionBlockedError. AgentManager's own picture is fuller than
    SectionManager.delete()'s internal Registry-only check -- it also
    resolves an agent not yet migrated into the data/ tree (falls
    through to its real default Section rather than being invisible to
    a Registry-only scan). Checked here, at the cross-manager caller,
    not inside SectionManager itself. SectionManager.delete()'s own
    Registry check still runs underneath as a real, independent safety
    net either way."""
    section = _section_manager.get_by_id(section_id)
    if section is None:
        raise SectionNotFoundError(section_id)
    blocked_by_agent_ids = agent_ids_by_section().get(section_id, [])
    if blocked_by_agent_ids:
        raise SectionBlockedError(_blocked_delete_message(section.name, blocked_by_agent_ids))
    result = _section_manager.delete(section_id)
    if not result["deleted"]:
        raise SectionBlockedError(
            _blocked_delete_message(section.name, result["blocked_by_agent_ids"])
        )
    return {"deleted": True}
