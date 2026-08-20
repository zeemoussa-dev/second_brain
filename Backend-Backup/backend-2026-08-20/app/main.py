import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.business import agent_registry, agent_schedule_registry
from app.api.email_poc_router import router as email_poc_router
from app.api.health_check_router import router as health_check_router
from app.api.hermes_router import router as hermes_router
from app.api.mcp_auth import require_hermes_shared_secret
from app.api.mcp_server import mcp_server
from app.api.my_day_router import router as my_day_router
from app.api.system_health_router import router as system_health_router
from app.api.vault_index_router import router as vault_index_router
from app.api.vault_search_router import router as vault_search_router
from app.business.pipelines.librarian_housekeeping import ensure_librarian_agents_and_section
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
        # REQ-SB-79-US-01 (ADR-058 Decision 5) — one-time, idempotent
        # "Librarian" Section + its two now-independent Agent identities'
        # bootstrap (replaces the former single librarian-housekeeping
        # bootstrap, REQ-SB-72-US-01-T08/ADR-049 Decision 6), existence-
        # checked per agent so a repeat app start (--reload included)
        # never creates a duplicate, disambiguated agent. Also idempotently
        # retires the old librarian-housekeeping identity and removes its
        # own now-stale schedule entry — a real, self-healing startup step,
        # never a one-off migration script.
        ensure_librarian_agents_and_section()
        agent_registry.retire_agent("librarian-housekeeping")
        agent_schedule_registry.remove_schedule("librarian-housekeeping", "run_housekeeping_pass")
        # 2026-08-20 (operator-directed): run_threads_cleaning_pass retired
        # as a Skill — Threads Cleaning's own 3 real Jobs (rename_threads,
        # link_thread_messages, backfill_thread_summaries) are now granted
        # to their own real Sub-Agents instead of one monolithic scheduled
        # pass on threads-cleaning itself. Idempotently removes any stale
        # schedule entry left over from before this change, self-healing,
        # mirroring librarian-housekeeping's own retirement above — never a
        # one-off migration script.
        agent_schedule_registry.remove_schedule("threads-cleaning", "run_threads_cleaning_pass")
        # 2026-08-20 (operator-directed, "we are building a framework this
        # is not acceptable" -- re: hand-writing a new create_or_update_
        # schedule call + comment block here for every new default
        # schedule): every default/bootstrap schedule this app ships with
        # (company-and-partner-building's 6-hour pass, rename-threads' and
        # link-thread-messages' 2-hour passes, today) lives in ONE
        # declarative file, app/scheduling/default_schedules.json — never
        # hand-written here. apply_default_schedules() idempotently
        # creates/replaces every one of them (safe on every app start,
        # --reload included) and returns only the entries marked
        # "run_on_app_start": true, in file order.
        #
        # Those are then dispatched once, SEQUENTIALLY in that same file
        # order (an IntervalTrigger schedule does not fire on
        # registration, only at its first real interval boundary — a
        # plain create_or_update_schedule call alone would never satisfy
        # "and when the App Start[s]"; confirmed by direct reading of
        # agent_schedule_registry._register_live_job). Sequential, not
        # independent asyncio.create_task calls per entry, because a
        # later entry may have a real depends_on edge onto an earlier one
        # (link-thread-messages -> rename-threads, agent_registry.py) and
        # must see that earlier Job's own already-finished output —
        # firing them independently would let them race for the shared
        # dispatch lock, and whichever lost would silently skip its
        # app-start run every single restart, not just occasionally.
        # Scheduled as ONE background task, never awaited here — mirrors
        # capture_scheduler.py's own lifespan's identical "never awaited,
        # or FastAPI's own 'application startup complete' (and therefore
        # all HTTP traffic) blocks on this finishing first" reasoning.
        # dispatch_with_shared_lock's own lock-skip logic still protects
        # this sequence against colliding with a real, in-progress
        # Outlook capture run.
        on_start_entries = agent_schedule_registry.apply_default_schedules()

        async def _run_on_app_start_schedules() -> None:
            for entry in on_start_entries:
                await agent_schedule_registry.dispatch_with_shared_lock(
                    entry["agent_id"], entry["capability_id"], trigger="scheduled",
                )

        asyncio.create_task(_run_on_app_start_schedules())
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
app.include_router(system_health_router)
app.include_router(vault_index_router)
app.include_router(vault_search_router)
app.include_router(hermes_router)

app.mount("/mcp", require_hermes_shared_secret(mcp_server.streamable_http_app()))
