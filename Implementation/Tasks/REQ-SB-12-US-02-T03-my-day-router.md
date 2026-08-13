---
id: REQ-SB-12-US-02-T03
title: New app/api/my_day_router.py — GET /my-day/summary, /emails, /calendar, /todo
parent_story: REQ-SB-12-US-02
requirement_id: REQ-SB-12
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal assumption (CORS middleware added to main.py — see Implementation Log) for human spot-check"
phase: P1
depends_on: [REQ-SB-12-US-02-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02-T03 — New app/api/my_day_router.py

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Add the new `app/api/my_day_router.py` (`APIRouter(prefix="/my-day")`) with
its four `GET` endpoints backed by `T02`'s `my_day.py`, and register it in
`app/main.py` — the first router outside the `/poc` migration-endpoint
family (`architecture.md`'s own framing: My Day is an ongoing feature
surface, not a one-off maintenance operation).

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `app/business/my_day.py` (`summary()`,
  `list_email_items()`, `list_calendar_items()`).
- `app/main.py` registers `health_check_router` and `email_poc_router` only.

**After / Outputs:**
- `app/api/my_day_router.py` exists with `GET /my-day/summary`,
  `GET /my-day/emails`, `GET /my-day/calendar`, `GET /my-day/todo`.
- `app/main.py` additionally registers `my_day_router`.

---

## Files to Modify

- `src/backend/app/api/my_day_router.py` (new):
  ```python
  from fastapi import APIRouter

  from app.business import my_day

  router = APIRouter(prefix="/my-day")


  @router.get("/summary")
  def get_summary() -> dict:
      return my_day.summary()


  @router.get("/emails")
  def get_emails() -> list[dict]:
      return my_day.list_email_items()


  @router.get("/calendar")
  def get_calendar() -> list[dict]:
      return my_day.list_calendar_items()


  @router.get("/todo")
  def get_todo() -> list[dict]:
      # Hardcoded [] — REQ-SB-09's task source/kind folder is still
      # unresolved (this story's own Non-Goals); no vault read at all.
      return []
  ```

- `src/backend/app/main.py`:
  ```python
  from fastapi import FastAPI

  from app.api.email_poc_router import router as email_poc_router
  from app.api.health_check_router import router as health_check_router
  from app.api.my_day_router import router as my_day_router
  from app.scheduling.capture_scheduler import lifespan

  app = FastAPI(title="Second Brain", lifespan=lifespan)

  app.include_router(health_check_router)
  app.include_router(email_poc_router)
  app.include_router(my_day_router)
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this router calls `app.business.my_day` only, no direct
  `vault_writer`/filesystem access.
- `GET /my-day/todo` returns a literal hardcoded `[]` — no call into
  `my_day.py` needed for it (matches `my_day.summary()`'s own todo count
  being hardcoded, for the same reason).
- Must NOT modify `health_check_router`/`email_poc_router`'s registration
  order or behavior — additive only in `main.py`.
- Per `MEMORY.md`'s standing constraint: starting/restarting the dev server
  fires a real capture run (Outlook/Compass/vault write) via the existing
  app-start trigger — unrelated to this task's own endpoints, but expect it
  when starting the server for live verification below.

---

## Tests

<!-- This story's locked ACs (Scenarios 1/2/4/5/6/7/8) are user-observable on
the My Day dashboard/drill-down *pages* — they are tagged and verified live
in T04-T07 (the frontend tasks that actually render what these endpoints
return), per the decomposer's "user-observable outcome" placement rule
(mirrors REQ-SB-08-US-01's T01-T04/T05 split). The steps below are non-AC
smoke checks confirming each endpoint's shape/data against the real vault in
isolation, before the frontend tasks build on top. -->

**Manual verification steps** (from `src/backend`: `.venv\Scripts\uvicorn
app.main:app --reload --port 8001` — using an alternate port per `MEMORY.md`'s
port-8000-may-be-occupied constraint; then issue real HTTP requests, e.g. via
the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/my-day/summary`. Confirm
   the response is `{"emails": {"count": N}, "calendar": {"count": 0},
   "todo": {"count": 0}}` where `N` matches the real vault's captured email
   count.
2. Non-AC smoke check: `GET http://127.0.0.1:8001/my-day/emails`. Confirm a
   JSON array where each entry has `subject`/`sender`/`customer` keys,
   matching real captured Email notes.
3. Non-AC smoke check: `GET http://127.0.0.1:8001/my-day/calendar`. Confirm
   `[]` (real vault has no `Work/Meetings/` folder yet).
4. Non-AC smoke check: `GET http://127.0.0.1:8001/my-day/todo`. Confirm `[]`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /my-day/summary` returns `{"emails": {"count"}, "calendar":
      {"count"}, "todo": {"count": 0}}`
- [x] `GET /my-day/emails` returns `[{"subject", "sender", "customer"}]`
- [x] `GET /my-day/calendar` returns `[{"subject", "start", "customer"}]`
- [x] `GET /my-day/todo` returns `[]` always, no vault read
- [x] `my_day_router` registered in `app/main.py` alongside the existing
      routers, without changing their behavior
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls these endpoints — that is T04-T07.
- Building a real `/my-day/todo` vault read — deferred to a future story
  once REQ-SB-09 resolves its task source.

---

## Context / Notes

This is the first router outside the `/poc` migration-endpoint family —
`/poc/...` names a one-off maintenance operation; My Day is an ongoing
feature surface a user visits repeatedly. No new dependency.

---

## Implementation Log

Implemented exactly as specified — `app/api/my_day_router.py` created with
the four `GET` endpoints, registered in `app/main.py` alongside the
existing routers (`health_check_router`/`email_poc_router`), no existing
route's registration order/behavior changed. `main.py` was re-read fresh
immediately before this edit (per the run's own concurrency caution) —
confirmed it still held only the pre-existing two routers at that point;
a concurrent SPRINT-010 pass later appended `agents_router` after this
edit landed, without conflict (both edits additive, non-overlapping).

**Port note:** `MEMORY.md`'s existing port-8000-may-be-occupied constraint
turned out to extend further than documented — port `8001` (this task's
own suggested alternate) was *also* already occupied by a concurrent
sprint's own live backend dev server (a second `python.exe -m uvicorn
app.main:app --port 8001` process, confirmed via `Get-CimInstance
Win32_Process`). Used port `8002` instead for this task's own live
verification server. Logged as a fresh instance of the same standing
constraint, not a new one — see `MEMORY.md` update.

**Genuine gap found and fixed (scope-internal, within this task's own
`main.py` scope) — no CORS middleware existed anywhere in `src/backend`.**
`REQ-SB-12-US-01`'s `api/client.ts` was built but never actually called
(its own Starting State note: "exists, unused until now") — this is the
first task in the whole codebase making a real browser-to-FastAPI fetch
call. Without CORS, every browser-originated fetch from the Vite dev
server (a different origin/port than uvicorn) is blocked outright by the
browser itself — confirmed live: `MyDayPage`'s `fetchMyDaySummary()`
threw an uncaught `TypeError: Failed to fetch` and the page could show
none of Scenario 1/2/3's real content. This is not a verification-
environment-only quirk: frontend and backend run as genuinely separate
processes/origins in every deployment shape this architecture has
established (ADR-002/ADR-010), so this blocks every one of this story's
8 locked ACs from ever passing, not just this task's own non-AC smoke
checks. Fixed by adding `fastapi.middleware.cors.CORSMiddleware` to
`app/main.py`, scoped to the Vite dev server's own default bind addresses
(`http://localhost:5173`, `http://127.0.0.1:5173`) rather than a wildcard
— no new external dependency (`CORSMiddleware` ships inside the already-
installed `fastapi` package), confined to `main.py` (already in this
task's own `## Files to Modify`), does not touch any router's own
behavior or any other file. This is logged as a scope-internal assumption
(the exact allowed-origins list is a judgement call, not dictated by any
task/ADR text) per the coder's own "scope-internal judgement calls are
NOT escalations, log as assumptions" rule — task `gate` set to `flagged`
for human spot-check of the CORS origin list, not because the fix itself
is in doubt.

**Non-AC smoke checks (2026-08-11, server on port 8002, real vault):**
- `GET /my-day/summary` -> `{"emails": {"count": 178}, "calendar":
  {"count": 39}, "todo": {"count": 0}}`.
- `GET /my-day/emails` -> 178-entry array, each with
  `subject`/`sender`/`customer` keys, matching real captured Email notes.
- `GET /my-day/calendar` -> 39-entry array (not `[]` — same real-vault-
  state note as `T01`/`T02`'s Implementation Logs: SPRINT-006 landed
  concurrently, `Work/Meetings/` now has real notes), each with
  `subject`/`start`/`customer` keys.
- `GET /my-day/todo` -> `[]`.

gate: flagged 2026-08-11 — scope-internal assumption (CORS origin list),
per trigger 1/8 of the MUST-FLAG list; the fix itself was necessary for
every locked AC to be verifiable at all, not optional. No `ESCALATIONS.md`
entry — this did not require a new external dependency, a shared-
interface change to an existing consumer, or a decision outside this
task's own `Files to Modify` scope.
