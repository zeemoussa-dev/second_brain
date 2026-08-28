"""Agent visual identity (icon + color): a new, persisted, user-mutable
per-agent concern, same shape as working_mode_registry.py — composed
alongside app/business/agent_registry.py, not inside it. Unlike working
mode, there is no fixed default value to self-heal missing agents to; an
agent with no override simply reads back {"icon": None, "color": None}
and the frontend falls back to its own default per-type treatment.
"""
import json

from app.data_access import vault_writer
from app.data_access.registry import loader as registry_loader

_DEFAULT_VISUAL = {"icon": None, "color": None}


def _write_registry_agent_visual(agent_id: str, entry: dict) -> None:
    """Keeps the Registry's own `Agent.json` (REQ-SB-80 -- one file per
    agent now, icon/color merged in alongside id/name/type/etc, not a
    separate Agent-visual.json) in sync with this store's real icon/color
    override -- same reasoning/shape as section_registry.py's
    `_write_registry_section_json`: additive, one-way, picked up by
    RegistryLoader's own hot-reload poll. A silent no-op for an agent not
    yet migrated into the data/ tree (nothing to write to yet) -- this
    store's own `.second-brain/agent_visuals.json` stays the real CRUD
    source of truth regardless."""
    agent_dir = registry_loader.agent_data_dir(agent_id)
    if agent_dir is None:
        return
    config_path = agent_dir / "Agent.json"
    if not config_path.is_file():
        return
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["icon"] = entry.get("icon")
    config["color"] = entry.get("color")
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


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
    _write_registry_agent_visual(agent_id, entry)
