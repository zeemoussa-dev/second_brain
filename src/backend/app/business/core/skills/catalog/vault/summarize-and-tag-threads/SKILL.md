---
name: summarize-and-tag-threads
description: Enrichment for email Threads. Reads a Thread once and emits ONE structured extraction -- summary, the people it reveals, the actions it contains, the facts worth remembering -- which is then fanned out to the Thread, the People notes and the company hubs. Use when asked to summarize, enrich or catch up on threads, and as the Enrichment pipeline's scheduled job.
version: 0.6.1
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, partner, summary, enrichment]
writes:
  - action: apply_thread_extract
    template: thread
    requires: 1
    sections: [Summary, Actions]
---

# Enrich Threads

**One read, many writes.** Reading a Thread is the expensive part of this
job, so read it ONCE and emit everything worth knowing as a single JSON
object -- summary, people, actions, important facts -- then let a script
fan that out. Four separate passes would cost four reads of the same
content for the same result (operator, 2026-09-10).

You do the reading and the judgment. `apply_thread_extract.py` does the
writing and decides nothing: every value it writes comes from your JSON.

## What is yours and what is not

**Metadata is not your job.** Company tags, engagement classification,
moving People into hub folders, creating hubs -- all of that is
mechanical, decided without a model, and runs nightly on its own. Do not
reproduce it. Your job is only what needs a reader: what this
conversation is *about*, and what it *reveals*.

## Prerequisites

- Real Customer/Partner hub notes must exist, so you have something to
  recognize company names against. If `Work/Customers/` and
  `Work/Partners/` are empty, stop and say so.
- Vault path: `$SECOND_BRAIN_VAULT_PATH`. Pass it as `--vault-path` on
  every script call.
- Pure local vault read/write. No Outlook, no network.

## The loop

A scheduled run's prompt header gives the EXACT interpreter and script folder -- use those verbatim. The deployed Skill is flat: there is no scripts\ subfolder, so a path copied from the repo layout does not exist on the machine that runs it.

### 1. Ask which Threads are due

```
terminal(command="python \"${HERMES_SKILL_DIR}\select_threads.py\" --limit 25")
```

It returns the batch, oldest first. **Do not pick threads yourself** and
do not widen the batch: the selector already knows which threads have
never been enriched and which have grown since they were, and the limit
is what keeps a run's cost bounded.

It is deliberately safe to run this while a history backfill is still
capturing. A backfill appends to the OLDEST end of existing
conversations, so the selector compares message COUNTS rather than
timestamps and will hand you a thread again if it grows. You may
occasionally re-read one. That is the intended trade.

### 2. Read each Thread as text

```
terminal(command="python \"${HERMES_SKILL_DIR}\read_thread.py\" --thread-dir \"<dir>\"")
```

Always this, never the message notes directly. Capture stores each body
exactly as it arrived, and **83% of a stored Outlook body is markup** --
measured across 119 real Threads, 6.66 M raw chars reducing to 1.14 M.
Stripped, a Thread averages **~5,000 tokens** (sampled across 2,282 real
Threads, 2026-09-11); read raw it would be roughly six times that.

Pass `--max-chars N` on a Thread big enough to threaten your context.
Truncation announces itself in the output; when you see it, say the
Thread was truncated rather than writing a summary that implies it was
complete.

### 3. Emit ONE extraction per Thread

Write the JSON to a scratch file, then apply it:

```
terminal(command="python \"${HERMES_SKILL_DIR}\apply_thread_extract.py\" --input-file <scratch path>")
```

```json
{
  "schema_version": 1,
  "thread_path": "<the Thread's own concept .md path>",
  "summary": "What was actually discussed, decided or asked.",
  "companies": ["Masdar"],
  "people": [
    {"email": "a@b.com", "name": "...", "job_title": "...",
     "department": "...", "company_name": "...", "phone": "...",
     "linkedin": "..."}
  ],
  "actions": [{"text": "...", "owner": "...", "due": "..."}],
  "important_info": [{"text": "...", "company": "Masdar"}]
}
```

`schema_version` is required and checked. The JSON is a contract between
your one read and several independent appliers; when a field is added,
they have to know which shape they are reading.

#### summary

What was actually discussed, decided or asked -- not a restatement of the
subject line. **Wiki-tag every company you recognize in the prose
itself**: if you write "reviewed the ADNOC account plan", make it
`[[ADNOC]]`. Match against a hub's real `name` or `aliases`, never
against whatever string a sender typed.

#### companies

Every company the Thread is genuinely about, not only the ones you
wikilinked. A Thread can be about several (operator: "Sometimes Emails
will contain more than one Company, tag all companies") -- an internal
forecast thread naming five customer accounts with nobody from those
companies on it is a real and common case. Detect it from content; never
assume "no external participant = no company".

**Use the SPECIFIC entity, never its parent.** A Thread about Masdar gets
`Masdar`, not `Mubadala` (operator: "the company in message is the
company not the parent"). The parent relationship already lives on
Masdar's own `affiliate_of` and Mubadala's `## Affiliates` back-link.

Every name here is also checked against the real hubs. One that matches a
hub, by name or alias, is tagged on the Thread; one with no hub is
filed for the operator to review, never created and never written into
`Entities.md` -- see **Companies nobody knew about** below. So name a
company you are confident the Thread is about even when you suspect it
has no hub yet: that is exactly the signal that pass is looking for.

#### people

Only what the Thread actually reveals -- almost always from an email
signature. **Never guess a job title from context.** These fill blanks on
real Person notes that other threads reference, and the applier is
deliberately fill-only: a value already there is never overwritten, so a
wrong guess you make is only prevented by you not making it.

Do not send `name` or `email` as corrections. They are the note's
identity, set at capture from real message headers.

A person the vault has never seen is reported and skipped, not created.
Capture owns Person creation, from headers -- not from your reading of a
signature.

#### actions

Real commitments and requests, with an owner and a due date when the
Thread states one. Leave them out when it does not; an invented deadline
is worse than a missing one. These become checkboxes in the Thread's
`## Actions`.

#### important_info

Facts worth remembering about the relationship beyond this Thread -- a
budget approved, a reorganisation, a change of decision-maker. Name the
company each belongs to. Carried in the persisted extraction for the
hub-side applier; not written by this script.

**If a Thread reveals nothing, say so with empty lists.** An empty
`people` or `actions` is a real and correct answer. Do not manufacture
content to fill the shape.

## Two rules that cost real runs to learn

**Always the script's full absolute path, never a bare filename.** A bare
`apply_thread_review.py` live-failed 19 times in a row in one cron run --
`python.exe: can't open file '<OPERATOR_HOME>\apply_thread_review.py'` --
because a cron-triggered agent's working directory is the user's home
folder, not this Skill's `scripts/`. Use the `${HERMES_SKILL_DIR}` form
above even when a `cwd` parameter is also available.

**Never wrap a call in `bash -lc "..."`** or any other `-c`/`-lc`
shell-string form. Hermes' `terminal` tool categorically requires human
approval for those, which stalls a cron-triggered run with nobody there
to approve it. A whole batch once stalled 20+ minutes on this, with the
agent falling back to hand-patching Thread files directly -- which
bypasses every applier and its checks. If a script will not run, **stop
and report it**; never improvise a workaround.

## What the applier guarantees

- **The extraction is persisted before anything is applied**, under
  `<data>/data/ThreadExtracts/<thread-id>.json`. If an applier turns out
  to have a bug, the fix re-applies from disk rather than re-reading
  thousands of Threads through a model.
- **Person fields are filled, never overwritten.**
- **Freshness is stamped last**, so a crash mid-apply leaves the Thread
  looking unenriched and it is simply picked up again.

## Companies nobody knew about

Domain-based discovery only ever finds a company someone **emailed**. A
company *discussed in the body* -- an account named in an internal
forecast thread, a competitor, a partner a third party mentioned -- has
no domain to be found by, and this pass is the only one that reads prose.

So every name in your `companies` that matches no real hub (by `name` or
any alias) is accumulated in `<data>/data/UnknownCompanies.json` with a
count and a few example Threads. Nothing is created and `Entities.md` is
never touched: the classification that follows -- Customer or Partner,
and the real company name behind a half-remembered one -- is the
operator's own call, and a model naming a company is a suggestion.

Read from the hubs rather than from `Entities.md` on purpose: a row the
operator marked `Ignore` or `Deleted` must not count as known, or a
company they deliberately dismissed would be re-proposed forever.
