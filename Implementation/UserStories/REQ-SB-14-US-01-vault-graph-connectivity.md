---
id: REQ-SB-14-US-01
title: Customer hub notes and automatic wikilinking for vault graph connectivity
requirement_ids: [REQ-SB-14]
requirement_section: "REQ-SB-14: Vault Graph Connectivity"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-002"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-14-US-01 — Customer hub notes and automatic wikilinking for vault graph connectivity

## Story

**As a** Second Brain user viewing my vault's graph in Obsidian
**I want** every customer-related note — the ones already in the vault and every
one captured from now on — to carry a real `[[wikilink]]` to that customer's hub
note, with hub notes created automatically wherever one is missing
**So that** the graph view shows connected clusters of related notes instead of
isolated dots, without me doing any manual linking or note creation myself

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-14: Vault Graph Connectivity*
- Root cause, already diagnosed in the PRD entry itself and in `MEMORY.md`
  (2026-08-10): existing notes carry `customer:` frontmatter and a
  `customer/<slug>` tag (per ADR-004) but no `[[wikilink]]` to an actual Customer
  note — because no Customer hub notes exist yet either. Obsidian's graph draws
  edges from wikilinks only, not tags, so tag-only relationships render as
  disconnected dots. Fixing this needs **both** a Customer hub note per customer
  (with content, per REQ-SB-10's pattern extended from People to Customers — see
  below) **and** a wikilink from every customer-tagged note to its hub note —
  for notes that already exist (one-time retrofit) and for every note captured
  from this point forward.
- **Schema for the Customer hub note** is already resolved in
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` — `Work/Customers/
  <Customer>.md`, one file per customer:
  ```yaml
  type: Customer
  customer: ADNOC
  tags: [customer/adnoc, kind/customer]
  affiliate_of: ""   # set only if this note is an Affiliate of another Customer
  ```
  Body: a curated overview + links to key contacts/current focus — not a manual
  index of every related note (those already surface via `customer/<slug>` tag
  search). This story does not reinvent that schema, only cites and implements
  it.
- **`Work/Customers/` as a folder is not a reversal of ADR-004** — ADR-004
  ("Customer is a tag, never a folder level") is about classifying *content* by
  customer; `Work/Customers/` here is a `kind` folder (alongside `Work/Emails/`,
  `Work/Files/`, etc.) holding one `Customer`-type hub note per customer, exactly
  the same pattern the taxonomy plan already establishes — `kind` stays a folder
  level, `customer` stays a tag.
- **REQ-SB-10's pattern, extended (cited directly by the PRD entry):** REQ-SB-10
  (People Living Documents) establishes that background agents create and update
  baseline entries as they're encountered, the user can enrich the note further,
  and *manual content must survive later automated updates to the same note*.
  REQ-SB-14's PRD text explicitly invokes this pattern "extended from People to
  Customers," so this story replicates that same auto-baseline +
  preserve-manual-edits behaviour for Customer hub notes. **Note:** REQ-SB-10
  itself has no story yet (`BACKLOG.md` — unstarted) and therefore no code to
  literally extend; this story stands the pattern up fresh for Customer notes,
  matching the *design principle* the PRD cites, not reusing REQ-SB-10
  implementation that doesn't exist yet.
- **Sibling requirement, not this story:** REQ-SB-15 (Manual-Entry Templates &
  Guidelines) covers the *manual* creation path for Customer/Opportunity/
  Agreement/Consumption-Snapshot notes via Obsidian's own Templates feature —
  specced as its own story, `REQ-SB-15-US-01`. This story is about the
  *automated* retrofit of already-captured notes and the *going-forward* capture
  pipeline change; it does not touch manual template authoring.
- Builds on the existing, already-`Done` capture infrastructure from
  `REQ-SB-07-US-01`: `app/business/email_classification.py` (the only capture
  pipeline that exists today) and `app/data_access/vault_writer.py` (which
  already derives `list_known_customers` from the vault itself, per the
  `MEMORY.md` pattern — never a hardcoded customer list).
- No `html-prototype/` screen applies — like `REQ-SB-07-US-01`, this is
  backend/vault-structure work with no user-facing screen; Obsidian's own graph
  view is the presentation surface, not a Second Brain UI.
- The actual vault this retrofit runs against lives outside this repo, at the
  path configured in `src/backend/.env`'s `VAULT_PATH` — retrofit logic touches
  live, real user data, not a fixture/test vault.

## Scoping decision (one story, not two)

The PRD frames "existing notes get linked retroactively" and "new notes get
linked automatically" as one acceptance outcome (a fully connected graph), and
the two pieces share the same underlying mechanism: an "ensure this customer's
hub note exists, then link this note to it" operation, used once as a one-time
batch (retrofit) and once as a per-write hook (going forward). Splitting that
shared mechanism across two stories would separate implementation that has no
independent value on its own — a customer's graph connectivity isn't "done"
until both existing and future notes are linked. This mirrors the
already-`Done` `REQ-SB-07-US-01` precedent, which bundled four closely related
backend pieces (persistence, pipeline wrapper, concurrency guard, scheduler
wiring) into one story. Treated as **one story**, decomposed into several tasks
at `/plan-tasks`.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-11). Wording tightened
for buildability against the architect's concrete mechanism (inline-body
wikilink placement, app/business/customer_hub_linking.py, the surgical
baseline-frontmatter-key-insert primitive); scenario intent unchanged from
the analyst's draft. -->

### Scenario 1: Retrofit creates a missing Customer hub note

```gherkin
Given the vault has one or more existing notes tagged `customer/<slug>` for a
    customer that has no `Work/Customers/<Customer>.md` hub note yet
When the one-time retrofit process runs
Then a Customer hub note is created at `Work/Customers/<Customer>.md` matching
    the resolved schema (`type: Customer`, `customer:`, `tags:
    [customer/<slug>, kind/customer]`, `affiliate_of: ""`)
  And running the retrofit again does not create a second, duplicate hub note
    for that same customer
```
<!-- AC-ID: REQ-SB-14-US-01-AC-01 -->

### Scenario 2: Retrofit links an existing customer-tagged note to its hub note

```gherkin
Given an existing note carries `customer: <Customer>` frontmatter and a
    `customer/<slug>` tag, but no wikilink to that customer's hub note
When the one-time retrofit process runs
Then the note gains a `[[wikilink]]` to its customer's hub note
  And opening Obsidian's graph view shows that note connected to the hub note,
    instead of appearing as an isolated dot
```
<!-- AC-ID: REQ-SB-14-US-01-AC-02 -->

### Scenario 3: Newly captured notes are linked automatically, going forward

```gherkin
Given the capture pipeline (`app/business/email_classification.py`) classifies
    a newly captured note as belonging to a customer
When the note is written to the vault
Then the note is written with a `[[wikilink]]` to that customer's hub note
    already in place — no separate manual linking step is required afterward
  And if no hub note exists yet for that customer, one is created
    automatically as part of that same write, matching Scenario 1's schema
```
<!-- AC-ID: REQ-SB-14-US-01-AC-03 -->

### Scenario 4: Auto-created or auto-updated hub notes preserve manually-added content

```gherkin
Given a Customer hub note already exists and has user-added content beyond
    its auto-populated baseline fields (per REQ-SB-10's pattern, extended to
    Customer notes)
When the retrofit process runs again, or a new note for that customer is
    captured and the hub note is touched as part of that write
Then the hub note's manually-added content is preserved unchanged
  And only the auto-populated baseline fields (frontmatter, tags) are updated
    if they need to be, never the user's own additions
```
<!-- AC-ID: REQ-SB-14-US-01-AC-04 -->

### Scenario 5: Idempotency — an already-linked note is left unchanged

```gherkin
Given an existing note already contains a `[[wikilink]]` to its customer's
    hub note
When the retrofit process runs
Then the note is left unchanged
  And no duplicate wikilink is added to that note
```
<!-- AC-ID: REQ-SB-14-US-01-AC-05 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or is
needed for this capability; Obsidian's own graph view is the surface this story
affects, not a Second Brain UI screen.

## Dependencies

- **Blocked by:** none — the capture pipeline and vault-writer infrastructure
  this story extends (`app/business/email_classification.py`,
  `app/data_access/vault_writer.py`) already exist and work, per
  `REQ-SB-07-US-01` (`Done`).
- **Related to:** REQ-SB-10 (People Living Documents) — this story replicates
  its auto-baseline + preserve-manual-edits pattern for Customer notes, per the
  PRD's own "REQ-SB-10's pattern, extended" text. REQ-SB-10 itself is not yet
  specced/built (see `BACKLOG.md`), so there is no existing People-note code to
  literally extend — this story implements the pattern fresh, for Customers
  only.
- **Related to:** REQ-SB-15 (Manual-Entry Templates & Guidelines,
  `REQ-SB-15-US-01`) — sibling story covering the manual-creation path for the
  same four note-type schemas via Obsidian Templates. Not overlapping: that
  story is about a human creating a *new* note by hand; this story is about
  automated retrofit of *existing* notes and automatic linking of
  *pipeline-captured* notes.
- **External:** none new.

## Constraints

- `Customer` is never a folder level for content classification (ADR-004);
  `Work/Customers/` here is a `kind` folder holding one `Customer`-type hub
  note per customer — consistent with, not a reversal of, ADR-004.
- The exact placement of the wikilink on a customer-tagged note (a frontmatter
  property vs. inline in the note body) is an architecture-level decision for
  `/plan-tasks`, not decided in this story.
- Auto-created/auto-updated Customer hub notes must follow REQ-SB-10's cited
  pattern: baseline fields auto-populate/update, user-added content always
  survives later automated touches.
- Must respect the `api → business → data_access` layer boundary (ADR-003).
- The retrofit must be idempotent — rerunning it must never create duplicate
  hub notes or duplicate wikilinks (Scenarios 1 and 5).
- This retrofit runs against the user's real, live Obsidian vault
  (`VAULT_PATH` in `src/backend/.env`), not a fixture/test vault — no-data-loss
  and idempotency are load-bearing requirements, not conveniences.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-14-US-01-T01 | backend | Add hub-note file-I/O primitives to `vault_writer.py` | `src/backend/app/data_access/vault_writer.py` | [T01](../Tasks/REQ-SB-14-US-01-T01-hub-note-vault-writer-primitives.md) |
| REQ-SB-14-US-01-T02 | backend | New `app/business/customer_hub_linking.py` orchestration module | `src/backend/app/business/customer_hub_linking.py` | [T02](../Tasks/REQ-SB-14-US-01-T02-customer-hub-linking-orchestration.md) |
| REQ-SB-14-US-01-T03 | backend | Wire the per-write hub-linking hook into `email_classification.py` | `src/backend/app/business/email_classification.py` | [T03](../Tasks/REQ-SB-14-US-01-T03-capture-pipeline-hub-linking-hook.md) |
| REQ-SB-14-US-01-T04 | backend | New `POST /poc/retrofit-customer-hub-links` endpoint | `src/backend/app/api/email_poc_router.py` | [T04](../Tasks/REQ-SB-14-US-01-T04-retrofit-endpoint.md) |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — all 5 verified live against the real vault
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-verification mode still in effect project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new decision emerged beyond what architect/decomposer already recorded
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Manual creation of Customer/Opportunity/Agreement/Consumption-Snapshot notes
  via Obsidian's Templates feature — that is REQ-SB-15 (`REQ-SB-15-US-01`), a
  separate story.
- Building capture pipelines for Opportunity/Agreement/Consumption-Snapshot
  notes — the taxonomy plan documents their schema, but no ingestion/agent code
  for them exists or is scoped here; this story only concerns the Customer hub
  note + linking mechanism for the capture pipeline(s) that already exist
  (currently just email).
- Any Second Brain UI surfacing of graph connectivity — Obsidian's own graph
  view is the presentation surface; no application screen is added or changed.
- Wiring the Meetings (REQ-SB-08) or To-Do (REQ-SB-09) capture pipelines into
  this same auto-linking behaviour — those pipelines don't exist yet; when
  they're specced, they will need to replicate this pattern themselves, not
  covered here.
- Building out REQ-SB-10 (Person living documents) itself — only the specific
  "auto-baseline + preserve manual edits" behaviour is replicated for Customer
  notes; Person notes remain unbuilt.

## Notes

**Architect pass (2026-08-11, `/plan-tasks` step 1):**

- **Wikilink placement:** inline in the note body (e.g. `**Customer:**
  [[ADNOC]]` near the top of the body), extending this project's existing
  inline-body-wikilink convention (`## Related Emails`) rather than a
  frontmatter-property link — more durable across Obsidian versions,
  consistent with ADR-001/ADR-002's durable-over-clever precedent. Documented
  in `architecture.md` → Data Model → "Customer Hub Notes & Graph Linking";
  no new ADR (a direct extension of an already-documented convention, not a
  new structural boundary).
- **Shared "ensure hub note exists, then link" logic:** lives in a new
  `app/business/customer_hub_linking.py` module (ADR-003 layering unchanged),
  with the actual file I/O added to `app/data_access/vault_writer.py`
  (hub-note path/existence helpers, baseline-note creation via `write_note`,
  and a surgical "insert this body line if missing" helper generalizing
  `insert_tags_line`'s precedent). Called from both the one-time retrofit and
  `email_classification.py`'s per-write hook — one shared mechanism, not two.
- **Preserving manually-added hub-note content:** "baseline fields" =
  frontmatter keys `type`, `customer`, `tags`, `affiliate_of` only, never the
  body. After first creation, hub notes are never rewritten wholesale again —
  only missing baseline frontmatter keys are inserted (surgical, per
  `insert_tags_line`'s precedent); `affiliate_of` is only ever written when
  absent, never reset once a real value exists; the body is never
  programmatically touched again after creation.
- **Retrofit endpoint:** yes — a new one-off `POST
  /poc/retrofit-customer-hub-links` in `app/api/email_poc_router.py`,
  matching the existing `/poc/backfill-tags` and
  `/poc/flatten-customer-folders` precedents.

**Architecture scope:** §Data Model → "Customer Hub Notes & Graph Linking
(REQ-SB-14)"; §Source Layout (new `app/business/customer_hub_linking.py`
module and layer boundary, ADR-003 unchanged). ADR-004 (customer-as-tag) and
ADR-003 (layering) bound this story unchanged — no new ADR was needed for
REQ-SB-14's own decisions.

gate: flagged 2026-08-11 — trigger-3 fired: this `/plan-tasks` batch (run
together with sibling story REQ-SB-15-US-01) created ADR-006 (new top-level
vault root `Templates/`, guide note placement) while processing the two
closely-related stories in one pass; per the architect's ADR-trigger rule,
both stories in the batch are flagged so the human reviews the ADR and both
stories' resulting tasks together. REQ-SB-14 itself needed no new ADR — its
own decisions (wikilink placement, module layering, baseline-field
preservation, retrofit endpoint) all extend already-Accepted ADR-003/ADR-004
without introducing a new tool/framework or structural boundary; see the
architect-pass notes above. No contradictory inputs; no ESCALATIONS.md entry
needed; the one-story-vs-two-stories scoping question raised at kickoff was
resolved with a clear, defensible rationale (shared "ensure hub note exists +
link" mechanism serves both the retrofit and the going-forward path — see
`## Scoping decision` above), so it is not treated as a genuinely unclear
trigger-8 case.

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to vault graph
connectivity or Customer hub notes; this is backend/vault-structure work only,
same shape as `REQ-SB-07-US-01`.

---

**Decomposer pass (2026-08-11):** All 5 scenarios locked as
`REQ-SB-14-US-01-AC-01`..`AC-05` (wording tightened for buildability against
the architect's concrete mechanism; no scenario intent changed). Decomposed
into four flat-root task files, `REQ-SB-14-US-01-T01`..`T04` (see
`## Implementation Tasks`): T01 adds the hub-note file-I/O primitives to
`data_access/vault_writer.py` (path resolution, existence check, baseline
creation, the surgical frontmatter-key-insert and body-line-insert helpers);
T02 adds the new `app/business/customer_hub_linking.py` orchestration module
(`ensure_customer_hub_note`, `link_note_to_customer_hub`,
`ensure_hub_note_and_link`, `retrofit_customer_hub_links`) on top of T01;
T03 wires `ensure_hub_note_and_link` into `email_classification.py`'s
per-write capture flow; T04 exposes T02's retrofit batch as
`POST /poc/retrofit-customer-hub-links`. `depends_on`:
`T02 → [T01]`, `T03 → [T02]`, `T04 → [T02]` — acyclic, T03/T04 are
independent siblings once T02 lands. Every locked AC has at least one
AC-tagged manual verification step: AC-01/AC-02/AC-04/AC-05 (the retrofit
scenarios) are verified live in T04 against the real vault via the new
endpoint; AC-03 (the going-forward capture hook) is verified live in T03
against the real Outlook/vault integration — matching this project's
established live-verification precedent (SPRINT-001). T01/T02 carry
non-AC-tagged smoke checks of their own new functions in isolation; every
locked AC's actual tagged verification lives at the layer where the
Gherkin's trigger ("the retrofit process runs" / "the note is written")
is truly observable. `status:` advances `Draft → Ready`; all four new tasks
are written at `status: Ready` to match, per the decomposer's
lockstep-status rule.

**`gate:` left `flagged`, unchanged from the architect's pass** —
`gate_reason: trigger-3 (ADR-006 created)` still applies, since this
decomposition pass ran in the same batch as sibling story
`REQ-SB-15-US-01` while ADR-006 (written during the architect's pass) is
still pending human review. No new MUST-FLAG trigger fired during this
decomposition pass itself: no material assumption beyond what the
architect's notes already settled (the frontmatter-key-insert helper
generalizes `insert_tags_line`'s already-documented "insert this line if
this key is absent" behaviour, not a new decision); no contradictory
inputs; no additional ADR/ESCALATIONS activity; no oversized task (each of
T01–T04 is a single-file-or-single-new-module change fitting one working
session); every locked AC is verifiable by a real, observable manual step
against the live vault (no trigger-6 unverifiable AC); the task breakdown
followed directly from the architect's own numbered decision points, not a
genuine multiple-equally-valid-options case. `REVIEW-QUEUE.md`'s existing
`REQ-SB-14-US-01` entry has been updated to also point at these four
now-created tasks, alongside ADR-006.

---

**Operator review (2026-08-11):** ADR-006 approved as written — no changes
requested. `gate: flagged → clear`. Proceeding to `/plan-sprints`.

---

**Product-owner pass (2026-08-11, `/plan-sprints`):** Grouped into a new
single-story sprint, `SPRINT-002`, on its own — sibling story
`REQ-SB-15-US-01` was deliberately kept in a separate sprint
(`SPRINT-003`) despite sharing the same `/plan-tasks` batch and ADR-006,
since neither story's tasks `depends_on` the other's and the two are
materially different kinds of work (this story's live backend
Outlook/vault integration vs. `REQ-SB-15-US-01`'s pure vault-content
authoring); see `SPRINT-002`'s own Grouping Rationale for the full
reasoning. `sprint: SPRINT-002` set above. `gate: clear` — advanced
`Draft → Ready`. No REVIEW-QUEUE or ESCALATIONS entry written by this
pass.
