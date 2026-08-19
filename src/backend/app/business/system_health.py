"""Read-only aggregation of Second Brain's own operational signals for
the System Health view (REQ-SB-31-US-01, extended REQ-SB-68-US-01) --
writes no new persisted state at all, composes only already-existing/
already-computed signals from provider_registry, agent_registry, and
agent_schedule_registry, plus one local, in-process GET /mcp
reachability check. Recompute fresh on every call -- no caching
(Scenario 7, REQ-SB-31-US-01).

REQ-SB-68-US-01-T03 dropped the "last_capture_run" key/vault_writer
import: agent_schedule_registry.get_job_run_states()'s own richer
"scheduling" list supersedes the former single aggregate finished_at
timestamp this module used to read directly via vault_writer."""
import httpx

from app.business import agent_registry, agent_schedule_registry, provider_registry

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
        # REQ-SB-68-US-01 / ADR-045 point 5 -- replaces the former
        # "last_capture_run" key (a single, aggregate finished_at
        # timestamp) with the richer per-covered-job running/duration/
        # outcome list. agent_schedule_registry.get_job_run_states()
        # recomputes fresh on every call, exactly like every other
        # signal in this dict.
        "scheduling": agent_schedule_registry.get_job_run_states(),
    }
