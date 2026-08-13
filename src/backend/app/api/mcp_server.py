"""Second Brain's own shared MCP server (ADR-015 points 7-11) -- exposes
vault-query tools to both Second Brain's own in-app LangGraph agents (via
agent_orchestration/mcp_client.py, a loopback MCP client) and Hermes's
own external orchestration, over the same mounted endpoint. Grows by
registering new tools on this same server, never a new server per
capability (ADR-015 point 9)."""
from mcp.server.fastmcp import FastMCP

from app.business import vault_query_tools, vault_write_tools

# streamable_http_path="/" -- FastMCP's own internal Streamable HTTP route
# defaults to "/mcp"; left at that default, mounting this sub-app at
# app.mount("/mcp", ...) in main.py would nest to an unreachable
# "/mcp/mcp" (live-confirmed via a real HTTP GET during this task's own
# verification, not assumed). Setting the internal route to "/" makes the
# externally reachable path exactly "/mcp" -- the single path ADR-015
# names and every consumer (mcp_client.py, Hermes) expects.
mcp_server = FastMCP("second-brain-vault-tools", streamable_http_path="/")


@mcp_server.tool()
def list_known_customers() -> list[str]:
    """List every distinct customer value currently used across the
    vault's notes."""
    return vault_query_tools.list_known_customers()


@mcp_server.tool()
def list_known_kinds() -> list[str]:
    """List every distinct note kind (Work/<kind>/ folder name) that
    currently exists in the vault."""
    return vault_query_tools.list_known_kinds()


@mcp_server.tool()
def list_known_partners() -> list[str]:
    """List every distinct partner value currently used across the
    vault's notes."""
    return vault_query_tools.list_known_partners()


@mcp_server.tool()
def list_notes_in_kind_folder(kind: str) -> list[str]:
    """List the file paths of every note in the vault's Work/<kind>/
    folder."""
    return vault_query_tools.list_notes_in_kind_folder(kind)


@mcp_server.tool()
def propose_vault_write(
    agent_id: str, subfolder: str, filename_stem: str, frontmatter: dict, body: str,
) -> dict:
    """Propose creating or modifying a vault note. Never writes directly --
    always creates a Pending Approval the user must explicitly approve or
    decline (REQ-SB-04-US-01, ADR-025). agent_id must resolve via the
    agent registry, or the proposal is rejected outright. The proposed
    target is also checked against agent_id's assigned vault tag/folder
    scope; today NO scope registry exists yet (REQ-SB-29-US-01, unbuilt),
    so this check is fail-closed and every write is honestly rejected as
    out of scope until that registry ships -- never silently allowed."""
    return vault_write_tools.propose_vault_write(agent_id, subfolder, filename_stem, frontmatter, body)
