"""Shared-secret authentication for a mounted ASGI app that Hermes itself
calls INTO (the reverse direction from every other module in this
library, which calls OUT to Hermes). A thin ASGI middleware wrapping
only the mounted sub-app, since `app.mount(path, app)` takes a raw ASGI
application with no `dependencies=` parameter a Depends()-based FastAPI
check could attach to."""
from __future__ import annotations

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_LOOPBACK_ADDRESSES = {"127.0.0.1", "::1"}
_SHARED_SECRET_HEADER = b"x-hermes-shared-secret"


class RequireHermesSharedSecret:
    """Callable ASGI middleware class. Loopback callers (the embedding
    app's own in-process MCP client) are exempted by real TCP peer
    address, never by anything the caller sends."""

    def __init__(self, app: ASGIApp, *, shared_secret: str) -> None:
        self._app = app
        self._shared_secret = shared_secret

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
        if provided_secret != self._shared_secret:
            response = PlainTextResponse("Unauthorized", status_code=401)
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)
