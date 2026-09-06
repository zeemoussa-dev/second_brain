# Blueprints — a Section you can pull onto a fresh install

A **Blueprint** is a *recipe* for a Section: its identity, the Agents in it, and
which Skills each Agent should have. Pull one on a new install and that Section
comes up running.

## Recipe, not snapshot

The snapshot path already exists: `.sbf` export/import carries an Agent as
`profile.tar.gz` — opaque bytes from one machine's `hermes profile export`.
That is right for *moving an install* and wrong for a *library*. It bakes in one
machine's model, keys and session history, cannot be reviewed or diffed, and
cannot be updated without re-exporting from a live machine.

A Blueprint carries a declaration instead: `model`, `reasoning_effort`, `soul`,
`type`, `icon`, `skill_ids`, `clone_from`. It builds cleanly anywhere via
`AgentManager.create()`, which already does `hermes profile create --clone` plus
the Registry side, and — since 2026-09-06 — deploys an Agent's declared Skills.

|  | `.sbf` export | Blueprint |
|---|---|---|
| Carries | a machine's actual profile | a recipe |
| Built from | one live install | authored, reviewed, versioned in the repo |
| Reviewable / diffable | no (tarball) | yes (JSON + Markdown) |
| Good for | moving or backing up an install | standing up a new one |

## What it does NOT contain

Everything it *references* already ships, so a Blueprint names it and stops:

- **Skills** — ship in `../skills/catalog/<tool>/<slug>/`
- **Master Templates** — ship in `../templates/masters/`, seeded on boot
- **The shared engine** — one `vault_manager.py`, on `PYTHONPATH`

**Required Templates are derived, never authored.** A Blueprint lists Skills; the
Templates follow from what those Skills declare in their own `writes:`
frontmatter. Authoring the list separately would create a second copy of a fact
that can drift — the same reason `section_access.json` is derived rather than
written by hand, and the same reason `allowed_callers` was removed from
`Template.json`.

For `librarian` that closure resolves to `file`, `note`, `thread` and
`research-kb-doc` — all four already shipped.

## Installing one

Preconditions first, then create — never half-provision:

1. Resolve the Skill set across every Agent in the Blueprint.
2. Derive the required Templates from those Skills' `writes:` declarations.
3. **Refuse** unless every Template exists at a compatible `version` and every
   declared section is `machine_write` — `SkillManager.validate_declared_writes`
   already answers this.
4. Create the Section, then each Agent (`AgentManager.create(..., skill_ids=…)`),
   which clones the profile, writes the Registry side, and deploys its Skills.

Refusing up front is the point. The alternative is an Agent that installs
cleanly and then fails inside a cron worker at 03:00, which is the failure shape
this codebase keeps producing.

## Versions

`schema_version` is the Blueprint format itself. `version` is this Blueprint's
own content — bump it when the Section's shape changes. Same split as a Master
Template, for the same reason: one says how to read the file, the other says what
it promises.

## Status

**Draft, 2026-09-06.** `librarian/` is drafted from the real live Section
(files-manager, notes-manager, research-agent) and parses, but nothing installs
it yet. The surface is intended to be a card under **Settings** for now.
