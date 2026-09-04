---
name: track-opportunities
description: Creates, updates, links, and answers questions about sales Opportunities filed under a real Customer hub note. Use this whenever the operator's message is about creating a new opportunity/deal/opp (e.g. "create a new opp", "new opportunity for ADNOC"), adding an update/log entry/action/related link to an EXISTING one ("log that I spoke to procurement on the ADNOC HPC opp", "add an action item to renew the Aldar deal"), linking a Thread or Meeting to an existing one ("link this thread to the ADNOC HPC Expansion opp"), or asking what opportunities exist / their status / consumption for a Customer ("what opportunities do we have in ADNOC", "what's the forecasted consumption this month").
version: 0.4.0
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
the moment the operator's own message matches its purpose. Four real
jobs: create, update, link, and answer. Same discipline as everywhere else in
this sequence -- an Opportunity's real content (which Customer, what
it's about) is only ever what the operator actually tells you; never
fabricate a Customer or an Opportunity that doesn't already exist.

## Prerequisites

- Real Customer hub notes must already exist (`create-companies-partners`'s
  own job) -- Opportunities are scoped to Customers only, never Partners
  (a sales/revenue concept, not a vendor relationship).
- Vault path (pass as `--vault-path` on every call):
  `$SECOND_BRAIN_VAULT_PATH`
- Template id for every `vault_manager.py` call below: `opportunity`.

**Create and Update (Jobs 1-2) are plain `vault_manager.py` calls now, no
per-job script** (2026-08-30 -- an earlier pass had its own
`create_opportunity.py`/`update_opportunity.py`; both were deleted once
the engine itself learned to resolve a Customer by name/alias and derive
where an Opportunity lives from it -- "extending what it can write
happens by adding a Template.json, never by writing a new script" now
holds for real). Only **Job 3 (Link)** still has its own script --
linking a Thread/Meeting is a genuinely different operation (writing
into a DIFFERENT note kind not on this engine yet), not reducible to a
plain template-driven create/update.

## Structure this builds

```
Work/Customers/<Customer>/Opportunities/<Title>/
    <Title>.md           -- the Opportunity's own note: Summary/Actions/
                             Related, plus a "## Log & Captures" index
                             (auto-populated wikilinks to the two files
                             below -- same shape Customer/Partner hub
                             notes already use).
    <Title>-log.md        -- dated, diary-style entries (2026-08-31,
                             operator: "the Opp has one file it should
                             have Capture and log as well" -- split off
                             the root note the same way Customer/
                             Partner's own log.md already is).
    <Title>-captures.md   -- a note that a real file/detail arrived (the
                             files THEMSELVES still live in files/ below
                             -- this is the log line about them, same
                             role the old "## Files" section had).
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

Root body: `## Summary` / `## Actions` / `## Related` / `## Log &
Captures` (the auto-populated index -- never edit this one directly,
`vault_manager.py`'s own `create()` regenerates it). The real diary
content (dated entries, e.g. "- 2026-08-22: Met [[Person X]] (Microsoft),
asked about status, he gave feedback that ...") lives in `<Title>-log.md`'s
own `## Log` section; a file-arrival note lives in `<Title>-captures.md`'s
own `## Captures` section -- both reached via `modify-section`'s
`child_suffix` field (Job 2 below), never by editing those files by hand
with a bare `write_file`.

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
JSON payload, then call `vault_manager.py` directly (the SAME shared
engine `capture-notes`/`capture-files`/every other real Skill in this
vault uses -- its own full absolute path never changes):

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\track-opportunities\\scripts\\vault_manager.py\" create --template-id opportunity --input-file <scratch path>")
```

Payload: `{"title": str, "parent_value": str, "frontmatter":
{"status": str, "expected_consumption": str, "technologies": [str, ...]}}`
(`parent_value` is the Customer's own real name or a known alias --
resolved against real Customer hub notes, never fabricated; `status`
optional, defaults `"Open"` via the template's own default). Note_name,
the Customer cross-reference, the `customer/<slug>` tag, and the
backlink into the Customer's own `## Opportunities` section are all
derived automatically from the resolved parent -- nothing else to pass.

**If the call returns `{"error": ...}` because the named customer
doesn't resolve to a real Customer hub note, say so honestly and ask the
operator to confirm the spelling or run `create-companies-partners`
first -- never guess, never create a placeholder Customer yourself.** If
it errors because an Opportunity with that title already exists for that
Customer, tell the operator and ask whether they meant a different title
or actually wanted to update the existing one -- if the latter, that's
Job 2 below.

## Job 2: Update an existing Opportunity

Triggered by any real update to an Opportunity that already exists --
"log that I spoke to procurement", "add an action item to follow up
next week", "note that Microsoft is now involved", a status/consumption
change mentioned in passing. **Never creates an Opportunity as a side
effect** -- if it doesn't already exist, say so and offer Job 1 instead.

Map what the operator said onto ONE of the real sections (ask if it's
genuinely unclear which one):
- **Log** -- a dated diary entry, what happened / who you talked to.
  Almost always `mode: "append"`. Lives on the `-log.md` child, not the
  root -- pass `"child_suffix": "log"` in the payload.
- **Actions** -- a follow-up/next-step. Almost always `append`. Root
  section, no `child_suffix`.
- **Related** -- a link to something else relevant (a person, a
  document, another note). `append`. Root section, no `child_suffix`.
- **Summary** -- the current-state description itself changed (not a
  new event) -- this one is usually `mode: "replace"`, not append. Root
  section, no `child_suffix`.
- **Captures** -- a real file arrived; `write_file` it directly into the
  Opportunity's own folder's `files/` subfolder (same as Job 1's own
  Structure note) -- no script call needed for the file itself, only
  call this script if you also want to log a line noting it arrived.
  Lives on the `-captures.md` child -- pass `"child_suffix": "captures"`.

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\track-opportunities\\scripts\\vault_manager.py\" modify-section --template-id opportunity --section \"<Log|Actions|Related|Summary|Captures>\" --mode append --input-file <scratch path>")
```

(`--mode replace` for a Summary rewrite -- everything else is `append`,
the default the SKILL.md examples above already assume.)

Payload: `{"content": str, "title": str, "parent_value": str, "child_suffix":
str}` (`child_suffix` only for Log/Captures -- `"log"` or `"captures"`;
omit it entirely for Actions/Related/Summary, which stay on the root
note). `parent_value` is matched the same way as Job 1 (real Customer
name or a known alias); `title` is matched exactly against the
Opportunity's own real title within that Customer -- this call resolves
the Customer AND finds the Opportunity by name itself, the same way Job
1's own create call does; it never creates one that doesn't already
exist (the template's own `on_missing: "error"` enforces this centrally,
not anything you have to check for yourself). A `child_suffix` naming a
child the template doesn't declare is a real error, not a silent no-op.

**If the call errors because the Customer or the Opportunity doesn't
resolve, say so honestly -- same never-fabricate discipline as every
other job here.**

## Job 3: Link a Thread or Meeting

Triggered by "link this [thread/meeting/email] to the [X] opp" (or
equivalent) -- **manual only, the operator's own explicit choice,
2026-08-22: never a proactive/automatic suggestion.** A Customer can
have several open Opportunities at once, so "this thread is about ADNOC"
alone never tells you which one -- only the operator's own real intent
does.

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\track-opportunities\\scripts\\link_opportunity.py\" --note-path \"<Thread or Meeting's own concept .md path>\" --opportunity \"<title>\" [--customer \"<name>\"]")
```

If the title matches more than one Opportunity across different
Customers, the script reports the real candidates and asks for
`--customer` to disambiguate -- never guesses which one. If it matches
zero, it means no such Opportunity exists yet -- report that honestly,
don't create one as a side effect of linking.

## Job 4: Answer questions

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
- **Never fabricate an Opportunity to satisfy an update or link request.**
  Job 2 and Job 3 only ever act on one that already exists.
- **Never wrap any of these scripts in `bash -lc "..."`** -- same categorical
  Hermes `terminal`-tool approval-block documented throughout this
  vault's own Skills; a bare `python ...` command with the script's own
  full absolute path (never a bare filename -- see
  `summarize-and-tag-threads`'s own SKILL.md for the live-confirmed
  incident) runs without a prompt.
- **This Skill's own trigger phrasing needs to be unambiguous** -- a
  live incident elsewhere in this vault (`new-company-discovery`) showed
  a vague request getting misrouted into a totally unrelated generic
  "which tool" flow. If a reply doesn't clearly match Job 1/2/3/4's own
  described intent, ask a clarifying question rather than guessing which
  job it is.

## Verification

- After a creation, confirm the returned `path` is real and the Customer
  hub's own `## Opportunities` section now lists it.
- After an update, confirm the returned `path` is real (a Log/Captures
  update returns the CHILD file's own path, `<Title>-log.md`/
  `<Title>-captures.md`, not the root's) and the section you targeted
  actually shows the new content (an append should sit below whatever
  was already there, not replace it).
- After a link, confirm the Thread/Meeting's own `opportunities`
  frontmatter and `## Related` section both show the right Opportunity,
  and that a genuinely ambiguous title correctly errored rather than
  guessing.
