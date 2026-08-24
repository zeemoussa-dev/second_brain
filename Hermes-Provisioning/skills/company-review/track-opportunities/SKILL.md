---
name: track-opportunities
description: Creates, links, and answers questions about sales Opportunities filed under a real Customer hub note. Use this whenever the operator's message is about creating a new opportunity/deal/opp (e.g. "create a new opp", "new opportunity for ADNOC"), linking a Thread or Meeting to an existing one ("link this thread to the ADNOC HPC Expansion opp"), or asking what opportunities exist / their status / consumption for a Customer ("what opportunities do we have in ADNOC", "what's the forecasted consumption this month").
version: 0.2.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, opportunity, customer, whatsapp, conversational]
---

# Track Opportunities

**Live and conversational, not cron-triggered** -- unlike every capture
pipeline in this vault, this Skill runs mid-chat (WhatsApp or otherwise)
the moment the operator's own message matches its purpose. Three real
jobs: create, link, and answer. Same discipline as everywhere else in
this sequence -- an Opportunity's real content (which Customer, what
it's about) is only ever what the operator actually tells you; never
fabricate a Customer or an Opportunity that doesn't already exist.

## Prerequisites

- Real Customer hub notes must already exist (`create-companies-partners`'s
  own job) -- Opportunities are scoped to Customers only, never Partners
  (a sales/revenue concept, not a vendor relationship).
- Vault path (pass as `--vault-path` on every script call):
  `C:\myWorx\Moussa MD\Moussa Brain`

## Structure this builds

```
Work/Customers/<Customer>/Opportunities/<Title>/
    <Title>.md          -- the Opportunity's own note
    files/                -- related files, saved here directly by you
                             (write_file) as they come in -- no separate
                             capture script, mirrors how a Thread's own
                             files/ folder works.
```

Frontmatter: `type: "Opportunity"`, `customer` (the real Customer hub's
own name), `status` (default `"Open"`), `expected_consumption` (free
text -- "capture then organize", operator, 2026-08-22: no rigid unit
imposed now, a later pass structures it once real patterns are visible),
`technologies` (list), `created`, `tags` (`customer/<slug>`,
`kind/opportunity`).

Body: `## Summary` / **`## Log`** (dated, diary-style entries -- notes
and log are the SAME thing here, operator's own explicit merge, e.g. "-
2026-08-22: Met [[Person X]] (Microsoft), asked about status, he gave
feedback that ...") / `## Actions` / `## Related` / `## Files`.

The Customer hub note itself gets a new `## Opportunities` section
(wikilinks down, mirrors the existing `## Affiliates` pattern) -- so
opening `Adnoc.md` directly shows every Opportunity, no search needed.

## Job 1: Create

Triggered by "create a new opp/opportunity" (or equivalent). **Ask ONE AT A
TIME, real back-and-forth, in this order** (revised by the operator,
2026-08-22 -- Customer is the only question you block on; everything after
it is a skippable follow-up):

1. "Which customer is this for?" -- **mandatory.** An Opportunity cannot
   exist without a real Customer hub to file it under. Keep asking (or ask
   them to confirm the spelling) until you have one that resolves for real
   -- never fabricate a Customer, never proceed without this answer.
2. "What's this opportunity called?" -- becomes the title (and the
   folder/file name). If they don't have one / skip it, default to
   `"New Opportunity - <Customer> - <today's date>"` rather than blocking --
   the note still needs a title to be created and findable.
3. "Do you know the expected consumption?" -- free text. If skipped/unknown,
   leave it blank.
4. "What technologies are you considering?" -- if skipped/unknown, leave it
   blank.

**Do not stall waiting for 3 or 4.** Ask each once; if the operator says
"skip", "not sure", "don't know", or just doesn't answer it, treat that
field as blank and move on. A real skeleton note the operator fills in later
beats a conversation that never finishes. Once you have the Customer (and
have asked about the rest, answered or not), create it.

Once you have real answers (blank where skipped), `write_file` a scratch
JSON payload, then call the one script -- as a PLAIN, direct `terminal`
call, using the script's own full absolute path:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\track-opportunities\\scripts\\create_opportunity.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --input-file <scratch path>")
```

Payload: `{"title": str, "customer": str, "expected_consumption": str,
"technologies": [str, ...], "status": str}` (`status` optional, defaults
`"Open"`).

**If the script returns `{"error": ...}` because the named customer
doesn't resolve to a real Customer hub note, say so honestly and ask the
operator to confirm the spelling or run `create-companies-partners`
first -- never guess, never create a placeholder Customer yourself.** If
it errors because an Opportunity with that title already exists for that
Customer, tell the operator and ask whether they meant a different title
or actually wanted to update the existing one (updating isn't this
Skill's job yet -- for now, just report it).

## Job 2: Link a Thread or Meeting

Triggered by "link this [thread/meeting/email] to the [X] opp" (or
equivalent) -- **manual only, the operator's own explicit choice,
2026-08-22: never a proactive/automatic suggestion.** A Customer can
have several open Opportunities at once, so "this thread is about ADNOC"
alone never tells you which one -- only the operator's own real intent
does.

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\track-opportunities\\scripts\\link_opportunity.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --note-path \"<Thread or Meeting's own concept .md path>\" --opportunity \"<title>\" [--customer \"<name>\"]")
```

If the title matches more than one Opportunity across different
Customers, the script reports the real candidates and asks for
`--customer` to disambiguate -- never guesses which one. If it matches
zero, it means no such Opportunity exists yet -- report that honestly,
don't create one as a side effect of linking.

## Job 3: Answer questions

"What opportunities do we have in ADNOC" / "what's the status of the
HPC Expansion opp" / "what's the forecasted consumption this month" --
**no script for this, just look**: `search_files`/`read_file` the real
Customer hub's own `## Opportunities` section (or the Customer's own
`Work/Customers/<Name>/Opportunities/` folder directly) and read what's
actually there.

**Real limitation, be upfront about it**: `expected_consumption` is free
text (the operator's own explicit "capture then organize" choice), not a
structured number -- a question like "total forecasted consumption this
month" gets your own honest synthesis from reading each Opportunity's
own text, not a precise summed figure. Say so if the operator seems to
expect an exact number; don't fabricate false precision.

## Pitfalls

- **Never fabricate a Customer.** Same rule as every other Skill in this
  sequence.
- **Never fabricate an Opportunity to satisfy a link request.** Job 2
  only ever links to one that already exists.
- **Never wrap either script in `bash -lc "..."`** -- same categorical
  Hermes `terminal`-tool approval-block documented throughout this
  vault's own Skills; a bare `python ...` command with the script's own
  full absolute path (never a bare filename -- see
  `summarize-and-tag-threads`'s own SKILL.md for the live-confirmed
  incident) runs without a prompt.
- **This Skill's own trigger phrasing needs to be unambiguous** -- a
  live incident elsewhere in this vault (`new-company-discovery`) showed
  a vague request getting misrouted into a totally unrelated generic
  "which tool" flow. If a reply doesn't clearly match Job 1/2/3's own
  described intent, ask a clarifying question rather than guessing which
  job it is.

## Verification

- After a creation, confirm the returned `path` is real and the Customer
  hub's own `## Opportunities` section now lists it.
- After a link, confirm the Thread/Meeting's own `opportunities`
  frontmatter and `## Related` section both show the right Opportunity,
  and that a genuinely ambiguous title correctly errored rather than
  guessing.
