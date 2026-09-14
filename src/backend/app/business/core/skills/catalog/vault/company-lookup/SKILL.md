---
name: company-lookup
description: Answer questions about the customer and partner portfolio from the vault itself -- how many there are, which company a name means, and where a relationship stands. Read-only; writes nothing.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, customers, partners, lookup, read-only]
---

# Look up a company

Use these whenever the CBO asks something the vault already knows:

> "How many partners do we have?"
> "Do we work with Mubadala?"
> "Where are we with TAQA?"

**Never answer any of these from your own reading.** You may have opened a
dozen company notes in this conversation; there are three hundred. A number
you arrive at by counting what you happened to see is wrong, and it is wrong
in a way that sounds completely confident. Run the script.

## How many — `company_counts.py`

```
terminal(command="python \"${HERMES_SKILL_DIR}\company_counts.py\"")
```

`--kind customer` or `--kind partner` to narrow, `--sectors` for the sector
breakdown, `--list` for the names themselves (long -- only when the question
actually needs them).

Three numbers come back per kind, and the difference between them is usually
the real answer:

- **`companies`** -- we have classified them. `affiliates` is counted
  separately, because an affiliate is not its own relationship.
- **`engaged`** -- their History has at least one dated event. This is how
  many we have actually *dealt with*.
- **`enriched`** -- the profile has been filled in.

So "224 partners" and "61 we have ever engaged" are both true. Give the one
that answers what was asked, and say which it is.

## Which company — `find_company.py`

```
terminal(command="python \"${HERMES_SKILL_DIR}\find_company.py\" --query \"<as said>\"")
```

Every company the name could mean, each saying how it matched (`name`,
`name form`, `part of the name`, `domain`, `sector`). Also finds a company
by a fragment ("distribution"), a domain ("adnoc.ae") or a sector ("energy"),
so "who do we have in healthcare" is one call.

When more than one comes back, **name them all**. A parent and its affiliate
are different companies -- "Mubadala" is not "Mubadala Health" -- and picking
one is how the wrong company ends up in an answer.

## Where do we stand — `company_brief.py`

```
terminal(command="python \"${HERMES_SKILL_DIR}\company_brief.py\" --company \"<resolved name>\"")
```

One company, gathered from the notes that own each part: recent History
events, durable facts from `## Captured`, the open (unticked) commitments in
`## Actions`, the people we know, the profile, and the affiliates. `--history`
and `--captures` set how far back to go; totals always come back, so you can
say "10 of 47 events".

A name that matches two companies gets **no brief** -- the answer comes back
with `status: "ambiguous"` and the candidates. Ask which; a brief about the
wrong company reads exactly like a brief about the right one.

## What these will not do

- **They never write.** Filing something the CBO said is `capture-engagement`.
- **They never report `## Notes` or `## Personal Notes`.** Those are the
  operator's own handwriting. A brief reports what the system captured, not
  what he wrote to himself.
- **They never invent a company.** A company with no hub is simply not
  tracked; say so. Creating one is the operator's own call.
