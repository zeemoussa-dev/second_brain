"""Working mode: a new, persisted, user-mutable per-agent concern
(ADR-018 point 1) — Autonomous | Supervised | Manual, gating both the
chat/direct-action funnel (app/api/agents_router.py) and the
background-capture scheduler tick (app/business/email_classification.py).
Composed alongside app/business/agent_registry.py, not inside it —
agent_registry.py is not modified (ADR-011 point 2's "agent identity/
type/actions stay hardcoded" reasoning untouched a second time over).
Unlike Sections/Providers (ADR-014), this is a fixed 3-value enum, not a
user-created catalog — no "list of entities" half to this file, only
the assignment map, so seeding folds directly into _load_state() rather
than a separate _seed_state() (ADR-018 point 1's own deliberate, minor
simplification).
"""
from app.business import agent_registry
from app.data_access import vault_writer

VALID_WORKING_MODES = ("autonomous", "supervised", "manual")
_DEFAULT_WORKING_MODE = "autonomous"


def _load_state() -> dict:
    state = vault_writer.load_working_modes_state()
    if state is None:
        state = {"assignments": {}}
    changed = False
    for agent in agent_registry.list_agents():
        if agent["id"] not in state["assignments"]:
            state["assignments"][agent["id"]] = _DEFAULT_WORKING_MODE
            changed = True
    if changed:
        vault_writer.save_working_modes_state(state)
    return state


def get_agent_working_mode(agent_id: str) -> str:
    """Never returns None — any known agent absent from assignments is
    self-healed to the default inside _load_state() before this reads
    it; an unknown agent_id also resolves to the default rather than
    raising, matching get_agent_section's own no-raise style."""
    state = _load_state()
    return state["assignments"].get(agent_id, _DEFAULT_WORKING_MODE)


def set_agent_working_mode(agent_id: str, mode: str) -> bool:
    if mode not in VALID_WORKING_MODES:
        return False
    state = _load_state()
    state["assignments"][agent_id] = mode
    vault_writer.save_working_modes_state(state)
    return True
