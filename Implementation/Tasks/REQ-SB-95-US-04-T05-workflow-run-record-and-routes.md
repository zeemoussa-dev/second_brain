---
id: REQ-SB-95-US-04-T05
title: Workflow runs — the run record, one-step-at-a-time routes, per-step confirmation and the composed report
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T03, REQ-SB-95-US-03-T04]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-04-T05 — Workflow Runs, Ordered by the Framework

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make "in order", "no skipped step", "no invented step" and "reports what the
Workflow says is reported" properties of a run record rather than promises by a
model — the framework hands back exactly one next step at a time.

---

## Starting State → End State

**Before / Inputs:**

- Workflows are stored, validated and reachable over HTTP (`T01`–`T03`).
- The Action call gate, dispatch by kind and the confirmation grant are
  complete (`REQ-SB-95-US-03-T02`/`T03`/`T04`).

**After / Outputs:**

- `app/data_access/workflow_runs.py` — raw I/O over
  `<DATA_PATH>/data/WorkflowRuns/<run_id>.json`: the workflow id, the ordered
  steps, each step's status and outcome, and the Action-call ids it produced.
- A run engine (business layer) that:
  - starts a run from a Workflow id;
  - returns **exactly one** next step at a time, in documented order;
  - **refuses to advance** until the current step's outcome is recorded;
  - dispatches every step through the existing Action gate — same validation,
    same refusals, same ledger;
  - pauses visibly on a confirmation-marked step at an
    `awaiting_confirmation` Action-call record;
  - composes the report back **from the recorded step outcomes**, so a failed
    step is never reported as done.
- Routes: `POST /workflows/{workflow_id}/run`, fetch the one next step, report
  that step's outcome.

---

## Files to Modify

- `src/backend/app/data_access/workflow_runs.py` (new)
- `src/backend/app/business/logic/workflow_run.py` (new — the run engine)
- `src/backend/app/api/workflows_router.py` (the three run routes)
- `src/backend/tests/test_workflow_runs.py` (new)

---

## Constraints

- Inherits from parent story.
- **Every step goes through the `ADR-033` Action gate unchanged** — no second
  validation path, no bypass, no new dispatch mechanism.
- **Per-step confirmation reuses `REQ-SB-95-US-03-T04`'s mechanism unchanged.**
- A `skill` step is **authorised, not performed** by the app; a `ui` step is
  reported to the operator as theirs to do and does not block the run from
  recording it; an `http` step is performed by the app.
- **Never run every step server-side inside one call** (`ADR-034` rejected it
  explicitly) — a confirmation pause inside one long request would be invisible
  and un-resumable.
- `WorkflowRuns/` is instance data: excluded from export, never in the repo.
- An abandoned run stays open and visible — it must never look complete.

---

## Tests

**Automated tests** — `src/backend/tests/test_workflow_runs.py`, run with
`pytest tests/test_workflow_runs.py` from `src/backend`, over
`httpx.ASGITransport(app=app)` with all stores on a tmp dir.

1. `[REQ-SB-95-US-04-AC-03]` Start a run of a three-step Workflow; assert
   exactly one next step is returned and it is step 1.
2. `[REQ-SB-95-US-04-AC-03]` Ask for the next step again without recording step
   1's outcome; assert the same step 1 is returned and the run did not advance.
3. `[REQ-SB-95-US-04-AC-03]` Record step 1's outcome, then fetch; assert step 2
   is returned and the run record holds step 1's recorded outcome.
4. `[REQ-SB-95-US-04-AC-03]` With step 2 marked as needing confirmation, assert
   fetching it opens an `awaiting_confirmation` Action-call record, that the run
   pauses there, and that it only advances once the operator confirms (and
   records `declined` with no advance when declined).
5. `[REQ-SB-95-US-04-AC-03]` Attempt to report an outcome for a step that is not
   the current one, and for a step id not in the Workflow; assert both are
   refused — no skipping, no invented step.
6. `[REQ-SB-95-US-04-AC-03]` Fail step 2 (scoped in-process monkeypatch of the
   dispatched call); assert the composed report names that step as failed and
   never as done, and that the run record carries every documented step.
7. `[REQ-SB-95-US-04-AC-03]` Assert the run record's step list equals the
   Workflow's documented steps in the documented order, with nothing added.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-03]` With the backend running, start a real run of a
   real two-step Workflow over loopback, step it through, confirm the pause at
   the confirmation-marked step and the real composed report at the end against
   the real run file on disk.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `WorkflowRuns/<run_id>.json` record with per-step status and outcome
- [ ] Exactly one next step at a time; no advance without a recorded outcome
- [ ] Every step dispatched through the existing Action gate, confirmation reused
- [ ] Report composed from recorded outcomes only
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Telling an agent which Workflows exist and when each applies — `T06`.
- Any screen over runs — not in this story.
- Scheduling a Workflow, branching, loops, conditional steps (story Non-Goals).

---

## Context / Notes

`architecture.md` → **§Workflow Runs — Ordered by the Framework**; `ADR-034` is
this task's spine, including the four rejected alternatives — read them before
choosing any shortcut, because each shortcut is one of them.

---

## Implementation Log

_(Filled in by the coder.)_
