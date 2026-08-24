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

from app.data_access.hermes_ws_client import HermesChatSession

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
