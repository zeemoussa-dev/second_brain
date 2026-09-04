---
name: research-kb-writer
description: The one real, mechanical write path into the Research knowledge area (Work/Research/). Use this whenever you've researched a topic and reached a real, conclusive finding worth keeping -- never for a request that found nothing conclusive.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, research, librarian, knowledge-base, vault-write]
---

# Research KB Writer

Your own real write access to `Work/Research/` -- the ONLY way content
lands there. You are the SOLE owner of this write path, same policy as
Azure Expert's own `azure-kb-writer`.

## Prerequisites

- Vault path (pass as `--vault-path` on every script call):
  `$SECOND_BRAIN_VAULT_PATH`

## What this builds

```
Work/Research/
  <topic>/
    <date>-<topic>.md          <- first research pass on this topic
    <date>-<topic> HH-MM.md    <- a later pass on the SAME topic, same day
```

One folder per real topic -- repeat research on the exact same `topic`
string lands in the SAME folder as a new file (never overwriting an
earlier pass), so multiple passes on one subject stay together instead of
scattering across `Work/Research/` as loose flat files. **Use the exact
same `topic` string across calls when you're continuing research on
something you already wrote a note about** -- a differently-worded topic
gets its own, separate folder.

Every note gets the same real shape: frontmatter (`type: "ResearchDoc"`,
`topic`, `tags: ["research"]`, `keywords` -- a real list, only when you
give some, never fabricated -- `source_url` -- omitted, never fabricated,
when no real source exists -- `created`), then `## Summary` / `## Details`.

## When to use this

**Use it whenever a real research request produced a real, conclusive
finding.** Do the actual lookup first -- Hermes' own bundled `web_search`/
`terminal` tools are your real research mechanism, the same ones
`azure-expert`/`compass-expert` already use. Never write something you
didn't actually verify -- no plausible-sounding guesses standing in for a
real finding.

**If your research genuinely finds nothing conclusive, report that
honestly to whoever asked and do NOT call this script.** No note gets
written for that request -- never fabricate content to fill the gap. This
is the one hard rule this Skill exists to protect: a missing note is
always the correct outcome of an inconclusive lookup, never a reason to
write something anyway.

## Job: Write one finding

1. Do the real work first -- research the topic (`web_search`, and
   `terminal` for anything a search alone can't answer). Stop and report
   honestly if nothing conclusive turns up (see above) -- do not proceed
   to step 2 in that case.
2. `write_file` a scratch JSON payload:
   ```json
   {
     "topic": "The real topic you researched",
     "summary": "One or two real sentences -- the actual conclusive finding.",
     "details": "The real supporting detail -- what you found, and why it answers the request.",
     "source_url": "https://... (the real source, if one exists -- omit entirely if not)",
     "keywords": ["2-5 real, specific terms someone would filter/search by -- omit entirely if none genuinely apply"]
   }
   ```
   **Always include a few real `keywords`** when you can -- specific
   terms (technology names, product names, domains), not generic filler
   like "research" or "information". This is what makes the folder
   actually browsable/filterable as it grows, not decoration.
3. Call the script as a PLAIN, direct `terminal` call using its own full
   absolute path:
   ```
   terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\profiles\\research-agent\\skills\\librarian\\research-kb-writer\\scripts\\write_research_doc.py\" --input-file <scratch path>")
   ```

## This script NEVER overwrites an existing note

**Unlike `azure-kb-writer`'s own update-in-place refresh behavior, calling
this script again with the same `topic` does NOT update the earlier note
-- it always creates a SECOND, distinctly-named file** (a time, then a
numeric, suffix disambiguates the filename; the original note's own
content is left completely untouched). This is a deliberate design choice
(`ADR-008`), not a bug: this Skill builds no merge/dedup logic against a
prior research note on the same or a similar topic -- repeated similar
requests may legitimately produce more than one note in `Work/Research/`.

## No approval needed

The write proceeds immediately once you have a real, conclusive finding
-- no confirmation step, no pending-approval call. This is safe because
the write is structurally confined to `Work/Research/` (the script has no
destination-path argument beyond `--vault-path`) and can never touch,
edit, or overwrite anything else in the vault.

## Pitfalls

- **Never wrap the script in `bash -lc "..."`** -- same categorical
  Hermes `terminal`-tool approval-block documented throughout this
  vault's Skills; a bare `python ...` command with the script's own full
  absolute path runs without a prompt.
- **Never fabricate a `source_url` or a fact you didn't actually find.**
  Omit `source_url` entirely rather than inventing one.
- **Never call this script for an inconclusive result.** Report honestly
  instead -- see "When to use this" above.

## Verification

- After a write, confirm the returned `path` is real and under
  `Work/Research/` -- there is no `updated` field in the response (unlike
  `azure-kb-writer`) since this script never updates in place; every
  successful call is a brand-new file.
