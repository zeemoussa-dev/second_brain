---
id: REQ-SB-18-US-01-T04
title: agents_router.py — PATCH /agents/{agent_id} (section_id) + merged section fields on GET /agents, GET /agents/{agent_id}
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T04 — agents_router.py Section-assignment surface

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Add the new `PATCH /agents/{agent_id}` verb to the existing
`app/api/agents_router.py` (`ADR-014` point 3) and merge `section_id`
(list) / `section_id`+`section_name` (detail) into `GET /agents` and
`GET /agents/{agent_id}`'s existing response shapes — composed at the
router layer via `section_registry`, without modifying `agent_registry.py`
(`ADR-014` point 2).

**Cross-story coordination note:** `REQ-SB-19-US-01-T04` extends this same
`PATCH /agents/{agent_id}` endpoint with the `provider_id` portion of its
body, and this same router's `_invoke_action` with the Provider-
availability gate. That task's own `depends_on` names this task
explicitly, so the two edits land in strict sequence, never in parallel,
on this shared file — see this task's Context/Notes.

---

## Starting State → End State

**Before / Inputs:**
- `agents_router.py` currently has `GET /agents` (`agent_registry.
  list_agents()` verbatim), `GET /agents/{agent_id}`, `POST /agents/
  {agent_id}/actions/{action_id}`, `POST /agents/{agent_id}/chat`,
  `GET /agents/{agent_id}/history` — no `PATCH` verb, no section-related
  field anywhere in any response.
- `T02` has landed `section_registry.get_agent_section(agent_id)` /
  `set_agent_section(agent_id, section_id) -> bool`.

**After / Outputs:**
- `GET /agents` → `[{"id","name","type","section_id"}]`.
- `GET /agents/{agent_id}` → the existing `{"id","name","type","settings",
  "actions"}` shape plus `"section_id"`, `"section_name"`.
- `PATCH /agents/{agent_id}` (body: `{"section_id"?: str}`) → validates
  the supplied `section_id` exists (`404` if not), updates the
  assignment, returns the same merged detail shape `GET /agents/
  {agent_id}` returns.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — add the `section_registry`
  import:
  ```python
  from app.business import agent_chat, agent_registry, section_registry
  ```
  Add a new request body model near the existing `ChatMessageBody`:
  ```python
  class AgentAssignmentUpdateBody(BaseModel):
      section_id: str | None = None
  ```
  Replace the existing `list_agents` and `get_agent` handlers with:
  ```python
  @router.get("")
  def list_agents() -> list[dict]:
      agents = agent_registry.list_agents()
      for agent in agents:
          section = section_registry.get_agent_section(agent["id"])
          agent["section_id"] = section["id"] if section else None
      return agents


  @router.get("/{agent_id}")
  def get_agent(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      section = section_registry.get_agent_section(agent_id)
      return {
          "id": agent_id,
          "name": agent["name"],
          "type": agent["type"],
          "settings": agent["settings"],
          "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
          "section_id": section["id"] if section else None,
          "section_name": section["name"] if section else None,
      }
  ```
  Add a new handler, placed after `get_agent` and before
  `trigger_action`:
  ```python
  @router.patch("/{agent_id}")
  def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      if body.section_id is not None:
          if not section_registry.set_agent_section(agent_id, body.section_id):
              raise HTTPException(status_code=404, detail="Unknown section")
      return get_agent(agent_id)
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`); `agent_registry.py` is NOT modified by this task.
- `list_agents`/`get_agent`'s existing fields (`id`/`name`/`type`/
  `settings`/`actions`) must be unchanged in shape and value — this is an
  additive-fields-only change; any existing caller reading only the
  previously-existing fields is unaffected (`ADR-014`'s own Consequences).
- `PATCH /agents/{agent_id}` must 404 for an unknown `agent_id` and 404
  for a supplied `section_id` that doesn't exist — never silently ignore
  an invalid id.
- `PATCH /agents/{agent_id}` with an empty body (`{}`, `section_id`
  omitted) must be a no-op that still returns the current merged detail —
  this is what lets `REQ-SB-19-US-01-T04` reuse the identical endpoint for
  a `provider_id`-only body without this task's own section logic firing.
- Do not touch `trigger_action`, `chat`, or `get_history` — out of scope
  for this task (Provider-availability gating inside `_invoke_action` is
  `REQ-SB-19-US-01-T04`'s own scope).

---

## Tests

<!-- This story's locked ACs are user-observable on the Agent Settings
surface — verified live in T05 (layoutAgents.ts, list-shape consumption)
and T08 (AgentDetailPanel.tsx, the actual reassignment UI), per the
established "user-observable outcome" placement rule. The steps below are
non-AC smoke checks confirming this endpoint's shape/behavior in
isolation. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET /agents`. Confirm every entry now has a
   `section_id` (non-null, defaulted to `"technical"` for any agent never
   explicitly reassigned). `GET /agents/email-capture`. Confirm
   `section_id`/`section_name` are present alongside the pre-existing
   `settings`/`actions` fields, unchanged in value/shape from before this
   task.
2. Non-AC smoke check: `PATCH /agents/email-capture` with `{"section_id":
   "sales"}`. Confirm the response's `section_id` is `"sales"`,
   `section_name` is `"Sales"`. `GET /agents/email-capture` confirms the
   change persisted. `PATCH /agents/email-capture` with `{"section_id":
   "not-a-real-id"}` — confirm `404`, and a follow-up `GET
   /agents/email-capture` confirms the assignment is unchanged (still
   `"sales"`). `PATCH /agents/not-a-real-agent` with any body — confirm
   `404`.
3. Non-AC smoke check: `PATCH /agents/email-capture` with `{}` (empty
   body). Confirm `200` and the response's `section_id` is unchanged
   (still `"sales"`) — a no-op body does not clear or alter the
   assignment.
4. Clean-up: `PATCH /agents/email-capture` with `{"section_id":
   "technical"}` to restore the seed-default assignment before later
   tasks' verification runs.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /agents` includes `section_id` per agent; `GET
      /agents/{agent_id}` includes `section_id`/`section_name`, both
      additive to the pre-existing response shape
- [ ] `PATCH /agents/{agent_id}` accepts `{"section_id"?}`, validates the
      supplied id, `404` for an unknown agent or unknown section,
      no-op-safe for an empty body
- [ ] `agent_registry.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls this endpoint — `T05`, `T08`.
- The `provider_id` portion of the `PATCH` body, the Provider-availability
  gate inside `_invoke_action`, and the merged `provider_*` response
  fields — all `REQ-SB-19-US-01-T04`'s own scope (that task depends on
  this one).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Shared-file coordination (read before touching this file):**
`app/api/agents_router.py` is edited by two sibling stories' tasks this
sprint — this task (Section-assignment portion) and
`REQ-SB-19-US-01-T04` (Provider-assignment portion, `depends_on: [...,
REQ-SB-18-US-01-T04]`). This task must land and be `Done` first; the other
task's own spec shows the exact diff it applies on top of this task's
already-landed code (extending `AgentAssignmentUpdateBody` with
`provider_id`, extending `list_agents`/`get_agent`'s merge step, and
adding the availability gate inside `_invoke_action`). Do not attempt to
pre-build any Provider-related field or check here — that would collide
with the other task's own literal diff.

---

## Implementation Log

**2026-08-11 — Done.** `agents_router.py` extended exactly per the task's
own code block: `section_registry` import added; `AgentAssignmentUpdateBody`
model added; `list_agents`/`get_agent` merge in `section_id`/`section_name`
via `section_registry.get_agent_section`; new `PATCH /agents/{agent_id}`
handler placed after `get_agent`, before `trigger_action`.

Live verification (real backend, `uvicorn app.main:app --port 8001`):
1. `GET /agents` → every entry has `section_id: "technical"` (seed
   default). `GET /agents/email-capture` → `section_id`/`section_name`
   present alongside the unchanged pre-existing `settings`/`actions`
   fields.
2. `PATCH /agents/email-capture {"section_id":"sales"}` → response
   `section_id: "sales"`, `section_name: "Sales"`; `GET
   /agents/email-capture` confirms persisted. `PATCH
   {"section_id":"not-a-real-id"}` → `404`, follow-up `GET` confirms
   assignment unchanged (still `"sales"`). `PATCH /agents/not-a-real-agent`
   → `404`.
3. `PATCH /agents/email-capture {}` (empty body) → `200`, `section_id`
   unchanged (`"sales"`) — no-op confirmed.
4. Clean-up: `PATCH /agents/email-capture {"section_id":"technical"}` —
   restored the seed-default assignment before later tasks' verification.

`agent_registry.py` not modified (confirmed by diff — only
`agents_router.py`/`main.py`/`sections_router.py` touched this pass).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block, no assumption needed.
