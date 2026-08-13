---
id: REQ-SB-10-US-01
title: Person notes auto-created and updated from email capture, preserving manual edits
requirement_ids: [REQ-SB-10]
requirement_section: "REQ-SB-10: People Living Documents"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: SPRINT-004
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-10-US-01 — Person notes auto-created and updated from email capture, preserving manual edits

## Story

**As a** Second Brain user
**I want** every person I've emailed with to get a Person-type note in my
vault — auto-populated with their name and contact info, tagged and (when their
company is a known customer) wikilinked to that customer's hub note, both for
people already in my captured email and every new sender going forward
**So that** I have a living directory of my contacts that builds itself from
captured email, without me creating a single note by hand, and anything I add
to a person's note myself is never overwritten by a later automated update

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-10: People Living Documents*
- **Schema already resolved** —
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "People
  (resolved 2026-08-11)". This story cites and implements that schema; it does
  not redesign it. Flat notes, `Work/People/<Person>.md` (`People` is just
  another `kind` folder, dynamically discovered by `list_known_kinds()` — no
  code change needed for it to be found):
  ```yaml
  type: Person
  name: Mohamed Eltanany
  email: mohamed.eltanany@core42.ai
  phone: ""
  linkedin: ""
  tags: [company/core42, kind/person]
  ```
  Body starts with an inline wikilink to the company's Customer hub note
  **when the company matches an existing customer** — `**Company:** [[ADNOC]]`
  — reusing REQ-SB-14's `ensure_hub_note_and_link` mechanism/pattern (see
  Constraints below for an important carve-out on how it's reused, not
  verbatim). When the company isn't a known customer (internal Core42
  colleague, a third party like Microsoft/G42), there is no hub note to link
  to yet, so the `company/<slug>` tag stands alone — per `MEMORY.md`'s
  standing "tags AND wikilinks, always, wherever a real link target exists"
  rule (a tag with no link target is a real absence, not an overlooked link).
  Below the link (or, if none, below the frontmatter): role/title, notes,
  personality observations — free-form, user-added, never overwritten by
  automation (REQ-SB-10's own living-document rule).
- **Scope — email half only, meeting-attendee half explicitly out of scope.**
  The PRD text says background agents backfill from "email senders, meeting
  attendees." Meeting-attendee extraction depends on REQ-SB-08 (Meetings
  Capture Pipeline), which doesn't exist yet — there is no Meeting-type note
  to extract attendees from. The taxonomy plan is explicit that "email-based
  backfill can proceed independently now" while "the Meeting-based half is
  real but blocked." This story implements only the email half: retrofitting
  already-captured Email notes' `sender`/`sender_email` fields, plus a
  going-forward per-write hook on the existing email capture pipeline. The
  meeting-attendee half is not invented here; it will need its own story once
  REQ-SB-08 exists (see Non-Goals).
- **Mirrors REQ-SB-14's shape.** Same underlying mechanism used twice: a
  one-time retrofit over already-captured Email notes, and a per-write hook on
  `app/business/email_classification.py` for every future email capture — both
  needing the same "auto-create/auto-update baseline, preserve manual edits"
  behaviour REQ-SB-10's own PRD acceptance text requires (word-for-word the
  pattern REQ-SB-14 replicated for Customer hub notes, extended back to its
  origin — People).
- **Company derivation from a captured Email note.** An Email note's only
  identity data for its sender is `sender` (display name) and `sender_email`
  (address) — there is no separate "company" field anywhere in the existing
  schema. The resolved People schema's own worked example demonstrates the
  only viable source: the sender's email domain (`core42.ai` → tag
  `company/core42`). This is not a judgment call between multiple options —
  it's the one data source that exists and the one the resolved schema already
  shows — so this story specs it as the expected behaviour rather than
  flagging it as an open assumption. The exact string-processing mechanism
  (how a raw domain becomes a company slug/name, and how a domain that clearly
  isn't a real organisation — e.g. a personal/free email provider — is told
  apart from one that is) is left as an architecture-level detail for
  `/plan-tasks`, the same kind of deferral REQ-SB-14 used for its wikilink
  placement mechanics (see Constraints).
- Builds on the already-`Done` capture infrastructure: `app/business/
  email_classification.py` (`REQ-SB-07-US-01`) for the going-forward hook and
  source data, and `app/business/customer_hub_linking.py` /
  `app/data_access/vault_writer.py`'s hub-note primitives (`REQ-SB-14-US-01`)
  for the company-hub-linking half — reused, not reimplemented, subject to the
  carve-out in Constraints.
- No `html-prototype/` screen applies — like `REQ-SB-07-US-01` and
  `REQ-SB-14-US-01`, this is backend/vault-structure work with no user-facing
  screen.
- The retrofit and going-forward hook both touch the user's real, live
  Obsidian vault at the path configured in `src/backend/.env`'s `VAULT_PATH`
  (not read/printed here) — not a fixture/test vault.

## Scoping decision (one story, not two)

Same reasoning `REQ-SB-14-US-01` used for its own one-story-vs-two call: the
retrofit (existing Email notes → Person notes) and the going-forward per-write
hook (new Email notes → Person notes, automatically) share one underlying
operation — "ensure this sender's Person note exists and is up to date,
linking to their company's Customer hub note if one exists" — used once as a
one-time batch and once as a per-write hook. Splitting that shared mechanism
across two stories would separate implementation that has no independent value
on its own: a contact isn't "captured" until both already-seen senders and
every new sender going forward produce a Person note. Treated as **one
story**, decomposed into several tasks at `/plan-tasks`.

## Acceptance Criteria

### Scenario 1: Backfill creates a Person note for an already-captured sender

```gherkin
Given the vault has one or more existing Email notes whose sender_email has
    not yet produced a Person note
When the one-time People backfill process runs
Then a Person note is created at Work/People/<Person>.md for each distinct
    sender email address, with name and email populated from that Email
    note's sender/sender_email fields and the kind/person tag present
  And multiple Email notes sharing the same sender_email produce exactly one
    Person note, not one per email
```
<!-- AC-ID: REQ-SB-10-US-01-AC-01 -->

### Scenario 2: Backfill is idempotent — rerunning does not duplicate notes

```gherkin
Given a Person note already exists for a sender's email address
When the backfill process runs again
Then no duplicate Person note is created for that email address
  And the existing note is left unchanged apart from topping up any baseline
    fields it may still be missing
```
<!-- AC-ID: REQ-SB-10-US-01-AC-02 -->

### Scenario 3: Company tag and wikilink when the company is a known customer

```gherkin
Given a sender's email domain resolves to a company name, and that company
    matches an existing Customer hub note
When the Person note is created or backfilled
Then the note's tags include company/<slug> for that company
  And the note's body includes a [[wikilink]] to that customer's hub note
  And no second Customer hub note is created for the same customer
```
<!-- AC-ID: REQ-SB-10-US-01-AC-03 -->

### Scenario 4: Company tag only, no wikilink, when the company is not a known customer

```gherkin
Given a sender's email domain resolves to a company name that has no existing
    Customer hub note (e.g. an internal colleague or a third party)
When the Person note is created or backfilled
Then the note's tags include company/<slug> for that company
  And no wikilink is added to the note's body
  And no new Customer hub note is created for that company
```
<!-- AC-ID: REQ-SB-10-US-01-AC-04 -->

### Scenario 5: No company tag or wikilink when no company can be determined

```gherkin
Given a sender's email address is from a domain that does not resolve to a
    recognisable company (e.g. a personal/free email provider)
When the Person note is created
Then the note has name and email populated and carries only the kind/person
    tag
  And no company tag and no wikilink are added
```
<!-- AC-ID: REQ-SB-10-US-01-AC-05 -->

### Scenario 6: Manually-added content survives later automated updates

```gherkin
Given a Person note already exists and has user-added content beyond its
    auto-populated baseline fields (role, personality notes, a filled-in
    LinkedIn link, or free-form observations in the body)
When the backfill process runs again, or a new email from that same sender is
    captured going forward and the note is touched as part of that write
Then the user's manually-added content is preserved unchanged
  And only missing baseline fields (frontmatter, tags, the company wikilink
    line if newly applicable) are added if needed — never overwriting a
    baseline field the user has already filled in themselves
```
<!-- AC-ID: REQ-SB-10-US-01-AC-06 -->

### Scenario 7: New email capture creates or updates a Person note automatically, going forward

```gherkin
Given the email capture pipeline (app/business/email_classification.py)
    classifies and writes a new Email note for a sender not yet known
When the note is written to the vault
Then a Person note is automatically created for that sender in the same way
    the backfill would create one — no separate manual step is required
    afterward
  And if a Person note already exists for that sender, it is updated (baseline
    top-up only) rather than duplicated
```
<!-- AC-ID: REQ-SB-10-US-01-AC-07 -->

### Scenario 8: A company becoming a known customer later adds the wikilink retroactively

```gherkin
Given a Person note already exists with a company tag but no wikilink,
    because that company was not a known customer at the time the note was
    created
When a Customer hub note for that company is later created (e.g. via
    REQ-SB-14's retrofit or capture hook) and the People backfill runs again
Then the wikilink to that company's hub note is added to the Person note's
    body
  And the rest of the note's content, including any manual additions, is left
    unchanged
```
<!-- AC-ID: REQ-SB-10-US-01-AC-08 -->

### Scenario 9: An Email note with no sender_email is skipped, not errored

```gherkin
Given a captured Email note has no sender_email value
When the People backfill or the going-forward capture hook processes it
Then no Person note is created or updated for that Email note
  And the backfill/capture run completes without erroring on that note
```
<!-- AC-ID: REQ-SB-10-US-01-AC-09 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or is
needed for this capability; Obsidian's own note/graph views are the surface
this story affects, not a Second Brain UI screen.

## Dependencies

- **Blocked by:** none — the capture pipeline (`app/business/
  email_classification.py`, `REQ-SB-07-US-01`, Done) and the hub-note
  primitives this story reuses (`app/business/customer_hub_linking.py`,
  `app/data_access/vault_writer.py`, `REQ-SB-14-US-01`, Done) already exist
  and work.
- **Related to:** REQ-SB-14 (`REQ-SB-14-US-01`) — this story reuses its
  hub-note file-I/O primitives and the "ensure hub note exists, then link"
  pattern for the company-to-customer half, with the carve-out described in
  Constraints (must not create a new Customer hub note for a company that
  isn't actually a customer).
- **Related to:** REQ-SB-08 (Meetings Capture Pipeline) — not yet specced or
  built. The meeting-attendee half of REQ-SB-10's PRD text is blocked on it;
  once REQ-SB-08 exists, a follow-on story should replicate this story's
  "ensure Person note exists and is up to date" mechanism for meeting
  attendees, the same way this story replicates REQ-SB-14's mechanism for
  companies.
- **External:** none new.

## Constraints

- Follows the resolved People schema exactly — `type`, `name`, `email`,
  `phone`, `linkedin`, `tags` frontmatter, inline-body company wikilink when
  applicable. Not redesigned here.
- Baseline frontmatter fields (`type`, `name`, `email`, `phone`, `linkedin`,
  `tags`) are only ever inserted if missing, never overwritten once a real
  value exists — the same surgical "insert this key if absent" pattern
  `REQ-SB-14-US-01` established for Customer hub notes
  (`insert_frontmatter_key_if_missing` / `ensure_hub_note_baseline_frontmatter`
  in `app/data_access/vault_writer.py`). The note body, once created, is never
  programmatically rewritten wholesale — only the company wikilink line may be
  surgically inserted later if it wasn't present at creation time (Scenario
  8), mirroring `insert_body_line_if_missing`'s idempotent-insert precedent.
- **Do not blindly reuse `customer_hub_linking.ensure_hub_note_and_link` for
  every derived company.** That function unconditionally creates a Customer
  hub note for any non-blank customer string passed to it — correct for
  email classification, where every note is already classified as belonging
  to a real customer, but wrong here: a derived company (e.g. "Core42",
  "Microsoft") is very often *not* a customer, and MEMORY.md is explicit that
  a non-customer company gets no hub note, tag only. The company-to-customer
  match must be checked (e.g. against `vault_writer.list_known_customers()`)
  **before** any hub-note-creating/linking call is made; a company that
  doesn't match gets its tag and nothing else. The precise matching mechanism
  (comparing derived company against known-customer names, which will differ
  in slug vs. display-name casing/spelling) is an architecture-level decision
  for `/plan-tasks`, the same kind of deferral `REQ-SB-14-US-01` used for its
  wikilink-placement mechanics.
- Company derivation from a sender's email domain, and telling a real
  organisation domain apart from a personal/free email provider (Scenario 5),
  is an architecture-level mechanism to design at `/plan-tasks` — this story
  specs the observable behaviour (tag+link when derivable and known,
  tag-only when derivable but unknown, neither when not derivable), not the
  exact string/domain-list logic.
- Dedup key is the sender's email address, per the resolved schema
  ("deduped by email address (names vary in formatting, addresses don't)").
  Filenames must remain collision-safe if two distinct email addresses happen
  to share an identical display name — per MEMORY.md's existing filename-
  uniqueness constraint (never build a vault filename from a value alone that
  isn't guaranteed unique); exact disambiguation mechanism is left to
  `/plan-tasks`.
- Must respect the `api → business → data_access` layer boundary (ADR-003).
- Both the retrofit and the going-forward hook must be idempotent — rerunning
  must never create duplicate Person notes or duplicate wikilinks/tags
  (Scenarios 2 and 6).
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`
  in `src/backend/.env`), not a fixture/test vault — no-data-loss and
  idempotency are load-bearing requirements, not conveniences.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-10-US-01-T01 | backend | Add person-note file-I/O primitives to `vault_writer.py`; promote `_tag_slug` to public `tag_slug` | `src/backend/app/data_access/vault_writer.py` | [T01](../Tasks/REQ-SB-10-US-01-T01-person-note-vault-writer-primitives.md) |
| REQ-SB-10-US-01-T02 | backend | New `app/business/people_extraction.py` orchestration module | `src/backend/app/business/people_extraction.py` | [T02](../Tasks/REQ-SB-10-US-01-T02-people-extraction-orchestration.md) |
| REQ-SB-10-US-01-T03 | backend | Wire the per-write Person-note hook into `email_classification.py` | `src/backend/app/business/email_classification.py` | [T03](../Tasks/REQ-SB-10-US-01-T03-capture-pipeline-people-hook.md) |
| REQ-SB-10-US-01-T04 | backend | New `POST /poc/retrofit-people-from-emails` endpoint | `src/backend/app/api/email_poc_router.py` | [T04](../Tasks/REQ-SB-10-US-01-T04-retrofit-endpoint.md) |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — all 9 verified live against the real vault
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-verification mode still in effect project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Meeting-attendee-based Person backfill/capture** — blocked on REQ-SB-08
  (Meetings Capture Pipeline), which does not exist yet. When REQ-SB-08 is
  specced/built, a follow-on story is needed to replicate this story's
  mechanism for meeting attendees; not invented here.
- Building REQ-SB-08 itself, or any other capture pipeline.
- The exact company-domain-to-name derivation algorithm and the personal-vs-
  organisation-domain distinction — architecture-level detail for
  `/plan-tasks` (see Constraints), not decided in this story.
- Any Second Brain UI surfacing of People data — no application screen is
  added or changed by this story; Obsidian's own note/graph views are the
  presentation surface.
- A `Person` Obsidian template for manual entry — that belongs with
  `REQ-SB-15`'s manual-entry-templates pattern if/when the operator wants a
  fifth template added there; not part of this story's automated-capture
  scope.

## Notes

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to People notes
or contact capture; this is backend/vault-structure work only, same shape as
`REQ-SB-07-US-01` and `REQ-SB-14-US-01`.

**Scoping transparency (company derivation):** as explained in Context, this
story treats "derive company from the sender's email domain" as the specced
expected behaviour, not an open assumption to flag — it's the only data
source available on a captured Email note, and it's exactly what the resolved
schema's own worked example (`core42.ai` → `company/core42`) already shows.
What genuinely is left open (the precise domain-parsing/company-matching
mechanism, and distinguishing a personal-email domain from an organisation
one) is deferred to the architect at `/plan-tasks` as a Constraint, mirroring
the deferral `REQ-SB-14-US-01` used for its own wikilink-placement mechanics —
consistent precedent, not a new pattern.

gate: clear 2026-08-11 — no triggers fired: no material assumption was needed
beyond what the resolved schema (`Implementation/Plans/
2026-08-10-vault-taxonomy-draft.md`) and MEMORY.md's 2026-08-11 People
decision already settle; REQ-SB-10 is finalised in the PRD (no `<!-- Draft
-->` marker); no ADR created or changed (analyst scope); no ESCALATIONS.md
entry needed; the story is sized comparably to the already-Done
`REQ-SB-14-US-01` (one shared mechanism, several tasks at `/plan-tasks`), not
oversized; no contradictory PRD/MEMORY inputs found; the one genuinely open
question (meeting-attendee backfill) is not ambiguity to guess at — it's
cleanly out of scope pending REQ-SB-08, stated as such in Non-Goals rather
than guessed.

Architecture scope: §Data Model → Person Notes & Email-Sender Extraction
(REQ-SB-10), §Source Layout (new `app/business/people_extraction.py` entry).

gate: clear 2026-08-11 (architect, `/plan-tasks` step 1) — no ADR created or
changed. The three architecture-level decisions this story explicitly
deferred to `/plan-tasks` (company-domain derivation + personal-domain
distinction, company-to-known-customer matching mechanism, and Person-note
filename/dedup-key scheme) were resolved by applying already-Accepted
ADR-003 (layering) and ADR-004 (tag-not-folder) patterns to a new note type,
plus the existing `insert_body_line_if_missing`/baseline-frontmatter/
`_slugify` primitives REQ-SB-14 already established — not a new structural
boundary, so documented in `architecture.md` only, no ADR. The one new
composition shape (`people_extraction.py` calling `customer_hub_linking.py`,
the first business-to-business call in this codebase) was evaluated against
ADR-003 and found non-violating (ADR-003 restricts `business/`'s I/O, not
business-to-business composition) — recorded explicitly in `architecture.md`
rather than left implicit. No contradiction found against any Accepted ADR,
the PRD, or a MEMORY.md constraint, so no ESCALATIONS.md entry. Full
reasoning: `Implementation/Architecture/architecture.md` → "Person Notes &
Email-Sender Extraction (REQ-SB-10)".

**Decomposer pass (2026-08-11, `/plan-tasks` step 2):** All 9 Gherkin
scenarios locked as `REQ-SB-10-US-01-AC-01` through `AC-09`, tagged
in-place after each scenario's closing fence — wording tightened only
where needed for buildability (e.g. "known customer" cross-referenced
against `vault_writer.list_known_customers()`), no scenario's observable
behaviour changed from the analyst's draft. Decomposed into four tasks,
mirroring `REQ-SB-14-US-01`'s 4-task shape (data_access primitives →
business orchestration module → per-write hook wiring → retrofit
endpoint): `T01` (person-note file-I/O primitives in `vault_writer.py`,
plus promoting `_tag_slug` to public `tag_slug`), `T02` (new
`app/business/people_extraction.py` — company derivation, customer
matching, and the shared `ensure_person_note` operation all folded into
this one task/module rather than split further, since none of them is
independently valuable or independently verifiable outside
`ensure_person_note`'s own call graph), `T03` (the going-forward per-write
hook into `email_classification.py`), `T04` (the one-time retrofit
endpoint). `depends_on`: `T02 → [T01]`, `T03 → [T02]`, `T04 → [T02]` —
acyclic, T03/T04 are independent siblings once T02 lands. Every locked AC
has at least one AC-tagged manual verification step: AC-07 (the
going-forward capture hook) is verified live in T03 against the real
Outlook/vault integration; the remaining eight (AC-01 through AC-06,
AC-08, AC-09 — all retrofit scenarios, since they share one underlying
code path with different sender data) are verified live in T04 against the
real vault via the new endpoint, falling back to throwaway test notes only
where the live vault has no natural example for a given scenario (e.g.
AC-05's personal-domain case), matching this project's established
live-verification precedent (SPRINT-001, `REQ-SB-14-US-01`) and this
story's own framing that it runs against real live data. T04 carries more
AC-tagged steps (8) than any prior task in this project, but the
underlying code is a thin ~15-line HTTP wrapper around T02's single
`retrofit_people_from_emails` code path — the volume is verification
setup-data variety, not independent logic paths — judged comparable in
kind (not degree) to `REQ-SB-14-US-01-T04`'s own successful precedent, so
not flagged as oversized (trigger 5).

`status: Draft → Ready` — every AC is locked (9/9), every locked AC has a
tagged verification step, `depends_on` is acyclic across all four tasks.
Task `status:` set to `Ready` in lockstep. `gate: clear 2026-08-11`
(decomposer) — no MUST-FLAG trigger fired: no material assumption beyond
what the architect's already-recorded decisions settle, REQ-SB-10 is
finalised, no ADR created/changed by this step, no ESCALATIONS.md entry
needed, decomposition judged not oversized (see above), every locked AC is
verifiable live against the real vault, no contradictory inputs, and the
one task-shape judgement call (folding company-derivation/customer-
matching into T02 rather than a separate task) has one clearly-better
answer per the `customer_hub_linking.py` precedent, not a genuinely
unclear/multiple-equally-valid choice.
