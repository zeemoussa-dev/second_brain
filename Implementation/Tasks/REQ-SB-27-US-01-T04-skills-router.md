---
id: REQ-SB-27-US-01-T04
title: New app/api/skills_router.py — GET /skills, GET/POST/DELETE /agents/{id}/skills[/{skill_id}], POST .../invoke; registered in app/main.py
parent_story: REQ-SB-27-US-01
requirement_id: REQ-SB-27
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-27-US-01-T03]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-27-US-01-T04 — New app/api/skills_router.py

## Parent Story

- Story: [[REQ-SB-27-US-01]] — `../UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-27 *Skills Repository*

---

## Objective

Add `app/api/skills_router.py` exposing `T03`'s `skill_registry.py`
surface over HTTP — catalog listing, per-agent grant/revoke, and the
plumbing-only invocation entry point — and register it in `app/main.py`.
This is the user/API-observable surface where every one of this story's
5 locked ACs is verified (this story ships zero UI).

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `skill_registry.py`'s full surface (`list_skills`,
  `list_agent_skills`, `grant_skill_access`, `revoke_skill_access`,
  `has_skill_access`, `invoke_skill`).
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`, `sections_router`, `providers_router`
  (and, once `REQ-SB-25-US-01` lands, an `app.mount("/mcp", ...)` call).

**After / Outputs:**
- `app/api/skills_router.py` exists with `GET /skills`, `GET
  /agents/{agent_id}/skills`, `POST /agents/{agent_id}/skills/{skill_id}`,
  `DELETE /agents/{agent_id}/skills/{skill_id}`, `POST
  /agents/{agent_id}/skills/{skill_id}/invoke`.
- `app/main.py` additionally registers `skills_router`.

---

## Files to Modify

- `src/backend/app/api/skills_router.py` (new):
  ```python
  from fastapi import APIRouter, HTTPException

  from app.business import agent_registry, skill_registry

  router = APIRouter()


  def _require_known_agent(agent_id: str) -> None:
      if agent_registry.get_agent(agent_id) is None:
          raise HTTPException(status_code=404, detail="Unknown agent")


  @router.get("/skills")
  def list_skills() -> list[dict]:
      return skill_registry.list_skills()


  @router.get("/agents/{agent_id}/skills")
  def list_agent_skills(agent_id: str) -> list[dict]:
      _require_known_agent(agent_id)
      return skill_registry.list_agent_skills(agent_id)


  @router.post("/agents/{agent_id}/skills/{skill_id}")
  def grant_skill(agent_id: str, skill_id: str) -> dict:
      _require_known_agent(agent_id)
      if skill_id not in {s["id"] for s in skill_registry.list_skills()}:
          raise HTTPException(status_code=404, detail="Unknown skill")
      skill_registry.grant_skill_access(agent_id, skill_id)
      return {"granted": True}


  @router.delete("/agents/{agent_id}/skills/{skill_id}")
  def revoke_skill(agent_id: str, skill_id: str) -> dict:
      _require_known_agent(agent_id)
      skill_registry.revoke_skill_access(agent_id, skill_id)
      return {"revoked": True}


  @router.post("/agents/{agent_id}/skills/{skill_id}/invoke")
  def invoke_skill(agent_id: str, skill_id: str) -> dict:
      _require_known_agent(agent_id)
      result = skill_registry.invoke_skill(agent_id, skill_id)
      if result.get("status") == "unknown_skill":
          raise HTTPException(status_code=404, detail="Unknown skill")
      if result.get("status") == "refused":
          raise HTTPException(status_code=403, detail=result.get("reason", "Access refused"))
      # Any other shape (honest "not yet available", or a real result once
      # a skill has a real handler) is returned as-is, 200 — never raised
      # as an error, since an honest-unavailable response is not a failure.
      return result
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.skills_router import router as skills_router
  ...
  app.include_router(skills_router)
  ```
  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `skill_registry`/`agent_registry` only.
- `POST .../invoke` must return `403` (refused, Scenario 3/`AC-03`) and a
  `200` honest-unavailable body (Scenario 4/`AC-04`) as **distinguishable**
  responses — never collapse them into the same status code or body shape.
- `GET/POST/DELETE /agents/{agent_id}/skills...` must `404` for an unknown
  `agent_id`; `POST .../skills/{skill_id}` (grant) must additionally `404`
  for an unknown `skill_id`.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.

---

## Tests

<!-- This story ships zero UI (see parent story's own Non-Goals) — every
locked AC is verified directly against this router's real HTTP surface,
the user/API-observable layer for a backend-only story, per this
project's own established placement rule (REQ-SB-08-US-01-T05's own
precedent). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`; delete any leftover
`.second-brain/agent_skills.json` first):

1. **[REQ-SB-27-US-01-AC-01]** `GET /skills`. Confirm the response
   includes exactly the one illustrative skill `T02` registered
   (`id`/`name`/`description` populated, matching `skill_tools.SKILLS`).
2. **[REQ-SB-27-US-01-AC-02]** `POST /agents/email-capture/skills/<skill
   id from step 1>`. Confirm `{"granted": true}`. `GET
   /agents/email-capture/skills` — confirm the response now includes that
   skill.
3. **[REQ-SB-27-US-01-AC-03]** `POST
   /agents/meeting-capture/skills/<skill id>/invoke` (an agent never
   granted this skill). Confirm `403`, with a refusal message — and
   confirm this response is distinct in status code and body shape from
   step 4's honest-unavailable response.
4. **[REQ-SB-27-US-01-AC-04]** `POST
   /agents/email-capture/skills/<skill id>/invoke` (the agent granted in
   step 2). Confirm `200` with a body that honestly states the skill is
   not yet available, and confirm no fabricated or guessed result
   (anything resembling a real diagram-understanding answer) is present
   anywhere in the response.
5. **[REQ-SB-27-US-01-AC-05]** `DELETE
   /agents/email-capture/skills/<skill id>`. Confirm `{"revoked": true}`.
   `GET /agents/email-capture/skills` — confirm the skill no longer
   appears. `POST /agents/email-capture/skills/<skill id>/invoke` again —
   confirm it now returns the same `403` refusal shape step 3 established,
   not the honest-unavailable shape from step 4.
6. Non-AC smoke check: `GET /agents/not-a-real-agent/skills` — confirm
   `404`. `POST /agents/email-capture/skills/not-a-real-skill` — confirm
   `404`.
7. Clean-up: delete `.second-brain/agent_skills.json` so no throwaway
   grant state leaks into later verification. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /skills` returns the registered catalog (Scenario 1/`AC-01`)
- [x] `POST /agents/{id}/skills/{skill_id}` grants access, reflected in
      `GET /agents/{id}/skills` (Scenario 2/`AC-02`)
- [x] `POST .../invoke` for an ungranted agent returns a `403` refusal,
      distinct from the honest-unavailable response (Scenario 3/`AC-03`)
- [x] `POST .../invoke` for a granted agent, with no real handler behind
      the skill, returns an honest `200` "not yet available" body, never a
      fabricated result (Scenario 4/`AC-04`)
- [x] `DELETE /agents/{id}/skills/{skill_id}` revokes access, reflected in
      `GET /agents/{id}/skills`, and Scenario 3's refusal now applies
      (Scenario 5/`AC-05`)
- [x] `404` for an unknown agent id on every route; `404` for an unknown
      skill id on grant
- [x] `skills_router` registered in `app/main.py` without changing any
      existing router's behavior
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component calling these endpoints — this story ships
  zero UI (see parent story's own Non-Goals); a future skill-invocation/UI
  follow-on story needs its own `/design` pass first.
- The skill catalog itself, the stub skill's implementation — `T02`.
- Grant/revoke CRUD, `has_skill_access`, `invoke_skill` business logic —
  `T03`.

---

## Context / Notes

**Was transitively blocked via `depends_on: [T03]`** — `T03` depends on
`T02`, which was itself genuinely blocked pending `REQ-SB-25-US-01`'s own
decomposer pass. Now resolved: `T02`'s `depends_on` is wired to the real
`REQ-SB-25-US-01-T05` (`ESCALATIONS.md` → `ESC-011`, `Resolved`).

If `REQ-SB-25-US-01` has already registered an `app.mount("/mcp", ...)`
call in `app/main.py` by the time this task runs (`REQ-SB-25-US-01-T05`),
add `skills_router` alongside it without reordering the existing
registrations.

---

## Implementation Log

**2026-08-12 — coder.** Created `src/backend/app/api/skills_router.py`
verbatim per this task's own code block (`GET /skills`, `GET
/agents/{agent_id}/skills`, `POST .../{skill_id}` grant, `DELETE
.../{skill_id}` revoke, `POST .../{skill_id}/invoke`). Registered in
`src/backend/app/main.py` additively (new import alongside the existing
`sections_router` import, new `app.include_router(skills_router)` call
appended after the existing `providers_router` registration) — no
existing router registration reordered or otherwise changed.

**Port note (same established pattern as `T04`/`SPRINT-014`):** verified
against the real backend on port `8002` (`mcp_client.py`'s own hardcoded
loopback MCP target; ports `8000`/`8001` both live-occupied on this host),
not this task's own literal `--port 8001` instruction — self-managed via
explicit kill-and-restart (real PIDs identified via `Get-CimInstance`,
never by image name).

**All 5 locked ACs verified live, real HTTP calls against the real
backend, `.second-brain/agent_skills.json` deleted before starting:**

- **[AC-01]** `GET /skills` → exactly the one `diagram-understanding`
  skill `T02` registered, `id`/`name`/`description` populated.
- **[AC-02]** `POST /agents/email-capture/skills/diagram-understanding` →
  `{"granted": true}`; `GET /agents/email-capture/skills` → includes it.
- **[AC-03]** `POST /agents/meeting-capture/skills/diagram-understanding
  /invoke` (never granted) → `403` with `{"detail": "Agent does not have
  access to this skill."}`.
- **[AC-04]** `POST /agents/email-capture/skills/diagram-understanding
  /invoke` (granted in AC-02) → `200` with `{"available": false,
  "message": "This skill is not yet available — no real handler has been
  built for it."}` — distinct status code and body shape from AC-03,
  confirmed no fabricated/guessed diagram-understanding result anywhere
  in the response.
- **[AC-05]** `DELETE /agents/email-capture/skills/diagram-understanding`
  → `{"revoked": true}`; `GET /agents/email-capture/skills` → `[]`; a
  further invoke on that agent/skill now returns the same `403` refusal
  shape AC-03 established.

**Non-AC smoke check (pass):** `GET /agents/not-a-real-agent/skills` →
`404`; `POST /agents/email-capture/skills/not-a-real-skill` → `404`.

**Clean-up:** `.second-brain/agent_skills.json` deleted afterward (its
only content was this verification session's own throwaway grant/revoke
state).

`status: Ready → Done`.

`gate: clear 2026-08-12` — implemented exactly per this task's own
literal code sample, no deviation from a locked AC, every AC-tagged
verification step performed and passing live. (The port choice mirrors
`SPRINT-014`'s own already-established, already-flagged pattern — not a
new finding requiring a fresh flag.)
