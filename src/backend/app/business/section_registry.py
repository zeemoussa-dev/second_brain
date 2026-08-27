"""Sections: a new, persisted, user-mutable concern (ADR-014) — which
Section an agent belongs to, independent of its Worker/Producer/Expert
Type. Composed alongside app/business/agent_registry.py, not inside it —
agent_registry.py itself is not modified (ADR-011 point 2's "agent
identity/type/actions stay hardcoded" reasoning is untouched).
"""
import json

from app.business import agent_registry
from app.data_access import vault_writer
from app.data_access.registry import loader as registry_loader

# 2026-08-22 (operator's own real taxonomy, verbatim): "Our Sections will
# be (Customer, Liberian, Industry, Technology, Data Gatherer, Sales)" --
# replaces the earlier placeholder starting-5 set. "Data Gatherer" is
# where the real Hermes-mirrored agents (ADR-003) are shown on the map;
# the rest start empty, real groupings for agents not built yet, not
# placeholders to be renamed later.
_STARTING_SECTION_NAMES = ["Customer", "Librarian", "Industry", "Technology", "Data Gatherer", "Sales"]


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
    narrowly to the one place a stale Registry copy was a real, live risk."""
    path = registry_loader.data_root() / "Sections" / section["id"] / "Section.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "id": section["id"],
                "name": section["name"],
                "icon": section.get("icon"),
                "color": section.get("color"),
                "subtitle": section.get("subtitle"),
                "description": section.get("description"),
                "folders": section.get("folders", []),
                "fallback_agent_id": section.get("fallback_agent_id"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _seed_state() -> dict:
    sections = [
        {
            "id": vault_writer.tag_slug(name), "name": name,
            "icon": None, "color": None, "subtitle": None, "description": None,
            "folders": [], "fallback_agent_id": None,
        }
        for name in _STARTING_SECTION_NAMES
    ]
    state = {"sections": sections, "assignments": {}}
    vault_writer.save_sections_state(state)
    for section in sections:
        _write_registry_section_json(section)
    return state


def _load_state() -> dict:
    """Seeds the starting 5 sections on first read (persisting
    immediately), then self-heals: any known agent
    (agent_registry.list_agents()) absent from assignments — true for
    every agent on first seed, and for any agent a future story adds
    without a migration step — is assigned to the first section in
    creation order and persisted (ADR-014 point 1)."""
    state = vault_writer.load_sections_state()
    if state is None:
        state = _seed_state()
    if not state["sections"]:
        return state
    default_section_id = state["sections"][0]["id"]
    changed = False
    for agent in agent_registry.list_agents():
        if agent["id"] not in state["assignments"]:
            state["assignments"][agent["id"]] = default_section_id
            changed = True
    if changed:
        vault_writer.save_sections_state(state)
    return state


def list_sections() -> list[dict]:
    state = _load_state()
    agent_ids_by_section: dict[str, list[str]] = {}
    for agent_id, section_id in state["assignments"].items():
        agent_ids_by_section.setdefault(section_id, []).append(agent_id)
    return [
        {
            "id": s["id"], "name": s["name"],
            "icon": s.get("icon"), "color": s.get("color"), "subtitle": s.get("subtitle"),
            "description": s.get("description"),
            "folders": s.get("folders", []),
            "fallback_agent_id": s.get("fallback_agent_id"),
            "agent_ids": agent_ids_by_section.get(s["id"], []),
        }
        for s in state["sections"]
    ]


def create_section(name: str) -> dict:
    state = _load_state()
    section_id = vault_writer.tag_slug(name)
    existing = next((s for s in state["sections"] if s["id"] == section_id), None)
    if existing is not None:
        # Same normalized name already exists — return it rather than
        # duplicating (tag_slug collisions collapse to the same section).
        return existing
    section = {
        "id": section_id, "name": name,
        "icon": None, "color": None, "subtitle": None, "description": None,
        "folders": [], "fallback_agent_id": None,
    }
    state["sections"].append(section)
    vault_writer.save_sections_state(state)
    _write_registry_section_json(section)
    return section


def update_section(
    section_id: str,
    *,
    name: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    subtitle: str | None = None,
    description: str | None = None,
    folders: list[str] | None = None,
    fallback_agent_id: str | None = None,
) -> dict | None:
    """General Section update (2026-08-23, operator: "the Hub can be
    clicked and has its own Settings... Section Color and Icon,
    Description and Name") — replaces the earlier name-only
    `rename_section`. `section_id` (the slug) is fixed at creation and
    never regenerated here (ADR-014 point 1), which is what keeps every
    existing assignments entry correct automatically across a rename.
    `description` is the real field layoutAgents.ts's own SectionSummary
    interface has been typing since 2026-08-15 ("The Description will be
    used later") without any backend field ever actually backing it —
    this is that "later". Each of icon/color/subtitle/description follows
    the same omitted-vs-empty-string convention as
    agent_visual_registry.py: the router only ever passes a field here
    when the caller actually sent it, so `None` always means "leave
    unchanged" and `""` always means "clear back to unset" — never
    ambiguous at this layer. `folders` (2026-08-27, Phase 4 of
    Implementation/Plans/2026-08-27-vault-index-and-section-agents.md)
    is a list, not a string, so it needs no such sentinel: `None` means
    "leave unchanged", any actual list (including `[]`) REPLACES the
    section's own folder scope wholesale — a Section can legitimately own
    zero, one, or several top-level Work/ folders (operator: "if a
    section need more than one folder we give both indexes to the
    Expert of Hub"). `fallback_agent_id` (2026-08-27, Phase 5) is back to
    the string omitted/""-clears convention -- the real Hermes profile
    (id == its profile folder name, chat_sessions.py's own convention)
    that answers on this Section's behalf when a mentioned entity in its
    scope has no dedicated Expert registered (operator: "Fallback-only").
    `None` when never configured -- moderator.match_customer_fallback_agent
    then correctly finds nothing rather than fabricating a fallback."""
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
            vault_writer.save_sections_state(state)
            _write_registry_section_json(section)
            return section
    return None


def delete_section(section_id: str) -> dict:
    """Never raises for ordinary control flow — returns a result dict
    (ADR-014 point 4), mirroring the existing _invoke_action/
    trigger_action result-dict convention. The router (T03) translates a
    blocked deletion into HTTP 409."""
    state = _load_state()
    blocked_by_agent_ids = [
        agent_id for agent_id, sid in state["assignments"].items() if sid == section_id
    ]
    # `assignments` above only ever tracked the now-fully-retired
    # pre-Hermes agent model (agent_registry.py's own 2026-08-22
    # emptying) -- it was NEVER populated for real Hermes agents, so this
    # check alone would silently let a Section with real migrated agents
    # in it (REQ-SB-80's data/ tree) be deleted out from under them.
    # Cross-check the RegistryLoader's own real, live placements too.
    registry = registry_loader.get_registry()
    if registry is not None:
        for agent_id, agent in registry.agents.items():
            if agent.section_id == section_id and agent_id not in blocked_by_agent_ids:
                blocked_by_agent_ids.append(agent_id)
    if blocked_by_agent_ids:
        return {"deleted": False, "blocked_by_agent_ids": blocked_by_agent_ids}
    state["sections"] = [s for s in state["sections"] if s["id"] != section_id]
    vault_writer.save_sections_state(state)
    return {"deleted": True, "blocked_by_agent_ids": []}


def get_agent_section(agent_id: str) -> dict | None:
    state = _load_state()
    section_id = state["assignments"].get(agent_id)
    if section_id is None:
        return None
    return next((s for s in state["sections"] if s["id"] == section_id), None)


def set_agent_section(agent_id: str, section_id: str) -> bool:
    state = _load_state()
    if not any(s["id"] == section_id for s in state["sections"]):
        return False
    state["assignments"][agent_id] = section_id
    vault_writer.save_sections_state(state)
    return True
