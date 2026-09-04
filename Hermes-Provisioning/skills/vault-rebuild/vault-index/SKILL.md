---
name: vault-index
description: Rebuilds the agent-facing structural index of the vault (paths, id, tags, frontmatter per note) -- recurring, mechanical, no judgment.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, vault, index, recurring, infrastructure]
---

# Vault Index

Walks `Work/` once and writes a fast, agent-readable structural index --
one JSON file per real top-level folder plus a whole-vault file -- so
other Skills' own lookups (`find_by_id`/`find_by_filename`/
`find_in_folder` in `vault_manager.py`) stop re-walking the entire vault
and re-parsing every note's frontmatter on every single call. See
`Implementation/Plans/2026-08-27-vault-index-and-section-agents.md` for
the full design and the real, confirmed slowdown this fixes
(`ingest_meeting.py`, 2026-08-26: an unscoped `find_by_id` "fell back to
scanning the ENTIRE Work/ tree").

Purely mechanical -- no summarization, no judgment about what's
important, no filtering beyond what Settings > Vault > Index Filtering
already configured on disk. Never rewrites, deletes, or touches a single
vault note itself; only writes JSON files under the App Database
Folder's own `index/` subfolder.

**No MCP server, no Second Brain backend process required to run this
Skill** -- `build_vault_index.py` is standalone (stdlib only), same
"keeps working even if the backend is down" model as `vault_manager.py`
(which it imports as a sibling module in this Skill's own `scripts/`
folder).

## Prerequisites

- Vault path (pass as `--vault-path` below):
  `$SECOND_BRAIN_VAULT_PATH`
- App Database Folder (pass as `--data-path` below) -- Second Brain's
  own data root, independently configurable from Settings > System since
  2026-08-27, defaults to `<vault>/.second-brain`:
  ``$SECOND_BRAIN_DATA_PATH``. **If the operator
  ever relocates the App Database Folder from that Settings page, this
  literal value in this file must be updated to match** -- this Skill has
  no way to read that backend setting itself.

## How to run

Call `build_vault_index.py` directly through the `terminal` tool -- a
PLAIN command starting with `python` itself, never wrapped in `bash -c`/
`-lc`. Hermes' own `terminal` tool categorically requires human approval
for any `-c`/`-lc` shell-string invocation, which would stall a
cron-triggered run with no one there to approve it (confirmed live,
`email-thread-capture`'s own SKILL.md, 2026-08-21):

```
terminal(command="python build_vault_index.py --data-path \"$SECOND_BRAIN_VAULT_PATH\\.second-brain\"")
```

Run from this Skill's own `scripts/` folder (so the sibling
`vault_manager.py` import resolves). Prints one JSON line:
`{"generated_at", "folders": {name: count, ...}, "total_notes"}` on
success. Report the `total_notes` figure back; no further action needed
-- this Skill never sends a WhatsApp message or asks the operator
anything, it's pure infrastructure maintenance (`--deliver local`).

## Recurring schedule

Registered as a Hermes cron job (`vault-index-rebuild`, `every 30m`,
`--deliver local`) on this profile. Also triggerable on demand outside
its schedule via `hermes cron run vault-index-rebuild` -- the same
mechanism Second Brain's own Settings > Vault > Overview "Rebuild index"
button uses, so there is exactly one real rebuild path, never two that
could drift.
