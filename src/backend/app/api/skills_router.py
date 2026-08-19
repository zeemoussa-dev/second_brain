from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import agent_registry, skill_registry

router = APIRouter()


class InvokeSkillBody(BaseModel):
    query: str | None = None


def _require_known_agent(agent_id: str) -> None:
    if agent_registry.get_agent(agent_id) is None:
        raise HTTPException(status_code=404, detail="Unknown agent")


@router.get("/skills")
def list_skills() -> list[dict]:
    return skill_registry.list_skills()


@router.get("/agents/{agent_id}/skills")
def list_agent_skills(agent_id: str) -> list[dict]:
    _require_known_agent(agent_id)
    return skill_registry.list_agent_skills(agent_id)


@router.post("/agents/{agent_id}/skills/{skill_id}")
def grant_skill(agent_id: str, skill_id: str) -> dict:
    _require_known_agent(agent_id)
    if skill_id not in {s["id"] for s in skill_registry.list_skills()}:
        raise HTTPException(status_code=404, detail="Unknown skill")
    skill_registry.grant_skill_access(agent_id, skill_id)
    return {"granted": True}


@router.delete("/agents/{agent_id}/skills/{skill_id}")
def revoke_skill(agent_id: str, skill_id: str) -> dict:
    _require_known_agent(agent_id)
    skill_registry.revoke_skill_access(agent_id, skill_id)
    return {"revoked": True}


@router.post("/agents/{agent_id}/skills/{skill_id}/invoke")
def invoke_skill(agent_id: str, skill_id: str, body: InvokeSkillBody | None = None) -> dict:
    _require_known_agent(agent_id)
    args = body.model_dump(exclude_none=True) if body else None
    # trigger="direct" is hardcoded server-side, never derived from the
    # client-supplied body -- ADR-028 point 2, mirroring
    # agents_router.py::trigger_action's own hardcoded trigger="direct".
    result = skill_registry.invoke_skill(agent_id, skill_id, args, trigger="direct")
    if result.get("status") == "unknown_skill":
        raise HTTPException(status_code=404, detail="Unknown skill")
    if result.get("status") == "refused":
        raise HTTPException(status_code=403, detail=result.get("reason", "Access refused"))
    # Any other shape (honest "not yet available", or a real result once
    # a skill has a real handler) is returned as-is, 200 — never raised
    # as an error, since an honest-unavailable response is not a failure.
    return result
