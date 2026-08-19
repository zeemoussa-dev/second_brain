---
id: REQ-SB-42-US-01-T04
title: pending_approval_registry.py — create/resolve broadcast agent_presence.broadcast_snapshot() (no new state)
parent_story: REQ-SB-42-US-01
requirement_id: REQ-SB-42
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-42-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-42-US-01-T04 — Pending-approval broadcast-only instrumentation

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

`pending_approval_registry.create_pending_approval(...)` and `resolve_pending_approval(...)` each gain one additional call to `agent_presence.broadcast_snapshot()` at the end of their body, so a pending-approval state change is pushed immediately rather than waiting for an unrelated broadcast (`ADR-035` point 3e). No new ephemeral marker — the steady/pending-approval highlight (Scenario 4) is always recomposed live from this module's own already-persisted state (`T01`'s `get_snapshot()`), never duplicated.

---

## Starting State → End State

**Before / Inputs:** `pending_approval_registry.py::create_pending_approval` returns `record` after `vault_writer.save_pending_approvals_state(state)`. `resolve_pending_approval` returns `record` after the same save call, or `None` if `approval_id` doesn't match any record.

**After / Outputs:**
```python
def create_pending_approval(...) -> dict:
    ...
    state["pending"].append(record)
    vault_writer.save_pending_approvals_state(state)
    agent_presence.broadcast_snapshot()
    return record


def resolve_pending_approval(approval_id: str, status: str) -> dict | None:
    state = _load_state()
    for record in state["pending"]:
        if record["id"] == approval_id:
            record["status"] = status
            record["resolved_at"] = datetime.now(timezone.utc).isoformat()
            vault_writer.save_pending_approvals_state(state)
            agent_presence.broadcast_snapshot()
            return record
    return None
```
The idempotency short-circuit inside `create_pending_approval` (returning an already-existing `trigger == "background"` record without appending a new one) does NOT call `broadcast_snapshot()` — no real state changed on that path.

---

## Files to Modify

- `src/backend/app/business/pending_approval_registry.py` — add the two `agent_presence.broadcast_snapshot()` calls per the shape above; add `from app.business import agent_presence` import.

---

## Constraints

- No new dict, field, or `.second-brain/` file — this task is broadcast-only.
- `create_pending_approval`'s existing `trigger == "background"` idempotency early-return (returning the pre-existing record without appending) is unchanged and does NOT call `broadcast_snapshot()` — nothing actually changed on that path.
- `resolve_pending_approval`'s existing `return None` (unknown `approval_id`) path is unchanged and does NOT call `broadcast_snapshot()`.
- Do not change either function's signature or return shape.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`):
1. **[REQ-SB-42-US-01-AC-04]** `q = agent_presence.subscribe()`. Call `pending_approval_registry.create_pending_approval("people-producer", "background", None, "test")`. Confirm `q.get_nowait()` returns a snapshot with `"people-producer"` in `"pending_approval_agent_ids"`.
2. **[REQ-SB-42-US-01-AC-04]** Call `pending_approval_registry.resolve_pending_approval(<id from step 1>, "approved")`. Confirm `q.get_nowait()` returns a fresh snapshot where `"people-producer"` is no longer in `"pending_approval_agent_ids"`.
3. Non-AC smoke check: call `create_pending_approval("people-producer", "background", None, "test 2")` a second time immediately (same agent, same `trigger="background"`) — confirm it returns the SAME record as a fresh idempotent create would (if step 1's record is already resolved, this creates a genuinely new one; if still pending, the idempotency guard returns the existing one) and, in the idempotent-reuse case, confirm the queue receives NO new item (`q.get_nowait()` raises `asyncio.QueueEmpty`).
4. Clean-up: `agent_presence.unsubscribe(q)`; resolve any pending record left open.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `create_pending_approval` calls `agent_presence.broadcast_snapshot()` after a real state change (not on the idempotent-reuse early return)
- [ ] `resolve_pending_approval` calls `agent_presence.broadcast_snapshot()` after a real state change (not on the unknown-id `None` return)
- [ ] No new state dict or persisted field introduced
- [ ] Both functions' signatures unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The single-agent and Hub-routed instrumentation — `T02`/`T03`.
- The SSE endpoint and any frontend change.

---

## Context / Notes

Full mechanism: `ADR-035` point 3e. Mirrors the "steady, non-animated highlight" Scenario 4 reading a live, single source of truth — never a second copy — already established by `T01`'s `get_snapshot()`.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
