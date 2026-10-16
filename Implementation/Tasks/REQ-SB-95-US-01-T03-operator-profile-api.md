---
id: REQ-SB-95-US-01-T03
title: GET/PUT /operator/profile — the singleton's two routes
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-01-T01]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-01-T03 — The Operator Profile API

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Expose the singleton over HTTP as exactly two routes — read it, replace it —
so the Settings page in `T05` has a real back end and the record keeps having
no id, no list and no delete.

---

## Starting State → End State

**Before / Inputs:**

- `T01`'s `OperatorProfileManager` with `get()` / `save()`.
- `app/api/index_router.py` and `app/api/settings_system_router.py` are the
  flat, single-purpose router convention to follow (read one directly before
  writing), and `app/main.py` is where routers are included.

**After / Outputs:**

- `app/api/operator_router.py` with exactly:
  - `GET /operator/profile` — the stored facts, plus the **mirrored** own
    address marked read-only/not-owned, plus whether a Profile has ever been
    saved.
  - `PUT /operator/profile` — replaces the one record and returns the saved
    state. No `POST` create, no `DELETE`, no id in any path.
- The router is included in `app/main.py` alongside the existing ones.
- A malformed team entry (missing `email`, or carrying extra person fields) is
  refused with a message naming what is wrong — never silently coerced, never
  partially saved.
- The response never offers the own address as an editable field; it names
  Settings → System as where that one is edited.

---

## Files to Modify

- `src/backend/app/api/operator_router.py` (new)
- `src/backend/app/main.py` (include the router — nothing else)
- `src/backend/tests/test_operator_profile_api.py` (new)

---

## Constraints

- Inherits from parent story.
- **Two routes, no more.** Anything resembling a collection endpoint
  contradicts `ADR-032`'s "configuration, not a catalogue".
- The router holds no business logic — it calls the Manager, the way the
  existing routers do (`ADR-003`).
- **`PUT` must not write the operator's own address anywhere** (`ADR-038`): an
  inbound payload that tries to set it is ignored or refused, never persisted.
- `app/api/settings_system_router.py` and `app/api/setup_router.py` are **not**
  touched.

---

## Tests

**Automated tests** — `src/backend/tests/test_operator_profile_api.py`, run with
`pytest tests/test_operator_profile_api.py` from `src/backend`. Drive the real
app with `httpx.ASGITransport(app=app)` / `TestClient` the way
`tests/test_blueprints_api.py` already does, with
`settings.second_brain_data_path` monkeypatched to a tmp dir.

1. `[REQ-SB-95-US-01-AC-01]` `PUT /operator/profile` with a name, other
   addresses, a timezone and three team entries → `200`; then
   `GET /operator/profile` returns exactly what was sent (the "reopening the
   page shows exactly what was saved" clause, proven at the API layer).
2. `[REQ-SB-95-US-01-AC-01]` Assert the app's route table carries no collection
   route for this resource — no `POST /operator/profiles`, no path with an id
   segment, no `DELETE` (assert over `app.routes`).
3. `[REQ-SB-95-US-01-AC-01]` `PUT` a malformed team entry (no `email`); assert a
   4xx naming the problem and that `GET` still returns the previous record
   unchanged.
4. `[REQ-SB-95-US-01-AC-04]` With `settings.self_email` monkeypatched, assert
   `GET` returns that address marked read-only/not-owned and names Settings →
   System as its editor.
5. `[REQ-SB-95-US-01-AC-04]` `PUT` a payload that tries to set the own address
   to something else; assert `200`/4xx per the chosen refusal shape, that `GET`
   still reports the **setting's** value, and that `Profile.json` contains no
   copy of either address.

**Manual verification steps:**

1. `[REQ-SB-95-US-01-AC-01]` With the backend running, `PUT` then `GET`
   `/operator/profile` with PowerShell and confirm the round trip, then confirm
   the real file appeared at `<DATA_PATH>/data/Operator/Profile.json`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Exactly `GET` + `PUT /operator/profile`; no list, create, delete or id
- [ ] Round-trip returns exactly what was saved
- [ ] Malformed input refused with a message, nothing partially saved
- [ ] The own address is read-only in the response and never written by `PUT`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Publication into agent context — `T02` (the save-side trigger lives in the
  Manager, so this router gets it for free; do not re-trigger it here).
- Export behaviour — `T04`.
- The screen — `T05`.

---

## Context / Notes

`architecture.md` → **§Operator Profile — the Singleton Record, and the Address
It Mirrors**. The singleton shape is the whole point: `ADR-032` chose
"configuration, not a catalogue" deliberately, and a collection-shaped API is
how that decision would quietly erode.

---

## Implementation Log

_(Filled in by the coder.)_
