---
id: REQ-SB-79-US-01-T05
title: main.py bootstrap — create both agents, retire librarian-housekeeping, create two independent schedules
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-79-US-01-T01, REQ-SB-79-US-01-T02, REQ-SB-79-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T05 — `main.py` bootstrap wiring

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines" § "Skill / grant / schedule split"; `Implementation/Architecture/ADR.md` → `ADR-058` Decision 5 (main.py bullet)

---

## Objective

Wire the app-start lifespan to idempotently create both new agents, retire `librarian-housekeeping` and remove its stale schedule, and create two independent, real, persisted schedule records — one per new `(agent_id, capability_id)` pair.

---

## Starting State → End State

**Before / Inputs:**
- `main.py`'s `lifespan` calls `ensure_librarian_agent_and_section()` then `create_or_update_schedule(agent_id="librarian-housekeeping", capability_id="run_housekeeping_pass", interval_value=6, interval_unit="hours")` on every app start.
- `T01` has added `agent_registry.retire_agent`. `T02` has renamed the bootstrap function to `ensure_librarian_agents_and_section()`. `T03` has granted both new capabilities to both new agents.

**After / Outputs:**
- `main.py`'s import updates to `ensure_librarian_agents_and_section`.
- The lifespan block becomes:

  ```python
  ensure_librarian_agents_and_section()
  agent_registry.retire_agent("librarian-housekeeping")
  agent_schedule_registry.remove_schedule("librarian-housekeeping", "run_housekeeping_pass")
  create_or_update_schedule(
      agent_id="threads-cleaning",
      capability_id="run_threads_cleaning_pass",
      interval_value=6,
      interval_unit="hours",
  )
  create_or_update_schedule(
      agent_id="company-and-partner-building",
      capability_id="run_company_partner_building_pass",
      interval_value=6,
      interval_unit="hours",
  )
  ```

  Called AFTER `capture_scheduler_lifespan` has published the live scheduler (existing ordering constraint, unchanged) and AFTER `ensure_librarian_agents_and_section()`/`T03`'s own grants exist (`create_or_update_schedule` refuses otherwise).
- `main.py` gains one new import, `from app.business import agent_registry` (or the specific `retire_agent` name), if not already imported.

---

## Files to Modify

- `src/backend/app/main.py` — lifespan block edit above.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — only if `ensure_librarian_agents_and_section`'s own rename from `T02` needs a matching import-name update here (confirm; likely already satisfied by `T02`).

---

## Constraints

- Inherits from parent story.
- **Idempotent on every app start (including `--reload`)** — `ensure_librarian_agents_and_section()` (T02, existence-checked), `retire_agent` (T01, idempotent no-op if already retired), `remove_schedule` (already idempotent/safe if absent), `create_or_update_schedule` (already replaces in place, never duplicates) — this task composes only already-idempotent primitives, introduces no new non-idempotent step.
- **Never a one-off migration script** (`MEMORY.md` — API-first, no script workarounds) — the retirement/schedule-removal must run through this same self-healing lifespan step, every start, not a standalone script.
- **Both new schedules default to the SAME 6-hour interval** `REQ-SB-72-US-01` originally chose — independently adjustable from the first tick onward, never hardcoded as permanently coupled.
- Ordering: `ensure_librarian_agents_and_section()` and the retirement/schedule-removal must run AFTER `capture_scheduler_lifespan` (existing constraint, unchanged) and the two `create_or_update_schedule` calls must run AFTER `T03`'s own grants exist (they do, unconditionally, since `_MIGRATION_GRANT_SEED` self-heals on every `_load_state()` read).

---

## Tests

**Manual verification steps:**
1. Start the real backend fresh (or restart an already-running one). Confirm no error during lifespan startup.
2. `[REQ-SB-79-US-01-AC-01]` `GET /agents` — confirm `threads-cleaning`/`company-and-partner-building` both appear, `librarian-housekeeping` does NOT appear (retired).
3. `[REQ-SB-79-US-01-AC-03]` Call `agent_schedule_registry.list_schedules()`. Confirm two real, distinct schedule records exist — one per new `(agent_id, capability_id)` pair — and the old `("librarian-housekeeping", "run_housekeeping_pass")` record is gone.
4. Restart the backend a second time. Confirm the app start is a true no-op for all of the above — no duplicate agent, no error on re-retiring, no duplicate schedule record, and (if the operator adjusted an interval between restarts) confirm the adjusted interval survives the restart rather than being silently reset to 6 hours — read `create_or_update_schedule`'s own "replaces the existing entry... never duplicates" contract to confirm this is the expected behavior BEFORE testing it.
5. Call `agent_registry.get_agent("librarian-housekeeping")` directly. Confirm it still resolves the real, original record (name/type/settings) — `retired` does not remove it from `get_agent`'s own reach.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-79-US-01-AC-01]` Real `GET /agents` shows both new agents, not the old retired one
- [ ] `[REQ-SB-79-US-01-AC-03]` Two distinct, real, persisted schedule records confirmed via `list_schedules()`
- [ ] Fresh restart is a true no-op (idempotent) across agent creation, retirement, schedule removal, schedule creation
- [ ] `get_agent("librarian-housekeeping")` still resolves the real record after retirement
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `capture_scheduler_lifespan` itself.
- The MCP-tool/Skill wrappers or POC routes — `T03`/`T04`.

---

## Context / Notes

This is the task that actually makes both new pipelines run on a real, independent, persisted schedule for the first time — the heaviest task in this story for real operational consequence, even though the code diff is small. Confirm live, don't just trust the code reads correctly.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
