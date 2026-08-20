"""Background Agent: a new, persisted, user-mutable per-agent concern
(REQ-SB-51-US-01) — excludes an agent from every other agent's Hub-routing
candidacy and the Cockpit's Available Agents bring-in list, while leaving
its own detail panel/direct chat/direct actions/scheduled runs untouched.
Composed alongside app/business/agent_registry.py, not inside it —
agent_registry.py is not modified (ADR-011 point 2's "agent identity/
type/actions stay hardcoded" reasoning untouched a further time over).
Mirrors working_mode_registry.py's exact shape (self-healing default
folded into _load_state(), no separate _seed_state()); the only deviation
is the default itself is not uniform — the 3 real capture-pipeline
Workers self-heal to True, every other known agent self-heals to False.
"""
from app.business import agent_registry
from app.data_access import vault_writer

_DEFAULT_BACKGROUND_AGENT_IDS = {"email-capture-pipeline", "meeting-capture", "todo-capture"}


def _load_state() -> dict:
    state = vault_writer.load_background_agent_flags_state()
    if state is None:
        state = {"assignments": {}}
    changed = False
    for agent in agent_registry.list_agents():
        if agent["id"] not in state["assignments"]:
            state["assignments"][agent["id"]] = agent["id"] in _DEFAULT_BACKGROUND_AGENT_IDS
            changed = True
    if changed:
        vault_writer.save_background_agent_flags_state(state)
    return state


def get_is_background_agent(agent_id: str) -> bool:
    """Never returns None — any known agent absent from assignments is
    self-healed inside _load_state() before this reads it; an unknown
    agent_id resolves to False rather than raising, matching
    get_agent_working_mode's own no-raise style."""
    state = _load_state()
    return state["assignments"].get(agent_id, False)


def set_is_background_agent(agent_id: str, is_background_agent: bool) -> None:
    state = _load_state()
    state["assignments"][agent_id] = is_background_agent
    vault_writer.save_background_agent_flags_state(state)
