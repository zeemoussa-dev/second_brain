---
id: REQ-SB-19-US-01-T03
title: New app/api/providers_router.py — GET/POST/PATCH/DELETE /providers, credential never returned
parent_story: REQ-SB-19-US-01
requirement_id: REQ-SB-19
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-19-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01-T03 — New app/api/providers_router.py

## Parent Story

- Story: [[REQ-SB-19-US-01]] — `../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-19 *Per-Agent LLM Provider Selection*

---

## Objective

Add `app/api/providers_router.py` exposing Provider CRUD over HTTP,
translate `T02`'s block-until-unused result dict into `HTTP 409` with a
name-resolved message (`ADR-014` point 4), and register the router in
`app/main.py`.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `provider_registry.py`'s full CRUD surface.
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`, and (once `REQ-SB-18-US-01-T03` has
  landed) `sections_router`.

**After / Outputs:**
- `app/api/providers_router.py` exists with `GET/POST /providers`,
  `PATCH/DELETE /providers/{provider_id}` — never a `credential` field in
  any response.
- `app/main.py` additionally registers `providers_router`.

---

## Files to Modify

- `src/backend/app/api/providers_router.py` (new):
  ```python
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel

  from app.business import agent_registry, provider_registry

  router = APIRouter(prefix="/providers")


  class ProviderCreateBody(BaseModel):
      name: str
      endpoint: str
      credential: str
      model: str


  class ProviderUpdateBody(BaseModel):
      name: str | None = None
      endpoint: str | None = None
      credential: str | None = None
      model: str | None = None


  def _blocked_removal_message(name: str, blocked_by_agent_ids: list[str]) -> str:
      names = [agent_registry.get_agent(aid)["name"] for aid in blocked_by_agent_ids]
      count = len(names)
      joined = ", ".join(names)
      return (
          f'Can\'t remove "{name}" — {count} agent{"s" if count != 1 else ""} '
          f'({joined}) currently {"select" if count != 1 else "selects"} this '
          "Provider. Switch every agent using it to a different Provider "
          "first, then try again."
      )


  @router.get("")
  def list_providers() -> list[dict]:
      # provider_registry.list_providers() never includes "credential" —
      # nothing to strip here (ADR-014 point 5).
      return provider_registry.list_providers()


  @router.post("")
  def create_provider(body: ProviderCreateBody) -> dict:
      provider_registry.create_provider(body.name, body.endpoint, body.credential, body.model)
      # Re-read via list_providers() rather than returning the raw created
      # dict, so the response never includes "credential" either.
      created = next(p for p in provider_registry.list_providers() if p["name"] == body.name)
      return created


  @router.patch("/{provider_id}")
  def update_provider(provider_id: str, body: ProviderUpdateBody) -> dict:
      updated = provider_registry.update_provider(
          provider_id,
          name=body.name,
          endpoint=body.endpoint,
          credential=body.credential,
          model=body.model,
      )
      if updated is None:
          raise HTTPException(status_code=404, detail="Unknown provider")
      return next(p for p in provider_registry.list_providers() if p["id"] == provider_id)


  @router.delete("/{provider_id}")
  def remove_provider(provider_id: str) -> dict:
      providers_by_id = {p["id"]: p for p in provider_registry.list_providers()}
      provider = providers_by_id.get(provider_id)
      if provider is None:
          raise HTTPException(status_code=404, detail="Unknown provider")
      result = provider_registry.remove_provider(provider_id)
      if not result["deleted"]:
          raise HTTPException(
              status_code=409,
              detail=_blocked_removal_message(provider["name"], result["blocked_by_agent_ids"]),
          )
      return {"deleted": True}
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.providers_router import router as providers_router
  ...
  app.include_router(providers_router)
  ```
  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones, including `sections_router` if
  `REQ-SB-18-US-01-T03` has already landed it.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `provider_registry`/`agent_registry`
  only, no direct filesystem access of its own.
- **`credential` must never appear in any response from this router, in
  any endpoint, under any circumstance** — `POST`/`PATCH`'s handlers
  deliberately re-read via `list_providers()` (which never includes it)
  rather than returning the create/update functions' own raw dicts
  (which do still hold `credential` internally, for `compass_client`-style
  future use) — this is the load-bearing guarantee `ADR-014` point 5
  requires.
- `DELETE /providers/{provider_id}` must 404 for an unknown id and 409
  (never 200, never silently no-op) when blocked.
- `POST /providers` requires all four fields (`name`/`endpoint`/
  `credential`/`model`) — Pydantic's own required-field validation
  (no defaults on `ProviderCreateBody`) enforces this; do not add
  defaults.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.

---

## Tests

<!-- This story's locked ACs are user-observable on Settings' Providers
area and the Agent Settings surface — verified live in T05 (ProvidersCard)
and T06 (AgentDetailPanel), per the established "user-observable outcome"
placement rule. The steps below are non-AC smoke checks confirming this
router's shape/behavior against the real backend in isolation, with
particular attention to the credential-never-returned guarantee. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/providers`. Confirm
   exactly one entry (`"Compass"`, `is_default: true`, `has_real_client:
   true`, `credential_set: true`) and **inspect the raw response body
   text** to confirm the substring `"credential"` (the key name itself,
   not just its value) does not appear anywhere in it.
2. Non-AC smoke check: `POST /providers` with `{"name": "Test Provider",
   "endpoint": "https://example.test", "credential": "secret-key",
   "model": "test-model"}`. Confirm the response has `id`, `name`,
   `endpoint`, `model`, `credential_set: true`, `is_default: false`,
   `has_real_client: false` — and again confirm no `"credential"`
   substring anywhere in the raw response body.
3. Non-AC smoke check: `PATCH /providers/test-provider` with
   `{"endpoint": "https://example.test/v2"}` (credential omitted).
   Confirm the response's `endpoint` updated, `credential_set` still
   `true`, still no `"credential"` substring in the response.
   `PATCH /providers/not-a-real-id` — confirm `404`.
4. Non-AC smoke check: `DELETE /providers/test-provider` (zero agents
   assigned). Confirm `{"deleted": true}` and it's gone from
   `GET /providers`. `DELETE /providers/compass` — confirm `409` with a
   message naming every currently-blocking agent by display name (should
   list all 5, since every agent defaults to Compass). `DELETE
   /providers/not-a-real-id` — confirm `404`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /providers` returns every provider, never a `credential` field
- [ ] `POST /providers` creates and returns the created provider (no
      `credential` field), requires all 4 fields
- [ ] `PATCH /providers/{id}` updates only the supplied fields (omitted
      `credential` preserves the stored value), no `credential` field in
      the response, `404` for an unknown id
- [ ] `DELETE /providers/{id}` deletes and returns `{"deleted": true}`
      when unblocked, `409` with a name-resolved message when blocked,
      `404` for an unknown id
- [ ] `providers_router` registered in `app/main.py` without changing any
      existing router's behavior
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls these endpoints — `T05`
  (`ProvidersCard.tsx`), `T06` (`AgentDetailPanel.tsx`).
- `PATCH /agents/{agent_id}` (per-agent Provider reassignment), the
  `_invoke_action` availability gate — `T04`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

If `REQ-SB-18-US-01-T03` has already registered `sections_router` in
`app/main.py` by the time this task runs, add `providers_router` alongside
it without reordering the existing registrations.

---

## Implementation Log

**Built 2026-08-11 (coder).** `src/backend/app/api/providers_router.py`
created verbatim per this task's own code block (`GET/POST /providers`,
`PATCH/DELETE /providers/{id}`, `_blocked_removal_message`); `providers_router`
registered in `app/main.py` alongside the existing routers (import + one
`app.include_router(providers_router)` line, additive only, no reordering).

**Non-AC smoke check (per this task's own Tests, all 4 steps), real backend
on `http://127.0.0.1:8001` (`uvicorn app.main:app --port 8001`), real HTTP
via `curl`:**
1. `GET /providers` — exactly one entry ("Compass", `is_default: true`,
   `has_real_client: true`, `credential_set: true`); raw response body text
   confirmed to contain **no** bare `"credential"` key substring (checked
   precisely, distinguishing it from `credential_set`). **PASS.**
2. `POST /providers` `{"name": "Test Provider", ...}` — response had `id`/
   `name`/`endpoint`/`model`/`credential_set: true`/`is_default: false`/
   `has_real_client: false`; no `"credential"` key in the raw response.
   **PASS.**
3. `PATCH /providers/test-provider` `{"endpoint": ".../v2"}` (credential
   omitted) — `endpoint` updated, `credential_set` still `true`, no
   `"credential"` key. `PATCH /providers/not-a-real-id` → `404`. **PASS.**
4. `DELETE /providers/test-provider` (0 agents) → `{"deleted": true}`, gone
   from `GET /providers`. `DELETE /providers/compass` → `409`, message named
   all 5 blocking agents by display name (`Can't remove "Compass" — 5
   agents (Email Capture, Meeting Capture, To-Do Capture, People Notes,
   Vault Q&A) currently select this Provider...`). `DELETE
   /providers/not-a-real-id` → `404`. **PASS.**

All test data cleaned up; final `GET /providers` state confirmed back to
just the seeded Compass entry. No assumptions beyond this task's own
literal code (implemented verbatim). `app/main.py`'s existing router
registrations (`health_check_router`/`email_poc_router`/`my_day_router`/
`agents_router`/`sections_router`) unchanged — confirmed by inspection,
purely additive diff.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
