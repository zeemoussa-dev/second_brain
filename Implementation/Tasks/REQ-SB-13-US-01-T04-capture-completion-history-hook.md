---
id: REQ-SB-13-US-01-T04
title: One additional vault_writer.append_agent_history_entry call in run_capture_and_record_completion
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T04 — run_capture_and_record_completion history hook

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add one additional call, `vault_writer.append_agent_history_entry(
"email-capture", "run_event", ...)`, inside the already-`Done`
`email_classification.run_capture_and_record_completion`, alongside its
existing `record_capture_run_completed()` call — so a capture run started by
the hourly scheduler, the app-start trigger, `/poc/classify-emails`, or
`T05`'s new action/chat triggers all produce the exact same history entry,
through the one shared entry point `ADR-005`/`ADR-008` already established.

**This is the only change to already-`Done` REQ-SB-07/REQ-SB-14/REQ-SB-10
code this story makes** — everything else in this story is new files
(`ADR-011`'s own Consequences).

---

## Starting State → End State

**Before / Inputs:**
- `email_classification.run_capture_and_record_completion(limit=10)` calls
  `classify_recent_emails(limit=limit)` then
  `vault_writer.record_capture_run_completed()`, and returns `results`.
- `T01` has landed `vault_writer.append_agent_history_entry(agent_id, kind,
  text)`.

**After / Outputs:**
- `run_capture_and_record_completion` additionally calls
  `vault_writer.append_agent_history_entry("email-capture", "run_event",
  <a human-readable summary of what the run did>)`, immediately after (or
  alongside) its existing `record_capture_run_completed()` call. Its
  existing behavior (return value, the `record_capture_run_completed()`
  call itself) is unchanged.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  ```python
  def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
      """Scheduling-layer entry point (ADR-005): runs the same capture
      pipeline the manual /poc/classify-emails endpoint uses, then records
      completion via vault_writer so the shared last-run record (read by
      the future REQ-SB-11 observability UI) reflects every scheduled run,
      not just manual ones. Also appends a run_event history entry
      (REQ-SB-13-US-01/ADR-011) so every trigger source — scheduler,
      app-start, /poc/classify-emails, or the new agent-panel action/chat
      triggers — produces the same Communication History entry through
      this one shared entry point."""
      results = classify_recent_emails(limit=limit)
      vault_writer.record_capture_run_completed()
      vault_writer.append_agent_history_entry(
          "email-capture",
          "run_event",
          f"Capture run completed — {len(results)} email(s) filed",
      )
      return results
  ```
  (`email_classification.py` already imports `vault_writer` at module level
  — no new import needed.)

---

## Constraints

- Inherits from parent story: `ADR-011`'s decision that this is the *only*
  change to already-`Done` code this story makes.
- Must NOT modify `classify_recent_emails`, `record_capture_run_completed`'s
  own definition, the function's `limit` parameter/default, or its return
  value — additive only, one new call.
- The history-entry `text` must be a genuinely descriptive summary (e.g.
  "Capture run completed — 3 email(s) filed") — not a placeholder string —
  since this is exactly the text `REQ-SB-13-US-01-T08`'s history log
  renders to the user.

---

## Tests

<!-- Exercised end-to-end, live, by T05's history endpoint (Scenarios 3,
3b), where this story's locked ACs are tagged. The smoke check below
confirms this one hook in isolation first — note MEMORY.md's standing
constraint that this call chain already fires for real on every dev-server
start/restart. -->

**Manual verification steps:**
1. Non-AC smoke check: from `src/backend`, start the dev server
   (`.venv\Scripts\uvicorn app.main:app --reload --port 8001` — this
   already triggers a real capture run on start, per `MEMORY.md`'s standing
   constraint). After it finishes, in a separate Python shell against the
   same `.venv`, call `vault_writer.load_agent_history("email-capture")`.
   Confirm the returned list's most recent entry has `kind: "run_event"`
   and a `text` value matching the pattern "Capture run completed — N
   email(s) filed", with a `timestamp` at or after the server's start time.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_capture_and_record_completion` appends one `run_event` history
      entry for `"email-capture"` on every call, alongside its existing
      `record_capture_run_completed()` call
- [ ] The entry's `text` describes how many emails were filed
- [ ] `classify_recent_emails`'s own behavior and this function's return
      value are unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to the scheduler, `/poc/classify-emails`, or any other caller
  of `run_capture_and_record_completion` — they all inherit this change for
  free, through the one shared entry point.
- Appending `chat_user`/`chat_agent` history entries — `T05`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**2026-08-11, coder pass.** Re-read `app/business/email_classification.py`
fresh immediately before editing (flagged as a shared file other in-flight
sprints may touch): found `run_capture_and_record_completion` already
differed from this task's assumed "Before" state — it now also calls
`meeting_classification.classify_recent_meetings()` (REQ-SB-08/SPRINT-006,
concurrent, uncommitted work), added between `classify_recent_emails` and
`record_capture_run_completed`. This is not a real conflict: added the one
`vault_writer.append_agent_history_entry("email-capture", "run_event",
...)` call immediately after the existing `record_capture_run_completed()`
call, additive only, leaving the meeting-capture call and every other line
untouched. Also extended the docstring by one sentence describing the new
hook (a real behavioral addition worth documenting, not scope creep).

Live confirmation: started the dev server (`--port 8003`, since ports
8000/8001/8002 were all already occupied — 8000 by the known `agentic-map`
process, 8001/8002 by concurrent Second Brain sessions verifying other
in-flight sprints, per `MEMORY.md`'s standing port-8000 constraint extended
to the multi-session case observed live this pass). This fired a real
capture run (Outlook fetch, Compass classify, meeting capture, vault
write) on startup, per `MEMORY.md`'s standing every-start constraint.
`GET /agents/email-capture/history` afterward showed the most recent
entry as `{"kind": "run_event", "text": "Capture run completed — 0
email(s) filed", "timestamp": "2026-08-11T13:41:23...+00:00"}` — 0 filed
because the inbox had no new unprocessed mail at the time, not an error
(`classify_recent_emails` legitimately returns `[]` when
`load_processed_email_ids()` already covers every fetched item).

- [x] Appends one `run_event` entry for `"email-capture"` on every call, alongside `record_capture_run_completed()` — confirmed live
- [x] The entry's `text` describes how many emails were filed — confirmed ("Capture run completed — N email(s) filed")
- [x] `classify_recent_emails`'s own behavior and this function's return value unchanged — confirmed by diff review (only one line added, `return results` untouched)
- [x] `MEMORY.md` updated — yes, see Decisions/Constraints entries for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes

Observed, not a defect (logged for spot-check): the shared
`agent_communication_history.json` accumulated additional `run_event`
entries beyond this session's own triggers during live verification
(timestamps not matching any request this coder made) — consistent with
other concurrently-running Second Brain backend processes (on 8001/8002,
started earlier without `--reload`) being restarted by their own
concurrent sessions after this task's `vault_writer.py`/
`email_classification.py` edits landed on disk, picking up the new hook on
their own next restart against the same shared vault. Expected, real,
multi-process behavior given the shared vault path — not a bug in this
task's own code.
