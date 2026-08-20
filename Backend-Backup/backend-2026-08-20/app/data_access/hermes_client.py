"""Client for Hermes' own REST API gateway
(https://github.com/nousresearch/hermes-agent) -- the real, documented
`hermes gateway` server (default `127.0.0.1:8642`, `Authorization: Bearer
<key>`), Second Brain's own agent/skill/schedule/approval runtime as of the
2026-08-20 architecture pivot (`MEMORY.md` "Decisions"). Mirrors compass_
client.py's own shape: plain httpx over a documented HTTP API, no SDK.

No Hermes gateway is deployed yet -- every call here can fail with a
connection error today, by design (`HermesUnavailableError` wraps that
honestly rather than crashing the caller), until a real instance is
configured via `HERMES_BASE_URL`/`HERMES_API_KEY`."""
from __future__ import annotations

import httpx

from app.config import settings


class HermesUnavailableError(Exception):
    """Hermes' gateway did not respond, or responded with an error -- never
    raised for "the feature doesn't exist yet"; only for a real, attempted
    call that failed."""


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.hermes_api_key:
        headers["Authorization"] = f"Bearer {settings.hermes_api_key}"
    return headers


def _request(method: str, path: str, **kwargs) -> dict:
    url = f"{settings.hermes_base_url.rstrip('/')}{path}"
    try:
        response = httpx.request(method, url, headers=_headers(), timeout=30.0, **kwargs)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HermesUnavailableError(f"Hermes call failed ({method} {path}): {exc}") from exc
    if not response.content:
        return {}
    return response.json()


def health() -> dict:
    """GET /health -- the cheapest real signal of whether a Hermes gateway
    is reachable at all. Callers wanting the fuller diagnostic should call
    detailed_health() instead."""
    return _request("GET", "/health")


def detailed_health() -> dict:
    """GET /health/detailed."""
    return _request("GET", "/health/detailed")


def list_capabilities() -> dict:
    """GET /v1/capabilities -- what this Hermes instance actually supports
    (models, tools, skill/job features enabled). The nearest real
    replacement for the archived agents_router's own "what agent types/
    skills exist" surface."""
    return _request("GET", "/v1/capabilities")


def list_models() -> dict:
    """GET /v1/models."""
    return _request("GET", "/v1/models")


def list_jobs() -> dict:
    """GET /api/jobs -- Hermes' own cron/scheduled-job registry, the real
    replacement for the archived agent_schedules_router.py's surface."""
    return _request("GET", "/api/jobs")


def create_job(spec: dict) -> dict:
    """POST /api/jobs."""
    return _request("POST", "/api/jobs", json=spec)


def run_job_now(job_id: str) -> dict:
    """POST /api/jobs/{job_id}/run."""
    return _request("POST", f"/api/jobs/{job_id}/run")


def pause_job(job_id: str) -> dict:
    """POST /api/jobs/{job_id}/pause."""
    return _request("POST", f"/api/jobs/{job_id}/pause")


def resume_job(job_id: str) -> dict:
    """POST /api/jobs/{job_id}/resume."""
    return _request("POST", f"/api/jobs/{job_id}/resume")


def list_sessions() -> dict:
    """GET /api/sessions -- the real replacement for the archived
    agents_router.py's own agent-chat surface (cockpit_router.py's
    person/research chat flows, agent_chat.py)."""
    return _request("GET", "/api/sessions")


def create_session(spec: dict | None = None) -> dict:
    """POST /api/sessions."""
    return _request("POST", "/api/sessions", json=spec or {})


def send_chat_message(session_id: str, message: str) -> dict:
    """POST /api/sessions/{session_id}/chat (non-streaming). Streaming
    (/chat/stream, SSE) is not wrapped here -- no caller needs it yet."""
    return _request("POST", f"/api/sessions/{session_id}/chat", json={"message": message})


def list_skills() -> dict:
    """GET /v1/skills -- Hermes' own Skill registry, the real replacement
    for the archived skill_registry.py/skills_router.py's HTTP surface.
    Second Brain's own MCP-registered tools (app/api/mcp_server.py) are
    what a Hermes Skill would actually call INTO -- this lists Hermes'
    side of that boundary, not Second Brain's."""
    return _request("GET", "/v1/skills")
