---
id: REQ-SB-21-US-01-T03
title: New app/business/pending_approval_registry.py — CRUD + background-trigger idempotency guard for the Pending Approvals workflow store
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** `ADR-020`
supersedes `ADR-018` points 3/5 only — this task's own scope (`ADR-018`
point 2) is untouched; no logic change needed. `ADR-020` point 3 adds a new
`"hub_routed"` value to the `trigger` enum this module's own record shape
carries — purely additive, this module's own code (a plain string field,
never validated against a fixed enum internally) needs no change to accept
it.

# REQ-SB-21-US-01-T03 — New app/business/pending_approval_registry.py

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add `app/business/pending_approval_registry.py`, owning the Pending
Approvals workflow record's full lifecycle (`ADR-018` point 2): create
(with the background-trigger-only idempotency guard), list, get, and
resolve (approve/decline). A genuinely different concern from working
mode itself (a workflow record with a lifecycle, not a settable
property), so it gets its own sibling module, mirroring `ADR-014`'s "one
module per concern" discipline.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_pending_approvals_state()`/
  `save_pending_approvals_state()`.
- This project's first use of the stdlib `uuid` module (`ADR-018` point 2)
  — no new dependency.

**After / Outputs:**
- `app/business/pending_approval_registry.py` (new) exposes:
  `list_pending_approvals(status=None, agent_id=None) -> list[dict]`,
  `get_pending_approval(approval_id) -> dict | None`,
  `create_pending_approval(agent_id, trigger, action_id, description) ->
  dict`, `resolve_pending_approval(approval_id, status) -> dict | None`.
- Record shape (`ADR-018` point 2): `{"id": str, "agent_id": str,
  "trigger": "chat" | "direct" | "background", "action_id": str | None,
  "description": str, "status": "pending" | "approved" | "declined",
  "created_at": iso8601, "resolved_at": iso8601 | None}`.
- `create_pending_approval` is idempotent **only** for
  `trigger="background"`: an existing unresolved (`status == "pending"`)
  record for the same `agent_id` + `trigger="background"` is returned
  as-is instead of duplicated. `trigger in ("chat", "direct")` is never
  deduplicated.

---

## Files to Modify

- `src/backend/app/business/pending_approval_registry.py` (new):
  ```python
  """Pending Approvals: the workflow-record concern behind a Supervised
  agent's "propose and wait for approval" behavior (ADR-018 point 2) — a
  genuinely different concern from working mode itself (a workflow record
  with a lifecycle, not a settable property), so this stays its own
  sibling module rather than folding into working_mode_registry.py,
  mirroring ADR-014's own "one module per concern" discipline (Sections
  vs. Providers) applied a second time.
  """
  from __future__ import annotations

  import uuid
  from datetime import datetime, timezone

  from app.data_access import vault_writer


  def _load_state() -> dict:
      state = vault_writer.load_pending_approvals_state()
      if state is None:
          state = {"pending": []}
          vault_writer.save_pending_approvals_state(state)
      return state


  def list_pending_approvals(status: str | None = None, agent_id: str | None = None) -> list[dict]:
      state = _load_state()
      records = state["pending"]
      if status is not None:
          records = [r for r in records if r["status"] == status]
      if agent_id is not None:
          records = [r for r in records if r["agent_id"] == agent_id]
      return records


  def get_pending_approval(approval_id: str) -> dict | None:
      state = _load_state()
      return next((r for r in state["pending"] if r["id"] == approval_id), None)


  def create_pending_approval(
      agent_id: str, trigger: str, action_id: str | None, description: str,
  ) -> dict:
      """Idempotency guard applies to trigger == "background" only
      (ADR-018 point 2): without it, every hourly tick for a still-
      unapproved Supervised background agent would pile up a new record
      on top of the last, unbounded. trigger in ("chat", "direct") is
      never deduplicated — each is a distinct, deliberate user request, a
      user asking twice on purpose is expected, ordinary behaviour."""
      state = _load_state()
      if trigger == "background":
          existing = next(
              (
                  r for r in state["pending"]
                  if r["agent_id"] == agent_id
                  and r["trigger"] == "background"
                  and r["status"] == "pending"
              ),
              None,
          )
          if existing is not None:
              return existing
      record = {
          "id": uuid.uuid4().hex[:12],
          "agent_id": agent_id,
          "trigger": trigger,
          "action_id": action_id,
          "description": description,
          "status": "pending",
          "created_at": datetime.now(timezone.utc).isoformat(),
          "resolved_at": None,
      }
      state["pending"].append(record)
      vault_writer.save_pending_approvals_state(state)
      return record


  def resolve_pending_approval(approval_id: str, status: str) -> dict | None:
      state = _load_state()
      for record in state["pending"]:
          if record["id"] == approval_id:
              record["status"] = status
              record["resolved_at"] = datetime.now(timezone.utc).isoformat()
              vault_writer.save_pending_approvals_state(state)
              return record
      return None
  ```

---

## Constraints

- Inherits from parent story and `ADR-018` point 2's exact record shape
  and idempotency rule.
- This module must NOT import `working_mode_registry`, `agent_registry`,
  or any API-layer module — a pure workflow-record store, composed by its
  callers (`T04`'s gate, `T05`'s background gate, `T06`'s router).
- `create_pending_approval`'s idempotency check must compare **exactly**
  `agent_id` + `trigger == "background"` + `status == "pending"` — a
  `"declined"` record must NOT suppress a new one (`ADR-018` point 2's own
  "a declined background proposal is not suppressed going forward"
  consequence).
- `resolve_pending_approval` must never raise for an unknown
  `approval_id` — returns `None`; the router layer (`T06`) is the only
  place a `404`/`409` is raised.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`; delete any leftover
   `.second-brain/agent_pending_approvals.json` first), call
   `list_pending_approvals()`. Confirm it returns `[]` and
   `.second-brain/agent_pending_approvals.json` now exists with
   `{"pending": []}`.
2. Non-AC smoke check: call `create_pending_approval("email-capture",
   "chat", "run_capture_now", "Run capture now (Email Capture)")`.
   Confirm the returned dict has a 12-hex-char `id`, `status: "pending"`,
   `resolved_at: null`. Call it again with the same arguments — confirm a
   **second**, distinct record is created (chat/direct is never
   deduplicated), `list_pending_approvals()` now returns 2 records.
3. Non-AC smoke check: call `create_pending_approval("meeting-capture",
   "background", None, "Run the scheduled meeting-capture step.")` twice
   in a row with identical arguments. Confirm the **second** call returns
   the exact same `id` as the first (idempotent per the background-only
   guard) — `list_pending_approvals(agent_id="meeting-capture")` still
   has exactly 1 record.
4. Non-AC smoke check: call `resolve_pending_approval(<the
   meeting-capture record's id>, "declined")`. Confirm `status:
   "declined"`, `resolved_at` now set. Call `create_pending_approval
   ("meeting-capture", "background", None, "...")` again — confirm a
   **new**, distinct record is created this time (a declined background
   proposal is not suppressed going forward, per this task's own
   Constraints). Call `resolve_pending_approval("not-a-real-id",
   "approved")` — confirm `None`, no error raised.
5. Clean-up: delete `.second-brain/agent_pending_approvals.json` so
   `T06`'s own verification starts from an empty queue.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `create_pending_approval` generates a `uuid.uuid4().hex[:12]` id,
      defaults `status: "pending"`/`resolved_at: null`
- [ ] `create_pending_approval` deduplicates only for
      `trigger == "background"` against an existing unresolved record for
      the same `agent_id`; `"chat"`/`"direct"` are never deduplicated
- [ ] A declined (or approved) background record does not suppress the
      next `create_pending_approval` call for that same `agent_id` +
      `"background"`
- [ ] `resolve_pending_approval` sets `status` + `resolved_at`, returns
      `None` (never raises) for an unknown id
- [ ] `list_pending_approvals`/`get_pending_approval` filter/read
      correctly
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any API surface — `T06` (`pending_approvals_router.py`).
- Calling this module from the chat/direct gate or the background gate —
  `T04`/`T05`.
- Working mode itself — `T02` (`working_mode_registry.py`).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created at
`/plan-tasks` step 1) — the human reviews `ADR-018` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

This task carries no AC-tagged step of its own — its locked-AC consumers
(`T05`'s background-propose scenario, `T06`'s approve/decline endpoints,
`T07`'s live chat-proposal UI) verify this module's real behaviour live,
against the real backend.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** New
`app/business/pending_approval_registry.py` built exactly as specified.

No locked AC of its own — verified via the Tests block's non-AC smoke
checks, live, against the real backend `.venv`/vault:
1. `list_pending_approvals()` returned `[]`, seeded
   `{"pending": []}`. PASS.
2. `create_pending_approval("email-capture", "chat",
   "run_capture_now", ...)` returned a 12-hex-char id, `status:
   "pending"`, `resolved_at: null`; calling it again with identical
   args produced a **second**, distinct record (chat is never
   deduplicated) — 2 total records. PASS.
3. `create_pending_approval("meeting-capture", "background", None,
   ...)` called twice returned the **same** id both times (background
   idempotency) — 1 record for `meeting-capture`. PASS.
4. `resolve_pending_approval(<id>, "declined")` set `status`/
   `resolved_at`; a subsequent `create_pending_approval(...,
   "background", ...)` call for the same agent produced a **new**,
   distinct record (a declined background proposal is not suppressed
   going forward). `resolve_pending_approval("not-a-real-id",
   "approved")` returned `None`, no error. PASS.
5. Cleaned up `.second-brain/agent_pending_approvals.json` per the
   task's own instruction so `T06`'s verification started clean.

Later, live end-to-end at `T04`/`T05`/`T06`'s own verification passes,
this module's full CRUD + idempotency guard were exercised repeatedly
against the real gate and Approve/Decline endpoints with no defect,
including the `action_id: null` background-approval dispatch branch
(a real 39-meeting `classify_recent_meetings()` run via Approve).

Gate: `clear` — no MUST-FLAG trigger fired.
