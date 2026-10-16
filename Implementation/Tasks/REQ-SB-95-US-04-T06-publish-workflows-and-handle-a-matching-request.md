---
id: REQ-SB-95-US-04-T06
title: Publish Workflows into agent context and handle a matching request end-to-end
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T05, REQ-SB-95-US-03-T01]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-04-T06 — Publication + a Matching Request, End to End

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Tell the agent which Workflows exist and when each applies, so that a real
request of that kind starts a real framework-driven run — the agent recognises
the intent, it does not drive the order.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-03-T01` publishes the Action catalogue as a marker-delimited
  auto-generated block in each agent's SOUL.md, republished by `ActionManager`
  on every change.
- The run engine and its routes exist (`T05`) but nothing tells an agent a
  Workflow exists.

**After / Outputs:**

- The same published block (or a sibling block in the identical idempotent
  marker shape) lists the Workflows available to that agent: the kind of
  request each handles, and that the way to act on one is to start a run.
- `WorkflowManager.create()` / `update()` / `delete()` trigger republication,
  exactly as `ActionManager` does.
- The agent's runner path can start a run and step through it, receiving one
  step at a time.
- A request of a published kind is handled by the documented Workflow: the
  steps run in order, confirmation is asked at exactly the marked steps, and
  the report back is the one the Workflow defines.

---

## Files to Modify

- `src/backend/app/business/core/agents/agent_manager.py`
- `src/backend/app/business/core/workflows/workflow_manager.py` (the republish trigger)
- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/scripts/` (the runner Skill gains the start-run / next-step / report-outcome calls — same script family `REQ-SB-95-US-03-T05` created)
- `src/backend/tests/test_workflow_publication.py` (new)

---

## Constraints

- Inherits from parent story.
- **Publication says which Workflows exist and when each applies; the framework
  runs them** (`ADR-034`). Do not recite the steps into context and trust the
  model — that is the rejected alternative.
- Idempotent, marker-delimited, derived, never hand-edited — same discipline as
  the Action block; no duplicate blocks, no mutation of hand-authored text.
- The run engine remains the only thing that decides order. Nothing in the
  published text may be load-bearing for ordering, skipping or reporting.
- Existing agent behaviour is otherwise unchanged.

---

## Tests

**Automated tests** — `src/backend/tests/test_workflow_publication.py`, run
with `pytest tests/test_workflow_publication.py` from `src/backend`.

1. `[REQ-SB-95-US-04-AC-03]` Compose an agent's SOUL text with two Workflows
   published; assert each is listed with the kind of request it handles and the
   start-a-run instruction, between markers, with nothing outside the markers
   changed.
2. `[REQ-SB-95-US-04-AC-03]` Change the Workflow catalogue and assert
   republication happened automatically and idempotently (one marker pair, new
   content, surrounding text byte-identical).
3. `[REQ-SB-95-US-04-AC-03]` Drive the runner script through a published
   Workflow against the real app transport: assert it starts a run, receives
   step 1, reports its outcome, receives step 2, and that the final report it
   relays is the run engine's composed report — not text the script assembled
   itself.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-03]` With the backend running and the runner Skill
   deployed to a real Hermes profile, make a real request of the published kind
   in a real chat. Confirm, against the real `WorkflowRuns/<run_id>.json` on
   disk: the documented steps ran in the documented order, confirmation was
   asked at exactly the marked steps, the report back matches what the Workflow
   defines, and no extra step was invented or documented step skipped. Record
   the run file's step list verbatim in the Implementation Log.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Workflows published per agent in the idempotent marker shape
- [ ] Republished automatically on every Workflow catalogue change
- [ ] A real matching request runs the documented Workflow through the run engine
- [ ] The report back comes from recorded outcomes, not from the model
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Workflows screen — `T07`.
- Inferring or suggesting Workflows from history (story Non-Goals).

---

## Context / Notes

`architecture.md` → **§Workflow Runs — Ordered by the Framework** and
**§Catalogue Publication Into Agent Context**. `ADR-034`'s first decision bullet
("Publication says which Workflows exist and when each applies; the framework
runs them. The agent recognises the intent and starts a run; it does not drive
the order") is the exact contract.

---

## Implementation Log

_(Filled in by the coder.)_
