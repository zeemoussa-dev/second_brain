---
name: entity-domain-extraction
description: One-time, mechanical scan of every Thread's real participants, grouped by email domain into a review file.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, company, partner, entities, one-time]
---

# Entity Domain Extraction (Step 1 of the company/partner sequence)

**Step 1 of 4** in the company/partner discovery sequence (2026-08-21):

1. **This Skill** -- cheap, mechanical, no LLM: group every Thread's
   real participants by email domain, write one flat file
   (`.second-brain/Settings/Entities.md`) for the operator to review by hand.
2. *(Manual, not this Skill)* Operator edits `Entities.md` directly --
   merges any duplicate entries, sets `Ignore: Yes` on noise, moves real
   partners into its `## Partners` section, flips `Created` once a hub
   note exists for an entry.
3. *(Separate, later, one-time pipeline -- not built yet)* Reads the
   curated `Entities.md`, creates the real Customer/Partner OKF hub
   notes from it.
4. *(Separate, later, one-time pipeline -- not built yet)* Summarizes
   every Thread (real LLM/agent work) -- with the curated company list
   already in hand, wiki-tags recognized company names directly into
   each summary instead of needing to discover them from scratch.

This Skill is ONLY step 1. It never calls an LLM, never writes to a
Thread, never creates a Customer/Partner note -- pure read of
already-captured vault data (from the `email-thread-capture` Skill),
grouped by domain. Domain-based grouping is deliberate: it's what keeps
two spellings of the same real company (e.g. "DGE" vs "Digital
Government Entity", both `@dge.gov.ae`) from ever becoming two separate
entries in the first place -- they share one domain, so they're the same
group by construction.

## Prerequisites

- Run `email-thread-capture` first -- this Skill reads `Work/Threads/`,
  which doesn't exist until that Skill has captured real email history.
- No `pywin32`, no Outlook, no network calls at all -- this only reads
  local vault files already on disk.
- Vault path: the scripts read `SECOND_BRAIN_VAULT_PATH` from Hermes' own
  `.env` themselves; `--vault-path` only overrides it.

## How to Run

One script, one call -- no loop, no paging, nothing to background:

```
terminal(command="python build_entities_report.py", cwd="<this Skill's scripts/ folder>")
```

Prints `{"report_path", "companies_found", "threads_scanned"}`. Report a
one-line summary of those three numbers when done.

## Output shape

`.second-brain/Settings/Entities.md` -- one `### <Company Name>` section per domain found,
each with a tab-indented field block (renders as an indented code block
in Obsidian, visually subordinate to the heading):

```
### Simplai

	Company Name: Simplai

	Aliases: 

	Affiliate of: 

	Created: No

	Ignore: No

	Domain: simplai.ai

```

`Aliases`/`Affiliate of`/`Created`/`Ignore` are the fields the later,
separate Step 3 pipeline will read -- this Skill always writes them
blank/`No`, since deciding them is the operator's own manual review, not
this Skill's job.

## Pitfalls

- **Re-running overwrites the file completely** -- this Skill does not
  merge with an already-curated `Entities.md`. Running it a second time
  after the operator has started editing would silently discard their
  edits. Don't re-run without checking with the operator first once the
  file has real edits in it.
- Personal email domains (gmail.com, outlook.com, etc.) and the
  operator's own organization (`core42.ai`, including subdomains) are
  excluded by a hardcoded denylist in the script -- extend it there if a
  real captured domain that should be excluded slips through (the
  operator can also just set `Ignore: Yes` on it in the output file
  instead of touching the script).
- Automated/notification senders on real third-party domains (e.g. a
  vendor's own ticketing or calendar-notification address) are NOT
  filtered -- they'll show up as entries. That's expected, not a bug:
  filtering "is this actually a business relationship" is exactly the
  judgment call left to the operator's own manual review.

## Verification

- Report the three summary numbers (`report_path`, `companies_found`,
  `threads_scanned`).
- Spot-check that `.second-brain/Settings/Entities.md` exists and its `## Companies`
  section has real entries (a zero-companies result on a vault that has
  real Threads is worth flagging, not silently accepting).
