---
id: REQ-SB-95-US-01-T03
title: GET/PUT /operator/profile — the singleton's two routes
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "Optional skim, nothing blocked — five scope-internal judgement calls, chiefly the refusal shape this task's own Tests step 5 delegated to the coder (an attempt to set the own address is REFUSED 409, not accepted-and-dropped) and the first use of pydantic `extra=\"forbid\"` in `app/api/`. One MEMORY.md candidate is parked in REVIEW-QUEUE.md rather than appended: MEMORY.md is 86 KB against the 40 KB budget its own rule 1 sets, which forbids appending while over."
phase: P2
depends_on: [REQ-SB-95-US-01-T01]
created: 2026-10-16
updated: 2026-10-18
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

- [x] Exactly `GET` + `PUT /operator/profile`; no list, create, delete or id
- [x] Round-trip returns exactly what was saved
- [x] Malformed input refused with a message, nothing partially saved
- [x] The own address is read-only in the response and never written by `PUT`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

**Coder, 2026-10-18 — `Ready → Done`. Both locked ACs verified; three files
touched, exactly the three listed.**

Built: `src/backend/app/api/operator_router.py` (new), one import line + one
`include_router` line in `src/backend/app/main.py`, and
`src/backend/tests/test_operator_profile_api.py` (new, 6 AC-tagged tests).
Commit `7629e57`.

### What the write route does with an own-address field, and the byte evidence

**Decided: an explicit refusal, not a silent drop.** A payload carrying
`own_address` or `self_email` is answered `409` with the sentence

> The operator's own email address is not stored in the Operator Profile and
> cannot be set here: it is the SELF_EMAIL setting, edited on Settings >
> System. Send the Profile without it; nothing was saved.

The Manager's `save()` keeps dropping unowned keys — that is what makes the
guarantee a property of the FILE rather than of each caller's good behaviour,
and this route does not change it. But a route carries a second obligation the
Manager does not: a `200` is the client's only evidence that what it sent was
stored. Answering `200` to "set my own address to X" would be true about the
Profile and false about what the operator asked for, and the Profile page
would then redraw showing the old value with no explanation. The refusal names
`SELF_EMAIL` and *Settings > System* (read from
`operator_profile.OWN_ADDRESS_SETTING_KEY`/`OWN_ADDRESS_EDITED_AT`, not
hardcoded a second time) so the client is told where the value really lives.
Every other unowned key — `email`, anything else — is refused `422` by
`extra="forbid"` on the request model. Both refusals happen before the Manager
is called, so nothing is written on either path.

**Byte-level evidence, not response-level** (`tests/test_operator_profile_api.py::
test_a_put_that_tries_to_set_the_own_address_is_refused_and_writes_nothing`):
after a good save, `Profile.json`'s raw bytes are snapshotted; three
own-address payload shapes and one unknown-key payload are then `PUT`; the
bytes afterwards are asserted **equal to the snapshot**, to contain neither
`operator@example.test` nor `someone-else@example.test`, to contain neither
`own_address` nor `self_email`, and to parse to exactly the four owned keys.
`GET` then still reports the setting's value. Reconfirmed live over a real
socket (below): `bytes unchanged: True`, and the file contains neither address.

### Verification — automated mode, both locked ACs

Run: `pytest tests/test_operator_profile_api.py` from `src/backend` — **6
passed**. Every test runs against a `second_brain_data_path` inside pytest's
own tmp dir asserted **not to exist** when the test starts, and fills every
`REQUIRED_FOR_STARTUP` setting itself, so the file passes on an empty install
and can never reach the operator's store. All values fictitious
(`operator@example.test` / `Robin Fictional`).

- **`[REQ-SB-95-US-01-AC-01]`** — **PASS**, three tagged tests.
  - *Tests step 1 (round trip):* `PUT` with a name, two other addresses, a
    timezone and three team entries → `200`; the `PUT` body, the following
    `GET` body and the stored JSON all equal the payload exactly, with
    `is_configured: true`.
  - *Tests step 2 (no collection route):* the live route table filtered to
    `/operator` is **exactly** `{("GET", "/operator/profile"),
    ("PUT", "/operator/profile")}` — no `POST`/`DELETE`/`PATCH`, no `{id}`
    segment, no `…/profiles`.
  - *Tests step 3 (malformed team entry):* a second entry with no `email` →
    `422` carrying `loc: ["body","team",1,"email"]`; an entry smuggling
    `name`/`title` → `422` naming both by position. The stored bytes are
    byte-identical to before and `GET` still returns the previous record.
- **`[REQ-SB-95-US-01-AC-04]`** — **PASS**, three tagged tests.
  - *Tests step 4 (mirror is read-only):* with `settings.self_email`
    monkeypatched, `GET` returns `own_address` = `{email: <the setting>,
    read_only: true, setting_key: "SELF_EMAIL", edited_at: "Settings >
    System"}` — the response names its editor and offers no editable field.
  - *Tests step 5 (own address never written):* as described above.
  - Plus the ordinary save path, byte-checked: the mirrored address reaches
    the response and never the file.

**Manual step 1 `[REQ-SB-95-US-01-AC-01]` — PASS, against a disposable
install, never the operator's store.** A real uvicorn on `127.0.0.1:8123`
with `SECOND_BRAIN_DATA_PATH`, `VAULT_PATH` and `HERMES_HOME_PATH` all pointed
at scratch directories and `SELF_EMAIL=operator@example.test`. `PUT` then
`GET` with PowerShell returned identical bodies, carrying the mirrored
`own_address` flagged `read_only` and naming *Settings > System*; the real
file appeared at `<DATA_PATH>/data/Operator/Profile.json` holding exactly the
four owned keys and no address of the operator's own. The refusals were
exercised over the same real socket: own-address `409` (twice), malformed team
entry `422` (twice), file bytes unchanged. Confirmed afterwards that the
operator's real data path has no `data/Operator` directory at all.

**Suite:** baseline measured **664 passed / 2 failed** before any edit; after,
**670 passed / 2 failed** (`+6`, mine). The two failures —
`test_workflow_action_integrity.py::test_validating_a_save_reads_the_catalogue_once_and_a_delete_scans_workflows_once`
and `test_workflow_artifact_kind.py::test_reading_a_workflow_costs_exactly_one_read`
— are **not mine**: they were already failing in the pre-edit baseline and
belong to the in-flight `REQ-SB-95-US-04-T06` edits to
`business/core/workflows/workflow_manager.py` in this shared checkout. None of
the four known order-dependent tests failed. The brief's 666-passed baseline
is the same 666 collected tests; 2 of them are currently red for that reason.

### Scope-internal judgement calls — all five, for human spot-check

1. **The refusal shape (the one the task delegated).** `409` + sentence for
   the own address; `422` + field name for everything else. `409` because
   FastAPI owns `422` for its own validation errors, whose `detail` is a LIST
   of error objects — a hand-written refusal under the same code would force
   the Profile page to tell two `detail` shapes apart before it could render
   anything. `409` is what `sections_router`/`blueprints_router`/
   `actions_router`/`workflows_router` already return for a refused write.
2. **`own_address` and `self_email` are declared on the request model purely
   so they can be refused BY NAME.** Left to `extra="forbid"` they would come
   back as a generic "extra inputs are not permitted" — and the payload most
   likely to carry them in good faith is a `GET` body posted straight back,
   which deserves to be told where the address actually lives.
3. **First use of `extra="forbid"` in `app/api/`** (no other router uses it —
   checked). It is load-bearing here, not stylistic: it is the only thing that
   makes "a team entry carrying extra person fields is refused, never silently
   coerced" true, which the task's End State requires and the Manager
   deliberately does not do (it drops).
4. **`PUT` replaces; an omitted field means empty, never "leave it".** No
   partial-update convention, unlike `ActionUpdateBody`/`WorkflowUpdateBody`:
   this is one small record edited whole on one page, and a merge could not
   tell "the operator removed a colleague" from "the client only sent what it
   changed". `role` stays optional — a colleague whose role has not been
   written down is a real state.
5. **The route-table assertion reads `app_route_table()`, not `app.routes`.**
   Measured first: a flat read of `app.routes` returns an **empty** set for
   `/operator` on this installed FastAPI, which keeps an included router as a
   lazy placeholder — the test would have passed while asserting nothing. The
   shared walker in `action_manager.py` already handles it and is the same
   table the Action gate resolves against.

### MEMORY.md

Not appended. `MEMORY.md` is 86 KB against the 40 KB budget its own rule 1
sets, which forbids appending while over. One candidate — *a route that cannot
store a mirrored field refuses it and names the surface that owns it, rather
than dropping it behind a `200`* — is recorded in `REVIEW-QUEUE.md` instead,
with that reason.

### Out of scope, untouched, confirmed

No soul marker block (`T02`), no export guard (`T04`), no settings page
(`T05`), and nothing re-triggers publication here — the save-side trigger
belongs to the Manager. `system_settings.py`, `config.py`, `setup_wizard.py`,
`setup_router.py` and `SettingsSystemPage.tsx` were not touched (`ADR-038`).
Nothing outside `## Files to Modify` was edited, so no `ESCALATIONS.md` entry
was written.
