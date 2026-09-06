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

## `allowed_callers` is on its way out

Some sections still carry `allowed_callers`, naming specific Skill Actions (e.g.
`apply_thread_review`). That is a **reverse edge** — it makes the structure depend
on the capability layer, and the dependency resolver already contradicts it
("A Template has no further real dependencies of its own").

It stays for now only because the live engine enforces it, and removing it before
the Skill side can declare `writes: [thread.Summary, …]` would silently *loosen*
access control. Remove it in the same change that lands the Skill-side
declaration, not before.

Note what `allowed_callers` is and is not protecting: across all 11 templates it
appears only on `machine_write` sections, never on `human_only`. What keeps agents
out of your Personal Notes is `access`, which names nobody and stays.

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
