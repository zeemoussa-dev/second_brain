"""View-only surface for Hermes' real Agent/Skill definitions (2026-08-22).
Separate file from hermes_router.py deliberately -- that one is live
session/status data from Hermes' own API; this is Agent/Skill definitions
read from Hermes' own files, a distinct concern (flat api/ convention,
one router file per concern)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business.hermes import profile_detail, profiles

router = APIRouter(prefix="/hermes")


@router.get("/agents")
def list_agents() -> list[dict]:
    return profiles.get_all()


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = profiles.find_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"No Hermes agent named {agent_id!r}")
    return agent


@router.get("/agents/{agent_id}/profile-detail")
def get_agent_profile_detail(agent_id: str) -> dict:
    """Everything one profile really is -- soul, skills with verdicts, both
    config layers, bound cron jobs, toolsets -- in one read-only response
    (`REQ-SB-99-US-01`, `ADR-043`).

    Deliberately the expensive route: one `hermes tools list` subprocess and
    one profile's skills comparison per call, paid here because an operator
    opened it, and never on a listing path (`BUG-086`).

    404 means the profile directory genuinely does not exist on a readable
    install. An install that cannot be read is a 200 whose `install.readable`
    is false and whose every region says it was not read -- rendering that as
    "no such profile" would be the same lie as rendering it as a profile that
    holds nothing.
    """
    detail = profile_detail.read_profile_detail(agent_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No Hermes agent named {agent_id!r}")
    return detail
