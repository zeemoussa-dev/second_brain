---
id: REQ-SB-70-US-01
title: Vault Base Provisioning API — idempotent endpoint that lays down the empty PARA/OKF folder skeleton
requirement_ids: [REQ-SB-70]
requirement_section: "REQ-SB-70: Vault Base Provisioning API — Fresh PARA/OKF Skeleton"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-048 created) — architect pass, 2026-08-18. Analyst's own gate: clear reasoning below is unaffected/preserved; the flag is the architect's own, added on top, per Implementation/Pipeline.md's ADR trigger. See ## Notes. [Coder, 2026-08-18: T01 Done, all ACs verified live against the real vault — see task's own Implementation Log. This flag stays open for the human's own pending ADR-048 review; not this role's to clear.]"
sprint: "SPRINT-060"
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-70-US-01 — Vault Base Provisioning API — idempotent endpoint that lays down the empty PARA/OKF folder skeleton

## Story

**As a** Second Brain operator
**I want** a single, safely-repeatable, real HTTP API endpoint that lays down
the redesigned vault's empty base folder skeleton (`Work/Customers/`,
`Work/Threads/`, `Work/Meetings/`, `Work/Resources/`, `Work/Archive/` with
its three subfolders) and nothing beyond that
**So that** I have one authoritative command to prepare a fresh `Work/` for
`REQ-SB-71`'s Email/Meeting pipelines to capture into — never a manual
`mkdir`, never a one-off script bypassing the app, and never a risk of
re-running it doing anything destructive or duplicating work

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-70: Vault Base Provisioning API —
  Fresh PARA/OKF Skeleton*. Raised 2026-08-18, same structural-design
  conversation as `REQ-SB-71`. Operator's own words: *"Structure the base
  we will have a Provison API for that."*
- **Scope is exactly the bucket list the PRD names, confirmed turn-by-turn
  with the operator, not analyst-assumed:** `Work/Customers/`,
  `Work/Threads/`, `Work/Meetings/`, `Work/Resources/` (empty bucket only —
  its own internal shape, e.g. Playbook/Competitive-Intel/Product-Knowledge
  subfolders, is explicitly NOT locked here), and `Work/Archive/` with
  `Opportunities/`, `Customers/`, `Resources/` subfolders. `Work/
  Opportunities/`, `Work/Websites/`, `Work/Notes/` are explicitly and
  deliberately excluded (operator: *"Keep Opp for later"*; the other two are
  future Capture kinds with no designed shape yet) — this story must not
  create them, and must actively verify their absence, not just omit
  building them.
- **`Work/` is assumed already empty — the operator's own responsibility,
  entirely out of scope here.** This mirrors this project's own established
  archive-not-delete discipline (`REQ-SB-59-US-01`, `ADR-047`), just
  performed by the operator directly this time rather than by a migration
  module. This story does not wipe, archive, or inspect any pre-existing
  `Work/` content — it only creates directories that don't already exist.
- **Idempotency mirrors `ADR-047`'s own "nothing left to act on" convention**
  (`REQ-SB-59-US-01`, `Done`) — a second call against an already-provisioned
  `Work/` succeeds with no error and creates nothing new, the same posture
  that migration module's own three functions already establish for this
  codebase. Directory creation in this codebase is already idempotent by
  construction wherever it exists today — every note-writing primitive
  (`vault_writer._write_frontmatter_note`, confirmed by direct reading,
  `path.parent.mkdir(parents=True, exist_ok=True)`) and `write_attachments`'s
  own `attachments_dir.mkdir(parents=True, exist_ok=True)` already use
  Python's own idempotent `mkdir(parents=True, exist_ok=True)` pattern — this
  story's own provisioning function should reuse that identical, already-
  proven idempotent-mkdir convention rather than inventing a new one.
- **Standing constraint, shared with `REQ-SB-71`:** this capability must be
  reachable via a real HTTP API endpoint (`/poc/*` convention), and every
  build-time and later verification call must go through that real endpoint
  — never a raw internal-function script call. The operator's own words:
  *"you don't do anything manually you do it by calling the APIs."* This is
  baked directly into every Scenario's own Given/When below (each names the
  real endpoint being called), not left as a separate, easily-skipped
  Constraint.
- **Soft, not hard, sequencing relationship to `REQ-SB-71`'s pipelines —
  confirmed by direct reading, not assumed:** `vault_writer._write_frontmatter_
  note` already self-creates any missing parent directory on every write
  (see above), so `REQ-SB-71`'s own Thread/Meeting note-writing code does
  not structurally *require* this endpoint to have run first to function —
  it would self-create `Work/Threads/`/`Work/Meetings/` on first write
  regardless. This story exists for the OPERATOR's own benefit (a clean,
  complete, Obsidian-browsable skeleton laid down deliberately, all five
  top-level buckets visible up front, `Work/Resources/`/`Work/Archive/`
  included even though nothing writes into them on day one) — not because
  the pipelines would otherwise fail. See `## Dependencies`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Provisioning an empty Work/ creates exactly the named base skeleton, nothing else

```gherkin
Given a real, empty Work/ directory (no pre-existing content)
When the operator calls the real provisioning endpoint (e.g.
    POST /poc/provision-vault-base)
Then a real directory listing of Work/ afterward shows exactly:
    Customers/, Threads/, Meetings/, Resources/, and Archive/ (with
    Archive/Opportunities/, Archive/Customers/, Archive/Resources/ as its
    three subfolders) — and no other top-level or nested folder
```
<!-- AC-ID: REQ-SB-70-US-01-AC-01 -->

### Scenario 2: A second call is a safe no-op

```gherkin
Given Work/ has already been provisioned by a prior real call to the
    provisioning endpoint
When the operator calls the same endpoint again
Then the call completes with no error
  And no duplicate folder, renamed folder, or any other change is made —
    a real before/after directory listing of Work/ is identical
```
<!-- AC-ID: REQ-SB-70-US-01-AC-02 -->

### Scenario 3: The explicitly deferred buckets are confirmed absent

```gherkin
Given the provisioning endpoint has been called against an empty Work/
When its own real directory listing is inspected afterward
Then Work/Opportunities/, Work/Websites/, and Work/Notes/ do NOT exist —
    proving these deliberately deferred buckets were genuinely excluded,
    not simply forgotten
```
<!-- AC-ID: REQ-SB-70-US-01-AC-03 -->

### Scenario 4: Per-Customer and other on-demand subshapes are not pre-created

```gherkin
Given the provisioning endpoint has been called against an empty Work/
When Work/Customers/ is inspected afterward
Then it exists but is empty — no individual Customer OKF directory is
    pre-created here; a real Customer's own directory (and its own
    People/, files/ subshapes) is created on demand the first time that
    Customer is actually captured, exactly as today's existing
    ensure_customer_hub_note-style behavior already works, unchanged by
    this story
```
<!-- AC-ID: REQ-SB-70-US-01-AC-04 -->

## Affected Screens

None — backend and vault-content only. No PRD text for `REQ-SB-70` names a
UI surface; `html-prototype/vault-browser.html` (already built, `REQ-SB-14`)
renders whatever folder/note structure exists in the vault generically —
it needs no change to display five new empty top-level folders. See
`## Notes` for the prototype-parity line.

## Dependencies

- **Blocked by:** none — this is new, self-contained work.
- **Related to, not hard-blocked by:** `REQ-SB-71` (`REQ-SB-71-US-01`,
  `-US-02`, `-US-03`) — the Email/Meeting pipelines this scaffold is
  prepared for. Confirmed by direct reading (see `## Context`) that this is
  a soft/organizational sequencing relationship, not a hard code
  dependency — those pipelines' own note-writing primitives already
  self-create any missing parent directory. The operator should still run
  this endpoint first in practice, for a clean, complete, Obsidian-browsable
  skeleton from day one, but neither story's own build order is blocked by
  the other.
- **Related to:** `REQ-SB-54-US-01` (`Done`) — the existing
  `ensure_customer_hub_note`/OKF-directory on-demand creation behavior for
  individual Customers, explicitly preserved unchanged by Scenario 4.
- **Related to:** `REQ-SB-59-US-01` (`Ready`) — `Work/Archive/`'s three
  subfolders formalize, as a first-class Obsidian-browsable location, what
  that migration module's own `.second-brain/migration_backup/` already
  does quietly; this story's own `Work/Archive/` is the destination shape a
  future archive-module iteration could adopt, though this story does not
  itself change `REQ-SB-59`'s own archive target.
- **External:** none.

## Constraints

- **Idempotent** — a second (or Nth) call must never error and must never
  duplicate or alter anything already provisioned (Scenario 2).
- **Exactly the named buckets, nothing more** — no extra convenience
  folder, no eagerly-created per-Customer directory, no `Work/Opportunities/`/
  `Work/Websites/`/`Work/Notes/` (Scenarios 1, 3, 4).
- **Empty scaffolding only** — no notes, no seed data, no placeholder files
  written into any provisioned folder.
- **Reachable only via a real HTTP endpoint** — every build-time and later
  verification call goes through that endpoint, never a raw script.
- **Does not touch, wipe, or inspect any pre-existing `Work/` content** —
  the operator's own responsibility to ensure `Work/` is empty first.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

<!-- Decomposer table, /plan-tasks, 2026-08-18 — supersedes the analyst's
starting-point table above. -->

| ID | Type | Task | Files / Area | Depends On | Task File |
|---|---|---|---|---|---|
| REQ-SB-70-US-01-T01 | backend | `provision_vault_base()` (idempotent `mkdir(parents=True, exist_ok=True)` for exactly the named buckets) + `POST /poc/provision-vault-base` in `email_poc_router.py` | `app/business/vault_provisioning.py` (new), `app/api/email_poc_router.py` | — | `../Tasks/REQ-SB-70-US-01-T01-vault-base-provisioning.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending; manual verification mode used throughout, per `Implementation/Pipeline.md`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Wiping, archiving, or inspecting any pre-existing `Work/` content** —
  the operator's own explicit responsibility, out of scope here.
- **`Work/Opportunities/`, `Work/Websites/`, `Work/Notes/`** — deliberately
  deferred, not designed or built here.
- **`Work/Resources/`'s own internal shape** (Playbook/Competitive-Intel/
  Product-Knowledge subfolders discussed but not locked) — only the empty
  bucket itself is in scope.
- **Individual Customer OKF directories, or `<slug>/People/`/`<slug>/files/`
  subshapes** — created on demand elsewhere (`REQ-SB-54`/`REQ-SB-71`), not
  pre-created by this story.
- **Any change to `REQ-SB-59`'s own migration-backup archive target** —
  unrelated, unmodified.
- **Any scheduling or recurring trigger for this endpoint** — genuinely
  one-time (but safely re-runnable), operator-triggered only, mirroring the
  `REQ-SB-59-US-01` migration-module precedent's own operator-triggered
  shape.

## Notes

**Prototype parity:** N/A — no new `html-prototype/` screen region.
`vault-browser.html` (`REQ-SB-14-US-01`, `Done`) already renders whatever
real vault folder structure exists, generically; five new empty top-level
folders need no prototype change.

**Why `gate: clear`:** the PRD's own text resolves every real design
question for this specific requirement directly and was individually
confirmed, turn-by-turn, with the operator per its own `<!-- Raised -->`
comment — the exact bucket list, the exact exclusions (with reasons), and
the idempotency convention to mirror (`ADR-047`) are all stated explicitly,
not inferred. No material assumption was made to fill a gap (trigger 1);
`REQ-SB-70` carries no `<!-- Draft -->` marker in the PRD — it is finalized
text (trigger 2 n/a); no ADR was created or changed by this analyst pass —
that is the architect's own role at `/plan-tasks` (trigger 3 n/a for this
role); no `ESCALATIONS.md` entry was written — this is ordinary forward
`/spec` work (trigger 4 n/a); this story is not oversized — one function,
one endpoint, comparable in shape to `REQ-SB-59-US-01`'s own smallest single
task (trigger 5 n/a); no locked AC is left unverifiable (trigger 6 n/a —
analyst role); no contradictory PRD inputs exist (trigger 7 n/a); no
genuinely unclear or multiple-equally-valid scope question exists — the one
soft-vs-hard dependency question on `REQ-SB-71` was resolved directly by
reading `_write_frontmatter_note`'s own real, already-shipped
`mkdir(parents=True, exist_ok=True)` behavior, not guessed (trigger 8 n/a).

gate: clear 2026-08-18 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above). [Analyst pass — see the architect
addendum immediately below for the trigger-3 flag added at `/plan-tasks`.]

---

**Architect addendum (2026-08-18, `/plan-tasks` step 1):**

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Vault Base Provisioning + Redesigned Email/Meeting Capture..." §"Vault
Base Provisioning (`REQ-SB-70-US-01`)" — the coder is bounded to that
subsection: a new, idempotent `app/business/vault_provisioning.py`
(`provision_vault_base() -> dict`, mirrors `vault_migration.py`'s own
module shape, explicitly NOT a migration) exposed as `POST /poc/
provision-vault-base` in the existing `app/api/email_poc_router.py`. No
other subsection of that architecture.md section applies to this story.

**ADR:** [ADR-048](../Architecture/ADR.md) — this story's own provisioning
scope is Decision 1 (a small part of a larger, four-story ADR covering the
whole `REQ-SB-70`/`REQ-SB-71` batch as one coherent redesign, per the
operator's own "one cohesive redesign... should not be built piecemeal"
framing). Nothing in this story's own scope was itself contested or
required a fresh assumption — the ADR's Decision 1 is a direct
transcription of this story's own already-`gate: clear` analyst text
(idempotent bucket list, module shape mirroring `vault_migration.py`).

**Why `gate: flagged` now, despite the analyst's own `gate: clear` above:**
trigger-3 fired — this architect pass created `ADR-048`, and this story is
one of the four the ADR covers. Per `Implementation/Pipeline.md`, creating
an ADR always flags the story it touches for human review, but does NOT
halt the pipeline — the decomposer still runs next on all four stories, so
the human reviews the ADR and the resulting tasks together in one pass. A
`REVIEW-QUEUE.md` entry has been added.

---

**Decomposer addendum (2026-08-18, `/plan-tasks` step 2):**

All 4 Scenarios locked as `REQ-SB-70-US-01-AC-01`..`AC-04`, wording
unchanged from the analyst's own text (already tight/buildable — no
tightening needed). One task, `T01`, covers all four — the whole story is
one function plus one endpoint, comparable in shape to `REQ-SB-59-US-01`'s
own smallest single task, exactly as the analyst's own sizing note
anticipated; no further decomposition would add value.

**Status → `Ready`; `gate` left `flagged` (architect's own `ADR-048` flag,
not cleared by this pass, per `Implementation/Pipeline.md`'s rule that the
decomposer does not clear an architect's own ADR flag).** No new MUST-FLAG
trigger fired during this pass beyond the already-recorded trigger-3: no
material assumption was made (trigger 1 n/a); nothing here is
`<!-- Draft -->` (trigger 2 n/a); this pass did not itself touch
`ADR-048` (trigger 3 n/a for this role, already flagged by the architect);
no `ESCALATIONS.md` entry was written (trigger 4 n/a); not oversized
(trigger 5 n/a); every locked AC got a tagged verification step in `T01`
(trigger 6 n/a — see below); no contradictory inputs (trigger 7 n/a); no
genuinely unclear/multiple-equally-valid task breakdown (trigger 8 n/a —
one task is the only reasonable shape here).

**AC → verification mapping:** `AC-01`..`AC-04` each get their own
numbered, AC-tagged manual verification step in `T01`'s `## Tests` — no
locked AC is left unverified.

gate: flagged (unchanged, architect's own `ADR-048` trigger-3) — decomposer
pass added nothing new to flag. See `REVIEW-QUEUE.md`'s existing
`REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 + REQ-SB-71-US-03`
entry (already covers all four stories in this batch; not duplicated
here).

---

**Coder addendum (2026-08-18, `/implement-sprint SPRINT-060`):**

`T01` built and verified `Done` — all 4 locked ACs verified with real,
live evidence against the real operator vault, via the real `POST
/poc/provision-vault-base` endpoint (never a raw script call). Full
evidence: `T01`'s own `## Implementation Log`. One scope-internal judgment
call disclosed there (a pre-existing, unrelated app-start capture trigger
ran concurrently with verification, per `ADR-005` — does not affect this
story's own correctness, `provision_vault_base`'s own machine-readable
return dict is exact on every call). Story status → `Done`. `gate` left
`flagged` — the architect's own `ADR-048` human-review flag is not this
role's to clear; see `REVIEW-QUEUE.md`.
