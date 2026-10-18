---
id: REQ-SB-95-US-05-T02
title: plugin_api.register_tag_namespace(namespace, entries) — the callable seam, and the single FRAMEWORK_API bump
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Blocked
gate: flagged
gate_reason: "AC-08's third clause is unmet and is not a coder's to take alone (`ESC-079`): `register_action` is present, so `ADR-037` assigns `REQ-SB-95`'s single `FRAMEWORK_API` bump here — but it is 11 -> 12, not 7 -> 8; `REVIEW-QUEUE.md` still carries choosing the sitting as the operator's open decision; the backend is running, so the bump refuses every installed plugin on save; and the repair (republishing `src/marketplace/*`) is outside this task's scope. The capability itself is built, tested and committed, and the first two clauses of AC-08 are verified."
phase: P2
depends_on: []
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-05-T02 — Registering a Tag Namespace

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give a plugin one way to say "I own the `<prefix>/` tag namespace, and here is
the function to ask for my current entries" — a callable asked at resolution
time, never a list captured at load time — and handle the single
`FRAMEWORK_API` bump that all of `REQ-SB-95` shares.

---

## Starting State → End State

**Before / Inputs:**

- `app/plugin_api.py`: `FRAMEWORK_API = 7`, and `PluginApi` is one instance per
  plugin carrying per-plugin collections (`routers`, `subject_enrichers`,
  `agent_matchers`, `services`, `people_folders`, `seed_data_files`) with
  `register_*` methods appending to them. `register_subject_enricher` /
  `register_agent_matcher` are the exact callable-seam precedents, and their
  `Callable[...]` type aliases are declared at module level.
- `app/business/core/plugins/plugin_manager.py` aggregates those per-plugin
  collections across `loaded_apis` in `load_all()` (e.g.
  `_plugin_agent_matchers = [m for api in loaded_apis for m in api.agent_matchers]`)
  and exposes `get_*` accessors. **Aggregation is the only place a plugin id is
  known per registration**, so cross-plugin conflict detection belongs there.
- `provide_service` is the precedent for refusing a name another plugin already
  took; `register_agent_matcher`'s docstring is the precedent for "a matcher
  that raises is skipped".
- The plugin host loads only plugins built for its **exact** `FRAMEWORK_API`
  (`MEMORY.md`, 2026-09-21), so the constant moving is what forces every
  installed plugin to be republished.
- `REQ-SB-95-US-02-T05` adds `register_action` to this same file. The two are
  the **only** `plugin_api.py` additions in `REQ-SB-95`.

**After / Outputs:**

- `PluginApi.register_tag_namespace(namespace, entries)` where
  `entries` is a **callable** returning `list[dict]` with `slug`, `name`,
  `aliases`, `domains`, `hub` and `kind`. Stored, **not invoked**, at
  registration. Declared with a module-level type alias beside
  `SubjectEnricher`/`AgentMatcher`, plain dicts out, never a framework entity
  class.
- `PluginManager` aggregates registered namespaces across loaded plugins,
  keeps the owning `plugin_id` per namespace, exposes a `get_tag_namespaces()`
  accessor, and **refuses a second registration of the same prefix naming both
  plugins**.
- **The `FRAMEWORK_API` decision, taken by reading the real file first:**
  - If `register_action` is **already present** in the real current
    `app/plugin_api.py`, this is the later of the two landings — move
    `FRAMEWORK_API` from 7 to 8 here, once, and update the module docstring's
    version narrative the way v7's own paragraph does.
  - If it is **not** present, leave `FRAMEWORK_API` at 7 and add a comment at
    the constant recording that the bump is owed by
    `REQ-SB-95-US-02` (`register_action`) as the later landing.
  - Either way the constant moves **exactly once** for all of `REQ-SB-95`
    (`ADR-037`), and the Implementation Log records which branch was taken and
    why.

---

## Files to Modify

- `src/backend/app/plugin_api.py`
- `src/backend/app/business/core/plugins/plugin_manager.py`
- `src/backend/tests/test_tag_namespace_registration.py` (new)

---

## Constraints

- Inherits from parent story.
- **A callable, never a captured list** (`ADR-037`). `Settings/Entities.md` is
  edited while the app runs, so a list captured at load time is stale by
  lunchtime, and the framework would be holding a copy of the plugin's
  business data.
- **Core names no plugin** (`ADR-022`, `ADR-023`). No `customer`, `partner` or
  `entities` string anywhere in this change.
- `kind` is an **opaque pass-through string** — never enumerated, never
  validated against a list, never mapped to a framework concept.
- **Never bump `FRAMEWORK_API` twice for `REQ-SB-95`**, and never bump it
  "to be safe". An unnecessary bump costs a republish of every installed
  plugin, on top of the seven taken this autumn.
- Do not edit `REQ-SB-95-US-02`'s task files — they belong to another story and
  are already `Ready`. The conditional read above is what makes this safe in
  either landing order; the gap in `US-02-T05`'s instructions is flagged in
  `REVIEW-QUEUE.md`.

---

## Tests

**Automated tests** — `src/backend/tests/test_tag_namespace_registration.py`,
run with `pytest tests/test_tag_namespace_registration.py` from `src/backend`;
follow `tests/test_plugin_host.py`'s existing fake-plugin technique.

1. `[REQ-SB-95-US-05-AC-08]` Register a namespace from a fake plugin with an
   `entries` callable that records every call; assert it was **not** called
   during registration/load, that the registration is attributed to the
   plugin's id, and that it IS called when entries are asked for.
2. `[REQ-SB-95-US-05-AC-08]` Call for entries twice with the callable returning
   different data each time; assert both reads see the current data — proving
   nothing was captured.
3. `[REQ-SB-95-US-05-AC-08]` Load two fake plugins registering the same
   namespace prefix; assert the second is refused and the refusal message names
   **both** plugin ids.
4. `[REQ-SB-95-US-05-AC-08]` Assert the single-bump rule holds against the real
   file: read `app/plugin_api.py`; if `register_action` is present assert
   `FRAMEWORK_API == 8`, otherwise assert `FRAMEWORK_API == 7`. (The same test
   therefore keeps passing whichever of `US-02`/`US-05` lands first, and fails
   loudly if both bumped.)
5. `[REQ-SB-95-US-05-AC-08]` Assert the facade rule: `register_tag_namespace`
   accepts and returns plain data only — no framework entity class crosses the
   seam — and that `kind` is carried through byte-identically for a value the
   framework has never seen.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-08]` With the backend running, install a throwaway
   local plugin that registers a namespace, confirm it loads and appears with
   its namespace attributed to it, then uninstall it and confirm the namespace
   is gone.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `register_tag_namespace(namespace, entries)` on the facade, per-plugin-instance
- [x] `entries` stored as a callable and invoked only at resolution time
- [x] Duplicate prefix refused, naming both plugins
- [ ] **`FRAMEWORK_API` moved exactly once for all of `REQ-SB-95`, decided by reading the real file** — the real file was read and the condition fired (`register_action` is present), but the move is 11 → 12 rather than 7 → 8, its timing is an open operator decision in `REVIEW-QUEUE.md`, and taking it refuses every installed plugin on a running backend while the republish is outside this task's scope. Owed, noted at the constant, pinned by a test: `ESC-079`. **This is what blocks the task.**
- [x] No plugin named in core; `kind` opaque
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — **not appended**: 86 KB against its own 40 KB budget, which forbids appending while over. The constraint is written in `ESC-079` and `REVIEW-QUEUE.md`.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any plugin's own namespace registration — that is `sb-plugins-entities`' work
  in its own repository (`ADR-023`, `ADR-035`).
- The resolver itself — `T03`.
- The tag-keyed index — `T01` (registration does **not** populate it).

---

## Context / Notes

`architecture.md` → **§Registering a Tag Namespace** and **§One Contract Bump
for All of `REQ-SB-95`**, plus `ADR-037`. Read the real current
`plugin_api.py` and `plugin_manager.py` before editing — the registration shape
must match what is actually there, and `plugin_api.py` is being extended
concurrently by `REQ-SB-95-US-02`.

---

## Implementation Log

**Coder, 2026-10-18 — `Ready → Blocked`. The capability is built, tested and
committed; the contract bump is not taken (`ESC-079`).**

### What was built

- `src/backend/app/plugin_api.py` — `TagNamespaceEntries` declared beside
  `SubjectEnricher`/`AgentMatcher`; `PluginApi.tag_namespaces` as a per-plugin
  collection; `register_tag_namespace(namespace, entries)` storing the callable
  and never calling it. Refusals at the facade: a namespace that is not one
  prefix (empty, bare separator, or carrying `/` or `\`), `entries` that is not
  callable (the "a list captured now" mistake fails loudly instead of silently
  going stale), and the same prefix twice from one plugin — each raises inside
  `register`, so the plugin is disabled with the reason, the established
  failure mode. `plugin_id` is stamped by the facade, `register_action`'s
  precedent: attribution a caller could supply is attribution it could forge.
- `src/backend/app/business/core/plugins/plugin_manager.py` —
  `_plugin_tag_namespaces`, keyed by prefix, rebuilt by every `load_all()` from
  the plugins that loaded, plus `get_tag_namespaces()`. Cross-plugin conflict
  detection is in `_one_owner_per_tag_namespace()` because aggregation is the
  only place two plugins' registrations meet.
- `src/backend/tests/test_tag_namespace_registration.py` — 18 tests, all
  AC-tagged `[REQ-SB-95-US-05-AC-08]`.

### `AC-08`, clause by clause — the observed outcome

`AC-08` has three clauses. **Two pass; the third is not taken, which is why this
task is `Blocked` rather than `Done`.**

1. **"`entries` is stored as a callable and invoked at resolution time, never
   called at registration time" — PASS.** Test 1 (task step 1): the fake plugin's
   `entries` writes a call record to a file beside its own backend. After
   `load_all()` the registration is present, attributed to `plugin_id`
   `"first-owner"`, `callable(...)` is True, and **the call file does not exist**
   — zero calls. Calling `registration["entries"]()` then returns the data and
   the count becomes 1. Test 2 (task step 2): two reads with the plugin's own
   registry file rewritten between them return `[AN_ENTRY]` then
   `[AN_ENTRY, ANOTHER_ENTRY]` — both reads see the registry as it is at that
   moment, which is only possible if nothing was captured. Count 2.
2. **"a second registration of the same namespace prefix is refused, naming both
   plugins" — PASS.** Test 3 (task step 3): two plugins both claim `widget`;
   `get_tag_namespaces()` returns exactly one registration, owned by
   `first-owner`, whose `entries()` really is the first plugin's; the warning
   captured by `caplog` contains `first-owner`, `late-comer` and `widget`.
3. **"`FRAMEWORK_API` … becomes 8 exactly once — in whichever of
   `register_tag_namespace` and `register_action` lands last" — NOT TAKEN.**
   See below. Test (task step 4) is written as the invariant that survives the
   open decision: the constant is the pre-`REQ-SB-95` baseline (11) or exactly
   one more (12), never two more, and while it is still 11 the file must carry
   `ESC-079`. It passes today and will pass after the bump; it fails loudly if
   anyone bumps twice.

Task step 5 (the facade rule) — **PASS**, over two tests: the registration record
holds exactly `{namespace, plugin_id, entries}` with two `str` and one callable;
each entry is a literal `dict` of `str`/`list[str]` — no framework entity class
crosses the seam; and `kind` comes back byte-identical for
`"a kind nobody enumerated :: 42/x"`, a value carrying a separator and
punctuation precisely so that anything splitting, trimming, casing or mapping it
would change a byte.

**Manual step — PASS, on a throwaway install, never the operator's.** A plugin
registering `widget` was written into a scratch App Database Folder and loaded by
the real `PluginManager`: load report `[('throwaway', 'loaded', None)]`,
`get_tag_namespaces()` `[('widget', 'throwaway', True)]`, and `entries()` asked
at that moment returned the entry including its opaque `kind`. The ownership
record was then rewritten empty and reloaded: report `[]`, namespaces `[]` — the
namespace is gone with the plugin, nothing stored to clean up. The "with the
backend running" half was done against a **real uvicorn on `127.0.0.1:8099`**
pointed at the same scratch store (never the operator's `:8001`), whose
`/system-health` reported the plugin `loaded` with `routes_prefix
/plugins/throwaway`. Noted honestly: there is **no HTTP surface for namespaces
yet** — none is in this task's scope and `get_tag_namespaces()` has no route — so
"appears with its namespace attributed to it" was observed through the real
loader and the real accessor, and only the "it loads" half through the server.

### The `FRAMEWORK_API` decision, and why it is an escalation

The conditional read fired as written: **`register_action` IS present** in the
real `app/plugin_api.py` (commit `68caf71`), so this is the later landing and
`ADR-037` assigns the single bump here. It was **not** taken, for three reasons
the task file could not see — written out in full in `ESC-079`:

- The numerals are four versions stale. The task, the architecture section and
  `ADR-037` all say 7 → 8; the constant was already **11** before this story
  began (`ADR-039`/`ADR-040`/`ADR-041`/`ADR-060` moved it 8 → 11 after `ADR-037`
  was accepted). The move owed is **11 → 12**. This part is not the blocker —
  `ADR-037`'s relation ("exactly one bump, taken by the later landing") is
  unambiguous and the numeral is just arithmetic.
- **The queue disagrees with itself, and the open half is the operator's.** The
  `REQ-SB-95-US-02-T05` item says the bump "should fire on its own" here, and its
  own **What to do** says "decide when the `FRAMEWORK_API` bump to 12 happens,
  which should be the sitting where the first plugin publishes an Action and every
  installed plugin is republished together" — re-confirmed as still open by
  today's `T06` update ("still yours"). That sitting has not happened.
- **The window is the worst available and the repair is out of scope.** The
  constant's own comment says to bump "only when ready to republish and reinstall
  every installed plugin in the same sitting"; the backend is running on
  `127.0.0.1:8001`, so the bump is live on save (the 2026-10-17 incident); and
  another session has just written `src/marketplace/entities/1.3.0/` and
  `src/marketplace/my-day/1.7.1/` declaring `framework_api: 11`. `src/marketplace/`
  is in no task's `## Files to Modify`.

What landed instead: a note at the constant recording the owed move, naming both
capabilities and `ESC-079`, plus the invariant test above — so the obligation
cannot evaporate, and the bump remains one line in one sitting.

### Judgement calls inside scope (for a spot-check, not decisions)

1. **A cross-plugin duplicate is refused by skipping and logging, not by
   disabling the second plugin.** `provide_service`'s precedent raises inside
   `register`, which disables the plugin — impossible here, because a prefix
   collision is only visible during aggregation, by which time the later plugin
   has imported, registered and had its routes mounted. First owner keeps the
   prefix: a namespace changing hands because of install order would be worse
   than one that stays put.
2. **The refusal is a log warning, not a field on the load report.** It follows
   `register_agent_matcher`'s "skipped and logged" precedent and keeps the load
   report's `reason` meaning "why this plugin is not working", which a loaded
   plugin would otherwise contradict. If the operator wants a refused namespace
   visible in System Health, that is a surface change, not this seam.
3. **`get_tag_namespaces()` returns a list of dicts, not a map.** It mirrors
   `get_actions()` and preserves install order; `T03` can key it however the
   resolver wants.
4. **A prefix may be registered with or without its trailing separator** —
   `"widget/"` and `"widget"` are the same namespace — because `ADR-037` writes
   namespaces both ways. A prefix with a separator *inside* it is refused.

### Scope and safety

Only the three listed files were written. The full backend suite was run from a
scratch CWD with `SECOND_BRAIN_DATA_PATH`/`VAULT_PATH`/`HERMES_HOME_PATH` pointed
at scratch directories before anything imported `app.config`: **595 → 618
passed**, with the non-passing set **identical** before and after (98 failed + 17
errors, the same 115 test ids, all pre-existing against an empty scratch install;
the passed count moved by more than this file's 18 because other sessions landed
tests during the run). The new test file isolates its own store explicitly —
`tests/conftest.py` sandboxes the Hermes install only — and restores
`_plugin_tag_namespaces` and `_load_report` so no temporary plugin can be seen by
a later test. No `MEMORY.md` entry was appended: the file is 86 KB against the
40 KB budget its own rule 1 sets, so the constraint this task produced is written
in `ESC-079` and `REVIEW-QUEUE.md` instead.

Commits: `c88e016` (the capability + tests), `89f470b` (the owed-bump note + its
invariant test).
