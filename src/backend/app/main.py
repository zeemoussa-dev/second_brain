from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_activity_router import router as agent_activity_router
from app.api.agent_schedules_router import router as agent_schedules_router
from app.api.agents_router import router as agents_router
from app.api.cockpit_router import router as cockpit_router
from app.api.demo_taxonomy_router import router as demo_taxonomy_router
from app.api.email_poc_router import router as email_poc_router
from app.api.health_check_router import router as health_check_router
from app.api.mcp_auth import require_hermes_shared_secret
from app.api.mcp_server import mcp_server
from app.api.my_day_router import router as my_day_router
from app.api.pending_approvals_router import router as pending_approvals_router
from app.api.providers_router import router as providers_router
from app.api.sections_router import router as sections_router
from app.api.skills_router import router as skills_router
from app.api.system_health_router import router as system_health_router
from app.api.vault_index_router import router as vault_index_router
from app.api.vault_search_router import router as vault_search_router
from app.business.agent_schedule_registry import create_or_update_schedule
from app.business.pipelines.librarian_housekeeping import ensure_librarian_agent_and_section
from app.scheduling.capture_scheduler import lifespan as capture_scheduler_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A Mount()-ed Starlette sub-application's own lifespan (here,
    # mcp_server.streamable_http_app()'s `session_manager.run()`, which
    # initializes the task group its Streamable HTTP transport needs —
    # every request 500s with "Task group is not initialized" without it,
    # confirmed live during this task's own verification) is NOT invoked
    # automatically just by mounting; it must be entered explicitly
    # alongside the app's own existing capture-scheduler lifespan
    # (ADR-005), for the life of the process (ADR-015 point 7).
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp_server.session_manager.run())
        await stack.enter_async_context(capture_scheduler_lifespan(app))
        # REQ-SB-72-US-01-T08 (ADR-049 Decision 6) — one-time, idempotent
        # "Librarian" Section + librarian-housekeeping Agent bootstrap,
        # existence-checked so a repeat app start (--reload included)
        # never creates a duplicate, disambiguated agent.
        ensure_librarian_agent_and_section()
        # REQ-SB-72-US-01-T09 (ADR-049 Decision 8) — seeds the real,
        # persisted default 6-hour schedule for the Librarian's own
        # orchestrating Job. Must run AFTER the agent/skill grant above
        # exist (create_or_update_schedule refuses otherwise) and AFTER
        # capture_scheduler_lifespan has published the live scheduler
        # (above) — safe to call unconditionally on every app start, since
        # it replaces the existing entry for this (agent_id, capability_id)
        # pair in place rather than duplicating it.
        create_or_update_schedule(
            agent_id="librarian-housekeeping",
            capability_id="run_housekeeping_pass",
            interval_value=6,
            interval_unit="hours",
        )
        yield


app = FastAPI(title="Second Brain", lifespan=lifespan)

# Frontend (Vite dev server) and backend (uvicorn) run as separate
# processes on different ports — every browser-originated fetch from
# src/frontend is cross-origin without this. Scoped to the Vite dev
# server's own default bind addresses (ADR-010) rather than a wildcard,
# since this is a single-user personal-data API (REQ-SB-12-US-02, first
# task to make a real browser->backend fetch call).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        # Vite auto-increments past 5173 when it's already bound by a
        # concurrent dev-server session (REQ-SB-13-US-01 live verification,
        # 2026-08-11) — additive only, does not remove the 5173 entry above.
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_check_router)
app.include_router(email_poc_router)
app.include_router(my_day_router)
app.include_router(agents_router)
app.include_router(sections_router)
app.include_router(providers_router)
app.include_router(skills_router)
app.include_router(system_health_router)
app.include_router(pending_approvals_router)
app.include_router(vault_index_router)
app.include_router(vault_search_router)
app.include_router(agent_activity_router)
app.include_router(agent_schedules_router)
app.include_router(cockpit_router)
app.include_router(demo_taxonomy_router)

app.mount("/mcp", require_hermes_shared_secret(mcp_server.streamable_http_app()))
