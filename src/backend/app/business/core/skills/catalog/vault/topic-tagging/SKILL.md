---
name: topic-tagging
description: Add `topic/*` subject tags to Thread notes from their existing summaries, selecting only from the closed vocabulary in Settings/Tag Taxonomy.md. Makes the corpus searchable by subject rather than only by account.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, librarian, tagging, knowledge-base, vault-write]
---

# Topic Tagging

Threads carry `customer/*`, `partner/*` and `engagement/*` tags today, so
the corpus can be sliced by **who** a conversation involved. Nothing
records **what it was about**: as at 2026-09-08 there were zero `topic/*`
tags across 278 Threads. This Skill fills that gap, and only that gap.

Your judgment does the classifying. The scripts select candidates and
record decisions -- neither one ever decides a topic.

## Prerequisites

- `SECOND_BRAIN_DATA_PATH` must be set (the scripts read
  `Settings/Tag Taxonomy.md` from it). They fail loudly if it is unset
  rather than guessing a vocabulary.
- Vault path (pass as `--vault-path`): `$SECOND_BRAIN_VAULT_PATH`
- No network calls. Pure local vault read/write.

## The vocabulary is CLOSED -- this is the whole point

Every topic you assign must be one of the 32 values declared under
`## topic/*` in `Settings/Tag Taxonomy.md`. You do not invent topics, and
you do not extend the list from here -- the taxonomy file says so itself:
"Extend the list here first; never in the prompt."

`apply_topic_tags.py` re-checks every value against that file and rejects
anything undeclared, so an invented tag never reaches a note. Treat a
rejection as a signal you drifted, not as an obstacle to route around.

**A wrong tag is worse than no tag**, because it makes retrieval
confidently incomplete -- the search looks like it worked. When a Thread
genuinely does not fit any declared topic, give it `topic/administrative`
or `topic/notification` if it is housekeeping, and otherwise return a low
confidence and let it quarantine.

## Step 1 -- select a batch

Call the selector as a PLAIN, direct `terminal` call, `command` starting
with `python` itself, and the script's own full absolute path:

```
terminal(command="python \"${HERMES_SKILL_DIR}\scripts\select_untagged_notes.py\" --vault-path \"<vault>\" --limit 25")
```

**Never wrap this in `bash -lc "..."`** (or any `-c`/`-lc` shell-string
form) and never use `python -c`. Hermes' `terminal` tool categorically
requires human approval for those, which stalls a cron run with nobody
there to approve it. The bare form above runs unprompted. Use the
absolute path even if a `cwd` is also available -- a cron-triggered
agent's working directory is the user's home folder, not this Skill's
`scripts/`.

It returns each candidate's `path`, `existing_tags` and its own
`## Summary` text, so **you classify the whole batch from this one call**
-- do not go and re-read the Thread folders.

### Why it reads the summary, not the messages

Threads are the operator's RAW evidence layer, deliberately excluded from
the vault index and retrieved on demand. A tagging pass has no business
dragging that raw layer back through a model, and it does not need to:
`summarize-and-tag-threads` has already distilled each Thread into a
`## Summary`. Classify from that.

### Meetings are out of scope for now

`--include` defaults to `threads`. 207 of 208 Meeting notes have an
**empty** `## Summary` and only `## Related` populated -- there is no
text to classify them from, and a topic guessed from a meeting title is
exactly the confidently-wrong tag this Skill exists to avoid. Meetings
need a summarization pass of their own first. Run `--include both` only
to report that gap, never to tag from titles.

## Step 2 -- classify

For each candidate, read its summary and decide:

- **1 to 3 topics**, most specific first. Most Threads have one. Three is
  the hard maximum and the script enforces it.
- **A confidence between 0 and 1.** Be honest: this is the only thing
  standing between a guess and a permanent wrong tag. Anything below
  `0.6` is quarantined for the operator instead of written.
- Prefer the **specific** topic over the general one --
  `topic/tender` over `topic/proposal` when it is genuinely a tender.
- `topic/notification` and `topic/administrative` are real answers. A
  large share of this corpus is automated service mail, and labelling it
  honestly is more useful than forcing a commercial topic onto it.

## Step 3 -- apply

`write_file` a scratch JSON payload, then one call:

```
terminal(command="python \"${HERMES_SKILL_DIR}\scripts\apply_topic_tags.py\" --input-file <scratch path>")
```

Payload shape -- the whole batch in one call:

```json
{"entries": [
  {"note_path": "<path exactly as the selector returned it>",
   "topics": ["topic/tender", "topic/pricing"],
   "confidence": 0.9}
]}
```

The script preserves every existing non-`topic/` tag, replaces any
previous topic tags with your current judgment, de-duplicates the tag
list, stamps `topics_tagged_at`, and leaves the body untouched.

Its result gives you a per-note `status`: `tagged`, `rejected`
(undeclared topic -- never written), `quarantined` (below the confidence
floor -- never written), `skipped`, or `error`. Rejected and quarantined
entries are appended to `Settings/Tag Taxonomy Review.md` for the
operator.

## Resumability

Safe to run in independent batches, and safe to re-run. A Thread is due
when it has no `topic/*` tag, or when `last_message_at` is newer than
`topics_tagged_at` -- the same watermark rule
`summarize-and-tag-threads` already uses. Work through batches of 20-25,
then stop cleanly and report progress (`counts.due` and
`counts.remaining_after_batch` come back from the selector). Do not try
to clear all 278 in one sitting.

## Pitfalls

- **Never invent a topic.** If nothing fits, that is information --
  return low confidence and let it quarantine.
- **Never tag from a subject line or filename.** If the selector did not
  give you a summary, the note is not classifiable yet.
- **Never hand-edit frontmatter to work around a rejection.** That
  bypasses the closed-list check entirely. If the script will not apply
  something, stop and report it.
- **Pass paths back exactly as the selector returned them.** They are
  plain absolute paths; do not re-derive or normalise them.

## Verification

- Report totals: classified, tagged, rejected, quarantined.
- Report the distinct topics you assigned across the batch -- if one
  topic dominates implausibly, say so; that is a signal you anchored.
- Spot-check one tagged Thread: its previous tags still present, its new
  `topic/*` tags added, `topics_tagged_at` stamped, body unchanged.
