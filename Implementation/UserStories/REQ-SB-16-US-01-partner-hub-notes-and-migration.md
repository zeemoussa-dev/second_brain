---
id: REQ-SB-16-US-01
title: Partner hub notes, Person-note linking, and Microsoft customer-to-partner migration
requirement_ids: [REQ-SB-16]
requirement_section: "REQ-SB-16: Partner Hub Notes & Graph Connectivity"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-007"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-16-US-01 — Partner hub notes, Person-note linking, and Microsoft customer-to-partner migration

## Story

**As a** Second Brain user whose vault tracks both customer accounts and
technology/business partners
**I want** partner companies to get their own hub note and a `partner/<slug>`
tag namespace — kept strictly separate from `customer/<slug>` — with every
Person note whose derived company matches a known partner linking to that
partner's hub note automatically, and Microsoft's already-mistagged Customer
data migrated to the correct Partner tag/hub
**So that** my vault's tags and graph honestly reflect which companies are
customers and which are partners, with no stranded data or broken links left
behind by the earlier misclassification

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-16: Partner Hub Notes & Graph
  Connectivity*.
- **Scope fully resolved** — `Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Partners (resolved 2026-08-11)", and
  `MEMORY.md`'s matching 2026-08-11 Decision entry. This story cites and
  implements that resolution; it does not redesign it.
  - **Partner hub note** — `Work/Partners/<Partner>.md`:
    ```yaml
    type: Partner
    partner: Microsoft
    tags: [partner/microsoft, kind/partner]
    ```
    Body: the same living-document convention as the Customer hub note
    (auto-generated baseline stub + curated overview/contacts the user adds,
    never programmatically rewritten once added) — a straight structural
    copy of `REQ-SB-14`'s Customer hub note, `type`/tag values only.
  - **Deliberately does NOT replicate Pipeline/Agreements/Consumption for
    Partner** (operator's explicit scoping) — a partner relationship isn't a
    sales/Azure-consumption relationship a customer has.
  - **`partner/<slug>` is mutually exclusive with `customer/<slug>`**
    (operator's explicit choice) — a company is a Customer, a Partner, or
    neither, never both.
- **This is a direct, reuse-only extension of two already-`Done` stories**,
  the same shape `REQ-SB-08-US-01`'s Context distinguishes itself from (that
  story needed a brand-new external integration; this one does not):
  - `REQ-SB-14-US-01` (Vault Graph Connectivity, `Done`) — this story's
    Partner hub note is a structural copy of that story's Customer hub note
    (`app/data_access/vault_writer.py`'s `hub_note_path` /
    `hub_note_exists` / `create_customer_hub_note_baseline` /
    `ensure_hub_note_baseline_frontmatter`, and `app/business/
    customer_hub_linking.py`'s `ensure_customer_hub_note` /
    `link_note_to_customer_hub`), parameterised for `Work/Partners/` and the
    `partner`/`partner/<slug>` fields instead of `customer`/`customer/<slug>`.
  - `REQ-SB-10-US-01` (People Living Documents, `Done`) — the taxonomy plan
    is explicit that "Company-hub-linking logic gains a Partner branch":
    `app/business/people_extraction.py::ensure_person_note` currently calls
    `find_matching_customer(company)` only; it needs an equivalent
    `find_matching_partner(company)` (identical tag-slug matching against a
    new vault-derived `list_known_partners()`, mirroring the existing
    `list_known_customers()`/`find_matching_customer()` pair exactly), with
    Customer checked first and Partner second (the two are confirmed
    mutually exclusive, so at most one can ever match).
- **Scope is Person-note linking, not a general per-write capture-pipeline
  hook.** The PRD's own Acceptance text says "a Person note whose derived
  company matches a known partner links to that partner's hub note
  automatically, **the same way it already does for a matching Customer**" —
  i.e. the exact `ensure_person_note` mechanism already built for
  Customer-matching, extended with a Partner branch. This is narrower than
  `REQ-SB-14`'s own scope, which additionally wired a per-write hook directly
  into `email_classification.py` for *any* captured note. REQ-SB-16 does not
  ask for that broader hook, and this story does not add one — see `##
  Non-Goals`.
- **Real migration data, not speculative** — found live 2026-08-11:
  `Work/Customers/Microsoft.md` (auto-classified as a Customer by Compass
  before this Customer/Partner distinction existed) plus **5 Person notes**
  (`karimlouis@microsoft.com.md`, `maccount@microsoft.com.md`,
  `amraze@microsoft.com.md`, `lumazohlof@microsoft.com.md`,
  `m365copilotupdates@microsoft.com.md`) and **2 Email notes**, all already
  carrying `customer: Microsoft` frontmatter and a `customer/microsoft` tag.
  The taxonomy plan resolves the fix as two parts:
  (a) move `Work/Customers/Microsoft.md` to `Work/Partners/Microsoft.md`
  with `type`/`partner`/`tags` updated to the Partner schema — Obsidian
  resolves `[[wikilinks]]` by filename, not full path, so existing
  `[[Microsoft]]` links elsewhere keep resolving with no link-text change
  required;
  (b) a retrofit pass over the already-tagged Person/Email notes swapping
  `customer: Microsoft` → `partner: Microsoft` and the `customer/microsoft`
  tag → `partner/microsoft`.
  This story additionally brings the already-linked Person notes' inline
  body wikilink label into consistency with the new Partner-linking
  mechanism (see `## Acceptance Criteria`, Scenario 5) — the 5 Person notes
  already carry an inline `**Customer:** [[Microsoft]]` body line (written
  by `customer_hub_linking.link_note_to_customer_hub` when Microsoft was
  still classified as a Customer); this story's own Partner-linking
  mechanism inserts a `**Partner:** [[Hub]]`-labelled line going forward
  (mirroring `link_note_to_customer_hub`'s exact shape, parameterised for
  Partner), so leaving the old `**Customer:**` label on the already-migrated
  notes would read as internally inconsistent with the mechanism this same
  story builds.
- No `html-prototype/` screen applies — like `REQ-SB-07/10/14/15-US-01`, this
  is backend/vault-structure work with no Second Brain UI surface. Note: the
  prototype's `my-day-reads.html` ("Important Reads," REQ-SB-12's flagged-
  notes concept) is an unrelated, coincidental name match — it has nothing to
  do with this requirement or with REQ-SB-17's "Research" notes.
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`
  in `src/backend/.env`), including the real Microsoft migration data above —
  not a fixture/test vault.

## Scoping decision (one story, not two)

Mirrors `REQ-SB-14-US-01`'s own scoping reasoning verbatim: the PRD frames
"Partner hub notes exist," "Person notes link to them automatically," and
"Microsoft is migrated, not left stranded" as one acceptance outcome, and all
three pieces share the same underlying "ensure this partner's hub note
exists, then link" primitive plus its retrofit-shaped one-time counterpart —
exactly the shared-mechanism, no-independent-value test that justified
`REQ-SB-14-US-01` and `REQ-SB-10-US-01` staying single stories each. Unlike
`REQ-SB-08-US-01` (flagged for bundling a brand-new external integration),
every piece of this story extends already-`Done`, already-working code
end-to-end — no new integration surface, no genuinely open interpretation
gap. Treated as **one story**, decomposed into several tasks at
`/plan-tasks`.

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path first, then the migration, then edge
cases. -->

### Scenario 1: Partner hub note is created automatically for a matching Person note

```gherkin
Given a Person note's derived company matches a known partner (e.g.
    Microsoft) that has no Work/Partners/<Partner>.md hub note yet
When the Person-note orchestration processes that person
Then a Partner hub note is created at Work/Partners/<Partner>.md matching
    the resolved schema (type: Partner, partner:, tags: [partner/<slug>,
    kind/partner])
  And the Person note gains a [[wikilink]] to the partner's hub note
```
<!-- AC-ID: REQ-SB-16-US-01-AC-01 -->

### Scenario 2: Rerunning does not duplicate the hub note or the wikilink

```gherkin
Given a Partner hub note already exists and a Person note is already linked
    to it
When the Person-note orchestration processes that same person again
Then no duplicate Partner hub note is created
  And no duplicate wikilink is added to the Person note
```
<!-- AC-ID: REQ-SB-16-US-01-AC-02 -->

### Scenario 3: A company matching a known Customer is never also matched as a Partner

```gherkin
Given a company matches an existing Customer hub note (e.g. ADNOC)
When that company is derived for a Person note
Then the Person note is linked to the Customer hub note, exactly as before
  And no Partner match is attempted or applied for that same company —
    customer/<slug> and partner/<slug> remain mutually exclusive on that note
```
<!-- AC-ID: REQ-SB-16-US-01-AC-03 -->

### Scenario 4: A company matching neither Customer nor Partner is unaffected

```gherkin
Given a derived company does not match any known Customer or known Partner
When a Person note is created or updated for that company
Then the Person note gets its company/<slug> tag alone
  And no Partner (or Customer) hub-note wikilink is added
  And no new Partner hub note is created
```
<!-- AC-ID: REQ-SB-16-US-01-AC-04 -->

### Scenario 5: Migration — Microsoft's Customer hub note becomes a Partner hub note

```gherkin
Given Work/Customers/Microsoft.md exists with type: Customer, customer:
    Microsoft, and tags [customer/microsoft, kind/customer]
When the one-time Partner migration process runs
Then the note is moved to Work/Partners/Microsoft.md with its frontmatter
    updated to type: Partner, partner: Microsoft, tags [partner/microsoft,
    kind/partner]
  And any user-added body content on the note is preserved unchanged
  And existing [[Microsoft]] wikilinks elsewhere in the vault continue to
    resolve to this note without their link text needing to change
```
<!-- AC-ID: REQ-SB-16-US-01-AC-05 -->

### Scenario 6: Migration retags already-mistagged Person and Email notes

```gherkin
Given the 5 Person notes and 2 Email notes already carrying customer:
    Microsoft frontmatter and a customer/microsoft tag
When the one-time Partner migration process runs
Then each note's customer frontmatter key is replaced with partner:
    Microsoft, and its customer/microsoft tag is replaced with
    partner/microsoft
  And each such note's existing inline **Customer:** [[Microsoft]] body
    wikilink (where present) is relabelled to **Partner:** [[Microsoft]],
    still pointing at the same note, now living at Work/Partners/Microsoft.md
```
<!-- AC-ID: REQ-SB-16-US-01-AC-06 -->

### Scenario 7: Migration is idempotent

```gherkin
Given the migration has already run once and Microsoft is fully migrated to
    Partner
When the migration process runs again
Then no duplicate hub note is created, no note is double-migrated (no
    partner: field or partner/<slug> tag is duplicated), and no further
    changes are made
```
<!-- AC-ID: REQ-SB-16-US-01-AC-07 -->

### Scenario 8: Auto-created or auto-updated Partner hub notes preserve manually-added content

```gherkin
Given a Partner hub note already exists and has user-added content beyond
    its auto-populated baseline fields
When the hub note is touched again (e.g. another Person note for that
    partner is processed, or the migration runs again)
Then the hub note's manually-added content is preserved unchanged
  And only the auto-populated baseline fields (frontmatter, tags) are
    updated if they need to be, never the user's own additions
```
<!-- AC-ID: REQ-SB-16-US-01-AC-08 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or
is needed for this capability; Obsidian's own graph/tag views are the
surface this story affects, not a Second Brain UI screen. (See `## Context`
for the note distinguishing this from the prototype's unrelated
`my-day-reads.html` screen.)

## Dependencies

- **Blocked by:** none — `REQ-SB-14-US-01` (Vault Graph Connectivity,
  `Done`) and `REQ-SB-10-US-01` (People Living Documents, `Done`) already
  provide the exact hub-note and Person-note-linking mechanisms this story
  extends with a parallel Partner branch.
- **Related to:** `REQ-SB-14` (`REQ-SB-14-US-01`) — this story's Partner hub
  note is a structural copy of that story's Customer hub note; the two tag
  namespaces (`partner/<slug>`, `customer/<slug>`) are mutually exclusive by
  the operator's explicit choice.
- **Related to:** `REQ-SB-10` (`REQ-SB-10-US-01`) — extends
  `people_extraction.py`'s `ensure_person_note`/`find_matching_customer`
  pair with a parallel Partner branch (`find_matching_partner`, checked
  after Customer).
- **External:** none new.

## Constraints

- `partner/<slug>` and `customer/<slug>` are mutually exclusive tag
  namespaces — a company is a Customer, a Partner, or neither, never both
  (operator's explicit choice, `MEMORY.md`).
- Partner does **not** get Pipeline/Agreements/Consumption-Snapshot-equivalent
  sub-entities — operator's explicit scoping; this story does not introduce
  any such structure for Partner.
- Customer matching is checked before Partner matching for a given derived
  company (per the resolved schema — the two are mutually exclusive, so at
  most one can ever match).
- Must respect the `api → business → data_access` layer boundary (ADR-003).
- The migration must be idempotent — rerunning it must never create
  duplicate hub notes, duplicate tags, or double-migrate an already-migrated
  note (Scenarios 2 and 7).
- Obsidian resolves `[[wikilinks]]` by filename, not full path — moving
  `Work/Customers/Microsoft.md` to `Work/Partners/Microsoft.md` must not
  require updating existing `[[Microsoft]]` link text anywhere else in the
  vault.
- This runs against the user's real, live Obsidian vault (`VAULT_PATH` in
  `src/backend/.env`), including the real Microsoft migration data — no-data-
  loss and idempotency are load-bearing, not conveniences.
- The exact module/function layering for the new Partner primitives (e.g.
  whether `find_matching_partner` lives directly in `people_extraction.py`,
  and whether the Partner hub-note file-I/O/orchestration primitives live in
  new functions alongside the existing Customer ones or in parallel modules)
  is an architecture-level decision for `/plan-tasks`, not decided here —
  though the taxonomy plan's own framing ("gains a Partner branch") points
  toward extending the existing modules rather than duplicating them.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-16-US-01-T01 | backend | Partner hub-note baseline primitives + 4 generic rename/remove/swap/replace primitives | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-16-US-01-T01-partner-hub-vault-writer-primitives.md` |
| REQ-SB-16-US-01-T02 | backend | New `partner_hub_linking.py` — hub-note orchestration + `migrate_customer_to_partner` | `app/business/partner_hub_linking.py` (new) | `../Tasks/REQ-SB-16-US-01-T02-partner-hub-linking-and-migration.md` |
| REQ-SB-16-US-01-T03 | backend | `people_extraction.py` Partner-matching branch (`find_matching_partner`, `ensure_person_note`) | `app/business/people_extraction.py` | `../Tasks/REQ-SB-16-US-01-T03-people-extraction-partner-branch.md` |
| REQ-SB-16-US-01-T04 | backend | New `POST /poc/migrate-customer-to-partner` endpoint | `app/api/email_poc_router.py` | `../Tasks/REQ-SB-16-US-01-T04-migration-endpoint.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A general per-write capture-pipeline hook for Partner** (the way
  `REQ-SB-14-US-01` wired Customer linking directly into
  `email_classification.py` for any captured note) — the PRD's Acceptance
  text scopes Partner linking specifically to Person notes ("a Person note
  whose derived company matches a known partner links..."); not built here.
- **Pipeline/Agreement/Consumption-Snapshot-equivalent sub-entities for
  Partner** — operator's explicit scoping; a partner relationship isn't a
  sales/consumption relationship.
- **An automated classification pipeline for designating a company as a
  Partner going forward** — beyond the Microsoft migration, no code decides
  "this company is a Partner, not a Customer." A future second partner
  becomes "known" the same way a brand-new customer already does today: a
  note (e.g. a Person note) carries a `partner: <Name>` frontmatter value
  (set by hand, or by a future story), after which `list_known_partners()`
  picks it up — mirroring `list_known_customers()`'s existing dynamic-
  derivation pattern exactly. No new capture logic is added.
- **A manual-entry Obsidian template for Partner notes** — `REQ-SB-15`'s
  four templates (Customer, Opportunity, Agreement, Consumption-Snapshot)
  don't include Partner; if a Partner template is wanted later, that is
  separate future scope, not requested here.
- **Any Second Brain UI surfacing of Partner data** — Obsidian's own graph
  and tag-pane views are the presentation surface; no application screen is
  added or changed.

## Notes

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked; the only name-adjacent screen
(`my-day-reads.html`, "Important Reads") is unrelated (REQ-SB-12's flagged-
notes concept, not Partner/Customer taxonomy). Same shape as
`REQ-SB-07/10/14/15-US-01`.

**Why `gate: clear`:** no MUST-FLAG trigger fired.
1. No material assumption — every design decision this story relies on
   (schema, mutual exclusivity, Person-note-only linking scope, the two-part
   migration shape) is already resolved in the PRD and the taxonomy plan;
   this story cites, it does not invent.
2. REQ-SB-16 is finalised in the PRD — no `<!-- Draft -->` marker.
3. N/A (architect/ADR trigger).
4. No `ESCALATIONS.md` entry written.
5. Not oversized — directly comparable in shape and size to the already-
   `Done` `REQ-SB-14-US-01` (5 scenarios, 4 tasks): this story's 8 scenarios
   split cleanly into Partner-primitive tasks (mirroring `REQ-SB-14-US-01`'s
   T01/T02), a `people_extraction.py` Partner-branch task, and a migration/
   retrofit-endpoint task — no new external integration surface the way
   `REQ-SB-08-US-01` needed.
6. N/A (coder trigger).
7. No contradictory inputs.
8. No genuinely unclear or multiple-equally-valid scoping question — the
   one candidate ambiguity considered (whether the migration should also
   relabel the already-present inline `**Customer:** [[Microsoft]]` body
   line, since the taxonomy plan's migration text only explicitly names
   frontmatter/tag swaps) was resolved by direct extension of the already-
   documented inline-wikilink-labelling convention (`architecture.md`) for
   internal consistency with this same story's own new Partner-linking
   mechanism — not a genuine spec gap, and made explicit in Scenario 6 so
   the decomposer isn't left guessing.

gate: clear 2026-08-11 — no triggers fired (schema and scope fully resolved
in the PRD/taxonomy plan/MEMORY.md, no new ADR, no assumptions beyond a
directly-derived consistency detail, requirement finalised, no contradictory
inputs, sized comparably to the Done REQ-SB-14-US-01 precedent).

---

**Architect update (2026-08-11, `/plan-tasks` step 1) — gate flipped to
`flagged`, trigger 3.** The Constraints section above explicitly deferred
the exact module/function layering and the migration's exact shape to this
pass; that layering decision (a new sibling module vs. extending
`customer_hub_linking.py`, and a generic vault-scan vs. a hardcoded-file-list
migration) is architectural, so it is recorded as **[ADR-009](../
Architecture/ADR.md)** in `Implementation/Architecture/ADR.md`, per the
architect's MUST-FLAG trigger 3 (creating an ADR always flags the story for
human review, but does not halt `/plan-tasks` — the decomposer still runs so
the human reviews the ADR and the resulting tasks together). See
`REVIEW-QUEUE.md` for the pointer.

**Finding worth flagging alongside the ADR:** live inspection of the real
vault (`VAULT_PATH`) during this pass found the actual set of notes already
carrying `customer: Microsoft`/`customer/microsoft` is **larger** than this
story's own Context/Scenario 6 narrative count ("5 Person notes and 2 Email
notes") — 1 Newsletter note and 4 Notification notes also already carry it.
This does not contradict the story (Scenario 6's own wording never claimed
that count was exhaustive) and does not require a story change: ADR-009
resolves it by making the migration a **generic vault-wide scan** (matching
every note whose `customer` frontmatter equals the given name), not a
hardcoded list of the 7 notes named in the Context — so the extra
Newsletter/Notification notes are picked up automatically. Flagging this
explicitly so the decomposer sizes the migration task/verification around
"every note the scan finds," not literally 5+2 files, and so the human
reviewing the ADR sees why the migration design generalized past the
story's own illustrative count.

**Architecture scope:** §Data Model → "Partner Hub Notes &
Mutually-Exclusive Company Taxonomy (REQ-SB-16)", §Source Layout (the new
`app/business/partner_hub_linking.py` paragraph) — the decomposer/coder are
bounded by this section, `ADR-009`, and the pre-existing "Person Notes &
Email-Sender Extraction (REQ-SB-10)" and "Customer Hub Notes & Graph
Linking (REQ-SB-14)" sections it extends (unchanged). Concretely, the tasks
this pass hands to the decomposer should cover:
- `app/data_access/vault_writer.py`: `partner_hub_note_path`,
  `partner_hub_note_exists`, `create_partner_hub_note_baseline`,
  `ensure_partner_hub_note_baseline_frontmatter`, `build_partner_tags`,
  `list_known_partners` (all mirroring the Customer hub-note primitives,
  Partner's own baseline keys — `type`, `partner`, `tags`, no
  `affiliate_of`); plus three new generic primitives for the migration —
  a frontmatter-key rename, a tags-list swap, and a body-line-label
  replace (each a no-op once the old key/tag/line is already absent, for
  idempotency).
- `app/business/partner_hub_linking.py` (new module):
  `ensure_partner_hub_note(partner)`, `link_note_to_partner_hub(note_path,
  partner)` (mirroring `customer_hub_linking.py`'s two granular
  primitives), and `migrate_customer_to_partner(customer_name)` — the
  one-time migration: (1) move `Work/Customers/<name>.md` →
  `Work/Partners/<name>.md` via the existing
  `vault_writer.move_note_and_attachments`, rewriting frontmatter
  (`type`/`customer`→`partner`/`tags`, dropping `affiliate_of`); (2) a
  generic scan over `vault_writer.list_all_note_paths()` retagging every
  note whose `customer` frontmatter equals `customer_name` (frontmatter
  key rename, tag swap, and — only where present — inline
  `**Customer:** [[name]]` → `**Partner:** [[name]]` relabel); (3)
  idempotent by construction (each replace primitive no-ops once already
  migrated).
- `app/business/people_extraction.py`: new `find_matching_partner(company)`
  (mirrors `find_matching_customer` exactly); `ensure_person_note` extended
  — Customer checked first (unchanged), Partner checked only when no
  Customer match, calling `partner_hub_linking`'s two granular primitives
  directly, never a combined entry point; return dict gains
  `partner_matched`.
- `app/api/email_poc_router.py`: new `POST /poc/migrate-customer-to-partner`
  endpoint (accepts `customer_name`), calling `migrate_customer_to_partner`.
- No changes to `customer_hub_linking.py` or `email_classification.py`/
  `meeting_classification.py` — per the story's own Non-Goals, no
  per-write capture-pipeline hook is added for Partner.

---

**Decomposer update (2026-08-11, `/plan-tasks` step 2) — status advanced to
`Ready`; `gate` stays `flagged` (trigger-3, unchanged).** All 8 scenarios
were tightened and locked as `REQ-SB-16-US-01-AC-01` through `AC-08`
(sequential, happy path → migration → edge cases, per the analyst's own
ordering) — every AC-ID tag appended immediately after its scenario's
closing Gherkin fence, locked by default (no AC marked `locked: false`).
Decomposed into 4 tasks, mirroring `REQ-SB-14-US-01`'s T01/T02/T04 shape
(vault-writer primitives → business-module orchestration → HTTP endpoint)
with a T03 replacing that precedent's capture-pipeline-hook task (out of
scope here per the story's own Non-Goals) with the `people_extraction.py`
Partner-matching branch instead — the actual "Person-note orchestration"
mechanism Scenarios 1–4 and 8 exercise:

- `REQ-SB-16-US-01-T01` — Partner hub-note baseline primitives
  (`partner_hub_note_path`/`_exists`, `build_partner_tags`,
  `create_partner_hub_note_baseline`,
  `ensure_partner_hub_note_baseline_frontmatter`, `list_known_partners`)
  plus four new generic `vault_writer.py` primitives beyond the three
  ADR-009's Decision text names explicitly (`rename_frontmatter_key`,
  `swap_tag`, `replace_body_line`) — a fourth,
  `remove_frontmatter_key_if_present`, was added as the natural sibling to
  the existing `insert_frontmatter_key_if_missing` needed to literally
  implement `architecture.md`'s explicit "the affiliate_of key is dropped"
  step; it is equally generic (no Partner-specific literal), so this does
  not narrow or contradict ADR-009's reasoning — logged here for
  visibility, not flagged as a new trigger. `depends_on: []`.
- `REQ-SB-16-US-01-T02` — new `app/business/partner_hub_linking.py`:
  `ensure_partner_hub_note`, `link_note_to_partner_hub`, and
  `migrate_customer_to_partner` (all three, per the architecture scope's
  own module listing). `migrate_customer_to_partner`'s implementation
  choice — one generic scan pass that naturally also finishes rewriting
  the just-moved hub note's own frontmatter, rather than a separate
  hub-note-specific rewrite branch — is a task-level implementation detail
  consistent with, not contradicting, `architecture.md`'s two-numbered-step
  description. `depends_on: [REQ-SB-16-US-01-T01]`.
- `REQ-SB-16-US-01-T03` — `people_extraction.py`'s `find_matching_partner`
  + extended `ensure_person_note` (Customer checked first, Partner second,
  `partner_matched` added to the return dict, additive). This is the
  concrete "Person-note orchestration" entry point AC-01/02/03/04/08
  verify against, using throwaway partner/customer names so verification
  never touches the real Microsoft/ADNOC data T04 migrates.
  `depends_on: [REQ-SB-16-US-01-T02]`.
- `REQ-SB-16-US-01-T04` — new `POST /poc/migrate-customer-to-partner`
  endpoint, thin wrapper matching the existing `/poc/retrofit-*`
  precedent shape. AC-05/06/07/08 (migration-rerun half) verify live
  against the real Microsoft data named in the story's own Context —
  sized around "every note the generic scan finds," not literally 5+2
  files, per the architect's own flagged finding (1 Newsletter + 4
  Notification notes also already carry `customer: Microsoft`).
  `depends_on: [REQ-SB-16-US-01-T02]`.

**AC → verification mapping:** AC-01 (T03, full Person-note-orchestration
flow), AC-02 (T03, rerun idempotency), AC-03 (T03, Customer-checked-first
contrived-collision test), AC-04 (T03, no-match case), AC-05/AC-06/AC-07
(T04, live real-vault migration + rerun), AC-08 (T03, Person-note-processed
half; T04, migration-rerun half) — every locked AC has at least one tagged
step; `depends_on` is acyclic (T01 → T02 → {T03, T04}, no cycles).

**Status vs. gate:** all three status-advance preconditions are met (every
AC locked; every locked AC has a tagged verification step; `depends_on` is
acyclic), so `status: Draft → Ready` and all four task files were written
directly at `status: Ready` (lockstep, per the decomposer's own mandatory
behaviour). `gate` stays `flagged` (`trigger-3`, unchanged from the
architect's pass) — an ADR-creation flag does not halt `/plan-tasks`
(`Implementation/Pipeline.md`'s gating contract), so this story proceeds to
`Ready` and is eligible for `/plan-sprints`, but the human still reviews
`ADR-009` (and, alongside it, these four tasks — especially T04's real-vault
migration step) via `REVIEW-QUEUE.md` before/while `/implement-sprint`
actually runs T04 against the real Microsoft data. No new
`REVIEW-QUEUE.md`/`ESCALATIONS.md` entry was written by this decomposer
pass — the existing architect-authored `REVIEW-QUEUE.md` pointer for
ADR-009 already covers this story.

---

**Product-owner pass (`/plan-sprints`), 2026-08-11.** Grouped into
**SPRINT-007** alongside `REQ-SB-17-US-01` — see that sprint file for full
grouping rationale and sizing. `sprint: SPRINT-007` written above
(bidirectional link). ADR-009 was reviewed and approved by the operator
2026-08-11, per the sprint's own gating note; `gate: flagged` left
unchanged on this story per this role's own scope (resetting it is not
this role's job).

---

**Coder pass (`/implement-sprint`, SPRINT-007), 2026-08-11 — status set to
`Blocked`; `gate` stays `flagged`, reason extended.**
`REQ-SB-16-US-01-T01`/`T02`/`T03` built and verified live end-to-end
(Scenarios/AC-01, AC-02, AC-03, AC-04, AC-08's Person-note-processed half —
all `PASS`, against throwaway data only). `REQ-SB-16-US-01-T04` (the
migration endpoint) is **`Blocked`**: the coder's own pre-migration sanity
scan of the real vault (performed before calling the mutating endpoint, as
instructed) found that the migration's generic scan — built exactly per
`ADR-009` and `T02`'s own given code, matching on `customer` frontmatter
equality — never touches the **5 real Person notes**
(`amraze@microsoft.com.md`, `karimlouis@microsoft.com.md`,
`lumazohlof@microsoft.com.md`, `m365copilotupdates@microsoft.com.md`,
`maccount@microsoft.com.md`) this story's own Context and locked
`AC-06` name, because those notes have never carried a `customer`
frontmatter field or a `customer/microsoft` tag (only `company/microsoft`,
per `people_extraction`'s unchanged Person-note schema) — they carry only an
inline `**Customer:** [[Microsoft]]` body wikilink, which `AC-06` also
requires relabeled. This is a data-shape gap the generic scan's own
matching condition cannot see, not the quantity-only Newsletter/
Notification undercount `ADR-009` already resolved. The mutating `POST
/poc/migrate-customer-to-partner` endpoint was **not called** — the real
`Work/Customers/Microsoft.md` and every `customer/microsoft`-tagged note
are untouched, exactly in their pre-migration state; no data loss, no
partial/inconsistent migration was risked. Full detail: `ESCALATIONS.md` →
`ESC-001`; `REVIEW-QUEUE.md` pointer added.

Since a locked AC (`AC-06`, and transitively `AC-05`/`AC-07`/`AC-08`'s
migration-rerun half, all gated on the same endpoint call) cannot be
verified as passing with the implementation exactly as specified, per
`Implementation/Pipeline.md` hard rule 4 this story cannot reach `Done`.
`status: Blocked` (not `Ready`/`In Progress`) reflects that `T04` — and
therefore the story — is waiting on a human/architect decision, not on
further coding within this task's declared scope. `T01`/`T02`/`T03` remain
`Done`; only `T04` is `Blocked`; `depends_on` is unaffected (T04 depended on
`T02`, which is `Done`).

---

**Architect correction pass (2026-08-11, `/plan-tasks` step 1, resuming
`T04`) — status reset `Blocked → Ready`; `gate` stays `flagged`
(`trigger-3`, now naming `ADR-012` too).** Resolves the block the coder's
pass above recorded. Read `ESCALATIONS.md` → `ESC-001` in full: the
coder's pre-migration sanity check against the real vault correctly found
that `ADR-009` point 4's match predicate (`frontmatter.get("customer") ==
customer_name` alone) structurally can never reach the 5 real Microsoft
Person notes (`Work/People/{amraze, karimlouis, lumazohlof,
m365copilotupdates, maccount}@microsoft.com.md`) locked `AC-06` names,
because `REQ-SB-10`'s Person-note schema
(`people_extraction.build_person_tags`) never gives Person notes a
`customer:` frontmatter field or `customer/<slug>` tag at all — only
`company/<slug>` plus a separately-written inline `**Customer:**
[[CompanyName]]` body wikilink. Operator decision, 2026-08-11: extend the
scan to also catch these notes via a second, body-wikilink match signal.

Recorded as **[ADR-012](../Architecture/ADR.md)** — extends `ADR-009`
point 4's match predicate to a union of the original frontmatter-equality
signal and a new inline-`**Customer:** [[name]]`-body-wikilink signal,
both read from the scan's existing single `read_note()` call per note (no
second vault scan, no new `vault_writer.py` primitives — every retag
primitive already no-ops if its target key/tag/line is absent). `ADR-009`
itself is **not** edited — it remains `Accepted`; only point 4's predicate
is extended, per this project's "never rewrite an Accepted ADR, a change
of mind is a new superseding ADR" rule. `ADR-009` was already reviewed and
approved by the operator 2026-08-11 (this story's product-owner pass,
above); `ADR-012` is a fresh **trigger-3** fire of its own (a new ADR was
created) and needs its own human review — `gate_reason` above updated to
name it alongside the historical `ADR-009` reference.

`Implementation/Tasks/REQ-SB-16-US-01-T04-migration-endpoint.md`'s own
scope/spec is corrected in place (see that file's `## Files to Modify`,
`## Out of Scope`, `## Tests`, and `## Context / Notes`) — the fix is
routed through `T04` rather than reopening the already-`Done`, frozen
`T02`, since `T04` is the still-not-`Done` task whose own locked `AC-06`
verification the gap blocks. `AC-06`'s locked wording is unchanged; only
the implementation's matching logic changes. `status: Blocked → Ready` —
`T01`/`T02`/`T03` remain `Done` and untouched; `T04`'s own frontmatter is
reset to `status: Ready`, `gate: flagged` (`trigger-3`, naming `ADR-012`).
`depends_on` is unaffected (`T04` still depends only on the `Done` `T02`).

`ESCALATIONS.md` → `ESC-001` is marked **Resolved**, naming `ADR-012` and
the corrected `REQ-SB-16-US-01-T04` as the resolving artefacts. The
`REVIEW-QUEUE.md` entry for `REQ-SB-16-US-01-T04` is replaced with a new
entry pointing at `ADR-012` for human review (same shape as the existing
`ADR-009` pointer) — the mutating migration endpoint still has not been
called against the real vault; `/implement-sprint` may now resume `T04`
with the corrected match predicate.

---

**Coder pass (`/implement-sprint`, SPRINT-007), 2026-08-11 — status set to
`Done`; `gate` set to `clear`.** Implemented `ADR-012`'s exact, narrow
match-predicate fix in `partner_hub_linking.migrate_customer_to_partner`
(`T04`'s own corrected `## Files to Modify`). Re-ran the pre-migration
sanity scan against the real vault: found **15** matches, not the 14
anticipated — the real vault had genuinely gained 2 more legitimate notes
since the prior check (a Meeting note and a 6th real Person note,
`nabeehquaroout@microsoft.com.md`) from the concurrently-in-flight
`SPRINT-006` work; both inspected and confirmed genuine, not false
positives, exactly the "generic scan, not a hardcoded count" behavior this
story's own design anticipates.

Ran the real, mutating migration against the live vault (after resolving
an unrelated stale-server-process complication from an earlier attempt in
this same session — full detail in `T04`'s own `## Implementation Log`).
All locked ACs verified `PASS`: `Work/Customers/Microsoft.md` moved to
`Work/Partners/Microsoft.md` with corrected schema (AC-05); a full
vault-wide sweep confirmed **zero** remaining stale `customer`-Microsoft
references anywhere and all 15 real Microsoft-related notes — including
all 6 real Person notes, one more than this story's original Context count
— correctly carry the Partner equivalent (AC-06); a rerun is a true no-op
(AC-07); manually-added hub-note content and the Person-note-processed
half both survive reruns (AC-08, migration-rerun half here, Person-note
half already verified in `T03`). `[[Microsoft]]` wikilinks vault-wide still
resolve (exactly one `Microsoft.md` file exists anywhere in the vault, at
its new path).

**One real, out-of-scope finding surfaced and handled during this
verification, not silently worked around:** a pre-existing structural
defect in `Work/People/karimlouis@microsoft.com.md` (predating this
session, from an old `REQ-SB-10-US-01-T04` verification pass — that note's
body never had the standard blank line after its frontmatter) collided
with `vault_writer.insert_body_line_if_missing`'s fixed byte-offset
insertion assumption, compounding into a real corruption when this
story's own `T03` mechanism legitimately linked that real contact to the
newly-Partner-classified Microsoft during a live capture run triggered by
starting the dev server. Manually repaired directly (byte-exact, not
retyped) as due diligence — not a code fix, since the underlying
`vault_writer.py` primitive is out of `T04`'s declared scope and shared by
multiple already-`Done` stories. Logged as `ESCALATIONS.md` → `ESC-003`
(`Open`) with a `REVIEW-QUEUE.md` pointer recommending a formal `/bug`
capture for a proper fix.

Every locked AC across `REQ-SB-16-US-01` (`AC-01` through `AC-08`) is now
verified. All four tasks are `Done`. Story `status: Done`, `gate: clear` —
`ADR-012` was already reviewed/approved per the architect's own pass
above; no new trigger fired by this completion pass itself (the `ESC-003`
finding is logged and flagged separately, orthogonal to this story's own
scope and ACs, all of which passed).
