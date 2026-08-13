---
id: REQ-SB-17-US-01
title: Obsidian template and guide-note entry for manual Research (books & reads) entries
requirement_ids: [REQ-SB-17]
requirement_section: "REQ-SB-17: Research Notes (Books & Reads)"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-007"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-17-US-01 — Obsidian template and guide-note entry for manual Research (books & reads) entries

## Story

**As a** Second Brain user who wants to capture a book summary or an
article/read I want to memorize
**I want** a native Obsidian template that pre-fills the minimal Research
schema (title, author, tags), plus an entry in the vault's existing manual-
entry guide note explaining what a Research note is for and how to use its
template
**So that** my book/read entries are structurally consistent with every
other manually-entered note type, and I don't need to leave Obsidian or
consult the project repo to know how to create one

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-17: Research Notes (Books & Reads)*.
- **Schema already resolved** —
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "Researches
  (resolved 2026-08-11)", and `MEMORY.md`'s matching 2026-08-11 Decision
  entry. This story cites and implements that schema; it does not redesign
  it.
  ```yaml
  type: Research
  title: "Beyond the Second Brain"
  author: "Mo Elkholy"
  tags: [kind/research]
  ```
  `Work/Researches/<Title>.md`. The free-form body carries the user's own
  takeaways/quotes/notes (per the "digest, not raw dump" principle already
  used elsewhere) — frontmatter stays deliberately thin.
- **Manual-entry only, no capture pipeline** — operator's explicit choice.
  AI-assisted summarization is explicitly deferred, not in scope here or
  anywhere yet.
- **No customer/company link, by design, not oversight.** Per the taxonomy
  plan: "a book/read isn't inherently tied to a customer relationship, so
  per the standing tags-and-wikilinks rule this is a genuine absence of a
  link target" — the same reasoning already applied to People with no known
  company. This story's ACs make that explicit so it is never mistaken for
  a missed link later (`MEMORY.md`'s standing tags-and-wikilinks rule
  otherwise requires checking for one).
- **Same mechanism as `REQ-SB-15`, extending its output rather than editing
  its story.** `REQ-SB-15-US-01` (`Done`) established Obsidian's core
  Templates plugin (`Templates/` vault root, per ADR-006) and authored the
  in-vault guide note at `Work/Guides/Manual-Entry-Guide.md` describing the
  four Customer/Opportunity/Agreement/Consumption-Snapshot templates. Per
  the pipeline's append-only-specs rule, that `Done` story's own file is
  never edited; this is a **new** story whose tasks add a fifth template
  file (`Templates/Research.md`) alongside the existing four, and add a
  fifth entry to the same guide note's vault content — the guide note is
  vault content this new story's tasks touch, not a spec file.
- No `html-prototype/` screen applies — like `REQ-SB-07/10/14/15-US-01`,
  this is vault-structure/authoring work with no Second Brain UI screen.
  Note: the prototype's `my-day-reads.html` screen ("Important Reads,"
  REQ-SB-12's flagged-notes concept — emails/notes worth a closer look this
  week) is an unrelated, coincidental name match to "Reads" in this
  requirement's title; it has nothing to do with book/article Research
  notes and this story does not touch it.
- The template and guide-note update are authored directly into the real
  Obsidian vault at the path configured in `src/backend/.env`'s
  `VAULT_PATH` — this is vault content, not application code.

## Scoping decision (extend the existing guide note, not a new one)

The PRD asks for "a template" and cites the guide-note mechanism `REQ-SB-15`
already built ("using a template ... so entries are structurally
consistent"); it does not ask for a second, Research-specific guide note.
Keeping **one** living guide document that lists every manual-entry note
type (now five, with Research added) matches `REQ-SB-15`'s own intent — a
single place the user checks, not a fragmented set of guide notes growing
one-per-type. This is a clear, defensible scoping call (comparable to
`REQ-SB-14-US-01`'s one-vs-two-story reasoning), not a genuinely unclear
question — not flagged.

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path first, then the guide-note update, then
edge cases. -->

### Scenario 1: Research template produces a schema-matching note

```gherkin
Given the vault's Templates feature is configured with a Research template
When the user inserts the Research template into a new note under
    Work/Researches/
Then the resulting note's frontmatter matches the resolved Research schema
    field-for-field (type: Research, title, author, tags: [kind/research])
  And the note's body is left free-form, ready for the user's own
    summary/takeaways
```
<!-- AC-ID: REQ-SB-17-US-01-AC-01 -->

### Scenario 2: Guide note explains the Research type and its template

```gherkin
Given the user is browsing the in-vault manual-entry guide note
When they read the entry for Research notes
Then it explains what a Research note is for (book summaries and articles/
    reads worth memorizing) and when to use it
  And it explains how to insert the Research template via Obsidian's
    Templates feature
```
<!-- AC-ID: REQ-SB-17-US-01-AC-02 -->

### Scenario 3: A newly inserted template with unfilled placeholder values still produces a structurally valid note

```gherkin
Given the user inserts the Research template and has not yet filled in
    title/author
When the note is saved
Then the note's frontmatter remains valid YAML and structurally consistent
    with the resolved schema
  And the note is not rejected or left malformed by the template's
    placeholder default values
```
<!-- AC-ID: REQ-SB-17-US-01-AC-03 -->

### Scenario 4: A Research note carries no customer/company link, by design

```gherkin
Given a Research note is created via the template
When its frontmatter and body are examined
Then no customer/<slug> or company/<slug> tag and no hub-note wikilink are
    present or expected
  And this is a deliberate absence of a link target (a book/read is not
    inherently tied to a customer relationship), not an overlooked link per
    the standing tags-and-wikilinks rule
```
<!-- AC-ID: REQ-SB-17-US-01-AC-04 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or
is needed; this story authors an Obsidian template file and a guide-note
addition directly into the vault, not a Second Brain application screen.
(See `## Context` for the note distinguishing this from the prototype's
unrelated `my-day-reads.html` screen.)

## Dependencies

- **Blocked by:** none — `REQ-SB-15-US-01` (`Done`) already established the
  `Templates/` vault root (ADR-006) and the in-vault guide note this story
  extends; both are ready to build on.
- **Related to:** `REQ-SB-15` (`REQ-SB-15-US-01`) — this story adds a fifth
  template and guide-note entry using the exact same mechanism (Obsidian
  core Templates plugin, `Work/Guides/Manual-Entry-Guide.md`), without
  editing that `Done` story's own spec file.
- **External:** none new — uses Obsidian's own core Templates plugin,
  already configured per `REQ-SB-15-US-01`'s one-time setup step (operator-
  confirmed done, per `REVIEW-QUEUE.md`'s SPRINT-003 entry).

## Constraints

- Must use Obsidian's **core** Templates plugin, never a community plugin —
  same constraint `REQ-SB-15-US-01` already established (`ADR-002`'s
  durable-over-clever precedent); this story does not introduce a new
  plugin.
- The template must match the resolved Research schema field-for-field —
  this story does not redesign or extend that schema.
- The guide-note update must be additive to `Work/Guides/Manual-Entry-
  Guide.md`'s existing content (four entries already there from
  `REQ-SB-15-US-01`) — it must not remove or alter those existing entries,
  only add a fifth.
- No customer/company wikilink or tag is added to the Research template or
  its guide-note entry — an intentional absence, not deferred to
  `/plan-tasks`.
- The template and guide-note update are vault content, not application
  code — no `src/backend`/`src/frontend` changes are implied by this story.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-17-US-01-T01 | content | Author the Research Obsidian core-Templates template | `Templates/Research.md` (vault) | `../Tasks/REQ-SB-17-US-01-T01-research-template.md` |
| REQ-SB-17-US-01-T02 | content | Add the Research entry to the in-vault Manual Entry Guide note | `Work/Guides/Manual-Entry-Guide.md` (vault) | `../Tasks/REQ-SB-17-US-01-T02-manual-entry-guide-research-entry.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any AI-assisted capture/summarization pipeline for Research notes** —
  explicitly deferred by the PRD and the taxonomy plan; manual entry only,
  for now.
- **An optional `topic/<slug>` tag** — the taxonomy plan notes Research notes
  "may gain an optional topic/<slug> tag" once a Topic/Industry note type is
  resolved; that type remains an open question (`Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Open questions"), not decided or
  added here.
- **Any Second Brain application UI for creating Research notes** — this is
  an Obsidian-native authoring experience, not a Second Brain screen. The
  prototype's unrelated `my-day-reads.html` ("Important Reads") screen is
  not touched or extended by this story.
- **Frontmatter schema validation/enforcement tooling** — per the taxonomy
  plan's own non-goals, this remains a writing convention until real content
  exists to validate against.

## Notes

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked; the only name-adjacent screen
(`my-day-reads.html`, "Important Reads") is unrelated (REQ-SB-12's flagged-
notes concept, not book/article Research notes). Same shape as
`REQ-SB-07/10/14/15-US-01`.

**Why `gate: clear`:** no MUST-FLAG trigger fired.
1. No material assumption — the schema, the manual-entry-only scope, and
   the "no customer/company link" decision are all already resolved in the
   PRD and the taxonomy plan; this story cites, it does not invent.
2. REQ-SB-17 is finalised in the PRD — no `<!-- Draft -->` marker.
3. N/A (architect/ADR trigger) — this story is expected to extend
   `Templates/`/the guide note, both already established by ADR-006; no new
   top-level vault-structure decision is anticipated, though the final call
   remains the architect's at `/plan-tasks`.
4. No `ESCALATIONS.md` entry written.
5. Not oversized — one template file plus one guide-note addition, smaller
   than the already-`Done` `REQ-SB-15-US-01` (four templates plus the guide
   note from scratch).
6. N/A (coder trigger).
7. No contradictory inputs.
8. No genuinely unclear or multiple-equally-valid scoping question — the one
   candidate scoping call (extend the existing guide note vs. author a new,
   Research-specific one) was resolved with a clear, defensible rationale
   (see `## Scoping decision` above), not a genuine trigger-8 case.

gate: clear 2026-08-11 — no triggers fired (schema and scope fully resolved
in the PRD/taxonomy plan/MEMORY.md, no new ADR anticipated, no assumptions,
requirement finalised, no contradictory inputs, smaller than the Done
REQ-SB-15-US-01 precedent it extends).

---

**Architect update (2026-08-11, `/plan-tasks` step 1) — `gate: clear`
confirmed, no ADR.** This is a direct, same-shape extension of the
already-`Accepted` `ADR-006` (`Templates/` root + `Work/Guides/Manual-
Entry-Guide.md`) — a fifth template file and a fifth guide-note section,
no new top-level vault root, no new plugin, no new structural boundary.
`architecture.md`'s "Vault Content Conventions — Templates & In-Vault Guide
(REQ-SB-15)" section was extended in place with a short REQ-SB-17 addendum
(same pass) rather than a new ADR. `Templates/Customer.md` and
`Work/Guides/Manual-Entry-Guide.md` were read in full to confirm the exact
placeholder convention (`REPLACE_WITH_...`) and section shape (`**Folder:**
... · **Template:** ...` + explanatory paragraph) this story's tasks must
match field-for-field.

**Architecture scope:** §Data Model → "Vault Content Conventions —
Templates & In-Vault Guide (REQ-SB-15)" (the REQ-SB-17 addendum). Bounds
the decomposer/coder to exactly:
- **New file:** `Templates/Research.md`, in the real vault at
  `VAULT_PATH` (`C:\myWorx\Moussa MD\Moussa Brain\Templates\Research.md`),
  sibling to the existing `Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`. Frontmatter: `type: Research`,
  `title:`/`author:` placeholders following the existing
  `REPLACE_WITH_...` convention, `tags: [kind/research]`. Body: free-form
  (matching `# {{title}}` heading convention already used), no forced
  section headings, and — per the story's own Constraints — **no**
  customer/company frontmatter field, tag, or wikilink placeholder
  anywhere in the file.
- **Edit location:** `Work/Guides/Manual-Entry-Guide.md`
  (`C:\myWorx\Moussa MD\Moussa Brain\Work\Guides\Manual-Entry-Guide.md`) —
  additive only: (a) update the opening paragraph's "four note types"
  count/list to five, adding Research; (b) append a new `## Research`
  section after the existing `## Consumption-Snapshot` section, matching
  the same `**Folder:** \`Work/Researches/\` · **Template:**
  \`Templates/Research.md\`` line + short explanatory-paragraph shape the
  four existing sections use. The four existing sections and the "How to
  insert a template" numbered steps are untouched.
- No `src/backend`/`src/frontend` changes — vault content only, as the
  story's own Constraints already state.

---

**Decomposer update (2026-08-11, `/plan-tasks` step 2) — status advanced to
`Ready`; `gate` stays `clear`.** All 4 scenarios were tightened and locked
as `REQ-SB-17-US-01-AC-01` through `AC-04` — every AC-ID tag appended
immediately after its scenario's closing Gherkin fence, locked by default
(no AC marked `locked: false`). Decomposed into 2 tasks, mirroring
`REQ-SB-15-US-01`'s T01/T02 template+guide shape exactly:

- `REQ-SB-17-US-01-T01` — `Templates/Research.md`, matching the
  architecture scope's schema/placeholder/no-customer-link spec
  field-for-field. Verifies AC-01 (schema match), AC-03 (unfilled
  placeholders still valid YAML), AC-04 (no customer/company link
  anywhere in the file). `depends_on: []`.
- `REQ-SB-17-US-01-T02` — the additive fifth `## Research` section (plus
  the opening-paragraph count/list edit) in
  `Work/Guides/Manual-Entry-Guide.md`, citing T01's actual file path/target
  folder. Verifies AC-02 (guide note explains the type and its template).
  `depends_on: [REQ-SB-17-US-01-T01]` (must describe T01's actual output).

**AC → verification mapping:** AC-01 and AC-03 and AC-04 (T01), AC-02
(T02) — every locked AC has at least one tagged step; `depends_on` is
acyclic (T01 → T02, no cycles).

**Status vs. gate:** all three status-advance preconditions are met (every
AC locked; every locked AC has a tagged verification step; `depends_on` is
acyclic), so `status: Draft → Ready` and both task files were written
directly at `status: Ready` (lockstep, per the decomposer's own mandatory
behaviour). `gate` stays `clear` — no MUST-FLAG trigger fired during this
pass either (this story's own scope is unchanged from the architect's
`gate: clear` confirmation; no new ADR, no material assumption, no
contradictory input, no unclear/multiple-valid-breakdown question — the
two-task split is the only reasonable one, directly mirroring
`REQ-SB-15-US-01`'s own precedent). No `REVIEW-QUEUE.md`/`ESCALATIONS.md`
entry written for this story.

---

**Product-owner pass (`/plan-sprints`), 2026-08-11.** Grouped into
**SPRINT-007** alongside `REQ-SB-16-US-01` — see that sprint file for full
grouping rationale and sizing. `sprint: SPRINT-007` written above
(bidirectional link).

---

**Coder pass (`/implement-sprint`, SPRINT-007), 2026-08-11 — status set to
`Done`; `gate` stays `clear`.** Both tasks built and verified live against
the real vault (`VAULT_PATH`): `Templates/Research.md` matches the resolved
schema field-for-field, both placeholders remain valid YAML unfilled, no
customer/company link of any kind appears anywhere in the file (AC-01/
AC-03/AC-04); `Work/Guides/Manual-Entry-Guide.md` gained a correct,
additive fifth `## Research` section plus the updated five-note-types
opening paragraph, with the four pre-existing sections and the "How to
insert a template" steps byte-for-byte unchanged (AC-02). All four locked
ACs verified `PASS`. No `ESCALATIONS.md`/new `REVIEW-QUEUE.md` entry — no
trigger fired.
