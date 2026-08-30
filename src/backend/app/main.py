import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.business.core.vault.vault_manager import VaultManager
from app.api.agents_router import router as agents_router
from app.api.boot_router import router as boot_router
from app.api.cockpit_router import router as cockpit_router
from app.api.health_check_router import router as health_check_router
from app.api.hermes_agents_router import router as hermes_agents_router
from app.api.hermes_router import router as hermes_router
from app.api.index_router import router as index_router
from app.api.my_day_router import router as my_day_router
from app.api.pipelines_router import router as pipelines_router
from app.api.sections_router import router as sections_router
from app.api.skills_router import router as skills_router
from app.api.settings_system_router import router as settings_system_router
from app.api.system_health_router import router as system_health_router
from app.api.tools_router import router as tools_router
from app.api.vault_index_router import router as vault_index_router
from app.api.vault_router import router as vault_router
from app.api.vault_search_router import router as vault_search_router
from app.config import settings
from app.data_access.registry import loader as registry_loader
from app.data_access.system.tools import registry as tools_registry

# capture_scheduler's own `lifespan` is deliberately NOT imported/entered
# below anymore (2026-08-24, operator: "something keeps creating log
# capture and index files in adnoc as a customer even that we stopped
# doing this a while back") -- the 2026-08-22 retirement pass just below
# (operator: "we're fully on Hermes now") correctly retired the old
# Second-Brain-native AGENT bootstrap, but missed this separate piece: a
# real, still-running scheduler that fires the OLD, pre-Hermes-pivot
# Outlook-COM email pipeline (email_classification.py) unconditionally on
# every app start plus hourly -- confirmed live as the real source of
# customer_hub_linking.ensure_customer_hub_note's own OKF baseline files
# (index.md/log.md/captures.md) reappearing under Work/Customers/Adnoc/
# minutes after a routine backend restart, well after email capture
# itself moved wholesale to Hermes' own email-thread-capture Skill (see
# MEMORY.md's own 2026-08-24 "Work/Emails/ no longer exists" entry).
# capture_scheduler.py itself is left in place, unused, rather than
# deleted -- same precedent librarian_housekeeping.py's own now-orphaned
# bootstrap function already set two lines below.


_vault_manager = VaultManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A Mount()-ed Starlette sub-application's own lifespan (here, every
    # Tool server mount_all_tools() already registered at module level
    # below) needs its own session_manager.run() entered explicitly --
    # it is NOT invoked automatically just by mounting, alongside the
    # app's own existing capture-scheduler lifespan (ADR-005), for the
    # life of the process (ADR-015 point 7). Confirmed live, 2026-08-20:
    # /mcp/outlook 404'd until this was added.
    async with AsyncExitStack() as stack:
        await tools_registry.enter_tool_server_lifespans(stack)
        # REQ-SB-80 -- RegistryLoader's cold boot + hot-reload poll loop.
        # Background task, never awaited (same "don't block 'application
        # startup complete'" reasoning as every other fire-and-forget task
        # in this lifespan) -- GET /boot-status is servable from the
        # instant the app accepts connections, so BootScreen can show real
        # "in_progress" stages instead of a blank screen while this runs.
        asyncio.create_task(registry_loader.boot_and_watch())
        # 2026-08-22 (operator-directed, "we're fully on Hermes now"): the
        # old Second-Brain-native Agent orchestration layer (the Librarian
        # bootstrap included) is retired -- ADR-001 already named Hermes as
        # the real agent/skill/schedule runtime going forward, and ADR-003
        # is the new, live, read-only mirror of Hermes' own real Agent/Skill
        # definitions (app/hermes/definitions.py). The former
        # bootstrap call here (ensure_librarian_agents_and_section, plus its
        # own librarian-housekeeping/threads-cleaning retire/schedule-
        # removal calls) is deliberately no longer invoked -- agent_
        # registry.py's own _SEED_AGENTS is now empty and .second-brain/
        # agents_registry.json's created_agents was cleared to match;
        # re-adding this call would just recreate the two agents that were
        # just removed. The function itself is left in librarian_
        # housekeeping.py, unused, rather than deleted, since nothing else
        # calls it and removing it isn't needed to stop the recreation.
        # 2026-08-27 (operator: "we're fully agentic now"): the
        # Second-Brain-native default-schedules dispatcher
        # (agent_schedule_registry.py, app/scheduling/default_schedules.json)
        # is retired -- Hermes owns all scheduling/dispatch natively now,
        # nothing left here to fire on app start.
        # 2026-08-23 (operator: "The Vault Browser page shows the wrong
        # notes then when I refresh it is showing no notes") --
        # vault_indexing.py's own index is a plain module-level dict, no
        # disk persistence at all (ADR-024's own explicit "no .second-
        # brain/ persistence, no database this pass" tradeoff) -- every
        # backend restart (a real, frequent event in dev, `--reload`
        # included) silently wiped it back to empty, with nothing left to
        # rebuild it automatically; GET /vault-search/status's own
        # `indexed: false` then made the WHOLE browse/search page show
        # its honest-but-blank "Nothing indexed yet" state until a human
        # remembered to call POST /vault-index/rebuild by hand. Rebuilds
        # eagerly on every start instead -- background task (never
        # awaited, same "don't block 'application startup complete'"
        # reasoning as the schedule dispatch above), `asyncio.to_thread`
        # since `rebuild_index()` itself is a synchronous, blocking,
        # read-heavy full-vault scan (confirmed live: ~1,126 notes,
        # comfortably sub-second) that would otherwise tie up the event
        # loop for its own duration if awaited directly on it.
        asyncio.create_task(asyncio.to_thread(_vault_manager.rebuild_index))
        yield


app = FastAPI(title="Second Brain", lifespan=lifespan)

# Frontend (Vite dev server) and backend (uvicorn) run as separate
# processes on different ports — every browser-originated fetch from
# src/frontend is cross-origin without this. Scoped to real origins
# (ADR-010) rather than a wildcard, since this is a single-user
# personal-data API (REQ-SB-12-US-02, first task to make a real
# browser->backend fetch call). Sourced from settings.cors_allowed_origins
# (System settings page, 2026-08-27) instead of hardcoded here — default
# still matches the two Vite dev ports this repo ships with.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_check_router)
app.include_router(boot_router)
app.include_router(cockpit_router)
app.include_router(my_day_router)
app.include_router(system_health_router)
app.include_router(vault_index_router)
app.include_router(vault_search_router)
app.include_router(hermes_router)
app.include_router(hermes_agents_router)
app.include_router(sections_router)
app.include_router(settings_system_router)
app.include_router(vault_router)
app.include_router(agents_router)
app.include_router(pipelines_router)
app.include_router(skills_router)
app.include_router(tools_router)
app.include_router(index_router)

# 2026-08-20 architecture pass -- Tools registry (data_access/system/
# tools/): mounts every declared Tool's own MCP server at its own
# mount_path (e.g. /mcp/outlook), called here at module level (NOT inside
# the async lifespan above) -- Starlette's routing table needs every
# mount registered before the app starts serving, not added mid-startup.
# Idempotent/additive-only by construction (registry.py's own
# _mounted_tool_ids tracking); a genuinely empty registry.json mounts
# nothing, real, tested behavior, not a theoretical no-op.
tools_registry.mount_all_tools(app)
