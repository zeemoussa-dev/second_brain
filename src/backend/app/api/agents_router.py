"""Agents Map's real /agents surface (2026-08-22 retrofit) -- a fresh,
view-only implementation over the Hermes mirror (ADR-003), NOT a revival
of the archived app/_archive/api/agents_router.py (that one is coupled to
the old, now-retired Second-Brain-native orchestration agents and their
own chat/create/action-trigger machinery, none of which has a real
Hermes-side counterpart yet). Same URL surface the frontend already calls
(agentsApiClient.ts), so no frontend rewiring is needed for list/detail.

Mostly read-only -- no create/action-trigger/job/knowledge-gap endpoints
(AgentDetailPanel.tsx shows those tabs disabled for a Hermes-sourced agent
rather than this router faking support for them). Real exceptions:
icon/color (PATCH, Visual tab, 2026-08-22) -- genuinely Second-Brain-owned
presentation data (agent_visual_registry.py, untouched from before this
retrofit), never written back to Hermes; and Chat (POST .../chat,
2026-08-23; POST .../chat/reset, 2026-08-24) -- the pre-existing per-agent
Chat tab in AgentDetailPanel.tsx was calling this route already, but it
had never been implemented against Hermes; wired to the real Hermes
gateway (app/hermes/chat_session.py, ADR-006) via a `HermesChatSession` kept
alive across requests per agent (chat_sessions.py, 2026-08-24 -- see
below), not the WS surface hermes_router.py briefly proxied and has
since dropped in favor of this.

Chat turn also surfaces `clarify.request`/`approval.request` (2026-08-23
fix) -- confirmed live against the real gateway (hermes-agent's own
`tui_gateway/server.py::_block`/`_clarify_block`) that these carry a
human-readable `question` (or a batch `questions` list) / `command`
field plus the request's own `request_id`. This REST turn has nowhere to
hold that `request_id` open for a follow-up HTTP request to answer it
via `clarify.respond`/`approval.respond`, so it surfaces the question/
approval text as the turn's own reply instead (rather than silently
blocking for the full `_CHAT_TURN_TIMEOUT_S` and 504ing). Hermes' own
gateway already tolerates this: a clarify/approval left unanswered past
its own configured timeout auto-resolves with locked/default answers on
Hermes' side and the agent continues on its own -- confirmed live
(2026-08-23 one-shot CLI test) via the exact "(clarify timed out after
120s -- locked answers returned)" fallback message.

Session continuity (2026-08-24, operator: "The Context disappear every
Message no Memory") -- every chat turn used to open a BRAND NEW
`HermesChatSession` (a real, fresh `session.create`, no prior
`session_id`) and close it in `finally`, so Hermes' own gateway (which
DOES hold real multi-turn history, keyed by `session_id`, the same way
an interactive CLI session works) had no way to know two consecutive
messages were even the same conversation. `chat_sessions.py` now keeps
one live session open PER AGENT across requests, only replaced when it's
missing or confirmed dead -- this endpoint no longer closes the session
after a reply, and a NEW `POST .../chat/reset` explicitly ends the
current conversation on request (mirrors a real Hermes CLI session's own
`/new` command, MEMORY.md's own documented "session prompt is injected
once at creation, never re-read mid-conversation" constraint -- the ONLY
way to pick up e.g. a changed SOUL.md mid-conversation is a fresh
session, same as that finding already established for the CLI)."""
from __future__ import annotations

import asyncio
import json
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.agents.agent_presentation import to_detail_dict, to_summary_dict
from app.business.hermes import agents_map_adapter, chat_sessions
from app.business.hermes.client import HermesUnavailableError, get_client


class AgentVisualUpdateBody(BaseModel):
    # None (field omitted) = leave unchanged; "" (explicit empty string) =
    # clear the override back to default -- agent_visual_registry.py's own
    # convention, unchanged from before this retrofit.
    icon: str | None = None
    color: str | None = None


class ChatMessageBody(BaseModel):
    message: str


router = APIRouter(prefix="/agents")
pipelines_router = APIRouter(prefix="/pipelines")
_agent_manager = AgentManager()


@pipelines_router.get("")
def list_pipelines() -> list[dict]:
    return agents_map_adapter.list_pipeline_refs()


@router.get("")
def list_agents() -> list[dict]:
    # Pipelines aren't a real Hermes profile -- AgentManager doesn't
    # cover them (deliberately, not yet), so they're composed in
    # separately here rather than swapping the whole endpoint over.
    # A Hub agent (2026-08-28) is excluded via AgentManager's own
    # exclude_types -- it's already rendered as its Section's own
    # SectionHub center node on the map, so this endpoint never returns
    # it as an ordinary agent in the first place (business logic, not a
    # frontend filter).
    agents = _agent_manager.get_all(exclude_types=["hub"])
    return [to_summary_dict(a) for a in agents] + agents_map_adapter.list_pipeline_summaries()


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = _agent_manager.get_by_id(agent_id)
    if agent is not None:
        return to_detail_dict(agent)
    # Not a real Hermes agent -- fall through to the Pipeline-aware path
    # (agents_map_adapter.get_agent_detail already checks pipeline_registry
    # first internally).
    detail = agents_map_adapter.get_agent_detail(agent_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    return detail


@router.patch("/{agent_id}")
def update_agent_visual(agent_id: str, body: AgentVisualUpdateBody) -> dict:
    agent = _agent_manager.update(agent_id, icon=body.icon, color=body.color)
    if agent is not None:
        return to_detail_dict(agent)
    # Not a real Hermes agent -- same Pipeline fallback as get_agent above.
    updated = agents_map_adapter.update_agent_visual(agent_id, icon=body.icon, color=body.color)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    return updated


@router.post("/{agent_id}/chat")
async def send_chat_message(agent_id: str, body: ChatMessageBody) -> dict:
    """One turn over the real Hermes gateway (ADR-006), on a session kept
    alive across requests (chat_sessions.py, see module docstring) so
    Hermes' own gateway sees real multi-turn conversation continuity,
    not a fresh session every message. Returns `{reply, action_triggered}`
    (action_triggered always None -- Hermes has no concept of a
    Second-Brain-native triggered Action, unlike the old, retired agent
    model this same response shape used to serve).

    The actual lock/session/timeout/discard-on-failure turn is
    `chat_sessions.send_and_await_reply` (factored out there,
    REQ-SB-82-US-04) so Cockpit Chat's own per-question routed calls
    share this exact same handling instead of a second copy of it."""
    if get_client().profiles.find_by_id(agent_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")

    try:
        reply_text = await chat_sessions.send_and_await_reply(agent_id, body.message)
    except HermesUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except asyncio.TimeoutError as exc:
        # The session itself may still be fine (a genuinely slow
        # turn) -- left open so the conversation's own history isn't
        # lost over one slow reply.
        raise HTTPException(status_code=504, detail="Hermes did not reply in time") from exc

    return {"reply": reply_text, "action_triggered": None}


# Real event types seen live on a Hermes chat session besides the ones
# _await_reply already handles (app/hermes/chat_session.py's own module
# docstring): thinking.delta/status.update/reasoning.available carry the
# model's own in-progress "what it's doing" signal, distinct from the
# actual reply text -- session.info/session.title are pure metadata, not
# a human-readable progress signal, deliberately excluded here rather
# than surfaced as noise. Only a real, non-empty text field is ever
# forwarded -- never a JSON dump of an event whose real shape isn't
# actually known to carry one.
_ACTIVITY_EVENT_TYPES = frozenset({"thinking.delta", "status.update", "reasoning.available"})


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


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_reply(session):
    """Mirrors `_await_reply`'s own event handling exactly (same event
    types, same clarify/approval formatting, same errors) but YIELDS as
    it goes instead of only returning the final text (2026-08-24,
    operator: "is there a way to stream the output... at least I will
    feel Agents are doing something"). Real SSE frames, one JSON object
    per line: `{"type": "activity", "text": ...}` for an in-progress
    thinking/status signal, `{"type": "delta", "text": ...}` per streamed
    reply chunk, `{"type": "complete", "text": ...}` with the FULL final
    reply once (matches message.complete's own real payload shape, not
    just the last chunk), or `{"type": "error", "detail": ...}`."""
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


@router.post("/{agent_id}/chat/stream")
async def stream_chat_message(agent_id: str, body: ChatMessageBody) -> StreamingResponse:
    """Streaming twin of `POST /{agent_id}/chat` -- same session/lock
    handling, same real event types, but the client sees the reply build
    up live instead of waiting for the whole turn. NOT used for
    agent-to-agent relays (operator: "Streaming to me Agent to Agent they
    need that mood of All message at once") -- those go through the
    completely separate `terminal(command="hermes -p ... chat -q ...")`
    one-shot CLI relay, never this REST surface at all, so that
    distinction is already structural, not something this endpoint has
    to enforce itself.

    No outer `asyncio.wait_for` around the whole stream the way the
    non-streaming endpoint has -- a slow turn now shows real, visible
    progress (an `activity`/`delta` frame) instead of dead silence, so
    the same 504-after-N-seconds protection isn't the right shape here;
    the underlying `HermesChatSession._call`'s own 30s per-RPC timeout
    (app/hermes/chat_session.py) still bounds any single request/response leg
    of the turn."""
    if get_client().profiles.find_by_id(agent_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")

    lock = chat_sessions.get_lock(agent_id)
    await lock.acquire()

    async def _generate():
        try:
            try:
                session = await chat_sessions.get_or_create_session(agent_id)
                await session.send_prompt(body.message)
            except HermesUnavailableError as exc:
                await chat_sessions.discard_session(agent_id)
                yield _sse({"type": "error", "detail": str(exc)})
                return
            async for frame in _stream_reply(session):
                yield frame
        finally:
            lock.release()

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("/{agent_id}/chat/reset")
async def reset_chat_session(agent_id: str) -> dict:
    """Explicitly ends the current conversation with this agent (mirrors
    a real Hermes CLI session's own `/new` command) -- the next message
    starts a genuinely fresh Hermes session_id, with no prior turns
    carried forward. The only real way to make an agent pick up a
    changed SOUL.md mid-conversation too (MEMORY.md's own documented
    "session prompt is injected once, never re-read" constraint)."""
    if get_client().profiles.find_by_id(agent_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    lock = chat_sessions.get_lock(agent_id)
    async with lock:
        await chat_sessions.reset_session(agent_id)
    return {"reset": True}


@router.get("/{agent_id}/jobs")
def get_agent_jobs(agent_id: str) -> list[dict]:
    # [] for any real (non-Pipeline) agent id -- matches the archived
    # router's own "never a 404, never fabricated" contract for this
    # sub-resource (agentsApiClient.ts's own JobTreeEntry comment).
    return agents_map_adapter.get_pipeline_job_tree(agent_id) or []


@router.get("/{agent_id}/history")
def get_agent_history(agent_id: str) -> list[dict]:
    """Always `[]` -- same "never a 404, never fabricated" contract as
    /jobs above (2026-08-23). This endpoint existed on the old, archived
    router (chat_user/chat_agent/run_event/proposal entries against
    agent_registry's own now-retired agents) but was never rebuilt here;
    AgentDetailPanel.tsx's History tab and its Overview tab's pending-
    approval scan both already degrade cleanly on an empty list (their
    own pre-existing "Nothing recorded yet" empty state) -- restoring a
    REAL version would mean either reconstructing that exact shape from
    Hermes' own session log (a real but separate effort; see
    `fetchHermesSessions` on the Overview tab for the live equivalent
    already surfaced there) or wiring up the still-archived
    pending_approvals_router.py this data's own `proposal` entries
    depend on -- neither undertaken here; this exists only so a real
    agent's panel stops 404ing on open."""
    return []
