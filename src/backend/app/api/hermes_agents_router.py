"""View-only surface for Hermes' real Agent/Skill definitions (2026-08-22).
Separate file from hermes_router.py deliberately -- that one is live
session/status data from Hermes' own API; this is Agent/Skill definitions
read from Hermes' own files, a distinct concern (flat api/ convention,
one router file per concern)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business.hermes import definitions

router = APIRouter(prefix="/hermes")


@router.get("/agents")
def list_agents() -> list[dict]:
    return definitions.list_agents()


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = definitions.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"No Hermes agent named {agent_id!r}")
    return agent
