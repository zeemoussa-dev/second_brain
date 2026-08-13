"""Sections: a new, persisted, user-mutable concern (ADR-014) — which
Section an agent belongs to, independent of its Worker/Producer/Expert
Type. Composed alongside app/business/agent_registry.py, not inside it —
agent_registry.py itself is not modified (ADR-011 point 2's "agent
identity/type/actions stay hardcoded" reasoning is untouched).
"""
from app.business import agent_registry
from app.data_access import vault_writer

_STARTING_SECTION_NAMES = ["Technical", "Sales", "Productivity", "Customers", "Products"]


def _seed_state() -> dict:
    sections = [{"id": vault_writer.tag_slug(name), "name": name} for name in _STARTING_SECTION_NAMES]
    state = {"sections": sections, "assignments": {}}
    vault_writer.save_sections_state(state)
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
        {"id": s["id"], "name": s["name"], "agent_ids": agent_ids_by_section.get(s["id"], [])}
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
    section = {"id": section_id, "name": name}
    state["sections"].append(section)
    vault_writer.save_sections_state(state)
    return section


def rename_section(section_id: str, name: str) -> dict | None:
    """Updates name in place only — section_id (the slug) is fixed at
    creation and never regenerated on rename (ADR-014 point 1), which is
    what makes every existing assignments entry stay correct
    automatically."""
    state = _load_state()
    for section in state["sections"]:
        if section["id"] == section_id:
            section["name"] = name
            vault_writer.save_sections_state(state)
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
