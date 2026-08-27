"""Per-agent persistent Hermes chat sessions (2026-08-24, operator: "The
Context disappear every Message no Memory") -- `agents_router.py`'s own
`POST /agents/{id}/chat` used to open a brand-new `HermesChatSession`
(a real, fresh `session.create` RPC, no `session_id` carried over) on
EVERY call and close it in `finally`, so the real Hermes gateway had no
way to know two consecutive chat messages were even the same
conversation -- confirmed live, this is a genuine "no memory" bug, not
a perception issue: Hermes' own gateway holds a session's real
conversation history keyed by `session_id`, and this app was simply
discarding that key every single turn.

This module is the fix: one live `HermesChatSession` held open PER
AGENT, reused across calls, only replaced when it's missing or has died
(confirmed via a real `connection.closed` event, not just assumed).
Module-level, in-process only -- a live WebSocket cannot survive this
process restarting (`--reload` included) any more than a real Hermes
CLI session can, so losing continuity across a backend restart is an
honest, unavoidable limit, not a regression from what a persisted store
could do better.

A `HermesChatSession` reads one event at a time off its own internal
queue and isn't safe for two overlapping turns on the same session, so
each agent's own `asyncio.Lock` (also held here) serializes calls
against it -- the second of two rapid-fire messages to the same agent
waits for the first turn to finish rather than racing it.
"""
from __future__ import annotations

import asyncio

from app.data_access.hermes_ws_client import HermesChatSession, HermesUnavailableError

# Outer bound on a WHOLE turn (connect + session.create + prompt.submit +
# every event up to message.complete) -- moved here from agents_router.py
# (REQ-SB-82-US-04) so the identical lock/session/timeout/discard-on-
# failure handling is shared by both the single-agent Chat tab and Cockpit
# Chat's own per-question routed calls, instead of duplicated. Value and
# its own reasoning (macc-expert's real multi-tool-call Step-1 workflow
# needing 80-90s+) unchanged from agents_router.py's original.
_CHAT_TURN_TIMEOUT_S = 360.0

_sessions: dict[str, HermesChatSession] = {}
_locks: dict[str, asyncio.Lock] = {}


def get_lock(agent_id: str) -> asyncio.Lock:
    lock = _locks.get(agent_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[agent_id] = lock
    return lock


async def get_or_create_session(agent_id: str) -> HermesChatSession:
    """Caller must already hold `get_lock(agent_id)` -- this mutates the
    shared `_sessions` dict and is not itself safe to call concurrently
    for the same agent_id."""
    session = _sessions.get(agent_id)
    if session is not None:
        return session
    session = HermesChatSession(agent_id)
    await session.connect()
    _sessions[agent_id] = session
    return session


async def discard_session(agent_id: str) -> None:
    """Drops a session that's confirmed dead (a real `connection.closed`
    event, or a `HermesUnavailableError` raised mid-call) so the NEXT
    real message gets a fresh connection instead of repeatedly failing
    against a socket that's already gone. Also the real mechanism behind
    an explicit "start a new conversation" action (`reset_session`
    below) -- discarding is what makes the NEXT `get_or_create_session`
    call open a genuinely new Hermes session_id instead of resuming the
    old conversation's history."""
    session = _sessions.pop(agent_id, None)
    if session is not None:
        await session.close()


async def reset_session(agent_id: str) -> None:
    """Explicit "forget this conversation, start fresh" -- same real
    mechanism as `discard_session` (closing the live session_id is what
    makes Hermes' own gateway stop carrying that history forward), kept
    as its own named entry point since the CALLER's intent differs (a
    deliberate reset vs. cleaning up a connection already confirmed
    dead) even though the action taken is identical."""
    await discard_session(agent_id)


def format_clarify_request(payload: dict) -> str:
    # Real wire shapes (hermes-agent's own tui_gateway/server.py::_clarify_block):
    # single question -- {"question": str, "choices": list[str] | None, ...};
    # batch -- {"questions": [{"question": str, "choices": ...}, ...]}. Either
    # way this IS the agent's question -- surfaced verbatim, never reworded,
    # so the reply the user sees matches exactly what Hermes itself asked.
    questions = payload.get("questions")
    if questions:
        return "\n\n".join(q.get("question", "") for q in questions if q.get("question"))
    return payload.get("question") or "The agent needs more information before it can continue."


def format_approval_request(payload: dict) -> str:
    # Real wire shape (hermes-agent's own tools/approval.py /
    # tui_gateway/server.py::_emit_approval_request): "command" is the
    # human-readable action awaiting approval, "reason" is optional context.
    command = payload.get("command")
    reason = payload.get("reason")
    if command and reason:
        return f"The agent needs your approval before continuing:\n\n{command}\n\n({reason})"
    if command:
        return f"The agent needs your approval before continuing:\n\n{command}"
    return "The agent needs your approval before it can continue."


async def _await_reply(session: HermesChatSession) -> str:
    async for event in session.events():
        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "message.complete":
            return payload.get("text", "")
        if event_type == "turn.error":
            raise HermesUnavailableError(f"Hermes turn failed: {payload}")
        if event_type == "clarify.request":
            return format_clarify_request(payload)
        if event_type == "approval.request":
            return format_approval_request(payload)
        if event_type == "connection.closed":
            # Confirmed dead -- fail fast instead of looping on an empty
            # queue until _CHAT_TURN_TIMEOUT_S expires.
            raise HermesUnavailableError("Hermes closed the connection")
    raise HermesUnavailableError("Hermes closed the connection before replying")


async def send_and_await_reply(agent_id: str, message: str) -> str:
    """One full turn over the real Hermes gateway on this agent's own kept-
    alive session (REQ-SB-82-US-04) -- the exact lock/session/timeout/
    discard-on-failure handling `agents_router.py`'s `POST /{agent_id}/chat`
    always used, factored out here so Cockpit Chat's own per-question
    routed calls (to a brought-in Expert OR the Research Agent fallback)
    reuse it instead of re-implementing it. Raises `HermesUnavailableError`
    or `asyncio.TimeoutError` on failure -- never returns a fabricated
    reply; the caller decides how to surface either as an honest message."""
    lock = get_lock(agent_id)
    async with lock:
        try:
            session = await get_or_create_session(agent_id)
            await session.send_prompt(message)
            return await asyncio.wait_for(_await_reply(session), timeout=_CHAT_TURN_TIMEOUT_S)
        except HermesUnavailableError:
            # The live session is confirmed bad (or never connected) --
            # drop it so the NEXT message gets a fresh one instead of
            # repeatedly failing against a socket that's already gone.
            await discard_session(agent_id)
            raise
