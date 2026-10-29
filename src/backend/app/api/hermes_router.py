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
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth_guard import requires
from app.business.core.users.user import Capability

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


@router.get("/sessions/search")
def search_sessions(q: str, limit: int = 50) -> dict:
    """Declared BEFORE /sessions/{session_id} on purpose: FastAPI matches
    in declaration order, so the dynamic route would otherwise swallow
    "search" as a session id."""
    return hermes_status.search_sessions(q, limit=limit)


@router.get("/sessions/{session_id}/transcript")
def get_session_transcript(session_id: str, limit: int = 200, offset: int = 0) -> dict:
    """REQ-SB-100 -- what the agent was told, what it decided, which
    tools it called with what arguments, and what each answered."""
    return hermes_status.get_session_transcript(session_id, limit=limit, offset=offset)


@router.get("/flow-map")
def get_flow_map() -> dict:
    """REQ-SB-102 -- entry points, the agents behind them, where each
    routes, what each may call, and every gap found on the way."""
    return hermes_status.get_flow_map()


@router.get("/entry-points")
def get_entry_points(scan: int = 400) -> dict:
    """REQ-SB-102 -- which outside doors reach which agent, as the
    operator declared it and as the traffic actually shows."""
    return hermes_status.get_entry_points(scan=scan)


@router.put("/entry-points")
def set_entry_points(
    body: list[dict],
    _: object = Depends(requires(Capability.MANAGE_HERMES)),
) -> dict:
    """Declaring which agent a door should reach is configuring the
    install, so it needs MANAGE_HERMES. Reading it does not."""
    return hermes_status.set_entry_points(body)


@router.put("/agents/{agent_id}/routing-conditions")
def set_routing_conditions(
    agent_id: str,
    body: dict[str, str],
    _: object = Depends(requires(Capability.MANAGE_AGENTS)),
) -> dict:
    """The `when` on each of this agent's specialist edges.

    Saved here only -- it does NOT rewrite the agent's soul. Publishing
    is a separate, explicit act (`POST /agents/{id}/regenerate-specialists`,
    which already exists and is deliberately manual) because a prompt
    change is a behaviour change on a live agent, and 43 of them should
    not move because someone typed in a form.
    """
    from app.data_access import routing_conditions as routing_conditions_data

    everything = routing_conditions_data.read_all()
    everything[agent_id] = {k: v for k, v in body.items() if (v or "").strip()}
    routing_conditions_data.write_all(everything)
    return everything.get(agent_id, {})


@router.get("/cron/jobs")
def list_cron_jobs() -> list[dict]:
    return hermes_cron_status.list_cron_jobs()


# The Crawlers screen reads this rather than `/cron/jobs` above, which
# is left exactly as it was: it is Hermes' own job list and other
# callers rely on that shape. This one composes the same jobs with what
# Hermes' client drops and with the operator's own labels.
@router.get("/crawlers")
def list_crawlers() -> dict:
    """Every cron job, with what defines it, what the operator calls it
    and how they grouped it (`REQ-SB-102`)."""
    from app.business.hermes import crawlers as crawlers_logic

    return crawlers_logic.list_crawlers()


class CrawlerAnnotationBody(BaseModel):
    """A label, never the job. Hermes keeps the schedule and the work;
    this is only what to call it and how to group it, and clearing both
    removes the annotation rather than storing an empty one."""
    friendly_name: str = ""
    tags: list[str] = []


@router.put("/crawlers/{job_id}/annotation")
def set_crawler_annotation(
    job_id: str,
    body: CrawlerAnnotationBody,
    _: object = Depends(requires(Capability.MANAGE_HERMES)),
) -> dict:
    """Naming and grouping crawlers is configuring this install, so it
    needs MANAGE_HERMES -- the same bar as declaring which agent a door
    reaches. Reading them does not.

    The job id is NOT checked against the live list: Hermes may be
    unreachable at the moment someone fixes a typo in a name, and
    refusing then would make a label depend on a service that has
    nothing to do with it. An annotation for a job that no longer
    exists is inert -- nothing reads it until a job of that id does.
    """
    from app.business.hermes import crawlers as crawlers_logic

    return crawlers_logic.set_annotation(job_id, body.friendly_name, body.tags)


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
