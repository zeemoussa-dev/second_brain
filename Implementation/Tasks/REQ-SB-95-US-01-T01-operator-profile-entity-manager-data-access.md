---
id: REQ-SB-95-US-01-T01
title: Operator Profile entity + singleton Manager + data access, with the mirrored own-address read
parent_story: REQ-SB-95-US-01
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

- [ ] Singleton entity + Manager + raw data access over `data/Operator/Profile.json`
- [ ] A team entry holds `email` + `role` and nothing else
- [ ] Unconfigured is distinguishable from "configured but empty"
- [ ] The own address is mirrored from `SELF_EMAIL`, never stored and never written
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder.)_
