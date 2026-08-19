---
id: REQ-SB-79-US-01-T03
title: Skill/grant catalog split — run_threads_cleaning_pass / run_company_partner_building_pass
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-79-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T03 — Skill/grant catalog split

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines" § "Skill / grant / schedule split"; `Implementation/Architecture/ADR.md` → `ADR-058` Decision 5

---

## Objective

Replace the single `run_housekeeping_pass` Skill/grant entry with two independent entries, one per new orchestrator (`T02`), so each new agent identity can carry its own independently-schedulable capability.

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS["run_housekeeping_pass"]` — one catalog entry, `"mutates": True`, `"tool": "Vault"`.
- `skill_tools.run_housekeeping_pass()` — one `@mcp_server.tool()`-decorated thin wrapper delegating to `librarian_housekeeping.run_housekeeping_pass()`.
- `skill_registry._SKILL_HANDLERS["run_housekeeping_pass"] = skill_tools.run_housekeeping_pass`.
- `skill_registry._MIGRATION_GRANT_SEED["run_housekeeping_pass"] = ["librarian-housekeeping"]`.
- `T02` has replaced `librarian_housekeeping.run_housekeeping_pass()` with `run_threads_cleaning_pass()`/`run_company_partner_building_pass()`.

**After / Outputs:**
- `skill_tools.SKILLS` — the `"run_housekeeping_pass"` entry is REPLACED by two entries, `"run_threads_cleaning_pass"` and `"run_company_partner_building_pass"` (same `"mutates": True`, `"tool": "Vault"` shape; description text updated to name each pipeline's own real scope).
- `skill_tools.py` — the old `run_housekeeping_pass()` `@mcp_server.tool()` wrapper is REPLACED by two thin wrappers, each delegating to the matching new orchestrator:

  ```python
  @mcp_server.tool()
  def run_threads_cleaning_pass() -> dict:
      return librarian_housekeeping.run_threads_cleaning_pass()


  @mcp_server.tool()
  def run_company_partner_building_pass() -> dict:
      return librarian_housekeeping.run_company_partner_building_pass()
  ```

- `skill_registry._SKILL_HANDLERS` — the single `"run_housekeeping_pass"` entry is REPLACED by `"run_threads_cleaning_pass": skill_tools.run_threads_cleaning_pass` and `"run_company_partner_building_pass": skill_tools.run_company_partner_building_pass`.
- `skill_registry._MIGRATION_GRANT_SEED` — the single `"run_housekeeping_pass": ["librarian-housekeeping"]` entry is REPLACED by `"run_threads_cleaning_pass": ["threads-cleaning"]` and `"run_company_partner_building_pass": ["company-and-partner-building"]`.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — `SKILLS` dict entry replacement, two new `@mcp_server.tool()` wrappers replacing the old one.
- `src/backend/app/business/skill_registry.py` — `_SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED` entry replacement.

---

## Constraints

- Inherits from parent story.
- **Same `"mutates": True`, `"tool": "Vault"` catalog shape** — no new catalog field.
- **`_MIGRATION_GRANT_SEED` self-heals on every `_load_state()` read** (existing mechanism, unchanged) — granting both new capabilities to their respective new agent ids the moment this task's edit lands, with zero separate migration step, mirroring this seed dict's own established "reuse this same mechanism for a genuinely new grant" precedent (`pull_email`/`process_staged_email`, `run_housekeeping_pass` itself, before this split).
- Do not leave the old `"run_housekeeping_pass"` key anywhere in `SKILLS`/`_SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED` — a clean replacement, not an addition alongside it.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. Confirm `skill_tools.SKILLS` no longer has a `"run_housekeeping_pass"` key, and has both `"run_threads_cleaning_pass"`/`"run_company_partner_building_pass"` keys, each `"mutates": True`.
2. Call `skill_registry.has_skill_access("threads-cleaning", "run_threads_cleaning_pass")`. Confirm `True` (the `_MIGRATION_GRANT_SEED` self-heal grants it on read). Same for `"company-and-partner-building"`/`"run_company_partner_building_pass"`.
3. `[REQ-SB-79-US-01-AC-03]` Call `agent_schedule_registry._is_schedulable("threads-cleaning", "run_threads_cleaning_pass")` and the Company-and-Partner-Building equivalent. Confirm both return `True` — the real precondition `create_or_update_schedule` (`T05`) needs to succeed.
4. Call `skill_registry.list_agent_skills("threads-cleaning")` and confirm the new Skill's own catalog entry (name/description) appears; same for the other agent/skill pair.
5. Dispatch each new Skill directly (`skill_registry._dispatch_skill` or the real `@mcp_server.tool()` call) and confirm it delegates correctly to `T02`'s own `run_threads_cleaning_pass()`/`run_company_partner_building_pass()`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `SKILLS`/`_SKILL_HANDLERS`/`_MIGRATION_GRANT_SEED` all cleanly replaced, no leftover `run_housekeeping_pass` key
- [ ] `[REQ-SB-79-US-01-AC-03]` Both new capabilities confirmed schedulable (`_is_schedulable` returns `True`) as a precondition for `T05`
- [ ] Both new `@mcp_server.tool()` wrappers dispatch correctly to `T02`'s own orchestrators
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually creating the persisted schedule records — `T05`'s own scope (this task only makes both capabilities schedulable).
- `agent_registry.py`/`librarian_housekeeping.py` — untouched by this task.

---

## Context / Notes

`skill_tools.py`'s own stale docstring comment (around the old `run_housekeeping_pass()` function, naming `librarian-housekeeping` as "the one real Agent identity that can ever be granted it") no longer holds once this task lands — update or remove it as part of this same edit, since it directly documents the function this task replaces.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
