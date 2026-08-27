"""One live two-way chat bridge to Hermes' own gateway.

Hermes' embedded chat is NOT a REST call -- it's a newline-delimited
JSON-RPC 2.0 protocol carried over one WebSocket, `/api/ws` (the same
dispatcher the desktop app and Hermes' own in-browser Chat tab both
drive).

Real, verified wire shape:
- Connect: `ws://<host>/api/ws?token=<session token>` -- the SAME per-
  install session token used for REST calls (`x-hermes-session-token`
  header there, `?token=` query param here -- a browser WS handshake
  can't carry a custom header, so Hermes accepts the identical
  credential as a query param on this one endpoint).
- `{"jsonrpc":"2.0","id":<n>,"method":"session.create","params":{...}}`
  -> `{"id":<n>,"result":{"session_id": "..."}}`. `profile` scopes the
  whole session to a non-default Hermes profile; omitted entirely for
  the launch/default identity.
- `{"jsonrpc":"2.0","id":<n>,"method":"prompt.submit","params":
  {"session_id","text"}}` -> a fast `{"status":"streaming"}` ack; the
  real reply arrives as a run of `event` frames on the SAME socket,
  terminated by `message.complete` (full final text) or `turn.error`.
- Approval/clarify prompts arrive the same way (`approval.request`/
  `clarify.request` events) and are answered with
  `approval.respond`/`clarify.respond` requests carrying the event's
  own `request_id`.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable

import websockets

from app.hermes.config import HermesConfig
from app.hermes.errors import HermesUnavailableError

_log = logging.getLogger(__name__)

_RPC_TIMEOUT_S = 30.0


def _ws_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.startswith("https://"):
        return "wss://" + base[len("https://"):] + "/api/ws"
    return "ws://" + base[len("http://"):] + "/api/ws"


class HermesChatSession:
    """One live bridge: a single Hermes `/api/ws` connection plus the one
    real Hermes chat session created on it. Not reusable across agents --
    a new instance per (agent_id, caller) connection, matching how the
    real dashboard's own Chat tab opens one socket per open chat.

    `get_token` is the owning `HermesClient`'s own token fetcher
    (`HermesRestAPI.get_session_token`) -- this class never fetches or
    caches a token itself, so the two always agree on the same cached
    value."""

    def __init__(self, config: HermesConfig, get_token: Callable[[], str], agent_id: str | None):
        self._config = config
        self._get_token = get_token
        # "default"/the launch identity is NOT a real `profiles/default`
        # dir Hermes' own `profile` param can resolve -- omit it entirely
        # so session.create falls back to its own launch/default profile.
        self._profile = agent_id if agent_id and agent_id != "default" else None
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self._events: asyncio.Queue[dict] = asyncio.Queue()
        self._recv_task: asyncio.Task | None = None
        self.session_id: str | None = None

    async def connect(self) -> None:
        token = self._get_token()
        try:
            self._ws = await websockets.connect(f"{_ws_url(self._config.base_url)}?token={token}", open_timeout=10)
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
