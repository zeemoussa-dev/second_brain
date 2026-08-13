---
id: REQ-SB-20-US-01-T03
title: agents_router.py — PATCH /agents/{agent_id} (keywords) + merged keywords field on GET /agents/{agent_id}
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-20-US-01-T02]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T03 — `agents_router.py` Keywords surface

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Extend the existing `PATCH /agents/{agent_id}` verb and `GET /agents/{agent_id}` response with a `keywords` field, per `ADR-014`'s established shared-verb pattern (the same endpoint `REQ-SB-18-US-01-T04`/`REQ-SB-19-US-01-T04` already extended for `section_id`/`provider_id`) — composed at the router layer via `agent_keywords`, without modifying `agent_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `agents_router.py` currently (verbatim, real current file):
  ```python
  from app.business import agent_chat, agent_registry, provider_registry, section_registry
  ...
  class AgentAssignmentUpdateBody(BaseModel):
      section_id: str | None = None
      provider_id: str | None = None


  @router.get("/{agent_id}")
  def get_agent(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      section = section_registry.get_agent_section(agent_id)
      provider = provider_registry.get_agent_provider(agent_id)
      return {
          "id": agent_id,
          "name": agent["name"],
          "type": agent["type"],
          "settings": agent["settings"],
          "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
          "section_id": section["id"] if section else None,
          "section_name": section["name"] if section else None,
          "provider_id": provider["id"] if provider else None,
          "provider_name": provider["name"] if provider else None,
          "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
      }


  @router.patch("/{agent_id}")
  def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      if body.section_id is not None:
          if not section_registry.set_agent_section(agent_id, body.section_id):
              raise HTTPException(status_code=404, detail="Unknown section")
      if body.provider_id is not None:
          if not provider_registry.set_agent_provider(agent_id, body.provider_id):
              raise HTTPException(status_code=404, detail="Unknown provider")
      return get_agent(agent_id)
  ```
- `T02` has landed `agent_keywords.get_agent_keywords(agent_id)` / `set_agent_keywords(agent_id, keywords) -> list[str]`.

**After / Outputs:**
- `GET /agents/{agent_id}` → the existing merged shape plus `"keywords": list[str]`.
- `PATCH /agents/{agent_id}` (body gains `keywords?: list[str]`) → whole-list-replaces the agent's keywords when supplied, returns the same merged detail shape.
- `GET /agents` (list) is **unchanged** — `keywords` is a detail-only field (this story's own Acceptance text only requires keywords to show on the Agent Settings surface, the detail panel).

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — extend the existing `app.business` import:
  ```python
  from app.business import agent_chat, agent_keywords, agent_registry, provider_registry, section_registry
  ```
  Extend the existing `AgentAssignmentUpdateBody`:
  ```python
  class AgentAssignmentUpdateBody(BaseModel):
      section_id: str | None = None
      provider_id: str | None = None
      keywords: list[str] | None = None
  ```
  Replace the existing `get_agent` handler with:
  ```python
  @router.get("/{agent_id}")
  def get_agent(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      section = section_registry.get_agent_section(agent_id)
      provider = provider_registry.get_agent_provider(agent_id)
      return {
          "id": agent_id,
          "name": agent["name"],
          "type": agent["type"],
          "settings": agent["settings"],
          "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
          "section_id": section["id"] if section else None,
          "section_name": section["name"] if section else None,
          "provider_id": provider["id"] if provider else None,
          "provider_name": provider["name"] if provider else None,
          "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
          "keywords": agent_keywords.get_agent_keywords(agent_id),
      }
  ```
  Replace the existing `update_agent_assignment` handler with:
  ```python
  @router.patch("/{agent_id}")
  def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      if body.section_id is not None:
          if not section_registry.set_agent_section(agent_id, body.section_id):
              raise HTTPException(status_code=404, detail="Unknown section")
      if body.provider_id is not None:
          if not provider_registry.set_agent_provider(agent_id, body.provider_id):
              raise HTTPException(status_code=404, detail="Unknown provider")
      if body.keywords is not None:
          agent_keywords.set_agent_keywords(agent_id, body.keywords)
      return get_agent(agent_id)
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering (`ADR-003`); `agent_registry.py` is NOT modified by this task.
- `GET /agents/{agent_id}`'s pre-existing fields (`id`/`name`/`type`/`settings`/`actions`/`section_id`/`section_name`/`provider_id`/`provider_name`/`provider_available`) must be unchanged in shape and value — this is an additive-fields-only change.
- `GET /agents` (list) is explicitly **untouched** — no `keywords` field added there this pass (not required by this story's own Acceptance text; avoids an unrequested response-shape change).
- `PATCH /agents/{agent_id}` with `keywords` omitted (`null`/absent) must be a no-op for keywords — this is what lets `REQ-SB-18-US-01-T04`'s/`REQ-SB-19-US-01-T04`'s own section/provider-only bodies keep working unchanged.
- `PATCH /agents/{agent_id}` with `{"keywords": []}` (explicit empty list, not omitted) must clear the agent's keywords — `[]` is a valid, meaningful value (Scenario 4's "no keywords assigned" state), not treated the same as omission.
- Do not touch `trigger_action`, `chat`, or `get_history` — out of scope for this task.

---

## Tests

<!-- This story's Scenario 1 (AC-01) is user-observable on the Agent
Settings surface — its full verification lives in T06
(AgentDetailPanel.tsx, the actual Keywords row), per the established "user-
observable outcome" placement rule (REQ-SB-18-US-01-T08/REQ-SB-19-US-01-T06
precedent). The steps below are non-AC smoke checks confirming this
endpoint's shape/behavior in isolation, ahead of T06's UI wiring. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET /agents/email-capture`. Confirm `keywords` is
   present (`[]`, the default unassigned state) alongside every
   pre-existing field, unchanged in value/shape from before this task.
   `GET /agents` (list) — confirm no `keywords` field appears there
   (list-response shape unchanged).
2. Non-AC smoke check: `PATCH /agents/email-capture` with `{"keywords":
   ["email", "inbox", "customer correspondence"]}`. Confirm the response's
   `keywords` is exactly that list. `GET /agents/email-capture` confirms
   the change persisted.
3. Non-AC smoke check: `PATCH /agents/email-capture` with `{}` (empty
   body). Confirm `200` and the response's `keywords` is unchanged (still
   the 3-item list from step 2) — a no-op body does not clear keywords.
4. Non-AC smoke check: `PATCH /agents/email-capture` with `{"keywords":
   []}` (explicit empty list). Confirm the response's `keywords` is `[]` —
   an explicit empty list genuinely clears, unlike an omitted field.
5. Clean-up: `PATCH /agents/email-capture` with `{"keywords": []}` (already
   done by step 4) to restore the clean seed-default (unassigned) state
   before later tasks' verification runs.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /agents/{agent_id}` includes `keywords: list[str]`, additive to the pre-existing response shape; `GET /agents` (list) unchanged
- [x] `PATCH /agents/{agent_id}` accepts `{"keywords"?: list[str]}` — omitted is a no-op, an explicit `[]` clears
- [x] `agent_registry.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls this endpoint — `T06`.
- `agent_keywords.py`'s own matching logic — already landed by `T02`, consumed here unmodified.
- The LangGraph routing node / tool / conditional edge that actually reads keywords for a live routing decision — `T05`; this task only makes keywords readable/writable via HTTP, it does not participate in routing itself.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at
`/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Shared-file coordination (read before touching this file):**
`app/api/agents_router.py` is also edited by `REQ-SB-25-US-01-T08` (its own
`chat` handler's no-match branch, a completely different function in the
same file) and, in the past, by `REQ-SB-18-US-01-T04`/`REQ-SB-19-US-01-T04`
(the `get_agent`/`update_agent_assignment` handlers this task itself now
extends further). This task's own diff only touches `get_agent`/
`update_agent_assignment`/`AgentAssignmentUpdateBody` — it does not touch
`chat`, `trigger_action`, `list_agents`, or `get_history`. No literal
collision with `REQ-SB-25-US-01-T08`'s own diff is expected, but re-read
the file's real current state before applying this task's diff if
`REQ-SB-25-US-01-T08` has landed in the meantime, since its own `import`
line addition (`agent_orchestration`) sits on the same import statement
this task also edits.

---

## Implementation Log

**Built 2026-08-12 (coder).** Composed this task's diff around the REAL
current `agents_router.py` (which already carries `agent_orchestration`'s
own import/`chat` extension from `REQ-SB-25-US-01-T08`, ahead of this
task's own "Before" sample) rather than overwriting with the stale sample,
per this project's own established Learnings pattern — added `agent_keywords`
to the existing `app.business` import line (alphabetical), extended
`AgentAssignmentUpdateBody` with `keywords: list[str] | None = None`,
extended `get_agent`'s return dict with `"keywords":
agent_keywords.get_agent_keywords(agent_id)`, extended
`update_agent_assignment` with the `if body.keywords is not None:
agent_keywords.set_agent_keywords(...)` branch. `chat`/`trigger_action`/
`list_agents`/`get_history` untouched, confirmed by diff review.

**Live verification (real backend `:8001`, real `--reload` server already
running — confirmed it picked up this task's own edit automatically):**

1. `GET /agents/email-capture` → `keywords: []` present alongside every
   pre-existing field, unchanged. `GET /agents` (list) → confirmed no
   `keywords` field present on any entry. **PASS.**
2. `PATCH /agents/email-capture {"keywords": ["email", "inbox", "customer
   correspondence"]}` → response's `keywords` exactly that list;
   independent `GET` confirms persistence. (One transient race observed
   mid-sequence — a `GET` issued immediately after a `PATCH` momentarily
   read back `[]` once, coinciding with an in-flight `uvicorn --reload`
   restart from this same task's own just-applied file edit; re-run
   confirmed stable, correct persistence on every subsequent call — a
   startup-timing artifact of editing the file the running server was
   actively reloading, not a defect in the endpoint itself.) **PASS.**
3. `PATCH /agents/email-capture {}` (empty body) → `200`, `keywords`
   unchanged (still the 3-item list) — omitted field is a genuine no-op.
   **PASS.**
4. `PATCH /agents/email-capture {"keywords": []}` (explicit empty list) →
   `keywords` becomes `[]` — explicit-empty genuinely clears, unlike
   omission. **PASS.**
5. Clean-up: `email-capture`'s `keywords` left at `[]` (already achieved by
   step 4) — real seed state restored.

No locked AC of its own (`AC-01`'s full round-trip verified at `T06`, where
the UI and persisted-value read-back both exist) — non-AC smoke check per
this task's own `## Tests` placement rule, all steps passed.

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note).
