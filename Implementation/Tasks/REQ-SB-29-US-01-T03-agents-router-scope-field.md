---
id: REQ-SB-29-US-01-T03
title: agents_router.py — PATCH /agents/{agent_id} (scope) + merged scope field on GET /agents/{agent_id}
parent_story: REQ-SB-29-US-01
requirement_id: REQ-SB-29
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-29-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-29-US-01-T03 — `agents_router.py` Vault scope surface

## Parent Story

- Story: [[REQ-SB-29-US-01]] — `../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-29 *Agent-to-Tag/Folder Scoping*

---

## Objective

Extend the existing `PATCH /agents/{agent_id}` verb and `GET /agents/{agent_id}` response with a `scope` field, per `ADR-014`'s established shared-verb pattern (the same endpoint `REQ-SB-18/19/20-US-01` already extended for `section_id`/`provider_id`/`keywords`) — composed at the router layer via `scope_registry`, without modifying `agent_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `agents_router.py`'s real current `AgentAssignmentUpdateBody`, `get_agent`, and `update_agent_assignment` (already carrying `section_id`/`provider_id`/`keywords`/`working_mode`, per `REQ-SB-18/19/20/21-US-01`) — read the REAL current file before applying this task's diff (it has been touched by multiple sibling stories since; do not overwrite with a stale sample).
- `T02` has landed `scope_registry.get_agent_scope(agent_id)` / `set_agent_scope(agent_id, scope) -> list[str]`.

**After / Outputs:**
- `GET /agents/{agent_id}` → the existing merged shape plus `"scope": list[str]`.
- `PATCH /agents/{agent_id}` (body gains `scope?: list[str]`) → whole-list-replaces the agent's scope when supplied, returns the same merged detail shape.
- `GET /agents` (list) is **unchanged** — `scope` is a detail-only field, matching `keywords`'s own precedent.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Extend the existing `app.business` import to include `scope_registry` (alphabetical, alongside the existing `agent_chat`, `agent_keywords`, `agent_orchestration`, `agent_registry`, `pending_approval_registry`, `provider_registry`, `section_registry`, `working_mode_registry`).
  - Extend the existing `AgentAssignmentUpdateBody`:
    ```python
    class AgentAssignmentUpdateBody(BaseModel):
        section_id: str | None = None
        provider_id: str | None = None
        keywords: list[str] | None = None
        working_mode: str | None = None
        scope: list[str] | None = None
    ```
  - In `get_agent`, add one more field to the returned dict, alongside the existing `"keywords"` key:
    ```python
    "scope": scope_registry.get_agent_scope(agent_id),
    ```
  - In `update_agent_assignment`, add one more branch, mirroring the existing `keywords` branch exactly:
    ```python
    if body.scope is not None:
        scope_registry.set_agent_scope(agent_id, body.scope)
    ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering (`ADR-003`); `agent_registry.py` is NOT modified by this task.
- `GET /agents/{agent_id}`'s pre-existing fields must be unchanged in shape and value — this is an additive-fields-only change.
- `GET /agents` (list) is explicitly **untouched** — no `scope` field added there this pass.
- `PATCH /agents/{agent_id}` with `scope` omitted (`null`/absent) must be a no-op for scope.
- `PATCH /agents/{agent_id}` with `{"scope": []}` (explicit empty list, not omitted) must clear the agent's scope — `[]` is a valid, meaningful value (Scenario 6's "no scope assigned" state), not treated the same as omission.
- Do not touch `trigger_action`, `chat`, or `get_history` — out of scope for this task.

---

## Tests

<!-- This story's Scenario 1 (AC-01) and Scenario 2 (AC-02) are user-
observable on the Agent Settings surface — their full verification lives
in T05 (AgentDetailPanel.tsx, the actual kv-row), per the established
"user-observable outcome" placement rule (REQ-SB-20-US-01-T03/T06
precedent). The steps below are non-AC smoke checks confirming this
endpoint's shape/behavior in isolation, ahead of T05's UI wiring. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET /agents/email-capture`. Confirm `scope` is present (`[]`, the default unassigned state) alongside every pre-existing field, unchanged in value/shape from before this task. `GET /agents` (list) — confirm no `scope` field appears there.
2. Non-AC smoke check: `PATCH /agents/email-capture` with `{"scope": ["customer/masdar"]}`. Confirm the response's `scope` is exactly that list. `GET /agents/email-capture` confirms the change persisted.
3. Non-AC smoke check: `PATCH /agents/email-capture` with `{"scope": ["customer/masdar", "Pipeline"]}` (a second, different scope value added — mirrors Scenario 2's own "assign a second scope" shape). Confirm the response's `scope` is exactly `["customer/masdar", "Pipeline"]` — both entries present, whole-list-replace semantics confirmed (not additive/merged at this layer — `T05`'s own UI-level draft-parsing is what produces the correct combined list to send).
4. Non-AC smoke check: `PATCH /agents/email-capture` with `{}` (empty body). Confirm `200` and the response's `scope` is unchanged (still the 2-item list from step 3) — a no-op body does not clear scope.
5. Non-AC smoke check: `PATCH /agents/email-capture` with `{"scope": []}` (explicit empty list). Confirm the response's `scope` is `[]` — an explicit empty list genuinely clears, unlike an omitted field.
6. Clean-up: `PATCH /agents/email-capture` with `{"scope": []}` (already done by step 5) to restore the clean seed-default (unassigned) state before later tasks' verification runs.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /agents/{agent_id}` includes `scope: list[str]`, additive to the pre-existing response shape; `GET /agents` (list) unchanged
- [x] `PATCH /agents/{agent_id}` accepts `{"scope"?: list[str]}` — omitted is a no-op, an explicit `[]` clears, a non-empty list whole-list-replaces
- [x] `agent_registry.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls this endpoint — `T05`.
- The scope-aware MCP retrieval tool — `T04` (that tool reads scope directly via `scope_registry.get_agent_scope`, not through this HTTP endpoint).

---

## Context / Notes

**Shared-file coordination (read before touching this file):**
`app/api/agents_router.py` is one of this codebase's most actively-extended
shared files (`REQ-SB-18/19/20/21/25/36-US-01` have all landed edits to it).
This task's own diff only touches `get_agent`/`update_agent_assignment`/
`AgentAssignmentUpdateBody`/the top-of-file import line — it does not touch
`chat`, `trigger_action`, `list_agents`, or `get_history`. Re-read the
file's real current state before applying this task's diff, per this
project's own established Learnings pattern (repeat drift on this exact
file has been found live multiple times already).

---

## Implementation Log

**2026-08-14 — Implemented and verified.** Read the REAL current
`agents_router.py` before editing (per this file's own known drift
history) — confirmed it already carries `REQ-SB-18/19/20/21/25/36`'s
landed edits (Skills dispatch fork via `_invoke_capability`/
`skill_tools.SKILLS`, async `_invoke_action`/`_execute_async_action`,
`compass-expert`'s `build_knowledge` handler) beyond this task's own
sample, none of which this task's diff touches. Applied exactly the
task's specified diff: `scope_registry` added to the `app.business`
import (alphabetically, between `provider_registry` and
`section_registry`); `AgentAssignmentUpdateBody` gained `scope: list[str]
| None = None`; `get_agent` gained `"scope": scope_registry.
get_agent_scope(agent_id)` alongside the existing `"keywords"` key;
`update_agent_assignment` gained the `if body.scope is not None:
scope_registry.set_agent_scope(agent_id, body.scope)` branch, mirroring
`keywords` exactly. `trigger_action`/`chat`/`get_history`/`list_agents`
untouched.

This story's `AC-01`/`AC-02` are fully verified at `T05` — the steps
below are this task's own non-AC smoke checks confirming the endpoint's
shape/behavior in isolation, run live against a real running backend
(`.venv\Scripts\uvicorn app.main:app --port 8001`).

1. `GET /agents/email-capture` → `scope: []` present (default unassigned
   state) alongside every pre-existing field, unchanged in value/shape.
   `GET /agents` (list) → confirmed no `scope` field on any of the 7 real
   agents (list comprehension of keys shown, none carry `scope`). PASS.
2. `PATCH /agents/email-capture` `{"scope": ["customer/masdar"]}` →
   response's `scope` exactly `["customer/masdar"]`; independent `GET`
   confirmed persistence. PASS.
3. `PATCH /agents/email-capture` `{"scope": ["customer/masdar",
   "Pipeline"]}` → response's `scope` exactly `["customer/masdar",
   "Pipeline"]`, whole-list-replace confirmed (2 entries, not merged/
   appended at this layer). PASS.
4. `PATCH /agents/email-capture` `{}` (empty body) → `200`, `scope`
   unchanged (still the 2-item list) — no-op body confirmed. PASS.
5. `PATCH /agents/email-capture` `{"scope": []}` (explicit empty list) →
   response's `scope` is `[]` — explicit clear confirmed, distinct from
   omission. PASS.
6. Clean-up: step 5's own `{"scope": []}` already restored the clean
   seed-default (unassigned) state; final `GET` confirms `scope: []`.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired; real-file
reconciliation needed (drift beyond the task's own sample) but produced
no contradiction, no new dependency, no shared-interface change beyond
what this task itself specifies.

Status: `Ready` → `Done`.
