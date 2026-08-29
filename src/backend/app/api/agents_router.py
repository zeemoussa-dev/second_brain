"""Agents Map's real /agents surface (2026-08-22 retrofit) -- a fresh,
view-only implementation over the Hermes mirror (ADR-003), NOT a revival
of the archived app/_archive/api/agents_router.py (that one is coupled to
the old, now-retired Second-Brain-native orchestration agents and their
own chat/create/action-trigger machinery, none of which has a real
Hermes-side counterpart yet). Same URL surface the frontend already calls
(agentsApiClient.ts), so no frontend rewiring is needed for list/detail.

No action-trigger/job/knowledge-gap endpoints (AgentDetailPanel.tsx shows
those tabs disabled for a Hermes-sourced agent rather than this router
faking support for them). POST /agents (2026-08-29) -- CreateAgentWizardModal.tsx
had called it and 404'd since this router's own 2026-08-22 retrofit,
confirmed live before fixing it -- now a thin wrapper over
AgentManager.create(), which already supported everything the real
frontend wizard sends. PATCH also covers real, structural fields now,
not just icon/color -- found
live the same day that AgentDetailPanel.tsx's own Vault Scope/Guardrails/
Section editing had been calling this route with `scope`/`guardrails`/
`section_id`/`is_background_agent` in its body all along, silently
dropped because this router's own body model never declared them
(FastAPI/Pydantic ignores unknown fields rather than erroring) -- so
AgentManager, which already fully supported all of these, never once
saw a real submission. Real exceptions: icon/color (PATCH, Visual tab,
2026-08-22) -- genuinely Second-Brain-owned presentation data
(agent_visual_registry.py, untouched from before this retrofit), never
written back to Hermes; and Chat (POST .../chat,
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

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.agents.agent_presentation import to_detail_dict, to_summary_dict
from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes import agents_map_adapter, chat_sessions
from app.business.hermes.client import HermesUnavailableError, get_client
from app.business.logic import agent_chat_stream

_vault_manager = VaultManager()


def _classify_scope(entries: list[str]) -> dict:
    """Splits the frontend's flat Vault Scope list back into
    {folders, tags} against the REAL current vault snapshot (same source
    the Vault Scope field's own typeahead uses, vault_search_router.py's
    /scope-suggestions) -- both folders and tags can contain "/" in this
    app's real data (e.g. "Work/Customers" vs "customer/masdar"), so a
    syntactic guess isn't reliable; a real membership check is. An entry
    matching neither (e.g. the vault has no notes under it yet) defaults
    to folder, the more common case, rather than being silently dropped."""
    suggestions = _vault_manager.list_scope_suggestions()
    known_tags = {t["tag"] for t in suggestions["tags"]}
    known_folders = set(suggestions["folders"])
    folders: list[str] = []
    tags: list[str] = []
    for raw in entries:
        entry = raw.strip()
        if not entry:
            continue
        if entry in known_tags and entry not in known_folders:
            tags.append(entry)
        else:
            folders.append(entry)
    return {"folders": folders, "tags": tags}


class AgentUpdateBody(BaseModel):
    # None (field omitted) = leave unchanged; "" (explicit empty string) =
    # clear the override back to default -- agent_visual_registry.py's own
    # convention, unchanged from before this retrofit.
    icon: str | None = None
    color: str | None = None
    # 2026-08-28 fix: these 4 were already sent by the real, live
    # AgentDetailPanel.tsx/CreateAgentWizardModal.tsx (updateAgentAssignment)
    # but silently dropped -- this body model never declared them, so
    # FastAPI/Pydantic ignored them rather than erroring, and neither
    # AgentManager nor Hermes ever saw a single real submission. `scope`
    # stays the frontend's own flat list shape (AgentDetail.scope); split
    # into {folders, tags} via _classify_scope before reaching AgentManager.
    section_id: str | None = None
    is_background_agent: bool | None = None
    prompt: str | None = None
    guardrails: str | None = None
    scope: list[str] | None = None
    # 2026-08-29: real, currently-ENABLED Hermes toolset names (e.g.
    # "terminal", "file") -- a full REPLACE when provided, same
    # declarative convention as `scope`, not an additive patch.
    tools: list[str] | None = None
    # 2026-08-29 fix: AgentManager.update() already fully supported both
    # of these -- neither was ever declared on this body model, so the
    # Agent Detail Panel had no real way to edit either (same silently-
    # dropped-field bug class as the scope/guardrails fix above).
    depends_on: list[str] | None = None
    preferred_index_ids: list[str] | None = None


class AgentCreateBody(BaseModel):
    # 2026-08-29 fix: POST /agents never existed -- CreateAgentWizardModal.tsx
    # has called it and 404'd since the router's own 2026-08-22 retrofit
    # (that pass was deliberately read-mostly, see the module docstring).
    # AgentManager.create() already supported all of this; this body model
    # is the only genuinely new piece. `id` matches the real Hermes profile
    # folder name AgentManager.create's own first positional arg expects.
    id: str
    name: str
    section_id: str
    type: str  # "worker" | "producer" | "expert" | "hub"
    is_background_agent: bool = False
    depends_on: list[str] | None = None
    description: str | None = None
    prompt: str | None = None
    guardrails: str | None = None
    scope: list[str] | None = None
    preferred_index_ids: list[str] | None = None
    tools: list[str] | None = None
    clone_from: str = "default"


class ChatMessageBody(BaseModel):
    message: str


router = APIRouter(prefix="/agents")
pipelines_router = APIRouter(prefix="/pipelines")
_agent_manager = AgentManager()


@router.post("")
def create_agent(body: AgentCreateBody) -> dict:
    # 2026-08-29 fix: a duplicate id used to reach AgentManager.create(),
    # which calls the real `hermes profile create` -- Hermes itself
    # refuses (a real, correct "Profile already exists" error), but that
    # came back through as an UNCAUGHT HermesUnavailableError -> a raw
    # 500 with a full stack trace exposed to the client, confirmed live
    # while building the Industry Expert tree. A pre-check + clean 409
    # is the same shape every other real Manager's own duplicate/conflict
    # case already uses in this router layer (e.g. sections_router.py).
    if _agent_manager.get_by_id(body.id) is not None:
        raise HTTPException(status_code=409, detail=f"Agent already exists: {body.id!r}")
    scope = _classify_scope(body.scope) if body.scope is not None else None
    agent = _agent_manager.create(
        body.id, name=body.name, section_id=body.section_id, type=body.type,
        is_background_agent=body.is_background_agent, depends_on=body.depends_on,
        description=body.description, prompt=body.prompt, guardrails=body.guardrails,
        scope=scope, preferred_index_ids=body.preferred_index_ids, tools=body.tools,
        clone_from=body.clone_from,
    )
    return to_detail_dict(agent)


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
def update_agent(agent_id: str, body: AgentUpdateBody) -> dict:
    scope = _classify_scope(body.scope) if body.scope is not None else None
    agent = _agent_manager.update(
        agent_id, icon=body.icon, color=body.color, section_id=body.section_id,
        is_background_agent=body.is_background_agent, prompt=body.prompt,
        guardrails=body.guardrails, scope=scope, tools=body.tools,
        depends_on=body.depends_on, preferred_index_ids=body.preferred_index_ids,
    )
    if agent is not None:
        return to_detail_dict(agent)
    # Not a real Hermes agent -- same Pipeline fallback as get_agent above.
    # Pipelines have no scope/guardrails/section_id concept, icon/color only.
    updated = agents_map_adapter.update_agent_visual(agent_id, icon=body.icon, color=body.color)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    return updated


@router.post("/{agent_id}/specialists/regenerate")
def regenerate_specialists(agent_id: str) -> dict:
    """Wires AgentManager.regenerate_specialists_section -- confirmed
    live, 2026-08-29 (built the Industry Expert tree end-to-end through
    the API), that this had ZERO API exposure: depends_on itself was
    settable via POST/PATCH, but the real, functional consequence (the
    parent's own SOUL.md actually learning it has these children, and
    how to reach one) required a direct Python call, with no way to
    trigger it from the frontend or any other real caller. Deliberately
    NOT triggered automatically inside create/update -- same operator
    reasoning AgentManager's own docstring already states (depends_on
    changes often while customizing; rewriting the parent's real prompt
    on every edit would be too disruptive) -- this is the explicit,
    on-demand trigger for that regeneration, callable whenever the real
    child roster has actually changed."""
    agent = _agent_manager.regenerate_specialists_section(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    return to_detail_dict(agent)


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


@router.post("/{agent_id}/chat/stream")
async def stream_chat_message(agent_id: str, body: ChatMessageBody) -> StreamingResponse:
    """Streaming twin of `POST /{agent_id}/chat` -- same session/lock
    handling, same real event types, but the client sees the reply build
    up live instead of waiting for the whole turn. The actual SSE
    interpretation and lock/session orchestration is
    `business/logic/agent_chat_stream.stream_chat_turn` -- this endpoint
    only 404-guards the agent id and hands the resulting generator to a
    StreamingResponse."""
    if get_client().profiles.find_by_id(agent_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")

    return StreamingResponse(
        agent_chat_stream.stream_chat_turn(agent_id, body.message),
        media_type="text/event-stream",
    )


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
