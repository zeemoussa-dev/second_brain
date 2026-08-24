"""Known-agent registry: a static, in-code seed set (_SEED_AGENTS,
ADR-011 points 1/3/4) merged at read time with a persisted
.second-brain/agents_registry.json overlay for runtime-created agents
(ADR-030, supersedes ADR-011 point 2 only).

Emptied 2026-08-22 (operator-directed, "we're fully on Hermes now") --
every Second-Brain-native Agent this registry used to seed/hold is
retired; Hermes is the real agent/skill/schedule runtime going forward
(ADR-001), mirrored read-only by app/data_access/hermes_definitions.py
(ADR-003). This module is left in place (rather than deleted) because
section_registry.py/skill_registry.py/agents_router.py's own archived
copy still import it; it now always returns an empty agent list, real
and honest, not a stale one.
"""
from app.data_access import vault_writer

_SEED_AGENTS: dict[str, dict] = {}


def _load_state() -> dict:
    state = vault_writer.load_agents_registry_state()
    if state is None:
        state = {"created_agents": {}}
        vault_writer.save_agents_registry_state(state)
    return state


def get_agent(agent_id: str) -> dict | None:
    if agent_id in _SEED_AGENTS:
        return _SEED_AGENTS[agent_id]
    return _load_state()["created_agents"].get(agent_id)


def list_agents(include_retired: bool = False) -> list[dict]:
    state = _load_state()
    seed_entries = [
        {"id": agent_id, "name": agent["name"], "type": agent["type"], "depends_on": agent.get("depends_on", [])}
        for agent_id, agent in _SEED_AGENTS.items()
    ]
    created_entries = [
        {"id": agent_id, "name": agent["name"], "type": agent["type"], "depends_on": agent.get("depends_on", [])}
        for agent_id, agent in state["created_agents"].items()
        if include_retired or not agent.get("retired", False)
    ]
    return seed_entries + created_entries


def get_action(agent_id: str, action_id: str) -> dict | None:
    """Resolves one action's own definition dict (including its
    "mutates" classification) by agent_id + action_id — the one place
    app/api/agents_router.py's working-mode gate (ADR-020 point 2)
    reads an action's own read-only-vs-mutating nature, so the nested-
    list search isn't duplicated inline at every call site."""
    agent = get_agent(agent_id)
    if agent is None:
        return None
    return next((a for a in agent["actions"] if a["id"] == action_id), None)


def create_agent(
    name: str, type: str, settings: list[dict] | None = None, depends_on: list[str] | None = None,
) -> dict:
    """agent_id is derived via vault_writer.tag_slug(name), keeping
    every agent-identifying id in this codebase human-readable and
    consistent (email-capture-pipeline, compass-expert, widgets-expert), not a
    UUID/integer. Unlike create_section's idempotent-collapse-on-
    collision semantic, disambiguates on collision (-2, -3, ...)
    against the union of _SEED_AGENTS and created_agents keys — two
    distinct agent-creation calls must never silently collide into
    one shared identity, and a created agent's slug must never be
    allowed to shadow a shipped agent's id. actions: [] mirrors the
    already-Done vault-filing-expert/compass-expert "starts with zero
    pre-seeded actions" precedent — REQ-SB-39's Skills unification
    remains the only path to a created agent gaining a capability,
    via the already-Done skill_registry.grant_skill_access.

    depends_on (2026-08-20) -- ids of Agents this one structurally
    receives from (a real pipeline predecessor), the first real source
    for AgentSummary.depends_on (agents_router.py's list_agents no
    longer hardcodes `[]` for every agent). Each id is validated to
    already be a real, known agent (seed or created) before this call
    succeeds -- never a dangling reference a future Job Tree render
    would silently fail to resolve."""
    state = _load_state()
    known_ids = set(_SEED_AGENTS.keys()) | set(state["created_agents"].keys())
    for dep_id in depends_on or []:
        if dep_id not in known_ids:
            raise ValueError(f"Unknown depends_on agent id: {dep_id}")
    base_id = vault_writer.tag_slug(name)
    agent_id = base_id
    suffix = 2
    while agent_id in known_ids:
        agent_id = f"{base_id}-{suffix}"
        suffix += 1
    record = {
        "name": name, "type": type, "settings": settings or [], "actions": [],
        "retired": False, "depends_on": depends_on or [],
    }
    state["created_agents"][agent_id] = record
    vault_writer.save_agents_registry_state(state)
    return {"id": agent_id, **record}


def retire_agent(agent_id: str) -> bool:
    """The first "retire without delete" primitive (REQ-SB-79-US-01,
    ADR-058 Decision 2) -- marks a CREATED agent's own record retired so
    list_agents() stops surfacing it by default, while get_agent() keeps
    resolving it forever so every already-existing Pending Approval/Agent
    History record attributed to it keeps a real, honest agent_name.
    Idempotent -- retiring an already-retired agent is a safe no-op,
    still returning True (needed for an "every app start" bootstrap
    call). _SEED_AGENTS entries (shipped, static agents) can never be
    retired -- returns False, never mutates _SEED_AGENTS."""
    if agent_id in _SEED_AGENTS:
        return False
    state = _load_state()
    record = state["created_agents"].get(agent_id)
    if record is None:
        return False
    record["retired"] = True
    vault_writer.save_agents_registry_state(state)
    return True
