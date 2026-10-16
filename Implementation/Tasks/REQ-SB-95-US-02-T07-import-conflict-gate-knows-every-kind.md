---
id: REQ-SB-95-US-02-T07
title: The import conflict gate knows every artifact kind, not four
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-95-US-02-T04]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T07 — The import conflict gate knows every artifact kind, not four

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-actions-as-the-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *Actions and Workflows*

Resolves `ESCALATIONS.md` → **ESC-065**, raised by `REQ-SB-95-US-02-T04`.

---

## Objective

Make `artifact_import_conflicts._MANAGER_BY_KIND` cover every artifact kind the
export side can put in a manifest, so a bundle containing an `action` — or an
`index`, broken the same way since 2026-09-06 — imports instead of failing whole.

---

## Starting State → End State

**Before / Inputs:**
- `_MANAGER_BY_KIND` maps four kinds (`skill`, `template`, `agent`, `pipeline`)
  and `detect_conflicts()` raises `ValueError` for anything else.
- `preview_import()` and `commit_import()` both call `detect_conflicts()` over the
  whole manifest before deploying, so one `action` or `index` entry fails the
  entire bundle and nothing in it is imported.
- `tests/test_index_artifact_kind.py` verifies the import side through
  `artifact_import._deploy_one`, which is precisely the call that bypasses this
  gate — which is why the hole has never shown up in the suite.

**After / Outputs:**
- Every kind `artifact_export` can emit resolves to a real Manager here.
- A mixed bundle carrying an `action` and an `index` alongside the older kinds
  previews and commits, each entry's `conflicts` flag decided independently.
- The `ValueError` still fires for a genuinely unknown kind — this task widens
  the set, it does not remove the guard.

---

## Files to Modify

- `src/backend/app/business/logic/artifact_import_conflicts.py` — add `index` and
  `action` to `_MANAGER_BY_KIND` (importing `IndexManager` and `ActionManager`,
  both of which already expose `get_by_id`). Correct the comment above the map:
  it claims a four-kind vocabulary matching `sbf_archive`/`artifact_export`, which
  is the stale assumption that caused this.
- `src/backend/tests/test_action_artifact_kind.py` — add the AC-tagged tests below.

---

## Constraints

- Inherits from parent story.
- **Drive the real route.** The new tests must call `preview_import` /
  `commit_import`, never `_deploy_one` — testing through `_deploy_one` is exactly
  what hid this defect, and a test that repeats that mistake does not close it.
- Do not change `detect_conflicts()`'s contract: unknown kinds still raise, every
  artifact is still checked independently with a freshly-constructed Manager, and
  no entry short-circuits a later one.
- Do not edit `tests/test_index_artifact_kind.py`. It belongs to a `Done` task;
  `index` coverage for this gate goes in this task's own tests.

---

## Tests

**Automated tests:** `cd src/backend && .venv/Scripts/python.exe -m pytest -q`

1. `[REQ-SB-95-US-02-AC-05]` `detect_conflicts` over a manifest naming all six
   kinds returns six entries with a `conflicts` flag each and raises nothing;
   assert the kind set it accepts now equals the kinds `artifact_export` can emit.
2. `[REQ-SB-95-US-02-AC-05]` A real `.sbf` carrying an `action` **and** an `index`
   alongside a `skill` passes `preview_import()` — the call that raised
   `ValueError: unrecognized artifact kind` before this task — and reports a
   per-entry conflict decision.
3. `[REQ-SB-95-US-02-AC-05]` `commit_import()` on that same bundle deploys every
   entry; re-reading each kind's Manager by id returns the imported artifact, and
   an unrelated artifact already on the machine is untouched.
4. `[REQ-SB-95-US-02-AC-05]` A manifest naming a genuinely unknown kind still
   raises `ValueError`, and the message still lists the accepted kinds.
5. Full suite green: `432 passed` or better, no new warnings.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `index` and `action` resolve to their real Managers in `_MANAGER_BY_KIND`
- [x] A mixed-kind bundle previews and commits through the real import route
- [x] An unknown kind still raises, with the accepted kinds named
- [x] The stale four-kind comment is corrected rather than left to mislead again
- [x] `ESCALATIONS.md` ESC-065 marked Resolved, naming this task as the resolving
      artefact (append only — never edit the original entry's body)
- [x] `REVIEW-QUEUE.md` ESC-065 pointer cleared
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — deliberately **not** updated; see the Implementation Log
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Workflow as the seventh kind — `REQ-SB-95-US-04` owns that, and it will add its
  own entry to the same map.
- Any change to `artifact_export`, `artifact_import._deploy_one`, or the secret
  scan: `T04` finished those and they are correct.
- Re-testing `index` end to end beyond this gate.

---

## Context / Notes

`ESC-065` measured the defect directly on this install:

```
kinds known to detect_conflicts: ['agent', 'pipeline', 'skill', 'template']
index  -> ValueError: unrecognized artifact kind 'index' ...
action -> ValueError: unrecognized artifact kind 'action' ...
```

The lesson worth carrying past this fix is in `MEMORY.md` already as of `T04`:
adding an artifact kind touches six files, and this is the one everybody misses.
A seventh kind arrives with `Workflow` shortly — leaving the map correct and its
comment honest is what keeps that task from rediscovering this.

---

## Implementation Log

**2026-10-16 — Done.** Commit `b2b09fe` (code + tests + `CHANGELOG.md`).

**Baseline before the first edit:** `432 passed, 1 warning in 32.85s` — the one
warning is pre-existing (`starlette/testclient.py` `anyio.abc.BlockingPortal`
deprecation), present at `e915965` and unchanged after.

**What changed.** `_MANAGER_BY_KIND` gained `"index": IndexManager` and
`"action": ActionManager` (plus their two imports). Neither Manager needed any
new machinery — `IndexManager.get_by_id` and `ActionManager.get_by_id` already
exist and both already answer `None` for an unknown id. `detect_conflicts()`
itself is untouched, so its contract holds: unknown kinds still raise, each
artifact is still checked against a freshly-constructed Manager, and no entry
short-circuits a later one. The map's comment no longer claims a 4-kind
vocabulary; it states that the map must cover every kind `artifact_export` can
emit, names why (the gate fails the whole bundle, not one entry) and names
`ESC-065`.

### Verification — automated mode, `cd src/backend && .venv/Scripts/python.exe -m pytest -q`

All four new tests live in `src/backend/tests/test_action_artifact_kind.py`
under the `-- The import conflict gate --` banner, and all four drive
`preview_import`/`commit_import`. None of them calls `_deploy_one`.

| Tests step | AC | Test | Observed |
|---|---|---|---|
| 1 | `REQ-SB-95-US-02-AC-05` | `test_the_gate_accepts_every_kind_the_export_can_emit` | **Pass.** `set(_MANAGER_BY_KIND) == set(artifact_export._PAYLOAD_FOLDER) \| {"pipeline"}` — six kinds. `detect_conflicts` over a six-kind manifest returned six entries, each with a `conflicts` flag, and raised nothing. (`pipeline` is the one exportable kind absent from `_PAYLOAD_FOLDER`: `commit_export` gives it its own branch because it ships as `pipelines/<id>.json`.) |
| 2 | `REQ-SB-95-US-02-AC-05` | `test_a_mixed_kind_bundle_previews_through_the_real_import_route` | **Pass.** A real `.sbf` written by `artifact_export.commit_export` carrying `index:adnoc`, `action:make-strategic-entity` and the `skill:vault-search` the Action pulls in. `preview_import()` — the exact call that raised `ValueError: unrecognized artifact kind` — returned a per-entry decision: `index` `True` (that id is on the receiving machine), `action` `False`, `skill` `False`. |
| 3 | `REQ-SB-95-US-02-AC-05` | `test_a_mixed_kind_bundle_commits_every_entry_through_the_real_import_route` | **Pass.** `commit_import()` on the same bundle returned `deployed` for all three. Re-read: `ActionManager().get_by_id("make-strategic-entity").description` is the exported one and its implementation still names `vault-search`; `IndexManager().get_by_id("adnoc").name == "ADNOC"`; `SkillManager().get_by_id("vault-search").name == "Vault Search"`, pushed once to one profile. An unrelated Action already on the receiving machine (`open-the-artifacts-page`) was untouched, description and implementation kind both unchanged. |
| 4 | `REQ-SB-95-US-02-AC-05` | `test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name` | **Pass.** A hand-written `.sbf` whose manifest names `kind: "workflow"` still raises `ValueError` out of `preview_import`, message `unrecognized artifact kind 'workflow' -- expected one of ['action', 'agent', 'index', 'pipeline', 'skill', 'template']` — all six accepted kinds named. |
| 5 | — | full suite | **Pass.** `436 passed, 1 warning in 36.34s` (432 → 436, the four above). No new warnings. |

**The tests were verified to fail without the fix**, not merely to pass with it:
with `artifact_import_conflicts.py` stashed back to the four-kind map, the file
runs `4 failed, 13 passed` — exactly the four new ones. Measured live before the
first edit, reproducing `ESC-065`'s own numbers, and again after:

```
kinds known to detect_conflicts: ['action', 'agent', 'index', 'pipeline', 'skill', 'template']
index  -> [{'kind': 'index',  'id': '...', 'conflicts': False}]
action -> [{'kind': 'action', 'id': '...', 'conflicts': False}]
workflow -> unrecognized artifact kind 'workflow' -- expected one of [... all six ...]
```

### Scope-internal judgement calls

- **No `MEMORY.md` entry.** `T04`'s 2026-10-16 entry ("Adding an artifact kind
  means six files, not five") already states the rule, the whole-bundle
  consequence, the `Index`-since-2026-09-06 history *and* "a new kind's import
  test must drive `commit_import`, not `_deploy_one`". This task is that entry
  being acted on, not a new lesson, and `CLAUDE.md` forbids trivial or duplicate
  entries. Nothing was added and the existing entry was left as written — it is
  still true as a forward rule for the `workflow` kind.
- **The new tests needed the install in memory.** `preview_import`/
  `commit_import` compose six Managers, the Hermes client and the Sections
  store, and `commit_import` really deploys. The `in_memory_install` fixture
  pins all of them, so the tests measure the gate rather than whatever is
  installed on the machine running them, and the commit test deploys into
  dictionaries. Same monkeypatch-the-data-layer style this file's existing
  `action_store`/`closure_sources` fixtures already use.
- **Observed, not fixed here (left in `ESC-065`'s resolution for `US-04`):**
  `Implementation/Architecture/architecture.md` §*Adding a Kind — the Measured
  Touch Points* still lists five files and folds conflict detection into its
  `artifact_import.py` bullet, so it does not name `artifact_import_conflicts.py`
  as a touch point of its own. That file is not in this task's `## Files to
  Modify`, and `MEMORY.md` carries the rule in stronger form, so it was left
  untouched rather than improvised into scope.
