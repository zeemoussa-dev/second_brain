"""Real two-way chat bridge to Hermes' own live gateway (2026-08-22,
operator: "how to chat with Agent Back and Forth Communication when the
Gateway is up").

Confirmed live (2026-08-22, against this machine's own running `hermes
serve`) by hand-driving the real protocol end-to-end and getting a real
model reply back: Hermes' embedded chat is NOT a REST call -- it's a
newline-delimited JSON-RPC 2.0 protocol carried over one WebSocket,
`/api/ws` (`tui_gateway/ws.py` -> `tui_gateway/server.py::dispatch`, the
same dispatcher the desktop app and the in-browser Chat tab both drive).

Real, verified wire shape:
- Connect: `ws://<host>/api/ws?token=<session token>` -- the SAME per-
  install session token hermes_client.py already scrapes from `GET /`'s
  HTML for its own REST calls (`x-hermes-session-token` header there,
  `?token=` query param here -- a WS handshake can't carry a custom
  header from a browser, so Hermes accepts the identical credential as a
  query param on this one endpoint).
- First frame in: a `gateway.ready` event (best-effort waited on, never
  required -- a slow/absent one must not block the chat from working).
- `{"jsonrpc":"2.0","id":<n>,"method":"session.create","params":{...}}`
  -> `{"id":<n>,"result":{"session_id": "..."}}`. `profile` param scopes
  the whole session to a non-default Hermes profile (opp-manager/
  notes-manager/files-manager); omitted entirely for "default"
  (Primary), which IS the profile-less launch identity, not a real
  `profiles/default` dir.
- `{"jsonrpc":"2.0","id":<n>,"method":"prompt.submit","params":
  {"session_id","text"}}` -> a fast `{"status":"streaming"}` ack; the
  real reply arrives as a run of `event` frames on the SAME socket,
  `params.session_id` scoped to this session:
  `{"jsonrpc":"2.0","method":"event","params":{"type":"message.delta",
  "session_id":"...","payload":{"text":"..."}}}` per streamed chunk,
  terminated by `message.complete` (payload.text is the FULL final
  reply, not just the last chunk) or `turn.error`. Other real event
  types seen live in between: `session.info`, `session.title`,
  `thinking.delta`, `status.update`, `reasoning.available` -- all passed
  through verbatim rather than filtered, so the caller decides what to
  render (never silently dropping a real signal).
- Approval/clarify prompts arrive the same way (`approval.request`/
  `clarify.request` events) and are answered with
  `approval.respond`/`clarify.respond` requests carrying the event's own
  `request_id`.

Deliberately kept separate from hermes_client.py (REST, request/response,
one call in and one dict back) -- this is a genuinely different shape
(one long-lived multiplexed connection, request/response AND
server-pushed events interleaved on the same socket), not a REST-client
method that happens to look different.
"""
from __future__ import annotations

import asyncio
import json
import logging

import websockets

from app.config import settings
from app.data_access.hermes_client import HermesUnavailableError, _fetch_session_token

_log = logging.getLogger(__name__)

_RPC_TIMEOUT_S = 30.0

__all__ = ["HermesUnavailableError", "HermesChatSession"]


def _ws_url() -> str:
    # hermes_base_url is the REST base (http://127.0.0.1:9119) -- same
    # host/port, different scheme, for the WS chat endpoint.
    base = settings.hermes_base_url.rstrip("/")
    if base.startswith("https://"):
        return "wss://" + base[len("https://"):] + "/api/ws"
    return "ws://" + base[len("http://"):] + "/api/ws"


class HermesChatSession:
    """One live bridge: a single Hermes `/api/ws` connection plus the one
    real Hermes chat session created on it. Not reusable across agents --
    a new instance per (agent_id, caller) connection, matching how the
    real dashboard's own Chat tab opens one socket per open chat."""

    def __init__(self, agent_id: str | None):
        # "default" is Primary's own real profile id (hermes_definitions.py)
        # but NOT a real `profiles/default` dir Hermes' own `profile` param
        # can resolve -- omit it entirely so session.create falls back to
        # its own launch/default profile, the correct target for Primary.
        self._profile = agent_id if agent_id and agent_id != "default" else None
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self._events: asyncio.Queue[dict] = asyncio.Queue()
        self._recv_task: asyncio.Task | None = None
        self.session_id: str | None = None

    async def connect(self) -> None:
        try:
            token = _fetch_session_token()
        except HermesUnavailableError:
            raise
        try:
            self._ws = await websockets.connect(f"{_ws_url()}?token={token}", open_timeout=10)
        except OSError as exc:
            raise HermesUnavailableError(f"Hermes WS connect failed: {exc}") from exc
        self._recv_task = asyncio.create_task(self._recv_loop())
        params: dict = {"source": "second-brain"}
        if self._profile:
            params["profile"] = self._profile
        result = await self._call("session.create", params)
        self.session_id = result["session_id"]

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if "id" in obj and obj["id"] in self._pending:
                    future = self._pending.pop(obj["id"])
                    if not future.done():
                        future.set_result(obj)
                elif obj.get("method") == "event":
                    await self._events.put(obj.get("params") or {})
        except websockets.ConnectionClosed:
            pass
        finally:
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(HermesUnavailableError("Hermes WS closed mid-call"))
            await self._events.put({"type": "connection.closed", "session_id": self.session_id, "payload": {}})

    async def _call(self, method: str, params: dict) -> dict:
        if self._ws is None:
            raise HermesUnavailableError("Hermes WS not connected")
        rid = self._next_id
        self._next_id += 1
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[rid] = future
        await self._ws.send(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}))
        try:
            obj = await asyncio.wait_for(future, timeout=_RPC_TIMEOUT_S)
        except asyncio.TimeoutError as exc:
            self._pending.pop(rid, None)
            raise HermesUnavailableError(f"Hermes RPC '{method}' timed out") from exc
        if "error" in obj:
            raise HermesUnavailableError(f"Hermes RPC '{method}' failed: {obj['error']}")
        return obj.get("result") or {}

    async def send_prompt(self, text: str) -> None:
        await self._call("prompt.submit", {"session_id": self.session_id, "text": text})

    async def respond_approval(self, request_id: str, choice: str, resolve_all: bool = False) -> None:
        await self._call(
            "approval.respond",
            {"session_id": self.session_id, "request_id": request_id, "choice": choice, "all": resolve_all},
        )

    async def respond_clarify(self, request_id: str, answer: str) -> None:
        await self._call("clarify.respond", {"session_id": self.session_id, "request_id": request_id, "answer": answer})

    async def events(self):
        """Yields every real event frame's `params` (type/session_id/
        payload) as Hermes emits it, in order, for as long as the
        connection stays open. Never filters by session_id -- one
        connection carries exactly one session, so every event on it is
        already this session's own."""
        while True:
            yield await self._events.get()

    async def close(self) -> None:
        if self._recv_task is not None:
            self._recv_task.cancel()
        if self._ws is not None:
            await self._ws.close()
