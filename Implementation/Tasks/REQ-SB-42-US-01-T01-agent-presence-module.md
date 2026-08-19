---
id: REQ-SB-42-US-01-T01
title: New app/business/agent_presence.py — in-memory activity/hub-route registry, snapshot composition, broadcast primitive
parent_story: REQ-SB-42-US-01
requirement_id: REQ-SB-42
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-42-US-01-T01 — New `app/business/agent_presence.py`

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

Add the new, ephemeral, in-memory-only `app/business/agent_presence.py` module `ADR-035` designs: two small state dicts, a per-client subscriber queue set, start/end mutators, and a `get_snapshot()` that composes both dicts with a fresh, live read of `pending_approval_registry`'s own already-persisted open-approvals — never a second, duplicated copy of pending-approval state.

---

## Starting State → End State

**Before / Inputs:**
- No `agent_presence.py` module exists.
- `app/business/pending_approval_registry.py::list_pending_approvals(status="pending")` already exists (Done, `REQ-SB-21-US-01`) — the single source of truth this module reads, never duplicates.

**After / Outputs:** new `app/business/agent_presence.py`:
```python
"""Ephemeral, in-memory-only agent-activity/presence registry (ADR-035) --
mirrors ADR-024's vault_indexing.py "in-memory, full-rebuild, no disk
persistence" shape one layer over. NEVER written to .second-brain/ -- an
empty registry after a process restart is the correct value (nothing
really is running the instant the process comes back up)."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.business import pending_approval_registry

_active: dict[str, dict] = {}          # agent_id -> {"kind": "capture" | "chat", "since": iso8601}
_hub_routes: dict[str, dict] = {}      # token -> {"from_agent_id", "to_agent_id", "since"}
_subscribers: set[asyncio.Queue] = set()


def start_activity(agent_id: str, kind: str) -> str:
    token = uuid.uuid4().hex[:12]
    _active[agent_id] = {"kind": kind, "since": datetime.now(timezone.utc).isoformat(), "token": token}
    broadcast_snapshot()
    return token


def end_activity(agent_id: str, token: str) -> None:
    entry = _active.get(agent_id)
    if entry is not None and entry.get("token") == token:
        del _active[agent_id]
    broadcast_snapshot()


def start_hub_routing(from_agent_id: str, to_agent_id: str) -> str:
    token = uuid.uuid4().hex[:12]
    _hub_routes[token] = {
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "since": datetime.now(timezone.utc).isoformat(),
    }
    broadcast_snapshot()
    return token


def end_hub_routing(token: str) -> None:
    _hub_routes.pop(token, None)
    broadcast_snapshot()


def get_snapshot() -> dict:
    pending_by_agent: dict[str, bool] = {}
    for approval in pending_approval_registry.list_pending_approvals(status="pending"):
        pending_by_agent[approval["agent_id"]] = True
    return {
        "active": dict(_active),
        "hub_routes": list(_hub_routes.values()),
        "pending_approval_agent_ids": sorted(pending_by_agent.keys()),
    }


def broadcast_snapshot() -> None:
    snapshot = get_snapshot()
    for queue in list(_subscribers):
        queue.put_nowait(snapshot)


def subscribe() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue) -> None:
    _subscribers.discard(queue)
```

---

## Files to Modify

- `src/backend/app/business/agent_presence.py` (new) — per the code block above.

---

## Constraints

- In-memory, module-level only — no `.second-brain/` file, no vault write, no `data_access` import beyond none needed.
- `get_snapshot()`'s pending-approval half is ALWAYS recomposed live from `pending_approval_registry.list_pending_approvals(status="pending")` — never stored into `_active`/`_hub_routes` or any new dict.
- `start_activity`/`start_hub_routing` return an opaque token; `end_activity`/`end_hub_routing` accept it back so a caller can only clear the marker IT created (a second, unrelated caller racing on the same `agent_id` cannot clobber the first's own `end_activity` — `end_activity` checks the token before deleting).
- `broadcast_snapshot()` must never raise on a full/closed queue — `asyncio.Queue.put_nowait` on an unbounded queue (the default) cannot block or raise `QueueFull`; do not pass a `maxsize`.
- Do not import `vault_writer` or write to disk anywhere in this module.

---

## Tests

<!-- This module has no directly-observable Scenario of its own (every Scenario is UI-observable, per the parent story) -- verified here as infra-only, non-AC-tagged smoke checks; downstream tasks (T02-T08) verify the locked ACs. -->

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`):
1. Non-AC smoke check: `token = agent_presence.start_activity("email-capture", "capture")` — confirm `agent_presence.get_snapshot()["active"]["email-capture"] == {"kind": "capture", "since": ..., "token": token}`.
2. Non-AC smoke check: `agent_presence.end_activity("email-capture", token)` — confirm `"email-capture" not in agent_presence.get_snapshot()["active"]`. Call `end_activity` again with a stale/wrong token — confirm no exception, no-op.
3. Non-AC smoke check: `token2 = agent_presence.start_hub_routing("meeting-capture", "vault-qa")` — confirm `get_snapshot()["hub_routes"]` contains an entry with `from_agent_id == "meeting-capture"`, `to_agent_id == "vault-qa"`. `agent_presence.end_hub_routing(token2)` — confirm the list is empty again.
4. Non-AC smoke check: create a real pending approval (`pending_approval_registry.create_pending_approval("people-producer", "background", None, "test")`), confirm `get_snapshot()["pending_approval_agent_ids"]` contains `"people-producer"`; resolve it (`resolve_pending_approval(<id>, "approved")`), confirm it no longer appears.
5. Non-AC smoke check: `q = agent_presence.subscribe()`; call `agent_presence.start_activity("email-capture", "chat")`; confirm `q.get_nowait()` returns a snapshot dict with `"email-capture"` present under `"active"`. `agent_presence.unsubscribe(q)`.
6. Clean-up: ensure `_active`/`_hub_routes` are empty and no test pending-approval record is left `"pending"` (resolve any created in step 4).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `agent_presence.py` exists with `_active`/`_hub_routes`/`_subscribers`, `start_activity`/`end_activity`/`start_hub_routing`/`end_hub_routing`, `get_snapshot`, `broadcast_snapshot`, `subscribe`/`unsubscribe`
- [ ] `get_snapshot()`'s pending-approval half is a live read of `pending_approval_registry`, never a duplicated copy
- [ ] No `.second-brain/` file written by this module
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Instrumenting any real dispatch call site — `T02`, `T03`, `T04`.
- The SSE endpoint — `T05`.
- Any frontend change — `T06`-`T08`.

---

## Context / Notes

Full mechanism/reasoning/alternatives: `Implementation/Architecture/ADR.md` → `ADR-035`. This task builds exactly `ADR-035` point 2's own code shape — do not redesign the state schema.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
