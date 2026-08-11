---
id: REQ-SB-15-US-01
title: Obsidian templates and in-vault guide for manual Customer/Pipeline/Agreement/Consumption entries
requirement_ids: [REQ-SB-15]
requirement_section: "REQ-SB-15: Manual-Entry Templates & Guidelines"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-003"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-15-US-01 — Obsidian templates and in-vault guide for manual Customer/Pipeline/Agreement/Consumption entries

## Story

**As a** Second Brain user entering Pipeline, Agreement, Consumption-Snapshot,
or Customer data by hand in Obsidian — since most of this data does not arrive
via email and must be typed in myself
**I want** a native Obsidian template for each note type that pre-fills the
resolved schema (frontmatter fields, the customer wikilink), plus a guide note
living inside the vault itself explaining what each type is for and how to use
its template
**So that** my manual entries are structurally consistent with what the
automated capture pipeline produces, and I don't need to leave Obsidian or
consult the project repo to know how to use them

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-15: Manual-Entry Templates &
  Guidelines*
- **Schema for all four note types is already resolved** —
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`. This story cites
  and implements that schema as Obsidian templates; it does not redesign it.
  Field-for-field:
  - **Customer** (`Work/Customers/<Customer>.md`): `type: Customer`,
    `customer:`, `tags: [customer/<slug>, kind/customer]`,
    `affiliate_of: ""`.
  - **Opportunity** — note: the PRD's requirement text calls this note type
    "Pipeline" (matching its folder, `Work/Pipeline/`), while the taxonomy
    plan's frontmatter `type:` value for an individual entry is `Opportunity`
    — "Pipeline" is the folder/kind name, "Opportunity" is the note type. Not
    a contradiction, just terminology worth calling out so the template is
    named/understood correctly. (`Work/Pipeline/<name>.md`): `type:
    Opportunity`, `customer:`, `stage:` (dynamic, vault-derived, no fixed
    enum), `value_usd:`, `description:`, `tags: [customer/<slug>,
    kind/opportunity]`.
  - **Agreement** (`Work/Agreements/<name>.md`): `type: Agreement`,
    `customer:`, `start_date:`, `end_date:`, `value_usd:`, `status:` (active |
    expired | renewal-pending), `tags: [customer/<slug>, kind/agreement]`.
  - **Consumption-Snapshot** (`Work/Consumption/<Customer>-<snapshot-date>.md`):
    `type: Consumption-Snapshot`, `customer:`, `snapshot_date:`,
    `azure_consumption_usd:`, `tags: [customer/<slug>,
    kind/consumption-snapshot]`. Per the taxonomy plan, this is append-only in
    spirit — a new snapshot is always a new note, an existing one is never
    edited; the template supports creating a new snapshot note, not editing
    one.
- **Obsidian's core Templates plugin, not a community plugin** — explicit in
  the PRD entry's own comment, citing this project's existing
  durable-over-clever precedent, `ADR-002` (portable Node.js toolchain over a
  system install — same "prefer the already-solved, native option" reasoning).
  No community plugin (e.g. Templater) is introduced by this story.
- **The customer wikilink** the PRD asks the template to pre-fill refers to
  the same wikilink mechanism `REQ-SB-14-US-01` (Vault Graph Connectivity)
  implements for automated captures — a template-inserted note should end up
  structurally identical (including that link) to what the automated pipeline
  would produce for the same note type, per this requirement's own Acceptance
  text.
- **Sibling requirement, not this story:** `REQ-SB-14-US-01` covers the
  automated retrofit of already-captured notes and the going-forward capture
  pipeline's automatic linking. This story covers the separate manual-entry
  path — a human inserting a template by hand in Obsidian for data that never
  arrives via automated capture (pipeline/agreement/consumption data, and
  Customer hub notes a user wants to create or enrich themselves).
- No `html-prototype/` screen applies — like `REQ-SB-07-US-01` and
  `REQ-SB-14-US-01`, this is vault-structure/authoring work (Obsidian template
  files + a guide note) with no Second Brain application screen involved.
- The templates and guide note are authored directly into the real Obsidian
  vault at the path configured in `src/backend/.env`'s `VAULT_PATH` — this is
  vault content, not application code.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-11). Wording tightened
for buildability against the architect's concrete mechanism (Templates/ as a
third top-level vault root, guide note at Work/Guides/Manual-Entry-Guide.md,
per ADR-006); scenario intent unchanged from the analyst's draft. -->

### Scenario 1: Customer template produces a schema-matching note

```gherkin
Given the vault's Templates feature is configured with a Customer template
When the user inserts the Customer template into a new note via Obsidian's
    own Templates feature
Then the resulting note's frontmatter matches the resolved Customer schema
    field-for-field (`type: Customer`, `customer:`, `tags:
    [customer/<slug>, kind/customer]`, `affiliate_of:`)
  And the note is structurally identical in shape to a Customer hub note the
    automated retrofit/capture path (`REQ-SB-14-US-01`) would produce
```
<!-- AC-ID: REQ-SB-15-US-01-AC-01 -->

### Scenario 2: Opportunity (Pipeline) template produces a schema-matching note

```gherkin
Given the vault's Templates feature is configured with an Opportunity
    template
When the user inserts the Opportunity template into a new note under
    `Work/Pipeline/`
Then the resulting note's frontmatter matches the resolved Opportunity schema
    field-for-field (`type: Opportunity`, `customer:`, `stage:`,
    `value_usd:`, `description:`, `tags: [customer/<slug>, kind/opportunity]`)
```
<!-- AC-ID: REQ-SB-15-US-01-AC-02 -->

### Scenario 3: Agreement template produces a schema-matching note

```gherkin
Given the vault's Templates feature is configured with an Agreement template
When the user inserts the Agreement template into a new note under
    `Work/Agreements/`
Then the resulting note's frontmatter matches the resolved Agreement schema
    field-for-field (`type: Agreement`, `customer:`, `start_date:`,
    `end_date:`, `value_usd:`, `status:`, `tags: [customer/<slug>,
    kind/agreement]`)
```
<!-- AC-ID: REQ-SB-15-US-01-AC-03 -->

### Scenario 4: Consumption-Snapshot template produces a schema-matching note

```gherkin
Given the vault's Templates feature is configured with a Consumption-Snapshot
    template
When the user inserts the Consumption-Snapshot template into a new note under
    `Work/Consumption/`
Then the resulting note's frontmatter matches the resolved Consumption-
    Snapshot schema field-for-field (`type: Consumption-Snapshot`,
    `customer:`, `snapshot_date:`, `azure_consumption_usd:`, `tags:
    [customer/<slug>, kind/consumption-snapshot]`)
  And using the template again for a later date creates a new, separate note
    rather than editing the existing snapshot note, per the taxonomy plan's
    append-only-in-spirit rule
```
<!-- AC-ID: REQ-SB-15-US-01-AC-04 -->

### Scenario 5: Guide note explains each type and its template

```gherkin
Given the user is browsing their vault in Obsidian
When they open the in-vault guide note
Then it explains what each of the four note types (Customer, Opportunity,
    Agreement, Consumption-Snapshot) is for and when to use it
  And it explains how to use each type's Templates-feature template
  And the guide note lives inside the vault itself — not only as documentation
    in this project's repo — since the user works primarily in Obsidian
```
<!-- AC-ID: REQ-SB-15-US-01-AC-05 -->

### Scenario 6: A template with an optional field left blank still produces a structurally valid note

```gherkin
Given the user inserts a template (e.g. Customer) and leaves an optional
    field blank (e.g. `affiliate_of`, which is only set for Affiliate
    notes)
When the note is saved
Then the note's frontmatter remains valid YAML and structurally consistent
    with the resolved schema
  And the note is not rejected or left malformed by leaving that field at its
    template-provided default/empty value
```
<!-- AC-ID: REQ-SB-15-US-01-AC-06 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or is
needed; this story authors Obsidian template files and a guide note directly
into the vault, not a Second Brain application screen.

## Dependencies

- **Blocked by:** none — the four schemas this story templates are already
  fully resolved in `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- **Related to:** `REQ-SB-14-US-01` (Vault Graph Connectivity) — sibling
  story; that story's automated retrofit/capture-time linking and this story's
  manual-template linking should produce structurally identical notes for the
  same type, per this requirement's Acceptance text, but neither story's
  implementation blocks the other (templates can be authored independently of
  the retrofit code).
- **External:** none new — uses Obsidian's own core Templates plugin, already
  present in any standard Obsidian install; no new plugin or dependency is
  introduced.

## Constraints

- Must use Obsidian's **core** Templates plugin, never a community plugin
  (Templater or otherwise) — per the PRD entry's explicit citation of
  `ADR-002`'s durable-over-clever precedent.
- Templates must match the resolved schema in
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` field-for-field —
  this story does not redesign or extend that schema.
- The exact in-vault location of the templates folder and the guide note
  (e.g. naming/placement) is an architecture-level decision for
  `/plan-tasks`, not decided in this story — Obsidian's Templates plugin
  requires a configured templates folder, and this story doesn't hardcode
  where in the vault that lives.
- Consumption-Snapshot notes are append-only in spirit (per the taxonomy
  plan) — the template supports creating a new snapshot note, never editing
  an existing one; this story does not add any note-editing tooling.
- The guide note and templates are vault content, not application code — no
  `src/backend` or `src/frontend` changes are implied by this story.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-15-US-01-T01 | content | Author the four Obsidian core-Templates note-type templates | `Templates/Customer.md`, `Templates/Opportunity.md`, `Templates/Agreement.md`, `Templates/Consumption-Snapshot.md` (vault-relative, at `VAULT_PATH`) | [T01](../Tasks/REQ-SB-15-US-01-T01-obsidian-templates.md) |
| REQ-SB-15-US-01-T02 | content | Author the in-vault Manual Entry Guide note | `Work/Guides/Manual-Entry-Guide.md` (vault-relative, at `VAULT_PATH`) | [T02](../Tasks/REQ-SB-15-US-01-T02-manual-entry-guide-note.md) |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — all 6 verified against the real vault
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, vault content, no pytest/vitest coverage applies
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new decision emerged
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Automated retrofit of already-captured notes, or automatic wikilinking of
  pipeline-captured notes — that is `REQ-SB-14-US-01`, a separate story.
- Any capture/ingestion pipeline for Opportunity, Agreement, or
  Consumption-Snapshot data (e.g. extracting it from email) — per the taxonomy
  plan's own non-goals, that structure and this template are ready, but no
  ingestion/agent code for these types is built or scoped here; this story
  only serves the fully-manual entry path.
- A community plugin (e.g. Templater) for more dynamic template behaviour —
  explicitly excluded by the PRD's own core-Templates-only direction.
- Any Second Brain application UI for creating these notes — this is an
  Obsidian-native authoring experience, not a Second Brain screen.
- Frontmatter schema validation/enforcement tooling — per the taxonomy plan's
  own non-goals, this remains a writing convention until real content exists
  to validate against; the template encourages consistency, it does not
  enforce it.

## Notes

**Architect pass (2026-08-11, `/plan-tasks` step 1):**

- **Templates folder location:** a new third top-level vault root,
  `Templates/` (sibling to `Personal/` and `Work/`), containing exactly the
  four template files (`Templates/Customer.md`, `Templates/Opportunity.md`,
  `Templates/Agreement.md`, `Templates/Consumption-Snapshot.md`). Obsidian's
  Settings → Templates → "Template folder location" is pointed at
  `Templates/` — confirmed a one-time manual step in the user's own Obsidian
  install; not something `src/backend` automates or this story's tasks
  should attempt to script.
- **Guide note location:** `Work/Guides/Manual-Entry-Guide.md` — under the
  existing `Work/<Kind>/` kind-folder convention, deliberately **not** inside
  `Templates/` (Obsidian's Templates feature lists every file in the
  configured template folder as insertable; a guide note there would appear,
  wrongly, in the "Insert Template" picker).
- **This is pure vault-content authoring, confirmed:** four template files +
  one guide note, written directly into the vault at `VAULT_PATH` — no
  `src/backend`/`src/frontend` changes, consistent with the story's own
  Constraints section. Both decisions rise to a new top-level vault-structure
  change (previously exactly two documented roots), so recorded as **ADR-006**
  (new — see `Implementation/Architecture/ADR.md`), not just an architecture.md
  note, since it changes an already-documented structural fact
  (`architecture.md`'s "two top-level roots" statement) future work depends
  on (e.g. a future indexer deciding whether to exclude `Templates/`).

**Architecture scope:** §Data Model → "Vault Content Conventions — Templates &
In-Vault Guide (REQ-SB-15)" (new subsection); ADR-006. No `src/backend` /
`src/frontend` source-layout sections apply — this story makes no code
changes.

gate: flagged 2026-08-11 — trigger-3 fired: this `/plan-tasks` pass created
**ADR-006** (new top-level vault root `Templates/`; guide note placed at
`Work/Guides/Manual-Entry-Guide.md`, deliberately outside `Templates/` so it
never appears in Obsidian's "Insert Template" picker). Run together with
sibling story REQ-SB-14-US-01 in the same batch (they share the customer
wikilink convention); both stories are flagged together per the architect's
ADR-trigger rule, so a human reviews the ADR and both stories' resulting
tasks in one pass. No contradictory inputs — the "Pipeline" (folder/
requirement wording) vs. "Opportunity" (frontmatter `type:` value) naming is a
terminology clarification cited directly from the taxonomy plan, not a genuine
contradiction; no ESCALATIONS.md entry needed (ADR-006 does not contradict any
Accepted ADR, the PRD, or a MEMORY.md constraint — MEMORY.md's `Work/`-only
constraint bounds backend writes specifically, not human-authored vault
content, so `Templates/` as a third root does not violate it); no material
assumption made beyond the placement decision itself, which is exactly the
architecture-level decision this story's own Constraints section deferred to
`/plan-tasks`.

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to Obsidian
templates or an in-vault guide note; this is vault-structure/authoring work
only, same shape as `REQ-SB-07-US-01` and `REQ-SB-14-US-01`.

---

**Decomposer pass (2026-08-11):** All 6 scenarios locked as
`REQ-SB-15-US-01-AC-01`..`AC-06` (wording tightened for buildability against
ADR-006's concrete `Templates/` root and guide-note placement; no scenario
intent changed). Decomposed into two flat-root task files,
`REQ-SB-15-US-01-T01`..`T02` (see `## Implementation Tasks`), both pure
vault-content authoring — no `src/backend`/`src/frontend` code, per this
story's own Constraints: T01 authors all four Obsidian core-Templates
template files (`Templates/Customer.md`, `Templates/Opportunity.md`,
`Templates/Agreement.md`, `Templates/Consumption-Snapshot.md`), each
matching `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`'s schema
field-for-field and, for the three non-Customer types, carrying the same
inline `**Customer:** [[Hub]]` wikilink body line `REQ-SB-14-US-01`
establishes for the automated path; T02 authors the in-vault guide note at
`Work/Guides/Manual-Entry-Guide.md`, describing all four types and how to
insert each template. `depends_on`: `T02 → [T01]` (the guide cites T01's
exact template/folder names, so it is written after them to stay accurate)
— acyclic, and independent of `REQ-SB-14-US-01`'s own task chain, per both
stories' `## Dependencies` sections (siblings, not blocking each other).
Every locked AC has at least one AC-tagged manual verification step: AC-01
through AC-04 and AC-06 (per-template schema/placeholder checks) are tagged
in T01; AC-05 (the guide note) is tagged in T02. Per this story's own
framing, Obsidian's "Insert Template" UI action and opening a note inside
the Obsidian app are manual human steps outside what a coder subagent can
drive — verification instead inspects the written template/guide files
directly and cross-checks field-for-field against the resolved schema
(explicitly, for AC-01's "structurally identical to REQ-SB-14-US-01's
output" claim, against that story's own hub-note-baseline shape, not by
literally exercising Obsidian's UI). `status:` advances `Draft → Ready`;
both new tasks are written at `status: Ready` to match, per the
decomposer's lockstep-status rule.

**`gate:` left `flagged`, unchanged from the architect's pass** —
`gate_reason: trigger-3 (ADR-006 created)` still applies; ADR-006 is still
pending human review. No new MUST-FLAG trigger fired during this
decomposition pass itself: the `REPLACE_WITH_...`/`"YYYY-MM-DD"` placeholder
convention is a scope-internal authoring judgement call, not a material
assumption filling a genuine spec gap (the schema itself, and the
requirement that placeholders stay valid YAML, were both already settled by
the story/taxonomy plan); no contradictory inputs; no additional
ADR/ESCALATIONS activity; no oversized task (T01 is four small, near-
identical content files, T02 is one guide note, both comfortably one
working session); every locked AC is verifiable by a real, observable
inspection step against the actual written vault files (no trigger-6
unverifiable AC — the Obsidian-UI-only claims within Scenarios 1 and 5 are
addressed via the documented cross-check/inspection proxy above, not left
unverified); the two-task split (templates vs. guide) was the only
defensible boundary, not a genuine multiple-equally-valid-options case.
`REVIEW-QUEUE.md`'s existing `REQ-SB-15-US-01` entry has been updated to
also point at these two now-created tasks, alongside ADR-006.

---

**Operator review (2026-08-11):** ADR-006 approved as written — no changes
requested. `gate: flagged → clear`. Proceeding to `/plan-sprints`.

---

**Product-owner pass (2026-08-11, `/plan-sprints`):** Grouped into a new
single-story sprint, `SPRINT-003`, on its own — sibling story
`REQ-SB-14-US-01` was deliberately kept in a separate sprint
(`SPRINT-002`) despite sharing the same `/plan-tasks` batch and ADR-006,
since neither story's tasks `depends_on` the other's and the two are
materially different kinds of work (this story's pure vault-content
authoring vs. `REQ-SB-14-US-01`'s live backend Outlook/vault integration);
see `SPRINT-003`'s own Grouping Rationale for the full reasoning.
`sprint: SPRINT-003` set above. `gate: clear` — advanced `Draft → Ready`.
No REVIEW-QUEUE or ESCALATIONS entry written by this pass.
