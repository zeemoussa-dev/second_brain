"""Skill access: a new, persisted, user-mutable concern (ADR-014's own
pattern, one concept over) — which agents may invoke which registered
skills, independent of a skill's own catalog entry or its actual
implementation. Composed alongside app/business/skill_tools.py, not
inside it. Deliberately no self-healing default assignment — an agent
gets skill access only via an explicit grant (Scenario 2); see the
parent story's own Non-Goals for the still-open "should some skills
default to all agents" question this module does not resolve.
"""
import inspect
from typing import Literal

from app.business import agent_registry, pending_approval_registry, skill_tools, working_mode_registry
from app.data_access import vault_writer

# Dispatch table reconciled against what T02's skill_tools.py actually
# built (one @mcp.tool()-decorated function per registry entry, not a
# single generic dispatcher) -- kept local to this module rather than
# added to skill_tools.py itself, since skill_tools.py is out of this
# task's own Files to Modify. Extending with a future second skill means
# adding one entry here alongside skill_tools.SKILLS' own new entry.
_SKILL_HANDLERS = {
    "diagram-understanding": skill_tools.diagram_understanding,
    "web-research": skill_tools.web_research,
    "view_last_run": skill_tools.view_last_run,
    "ask_question": skill_tools.ask_question,
    "view_channel_status": skill_tools.view_channel_status,
    # REQ-SB-39-US-02 -- the 4 formerly-hardcoded mutating Action ids.
    "run_capture_now": skill_tools.run_capture_now,
    "pause_schedule": skill_tools.pause_schedule,
    # REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- pull_email/
    # process_staged_email, two independently-dispatched capabilities of
    # email-capture-pipeline.
    "pull_email": skill_tools.pull_email,
    "process_staged_email": skill_tools.process_staged_email,
    "rebuild_person_note": skill_tools.rebuild_person_note,
    "build_knowledge": skill_tools.build_knowledge,
    "write-to-vault-draft": skill_tools.write_to_vault_draft,
    "summarize-file": skill_tools.summarize_file,
    "propose_person_note_update": skill_tools.propose_person_note_update,
    # REQ-SB-72-US-01-T09 (ADR-049 Decision 8) -- the Librarian's own
    # orchestrating Job, dispatchable so it can carry a real, persisted
    # recurring schedule.
    "run_housekeeping_pass": skill_tools.run_housekeeping_pass,
}


# One-time, explicitly-scoped migration backfill (ADR-028 point 5) --
# grants the 4 real, already-shipped agents that carried these 3 ids as a
# hardcoded agent_registry.py Action, before this migration, the
# equivalent Skill access. This is a bounded historical fact about
# exactly these 3 already-migrated ids and 4 named agents, NOT a general
# self-healing default-assignment mechanism -- it must never grow to
# cover a future Skill without its own new mapping entry and its own new
# ADR (ADR-028's own Alternatives Considered explicitly rejects a blanket
# self-heal here). compass-expert and vault-filing-expert never carried
# these Action ids and are deliberately absent from this mapping.
_MIGRATION_GRANT_SEED = {
    "view_last_run": ["email-capture-pipeline", "meeting-capture", "todo-capture", "people-producer"],
    "ask_question": ["vault-qa"],
    "view_channel_status": ["vault-qa"],
    # REQ-SB-39-US-02 (ADR-029 point 7) -- the 4 formerly-hardcoded
    # mutating Action ids, retrofitted onto the exact 5 real agents that
    # carried them before migration (3 agents share run_capture_now +
    # pause_schedule, 2 each carry one distinct id). vault-filing-expert
    # is deliberately NOT part of any of these 4 mappings -- it never
    # carried these Action ids. "email-capture" renamed to
    # "email-capture-pipeline" (REQ-SB-55-US-01-T08, ADR-043 point 6) --
    # this seed's own job is unchanged (grant these ids to the SAME real
    # agent under its new identity), not a new migration concern.
    "run_capture_now": ["email-capture-pipeline", "meeting-capture", "todo-capture"],
    "pause_schedule": ["email-capture-pipeline", "meeting-capture", "todo-capture"],
    "rebuild_person_note": ["people-producer"],
    "build_knowledge": ["compass-expert"],
    "propose_person_note_update": ["people-producer"],
    # REQ-SB-69-US-01-T04 (ADR-046 Decision 4) -- a genuinely NEW grant,
    # not a migration backfill of an old Action id; reuses this same seed
    # dict/mechanism for consistency, and because agent_schedule_
    # registry._is_schedulable already reads granted-skill membership from
    # this same access layer (so both new capabilities become
    # independently schedulable via the already-generic per-(agent_id,
    # capability_id) schedule mechanism, with zero new plumbing).
    "pull_email": ["email-capture-pipeline"],
    "process_staged_email": ["email-capture-pipeline"],
    # REQ-SB-72-US-01-T09 (ADR-049 Decision 8) -- a genuinely NEW grant
    # (not a migration backfill), reusing this same seed dict/mechanism a
    # second time for the SAME reason pull_email/process_staged_email did
    # (T04): a new ADR (ADR-049) names the new mapping entry explicitly,
    # and self-healing the grant on every _load_state() read is what makes
    # librarian-housekeeping's own schedule survive a fresh app start.
    "run_housekeeping_pass": ["librarian-housekeeping"],
}


def _load_state() -> dict:
    state = vault_writer.load_skills_state()
    if state is None:
        state = {"assignments": {}}
        vault_writer.save_skills_state(state)
    # _preloaded_state (below) is what makes this safe to call from inside
    # _load_state() itself -- grant_skill_access's own ordinary path calls
    # _load_state(), which would otherwise recurse infinitely every time
    # this seed runs (ADR-028 point 5's own "runs on every read" framing).
    for skill_id, agent_ids in _MIGRATION_GRANT_SEED.items():
        for agent_id in agent_ids:
            grant_skill_access(agent_id, skill_id, _preloaded_state=state)
    return state


def list_skills() -> list[dict]:
    return list(skill_tools.SKILLS.values())


def list_agent_skills(agent_id: str) -> list[dict]:
    state = _load_state()
    granted_ids = state["assignments"].get(agent_id, [])
    return [skill_tools.SKILLS[sid] for sid in granted_ids if sid in skill_tools.SKILLS]


def has_skill_access(agent_id: str, skill_id: str) -> bool:
    state = _load_state()
    return skill_id in state["assignments"].get(agent_id, [])


def grant_skill_access(agent_id: str, skill_id: str, *, _preloaded_state: dict | None = None) -> bool:
    """Returns False (no-op) if agent_id or skill_id is unknown.

    `_preloaded_state` is an internal seam used only by _load_state()'s own
    migration-grant retrofit seed (T05, ADR-028 point 5), so that seed can
    reuse this exact idempotent "only append if not already granted" logic
    without re-entering _load_state() itself, which would recurse
    infinitely. Every real external caller omits it and this function loads
    state itself exactly as before."""
    if agent_registry.get_agent(agent_id) is None or skill_id not in skill_tools.SKILLS:
        return False
    state = _preloaded_state if _preloaded_state is not None else _load_state()
    granted = state["assignments"].setdefault(agent_id, [])
    if skill_id not in granted:
        granted.append(skill_id)
        vault_writer.save_skills_state(state)
    return True


def revoke_skill_access(agent_id: str, skill_id: str) -> bool:
    """Returns False if the agent did not have this skill granted (or
    agent_id is unknown); True once revoked (idempotent — revoking an
    already-ungranted skill for a known agent still returns True, mirrors
    section_registry.py's own idempotent-delete shape)."""
    if agent_registry.get_agent(agent_id) is None:
        return False
    state = _load_state()
    granted = state["assignments"].get(agent_id, [])
    if skill_id in granted:
        granted.remove(skill_id)
        vault_writer.save_skills_state(state)
    return True


def invoke_skill(
    agent_id: str,
    skill_id: str,
    args: dict | None,
    trigger: Literal["chat", "direct", "hub_routed", "scheduled", "cockpit_mention"],
) -> dict:
    """Never raises for ordinary control flow — returns a result dict the
    router (T04) translates into the right HTTP response. Checks access
    before checking whether a real handler exists, so Scenario 3's
    refusal and Scenario 4's honest-unavailable are always distinguishable
    (AC-03 vs AC-04). `args` is additive (REQ-SB-36-US-01-T05) -- every
    existing zero-arg caller (diagram-understanding) is unaffected, since
    args defaults to None and is only threaded through when given.

    `agent_id` is additionally injected into the call whenever the
    resolved handler's own signature declares an `agent_id` parameter
    (operator correction, 2026-08-12 -- web_research resolves its real
    backend from the INVOKING agent's own linked Provider, per
    provider_registry.get_agent_provider, not a hardcoded Provider id;
    see ADR-022's own Correction addendum). This is a caller-supplied
    value from invoke_skill's own already-authenticated agent_id
    parameter, never taken from the router's own request body -- a
    caller cannot spoof a different agent's Provider by passing
    "agent_id" inside the JSON body, since that key is silently
    overwritten here.

    `trigger` is required, no default -- mirrors agents_router.py's
    `_invoke_action(agent_id, action_id, trigger)`'s own "no default,
    every call site explicit" discipline (ADR-028 point 2).

    Gained the two-axis working-mode gate (REQ-SB-39-US-02, ADR-029
    point 2), inserted AFTER the access check (so an agent never granted
    a skill is still refused before any pending record could be created)
    and BEFORE dispatch -- mirrors agents_router.py::_invoke_action's own
    ADR-020 gate one layer over. This is the ONE function every real call
    site (skills_router.py's direct invoke endpoint, agents_router.py's
    dispatch fork, knowledge_bootstrap.py's Hub-routed call) already
    passes through, so centralizing the gate here makes "never a route
    around the gate" (Scenario 8) true by construction, not by caller
    discipline."""
    if skill_id not in skill_tools.SKILLS:
        return {"status": "unknown_skill"}
    if not has_skill_access(agent_id, skill_id):
        return {"status": "refused", "reason": "Agent does not have access to this skill."}

    mode = working_mode_registry.get_agent_working_mode(agent_id)

    if mode == "manual" and trigger == "hub_routed":
        return {
            "status": "refused",
            "reason": "This agent is in Manual mode — it does not act on another agent's request.",
        }

    # ADR-037 point 5 -- generalizes email_classification.py's own
    # per-capture-type "Manual skips silently, no history entry" precedent
    # to any scheduled capability, one layer over. "direct" (run now) is
    # deliberately unaffected -- a user is presently, explicitly requesting
    # it, unlike a fully-automatic tick.
    if mode == "manual" and trigger == "scheduled":
        return {
            "status": "skipped_manual",
            "reason": "This agent is in Manual mode — its scheduled runs stay dormant.",
        }

    mutates = skill_tools.SKILLS[skill_id].get("mutates", True)

    if mode == "supervised" and mutates:
        skill = skill_tools.SKILLS[skill_id]
        agent = agent_registry.get_agent(agent_id)
        agent_name = agent["name"] if agent else agent_id
        # ADR-056 (BUGFIX-08-US-01) -- generalized close for BUG-029's
        # scheduled-vs-direct race: any Supervised mutating Skill racing
        # across trigger sources for the SAME (agent_id, skill_id) decision
        # point collapses to the one already-pending record, computed here
        # so every real caller (dispatch_with_shared_lock, skills_router.py,
        # agents_router.py's dispatch fork, knowledge_bootstrap.py) is fixed
        # with zero change to any of them.
        dedupe_key = f"{agent_id}:{skill_id}"
        approval = pending_approval_registry.create_pending_approval(
            agent_id=agent_id,
            trigger=trigger,
            action_id=skill_id,
            description=f"{skill['name']} ({agent_name})",
            payload=args,
            dedupe_key=dedupe_key,
        )
        message = f"Proposed — {skill['name']}. Awaiting your approval."
        vault_writer.append_agent_history_entry(
            agent_id, "proposal", message, pending_approval_id=approval["id"],
        )
        return {"status": "pending", "message": message, "pending_approval_id": approval["id"]}

    return _dispatch_skill(agent_id, skill_id, args)


def _dispatch_skill(
    agent_id: str, skill_id: str, args: dict | None = None, *, already_approved: bool = False,
) -> dict:
    """Raw, ungated dispatch -- the exact pre-REQ-SB-39-US-02 body of
    invoke_skill, extracted unchanged (ADR-029 point 3). Called both by
    invoke_skill's own post-gate fallthrough, above, and by
    pending_approvals_router.py's Approve endpoint (REQ-SB-39-US-02-T02),
    which deliberately bypasses the gate on Approve -- the approval
    itself is the authorization; re-entering the gate would find the
    agent still Supervised and defer forever (ADR-018 point 6, mirrored
    one layer over).

    already_approved is a new, keyword-only, opt-in flag (ADR-038 point
    7, REQ-SB-49-US-02) forwarded to a handler via the SAME signature-
    introspection seam that already forwards agent_id -- a no-op for
    every handler that does not declare it (confirmed by direct reading:
    none of the 11 pre-existing handlers declare this parameter).
    pending_approvals_router.py's Approve branch passes True explicitly
    on its one call site (the ONLY real caller that ever does);
    invoke_skill's own Manual/Autonomous fallthrough (below) omits it,
    leaving it at its default False."""
    handler = _SKILL_HANDLERS[skill_id]
    call_args = dict(args) if args else {}
    if "agent_id" in inspect.signature(handler).parameters:
        call_args["agent_id"] = agent_id
    if "already_approved" in inspect.signature(handler).parameters:
        call_args["already_approved"] = already_approved
    if call_args:
        return handler(**call_args)
    return handler()


def list_agent_capabilities(agent_id: str) -> list[dict]:
    """Combines an agent's still-real Actions (agent_registry.py, filtered
    to exclude any id also present in skill_tools.SKILLS, so a migrated id
    never appears twice -- once via the raw actions array, once via
    list_agent_skills) with its granted Skills (list_agent_skills,
    including the 3 migrated read-only ones) into one uniformly-shaped
    list (ADR-028 point 6). Per-item shape: {"id": str, "label": str,
    "kind": "action" | "skill"} -- reconciles Actions' {"id","label"}
    with Skills' {"id","name","description"} (Skills' "name" becomes
    "label"; "description" is dropped from this aggregate view, still
    available via list_skills()/list_agent_skills() directly).

    Returns [] for a known agent with zero capabilities of either kind;
    propagates whatever agent_registry.get_agent returns for an unknown
    agent -- this function does not itself validate agent existence,
    callers (e.g. agents_router.py's get_agent) already do. Placed here,
    not in agent_registry.py, since this module already imports
    agent_registry (a one-directional dependency) -- the reverse would
    need agent_registry.py to import skill_registry, a layering direction
    this project has never used (ADR-028 point 6)."""
    agent = agent_registry.get_agent(agent_id)
    still_real_actions = [
        {"id": action["id"], "label": action["label"], "kind": "action"}
        for action in agent["actions"]
        if action["id"] not in skill_tools.SKILLS
    ]
    granted_skills = [
        {"id": skill["id"], "label": skill["name"], "kind": "skill", "tool": skill["tool"]}
        for skill in list_agent_skills(agent_id)
    ]
    return still_real_actions + granted_skills
