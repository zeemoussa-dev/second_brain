"""Agent visual identity (icon + color): a new, persisted, user-mutable
per-agent concern, same shape as working_mode_registry.py — composed
alongside app/business/agent_registry.py, not inside it. Unlike working
mode, there is no fixed default value to self-heal missing agents to; an
agent with no override simply reads back {"icon": None, "color": None}
and the frontend falls back to its own default per-type treatment.
"""
from app.data_access import vault_writer

_DEFAULT_VISUAL = {"icon": None, "color": None}


def _load_state() -> dict:
    state = vault_writer.load_agent_visuals_state()
    if state is None:
        state = {"assignments": {}}
    return state


def get_agent_visual(agent_id: str) -> dict:
    state = _load_state()
    return state["assignments"].get(agent_id, dict(_DEFAULT_VISUAL))


def set_agent_visual(agent_id: str, icon: str | None = None, color: str | None = None) -> None:
    """icon/color of None means "not provided in this call, leave
    unchanged" (mirrors AgentAssignmentUpdateBody's own omitted-field
    convention); an explicit empty string means "clear this override
    back to the default" — the PATCH body's own Reset-to-default path."""
    state = _load_state()
    entry = state["assignments"].setdefault(agent_id, dict(_DEFAULT_VISUAL))
    if icon is not None:
        entry["icon"] = icon or None
    if color is not None:
        entry["color"] = color or None
    vault_writer.save_agent_visuals_state(state)
