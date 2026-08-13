"""Thin business-layer functions over already-existing read-only
vault_writer primitives -- the tool *implementations* the shared MCP
server (app/api/mcp_server.py) registers as @mcp.tool()s, consumed both
by Second Brain's own in-app LangGraph agents (via mcp_client.py) and by
Hermes's own external orchestration -- one implementation, reused both
ways (ADR-015 points 3, 8). No new data_access reads; no business rules
beyond simple projection (ADR-003)."""
from app.data_access import vault_writer


def list_known_customers() -> list[str]:
    return vault_writer.list_known_customers()


def list_known_kinds() -> list[str]:
    return vault_writer.list_known_kinds()


def list_known_partners() -> list[str]:
    return vault_writer.list_known_partners()


def list_notes_in_kind_folder(kind: str) -> list[str]:
    """Projects vault_writer's Path objects to plain path strings -- MCP
    tool return values must be JSON-serializable; a Path is not."""
    return [str(path) for path in vault_writer.list_notes_in_kind_folder(kind)]
