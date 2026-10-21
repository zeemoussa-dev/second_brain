"""Agents Map's real /skills surface (2026-08-22 retrofit), over the
Hermes mirror (ADR-003). Same URL surface the frontend already calls
(skillsApiClient.ts).

**It was view-only until 2026-10-21, and that is no longer true.** This
docstring used to say "No grant/revoke endpoints -- Skill assignment for
a Hermes agent happens by editing its real profile (outside this backend
entirely), never through a UI action here." That was written when
nothing in this app could deploy a Skill. `SkillManager.deploy` and
`undeploy` arrived with `REQ-SB-96` and were never exposed, so the
operator could SEE what was deployed to an agent and still had to leave
the app to change it. `REQ-SB-102` asked for assignment from the flow
screens, so the two routes at the bottom of this file now wire the
Manager that already existed.

The reads stay what they were. The writes go through `SkillManager`,
which owns what deploying means -- shared managers refreshed, nothing
bundled that would shadow them -- and this router adds no rules of its
own beyond who may call it."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth_guard import requires
from app.business.core.skills.skill_manager import SkillManager, SkillPreconditionError
from app.business.core.users.user import Capability

from app.business.hermes import agents_map_adapter

router = APIRouter(prefix="")


@router.get("/skills")
def list_skills() -> list[dict]:
    return agents_map_adapter.list_all_skill_summaries()


@router.get("/agents/{agent_id}/skills")
def list_agent_skills(agent_id: str) -> list[dict]:
    skills = agents_map_adapter.list_agent_skill_summaries(agent_id)
    if skills is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id!r}")
    return skills


@router.post("/agents/{agent_id}/skills/{skill_id}", status_code=201)
def deploy_skill_to_agent(
    agent_id: str,
    skill_id: str,
    _: object = Depends(requires(Capability.MANAGE_AGENTS)),
) -> dict:
    """Push one Skill's current content into one agent's real Hermes
    profile (`REQ-SB-102`).

    `SkillManager.deploy` has existed since `REQ-SB-96` and nothing has
    ever exposed it over HTTP -- the operator could see what was
    deployed and never change it from the app. This is that route.

    Deploying is idempotent in the Manager: a Skill already on this
    profile returns None rather than being written twice, which is
    reported here as "already there" rather than as a failure, because
    the caller's intent (this Skill should be on this agent) is
    satisfied either way.
    """
    manager = SkillManager()
    if manager.get_by_id(skill_id) is None:
        raise HTTPException(status_code=404, detail=f"There is no skill {skill_id!r}.")
    try:
        deployed = manager.deploy(skill_id, agent_id)
    except SkillPreconditionError as exc:
        # The Manager refuses with a sentence naming what is missing --
        # a precondition is the operator's to fix, not a server fault.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "skill_id": skill_id,
        "agent_id": agent_id,
        "deployed": deployed is not None,
        "detail": (
            f"{skill_id!r} is now deployed to {agent_id!r}."
            if deployed is not None
            else f"{skill_id!r} was already deployed to {agent_id!r}; nothing changed."
        ),
    }


@router.delete("/agents/{agent_id}/skills/{skill_id}")
def undeploy_skill_from_agent(
    agent_id: str,
    skill_id: str,
    _: object = Depends(requires(Capability.MANAGE_AGENTS)),
) -> dict:
    """Remove one Skill from one agent's profile. Removing something
    that is not there is reported, not refused: the end state the
    caller asked for is the end state they get."""
    manager = SkillManager()
    removed = manager.undeploy(skill_id, agent_id)
    return {
        "skill_id": skill_id,
        "agent_id": agent_id,
        "removed": removed is not None,
        "detail": (
            f"{skill_id!r} is no longer deployed to {agent_id!r}."
            if removed is not None
            else f"{skill_id!r} was not deployed to {agent_id!r}; nothing changed."
        ),
    }
