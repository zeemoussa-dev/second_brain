---
name: capture-engagement
description: File what the CBO says about a company -- a meeting, a call, an agreement -- against that company's own notes. Resolve first, then apply one structured capture; never write a note by hand.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, customers, partners, capture, vault-write]
---

# Capture an engagement

The CBO reports an interaction in his own words, usually by voice:

> "Met the CEO of TAQA Distribution today, very positive. We went through the
> managed-services scope and agreed the Q1 phasing. They're sending the RFP
> next week, and I owe them the revised pricing by Friday."

That is not a loose note. It is a dated event about a specific company, with
people, facts worth keeping, and a commitment. Your job is to turn it into ONE
structured capture and let the applier file it. You decide what it says; the
applier decides where it goes.

## The loop

### 1. Resolve before anything

```
terminal(command="python \"${HERMES_SKILL_DIR}\resolve_capture.py\" --company \"<as said>\" --person \"<as said>\"")
```

Read the `status` of each block:

- **`one`** -- go ahead.
- **`ambiguous`** -- STOP and ask. Two companies can share a name and three
  people can share a first name. Return the question with the candidates;
  do not pick one.
- **`none`** -- say the company is not tracked, and show `did_you_mean` if it
  is there. Never file against a company that does not exist, and never create
  one: new companies are the operator's own call.

**A parent is not its affiliate.** "TAQA" is not "TAQA Distribution", and
"Mubadala" is not "Mubadala Health". If what was said could mean either, ask
which.

### 2. Apply exactly one capture

Write the JSON to a scratch file, then:

```
terminal(command="python \"${HERMES_SKILL_DIR}\apply_capture.py\" --input-file <scratch path>")
```

```json
{
  "schema_version": 1,
  "said_at": "2026-09-12",
  "company": "TAQA Distribution",
  "people": ["irfan.siddiqui@taqadistribution.com"],
  "history_line": "Met Irfan Siddiqui (CEO); positive; agreed Q1 phasing of managed services",
  "important_info": [{"text": "RFP expected next week"}],
  "actions": [{"text": "Send revised pricing", "owner": "Sherif", "due": "Friday"}]
}
```

#### said_at

The day it HAPPENED, not the day it was told to you. "Yesterday" said on the
12th is `2026-09-11`. Leave it out only when the CBO gives no time at all.

#### company

One company, exactly as `resolve_capture.py` returned its `name`. Use the
resolved spelling, not what was said.

#### people

Who was actually there, by email when you have it from the resolver, otherwise
by the name that resolved. They are wiki-linked into the History line. A person
with no note is reported back and skipped -- never invented.

#### history_line

One line: what happened with them. This is the line someone reading the
company's History next year wants to see -- "Met the CEO; positive; agreed Q1
phasing", not "had a meeting". No date in the text; the applier dates it.

#### important_info

Facts that outlive this conversation -- a budget, a reorganisation, a new
decision-maker, a deadline they stated. Not the pleasantries, and not the same
sentence as the history line. Leave the list empty when there is nothing
durable; an empty list is a real answer.

#### actions

Real commitments, with an owner and a due date when they were stated. Never
invent a deadline.

## What this Skill will not do

- **It never creates a company or a person.** Both are the operator's own
  curation, and a capture filed against a company that does not exist is worse
  than no capture.
- **It never writes into `## Notes` or `## Personal Notes`.** Those are the
  operator's own handwriting. Automated lines go to History, to `## Captured`
  and to `## Actions`, each stamped `-- CBO capture` so a stated fact is never
  confused with one derived from email.
- **It does not file meeting notes.** There is no meeting-notes system yet; a
  capture stands on its own against the company and its date.

Applying the same capture twice writes nothing the second time, so a repeat or
a retry is safe.
