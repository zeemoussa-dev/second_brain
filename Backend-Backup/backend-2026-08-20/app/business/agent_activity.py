"""Read-only aggregation of Second Brain's own background-agent-run
history for the Agent Activity view (REQ-SB-11-US-01) -- writes no new
persisted state at all, composes only already-existing signals from
agent_registry and vault_writer, plus one local Outlook COM
reachability check. Recompute fresh on every call -- no caching
(Scenario 7).

Scope: "run_event" (success) and "run_error" (failure) history-entry
kinds only -- "chat_user"/"chat_agent"/"proposal" entries are excluded,
per the story's own Constraints (they are surfaced elsewhere: each
agent's own Communication History panel, and Pending Approvals,
respectively).
"""
from __future__ import annotations

from app.business import agent_registry
from app.data_access import outlook_com, vault_writer

_ACTIVITY_KINDS = {"run_event", "run_error"}


def list_activity_log() -> list[dict]:
    """Every "run_event"/"run_error" entry across every known agent
    (agent_registry.list_agents() -- generic by agent id, not
    hardcoded to today's two capture agents, so a future capture
    agent's entries appear automatically), newest first."""
    entries: list[dict] = []
    for agent in agent_registry.list_agents():
        for entry in vault_writer.load_agent_history(agent["id"]):
            if entry["kind"] not in _ACTIVITY_KINDS:
                continue
            entries.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "kind": entry["kind"],
                "text": entry["text"],
                "timestamp": entry["timestamp"],
            })
    entries.sort(key=lambda entry: entry["timestamp"], reverse=True)
    return entries


def get_agent_activity() -> dict:
    return {
        "activity_log": list_activity_log(),
        "outlook_channel": outlook_com.check_reachable(),
    }
