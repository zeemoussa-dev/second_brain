---
id: REQ-SB-95-US-01-T01
title: Operator Profile entity + singleton Manager + data access, with the mirrored own-address read
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (scope-internal judgement calls, spot-check only — nothing is blocked): four shape decisions inside this task's own files, logged in full in the Implementation Log — (1) the Manager reads `settings.self_email` directly, as the task's own Context instructed; (2) `save()` takes a payload mapping and DROPS every key the Profile does not own rather than refusing it; (3) a team entry with a blank email, and a blank other-address, are dropped rather than stored empty; (4) no `created_at`/`updated_at` on the record, unlike Action/Index. No ESCALATIONS entry, no ADR touched, no new dependency, no file outside the list."
phase: P2
depends_on: []
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-01-T01 — Operator Profile Entity + Singleton Manager + Data Access

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make the Operator Profile a real, stored **singleton**: the entity, the one
Manager that is the sole gateway onto it, the raw file I/O over
`<DATA_PATH>/data/Operator/Profile.json`, and the read-only **mirror** of the
operator's own address from the existing `SELF_EMAIL` setting.

---

## Starting State → End State

**Before / Inputs:**

- Nothing stores who the operator is or who is on their team.
- `app/business/core/index/index_manager.py` + `app/data_access/indexes.py` are
  the Manager/data-access shape to mirror; `data_access/indexes.py` builds its
  paths as `settings.second_brain_data_path.joinpath("data", "Indexes")` and
  exposes read/write/delete with **zero** business interpretation (read
  directly before writing — it is the precedent, not a remembered shape).
- `self_email` is a live System setting: `app/business/system_settings.py`
  `_FIELDS["self_email"]` (label "Your Email Address", `env_key: SELF_EMAIL`,
  `_check_email` validation), present in `app/config.py`'s
  `REQUIRED_FOR_STARTUP`, with the live value on `settings.self_email`.

**After / Outputs:**

- `app/business/core/operator/operator_profile.py` — the `OperatorProfile`
  entity: the operator's `name`, their **other** mail addresses, `timezone`,
  and `team` as `email` + `role` entries **and nothing else about a person**.
- `app/business/core/operator/operator_profile_manager.py` — the sole gateway,
  a **singleton** Manager: `get()` / `save()` only. No `get_all`, no `create`,
  no `delete`, no id namespace, no list.
- `app/data_access/operator_profile.py` — raw I/O only over
  `settings.second_brain_data_path / "data" / "Operator" / "Profile.json"`:
  read, write, and "does it exist", with no defaults applied and no shape
  validated.
- `get()` on an install that has never saved returns an honest **unconfigured**
  result (not an invented empty profile that looks configured) — `T02` needs to
  tell those two apart to satisfy AC-05.
- `get()` additionally returns the operator's own address **mirrored** from the
  `SELF_EMAIL` setting, flagged as read-only/not-owned. `save()` never persists
  it and never writes it anywhere.

---

## Files to Modify

- `src/backend/app/business/core/operator/__init__.py` (new)
- `src/backend/app/business/core/operator/operator_profile.py` (new)
- `src/backend/app/business/core/operator/operator_profile_manager.py` (new)
- `src/backend/app/data_access/operator_profile.py` (new)
- `src/backend/tests/test_operator_profile.py` (new — this task's automated tests)

---

## Constraints

- Inherits from parent story.
- **Layering (`ADR-003`):** the Manager understands the `OperatorProfile`
  entity; `data_access/` understands files only. No path building or JSON
  parsing in the Manager, no defaulting or validation in `data_access/`.
- **Singleton, not a catalogue.** If this task produces anything with an id, a
  list or a delete, it is wrong.
- **Membership, not copies.** A team entry is exactly `email` + `role`. Do not
  add a name, title, avatar or description field "for later" — AC-03 is
  satisfied by *not storing* anything else.
- **The own address is read, never written** (`ADR-038`). Read the live
  `settings.self_email`; do not copy it into `Profile.json`, do not write it to
  any `.env`, and do not call `setup_wizard.sync_settings_to_hermes(...)`.
- **Out of this story's blast radius entirely — do not open these files:**
  `app/business/system_settings.py`, `app/config.py`,
  `app/business/setup_wizard.py`, `app/api/setup_router.py`, and the deployed
  payload capture scripts. `self_email` stays a startup-required setting.
- Instance data, never the repository — the store is under
  `settings.second_brain_data_path`, not `src/`.

---

## Tests

**Automated tests** — `src/backend/tests/test_operator_profile.py`, run with
`pytest tests/test_operator_profile.py` from `src/backend`. Monkeypatch
`settings.second_brain_data_path` to a tmp dir the way
`tests/test_index_data_path.py` already does, so no real data path is touched.

1. `[REQ-SB-95-US-01-AC-01]` Save a profile with a name, two other addresses, a
   timezone and three team entries; assert the file written is exactly
   `<second_brain_data_path>/data/Operator/Profile.json` (assert on the
   resolved `Path`) and that `get()` returns the same name, the same addresses
   in order, the same timezone and the same three team entries.
2. `[REQ-SB-95-US-01-AC-01]` Assert the Manager's public surface is a singleton:
   it exposes `get`/`save` and exposes **no** `get_all`, `create`, `delete` or
   id parameter (assert on `dir()`/signatures), and that a second `save()`
   replaces the one record rather than producing a second file anywhere under
   `data/Operator/`.
3. `[REQ-SB-95-US-01-AC-03]` Save a team entry and assert the persisted JSON for
   that entry has exactly the keys `email` and `role` — no name, no title, no
   description — and that `get()` round-trips exactly those two.
4. `[REQ-SB-95-US-01-AC-03]` Assert the stored email is returned unchanged and
   is usable as the lookup key into the app's existing person-note lookup
   (compose the real `find_person_note_path`-style lookup the way
   `tests/test_find_person_note_path.py` does, against a tmp vault holding a
   Person note filenamed by that email).
5. `[REQ-SB-95-US-01-AC-04]` With `settings.self_email` monkeypatched to a known
   value, assert `get()` returns that value as the operator's own address,
   marked read-only/not-owned.
6. `[REQ-SB-95-US-01-AC-04]` Save a profile (including a payload that tries to
   set the own address) and assert the written `Profile.json` contains **no**
   copy of the `SELF_EMAIL` value anywhere in its bytes.
7. `[REQ-SB-95-US-01-AC-04]` Spy on `app.business.setup_wizard` — assert
   `save()` never calls `sync_settings_to_hermes`; and assert
   `"self_email" in app.config.REQUIRED_FOR_STARTUP` and
   `"self_email" in system_settings._FIELDS` still hold after this task
   (the regression clause that replaces the dropped boot-path scenario).
8. `[REQ-SB-95-US-01-AC-04]` Change the monkeypatched `settings.self_email` and
   assert the next `get()` reflects the new value with no save in between.

**Manual verification:** none required — this task has no screen.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Singleton entity + Manager + raw data access over `data/Operator/Profile.json`
- [x] A team entry holds `email` + `role` and nothing else
- [x] Unconfigured is distinguishable from "configured but empty"
- [x] The own address is mirrored from `SELF_EMAIL`, never stored and never written
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint —
      **nothing new to record.** The one rule this task could have produced (the
      Profile mirrors `SELF_EMAIL` and never writes it) is already `ADR-038`, and
      `MEMORY.md` is 86 KB against its own rule 1's 40 KB budget, which forbids
      appending while over budget. Nothing was appended and nothing is owed.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Publishing anything into agent context — `T02`.
- The HTTP routes — `T03`.
- Export behaviour — `T04`.
- Any screen — `T05`.
- Editing, moving or retiring the `SELF_EMAIL` setting in any way (`ADR-038`).

---

## Context / Notes

`architecture.md` → §An Agent Acts From a Published Catalogue (`REQ-SB-95`) →
**§Operator Profile — the Singleton Record, and the Address It Mirrors** is
authoritative. `ADR-032` (singleton, store location, membership-not-copies,
export exclusion) and **`ADR-038`** (the setting stays; the Profile mirrors it)
bound the fields. `ADR-036`'s `SELF_EMAIL` retirement is **superseded** — if a
sample or an older note anywhere implies the Profile owns that address, the
note is stale and `ADR-038` wins.

One judgement call worth making consciously: `Learnings.md` records a standing
correction that "reading entity data values out of `settings` is the same class
of I/O as reading the JSON store" (the `ProviderManager` layering fix). Here the
mirrored value is a *config* setting that the architecture explicitly tells this
Manager to read, not entity data in a store. Read it the simplest honest way and
log the call in the Implementation Log rather than restructuring `config`.

---

## Implementation Log

**2026-10-18 — built and verified. `status: Done`, `gate: flagged` (trigger-1
only, spot-check — nothing is blocked and `T02`/`T03` are unblocked).**

### What was built — five new files, nothing else touched

| File | Holds |
|---|---|
| `src/backend/app/business/core/operator/__init__.py` | the package note: singleton, membership-not-copies, the mirrored address |
| `src/backend/app/business/core/operator/operator_profile.py` | `OperatorProfile`, `TeamMember`, `MirroredOwnAddress` |
| `src/backend/app/business/core/operator/operator_profile_manager.py` | `OperatorProfileManager` — `get()` / `save()` and nothing else public |
| `src/backend/app/data_access/operator_profile.py` | `profile_path()` / `profile_exists()` / `read_profile_json()` / `write_profile_json()` |
| `src/backend/tests/test_operator_profile.py` | 9 tests — 8 AC-tagged, 1 supporting |

Nothing imports these yet, which is correct for this task: `T03` registers the
router and `T02` wires publication. No switch-on site was needed for this task's
own tests to run, so nothing outside the list was opened for writing.

**Layering (`ADR-003` + the operator's 2026-08-28 reversal), checked both ways:**
`operator_profile_manager.py` contains zero path building and zero `json` calls —
it imports no `json`, no `pathlib`, and reaches disk only through
`data_access/operator_profile.py`. `data_access/operator_profile.py` applies no
default, validates no shape, and has no notion of "configured" — it reports an
absent file as absent (`profile_exists()`), raises `FileNotFoundError` on a read
of a store that was never written, and lets a malformed file raise
`json.JSONDecodeError`. The precedent read before designing was
`data_access/actions.py` + `business/core/actions/action_manager.py`, plus
`data_access/vault_index_config.py` — the closer shape, being the other
single-file store.

### Verification — automated mode, `pytest` from `src/backend`

Run: `.venv/Scripts/python.exe -m pytest tests/test_operator_profile.py -q` →
**9 passed in 2.23s**.

- **Suite baseline, measured BEFORE any file was written: `634 passed, 0 failed,
  39.77s`.** The three known order-dependent tests
  (`test_health_check.py::test_health_reports_the_commit_the_running_code_was_loaded_from`,
  `test_marketplace_source.py`,
  `test_marketplace.py::test_install_repairs_a_plugin_left_with_only_its_bytecode_cache`)
  all PASSED in that baseline, so the baseline is clean.
- **Suite after: `642 passed, 1 failed, 41.63s`** — 643 total = 634 + this task's
  9, so every one of this task's tests is accounted for and no previously-passing
  test of mine broke.
- **The one failure is NOT this task's and is NOT in this task's files.**
  `tests/test_action_artifact_kind.py::test_the_gate_accepts_every_kind_the_export_can_emit`
  fails on `artifact_export._PAYLOAD_FOLDER` now carrying `workflow` while
  `artifact_import_conflicts._MANAGER_BY_KIND` does not. It reproduces **in
  isolation** (`pytest tests/test_action_artifact_kind.py::... -q` → 1 failed,
  with this task's files never imported), and `git status` shows five
  `business/logic/artifact_*.py` files modified in the shared working tree by
  another live session (the `REQ-SB-95-US-04` Workflow export work). It passed in
  this session's own baseline 40 minutes earlier, so it flipped between the two
  runs. Reported, not fixed: fixing it would edit files outside this task's list.

**No test reads or writes the operator's real store, and that is proved rather
than assumed.** The autouse `empty_install` fixture points
`settings.second_brain_data_path` at a path inside pytest's tmp dir that **does
not exist when the test starts** (asserted in the fixture itself), so every test
runs against a genuinely empty install. Confirmed afterwards against the real
configured data path: it exists, and `data/Operator` does **not** — the suite
created nothing there. `settings.self_email` is monkeypatched to a fictitious
value, so nothing here read the operator's real address either. Every fixture
value is obviously fake (`operator@example.test`, `Robin Fictional`,
`blue/green/amber@example.test`).

### Each locked AC, with what was observed

**`REQ-SB-95-US-01-AC-01` — singleton record, one store, no catalogue surface.
PASS.** Two tagged tests.

- `test_the_profile_is_one_record_at_one_path_and_reads_back_as_saved` — saved a
  profile with a name, two other addresses, a timezone and three team entries.
  Asserted on the **resolved `Path`** that the file written is exactly
  `<second_brain_data_path>/data/Operator/Profile.json`, and that both the
  `save()` return and a fresh `OperatorProfileManager().get()` give back the same
  name, the same two addresses **in the same order**, the same timezone and the
  same three `(email, role)` pairs in order. Observed: pass.
- `test_the_manager_is_a_singleton_and_a_second_save_replaces_the_one_record` —
  asserted the Manager's public surface is **exactly** `{"get", "save"}` (every
  non-underscore name on the class), so `get_all`, `create` and `delete` are
  absent by assertion and not merely by reading; asserted neither signature takes
  `id`/`profile_id`/`operator_id`. Then saved twice and walked
  `data/Operator/` with `rglob("*")`: observed exactly one file, `Profile.json`,
  carrying the second save's name. Observed: pass.

**`REQ-SB-95-US-01-AC-03` — membership, not copies. PASS.** Two tagged tests.

- `test_a_team_entry_holds_an_email_and_a_role_and_nothing_else` — saved a team
  entry whose payload also carried `name`, `title` and `description`. Read the
  **persisted JSON** back: the stored entry's key set is exactly
  `{"email", "role"}` and its value is exactly
  `{"email": "blue@example.test", "role": "Engineer"}` — the three extra fields
  are not in the file. `get()` round-trips exactly those two. Observed: pass.
  Note the assertion is against the **literal** `{"email", "role"}`, not against
  a constant the production code also reads, so it is not tautological.
- `test_the_stored_email_is_what_reaches_the_real_person_note` — built a tmp
  vault holding a Person note filenamed `blue@example.test.md` under
  `Work/Customers/Acme/People/`, composed the real
  `vault_writer.find_person_note_path(...)` the way
  `tests/test_find_person_note_path.py` does (monkeypatching
  `vault_writer.settings`), and passed it the email **read back out of the saved
  Profile**, not a literal. Observed: the real lookup returned that exact note
  path — the stored email is unchanged and is usable as the join key.

**`REQ-SB-95-US-01-AC-04` — the own address is mirrored, never stored, never
written. PASS.** Four tagged tests.

- `test_the_own_address_is_mirrored_from_the_setting_and_marked_read_only` —
  with `settings.self_email` monkeypatched to `operator@example.test`, `get()`
  returned `own_address.email == "operator@example.test"` with
  `read_only is True`, `setting_key == "SELF_EMAIL"` and
  `edited_at == "Settings > System"`. Observed: pass — read-only/not-owned is
  carried on the value itself, not left for a caller to remember.
- `test_no_copy_of_the_own_address_is_ever_written` — saved a payload that
  deliberately tries three ways to set the own address (`own_address`,
  `self_email`, `email`). Read the written `Profile.json` as **bytes**: the
  `SELF_EMAIL` value does not appear anywhere in them, nor do the keys
  `self_email`/`own_address`, and the record's top-level key set is exactly
  `{"name", "other_email_addresses", "timezone", "team"}`. Observed: pass.
- `test_saving_the_profile_leaves_the_self_email_setting_entirely_alone` — spied
  on `app.business.setup_wizard.sync_settings_to_hermes` with a recorder and
  saved: **zero calls**. Because a module-attribute spy cannot see a
  `from ... import` binding, the test additionally pins the absence of any
  `import` line naming `setup_wizard` in both new modules. The regression clause
  holds: `"self_email" in app.config.REQUIRED_FOR_STARTUP`,
  `"self_email" in system_settings._FIELDS`, and that field's `env_key` is still
  `"SELF_EMAIL"`. Observed: pass. Neither file was edited — they were imported
  read-only by the test, which the task's own `## Tests` step 7 requires.
- `test_changing_the_setting_changes_what_the_profile_returns_with_no_save` —
  saved once, re-pointed `settings.self_email` at `moved@example.test`, then
  called `get()` again with **no save in between**: the new value came back, and
  the stored record was byte-unchanged (its `name` still reads as saved).
  Observed: pass.

**Supporting, untagged:**
`test_an_install_that_never_saved_reads_back_as_unconfigured` — on an install
that has never saved, `get()` returns `is_configured=False` with empty name,
empty address list, empty timezone and empty team, rather than an invented empty
record that looks configured. Not tagged to an AC because the AC it serves
(`AC-05`) belongs to `T02`; `T02` needs exactly this flag to tell the two states
apart, so it is pinned here where the flag is produced.

**Manual verification:** none required — this task has no screen, as the task's
own `## Tests` block states.

### Scope-internal judgement calls (the gate flag — spot-check, nothing blocked)

1. **The Manager reads `settings.self_email` directly.** The task's own Context
   asked for this call to be made consciously and logged rather than resolved by
   restructuring `config`. `Learnings.md`'s standing correction (the
   `ProviderManager` layering fix — "reading entity data values out of `settings`
   is the same class of I/O as reading the JSON store") is about **entity data**
   that belongs in a store. This value is a *config setting* that `ADR-038` makes
   the single source of truth and that the architecture explicitly tells this
   Manager to read; routing it through `data_access/operator_profile.py` would
   have made that module know about a second store it has no business knowing,
   and inventing a `data_access/settings.py` is a change well outside this task.
   `_mirrored_own_address()` reads it at call time, never caches it — which is
   what makes the no-save-in-between test above true.
2. **`save()` takes a payload mapping and silently drops every key the Profile
   does not own**, rather than refusing an unexpected key. `_owned_record()`
   builds the stored dict from exactly four fields, so "`Profile.json` holds no
   copy of the own address" and "a team entry holds email+role and nothing else"
   are properties of the file itself, not of each caller having been validated.
   Refusing instead would have meant `T03`'s router and any future importer each
   re-deriving the rule. The cost: a caller that misspells a field gets a silent
   no-op on it rather than an error.
3. **A team entry with a blank email is dropped, and blank other-addresses are
   dropped**; non-blank addresses keep their given order exactly. An entry with
   no email is membership in nothing — the email IS the join key onto the Person
   note (AC-03), so it could never resolve. Order is preserved because the list
   is one the operator wrote.
4. **No `created_at` / `updated_at` on the record**, unlike `Action.json` and
   `Index.json`. Nothing in this story's ACs reads them, the other single-file
   store (`index_config.json`) has none either, and adding fields "for later" is
   the thing this task's Constraints warn against. If `T05`'s page wants a "last
   saved", that is a new field decided then.

### Notes for `T02` and `T03`

- `OperatorProfileManager().get()` is the one read. `is_configured` is the flag
  `T02`'s `AC-05` block turns on; `own_address` is already composed into the same
  object, so publication needs no second read of the setting.
- `save(payload)` returns the profile exactly as `get()` would, so `T03`'s `PUT`
  can return its result directly.
- **This task fires no publication.** `save()` deliberately does not call into
  `AgentManager` — `T02` owns adding that trigger, and it will be adding it to a
  Manager that currently has no `agents` import at all.
