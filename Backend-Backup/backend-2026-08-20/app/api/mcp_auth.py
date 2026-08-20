"""Shared-secret authentication for the /mcp mount (ADR-025 point 1) --
a thin ASGI middleware wrapping only the mounted FastMCP sub-app, since
app.mount(path, app) takes a raw ASGI application with no dependencies=
parameter a Depends()-based FastAPI check could attach to. Second Brain's
own in-app loopback MCP client (agent_orchestration/mcp_client.py,
"http://127.0.0.1:8001/mcp") is exempted by real TCP peer address, never
by anything the caller sends."""
from __future__ import annotations

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings

_LOOPBACK_ADDRESSES = {"127.0.0.1", "::1"}
_SHARED_SECRET_HEADER = b"x-hermes-shared-secret"


class require_hermes_shared_secret:
    """Callable ASGI middleware class (usable as
    require_hermes_shared_secret(app) per ADR-025's own naming)."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Streamable HTTP's own SSE/streaming framing rides over
            # non-"http" ASGI scope types in places -- must not be
            # disturbed by an auth check meant for ordinary HTTP requests.
            await self._app(scope, receive, send)
            return

        client = scope.get("client")
        peer_address = client[0] if client else None
        if peer_address in _LOOPBACK_ADDRESSES:
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        provided_secret = headers.get(_SHARED_SECRET_HEADER, b"").decode("utf-8")
        if provided_secret != settings.hermes_mcp_shared_secret:
            response = PlainTextResponse("Unauthorized", status_code=401)
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)
