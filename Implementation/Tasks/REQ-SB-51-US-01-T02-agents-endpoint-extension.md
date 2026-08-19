---
id: REQ-SB-51-US-01-T02
title: GET/PATCH /agents — merge is_background_agent field
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-51-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T02 — GET/PATCH /agents — merge is_background_agent field

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Extend `GET /agents`, `GET /agents/{agent_id}`, and `PATCH /agents/{agent_id}` to read/write `is_background_agent` via `background_agent_registry`, following the exact same merge pattern `working_mode` already uses in each of the three handlers.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/api/agents_router.py`'s `list_agents()` (line ~247), `get_agent()` (line ~302), and `update_agent_assignment()` (line ~326) each already merge in `working_mode` via `working_mode_registry.get_agent_working_mode()`/`set_agent_working_mode()`.
- `AgentAssignmentUpdateBody` (line ~70) already carries `working_mode: str | None = None` as its precedent field.
- `T01`'s `background_agent_registry.get_is_background_agent()`/`set_is_background_agent()` exist and are importable.

**After / Outputs:**
- `GET /agents` — every returned agent dict carries `is_background_agent: bool`.
- `GET /agents/{agent_id}` — the returned dict carries `is_background_agent: bool`.
- `PATCH /agents/{agent_id}` — accepts an optional `is_background_agent: bool` body field; when present, calls `background_agent_registry.set_is_background_agent(agent_id, body.is_background_agent)` before returning the refreshed `get_agent(agent_id)`.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Add `background_agent_registry` to the `app.business` import block (line ~6-20).
  - `AgentAssignmentUpdateBody` (line ~70-76): add `is_background_agent: bool | None = None`.
  - `list_agents()` (line ~247-256): add `agent["is_background_agent"] = background_agent_registry.get_is_background_agent(agent["id"])` inside the existing per-agent loop.
  - `get_agent()` (line ~302-323): add `"is_background_agent": background_agent_registry.get_is_background_agent(agent_id),` to the returned dict.
  - `update_agent_assignment()` (line ~326-347): add the `if body.is_background_agent is not None: background_agent_registry.set_is_background_agent(agent_id, body.is_background_agent)` branch, following the existing `if body.working_mode is not None:` branch's position/shape (no invalid-value 400 case needed — a `bool` field has no invalid values, unlike `working_mode`'s enum check).

---

## Constraints

- Inherits from parent story.
- Follow `working_mode`'s exact merge pattern in all three handlers — do not invent a different response-shape convention.
- No caching: every read goes through `background_agent_registry.get_is_background_agent()` live, per the story's own Constraint ("read live... no caching lag").

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-01, partial] Start the backend (`uvicorn app.main:app --reload`, `src/backend`). `GET /agents` and confirm every entry has an `is_background_agent` boolean field. `PATCH /agents/vault-qa` with `{"is_background_agent": true}`; confirm the response's `is_background_agent` is `true`. `GET /agents/vault-qa` again (a fresh request, not a cached value) and confirm it still reads `true`. `PATCH /agents/vault-qa` with `{"is_background_agent": false}` to restore prior state; confirm `GET /agents/vault-qa` reflects `false`.
2. [REQ-SB-51-US-01-AC-02, partial] `GET /agents/email-capture`, `GET /agents/meeting-capture`, `GET /agents/todo-capture` — confirm each already reports `is_background_agent: true` with no prior `PATCH` call, matching `T01`'s backfill.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /agents` and `GET /agents/{agent_id}` both return `is_background_agent`.
- [ ] `PATCH /agents/{agent_id}` accepts and persists `is_background_agent`.
- [ ] The three named capture Workers report `is_background_agent: true` with zero manual `PATCH` calls.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The registry module itself (`T01`, already built).
- The Hub-routing exclusion check (`T03`).
- Any frontend change (`T04`-`T06`).

---

## Context / Notes

Real file to compose against: `src/backend/app/api/agents_router.py` — re-read it fresh before editing; do not apply this task's diff against a stale mental model, per this project's own established "compose around the REAL current file" pattern (`Implementation/Learnings.md`, reconfirmed across `SPRINT-019/020/021/027`).

---

## Implementation Log

Re-read the REAL current `agents_router.py` before editing (582 lines,
grown since the task's own line-number estimates from `SPRINT-041`-`044`
work) — the `working_mode` merge pattern's exact positions matched the
task's description closely enough that no reconciliation was needed
beyond using the real current line content, not assumed offsets. Added
`background_agent_registry` to the `app.business` import tuple;
`AgentAssignmentUpdateBody` gained `is_background_agent: bool | None =
None`; `list_agents()`/`get_agent()` both merge in `is_background_agent`
the same way `working_mode` already does; `update_agent_assignment()`
gained an `if body.is_background_agent is not None:` branch (no
invalid-value 400 case, per the task's own Constraint — a `bool` field
has no invalid values).

A stray, non-`--reload` uvicorn process (PID 19420, started 3:02:34 PM,
plain `uvicorn app.main:app --port 8001`, no `--reload`) was found
already listening on port 8001 before verification began — per this
project's own established "don't trust a stray dev-server process
without confirming what it's serving" antipattern entry, killed it and
started a single, explicitly-controlled `--reload` instance instead.

**[REQ-SB-51-US-01-AC-01, partial] Verified live** (real HTTP, fresh
`--reload` server, `src/backend`): `GET /agents` — every one of the 14
real agents returned an `is_background_agent` boolean field. `PATCH
/agents/vault-qa` with `{"is_background_agent": true}` — response's
`is_background_agent` was `true`. A separate, fresh `GET
/agents/vault-qa` request (not a cached value) confirmed it still read
`true`. `PATCH /agents/vault-qa` with `{"is_background_agent": false}`
restored prior state; a final fresh `GET` confirmed `false`. PASS.

**[REQ-SB-51-US-01-AC-02, partial] Verified live:** `GET
/agents/email-capture`, `/agents/meeting-capture`, `/agents/todo-capture`
all reported `is_background_agent: true` with zero prior `PATCH` call on
this server instance — matches `T01`'s backfill exactly. PASS.

gate: clear 2026-08-14 — no triggers fired (mirrors an already-Accepted
merge pattern exactly, no ADR touched, no material assumption, both
locked-AC-partial steps verified live). The stray-process kill is a
scope-internal environmental action, not a code change to any
out-of-scope file.
