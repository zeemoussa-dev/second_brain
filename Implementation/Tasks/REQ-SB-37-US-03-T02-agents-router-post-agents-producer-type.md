---
id: REQ-SB-37-US-03-T02
title: agents_router.py — POST /agents `type` check extended to accept "producer" (Purpose via settings, required)
parent_story: REQ-SB-37-US-03
requirement_id: REQ-SB-37
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-031 created at /plan-tasks step 1) — carried forward, does not halt"
phase: P1
depends_on: [REQ-SB-37-US-02-T01, REQ-SB-37-US-03-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-03-T02 — `agents_router.py` — `POST /agents` accepts `"producer"`

## Parent Story

- Story: [[REQ-SB-37-US-03]] — `../UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Extend the existing `POST /agents` endpoint's `type` dispatch so
`"producer"` is accepted alongside `"expert"`/`"worker"`, requiring a
non-blank `purpose` field, stored via `agent_registry.create_agent(name,
"producer", settings=[{"key": "Purpose", "value": purpose}])` — the same
generic `settings` kv-list mechanism Expert's Domain already uses
(`ADR-031` point 3). No other handler in this file changes.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-37-US-02-T01`'s real, live `POST /agents` — `CreateAgentBody`
  (`name: str`, `type: str`, `domain: str | None`), dispatch accepting
  `type in ("expert", "worker")`, refusing anything else with `400`.
- `REQ-SB-37-US-03-T01` has landed `write-to-vault-draft` in
  `skill_tools.SKILLS` — needed so this task's own `AC-02` verification
  step (granting the output Skill to a freshly created Producer) has a
  real, selectable Skill to grant.
- `PATCH /agents/{agent_id}` already accepts `section_id` (`REQ-SB-18-US-01`)
  — unchanged, used by the wizard's own follow-up call, not by this
  endpoint.
- `POST /agents/{agent_id}/skills/{skill_id}` (grant) already exists and is
  `Done` (`REQ-SB-27-US-01-T04`) — unchanged, used by the wizard's own
  output-Skill step, not by this endpoint.

**After / Outputs:**
- `POST /agents` (body: `name`, `type`, `domain?`, `purpose?`) accepts
  `type == "producer"` in addition to `"expert"`/`"worker"`. For a
  Producer, `purpose` is required and non-blank; if a Producer is created,
  `agent_registry.create_agent(name, "producer", settings=[{"key":
  "Purpose", "value": purpose}])` is called. For Expert/Worker, behavior
  is byte-identical to `REQ-SB-37-US-02-T01`.
- Any `type` other than `"expert"`/`"worker"`/`"producer"` is still refused
  with an honest `400`, naming all three supported types.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  1. Read the REAL current file first (per this project's own established
     "compose around the real current file" convention — this file is
     actively extended by multiple sibling stories) and reconcile this
     task's diff against it if anything has drifted since
     `REQ-SB-37-US-02-T01` landed.
  2. Add `purpose` to `CreateAgentBody`:
     ```python
     class CreateAgentBody(BaseModel):
         name: str
         type: str
         domain: str | None = None
         purpose: str | None = None
     ```
  3. Extend `create_agent`'s validation/dispatch with a third branch:
     ```python
     @router.post("")
     def create_agent(body: CreateAgentBody) -> dict:
         name = body.name.strip()
         if not name:
             raise HTTPException(status_code=400, detail="A name is required.")
         if body.type not in ("expert", "worker", "producer"):
             raise HTTPException(
                 status_code=400,
                 detail=f"Creating a '{body.type}' agent is not yet available — only Expert, Worker, and Producer are supported today.",
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
         elif body.type == "worker":
             # No Domain-equivalent setting — a Worker's real configuration
             # (Skills, Vault Scope, Section) lives entirely in the
             # wizard's own three follow-up calls, never in settings.
             created = agent_registry.create_agent(name, "worker", settings=[])
         else:
             # Producer: Purpose is stored via the same generic settings
             # kv-list Expert's Domain already uses (ADR-031 point 3), not
             # a new field and not Worker's empty-settings pattern. The
             # output Skill and Section are the wizard's own separate
             # follow-up calls (grant + PATCH), never this endpoint's job.
             purpose = (body.purpose or "").strip()
             if not purpose:
                 raise HTTPException(
                     status_code=400,
                     detail="A Purpose is required for a Producer agent.",
                 )
             created = agent_registry.create_agent(
                 name, "producer", settings=[{"key": "Purpose", "value": purpose}],
             )
         return get_agent(created["id"])
     ```
     (Keep `get_agent` referring to the existing `GET /agents/{agent_id}`
     handler function, exactly as `REQ-SB-37-US-01-T03` established —
     reconcile placement against the real current file, not literal line
     order.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this endpoint calls `agent_registry.create_agent` and the
  existing `get_agent` handler only; it does not call `vault_writer`,
  `skill_registry`, or `section_registry` directly (those are the
  wizard's own separate follow-up calls).
- Must reject a missing `name` with `400` before calling `create_agent` at
  all, for all three types.
- For `type == "producer"`, must reject a missing/blank `purpose` with
  `400` naming Purpose as missing — byte-identical-in-spirit to Expert's
  own required-domain check.
- For `type == "producer"`, must NOT require `domain`; for `type ==
  "expert"`/`"worker"`, must NOT require `purpose`.
- Must reject any `type` other than `"expert"`/`"worker"`/`"producer"` with
  an honest `400` naming all three supported types.
- A Producer's `create_agent` call MUST pass `settings=[{"key": "Purpose",
  "value": purpose}]` — never `[]`, never a `"Domain"`-labeled key.
- Must NOT accept a `section_id` or a Skill id in this endpoint's own body
  — Section assignment and the output-Skill grant stay the wizard's own
  separate, already-real calls (`PATCH /agents/{agent_id}`,
  `POST /agents/{agent_id}/skills/{skill_id}`).
- Do not change any other existing handler in this file (`GET /agents`,
  `GET /agents/{agent_id}`, `PATCH /agents/{agent_id}`, `/chat`,
  `/history`, `/actions/{action_id}`; the Skills routes live in
  `skills_router.py`, untouched).

---

## Tests

<!-- AC-02/AC-03/AC-06's own Given clauses each only require "a Producer
agent has just been created" — not specifically "via the wizard." This
endpoint is the real mechanism the wizard (T03) itself calls, so these
three scenarios are verified here, end-to-end, against every already-Done
downstream surface, before the wizard's own Producer UI exists —
backend-layer-first verification, mirroring REQ-SB-37-US-01-T03's own
AC-04/05/06/08 and REQ-SB-37-US-02-T01's own AC-03/05/06 placement
precedent exactly. AC-01/AC-04/AC-05 need a real, reachable wizard UI and
are tagged in T03 instead. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`; delete any leftover
`.second-brain/agents_registry.json`/`agent_skills.json` first; the
frontend dev server, `npm run dev` from `src/frontend`, should also be
running and already reachable at `/agents-map` for the Agents Map step —
no new frontend code is needed there, that surface is already `Done`):

1. Non-AC smoke check (Expert/Worker regression, quick confirm — already
   proven in `REQ-SB-37-US-02-T01`): `POST /agents` with `{"name":
   "Widgets Expert", "type": "expert", "domain": "Widgets manufacturing"}`
   → `200`. `POST /agents` with `{"name": "Ops Helper", "type": "worker"}`
   → `200`. Neither behavior changed by this task.
2. Non-AC smoke check (validation): `POST /agents` with `{"name": "Vault
   Scribe", "type": "producer"}` (no `purpose` key). Confirm `400`,
   message names the missing Purpose. `POST /agents` with `{"name": "Vault
   Scribe", "type": "producer", "purpose": "   "}` (whitespace only).
   Confirm `400` also.
3. Non-AC smoke check (type refusal unchanged): `POST /agents` with
   `{"name": "Reporter", "type": "coordinator"}`. Confirm `400`, message
   honestly names Expert, Worker, and Producer as the supported types.
   Confirm `GET /agents` lists only the 7 seed agents plus
   `widgets-expert`/`ops-helper` from step 1 — nothing partial created.
4. Non-AC smoke check (real creation): `POST /agents` with `{"name":
   "Vault Scribe", "type": "producer", "purpose": "Draft outbound
   account-plan notes for review."}`. Confirm `200`, response shape
   matches `GET /agents/{id}` (`id: "vault-scribe"`, `name`, `type:
   "producer"`, `settings` includes `{"key": "Purpose", "value": "Draft
   outbound account-plan notes for review."}`, `actions: []`,
   `section_id`/`section_name` self-healed default, `provider_id`/
   `provider_name` self-healed default, `keywords: []`, `working_mode`
   self-healed default). Confirm `GET /agents` now includes it.
5. **[REQ-SB-37-US-03-AC-02]** Grant the output Skill (the wizard's own
   single-grant-call mechanism): `POST /agents/vault-scribe/skills/
   write-to-vault-draft`. Confirm `{"granted": true}`. Assign a Section
   (mirrors the wizard's own follow-up call, `ADR-031` point 4):
   `PATCH /agents/vault-scribe` with `{"section_id": "technical"}` (or any
   real seed section id from `GET /sections`). Confirm `200`,
   `section_id`/`section_name` now reflect it. `GET
   /agents/vault-scribe/skills` — confirm `write-to-vault-draft` is
   present. `GET /agents/vault-scribe` — confirm `settings` still carries
   the Purpose entry from step 4 and the assigned Section — the full
   Purpose + granted output Skill + Section combination this AC's `Then`
   clause requires, all via the exact calls the wizard itself will issue.
6. **[REQ-SB-37-US-03-AC-03]** Open the already-`Done` Agents Map
   (`/agents-map`) in a browser — a fresh load or an SPA-internal
   nav-away/nav-back is sufficient, no server restart. Confirm
   `vault-scribe` renders on the Producer ring, inside the Section
   assigned in step 5, alongside the existing seed agents and
   `widgets-expert`/`ops-helper` — with zero Producer-specific frontend
   code from this story yet built.
7. **[REQ-SB-37-US-03-AC-06]** `POST /agents/vault-scribe/chat` with an
   ordinary conversational message (e.g. "hello"). Confirm an ordinary
   conversational reply, the same conversational path any existing agent
   uses. `GET /agents/vault-scribe/history` — confirm it returns
   `chat_user`/`chat_agent` entries in the exact same shape
   `GET /agents/{id}/history` already returns for any existing agent — no
   distinct "read-only"/"second-class" field or shape anywhere in the
   response.
8. Clean-up: delete `.second-brain/agents_registry.json` and
   `.second-brain/agent_skills.json`. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** — creating a Producer stores Purpose via `settings`, and
      the selected output Skill can be granted via the single existing
      grant call, and Section assignment reflects immediately — the full
      mechanism this AC's `Then` clause requires
- [ ] **AC-03** — the created Producer appears on the Agents Map, on the
      Producer ring, in its assigned Section, with no reload/restart
- [ ] **AC-06** — the created Producer's Chat and History behave
      identically to an existing agent's, with no second-class/read-only
      distinction
- [ ] `POST /agents` accepts `type == "producer"`; `purpose` required
      non-blank; stored via `settings=[{"key": "Purpose", "value":
      purpose}]`
- [ ] `POST /agents` for `type == "expert"`/`"worker"` remains
      byte-identical to prior behavior
- [ ] `POST /agents` rejects any `type` other than
      `"expert"`/`"worker"`/`"producer"` with an honest `400`
- [ ] `POST /agents` never accepts `section_id` or a Skill id in its own
      body
- [ ] No other existing `agents_router.py` handler's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The wizard's own Producer step UI, its Purpose field/single-select
  output-Skill control/Section picker, the three-call sequencing, and the
  honest missing-field rejection UI (`AC-01`/`AC-04`/`AC-05`) — all `T03`.
- Any change to `agent_registry.py`, `skill_registry.py`, `skill_tools.py`,
  `skills_router.py`, or `section_registry.py` — all reused unmodified.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-031` created at
`/plan-tasks` step 1) — the human reviews `ADR-031` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

**Why AC-02/AC-03/AC-06 are verified here, not in T03:** each scenario's
own Given clause only requires "a Producer agent has just been created,"
not specifically "via the wizard" — and every downstream surface exercised
(Skills grant, Agents Map, chat, history) is already `Done` and needs zero
code change for a created Producer. Verifying them here, against the real
mechanism the wizard itself will call, follows this project's own
established backend-layer-first verification pattern
(`REQ-SB-37-US-01-T03`/`REQ-SB-37-US-02-T01`'s own precedent) — it does
not weaken or defer proof of any locked AC, it proves it earlier and
against the real, unmodified downstream surfaces directly.

Full composition/sequencing reasoning: `Implementation/Architecture/
architecture.md` → "Amendment — Producer-type flow (REQ-SB-37-US-03,
ADR-031)"; `Implementation/Architecture/ADR.md` → `ADR-031` points 1/3/4.

---

## Implementation Log

**2026-08-14, coder.** Read the REAL current `agents_router.py` first — it
matched `REQ-SB-37-US-02-T01`'s own already-landed shape exactly (`domain:
str | None`, dispatch on `type in ("expert", "worker")`). Applied the
task's own diff verbatim: `purpose: str | None = None` added to
`CreateAgentBody`; `create_agent` dispatch gained the third `"producer"`
branch (Purpose required non-blank, stored via `settings=[{"key":
"Purpose", "value": purpose}]`); the type-refusal message now names all
three supported types.

**Environment finding, resolved in-scope (not an escalation):** the
`--reload` watcher did not pick up this edit on the first attempt — a
follow-up request still returned the stale pre-edit refusal message even
after a `WatchFiles ... Reloading` line had fired for an unrelated,
earlier `T01`-era `skill_tools.py` change. Direct process inspection
(`Get-CimInstance Win32_Process`) found an orphaned
`--multiprocessing-fork` child still serving requests under a parent PID
that no longer existed — the exact orphaned-reload-child shape this
project's own `Implementation/Learnings.md` already documents
(`SPRINT-019`/`021`/`022`/`029`), just triggered here by a rapid two-file
edit sequence rather than a single hang. Killed the specific orphaned PID,
started one fresh, explicitly-controlled `uvicorn` instance, and
re-confirmed the new refusal message ("...Expert, Worker, and Producer
are supported today.") before re-running any of this task's own Tests —
no test result reported below was taken against stale code.

**Verification (manual mode, real HTTP against the fresh backend
instance):**

- Non-AC smoke (Expert/Worker regression): both still `200`, unchanged.
- Non-AC smoke (validation): `POST /agents` `{"name": "Vault Scribe",
  "type": "producer"}` (no `purpose`) → `400`, "A Purpose is required for
  a Producer agent." Whitespace-only `purpose` → `400` also.
- Non-AC smoke (type refusal): `POST /agents` `{"type": "coordinator"}` →
  `400`, names Expert/Worker/Producer. `GET /agents` confirmed only the 7
  seeds + `widgets-expert` + `ops-helper` present — nothing partial from
  the refused/rejected attempts.
- Non-AC smoke (real creation): `POST /agents` `{"name": "Vault Scribe",
  "type": "producer", "purpose": "Draft outbound account-plan notes for
  review."}` → `200`, `id: "vault-scribe"`, `settings` carries the Purpose
  entry, all self-healed fields present.
- **AC-02 — PASS.** `POST /agents/vault-scribe/skills/write-to-vault-draft`
  → `{"granted": true}`. `PATCH /agents/vault-scribe` `{"section_id":
  "technical"}` → `200`, Section reflected immediately.
  `GET /agents/vault-scribe/skills` confirmed `write-to-vault-draft`
  present; `GET /agents/vault-scribe` confirmed Purpose + granted Skill +
  Section all present together — the full mechanism this AC's `Then`
  clause requires, via the exact calls the wizard itself will issue.
- **AC-03 — PASS.** CDP-driven headless-Edge screenshot of the real,
  already-`Done` Agents Map (waited for the real data fetch to complete
  before capturing, unlike a plain CLI `--screenshot` invocation which
  fired before the SPA's own async load finished on a first attempt —
  corrected by using `Page.captureScreenshot` after an explicit delay).
  `vault-scribe` rendered as the new Producer-ring (purple) node inside
  the Technical cluster, alongside `ops-helper` (Worker) and the 2
  Technical experts — matching the expected count exactly.
- **AC-06 — PASS.** `POST /agents/vault-scribe/chat` "hello" → an
  ordinary conversational reply. `GET /agents/vault-scribe/history`
  returned `chat_user`/`chat_agent` entries in the exact same shape any
  existing agent's history returns.
- Cleanup: reset `.second-brain/agents_registry.json`/`agent_skills.json`
  to a clean slate for `T03`'s own live testing; confirmed `GET /agents`
  back to 7 seeds. No stray pending-approval record was created by this
  task's own testing (no Supervised-mode invocation was exercised here).

**No other existing `agents_router.py` handler's behavior changed** —
confirmed via the unchanged Expert/Worker smoke checks above.

gate stays flagged (trigger-3, `ADR-031`, carried forward) — no new
MUST-FLAG trigger fired this pass; the orphaned-reload-child finding above
is a reconfirmation of an already-documented antipattern, not a new one.
