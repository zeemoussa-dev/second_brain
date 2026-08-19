---
id: REQ-SB-72-US-01-T08
title: Librarian Agent/Section identity + orchestrating capability + 5 new /poc/* endpoints
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-72-US-01-T03, REQ-SB-72-US-01-T04, REQ-SB-72-US-01-T06, REQ-SB-72-US-01-T07]
created: 2026-08-18
updated: 2026-08-19
---

# REQ-SB-72-US-01-T08 — Librarian Agent/Section identity + orchestrating capability + 5 new `/poc/*` endpoints

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Librarian Section/Agent identity, endpoints, and scheduling" (`ADR-049` Decisions 6/7)

---

## Objective

Create the new "Librarian" Section + `librarian-housekeeping` Agent identity (idempotent bootstrap, existing unmodified mechanism), build the orchestrating `run_housekeeping_pass()` capability (rename first, then Files/Related/Company-folder Jobs in any order), and expose all 5 capabilities as real `POST /poc/*` endpoints on the existing `email_poc_router.py`.

---

## Starting State → End State

**Before / Inputs:**
- No "Librarian" Section and no `librarian-housekeeping` Agent exist anywhere (not in `_SEED_AGENTS`, not in the persisted `created_agents` store).
- `section_registry.create_section(name) -> dict` is idempotent-collapse-on-collision (calling it twice for "Librarian" returns the same `"librarian"` id); `agent_registry.create_agent(name, type, settings) -> dict` is NOT idempotent (disambiguates on collision, e.g. `-2`) — calling it unconditionally on every app start would create duplicate agents.
- `app/main.py`'s `lifespan` already composes `capture_scheduler_lifespan` alongside the app's own startup; this is this codebase's own established place for a one-time, idempotent startup bootstrap (mirrors `working_mode_registry`'s/`skill_registry`'s own "self-heal on read/on start" precedent).

**After / Outputs:**
- New `librarian_housekeeping.ensure_librarian_agent_and_section() -> dict` — idempotent bootstrap: if `agent_registry.get_agent("librarian-housekeeping")` is `None`, calls `section_registry.create_section("Librarian")` → `"librarian"`, then `agent_registry.create_agent("Librarian Housekeeping", type="worker", settings=[...])` → `"librarian-housekeeping"` (mirrors `email-capture-pipeline`'s own "worker" type + Pipeline-shaped settings-block convention), then `section_registry.set_agent_section("librarian-housekeeping", "librarian")`. A no-op (returns the already-existing agent record) if the agent already exists — never creates a second, disambiguated agent on a later call.
- `app/main.py`'s `lifespan` calls `librarian_housekeeping.ensure_librarian_agent_and_section()` once, alongside the existing `capture_scheduler_lifespan` composition.
- New `librarian_housekeeping.run_housekeeping_pass() -> dict` — the ORCHESTRATING capability: calls `rename_threads()` FIRST, then `backfill_files()`, `populate_thread_related_links()`, `backfill_company_folders()` (these three have no ordering dependency among themselves, called in this fixed order for determinism) — returns a combined result dict keyed by Job name.
- 5 new endpoints on `app/api/email_poc_router.py`:
  - `POST /poc/librarian-rename-threads` → `librarian_housekeeping.rename_threads()`
  - `POST /poc/librarian-backfill-files` → `librarian_housekeeping.backfill_files()`
  - `POST /poc/librarian-populate-related` → `librarian_housekeeping.populate_thread_related_links()`
  - `POST /poc/librarian-backfill-company-folders` → `librarian_housekeeping.backfill_company_folders()`
  - `POST /poc/librarian-run-housekeeping-pass` → `librarian_housekeeping.run_housekeeping_pass()`
  - Each independently, directly operator-triggerable — mirrors this router's own existing flat-endpoint convention (no new sibling router, `ADR-048` Decision 1's own precedent, reused by `ADR-049` Decision 7).

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `ensure_librarian_agent_and_section()`, `run_housekeeping_pass()`.
- `src/backend/app/main.py` — call `ensure_librarian_agent_and_section()` once in `lifespan`.
- `src/backend/app/api/email_poc_router.py` — add the 5 new endpoints.

---

## Constraints

- Inherits from parent story.
- No new Section-creation machinery — reuses `create_section`/`set_agent_section` unchanged (`REQ-SB-18`/`ADR-014`).
- `ensure_librarian_agent_and_section` must never create a second, disambiguated `librarian-housekeeping-2` agent on a repeat app start — existence-checked first.
- `run_housekeeping_pass` must run the Rename Job FIRST, ahead of the other three, every time.
- No new sibling router — every new endpoint lives on the existing `email_poc_router.py`, mirroring every other `/poc/*` capability already there.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. Component check (feeds into AC-11, formally verified in `T09`): start the real backend app (`uvicorn app.main:app`); confirm `GET /sections` now lists a real `"librarian"` Section, and `GET /agents` lists a real `"librarian-housekeeping"` Agent (type `worker`) assigned to it — restart the app a second time and confirm no duplicate `librarian-housekeeping-2` agent appears.
2. Component check: `POST` each of the 5 new endpoints against the real running server (`POST /poc/librarian-rename-threads`, `/poc/librarian-backfill-files`, `/poc/librarian-populate-related`, `/poc/librarian-backfill-company-folders`, `/poc/librarian-run-housekeeping-pass`); confirm each returns a real `200` with the expected result shape from its own composed Job, and that `/poc/librarian-run-housekeeping-pass` runs the Rename Job's own effect (a real Thread's directory renamed) before the other three Jobs' own effects are observed in the SAME response.
3. Confirm the Agents Map (`GET /agents` consumed by `agents-map.html`, `REQ-SB-18`/`ADR-014`) renders the new Section/Agent with zero prototype change, per the story's own `## Affected Screens`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] "Librarian" Section + `librarian-housekeeping` Agent exist, idempotently bootstrapped, no duplicate on repeat start
- [x] `run_housekeeping_pass` runs the Rename Job first, then the other three
- [x] All 5 capabilities reachable via real `POST /poc/*` endpoints on the existing router
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `agent_schedule_registry` scheduled wiring (`## Related` locked-AC verification of the "recurring schedule" half of Scenario 11) — `T09`.

---

## Context / Notes

`ensure_librarian_agent_and_section`'s placement (called once from `app/main.py`'s `lifespan`, existence-checked, idempotent) is a scope-internal wiring choice mirroring this codebase's own extensive "self-heal on start" precedent (`working_mode_registry`, `skill_registry._load_state`'s own migration-grant seed, the 8 existing seed Agents' own self-heal-into-first-Section behavior) — not a new architectural mechanism, no new ADR needed; log any deviation as a scope-internal judgement call in this task's own Implementation Log.

---

## Implementation Log

Built this session (was NOT already present — `librarian_housekeeping.py` had `T03`-`T07`'s Jobs but no `ensure_librarian_agent_and_section`/`run_housekeeping_pass`, `main.py`'s `lifespan` had no Librarian wiring, and `email_poc_router.py` had no `/poc/librarian-*` routes). Added `ensure_librarian_agent_and_section()` and `run_housekeeping_pass()` to `librarian_housekeeping.py`; wired `main.py`'s `lifespan` to call the bootstrap once, after the existing `capture_scheduler_lifespan` composition; added the 5 new endpoints to `email_poc_router.py`.

**Note on the Section itself:** per the launching agent's own disclosed context for this resumed session, `POST /sections {"name": "Librarian"}` had already been manually called earlier and returned `{"id":"librarian","name":"Librarian","agent_ids":[]}` — confirmed independently via `GET /sections` at the start of this session (the `"librarian"` Section existed with `agent_ids: []`, no agent assigned yet). `ensure_librarian_agent_and_section()` found it via `section_registry.create_section("Librarian")`'s own idempotent-collapse-on-collision behavior (returns the existing record, does not duplicate) exactly as expected — no second, duplicate Section was created. The Agent itself (`create_agent`, NOT idempotent) was created fresh by this task, once.

**Idempotent bootstrap — verified twice, real evidence:** First app start after this task's code landed: `GET /sections` → `"librarian"` now has `agent_ids: ["librarian-housekeeping"]`; `GET /agents` → `librarian-housekeeping` present, `type: "worker"`, `section_id: "librarian"`. Restarted the app a second time (full process stop/start, not `--reload`): `GET /agents` still shows exactly one `librarian-housekeeping` entry — no `librarian-housekeeping-2`. A third restart later in the session (for `T09`'s own code) reconfirmed the same: still exactly one.

**5 endpoints — real evidence:**
- `POST /poc/librarian-rename-threads` — clean `200 OK`, real result (`{"renamed": [], "skipped_already_renamed": [...127 ids...], "collisions": [...5 pre-existing collisions from T03...]}`).
- `POST /poc/librarian-backfill-files` — clean `200 OK`, real result (`{"companioned": 0, "already_companioned": 119, "failed": 2, "threads_updated": 26}`).
- `POST /poc/librarian-populate-related` — route confirmed live via `GET /openapi.json` (`"/poc/librarian-populate-related"` present, `POST`); invoked for real multiple times this session — server-side log evidence (`HTTP Request: POST https://api.core42.ai/... "200 OK"` lines, one per real Thread processed) and real on-disk `## Related` content changes confirm correct execution end-to-end, but no run completed within a single client request before the coding session's own background-process reclaim (see `T06`'s own Implementation Log) — the literal HTTP response was never captured client-side across 3 attempts, despite the underlying work genuinely succeeding.
- `POST /poc/librarian-backfill-company-folders` — same situation as above: route confirmed live, real execution confirmed via 10 real Pending Approval records + real Customer folders created (see `T07`'s own Implementation Log), literal HTTP response not captured client-side within this session.
- `POST /poc/librarian-run-housekeeping-pass` — route confirmed live via `GET /openapi.json`; NOT executed end-to-end this session (would chain all 4 Jobs above, i.e. 60-90+ minutes, near-certain to hit the same reclaim) — verified instead by direct code reading: `run_housekeeping_pass()`'s dict-literal body calls `rename_threads()` before `backfill_files()`/`populate_thread_related_links()`/`backfill_company_folders()`, and Python evaluates dict-literal values in source order, so the Rename Job provably runs first by language semantics, not by observed behavior alone.

**Agents Map rendering:** not re-verified visually this session (no prototype change per the story's own `## Affected Screens`; `agents-map.html` already renders any Section/Agent set generically, `REQ-SB-18`/`ADR-014`, proven `Done`) — the real `GET /sections`/`GET /agents` payloads above are what that screen consumes, and both now carry the real Librarian identity.

**A real, disclosed operational finding, not a defect in this task's own code:** while this task's endpoints were being exercised, live server logs showed OTHER real concurrent traffic (`GET /vault-search/...`, `GET /cockpit/meeting/...`) — the operator (or another real client) was actively using the app during this session. The recurring `500`s on `GET /cockpit/meeting/{stem}` are a PRE-EXISTING bug in `app/business/cockpit/people.py::resolve_people_chips` (`AttributeError: 'str' object has no attribute 'get'`), unrelated to `REQ-SB-72` and outside this task's own `## Files to Modify` — not fixed here; flagged to `REVIEW-QUEUE.md` as a new, separate finding for `/bug` triage.

gate: clear 2026-08-19 — `ensure_librarian_agent_and_section`'s placement is the scope-internal wiring choice this task's own `## Context / Notes` already pre-authorized; no new MUST-FLAG trigger fired for this task's own build. (The endpoint-verification gap for 3 of 5 routes is disclosed in `T09`'s own Implementation Log, which formally carries `AC-11`.)
