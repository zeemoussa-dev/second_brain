"""Second Brain's own HTTP surface for Hermes status (2026-08-20 pivot --
see app/_archive/README.md). Replaces the archived agents_router.py/
agent_schedules_router.py/skills_router.py's own frontend-facing role for
"what agents/skills/schedules exist" with the real equivalent question
against Hermes -- honestly empty/unreachable today until a Hermes gateway
is actually deployed and configured (HERMES_BASE_URL/HERMES_API_KEY)."""
from fastapi import APIRouter

from app.business import hermes_status

router = APIRouter(prefix="/hermes")


@router.get("/health")
def get_health() -> dict:
    return hermes_status.get_health()


@router.get("/capabilities")
def get_capabilities() -> dict:
    return hermes_status.get_capabilities()


@router.get("/jobs")
def get_jobs() -> dict:
    return hermes_status.get_jobs()


@router.get("/sessions")
def get_sessions() -> dict:
    return hermes_status.get_sessions()
