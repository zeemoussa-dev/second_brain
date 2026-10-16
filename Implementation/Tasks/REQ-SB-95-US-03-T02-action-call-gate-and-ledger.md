---
id: REQ-SB-95-US-03-T02
title: The validating call gate — action_invocation.py, POST /actions/{action_id}/call, and the Action-call ledger
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T03]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-03-T02 — The Validating Call Gate + the Action-Call Ledger

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Build the one validating door — unknown id, unknown or missing required input,
caller not permitted, implementation no longer resolving — so the refusal comes
from the framework and no prompt text can route around it, with every call
recorded in a ledger.

---

## Starting State → End State

**Before / Inputs:**

- `app/api/actions_router.py` exists with CRUD (`REQ-SB-95-US-02-T03`); there is
  no call route.
- There is no `business/logic/action_invocation.py` and no `ActionCalls` store.
- `business/logic/agent_chat_stream.py` is an SSE relay that *observes*
  `tool.start` / `tool.complete` after the fact — it is **not** an interception
  point and must not be touched by this task (`ADR-033`).

**After / Outputs:**

- `app/data_access/action_calls.py` — raw I/O only over
  `<DATA_PATH>/data/ActionCalls/<call_id>.json`.
- `app/business/logic/action_invocation.py` — the one gate. In order, before any
  dispatch: the action id exists in the live catalogue; the caller's agent id is
  in `allowed_callers` (or `allowed_callers == ["*"]`); every required input is
  supplied and no unknown input is passed; the implementation still resolves.
  Each failure returns a refusal naming the specific cause and writes a
  `refused:<reason>` ledger record.
- `POST /actions/{action_id}/call` on `actions_router.py`, taking the caller's
  agent id and the inputs, returning the gate's verdict.
- Validation completes before dispatch begins — **nothing is half-performed**.
- The gate reads the **live catalogue**, never the published SOUL text.

---

## Files to Modify

- `src/backend/app/data_access/action_calls.py` (new)
- `src/backend/app/business/logic/action_invocation.py` (new)
- `src/backend/app/api/actions_router.py` (the call route)
- `src/backend/tests/test_action_invocation_gate.py` (new)

---

## Constraints

- Inherits from parent story.
- **Enforcement is a gate, not an instruction** (`ADR-032`). No part of this may
  depend on prompt text.
- **No silent fallback and no guessing:** a missing required input is refused by
  name; no default, inferred or substituted value, ever.
- The gate reads the live catalogue — never the published block.
- `agent_chat_stream.py` is not touched by this task.
- Dispatch itself is `T03`; this task validates and, on success, hands off to a
  dispatch seam `T03` fills (a clearly-named not-yet-implemented branch is
  correct here, provided a successful validation does not claim an operation was
  performed).
- The ledger is instance data — excluded from artifact export, never written
  into the repository.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_invocation_gate.py`, run
with `pytest tests/test_action_invocation_gate.py` from `src/backend`, driving
the real app through `httpx.ASGITransport(app=app)` with the Actions and
ActionCalls data access monkeypatched onto a tmp dir.

1. `[REQ-SB-95-US-03-AC-03]` `POST /actions/does-not-exist/call`; assert the
   call is refused, the response names the unknown id, no dispatch seam was
   entered (spy asserts zero calls), and a `refused:` ledger record naming the
   unknown id was written.
2. `[REQ-SB-95-US-03-AC-04]` Call a catalogued Action with a required input
   omitted; assert the refusal names that input by name, that no value was
   substituted anywhere in the recorded inputs, that nothing was dispatched, and
   that the ledger records the refusal.
3. `[REQ-SB-95-US-03-AC-04]` Call the same Action with an input it does not
   declare; assert the refusal names the unknown input rather than silently
   dropping it.
4. `[REQ-SB-95-US-03-AC-07]` Call an Action whose `allowed_callers` is
   `["other-agent"]` as `this-agent`; assert the refusal states this caller may
   not run that action, nothing is dispatched, and the ledger records it. Then
   set `allowed_callers: ["*"]` and assert the same caller is accepted.
5. `[REQ-SB-95-US-03-AC-02]` Call a fully valid, non-confirmation Action with
   every required input; assert validation passes, the ledger record carries the
   caller, the action id and the validated inputs, and the dispatch seam is
   entered exactly once with those validated inputs.
6. `[REQ-SB-95-US-03-AC-02]` Make the implementation stop resolving, then call;
   assert the gate refuses naming what no longer resolves (the second line
   behind `REQ-SB-95-US-02-T02`'s save-time check) and nothing is dispatched.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-03]` With the backend running, `POST
   http://127.0.0.1:8001/actions/not-a-real-action/call` from PowerShell and
   confirm the real refusal body and the real ledger file written under the
   configured data path.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] One gate module refusing all four failure classes, naming each cause
- [ ] `POST /actions/{action_id}/call` on the existing Actions router
- [ ] Every call outcome recorded in `<DATA_PATH>/data/ActionCalls/<call_id>.json`
- [ ] Validation completes before any dispatch; nothing half-performed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Dispatch by implementation kind — `T03`.
- Confirmation and the single-use grant — `T04`.
- The runner Skill and the agent-facing refusal wording — `T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** and **§Confirmation and the
Action-Call Ledger**; `ADR-033` decides the surface, the caller identity and why
the in-app chat path cannot be the chokepoint. The trust boundary is loopback
and is stated honestly in `ADR-033`'s Consequences — this task does not sandbox
Hermes and must not claim to.

---

## Implementation Log

_(Filled in by the coder.)_
