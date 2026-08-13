---
id: REQ-SB-21-US-01-T05
title: email_classification.py — per-agent background-pipeline working-mode gate inside run_capture_and_record_completion, new run_capture_for_agent helper
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T02, REQ-SB-21-US-01-T03]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** `ADR-020`
point 4 confirms this task's own design needs no structural change — both
gated steps below (`classify_recent_emails` for email-capture,
`meeting_classification.classify_recent_meetings()` for meeting-capture)
are always `"mutates": True` actions today, so `ADR-020`'s corrected
mutates-based Supervised rule and `ADR-018`'s original trigger-based rule
produce the identical outcome for the background trigger, by construction.
**Only the AC-tag references below were renumbered** (the old `AC-05`, for
the pre-re-spec "Supervised background also waits" scenario, is now merged
into `AC-03` — the current, single "mutating action proposes+waits,
regardless of trigger" scenario) — no logic in this file's own `Files to
Modify` sample changed.

# REQ-SB-21-US-01-T05 — Background-pipeline working-mode gate

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add the two explicit, independent per-agent working-mode checks inside
`email_classification.py::run_capture_and_record_completion` (`ADR-018`
point 4) — one for `"email-capture"`, one for `"meeting-capture"` — plus
the new shared `run_capture_for_agent(agent_id, limit) -> list` helper
both this scheduled path and `T06`'s Pending-Approvals-Approve path call,
so the "which function does this agent_id's capture step call" mapping
is never duplicated. `app/scheduling/capture_scheduler.py` requires
**zero changes** — this conditionality lives entirely inside the one
function it already treats as opaque (`ADR-005`/`ADR-008` point 4).

---

## Starting State → End State

**Before / Inputs:**
- `run_capture_and_record_completion` unconditionally calls
  `classify_recent_emails(limit=limit)` then
  `meeting_classification.classify_recent_meetings()`, records completion,
  and appends one `"run_event"` history entry for `"email-capture"` only
  (meeting-capture has never had its own completion history entry —
  preserved, not introduced, by this task).
- `T02` has landed `working_mode_registry.get_agent_working_mode`.
- `T03` has landed `pending_approval_registry.create_pending_approval`
  (idempotent per `agent_id` + `trigger="background"`).

**After / Outputs:**
- New `run_capture_for_agent(agent_id, limit=10) -> list[dict]` — maps
  `"email-capture"` to `classify_recent_emails(limit=limit)`,
  `"meeting-capture"` to `meeting_classification.classify_recent_meetings()`.
- `run_capture_and_record_completion` gates each of its two existing
  internal calls independently: **Autonomous** — runs via
  `run_capture_for_agent`, exactly as today; **Supervised** — creates a
  `trigger="background"` pending-approval record (idempotent) plus a
  `"proposal"`-kind history entry, does not run the step; **Manual** —
  skips silently, no record, no history entry at all.
- Return shape unchanged: still the email-capture results list (empty
  when email-capture's own mode is non-Autonomous).

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add the import,
  alongside the existing ones:
  ```python
  from app.business import (
      customer_hub_linking,
      meeting_classification,
      pending_approval_registry,
      people_extraction,
      working_mode_registry,
  )
  from app.data_access import compass_client, outlook_com, vault_writer
  ```
  Leave `classify_recent_emails` entirely unchanged. Add the new helper
  and replace `run_capture_and_record_completion` with this gated
  version:
  ```python
  def run_capture_for_agent(agent_id: str, limit: int = 10) -> list[dict]:
      """The one place both the scheduled tick below and a
      Pending-Approvals approval (app/api/pending_approvals_router.py,
      T06) resolve "which function does this agent_id's own background
      capture step call" — so the mapping is never duplicated (ADR-018
      point 4)."""
      if agent_id == "email-capture":
          return classify_recent_emails(limit=limit)
      if agent_id == "meeting-capture":
          return meeting_classification.classify_recent_meetings()
      raise ValueError(f"No background capture step for agent_id={agent_id!r}")


  def run_capture_and_record_completion(limit: int = 10) -> list[dict]:
      """Scheduling-layer entry point (ADR-005): runs the same capture
      pipeline the manual /poc/classify-emails endpoint uses, then records
      completion via vault_writer so the shared last-run record reflects
      every scheduled run, not just manual ones. Also runs Meetings
      capture (REQ-SB-08, ADR-008) on the same tick — no second scheduled
      job, no second concurrency guard; app/scheduling/capture_scheduler.py
      requires zero changes since it already treats this function as an
      opaque unit.

      REQ-SB-21/ADR-018 point 4: each of the two capture steps below is
      now independently gated by that agent's own working mode.
      Autonomous runs the step exactly as before this story (no change to
      the default-path behaviour or history-entry text for email-capture;
      meeting-capture's Autonomous branch likewise still just calls its
      capture step with no new history entry, preserving today's exact
      no-entry behaviour rather than inventing one). Supervised creates a
      trigger="background" pending-approval record (idempotent per tick)
      plus a "proposal" history entry instead of running the step.
      Manual skips silently — no record, no history entry at all, the
      literal "stays dormant" PRD language for the one trigger context
      where Manual and Supervised are meant to differ (see
      app/api/agents_router.py, T04, for the chat/direct trigger context,
      where Manual does not gate).

      Return shape is unchanged: still exactly the email-capture results
      list (REQ-SB-08-US-01-T04's own documented constraint) — empty when
      email-capture's own mode is non-Autonomous, new user-opted-into
      behaviour, not a default-path regression, since Autonomous stays
      the default per this story's own behavior-preservation Constraint.
      """
      email_mode = working_mode_registry.get_agent_working_mode("email-capture")
      if email_mode == "autonomous":
          results = run_capture_for_agent("email-capture", limit=limit)
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
      if meeting_mode == "autonomous":
          run_capture_for_agent("meeting-capture")
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

      vault_writer.record_capture_run_completed()
      return results
  ```

---

## Constraints

- Inherits from parent story and `ADR-018` point 4.
- `classify_recent_emails` must NOT be modified — only `run_capture_and_
  record_completion` and the new `run_capture_for_agent` helper.
- `meeting_classification.py`'s own public functions must NOT be
  modified (parent story's own Constraint, restated).
- `app/scheduling/capture_scheduler.py` must NOT be modified at all — the
  gate lives entirely inside this one function's own body.
- The email-capture Autonomous branch's history-entry text and
  `vault_writer.record_capture_run_completed()` call must be
  byte-for-byte behavior-preserving relative to today — no new history
  entry is introduced for meeting-capture's own Autonomous branch (today
  has none; this task must not add one, to avoid an unrequested new
  behaviour on the default path).
- `run_capture_and_record_completion`'s return value must remain exactly
  the email-capture results list under every combination of modes —
  never include meeting-capture's own results, matching
  `REQ-SB-08-US-01-T04`'s documented return-shape constraint.
- Two explicit sequential blocks (email-capture's, then
  meeting-capture's) — no generic per-agent dispatch loop over a dict of
  handlers (`ADR-018`'s own "Alternatives Considered" rejection of this
  shape).

---

## Tests

<!-- REQ-SB-21-US-01-AC-02 (Autonomous unaffected, background trigger),
AC-03 (Supervised background propose+wait — background half of the merged
"mutating action proposes, regardless of trigger" scenario; T04 covers the
chat/direct half), and AC-06 (Manual silently skips a background trigger)
are all genuinely background-pipeline-only
scenarios — the one place this story's own gate differs by trigger
context — so all three are verified here, live, by invoking the real
scheduled entry point directly. Deliberate: every step below triggers a
real Outlook/Compass/vault-write capture attempt — be careful, per
MEMORY.md's standing caution, and confirm each mode's own expected side
effect (or lack of one) before moving to the next step. -->

**Manual verification steps** (from `src/backend`, a Python shell against
the `.venv`, real `vault_path`, real Outlook/Compass wiring — calling
`app.business.email_classification.run_capture_and_record_completion()`
directly, exactly what the scheduler itself calls once per tick):

1. **[REQ-SB-21-US-01-AC-02]** Confirm both `email-capture` and
   `meeting-capture` are `"autonomous"` (the untouched default — via
   `working_mode_registry.get_agent_working_mode`). Call
   `run_capture_and_record_completion()` **exactly once**. Confirm it
   returns the email-capture results list (same shape as before this
   task) and, via `vault_writer.load_agent_history("email-capture")`,
   the newest entry is a `"run_event"` reading `"Capture run completed —
   N email(s) filed"` — identical wording to pre-this-task behaviour,
   proving Autonomous is unaffected by the new gate for the background
   trigger too.
2. **[REQ-SB-21-US-01-AC-03]** `working_mode_registry.
   set_agent_working_mode("meeting-capture", "supervised")`. Call
   `run_capture_and_record_completion()` again. Confirm — via
   `vault_writer.load_agent_history("meeting-capture")` — a new
   `"proposal"`-kind entry was appended, and (critically) **no new
   Meeting notes were written to the vault** (spot-check: no new file
   under `Work/Meetings/` since step 1). Confirm
   `pending_approval_registry.list_pending_approvals(agent_id=
   "meeting-capture", status="pending")` now has exactly 1 record,
   `trigger: "background"`, `action_id: null`. Call
   `run_capture_and_record_completion()` a **third** time — confirm the
   pending-approvals list for `meeting-capture` still has exactly 1
   record (idempotent per tick, `T03`'s own guard), not 2.
3. **[REQ-SB-21-US-01-AC-06]** `working_mode_registry.
   set_agent_working_mode("meeting-capture", "manual")`. Call
   `run_capture_and_record_completion()` once more. Confirm — via
   `vault_writer.load_agent_history("meeting-capture")` — **no new
   history entry of any kind** was appended for `meeting-capture` by this
   call (history length unchanged from step 2's end state), and
   `pending_approval_registry.list_pending_approvals(agent_id=
   "meeting-capture", status="pending")` is unchanged (still the 1 record
   from step 2 — Manual creates no new record, but does not resolve the
   pre-existing Supervised one either).
4. Clean-up: `working_mode_registry.set_agent_working_mode
   ("meeting-capture", "autonomous")`, restoring the seed default.
   `pending_approval_registry.resolve_pending_approval(<the
   meeting-capture record's id from step 2>, "declined")` so it does not
   leak into `T06`'s own verification as stray state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (partial — background trigger) — with both agents
      Autonomous, `run_capture_and_record_completion` behaves identically
      to its pre-this-task self (return shape, history-entry text,
      `record_capture_run_completed` call)
- [ ] **AC-03** (background half — `T04` covers the chat/direct half) — a
      Supervised agent's background trigger creates a `trigger="background"`
      pending-approval record (idempotent per tick) and a `"proposal"`
      history entry, does **not** run the real capture step
- [ ] **AC-06** (partial — background trigger) — a Manual agent's
      background trigger produces no record and no history entry at all
- [ ] `run_capture_for_agent` correctly maps `"email-capture"` /
      `"meeting-capture"` to their real capture functions
- [ ] `classify_recent_emails`, `meeting_classification.py`'s public
      functions, and `capture_scheduler.py` not modified
- [ ] `run_capture_and_record_completion`'s return shape unchanged (still
      exactly the email-capture results list)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The chat/direct-action gate — `T04` (`agents_router.py`).
- `POST /pending-approvals/{id}/approve|decline` — `T06`
  (`pending_approvals_router.py`); this task only creates the pending
  record, it does not resolve it.
- Any frontend page/component — `T07`/`T08`.
- `"todo-capture"` — no real background pipeline exists for it yet
  (`REQ-SB-09` unbuilt); a future pass adds a third block following this
  exact pattern (`ADR-018` point 4).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created, later
`ADR-020` superseded points 3/5 only — this task's own scope, `ADR-018`
point 4, is unaffected by `ADR-020` and needed no rewrite, see the note at
the top of this file) — the human reviews `ADR-020` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

This is the one task whose live verification directly exercises the real
Outlook/Compass-backed scheduled pipeline multiple times in a row — read
each step fully before running it, and confirm the expected side effect
(or explicit lack of one) before proceeding to the next, per this task's
own Tests instructions.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** Read the REAL
current `email_classification.py` — matched this task's own "Before"
narrative exactly (no drift beyond what the task file already knew:
`classify_recent_emails`, `meeting_classification.classify_recent_
meetings()`, `vault_writer.record_capture_run_completed()`, one
`run_event` history entry for `email-capture`). Added the
`pending_approval_registry`/`working_mode_registry` imports and
replaced `run_capture_and_record_completion` with the gated version +
new `run_capture_for_agent` helper, exactly as specified.

**Live verification** (real backend `.venv`, real Outlook/Compass, real
vault — calling `run_capture_and_record_completion()` directly,
exactly what the scheduler itself calls):

- **[AC-02]** (background, Autonomous unaffected) Both agents confirmed
  `"autonomous"`. Called once → returned the email-capture results list
  (unchanged shape); newest `email-capture` history entry read
  `"Capture run completed — N email(s) filed"` — identical wording to
  pre-task behaviour. PASS.
- **[AC-03]** (background half — `T04` covers chat/direct)
  `meeting-capture` set `"supervised"`. Called again → a new
  `"proposal"`-kind entry appended to `meeting-capture`'s history;
  **confirmed no new Meeting note was written** — spot-checked via
  `Get-ChildItem Work/Meetings -Filter *.md | Sort LastWriteTime`, the
  most recent file's timestamp predated the tick by ~2h20m, no file
  touched at tick time. `list_pending_approvals(agent_id=
  "meeting-capture", status="pending")` → exactly 1 record, `trigger:
  "background"`, `action_id: null`. A third call left the count at
  exactly 1 (idempotent per tick, `T03`'s own guard). PASS.
- **[AC-06]** (background, Manual skips silently) `meeting-capture` set
  `"manual"`. Called once more → **zero** new history entries appended
  for `meeting-capture` (count unchanged before/after), pending count
  unchanged (still the 1 pre-existing Supervised record — Manual
  creates no new record but does not resolve the pre-existing one
  either). PASS.
- Cleanup: `meeting-capture` reset to `"autonomous"`; the leftover
  Supervised pending record declined so it did not leak into `T06`'s
  own verification.

This is the one task whose live verification directly exercises the
real Outlook/Compass-backed scheduled pipeline multiple times in a
row, per this task's own Context/Notes — each real capture call took
roughly 1.5–5 minutes end to end (Outlook COM + Compass + a full
39-meeting sweep); verified via backgrounded shell invocations with
explicit `flush=True` output rather than blocking synchronously.

Gate: `clear` — every locked AC this task carries was verified live; no
MUST-FLAG trigger fired.
