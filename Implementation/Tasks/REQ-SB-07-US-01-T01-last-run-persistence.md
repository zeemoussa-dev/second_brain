---
id: REQ-SB-07-US-01-T01
title: Persist the last-successful-capture-run record
parent_story: REQ-SB-07-US-01
requirement_id: REQ-SB-07
type: backend
status: Done
gate: clear
gate_reason: "trigger-3 (ADR-005 created) — inherited from parent story; resolved by operator review 2026-08-10 (ADR-005 approved, REVIEW-QUEUE entry cleared) before this task started"
phase: P1
depends_on: []
created: 2026-08-10
updated: 2026-08-10
---

# REQ-SB-07-US-01-T01 — Persist the last-successful-capture-run record

## Parent Story

- Story: [[REQ-SB-07-US-01]] — `../UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-07 *Scheduled Recurring Agent Capture*

---

## Objective

Add a small JSON-backed "last capture run completed" record to the
`.second-brain/` state directory, following the exact same read/write shape
`vault_writer.py` already uses for `processed_email_ids.json` /
`conversation_index.json`, so later tasks in this story can update and read
it (ADR-005, point 4).

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py` already owns `.second-brain/` state
  files (`processed_email_ids.json`, `conversation_index.json`) via
  `_processed_emails_path()` / `_conversations_path()` and their
  load/mark functions — no last-run record exists yet.

**After / Outputs:**
- A new `.second-brain/last_capture_run.json` file convention, written and
  read via two new `vault_writer.py` functions, ready for the business
  layer (T02) to call.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add:
  - Module-level constant `_LAST_CAPTURE_RUN_FILE = "last_capture_run.json"`.
  - `_last_capture_run_path()` — mirrors `_processed_emails_path()` /
    `_conversations_path()` (ensures `.second-brain/` exists, returns the
    file path). Reuse the existing `_STATE_DIR` constant.
  - `record_capture_run_completed() -> None` — writes
    `{"finished_at": "<ISO-8601 UTC timestamp>"}` to the file (use
    `datetime.now(timezone.utc).isoformat()`; add the `datetime` import at
    the top of the module alongside the existing `json`/`re` imports).
  - `load_last_capture_run() -> dict | None` — returns the parsed JSON dict,
    or `None` if the file does not exist yet (mirrors `load_processed_email_
    ids()`'s "empty state until first write" shape).

---

## Constraints

- Inherits from parent story (Hermes not touched; `api → business →
  data_access` layering per ADR-003; no admin-rights assumptions).
- This file lives in `data_access/` only — no business rules, no HTTP
  concerns, per ADR-003's boundary (restated by ADR-005 for the new
  `scheduling/` layer that will call into this indirectly via `business/`
  in T02/T03 — this task itself does not touch `scheduling/` or
  `business/`).
- Must not collide with the two existing state files
  (`processed_email_ids.json`, `conversation_index.json`) — use the exact
  filename `last_capture_run.json`.
- Timestamp must be UTC and ISO-8601 (matches how other timestamped fields
  in this codebase are handled — no local-timezone ambiguity on a
  laptop-hosted process).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-07-US-01-AC-01] In a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`), import `app.data_access.vault_writer` and
   call `record_capture_run_completed()` directly. Confirm
   `.second-brain/last_capture_run.json` is created (or overwritten) under
   the configured `vault_path`, containing a `finished_at` key with a valid
   ISO-8601 UTC timestamp string. Then call `load_last_capture_run()` and
   confirm it returns a dict with that same timestamp (round-trip). Then,
   with the file temporarily renamed/removed, call `load_last_capture_run()`
   again and confirm it returns `None` rather than raising — this is the
   underlying mechanism behind AC-01's "the last-successful-run record is
   updated once the run completes."

**Automated tests:** `n/a — test tooling pending; add a pytest module under
src/backend/tests/ covering these two functions once this layer gets
automated coverage`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `record_capture_run_completed()` writes a valid ISO-8601 UTC
      `finished_at` timestamp to `.second-brain/last_capture_run.json`
- [x] `load_last_capture_run()` round-trips that value and returns `None`
      when the file does not exist
- [x] No collision with `processed_email_ids.json` / `conversation_index.json`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      (judged: no new decision/pattern/constraint emerged — this task is a
      direct mirror of the existing `_conversations_path()` /
      `record_conversation_note()` shape, nothing novel to record)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling these functions from anywhere else in the codebase — that is T02
  (business-layer wiring) and T04 (scheduler wiring), not this task.
- Reading this record back to *decide* whether to fire a run — per ADR-005
  point 4, none of this story's ACs require that conditional logic; this
  task only persists the record for audit / future REQ-SB-11 use.

---

## Context / Notes

`vault_writer.py` currently has no `datetime` import — add
`from datetime import datetime, timezone` near the top alongside the
existing `import json` / `import re`. Follow the exact same
mkdir-then-write pattern `_processed_emails_path()` uses so the new function
behaves identically on a fresh vault with no `.second-brain/` directory yet.

---

## Implementation Log

**Implemented (2026-08-10):** Added to `src/backend/app/data_access/vault_writer.py`,
mirroring the existing `_conversations_path()` / `record_conversation_note()` /
`_load_conversation_index()` shape exactly, per the task's Context/Notes:
- `from datetime import datetime, timezone` added to the module's import block.
- Module-level constant `_LAST_CAPTURE_RUN_FILE = "last_capture_run.json"` added
  alongside the existing `_PROCESSED_EMAILS_FILE` / `_CONVERSATIONS_FILE` constants.
- `_last_capture_run_path()` — mkdir-then-return-path, same shape as
  `_processed_emails_path()` / `_conversations_path()`, reusing `_STATE_DIR`.
- `record_capture_run_completed() -> None` — writes
  `{"finished_at": datetime.now(timezone.utc).isoformat()}` as JSON.
- `load_last_capture_run() -> dict | None` — returns the parsed dict, or `None`
  if the file doesn't exist yet.

No deviations from the task spec. No out-of-scope files touched; no new
dependency, ADR deviation, or shared-interface change encountered.

**Verification — [REQ-SB-07-US-01-AC-01] (manual mode, per
`Implementation/Pipeline.md`'s coder verification-mode section — no automated
test runner wired to `data_access/` yet):**

Ran a throwaway script (`src/backend/verify_t01.py`, deleted after the run —
not part of `## Files to Modify`) via `.venv\Scripts\python.exe` against the
real configured `vault_path`:

1. Called `record_capture_run_completed()` directly. Observed
   `.second-brain/last_capture_run.json` created under the configured vault
   path, containing `{"finished_at": "2026-08-10T14:58:48.667728+00:00"}` — a
   valid ISO-8601 UTC timestamp (regex-validated: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).
   **PASS.**
2. Called `load_last_capture_run()`. Observed it returned
   `{"finished_at": "2026-08-10T14:58:48.667728+00:00"}` — the identical
   dict/timestamp from step 1, confirming the round-trip. **PASS.**
3. Renamed `last_capture_run.json` to `last_capture_run.json.bak` (simulating
   "file does not exist yet"), then called `load_last_capture_run()` again.
   Observed it returned `None` without raising. Restored the file to its
   original path/name afterward, leaving vault state unchanged. **PASS.**

Also visually confirmed in the same session that `_PROCESSED_EMAILS_FILE`
(`processed_email_ids.json`) and `_CONVERSATIONS_FILE`
(`conversation_index.json`) remain distinct constants from the new
`_LAST_CAPTURE_RUN_FILE` (`last_capture_run.json`) — no filename collision.

**AC-01 result: PASS** (this task's slice of AC-01 — "the last-successful-run
record is updated once the run completes" — is fully covered by steps 1–2
above; AC-01's other clauses, e.g. the hourly trigger firing the run itself,
are covered by later tasks T02/T04 per the story's task table).

gate: clear 2026-08-10 — the task's inherited `gate: flagged` (trigger-3,
ADR-005) was already resolved by the operator's review of the parent story
before this task began (ADR-005 approved as written, `REVIEW-QUEUE.md` entry
removed — see story `## Notes`); no new MUST-FLAG trigger fired during this
task's own implementation (no new assumption beyond what ADR-005/the task
spec already settled, no contradictory inputs, no ADR/ESCALATIONS activity,
AC-01's tagged step verified successfully).
