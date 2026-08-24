"""Tool / Category / Action schema (2026-08-20 architecture pass).

Tool = its own MCP server. Category = a subfolder inside a Tool. Action =
an individual callable inside a Category (renamed from "Skill" to avoid
colliding with Hermes' own distinct Skill concept at /v1/skills).
"""
from __future__ import annotations

from dataclasses import dataclass


# icon fields hold a Google Fonts (Material Symbols) icon name, e.g.
# "mail", "send", "calendar_month" -- operator-decided, 2026-08-20. Never
# an image/SVG asset, never MCP's own protocol-level Icon type (that
# needs a real resource `src` -- confirmed live it's a different concept,
# see registry.py's own _build_mcp_server_for_tool).


@dataclass
class Action:
    id: str
    name: str
    description: str
    icon: str
    # "module.path:function_name" -- resolved via registry.py's own
    # resolve_handler. Not optional: without it this entry is display
    # metadata only, nothing a Tool's MCP server could actually call.
    handler: str


@dataclass
class Category:
    id: str
    name: str
    description: str
    icon: str
    actions: list[Action]


@dataclass
class Tool:
    id: str
    name: str
    description: str
    icon: str
    # Where this Tool's own MCP server gets mounted, e.g. "/tools/outlook".
    # Deliberately NOT nested under "/mcp" -- that path is already owned
    # by the original single shared MCP server (api/mcp_server.py); a
    # Tool mount nested under it gets silently swallowed by Starlette's
    # route-registration-order matching (confirmed live, 2026-08-20 --
    # /mcp/outlook 404'd for exactly this reason, distinct from the
    # session_manager.run() bug fixed alongside it).
    mount_path: str
    categories: list[Category]
