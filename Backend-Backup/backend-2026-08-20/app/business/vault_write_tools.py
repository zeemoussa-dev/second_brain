"""Write-capable MCP tool for a Hermes-connected agent (REQ-SB-04-US-01,
ADR-025 points 4-6) -- a sibling to vault_query_tools.py, the same "thin
business-layer wrapper the MCP server registers" shape (ADR-015 point 3).

propose_vault_write never writes directly -- it always creates a Pending
Approval (new trigger="hermes"), unconditionally bypassing
working_mode_registry regardless of the target agent's own working mode
(extending ADR-021 point 5's own bypass-by-construction precedent to a
second case): a Hermes-originated write is a materially bigger trust
surface than an in-app action, so it is gated on every write, with no
Autonomous-mode carve-out.
"""
from __future__ import annotations

from app.business import agent_registry, pending_approval_registry
from app.data_access import vault_writer


def _is_within_assigned_scope(agent_id: str, subfolder: str, frontmatter: dict) -> bool:
    """Fail-CLOSED seam, per ADR-025 point 6 -- no REQ-SB-29 scope registry
    exists yet, so every write is rejected as out-of-scope until one does.
    This is the fail-closed default, never fail-open, matching
    REQ-SB-29-US-01 Scenario 6's own 'no assigned scope = no bounded
    access' rule extended to writes. REQ-SB-04-US-01-T03 (blocked on
    REQ-SB-29-US-01) replaces this body with a real scope-match check --
    do not implement real matching logic here, and never return True for
    any input."""
    return False


def propose_vault_write(
    agent_id: str, subfolder: str, filename_stem: str, frontmatter: dict, body: str,
) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        return {"status": "rejected", "message": f"Unknown agent '{agent_id}' -- write refused."}

    if not _is_within_assigned_scope(agent_id, subfolder, frontmatter):
        return {
            "status": "rejected",
            "message": (
                f"'{agent_id}' has no assigned vault scope covering "
                f"'{subfolder}' -- write refused (no REQ-SB-29 scope "
                "registry exists yet, so every write is currently "
                "out of scope)."
            ),
        }

    record = pending_approval_registry.create_pending_approval(
        agent_id,
        trigger="hermes",
        action_id="hermes_vault_write",
        description=f"Hermes-proposed write: {subfolder}/{filename_stem}",
        payload={
            "subfolder": subfolder,
            "filename_stem": filename_stem,
            "frontmatter": frontmatter,
            "body": body,
        },
    )
    return {
        "status": "pending",
        "message": "Write proposal held pending user approval.",
        "pending_approval_id": record["id"],
    }


def finalize_hermes_write(payload: dict) -> dict:
    path = vault_writer.write_note(
        payload["subfolder"], payload["filename_stem"], payload["frontmatter"], payload["body"],
    )
    return {"path": path}
