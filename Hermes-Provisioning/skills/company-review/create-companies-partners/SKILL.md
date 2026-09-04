---
name: create-companies-partners
description: One-time build of real Customer/Partner (and Affiliate) hub notes from the operator's curated Entities.md.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, partner, entities, one-time]
---

# Create Companies & Partners (Step 3 of the company/partner sequence)

**Step 3 of 4.** Reads the operator's own hand-curated `.second-brain/Settings/Entities.md`
(written by `entity-domain-extraction`, then edited by hand -- Ignore/
Created flags set, Aliases/Affiliate of filled in) and creates the real
Customer/Partner hub notes, their Affiliate sub-entities, and moves each
one's existing People notes into place. Never touches Threads, never
summarizes -- that's Step 4, separate and later, not built yet.

## Prerequisites

- `.second-brain/Settings/Entities.md` must exist and be curated -- run
  `entity-domain-extraction` first, then wait for the operator to have
  actually edited it (set real `Ignore`/`Affiliate of` values). Running
  this Skill against the raw, un-curated output would create a hub note
  for every mechanically-detected domain, noise included.
- No `pywin32`, no Outlook, no network calls -- pure local vault read/write.
- Vault path: the scripts read `SECOND_BRAIN_VAULT_PATH` from Hermes' own
  `.env` themselves; `--vault-path` only overrides it.

## How to Run

One script, one call:

```
terminal(command="python create_companies_partners.py", cwd="<this Skill's scripts/ folder>")
```

Prints `{"created", "auto_created_parents", "skipped_ignored",
"skipped_already", "people_moved", "people_retagged", "people_relinked",
"hub_notes_self_tagged", "hub_notes_log_captures_backfilled",
"threads_related_updated", "messages_company_linked",
"engagement_threads_tagged", "engagement_meetings_tagged"}`.

## Structure this builds

```
Work/Customers/<Name>/
    <Name>.md              -- hub file. "## Affiliates" lists any
                               Affiliates (wikilinks down); "## Log &
                               Captures" links the two files below.
                               Deliberately NO People list here -- every
                               moved Person note carries a link UP
                               instead, and Obsidian's own backlinks
                               panel shows who belongs to it.
    <Name>-log.md            -- identifying "# <Name>" header only, real
                               content is a later job's job. Name-prefixed
                               (not bare "log.md") so it's identifiable in
                               a flat file listing and never collides with
                               another Customer's own log.md as a wikilink
                               target.
    <Name>-captures.md        -- same, for captures.
    People/
        <person>.md         -- existing Work/People/ notes on this
                               entity's own domain, moved here, each with
                               a "**Customer:** [[Name]]" line inserted.
    Affiliates/
        <Affiliate>/
            <Affiliate>.md   -- same shape one level deeper.
            <Affiliate>-log.md
            <Affiliate>-captures.md
            People/
                <person>.md

Work/Partners/<Name>/        -- identical shape; Partners can have
                                 Affiliates too.
```

`Entities.md` itself gets rewritten at the end: `Created: No` flips to
`Yes` for everything this run actually created (including any
auto-created parents -- see Pitfalls), every other field preserved.

Every run also calls `retag_people_by_domain` at the end (2026-08-21 bug
fix -- "Mubadala for example wasn't tagged customer/mubadala", "People
who moved to Masdar don't have the masdar tag"): every hub note gets its
own self-tag (e.g. `Mubadala.md` gets `tags: ["customer/mubadala"]`),
and every Person note vault-wide gets tagged/wikilinked to a company
if -- and only if -- THEIR OWN email domain matches that company's own
domain, independent of which threads mention them. Re-runnable anytime
via `--retag-only` (skips Entities.md entirely) if new People notes show
up later and need catching up.

A `Domain:`/`domain` field can now name more than one domain,
comma-separated (2026-08-21, operator: "I want both core42.ai and
core42.ae to be Partner Core42" -- one real organization, two registrar
domains) -- every match site (`move_people_for_domain`,
`retag_people_by_domain`, the new pass below) treats it as a set via
`_split_domains`, not a single string.

Every run also calls `retag_threads_by_participant_company` (2026-08-21,
operator: "Threads and Emails now need to contain in Related the Company
as we included before in Related Section"): for every Thread, the union
of every real hub note whose own domain matches any of that Thread's
participants' own email domains gets wikilinked into the Thread's own
`## Related` section (alongside the Person wikilinks
`email-thread-capture`'s own `link_person_to_thread.py` already puts
there), and each individual RawMessage note under it gets the same
resolution scoped to just its own participants, in a new `company_links`
frontmatter list. Expect `[[Core42]]` on nearly every Thread once Core42
is a real hub note -- almost every real email involves an internal
core42.ai/core42.ae participant, so that's correct, not a bug.

Every run also calls `tag_engagement_type` (2026-08-22, operator's own
explicit rule) -- classifies every Thread and Meeting as exactly one of
`engagement/customer`, `engagement/partner`, or `engagement/internal`:
customer if any real Customer company is involved; else partner if any
real (non-internal) Partner company is involved; else internal
(the operator's own explicit fallback -- a Thread with only noise-domain
or zero resolvable participants correctly lands here too, not a separate
"zero external domains" gate). Customer always wins a tie ("If there is a
Partner and Customer engaged then its Customer", verbatim). **G42 and
every hub whose own `affiliate_of` chain resolves to G42 (Core42,
Inception, Presight today -- computed from real hub data, never a
hardcoded name list) never count as a real Partner for this
classification** -- "G42 and its Affiliates are internal" (operator,
verbatim), even though they're filed under Entities.md's own `##
Partners` section for Job 3's own creation purposes. The internal
root(s) are real config (`.second-brain/engagement_classification_config.json`,
self-healing to `{"internal_roots": ["G42"]}` on first read), not a
hardcoded literal. Depends on `retag_threads_by_participant_company`/
`retag_meetings_by_attendee_company` having already run in the same
pass -- reads their `customer/<slug>`/`partner/<slug>` tags, never
re-derives company membership from participants itself. Idempotent,
mutually-exclusive tags (a stale `engagement/*` value is replaced, not
just unioned, if the real classification changes later -- e.g. a
customer joins a previously internal-only thread).

## Pitfalls

- **An Affiliate whose named parent has no top-level entry anywhere in
  Entities.md gets a bare placeholder parent auto-created**, not skipped
  (operator: "Add the Parent if it's not in the file, it will come later
  when we start Parsing the files"). The placeholder has blank
  Domain/Aliases -- check `auto_created_parents` in the result and go
  fill those in (in Entities.md, or directly on the new hub note) once
  more evidence turns up.
- **Idempotent by design** -- safe to re-run after the operator adds more
  curated entries later. An entry already `Created: Yes` is skipped for
  creation but its path is still resolved (so a newly-added Affiliate
  naming it as parent still works); a Person note whose target path
  already exists is left alone, never moved twice.
- **Running this against a not-yet-curated Entities.md** creates a hub
  note for every mechanically-detected domain, including obvious noise
  (notification senders, mailing lists) that the operator hasn't had a
  chance to mark `Ignore: Yes` yet. Confirm the file has real edits in
  it first.

## Verification

- Report the five result counts, and explicitly call out
  `auto_created_parents` if non-empty (needs operator follow-up).
- Spot-check one created Customer and one created Affiliate: hub file
  frontmatter (`type`, `name`, `affiliate_of`), a moved Person note's
  link line, and the parent's own `## Affiliates` section.
