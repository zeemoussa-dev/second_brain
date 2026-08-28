"""Real-time SSE interpretation and orchestration for one streamed
per-agent Hermes chat turn -- moved out of agents_router.py (2026-08-28,
API layer holds no business logic): deciding which Hermes event types
are "real activity" vs noise, stripping Hermes' own kaomoji branding,
and the lock/session/error-handling orchestration around a turn are all
business rules, not HTTP concerns. The router's own job is only to
404-guard the agent id and hand the resulting async generator to a
StreamingResponse.
"""
from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator

from app.business.hermes import chat_sessions
from app.business.hermes.client import HermesUnavailableError

# Real event types seen live on a Hermes chat session besides the ones
# chat_sessions.send_and_await_reply already handles (app/hermes/
# chat_session.py's own module docstring): thinking.delta/status.update/
# reasoning.available carry the model's own in-progress "what it's
# doing" signal, distinct from the actual reply text -- session.info/
# session.title are pure metadata, not a human-readable progress
# signal, deliberately excluded here rather than surfaced as noise.
_ACTIVITY_EVENT_TYPES = frozenset({"thinking.delta", "status.update", "reasoning.available"})

# A real status line often arrives as a Hermes-branded kaomoji plus a
# word ("(°ロ°) cogitating...", "( ˘⌣˘)♡ reasoning...", "(｡•́︿•̀｡)
# computing...") -- real Hermes personality, but operator: "fix the
# Icons added next to computing, collaborating etc it looks like it's
# not ours". Strips every leading character that isn't a plain ASCII
# letter, up to the first one -- covers the real kaomoji shapes seen
# live without hand-listing each one. Falls back to the original text
# if stripping would empty it out entirely (a real line that's ALL
# symbols, no trailing word) rather than ever showing a blank activity
# line.
_LEADING_NON_LETTER_RE = re.compile(r"^[^a-zA-Z]+")


def _strip_kaomoji_prefix(text: str) -> str:
    stripped = _LEADING_NON_LETTER_RE.sub("", text)
    return stripped if stripped else text


def _extract_activity_text(payload: dict) -> str | None:
    for key in ("text", "status", "message", "summary"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            # Found live, 2026-08-24: a real `status.update`/`reasoning.
            # available` event can carry an unrelated internal warning
            # (e.g. "Auxiliary title generation failed: HTTP 400...") --
            # Hermes' own session-title generation misfiring, nothing to
            # do with the actual conversation. It reads exactly like a
            # real thinking step if shown, so anything starting with
            # Hermes' own "⚠" warning marker is dropped here rather than
            # surfaced as if it were genuine agent activity.
            if value.lstrip().startswith("⚠"):
                continue
            return _strip_kaomoji_prefix(value)
    return None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_reply(session) -> AsyncIterator[str]:
    """Mirrors `chat_sessions.send_and_await_reply`'s own event handling
    exactly (same event types, same clarify/approval formatting, same
    errors) but YIELDS as it goes instead of only returning the final
    text (2026-08-24, operator: "is there a way to stream the output...
    at least I will feel Agents are doing something"). Real SSE frames,
    one JSON object per line: `{"type": "activity", "text": ...}` for an
    in-progress thinking/status signal, `{"type": "delta", "text": ...}`
    per streamed reply chunk, `{"type": "complete", "text": ...}` with
    the FULL final reply once (matches message.complete's own real
    payload shape, not just the last chunk), or `{"type": "error",
    "detail": ...}`."""
    async for event in session.events():
        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "message.delta":
            yield _sse({"type": "delta", "text": payload.get("text", "")})
        elif event_type == "message.complete":
            yield _sse({"type": "complete", "text": payload.get("text", "")})
            return
        elif event_type == "turn.error":
            yield _sse({"type": "error", "detail": f"Hermes turn failed: {payload}"})
            return
        elif event_type == "clarify.request":
            yield _sse({"type": "complete", "text": chat_sessions.format_clarify_request(payload)})
            return
        elif event_type == "approval.request":
            yield _sse({"type": "complete", "text": chat_sessions.format_approval_request(payload)})
            return
        elif event_type == "connection.closed":
            yield _sse({"type": "error", "detail": "Hermes closed the connection"})
            return
        elif event_type in _ACTIVITY_EVENT_TYPES:
            text = _extract_activity_text(payload)
            if text:
                yield _sse({"type": "activity", "text": text})
    yield _sse({"type": "error", "detail": "Hermes closed the connection before replying"})


async def stream_chat_turn(agent_id: str, message: str) -> AsyncIterator[str]:
    """The full orchestration for one streamed chat turn: acquire this
    agent's own chat lock, send the prompt over a kept-alive Hermes
    session, and yield real SSE frames as the reply streams in --
    releasing the lock when done regardless of outcome. NOT used for
    agent-to-agent relays (operator: "Streaming to me Agent to Agent
    they need that mood of All message at once") -- those go through
    the completely separate `terminal(command="hermes -p ... chat -q
    ...")` one-shot CLI relay, never this path at all.

    No outer timeout around the whole stream -- a slow turn now shows
    real, visible progress (an `activity`/`delta` frame) instead of dead
    silence; the underlying `HermesChatSession._call`'s own 30s per-RPC
    timeout (app/hermes/chat_session.py) still bounds any single
    request/response leg of the turn."""
    lock = chat_sessions.get_lock(agent_id)
    await lock.acquire()
    try:
        try:
            session = await chat_sessions.get_or_create_session(agent_id)
            await session.send_prompt(message)
        except HermesUnavailableError as exc:
            await chat_sessions.discard_session(agent_id)
            yield _sse({"type": "error", "detail": str(exc)})
            return
        async for frame in _stream_reply(session):
            yield frame
    finally:
        lock.release()
