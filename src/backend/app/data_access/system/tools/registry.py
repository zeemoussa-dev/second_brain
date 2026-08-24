"""Tool registry mounting mechanics (2026-08-20 architecture pass).

Turns registry.json's declared Tool -> Category -> Action entries into
real, mounted MCP servers -- one per Tool. load_tools_registry/
resolve_handler/mount_all_tools are real and generic (correct for any
number of declared Tools, including zero); they don't depend on any
specific Tool/Action existing yet, only on registry.json's own shape
being valid.

Auth: reuses app.api.mcp_auth.require_hermes_shared_secret uniformly for
every Tool mount, same as the pre-redesign single-server pattern -- a
reasonable default, not a decision that per-Tool scoped auth is rejected.
Revisit if/when a real need for per-Tool auth scoping shows up (see
Implementation/Plans/2026-08-20-backend-architecture-redesign.md, Open
Questions).
"""
from __future__ import annotations

import importlib
import json
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.api.mcp_auth import require_hermes_shared_secret
from app.data_access.system.tools.schema import Action, Category, Tool

_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"

# Tool id -> the real FastMCP instance mounted for it. Tracked (not just
# the id) because each one's own session_manager.run() lifespan must
# still be entered inside the app's own lifespan (see
# enter_tool_server_lifespans below) -- a Mount()-ed sub-app's lifespan is
# NOT invoked automatically just by app.mount(), the exact same gap
# api/mcp_server.py's own mount already has to work around in main.py.
# Also doubles as the "already mounted" set reload_tools_registry checks
# -- FastAPI/Starlette has no unmount primitive, so mid-session refresh is
# additive-only by construction, not a limitation to fix later.
_mounted_servers: dict[str, FastMCP] = {}


def load_tools_registry() -> list[Tool]:
    """Reads and parses registry.json into typed Tool/Category/Action
    objects. Pure I/O + parsing, no side effects, safe to call repeatedly
    (mirrors agent_schedule_registry.load_default_schedules's own shape,
    Backend-Backup/backend-2026-08-20/)."""
    raw = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        Tool(
            id=t["id"], name=t["name"], description=t["description"], icon=t["icon"],
            mount_path=t["mount_path"],
            categories=[
                Category(
                    id=c["id"], name=c["name"], description=c["description"], icon=c["icon"],
                    actions=[
                        Action(
                            id=a["id"], name=a["name"], description=a["description"],
                            icon=a["icon"], handler=a["handler"],
                        )
                        for a in c["actions"]
                    ],
                )
                for c in t["categories"]
            ],
        )
        for t in raw["tools"]
    ]


def resolve_handler(dotted_path: str) -> Callable:
    """Resolves a "module.path:function_name" handler string to the real
    callable it names. Generic -- works for any Action, whether or not
    that Action's own module has a real (non-NotImplementedError)
    implementation yet; raises the same ImportError/AttributeError Python
    would for any bad import, never swallowed."""
    module_path, function_name = dotted_path.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, function_name)


def _build_mcp_server_for_tool(tool: Tool) -> FastMCP:
    """One real FastMCP instance per Tool, one registered tool per
    declared Action -- uses the Action's OWN declared name/description
    (confirmed live against the real FastMCP.tool() signature), never the
    handler function's own docstring, so a NotImplementedError-stubbed
    handler still gets a real, correct tool listing.

    `action.icon` is deliberately NOT passed to FastMCP's own `icons`
    param -- confirmed live that MCP's `Icon` type requires a real `src`
    resource URI, not a bare label string. Our `icon` field is for our
    own registry/display purposes (e.g. a future UI), a different concept
    from MCP's protocol-level icon."""
    server = FastMCP(tool.id, streamable_http_path="/")
    for category in tool.categories:
        for action in category.actions:
            handler = resolve_handler(action.handler)
            server.tool(name=action.id, description=action.description)(handler)
    return server


def mount_all_tools(app: FastAPI) -> None:
    """Startup entrypoint -- mounts every declared Tool's own MCP server
    at its own mount_path, skipping any already mounted (idempotent,
    safe to call more than once). Called at MODULE level in main.py (not
    inside the lifespan) since Starlette's routing table needs every
    mount registered before the app starts serving -- mirrors mcp_server's
    own mount. Each mounted server's own session_manager.run() lifespan
    still needs entering separately -- see enter_tool_server_lifespans,
    called from inside main.py's lifespan, same as mcp_server's own."""
    for tool in load_tools_registry():
        if tool.id in _mounted_servers:
            continue
        server = _build_mcp_server_for_tool(tool)
        app.mount(tool.mount_path, require_hermes_shared_secret(server.streamable_http_app()))
        _mounted_servers[tool.id] = server


async def enter_tool_server_lifespans(stack: AsyncExitStack) -> None:
    """Enters every currently-mounted Tool server's own session_manager.
    run() context onto the caller's AsyncExitStack -- without this, a
    mounted Tool's own Streamable HTTP transport never initializes the
    task group it needs, and every request to it 404s/500s (confirmed
    live, 2026-08-20: /mcp/outlook 404'd until this fix, while /mcp itself
    -- whose session_manager.run() main.py's lifespan already enters --
    correctly returned a real MCP protocol response). Call AFTER
    mount_all_tools(app) has already run (module level), from inside
    main.py's own lifespan, mirroring mcp_server.session_manager.run()'s
    identical existing entry there."""
    for server in _mounted_servers.values():
        await stack.enter_async_context(server.session_manager.run())


def reload_tools_registry(app: FastAPI) -> None:
    """Mid-session refresh -- re-reads registry.json and mounts any Tool
    not already mounted (a newly-added Tool). An edit to an ALREADY-
    mounted Tool's own Categories/Actions is NOT picked up by this call
    -- that Tool's FastMCP instance was already built and mounted; a
    genuine "add an Action to an existing Tool without restarting"
    capability is a real gap, not yet solved (would need either a
    restart or a live-mutation primitive on the already-mounted FastMCP
    instance itself).

    Disclosed, not yet solved: a Tool newly mounted by THIS call still
    won't actually work until enter_tool_server_lifespans is called again
    for it -- the app's own startup AsyncExitStack has already run by the
    time any mid-session reload happens, so a mid-session-added Tool's own
    session_manager.run() never gets entered, reproducing the exact
    /mcp/outlook 404 bug this same file's mount_all_tools/
    enter_tool_server_lifespans split was built to fix, just for a
    different trigger (mid-session add, not startup). A real fix needs a
    live-appendable AsyncExitStack kept open for the app's whole process
    lifetime, not the one-shot stack main.py's lifespan currently builds
    -- not built yet, since nothing has needed a genuine mid-session Tool
    addition tested end-to-end so far."""
    mount_all_tools(app)
