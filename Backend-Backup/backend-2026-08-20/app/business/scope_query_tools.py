"""Scope-aware, business-rule-enforcing MCP tool (REQ-SB-29-US-01) -- a
sibling to vault_write_tools.py, not vault_query_tools.py's own thin
1:1-passthrough shape (ADR-015 point 3), because this tool must itself
enforce a business rule (resolve and bound the requesting agent's own
assigned scope server-side, never accept a freeform tags/folders
argument from the model) rather than merely project an existing
read-only vault_writer primitive unchanged. Mirrors propose_vault_write's
own explicit-agent_id/server-resolved shape (ADR-025 points 4-6)."""
from app.business import agent_registry, scope_registry
from app.data_access import vault_writer


def retrieve_notes_in_agent_scope(agent_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        return {"status": "rejected", "message": f"Unknown agent '{agent_id}' -- request refused."}

    scope = scope_registry.get_agent_scope(agent_id)
    if not scope:
        return {
            "status": "no_scope",
            "message": (
                f"'{agent_id}' has no assigned vault tag/folder scope -- "
                "it has no bounded vault query access to use."
            ),
        }

    paths = vault_writer.list_notes_matching_scope(scope)
    if not paths:
        return {
            "status": "empty",
            "message": f"No notes matching '{agent_id}'s assigned scope ({', '.join(scope)}) were found.",
        }

    notes = []
    for path in paths:
        frontmatter, body = vault_writer.read_note(path)
        notes.append({"path": str(path), "frontmatter": frontmatter, "body": body})
    return {"status": "ok", "scope": scope, "notes": notes}
