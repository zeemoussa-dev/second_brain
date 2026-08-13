---
id: REQ-SB-02-US-01-T03
title: API surface — app/api/vault_search_router.py
parent_story: REQ-SB-02-US-01
requirement_id: REQ-SB-02
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-02-US-01-T01, REQ-SB-02-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-02-US-01-T03 — API surface (`vault_search_router.py`)

## Parent Story

- Story: [[REQ-SB-02-US-01]] — `../UserStories/REQ-SB-02-US-01-browse-and-search.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-02 *Browse & Search*

---

## Objective

Expose `T01`'s `list_notes`/`get_note_detail` and `T02`'s `search` over
HTTP, plus a `status` endpoint surfacing `vault_indexing.
get_last_rebuilt_at()` for Scenario 7's honest "nothing indexed yet" state.

---

## Starting State → End State

**Before / Inputs:**
- `T01`/`T02` (dependencies, must be `Done` first) provide `app.business.
  vault_search.list_notes/get_note_detail/search` and `app.business.
  vault_indexing.get_last_rebuilt_at()`.
- No `/vault-search` route exists anywhere in `app/api/`.

**After / Outputs:**
- New `app/api/vault_search_router.py`, `APIRouter(prefix="/vault-search")`:
  `GET /vault-search/status`, `GET /vault-search/notes`, `GET
  /vault-search/notes/{stem}`, `GET /vault-search/search`, `GET
  /vault-search/tags`.
- Registered in `app/main.py`.

---

## Files to Modify

- `src/backend/app/api/vault_search_router.py` (new):
  ```python
  """HTTP surface for browse/tag-filter/note-detail/ranked-search
  (REQ-SB-02-US-01) -- delegates to app.business.vault_search/
  vault_indexing only, HTTP-only, no data_access/filesystem access of its
  own (ADR-003)."""
  from __future__ import annotations

  from fastapi import APIRouter, HTTPException

  from app.business import vault_indexing, vault_search

  router = APIRouter(prefix="/vault-search")


  @router.get("/status")
  def get_status() -> dict:
      """Scenario 7 -- the frontend calls this first, on page load.
      indexed=false means the entire browse/search surface should render
      the honest "nothing indexed yet" state instead of any list/search
      UI."""
      last_rebuilt_at = vault_indexing.get_last_rebuilt_at()
      return {"indexed": last_rebuilt_at is not None, "last_rebuilt_at": last_rebuilt_at}


  @router.get("/notes")
  def get_notes(tag: str | None = None, page: int = 1, page_size: int = 20) -> dict:
      """Scenarios 1, 2, 6 -- tag omitted = all notes."""
      return vault_search.list_notes(page=page, page_size=page_size, tag=tag)


  @router.get("/notes/{stem}")
  def get_note(stem: str) -> dict:
      """Scenario 3."""
      detail = vault_search.get_note_detail(stem)
      if detail is None:
          raise HTTPException(status_code=404, detail=f"No indexed note with stem '{stem}'")
      return detail


  @router.get("/search")
  def get_search(q: str, limit: int = 20) -> dict:
      """Scenarios 4, 5."""
      return vault_search.search(q, limit=limit)


  @router.get("/tags")
  def get_tags() -> dict:
      """Feeds the frontend's tag-filter chip row (Scenario 2's own
      real-tag-discovery prerequisite)."""
      return vault_search.list_tags()
  ```
- `src/backend/app/main.py`:
  - Add `from app.api.vault_search_router import router as vault_search_router`
    to the existing alphabetically-grouped router imports (after
    `system_health_router`, before `from app.scheduling...`).
  - Add `app.include_router(vault_search_router)` alongside the other
    `app.include_router(...)` calls.

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `vault_search`/`vault_indexing` only,
  never `vault_writer`/filesystem directly.
- `GET /vault-search/status` must reflect `vault_indexing.
  get_last_rebuilt_at()` on every call, live — no caching of the readiness
  flag at the router layer.
- `GET /vault-search/notes/{stem}` returns `404` for an unresolvable stem —
  never a `200` with an empty/null body standing in for "not found."
- Do not gate any of these endpoints behind a working mode
  (`ADR-018`/`ADR-020`) — browse/search is not an Agents Map agent action.
- Do not add a write/mutation endpoint of any kind — this story is
  read-only throughout (standing `MEMORY.md`/story Constraint).

---

## Tests

<!-- Covers the HTTP surface for all 7 ACs -- the underlying functions are
already covered by T01/T02's own Tests; this task's Tests exercise the real
HTTP round-trip, mirroring REQ-SB-01-US-01-T03's own precedent. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001` — an alternate
port per `MEMORY.md`'s port-8000-may-be-occupied constraint; then real HTTP
requests via `Invoke-RestMethod`):

1. **[REQ-SB-02-US-01-AC-01]** `GET /vault-search/notes?page=1&page_size=1000`
   — confirm the response's `"total"` matches the real vault's indexed
   note count and `"notes"` is a correctly-shaped, sorted list.
2. **[REQ-SB-02-US-01-AC-02]** `GET /vault-search/notes?tag=<a real tag>`
   — confirm only notes carrying that tag are returned.
3. **[REQ-SB-02-US-01-AC-03]** `GET /vault-search/notes/{stem}` for a real
   note with at least one real link — confirm `forward_links`/`backlinks`
   are present and correctly resolved; `GET /vault-search/notes/
   _no_such_stem_` returns `404`.
4. **[REQ-SB-02-US-01-AC-04]/[AC-05]** `GET /vault-search/search?q=<a real
   query>` returns ranked `results`; `GET /vault-search/search?q=<a
   nonsense token>` returns `{"query": ..., "results": []}`.
5. **[REQ-SB-02-US-01-AC-06]** `GET /vault-search/notes?tag=<a tag with no
   matches>` — confirm `{"total": 0, "notes": []}`, HTTP `200`, not an
   error.
5b. Non-AC smoke check (feeds AC-02's frontend UI): `GET /vault-search/tags`
   returns every real tag with a correct count, sorted by count descending.
6. **[REQ-SB-02-US-01-AC-07]** `GET /vault-search/status` — confirm
   `"indexed": true` and a real `last_rebuilt_at` timestamp against the
   already-running, already-indexed dev server (the honest "not indexed"
   branch, `indexed: false`/`last_rebuilt_at: null`, is verified indirectly
   via `T01`'s own direct-function-call test of `get_last_rebuilt_at()`
   before any rebuild has run in a process — restarting the real dev server
   is not a practical way to observe this HTTP-level, since the existing
   app-start scheduler tick, per `MEMORY.md`, rebuilds the index almost
   immediately on every start).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /vault-search/notes` returns the full, paginated, sorted browse
      list (AC-01)
- [x] `GET /vault-search/notes?tag=...` correctly narrows by tag (AC-02)
- [x] `GET /vault-search/notes/{stem}` returns a note's forward-links/
      backlinks, `404` for an unknown stem (AC-03)
- [x] `GET /vault-search/search?q=...` returns ranked results (AC-04)
- [x] `GET /vault-search/search?q=...` for a non-matching query returns an
      honest empty `results` list (AC-05)
- [x] `GET /vault-search/notes?tag=...` for a non-matching tag returns an
      honest empty `notes` list, HTTP 200 (AC-06)
- [x] `GET /vault-search/status` accurately reflects index readiness
      (AC-07)
- [x] `app/main.py` registers the new router; no other router's
      registration order/behavior changes
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend — `T04`.
- Any write/mutation endpoint.
- Gating this router behind a working mode.

---

## Context / Notes

Matches `architecture.md`'s "Browse & Search" section verbatim. Starting/
restarting the dev server fires a real capture run (Outlook/Compass/vault
write) via the existing app-start trigger (`MEMORY.md`'s standing
constraint) — unrelated to this task's own endpoints, but expect it.

---

## Implementation Log

**2026-08-13 — Built and live-verified via real HTTP against the real
vault.** New `app/api/vault_search_router.py` (`/status`, `/notes`,
`/notes/{stem}`, `/search`, `/tags`) exactly as specified; registered in
`app/main.py` alphabetically after `vault_index_router`, before
`agent_activity_router` — import placement matched the task's own
instruction (after `system_health_router`, before the `app.scheduling`
import).

**Verification** — started the real dev server (`.venv\Scripts\python.exe
-m uvicorn app.main:app --port 8001`; the app-start capture trigger fired
and completed as expected per this task's own Context note, confirmed via
`GET /vault-search/status` eventually returning `indexed: true`):
- **[AC-01]** `GET /vault-search/notes?page=1&page_size=1000` → `"total":
  503`, 503 real notes returned — PASS.
- **[AC-02]** `GET /vault-search/notes?tag=customer/masdar` → `"total":
  54`, every note carries the tag — PASS.
- **[AC-03]** `GET /vault-search/notes/Core42` → real `forward_links`
  (`[]`, a hub note is a link target not source, honestly empty) and 208
  real `backlinks`; `GET /vault-search/notes/_no_such_stem_` → `404` —
  PASS.
- **[AC-04]/[AC-05]** `GET /vault-search/search?q=masdar%20renewal` → 8+
  real ranked results, `Masdar` (Customer hub) ranked #1; `GET
  /vault-search/search?q=zzqxvbjklmnop9999nonexistenttoken` (see `T02`'s
  own logged AC-05 query-substitution note) → `{"results": []}` — PASS.
- **[AC-06]** `GET /vault-search/notes?tag=customer/_no_such_tag_exists_`
  → `{"total": 0, "notes": []}`, HTTP `200` — PASS.
- Non-AC smoke check: `GET /vault-search/tags` → real tag list with
  correct counts, sorted descending (`kind/emails` 199, `customer/core42`
  146, ...) — PASS.
- **[AC-07]** `GET /vault-search/status` on the already-running, already-
  indexed dev server → `{"indexed": true, "last_rebuilt_at":
  "2026-08-13T11:58:59...Z"}` — PASS. The honest `indexed: false` branch
  is verified indirectly via `T01`'s own direct
  `get_last_rebuilt_at()`-before-any-rebuild test, per this task's own
  Tests note (restarting the real dev server is impractical to catch live
  given the near-immediate app-start scheduler tick) — additionally
  re-confirmed end-to-end at the UI layer in `T04`'s own verification via a
  disclosed, reverted client-side fetch stub.

No deviation from the plan. `app/main.py`'s other router registrations/
CORS config untouched (confirmed by diff). No write/mutation endpoint
added. Not gated behind a working mode, per Constraints.

gate: clear 2026-08-13 — no new MUST-FLAG trigger fired in this task's own
build.
