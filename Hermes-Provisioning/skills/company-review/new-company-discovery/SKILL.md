---
name: new-company-discovery
description: Approves, classifies (Customer/Partner/Affiliate/Ignore), or discovers a company entry in the vault's Work/Entities.md file. Use this whenever the operator's message approves, classifies, or makes a decision about a company/partner/customer/affiliate/vendor entry -- e.g. "make Oracle a partner", "Inb is an affiliate of Investbank", "ignore that company", "approve Oracle" -- even without the word Entities.md in the message. Also runs the recurring scan that finds new company domains in Threads/Meetings and adds them to Entities.md for review.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, entities, whatsapp, recurring]
---

# New Company Discovery (WhatsApp approval loop)

**Recurring**, unlike every other Skill in the company/partner sequence
(`entity-domain-extraction` is a one-time Step 1; `create-companies-
partners` and `summarize-and-tag-threads` are one-time backlog-clearing
passes). New email Threads and Meetings keep getting captured over time,
so this Skill keeps watching for a real company domain the operator
hasn't seen yet, and pings them about it -- it never guesses a
classification itself.

## Two scripts, two different jobs

- **`find_new_entities.py`** -- mechanical, no judgment. Scans Threads
  (`participant_links`) and Meetings (`attendees`) for real email
  domains, compares against every domain already covered by an existing
  `Work/Entities.md` entry (comma-split, so a multi-domain entry like
  Core42's own "core42.ae, core42.ai" correctly counts as two), and
  APPENDS a new entry for anything genuinely new -- defaulting to
  `Ignore: Yes` (safe: `create-companies-partners.py` never creates a
  hub note for an Ignore: Yes entry). **Never rewrites the file** the way
  `entity-domain-extraction`'s own one-time `build_entities_report.py`
  does -- by now Entities.md is the operator's own hand-curated file, and
  a rewrite would destroy that curation. If nothing new is found, the
  file isn't touched at all (not even re-rendered) -- returns an empty
  `new_entities` list.
- **`apply_entity_decision.py`** -- mechanical, no judgment. Given a
  company name/domain and ONE decision (`customer`/`partner`/
  `affiliate`/`ignore`), flips that one entry's own `Ignore` flag and
  section, and optionally sets `Affiliate of`/appends `Aliases`. This is
  what a live chat session calls once IT has parsed the operator's own
  reply -- this script never parses natural language itself, mirroring
  `apply_thread_review.py`'s own "the agent decides, the script applies"
  split.

## How to run the discovery half (recurring)

```
terminal(command="python find_new_entities.py --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\"", cwd="<this Skill's scripts/ folder>")
```

**Never wrap this in `bash -lc "..."`** -- same categorical Hermes
`terminal`-tool approval-block documented in every other Skill's own
SKILL.md in this sequence; a bare `python ...` command runs without a
prompt.

Prints `{"new_entities": [{"name","domain","thread_count",
"meeting_count"}, ...], "entities_path"}`.

**If `new_entities` is non-empty**, compose ONE WhatsApp message listing
every new entry, e.g.:

```
Found 3 new companies in Threads/Meetings, added to Entities.md
(Ignore: Yes until you approve):

- Investbank (investbank.ae) -- 1 meeting
- Inb (inb.ae) -- 1 meeting
- Oracle (oracle.com) -- 1 meeting

Reply mentioning Entities.md and your decision for any of these (e.g.
"Entities: make Oracle a partner", "Entities: Inb is an affiliate of
Investbank", "Entities: ignore Inb") and I'll update the file.
```

The "Entities:" / "Entities.md" anchor word in both the notification and
the reply is deliberate (2026-08-21, live-confirmed incident): a bare
"add Oracle as a partner" with no anchor was once misrouted entirely --
Hermes' own general chat agent interpreted it as a generic CRM/contact
request and asked the operator an unrelated clarifying poll about which
external tool to use, never reaching this Skill or
`apply_entity_decision.py` at all. A cron-triggered notification runs as
a one-shot execution -- the operator's later WhatsApp reply does NOT
inherit that run's own `--skill new-company-discovery` context, so
without an unambiguous anchor there's nothing connecting the reply back
to this Skill except Hermes' own generic semantic skill-matching, which
this incident showed is not reliable enough alone.

**If `new_entities` is empty, stay silent** -- reply with nothing
substantive (this job is delivered via `--deliver whatsapp`, so
whatever you say becomes a WhatsApp message; a "nothing new today" ping
on every single scheduled run is noise the operator explicitly doesn't
want -- see this codebase's own repeated tag-cascade/duplicate-noise
lessons elsewhere in this vault).

## How to handle the operator's own reply (live chat, not the cron job)

Any message mentioning Entities/Entities.md alongside a company name and
a decision -- "Entities: make Oracle a partner", "Entities.md: Inb is an
affiliate of Investbank", "Entities: ignore that one", "Entities: add
'Investment Bank' as an alias for Investbank" -- is this Skill's job,
regardless of which conversation or how long after the original
notification it arrives (a fresh chat session has no memory of that
notification -- the anchor word is what makes the connection, not
conversational continuity). Parse the company name and the real intent,
then call:

```
terminal(command="python apply_entity_decision.py --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --company \"Oracle\" --decision partner [--affiliate-of \"PARENT\"] [--aliases \"extra text\"]")
```

`--company` matches an entry's own `Company Name` OR any of its own
`Domain` values, case-insensitive -- either "Oracle" or "oracle.com"
works. `--decision affiliate` needs `--affiliate-of` to mean anything
real; `--decision customer`/`partner` can also carry `--affiliate-of` if
the operator names a parent in the same breath ("make Simplai a partner,
affiliate of G42").

**Never fabricate a company that isn't already a pending (or existing)
Entities.md entry** -- if the operator names something this Skill never
flagged, that's `entity-domain-extraction`'s/the operator's own manual
edit's job, not this one. Report `{"error": ...}` back honestly if
`apply_entity_decision.py` returns one (a typo'd company name, most
likely) rather than guessing which entry they meant.

Once approved (`Ignore: No`), the entry sits ready for
`create-companies-partners.py`'s own next run to actually create the hub
note -- this Skill never creates one itself.

## Pitfalls

- **This Skill never decides Customer vs. Partner vs. Ignore itself** --
  every new entry defaults to `Ignore: Yes`, full stop. The WhatsApp
  approval is the only path to `Ignore: No`.
- **A domain already covered by ANY existing entry (including a
  multi-domain one) is never re-flagged** -- `_split_domains`-aware
  comparison, same discipline `create-companies-partners.py` itself
  uses for domain matching.
- **Running `find_new_entities.py` is always safe to repeat** -- a
  domain it already added stays covered (its own new entry's `Domain`
  field now counts), so a second run in the same day finds nothing new
  from the same evidence.

## Verification

- Report `new_entities`' own length and, for each, its evidence counts.
- After an `apply_entity_decision.py` call, confirm the returned
  `section`/`ignore`/`affiliate_of` match what the operator actually
  asked for before considering the reply "handled."
