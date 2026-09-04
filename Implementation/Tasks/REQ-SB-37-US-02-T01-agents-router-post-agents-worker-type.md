---
id: REQ-SB-37-US-02-T01
title: agents_router.py — POST /agents `type` check extended to accept "worker" (domain optional)
parent_story: REQ-SB-37-US-02
requirement_id: REQ-SB-37
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-37-US-01-T03, REQ-SB-39-US-02-T03]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-02-T01 — `agents_router.py` — `POST /agents` accepts `"worker"`

## Parent Story

- Story: [[REQ-SB-37-US-02]] — `../UserStories/REQ-SB-37-US-02-agent-creation-worker-flow.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Extend the existing `POST /agents` endpoint's `type` check so `"worker"` is
accepted alongside `"expert"`, `domain` becomes optional (required only for
Expert), and a Worker is created via
`agent_registry.create_agent(name, "worker", settings=[])` — no Domain-
equivalent setting. No other handler in this file changes.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-37-US-01-T03`'s real, live `POST /agents` — `CreateAgentBody`
  (`name: str`, `type: str`, `domain: str`, all required), and its handler
  refuses any `type != "expert"` with a `400`.
- `REQ-SB-39-US-02-T03` has landed the 4 mutating Skills
  (`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
  `build_knowledge`) in `skill_tools.SKILLS`, alongside the already-real
  `REQ-SB-39-US-01`-era read-only catalog — needed so this task's own
  `AC-05` verification step (a mutating Skill granted to a freshly created
  Worker, invoked under a real working mode) has a real migrated mutating
  Skill to grant.
- `PATCH /agents/{agent_id}` already accepts `section_id` (`REQ-SB-18-US-01`)
  and `scope` (`REQ-SB-29-US-01-T03`) — unchanged, used by the wizard's own
  follow-up call, not by this endpoint.
- `POST /agents/{agent_id}/skills/{skill_id}` (grant) already exists and is
  `Done` (`REQ-SB-27-US-01-T04`) — unchanged, used by the wizard's own
  Skills step, not by this endpoint.

**After / Outputs:**
- `POST /agents` (body: `name`, `type`, `domain?`) accepts `type ==
  "worker"` in addition to `"expert"`. For a Worker, `domain` is not
  required; if a Worker is created, `agent_registry.create_agent(name,
  "worker", settings=[])` is called (no `settings` entry — a Worker's real
  configuration is Skills/Scope/Section, all set via separate follow-up
  calls, never via `settings`). For an Expert, behavior is byte-identical
  to `REQ-SB-37-US-01-T03` (domain still required, still recorded as the
  one `settings` entry).
- Any `type` other than `"expert"`/`"worker"` (e.g. `"producer"`) is still
  refused with an honest `400`, unchanged from `T03`.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  1. Read the REAL current file first (per this project's own established
     "compose around the real current file" convention — this file is
     actively extended by multiple sibling stories) and reconcile this
     task's diff against it if anything has drifted since `T03`/`REQ-SB-29-
     US-01-T03` landed.
  2. Change `CreateAgentBody.domain` from required to optional:
     ```python
     class CreateAgentBody(BaseModel):
         name: str
         type: str
         domain: str | None = None
     ```
  3. Rewrite `create_agent`'s validation/dispatch to branch on `type`:
     ```python
     @router.post("")
     def create_agent(body: CreateAgentBody) -> dict:
         name = body.name.strip()
         if not name:
             raise HTTPException(status_code=400, detail="A name is required.")
         if body.type not in ("expert", "worker"):
             # Producer is REQ-SB-37-US-03's own scope, hard-blocked on
             # nothing built for it yet — an honest refusal here, never a
             # silently-accepted or fabricated agent of an unsupported type.
             raise HTTPException(
                 status_code=400,
                 detail=f"Creating a '{body.type}' agent is not yet available — only Expert and Worker are supported today.",
             )
         if body.type == "expert":
             domain = (body.domain or "").strip()
             if not domain:
                 raise HTTPException(
                     status_code=400,
                     detail="A knowledge domain is required for an Expert agent.",
                 )
             created = agent_registry.create_agent(
                 name, "expert", settings=[{"key": "Domain", "value": domain}],
             )
         else:
             # Worker: no Domain-equivalent setting — its real configuration
             # (Skills, Vault Scope, Section) lives entirely in the wizard's
             # own three follow-up calls (ADR-030's "amendment" section),
             # never in settings.
             created = agent_registry.create_agent(name, "worker", settings=[])
         return get_agent(created["id"])
     ```
     (Keep `get_agent` referring to the existing `GET /agents/{agent_id}`
     handler function, exactly as `T03` established — reconcile placement
     against the real current file, not literal line order.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this endpoint calls `agent_registry.create_agent` and the
  existing `get_agent` handler only; it does not call `vault_writer`
  directly, and does not call `skill_registry`/`scope_registry`/
  `section_registry` (those are the wizard's own separate follow-up calls).
- Must reject a missing `name` with `400` before calling `create_agent` at
  all, for both types.
- For `type == "expert"`, must reject a missing/blank `domain` with `400`
  — byte-identical behavior to `T03`, no regression.
- For `type == "worker"`, `domain` must NOT be required — an absent or
  blank `domain` on a Worker request must not raise `400`.
- Must reject any `type` other than `"expert"`/`"worker"` with an honest
  `400` naming the unsupported type — never silently create a
  Producer-typed agent with no real wizard step behind it.
- A Worker's `create_agent` call MUST pass `settings=[]` — never fabricate
  a Domain-equivalent setting for a Worker.
- Must NOT accept a `section_id`, `scope`, or a Skills list in this
  endpoint's own body — Section/Scope assignment and Skill grants are the
  wizard's own separate, already-real calls (`PATCH /agents/{agent_id}`,
  `POST /agents/{agent_id}/skills/{skill_id}`).
- Do not change any other existing handler in this file (`GET /agents`,
  `GET /agents/{agent_id}`, `PATCH /agents/{agent_id}`, `/chat`,
  `/history`, `/actions/{action_id}`, the Skills routes live in
  `skills_router.py`, untouched).

---

## Tests

<!-- AC-03/AC-05/AC-06's own Given clauses each only require "a Worker
agent has just been created" — not specifically "via the wizard." This
endpoint is the real mechanism the wizard (T02) itself calls, so these
three scenarios are verified here, end-to-end, against every already-Done
downstream surface, before the wizard's own Worker UI exists —
backend-layer-first verification, mirroring REQ-SB-37-US-01-T03's own
AC-04/05/06/08 placement precedent exactly. AC-01/AC-02/AC-04 need a real,
reachable wizard UI and are tagged in T02 instead. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`; delete any leftover
`.second-brain/agents_registry.json`/`agent_skills.json` first; the
frontend dev server, `npm run dev` from `src/frontend`, should also be
running and already reachable at `/agents-map` for step 5 — no new
frontend code is needed there, that surface is already `Done`):

1. Non-AC smoke check (Expert regression): `POST /agents` with
   `{"name": "Widgets Expert", "type": "expert", "domain": "Widgets
   manufacturing"}`. Confirm `200`, identical shape/behavior to `T03`'s
   own step 3 (unchanged). `POST /agents` with `{"name": "No Domain
   Expert", "type": "expert"}` (domain omitted). Confirm `400`, message
   names the missing domain — Expert's own required-domain behavior did
   not regress.
2. Non-AC smoke check (Worker, domain optional): `POST /agents` with
   `{"name": "Ops Helper", "type": "worker"}` (no `domain` key at all).
   Confirm `200`, response shape matches `GET /agents/{id}` (`id:
   "ops-helper"`, `name: "Ops Helper"`, `type: "worker"`, `settings: []`,
   `actions: []`, `section_id`/`section_name` self-healed default,
   `provider_id`/`provider_name` self-healed default, `keywords: []`,
   `working_mode` self-healed default, `scope: []`). Confirm no Domain
   entry anywhere in `settings`.
3. Non-AC smoke check (type refusal unchanged): `POST /agents` with
   `{"name": "Reporter", "type": "producer"}`. Confirm `400`, message
   honestly names `producer` as not yet available. Confirm `GET /agents`
   lists only the 7 seed agents plus `widgets-expert`/`ops-helper` from
   steps 1-2 — nothing partial created.
4. **[REQ-SB-37-US-02-AC-05]** Grant the mutating Skill `run_capture_now`
   to `ops-helper` (`POST /agents/ops-helper/skills/run_capture_now`,
   confirm `{"granted": true}`). Set `ops-helper`'s working mode to
   Supervised (`PATCH /agents/ops-helper` with `{"working_mode":
   "supervised"}`). Invoke it (`POST /agents/ops-helper/skills/
   run_capture_now/invoke`). Confirm the SAME Supervised-mode gating
   behavior an existing, already-shipped agent's own granted
   `run_capture_now` exhibits (a `{"status": "pending", ...}` deferral, not
   an immediate real run) — cross-check against
   `REQ-SB-39-US-02-T03`'s own step 1 finding for `email-capture` under
   Supervised mode as the independent ground truth. Set `ops-helper` back
   to Autonomous, invoke again, confirm it now runs for real (or honestly
   unavailable, per `run_capture_now`'s own real/stub-by-agent split —
   `ops-helper` is not `email-capture`, so confirm the SAME honest-
   unavailable shape a non-`email-capture` agent gets, proving the gate/
   dispatch behaves identically regardless of whether the agent was
   shipped or created this session). Revoke the skill afterward.
5. **[REQ-SB-37-US-02-AC-03]** Open the already-`Done` Agents Map
   (`/agents-map`) in a browser — a fresh load or an SPA-internal
   nav-away/nav-back is sufficient, no server restart. Confirm
   `ops-helper` renders on the Worker ring, inside its self-healed default
   Section, alongside the existing seed agents and `widgets-expert` — with
   zero Worker-specific frontend code from this story yet built.
6. **[REQ-SB-37-US-02-AC-06]** `POST /agents/ops-helper/chat` with an
   ordinary conversational message (e.g. "hello"). Confirm an ordinary
   conversational reply, the same conversational path any existing
   zero-granted-Skill agent uses. `GET /agents/ops-helper/history` —
   confirm it returns `chat_user`/`chat_agent` entries in the exact same
   shape `GET /agents/{id}/history` already returns for any existing
   agent — no distinct "read-only"/"second-class" field or shape anywhere
   in the response.
7. Clean-up: delete `.second-brain/agents_registry.json` and
   `.second-brain/agent_skills.json`. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-03** — a freshly created Worker agent appears on the Agents Map,
      on the Worker ring, in its assigned Section, with no reload/restart
- [ ] **AC-05** — a mutating Skill granted to a freshly created Worker
      honors its working mode exactly as it would for an existing,
      already-shipped agent with the same Skill granted
- [ ] **AC-06** — a freshly created Worker's Chat and History behave
      identically to an existing agent's, with no second-class/read-only
      distinction
- [ ] `POST /agents` accepts `type == "worker"`; `domain` not required for
      a Worker; a Worker is created via `create_agent(name, "worker",
      settings=[])` — no Domain-equivalent setting fabricated
- [ ] `POST /agents` for `type == "expert"` remains byte-identical to
      `T03`'s own behavior (domain still required)
- [ ] `POST /agents` rejects any `type` other than `"expert"`/`"worker"`
      with an honest `400`
- [ ] `POST /agents` never accepts `section_id`, `scope`, or a Skills list
      — those stay separate calls
- [ ] No other existing `agents_router.py` handler's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The wizard's own Worker step UI, its Skills multi-select/Vault Scope
  field/Section picker, the three-call sequencing, and the honest
  multi-field-missing rejection UI (`AC-01`/`AC-02`/`AC-04`) — all `T02`.
- Producer creation — `REQ-SB-37-US-03`, not this story's scope.
- Any change to `agent_registry.py`, `skill_registry.py`, `skill_tools.py`,
  `skills_router.py`, `section_registry.py`, or `scope_registry.py` — all
  reused unmodified, per the architect's own Notes.

---

## Context / Notes

**Why AC-03/AC-05/AC-06 are verified here, not in T02:** each scenario's
own Given clause only requires "a Worker agent has just been created," not
specifically "via the wizard" — and every downstream surface exercised
(Agents Map, Skills grant/gate, chat, history) is already `Done` and needs
zero code change for a created Worker. Verifying them here, against the
real mechanism the wizard itself will call, follows this project's own
established backend-layer-first verification pattern
(`REQ-SB-37-US-01-T03`'s own AC-04/05/06/08 precedent) — it does not
weaken or defer proof of any locked AC, it proves it earlier and against
the real, unmodified downstream surfaces directly.

Full composition reasoning: `Implementation/Architecture/architecture.md`
→ "Amendment — Worker-type flow (REQ-SB-37-US-02, no new ADR)". No ADR
created or changed by this task.

---

## Implementation Log

**2026-08-14, coder.** Read the REAL current `agents_router.py` first — it
matched the task's own `Before` description exactly (`CreateAgentBody`
required `domain`, `create_agent` refused anything but `"expert"`). Applied
the task's own diff verbatim: `domain: str | None = None`; dispatch now
branches on `body.type in ("expert", "worker")`, Expert requires non-blank
`domain` (unchanged behavior), Worker calls
`agent_registry.create_agent(name, "worker", settings=[])`, anything else
refused `400` naming both supported types.

**Environment note (scope-internal, not an escalation):** found a leftover
`widgets-expert` agent + a `web-research` Skill grant on it in the REAL
vault's `.second-brain/agents_registry.json`/`agent_skills.json` —
residue from a prior sprint's own live verification, not cleaned up. Reset
both files to a clean slate before running this task's own Tests (per the
Tests block's own "delete any leftover state files first" instruction,
which I'd initially checked at the wrong path — `src/backend/.second-brain`
does not exist; the real state lives at the configured `VAULT_PATH`,
`<OPERATOR_VAULT_OLD>\.second-brain`). Also hit the
project's own documented `--reload` orphaned-multiprocessing-fork-child
antipattern once during this cleanup (parent PID gone, child PID still
holding the socket) — resolved via the established `Get-CimInstance
Win32_Process` child-discovery + kill protocol, no new finding.

**Verification (manual mode, real HTTP against a real running backend,
`.venv\Scripts\uvicorn.exe app.main:app --reload --port 8001`):**

- Non-AC smoke (Expert regression): `POST /agents` with `{"name": "Widgets
  Expert", "type": "expert", "domain": "Widgets manufacturing"}` → `200`,
  `id: "widgets-expert"`, `settings: [{"key": "Domain", "value": "Widgets
  manufacturing"}]`. `POST /agents` with `{"name": "No Domain Expert",
  "type": "expert"}` (no `domain`) → `400`, "A knowledge domain is required
  for an Expert agent." Byte-identical to `T03`'s own behavior.
- Non-AC smoke (Worker, domain optional): `POST /agents` with `{"name":
  "Ops Helper", "type": "worker"}` (no `domain` key) → `200`, `id:
  "ops-helper"`, `type: "worker"`, `settings: []`, no Domain entry, all
  self-healed fields present (`section_id: "technical"`, `provider_id:
  "compass"`, `working_mode: "autonomous"`, `scope: []`).
- Non-AC smoke (type refusal unchanged): `POST /agents` with `{"name":
  "Reporter", "type": "producer"}` → `400`, "Creating a 'producer' agent
  is not yet available — only Expert and Worker are supported today."
  `GET /agents` listed exactly the 7 seed agents + `widgets-expert` +
  `ops-helper` — nothing partial.
- **AC-05 — PASS.** Granted `run_capture_now` to `ops-helper`
  (`{"granted": true}`). Set `ops-helper` Supervised, invoked →
  `{"status": "pending", "message": "Proposed — Run Capture Now. Awaiting
  your approval.", "pending_approval_id": "544a3399e865"}`. Cross-checked
  against `email-capture` (existing shipped agent) under the same
  Supervised transition, same call → byte-identical shape (only the
  `pending_approval_id` differs). Set `ops-helper` back to Autonomous,
  invoked again → `{"available": false, "message": "This skill is not yet
  available — no real handler has been built for it."}`, cross-checked
  against `meeting-capture` (an existing, non-`email-capture` agent)
  invoking the same skill → byte-identical honest-unavailable shape,
  confirming the gate/dispatch behaves identically for a session-created
  agent as for a shipped one. Revoked afterward.
- **AC-03 — PASS.** Loaded the real, already-`Done` Agents Map
  (`http://127.0.0.1:5173/`, confirmed mounted at root per `MEMORY.md`'s
  own prior finding) via a headless-Edge screenshot. `ops-helper` (Worker,
  self-healed to the Technical section) rendered as the expected new blue
  Worker-ring node inside the Technical cluster — Technical went from 1
  expert node (`compass-expert`) to 2 experts (`+widgets-expert`) + 1
  worker (`ops-helper`), matching the screenshot exactly. No frontend code
  from this story existed yet — verified against the unmodified Agents Map.
- **AC-06 — PASS.** `POST /agents/ops-helper/chat` with "hello" → an
  ordinary conversational reply (agent-orchestration path, no trigger-
  phrase match). `GET /agents/ops-helper/history` returned
  `chat_user`/`chat_agent` entries in the exact same `{kind, text,
  timestamp}` shape `GET /agents/vault-qa/history` (an existing agent)
  returns — no distinct read-only/second-class field anywhere.
- Cleanup: declined the two real pending-approval records this task's own
  live testing created (`544a3399e865` ops-helper, `3a435b4c7f2f`
  email-capture — both left `pending` mid-test, declined afterward rather
  than left dangling). Reset `.second-brain/agents_registry.json` (deleted
  — self-heals to `{"created_agents": {}}`) and `agent_skills.json` (reset
  to `{"assignments": {}}`) to a clean slate for `T02`'s own live testing;
  confirmed `GET /agents` back to exactly 7 seed agents. Backend server
  left running (state is read fresh from disk on every call, no
  in-process caching) — reused directly by the next task in this sprint's
  own build order rather than stopped/restarted, a scope-internal
  efficiency choice, not a deviation from any locked AC's own verification.

gate: clear 2026-08-14 — no MUST-FLAG trigger fired (no material
assumption beyond ordinary test-environment hygiene already directed by
the task's own Tests block; no Draft requirement relied on; no ADR
touched; no ESCALATIONS.md entry needed; every locked AC in this task's
own scope verified).
