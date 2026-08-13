---
id: REQ-SB-21-US-01-T06
title: New app/api/pending_approvals_router.py — GET/POST /pending-approvals, Approve executes via _execute_action/run_capture_for_agent (bypassing the gate), Decline discards
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T04, REQ-SB-21-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** `ADR-020`
supersedes `ADR-018` points 3/5 only — this router's own design (`ADR-018`
point 6: Approve/Decline calling `_execute_action`/`run_capture_for_agent`
directly, bypassing the gate) is untouched. `AC-04` (decline) keeps its same
number — no scenario renumbering affects this task. Still depends on the
now-rewritten `T04` for `_execute_action` (renamed, internal logic
unaffected by `ADR-020`) and unchanged `T05` for `run_capture_for_agent`.

# REQ-SB-21-US-01-T06 — New app/api/pending_approvals_router.py

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add `app/api/pending_approvals_router.py` exposing the Pending Approvals
workflow over HTTP (`ADR-018` point 6): list/read, Approve (executes the
deferred action directly, bypassing the working-mode gate — the approval
itself is the authorization), Decline (discards, no action taken).
Register the router in `app/main.py`.

**This task requires `T04` and `T05` to already be `Done`** — Approve
calls `agents_router._execute_action` (`T04`) and
`email_classification.run_capture_for_agent` (`T05`) directly.

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `pending_approval_registry`'s full CRUD/lifecycle
  surface.
- `T04` has landed `agents_router._execute_action(agent_id, action_id)`.
- `T05` has landed `email_classification.run_capture_for_agent(agent_id,
  limit=10)`.
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`, `sections_router`, `providers_router`.

**After / Outputs:**
- `app/api/pending_approvals_router.py` exists with `GET
  /pending-approvals` (optional `status`/`agent_id` query filters), `GET
  /pending-approvals/{id}`, `POST /pending-approvals/{id}/approve`, `POST
  /pending-approvals/{id}/decline` — every response includes a
  resolved `agent_name`.
- `app/main.py` additionally registers `pending_approvals_router`.

---

## Files to Modify

- `src/backend/app/api/pending_approvals_router.py` (new):
  ```python
  from fastapi import APIRouter, HTTPException

  from app.api.agents_router import _execute_action
  from app.business import agent_registry, pending_approval_registry
  from app.business.email_classification import run_capture_for_agent
  from app.data_access import vault_writer

  router = APIRouter(prefix="/pending-approvals")


  def _resolved(record: dict) -> dict:
      agent = agent_registry.get_agent(record["agent_id"])
      return {**record, "agent_name": agent["name"] if agent else record["agent_id"]}


  @router.get("")
  def list_pending_approvals(status: str | None = None, agent_id: str | None = None) -> list[dict]:
      records = pending_approval_registry.list_pending_approvals(status=status, agent_id=agent_id)
      return [_resolved(r) for r in records]


  @router.get("/{approval_id}")
  def get_pending_approval(approval_id: str) -> dict:
      record = pending_approval_registry.get_pending_approval(approval_id)
      if record is None:
          raise HTTPException(status_code=404, detail="Unknown pending approval")
      return _resolved(record)


  @router.post("/{approval_id}/approve")
  def approve_pending_approval(approval_id: str) -> dict:
      record = pending_approval_registry.get_pending_approval(approval_id)
      if record is None:
          raise HTTPException(status_code=404, detail="Unknown pending approval")
      if record["status"] != "pending":
          raise HTTPException(status_code=409, detail=f"Already {record['status']}")

      if record["action_id"] is not None:
          # Chat/direct proposal — execute unconditionally via
          # _execute_action, NEVER _invoke_action (re-entering the gate
          # would find the agent still Supervised and create a second
          # pending record instead of ever actually running — ADR-018
          # point 6's own infinite-defer-bug rejection).
          result = _execute_action(record["agent_id"], record["action_id"])
          outcome_message = result["message"]
      else:
          # Background proposal — no discrete action id; runs the same
          # capture step the scheduled tick would have run.
          results = run_capture_for_agent(record["agent_id"])
          outcome_message = f"Approved — background step ran, {len(results)} result(s)."

      resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")
      vault_writer.append_agent_history_entry(record["agent_id"], "run_event", outcome_message)
      return _resolved(resolved)


  @router.post("/{approval_id}/decline")
  def decline_pending_approval(approval_id: str) -> dict:
      record = pending_approval_registry.get_pending_approval(approval_id)
      if record is None:
          raise HTTPException(status_code=404, detail="Unknown pending approval")
      if record["status"] != "pending":
          raise HTTPException(status_code=409, detail=f"Already {record['status']}")

      resolved = pending_approval_registry.resolve_pending_approval(approval_id, "declined")
      vault_writer.append_agent_history_entry(record["agent_id"], "run_event", "Declined — no action taken")
      return _resolved(resolved)
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.pending_approvals_router import router as pending_approvals_router
  ...
  app.include_router(pending_approvals_router)
  ```
  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) is bent deliberately once here, per `ADR-018` point 6's own
  explicit direction — this router imports `_execute_action` directly
  from `agents_router.py` (an api-layer-to-api-layer import) specifically
  to avoid re-entering `_invoke_action`'s working-mode gate; do not
  "fix" this by routing through `_invoke_action` instead — that
  reintroduces the exact infinite-defer bug this design avoids.
- `POST /pending-approvals/{id}/approve|decline` must `404` for an
  unknown id and `409` (never `200`, never silently no-op) for an
  already-resolved one.
- Approve must call `_execute_action`/`run_capture_for_agent` — never
  `_invoke_action`/`run_capture_and_record_completion` — under any
  circumstance.
- Every response (list, get, approve, decline) must include a
  name-resolved `agent_name`, never just a bare `agent_id`.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.

---

## Tests

<!-- REQ-SB-21-US-01-AC-04 (decline discards) is fully backend-observable
(no distinct frontend rendering need to check beyond what T07 separately
verifies for the chat card's own live status resolution) — verified here
directly against the real backend, per the established "user-observable
outcome" placement rule. AC-03's full propose→approve→executes round
trip is verified live via the real chat UI in T07; this task's own step 1
below re-confirms the backend half of that same round trip in isolation,
non-AC (T07 owns the AC tag for the full, real-click flow). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via `Invoke-RestMethod`; deliberate — step 1 triggers one real
capture run on Approve):

1. Non-AC smoke check (backend half of AC-03's round trip): `PATCH
   /agents/email-capture` `{"working_mode": "supervised"}`. `POST
   /agents/email-capture/actions/run_capture_now` — confirm `status:
   "pending"`, capture `pending_approval_id`. `POST
   /pending-approvals/<id>/approve` — confirm the response's `status:
   "approved"`, `resolved_at` set, `agent_name: "Email Capture"`. Confirm
   via `GET /agents/email-capture/history` a new `"run_event"` entry
   reading `"Done — N email(s) filed."` was appended, proving the real
   capture step actually ran on Approve. `PATCH /agents/email-capture`
   `{"working_mode": "autonomous"}` afterward.
2. **[REQ-SB-21-US-01-AC-04]** `PATCH /agents/email-capture`
   `{"working_mode": "supervised"}`. `POST
   /agents/email-capture/actions/run_capture_now` — capture the new
   `pending_approval_id`. `POST /pending-approvals/<id>/decline` —
   confirm the response's `status: "declined"`, `resolved_at` set.
   Confirm via `GET /agents/email-capture/history` that the newest entry
   reads `"Declined — no action taken"`, **not** a `"Done — N email(s)
   filed"` success message — proving no real capture step ran. `POST
   /pending-approvals/<same id>/decline` again — confirm `409`. `PATCH
   /agents/email-capture` `{"working_mode": "autonomous"}` afterward.
3. Non-AC smoke check: approve the leftover `meeting-capture`
   `"background"`-trigger pending record from `T05`'s own verification
   (if still present — `GET /pending-approvals?agent_id=meeting-
   capture&status=pending`). Confirm the response's `status: "approved"`
   and, via `vault_writer`-level inspection or `GET
   /agents/meeting-capture/history`, a new `"run_event"` entry appended
   — proving `run_capture_for_agent` (the `action_id: null` background
   branch) is reachable and correctly dispatches to
   `meeting_classification.classify_recent_meetings()`.
4. Non-AC smoke check: `GET /pending-approvals/not-a-real-id` — confirm
   `404`. `POST /pending-approvals/not-a-real-id/approve` — confirm
   `404`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-04** — declining a pending proposal marks it `"declined"`,
      appends a "no action taken" history entry, and never invokes the
      real handler/capture step
- [ ] `POST /pending-approvals/{id}/approve` calls `_execute_action`
      (chat/direct, `action_id` set) or `run_capture_for_agent`
      (background, `action_id: null`) directly, never re-enters the
      working-mode gate
- [ ] `GET /pending-approvals`/`GET /pending-approvals/{id}` return every
      record with a resolved `agent_name`, filterable by `status`/
      `agent_id`
- [ ] `404` for an unknown id (get/approve/decline), `409` for an
      already-resolved one (approve/decline)
- [ ] `pending_approvals_router` registered in `app/main.py` without
      changing any existing router's behavior
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls these endpoints — `T07`
  (`AgentDetailPanel.tsx`), `T08` (`MyDayApprovalsPage.tsx`).
- Creating pending-approval records — `T04` (chat/direct gate), `T05`
  (background gate).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created at
`/plan-tasks` step 1) — the human reviews `ADR-018` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** New
`app/api/pending_approvals_router.py` built exactly as specified.
`app/main.py` had drifted beyond this task's own stale sample (it also
registers `skills_router`/`system_health_router` and mounts
`mcp_server`, none of which the sample knew about, both landed by
sibling stories after this task was authored) — the new
`pending_approvals_router` import/`include_router` call was added
additively at the real current file's own end, preserving every
existing registration's order untouched, rather than overwriting with
the stale sample.

**Live verification** (real backend, port 8002, `Invoke-RestMethod`):

1. Non-AC smoke check (backend half of `AC-03`'s round trip): Set
   `email-capture` Supervised, `POST .../run_capture_now` → `pending`,
   captured `pending_approval_id`. `POST /pending-approvals/<id>/approve`
   → `status: "approved"`, `resolved_at` set, `agent_name: "Email
   Capture"`; confirmed via history a new `"run_event"` reading `"Done
   — N email(s) filed."` was appended immediately after — the real
   capture step genuinely ran on Approve. PASS.
2. **[AC-04]** `POST .../decline` on a fresh pending record → `status:
   "declined"`, `resolved_at` set; newest history entry read
   `"Declined — no action taken"`, **not** a success message — no real
   capture step ran. A second decline on the same id → `409`. PASS.
3. Non-AC smoke check: approved a real `meeting-capture`
   `"background"`-trigger record (`action_id: null`) — confirmed
   `run_capture_for_agent`'s background dispatch branch is reachable
   and correctly calls `meeting_classification.classify_recent_
   meetings()` (`"Approved — background step ran, 39 result(s)."`
   appended to history). PASS.
4. Non-AC smoke check: `GET /pending-approvals/not-a-real-id` → `404`;
   `POST /pending-approvals/not-a-real-id/approve` → `404`. PASS.

Gate: `clear` — the locked AC this task carries (`AC-04`) was verified
live; no MUST-FLAG trigger fired.
