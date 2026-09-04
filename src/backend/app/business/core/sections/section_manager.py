"""SectionManager -- the ONLY door onto Section data (ADR-014). Every
caller anywhere in the app that needs a Section reads or writes it
through here, never through a separate registry module (mirrors the
existing "all Hermes calls go through app/business/hermes/client.py"
boundary, same reasoning: one real gateway, not several equally-valid
ways in). Owns the real persisted CRUD itself now -- section_registry.py
was folded in here and deleted, not kept as a second layer underneath.

Does NOT route through vault_writer.py -- vault_writer.py is a
retirement target (operator: "our job is to retire vault_writer as well
its there because its everywhere"), so a new Manager adding itself as
one more caller of it would work against that goal, not toward it.
registry_loader stays the real live Registry this cross-checks against
for delete-safety -- that's RegistryLoader's own concern, unrelated to
vault_writer.

Raw I/O (2026-08-28 layering correction, operator: "Managers understand
Entities, Data Access understands stores... I/O always happens in Data
Access") lives in `data_access/sections.py` (this Manager's own
`agent_sections.json` state) and `data_access/registry/writer.py` (the
Section.json push-mirror, shared with AgentManager since both write into
the same Registry tree) -- this file holds zero raw file calls, only
entity-shaping, seeding, and the delete-blocking check.
"""
from __future__ import annotations

from app.business.core.sections.section import Section
from app.data_access import sections as sections_data
from app.data_access.registry import loader as registry_loader
from app.data_access.registry import writer as registry_writer
from app.obsidian.tags import tag_slug

# A fresh install starts with NO Sections (operator, 2026-09-04: "Delete all
# Sections now and Remove anything that Generates them, This is a Clean
# Build"). The previous starting six (Customer, Librarian, Industry,
# Technology, Data Gatherer, Sales) were seeded here on first read, which
# meant a clean machine came up already populated with groupings nobody on
# that machine had chosen. Sections are now created only by an explicit
# human action.


def _write_registry_section_json(section: dict) -> None:
    """Keeps the RegistryLoader's own `data/Sections/<id>/Section.json`
    (REQ-SB-80) in sync with this store's own `name`/`icon`/`color`/
    `subtitle`/`description`/`folders` -- without this, a rename/recolor
    through Settings would go stale in the Registry (and therefore the
    Agents Map, which resolves a migrated agent's section NAME via the
    Registry now, not this file) until someone re-ran the one-off
    migration script by hand. `folders` (2026-08-27, Phase 4 of
    Implementation/Plans/2026-08-27-vault-index-and-section-agents.md)
    is this same disk mirror's real purpose for a future Section
    fallback agent -- a standalone Hermes-side agent has no way to call
    this backend's own API, so it reads its own folder scope from this
    exact file instead, same "read config directly off disk" pattern
    already established by Index Filtering and build_vault_index.py.
    RegistryLoader's own hot-reload poll (~2s) picks this write up
    automatically -- no other plumbing needed. This store's own
    `.second-brain/agent_sections.json` stays the actual CRUD source of
    truth (id/creation/agent-assignment-for-the-old-model); this is a
    one-way push of its own metadata subset, mirroring the "Second Brain
    pushes to targets it owns" shape REQ-SB-80 established, scoped
    narrowly to the one place a stale Registry copy was a real, live
    risk. The actual write is registry_writer.write_section_json --
    this function's own job is deciding WHICH fields go into it."""
    registry_writer.write_section_json(section["id"], {
        "id": section["id"],
        "name": section["name"],
        "icon": section.get("icon"),
        "color": section.get("color"),
        "subtitle": section.get("subtitle"),
        "description": section.get("description"),
        "folders": section.get("folders", []),
        "fallback_agent_id": section.get("fallback_agent_id"),
    })


def _seed_state() -> dict:
    """Persists an EMPTY Section store on first read.

    Still writes the file rather than returning a transient empty dict, so
    "no Sections yet" is a real persisted state and every later read takes
    the normal load path instead of re-entering this one.
    """
    state: dict = {"sections": []}
    sections_data.save_state(state)
    return state


def _load_state() -> dict:
    """Creates an empty Section store on first read (persisting
    immediately). Sections only ever come from an explicit human
    action."""
    state = sections_data.load_state()
    return state if state is not None else _seed_state()


class SectionManager:
    def get_all(self) -> list[Section]:
        """`agent_ids` always comes back `[]` here -- which agents belong
        to a Section is AgentManager's own concern now (the Agent/Section
        ownership split), never something this Manager computes itself.
        A real, filled-in `agent_ids` is cross-manager business logic,
        composed at the caller (sections_router.py's own list_sections),
        not reached into from in here."""
        state = _load_state()
        return [
            Section(
                id=s["id"], name=s["name"],
                icon=s.get("icon"), color=s.get("color"), subtitle=s.get("subtitle"),
                description=s.get("description"),
                folders=s.get("folders", []),
                fallback_agent_id=s.get("fallback_agent_id"),
                agent_ids=[],
            )
            for s in state["sections"]
        ]

    def get_by_id(self, section_id: str) -> Section | None:
        return next((s for s in self.get_all() if s.id == section_id), None)

    def create(self, name: str) -> Section:
        """A new Section is not complete until its own Hub Agent exists
        too (operator: "create section is not complete till we finish
        the agent as well") -- SectionManager asks AgentManager to
        create it, gets back its real id, and links it back as this
        Section's own `fallback_agent_id`. A genuine Manager-to-Manager
        call, a deliberate exception to the "compose at the caller"
        rule get_all's own agent_ids uses -- hub creation is an
        intrinsic part of what creating a Section MEANS, not an
        aggregate query across many agents. Imported lazily inside this
        method, not at module level: AgentManager already imports
        SectionManager at import time (to resolve a not-yet-migrated
        agent's own fallback section), so a module-level import here
        would be a real circular import."""
        state = _load_state()
        section_id = tag_slug(name)
        existing = next((s for s in state["sections"] if s["id"] == section_id), None)
        if existing is None:
            # Same normalized name already exists — return it rather than
            # duplicating (tag_slug collisions collapse to the same section).
            section = {
                "id": section_id, "name": name,
                "icon": None, "color": None, "subtitle": None, "description": None,
                "folders": [], "fallback_agent_id": None,
            }
            state["sections"].append(section)
            sections_data.save_state(state)
            _write_registry_section_json(section)

            from app.business.core.agents.agent_manager import AgentManager
            hub_id = f"{section_id}-hub"
            AgentManager().create(
                hub_id, name=f"{name} Hub", section_id=section_id, type="hub",
                description=f"Entry point for the {name} section.",
                prompt=f"You are the {name} Hub -- the entry point for the {name} section's own specialists.",
            )
            return self.update(section_id, fallback_agent_id=hub_id)
        return self.get_by_id(section_id)

    def update(
        self,
        section_id: str,
        *,
        name: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        subtitle: str | None = None,
        description: str | None = None,
        folders: list[str] | None = None,
        fallback_agent_id: str | None = None,
    ) -> Section | None:
        """`description` is the real field layoutAgents.ts's own
        SectionSummary interface has been typing since 2026-08-15 ("The
        Description will be used later") without any backend field ever
        actually backing it until this. Each of icon/color/subtitle/
        description follows the same omitted-vs-empty-string convention as
        agent_visual_registry.py: `None` always means "leave unchanged"
        and `""` always means "clear back to unset" -- never ambiguous at
        this layer. `folders` is a list, not a string, so it needs no such
        sentinel: `None` means "leave unchanged", any actual list
        (including `[]`) REPLACES the section's own folder scope wholesale
        -- a Section can legitimately own zero, one, or several top-level
        Work/ folders (operator: "if a section need more than one folder
        we give both indexes to the Expert of Hub"). `fallback_agent_id`
        is back to the string omitted/""-clears convention -- the real
        Hermes profile (id == its profile folder name, chat_sessions.py's
        own convention) that answers on this Section's behalf when a
        mentioned entity in its scope has no dedicated Expert registered
        (operator: "Fallback-only"). `None` when never configured --
        moderator.match_customer_fallback_agent then correctly finds
        nothing rather than fabricating a fallback."""
        state = _load_state()
        for section in state["sections"]:
            if section["id"] == section_id:
                if name is not None:
                    section["name"] = name
                if icon is not None:
                    section["icon"] = icon or None
                if color is not None:
                    section["color"] = color or None
                if subtitle is not None:
                    section["subtitle"] = subtitle or None
                if description is not None:
                    section["description"] = description or None
                if folders is not None:
                    section["folders"] = folders
                if fallback_agent_id is not None:
                    section["fallback_agent_id"] = fallback_agent_id or None
                sections_data.save_state(state)
                _write_registry_section_json(section)
                return self.get_by_id(section_id)
        return None

    def delete(self, section_id: str) -> dict:
        """Never raises for ordinary control flow — returns a result dict
        (ADR-014 point 4), mirroring the existing _invoke_action/
        trigger_action result-dict convention. The router translates a
        blocked deletion into HTTP 409.

        Blocking check reads the Registry directly (structural data this
        Manager already legitimately touches for its own Section.json
        push-mirror, NOT a reach into AgentManager) -- catches every
        agent already migrated into the data/ tree, but misses one still
        only resolved through AgentManager's own not-yet-migrated
        fallback. sections_router.py's own delete handler layers
        AgentManager's fuller picture on top of this before calling
        delete, same cross-manager-composition-at-the-caller shape
        get_all's own agent_ids uses."""
        state = _load_state()
        blocked_by_agent_ids: list[str] = []
        registry = registry_loader.get_registry()
        if registry is not None:
            for agent_id, agent in registry.agents.items():
                if agent.section_id == section_id and agent_id not in blocked_by_agent_ids:
                    blocked_by_agent_ids.append(agent_id)
        if blocked_by_agent_ids:
            return {"deleted": False, "blocked_by_agent_ids": blocked_by_agent_ids}
        state["sections"] = [s for s in state["sections"] if s["id"] != section_id]
        sections_data.save_state(state)
        return {"deleted": True, "blocked_by_agent_ids": []}
