---
id: REQ-SB-19-US-01-T04
title: agents_router.py — PATCH /agents/{agent_id} (provider_id) + merged provider fields + _invoke_action availability gate
parent_story: REQ-SB-19-US-01
requirement_id: REQ-SB-19
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-19-US-01-T02, REQ-SB-18-US-01-T04]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01-T04 — agents_router.py Provider-assignment surface + availability gate

## Parent Story

- Story: [[REQ-SB-19-US-01]] — `../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-19 *Per-Agent LLM Provider Selection*

---

## Objective

Extend `REQ-SB-18-US-01-T04`'s already-landed `PATCH /agents/{agent_id}`
with the `provider_id` portion of its body, merge `provider_id`/
`provider_name`/`provider_available` into `GET /agents/{agent_id}`'s
response, and add the Provider-availability gate inside `_invoke_action`
(`ADR-014` points 3 and 7) — reusing `ADR-011` point 3's "declared but not
yet backed by a real handler" pattern one layer up.

**This task requires `REQ-SB-18-US-01-T04` to already be `Done`** — it
edits the exact same file, on top of that task's already-landed code. Do
not start this task until that one is complete.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-18-US-01-T04` has landed: `AgentAssignmentUpdateBody(BaseModel)`
  with `section_id: str | None = None`; `list_agents`/`get_agent` merging
  `section_id`/`section_name`; `PATCH /agents/{agent_id}` calling
  `section_registry.set_agent_section`.
- `T02` has landed `provider_registry.get_agent_provider(agent_id)` /
  `set_agent_provider(agent_id, provider_id) -> bool` /
  `has_real_client(provider_id) -> bool`.
- `_invoke_action` currently looks up `_ACTION_HANDLERS.get((agent_id,
  action_id))` with no Provider check at all.

**After / Outputs:**
- `AgentAssignmentUpdateBody` gains `provider_id: str | None = None`.
- `list_agents`/`get_agent` additionally merge `provider_id`/
  `provider_name`/`provider_available` (detail only for the latter two;
  list gets `provider_id` only, matching the existing `section_id`-on-list
  precedent).
- `PATCH /agents/{agent_id}` additionally validates and applies a
  supplied `provider_id`.
- `_invoke_action` short-circuits with an honest unavailable message
  before ever calling a real handler, when the agent's Provider has no
  real client.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — add the `provider_registry`
  import, alongside the existing `section_registry` one (landed by
  `REQ-SB-18-US-01-T04`):
  ```python
  from app.business import agent_chat, agent_registry, provider_registry, section_registry
  ```
  Extend the existing `AgentAssignmentUpdateBody`:
  ```python
  class AgentAssignmentUpdateBody(BaseModel):
      section_id: str | None = None
      provider_id: str | None = None
  ```
  Extend `list_agents` (already merging `section_id` from
  `REQ-SB-18-US-01-T04`) to also merge `provider_id`:
  ```python
  @router.get("")
  def list_agents() -> list[dict]:
      agents = agent_registry.list_agents()
      for agent in agents:
          section = section_registry.get_agent_section(agent["id"])
          agent["section_id"] = section["id"] if section else None
          provider = provider_registry.get_agent_provider(agent["id"])
          agent["provider_id"] = provider["id"] if provider else None
      return agents
  ```
  Extend `get_agent` (already merging `section_id`/`section_name`) to also
  merge `provider_id`/`provider_name`/`provider_available`:
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
      }
  ```
  Extend `update_agent_assignment` (already handling `section_id`) to also
  handle `provider_id`:
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
      return get_agent(agent_id)
  ```
  Extend `_invoke_action` with the availability gate, placed before the
  existing `_ACTION_HANDLERS.get(...)` lookup:
  ```python
  def _invoke_action(agent_id: str, action_id: str) -> dict:
      """Shared by both the direct action-trigger endpoint and the chat
      endpoint, so a button click and a matching chat message invoke the
      identical handler and produce the identical history entries."""
      handler = _ACTION_HANDLERS.get((agent_id, action_id))
      if handler is None:
          return {"status": "error", "message": "This action is not yet available."}
      provider = provider_registry.get_agent_provider(agent_id)
      if provider is None or not provider_registry.has_real_client(provider["id"]):
          provider_name = provider["name"] if provider else "This agent's selected Provider"
          return {
              "status": "error",
              "message": f"{provider_name} is not available yet — no client has been built for it.",
          }
      results = handler()
      return {"status": "ok", "message": f"Done — {len(results)} email(s) filed."}
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`); `agent_registry.py`, `compass_client.py`, `app/config.py`
  NOT modified by this task.
- `_invoke_action`'s availability gate runs **before** the handler-lookup
  short-circuit is bypassed — i.e. it only matters once a real `handler`
  exists (an unavailable-provider agent with no handler at all still hits
  the pre-existing "not yet available" message first, for the same
  reason, just via a different branch — both branches say essentially the
  same honest thing, which is correct, not a defect).
- The gate must fire **without calling `handler()` at all** when the
  Provider is unavailable — no silent fallback to Compass, no fabricated
  response (`ADR-014` point 7, `REQ-SB-19` Scenario 7 literally).
- `list_agents`/`get_agent`'s pre-existing fields (including
  `REQ-SB-18-US-01-T04`'s own `section_id`/`section_name` additions) must
  be unchanged — purely additive.
- `PATCH /agents/{agent_id}` with only `{"provider_id": ...}` (no
  `section_id`) must not touch the agent's section assignment, and
  vice versa — each field is independently optional, per
  `REQ-SB-18-US-01-T04`'s own no-op-safe contract.

---

## Tests

<!-- This story's locked ACs are user-observable on the Agent Settings
surface (Scenario 5) or are backend-behavioral with no distinct frontend
rendering need (Scenarios 6, 7 — "an agent behaves/reports X", not "a
screen shows Y"). AC-06 is verified live in T06 (AgentDetailPanel.tsx);
AC-07/AC-08 are verified here, directly against the real backend, per the
established "user-observable outcome" placement rule (a purely functional/
API-level outcome is verified at the API level when no frontend rendering
distinction exists to check). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod` — **be deliberate**, per
`MEMORY.md`'s standing caution: step 1 below triggers one real Outlook/
Compass/vault-write capture run):

1. **[REQ-SB-19-US-01-AC-07]** Confirm `email-capture`'s Provider is
   `"compass"` (the untouched default — `GET /agents/email-capture`).
   `PATCH /providers/compass` with `{"endpoint":
   "https://compass.internal.example/api-edited"}` (edit the Provider
   *representation* only). Then, **exactly once**, `POST
   /agents/email-capture/actions/run_capture_now`. Confirm the response
   is `{"status": "ok", ...}` and a real capture run completes exactly as
   it did before this story existed — proving the edited representation
   in `agent_providers.json` had zero effect on the real call path
   (`app/data_access/compass_client.py` is untouched, still reading
   `.env`/`Settings.compass_*` directly, per `ADR-014` point 5).
   `PATCH /providers/compass` back to its original `endpoint` afterward
   (`https://compass.internal.example/api` matches the earlier
   `T03`-verification-observed value, or re-read it from
   `Settings().compass_base_url` before editing so it's restorable
   exactly).
2. **[REQ-SB-19-US-01-AC-08]** `POST /providers` with `{"name": "Verify
   Unavailable", "endpoint": "https://example.test", "credential": "x",
   "model": "x"}`. `PATCH /agents/email-capture` with `{"provider_id":
   "verify-unavailable"}`. Then `POST /agents/email-capture/actions/
   run_capture_now`. Confirm the response is `{"status": "error",
   "message": "Verify Unavailable is not available yet — no client has
   been built for it."}` and, critically, **no real Outlook/Compass call
   happened** (confirm via `GET /agents/email-capture/history` — the most
   recent `run_event` entry is this honest unavailable message, not a
   "Done — N email(s) filed" success message from an actual run).
   Clean-up: `PATCH /agents/email-capture` with `{"provider_id":
   "compass"}`, then `DELETE /providers/verify-unavailable`, restoring
   the seed state before later tasks' verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-07** (Scenario 6) — an agent using Compass behaves identically
      to before this story existed, regardless of any edit to the
      "Compass" Provider entry's representation
- [ ] **AC-08** (Scenario 7) — an agent whose selected Provider has no
      real client honestly reports unavailability, without invoking the
      handler, without falling back to Compass, without fabricating a
      response
- [ ] `GET /agents`/`GET /agents/{agent_id}` additionally merge
      `provider_id` (list) / `provider_id`+`provider_name`+
      `provider_available` (detail), purely additive to
      `REQ-SB-18-US-01-T04`'s existing fields
- [ ] `PATCH /agents/{agent_id}` accepts `{"provider_id"?}` independently
      of `{"section_id"?}`, `404` for an unknown provider id
- [ ] `agent_registry.py`, `compass_client.py`, `app/config.py` not
      modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component — `T06` (`AgentDetailPanel.tsx`).
- The Section-assignment portion of `PATCH /agents/{agent_id}` and
  `section_id`/`section_name` merging — already landed by
  `REQ-SB-18-US-01-T04`, untouched here beyond the additive extension
  shown above.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Why this task requires an out-of-story `depends_on`:** this task and
`REQ-SB-18-US-01-T04` both edit `app/api/agents_router.py`'s
`AgentAssignmentUpdateBody`/`list_agents`/`get_agent`/
`update_agent_assignment`. Wiring this task's `depends_on` to name
`REQ-SB-18-US-01-T04` explicitly (a cross-story task-id edge, which
`depends_on` supports — task ids, never story ids) guarantees the build
loop lands the Section portion first, and this task's own code blocks
above are written as the literal diff on top of that already-landed
state — never two tasks racing to edit the same file in parallel.

`REQ-SB-19` Scenario 7's only currently-real, non-LLM-independent handler
this pass is `email-capture`'s `run_capture_now` (`ADR-011`) — this is why
step 2's verification reassigns `email-capture` itself to the unavailable
test Provider, rather than an agent with no handler at all (which would
already return "not yet available" via the pre-existing handler-lookup
branch, proving nothing new about this task's own gate).

---

## Implementation Log

**Built 2026-08-11 (coder).** `src/backend/app/api/agents_router.py`
extended verbatim per this task's own diff, on top of
`REQ-SB-18-US-01-T04`'s already-landed Section portion: `provider_registry`
import added; `AgentAssignmentUpdateBody` gained `provider_id`;
`list_agents`/`get_agent` merge `provider_id` (list) /
`provider_id`+`provider_name`+`provider_available` (detail);
`update_agent_assignment` applies a supplied `provider_id` independently of
`section_id`; `_invoke_action` gained the availability-gate check before
the handler lookup's short-circuit is bypassed.

**Live verification (real backend on `:8001`, real HTTP), both AC-tagged
scenarios, deliberate (each triggers a real Outlook/Compass/vault-write
capture run exactly once, per this task's own instruction):**

- **[REQ-SB-19-US-01-AC-07]** Confirmed `email-capture`'s Provider was
  `"compass"` (untouched default). `PATCH /providers/compass`
  `{"endpoint": "https://compass.internal.example/api-edited"}` (edits the
  Provider *representation* only). `POST
  /agents/email-capture/actions/run_capture_now` (exactly once) →
  `{"status": "ok", "message": "Done — 0 email(s) filed."}` — a real
  capture run completed normally despite the edited representation,
  confirming `compass_client.py` never reads `agent_providers.json`'s
  Compass entry, only the real `.env`-sourced `Settings.compass_*`.
  `PATCH /providers/compass` restored to the real `.env` value
  (`https://api.core42.ai/v1/chat/completions`, read from `.env` directly
  before editing so the restore was exact). **PASS.**
- **[REQ-SB-19-US-01-AC-08]** `POST /providers` `{"name": "Verify
  Unavailable", ...}`. `PATCH /agents/email-capture`
  `{"provider_id": "verify-unavailable"}`. `POST
  /agents/email-capture/actions/run_capture_now` →
  `{"status": "error", "message": "Verify Unavailable is not available yet
  — no client has been built for it."}`. Confirmed via `GET
  /agents/email-capture/history` that the most recent `run_event` entry is
  this exact honest-unavailable message, immediately following the
  AC-07 step's own "Done — 0 email(s) filed." entry — no new "Capture run
  completed"/"Done — N email(s) filed" success entry appears after it,
  confirming no real Outlook/Compass call happened for this trigger.
  Cleaned up: `PATCH /agents/email-capture` `{"provider_id": "compass"}`,
  `DELETE /providers/verify-unavailable`. **PASS.**

Also confirmed (non-AC): `GET /agents` (list) merges `provider_id`
additively alongside the existing `section_id`, for all 5 agents, all
`"compass"` in the seeded/self-healed state. `agent_registry.py`,
`compass_client.py`, `app/config.py` unmodified — confirmed by inspection.
No assumptions beyond this task's own literal code (implemented verbatim).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired. Both trust-surface
scenarios (AC-07 no-regression, AC-08 honest-unavailable-no-fallback-no-
fabrication) verified against the real backend, not a construction.
