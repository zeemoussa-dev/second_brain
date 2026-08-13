---
id: REQ-SB-36-US-01-T05
title: skill_registry.invoke_skill additive args parameter; skills_router.py optional invoke body
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created) plus the same mid-build operator correction recorded on T04 (adr-deviation, ESCALATIONS.md -> ESC-019, Resolved) -- this task's own invoke_skill needed one additional, additive change (agent_id injection) to carry it. See Implementation Log."
phase: P1
depends_on: [REQ-SB-36-US-01-T04]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T05 — `invoke_skill`'s additive `args` parameter

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Extend the already-`Done` `skill_registry.invoke_skill(agent_id, skill_id)` (`REQ-SB-27-US-01`) with an additive optional third parameter, `args: dict | None = None`, threaded through to the resolved handler when it accepts one — the mechanism `web_research`'s own `query` argument needs (`ADR-022` point 5). `skills_router.py`'s invoke endpoint gains a matching optional JSON body. This is where the full Scenario 1 (real, granted invocation) and Scenario 2 (refused, ungranted) round trips become verifiable end-to-end.

---

## Starting State → End State

**Before / Inputs:**
- `T04` has landed `skill_tools.SKILLS["web-research"]`/`skill_tools.web_research(query)`.
- `skill_registry.invoke_skill(agent_id, skill_id)` takes no `args`; `_SKILL_HANDLERS = {"diagram-understanding": skill_tools.diagram_understanding}` (zero-arg call only). `skills_router.py`'s invoke endpoint takes no request body.

**After / Outputs:**
- `skill_registry._SKILL_HANDLERS` gains `"web-research": skill_tools.web_research`.
- `skill_registry.invoke_skill(agent_id, skill_id, args: dict | None = None) -> dict` — when `args` is given and the resolved handler accepts a parameter, calls `handler(**args)`; otherwise calls `handler()` unchanged (every existing zero-arg caller, i.e. `diagram-understanding`, is unaffected).
- `skills_router.py`'s `POST /agents/{agent_id}/skills/{skill_id}/invoke` accepts an optional JSON body (e.g. `{"query": "..."}`), passed through as `args`.

---

## Files to Modify

- `src/backend/app/business/skill_registry.py`:
  ```python
  _SKILL_HANDLERS = {
      "diagram-understanding": skill_tools.diagram_understanding,
      "web-research": skill_tools.web_research,
  }


  def invoke_skill(agent_id: str, skill_id: str, args: dict | None = None) -> dict:
      """Never raises for ordinary control flow -- returns a result dict
      the router translates into the right HTTP response. Checks access
      before checking whether a real handler exists, so Scenario 2's
      refusal and Scenario 4's honest-unavailable stay distinguishable
      (AC-02 vs AC-04). `args` is additive -- every existing zero-arg
      caller (diagram-understanding) is unaffected, since args defaults
      to None and is only threaded through when given."""
      if skill_id not in skill_tools.SKILLS:
          return {"status": "unknown_skill"}
      if not has_skill_access(agent_id, skill_id):
          return {"status": "refused", "reason": "Agent does not have access to this skill."}
      handler = _SKILL_HANDLERS[skill_id]
      if args:
          return handler(**args)
      return handler()
  ```
- `src/backend/app/api/skills_router.py`:
  ```python
  from pydantic import BaseModel


  class InvokeSkillBody(BaseModel):
      query: str | None = None


  @router.post("/agents/{agent_id}/skills/{skill_id}/invoke")
  def invoke_skill(agent_id: str, skill_id: str, body: InvokeSkillBody | None = None) -> dict:
      _require_known_agent(agent_id)
      args = body.model_dump(exclude_none=True) if body else None
      result = skill_registry.invoke_skill(agent_id, skill_id, args)
      if result.get("status") == "unknown_skill":
          raise HTTPException(status_code=404, detail="Unknown skill")
      if result.get("status") == "refused":
          raise HTTPException(status_code=403, detail=result.get("reason", "Access refused"))
      return result
  ```
  (`InvokeSkillBody` is intentionally a loose, additive shape — `query` today, more fields later if a future skill needs them — rather than a per-skill-typed body, since `invoke_skill`'s own `args` parameter is already generic `dict | None`.)

---

## Constraints

- Inherits from parent story and `ADR-022` point 5.
- `args` is additive and optional — every existing zero-arg caller (`diagram-understanding`) must be unaffected; do not change `diagram_understanding`'s own signature.
- `has_skill_access` is checked BEFORE dispatching to the handler, unchanged from the existing order — Scenario 2's refusal must never depend on `args` being present or absent.
- The web-research skill is invoked exclusively through this REST/`invoke_skill` plumbing this pass — do not bind it into `run_agent_conversation`'s own LangGraph tool loop (that binding, for access-control purposes only, is `T06`'s narrower scope; general conversational "ask your agent to search the web" wiring stays out of scope per the parent story's own Non-Goals).

---

## Tests

<!-- AC-01/AC-02 verified here, the full grant/invoke-with-args and
refused-without-grant round trips, via the real skill_registry +
skills_router.py layer against a real running backend. -->

**Manual verification steps:**
1. **[REQ-SB-36-US-01-AC-01]** In a Python shell against the backend `.venv` (real Anthropic Provider configured). Grant a scratch test agent (e.g. `todo-capture`, reserving it as the untouched fixture per this project's own "reserve one fixture entity" Pattern) access: `skill_registry.grant_skill_access("todo-capture", "web-research")`. Call `skill_registry.invoke_skill("todo-capture", "web-research", {"query": "What is the current version of the Python programming language?"})`. Confirm the result is `{"found": True, "summary": <non-empty>, "sources": [...]}` — real, not fabricated. Repeat via a real HTTP call: `POST /agents/todo-capture/skills/web-research/invoke` with body `{"query": "..."}` — confirm the identical shape over HTTP.
2. **[REQ-SB-36-US-01-AC-02]** Confirm a *different* agent (e.g. `vault-qa`) has NOT been granted `"web-research"` access (`skill_registry.has_skill_access("vault-qa", "web-research")` is `False`, the real starting state). Call `skill_registry.invoke_skill("vault-qa", "web-research", {"query": "anything"})`. Confirm `{"status": "refused", ...}`. Repeat via real HTTP — confirm `403`, distinct from Scenario 4's honest-unavailable `200` response (verified in `T04`).
3. Clean-up: `skill_registry.revoke_skill_access("todo-capture", "web-research")` — restore the clean seed state, mirroring the untouched-fixture convention this project already uses.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a granted agent invoking `web-research` with a query gets real results, over both the direct function call and real HTTP — **re-verified live 2026-08-13 against a real, genuine `ANTHROPIC_API_KEY`; both halves now confirmed (dispatch AND a real, non-fabricated result with real sources); see this task's own Implementation Log.**
- [x] **AC-02** (Scenario 2) — an ungranted agent's invocation is refused (`403` over HTTP), distinct from the honest-unavailable case
- [x] `invoke_skill`'s `args` parameter is additive — `diagram-understanding`'s own zero-arg invocation still works unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The skill's own honest-empty/honest-unavailable logic — `T04`, already built.
- The conversational tool-binding access-control gap — `T06`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

---

## Implementation Log

Built exactly per spec for the `args`/router-body plumbing:
`skill_registry._SKILL_HANDLERS` gained `"web-research":
skill_tools.web_research`; `invoke_skill(agent_id, skill_id, args=None)`
threads `args` into `handler(**args)` when given, `handler()` otherwise —
`skills_router.py` gained `InvokeSkillBody`/an optional JSON body on the
invoke endpoint, exactly per the task's own literal sample.

**One additional, additive change beyond the task's own literal sample,
required by `T04`'s own mid-build correction (see that task's own
Implementation Log, `ADR-022`'s "Correction" addendum,
`ESCALATIONS.md` → `ESC-019`):** `invoke_skill` now also injects
`agent_id` into the call whenever the resolved handler's own signature
declares an `agent_id` parameter (`inspect.signature(handler).parameters`),
since `web_research` now needs to know which agent is invoking it to
resolve that agent's own linked Provider. This is additive and
backward-compatible by construction — `diagram-understanding`'s own
zero-arg signature has no `agent_id` parameter, so it is completely
unaffected; `skills_router.py`'s own request-body contract
(`InvokeSkillBody`) is UNCHANGED — a caller still only ever supplies
`{"query": "..."}"}`, never `agent_id` — `agent_id` comes exclusively
from `invoke_skill`'s own already-authenticated first parameter (the
router's own `{agent_id}` path segment), so a request body cannot spoof a
different agent's own Provider.

**AC-01/AC-02 verified live, end-to-end, over real HTTP against a freshly-
started backend instance** (port `8020` — this project's own documented
port `8001` was held by an unkillable "ghost" TCP listener this session's
tooling could not identify/clear, no admin rights available to force it;
recorded in `REVIEW-QUEUE.md`, does not affect this task's own REST-layer
verification, which never touches the MCP loopback):

- **AC-01** (Scenario 1): granted `todo-capture` access to `web-research`
  (`POST /agents/todo-capture/skills/web-research` → `{"granted": true}`).
  Confirmed its real default Provider is `"compass"`
  (`GET /agents/todo-capture` → `"provider_id":"compass"`). Invoked
  (`POST .../invoke {"query":"anything"}`) → `200 OK`, the honest
  not-available shape (correct — Compass has no real search, see `T04`).
  Reassigned to `"anthropic-claude"` (`PATCH /agents/todo-capture
  {"provider_id":"anthropic-claude"}`). Invoked again with a real query
  → the request genuinely dispatched to Anthropic's real API (confirmed
  both via the direct Python-level call, which raised a real
  `AnthropicResearchError` with a real `401 invalid x-api-key` from
  Anthropic's own server, and via the same call over real HTTP, which
  surfaced as a real `500 Internal Server Error` — the FastAPI-default
  unhandled-exception response, since neither `T04`'s own function nor
  `invoke_skill` wraps this specific call in a try/except; this is an
  honest failure, not a fabricated result, and is a genuine open follow-up
  worth a nicer error shape in a future pass, not a defect introduced by
  this task). The real dispatch attempt itself is direct, live proof the
  Provider-resolution routing is correct; the actual "real relevant
  result" half of AC-01 is blocked purely on the missing genuine
  credential (`T01`'s own Implementation Log; flagged in
  `REVIEW-QUEUE.md`), not on any code defect.
- **AC-02** (Scenario 2): confirmed `vault-qa` has NOT been granted
  `web-research` access (`GET /agents/vault-qa/skills` → `[]`). Invoked
  → `403 Forbidden`, `{"detail":"Agent does not have access to this
  skill."}` — correctly distinct from both the `200` honest-unavailable
  and the `500` blocked-real-call responses above.
- Confirmed `diagram-understanding`'s own zero-arg invocation still works
  unaffected: granted, invoked with no body → `200 OK`, the honest
  not-available shape (unchanged from before this task).
- Cleanup: `todo-capture` reverted to `"compass"`; both grants
  (`web-research`, `diagram-understanding`) revoked; `vault-qa` untouched
  throughout (never granted, matching this project's own "reserve one
  untouched fixture" Pattern) — confirmed via a final `GET
  /agents/todo-capture` (`provider_id: "compass"`) and `GET
  /agents/todo-capture/skills` (`[]`).

**Re-verification pass (2026-08-13, coder) — the `AC-01` "gets real
results" gap flagged in `REVIEW-QUEUE.md`'s `SPRINT-022` entry, closed.
No source code changed; re-verification only. Full detail (backend
restart, the stale-placeholder-credential root cause found and resolved
by re-seeding `.second-brain/agent_providers.json`, and the exact
real-result evidence) is recorded in `T04`'s own Implementation Log,
where the direct `skill_tools.web_research` behavior is analyzed —
summarized here at this task's own REST-layer:** `POST /agents/todo-
capture/skills/web-research/invoke {"query": "What is the current stable
version of the Python programming language?"}` (after granting access and
relinking `todo-capture` to `"anthropic-claude"`) returned `200 OK` with a
real, non-fabricated result (`"found": true`, real summary, real sources
— `python.org`, Wikipedia). This is the same real dispatch path this
task's own `invoke_skill`/router plumbing built and verified for
routing/refusal in `SPRINT-022`; this pass additionally confirms the
"produces a real result" half now that a genuine credential is
provisioned. Cleanup repeated identically: `todo-capture` reverted to
`"compass"`, `web-research` grant revoked, `vault-qa` confirmed untouched
(its own separate, `SPRINT-024`-documented permanent grant left exactly
as found).
