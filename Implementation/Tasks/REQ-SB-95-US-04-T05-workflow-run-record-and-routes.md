---
id: REQ-SB-95-US-04-T05
title: Workflow runs — the run record, one-step-at-a-time routes, per-step confirmation and the composed report
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1: one scope-internal judgement call — a step marked needs_confirmation whose Action is not confirmation-required is refused rather than performed, because the ADR-033 gate takes confirmation from the Action's own flag and takes no override. Optional skim; nothing blocked."
phase: P2
depends_on: [REQ-SB-95-US-04-T03, REQ-SB-95-US-03-T04]
created: 2026-10-16
updated: 2026-10-18
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

- [x] `WorkflowRuns/<run_id>.json` record with per-step status and outcome
- [x] Exactly one next step at a time; no advance without a recorded outcome
- [x] Every step dispatched through the existing Action gate, confirmation reused
- [x] Report composed from recorded outcomes only
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not appended**: `MEMORY.md` is ~86 KB against the 40 KB budget its own
      rule 1 sets, and that rule forbids appending while over budget. The one
      candidate constraint is recorded in `REVIEW-QUEUE.md` instead.
- [x] `CHANGELOG.md` entry appended

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

**2026-10-18 — Done. `AC-03` verified; one scope-internal judgement call.**

### What was built (the four files in `## Files to Modify`, nothing else)

- `app/data_access/workflow_runs.py` (new) — raw I/O over
  `<DATA_PATH>/data/WorkflowRuns/<run_id>.json`. Flat file-per-run like
  `data_access/action_calls.py`, not folder-per-id like
  `data_access/workflows.py`: a Workflow is a definition that may grow
  companion files, a run is one record of one occurrence and there will be
  very many. **Nothing deletes a run** — a run that could be removed could
  also be removed *instead of* finished (`ADR-034`: an abandoned run stays
  open and visible).
- `app/business/logic/workflow_run.py` (new) — the engine: `start_run`,
  `next_step`, `record_step_outcome`, `compose_report`.
- `app/api/workflows_router.py` — the three run routes appended, nothing
  else in that file touched.
- `tests/test_workflow_runs.py` (new) — 11 AC-tagged tests.

### How the four step states are distinguishable in the stored bytes

Not inferred, and not derived from "has an outcome been written": every step
carries a literal `status` word, written for **every** documented step from
the first write of the record. Six words, because the app really does six
different things and collapsing any pair makes at least one unreadable:

| stored `status` | means |
|---|---|
| `not_reached` | the run has not got here. Written at start for every step, so "nobody got there" is a recorded fact, not an absence to interpret |
| `running` | handed out and dispatched through the gate; nothing has reported what came of it |
| `awaiting_confirmation` | dispatched, and the gate opened an `awaiting_confirmation` call record; the run is paused here |
| `done` | an outcome was reported and it succeeded |
| `failed` | the caller reported failure, or the gate's own dispatch did |
| `refused` | the gate refused it, or the operator declined it |

Beside it, **`dispatch_outcome` keeps the gate's own word verbatim**
(`pointed_at` / `performed` / `authorised` / `failed` / `refused:*`) and is
never overwritten by what a caller later reports: what the app did and what
the caller says came of it are two different facts about one step, and
overwriting the first with the second is exactly how a `ui` step the operator
was merely pointed at comes to read as though the app performed it. The real
run file produced by the manual step shows both side by side.

### The three routes, and why there is no fourth

- `POST /workflows/{workflow_id}/run` — opens the record. Dispatches nothing:
  every step reads `not_reached`, which is what makes "holds every documented
  step and no step that is not in the Workflow" checkable from the first byte.
- `POST /workflows/runs/{run_id}/next-step` — the ONE step the run is on,
  dispatched through the gate if it has not been already. `POST`, not `GET`,
  and named `take` rather than `get`: handing a step out is what dispatches it,
  so it really performs an `http` step and really opens the confirmation
  record. A `GET` doing that would lie to every cache and retry.
- `POST /workflows/runs/{run_id}/steps/{step_id}/outcome` — records the
  outcome of the step the run is on, and refuses anything else.

No read-only "get the run" route: a run is read by asking for its next step,
which answers with the step or — when there is none — with the composed
report. A second answer to one question is two answers that can disagree.

### Verification — automated (`pytest tests/test_workflow_runs.py` from `src/backend`)

Backend suite **655 passed / 0 failed** at baseline → **666 passed / 0 failed**
after (44.1s → 39.5s). The three known order-dependent tests
(`test_health_check.py::test_health_reports_the_commit_…`,
`test_marketplace_source.py`, `test_marketplace.py::test_install_repairs_…`)
were green in both runs. The new file was also re-run with
`SECOND_BRAIN_DATA_PATH` pointed at an **empty scratch directory**: 11 passed,
and the directory contained **0 entries** afterwards.

| Tests block step | Test | Observed |
|---|---|---|
| 1 — one next step, and it is step 1 | `test_a_started_run_hands_back_exactly_one_step_and_it_is_the_first` | PASS — start writes `[not_reached, not_reached, not_reached]` and dispatches nothing; the first `next-step` answers a single step object (not a list) `('collect', 1)`, `dispatch_outcome == pointed_at`, record `[running, not_reached, not_reached]`, and the `http` target route was never entered |
| 2 — ask again, no advance | `test_asking_again_without_recording_an_outcome_returns_the_same_step` | PASS — same step id, same `call_ids`, record unchanged, and the spy AROUND the real dispatch seam counted exactly **one** dispatch |
| 3 — record, then advance | `test_recording_the_current_steps_outcome_is_what_advances_the_run` | PASS — step 1 on disk reads `status: done`, the reporter's words in `detail`, the gate's `pointed_at` still in `dispatch_outcome`; `next-step` then answers `('file', 2)` and the `http` step really ran in process, once |
| 4 — confirmation pause, confirm and decline | `test_a_confirmation_marked_step_pauses_at_an_awaiting_call_record_until_the_operator_says_yes` + `test_a_declined_confirmation_leaves_the_run_blocked_at_that_step` | PASS — a real `awaiting_confirmation` ledger row on disk with the step's own inputs, the step at `awaiting_confirmation`, the row on `GET /actions/calls/pending`, **no second call opened** when asked again, zero dispatches of that Action while paused; after `POST /actions/calls/{id}/confirm` the step advances with **two** call ids joined by `granted_by_call_id` and `authorised`. Declined: step `refused` carrying the operator's own sentence, run `blocked`, step 2 never dispatched, and it stays blocked when asked again |
| 5 — not the current step / not in the Workflow | `test_an_outcome_for_a_step_that_is_not_the_current_one_or_not_in_the_workflow_is_refused` | PASS — four 409s each carrying the engine's own sentence (not handed out yet; "none is skipped" naming the step the run is on; an invented step id with "no step was added"; an outcome word that is neither `done` nor `failed`), and the stored record is equal to what it was before all four. An unknown run id is a 404 |
| 6 — a failed step is never reported as done | `test_a_failed_step_is_reported_as_failed_and_never_as_done` | PASS — a scoped monkeypatch of the one function behind the test-only target route (route, gate and dispatch all real) gives `dispatch_outcome: failed`; the composed report reads `[done, failed, not_reached]`, `every_documented_step_done: false`, and the step after it carries `not_reached` with no call ids rather than being absent. Reporting that step `done` afterwards is a 409 |
| 7 — every documented step, in order, nothing added | `test_the_run_record_holds_every_documented_step_in_order_and_nothing_else` | PASS — step ids, action ids, inputs and confirmation flags equal to the catalogue's own `GET /workflows/{id}`, positions `[1,2,3]`; and editing the Workflow down to one step afterwards leaves the in-flight run's three steps untouched (the run snapshots at start) |

Two supporting tests beyond the Tests block: the premise pin that these tests
bring their own Action catalogue (`ESC-064`/`ESC-075`), and the start-time
refusals (unknown Workflow 404, no documented steps 409, no caller named 409,
with no run record written by any of them).

### Verification — manual (the Tests block's one manual step)

`[REQ-SB-95-US-04-AC-03]` Passed against a **disposable** backend on
`127.0.0.1:8099` with a scratch vault, scratch `SECOND_BRAIN_DATA_PATH` and a
scratch (non-existent) `HERMES_HOME_PATH` — never the operator's `:8001`, and
never the operator's data store or Hermes install. A two-step Workflow
(`summarise-and-publish`: a `ui` step, then a confirmation-required `http`
step) over real loopback HTTP:

1. start → `status: running`, both steps `not_reached`;
2. `next-step` → step `look` (position 1), `pointed_at`; asked again → the
   same call id;
3. report `done` → `next-step` → **paused**: `awaiting_confirmation`, call
   `c227cdee…`, and that call on `GET /actions/calls/pending`;
4. `POST /actions/calls/c227cdee…/confirm` → `next-step` → step `publish`
   advances, `performed`, **two** call ids, carrying the real result of the
   route it ran;
5. report `done` → `next-step` → `step: null`, `status: complete`, report
   `every_documented_step_done: true`.

The real `WorkflowRuns/067328…json` on disk was read back and matches: both
steps `done`, each with its own `dispatch_outcome` (`pointed_at` /
`performed`), `handed_out_at`, `recorded_at` and call ids. The scratch backend
was stopped afterwards.

### Scope-internal judgement calls (for human spot-check — this is the `gate: flagged`)

1. **A step marked `needs_confirmation` whose Action is not
   confirmation-required is REFUSED, not performed.** `ADR-034` says
   per-step confirmation "reuses `ADR-033`'s mechanism unchanged", and that
   mechanism takes confirmation from the **Action's own flag and from nothing
   else** (`REQ-SB-95-US-03-T04`: "an Action's confirmation flag, not the
   caller's say-so"). `call_action()` accepts no override, and
   `action_invocation.py` is outside this task's `## Files to Modify`. So the
   only two things this engine could do with such a step were refuse it or
   perform something the operator asked to be asked about first. It refuses,
   naming the step, its position, the action and what to change. The run
   blocks visibly and nothing is dispatched (asserted:
   `test_a_step_marked_for_confirmation_whose_action_needs_none_is_refused_not_performed`).
   **The residual functional gap is real** — an operator who wants confirmation
   only *inside one Workflow* cannot have it today — and the one-parameter
   change that would close it is written out in `REVIEW-QUEUE.md`. Escalating
   instead would have blocked `T05`, `T06` and `T07` over a change nobody has
   yet asked for.
2. **`next-step` on a blocked run answers 200 with the composed report, not a
   409.** A refused *operation* is a 409 carrying the engine's sentence (the
   2026-10-17 `MEMORY.md` rule, applied to all four refusals above). Asking
   where a blocked run stands is not a refused operation — and the caller who
   most needs the report is the one whose run broke, so a 409 would put it out
   of reach.
3. **The report is composed on demand and never stored on the run.** A second
   copy of a derived answer can disagree with the outcomes it was derived
   from, which is the one thing "composed from the recorded step outcomes" has
   to rule out. The run record keeps the outcomes; the report is a function of
   them.
4. **A run snapshots its steps, inputs, confirmation flags and report
   definition at start.** Editing a Workflow must not change a run already in
   flight, which could otherwise be running handling nobody authorised.
   Asserted as part of Tests-block step 7.
5. **The caller reports an outcome for every step, including an `http` one the
   app performed** — one rule with no per-kind exception — **but a dispatch the
   app itself settled is not reportable over.** A step the gate recorded as
   `failed` or `refused` is terminal, so "the app knows it failed" can never be
   talked into `done`.
6. **No switch-on site exists for this task** (the standing
   `.claude/agents/decomposer.md` rule, checked rather than assumed):
   `workflows_router` is already registered in `app/main.py` (`T03`), and
   `WorkflowRuns/` is excluded from artifact export **structurally** — export
   maps named artifact *kinds* and a run is not a kind, which
   `artifact_export.py` already states by name for both `ActionCalls/` and
   `WorkflowRuns/`. The four files in the list are the whole change.

No `ESCALATIONS.md` entry: nothing outside the four files was needed, no
shared interface changed, no ADR deviated from, no new dependency.
