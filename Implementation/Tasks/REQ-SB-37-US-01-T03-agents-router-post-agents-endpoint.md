---
id: REQ-SB-37-US-01-T03
title: agents_router.py — new POST /agents endpoint (Expert type only this pass)
parent_story: REQ-SB-37-US-01
requirement_id: REQ-SB-37
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-37-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-01-T03 — agents_router.py — new POST /agents endpoint

## Parent Story

- Story: [[REQ-SB-37-US-01]] — `../UserStories/REQ-SB-37-US-01-agent-creation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Add `POST /agents` to `app/api/agents_router.py`, calling `T02`'s
`agent_registry.create_agent(...)` and returning the same shape
`GET /agents/{agent_id}` already returns. This is the real, first-time
"create an agent, no source-code change" HTTP entry point — the mechanism
the wizard (`T04`) itself calls — and the point at which every already-
`Done`, zero-code-change downstream surface (`AgentsMapCanvas.tsx`,
`AgentDetailPanel.tsx`, `/chat`, `/history`) can be proven to work for a
created agent for the first time.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `agent_registry.create_agent(name, type, settings=None)`.
- `agents_router.py`'s existing `GET /agents/{agent_id}` handler (see the
  real current file) already composes `section_registry`/
  `provider_registry`/`agent_keywords`/`working_mode_registry` into one
  response shape — this task's own `POST /agents` reuses that exact
  function, does not duplicate its shape.
- `agents_router.py`'s existing `PATCH /agents/{agent_id}`
  (`update_agent_assignment`) already accepts `section_id` — unchanged,
  used by the wizard's own follow-up call (`ADR-030` point 6), not by this
  endpoint itself.

**After / Outputs:**
- `POST /agents` (body: `name`, `type`, `domain`) creates a new agent and
  returns the `GET /agents/{agent_id}` shape. Only `type == "expert"` is
  accepted this pass (Worker/Producer are `REQ-SB-37-US-02`/`US-03`'s own
  scope, hard-blocked on `REQ-SB-39`) — any other `type` value is refused
  with an honest 400, never silently accepted or fabricated.
- `agent_registry.py` stays ignorant of Sections (`ADR-014`) — this
  endpoint does not accept a `section_id`; Section assignment is the
  wizard's own second, immediate `PATCH /agents/{agent_id}` call.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  1. Add a new request body model, alongside the existing
     `ChatMessageBody`/`AgentAssignmentUpdateBody`:
     ```python
     class CreateAgentBody(BaseModel):
         name: str
         type: str
         domain: str
     ```
  2. Add the new endpoint, placed alongside the existing `@router.get("")`
     `list_agents` handler:
     ```python
     @router.post("")
     def create_agent(body: CreateAgentBody) -> dict:
         name = body.name.strip()
         domain = body.domain.strip()
         if not name or not domain:
             raise HTTPException(
                 status_code=400,
                 detail="Both a name and a knowledge domain are required.",
             )
         if body.type != "expert":
             # Worker/Producer are REQ-SB-37-US-02/US-03's own scope,
             # hard-blocked on REQ-SB-39 — an honest refusal here, never a
             # silently-accepted or fabricated agent of an unsupported type.
             raise HTTPException(
                 status_code=400,
                 detail=f"Creating a '{body.type}' agent is not yet available — only Expert is supported today.",
             )
         created = agent_registry.create_agent(
             name, body.type, settings=[{"key": "Domain", "value": domain}],
         )
         return get_agent(created["id"])
     ```
     (`get_agent` here is the existing `GET /agents/{agent_id}` handler
     function already defined lower in this same file — Python's
     module-level ordering means this new `create_agent` function must be
     placed so `get_agent` is already defined by the time it's called, or
     called by its fully-qualified reference; reconcile placement against
     the real current file rather than assuming today's literal line
     order.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this endpoint calls `agent_registry.create_agent` and the
  existing `get_agent` handler only; it does not call `vault_writer`
  directly.
- Must reject a missing `name` or `domain` with `400`, naming what's
  missing, before calling `agent_registry.create_agent` at all — never
  create a partial/broken agent record.
- Must reject any `type` other than `"expert"` with a `400` that honestly
  names the type as not yet available — never silently create a
  Worker/Producer-typed agent with no real wizard step behind it.
- Must NOT accept a `section_id` in this endpoint's own body —
  `agent_registry.py` stays ignorant of Sections (`ADR-014`); Section
  assignment is a separate, already-`Done` `PATCH /agents/{agent_id}` call.
- Do not change any other existing handler in this file (`GET /agents`,
  `GET /agents/{agent_id}`, `PATCH /agents/{agent_id}`, `/chat`,
  `/history`, `/actions/{action_id}`).

---

## Tests

<!-- AC-04/AC-05/AC-06/AC-08's own Given clauses each only require "an
Expert agent has just been created" — not specifically "via the wizard."
This endpoint is the real mechanism the wizard (T04) itself calls, so
these four scenarios are verified here, end-to-end, against every
already-Done downstream surface, before the wizard's own UI exists —
backend-layer-first verification, this project's own established
pattern. AC-01/AC-02/AC-03/AC-07 need a real, reachable wizard UI and are
tagged in T04 instead. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`; delete any leftover
`.second-brain/agents_registry.json` first; the frontend dev server, `npm
run dev` from `src/frontend`, should also be running and already reachable
at `/agents-map` — no new frontend code is needed for steps 6/8/9 below,
those surfaces are already `Done`):

1. Non-AC smoke check (validation): `POST /agents` with `{"name": "",
   "type": "expert", "domain": "Widgets"}`. Confirm `400`, message names
   the missing name. `POST /agents` with `{"name": "Widgets Expert",
   "type": "expert", "domain": ""}`. Confirm `400`, message names the
   missing domain.
2. Non-AC smoke check (type refusal): `POST /agents` with `{"name": "Ops
   Helper", "type": "worker", "domain": "n/a"}`. Confirm `400`, message
   honestly states Worker creation is not yet available. Confirm
   `GET /agents` still lists exactly the 7 seed agents afterward — nothing
   partial was created.
3. Non-AC smoke check (real creation): `POST /agents` with `{"name":
   "Widgets Expert", "type": "expert", "domain": "Widgets manufacturing"}`.
   Confirm `200`, response shape matches `GET /agents/{id}` exactly
   (`id: "widgets-expert"`, `name`, `type: "expert"`, `settings` includes
   `{"key": "Domain", "value": "Widgets manufacturing"}`, `actions: []`,
   `section_id`/`section_name` populated with the self-healed default
   Section, `provider_id`/`provider_name` populated with the self-healed
   default Provider, `keywords: []`, `working_mode` the self-healed
   default). Confirm `GET /agents` now includes it, after the 7 seed
   agents.
4. Non-AC smoke check (collision): `POST /agents` again with the same
   `{"name": "Widgets Expert", ...}`. Confirm `200`, `id ==
   "widgets-expert-2"` — a genuinely distinct agent, not the same one
   returned again.
5. Assign a Section (mirrors the wizard's own follow-up call, `ADR-030`
   point 6): `PATCH /agents/widgets-expert` with `{"section_id":
   "technical"}` (or any real seed section id from `GET /sections`).
   Confirm `200`, `section_id`/`section_name` now reflect it.
6. **[REQ-SB-37-US-01-AC-05]** Open the already-`Done` Agents Map
   (`/agents-map`) in a browser — a fresh load or an SPA-internal
   nav-away/nav-back is sufficient, no server restart. Confirm
   `widgets-expert` renders on the Expert ring, inside the Section
   assigned in step 5, alongside the existing seed agents — with zero
   frontend code from this story yet built.
7. **[REQ-SB-37-US-01-AC-04]** `POST /agents/widgets-expert/chat` with
   `{"message": "What is our current return policy for widgets?"}` (a
   question squarely within its stated domain, before any real content
   exists in its scope). Confirm the reply honestly states it doesn't
   know / has no grounded information to answer from — never a fabricated,
   confident-sounding answer.
8. **[REQ-SB-37-US-01-AC-06]** `PATCH /agents/widgets-expert` with
   `{"provider_id": "compass", "working_mode": "supervised"}`. Confirm
   `200`, `provider_id`/`provider_name`/`working_mode` all reflect the
   change. `POST /agents/widgets-expert/skills/web-research` (the existing
   skill-grant endpoint, `REQ-SB-27`). Confirm `{"granted": true}`.
   `GET /agents/widgets-expert` — confirm `provider_id`/`working_mode`
   still reflect the change; `GET /agents/widgets-expert/skills` — confirm
   `web-research` is present. All via the exact same endpoints an existing
   built-in agent's own Settings surface already uses — no new/parallel
   configuration mechanism.
9. **[REQ-SB-37-US-01-AC-08]** `POST /agents/widgets-expert/chat` with a
   second, unrelated message (e.g. "hello"). Confirm an ordinary
   conversational reply, the same conversational path any existing
   zero-action agent uses. `GET /agents/widgets-expert/history` — confirm
   it returns `chat_user`/`chat_agent` entries for both messages sent so
   far, in the exact same shape `GET /agents/{id}/history` already returns
   for any existing agent — no distinct "read-only"/"second-class" field
   or shape anywhere in the response.
10. Clean-up: delete `.second-brain/agents_registry.json` (no
    `delete_agent` exists this pass — resetting the file is the only way
    to clear `widgets-expert`/`widgets-expert-2` before `T04`'s own
    verification). Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-04** — a freshly created Expert agent, asked a question within
      its stated (empty) domain, honestly answers that it doesn't know —
      no fabrication
- [x] **AC-05** — the created agent appears on the Agents Map, in its
      assigned Section on the Expert ring, with no reload/restart
- [x] **AC-06** — Provider, Working mode, and Skill grants can be set on
      the created agent via the exact same endpoints an existing agent
      uses, and are reflected immediately
- [x] **AC-08** — the created agent's Chat and History behave identically
      to an existing agent's, with no second-class/read-only distinction
- [x] `POST /agents` rejects a missing `name`/`domain` with `400`, naming
      what's missing, before calling `create_agent`
- [x] `POST /agents` rejects any `type != "expert"` with an honest `400`
- [x] `POST /agents` never accepts a `section_id` — Section assignment
      stays a separate `PATCH` call
- [x] No other existing `agents_router.py` handler's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The wizard UI itself, the "no source-code change to REACH it" entry
  point, the type-selector's field-set switching, and the honest-rejection
  UI for a missing field (`AC-01`/`AC-02`/`AC-03`/`AC-07`) — all `T04`.
- Worker/Producer creation — `REQ-SB-37-US-02`/`US-03`, hard-blocked on
  `REQ-SB-39`.
- Any `delete_agent`/rename mechanism — not built by `ADR-030` or this
  story (additive-only, per the parent story's own Non-Goals).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-030` created at
`/plan-tasks` step 1) — the human reviews `ADR-030` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

**Why AC-04/05/06/08 are verified here, not in T04:** each scenario's own
Given clause only requires "an Expert agent has just been created," not
specifically "via the wizard" — and every downstream surface exercised
(Agents Map, chat, history, Provider/working-mode/skill configuration) is
already `Done` and needs zero code change for a created agent (`ADR-030`
Consequences). Verifying them here, against the real mechanism the wizard
itself will call, follows this project's own established
backend-layer-first verification pattern (e.g. `REQ-SB-27-US-01-T04`) —
it does not weaken or defer proof of any locked AC, it proves it earlier
and against the real, unmodified downstream surfaces directly.

---

## Implementation Log

**Coder pass, 2026-08-14.** Read the real current `agents_router.py`
before editing — it has drifted materially beyond the task's own sample
since it was written (`SPRINT-030`/`031` Skills unification landed
`_invoke_capability`, `skill_tools`, richer `get_agent`/`list_agents`
responses with `capabilities`/`provider_available`/`scope`; `SPRINT-032`
added `scope` to `AgentAssignmentUpdateBody`). Composed the new
`CreateAgentBody` model and `POST /agents` `create_agent` handler exactly
per the task's own code sample, placed after the existing `list_agents`
(`GET ""`) handler and before `get_agent` (`GET /{agent_id}`) — `get_agent`
is resolved at call time (Python module-level name lookup), not def time,
so this placement is safe regardless of physical ordering. No other
existing handler touched.

Backend started (`--reload --port 8001`) and reachable within seconds
(`BUG-008` fix confirmed still holding). Frontend dev server was already
running (confirmed real, serving this project's own `src/main.tsx`, not a
stray process) on port 5173 — reused, not restarted.

- Step 1 (validation): `{"name":"","type":"expert","domain":"Widgets"}` →
  `400`, "Both a name and a knowledge domain are required."; same for
  empty `domain`. Confirmed.
- Step 2 (type refusal): `{"name":"Ops Helper","type":"worker",...}` →
  `400`, "Creating a 'worker' agent is not yet available — only Expert is
  supported today."; `GET /agents` afterward still exactly the 7 seed
  agents — nothing partial created. Confirmed.
- Step 3 (real creation): `{"name":"Widgets Expert","type":"expert",
  "domain":"Widgets manufacturing"}` → `200`, `id: "widgets-expert"`,
  matches `GET /agents/{id}` shape exactly (self-healed `section_id:
  "technical"`, `provider_id: "compass"`, `working_mode: "autonomous"`,
  `keywords: []`, `capabilities: []`). Confirmed.
- Step 4 (collision): same body again → `200`, `id: "widgets-expert-2"`, a
  genuinely distinct agent. Confirmed.
- Step 5 (Section assignment): `PATCH /agents/widgets-expert
  {"section_id":"technical"}` → `200`, reflected. Confirmed.
- **AC-05** (step 6): headless-Edge screenshot + DOM dump of the Agents
  Map — **the real mount path is `/` (root), not `/agents-map` as the
  task's own informal step text names; `App.tsx`'s own route table
  confirms `<Route path="/" element={<AgentsMapPage />} />`, no
  `/agents-map` route exists** (scope-internal correction, not an
  escalation — verification-method detail only, no locked AC's own
  wording names a literal URL). Confirmed via real rendered DOM:
  `data-agent-id="widgets-expert"` and `data-agent-id="widgets-expert-2"`
  both present, class `agent-node agent-node--expert`, positioned in the
  Technical Section's cluster — no server restart, no frontend code
  change, a fresh page load of the already-running SPA. **PASS.**
- **AC-04** (step 7): `POST /agents/widgets-expert/chat
  {"message":"What is our current return policy for widgets?"}` → real
  Compass round-trip, honest reply: "I don't have access to the vault
  content to answer that yet... has no assigned vault scope... No policy
  text has come back yet" — explicitly declines rather than fabricating a
  policy. **PASS.**
- **AC-06** (step 8): `PATCH /agents/widgets-expert
  {"provider_id":"compass","working_mode":"supervised"}` → `200`, both
  reflected; `POST /agents/widgets-expert/skills/web-research` →
  `{"granted": true}`; `GET /agents/widgets-expert` → `working_mode:
  "supervised"` confirmed, `capabilities` now includes `web-research`;
  `GET /agents/widgets-expert/skills` → `web-research` present. Exact same
  endpoints an existing agent's Settings surface uses. **PASS.**
- **AC-08** (step 9): `POST /agents/widgets-expert/chat {"message":
  "hello"}` → ordinary conversational reply (not the honest-decline path —
  correctly distinct from the domain-specific question above).
  `GET /agents/widgets-expert/history` → 4 entries
  (`chat_user`/`chat_agent` × 2), `{"kind","text","timestamp"}` shape —
  compared directly against `GET /agents/vault-qa/history` (an existing
  agent), byte-identical shape, no second-class/read-only field anywhere.
  **PASS.**
- Step 10: deleted `.second-brain/agents_registry.json` (cleaned for
  `T04`'s own verification). Backend/frontend dev servers left running —
  `T04` (this same sprint's next task) needs both.

`GET`/`PATCH /agents...`, `/chat`, `/history`, `/actions/{action_id}` —
confirmed unchanged behavior throughout (all pre-existing steps that
exercised them behaved exactly as documented elsewhere in this project).

gate: clear 2026-08-14 — no MUST-FLAG trigger fired. The `/agents-map` vs.
`/` URL discrepancy is a scope-internal verification-method correction
(logged above for human spot-check), not an escalation — no locked AC's
own wording names a specific URL, and the real mounted route was used.

**Status: Done.**
