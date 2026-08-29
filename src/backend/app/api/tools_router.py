"""Real Hermes toolset catalog (2026-08-29, Tools picker) -- agent-
independent (every real profile shares the same fixed catalog; only
enabled/disabled state varies per profile, which the Agent detail
response already carries via `Agent.tools`). Mirrors skills_router.py's
own `/skills` catalog shape."""
from __future__ import annotations

from fastapi import APIRouter

from app.business.core.agents.agent_manager import AgentManager

router = APIRouter(prefix="")
_agent_manager = AgentManager()


@router.get("/tools")
def list_tool_catalog() -> list[str]:
    return _agent_manager.list_tool_catalog()
