"""Read-only aggregation of Second Brain's own operational signals for
the System Health view (REQ-SB-31-US-01) -- writes no new persisted
state at all, composes only already-existing/already-computed signals
from provider_registry and agent_registry. Recompute fresh on every
call -- no caching (Scenario 7, REQ-SB-31-US-01).

2026-08-27: dropped the "mcp" reachability check (the /mcp mount it
probed was deleted -- Second Brain is fully agentic via Hermes now, no
in-process MCP server of its own left to check) and the "scheduling"
key (agent_schedule_registry.py, whose own skill-dispatch mechanism it
reported on, was deleted the same pass -- superseded by Hermes' own
native cron scheduling)."""
from app.business import agent_registry, provider_registry


def list_disabled_agents() -> list[dict]:
    """Every agent whose selected Provider has no real client configured
    -- the System-Health-view-specific Disabled/Health-Issue override
    (scoped to this view only, per the story's own Constraints)."""
    disabled = []
    for agent in agent_registry.list_agents():
        provider = provider_registry.get_agent_provider(agent["id"])
        if provider is None or not provider_registry.has_real_client(provider["id"]):
            disabled.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "provider_name": provider["name"] if provider else None,
            })
    return disabled


def _providers_with_agent_names() -> list[dict]:
    """provider_registry.list_providers() already rolls up each
    Provider's agent_ids -- this adds a display-only agent_names field
    (resolved via agent_registry.get_agent) alongside it, additive only,
    so the frontend never has to make a second round-trip or duplicate
    the id->name lookup itself. Does not modify provider_registry.py's
    own return contract."""
    providers = provider_registry.list_providers()
    for provider in providers:
        provider["agent_names"] = [
            agent_registry.get_agent(agent_id)["name"] for agent_id in provider["agent_ids"]
        ]
    return providers


def get_system_health() -> dict:
    return {
        "providers": _providers_with_agent_names(),
        "disabled_agents": list_disabled_agents(),
    }
