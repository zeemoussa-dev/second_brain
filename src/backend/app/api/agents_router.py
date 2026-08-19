import inspect

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.business import (
    agent_chat,
    agent_keywords,
    agent_orchestration,
    agent_prompts,
    agent_registry,
    agent_schedule_registry,
    agent_visual_registry,
    background_agent_registry,
    knowledge_gap_tracking,
    pending_approval_registry,
    provider_registry,
    scope_registry,
    section_registry,
    skill_registry,
    skill_tools,
    vault_filing_expert,
    working_mode_registry,
)
from app.business.agent_orchestration import knowledge_bootstrap
from app.business.email_classification import run_capture_and_record_completion
from app.business.pipelines import email_capture_pipeline
from app.data_access import upload_storage, vault_writer

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


# email-capture-pipeline's run_capture_now (REQ-SB-55-US-01-T08, ADR-043
# point 6 -- renamed 1:1 from the former "email-capture" id) and
# compass-expert's build_knowledge (REQ-SB-36-US-02) are backed by a real
# handler this pass (ADR-011/ADR-023) — every other declared action has
# no handler yet and returns an honest "not yet available" result rather
# than a fabricated success.
_ACTION_HANDLERS = {
    ("email-capture-pipeline", "run_capture_now"): run_capture_and_record_completion,
    ("compass-expert", "build_knowledge"): _run_build_knowledge,
}


class ChatMessageBody(BaseModel):
    message: str


class AgentAssignmentUpdateBody(BaseModel):
    section_id: str | None = None
    provider_id: str | None = None
    keywords: list[str] | None = None
    working_mode: str | None = None
    scope: list[str] | None = None
    is_background_agent: bool | None = None
    # Omitted (None) = leave unchanged; "" = clear back to default
    # (agent_visual_registry.set_agent_visual's own convention).
    icon: str | None = None
    color: str | None = None
    prompt: str | None = None
    guardrails: str | None = None


class JobSettingsUpdateBody(BaseModel):
    # Omission-means-unchanged convention, mirroring
    # AgentAssignmentUpdateBody's own prompt/guardrails fields (T04).
    prompt: str | None = None
    guardrails: str | None = None


class GapResolveBody(BaseModel):
    answer: str


class CreateAgentBody(BaseModel):
    name: str
    type: str
    domain: str | None = None
    purpose: str | None = None
    trigger: str | None = None
    # 2026-08-20 -- real pipeline-predecessor ids (AgentSummary.depends_on,
    # agents_router.py::list_agents), for a Sub-Agent that structurally
    # receives from another real agent (a Job Tree/Agents Map pipeline
    # chain). Optional, defaults to no dependency (a pipeline entry point
    # or a standalone agent) -- every existing wizard call site is
    # unaffected.
    depends_on: list[str] | None = None


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


async def _invoke_capability(agent_id: str, capability_id: str, trigger: str) -> dict:
    """Routes a capability id that is a skill_tools.SKILLS member to
    skill_registry.invoke_skill, translating its varying result shapes
    into the same {"status", "message"} envelope _invoke_action's
    callers already expect (ADR-028 point 3). Reconciled against the REAL
    skill_registry.invoke_skill/skill_tools return shapes (not the task's
    own illustrative sample verbatim): a successful/honest-unavailable
    dispatch (T01's stub handlers, web_research) returns
    {"available": bool, "message": str} with NO "status" key at all, so
    every check below reads result.get("status") rather than
    result["status"] -- the literal sample's own result["status"] would
    KeyError on that branch.

    ADR-045 point 1: when capability_id == "run_capture_now" (the one
    capability id shared by exactly the three capture-style covered
    agents -- email-capture-pipeline/meeting-capture/todo-capture, per
    skill_registry._MIGRATION_GRANT_SEED["run_capture_now"], read from
    there, never re-hardcoded here), the dispatch itself is routed
    through agent_schedule_registry.dispatch_with_shared_lock instead of
    calling skill_registry.invoke_skill directly -- gaining
    asyncio.to_thread (the non-blocking fix, this task) AND the shared
    Outlook-COM dispatch lock (closing the race-condition risk between a
    manual trigger and a concurrent scheduled tick) in the same
    already-Accepted, already-proven function.

    ESC-045 (REQ-SB-69-US-01-T04 follow-up, ADR-046 Decision 4): this
    endpoint (POST /agents/{agent_id}/actions/{action_id}) is also a
    real, reachable manual-dispatch path for "pull_email"/"process_
    staged_email" now that both are skill_tools.SKILLS members (trigger_
    action/chat route any SKILLS member here). Before this fix, neither
    id was routed through ANY lock here -- both fell into the generic
    skill_registry.invoke_skill else-branch below, unlike run_capture_
    now. "pull_email" now joins "run_capture_now" through the shared
    Outlook-COM lock (it is the one of the two that actually touches
    Outlook); "process_staged_email" is routed through the dedicated
    processing lock instead -- mirrors agent_schedule_registry._make_
    scheduled_tick_callback's/capture_scheduler._build_scheduled_tick's
    own identical dispatch-selection shape. Every other capability_id is
    unaffected -- still the generic skill_registry.invoke_skill call.

    result.get("status") == "skipped" (the lock-already-held outcome) is
    now translated verbatim rather than folded into the generic
    "available" -> "ok" fallback, which would otherwise mislabel a
    genuine skip as a success. The translated result additionally
    carries "history_recorded": True whenever the call was routed
    through one of the two lock-holding dispatch functions -- both
    already record their own outcome to history internally
    (_record_outcome, ADR-037 point 1); without this flag,
    trigger_action's/chat's own generic post-call
    vault_writer.append_agent_history_entry would write a second,
    duplicate entry for the same run (a real, disclosed side effect of
    this fix that also closes a pre-existing duplicate-history-entry
    gap for run_capture_now specifically -- ADR-045 point 1)."""
    if capability_id in ("run_capture_now", "pull_email"):
        result = await agent_schedule_registry.dispatch_with_shared_lock(
            agent_id, capability_id, trigger=trigger,
        )
    elif capability_id == "process_staged_email":
        result = await agent_schedule_registry.dispatch_with_dedicated_processing_lock(
            agent_id, capability_id, trigger=trigger,
        )
    else:
        result = skill_registry.invoke_skill(agent_id, capability_id, args=None, trigger=trigger)

    history_recorded = capability_id in ("run_capture_now", "pull_email", "process_staged_email")

    if result.get("status") == "skipped":
        return {"status": "skipped", "message": result["message"], "history_recorded": history_recorded}
    if result.get("status") == "unknown_skill":
        # Defensive only -- capability_id is already confirmed a
        # skill_tools.SKILLS member by the caller before this is reached.
        return {
            "status": "error",
            "message": "This capability is not registered.",
            "history_recorded": history_recorded,
        }
    if result.get("status") == "refused":
        return {"status": "refused", "message": result["reason"], "history_recorded": history_recorded}
    # A skill handler's own {"available": bool, "message": str} shape
    # (T01's stub handlers, and web_research) maps onto the same
    # {"status", "message"} envelope _execute_action already uses for
    # "not yet available" (status "error") vs. a real result (status "ok").
    return {
        "status": "ok" if result.get("available", True) else "error",
        "message": result.get("message", ""),
        "history_recorded": history_recorded,
    }


@router.get("")
def list_agents() -> list[dict]:
    agents = agent_registry.list_agents()
    for agent in agents:
        section = section_registry.get_agent_section(agent["id"])
        agent["section_id"] = section["id"] if section else None
        provider = provider_registry.get_agent_provider(agent["id"])
        agent["provider_id"] = provider["id"] if provider else None
        agent["working_mode"] = working_mode_registry.get_agent_working_mode(agent["id"])
        agent["is_background_agent"] = background_agent_registry.get_is_background_agent(agent["id"])
        visual = agent_visual_registry.get_agent_visual(agent["id"])
        agent["icon"] = visual["icon"]
        agent["color"] = visual["color"]
        # AgentSummary.depends_on (frontend agentsApiClient.ts) now has a
        # real source (2026-08-20): agent_registry.list_agents() already
        # carries each agent's own real depends_on (empty for every agent
        # created before this change, and for every seed agent — an
        # honest, structurally-correct default, not fabricated data).
        # branch_target_agent_id still has no real backend source.
        agent["depends_on"] = agent.get("depends_on", [])
        agent["branch_target_agent_id"] = None
    return agents


@router.post("")
def create_agent(body: CreateAgentBody) -> dict:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="A name is required.")
    if body.type not in ("expert", "worker", "producer"):
        raise HTTPException(
            status_code=400,
            detail=f"Creating a '{body.type}' agent is not yet available — only Expert, Worker, and Producer are supported today.",
        )
    # REQ-SB-46-US-01-T05 / ADR-039 point 3 — Trigger (User/Agent/Schedule,
    # defaulting to "user") is recorded as agent metadata only, via the same
    # generic settings kv-list Domain/Purpose already use, appended
    # uniformly after each branch's own settings are built below — never a
    # per-type special case.
    trigger_value = (body.trigger or "user").strip() or "user"

    if body.type == "expert":
        domain = (body.domain or "").strip()
        if not domain:
            raise HTTPException(
                status_code=400,
                detail="A knowledge domain is required for an Expert agent.",
            )
        created = agent_registry.create_agent(
            name,
            "expert",
            settings=[
                {"key": "Domain", "value": domain},
                {"key": "Trigger", "value": trigger_value},
            ],
            depends_on=body.depends_on,
        )
    elif body.type == "worker":
        # No Domain-equivalent setting — a Worker's real configuration
        # (Skills, Vault Scope, Section) lives entirely in the wizard's
        # own three follow-up calls, never in settings (Trigger excepted,
        # above).
        created = agent_registry.create_agent(
            name, "worker", settings=[{"key": "Trigger", "value": trigger_value}],
            depends_on=body.depends_on,
        )
    else:
        # Producer: Purpose is stored via the same generic settings
        # kv-list Expert's Domain already uses (ADR-031 point 3), not a
        # new field and not Worker's empty-settings pattern. The output
        # Skill and Section are the wizard's own separate follow-up
        # calls (grant + PATCH), never this endpoint's job.
        purpose = (body.purpose or "").strip()
        if not purpose:
            raise HTTPException(
                status_code=400,
                detail="A Purpose is required for a Producer agent.",
            )
        created = agent_registry.create_agent(
            name,
            "producer",
            settings=[
                {"key": "Purpose", "value": purpose},
                {"key": "Trigger", "value": trigger_value},
            ],
            depends_on=body.depends_on,
        )
    return get_agent(created["id"])


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    section = section_registry.get_agent_section(agent_id)
    provider = provider_registry.get_agent_provider(agent_id)
    visual = agent_visual_registry.get_agent_visual(agent_id)
    return {
        "id": agent_id,
        "name": agent["name"],
        "type": agent["type"],
        "settings": agent["settings"],
        "capabilities": skill_registry.list_agent_capabilities(agent_id),
        "section_id": section["id"] if section else None,
        "section_name": section["name"] if section else None,
        "provider_id": provider["id"] if provider else None,
        "provider_name": provider["name"] if provider else None,
        "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
        "keywords": agent_keywords.get_agent_keywords(agent_id),
        "working_mode": working_mode_registry.get_agent_working_mode(agent_id),
        "scope": scope_registry.get_agent_scope(agent_id),
        "is_background_agent": background_agent_registry.get_is_background_agent(agent_id),
        "icon": visual["icon"],
        "color": visual["color"],
        "prompt": agent_prompts.get_prompt(agent_id),
        "guardrails": agent_prompts.get_guardrails(agent_id),
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
    if body.scope is not None:
        scope_registry.set_agent_scope(agent_id, body.scope)
    if body.working_mode is not None:
        if not working_mode_registry.set_agent_working_mode(agent_id, body.working_mode):
            raise HTTPException(
                status_code=400,
                detail="Invalid working_mode — must be one of: autonomous, supervised, manual",
            )
    if body.is_background_agent is not None:
        background_agent_registry.set_is_background_agent(agent_id, body.is_background_agent)
    if body.icon is not None or body.color is not None:
        agent_visual_registry.set_agent_visual(agent_id, icon=body.icon, color=body.color)
    if body.prompt is not None:
        agent_prompts.set_prompt(agent_id, body.prompt)
    if body.guardrails is not None:
        agent_prompts.set_guardrails(agent_id, body.guardrails)
    return get_agent(agent_id)


@router.post("/{agent_id}/actions/{action_id}")
async def trigger_action(agent_id: str, action_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    # ADR-028 point 3 -- a migrated read-only id (view_last_run/
    # ask_question/view_channel_status) is a skill_tools.SKILLS member and
    # routes through skill_registry.invoke_skill; every still-real Action
    # id keeps calling _invoke_action exactly as before this story.
    if action_id in skill_tools.SKILLS:
        result = await _invoke_capability(agent_id, action_id, trigger="direct")
    else:
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
        matched_capability_id = matched["matched_action_id"]
        # Same ADR-028 point 3 dispatch fork as trigger_action, above.
        if matched_capability_id in skill_tools.SKILLS:
            result = await _invoke_capability(agent_id, matched_capability_id, trigger="chat")
        else:
            result = await _invoke_action(agent_id, matched_capability_id, trigger="chat")
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
        action_triggered = matched_capability_id
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


@router.post("/{agent_id}/chat/attachment")
async def chat_with_attachment(
    agent_id: str, message: str = Form(""), file: UploadFile = File(...)
) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")

    content = await file.read()
    rejection = upload_storage.validate_upload(file.filename, len(content))
    if rejection is not None:
        # Scenarios 7-8/AC-07-08: no storage, no history entry, no
        # summarization/filing attempted for a rejected upload.
        return {"reply": rejection, "attachment_status": "rejected", "vault_path": None}

    upload_id = upload_storage.save_upload(file.filename, content)
    attachment_note = f"{message} [attached: {file.filename}]".strip()
    vault_writer.append_agent_history_entry(agent_id, "chat_user", attachment_note)

    try:
        extracted_text = upload_storage.extract_text_content(upload_id, file.filename)
    except ValueError as exc:
        # Honest, not silent -- mirrors Scenario 9's "never fabricate"
        # posture for a file that validated by extension but yields no
        # real text (e.g. a scanned/image-only PDF).
        upload_storage.delete_upload(upload_id, file.filename)
        reply = f"Couldn't read {file.filename}: {exc}"
        vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
        return {"reply": reply, "attachment_status": "extraction_failed", "vault_path": None}

    # summarize-file is this story's own mandatory default capability
    # (not an opt-in Skill like web-research) -- grant is unconditional
    # and idempotent, not gated behind a separate manual-grant workflow.
    # See the parent story's Decomposer-pass Notes for why.
    skill_registry.grant_skill_access(agent_id, "summarize-file")
    source_description = f"Uploaded file: {file.filename} (via {agent['name']} chat)"
    summary_result = skill_registry.invoke_skill(
        agent_id,
        "summarize-file",
        {"content": extracted_text, "source_description": source_description},
        trigger="direct",
    )
    if summary_result.get("status") != "ok":
        # Scenario 9/AC-09 -- honest, specific failure; Vault Filing
        # Expert never invoked; no partial vault note.
        upload_storage.delete_upload(upload_id, file.filename)
        reply = summary_result.get("message", "Summarization failed.")
        vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
        return {"reply": reply, "attachment_status": "summarization_failed", "vault_path": None}

    summary = summary_result["summary"]
    # Scenario 5/AC-05 -- the temporary copy is deleted once summarized,
    # regardless of the downstream filing outcome (its own job -- feeding
    # the summary -- is already done).
    upload_storage.delete_upload(upload_id, file.filename)

    filing_result = vault_filing_expert.determine_placement_and_file(
        content=summary, source_description=source_description, requesting_agent_id=agent_id,
    )
    if filing_result["status"] == "written":
        reply = f"Filed — {filing_result['path']} (tags: {', '.join(filing_result['tags'])})."
        vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
        return {"reply": reply, "attachment_status": "filed", "vault_path": filing_result["path"]}

    # Scenario 10/AC-10 -- filing failed or is pending; the summary is
    # NOT discarded, it stays visible in the thread.
    failure_detail = filing_result.get("message") or filing_result["status"]
    reply = (
        f"I summarized {file.filename}, but couldn't file it into the vault yet "
        f"({failure_detail}). Here's the summary so it isn't lost:\n\n{summary}"
    )
    vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
    return {"reply": reply, "attachment_status": "summarized_unfiled", "vault_path": None}


@router.get("/{agent_id}/history")
def get_history(agent_id: str) -> list[dict]:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return vault_writer.load_agent_history(agent_id)


@router.get("/{agent_id}/jobs")
def get_jobs(agent_id: str) -> list[dict]:
    """Read-only Job-tree sub-resource (REQ-SB-65-US-01-T01) -- mirrors
    get_history/get_knowledge_gaps' own 404-on-unknown-agent convention.
    Only `email-capture-pipeline` has a real, populated compiled-graph
    Job tree today (Scenario 5's own scope bound); every other real,
    known agent honestly returns `[]` -- never a 404, never a fabricated
    tree."""
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    if agent_id != "email-capture-pipeline":
        return []
    section = section_registry.get_agent_section(agent_id)
    section_id = section["id"] if section else None
    jobs = email_capture_pipeline.get_job_tree()
    for job in jobs:
        job["section_id"] = section_id
    return jobs


# The 1 real Job with no real LLM call site of its own (ADR-044 Decision
# 2, ESC-039 Resolved) -- a small, disclosed, hand-maintained set; "does
# this Job's own function call Compass" is a fact about
# email_classification.py's real code, not something get_job_tree()'s
# generic graph introspection can ever expose. thread_match_merge moved
# OUT of this set (REQ-SB-67-US-01-T02) -- it gained a real Compass call
# site (_synthesize_thread_summary), exactly the mechanical update
# ADR-044's own Consequences already anticipated.
_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE = {"detect_recurring_pattern"}


def _get_known_job_or_404(agent_id: str, job_id: str) -> dict:
    """Shared agent_id/job_id resolution for the Job Settings endpoint
    pair below -- mirrors get_jobs's own 404-on-unknown-agent convention,
    then looks up job_id among that agent's own real get_job_tree()
    entries (only email-capture-pipeline has any today, exactly as
    get_jobs already established). agent_id is validation/scoping only --
    never used as agent_prompts.json's own storage key (ADR-044
    Decision 2)."""
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    jobs = email_capture_pipeline.get_job_tree() if agent_id == "email-capture-pipeline" else []
    job = next((candidate for candidate in jobs if candidate["id"] == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job


@router.get("/{agent_id}/jobs/{job_id}/settings")
def get_job_settings(agent_id: str, job_id: str) -> dict:
    """Job-tier Settings-only surface (ADR-044 Decision 2) -- a genuinely
    separate resource, never a widening of GET /agents/{agent_id} or
    agent_registry.get_agent() itself. prompt is the KEY OMITTED (not
    null) for the 2 excluded Jobs -- honestly absent rather than
    present-but-inert (Scenario 10)."""
    job = _get_known_job_or_404(agent_id, job_id)
    settings = {"id": job_id, "name": job["name"]}
    if job_id not in _JOBS_WITHOUT_REAL_PROMPT_CALL_SITE:
        settings["prompt"] = agent_prompts.get_prompt(job_id)
    settings["guardrails"] = agent_prompts.get_guardrails(job_id)
    return settings


@router.patch("/{agent_id}/jobs/{job_id}/settings")
def update_job_settings(agent_id: str, job_id: str, body: JobSettingsUpdateBody) -> dict:
    """Writes directly into agent_prompts.json under job_id's own key,
    via the SAME agent_prompts.set_prompt/set_guardrails functions real
    Agent ids use -- no special-casing (T01 Scenario 8). PATCHing prompt
    for one of the 2 excluded Jobs is rejected outright (this task's own
    disclosed Constraint) rather than silently stored with no effect."""
    _get_known_job_or_404(agent_id, job_id)
    if body.prompt is not None:
        if job_id in _JOBS_WITHOUT_REAL_PROMPT_CALL_SITE:
            raise HTTPException(
                status_code=400,
                detail="This Job has no real Prompt call site — Prompt cannot be set.",
            )
        agent_prompts.set_prompt(job_id, body.prompt)
    if body.guardrails is not None:
        agent_prompts.set_guardrails(job_id, body.guardrails)
    return get_job_settings(agent_id, job_id)


@router.get("/{agent_id}/knowledge-gaps")
def get_knowledge_gaps(agent_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return {
        "gaps": knowledge_gap_tracking.list_agent_gaps(agent_id),
        "open_count": knowledge_gap_tracking.count_open_gaps(agent_id),
    }


@router.post("/{agent_id}/knowledge-gaps/{gap_id}/resolve")
def resolve_knowledge_gap(agent_id: str, gap_id: str, body: GapResolveBody) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    gap = knowledge_gap_tracking.get_gap(gap_id)
    if gap is None or gap["agent_id"] != agent_id:
        raise HTTPException(status_code=404, detail="Unknown knowledge gap")
    if gap["status"] != "open":
        raise HTTPException(status_code=409, detail="Gap is already closed")
    filing_result = knowledge_gap_tracking.resolve_gap_with_human_answer(gap_id, agent_id, body.answer)
    return {"gap": knowledge_gap_tracking.get_gap(gap_id), "filing_result": filing_result}


@router.post("/{agent_id}/knowledge-gaps/{gap_id}/research")
async def research_knowledge_gap(agent_id: str, gap_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    gap = knowledge_gap_tracking.get_gap(gap_id)
    if gap is None or gap["agent_id"] != agent_id:
        raise HTTPException(status_code=404, detail="Unknown knowledge gap")
    if gap["status"] != "open":
        raise HTTPException(status_code=409, detail="Gap is already closed")
    research_result = await knowledge_gap_tracking.resolve_gap_via_research(gap_id, agent_id)
    message = {
        "written": f"Gap resolved — filed to {research_result.get('path')}.",
        "pending_approval": "Research gathered; filing paused pending approval of a new top-level vault area.",
        "no_match": f"Could not find a matching agent for the {research_result.get('hop')} step — gap remains open.",
        "no_results": "The research found nothing relevant — gap remains open.",
        "not_autonomous": f"{research_result.get('matched_agent_id')} is not in Autonomous mode — gap remains open.",
        "unavailable": research_result.get("message", "The Vault Filing Expert is not available.") + " — gap remains open.",
    }.get(research_result["status"], "The research chain completed with an unexpected status — gap remains open.")
    return {"gap": knowledge_gap_tracking.get_gap(gap_id), "research_result": research_result, "message": message}
