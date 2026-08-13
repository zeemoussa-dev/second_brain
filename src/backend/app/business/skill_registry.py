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

from app.business import agent_registry, skill_tools
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
}


def _load_state() -> dict:
    state = vault_writer.load_skills_state()
    if state is None:
        state = {"assignments": {}}
        vault_writer.save_skills_state(state)
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


def grant_skill_access(agent_id: str, skill_id: str) -> bool:
    """Returns False (no-op) if agent_id or skill_id is unknown."""
    if agent_registry.get_agent(agent_id) is None or skill_id not in skill_tools.SKILLS:
        return False
    state = _load_state()
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


def invoke_skill(agent_id: str, skill_id: str, args: dict | None = None) -> dict:
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
    overwritten here."""
    if skill_id not in skill_tools.SKILLS:
        return {"status": "unknown_skill"}
    if not has_skill_access(agent_id, skill_id):
        return {"status": "refused", "reason": "Agent does not have access to this skill."}
    handler = _SKILL_HANDLERS[skill_id]
    call_args = dict(args) if args else {}
    if "agent_id" in inspect.signature(handler).parameters:
        call_args["agent_id"] = agent_id
    if call_args:
        return handler(**call_args)
    return handler()
