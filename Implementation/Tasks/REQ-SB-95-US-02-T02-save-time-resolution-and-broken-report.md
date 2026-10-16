---
id: REQ-SB-95-US-02-T02
title: Save-time implementation resolution for skill / http / ui, plus the broken-entry read status
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T01]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T02 — Save-Time Implementation Resolution + Broken-Entry Status

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Refuse to save an Action whose one implementation does not resolve on this
install, naming what did not resolve — and report, on every read, which
catalogued Actions have since become broken.

---

## Starting State → End State

**Before / Inputs:**

- `T01`'s `ActionManager` saves any cardinality-valid Action without checking
  that the thing it names exists.
- `SkillManager.deploy()` is the in-repo precedent for refusing rather than
  shipping something that only fails when it runs; `SkillManager`'s deployment
  report (`current` / `stale` / `missing` / `modified` per skill+profile) is the
  shape to mirror for the read-side status.

**After / Outputs:**

- `ActionManager.create()` / `update()` resolve the named implementation before
  anything is written:
  - `skill` → resolves against `SkillManager` as **deployed**, not merely
    catalogued;
  - `http` → resolves against the running app's own route table (which already
    includes plugin routes mounted under `/plugins/<plugin_id>/`);
  - `ui` → resolves against the registered front-end feature key.
- A non-resolving implementation is refused with a message naming exactly what
  did not resolve, and **nothing is written or changed on disk**.
- `ActionManager` exposes a read-side resolution status per Action
  (`resolves` | `broken`, with what no longer resolves), computed on read, never
  cached — `business/logic/`'s own no-caching convention.

---

## Files to Modify

- `src/backend/app/business/core/actions/action_manager.py`
- `src/backend/app/business/core/actions/action.py` (the resolution-status shape, if it needs a type)
- `src/backend/tests/test_action_resolution.py` (new)

---

## Constraints

- Inherits from parent story.
- **Resolution happens at save, not at call** (`ADR-032`). A call-time-only
  check does not satisfy `AC-02`. (`US-03`'s gate re-checks at call time as
  well, but that is a second line, not this one.)
- The resolution status is **computed on read, never cached** and never written
  into `Action.json`.
- No change to `SkillManager` — this task reads it, it does not extend it.
- The route-table lookup must read the live app's routes, not a hand-maintained
  list of paths.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_resolution.py`, run with
`pytest tests/test_action_resolution.py` from `src/backend`. Monkeypatch the
data-access writes as in `T01`, and monkeypatch `SkillManager`'s deployed-skill
lookup to control what resolves.

1. `[REQ-SB-95-US-02-AC-02]` Save an Action naming a `skill` implementation that
   is catalogued but **not deployed**; assert the refusal message names that
   skill id and that `write_action_json` was never called.
2. `[REQ-SB-95-US-02-AC-02]` Save an Action naming an `http` implementation
   whose path is not in the app's route table; assert the refusal names the
   path and nothing is written.
3. `[REQ-SB-95-US-02-AC-02]` Save an Action naming a `ui` feature key that is not
   registered; assert the refusal names the key and nothing is written.
4. `[REQ-SB-95-US-02-AC-02]` Re-save the same Action with a resolvable
   implementation; assert it is written and `get_by_id()` returns it.
5. `[REQ-SB-95-US-02-AC-07]` Save an Action against a deployed Skill, then
   monkeypatch that Skill out of the deployed set; assert the read-side status
   reports that Action as `broken` naming the missing skill, that every other
   Action still reports `resolves`, and that nothing had to call the Action to
   discover it.

**Manual verification steps:**

1. `[REQ-SB-95-US-02-AC-07]` With the backend running, save an Action against a
   really-deployed Skill, undeploy that Skill, then re-read the catalogue
   through `ActionManager` in a Python shell against the real data path; confirm
   the broken status and the named cause appear without any call being made.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] All three implementation kinds resolve at save time, against real sources
- [ ] A non-resolving save is refused naming the cause, with zero disk effect
- [ ] Read-side `resolves` | `broken` status per Action, computed fresh
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The API surface that exposes the refusal and the status — `T03`.
- Showing broken state on a screen — `T06`.
- Call-time validation — `REQ-SB-95-US-03-T02`.

---

## Context / Notes

`architecture.md` → **§Action Catalogue — the Sixth Artifact Kind** names all
three resolution sources and the `SkillManager`-report shape for the read-side
status. `ADR-032` fixes save-time resolution as the decision ("so a broken
action cannot sit in the catalogue waiting to fail in front of the operator").

---

## Implementation Log

**Coder, 2026-10-16 — built, both locked ACs verified green, then BLOCKED on an
out-of-scope file (`ESC-064`).**

### What was built

- `app/business/core/actions/action_manager.py`
  - `deployed_skill_ids()` — the `skill` source. `{skill.id for skill in
    SkillManager().get_all() if skill.deployed_to}`: **deployed**, not merely
    catalogued. `SkillManager` is read, never extended (Constraint).
  - `app_route_table()` + `_collect_routes()` — the `http` source, read off the
    **live** `app.routes` (Constraint: not a hand-maintained list).
    `from app.main import app` is a deliberate in-function import: `app.main`
    imports the API layer which imports this module, so a module-level import
    would be a cycle and would invert `ADR-003`'s `api -> business` direction.
  - `UI_FEATURE_KEYS` (in `action.py`) — the `ui` source.
  - `_ResolutionSources` — gathers all three ONCE per save or per report, then
    answers `unresolved_reason(kind, spec)`; `None` means it resolves.
  - `_require_resolvable_implementation()` — cardinality first, then resolution,
    raising `ActionImplementationUnresolvedError` **before** any write. Wired
    into `create()` and `update()` in place of the bare cardinality call.
  - `resolution_report()` — `list[dict]` of
    `{action_id, implementation_kind, status, reason}`, status in
    `("resolves", "broken")`, mirroring `SkillManager.check_deployment_drift()`'s
    flat-list-of-dicts shape. Recomputed from the live sources on every call.
- `app/business/core/actions/action.py` — `RESOLUTION_STATUSES`, `UI_FEATURE_KEYS`.
- `tests/test_action_resolution.py` (new) — 9 AC-tagged tests.

`T01`'s keyed-by-kind `implementation` shape was **inherited unchanged**, as the
`REVIEW-QUEUE` spot-check asks. `action_file()` was not needed after all —
nothing here touches a path.

### Locked ACs — verification performed and observed

Run from `src/backend` as `.venv/Scripts/python.exe -m pytest`.

`pytest tests/test_action_resolution.py -q` → **`9 passed in 1.31s`**

| AC | Tagged step | Observed |
|---|---|---|
| `REQ-SB-95-US-02-AC-02` | `test_a_skill_that_is_catalogued_but_not_deployed_is_refused` | PASS — refusal names `vault-search` and "not deployed"; `stored_actions == {}` |
| `REQ-SB-95-US-02-AC-02` | `test_an_http_route_the_app_does_not_expose_is_refused` | PASS — refusal names `/vault-index/refersh`; nothing written |
| `REQ-SB-95-US-02-AC-02` | `test_the_same_path_under_the_wrong_method_is_refused` | PASS — a route is method AND path; nothing written |
| `REQ-SB-95-US-02-AC-02` | `test_a_ui_feature_key_that_is_not_registered_is_refused` | PASS — refusal names `/settings/artefacts` and "not registered"; nothing written |
| `REQ-SB-95-US-02-AC-02` | `test_resaving_the_refused_action_with_a_resolvable_implementation_succeeds` | PASS — same id saves once resolvable; `get_by_id()` returns it |
| `REQ-SB-95-US-02-AC-02` | `test_an_update_onto_an_unresolvable_implementation_changes_nothing` | PASS — stored definition byte-identical after the refusal (the "editing" half) |
| `REQ-SB-95-US-02-AC-02` | `test_the_http_route_table_is_read_off_the_live_app` | PASS — unmonkeypatched; `("POST", "/vault-index/refresh")` really is in the live table |
| `REQ-SB-95-US-02-AC-07` | `test_an_action_that_breaks_after_it_was_saved_is_reported_on_read` | PASS — the undeployed one reports `broken` naming the skill, the other two still `resolves`, no call surface exists, and no status is written into the stored definition |
| `REQ-SB-95-US-02-AC-07` | `test_the_read_side_status_is_recomputed_every_time` | PASS — the SAME manager instance flips `broken` → `resolves` when the Skill returns, so nothing is cached |

**Manual step `[REQ-SB-95-US-02-AC-07]` (backend running, real data path) — NOT
performed.** It undeploys a really-deployed Skill from a live Hermes profile on
the operator's own install to observe the broken status. Seven Skills are really
deployed here (`email-thread-capture`, `meeting-capture`, `capture-files`,
`capture-notes`, `research-kb-writer`, `vault-index`,
`summarize-and-tag-files`); undeploying one mutates live instance state this task
has no mandate to touch, and `SkillManager.undeploy()` deletes the copy from the
Hermes profile. The automated `AC-07` pair above exercises the same code path
against the same `deployed_skill_ids()` seam, and the live source is proven real
by the unmonkeypatched route-table test. Flagged here rather than silently
skipped.

### Blocker — `ESC-064`

Full suite: `.venv/Scripts/python.exe -m pytest -q` →
**`1 failed, 423 passed, 1 warning in 65.37s`** (was `415 passed` before this
task; +9 new, −1 regression).

The one failure is **not** in this task's scope:

```
FAILED tests/test_action_artifact_kind.py::test_a_saved_action_round_trips_everything_the_operator_authored
ActionImplementationUnresolvedError: this Action's skill implementation does not
resolve on this install: skill 'vault-search' is not deployed on this install
```

`T01` (`Done`) wrote that test before the save-time gate existed; it saves an
example Action against `{"skill": {"skill_id": "vault-search"}}`, and
`SkillManager().get_by_id("vault-search").deployed_to == []` on this install
(measured). The gate refuses it, correctly — refusing exactly that is `AC-02`.
`src/backend/tests/test_action_artifact_kind.py` is **not** in this task's
`## Files to Modify`, so editing it is an out-of-scope event (Pipeline.md hard
rule 5) and the build stopped instead of improvising. The fix is ~5 lines and
does not change what `AC-01` asserts — see `ESC-064` for it.

### Assumptions logged for human spot-check (scope-internal, nothing blocked)

1. **A `ui` feature key is a front-end route path**, and `UI_FEATURE_KEYS` in
   `action.py` is the registry, seeded verbatim from `src/frontend/src/App.tsx`'s
   25 declared routes. Nothing in this codebase registers front-end features and
   the backend cannot read React's route table — the front end is a separate
   build that may not be deployed beside the API — so some declaration was
   unavoidable. Route paths were chosen over an invented key vocabulary because
   they are checkable against a real file, and because `ADR-033` says a `ui` call
   returns "where the operator does it", which is this same string. The cost: the
   tuple drifts if a screen is added without updating it, and `T06` adds a screen.
   If you would rather it were a named-feature registry, or a
   `plugin_api.register_ui_feature()` seam, say so before `T03` builds the API
   over it.
2. **`import_action()` was deliberately left un-gated.** The task's End State
   names `create()`/`update()` only, and import-time resolution belongs with
   `AC-05`'s bundle machinery (`T04`), which has its own "resolves there too"
   criterion. Adding it here would have pre-empted `T04`.
3. **`update()` does not re-resolve an *omitted* implementation.** Editing a
   description must not be refused because something unrelated broke on the
   install in the meantime; that is what `resolution_report()` is for. A
   *supplied* implementation is held to both rules afresh.
4. **An http implementation with no method is treated as `GET`**, matching the
   route table's own fallback.

### Framework defect found and worked around (recorded in `MEMORY.md`)

The installed FastAPI does **not** flatten an included router into `app.routes`
— it stores a lazy `_IncludedRouter` placeholder holding the original router and
its prefix. A flat read of `app.routes` returns **4 paths** (the `/docs` family)
and nothing else; `("POST", "/vault-index/refresh")` was absent. Walking into
`route.original_router.routes`, composing `include_context.prefix` on the way
down, returns **101** (METHOD, path) pairs and finds it. Any future code that
reads this app's own route table must recurse, or it will silently see almost
nothing.

## Unblocked — 2026-10-16

`ESC-064` resolved by the operator's delegate driving this sprint. The gate this task added was **correct**: it refused an implementation naming a Skill that is catalogued but not deployed, which is precisely what `AC-02` requires. What was wrong was `tests/test_action_artifact_kind.py` (T01's file), whose fixtures named `vault-search` — catalogued, undeployed here — so a test about round-tripping had quietly become a test of the local deployment.

Fix: one autouse fixture in that file monkeypatching `deployed_skill_ids`, the same source `tests/test_action_resolution.py` already controls. **No AC-01 assertion was changed, weakened or removed** — the file asserts exactly what it asserted before. Suite restored to green: **424 passed**.

Authorising the edit rather than minting a T02a: it is five lines of test scaffolding in the file the new gate invalidated, the coder was right to refuse it as out of its own scope, and leaving the suite red would have blocked T03 and T04.
