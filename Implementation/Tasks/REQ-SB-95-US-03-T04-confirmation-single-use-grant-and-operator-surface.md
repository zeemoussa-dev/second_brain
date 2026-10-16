---
id: REQ-SB-95-US-03-T04
title: Confirmation-required Actions — awaiting_confirmation, the single-use grant, and the operator confirm/decline surface
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

# REQ-SB-95-US-03-T04 — Confirmation and the Single-Use Grant

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Honour the `needs_confirmation` flag `REQ-SB-95-US-02` stores: the first call
performs nothing and opens an `awaiting_confirmation` ledger record; the
operator confirms or declines; a confirmed record is a single-use grant the
re-call consumes exactly once.

---

## Starting State → End State

**Before / Inputs:**

- The Action-call ledger exists (`T02`) and dispatch works (`T03`); the
  confirmation flag is stored but honoured nowhere.
- **The Pending Approvals surface is not live and must not be planned against:**
  `pending_approvals_router.py` is absent from the repo,
  `GET /agents/{id}/history` returns `[]` with a comment naming it, and
  `Agent.working_mode`'s own comment records that the Hermes
  `approval.request`/`respond` path was never wired.

**After / Outputs:**

- First call of a confirmation-required Action: nothing performed, a ledger
  record at `awaiting_confirmation`, and a refusal carrying the `call_id`.
- Confirm / decline routes on `actions_router.py` over the ledger; confirming
  turns the record into a single-use grant, declining records `declined`.
- A re-call consumes the grant exactly once and then dispatches through `T03`;
  a second re-call finds nothing to consume and is refused.
- A small operator surface over the ledger — the pending confirmations list and
  a confirm/decline control per entry, on the existing approved
  `.item-list`/`.item-row` + `.btn` families. It is **not**
  `html-prototype/my-day-approvals.html` and does not revive that subsystem.
- `Agent.working_mode` is untouched — an Action's confirmation flag is a
  per-operation operator decision, orthogonal to it.

---

## Files to Modify

- `src/backend/app/business/logic/action_invocation.py`
- `src/backend/app/data_access/action_calls.py`
- `src/backend/app/api/actions_router.py` (list-pending, confirm, decline)
- `src/frontend/src/pages/SettingsActionsPage.tsx` (a pending-confirmations region on the existing Actions page)
- `src/frontend/src/features/settings/actionsApiClient.ts`
- `src/backend/tests/test_action_confirmation.py` (new)

---

## Constraints

- Inherits from parent story.
- **Nothing is half-performed.** The first call of a confirmation-required
  Action performs no part of the operation.
- The grant is **single-use**; reuse the mechanism `T03` built rather than
  adding a second one.
- Do not revive `pending_approvals_router.py` / `agent_pending_approvals.json`
  and do not touch `load_pending_approvals_state` /
  `save_pending_approvals_state` in `data_access/vault_writer.py`.
- `Agent.working_mode` and the Hermes approval path stay exactly as they are.
- A confirmed-but-never-re-called Action stays visible in the ledger rather
  than silently performing nothing.
- Frontend assertions are on DOM structure only.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_confirmation.py`, run with
`pytest tests/test_action_confirmation.py` from `src/backend`, over
`httpx.ASGITransport(app=app)` with the stores monkeypatched to a tmp dir.

1. `[REQ-SB-95-US-03-AC-06]` Call an Action with `needs_confirmation: true`;
   assert nothing was dispatched, the response carries `awaiting_confirmation`
   and a `call_id`, and the ledger record exists at that state.
2. `[REQ-SB-95-US-03-AC-06]` Confirm that `call_id`, then re-call; assert the
   grant is consumed exactly once and the operation is really performed
   (dispatch seam entered once, ledger `performed`).
3. `[REQ-SB-95-US-03-AC-06]` Re-call a second time with the same `call_id`;
   assert it is refused — a grant cannot be consumed twice.
4. `[REQ-SB-95-US-03-AC-06]` Decline a `call_id`; assert the ledger records
   `declined`, nothing is performed, and a re-call is refused with `declined`.
5. `[REQ-SB-95-US-03-AC-06]` Assert a confirmation-required Action never
   dispatches on the first call regardless of implementation kind (http / ui /
   skill all return `awaiting_confirmation`).

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-06]` With the backend and frontend running, call a real
   confirmation-required Action over loopback; confirm the pending entry renders
   on the Actions page as an `.item-row` with confirm and decline controls;
   click confirm, re-call, confirm the real operation happened. Repeat with
   decline and confirm nothing happened and the agent is told so.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] First call performs nothing and opens `awaiting_confirmation`
- [ ] Confirm → single-use grant, consumed exactly once on the re-call
- [ ] Decline → `declined`, nothing performed, honestly reported
- [ ] A small operator surface over the ledger, not the archived approvals one
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- A reviewable surface over the whole ledger / unmet-request backlog (story
  Non-Goals).
- Per-step workflow confirmation — `REQ-SB-95-US-04-T05` reuses this mechanism
  unchanged.
- Reviving or extending the archived Pending Approvals subsystem.

---

## Context / Notes

`architecture.md` → **§Confirmation and the Action-Call Ledger** is
authoritative, including the evidence for why the existing approvals machinery
is unavailable. `ADR-033`'s fourth decision bullet fixes the state machine
(`awaiting_confirmation` → single-use grant → consumed once, or `declined`).

---

## Implementation Log

_(Filled in by the coder.)_
