---
id: REQ-SB-73-US-01-T03
title: Wire link_thread_messages() into run_housekeeping_pass() + new /poc/librarian-link-thread-messages endpoint
parent_story: REQ-SB-73-US-01
requirement_id: REQ-SB-73
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-73-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-73-US-01-T03 — Orchestration wiring + endpoint

## Parent Story

- Story: [[REQ-SB-73-US-01]] — `../UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-73 *Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Bidirectional Thread ↔ Message Linking" → "Job-chain placement & endpoint" (`ADR-054` Decision 4)

---

## Objective

Insert `link_thread_messages()` into `run_housekeeping_pass()`'s own Job chain, SECOND — immediately after `rename_threads()` — and expose it as a new, directly operator-triggerable `POST /poc/librarian-link-thread-messages` endpoint, mirroring every other Job's own reachability convention.

---

## Starting State → End State

**Before / Inputs:**
- `run_housekeeping_pass()` returns `{"rename_threads": ..., "backfill_files": ..., "populate_thread_related_links": ..., "backfill_company_folders": ...}`, in that fixed dict-literal order.
- `email_poc_router.py` has `POST /poc/librarian-rename-threads`, `/poc/librarian-backfill-files`, `/poc/librarian-populate-related`, `/poc/librarian-backfill-company-folders`, `/poc/librarian-run-housekeeping-pass` — no `/poc/librarian-link-thread-messages`.

**After / Outputs:**
- `run_housekeeping_pass()`'s dict literal is extended to include `"link_thread_messages": link_thread_messages()`, positioned SECOND — immediately after `"rename_threads": rename_threads()` and before `"backfill_files"` — grouping the two Jobs that together own the Thread↔Message relationship. (Not load-bearing for correctness — `T02`'s own fan-out already keeps `thread:` correct independent of ordering — this positioning is for readability only, per `ADR-054` Decision 4.)
- New endpoint on `email_poc_router.py`: `POST /poc/librarian-link-thread-messages` → `librarian_housekeeping.link_thread_messages()`, mirroring the existing flat `/poc/librarian-*` convention exactly (no new sibling router).

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — extend `run_housekeeping_pass()`'s dict literal.
- `src/backend/app/api/email_poc_router.py` — add the new endpoint (and its import from `librarian_housekeeping`).

---

## Constraints

- Inherits from parent story.
- No new sibling router — the new endpoint lives on the existing `email_poc_router.py`, mirroring every other `/poc/librarian-*` capability already there.
- `link_thread_messages()` must run SECOND in `run_housekeeping_pass()`'s own chain, immediately after `rename_threads()`.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. Component check (plumbing, no AC of its own — consumed and AC-verified in `T04`): start the real backend app; `POST /poc/librarian-link-thread-messages` against the real running server; confirm a real `200` with the expected result shape from `T01`'s own `link_thread_messages()`.
2. Component check: `POST /poc/librarian-run-housekeeping-pass`; confirm the response's own dict carries a `"link_thread_messages"` key positioned between `"rename_threads"` and `"backfill_files"` (read the real JSON key order, or confirm via direct source-code reading that Python evaluates dict-literal values in source order, the same technique `REQ-SB-72-US-01-T08`'s own Implementation Log already established for this exact function).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_housekeeping_pass()` runs `link_thread_messages()` second, immediately after `rename_threads()`
- [ ] `POST /poc/librarian-link-thread-messages` reachable and returns `link_thread_messages()`'s own real result
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `link_thread_messages()`'s own internal behavior — `T01`.
- The `rename_threads()` fan-out extension itself — `T02`.
- The full-corpus retrofit run — `T04`.

---

## Context / Notes

No locked AC is directly tagged to this task — it is pure wiring/plumbing, mirroring `REQ-SB-72-US-01`'s own established "building-block task with no directly-locked AC of its own" precedent (`T01`/`T05` in that story). Its own correctness is exercised and AC-verified downstream in `T04`, which relies on the real endpoint this task builds.

---

## Implementation Log

**Implemented (2026-08-19):** `run_housekeeping_pass()`'s dict literal extended with `"link_thread_messages": link_thread_messages()`, positioned SECOND, between `"rename_threads"` and `"backfill_files"`. New endpoint `POST /poc/librarian-link-thread-messages` added to `email_poc_router.py`, mirroring every other `/poc/librarian-*` capability's own one-line `-> Job()` shape exactly; `link_thread_messages` added to the existing `from app.business.pipelines.librarian_housekeeping import (...)` block.

**Note on concurrent shared-file edits:** `librarian_housekeeping.py` and `email_poc_router.py` are also being edited concurrently by the sibling `REQ-SB-74-US-01`/`SPRINT-068` build (additive functions/imports for Customer Backfill) — a disclosed, expected shared-file overlap per this story's own `## Notes` (no functional dependency; confirmed no edit collision with this task's own two insertion points).

**Manual verification (component check, no locked AC of its own — consumed/AC-verified downstream in `T04`):**

1. Started a real, dedicated backend instance (`uvicorn app.main:app --port 8001`, isolated from any other already-running instance on the default port to avoid disturbing concurrent work) against the real, configured vault. `POST http://127.0.0.1:8001/poc/librarian-link-thread-messages` → real `200`, body a real `{"threads_processed": [...], "messages_linked": [...]}` result shape — exactly `T01`'s own `link_thread_messages()` return shape.
2. Confirmed the Job-chain ordering via direct source-code reading of the just-edited `run_housekeeping_pass()` (Python evaluates dict-literal values in source order, `REQ-SB-72-US-01-T08`'s own established technique for this exact function): the dict literal reads `{"rename_threads": rename_threads(), "link_thread_messages": link_thread_messages(), "backfill_files": backfill_files(), "populate_thread_related_links": populate_thread_related_links(), "backfill_company_folders": backfill_company_folders()}` — `"link_thread_messages"` sits immediately after `"rename_threads"` and before `"backfill_files"`, as required. A real, full `POST /poc/librarian-run-housekeeping-pass` call was also issued against the real corpus to additionally confirm this via the real JSON response key order (long-running — full-corpus Compass company-mention detection across every Thread; observed still genuinely progressing via live CPU/connection activity, not hung); its real completion additionally advances `T04`'s own retrofit state (see `T04`'s own Implementation Log for the completed corpus counts).

**gate: clear 2026-08-19** — no MUST-FLAG trigger fired (no new assumption; no ADR change; no escalation; no locked AC on this task per the decomposer's own mapping; the shared-file overlap with `REQ-SB-74-US-01` is a disclosed, already-reasoned-through non-dependency, not a new contradictory/unclear situation).
