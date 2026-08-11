---
id: REQ-SB-07-US-01-T02
title: Wrap the capture pipeline with last-run bookkeeping
parent_story: REQ-SB-07-US-01
requirement_id: REQ-SB-07
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-07-US-01-T01]
created: 2026-08-10
updated: 2026-08-10
---

# REQ-SB-07-US-01-T02 — Wrap the capture pipeline with last-run bookkeeping

## Parent Story

- Story: [[REQ-SB-07-US-01]] — `../UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-07 *Scheduled Recurring Agent Capture*

---

## Objective

Add one business-layer function that runs the existing capture pipeline and
then records completion via T01's new persistence functions — the single
entry point the new `scheduling/` layer (T03/T04) will call, without
touching or duplicating the existing `classify_recent_emails` pipeline or
the existing manual `POST /poc/classify-emails` endpoint.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/email_classification.py::classify_recent_emails` exists,
  unchanged, and is called directly by `app/api/email_poc_router.py`'s
  manual endpoint.
- T01 added `vault_writer.record_capture_run_completed()`.

**After / Outputs:**
- A new `run_capture_and_record_completion(limit: int = 10) -> list[dict]`
  function in the same module, calling `classify_recent_emails` then
  `vault_writer.record_capture_run_completed()`, returning the same results
  list unchanged.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add:
  ```python
  def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
      """Scheduling-layer entry point (ADR-005): runs the same capture
      pipeline the manual /poc/classify-emails endpoint uses, then records
      completion via vault_writer so the shared last-run record (read by
      the future REQ-SB-11 observability UI) reflects every scheduled run,
      not just manual ones."""
      results = classify_recent_emails(limit=limit)
      vault_writer.record_capture_run_completed()
      return results
  ```
  Place it directly below `classify_recent_emails` in the same file.

---

## Constraints

- Inherits from parent story.
- Must NOT modify `classify_recent_emails` itself or
  `app/api/email_poc_router.py` — the manual endpoint continues to call
  `classify_recent_emails` directly and unchanged (this story's Non-Goals).
- Must respect `api → business → data_access` layering (ADR-003): this is a
  `business/` function calling `data_access` (`vault_writer`) — already the
  pattern this module uses for `mark_email_processed` /
  `record_conversation_note`, so no new layering shape is introduced.
- Record completion after every run, including a run that returns an empty
  results list (no new emails) — "the run completes" per AC-01 does not
  require any items to have been found or classified.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-07-US-01-AC-01] In a Python shell against the backend `.venv`,
   call `email_classification.run_capture_and_record_completion(limit=1)`
   against a real (or test) vault/Outlook session. Confirm it returns the
   same shape of results list `classify_recent_emails` alone would, AND that
   `vault_writer.load_last_capture_run()` reflects a fresh `finished_at`
   timestamp immediately afterward (compare against the timestamp observed
   before the call, or against `None` on a first run). Re-run it a second
   time with zero new emails available (e.g. after the first run already
   processed everything pending) and confirm the record still updates even
   though `results` is empty — completion is unconditional on finding work.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `run_capture_and_record_completion` calls `classify_recent_emails`
      unchanged and returns its results
- [x] `vault_writer.record_capture_run_completed()` is called exactly once
      per invocation, after the pipeline finishes (including when the
      pipeline finds nothing to process)
- [x] `classify_recent_emails` and `email_poc_router.py`'s manual endpoint
      are untouched
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The concurrency guard around this function (T03) and the scheduler/
  app-start wiring that calls it (T04) — this task only adds the
  orchestration function itself.
- Error handling beyond what `classify_recent_emails` already does
  (per-email `CompassError` capture) — not changed here.

---

## Context / Notes

This function is intentionally thin — it exists solely so the scheduling
layer (which per ADR-005 may only call into `business/`, never
`data_access/` directly) has exactly one call to make per capture run,
keeping the "update last-run after every completed run" rule in one place
rather than duplicated at every trigger source.

---

## Implementation Log

**Change made (2026-08-10):** Added `run_capture_and_record_completion(limit:
int = 10) -> list[dict]` to `src/backend/app/business/email_classification.py`,
placed directly below `classify_recent_emails`, exactly as specified in
`## Files to Modify` — no deviation from the plan. `classify_recent_emails`
itself and `app/api/email_poc_router.py` were not touched (confirmed by
re-reading `email_poc_router.py` before editing — it still imports and calls
`classify_recent_emails` directly).

**Verification — REQ-SB-07-US-01-AC-01 (manual mode, per this task's `##
Tests`):** Ran against the real configured backend (`.venv` on Python 3.14,
real Compass credentials and vault path from `.env`, real running Outlook
desktop session) via `python -c` against `src/backend`:

1. Baseline: `vault_writer.load_last_capture_run()` →
   `{'finished_at': '2026-08-10T14:58:48...'}` (pre-existing record from
   T01's own verification).
2. Call 1 — `run_capture_and_record_completion(limit=1)`: returned
   `[{'subject': 'Workshop slides', 'customer': 'Masdar', 'kind': 'Emails',
   'confidence': 0.96, 'attachments': 0, 'related_emails': 0, 'note_path':
   '...Work/Emails/2026-08-10-Workshop slides-7A780000.md'}]` — same result
   shape `classify_recent_emails` alone produces (confirmed against its
   `results.append(...)` fields). A real vault note was written and the
   email was marked processed. `load_last_capture_run()` immediately after
   returned a fresh `finished_at` (`2026-08-10T15:01:26...`), newer than the
   baseline — PASS.
3. Call 2 — same invocation again, immediately after: the one Outlook item
   within `limit=1` was already marked processed by call 1, so
   `classify_recent_emails` found nothing new and returned `[]`. Despite the
   empty results list, `load_last_capture_run()` still updated to a further
   fresh `finished_at` (`2026-08-10T15:01:34...`) — confirms completion is
   recorded unconditionally, even when the pipeline finds nothing to
   process, per the task's "unconditional on finding work" constraint —
   PASS.

**Outcome: REQ-SB-07-US-01-AC-01 — PASS** (both the fresh-timestamp-on-work
and fresh-timestamp-on-no-work cases verified live).

**Assumption (scope-internal, not an escalation):** used a `python -c`
one-liner against the `.venv` interpreter rather than an interactive shell
session, per the task's "Python shell against the backend `.venv`"
instruction — same effect (real process, real imports, real I/O), just
non-interactive; flagged here for spot-check per Pipeline.md's
scope-internal-judgement-call rule.

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task followed the existing thin-orchestration-wrapper pattern already
established by `mark_email_processed`/`record_conversation_note` call sites
in the same module, and ADR-005 (already recorded) fully covers the
scheduling-layer rationale.

gate: clear 2026-08-10 — no triggers fired (ADR-005 already reviewed and
approved by the operator at the story level; no new material assumption
beyond the non-interactive-shell note above, which is scope-internal per
Pipeline.md and not itself a MUST-FLAG trigger; no contradictory inputs; no
new ADR/architecture change; no oversized task; the one locked AC in scope
here, AC-01, was verified live and passed).
