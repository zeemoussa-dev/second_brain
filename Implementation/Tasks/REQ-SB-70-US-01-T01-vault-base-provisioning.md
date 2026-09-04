---
id: REQ-SB-70-US-01-T01
title: provision_vault_base() — idempotent Work/ base-skeleton mkdir + POST /poc/provision-vault-base
parent_story: REQ-SB-70-US-01
requirement_id: REQ-SB-70
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgment call — concurrent, pre-existing app-start capture trigger noise during real-vault verification; see Implementation Log"
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-70-US-01-T01 — Vault Base Provisioning API

## Parent Story

- Story: [[REQ-SB-70-US-01]] — `../UserStories/REQ-SB-70-US-01-vault-base-provisioning-api.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-70 *Vault Base Provisioning API — Fresh PARA/OKF Skeleton*

---

## Objective

New, idempotent `app/business/vault_provisioning.py::provision_vault_base() -> dict`
that lays down exactly the named empty `Work/` base skeleton (never a
migration — no archive, no wipe), exposed as a real `POST
/poc/provision-vault-base` endpoint in the existing `app/api/
email_poc_router.py`.

---

## Starting State → End State

**Before / Inputs:**
- No provisioning module exists. `Work/` may be empty (the operator's own
  responsibility to ensure this — out of scope here) or already partially
  provisioned by a prior real call.
- `_write_frontmatter_note`/`write_attachments` already establish this
  codebase's own idempotent-mkdir convention (`path.parent.mkdir(parents=True,
  exist_ok=True)`) — this task reuses that identical convention, not a new
  one.
- `vault_migration.py` is the closest existing module-shape precedent
  (one-off, `app/business/`, operator-triggered) — mirrored in shape, but
  this module is explicitly NOT a migration.

**After / Outputs:**
- `provision_vault_base() -> dict` idempotently creates exactly:
  `Work/Customers/`, `Work/Threads/`, `Work/Meetings/`, `Work/Resources/`,
  `Work/Archive/Opportunities/`, `Work/Archive/Customers/`,
  `Work/Archive/Resources/` — nothing else. `Work/Opportunities/`,
  `Work/Websites/`, `Work/Notes/` are never created by this function.
- `POST /poc/provision-vault-base` in `email_poc_router.py` calls it and
  returns its result dict.
- A second (or Nth) call against an already-provisioned `Work/` succeeds
  with no error and creates nothing new — a real before/after directory
  listing is identical.

---

## Files to Modify

- `src/backend/app/business/vault_provisioning.py` (new) — one public
  function, `provision_vault_base() -> dict`. Mirrors `vault_migration.py`'s
  own module docstring/shape convention, but its own module docstring must
  explicitly state this is NOT a migration (no archive, no wipe, no
  re-run-over-Outlook-history). Returns a dict reporting which of the
  named buckets were newly created vs. already present (e.g.
  `{"created": [...], "already_existed": [...]}`) — mirrors this
  codebase's own established "report what actually happened" return-shape
  convention (e.g. `ensure_person_note`'s own `created: bool`).
- `src/backend/app/api/email_poc_router.py` — add `POST
  /poc/provision-vault-base`, calling `vault_provisioning.
  provision_vault_base()` and returning its dict. No request body, no
  query parameters — a bare trigger endpoint, mirroring this router's own
  existing bare-trigger `/poc/*` endpoints (e.g. `backfill-tags`,
  `flatten-customer-folders`).

---

## Constraints

- Inherits from parent story.
- **Idempotent** — `mkdir(parents=True, exist_ok=True)` for every named
  bucket, the identical convention `_write_frontmatter_note`/
  `write_attachments` already use. A second call must never error and must
  never duplicate or alter anything already provisioned.
- **Exactly the named buckets, nothing more** — do not create
  `Work/Opportunities/`, `Work/Websites/`, `Work/Notes/`, and do not
  pre-create any individual Customer OKF directory or its `People/`/
  `files/` subshapes.
- **Empty scaffolding only** — no notes, no seed data, no placeholder files
  written into any provisioned folder.
- **Does not touch, wipe, inspect, or archive any pre-existing `Work/`
  content** — this function only creates directories that don't already
  exist; it never lists, reads, or deletes anything else under `Work/`.
- Reachable only via the real `POST /poc/provision-vault-base` endpoint —
  every verification call in this task's own `## Tests` goes through that
  endpoint, never a raw internal-function script call.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — this is a `business`-layer module composing only Python's
  standard `pathlib`/`Settings.vault_path`, no new `data_access` primitive
  needed (plain `mkdir` calls, no note-writing).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-70-US-01-AC-01]` Against a real, empty `Work/` directory (or a
   disposable scratch vault pointed at by `VAULT_PATH`), call `POST
   /poc/provision-vault-base`. Confirm the call succeeds, then take a real
   directory listing of `Work/` — expect exactly `Customers/`, `Threads/`,
   `Meetings/`, `Resources/`, `Archive/` (with `Archive/Opportunities/`,
   `Archive/Customers/`, `Archive/Resources/` as its three subfolders), and
   no other top-level or nested folder.
2. `[REQ-SB-70-US-01-AC-02]` Take a directory listing of `Work/` from step
   1 (the "before" state). Call `POST /poc/provision-vault-base` a second
   time. Confirm the call completes with no error, then take a second
   directory listing — confirm it is byte-for-byte identical to the
   "before" listing (no duplicate, renamed, or otherwise-changed folder).
3. `[REQ-SB-70-US-01-AC-03]` Using the same provisioned `Work/` from step
   1, confirm `Work/Opportunities/`, `Work/Websites/`, and `Work/Notes/` do
   NOT exist.
4. `[REQ-SB-70-US-01-AC-04]` Inspect `Work/Customers/` from step 1 —
   confirm it exists and is empty (no individual Customer OKF directory
   pre-created). Separately, confirm (by direct reading of
   `customer_hub_linking.ensure_customer_hub_note`, unmodified by this
   task) that a real Customer's own directory is still created on demand
   the first time that Customer is actually captured — this task changes
   nothing about that existing behavior.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-70-US-01-AC-01` — provisioning an empty `Work/` creates
      exactly the named base skeleton, nothing else
- [x] `REQ-SB-70-US-01-AC-02` — a second call is a safe no-op
- [x] `REQ-SB-70-US-01-AC-03` — the explicitly deferred buckets
      (`Opportunities/`, `Websites/`, `Notes/`) are confirmed absent
- [x] `REQ-SB-70-US-01-AC-04` — `Work/Customers/` exists but is empty; no
      on-demand subshape is pre-created
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiping, archiving, or inspecting any pre-existing `Work/` content.
- `Work/Opportunities/`, `Work/Websites/`, `Work/Notes/`.
- `Work/Resources/`'s own internal shape (Playbook/Competitive-Intel/
  Product-Knowledge subfolders) — only the empty bucket itself.
- Individual Customer OKF directories, or `<slug>/People/`/`<slug>/files/`
  subshapes.
- Any scheduler/autonomous-triggering wiring for this endpoint — genuinely
  one-time (but safely re-runnable), operator-triggered only.

---

## Context / Notes

`ADR-048` Decision 1 (`Implementation/Architecture/ADR.md`) and
`architecture.md`'s own "Vault Base Provisioning (`REQ-SB-70-US-01`)"
subsection are the full architectural reasoning — this task is a direct,
literal implementation of that Decision, with no open mechanism question
left. No dependency on any other story in this batch — this task is
buildable and verifiable in complete isolation.

---

## Implementation Log

**What was built:** `app/business/vault_provisioning.py` (new) —
`provision_vault_base() -> dict`, idempotent `mkdir(parents=True,
exist_ok=True)` for exactly `Work/Customers/`, `Work/Threads/`,
`Work/Meetings/`, `Work/Resources/`, `Work/Archive/{Opportunities,
Customers,Resources}/`, returning `{"created": [...],
"already_existed": [...]}` (vault-relative POSIX paths). Wired as `POST
/poc/provision-vault-base` in `app/api/email_poc_router.py`. No deviation
from the plan.

**Verification environment:** the REAL operator vault
(`VAULT_PATH=<OPERATOR_VAULT_OLD>`, from `src/backend/.env`),
via the REAL running app (`uvicorn app.main:app`, port 8000) — every call
below went through the real HTTP endpoint, never a raw internal-function
script call, per this task's own Constraint. `Work/` was confirmed
genuinely empty (`Get-ChildItem -Force -Recurse` → 0 items) immediately
before the first call — a real, not synthetic, empty-`Work/` precondition
for Scenario 1.

**Assumption/observation logged for human spot-check (scope-internal, not
a MUST-FLAG trigger):** starting the real app to reach the endpoint also
starts its own pre-existing, already-shipped, unrelated app-start capture
trigger (`app/scheduling/capture_scheduler.py::lifespan`, `ADR-005` — "an
unconditional app-start trigger... always fires once"). That trigger ran
concurrently with this task's own verification and wrote real Meeting/
People/Thread/Customer content into the same real `Work/` during this
session — this is pre-existing, disclosed, unrelated production behavior,
not something this task's own code causes or controls. `provision_vault_
base`'s own action is proven exact independent of that noise, via its own
machine-readable return dict on both calls (see AC-01/AC-02 below) — that
dict never lists anything beyond the 7 named target directories on either
call. `Work/People/` and `Work/Partners/` are pre-existing/unrelated
top-level namespaces this story never scoped in either direction (`ADR-009`
for Partners; People is `vault_writer.person_note_path`'s own existing flat
location) — outside this task's own bucket list, not something it was ever
meant to create OR exclude.

- `[REQ-SB-70-US-01-AC-01]` **PASS.** First real `POST
  /poc/provision-vault-base` call against the confirmed-empty real `Work/`
  returned `{"created": ["Work/Customers", "Work/Threads",
  "Work/Resources", "Work/Archive/Opportunities", "Work/Archive/Customers",
  "Work/Archive/Resources"], "already_existed": ["Work/Meetings"]}` —
  `Work/Meetings` was flagged `already_existed` because the concurrent
  app-start capture trigger (see above) had already created it by the time
  this call ran; the function's own idempotent-mkdir logic correctly
  detected and reported this rather than erroring. Every one of the 7
  named target directories exists after the call, confirmed by a real
  recursive listing; the function's own report is exact and matches spec
  on both created/already-existed classification.
- `[REQ-SB-70-US-01-AC-02]` **PASS.** Captured a real recursive `Work/`
  listing (146 items, includes real content from the concurrent capture
  activity — irrelevant to idempotency, which only requires before==after).
  Called `POST /poc/provision-vault-base` a second time — returned
  `{"created": [], "already_existed": [<all 7 buckets>]}`. Re-captured the
  listing (146 items). `Compare-Object` between before/after produced zero
  differences — byte-for-byte identical, no duplicate/renamed/altered
  folder.
- `[REQ-SB-70-US-01-AC-03]` **PASS.** `Test-Path` against the real vault
  confirmed `Work/Opportunities`, `Work/Websites`, `Work/Notes` all `False`
  (do not exist) after both provisioning calls.
- `[REQ-SB-70-US-01-AC-04]` **PASS.** Immediately after the first
  provisioning call, `Work/Customers/` had zero children (confirmed via
  the initial full recursive listing) — no individual Customer OKF
  directory pre-created by `provision_vault_base` itself. Later in this
  same session, `Work/Customers/Unsorted/` appeared — but via an entirely
  separate, unrelated, unmodified real code path
  (`customer_hub_linking.ensure_customer_hub_note`, triggered by a real
  email-capture run during `REQ-SB-71-US-01-T02`'s own verification, not
  by this task's endpoint) — a live, real demonstration of AC-04's own
  second clause: on-demand Customer directory creation is unchanged by
  this story. Confirmed by direct reading that `ensure_customer_hub_note`
  is not in this task's own `## Files to Modify` and was not touched.

gate: flagged 2026-08-18 — scope-internal judgment call disclosed above
(concurrent, pre-existing app-start capture trigger noise during
verification); not a MUST-FLAG escalation trigger (no new dependency, no
ADR deviation, no shared-interface change, nothing unclear) — flagged per
Pipeline.md's "log scope-internal judgement calls... they make the task
gate: flagged" convention, for human spot-check of the reasoning above.
