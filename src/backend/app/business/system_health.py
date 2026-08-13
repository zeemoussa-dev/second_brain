"""Read-only aggregation of Second Brain's own operational signals for
the System Health view (REQ-SB-31-US-01) -- writes no new persisted
state at all, composes only already-existing/already-computed signals
from provider_registry, agent_registry, and vault_writer, plus one
local, in-process GET /mcp reachability check. Recompute fresh on every
call -- no caching (Scenario 7)."""
import httpx

from app.business import agent_registry, provider_registry
from app.data_access import vault_writer

# Same hardcoded loopback host:port agent_orchestration/mcp_client.py
# already calls -- this project's own documented port convention
# (tools/run-backend.cmd --port 8001), not a new port-discovery
# mechanism.
_MCP_MOUNT_URL = "http://127.0.0.1:8001/mcp"


def mcp_mount_reachable() -> bool:
    """True only on the mount's own proven "alive" signal (a bare GET
    correctly returns HTTP 406 Not Acceptable when the mount is alive --
    confirmed live 2026-08-12, see architecture.md). Any other status
    code, connection error, or timeout is honestly reported as
    unreachable -- never a fabricated True.

    follow_redirects=True is required here -- live-discovered correction
    (this task's own Implementation Log): a bare GET /mcp (no trailing
    slash) actually 307-redirects to /mcp/ first, which only then answers
    406; httpx.get()'s own default (follow_redirects=False) stops at the
    307 and would falsely report the mount unreachable even when it is
    genuinely healthy. The story's own "confirmed live" 406 finding used a
    client (browser/PowerShell) that follows redirects automatically."""
    try:
        response = httpx.get(_MCP_MOUNT_URL, timeout=3.0, follow_redirects=True)
    except httpx.HTTPError:
        return False
    return response.status_code == 406


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
        "mcp": {"reachable": mcp_mount_reachable()},
        "providers": _providers_with_agent_names(),
        "disabled_agents": list_disabled_agents(),
        "last_capture_run": vault_writer.load_last_capture_run(),
    }
