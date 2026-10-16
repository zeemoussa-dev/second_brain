---
id: REQ-SB-95-US-03-T03
title: Dispatch by implementation kind — http performed, ui pointed at, skill authorised via single-use grant
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-03-T02]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-03-T03 — Dispatch by Implementation Kind

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make a validated call actually do the thing — performing what the app owns,
authorising what it does not, and pointing at what only the operator can do.

---

## Starting State → End State

**Before / Inputs:**

- `T02`'s gate validates and hands off to a dispatch seam that performs nothing
  yet.
- `ADR-019` keeps `business/core/skills/catalog/` as payload the app never
  imports — the app is not a second executor of Skill payload.

**After / Outputs:**

- `action_invocation.py` dispatches on the Action's one implementation kind:
  - **`http`** — performed by the app against its own route, with the validated
    inputs; the real result is returned and recorded as `performed`.
  - **`ui`** — **never performed**: the response names where the operator does
    it, and the ledger records that it was pointed at, not done.
  - **`skill`** — **authorised, not performed**: the response carries a
    single-use grant naming the deployed Skill and the validated inputs, which
    the runner performs in the profile where Skills already run; the ledger
    records the authorisation and, when the runner reports back, the outcome.
- No dispatch path imports or executes anything under `skills/catalog/`.

---

## Files to Modify

- `src/backend/app/business/logic/action_invocation.py`
- `src/backend/app/data_access/action_calls.py` (grant fields, if the record shape needs them)
- `src/backend/tests/test_action_dispatch.py` (new)

---

## Constraints

- Inherits from parent story.
- **The app does not perform what it does not own** (`ADR-033`). A `skill`
  implementation is authorised only; a `ui` implementation is never performed.
- `ADR-019` is binding: no import of `skills/catalog/` payload, no subprocess
  execution of a Skill script from the app.
- A grant is **single-use** — the consumption mechanics are shared with `T04`'s
  confirmation grant; build one mechanism, not two.
- Nothing half-performed: a dispatch that fails records an honest failure
  outcome and never reports `performed`.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_dispatch.py`, run with
`pytest tests/test_action_dispatch.py` from `src/backend`.

1. `[REQ-SB-95-US-03-AC-02]` Call an `http`-implementation Action with valid
   inputs through `POST /actions/{id}/call` over
   `httpx.ASGITransport(app=app)`; assert the app really performed the route
   (the target function was entered with the validated inputs), the response
   carries its real result, and the ledger record says `performed`.
2. `[REQ-SB-95-US-03-AC-02]` Call a `skill`-implementation Action; assert the
   response carries a single-use grant naming the deployed Skill and the
   validated inputs, that nothing under `skills/catalog/` was imported or
   executed, and that the ledger records an authorisation rather than a
   performance.
3. `[REQ-SB-95-US-03-AC-02]` Consume that grant once, then attempt to consume it
   a second time; assert the second attempt is refused.
4. `[REQ-SB-95-US-03-AC-02]` Call a `ui`-implementation Action; assert nothing
   was performed, the response names where the operator performs it, and the
   ledger says so.
5. `[REQ-SB-95-US-03-AC-02]` Induce a failure inside an `http` dispatch (scoped
   in-process monkeypatch, this project's established technique); assert the
   outcome recorded is an honest failure, never `performed`.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-02]` With the backend running, call a real
   `http`-implementation Action over loopback and confirm the operator sees the
   real result of the real operation (check the real side effect, not the
   response text alone).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Three dispatch paths, each behaving exactly as `ADR-033` decides
- [ ] Single-use grant minted for `skill`, consumable exactly once
- [ ] No `skills/catalog/` payload imported or executed by the app
- [ ] Honest failure outcomes; nothing half-performed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Confirmation-required Actions — `T04`.
- The runner Skill that consumes the grant — `T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate**, "Dispatch by kind". `ADR-033`'s
second decision bullet is the exact contract, including why the app must not
become a second executor of Skill payload.

---

## Implementation Log

_(Filled in by the coder.)_
