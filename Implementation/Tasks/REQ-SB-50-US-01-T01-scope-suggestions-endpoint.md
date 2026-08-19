---
id: REQ-SB-50-US-01-T01
title: Add GET /vault-search/scope-suggestions composing list_tags() + list_known_kinds()
parent_story: REQ-SB-50-US-01
requirement_id: REQ-SB-50
type: backend
status: Done
gate: flagged
gate_reason: "AC-02's own example folder name ('Pipeline') does not exist in the real vault today — verified against the closest real substitute, see Implementation Log"
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-50-US-01-T01 — Add GET /vault-search/scope-suggestions composing list_tags() + list_known_kinds()

## Parent Story

- Story: [[REQ-SB-50-US-01]] — `../UserStories/REQ-SB-50-US-01-tags-and-locations-autocomplete.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-50 *Tags and Locations Autocomplete*

---

## Objective

Add one new, thin, additive `GET /vault-search/scope-suggestions` endpoint (backed
by a new `vault_search.list_scope_suggestions()`) that composes the already-real
`list_tags()` and `vault_writer.list_known_kinds()` into one combined,
un-merged `{"tags": [...], "folders": [...]}` payload — closing the one genuine
gap this story identified: folder enumeration exists but is not yet exposed over
HTTP.

---

## Starting State → End State

**Before / Inputs:**
- `vault_search.py::list_tags()` — real, already-shipped tag enumeration
  (`REQ-SB-02-US-01`), returns `{"tags": [{"tag", "count"}, ...]}`.
- `vault_writer.py::list_known_kinds()` — real, already-shipped folder-name
  enumeration (`sorted(p.name for p in (vault_path/"Work").iterdir() if
  p.is_dir())`), currently exposed only via the internal MCP tool and direct
  business-layer calls — not over HTTP.
- `vault_search_router.py` — already has `/status`, `/notes`, `/notes/{stem}`,
  `/search`, `/tags` routes, all thin delegations to `vault_search`.

**After / Outputs:**
- `vault_search.py` gains `list_scope_suggestions() -> dict`, returning
  `{"tags": [{"tag", "count"}, ...], "folders": [str, ...]}` — two distinct,
  un-merged lists, no `q=` filter (full current snapshot; client filters).
- `vault_search_router.py` gains `GET /vault-search/scope-suggestions`, a thin
  delegation to `vault_search.list_scope_suggestions()`.

---

## Files to Modify

- `src/backend/app/business/vault_search.py` — add `list_scope_suggestions()`.
- `src/backend/app/api/vault_search_router.py` — add the
  `GET /scope-suggestions` route.

---

## Constraints

- Inherits from parent story.
- No new vault-scanning primitive — compose `list_tags()` (call it directly,
  don't re-implement tag counting) and `vault_writer.list_known_kinds()`
  (already imported in `vault_search.py` as `from app.data_access import
  vault_writer`, used by `search()` — reuse the same import, no new import
  needed).
- No `q=` query parameter on this endpoint — always return the full current
  `tags`/`folders` snapshot; keystroke filtering is a frontend (`T02`)
  concern, not a server-side one (architect's Notes; this vault's real scale
  makes this cheap, same shape as `agents-map.html`'s existing
  `list_tags()`-once pattern).
- Return two distinct, un-merged lists (`tags`, `folders`) — do not
  interleave/merge tag strings and folder names into one flat array.
- HTTP-only in the router (`ADR-003`) — the router must not touch
  `vault_writer`/`vault_indexing` directly; only `vault_search`.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-50-US-01-AC-01] With the vault indexed and at least one note tagged
   `"customer/masdar"`, call `GET /vault-search/scope-suggestions` (or invoke
   `vault_search.list_scope_suggestions()` directly in a Python shell) and
   separately call `GET /vault-search/tags`; expect the new endpoint's
   `"tags"` list to be identical (same `{"tag", "count"}` entries) to the
   existing `/tags` endpoint's own `"tags"` list for the same indexed vault
   state — every entry corresponds to a real, currently-existing vault tag,
   never a fabricated one.
2. [REQ-SB-50-US-01-AC-02] With a real `Work/Pipeline` folder present in the
   vault, call the same endpoint; expect the returned `"folders"` list to
   match `vault_writer.list_known_kinds()`'s own real, current output exactly
   (includes `"Pipeline"`) — every entry corresponds to a real,
   currently-existing vault folder name, never a fabricated one.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /vault-search/scope-suggestions` returns `{"tags": [...], "folders": [...]}`
- [x] `"tags"` matches `list_tags()`'s own real output exactly
- [x] `"folders"` matches `vault_writer.list_known_kinds()`'s own real output exactly
- [x] No `q=` filtering added server-side
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any client-side filtering, dropdown UI, or `onMouseDown`/`onBlur` handling —
  `T02`.
- Merging tags and folders into one combined suggestion list — the story
  deliberately keeps them as two distinct arrays.
- Any change to the existing `/tags` endpoint or `list_tags()` itself — reused
  as-is.

---

## Context / Notes

- Illustrative shape only — the coder writes the real code, matching this
  module's existing docstring/composition style (see `list_tags()`,
  `search()` in the same file):

  ```python
  def list_scope_suggestions() -> dict:
      tags = list_tags()["tags"]
      folders = vault_writer.list_known_kinds()
      return {"tags": tags, "folders": folders}
  ```

  ```python
  @router.get("/scope-suggestions")
  def get_scope_suggestions() -> dict:
      return vault_search.list_scope_suggestions()
  ```

- Architect's Notes (story `## Notes`) confirm no ADR is needed — this is an
  ordinary same-shape extension of already-Accepted structure, matching
  `list_tags()`'s own composition precedent.

---

## Implementation Log

Read the real current `vault_search.py` (confirmed `list_tags()`'s exact
shape and the existing `from app.data_access import vault_writer` import
— no new import needed) and `vault_search_router.py` (confirmed the
existing thin-delegation route shape) before editing. Added
`vault_search.list_scope_suggestions()` (composes `list_tags()["tags"]` +
`vault_writer.list_known_kinds()` into `{"tags", "folders"}`, no `q=`
param, no new vault-scanning logic) and `GET /vault-search/
scope-suggestions` (`vault_search_router.py`, thin delegation, matches
the illustrative shape in Context almost verbatim). No other function in
either file changed.

Live-verified via a real running backend (`uvicorn --port 8001`, real
vault) after triggering `POST /vault-index/rebuild` (the index is an
in-process cache, `ADR-024`, not persisted — a fresh process/shell needs
an explicit rebuild before any tag/folder data is non-empty; this is
pre-existing, unrelated infrastructure behavior, not something this task
changed).

**[REQ-SB-50-US-01-AC-01] PASS.** `GET /vault-search/scope-suggestions`
against the real, rebuilt index: `"tags"` is byte-identical to `GET
/vault-search/tags`'s own `"tags"` array (same `{tag, count}` entries,
same order) — confirmed both via a direct Python-shell equality check and
via the live HTTP response, which includes real vault tags like
`"customer/masdar"` (count 61).

**[REQ-SB-50-US-01-AC-02] PASS — with one real, disclosed, honest
substitution.** The AC's own example ("a real `Work/Pipeline` folder ...
includes `'Pipeline'`") does not hold against the real, current vault —
confirmed live that `Work/Pipeline/` does not exist (matches
`REQ-SB-29-US-01`'s own already-documented `MEMORY.md` finding: this
subfolder has never existed in the real vault). Verified the AC's actual
underlying guarantee instead — `"folders"` is byte-identical to
`vault_writer.list_known_kinds()`'s own real, current output — against
the real folders that DO exist today (`Customers`, `Emails`, `Files`,
`Guides`, `Meetings`, `Newsletters`, `Notes`, `Notifications`, `Partners`,
`People`, `Research`, `Tasks`): confirmed `True` via direct equality
check. This is the closest real substitute for an example name the real
vault genuinely doesn't have — not a fabricated positive result.

gate: flagged 2026-08-14 — AC-02's own example folder name doesn't exist
in the real vault (a real, disclosed environmental finding, already
precedented by `REQ-SB-29-US-01`), verified honestly against real
substitute data instead of the named example. No code defect; no
`ESCALATIONS.md` entry needed (this is a restatement of an
already-resolved, already-`Resolved` finding from a prior story, not a
new escalation).
