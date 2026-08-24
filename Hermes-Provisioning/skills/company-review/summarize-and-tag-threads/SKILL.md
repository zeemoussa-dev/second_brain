---
name: summarize-and-tag-threads
description: One-time, long-running Thread summarization and company wiki-tagging pass.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, partner, summary, one-time]
---

# Summarize & Tag Threads (Step 4 of the company/partner sequence)

**Step 4 of 4, the last one.** Real work, not mechanical: read every
Thread, understand what it's actually about, write a real summary, and
recognize which known Companies (Customers/Partners/Affiliates -- Step 3
already built their real hub notes) it's genuinely about. This has to be
YOUR OWN judgment, every time -- there is no script that can read and
understand a conversation for you (operator, 2026-08-21: "This should be
done by Prompts as much as possible... Tagging is the only task that
needs code"). `apply_thread_review.py` exists ONLY to apply a decision
you already made -- it never decides anything itself.

## Prerequisites

- Run `entity-domain-extraction` then `create-companies-partners` first
  -- this Skill needs real Customer/Partner/Affiliate hub notes to
  recognize company names against. If `Work/Customers/` and
  `Work/Partners/` are empty, stop and say so rather than tagging
  nothing usefully.
- No `pywin32`, no Outlook, no network calls beyond your own normal
  reasoning -- pure local vault read/write.
- Vault path (pass as `--vault-path` on every script call):
  `C:\myWorx\Moussa MD\Moussa Brain`

## Before you start: build your own company list

`search_files` or `read_file` every `Work/Customers/**/*.md` and
`Work/Partners/**/*.md` EXCEPT the ones ending in `-log.md`/
`-captures.md` (those are logs, not company identities). For each,
note its `name` and `aliases` frontmatter -- this is the real,
authoritative list of what "a known company" means for this pass. Keep
it in mind for every Thread you read; a company mentioned in a Thread
that ISN'T on this list is not this Skill's job to add (that's Step 3,
gated through the operator's own curated `Entities.md` -- never invent a
new hub note here).

## Resumability -- this runs across MULTIPLE sessions

209 Threads is too much for one continuous session's own context (the
first validation run used ~150K tokens for just 8) -- this pass runs as
several separate, bounded batches over time, not one sitting.

**Skip rule (2026-08-21): a Thread's own `last_summarized_at` and
`last_message_at` frontmatter fields are the real signal, not `##
Summary`.** `apply_thread_review.py` stamps both on every call --
`last_message_at` from its latest message's own `received`,
`last_summarized_at` to the time the script ran. Before summarizing a
Thread, read its frontmatter: **skip it if `last_summarized_at` is
non-empty AND `last_summarized_at >= last_message_at`** (already
summarized, nothing new since -- don't re-read it, don't re-call the
script). If `last_message_at` is newer (a message arrived after the last
summarization pass -- recurring capture keeps `last_message_at` current
even on Threads already summarized once), re-summarize it for real: read
the whole Thread again, not just the new message, since the summary
needs to reflect the full conversation. A blank `last_summarized_at`
means never summarized -- always process it. (`## Summary` being
non-empty is no longer the gate -- a Thread can have a real summary AND
still need a re-pass if new messages landed since.)

This is what makes every batch safe to run independently: work through
`Work/Threads/` in order by this rule, process up to the batch size you
were told for this run, then stop cleanly and report your own progress
(how many you did, how many remain) -- don't try to finish all 209 in
one sitting even if asked to "go full," since that risks running out of
context mid-Thread and leaving a half-applied state.

## The real per-Thread judgment

For each Thread (`Work/Threads/<Name>/<Name>.md` + its `messages/*.md`):

1. **Read the whole Thread** -- every message, not just the first one.
2. **Write a real summary** -- what was actually discussed, decided, or
   asked. Not a restatement of the subject line. This becomes the
   Thread's own `## Summary`.
3. **Wiki-tag every company you recognize IN the summary text itself**
   -- if you wrote "...reviewed the Adnoc account plan...", make that
   `[[Adnoc]]`. Match against your own list from the step above (by
   `name` OR any `aliases`), not the raw text some sender typed.
4. **List every company this Thread is genuinely about** -- not just
   the ones you happened to wikilink in prose. A Thread can genuinely be
   about more than one (operator: "Sometimes Emails will contain more
   than one Company, tag all companies") -- an internal forecast-tracker
   thread naming five customer accounts with nobody from those
   companies actually on the thread is a real, common case; detect it
   from content, never assume "no external participant = no company."
5. **Use the SPECIFIC entity, never its parent** -- a Thread about
   Masdar gets `Masdar`, not `Mubadala` (operator: "the company in
   message is the company not the parent"). The parent relationship is
   already on Masdar's own hub note (`affiliate_of`) and Mubadala's own
   `## Affiliates` backlink -- no second, redundant tag needed here.
6. **Write one short, one-line summary too** -- separate from the full
   summary, for the company log entries (step 4's own log requirement).
   "Reviewed ADNOC H2 FY26 account plan", not the full paragraph.

## Applying it

For each Thread you've just reasoned about, `write_file` a scratch JSON
payload, then call the one script -- as a PLAIN, direct `terminal` call,
`command` starting with `python` itself, and **the script's own full
absolute path, never a bare filename**:

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\company-review\\summarize-and-tag-threads\\scripts\\apply_thread_review.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --input-file <scratch path>")
```

**2026-08-21 bug fix, live-confirmed:** a bare `apply_thread_review.py`
filename (no `cwd`, no full path) live-failed 19 times in a row in one
real cron run -- `python.exe: can't open file
'C:\Users\mahmoud.moussa\apply_thread_review.py'` -- because a
cron-triggered agent's own default working directory is the user's home
folder, not this Skill's own `scripts/` folder, and nothing in the
`terminal` call told it otherwise. The run eventually self-corrected and
did complete real work (confirmed: 20 real Threads got genuinely
summarized in that same run), but only after burning ~19 wasted API
calls first. The absolute-path form above removes the dependency on
`cwd` being set at all -- always use it, never the bare filename form,
even if a `cwd` parameter is also available on the `terminal` call.

**Do not wrap this in `bash -lc "..."`** (or any other `-c`/`-lc`
shell-string form) -- confirmed live 2026-08-21
(`hermes approvals test`): Hermes' own `terminal` tool categorically
requires human approval for ANY `-c`/`-lc` shell-string invocation,
which stalls a cron-triggered run with no one there to approve it (the
exact same class of issue as `python -c "..."` in the
`email-thread-capture` Skill -- see that Skill's own Prerequisites). A
whole batch previously stalled for 20+ minutes hitting this repeatedly,
with the agent falling back to hand-patching Thread files directly
(which bypasses the tag/company-resolution/log-entry logic entirely --
never do that either; if `apply_thread_review.py` won't run, stop and
report it, don't improvise a workaround). The plain form above (a bare
`python ...` command, no shell wrapper at all) is confirmed to run
without a prompt.

Payload shape: `{"thread_path": "<the Thread's own concept .md path>",
"summary": "<full summary, with your own [[wikilinks]] already in
it>", "short_summary": "<one line>", "companies": ["Name1", "Name2"]}`
-- pass company names or aliases as you recognized them; the script
resolves them against the real hub notes itself and tells you if one
didn't resolve (`companies_unresolved` in its result -- if that's
non-empty, you named something not on your own list from step 0; don't
retry with a fabricated name, just note it).

The script handles everything mechanical from there: writes your summary
onto the Thread, tags the Thread + every message under it with
`customer/<slug>`/`partner/<slug>` (one tag per company you listed), and
appends your short_summary as a dated log line to each company's own
`<Name>-log.md` (it re-sorts the whole file newest-to-oldest itself --
you never need to worry about ordering).

**This never tags Person notes** (2026-08-21 bug fix -- an earlier
version did, cascading a Thread's own company tags onto every
participant, which tagged an internal `@core42.ai` person with every
company mentioned on every thread they were ever CC'd on). Person
tagging is exclusively domain-based and lives in
`create-companies-partners`'s own `retag_people_by_domain` -- not this
Skill's job.

## Batching for cost

209 Threads is a lot of individual LLM round-trips if done one at a
time. Read and reason about a BATCH of Threads (10-20) in one pass
before calling the script -- you can still call `apply_thread_review.py`
once per Thread in that batch (it only ever takes one Thread's data),
just don't stop to reason fresh between every single call once you've
already read and understood the whole batch.

## Pitfalls

- **Never fabricate a company hub note.** A name you don't recognize
  from your own step-0 list stays unresolved and unTagged -- report it,
  don't invent it. That gate belongs to Step 3/the operator.
- **Never skip a Thread for looking unimportant or short.** Every real
  Thread gets a real summary, even a one-line "FYI, no action needed."
- **The short_summary is genuinely short** -- one line, for a log a
  human will scan quickly across many entries. The full summary can be
  longer.
- **`companies_unresolved` in the script's result is a real signal**,
  not noise -- track it across the whole run and report the distinct
  set at the end, so the operator knows what showed up in real content
  but isn't in their curated Customer/Partner list yet.

## Verification

- Track running totals: Threads summarized, distinct companies tagged,
  distinct unresolved company names seen.
- Spot-check one real Thread's own `## Summary` (wikilinked correctly)
  and one company's own `<Name>-log.md` (newest entry actually on top).
- Report the final totals, and the full distinct `companies_unresolved`
  list if non-empty.
