---
name: compass-kb-writer
description: The one real, mechanical write path into the Compass Technology KB (Work/Technology/Compass/). Use this whenever you've researched or been handed real content worth keeping -- a pricing detail, a solution pattern, general selling/usage knowledge, or an update to the external-models list.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, compass, knowledge-base, vault-write]
---

# Compass KB Writer

Your own real write access to `Work/Technology/Compass/` -- the ONLY way
content lands there. Serves two real triggers the same way: your own
cron-scheduled refresh (research via `web_search`/`web_extract`), and
Mahmoud handing you a document or tidbit to add later. Either way, you
do the real judgment (what's true, what's worth keeping, how to phrase
it); this script's own job is purely mechanical placement.

## Prerequisites

- Vault path (pass as `--vault-path` on every script call):
  `C:\myWorx\Moussa MD\Moussa Brain`

## What this builds

```
Work/Technology/Compass/
  Compass.md              <- the real hub note, not written by this script
  Pricing/<topic>.md
  General/<topic>.md
  Solutions/<topic>.md
  Models/Compass Exposed Models.md   <- ONE list note, see below
```

Every doc note gets the same real shape: frontmatter (`type:
"CompassDoc"`, `area`, `tags: ["technology/compass", "compass/<area>"]`,
`source_url`, `last_refreshed`), a `**Technology:** [[Compass]]`
wikilink back to the hub, then `## Summary` / `## Details`, then any
real images you attached.

## Job: Write or update one doc

1. Do the real work first -- research the topic (`web_search`/
   `web_extract`) or read a document Mahmoud handed you. Never write
   something you didn't actually verify.
2. Decide the real `area`: `"pricing"`, `"general"`, `"solutions"`, or
   `"models"` (see the Models note below -- it's a different shape).
3. If there's a real diagram/screenshot worth keeping (not just
   describing), save it locally first, then pass its real local path.
4. `write_file` a scratch JSON payload:
   ```json
   {
     "area": "pricing",
     "title": "GPU Pricing Tiers",
     "summary": "One or two real sentences of what this doc covers.",
     "details": "The real content -- as much structure/detail as the topic actually needs.",
     "source_url": "https://... or omit/null if hand-added with no real URL",
     "images": [{"local_path": "C:\\...\\real-file.png", "caption": "What it shows"}]
   }
   ```
5. Call the script as a PLAIN, direct `terminal` call using its own full
   absolute path:
   ```
   terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\profiles\\compass-expert\\skills\\knowledge-base\\compass-kb-writer\\scripts\\write_compass_doc.py\" --vault-path \"C:\\myWorx\\Moussa MD\\Moussa Brain\" --input-file <scratch path>")
   ```

Calling it again with the same `title`/`area` overwrites that SAME note
in place (`updated: true` in the response) -- this is the real refresh
mechanism, not a second copy. A genuinely different topic gets its own
new title/file.

## Models is a different shape -- read first, don't just append

**Operator's own explicit framing: "Models should be just a list for
now... it's not Compass Technology, it's External Models Compass
Exposes... we might need to have a section for each Model Later."**
There is exactly ONE real note here, `Models/Compass Exposed Models.md`
-- not one file per model. To add or update a model's own entry:

1. `read_file` the existing note first (if it exists yet).
2. Add or update that ONE model's own `### <Model Name>` subsection in
   the full body -- brief: what it is, what it's good for, nothing more
   unless asked. Leave every other model's own section untouched.
3. Call this script with `area: "models"`, `title: "Compass Exposed
   Models"` (always this exact title), and the FULL regenerated body
   (every model's section, not just the one you changed) as `details`.

This keeps each model's own entry easy to promote into its own real
note later (its own `### ` heading is already a clean cut point) without
needing to restructure anything now.

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
- **Don't touch `Compass.md` (the hub note) with this script** -- it's
  a stable, rarely-changing overview, not a refresh target. If it
  genuinely needs an update, edit it as a one-off, separate ask.

## Verification

- After a write, confirm the returned `path` is real and under the
  correct area folder, and (for an update) that `updated: true` matches
  what you intended -- a `false` when you meant to refresh an existing
  doc means the title didn't match and you just created a duplicate.
