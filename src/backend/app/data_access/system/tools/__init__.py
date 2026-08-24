"""Tools registry block (2026-08-20 architecture pass).

Declarative Tool -> Category -> Action registry (registry.json/schema.py)
plus the mounting mechanics (registry.py) that turn each declared Tool
into its own MCP server, mounted at its own path, picked up on startup
and refreshable mid-session without a restart.
"""
