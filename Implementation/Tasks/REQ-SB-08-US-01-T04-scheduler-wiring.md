---
id: REQ-SB-08-US-01-T04
title: Wire meeting capture into REQ-SB-07's existing hourly scheduled run
parent_story: REQ-SB-08-US-01
requirement_id: REQ-SB-08
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-08-US-01-T03]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-08-US-01-T04 — Wire meeting capture into REQ-SB-07's existing hourly scheduled run

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Meeting capture runs automatically on the exact same recurring schedule
email capture already runs on (hourly, once on app start, and catching up a
missed run) — no second scheduled job, no second concurrency guard, and no
change to `app/scheduling/capture_scheduler.py` at all (ADR-008 point 4).

---

## Starting State → End State

**Before / Inputs:**
- `email_classification.run_capture_and_record_completion` calls
  `classify_recent_emails(limit=limit)` then
  `vault_writer.record_capture_run_completed()`. It is the sole function
  `app/scheduling/capture_scheduler.py` calls (both the app-start trigger
  and the hourly `IntervalTrigger` job).
- T03 added `meeting_classification.classify_recent_meetings()`.

**After / Outputs:**
- `run_capture_and_record_completion` gains one additional call,
  `meeting_classification.classify_recent_meetings()`, between
  `classify_recent_emails(...)` and
  `vault_writer.record_capture_run_completed()`. No other function in this
  file changes. `capture_scheduler.py` is untouched.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  1. Change the existing import line
     ```python
     from app.business import customer_hub_linking, people_extraction
     ```
     to
     ```python
     from app.business import customer_hub_linking, meeting_classification, people_extraction
     ```
     (No other import line changes.)
  2. In `run_capture_and_record_completion`, replace:
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
     with:
     ```python
     def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
         """Scheduling-layer entry point (ADR-005): runs the same capture
         pipeline the manual /poc/classify-emails endpoint uses, then records
         completion via vault_writer so the shared last-run record (read by
         the future REQ-SB-11 observability UI) reflects every scheduled run,
         not just manual ones. Also runs Meetings capture (REQ-SB-08,
         ADR-008) on the same tick — no second scheduled job, no second
         concurrency guard; app/scheduling/capture_scheduler.py requires zero
         changes since it already treats this function as an opaque unit."""
         results = classify_recent_emails(limit=limit)
         meeting_classification.classify_recent_meetings()
         vault_writer.record_capture_run_completed()
         return results
     ```

---

## Constraints

- Inherits from parent story (ADR-005 extended, not rewritten; ADR-008
  point 4).
- Must NOT modify `classify_recent_emails`, `app/scheduling/
  capture_scheduler.py`, the manual `POST /poc/classify-emails` endpoint,
  or any other function/line in `email_classification.py` beyond the
  import line and the two-line addition above.
- Must not change `run_capture_and_record_completion`'s return shape (still
  the email-results list) — Meetings capture is a side-effecting addition
  only, matching ADR-008 point 4 exactly.
- Call order matters: `classify_recent_emails` first, then
  `classify_recent_meetings()`, then
  `vault_writer.record_capture_run_completed()` — matching ADR-008's own
  specified ordering.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-08-US-01-AC-10] With the real Outlook desktop client running
   and at least one real calendar event within the default sync window
   (`days_back=7`, `days_ahead=14`), start the dev server
   (`.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from
   `src/backend` — check `MEMORY.md`'s port-8000-may-be-occupied constraint
   first). This fires the unconditional app-start trigger
   (`capture_scheduler.run_capture_if_idle` →
   `email_classification.run_capture_and_record_completion`). Confirm, via
   `Work/Meetings/` before/after, that at least one Meeting note was
   created or topped-up as a direct result of this single app-start call —
   with no separate manual step, no separate scheduled job, and no call
   made directly to `meeting_classification.classify_recent_meetings()`
   outside of this trigger. Confirm `app/scheduling/capture_scheduler.py`
   itself was not modified by this task (diff check) and still shows
   exactly one job (`_HOURLY_CAPTURE_JOB_ID`).
2. [REQ-SB-08-US-01-AC-10] Confirm (via code inspection) that
   `run_capture_and_record_completion`'s return value is still exactly the
   email-results list (same shape as before this task) — Meetings capture
   is not reflected in the return value, only as a side effect, matching
   ADR-008 point 4.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `run_capture_and_record_completion` calls
      `meeting_classification.classify_recent_meetings()` on every trigger
      (app-start and hourly), between `classify_recent_emails` and
      `record_capture_run_completed`
- [x] `app/scheduling/capture_scheduler.py` requires zero changes and is
      untouched by this task
- [x] `run_capture_and_record_completion`'s return shape is unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The manual on-demand trigger endpoint — that is T05.
- Any change to the concurrency guard, `IntervalTrigger`, or misfire/
  coalesce configuration — untouched, per ADR-008 point 4.

---

## Context / Notes

This is the smallest task in this story — a two-line change to one
already-`Done` file, per ADR-008's own explicit "one additional call"
framing. `capture_scheduler.py`'s own docstring already treats
`run_capture_and_record_completion` as an opaque unit, which is exactly
why zero changes are needed there.

---

## Implementation Log

**2026-08-11, coder.** Two-line change applied exactly as specified: the
import line gained `meeting_classification`, and
`run_capture_and_record_completion` gained the one additional call, in the
exact order specified (`classify_recent_emails` → `classify_recent_meetings`
→ `record_capture_run_completed`). No other line changed.

**[REQ-SB-08-US-01-AC-10] Live verification:** stopped a stray, pre-existing
dev-server process bound to port 8001 (leftover from an earlier session,
running stale pre-this-sprint code) and started a fresh one
(`.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001` — port 8000
was occupied by an unrelated `agentic-map` process, matching `MEMORY.md`'s
known constraint). The unconditional app-start trigger fired
`run_capture_and_record_completion` once, with **no separate manual call**
to `classify_recent_meetings`. Before this restart, `Work/Meetings/`
contained the 5 real notes T03's own smoke check had already created (plus
1 pre-existing, unrelated Email-pipeline note filed under `kind: "Meetings"`
— an existing, unrelated data-quality wrinkle, not created by this task).
After the restart, `Work/Meetings/` contained 38 real Meeting notes (the
full `days_back=7, days_ahead=14` window) — confirming Meetings capture ran
as a direct side effect of the single app-start call. **Diff check:**
`git diff --stat app/scheduling/capture_scheduler.py` is empty — zero
changes, confirmed. **Job count:** exactly one job
(`_HOURLY_CAPTURE_JOB_ID = "hourly_capture"`) registered in
`capture_scheduler.py`, unchanged. PASS.

**[REQ-SB-08-US-01-AC-10] Return-shape check (code inspection):**
`run_capture_and_record_completion` still returns exactly `results` (the
`classify_recent_emails` list) — `classify_recent_meetings()`'s return value
is called and discarded, not merged into the response. PASS.

**Result: PASS.** AC-10 verified live; both Acceptance-Criteria checklist
items confirmed by diff/code inspection.
