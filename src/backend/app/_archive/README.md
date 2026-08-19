# Archive

Retired code, moved here rather than deleted (archive-never-delete —
`MEMORY.md`). Nothing under this directory is imported by the live app.

## api/ — orchestration-layer HTTP routers (archived 2026-08-20)

`agents_router.py`, `agent_schedules_router.py`, `agent_activity_router.py`,
`cockpit_router.py`, `demo_taxonomy_router.py`, `pending_approvals_router.py`,
`providers_router.py`, `sections_router.py`, `skills_router.py`.

**Why:** REQ-SB-79 follow-up — the operator decided Hermes replaces Second
Brain's own hand-built Agent/Skill/Schedule/Approval orchestration layer
(see `MEMORY.md` "Decisions", 2026-08-20). These 9 routers were the HTTP
surface for that layer (Agents Map, Cockpit, Skills Tree, the agent-creation
wizard, Pending Approvals UI). No other backend module imports a router
file (routers are leaf nodes, only ever `include_router`-ed by `main.py`),
so removing their `main.py` registration is safe and self-contained —
confirmed by grep before moving, not assumed.

**Deliberately NOT archived alongside them** (real, live dependents found
by tracing actual imports, not by the original file-list alone): the
underlying business-layer registries these routers called into —
`agent_registry.py`, `agent_schedule_registry.py`, `skill_registry.py`,
`skill_tools.py`, `pending_approval_registry.py`, `working_mode_registry.py`,
`provider_registry.py`, `section_registry.py`, `scope_registry.py` /
`scope_query_tools.py`, `agent_prompts.py`, `agent_orchestration/`,
`cockpit/` (the business package, as opposed to the archived router) —
because real, currently-live KEEP code still depends on them:
`capture_scheduler.py`'s hourly Outlook pull (shared dispatch lock +
per-agent schedule iteration), `mcp_server.py`'s tool registration chain
(`main.py` → `agent_schedule_registry` → `skill_tools` → the `@mcp_server.
tool()` decorators that make `rename_threads`/`link_thread_messages`/
`backfill_thread_summaries` reachable at all), `vault_write_tools.py`'s
write-approval safety gate (`propose_vault_write` always creates a Pending
Approval — this is the one thing currently stopping a Hermes-triggered
write from landing unreviewed), `system_health.py`, `librarian_
housekeeping.py`'s Company Review pipeline (which has real, live, unresolved
Pending Approvals awaiting the operator's own review right now), and
`thread_summary_backfill.py`/`todo_classification.py`'s prompt-override
reads.

Fully separating this business layer requires resolving an explicitly
open, operator-deferred question: does Hermes' own run-approval mechanism
replace `pending_approval_registry.py`/`working_mode_registry.py`
outright, or does Second Brain keep its own gate for vault writes
regardless of trigger source? Attempting that split without an answer
risked breaking live Outlook capture or the write-approval gate while
unsupervised — see `Implementation/Tasks` follow-up task tracking this
(frontend scope + the remaining business-layer split are still open).
