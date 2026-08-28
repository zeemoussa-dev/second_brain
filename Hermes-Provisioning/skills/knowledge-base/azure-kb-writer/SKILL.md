---
name: azure-kb-writer
description: The one real, mechanical write path into the Azure Technology KB (Work/Technology/Azure/). Use this whenever you've researched or been handed real content worth keeping -- a service summary, a reference architecture, a Landing Zone pattern, or general Azure knowledge.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, azure, knowledge-base, vault-write]
---

# Azure KB Writer

Your own real write access to `Work/Technology/Azure/` -- the ONLY way
content lands there. You are the SOLE real owner of Azure KB writes,
same policy as Compass Expert's own `compass-kb-writer` -- none of your
own specialists (`azure-services-expert`, `azure-enterprise-architect`,
`azure-data-architect`, `azure-infra-architect`) write to the vault
themselves; they report real findings back to you, and you do the write.

## Prerequisites

- Vault path (pass as `--vault-path` on every script call):
  `C:\myWorx\Moussa MD\Moussa Brain`

## What this builds

```
Work/Technology/Azure/
  Azure.md                          <- the real hub note, NOT written by this script (see below)
  Services/<Category>/<slug>.md     <- e.g. Services/Compute/Virtual Machines.md
  Architecture/Enterprise/<slug>.md <- Landing Zone / Enterprise-Scale patterns
  Architecture/Data/<slug>.md       <- data platform reference architectures
  Architecture/Infra/<slug>.md      <- infra/compute/network reference architectures
```

Every doc note gets the same real shape: frontmatter (`type: "AzureDoc"`,
`area`, `tags`, `source_url`, `last_refreshed`, plus `category` for a
Services note), a `**Technology:** [[Azure]]` wikilink back to the hub,
then `## Summary` / `## Details`, then any real images you attached.

## Job: Write or update one doc

1. Do the real work first -- research the topic (`web_search`/
   `web_extract`), read a document Mahmoud handed you, or receive a
   specialist's own reported finding. Never write something nobody
   actually verified.
2. Decide the real `area`: `"services"`, `"architecture-enterprise"`,
   `"architecture-data"`, or `"architecture-infra"`.
3. For `"services"` ONLY: also decide the real `category` (e.g.
   "Compute", "Storage", "Networking", "Databases", "AI + ML",
   "Security", "Identity", "Integration", "DevOps", "Management &
   Governance") -- match an existing category folder under `Services/`
   if one already fits; only introduce a new category name when nothing
   real already covers it.
4. If there's a real diagram/screenshot worth keeping (not just
   describing), save it locally first, then pass its real local path.
5. `write_file` a scratch JSON payload:
   ```json
   {
     "area": "services",
     "category": "Compute",
     "title": "Virtual Machines",
     "summary": "One or two real sentences -- what it is, what it's for.",
     "details": "A SHORT local summary, not a full distillation -- link out for depth (see below).",
     "source_url": "https://learn.microsoft.com/... (the real Microsoft Learn page)",
     "images": [{"local_path": "C:\\...\\real-file.png", "caption": "What it shows"}]
   }
   ```
6. Call the script as a PLAIN, direct `terminal` call using its own full
   absolute path:
   ```
   terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\profiles\\azure-expert\\skills\\knowledge-base\\azure-kb-writer\\scripts\\write_azure_doc.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --input-file <scratch path>")
   ```

Calling it again with the same `title`/`area` (and same `category` for
Services) overwrites that SAME note in place (`updated: true`) -- this is
the real refresh mechanism, not a second copy. A genuinely different
topic gets its own new title/file.

## Services notes stay SHORT -- link out, don't distill

**Operator's own explicit framing: "Services will have Azure Services
with a quick short Description in our vault but a link to the actual
documentation of Azure so if the info I am asking for is not enough from
MD we look online."** A Services note is a pointer with just enough
local context to be useful at a glance -- what the service is, what
category it's in, a couple of real facts if they matter -- NOT a full
distillation of Microsoft's own docs. `source_url` must be the real,
correct Microsoft Learn page every time; `azure-services-expert` has its
own live `web_search`/`web_extract` access for anything the local note
doesn't cover, the same live-lookup fallback `compass-models-expert` has
for Compass models.

## Architecture notes ARE substantive

Unlike Services, a reference-architecture note is the real content
itself (the pattern, its components, when to use it, real tradeoffs) --
Microsoft's own Architecture Center pages are the source, but the note
should stand on its own, not just link out. Cite the real source page in
`source_url` regardless.

## The hub note (`Azure.md`) is a one-off, not scripted

Unlike every other note above, `Azure.md` carries real substantive
content directly in three named sections ("What is Azure", "What is
Sovereignty in Azure", "How to start an Enterprise company in Azure") --
this is a deliberate difference from Compass's own hub note (which stays
structure-only). Edit it directly with `read_file`/`write_file` when you
have real, verified content for one of those sections (never invent
one) -- this script does not manage it, matching `compass-kb-writer`'s
own "don't touch the hub note" precedent, just with real content instead
of none expected here.

## Pitfalls

- **Never wrap the script in `bash -lc "..."`** -- same categorical
  Hermes `terminal`-tool approval-block documented throughout this
  vault's Skills; a bare `python ...` command with the script's own
  full absolute path runs without a prompt.
- **Never fabricate a `source_url` or a fact you didn't actually find.**
  A hand-added doc from Mahmoud genuinely has no real URL -- omit
  `source_url` rather than inventing one. Same for content: if research
  came up empty on a topic, say so instead of writing something
  plausible-sounding.
- **`category` is required for `"services"` and ignored for every other
  area** -- passing it for an architecture area is harmless (the script
  ignores it) but don't invent one where it doesn't apply.

## Verification

- After a write, confirm the returned `path` is real and under the
  correct area/category folder, and (for an update) that `updated: true`
  matches what you intended -- a `false` when you meant to refresh an
  existing doc means the title (or category, for Services) didn't match
  and you just created a duplicate.
