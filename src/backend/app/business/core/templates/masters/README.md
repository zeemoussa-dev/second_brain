# Master Templates — the shipped Entity Template set

An **Entity Template** (a "Master Template") defines one **vault structure**: what
a note of that type looks like, which sections it has, and what kind of actor may
write each one. It is a *data contract*, nothing else.

These 11 ship with the product and are installed into
`<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/Template.json` on a fresh install.
Before 2026-09-06 nothing shipped: all 11 existed only in one operator's config
folder, the setup wizard seeded none, and a fresh install therefore had **no
templates at all** — so every capture Skill would have failed on a missing
structure. The framework shipped the engine and none of the contracts.

## The rules

- **Framework artifact.** Would it still be true on a fresh install with a
  different vault? Yes → it belongs here. No → it is instance data and belongs in
  the install's own folder, never in this directory.
- **No instance detail, ever.** No real paths, vault names, mailboxes or operator
  names. These files were verified clean when they were brought in; keep them so.
- **Structure only — a Master Template never names a Skill.** The dependency runs
  one way: a Skill needs a Template; a Template knows nothing about Skills. An
  Entity Template is a vault structure at the end of the day.

## `allowed_callers` is gone (2026-09-06)

Sections no longer name Skill Actions. That was a **reverse edge** — it made a
vault structure definition depend on the capability layer, contradicting the
dependency resolver's own "a Template has no further real dependencies of its
own", and it meant a Master Template could not be shipped or versioned without
knowing which Skills exist.

The control itself was not dropped. It moved to the side that owns the Actions:
a Skill declares `writes:` in its `SKILL.md` frontmatter, and the backend derives
`<data>/data/section_access.json` from what is actually **deployed**. The shared
`vault_manager` reads that map at write time, so ADR-017's per-caller enforcement
is intact. The migration was verified lossless — the derived map reproduces
exactly what these templates used to declare.

Derived beats authored here: the map cannot name an Action that is not deployed,
and cannot rot against a renamed script the way the hand-maintained list silently
did. `SkillManager.validate_declared_writes` now refuses to deploy a Skill whose
declaration does not resolve against a real, `machine_write` section.

What `allowed_callers` protected is worth being precise about: across all 11
templates it appeared only on `machine_write` sections, never on `human_only`.
What keeps agents out of your Personal Notes is `access`, which names nobody and
stays.

## Known blocker

`TemplateManager._to_template` reads the **v1 flat** field names (`note_name`,
`sections`, `note_own_folder`) while all 11 files here are **v2** (`root.sections`,
`root.own_folder`, `identity` as an object). Every `.get()` falls back to its
default, so all 11 parse to **zero sections with `error=None`** — a silent
mis-read, not a failure.

Until that is fixed the backend cannot validate a template's contents, which means
the "a Skill refuses to deploy unless its Template has the sections it writes"
check cannot be built. Fix the reader — and add an explicit `schema_version` to
these files in that same change, so a template says which engine it targets rather
than being guessed at.
