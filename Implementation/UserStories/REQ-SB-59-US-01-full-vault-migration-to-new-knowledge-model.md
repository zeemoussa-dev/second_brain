---
id: REQ-SB-59-US-01
title: Full Vault Migration to the New Knowledge Model — wipe Work/Emails/, re-run capture over Outlook history through the new pipelines
requirement_ids: [REQ-SB-59]
requirement_section: "REQ-SB-59: Full Vault Migration to the New Knowledge Model"
phase: P1
status: Ready
gate: clear
gate_reason: "Human reviewed and approved directly in chat, 2026-08-18 — ADR-047's archive-not-delete design (migration_backup/<run-timestamp>/, built on the existing move_note_and_attachments primitive, never a hard delete), the T01->T02 dependency, T03's independent scope (including its ESC-046 resolution), and the decomposer's 5 locked ACs / 3 tasks were all summarized to the operator, who chose 'Proceed now' over reading the raw ADR or requesting a dry-run count first. Flag cleared; eligible for /plan-sprints. Prior flagged history (trigger-3, ADR-047 created) preserved in git history of this file."
sprint: "SPRINT-059"
created: 2026-08-16
updated: 2026-08-18
---

# REQ-SB-59-US-01 — Full Vault Migration to the New Knowledge Model — wipe Work/Emails/, re-run capture over Outlook history through the new pipelines

## Story

**As a** Second Brain user
**I want** a one-time backfill that wipes the old per-email `Work/Emails/`
notes and any stale cross-links they produced, then fully re-runs capture
over Outlook history through the new Thread/Meeting/Project/Customer
pipelines
**So that** my whole vault reflects the new knowledge model consistently
from day one, instead of old per-email notes and new Thread notes coexisting
side by side

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-59: Full Vault Migration to the New
  Knowledge Model*. One-time backfill: wipe `Work/Emails/` and any stale
  cross-links it produced, then fully re-run capture over Outlook history
  through the pipelines built in `REQ-SB-55`/`REQ-SB-56`, populating
  Threads/Meetings/Projects/Customers under the new model from scratch.
- **Hard dependency, not a sequencing preference — depends on `REQ-SB-54`
  through `REQ-SB-58` ALL being `Done` first.** The PRD's own text says
  this explicitly: "this is integration work, not something that can run
  against a partial pipeline." This story cannot be meaningfully planned
  into tasks, let alone built, until every one of `REQ-SB-54-US-01`,
  `REQ-SB-55-US-01`, `REQ-SB-56-US-01`, `REQ-SB-57-US-01`, and
  `REQ-SB-58-US-01` is `Done` — mirroring `BACKLOG.md`'s own existing
  precedent for `REQ-SB-03-US-01` ("blocked on `REQ-SB-01`/`REQ-SB-02`
  shipping").
- Raised 2026-08-16, same discussion. **Operator explicitly authorized
  data loss/rewrite:** "I am okay with rewriting the data." Resolved
  directly: wipe-then-recapture, not a parallel run compared/diffed before
  cutover — reasoning confirmed with the operator: Outlook remains the real
  source of truth (nothing is destroyed at the source), and a
  parallel-run/diff approach adds real complexity for a single-user vault
  where the cost of "wrong" is cheap (re-run capture again), so the simpler
  approach was preferred over the more defensive one.
- **The exact replacement folder name (`Work/Threads/` or otherwise) is not
  locked by the PRD** — the Acceptance text itself hedges ("`Work/Emails/`
  (or its replacement `Work/Threads/`)"). This is a `REQ-SB-54-US-01`
  implementation detail (folder naming), not a fresh decision this story
  needs to make — this story's own scenarios reference "the Thread folder"
  generically, not a hardcoded literal path.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-18). Every scenario
below carries a trailing AC-ID tag and is locked (no `| locked: false`
markers used — every scenario is verifiable as written; see this story's
own ## Notes, "Decomposer pass," for the tightening rationale). -->

### Scenario 1: Pre-migration Email notes and stale cross-links are wiped

```gherkin
Given real, pre-migration notes exist under `Work/Emails/`, plus the two
    stale `.second-brain/` stores the old per-email shape produced
    (`processed_email_ids.json` and `conversation_index.json`)
When the operator calls `wipe_legacy_email_notes()` (via
    `POST /poc/wipe-legacy-email-notes`)
Then `Work/Emails/` contains zero notes afterward — every pre-migration
    note is archived (never deleted) into
    `.second-brain/migration_backup/<run-timestamp>/Emails/`, preserving
    its own content and any sibling `attachments/<slug>/` folder
  And `processed_email_ids.json` and `conversation_index.json` no longer
    exist at their canonical `.second-brain/` paths afterward — archived
    into the same `migration_backup/<run-timestamp>/` root, not left
    dangling
```
<!-- AC-ID: REQ-SB-59-US-01-AC-01 -->

### Scenario 2: Every Customer note is regenerated with the new four-section shape, preserving durable content

```gherkin
Given a real, pre-migration flat Customer hub note exists at
    `Work/Customers/<Name>.md` (the legacy, non-OKF shape), whose body
    contains a genuine durable fact or concluded item
When the operator calls `regenerate_customer_notes()` (via
    `POST /poc/regenerate-customer-notes`)
Then that Customer's OKF concept file (`Work/Customers/<slug>/<slug>.md`)
    exists afterward and carries the Background/History/Glimpse/Captures
    four-section shape
  And the durable fact/concluded item from the flat note's own
    pre-migration body is surfaced as a new `propose_background_amendment`
    Pending Approval — never silently discarded, and never auto-written
    directly into `## Background`
  And the flat legacy note is archived (never deleted) into
    `.second-brain/migration_backup/<run-timestamp>/Customers/`,
    resolving the filename-stem collision this shape produced in the
    vault's own note index
```
<!-- AC-ID: REQ-SB-59-US-01-AC-02 -->

### Scenario 3: A spot-check of 3 real, previously-known multi-message conversations confirms correct Thread consolidation

```gherkin
Given 3 real, previously-known multi-message Outlook conversations that
    existed before this migration
When the operator calls `recapture_outlook_history(email_limit,
    meeting_days_back)` (via `POST /poc/recapture-outlook-history`) and it
    completes
Then each of the 3 conversations now exists as exactly ONE Thread note
    under the Thread folder, whose transcript contains every one of that
    conversation's real messages — not split across multiple notes, and
    not missing any message
```
<!-- AC-ID: REQ-SB-59-US-01-AC-03 -->

### Scenario 4: Outlook itself is never modified or destroyed by this migration

```gherkin
Given the real Outlook mailbox/calendar this migration re-captures from
When `wipe_legacy_email_notes()`, `recapture_outlook_history(...)`, and
    `regenerate_customer_notes()` all run
Then Outlook's own real mailbox item count/calendar event count and
    content are byte-for-byte unchanged before and after the run — every
    Outlook read this migration performs is read-only, and only the
    vault's own captured notes (and its own `.second-brain/` stores) are
    wiped/archived and rewritten, never Outlook's own source data
```
<!-- AC-ID: REQ-SB-59-US-01-AC-04 -->

### Scenario 5: Meeting notes and their own stale cross-links are also cleaned up, not only Email notes

```gherkin
Given real, pre-migration Meeting notes exist with cross-links (including
    a Thread link) produced under the old shape
When `recapture_outlook_history(email_limit, meeting_days_back)` runs its
    own wide-window `classify_recent_meetings` re-run
Then those Meeting notes are topped-up/re-linked in place under the new
    model — each one's own Thread cross-link resolves to the
    now-recaptured Thread note, not a stale or dangling reference — the
    migration is not scoped to Email notes alone
```
<!-- AC-ID: REQ-SB-59-US-01-AC-05 -->

## Affected Screens

None — backend, one-time migration only. This is an operator-triggered
maintenance operation (mirroring this codebase's existing one-module-per-
maintenance-operation retrofit precedent — `tag_backfill.py`,
`vault_restructure.py`, `partner_hub_linking.migrate_customer_to_partner`),
not a recurring or UI-driven feature.

## Dependencies

- **Blocked by (hard, all required):** `REQ-SB-54-US-01`, `REQ-SB-55-US-01`,
  `REQ-SB-56-US-01`, `REQ-SB-57-US-01`, `REQ-SB-58-US-01` — every one of
  these five must be `Done` before this story can be planned into tasks.
  Not a soft/sequencing preference — the PRD's own text calls this
  "integration work" that cannot run against a partial pipeline.
- **Related to:** the existing retrofit-script precedent
  (`app/business/tag_backfill.py`, `vault_restructure.py`,
  `partner_hub_linking.migrate_customer_to_partner`) — this story's own
  migration mechanism should follow the same one-time, operator-triggered,
  one-module shape, not invent a new maintenance-operation convention.
- **External:** the real, live Outlook mailbox/calendar this migration
  re-captures from (read-only from Outlook's own perspective, per
  Scenario 4).

## Constraints

- **Wipe-then-recapture, not parallel-run/diff-then-cutover** — locked by
  the operator's own resolution; do not build a comparison/diff mechanism
  instead.
- **Outlook itself is never modified or destroyed** — this migration only
  wipes and rewrites the vault's own captured notes (Scenario 4).
- **Durable/concluded pre-migration content must be preserved, not silently
  discarded** (Scenario 2) — a blanket wipe of Customer notes' own
  narrative content is not acceptable; the migration must apply the same
  judgment the Customer Synthesizer (`REQ-SB-57`) already uses going
  forward, to the historical backlog.
- **One-time, operator-triggered** — not a recurring scheduled job.
- **Hard-blocked on all 5 dependency stories being `Done`** — do not begin
  planning this story's own tasks in isolation before then.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (2026-08-18) — supersedes the analyst-authored
starting point above. 3 tasks, one per public function in the new
app/business/vault_migration.py module (ADR-047). depends_on read directly
from each task file's own frontmatter, not re-derived here. -->

| ID | Type | Task | Files / Area | Task File | depends_on |
|---|---|---|---|---|---|
| REQ-SB-59-US-01-T01 | backend | New `app/business/vault_migration.py` — `wipe_legacy_email_notes()`: archives `Work/Emails/` notes + `processed_email_ids.json`/`conversation_index.json` into `.second-brain/migration_backup/<run-timestamp>/` | `app/business/vault_migration.py` (new), `app/api/email_poc_router.py` | `../Tasks/REQ-SB-59-US-01-T01-wipe-legacy-email-notes.md` | — |
| REQ-SB-59-US-01-T02 | backend | `recapture_outlook_history(email_limit, meeting_days_back)`: one call each to `pull_and_stage_emails` → `run_email_capture_pipeline` → `classify_recent_meetings` over a full-history window | `app/business/vault_migration.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-59-US-01-T02-recapture-outlook-history.md` | `REQ-SB-59-US-01-T01` |
| REQ-SB-59-US-01-T03 | backend | `regenerate_customer_notes()`: regenerates every legacy flat `Work/Customers/<Name>.md` note onto the OKF shape via `synthesize_customer(evidence_text=...)`, archives the flat file — also resolves `ESC-046` | `app/business/vault_migration.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-59-US-01-T03-customer-note-regeneration.md` | — (see Notes) |

**Dependency graph:** `T01 -> T02` (hard, load-bearing — `T02`'s recapture
silently no-ops without `T01`'s dedup-gate reset, `ADR-047` Context point 1).
`T03` carries `depends_on: []` — a deliberate decomposer finding, not an
oversight: direct reading of `synthesize_customer`/`_build_customer_glimpse`
confirmed `T03`'s own evidence (the flat note's pre-migration body) and its
Glimpse rollup (existing Project frontmatter) are both fully disjoint from
what `T01` archives and what `T02` recaptures. Acyclic; no cross-sprint edge
needed.

## Definition of Done

- [ ] `REQ-SB-54-US-01`, `REQ-SB-55-US-01`, `REQ-SB-56-US-01`,
      `REQ-SB-57-US-01`, `REQ-SB-58-US-01` are all `Done`, before this
      story's own tasks are planned
- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A parallel-run/diff-then-cutover mechanism** — explicitly declined by
  the operator in favor of the simpler wipe-then-recapture approach.
- **Any change to the capture pipelines themselves** — this story only
  re-runs the already-`Done` `REQ-SB-55`/`REQ-SB-56` pipelines over
  historical Outlook data; it does not modify their own logic.
- **A recurring/scheduled version of this migration** — genuinely one-time.
- **Modifying Outlook's own source data** — never in scope (Scenario 4).

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen change; this is a
backend maintenance operation.

**Why `gate: clear`:** the PRD's own text resolves every real design
question for this specific requirement directly — wipe-then-recapture vs.
parallel-run/diff (resolved, with the operator's own quoted reasoning),
Outlook remaining the untouched source of truth (resolved), and durable
pre-migration content being preserved rather than discarded (stated
directly in the Acceptance text). No material assumption, no genuinely
unclear/multiple-equally-valid interpretation, no contradictory PRD input,
not oversized (three tightly-scoped tasks mirroring this codebase's own
established retrofit-module precedent). This story is entirely blocked on
a real, explicit, hard cross-requirement dependency (all 5 sibling stories
`Done`) rather than any ambiguity of its own — the same "gate: clear —
blocked on X shipping" pattern this project already uses for
`REQ-SB-03-US-01` (blocked on `REQ-SB-01`/`REQ-SB-02`), scaled to a 5-story
dependency set instead of 2.

---

**Architect pass (2026-08-18, `/plan-tasks` step 1) — all 5 dependency
stories now confirmed `Done`; story unblocked and planned.**

**Architecture scope: §"Vault Migration — One-Time Full Vault Migration to
the New Knowledge Model (REQ-SB-59, see ADR-047)"** in
`Implementation/Architecture/architecture.md` (inserted directly after
"Project & Customer Synthesizer", before "Authentication & Authorisation")
— this is the section the decomposer and coder are bounded by. Full
reasoning, decisions, and Alternatives Considered: `ADR-047` in
`Implementation/Architecture/ADR.md`.

**New ADR: `ADR-047`.** Sets `gate: flagged` (MUST-FLAG trigger 3) per
Pipeline.md — the decomposer still runs immediately after this flag so the
human reviews `ADR-047` and the resulting task breakdown together in one
pass; this story does NOT halt at this stage.

**Concrete scope the decomposer/coder must build against (do not
re-derive from the story alone — read `ADR-047` and the architecture.md
section in full before authoring tasks):**

- One new module, `app/business/vault_migration.py` (fifth instance of
  the existing `tag_backfill.py`/`vault_restructure.py`/
  `partner_hub_linking.py` one-off-migration-module shape), three public
  functions matching T01/T02/T03 exactly: `wipe_legacy_email_notes()`,
  `recapture_outlook_history(email_limit: int, meeting_days_back: int)`,
  `regenerate_customer_notes()` — each exposed as its own new flat
  `POST /poc/<verb>` endpoint in `email_poc_router.py`.
- **T01** archives (never deletes) every note under `Work/Emails/` plus
  `.second-brain/processed_email_ids.json` (load-bearing — see `ADR-047`
  Context point 1: leaving this in place makes T02 a silent no-op) and
  `.second-brain/conversation_index.json` into a new
  `.second-brain/migration_backup/<run-timestamp>/` archive root, reusing
  the existing, unmodified `vault_writer.move_note_and_attachments`
  primitive for Notes and a plain `Path.rename` for the two JSON stores.
  **T01 does not touch `Work/Meetings/` at all** — Scenario 5 is satisfied
  entirely by T02's wide-window meeting re-run (meeting dedup is already
  non-gating/top-up-only, confirmed by direct reading of
  `mark_meeting_processed`'s own docstring).
- **T02** calls `email_pull.pull_and_stage_emails(limit=email_limit)` →
  `email_capture_pipeline.run_email_capture_pipeline()` →
  `meeting_classification.classify_recent_meetings(days_back=
  meeting_days_back, days_ahead=14, limit=...)`, each exactly once —
  `email_limit`/`meeting_days_back` are required, operator-supplied
  parameters (never hardcoded), large enough to cover the mailbox's real
  history. No new Outlook-COM primitive.
- **T03 also resolves `ESC-046`** (the legacy-flat-vs-OKF-directory
  Customer filename-stem collision, `ESCALATIONS.md`, `Open`) as a
  direct, in-scope consequence — NOT a separate `BUGFIX-NN-US-01`. For
  every flat `Work/Customers/<Name>.md` note (`list_all_note_paths()`
  filtered to `type == "Customer"` and `path.parent.name == "Customers"`):
  ensure its OKF directory exists, feed its full body into the SAME,
  unmodified `project_customer_synthesizer.synthesize_customer(customer,
  evidence_text=...)` the ongoing `REQ-SB-57` Synthesizer already uses
  (routes any durable fact through the existing `detect_customer_durable_
  fact`/Pending-Approval gate — deliberately never a migration-only
  auto-write bypass), then archive the flat file the same way T01
  archives Email notes. Archiving the flat file is what removes the
  stem collision from `vault_indexing`'s index.
- Pending Approvals `regenerate_customer_notes()` produces are explicitly
  **not** part of this story's own Definition of Done — resolving them is
  ordinary, ongoing operator review, decoupled from "migration complete."
  The decomposer should not author a locked AC requiring every Pending
  Approval to be *approved*, only that they are correctly *created*.
- No new "already-ran" state marker / dry-run flag — every function is
  naturally idempotent via the archive-not-delete mechanism (see `ADR-047`
  Alternative 5).

**`ESC-046` resolution decision (explicit, not left ambiguous):** resolved
via this story's own T03, per the analysis above and `ADR-047` Decision 5
— NOT deferred to a separate bugfix story. `REVIEW-QUEUE.md` carries a
pointer for the human to confirm this resolution alongside `ADR-047`.

---

**Decomposer pass (2026-08-18) — `/plan-tasks` step 2:**

Read `ADR-047` and the architecture.md "Vault Migration" section in full,
plus the real current code each grounds (`vault_writer.py`'s
`move_note_and_attachments`/`remove_empty_dirs`/`load_processed_email_ids`/
`list_all_note_paths`, `email_pull.pull_and_stage_emails`,
`email_capture_pipeline.run_email_capture_pipeline`,
`meeting_classification.classify_recent_meetings`/`mark_meeting_processed`'s
own docstring, `customer_hub_linking.ensure_customer_hub_note`,
`project_customer_synthesizer.synthesize_customer`/`_build_customer_glimpse`,
and `email_poc_router.py`'s existing `/poc/*` endpoint shapes) before
authoring tasks and locking ACs — not re-derived from the story alone.

- **5/5 scenarios tightened, AC-ID'd, and locked** —
  `REQ-SB-59-US-01-AC-01`..`AC-05`, all locked (no `locked: false` marker
  used — every scenario is verifiable as written against the concrete
  function/endpoint names `ADR-047` fixed). Tightening replaced generic
  "the migration runs" phrasing with the real function names
  (`wipe_legacy_email_notes`/`recapture_outlook_history`/
  `regenerate_customer_notes`) and their own concrete, checkable outputs
  (archive path shape, Pending Approval `action_id`/`payload` shape,
  byte-for-byte Outlook-unchanged framing) — an ordinary buildability
  tightening, not a scope change.
- **3 tasks, one per public function** `ADR-047` names, matching the
  story's own T01/T02/T03 split:
  - `REQ-SB-59-US-01-T01` — `wipe_legacy_email_notes()`. `depends_on: []`.
    Carries `AC-01`.
  - `REQ-SB-59-US-01-T02` — `recapture_outlook_history(email_limit,
    meeting_days_back)`. `depends_on: [REQ-SB-59-US-01-T01]` — hard,
    load-bearing: `T01`'s archiving of `processed_email_ids.json` is what
    resets the email dedup gate (`ADR-047` Context point 1); without it,
    `T02`'s recapture silently processes zero real emails. Carries `AC-03`,
    `AC-04`, `AC-05`.
  - `REQ-SB-59-US-01-T03` — `regenerate_customer_notes()`. `depends_on: []`
    — **a directly-verified finding, not the "likely straight chain"
    assumption carried into this pass.** Read `synthesize_customer`'s own
    full docstring and `_build_customer_glimpse`'s own body: `T03`'s
    `evidence_text` is the flat legacy Customer note's OWN pre-migration
    body (`vault_writer.read_note`, never anything `T02` recaptures), and
    the Glimpse rollup reads existing Project frontmatter under that
    Customer's own directory (never a Thread/email note). `T03`'s own file
    scope (`Work/Customers/<Name>.md` flat notes) is fully disjoint from
    what `T01` archives (`Work/Emails/`, two `.second-brain/` JSON stores)
    and what `T02` writes (`Work/Threads/`, `Work/Meetings/`). No
    code-level dependency exists either direction. Carries `AC-02`.
  - Acyclic (`T01 -> T02`, `T03` independent). No cross-sprint edge needed
    — all three land in one story/sprint regardless.
- **AC → verification mapping confirmed complete:** all 5 locked ACs
  (`AC-01`..`AC-05`) each have at least one matching AC-tagged manual
  verification step — `AC-01` in `T01`; `AC-03`/`AC-04`/`AC-05` in `T02`;
  `AC-02` in `T03`. Every step names a concrete, observable outcome (a
  real byte-for-byte archive comparison, a real Outlook read-before/read-
  after diff, a real Pending Approval record, a real re-linked Thread
  reference) — no locked AC here is unverifiable in principle; the real
  cost is live wall-clock time against a real mailbox/vault, not
  verification-method ambiguity.
- **No MUST-FLAG trigger fired from this pass itself:** no NEW material
  assumption beyond ordinary AC-tightening (every real design fork was
  already resolved by `ADR-047`/architecture.md); no `<!-- Draft -->`/
  unfinalised requirement relied on; this pass did not itself create or
  change an ADR (the architect already did, in the prior step — its flag
  is preserved, not re-raised); no NEW `ESCALATIONS.md` entry written by
  this pass (the pre-existing `ESC-046` is being resolved, not newly
  raised); not oversized (3 tightly-scoped tasks, one per function,
  mirroring this codebase's own established one-off-migration-module
  precedent); every locked AC is verifiable; no contradictory inputs; the
  one real fork this pass resolved (T03's dependency edges) was resolved
  by direct code reading, not a guess, and is logged above rather than
  treated as an unclear/multiple-equally-valid split.
- **`gate` stays `flagged`, per Pipeline.md's explicit rule for this
  situation** ("if the architect flagged the story this run for an ADR
  change, leave it `gate: flagged` — the human reviews the ADR and your
  tasks together") — this pass does not clear or re-raise the flag, only
  confirms it stands. `status: Draft -> Ready` (all 5 ACs locked, every
  locked AC has a tagged step, `depends_on` is acyclic — the three
  conditions Pipeline.md requires for this transition are all met). All 3
  tasks written directly at `status: Ready` (status moves in lockstep with
  the story, per Pipeline.md). `REVIEW-QUEUE.md`'s existing `REQ-SB-59-US-01`
  entry (written by the architect) now also lists the 3 task files and the
  `T03`-independence finding, for the human's convenience reviewing both
  together — see that entry.

Eligible for `/plan-sprints` once the human clears the flag (or the
product-owner may also read this as "flagged, parked" per Pipeline.md's own
batching rule — a flagged item is never silently advanced past review).

---

**Product-owner pass (2026-08-18, `/plan-sprints`) — grouped into
`SPRINT-059`.** Only `Ready`, ungrouped story in scope this pass. Single-story
sprint, mirroring `SPRINT-057`/`SPRINT-058`'s precedent from this same batch.
Dependency graph read directly from the 3 task files' own `depends_on:`
frontmatter (`T01` → `T02` hard edge, `T03` independent) — acyclic, single
phase (`P1`). No `depends_on_sprints` edge needed: all 5 hard-blocking sibling
stories are already `Done`. Sizing: ~3 tasks, S. No MUST-FLAG trigger fired
from this grouping pass — `gate: clear`, `SPRINT-059` created directly at
`status: Ready`. Full rationale:
`Implementation/Sprints/SPRINT-059-full-vault-migration-to-new-knowledge-model.md`.

gate: clear 2026-08-18 — no triggers fired (no ADR touched by product-owner,
grouping unambiguous, not oversized).
