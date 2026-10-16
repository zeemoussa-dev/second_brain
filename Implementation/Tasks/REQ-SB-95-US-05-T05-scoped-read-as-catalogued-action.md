---
id: REQ-SB-95-US-05-T05
title: The scoped read as a shipped, catalogued Action reached through the call gate
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-05-T04, REQ-SB-95-US-02-T02, REQ-SB-95-US-03-T02, REQ-SB-95-US-03-T03]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-05-T05 — The Scoped Read, Reached Through the Catalogue

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make the scoped entity read something an agent reaches the same way it reaches
anything else — a shipped Action whose `http` implementation names its own
route, validated by the call gate like every other action call.

---

## Starting State → End State

**Before / Inputs:**

- `T04`'s scoped read, as business logic with no HTTP surface of its own.
- `REQ-SB-95-US-02-T02`'s save-time implementation resolution (an `http`
  implementation resolves against the running app's own route table).
- `REQ-SB-95-US-03-T02`'s `POST /actions/{action_id}/call` gate and the
  Action-call ledger; `REQ-SB-95-US-03-T03`'s dispatch by implementation kind.
- `ADR-032` allows the framework to ship starter Actions, the way it ships
  Master Templates.

**After / Outputs:**

- A route exposing the scoped read (on a new or existing router — one choice,
  logged), taking the entity name and returning the resolved entity plus the
  scoped result, including the honest "did not resolve" and "ambiguous"
  results from `T03`.
- A **shipped starter Action** whose single `implementation` is `http` naming
  that route, with its inputs typed and the entity name marked required.
- An agent's call therefore goes through the gate: unknown id, missing
  required input, and an implementation that no longer resolves are refused
  exactly as for any other Action, and a caller outside `allowed_callers` is
  refused with the refusal recorded in the ledger.

---

## Files to Modify

- the route's router file (new, or the closest existing single-purpose router —
  read the real current `app/api/` convention first and log the choice)
- the shipped-starter Action definition, wherever `REQ-SB-95-US-02`'s landed
  code puts shipped starters (**read that real code before writing** — do not
  invent a second mechanism for shipping one)
- `src/backend/tests/test_scoped_read_action.py` (new)

---

## Constraints

- Inherits from parent story.
- **The gate is not re-implemented here.** This task contributes an Action and
  a route; validation, dispatch, refusal and the ledger are `US-03`'s and must
  be used unchanged.
- **No plugin named**, and the Action's description must not name a business
  vocabulary (`Customer`, `Partner`) — it is generic entity resolution.
- The route is the `http` implementation of the Action **and** may back an
  in-app surface later; the agent's door is still the Action call, not a
  private endpoint it is told about.
- If `US-02`/`US-03` have not landed when this task is picked up, it is
  **blocked**, not improvised against an imagined interface — its `depends_on`
  says so.

---

## Tests

**Automated tests** — `src/backend/tests/test_scoped_read_action.py`, run with
`pytest tests/test_scoped_read_action.py` from `src/backend`; drive the real
app with `httpx.ASGITransport(app=app)` the way the existing API tests do.

1. `[REQ-SB-95-US-05-AC-06]` Call the shipped Action through
   `POST /actions/{id}/call` with a valid caller and a resolvable entity name;
   assert the response carries the scoped read's own result (hub first, then
   evidence) and that a ledger record was written for the call.
2. `[REQ-SB-95-US-05-AC-06]` Call it with the required entity-name input
   missing; assert the gate refuses naming the missing input and that the
   scoped read was never executed (spy it).
3. `[REQ-SB-95-US-05-AC-06]` Call an unknown action id; assert the same
   refusal path as any other unknown id.
4. `[REQ-SB-95-US-05-AC-06]` Call as a caller **not** in `allowed_callers`;
   assert it is refused and that the refusal is recorded in the Action-call
   ledger with the caller and the reason.
5. `[REQ-SB-95-US-05-AC-06]` Break the implementation's target route (rename it
   in-process) and assert the Action is reported as no longer resolving, and
   that a call is refused rather than half-performed.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-06]` With the backend running and the Action in the
   catalogue, call it from a real agent through the shipped runner Skill and
   confirm the answer comes back scoped; then call it as an agent outside
   `allowed_callers` and confirm the refusal appears in the ledger. Record both
   outcomes in the Implementation Log.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The scoped read has a route, and a shipped Action whose `http` implementation names it
- [ ] Calls go through the existing gate; unknown id / missing input / unresolved implementation refused there
- [ ] A caller outside `allowed_callers` is refused and the refusal is in the ledger
- [ ] No gate, ledger or dispatch logic duplicated in this task
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The gate, the ledger, confirmation and dispatch — `REQ-SB-95-US-03`.
- The Action artifact kind itself — `REQ-SB-95-US-02`.
- Any screen.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** (read-only context for this
story) and the scoped-read bullet of **§The One Tag-Keyed Index**. This is the
story's only genuinely cross-story task: Scenarios 1–5 and 7 stand alone, so if
the product-owner needs to sequence this story ahead of the `REQ-SB-95` spine,
this task is the one that waits.

---

## Implementation Log

_(Filled in by the coder.)_
