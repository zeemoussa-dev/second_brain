---
id: REQ-SB-11-US-01-T01
title: Honest-failure-recording fix — meeting-capture success-entry parity + per-step honest-failure-funnel, email_classification.py only
parent_story: REQ-SB-11-US-01
requirement_id: REQ-SB-11
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
sprint: "SPRINT-027"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-11-US-01-T01 — Capture-pipeline honest-failure-recording fix

## Parent Story

- Story: [[REQ-SB-11-US-01]] — `../UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-11 *Agent Activity & Error Observability*

---

## Objective

Close the two confirmed recording gaps inside
`email_classification.py::run_capture_and_record_completion` — (1)
meeting-capture's Autonomous branch never wrote a success history entry
at all; (2) neither capture step's call was wrapped in a try/except, so
an exception escaping `classify_recent_emails`'s/`classify_recent_meetings`'s
own per-item handling propagated uncaught, with zero history entry ever
written. **Only `email_classification.py` changes** — it is the one
function that already orchestrates both pipelines; `meeting_classification.py`
itself is untouched (see architecture.md's "Agent Activity & Error
Observability" section for the full reasoning).

---

## Starting State → End State

**Before / Inputs:**
- `email_classification.py::run_capture_and_record_completion`'s
  Autonomous branches: email-capture calls `run_capture_for_agent(
  "email-capture", limit=limit)` and appends a `"run_event"` history entry
  unconditionally after the call (no try/except); meeting-capture calls
  `run_capture_for_agent("meeting-capture")`, discards the result, and
  appends no history entry at all.
- `vault_writer.append_agent_history_entry(agent_id, kind, text,
  pending_approval_id=None)` (`Done`) — the shared primitive both branches
  already call; unmodified signature, only a new `kind` value used.
- `vault_writer.record_capture_run_completed()` (`Done`) — called
  unconditionally at the very end of the function today; only reached
  when nothing above it raised (`REQ-SB-31-US-01`'s own documented
  `last_capture_run.json` semantics).

**After / Outputs:**
- Both Autonomous branches wrap their own `run_capture_for_agent(...)`
  call in an independent `try/except Exception as exc:`. On success, the
  existing `"run_event"` entry is appended (email-capture's text
  unchanged; meeting-capture gains a new, parallel `"run_event"` entry —
  "Capture run completed — N meeting(s) filed"). On a caught exception,
  a new `"run_error"`-kind entry is appended instead — "Capture run
  failed — {exc}" — and that branch's own capture attempt is treated as
  having filed nothing this tick.
- `record_capture_run_completed()` is called only when neither branch's
  `try/except` caught an exception this tick — preserving its existing
  "only reached when nothing raised" observable behavior exactly, on top
  of the new `"run_error"` entry.
- The function's own return contract is unchanged: still exactly the
  email-capture results list (`[]` on non-Autonomous mode, and now also
  `[]` on a caught email-capture failure — both are the same honest "no
  items filed this tick" signal).

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — inside
  `run_capture_and_record_completion`, replace the two Autonomous
  branches and the trailing `record_capture_run_completed()` call:

  ```python
  def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
      """... (existing docstring, extend with:)

      REQ-SB-11/architecture.md "Agent Activity & Error Observability":
      each Autonomous-mode capture step below is now independently
      wrapped in a try/except -- an exception escaping that step's own
      per-item handling (e.g. outlook_com.OutlookUnavailable) is caught
      here and recorded as a new "run_error"-kind history entry instead
      of propagating uncaught (mirrors ADR-015's own call-site
      honest-failure-funnel pattern, applied to this orchestration
      function). record_capture_run_completed() is only called when
      neither step's try/except fired this tick -- preserving its
      existing "only reached when nothing raised" semantics
      (REQ-SB-31-US-01's own documented last_capture_run.json signal)
      unchanged.
      """
      email_mode = working_mode_registry.get_agent_working_mode("email-capture")
      email_capture_failed = False
      results: list[dict] = []
      if email_mode == "autonomous":
          try:
              results = run_capture_for_agent("email-capture", limit=limit)
          except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
              email_capture_failed = True
              results = []
              vault_writer.append_agent_history_entry(
                  "email-capture",
                  "run_error",
                  f"Capture run failed — {exc}",
              )
          else:
              vault_writer.append_agent_history_entry(
                  "email-capture",
                  "run_event",
                  f"Capture run completed — {len(results)} email(s) filed",
              )
      elif email_mode == "supervised":
          approval = pending_approval_registry.create_pending_approval(
              agent_id="email-capture",
              trigger="background",
              action_id=None,
              description="Run the scheduled email-capture step — checks the "
                          "inbox for new mail and files it into the vault.",
          )
          vault_writer.append_agent_history_entry(
              "email-capture",
              "proposal",
              f"Proposed — {approval['description']} Awaiting your approval.",
              pending_approval_id=approval["id"],
          )
          results = []
      else:  # manual — stays dormant this tick, no record, no history entry
          results = []

      meeting_mode = working_mode_registry.get_agent_working_mode("meeting-capture")
      meeting_capture_failed = False
      if meeting_mode == "autonomous":
          try:
              meeting_results = run_capture_for_agent("meeting-capture")
          except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11 Scenario 2), extends ADR-015's existing pattern to this call site
              meeting_capture_failed = True
              vault_writer.append_agent_history_entry(
                  "meeting-capture",
                  "run_error",
                  f"Capture run failed — {exc}",
              )
          else:
              vault_writer.append_agent_history_entry(
                  "meeting-capture",
                  "run_event",
                  f"Capture run completed — {len(meeting_results)} meeting(s) filed",
              )
      elif meeting_mode == "supervised":
          approval = pending_approval_registry.create_pending_approval(
              agent_id="meeting-capture",
              trigger="background",
              action_id=None,
              description="Run the scheduled meeting-capture step — checks the "
                          "calendar for new events and files them into the vault.",
          )
          vault_writer.append_agent_history_entry(
              "meeting-capture",
              "proposal",
              f"Proposed — {approval['description']} Awaiting your approval.",
              pending_approval_id=approval["id"],
          )
      # else: manual — stays dormant this tick, no record, no history entry

      if not email_capture_failed and not meeting_capture_failed:
          vault_writer.record_capture_run_completed()
      return results
  ```

  Every other line of the function (its docstring's existing paragraphs,
  the Supervised-branch bodies, the `manual` fallthroughs) is unchanged in
  meaning — only reproduced above because the two Autonomous branches and
  the trailing call sit in between them.

---

## Constraints

- Inherits from parent story: `business/` layer only, no HTTP framework
  import, no direct filesystem access of its own (only via
  `vault_writer`).
- **Only `email_classification.py` changes.** Do not touch
  `meeting_classification.py` — its `classify_recent_meetings()` keeps its
  exact existing shape (see Objective/architecture.md for why).
- **Two independent `try/except` blocks**, one per capture step — an
  email-capture failure must never suppress meeting-capture's own success
  (or failure) from being recorded, and vice versa (Scenario 3).
- **New `kind` value is the literal string `"run_error"`** — do not modify
  `vault_writer.append_agent_history_entry`'s signature or add a new
  parameter; call it exactly as every existing caller already does
  (`agent_id, kind, text`).
- `record_capture_run_completed()` must be called **only** when neither
  Autonomous branch's `try/except` caught an exception this tick — do not
  make it unconditional (that would silently change `REQ-SB-31-US-01`'s
  already-documented `last_capture_run.json` failure signal).
- The function's return value stays exactly `results` (email-capture's own
  list) — do not fold meeting-capture's results into the return value.
- No change to the Supervised or Manual branches' existing behavior/text.
- No general exception-catching/logging middleware beyond these two named
  call sites (the story's own Non-Goals).

---

## Tests

<!-- No locked AC of its own -- both Scenario 2's and Scenario 3's own
"Then" clauses describe user-observable outcomes on the activity log
screen, so their AC-tagged verification lives in T04 once a real page
renders what this fix produces. Non-AC smoke checks here, mirroring
REQ-SB-31-US-01-T01's/T02's own identical split. -->

**Manual verification steps** (throwaway interpreter against
`src/backend`'s `.venv`; the real vault's `.second-brain/
agent_communication_history.json` is a real, live side-effect file —
back it up before inducing a failure, restore after):

1. Non-AC smoke check — meeting-capture success parity: with
   meeting-capture's working mode `autonomous` (the real default),
   directly call `email_classification.run_capture_and_record_completion()`
   against the real vault/Outlook. Confirm
   `vault_writer.load_agent_history("meeting-capture")`'s last entry is
   `kind: "run_event"`, text matching `"Capture run completed — N
   meeting(s) filed"` — a success entry now exists where none did before
   this fix.
2. Non-AC smoke check — induced email-capture failure: temporarily
   monkeypatch `email_classification.run_capture_for_agent` (or
   `outlook_com.list_recent_mail`) in-process to raise
   `outlook_com.OutlookUnavailable("INDUCED-VERIFY: simulated Outlook
   failure")` for the email-capture branch only, then call
   `run_capture_and_record_completion()`. Confirm: no exception escapes
   the call; `vault_writer.load_agent_history("email-capture")`'s last
   entry is `kind: "run_error"`, text containing "INDUCED-VERIFY:
   simulated Outlook failure"; the function's own return value is `[]`;
   meeting-capture's own branch still ran and recorded its own
   `"run_event"` entry independently (proving Scenario 3 — one agent's
   failure does not suppress the other's success). Revert the monkeypatch
   immediately after.
3. Non-AC smoke check — `record_capture_run_completed()` gating: capture
   `.second-brain/last_capture_run.json`'s `finished_at` value
   immediately before step 2's induced failure, re-check it immediately
   after. Confirm it is **unchanged** (the failed tick did not advance
   it) — proving the "only reached when nothing raised" semantics are
   preserved. Then re-run `run_capture_and_record_completion()` with the
   monkeypatch reverted (a genuinely successful tick) and confirm
   `finished_at` **does** advance.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Meeting-capture's Autonomous branch appends a `"run_event"` history
      entry on a successful run — "Capture run completed — N meeting(s)
      filed" — parity with email-capture's existing behavior
- [x] Both capture steps' `run_capture_for_agent(...)` calls are each
      independently wrapped; an exception from either is caught and
      recorded as a `"run_error"`-kind entry with the real exception text,
      never left to propagate
- [x] One capture step's failure does not prevent the other's own
      success (or failure) from being independently recorded
- [x] `record_capture_run_completed()` fires only when neither step
      failed this tick — its prior "only reached when nothing raised"
      behavior is unchanged
- [x] `run_capture_and_record_completion`'s return value contract is
      unchanged (still exactly email-capture's own results list)
- [x] `meeting_classification.py` is not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `meeting_classification.py`, `classify_recent_emails`,
  `classify_recent_meetings` — none of these are modified; the funnel
  closes the gap at the orchestration call site only.
- `app/business/agent_activity.py`/`app/api/agent_activity_router.py`/any
  frontend page — `T02`-`T04`.
- General exception-catching/logging middleware for the ASGI application
  as a whole — the story's own Non-Goals.
- Retrofitting/reconstructing run outcomes recorded before this fix
  shipped — the story's own Non-Goals.

---

## Context / Notes

This task has no dependency on `T02`-`T04` and can be built first or in
parallel — it is a self-contained fix to an already-`Done` orchestration
function, unrelated to the new activity-page surface's own read path
(which `T02` builds independently against whatever history entries exist
by the time it runs).

Full reasoning for the fix-site choice (call site inside
`run_capture_and_record_completion`, not inside
`classify_recent_emails`/`classify_recent_meetings` themselves) and the
`record_capture_run_completed()` gating decision:
`Implementation/Architecture/architecture.md` → "Agent Activity & Error
Observability (REQ-SB-11-US-01)".

---

## Implementation Log

**Built 2026-08-13.** Composed directly around the REAL current file, not
the task's own sample — `email_classification.py` had already gained an
unconditional `vault_indexing.rebuild_index()` call (SPRINT-025,
`ADR-024`) between when this task was authored and when it was built.
**Scope-internal judgment call (logged for human spot-check, not an
escalation):** kept `vault_indexing.rebuild_index()` unconditional,
running on every tick regardless of either capture step's own
success/failure, placed immediately before the (now-gated)
`record_capture_run_completed()` call — re-indexing after a
partial-failure tick still correctly reflects whatever the other,
non-failing step actually wrote, and SPRINT-025's own design intent was
"indexing is core plumbing, not an Agents Map agent action," which this
preserves. The task's own literal code sample didn't address this
interaction (predates SPRINT-025 landing), so this is a same-scope
composition decision, not a deviation from any locked AC/Constraint.

**Manual verification — all real, live, against the real vault/Outlook
(no mocks, no automated test tooling exists yet):**

1. **Meeting-capture success parity (Tests step 1):** the real
   app-start scheduler tick (triggered by starting the real backend,
   `uvicorn app.main:app --port 8001`) produced a real new
   `meeting-capture` `"run_event"` entry — `"Capture run completed —
   37 meeting(s) filed"` — where none would have existed before this
   fix. Confirmed via `vault_writer.load_agent_history("meeting-capture")`
   through the live `GET /agent-activity` response (T02/T03 already
   landed at verification time) and directly via Python shell. PASS.
2. **Induced email-capture failure + Scenario 3 (Tests step 2):** a
   throwaway in-process script (per this project's own established
   monkeypatch-technique pattern) monkeypatched
   `email_classification.run_capture_for_agent` to raise
   `outlook_com.OutlookUnavailable("INDUCED-VERIFY: simulated Outlook
   failure")` for the `"email-capture"` branch only, then called the
   real, unmodified `run_capture_and_record_completion()`. Observed: no
   exception escaped the call; `email-capture`'s last history entry was
   `kind: "run_error"`, text `"Capture run failed — INDUCED-VERIFY:
   simulated Outlook failure"`; the function's return value was `[]`;
   `meeting-capture`'s own branch independently ran and recorded its own
   `"run_event"` (`"Capture run completed — 37 meeting(s) filed"`) —
   proving one agent's failure does not suppress the other's own
   success. PASS.
3. **`record_capture_run_completed()` gating (Tests step 3):**
   `last_capture_run.json`'s `finished_at` was captured immediately
   before/after step 2's induced failure — confirmed **unchanged**
   (`2026-08-13T11:46:21.545543+00:00` both before and after). A
   follow-up genuinely successful tick (monkeypatch reverted) confirmed
   `finished_at` **does** advance
   (`2026-08-13T11:50:06.810301+00:00`) and `email-capture`'s last
   entry reverted to `kind: "run_event"`. PASS.

Every AC-tagged locked-scenario check for this fix's own observable
effect (Scenario 2/3) is re-confirmed screen-level in `T04`'s
Implementation Log (`AC-02`/`AC-03`), per this story's own decomposer
note that this task carries no AC of its own.

No `meeting_classification.py` change (confirmed — file untouched).
Return-value contract unchanged (confirmed — `[]` on both non-Autonomous
mode and a caught failure). Both `try/except` blocks are independent
(confirmed live, step 2 above).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: the
`vault_indexing.rebuild_index()` placement decision above is a
scope-internal judgment call within an already-`Accepted` pattern
(`ADR-024`), not a new assumption/ADR/escalation; every locked
Constraint was honored and verified live.
