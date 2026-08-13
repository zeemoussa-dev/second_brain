---
id: REQ-SB-18-US-01-T03
title: New app/api/sections_router.py — GET/POST/PATCH/DELETE /sections
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

# REQ-SB-18-US-01-T03 — New app/api/sections_router.py

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Add `app/api/sections_router.py` exposing Section CRUD over HTTP, translate
`T02`'s block-until-empty result dict into `HTTP 409` with a name-resolved
message (`ADR-014` point 4), and register the router in `app/main.py`.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `section_registry.py`'s full CRUD surface.
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`.

**After / Outputs:**
- `app/api/sections_router.py` exists with `GET/POST /sections`,
  `PATCH/DELETE /sections/{section_id}`.
- `app/main.py` additionally registers `sections_router`.

---

## Files to Modify

- `src/backend/app/api/sections_router.py` (new):
  ```python
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel

  from app.business import agent_registry, section_registry

  router = APIRouter(prefix="/sections")


  class SectionCreateBody(BaseModel):
      name: str


  class SectionRenameBody(BaseModel):
      name: str


  def _blocked_delete_message(name: str, blocked_by_agent_ids: list[str]) -> str:
      names = [agent_registry.get_agent(aid)["name"] for aid in blocked_by_agent_ids]
      count = len(names)
      joined = ", ".join(names)
      return (
          f'Can\'t delete "{name}" — {count} agent{"s" if count != 1 else ""} '
          f'({joined}) {"are" if count != 1 else "is"} still assigned to this '
          "section. Move them to a different section first, then try again."
      )


  @router.get("")
  def list_sections() -> list[dict]:
      return section_registry.list_sections()


  @router.post("")
  def create_section(body: SectionCreateBody) -> dict:
      section = section_registry.create_section(body.name)
      return {**section, "agent_ids": []}


  @router.patch("/{section_id}")
  def rename_section(section_id: str, body: SectionRenameBody) -> dict:
      section = section_registry.rename_section(section_id, body.name)
      if section is None:
          raise HTTPException(status_code=404, detail="Unknown section")
      return section


  @router.delete("/{section_id}")
  def delete_section(section_id: str) -> dict:
      sections_by_id = {s["id"]: s for s in section_registry.list_sections()}
      section = sections_by_id.get(section_id)
      if section is None:
          raise HTTPException(status_code=404, detail="Unknown section")
      result = section_registry.delete_section(section_id)
      if not result["deleted"]:
          raise HTTPException(
              status_code=409,
              detail=_blocked_delete_message(section["name"], result["blocked_by_agent_ids"]),
          )
      return {"deleted": True}
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.sections_router import router as sections_router
  ...
  app.include_router(sections_router)
  ```
  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `section_registry`/`agent_registry`
  only, no direct filesystem access of its own.
- `POST /sections`'s response must include an `agent_ids: []` key (a
  freshly created section always has zero agents) so the frontend's
  `SectionSummary` shape is uniform across `GET`/`POST` responses without
  a second round-trip.
- `DELETE /sections/{section_id}` must 404 for an unknown id and 409
  (never 200, never silently no-op) when blocked — never partially delete.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.

---

## Tests

<!-- This story's locked ACs are user-observable on Settings' Sections
area and the Agent Settings surface — verified live in T07/T08 (the
frontend tasks that render/drive this router's endpoints), per the
established "user-observable outcome" placement rule (REQ-SB-13-US-01's
own T05/T06-T08 split). The steps below are non-AC smoke checks confirming
each endpoint's shape/behavior against the real backend in isolation. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/sections`. Confirm 5
   sections (Technical, Sales, Productivity, Customers, Products), each
   with an `agent_ids` list.
2. Non-AC smoke check: `POST /sections` with `{"name": "Operations"}`.
   Confirm the response includes `id`, `name: "Operations"`,
   `agent_ids: []`. `GET /sections` now includes it.
3. Non-AC smoke check: `PATCH /sections/operations` with `{"name":
   "Ops"}`. Confirm the response's `id` is unchanged, `name` is now
   `"Ops"`. `PATCH /sections/not-a-real-id` with any body — confirm `404`.
4. Non-AC smoke check: `DELETE /sections/ops` (zero agents assigned).
   Confirm `{"deleted": true}` and it's gone from `GET /sections`.
   `DELETE /sections/technical` (has agents assigned, from the seed
   default) — confirm `409` with a message naming every currently-blocking
   agent by display name (not raw id). `DELETE /sections/not-a-real-id` —
   confirm `404`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /sections` returns every section with its `agent_ids`
- [ ] `POST /sections` creates and returns `{"id","name","agent_ids": []}`
- [ ] `PATCH /sections/{id}` renames in place (same `id`), `404` for an
      unknown id
- [ ] `DELETE /sections/{id}` deletes and returns `{"deleted": true}` when
      unblocked, `409` with a name-resolved message when blocked, `404`
      for an unknown id
- [ ] `sections_router` registered in `app/main.py` without changing any
      existing router's behavior
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls these endpoints — `T05`
  (`layoutAgents.ts`), `T07` (`SectionsCard.tsx`), `T08`
  (`AgentDetailPanel.tsx`).
- `PATCH /agents/{agent_id}` (per-agent section reassignment) — `T04`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

If a concurrent session has already registered another router in
`app/main.py` by the time this task runs, add `sections_router` alongside
it without reordering the existing registrations (router registration
order has no behavioral significance in FastAPI).

---

## Implementation Log

**2026-08-11 — Done.** Created `app/api/sections_router.py` matching the
task's own code block verbatim (`GET/POST /sections`, `PATCH/DELETE
/sections/{section_id}`), registered in `app/main.py` additively
(`from app.api.sections_router import router as sections_router` +
`app.include_router(sections_router)`, appended after the existing
registrations, no reordering).

Live verification (real backend, `uvicorn app.main:app --port 8001`):
1. `GET /sections` → all 5 seed sections, each with `agent_ids`.
2. `POST /sections {"name":"Operations"}` → `{"id":"operations",
   "name":"Operations","agent_ids":[]}`; confirmed present in `GET
   /sections`.
3. `PATCH /sections/operations {"name":"Ops"}` → `id` unchanged
   (`"operations"`), `name` now `"Ops"` — confirms the slug-fixed-at-
   creation contract live. `PATCH /sections/not-a-real-id` → `404`.
4. `DELETE /sections/operations` (0 agents, the renamed "Ops" row) →
   `{"deleted": true}`, gone from `GET /sections`. `DELETE
   /sections/technical` (5 agents assigned) → `409` with `detail: "Can't
   delete \"Technical\" — 5 agents (Email Capture, Meeting Capture, To-Do
   Capture, People Notes, Vault Q&A) are still assigned to this section.
   Move them to a different section first, then try again."`. `DELETE
   /sections/not-a-real-id` → `404`.

One assumption logged (scope-internal, not an escalation): this task's own
step 4 literally reads "`DELETE /sections/ops`" — but since `PATCH` never
regenerates a section's `id` on rename (this task's own point, correctly
implemented), the renamed section's id stayed `"operations"`, not `"ops"`.
`DELETE /sections/ops` correctly 404'd (no such id) — used
`/sections/operations` instead, which behaved exactly as this task's own
AC describes. This is confirmatory of the design, not a defect.

Final state after this task's run: exactly the clean 5-section seed
(Technical/Sales/Productivity/Customers/Products) — no cleanup needed.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block. The `/sections/ops` vs
`/sections/operations` note above is a scope-internal judgement call
(spotted and corrected during verification), not a material assumption
about the code's own behavior.
