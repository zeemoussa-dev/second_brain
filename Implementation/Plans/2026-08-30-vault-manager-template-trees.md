# Vault Manager — template trees, parent resolution, and the retirement of `vault_writer.py` — design (not yet built)

**Date:** 2026-08-30
**Status:** Design converged through a live collaborative session. Extends
`Implementation/Plans/2026-08-25-vault-writer-standardization.md` (the
original `vault_manager.py` engine — five functions, single-file templates,
now live in 7 real Hermes Skills). Not yet built. Rollout order decided
(operator): **Notes → Opportunities → Customers → Messages → Threads.**

## Why this document exists

The 2026-08-25 design proved the engine (`find`/`create`/`update`/
`get_section`/`modify_section`) and got it into real use, but only for
entities that are a **single file** (`note`, `file`, `meeting`,
`meeting-series`, the KB-doc templates). Trying to fit Customer, Project,
Opportunity, and Thread into that same single-file `Template.json` shape is
what surfaced this design: those aren't edge cases needing one more boolean
flag each — they're a genuinely different, and actually more common, shape.
Operator: **"Template is not just a file, Sometimes actually most of the
time it should be the full Structure Parameterized."**

## The core reframe: a Template is a parameterized tree, not a file

A Template describes a **tree of nodes** — `directory` or `md` (or an
opaque attachment slot for a real non-md file, a PPTX, dropped in
alongside a note) — stamped out once per real record, with names and
content substituted from tokens (the record's own identity, the template's
own entity name, computed cross-references). This single grammar covers
every real shape already found in the vault, so there is no separate
"single-file template" vs "compound template" concept — a single file is
just a one-node tree:

| Shape | Real example | Tree |
|---|---|---|
| Single file | `note`, `file`, `meeting`, kb-docs, **Customer** (hub note) | one `md` node |
| Fixed multi-role structure | **Project** (OKF) | a `directory` node with four fixed `md` children (`index`, `<slug>`, `log`, `captures`), created atomically together |
| Growing-collection structure | **Thread** | a `directory` node (`concept` + a dynamic `messages` slot) — the slot is a shape, not a list; a new child is stamped into it once per real event, unbounded, never fixed at template-authoring time |

Two further real requirements sit **orthogonal** to tree shape — every
node can independently need either of these regardless of what shape it's
part of:

- **Two different kinds of link, resolved completely differently.** A node
  linking back to its own record's root (a Project's `log.md` linking to
  its own `index.md`) is an **internal sibling link** — always resolvable,
  because the whole tree was created atomically together. Opportunity
  linking to its parent Customer is an **external required-parent link** —
  a *different* tree, that must already exist, that this template refuses
  to fabricate. Same-looking token, opposite resolution rules; the schema
  needs two distinct concepts, not one.
- **Per-node folder-creation permission.** Can this node's containing
  folder be auto-created if it's missing, or is that an error condition?
  Operator's own worked examples: **"for thread for example its a yes) in
  Customer its a no."** A new message arriving is a completely normal
  reason for `messages/` to not exist yet. A Customer's own folder not
  existing when something tries to write into it is a bug, not a normal
  state to paper over.

## Identity / lookup, declared by the template, not the caller

Operator: **"a flag in the template search by tag or reach by file
name."** Today's `find()` already supports `id`/`filename`/`folder` — but
which one a given entity should be found by is currently up to whatever
the calling script happens to pass. That's backwards: the **template**
should declare its own identity strategy (`by_tag`, `by_filename`,
`by_id`), and callers just supply the value — matching what Person
dedup (by email tag, falling back to name) already needs today and
`vault_writer.py` currently hand-rolls per entity.

## What Templates are explicitly NOT for — scope discipline

Operator: **"This is not a full library and this why Second Brain System
is needed."** Two corollaries, both real corrections made live in this
same design session:

1. **The vault search index is derived, not a target.** Database analogy
   (operator): a user creates a table and chooses where it lives; an index
   is auto-tuned, invisible, built *from* the table — nobody reads the
   index, they read the real row/document. `build_vault_index.py` /
   `.second-brain/index/folders/*.json` must stay correct against whatever
   real structure a Template produces — a Template is never designed
   *around* what the index currently understands. If a new tree shape
   doesn't fit the index-builder's current scanning logic, the fix is in
   the index-builder, never a constraint pushed backward onto the
   Template.
2. **Placement is a Second Brain business-layer decision, never a Template
   concern.** By the same logic: a Template doesn't know its own Section,
   doesn't decide where a new record goes, doesn't make any routing
   judgment (that's REQ-SB-64's future Section-Hub/Librarian territory,
   not built yet). `vault_manager.py` stays a pure mechanical executor —
   it finds, places (at a path it's *told*), and writes bytes. Every
   smart decision (which template, which parent, where) happens in the
   calling Skill or, eventually, Second Brain's own backend — exactly the
   "`vault_manager.py` never makes a domain decision" split the
   2026-08-25 document already established for the single-file case, now
   confirmed to hold for the tree-shaped case too.

## Requirements this puts on the Template schema

- Tree shape: nodes, fixed children, or one dynamic child slot.
- Identity/lookup strategy, declared once per template (`id` / `filename`
  / `tag`).
- Two link kinds: internal-sibling (auto-resolvable) vs. external-required
  (must pre-exist, template-declared "error if missing," never fabricated).
- Per-node auto-vivify-folder permission (yes/no).
- Per-section access (already real today — `machine_write`/`user_edit`),
  now living per-node instead of flat.
- Token substitution: record identity, entity name, computed
  cross-references (the internal sibling link) vs. caller-supplied content
  vs. left empty until filled.

## Requirements this puts on `vault_manager.py` (the engine)

- **Atomic multi-node creation** — a fixed tree (OKF) is stamped as one
  `create()` call, not N independent ones that could half-fail.
- **A dynamic-child operation, distinct from `create()`** —
  `add_child(parent_record, slot, ...)` — reusing the same node grammar
  for just the one child being added (this is what a new Thread message
  actually is).
- **Node-path addressing** for later calls — `modify_section(record,
  node="log.md", section=..., mode=...)` — replacing today's implicit
  "the one file."
- **Lookup dispatch by the template's own declared strategy** — today's
  `find()` gains a real `tag` mode alongside `id`/`filename`/`folder`.
- **Parent-resolution check** — generic, any template can declare an
  external-required-parent link; the engine resolves-and-errors, never
  fabricates.
- **Folder-create-permission check** — generic, any node can declare
  whether its own containing folder may be auto-vivified.

None of the above is entity-specific code — once built, Customer,
Opportunity, and every future entity are pure `Template.json`
authoring, zero Python, matching the original "extending what it can
write happens by adding a Template.json, never by writing a new script"
principle from the 2026-08-25 design.

## Retiring `vault_writer.py` — the real remaining scope

Full retirement is bigger than the entities in this rollout. Named here so
it isn't lost, not solved by this pass:

- **Person** — needs dedup-by-email-or-name-slug, i.e. exactly the
  template-declared-lookup-strategy capability above, generalized to a
  fallback chain (try `tag`/frontmatter-field, fall back to `filename`).
- **Task** — needs specific frontmatter fields (`due`, `status`) to
  always-overwrite on update; today the create-or-update flow only fills
  frontmatter at creation time, never refreshes it on the update path.
- **Meeting attendee-linking** (`upsert_attendee_links`) — needs a real
  merge/dedup mode; today's `modify_section(mode="append")` just
  concatenates text, no dedup — a genuinely different primitive from
  either `replace` or `append`.
- **Confirm dead code**: `vault_writer.py`'s own hand-written Meeting
  functions (`create_meeting_note_baseline` etc.) may already be fully
  superseded now that `ingest_meeting.py` uses the real `meeting`/
  `meeting-series` Templates — if no other caller still uses them, that
  part of the retirement is a deletion, not a template-authoring task.

## Rollout order (operator, decided)

**Notes → Opportunities → Customers → Messages → Threads.**

1. **Notes** — re-verify the existing single-file `note` template against
   the new engine once the tree-shape/lookup-strategy additions land, as a
   regression baseline (the simplest, already-proven shape, first against
   the widened engine) before building anything new on top of it.
2. **Opportunities** — first real use of the external-required-parent
   link + parent-resolution check (child-of-Customer, refuse to
   fabricate). Single-file shape, so this proves the new *relationship*
   primitive in isolation, without also needing tree/dynamic-child work.
3. **Customers** — first real use of the declared-lookup-strategy
   (by name/tag) + dateless singleton filenames + the hub-note
   `user_edit`-body convention. Single-file shape (per the earlier
   decision: Customer stays the hub note, Project stays OKF, both
   legitimate) — proves identity/lookup in isolation.
4. **Messages** — first real use of the dynamic-child-slot primitive
   (`add_child`), nested under an existing Thread.
5. **Threads** — composes a `concept` node with the `messages` dynamic
   slot proved in step 4; built last because it depends on that primitive
   already working.

## Open, not decided

- Exact token syntax (the `[[record_name]]`-style placeholders were a
  first sketch, explicitly called "very wrong... and not complete" by the
  operator — the vocabulary itself still needs to be nailed down, not just
  the concepts behind it).
- Exact node-path addressing syntax for `modify_section`'s `node=`
  parameter (a literal filename like `"log.md"`, a declared node id, or
  something else).
- Whether `id` backfill for existing pre-`vault_manager.py` content ever
  happens, or new-only adoption stays permanent (carried over, still open,
  from the 2026-08-25 document).
- The attachment-node type name/shape for a real non-md file (PPTX, etc.)
  dropped in alongside a note — mentioned as a real case, not yet modeled.
- Full `vault_writer.py` retirement scope (Person/Task/Meeting
  attendee-linking, above) — named, not scheduled; this rollout only
  covers Notes/Opportunities/Customers/Messages/Threads.
