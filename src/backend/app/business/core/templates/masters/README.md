# Master Templates — the shipped Entity Template set

An **Entity Template** (a "Master Template") defines one **vault structure**: what
a note of that type looks like, which sections it has, and what kind of actor may
write each one. It is a *data contract*, nothing else.

These 16 ship with the product and are installed into
`<SECOND_BRAIN_DATA_PATH>/data/Templates/<id>/Template.json` on a fresh install.
Before 2026-09-06 nothing shipped: all 11 existed only in one operator's config
folder, the setup wizard seeded none, and a fresh install therefore had **no
templates at all** — so every capture Skill would have failed on a missing
structure. The framework shipped the engine and none of the contracts.

## Every note carries a kind (2026-09-11)

The operator's rule: **no note without tags, no note without a `kind/*`; `type` is
optional.** So `kind` is the universal classifier and cannot be derived from
`type` — each Template declares its own kind in `frontmatter_defaults.tags`, and
so does each child.

`industry`, `technology`, `industry-doc`, `ot-doc` and `sales-doc` were added
because five real note types had no Template at all, which is why 1,362 notes in
one real vault had no kind to inherit. The three doc types share `kind/kb-doc`
with `azure-kb-doc`/`compass-kb-doc` — `kind` is the artefact's form, `type`
its domain.

`thread` declares a **`files` child** so an email attachment gets
`kind/attachment` rather than the `file` Template's `kind/file`: an attachment
and a file the operator uploaded are different things, and both carry
`type: File`, so position in the Template — not type — is what separates them.
Note the mismatch to fix on the capture side: this dynamic child produces
`files/<title>.md`, while capture writes `files/<slug>/<slug>.md` directly
without going through the engine. Today the declaration governs
*classification*, not creation.

## Upgrading an install (they never overwrite)

`seed_shipped_masters()` installs only ids an install lacks, so **a fix to a
master never reaches an install that already has that id.** That is not a bug —
overwriting on every boot would silently revert an operator's edit — but it does
mean a stale copy can persist indefinitely. One real install still had the
pre-`kind` `thread` Template weeks later, so every Thread it captured was born
without `kind/thread` and no backfill could ever stay ahead of it.

Before diagnosing a missing field, diff the install's copy against its master.
Upgrade only where the install is a strict *subset* of the master (nothing of the
operator's to lose); anything else needs reading first. Renames are the dangerous
case: `customer`, `partner` and `opportunity` moved `Log & Captures` to
`History & Captures`, so upgrading those Templates without migrating the existing
`<Name>-log.md` notes in the same change leaves hubs half-renamed.

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

## The v1/v2 reader trap (fixed 2026-09-06, worth keeping in mind)

`TemplateManager._to_template` once read the **v1 flat** field names
(`note_name`, `sections`, `note_own_folder`) while every file here is **v2**
(`root.sections`, `root.own_folder`, `identity` as an object). Reading v1 names
out of a v2 file never raises — every `.get()` returns its default — so all 11
parsed to **zero sections with `error=None`**: a silent mis-read, not a failure.

The reader now honours both schemas and every file here declares
`schema_version: 2`. The lesson survives the fix: **if a Template's sections come
back empty, suspect a schema mismatch before anything else.**
