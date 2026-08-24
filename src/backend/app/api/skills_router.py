"""Agents Map's real /skills surface (2026-08-22 retrofit) -- fresh,
view-only, over the Hermes mirror (ADR-003). Same URL surface the
frontend already calls (skillsApiClient.ts). No grant/revoke endpoints --
Skill assignment for a Hermes agent happens by editing its real profile
(outside this backend entirely), never through a UI action here."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
