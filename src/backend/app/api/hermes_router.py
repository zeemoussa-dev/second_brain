"""Second Brain's own HTTP surface for Hermes status (2026-08-20 pivot --
see app/_archive/README.md). Rebuilt 2026-08-20 to match hermes_status.py's
real, verified functions. Extended 2026-08-22 with real cron job/schedule/
run-history/log reads (hermes_cron_status.py) -- operator: "Reading Corn
Jobs and Their Schedule, Server Status... Details Log so we can link and
know what happened". Real two-way chat (app/hermes/chat_session.py) is wired
through agents_router.py's existing POST /agents/{id}/chat instead of a
dedicated WS route here -- see that router's own docstring (2026-08-23,
ADR-006) for why: the standalone chat widget this router used to proxy
was removed in favor of the pre-existing per-agent Chat tab in
AgentDetailPanel.tsx, which is REST request/response, not WS.
/sessions gained real limit/offset query params 2026-08-23 for the Agent
Activity page's own real Hermes session log (operator: "the Agents
Activities Tab should get the Agents Log from Hermes")."""
from fastapi import APIRouter, HTTPException

from app.business.hermes import cron_status as hermes_cron_status, status as hermes_status

router = APIRouter(prefix="/hermes")


@router.get("/status")
def get_status() -> dict:
    return hermes_status.get_status()


@router.get("/sessions")
def get_sessions(limit: int = 50, offset: int = 0, profile: str | None = None) -> dict:
    return hermes_status.get_sessions(limit=limit, offset=offset, profile=profile)


@router.get("/sessions/stats")
def get_session_stats() -> dict:
    return hermes_status.get_session_stats()


@router.get("/cron/jobs")
def list_cron_jobs() -> list[dict]:
    return hermes_cron_status.list_cron_jobs()


@router.get("/cron/jobs/{job_id}/runs")
def list_cron_job_runs(job_id: str, limit: int = 20) -> list[dict]:
    runs = hermes_cron_status.list_cron_executions(job_id, limit=limit)
    if runs is None:
        raise HTTPException(status_code=404, detail=f"No cron job '{job_id}'")
    return runs


@router.get("/cron/jobs/{job_id}/runs/{execution_id}/detail")
def get_cron_run_detail(job_id: str, execution_id: str) -> dict:
    detail = hermes_cron_status.get_execution_detail(job_id, execution_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No run '{execution_id}' for cron job '{job_id}'")
    return detail
