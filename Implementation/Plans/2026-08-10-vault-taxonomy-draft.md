# Vault taxonomy — working draft

**Date:** 2026-08-10 (Customer/Pipeline/Agreements/Consumption section added
same day, once real captured email data existed to design against — see
below).
**Status:** Core taxonomy resolved, including Meeting, generic Notes,
Partner, and Research (all 2026-08-11). Only Industry/Topic note shape
remains genuinely open.

## Direction agreed so far

Type-based notes: each note carries a `type:` frontmatter field and lives
under a matching top-level vault folder; relationships between notes are
wikilinks, not duplicated data. This lets `REQ-SB-01`'s indexer (frontmatter +
wikilinks + tags) build the whole relationship graph without new backend
schema work.

Types identified so far:
- **Person** — individuals (attendees, contacts).
- **Meeting** / **Meeting-Minutes** — calendar events and their notes; link
  out to attendee `Person` notes and relevant `Industry`/`Customer` notes.
- **Industry / Topic** — "required knowledge" and industry-understanding
  notes; linked from Meetings that need them.
- **Customer** — a hub note per customer; People, Meetings, and Industry
  notes link back to it rather than duplicating customer context per-note.
- **Affiliate** — related to Customer, but its exact shape is an **open
  question** (see below).

Email and calendar events arrive as vault notes via the Hermes-wrapped
`outlook_com` skill (ported from agentic-map, COM automation against local
desktop Outlook — see `MEMORY.md`'s Hermes integration-sourcing constraint),
not manual entry.

## Customer structured data (resolved 2026-08-10)

Real captured email data confirmed the domain: Azure MACC/consumption
business (ADNOC/TAQA/Masdar/Core42), the same one agentic-map's
`pipeline_items`/`customer_entitlements` (REQ-079/080/081) were built for.
**Reverses that earlier port-classification "Drop"** — see
`2026-08-10-agentic-map-requirement-port.md`; those requirements are now
genuinely relevant, reshaped for notes instead of DB rows. Full reasoning
and the resolved shape recorded in `MEMORY.md`.

Follows `ADR-004`'s established pattern throughout: `kind` is a folder,
`customer` is a tag, never the reverse.

**Customer hub note** — `Work/Customers/<Customer>.md`, one file per
customer (`Customers` is just another kind folder, alongside `Emails`/
`Files`/etc.). This resolves the Affiliate question below: an Affiliate is
a `Customer`-type note with `affiliate_of:` pointing at its parent — no
distinct note type needed.
```yaml
type: Customer
customer: ADNOC
tags: [customer/adnoc, kind/customer]
affiliate_of: ""   # set only if this note is an Affiliate of another Customer
```
Body: a curated overview + links to key contacts/current focus — **not** a
manual index of every related email/file. Those are already surfaced for
free via `customer/<slug>` tag search (per the book's "digest, not raw
dump" principle) — the hub note's value is the distillation, not
duplication.

**Pipeline (Opportunity)** — atomic notes, `Work/Pipeline/<name>.md`:
```yaml
type: Opportunity
customer: ADNOC
stage: Prospecting        # dynamic, vault-derived — same extensible
                           # pattern as customer/kind, no fixed enum
value_usd: 250000
description: "..."
tags: [customer/adnoc, kind/opportunity]
```

**Agreements** — atomic notes, `Work/Agreements/<name>.md`:
```yaml
type: Agreement
customer: ADNOC
start_date: 2026-01-01
end_date: 2026-12-31
value_usd: 500000
status: active            # active | expired | renewal-pending
tags: [customer/adnoc, kind/agreement]
```

**Azure Consumption** — one note per snapshot (fully atomic, per the
operator's explicit choice over a single growing log note), `Work/
Consumption/<Customer>-<snapshot-date>.md`:
```yaml
type: Consumption-Snapshot
customer: ADNOC
snapshot_date: 2026-08-01
azure_consumption_usd: 145000
tags: [customer/adnoc, kind/consumption-snapshot]
```
Append-only in spirit: a new snapshot is always a new note, an existing
snapshot note is never edited. "Latest consumption for a customer" is a
query (most recent `snapshot_date` among notes tagged `customer/<slug>` +
`kind/consumption-snapshot`), not a special file.

## People (resolved 2026-08-11)

**Flat structure, Company as a tag — not nested under Company.** Same
reasoning `ADR-004` already established for Customer: a person's employer
is at least as multidimensional as a note's customer relevance (people
change jobs; plenty of real contacts in the captured emails — e.g. Core42
colleagues — work across multiple customer accounts at once), so nesting
People under Company folders would hit the same problem ADR-004 fixed once
already. **Company gets its own tag namespace, `company/<slug>`, separate
from `customer/<slug>`** — a person's employer isn't always a customer
account (many are internal Core42 colleagues or third parties like
Microsoft/G42), so conflating the two namespaces would misuse "customer" to
mean "employer."

**Person** — atomic notes, one per person, `Work/People/<Person>.md`
(`People` is just another kind folder):
```yaml
type: Person
name: Mohamed Eltanany
email: mohamed.eltanany@core42.ai
phone: ""
linkedin: ""
tags: [company/core42, kind/person]
```
Body starts with an inline wikilink to the company's Customer hub note
**when the company matches an existing customer** — `**Company:**
[[ADNOC]]` — reusing REQ-SB-14's existing `ensure_hub_note_and_link`
mechanism as-is, no new concept. When the company isn't a known customer
(internal Core42, a third party like Microsoft/G42), there's no hub note to
link to yet, so the `company/<slug>` tag stands alone until one exists —
per MEMORY.md's standing "tags AND wikilinks, always, wherever a real link
target exists" rule. Below the link: role/title, notes, personality
observations — free-form, user-added, never overwritten by automation
(REQ-SB-10's living-document rule, same as Customer hub notes).

**Backfill:** extract from already-captured Email notes' `sender`/
`sender_email` frontmatter, deduped by email address (names vary in
formatting, addresses don't) — same retrofit-endpoint pattern `REQ-SB-14`
already established for Customer hub notes. **Meeting-based extraction is
real but blocked** — `REQ-SB-08` (Meetings capture) doesn't exist yet, so
that half of "backfilled from Emails and Meetings" only activates once it
does; email-based backfill can proceed independently now.

**Manual add:** a `Person` template, same mechanism as `REQ-SB-15`'s four
templates (Obsidian core Templates plugin, not a new one).

## Meetings (resolved 2026-08-11)

Designed by direct extension of the already-resolved Email/Person/Customer
patterns, not from a real captured calendar example yet (the parking
rationale was "no real data" — this resolves the *shape* by precedent so
`REQ-SB-08` isn't blocked on it; the exact Outlook calendar-sync mechanism
is still an architecture-level decision for `/plan-tasks`, same deferral
style as REQ-SB-14/REQ-SB-10 used for their own sync mechanics).

**One note per meeting, not a separate Meeting-Minutes type.** The original
brainstorm considered Meeting and Meeting-Minutes as two types; collapsed
into one living-document note (minutes go in the same note's body, same
"auto-populated baseline + user-added content preserved" pattern as
Customer/Person notes) — avoids an extra note type until real usage shows
attendees/logistics and minutes genuinely need to be separate notes.

`Work/Meetings/<subject>-<date>-<entry-id-suffix>.md` (`Meetings` is a
`kind` folder; the EntryID-suffix filename rule already fixed for email
collisions applies identically here — two meetings can share a subject and
date):
```yaml
type: Meeting
customer: ADNOC          # derived from attendee company matches, per below
subject: "..."
start: 2026-08-12T10:00:00Z
end: 2026-08-12T11:00:00Z
location: "..."
organizer: "..."
tags: [customer/adnoc, kind/meeting]   # customer/ tag only if a match was found
```
Body starts with the same inline-wikilink convention as Email notes:
`**Customer:** [[ADNOC]]` when an attendee's company matches a known
customer (reusing `customer_hub_linking`'s existing mechanism directly, no
new concept), followed by `**Attendees:** [[Person1]], [[Person2]], ...`
— every attendee gets the exact `ensure_person_note` treatment
`REQ-SB-10` already built for email senders, extended from "sender" to
"attendee" as the person-identifying event. This is also what finally
activates the "Meeting-based half" of People backfill that
`REQ-SB-10-US-01`'s own Non-Goals flagged as blocked on this. Below that:
free-form space for the user's own meeting notes/minutes — never
programmatically rewritten once added.

**Customer derivation for a meeting:** intended behavior — check each
attendee's company (same `derive_company_from_email`/
`find_matching_customer` logic `people_extraction.py` already has) and use
the first/majority match; no match means no `customer` tag on the meeting.
Exact tie-breaking mechanism (majority vs. organizer-priority vs.
first-match) is left to `/plan-tasks`, not decided here — a real but
narrow judgement call, not a blocker to speccing the requirement.

## Generic customer-related Notes (resolved 2026-08-11)

Content about a customer that doesn't fit any existing `kind` (not an Email,
Pipeline item, Agreement, Consumption snapshot, or Meeting) — e.g. free-form
strategy notes, an org chart writeup. No new mechanism needed: `customer` is
already a tag, not a folder (`ADR-004`), so this is just one more `kind/`
value, exactly the extension pattern the "so many entities" open question
below already anticipated.

`Work/Notes/<title>.md`:
```yaml
type: Note
customer: ADNOC          # only if customer-relevant; blank/omitted otherwise
tags: [customer/adnoc, kind/note]   # customer/ tag only if relevant
```
Body: free-form. No new business logic required — `list_known_kinds()` is
already vault-derived, so writing a note with `kind: Note` needs zero code
changes. A manual-entry template for it can be added to `REQ-SB-15`'s set
later if wanted; not requested yet.

## Partners (resolved 2026-08-11)

**Same hub-note/tag/wikilink graph-connectivity mechanism as Customer
(`REQ-SB-14`'s pattern) — deliberately *not* the Pipeline/Agreements/
Consumption sub-entities.** Operator's explicit scoping: those three track a
sales/Azure-consumption relationship a technology partner (e.g. Microsoft)
doesn't have; replicating them for Partner would be structure without a real
use. `partner/<slug>` is a **new tag namespace, mutually exclusive with
`customer/<slug>`** (operator's explicit choice) — a company is a Customer,
a Partner, or neither, never both; this matches the reasoning already used
for `company/<slug>` vs `customer/<slug>` (MEMORY.md).

**Partner hub note** — `Work/Partners/<Partner>.md`:
```yaml
type: Partner
partner: Microsoft
tags: [partner/microsoft, kind/partner]
```
Body: same living-document convention as the Customer hub note (curated
overview + key contacts, never programmatically rewritten once the operator
adds content) — a straight structural copy of `REQ-SB-10`'s Customer hub
note, `type`/tag values only.

**Company-hub-linking logic gains a Partner branch:** `people_extraction.
ensure_person_note` currently calls `find_matching_customer(company)` only;
it needs an equivalent `find_matching_partner(company)` (identical tag-slug
matching against a new vault-derived `list_known_partners()`, mirroring
`list_known_customers()`) — check Customer first, then Partner, since the
operator confirmed the two are mutually exclusive so at most one can match.
A company matching neither gets the `company/<slug>` tag alone, same as
today.

**Real migration needed, not just new-data-forward:** `Work/Customers/
Microsoft.md` already exists — Microsoft was auto-classified as a Customer
by Compass before this distinction existed, and 5 Person notes +
2 Email notes already carry `customer/microsoft` + `customer: Microsoft`.
Fixing this is: (a) move `Work/Customers/Microsoft.md` to `Work/Partners/
Microsoft.md` with `type`/tag updated to Partner (Obsidian wikilinks
resolve by filename, not full path, so existing `[[Microsoft]]` links
elsewhere keep resolving — no link text needs to change); (b) a retrofit
pass over already-tagged notes to swap `customer/microsoft` →
`partner/microsoft` (and the `customer: Microsoft` frontmatter value to
`partner: Microsoft`). Real data to design the retrofit against — not
speculative.

## Researches (resolved 2026-08-11)

**Manual-entry only, for now** — a new Obsidian template (extending
`REQ-SB-15`'s existing four), no new capture/business-logic pipeline.
AI-assisted summarization is explicitly deferred, not in scope here.

**Minimal fields** — the free-form body carries takeaways/quotes/notes
(per the "digest, not raw dump" principle already used elsewhere); frontmatter
stays deliberately thin:
```yaml
type: Research
title: "Beyond the Second Brain"
author: "Mo Elkholy"
tags: [kind/research]
```
`Work/Researches/<Title>.md`. No customer/company link — a book/read isn't
inherently tied to a customer relationship, so per the standing
tags-and-wikilinks rule this is a genuine absence of a link target, not an
overlooked link (same reasoning already used for People with no known
company). If a Topic/Industry note type is resolved later, Research notes
may gain an optional `topic/<slug>` tag then — not decided now.

## Open questions (not yet answered)

- **"So many entities" under a Customer:** the operator's original flag —
  Pipeline/Agreements/Consumption resolve three of them; more may still
  surface. Keep extending this same pattern (new `kind/` folder + tags) as
  they come up, rather than redesigning.
- **Industry / Topic note shape** — still genuinely no real data to design
  against; unchanged from the original parking rationale.
- **Affiliate rollup query (found 2026-08-12, no code yet):** the Affiliate
  shape resolved above (a `Customer`-type note with `affiliate_of:` pointing
  at its parent) tells you *that* TAQA is ADNOC's affiliate, but nothing
  currently *uses* that link. Every Pipeline/Agreement/Consumption/Meeting/
  Note about TAQA is tagged `customer/taqa`, never `customer/adnoc` — so a
  plain `customer/adnoc` tag search (or any future "show me everything about
  ADNOC" view: My Day, Agents Map, an MCP query) silently excludes its
  affiliates' data. Confirmed by inspection of `src/backend` — no
  `list_customer_family`-style traversal of `affiliate_of` exists anywhere
  yet (`vault_writer.py`/`vault_query_tools.py` only have the flat
  `list_known_customers`).
  **Recommended direction (not yet built):** resolve at query time, not by
  writing structure — add a function that reads a Customer hub note, follows
  `affiliate_of` in both directions (its own affiliates, and its parent if
  it is one) to build the full slug set, and unions tag search across that
  set. This is a direct extension of ADR-004's "derive, don't duplicate"
  philosophy — no vault migration, no dual-tagging (which would drift the
  moment an affiliate relationship changes), just a new read-path function
  ahead of whichever consumer needs a customer-family view. Build this
  *before* shipping any "customer overview" feature, not after one ships
  without it.

## Non-goals right now

- No frontmatter schema validation tooling yet — this is a writing
  convention, not enforced structure, until real content exists to validate
  against.
- No ingestion/agent code for Pipeline/Agreements/Consumption yet — this is
  the structure only. Building capture for it (manual entry? extracted from
  emails? both?) is unscoped, separate work.

## Next step

Industry/Topic shape resumes once real examples exist. Pipeline/
Agreements/Consumption/People/Meetings/Notes/Partners/Researches structure
is resolved and ready to build capture for (People is `REQ-SB-10`, Done;
Meetings is `REQ-SB-08`, being specced; Partners is `REQ-SB-16` and
Researches is `REQ-SB-17`, both new, not yet specced; Notes needs no
requirement of its own — zero code change; Pipeline/Agreements/Consumption
have no requirement ID of their own yet).
