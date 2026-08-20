"""The in-app LangGraph agent's own MCP client -- connects to Second
Brain's own MCP server (app/api/mcp_server.py) over a loopback HTTP call
to the same mounted /mcp Streamable HTTP endpoint every other MCP client
(including Hermes) would use. A tool's name/description/argument-schema
is therefore declared exactly once, on the server side -- this module
never re-wraps a tool implementation directly (ADR-015 point 8)."""
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.business import skill_registry, skill_tools

# Same single FastAPI process, same host:port the app itself binds to --
# this project's actual, documented port (`tools/run-backend.cmd`'s
# `--port 8001`, `.claude/launch.json`). A loopback call, not a network
# hop. (Historical note: an earlier build session hardcoded 8002 here as
# a workaround for port 8001 being stuck due to an orphaned uvicorn
# --reload worker whose parent had died -- see MEMORY.md's Pattern entry
# on diagnosing that exact failure mode. That was a real, but session-
# local, environment anomaly, not a reason to permanently point this
# client at a non-standard port in shipped code -- restored to 8001,
# confirmed live 2026-08-12 after killing the orphaned process.)
_MCP_CLIENT = MultiServerMCPClient(
    {
        "second-brain-vault-tools": {
            "url": "http://127.0.0.1:8001/mcp",
            "transport": "streamable_http",
        }
    }
)


async def load_agent_tools(agent_id: str) -> list:
    """Filters the shared MCP server's full tool list per-agent
    (ADR-022 point 6) -- the four core vault-query tools stay always
    available; a skill-catalog tool (skill_tools.SKILLS) is only
    included when skill_registry.has_skill_access(agent_id, skill_id)
    is True. Replaces load_vault_query_tools() as this module's one
    public entry point -- reuses has_skill_access exactly as
    skill_registry.py's own docstring already anticipated, not a new
    enforcement concept."""
    all_tools = await _MCP_CLIENT.get_tools()
    return [
        t for t in all_tools
        if t.name not in skill_tools.SKILLS or skill_registry.has_skill_access(agent_id, t.name)
    ]
