---
id: REQ-SB-95-US-05-T01
title: The one tag-keyed index as a projection, computed and rebound inside VaultManager.rebuild_index()
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "coder, 2026-10-18 — scope-internal judgement calls for human spot-check, nothing blocked: (1) the manual step was performed against a SYNTHETIC vault over the real HTTP surface rather than against the operator's real vault, because this session's standing conditions forbid reading the real vault even from a throwaway probe — AC-04 is independently verified by its four automated steps; (2) the one tag-shape rule keeps a deeper tag (`a/b/c`) as its own key rather than dropping it; (3) a new framework constraint could NOT be appended to `MEMORY.md`, which stands at 86 KB against the 40 KB budget its own rule 1 sets — recorded in `REVIEW-QUEUE.md` instead"
phase: P2
depends_on: []
created: 2026-10-16
updated: 2026-10-18
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

- [x] Projection computed and rebound inside `rebuild_index()`, one assignment site
- [x] Keys are every `<namespace>/<slug>` tag in the vault, no namespace list
- [x] No new artifact, no new cron job, no second refresh trigger
- [x] Existing per-entity Indexes untouched
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not done, and deliberately so:** `MEMORY.md` is 86 KB against the 40 KB
      budget its own rule 1 sets, which forbids appending while over. The one
      constraint this task produced is written out verbatim in `REVIEW-QUEUE.md`
      for the human to place once the file is under budget.
- [x] `CHANGELOG.md` entry appended

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

**Coder, 2026-10-18. `Ready → Done`. Both locked ACs verified.**

### What was built

Two files, exactly the two in `## Files to Modify`.

`app/business/core/vault/vault_manager.py` gains a module-level
`_vault_tag_index: dict[str, list[dict]]` beside `_vault_entries`, a
`_build_tag_index(entries)` builder, and two read accessors —
`get_entries_for_tag(tag)` and `get_tag_index_keys()`. `rebuild_index()`
computes `new_tag_index = _build_tag_index(new_entries)` and rebinds it in the
same assignment block as `_vault_entries`, one statement later. One extra pass
over entries already in memory: no second disk walk, no note re-read, no
`Index` artifact, no `storage_path`, no cron call. `IndexManager` and the three
existing per-customer Indexes are not imported, named or touched by this change
(`ADR-032`).

`tests/test_tag_keyed_index.py` is new: 10 tests, 8 of them AC-tagged, driving a
real `rebuild_index()` over a synthetic tmp vault through the **real** walk
(`vault_writer.list_all_note_paths()` is not monkeypatched anywhere in the
file), with an autouse fixture that fails any test in which
`data_access.indexes.write_index_json` or `HermesCLI.create_cron_job` is called.

### The one tag-shape rule, as implemented

A tag is a key when it **has a namespace** — a `/` with text on both sides. The
namespace is the text before the FIRST separator and the slug is everything
after it, so `a/b/c` keeps its own full name as a key rather than being
discarded; nothing carrying a namespace is ever dropped. A tag with no
separator (`urgent`) has no namespace, is not an entity tag and is not a key —
`list_tags()` is what answers whole-vault tag counts, and it still reports it.
`""`, `"/leading"` and `"trailing/"` are keys under neither reading. Stated in
the builder's docstring and asserted at both edges
(`test_the_one_tag_shape_rule_holds_at_both_edges`).

This is a judgement call inside scope, taken the lossless way: keeping `a/b/c`
rather than dropping it is the reading closest to AC-07's "no namespace prefix
is filtered in or out". Flagged for a human skim, not escalated.

### Locked ACs, step by step, with what was observed

**`[REQ-SB-95-US-05-AC-04]` — verified.** Four automated steps, all passing.

1. *Groups every note under each of its tags, no per-entity setup.* Seven-note
   synthetic vault, one `rebuild_index()`. Observed: `glyph/lumen-cartography`
   holds exactly its 4 notes, `ward/tessellate-works` its 1, `kind/hub` its 2,
   `kind/meeting` its 1; a three-tag note appears under all of its tags, not
   filed once. No provisioning call of any kind was made — the spies below were
   armed for this test too. (`test_every_note_is_grouped_under_each_of_its_tags`)
2. *A brand-new tag is a key immediately, with no artifact and no cron job.*
   `glyph/first-mention` asserted absent, one note carrying it written, one
   `rebuild_index()`. Observed: the key is present and holds exactly that note.
   `data_access.indexes.write_index_json` and `HermesCLI.create_cron_job` are
   both monkeypatched to `pytest.fail` for every test in the file; neither
   fired. (`test_a_brand_new_tag_is_a_key_immediately_after_the_next_rebuild`)
3. *Rebound in the same pass as `_vault_entries`.* A note deleted and a note
   added, then ONE `rebuild_index()` and an immediate assertion with no other
   refresh invoked. Observed: every entry in the projection **is the same object**
   (identity, not equality) as the one `get_entries()` returns; the two describe
   the same set of notes; the added note is in both; the deleted note and its
   now-empty `kind/meeting` key are in neither. There is no intermediate state
   in which one is newer.
   (`test_the_projection_describes_the_same_notes_as_the_entries_after_one_rebuild`)
4. *Exactly one refresh path.* The module's own source is parsed with `ast`.
   Observed: exactly 2 assignments to `_vault_tag_index` in the whole file — one
   module-level declaration and one rebind — the rebind is inside
   `rebuild_index`, no other function in the module assigns it, and it is the
   statement **immediately after** `_vault_entries = new_entries`.
   (`test_the_projection_is_assigned_in_exactly_one_place`)

*Manual step, performed against a synthetic vault — see the judgement call
below.* `POST /vault-index/refresh` over the real app returned `200`
`{'notes_indexed': 5, 'rebuilt_at': '2026-10-18T18:22:44…', 'agent_index_rebuild_triggered': False}`.
Projection key count **5**; namespaced tags in `GET /vault-search/tags` **5**;
the two key sets compared equal. Two spot checks both agreed:
`glyph/lumen-cartography` projection 3 vs `/tags` 3, `kind/hub` projection 2 vs
`/tags` 2. The unnamespaced `urgent` is in `/tags` and is correctly not a
projection key.

**`[REQ-SB-95-US-05-AC-07]` — verified.** Zero namespaces are registered
anywhere in this task — `register_tag_namespace` is `T02` and does not exist
yet, so the "install with no plugins at all" condition is literal, not simulated.

5. *Every `<namespace>/<slug>` tag present is a key.* Observed: the key list is
   exactly `['glyph/lumen-cartography', 'glyph/lumen-cartography/northern-reach',
   'kind/hub', 'kind/meeting', 'kind/thread', 'ward/tessellate-works']`, which
   includes `kind/thread` — a tag no plugin would ever claim as an entity
   namespace — and three distinct namespace prefixes. Four further invented
   namespaces (`quarl/`, `zz9/`, `a/`, `Mixed-Case/`), none of which exists
   anywhere in this repository, are keyed on identical terms. Structurally: the
   builder function's own syntax tree carries **no string literal containing a
   separator at all** besides its docstring, so there is no list for it to
   consult — asserted over the real source rather than against a hand-kept list
   of forbidden prefixes, which would date itself.
   (`test_every_namespace_present_is_a_key_with_nothing_registered`,
   `test_an_invented_namespace_is_a_key_on_the_same_terms`,
   `test_the_builder_carries_no_namespace_literal_at_all`)
6. *An unregistered key is retained and nameable.* With nothing registered,
   every key here is a key with no registered entry. Observed: all of them are
   returned by `get_tag_index_keys()` by name, and the notes behind them are
   still reachable through `get_entries_for_tag()` — none is dropped.
   (`test_a_tag_no_namespace_claims_is_retained_and_nameable`)

### The Windows `MAX_PATH` trap, proved rather than assumed

The fixture's deepest note sits at a path over 260 characters and the fixture
asserts that precondition, so every assertion above already covers a note the
limit could have hidden. A separate measurement, run against a throwaway
synthetic vault, pins the mechanism:

```
deep note path length    : 308
plain os.path.isfile()   : False
long_path os.path.isfile : True
notes found by real walk : 2
deep note in walk        : True
tag index keys           : ['glyph/probe', 'kind/thread']
grouped under glyph/probe: 2
deep note grouped        : True
```

`os.path.isfile()` answers **False** on a file that exists, with no exception —
which is exactly how a walk loses a note silently. The real walk
(`obsidian/notes.list_all_note_paths`, which already goes through `long_path()`
and prunes `_`-prefixed folders inside the traversal) finds it, `read_note`
opens it through the same prefix, and the projection groups it. Nothing new was
needed for this: the projection reads entries that are already in memory, so it
inherits the walk's correctness rather than repeating the walk.

### Test runs

Baseline measured before the first edit, and the final run, both from a
**scratch CWD** with `VAULT_PATH` and `SECOND_BRAIN_DATA_PATH` pointed at scratch
directories and the four other startup-required settings set to obvious fakes,
so the repository `.env` was never read and the operator's vault and data store
were never reachable:

- **Baseline: 677 passed / 9 failed** (686 collected).
- **Final: 687 passed / 9 failed** — exactly +10, the new file, no regression.

The 9 failures are identical in both runs and are not this task's: they are the
empty-install consequence of a scratch `SECOND_BRAIN_DATA_PATH` with no seeded
Templates (`test_template_editing`-adjacent readers in
`test_skill_writes_declaration.py`, `test_versioning.py`,
`test_vault_engine_is_single.py`, `test_blueprint_install.py`,
`test_blueprints_api.py`). The new file itself passes on that empty install, and
the only thing the whole suite wrote into the scratch data store was three state
files (`agent_providers.json`, `agent_sections.json`, `cockpit_chat.json`) —
which is three files that would otherwise have landed in the operator's real
store. Scratch directories were emptied afterwards.

### Judgement calls logged for human spot-check (none blocking)

1. **The manual step was run against a synthetic vault, not the operator's.**
   The task's manual step names the real vault; this session's standing
   conditions forbid reading or writing it, including from a throwaway probe,
   and starting the backend against it would also run startup side effects that
   can write. The same reconciliation was therefore performed over the real HTTP
   surface against a synthetic vault, and is recorded verbatim above. AC-04 does
   not depend on it: its four automated steps all pass.
2. **A deeper tag is kept, not dropped** — see the rule above.
3. **No `MEMORY.md` entry was appended.** The constraint this task produced is
   real and worth keeping, but `MEMORY.md` is 86 KB against the 40 KB budget its
   own rule 1 sets, which forbids appending while over. The text is written out
   in `REVIEW-QUEUE.md` for the human to place.

### Not done, deliberately

No `Index` artifact, no `IndexManager` call, no `hermes cron create`, no second
refresh path, no `storage_path`, no namespace registration (`T02`), no resolver
(`T03`), no scoped read (`T04`), no screen. The second `vault_manager.py` at
`business/core/skills/managers/` is Hermes payload (`ADR-019`) and was not
touched or synchronised.

### Escalations

**None.** No file outside `## Files to Modify` was needed: this task's switch-on
site is the rebind inside `rebuild_index()`, which is in the file the task
already names, and the projection has no caller yet to wire up (`T03` is its
first). No existing fixture is invalidated — the change is purely additive and
no validation was added.
