"""Per-agent vault tag/folder scope -- what an agent CAN REACH, not what
it knows (REQ-SB-29-US-01; keywords, REQ-SB-20/ADR-017, describe what an
agent knows -- a deliberately separate, non-overlapping dimension).
Mirrors agent_keywords.py's exact composition shape. Composed alongside
app/business/agent_registry.py, not inside it -- agent_registry.py
itself is not modified (ADR-011 point 2's "agent identity/type/actions
stay hardcoded" reasoning stays untouched).

get_agent_scope is also the real per-agent scope lookup ADR-025 point 6's
fail-closed vault_write_tools._is_within_assigned_scope(...) seam names
as a stable future contract (REQ-SB-04-US-01-T03, still blocked, ESC-026)
-- this function's own name/signature must stay stable; wiring that seam
to actually call it is REQ-SB-04-US-01-T03's own task, not this one."""
from app.data_access import vault_writer


def get_agent_scope(agent_id: str) -> list[str]:
    return vault_writer.load_agent_scope(agent_id)


def set_agent_scope(agent_id: str, scope: list[str]) -> list[str]:
    """Whole-list replace semantics, matching the free-text kv-list
    editing UX the Agent Settings panel already uses for Keywords."""
    vault_writer.save_agent_scope(agent_id, scope)
    return scope
