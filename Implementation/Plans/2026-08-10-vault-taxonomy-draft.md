# Vault taxonomy — working draft

**Date:** 2026-08-10 (Customer/Pipeline/Agreements/Consumption section added
same day, once real captured email data existed to design against — see
below).
**Status:** Core taxonomy resolved. Person/Meeting/Industry note shapes
still open (genuinely no real data yet for those).

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

## Open questions (not yet answered)

- **"So many entities" under a Customer:** the operator's original flag —
  Pipeline/Agreements/Consumption resolve three of them; more may still
  surface. Keep extending this same pattern (new `kind/` folder + tags) as
  they come up, rather than redesigning.
- **Meeting / Industry note shapes** — still genuinely no real data to
  design against; unchanged from the original parking rationale.

## Non-goals right now

- No frontmatter schema validation tooling yet — this is a writing
  convention, not enforced structure, until real content exists to validate
  against.
- No ingestion/agent code for Pipeline/Agreements/Consumption yet — this is
  the structure only. Building capture for it (manual entry? extracted from
  emails? both?) is unscoped, separate work.

## Next step

Meeting/Industry shapes resume once real examples of those exist.
Pipeline/Agreements/Consumption/People structure is resolved and ready to
build capture for whenever the operator wants to move on it (People capture
would be `REQ-SB-10`'s implementation; Pipeline/Agreements/Consumption have
no requirement ID of their own yet).
