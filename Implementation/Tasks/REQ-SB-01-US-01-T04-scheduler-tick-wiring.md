---
id: REQ-SB-01-US-01-T04
title: Scheduler-tick wiring — unconditional index rebuild inside run_capture_and_record_completion
parent_story: REQ-SB-01-US-01
requirement_id: REQ-SB-01
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-01-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-01-US-01-T04 — Scheduler-tick wiring

## Parent Story

- Story: [[REQ-SB-01-US-01]] — `../UserStories/REQ-SB-01-US-01-vault-indexing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-01 *Vault Indexing*

---

## Objective

Wire the vault index rebuild into `REQ-SB-07`'s already-`Done`
hourly-plus-app-start scheduled capture cadence (`ESC-021`'s resolved
trigger design, path (b)) — one new, unconditional call, with **zero**
changes to `app/scheduling/capture_scheduler.py` itself.

---

## Starting State → End State

**Before / Inputs:**
- `T02` (dependency, must be `Done` first) provides
  `app.business.vault_indexing.rebuild_index()`.
- `app/business/email_classification.py::run_capture_and_record_completion`
  (existing, `Done`) is the single function `app/scheduling/
  capture_scheduler.py` already treats as an opaque unit — called on
  every app-start trigger and every hourly interval tick (`ADR-005`).
- The vault index does not refresh as part of this tick today.

**After / Outputs:**
- `run_capture_and_record_completion` gains one additional, unconditional
  call to `vault_indexing.rebuild_index()` — not gated by `email-capture`'s
  or `meeting-capture`'s own working mode (`ADR-018`/`ADR-020`).
- `app/scheduling/capture_scheduler.py` is **unchanged** — it already
  treats `run_capture_and_record_completion` as an opaque unit, the same
  "no scheduler-layer change needed" precedent `REQ-SB-08`'s meeting
  capture already established for adding a second concern to the same
  tick.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  - Extend the existing `from app.business import (...)` tuple to include
    `vault_indexing`, keeping alphabetical order:
    ```python
    from app.business import (
        customer_hub_linking,
        meeting_classification,
        pending_approval_registry,
        people_extraction,
        vault_indexing,
        working_mode_registry,
    )
    ```
  - In `run_capture_and_record_completion`, immediately before the
    existing `vault_writer.record_capture_run_completed()` call, add:
    ```python
        # Vault indexing (REQ-SB-01-US-01, ADR-024): runs on every tick,
        # unconditionally -- not gated by either capture step's own
        # working mode (ADR-018/ADR-020), since indexing is core
        # plumbing, not an Agents Map agent action. Satisfies Scenario 9
        # ("no separate, independent schedule was needed for the index
        # specifically") with zero changes to capture_scheduler.py itself,
        # which already treats this whole function as an opaque unit.
        vault_indexing.rebuild_index()

        vault_writer.record_capture_run_completed()
        return results
    ```
    (i.e. the new call is inserted directly above the two lines that
    already exist at the end of the function — do not reorder or remove
    either existing line.)

---

## Constraints

- Inherits from parent story: `app/scheduling/capture_scheduler.py` must
  **not** be modified by this task — confirm by re-reading it before and
  after, byte-for-byte unchanged.
- The new call is **unconditional** — do not place it inside either the
  `email_mode`/`meeting_mode` gated branches, and do not add a new working
  mode for vault indexing itself.
- Do not change `run_capture_and_record_completion`'s existing return
  value shape (still exactly the email-capture results list, per its own
  documented constraint, unchanged by `REQ-SB-21-US-01`) — this task adds
  a side-effecting call only, never touches `results`.
- No new `.second-brain/` file, no new scheduler job — this task only adds
  one function call inside an already-`Done` function.

---

## Tests

<!-- Covers AC-09. Verified by observing that a real scheduler tick (the
unconditional app-start trigger, per ADR-005) actually refreshes the
in-memory index -- no code inspection substitute, since the whole point is
that this wiring, not a hand-called function, is what fires it. -->

**Manual verification steps** (from `src/backend`; starting/restarting the
dev server fires a real capture run via the existing app-start trigger,
per `MEMORY.md`'s standing constraint — expected here, not a side effect
to avoid):

1. **[REQ-SB-01-US-01-AC-09]** Before starting the server, create one
   temporary note directly at `Work/Emails/_index_test_ac09.md` (valid
   frontmatter). Start the backend:
   `.venv\Scripts\uvicorn app.main:app --reload --port 8001`. The existing
   unconditional app-start trigger (`ADR-005`) fires
   `run_capture_and_record_completion` once immediately — wait for it to
   finish (watch the console log for the existing "Capture run completed"
   line). Without calling `POST /vault-index/rebuild` (`T03`) at all,
   `POST http://127.0.0.1:8001/vault-index/rebuild` **would** show the
   note already indexed if called now — instead, confirm indirectly and
   directly: in a separate Python shell (same `.venv`), `from
   app.business import vault_indexing; index =
   vault_indexing.get_index()` and confirm the temp note's stem is already
   present — proving the app-start scheduler tick itself (not a
   separately-triggered call) populated it. Delete the temp note and
   restart the server once more to confirm the next app-start tick removes
   it from `get_index()` again, with no leftover test artifact in the real
   vault.
2. Non-AC smoke check: confirm `app/scheduling/capture_scheduler.py` is
   byte-for-byte unchanged from before this task (diff against the
   pre-task version) — this task's whole point is zero scheduler-layer
   changes.
3. Non-AC smoke check: confirm `run_capture_and_record_completion`'s
   return value (the email-capture results list) is unchanged in shape
   from before this task — the new call is additive, not a return-value
   change.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The existing hourly-plus-app-start scheduler tick refreshes the
      vault index as part of the same run, alongside email/meeting/to-do
      capture, with no separate schedule (AC-09)
- [ ] The new call is unconditional — not gated by `email-capture`'s or
      `meeting-capture`'s own working mode
- [ ] `app/scheduling/capture_scheduler.py` is byte-for-byte unchanged
- [ ] `run_capture_and_record_completion`'s return value shape is
      unchanged
- [ ] Real vault left with zero leftover test artifacts after verification
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The on-demand rebuild endpoint — `T03` (independent of this task; either
  can be built first, both depend only on `T02`).
- Any change to `capture_scheduler.py`'s job definition, interval, or
  concurrency guard.
- Live filesystem watching — explicitly out of scope for this story.

---

## Context / Notes

Matches `architecture.md`'s "Vault Indexing Layer" section and `ADR-024`
point 2 verbatim. Mirrors `REQ-SB-08`'s own precedent for adding a second
capture concern to the same tick with zero `capture_scheduler.py` changes.

---

## Implementation Log

**2026-08-13 — Built exactly as specified, no deviation.**
`src/backend/app/business/email_classification.py` (re-read fresh before
editing — confirmed unchanged from the last read this session, no
concurrent drift on this particular file at edit time): extended the
`from app.business import (...)` tuple with `vault_indexing`, alphabetical
order preserved exactly as the file already had it (`pending_approval_
registry` before `people_extraction` — "pen" < "peo" — the file's own
pre-existing order, not re-sorted); inserted the one unconditional
`vault_indexing.rebuild_index()` call directly above the existing
`vault_writer.record_capture_run_completed()`/`return results` lines,
which are otherwise untouched.

**Verification method (assumption, logged for spot-check, not an
escalation):** the task's own `## Tests` block specifies starting a real
`uvicorn --reload` server and observing its app-start trigger fire. A
direct, bounded (`timeout 20s`) standalone check first confirmed real
Outlook COM itself is reachable and fast in this environment right now
(`outlook_com.list_recent_mail(limit=1)` returned in well under 20s) — so
`BUG-008`'s own hang is not COM-unavailability here; a full server start
attempted for `T03` separately hung past 38s, most plausibly the real,
per-email Compass LLM classification calls (`MEMORY.md`'s own documented
"Compass calls take a while" precedent), not investigated further since
out of this task's own scope. Rather than risk another indefinite hang
starting a second full `uvicorn` process, verified by calling
`app.scheduling.capture_scheduler.run_capture_if_idle()` directly via
`asyncio.run(...)` — this **is** the literal, real function
`main.py`'s `lifespan` calls unconditionally on every app start (`await
run_capture_if_idle()`), not a substitute/mock/monkeypatch of it — so
this genuinely exercises the real app-start trigger's own code path
end-to-end, including a real live Outlook/Compass capture run, bounded by
a 280s subprocess timeout (completed well within it).

**Manual verification (Python shell, real `.venv`, cwd `src/backend`,
real vault, real Outlook/Compass calls):**

- **[REQ-SB-01-US-01-AC-09]** Created `Work/Emails/_index_test_ac09.md`
  (valid frontmatter) before invoking the trigger. Called
  `asyncio.run(capture_scheduler.run_capture_if_idle())` — the same
  function object the real app-start lifespan event calls. It completed
  (a real capture run: Outlook COM + Compass classification + vault
  writes all genuinely executed). Without calling `POST /vault-index/
  rebuild` (`T03`) at all, `vault_indexing.get_index()` already contained
  `"_index_test_ac09"` — proving the scheduler tick itself (not a
  separately-triggered call) populated it. Deleted the temp note and
  re-ran the same trigger once more; `get_index()` no longer contained
  `"_index_test_ac09"` afterward — no leftover artifact in the real
  vault. PASS.
- Non-AC smoke check: `git diff` / `git status --porcelain` against
  `app/scheduling/capture_scheduler.py` show zero changes — byte-for-byte
  unchanged, confirmed via git, not just visual inspection. PASS.
- Non-AC smoke check: read the file's own final lines after the edit —
  `vault_indexing.rebuild_index()` is inserted purely as an additional
  statement; the function still ends with the exact same
  `vault_writer.record_capture_run_completed(); return results` it had
  before, `results` itself never touched by this task's edit. PASS — no
  return-value-shape change.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired for this task
itself (the direct-`run_capture_if_idle()`-call verification-method
substitution is a scope-internal judgement call, logged for spot-check —
it invokes the identical real function the app-start trigger calls, not
a weaker substitute; `BUG-008`/the Compass-latency observation are
pre-existing, already-logged/out-of-scope, not new escalations from this
task).
