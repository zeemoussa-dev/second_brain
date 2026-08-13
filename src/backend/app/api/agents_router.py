import inspect

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import (
    agent_chat,
    agent_keywords,
    agent_orchestration,
    agent_registry,
    pending_approval_registry,
    provider_registry,
    section_registry,
    working_mode_registry,
)
from app.business.agent_orchestration import knowledge_bootstrap
from app.business.email_classification import run_capture_and_record_completion
from app.data_access import vault_writer

router = APIRouter(prefix="/agents")


async def _run_build_knowledge(agent_id: str) -> dict:
    """The build_knowledge action handler (REQ-SB-36-US-02, ADR-023
    point 3) — resolves `subject` from the matched agent's own
    configured "Subject" setting, keeping knowledge_bootstrap.
    bootstrap_agent_knowledge itself fully generic over agent_id/subject
    (Scenario 6), never hardcoded here. Translates
    bootstrap_agent_knowledge's own richer status shape into the same
    {"status", "message"} envelope every other _ACTION_HANDLERS entry
    returns. "history_recorded": True signals _invoke_action's own
    generic post-call history append (trigger_action/chat, below) to
    skip its own append — bootstrap_agent_knowledge already records
    exactly one real run_event itself for every branch (ADR-023 point
    4's own "recorded as ONE run_event history entry"); without this
    flag the generic append would create a second, duplicate entry."""
    agent = agent_registry.get_agent(agent_id)
    subject = next((s["value"] for s in agent["settings"] if s["key"] == "Subject"), agent["name"])
    result = await knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject)
    message = {
        "written": f"Built knowledge — filed to {result.get('path')}.",
        "pending_approval": "Research gathered; filing paused pending approval of a new top-level vault area.",
        "no_match": f"Could not find a matching agent for the {result.get('hop')} step.",
        "no_results": "The web research step found nothing relevant.",
        "not_autonomous": f"{result.get('matched_agent_id')} is not in Autonomous mode.",
        "unavailable": result.get("message", "The Vault Filing Expert is not available."),
    }.get(result["status"], "The build-knowledge chain completed with an unexpected status.")
    return {"status": result["status"], "message": message, "history_recorded": True}


# email-capture's run_capture_now and compass-expert's build_knowledge
# (REQ-SB-36-US-02) are backed by a real handler this pass (ADR-011/
# ADR-023) — every other declared action has no handler yet and returns
# an honest "not yet available" result rather than a fabricated success.
_ACTION_HANDLERS = {
    ("email-capture", "run_capture_now"): run_capture_and_record_completion,
    ("compass-expert", "build_knowledge"): _run_build_knowledge,
}


class ChatMessageBody(BaseModel):
    message: str


class AgentAssignmentUpdateBody(BaseModel):
    section_id: str | None = None
    provider_id: str | None = None
    keywords: list[str] | None = None
    working_mode: str | None = None


def _execute_action(agent_id: str, action_id: str) -> dict:
    """Today's unconditional dispatch — renamed from _invoke_action
    (ADR-018 point 3; ADR-020 does not change this function's own body
    at all). Never itself checks working mode — called only by
    _invoke_action's fall-through branches below, and by
    app/api/pending_approvals_router.py's Approve endpoint (T06),
    deliberately bypassing the gate entirely (the approval itself is
    the authorization; re-entering the gate would find the agent still
    Supervised and defer forever, ADR-018 point 6)."""
    handler = _ACTION_HANDLERS.get((agent_id, action_id))
    if handler is None:
        return {"status": "error", "message": "This action is not yet available."}
    provider = provider_registry.get_agent_provider(agent_id)
    if provider is None or not provider_registry.has_real_client(provider["id"]):
        provider_name = provider["name"] if provider else "This agent's selected Provider"
        return {
            "status": "error",
            "message": f"{provider_name} is not available yet — no client has been built for it.",
        }
    results = handler()
    return {"status": "ok", "message": f"Done — {len(results)} email(s) filed."}


async def _execute_async_action(agent_id: str, action_id: str, handler) -> dict:
    """Async counterpart to _execute_action, above (that function is
    left fully unchanged — still used as-is by app/api/
    pending_approvals_router.py's own synchronous Approve dispatch,
    which never reaches an async handler in this story's own real scope:
    compass-expert stays Autonomous per this story's own Constraint, so
    build_knowledge is never deferred into a pending-approval record).
    Mirrors _execute_action's own Provider-availability gate exactly;
    only the handler invocation itself differs (awaited, agent_id-aware,
    returns its own already-shaped {"status", "message"} envelope
    directly rather than the generic "Done — N email(s) filed." shape
    _execute_action's own zero-arg/list-returning handler convention
    assumes) — a real, load-bearing reconciliation found composing
    around the REAL current file: _execute_action's own handler-calling
    convention (handler(), len(results)) does not generalize to
    build_knowledge's own agent_id-taking, async, richer-envelope
    handler shape."""
    provider = provider_registry.get_agent_provider(agent_id)
    if provider is None or not provider_registry.has_real_client(provider["id"]):
        provider_name = provider["name"] if provider else "This agent's selected Provider"
        return {
            "status": "error",
            "message": f"{provider_name} is not available yet — no client has been built for it.",
        }
    return await handler(agent_id)


def _action_label(agent_id: str, action_id: str) -> str:
    agent = agent_registry.get_agent(agent_id)
    action = next((a for a in agent["actions"] if a["id"] == action_id), None) if agent else None
    return action["label"] if action else action_id


async def _invoke_action(agent_id: str, action_id: str, trigger: str) -> dict:
    """The corrected, two-axis working-mode gate (ADR-020 point 2 —
    supersedes ADR-018 point 3 in full). trigger is "chat" | "direct" |
    "hub_routed" (background never reaches this function — it has its
    own separate, structurally-unchanged gate, app/business/
    email_classification.py, T05).

    Checked BEFORE _execute_action's own handler-lookup/Provider-
    availability checks, so neither a refusal nor a proposal ever
    reveals an execute-time detail (e.g. a Provider error) the human
    hasn't earned yet by approving.

    1. Manual + trigger == "hub_routed": refuse outright — no pending
       record, no execution (REQ-SB-21-US-01 Scenario 5b / AC-07).
       Today unreachable via any real call site (ADR-017's Hub-routing
       node never itself invokes a target agent's action yet) — kept
       as named forward-looking correctness per ADR-020, not dead code.
    2. Supervised + the resolved action's own "mutates" flag is True
       (or unresolvable — fail-safe to True, ADR-020 point 1):
       short-circuits into a pending-approval record — now regardless
       of trigger (chat, direct, or hub_routed), not only a specific
       trigger value the way ADR-018 point 3 gated.
    3. Supervised + "mutates" is False: falls straight through to
       _execute_action, identical to Autonomous — the corrected
       behaviour ADR-018 point 3 did not have (it gated every chat/
       direct action uniformly, read-only or not).
    4. Autonomous (any trigger), Manual ("chat"/"direct" trigger): fall
       straight through to _execute_action, unchanged from ADR-018
       point 5's own conclusion — a matched chat message or an
       Available-Actions button press remains this codebase's one
       mechanism for "the user explicitly asking" (ADR-007/ADR-011, no
       NLU), so Manual still executes immediately on either, regardless
       of whether the action reads or writes.
    """
    mode = working_mode_registry.get_agent_working_mode(agent_id)

    if mode == "manual" and trigger == "hub_routed":
        return {
            "status": "refused",
            "message": "This agent is in Manual mode — it does not act on another agent's request.",
        }

    action = agent_registry.get_action(agent_id, action_id)
    mutates = action["mutates"] if action is not None and "mutates" in action else True

    if mode == "supervised" and mutates:
        action_label = _action_label(agent_id, action_id)
        agent = agent_registry.get_agent(agent_id)
        agent_name = agent["name"] if agent else agent_id
        approval = pending_approval_registry.create_pending_approval(
            agent_id=agent_id,
            trigger=trigger,
            action_id=action_id,
            description=f"{action_label} ({agent_name})",
        )
        message = f"Proposed — {action_label}. Awaiting your approval."
        vault_writer.append_agent_history_entry(
            agent_id, "proposal", message, pending_approval_id=approval["id"],
        )
        return {"status": "pending", "message": message, "pending_approval_id": approval["id"]}

    handler = _ACTION_HANDLERS.get((agent_id, action_id))
    if handler is not None and inspect.iscoroutinefunction(handler):
        # REQ-SB-36-US-02: build_knowledge's own handler is async and
        # agent_id-aware (knowledge_bootstrap.bootstrap_agent_knowledge's
        # caller) — routed to _execute_async_action instead of
        # _execute_action, whose own handler-calling convention
        # (handler(), len(results)) is specific to run_capture_now's
        # zero-arg/list-returning shape and left unchanged.
        return await _execute_async_action(agent_id, action_id, handler)
    return _execute_action(agent_id, action_id)


@router.get("")
def list_agents() -> list[dict]:
    agents = agent_registry.list_agents()
    for agent in agents:
        section = section_registry.get_agent_section(agent["id"])
        agent["section_id"] = section["id"] if section else None
        provider = provider_registry.get_agent_provider(agent["id"])
        agent["provider_id"] = provider["id"] if provider else None
        agent["working_mode"] = working_mode_registry.get_agent_working_mode(agent["id"])
    return agents


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    section = section_registry.get_agent_section(agent_id)
    provider = provider_registry.get_agent_provider(agent_id)
    return {
        "id": agent_id,
        "name": agent["name"],
        "type": agent["type"],
        "settings": agent["settings"],
        "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
        "section_id": section["id"] if section else None,
        "section_name": section["name"] if section else None,
        "provider_id": provider["id"] if provider else None,
        "provider_name": provider["name"] if provider else None,
        "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
        "keywords": agent_keywords.get_agent_keywords(agent_id),
        "working_mode": working_mode_registry.get_agent_working_mode(agent_id),
    }


@router.patch("/{agent_id}")
def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    if body.section_id is not None:
        if not section_registry.set_agent_section(agent_id, body.section_id):
            raise HTTPException(status_code=404, detail="Unknown section")
    if body.provider_id is not None:
        if not provider_registry.set_agent_provider(agent_id, body.provider_id):
            raise HTTPException(status_code=404, detail="Unknown provider")
    if body.keywords is not None:
        agent_keywords.set_agent_keywords(agent_id, body.keywords)
    if body.working_mode is not None:
        if not working_mode_registry.set_agent_working_mode(agent_id, body.working_mode):
            raise HTTPException(
                status_code=400,
                detail="Invalid working_mode — must be one of: autonomous, supervised, manual",
            )
    return get_agent(agent_id)


@router.post("/{agent_id}/actions/{action_id}")
async def trigger_action(agent_id: str, action_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    result = await _invoke_action(agent_id, action_id, trigger="direct")
    if result["status"] not in ("pending", "refused") and not result.get("history_recorded"):
        vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
    return result


@router.post("/{agent_id}/chat")
async def chat(agent_id: str, body: ChatMessageBody) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")

    # Captured BEFORE this message's own "chat_user" entry is appended,
    # below -- run_agent_conversation's own `history` argument is the
    # conversation's prior turns only; the current message is passed
    # separately as `message` (ADR-015 point 5/6).
    history_before_this_message = vault_writer.load_agent_history(agent_id)

    vault_writer.append_agent_history_entry(agent_id, "chat_user", body.message)

    matched = agent_chat.handle_chat_message(agent_id, body.message)
    if matched["matched_action_id"] is not None:
        result = await _invoke_action(agent_id, matched["matched_action_id"], trigger="chat")
        # _invoke_action's own run_event entry (via trigger_action) is NOT
        # reused here — this path appends its own run_event directly, so
        # the chat-triggered action's history entry is attributed to this
        # call, not a second internal HTTP round-trip. A "pending"/
        # "refused" outcome needs no run_event at all — the gate itself
        # already appended the "proposal" entry for "pending" (ADR-020
        # point 2), and "refused" mirrors Manual's own silent-skip
        # posture on the background trigger (ADR-018 point 4).
        # "history_recorded" (REQ-SB-36-US-02) additionally skips this
        # generic append whenever the handler itself already recorded its
        # own real run_event (build_knowledge's own chain does, via
        # knowledge_bootstrap._record, for every branch it returns) —
        # avoids a duplicate second entry for the identical outcome.
        if result["status"] not in ("pending", "refused") and not result.get("history_recorded"):
            vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
        reply = result["message"]
        action_triggered = matched["matched_action_id"]
    else:
        # Stored facts from earlier, separate conversations with this
        # same agent (ADR-016) -- loaded fresh from disk on every
        # call, never cached in-process, mirroring history's own
        # "passed in fresh from outside" shape (ADR-015 point 6).
        memory = vault_writer.load_agent_memory(agent_id)
        conversation_result = await agent_orchestration.run_agent_conversation(
            agent_id, body.message, history_before_this_message, memory
        )
        reply = conversation_result.get("reply") or conversation_result.get("error")
        action_triggered = None
        # Persisted immediately, mirroring the "router persists
        # post-graph side effects" shape already established for
        # conversation history -- a true no-op when extraction
        # returned nothing this turn (Scenario 3).
        extracted_facts = conversation_result.get("extracted_facts") or []
        if extracted_facts:
            vault_writer.append_agent_memory_entries(agent_id, extracted_facts)

    vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
    return {"reply": reply, "action_triggered": action_triggered}


@router.get("/{agent_id}/history")
def get_history(agent_id: str) -> list[dict]:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return vault_writer.load_agent_history(agent_id)
