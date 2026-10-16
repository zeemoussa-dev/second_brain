---
id: REQ-SB-95-US-05-T01
title: The one tag-keyed index as a projection, computed and rebound inside VaultManager.rebuild_index()
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-05-T01 — The Tag-Keyed Index as a Projection

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Group every `<namespace>/<slug>` tag in the vault into ONE in-memory index,
computed inside `VaultManager.rebuild_index()` and rebound in the same pass as
`_vault_entries` — so it can never be newer or older than the notes it groups,
and no new artifact, cron job or refresh trigger exists.

---

## Starting State → End State

**Before / Inputs:**

- `app/business/core/vault/vault_manager.py` holds module-level
  `_vault_index` / `_vault_entries` / `_last_rebuilt_at`, and
  `rebuild_index()` assembles brand-new structures end to end and then
  **atomically reassigns** them (a single-reference rebind, safe under the GIL
  — read the real function and its docstring before editing).
- Each entry already carries `tags` (`_build_entry` reads `frontmatter["tags"]`
  and defaults to `[]` when it is not a list). No extra parsing is needed.
- `get_entries()` is the iteration surface; `get_index()` is lookup-by-name and
  **loses collisions** (`BUG-076`, `MEMORY.md` 2026-09-25) — do not build the
  projection from it.
- `BUG-082` is why this is a projection at all: a stored copy with its own
  refresh trigger is how the backend served a three-day-stale vault.

**After / Outputs:**

- A module-level tag-keyed projection in the same file, built from
  `new_entries` inside `rebuild_index()` and rebound in the same assignment
  block as `_vault_entries`.
- Keys are **every** tag of the shape `<namespace>/<slug>` actually present in
  the vault — registered or not, with **no** hardcoded namespace allow-list or
  deny-list anywhere (a framework that filters to `customer/`/`partner/` would
  be naming a plugin's vocabulary; `ADR-022`/`ADR-035`). A tag with no `/`, or
  with more than one segment boundary, is handled by one stated, documented
  rule rather than silently.
- A read accessor returning, for one tag key, the entries carrying it — and an
  accessor for all keys.
- **No** new `Index` artifact, **no** `IndexManager` involvement, **no** new
  Hermes cron job, **no** second refresh path. It refreshes exactly when the
  vault index does.

---

## Files to Modify

- `src/backend/app/business/core/vault/vault_manager.py`
- `src/backend/tests/test_tag_keyed_index.py` (new)

---

## Constraints

- Inherits from parent story.
- **One rebind, one pass.** The projection must be assigned in the same place
  `_vault_entries` is. Computing it lazily on first read, or on a timer, or in
  a second function a caller must remember to call, all reintroduce `BUG-082`.
- **No new artifact and no new job.** If this task creates an `Index.json`, a
  `storage_path`, or calls `hermes cron create`, it is wrong.
- **The three existing per-customer Indexes and their hourly jobs are not
  touched, migrated or deleted** (`ADR-032`).
- Build from `get_entries()`-shaped data (every note), never from the by-stem
  map.
- Rebuild cost must stay proportional to one extra pass over entries already in
  memory — no second disk walk, no re-reading notes.

---

## Tests

**Automated tests** — `src/backend/tests/test_tag_keyed_index.py`, run with
`pytest tests/test_tag_keyed_index.py` from `src/backend`; follow
`tests/test_vault_index_collisions.py` and `tests/test_vault_index_refresh.py`
for the existing technique of driving a real `rebuild_index()` over a tmp
vault.

1. `[REQ-SB-95-US-05-AC-04]` Build a tmp vault whose notes carry several
   different `<namespace>/<slug>` tags; call `rebuild_index()` once and assert
   the projection groups every note under each of its tags, with no
   per-entity setup step of any kind having been performed.
2. `[REQ-SB-95-US-05-AC-04]` Add a note carrying a **brand-new** tag, call
   `rebuild_index()` again, and assert the new tag is a key immediately — and
   that no `Index` artifact was created (`data_access.indexes.write_index_json`
   spy never called) and no cron-creating call was made (spy the Hermes CLI).
3. `[REQ-SB-95-US-05-AC-04]` Assert the projection is rebound in the same pass
   as `_vault_entries`: mutate the vault, call `rebuild_index()`, and assert
   the projection and `get_entries()` describe the same set of notes with no
   intermediate state where one is newer (assert immediately after the single
   call, with no other refresh invoked).
4. `[REQ-SB-95-US-05-AC-04]` Assert there is exactly one refresh path — grep-
   equivalent assertion in the test: the projection is assigned in exactly one
   place in `vault_manager.py` (read the module source and count assignments).
5. `[REQ-SB-95-US-05-AC-07]` With **zero** namespaces registered, assert every
   `<namespace>/<slug>` tag in the tmp vault — including ones no plugin would
   ever claim, e.g. `kind/thread` — is present as a key, and that no namespace
   prefix is filtered in or out by any list in the framework.
6. `[REQ-SB-95-US-05-AC-07]` Assert a tag key carrying no registered entry is
   retained and reportable as unknown (naming the tag), never dropped from the
   index.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-04]` With the backend running against the real vault,
   `POST /vault-index/refresh`, then read the projection's key count and spot-
   check two real tags against `GET /vault/tags`; confirm the counts agree.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Projection computed and rebound inside `rebuild_index()`, one assignment site
- [ ] Keys are every `<namespace>/<slug>` tag in the vault, no namespace list
- [ ] No new artifact, no new cron job, no second refresh trigger
- [ ] Existing per-entity Indexes untouched
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Registering a namespace — `T02`.
- Turning a name into a tag (resolution) — `T03`.
- Reading an entity's notes in order — `T04`.
- Any screen; surfacing the index for inspection is a story Non-Goal.
- A freshness/staleness surface — `ADR-032` defers it to `BUG-085`.

---

## Context / Notes

`architecture.md` → **§The One Tag-Keyed Index — a Projection, Not an
Artifact** and `ADR-037` are authoritative, including why `ADR-032`'s "a single
artifact" is read as one index with a dict lookup rather than an `Index`
kind instance. If the operator rejects that reading, `ADR-037` is the thing
that changes — not this task's own judgement.

---

## Implementation Log

_(Filled in by the coder.)_
