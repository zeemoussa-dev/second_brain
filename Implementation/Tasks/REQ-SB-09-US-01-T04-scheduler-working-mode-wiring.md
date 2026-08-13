---
id: REQ-SB-09-US-01-T04
title: Wire To-Do capture into REQ-SB-07's existing hourly scheduled run, gated by working mode
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-09-US-01-T03, REQ-SB-11-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T04 — Wire To-Do capture into the existing scheduled run

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

To-Do capture runs automatically on the exact same recurring schedule
email/meeting capture already run on (hourly, once on app start, and
catching up a missed run) — a third gated block in
`run_capture_and_record_completion`, structurally identical to the
existing `"meeting-capture"` one, with **zero** changes to
`app/scheduling/capture_scheduler.py` (`ADR-027` point 5). Also resolves
`agent_registry.py`'s `"todo-capture"` placeholder "Task source" value.

**Real cross-story dependency, confirmed by direct reading — not
assumed:** `REQ-SB-11-US-01-T01` (`status: Ready`, not yet built)
independently rewrites this exact same function — wrapping each
Autonomous branch's `run_capture_for_agent(...)` call in its own
`try/except`, adding a new `"run_error"`-kind history entry on failure,
and making `record_capture_run_completed()` conditional on neither step
having failed this tick. This task is written to build **on top of that
already-landed shape** (see `depends_on`, above) — not the older,
unwrapped shape `REQ-SB-09-US-01`'s own architect pass (`ADR-027`)
happened to read the file as, before `REQ-SB-11-US-01-T01` existed as a
concrete task. See `## Context / Notes` for the full reasoning.

---

## Starting State → End State

**Before / Inputs (the shape AFTER `REQ-SB-11-US-01-T01` has landed —
this task's own real starting point, per its `depends_on`):**
- `run_capture_and_record_completion`'s `email_mode`/`meeting_mode`
  Autonomous branches each wrap their own `run_capture_for_agent(...)`
  call in an independent `try/except Exception as exc:`, appending a
  `"run_event"` entry on success or a `"run_error"` entry on a caught
  exception; two local booleans (`email_capture_failed`/
  `meeting_capture_failed`) track whether either branch's `try/except`
  fired; `vault_writer.record_capture_run_completed()` is called only
  when neither did (see `REQ-SB-11-US-01-T01`'s own `## Files to Modify`
  for the exact literal code this task's own edit lands on top of).
- `run_capture_for_agent(agent_id, limit)` dispatches `"email-capture"` and
  `"meeting-capture"` only; any other `agent_id` raises `ValueError`.
- `agent_registry.py`'s `"todo-capture"` agent already exists (pre-seeded
  ahead of this story) with a placeholder `"Task source"` setting value:
  `"Open question — resolved at /spec (REQ-SB-09)"`.
- `T03` added `todo_classification.classify_recent_todos()`.

**After / Outputs:**
- `run_capture_for_agent` gains a `"todo-capture"` branch calling
  `todo_classification.classify_recent_todos()`.
- `run_capture_and_record_completion` gains a third gated block for
  `"todo-capture"`, structurally identical to the (post-`REQ-SB-11-US-01-
  T01`) `meeting_mode` block — its own `try/except`, its own
  `todo_capture_failed` boolean, `"run_event"`/`"run_error"` entries on
  success/failure, Supervised proposal, Manual silent skip — and the
  trailing `record_capture_run_completed()` gate is extended to also
  check `not todo_capture_failed`.
- `agent_registry.py`'s `"todo-capture"` "Task source" value is updated to
  `"Outlook Tasks folder"`.
- `app/scheduling/capture_scheduler.py` is **unchanged**.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:

  1. Change the existing import line
     ```python
     from app.business import (
         customer_hub_linking,
         meeting_classification,
         pending_approval_registry,
         people_extraction,
         working_mode_registry,
     )
     ```
     to
     ```python
     from app.business import (
         customer_hub_linking,
         meeting_classification,
         pending_approval_registry,
         people_extraction,
         todo_classification,
         working_mode_registry,
     )
     ```
     (Alphabetical order preserved; no other import line changes. If
     `REQ-SB-11-US-01-T01` has already landed, this import tuple already
     matches this shape minus `todo_classification` — add only that
     entry.)

  2. In `run_capture_for_agent`, add a `"todo-capture"` branch before the
     final `raise ValueError`:
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
         if agent_id == "todo-capture":
             return todo_classification.classify_recent_todos()
         raise ValueError(f"No background capture step for agent_id={agent_id!r}")
     ```
     (Only the new `if agent_id == "todo-capture":` branch is added,
     directly after the existing `"meeting-capture"` branch and before
     the existing `raise ValueError` line — every other line in this
     function is unchanged.)

  3. **Re-read the real current `run_capture_and_record_completion` before
     editing it** — by the time this task builds, it must already reflect
     `REQ-SB-11-US-01-T01`'s own landed shape (the `email_capture_failed`/
     `meeting_capture_failed` booleans, each branch's own `try/except`,
     the conditional trailing call). Add a third gated block, structurally
     identical to the existing (post-fix) `meeting_mode` block, directly
     below it and directly above the trailing `if not email_capture_failed
     and not meeting_capture_failed: vault_writer.
     record_capture_run_completed()` / `return results` lines — extending
     that same `if` condition to also check the new boolean:
     ```python
         todo_mode = working_mode_registry.get_agent_working_mode("todo-capture")
         todo_capture_failed = False
         if todo_mode == "autonomous":
             try:
                 todo_results = run_capture_for_agent("todo-capture")
             except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-11), same shape as the email/meeting branches above
                 todo_capture_failed = True
                 vault_writer.append_agent_history_entry(
                     "todo-capture",
                     "run_error",
                     f"Capture run failed — {exc}",
                 )
             else:
                 vault_writer.append_agent_history_entry(
                     "todo-capture",
                     "run_event",
                     f"Capture run completed — {len(todo_results)} task(s) filed",
                 )
         elif todo_mode == "supervised":
             approval = pending_approval_registry.create_pending_approval(
                 agent_id="todo-capture",
                 trigger="background",
                 action_id=None,
                 description="Run the scheduled To-Do capture step — checks "
                             "the Outlook Tasks folder for new/changed tasks "
                             "and files them into the vault.",
             )
             vault_writer.append_agent_history_entry(
                 "todo-capture",
                 "proposal",
                 f"Proposed — {approval['description']} Awaiting your approval.",
                 pending_approval_id=approval["id"],
             )
         # else: manual — stays dormant this tick, no record, no history entry

         if not email_capture_failed and not meeting_capture_failed and not todo_capture_failed:
             vault_writer.record_capture_run_completed()
         return results
     ```
     (i.e.: insert the `todo_mode`/`todo_capture_failed` block directly
     after the existing `meeting_mode` block, and extend — never
     duplicate — the existing trailing `if not email_capture_failed and
     not meeting_capture_failed:` condition to also require `not
     todo_capture_failed`, replacing that one line. Do not reorder or
     otherwise alter the `email_mode`/`meeting_mode` blocks above it.)

- `src/backend/app/business/agent_registry.py`:
  - Change the `"todo-capture"` agent's `"Task source"` setting value from
    `"Open question — resolved at /spec (REQ-SB-09)"` to
    `"Outlook Tasks folder"` — an ordinary data-only registry edit
    (`ADR-027` point 5). No other line in this file changes.

---

## Constraints

- Inherits from parent story (`ADR-005` extended, not rewritten; `ADR-027`
  point 5).
- **This task assumes `REQ-SB-11-US-01-T01` is `Done` before it starts
  (`depends_on`, above).** If, for any reason, this task is built while
  `REQ-SB-11-US-01-T01` is still not `Done`, stop and escalate rather than
  building against the older unwrapped shape — the two shapes are
  materially different (no `try/except`, no `_failed` booleans, no
  `"run_error"` kind) and silently building against the wrong one would
  either conflict with or be immediately overwritten by the sibling
  task's own edit.
- Must NOT modify `classify_recent_emails`, `meeting_classification.py`,
  `app/scheduling/capture_scheduler.py`, the manual `POST
  /poc/classify-emails`/`POST /poc/classify-meetings` endpoints, or any
  line in `email_classification.py`/`agent_registry.py` beyond what is
  specified above.
- Must not change `run_capture_and_record_completion`'s existing return
  shape (still exactly the email-capture results list) — To-Do capture is
  a side-effecting addition only, matching the existing `meeting_mode`
  block's own precedent exactly.
- The new `todo_mode` block must wrap its own `run_capture_for_agent(
  "todo-capture")` call in its own independent `try/except` — a
  `"todo-capture"` failure must never suppress `"email-capture"`'s or
  `"meeting-capture"`'s own success (or failure) being recorded this
  tick, and vice versa — the same independent-per-branch funnel
  `REQ-SB-11-US-01-T01` establishes for the first two branches.
- `record_capture_run_completed()`'s trailing gate must check all THREE
  `_failed` booleans (extend the existing condition, never leave the
  older two-boolean condition in place alongside a separate check).
- Call order matters: the existing `email_mode` block, then the existing
  `meeting_mode` block, then this new `todo_mode` block, then the
  (extended) trailing gate + `return results` — matching `ADR-027` point
  5's own specified ordering (third pipeline, rides the same tick).
- **Separate cross-story note, no additional `depends_on` edge needed:**
  `REQ-SB-01-US-01-T04` (`status: Ready`) independently adds one
  **unconditional** `vault_indexing.rebuild_index()` call immediately
  before this function's existing final `vault_writer.
  record_capture_run_completed()` call — not gated by any capture step's
  own working mode or `_failed` boolean. That call already covers To-Do
  capture's own vault writes; **do not add a second index-refresh call
  here.** This edit targets a different anchor point (immediately before
  the trailing `record_capture_run_completed()` call, wherever it
  currently sits) and is order-independent with this task's own edit
  regardless of which of the two lands first — re-read the real current
  file before editing either way.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-09-US-01-AC-04]** With the real Outlook desktop client
   running and at least one real Outlook Task in the Tasks folder, and
   `"todo-capture"`'s working mode confirmed `"autonomous"` (the
   self-healing default), start the dev server
   (`.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from
   `src/backend`). This fires the unconditional app-start trigger
   (`capture_scheduler.run_capture_if_idle` →
   `email_classification.run_capture_and_record_completion`). Confirm,
   via `Work/Tasks/` before/after, that at least one Task note was
   created or topped-up as a direct result of this single app-start
   call — with no separate manual step, no separate scheduled job, and
   no call made directly to `todo_classification.classify_recent_todos()`
   outside of this trigger. Confirm `app/scheduling/capture_scheduler.py`
   itself was not modified by this task (diff check) and still shows
   exactly one job (`_HOURLY_CAPTURE_JOB_ID`).
2. Non-AC smoke check: confirm (via code inspection)
   `run_capture_and_record_completion`'s return value is still exactly
   the email-capture results list (unchanged shape) — To-Do capture is
   not reflected in the return value, only as a side effect.
3. Non-AC smoke check: confirm `vault_writer.load_agent_history(
   "todo-capture")`'s last entry is `kind: "run_event"` with text matching
   `"Capture run completed — N task(s) filed"` after step 1's real run.
4. Non-AC smoke check: temporarily monkeypatch
   `todo_classification.classify_recent_todos` in-process to raise a real
   exception, call `run_capture_and_record_completion()` directly, and
   confirm: no exception escapes the call; `load_agent_history(
   "todo-capture")`'s last entry is `kind: "run_error"` with the real
   exception text; `email-capture`'s and `meeting-capture`'s own branches
   still ran and recorded their own outcomes independently (one branch's
   failure does not suppress the others' — the same funnel property
   `REQ-SB-11-US-01-T01`'s own Scenario 3 established for the first two
   branches); `.second-brain/last_capture_run.json`'s `finished_at` did
   NOT advance for this failed tick. Revert the monkeypatch and confirm a
   subsequent genuine run advances `finished_at` again.
5. Non-AC smoke check: set `"todo-capture"`'s working mode to
   `"supervised"` (via `PATCH /agents/todo-capture` or directly editing
   `.second-brain/agent_working_modes.json`), trigger a capture run, and
   confirm a new `trigger="background"` pending-approval record was
   created for `"todo-capture"` and a `"proposal"` history entry was
   appended — no Task note was written as a direct result of this tick
   while Supervised. Set it back to `"autonomous"` afterward.
6. Non-AC smoke check: confirm `agent_registry.py`'s `"todo-capture"`
   entry's `"Task source"` setting value now reads `"Outlook Tasks
   folder"` via `GET /agents/todo-capture`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_capture_and_record_completion` runs To-Do capture on every
      trigger (app-start and hourly), gated by `"todo-capture"`'s own
      working mode, on the same tick as email/meeting capture
- [ ] The `"todo-capture"` branch's own `try/except` records a
      `"run_event"` entry on success or a `"run_error"` entry on failure,
      independent of the other two branches' own outcomes
- [ ] `record_capture_run_completed()` fires only when none of the three
      branches failed this tick
- [ ] `app/scheduling/capture_scheduler.py` requires zero changes and is
      untouched by this task
- [ ] `run_capture_and_record_completion`'s return shape is unchanged
- [ ] `agent_registry.py`'s `"todo-capture"` "Task source" value reads
      `"Outlook Tasks folder"`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to the concurrency guard, `IntervalTrigger`, or
  misfire/coalesce configuration in `capture_scheduler.py` — untouched.
- The vault-index-refresh call — already covered by
  `REQ-SB-01-US-01-T04`'s own unconditional addition; see this task's own
  Constraints, above.
- A manual on-demand trigger endpoint for To-Do capture — not built for
  this story (see `T03`'s own Out of Scope).
- Re-verifying `REQ-SB-11-US-01-T01`'s own locked behavior (the email/
  meeting branches' `try/except`/`"run_error"` shape) — that task's own
  `## Tests` cover it; this task only adds a third, structurally
  matching branch.

---

## Context / Notes

**Why this task carries a real cross-story `depends_on` edge, unlike
`REQ-SB-01-US-01-T04`'s own unconditional index-rebuild call (see the
parent story's own decomposer Notes for that comparison):** the two
situations look similar (two sibling stories' tasks both touch
`run_capture_and_record_completion`) but are NOT the same shape.
`REQ-SB-01-US-01-T04`'s edit is a single, unconditional call added at a
fixed anchor point, valid regardless of what else exists in the function
around it — genuinely order-independent. `REQ-SB-11-US-01-T01`'s edit
changes the function's own CONTROL FLOW (wraps existing calls in
`try/except`, introduces new local `_failed` booleans, and makes the
trailing `record_capture_run_completed()` call conditional on them) — a
new `todo_mode` block written against the OLD (unwrapped) shape would
either (a) look inconsistent with its two sibling branches once
`REQ-SB-11-US-01-T01` lands afterward, or (b) if `REQ-SB-11-US-01-T01`
lands first, silently omit the new `todo_capture_failed` boolean from the
trailing gate's condition, quietly breaking that story's own Scenario 3
guarantee for the third branch. This is a genuine, structural build-order
dependency, not a defensive over-caution — hence the explicit
`depends_on` edge onto `REQ-SB-11-US-01-T01`, a concrete existing task ID
(that story is already decomposed, `status: Ready`), not a placeholder.

Mirrors `REQ-SB-08-US-01-T04`'s own precedent for the "one additional
gated block, zero scheduler changes" shape, but this task's own literal
code sample is written directly against `REQ-SB-11-US-01-T01`'s
post-fix function shape (not Meeting's own original, pre-`REQ-SB-11`
two-branch sample) — per this project's own "compose around the real
current file" pattern (`Implementation/Learnings.md`), applied here
proactively (before build time) because the target shape is already
fully known from `REQ-SB-11-US-01-T01`'s own concrete task file, not
left to the coder to reconcile live.

---

## Implementation Log (built 2026-08-13)

Confirmed `REQ-SB-11-US-01-T01` was `Done` before starting (per this
task's own Constraint) — read the REAL current
`email_classification.py` fresh: it already had the post-fix
`email_capture_failed`/`meeting_capture_failed` two-boolean shape from
`REQ-SB-11-US-01-T01`, PLUS `SPRINT-025`'s own unconditional
`vault_indexing.rebuild_index()` call immediately before the trailing
gate — both composed around exactly as this task's own Context/Notes
anticipated. Added the `todo_mode` block directly after the existing
`meeting_mode` block and before the `vault_indexing.rebuild_index()`
call; extended the trailing `if not email_capture_failed and not
meeting_capture_failed:` condition to `and not todo_capture_failed`, one
line, no duplication. Added the `"todo-capture"` branch to
`run_capture_for_agent`. Updated `agent_registry.py`'s `"todo-capture"`
"Task source" value to `"Outlook Tasks folder"`.

**[REQ-SB-09-US-01-AC-04] PASS.** Started a fresh, explicitly-controlled
`uvicorn` instance (port 8010, per this project's own "don't trust a
stray dev-server process" precedent — two genuinely stray Vite
processes were separately found and killed later for the frontend
check, same precedent). The unconditional app-start trigger
(`capture_scheduler.run_capture_if_idle` →
`run_capture_and_record_completion`) fired automatically — no manual
trigger, no direct call to `todo_classification.classify_recent_todos()`
outside this one trigger. Confirmed via
`vault_writer.load_agent_history("todo-capture")`: a fresh `run_event`
entry, `"Capture run completed — 100 task(s) filed"`
(`2026-08-13T12:35:49Z`), and `Work/Tasks/` grew from 23 to 82 real
files as a direct result. `capture_scheduler.py` confirmed untouched
(`git diff` — zero output). `run_capture_and_record_completion`'s return
value confirmed unchanged (still exactly email-capture's own list).

**Non-AC smoke checks, all PASS:**
- `agent_registry.py`'s `"todo-capture"` entry's "Task source" confirmed
  `"Outlook Tasks folder"` via real `GET /agents/todo-capture`.
- **Induced failure (independent-branch-funnel):** monkeypatched
  `todo_classification.classify_recent_todos` in-process to raise
  `RuntimeError("INDUCED-VERIFY: ...")`, called the real, unmodified
  `run_capture_and_record_completion()` directly. No exception escaped;
  `todo-capture`'s last entry was `kind: "run_error"` with the real
  exception text; `email-capture`'s and `meeting-capture`'s own branches
  BOTH still ran and recorded their own fresh `run_event` successes
  independently (proving one branch's failure does not suppress the
  others'); `last_capture_run.json`'s `finished_at` stayed
  byte-identical before/after the induced failure (the trailing gate
  correctly did not fire).
- **Recovery:** reverted the monkeypatch (bounding only the real Outlook
  data source to a small real subset, to avoid a second ~100-item
  Compass sweep already proven by the `AC-04` check above) and called
  `run_capture_and_record_completion()` again — `finished_at` genuinely
  advanced, confirming the gate recovers on a real subsequent success.
- **Supervised mode:** set `"todo-capture"` to `"supervised"`, ran a
  real capture tick — `Work/Tasks/` file count unchanged (82 → 82, no
  write while Supervised), a real `trigger="background"` pending
  approval was created with a `"proposal"` history entry. Reverted to
  `"autonomous"` and declined the resulting test pending-approval
  afterward (cleanup, avoiding stale test debris in Pending Approvals).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: `REQ-SB-11-US-01-T01`
was confirmed `Done` and composed around correctly (not the older,
unwrapped shape); `REQ-SB-01-US-01-T04`'s own unconditional index-rebuild
call required zero interaction (confirmed order-independent, as its own
Constraints anticipated); every locked AC and Constraint verified live.
