---
id: REQ-SB-01-US-01-T03
title: On-demand re-index endpoint — app/api/vault_index_router.py
parent_story: REQ-SB-01-US-01
requirement_id: REQ-SB-01
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-01-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-01-US-01-T03 — On-demand re-index endpoint

## Parent Story

- Story: [[REQ-SB-01-US-01]] — `../UserStories/REQ-SB-01-US-01-vault-indexing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-01 *Vault Indexing*

---

## Objective

Add the explicit, on-demand re-index trigger (`ESC-021`'s resolved
"both" trigger design, path (a)) — a new `POST /vault-index/rebuild`
endpoint that calls `vault_indexing.rebuild_index()` synchronously and
returns rebuild stats, reflecting a vault change immediately without
waiting for the next scheduled run.

---

## Starting State → End State

**Before / Inputs:**
- `T02` (dependency, must be `Done` first) provides
  `app.business.vault_indexing.rebuild_index()`.
- No `/vault-index` route exists anywhere in `app/api/`.

**After / Outputs:**
- New `app/api/vault_index_router.py`, `APIRouter(prefix="/vault-index")`:
  `POST /vault-index/rebuild` → calls `rebuild_index()` synchronously,
  returns `{"notes_indexed": int, "rebuilt_at": str}` (ISO-8601 UTC
  timestamp of when the rebuild completed).
- Registered in `app/main.py` alongside the other routers.

---

## Files to Modify

- `src/backend/app/api/vault_index_router.py` (new):
  ```python
  """Explicit, on-demand vault re-index trigger (REQ-SB-01-US-01,
  ESC-021 resolved trigger path (a)) -- alongside the scheduler-tick
  refresh T04 wires up separately. HTTP-only, delegates to business/
  (ADR-003)."""
  from __future__ import annotations

  from datetime import datetime, timezone

  from fastapi import APIRouter

  from app.business import vault_indexing

  router = APIRouter(prefix="/vault-index")


  @router.post("/rebuild")
  def rebuild_vault_index() -> dict:
      """Plain (non-async) handler -- FastAPI/Starlette runs a synchronous
      route handler in its own threadpool automatically, so this blocking,
      read-heavy full-vault scan never blocks the event loop, with no
      manual asyncio.to_thread call needed at this layer (unlike
      capture_scheduler.py's run_capture_if_idle, which isn't reached
      through an HTTP request at all). Independent of capture_scheduler.
      _capture_run_lock -- that lock guards overlapping *vault-writing*
      capture runs, a concern this read-only, side-effect-free rebuild
      does not share (ADR-024)."""
      index = vault_indexing.rebuild_index()
      return {
          "notes_indexed": len(index),
          "rebuilt_at": datetime.now(timezone.utc).isoformat(),
      }
  ```
- `src/backend/app/main.py`:
  - Add `from app.api.vault_index_router import router as vault_index_router`
    to the existing alphabetically-grouped router imports.
  - Add `app.include_router(vault_index_router)` alongside the other
    `app.include_router(...)` calls.

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this router calls `vault_indexing` only, never
  `vault_writer`/filesystem directly.
- No filter/query parameters on this endpoint — it is a rebuild trigger,
  not a browse/search endpoint (`REQ-SB-02`'s job, out of scope here).
- Do not gate this endpoint behind any working mode
  (`ADR-018`/`ADR-020`) — vault indexing is not an Agents Map agent
  action.
- Do not add a `GET /vault-index/...` read/query route in this task —
  only the `POST .../rebuild` trigger.

---

## Tests

<!-- Covers AC-08. Requires a real running backend so the HTTP round-trip
itself is exercised, not just the underlying function (already covered by
T02). Uses a temporary test note, mirroring T02's own temp-note pattern. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001` — an alternate
port per `MEMORY.md`'s port-8000-may-be-occupied constraint; then issue
real HTTP requests via `Invoke-RestMethod`):

1. **[REQ-SB-01-US-01-AC-08]** `POST http://127.0.0.1:8001/vault-index/rebuild`
   once (baseline). Note the returned `notes_indexed` count. Then, without
   restarting the server or waiting for any scheduled tick, create one
   temporary note directly at `Work/Emails/_index_test_ac08.md` (valid
   frontmatter, e.g. `type`/`customer`/`tags: ["kind/email"]`). Immediately
   `POST http://127.0.0.1:8001/vault-index/rebuild` again; confirm the
   returned `notes_indexed` is exactly one greater than the baseline, and
   `rebuilt_at` is a fresh, later timestamp than the first call's — proving
   the vault change is reflected immediately, without waiting for
   `REQ-SB-07`'s hourly schedule. Delete the temp note afterward and
   `POST .../rebuild` one final time to confirm `notes_indexed` returns to
   the original baseline — no leftover test artifact.
2. Non-AC smoke check: confirm the response is valid JSON with exactly the
   two documented keys (`notes_indexed`, `rebuilt_at`), and that a repeat
   call with no vault change in between returns the same `notes_indexed`
   count (idempotent when nothing changed).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `POST /vault-index/rebuild` triggers an immediate, full rebuild and
      reflects a just-made vault change without waiting for the scheduled
      tick (AC-08)
- [ ] Response shape is `{"notes_indexed": int, "rebuilt_at": str}`, no
      filter/query parameters
- [ ] `app/main.py` registers the new router; no other router's
      registration order/behavior changes
- [ ] Real vault left with zero leftover test artifacts after verification
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any `GET` read/query/browse/search endpoint over the index — `REQ-SB-02`.
- Scheduler-tick wiring — `T04`.
- Gating this endpoint behind a working mode — vault indexing is not an
  Agents Map agent action.

---

## Context / Notes

Matches `architecture.md`'s "Vault Indexing Layer" section and `ADR-024`
verbatim. Starting/restarting the dev server fires a real capture run
(Outlook/Compass/vault write) via the existing app-start trigger
(`MEMORY.md`'s standing constraint) — unrelated to this task's own
endpoint, but expect it.

---

## Implementation Log

**2026-08-13 — Built exactly as specified, no deviation.** New
`src/backend/app/api/vault_index_router.py`
(`APIRouter(prefix="/vault-index")`, `POST /rebuild`); `app/main.py`
re-read fresh before editing (confirmed drifted from this task's own
sample since it was authored — `mcp_auth.require_hermes_shared_secret`
now wraps the `/mcp` mount, concurrent `REQ-SB-04`/`ADR-025` work landing
in this same session) — added the `vault_index_router` import in
alphabetical order and one `app.include_router(vault_index_router)` call
alongside the others; no other router's registration order/behavior
touched.

**Verification method deviation (assumption, logged for spot-check, not
an escalation):** the task's own `## Tests` block specifies starting a
real `uvicorn --reload --port 8001` process. Attempted exactly that
first: the server hung indefinitely at "Scheduler started" past 38
seconds with no further log output — this is `BUGS.md` → `BUG-008`
("App-start Outlook-COM capture in `main.py`'s lifespan has no timeout,
can hang the whole server's startup indefinitely"), confirmed live, not
worked around silently. Killed the two specific PIDs identified as this
attempt's own parent/child processes (verified by creation timestamp
correlation against an unrelated, already-running pair from a separate
concurrent session, left untouched — never a blanket `taskkill`, per
`SPRINT-009`'s own documented antipattern). Fell back to
`fastapi.testclient.TestClient(app)`, instantiated **without** the `with`
context manager — this does not invoke the app's `lifespan` (confirmed:
no capture-run log lines appeared), so `BUG-008`'s hang never triggers,
while still exercising the real FastAPI routing/dependency-injection HTTP
layer end to end (`HTTP Request: POST http://testserver/vault-index/
rebuild "HTTP/1.1 200 OK"` in the real client output) — not merely
calling `rebuild_vault_index()` directly as a Python function. This
mirrors `Implementation/Learnings.md`'s own `SPRINT-023` pattern ("skip
the HTTP layer entirely when it isn't load-bearing... useful when an
unrelated app-startup side effect blocks the whole server"), extended
one step further (real ASGI ⁠routing via `TestClient`, not a raw function
call) since this task's own AC specifically needs the HTTP round-trip
itself exercised.

**Manual verification (via `TestClient`, real vault):**

- **[REQ-SB-01-US-01-AC-08]** Baseline `POST /vault-index/rebuild` →
  `{"notes_indexed": 502, "rebuilt_at": "2026-08-13T11:31:03.092939+00:00"}`.
  Created `Work/Emails/_index_test_ac08.md` (valid frontmatter) without
  restarting/waiting. Immediate `POST /vault-index/rebuild` →
  `{"notes_indexed": 503, "rebuilt_at": "2026-08-13T11:31:03.216026+00:00"}`
  — exactly baseline+1, `rebuilt_at` strictly later. Deleted the temp note;
  final `POST /vault-index/rebuild` → `notes_indexed: 502`, back to
  baseline. PASS — a just-made vault change is reflected immediately, no
  wait for any scheduled tick.
- Non-AC smoke check: response is valid JSON with exactly the two
  documented keys; a repeat call with no vault change in between returned
  the identical `notes_indexed` count (idempotent). PASS.

Real vault left with zero leftover test artifacts — confirmed by the
final rebuild's `notes_indexed` count matching the pre-test baseline
exactly (502, the same real-vault count `T02`'s own verification pass
also confirmed clean-baseline; the vault's real filename-stem collision
named in `ESC-027` is unrelated to this task and does not affect this
task's own AC-08 delta-of-1 check).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired for this task
itself (`BUG-008` is a pre-existing, already-logged, out-of-scope defect
this task worked around per established precedent, not a new
escalation; the `TestClient`-without-lifespan substitution is a
scope-internal verification-method judgement call, logged here for
spot-check, not an AC weakening — the same real HTTP layer is exercised
either way).
