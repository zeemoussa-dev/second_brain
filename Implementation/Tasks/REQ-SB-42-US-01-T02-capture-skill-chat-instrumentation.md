---
id: REQ-SB-42-US-01-T02
title: Instrument the three single-agent activity triggers — capture/Skill run and chat generation call agent_presence.start_activity/end_activity
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

# REQ-SB-42-US-01-T02 — Capture/Skill + chat-generation instrumentation

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

Wrap the three real dispatch call sites `ADR-035` point 3(a-c) names for the "single-agent working" glow (Scenarios 1/2) in `agent_presence.start_activity(agent_id, kind)` / `end_activity(agent_id, token)`, each in a `finally` block so a raised exception still clears the marker.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `agent_presence.start_activity`/`end_activity`.
- `app/business/email_classification.py::run_capture_for_agent(agent_id, limit=10)` — the one function every real capture-EXECUTION path (scheduled tick, Supervised Approve dispatch) funnels through.
- `app/business/skill_registry.py::_dispatch_skill(agent_id, skill_id, args=None)` — the one raw, ungated dispatch primitive every real skill-EXECUTION path funnels through.
- `app/api/agents_router.py::chat`'s call to `agent_orchestration.run_agent_conversation(agent_id, body.message, history_before_this_message, memory)` (only reached on the no-trigger-phrase-match branch).

**After / Outputs:**
- `email_classification.py`:
  ```python
  def run_capture_for_agent(agent_id: str, limit: int = 10) -> list[dict]:
      token = agent_presence.start_activity(agent_id, "capture")
      try:
          if agent_id == "email-capture":
              return classify_recent_emails(limit=limit)
          if agent_id == "meeting-capture":
              return meeting_classification.classify_recent_meetings()
          if agent_id == "todo-capture":
              return todo_classification.classify_recent_todos()
          raise ValueError(f"No background capture step for agent_id={agent_id!r}")
      finally:
          agent_presence.end_activity(agent_id, token)
  ```
- `skill_registry.py::_dispatch_skill` gains the identical wrap, `kind="capture"` (Scenario 1 groups capture and Skill runs under one glow treatment; a skill invoked mid-conversation via the model's own tool-calling is already covered by the chat wrap below, not double-marked here).
- `agents_router.py::chat`'s `run_agent_conversation` call:
  ```python
  token = agent_presence.start_activity(agent_id, "chat")
  try:
      conversation_result = await agent_orchestration.run_agent_conversation(
          agent_id, body.message, history_before_this_message, memory
      )
  finally:
      agent_presence.end_activity(agent_id, token)
  ```

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — wrap `run_capture_for_agent`'s body; add `from app.business import agent_presence` import.
- `src/backend/app/business/skill_registry.py` — wrap `_dispatch_skill`'s body; add `from app.business import agent_presence` import.
- `src/backend/app/api/agents_router.py` — wrap the `run_agent_conversation` call inside `chat`; add `from app.business import agent_presence` import (or extend the existing `app.business` import tuple).

---

## Constraints

- Every wrap uses `try/finally` — `end_activity` MUST run even when the wrapped call raises (`ADR-035`'s own Consequences: "a real correctness requirement... not just the happy path").
- `run_capture_for_agent`'s own `ValueError` for an unknown `agent_id` is raised from INSIDE the `try` — the `finally` still runs (harmless: `end_activity` on an `agent_id` that was never marked `_active` is idempotent by construction, since `start_activity` unconditionally set the token being cleared).
- `_dispatch_skill`'s own body (handler lookup, `agent_id` injection, dispatch) is otherwise byte-identical — this task only wraps it, never changes its logic.
- `agents_router.py::chat`'s trigger-phrase-matched branch (the `if matched["matched_action_id"] is not None:` branch) is NOT wrapped by this task — that path already dispatches through `_invoke_capability`/`_invoke_action`, whose own Skill-run instrumentation is this same task's `_dispatch_skill` wrap (skills) or is out of scope (legacy Actions, which this story does not instrument, per the story's own four-trigger Constraint naming only capture/Skill/chat/Hub-routed).
- Do not change any function's signature or return shape.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; or a real dev server for the chat half):
1. **[REQ-SB-42-US-01-AC-01]** Monkeypatch `email_classification.classify_recent_emails` to a function that, mid-call, asserts `agent_presence.get_snapshot()["active"].get("email-capture", {}).get("kind") == "capture"` (proving the marker is set DURING the real call), then returns `[]`. Call `email_classification.run_capture_for_agent("email-capture")`. After it returns, confirm `"email-capture" not in agent_presence.get_snapshot()["active"]` (cleared on completion). Revert the monkeypatch.
2. **[REQ-SB-42-US-01-AC-01]** Repeat step 1's shape with `classify_recent_emails` raising an exception instead of returning — confirm the exception propagates AND `"email-capture" not in agent_presence.get_snapshot()["active"]` afterward (the `finally` ran).
3. **[REQ-SB-42-US-01-AC-01]** Grant a real skill (e.g. `skill_registry.grant_skill_access("email-capture", "web-research")`), monkeypatch `skill_tools.web_research` to assert `agent_presence.get_snapshot()["active"].get("email-capture", {}).get("kind") == "capture"` mid-call, then call `skill_registry._dispatch_skill("email-capture", "web-research", {"query": "x"})`. Confirm the marker clears after. Revert.
4. **[REQ-SB-42-US-01-AC-02]** Real dev server (`uvicorn app.main:app --reload --port 8001`): send `POST /agents/vault-qa/chat` with a message that does NOT match a trigger phrase (routes to `run_agent_conversation`). While the request is in flight (or via a monkeypatch of `agent_orchestration.run_agent_conversation` that asserts the marker mid-call before calling through to the real function), confirm `agent_presence.get_snapshot()["active"]["vault-qa"]["kind"] == "chat"`; after the response returns, confirm the marker is cleared.
5. Non-AC smoke check: revoke any skill grants added for this test (`skill_registry.revoke_skill_access("email-capture", "web-research")` if not already granted before this test).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_capture_for_agent` wraps its body in `start_activity(agent_id, "capture")`/`end_activity` via `try/finally`
- [ ] `_dispatch_skill` wraps its body in `start_activity(agent_id, "capture")`/`end_activity` via `try/finally`, body otherwise unchanged
- [ ] `agents_router.py::chat`'s `run_agent_conversation` call wraps in `start_activity(agent_id, "chat")`/`end_activity` via `try/finally`
- [ ] The marker clears even when the wrapped call raises
- [ ] No function signature changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Hub-routed traveling-pulse instrumentation — `T03`.
- The pending-approval broadcast-only instrumentation — `T04`.
- The SSE endpoint and any frontend change.

---

## Context / Notes

Full mechanism: `ADR-035` point 3(a-c). Read `email_classification.py`, `skill_registry.py`, and `agents_router.py`'s REAL current bodies before editing (this project's own standing "compose around the real current file" pattern) — do not assume the code samples above are byte-for-byte what exists; reconcile against the real file.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
