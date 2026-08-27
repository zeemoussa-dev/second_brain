# Vault Writer standardization — design (not yet built)

**Date:** 2026-08-25
**Status:** Design converged through a live collaborative session, then
built and verified (operator: "Start Building"). Not yet a REQ/ADR; this
document is the real starting point for both.

**Built (2026-08-25):** `Hermes-Provisioning/shared/vault_manager.py` — the
real, template-driven engine (`find`/`create`/`update`/`get_section`/
`modify_section`), standalone/stdlib-only. Verified live via its own CLI
against a scratch vault (not the real one) covering every scenario named
below: hierarchical `note_name` placement, `update_section` overwrite-on-
same-title (no duplicate, same `id`), `always_new` never-overwrite
(disambiguated filenames), `modify_section`'s combined create-or-append,
`on_missing="error"` refusing to auto-create (person-lookup's own real
guard), the `user_edit` section guard refusing a machine write, and
`update()` renaming a title while `find(by="id")` keeps resolving the same
file. 13 pytest cases lock the same scenarios in as regression coverage
(`Hermes-Provisioning/shared/tests/test_vault_manager.py`). **Not yet
copied into any real Skill** — see "Execution location" below; that step,
and Template.json authoring for the remaining real write patterns, are the
concrete next steps, not done here.

## Motivation

Every vault-writing Hermes Skill (azure-kb-writer, compass-kb-writer,
research-kb-writer, capture-notes, capture-files, track-opportunities,
summarize-and-tag-files/threads, macc-forecast-generator, plus the
Meeting/Thread capture pipeline) carries its own hand-written Python script.
Reading them directly (this session, 2026-08-25) found the SAME low-level
primitives — `_slugify`, frontmatter format/parse, `insert_body_section_if_missing`
/ `replace_body_section` / `read_body_section`, `merge_tags`,
`upsert_frontmatter_key`, collision-avoiding unique-path helpers — copy-pasted
near byte-for-byte across at least `create_opportunity.py`,
`apply_thread_review.py`, `capture_file.py`, and `vault_lib.py`
(meeting-capture). `vault_lib.py`'s own docstring confirms this is
acknowledged, deliberate duplication: "Trimmed/adapted port of Second Brain's
own `app/data_access/vault_writer.py`'s Meeting-note primitives... duplicated
per this codebase's established per-Skill self-containment convention."

So the shared engine already exists (`app/data_access/vault_writer.py`,
2,600+ lines) — Skills just don't call it, because Hermes Skills need to keep
working even if Second Brain's backend is down. That tension is the real
fork this design has to resolve, not a detail to gloss over.

## The real write-pattern taxonomy (read from the actual scripts, not guessed)

| Pattern | Real example(s) | Shape |
|---|---|---|
| KB append-or-overwrite | azure-kb-writer, compass-kb-writer | area→subpath map, slug filename, silently overwrites same title, frontmatter+`##Summary`/`##Details`, optional images |
| KB append-never-overwrite | research-kb-writer | same body shape, but ADR-008 deliberately forces a brand-new file on every call — never touches an existing note |
| Append into an existing note only | person-lookup | must already exist (errors if not, REQ-SB-10's own guard against a lookup skill fabricating a Person note), frontmatter untouched, body appended |
| New dated artifact, flat file | capture-notes | `Work/Notes/<date>/<slug>.md`, collision→disambiguate, auto-wikilinks known Customer/Partner names |
| New dated artifact, folder-per-thing | capture-files | `Work/Files/<date>/<stem>/{file, stem.md}`, real file move, plus a second "append details" mode |
| Create child under a resolved parent, link back | create_opportunity (Opportunities under Customer hubs) | resolve parent by name/alias (fail if none), fixed rich section skeleton, accumulate a wikilink into the parent's own named section |
| Bulk review pass | apply_thread_review / apply_file_review | batch job: resolve companies, merge tags across many files, upsert two "already processed" timestamps, append+re-sort a dated `<Name>-log.md` |
| Template-file staging (standard) + custom fill | macc-forecast-generator | **two skills, not one** — staging the `.xlsx` copy is ordinary file placement (standard writer); `fill_macc_template.py`'s real cell/formula writes stay a bespoke skill |
| Rich structured entity, folder + occurrences | Threads, Meetings (`vault_lib.py`) | the deepest gap — see below |

### Threads/Meetings — the real gaps, not a hand-wave

- **Identity is external-id-based, not name-based.** Dedup works by scanning
  every existing note's frontmatter for a matching `calendar_event_id`/
  `calendar_series_id` — never by trusting a computed path from a raw
  Outlook id (Outlook's own ids are known-unreliable, per `outlook_lib.py`).
- **Recurring series is a real two-level entity** — a series concept note
  (`## History`, re-sorted like the company `-log.md` files) plus one full
  child note per occurrence.
- **One capture touches multiple notes atomically** — occurrence, series
  note, linked Person notes, linked Thread, all in one logical operation
  with real two-way wikilinks.
- **Permission-gated, human-owned sections** — `vault_lib.py`'s own
  `_CALLER_ALLOW_LISTS` (only `link_person_to_meeting` may touch
  `## Related`) plus a hard-blocked set (`## Personal Notes`, `## Actions`)
  no automated caller may ever write.

All four are resolved by the converged design below (id-based `find`,
multi-call orchestration left to the calling Skill, template-owned section
access) — none of them required leaving Threads/Meetings structurally
special, just using the same primitives more than once per capture.

## Converged design: `vault_manager.py`

```
find(by: "id" | "filename" | "folder", value: X) -> note | [notes]
create(id, note_name, title, frontmatter) -> note
update(id, frontmatter | title) -> note
get_section(id, section_name) -> content
modify_section(id, section_name, content, mode: replace|append) -> ok
```

Five real functions. The split of responsibility is exact: `vault_manager.py`
never makes a domain decision — it finds, places, and writes bytes. The
calling Skill reads via `get_section`, does its own real judgment (re-sort a
log, merge tags, decide what changed), and hands the finished content back.
This is the same "agent decides, script applies" split already established
everywhere in this codebase (SOUL.md-level docstrings, repeatedly) — this
design just makes it universal instead of duplicated per skill.

**Identity — `find` has three modes, deliberately, not just `id`:**
`id`-based lookup (a real UUID, or an external id like `calendar_event_id`
when one genuinely exists) is the long-term model and is what makes rename
free — `update(id, title=...)` changes the display name without moving the
file or breaking a single backlink, because nothing else depends on the
title. But `id` is a NEW required frontmatter field no existing note has
today — `filename`/`folder`-based `find` is what lets this module work
against every note that already exists, with zero backfill required before
it's usable. `id` is adopted going forward, not a blocking migration.

**Section access is template data, not per-skill code:** each template
tags its own sections, e.g. `Personal Notes: user_edit`, `Summary:
machine_write` — checked once inside `modify_section`, centrally, instead of
re-implemented as an allow-list inside every script (today's
`_CALLER_ALLOW_LISTS` pattern, copy-pasted per skill).

**Bulk operations fall out for free.** Because `find(by="folder"/"all")`
already returns a real list of notes, a schema/requirement change — "add
Section XX to every existing node," "add a new frontmatter field vault-wide"
— becomes one script: get all matching notes, call `modify_section`/`update`
per note. Today that would mean auditing every one of the ~13 write scripts
to see whether it needs a matching change. With one real write path, a
migration touches one place, once — this is the concrete version of "we
don't need to look at every single code file and see if we need to modify
it," not just a hoped-for benefit.

## Execution location — decided: copy the file, not an MCP call

Two real options were on the table. Option A (first proposed): a Vault Tool
MCP Action at `/tools/vault`, backed by Second Brain's own
`vault_writer.py` — genuinely one engine, but every vault-writing Skill call
would then depend on the backend being reachable, a real regression from
today's self-contained-script property. Option B (operator's own decision,
2026-08-25): keep `vault_manager.py` standalone and physically copy it into
each Skill's own `scripts/` folder — same "prepare here, apply there"
workflow this repo already uses for every other Hermes-Provisioning/ asset.
This is what got built. A Skill still can't write if it's genuinely
missing its own copy of the file, but that's a copy-it-in step, not a
live network dependency — the self-containment property survives.

The real duplication this eliminates is at the LOGIC layer, not the file-
count layer: today, N Skills each hand-wrote (and independently drifted)
their own primitives. Now N Skills each carry a copy of the exact same
file — editing the engine is one edit + a re-copy to however many Skills
carry it, not N independent edits to N independently-evolved scripts.

## A related, separate gap this session also surfaced (not part of this design)

`REQ-SB-80`'s own `data/` tree (Sections/Agents/Tools/Providers) currently
lives at `<vault>/.second-brain/data/` — convenient (matches the existing
`_STATE_DIR` pattern) but re-introduces exactly the System-Data-vs-Vault-Data
conflation the **2026-08-20 backend-architecture-redesign plan already named**
(`app/data_access/system/` vs `app/data_access/vault/`, this same document's
own "Data taxonomy" section). Operator, 2026-08-25: "in Reality they should
be living Separately from the Vault we don't want the user to destroy those."
Deferred, not acted on — flagged here so it isn't lost, and so whoever picks
up either piece of work sees the other.

## Explicitly out of scope for `vault_manager.py`

- `fill_macc_template.py`'s real cell/formula writes — a document-merge
  skill, not a note-writer; only its file-staging half goes through the
  standard writer.
- Nothing about *how* a calling Skill decides what content to write —
  that stays 100% the calling agent's own judgment, unchanged.

## Open, not decided

- Which real Skill gets the first real copy of `vault_manager.py` +
  Template.json set, and when — not done in this pass, deliberately (this
  pass built and proved the engine against a scratch vault, not against a
  real Skill's real behavior).
- Template.json authoring for the remaining real patterns not yet given a
  template (append-only-must-already-exist for person-lookup is provable
  today via `on_missing: "error"`; create-child-under-resolved-parent for
  Opportunities and the Threads/Meetings multi-note orchestration still
  need their own real templates written and proved).
- Whether `id` backfill for existing content ever happens, or new-only
  adoption is permanent.
- The System-Data-vs-Vault-Data location fix (previous section) — same
  underlying taxonomy question as 2026-08-20's plan, still open five days
  later.
