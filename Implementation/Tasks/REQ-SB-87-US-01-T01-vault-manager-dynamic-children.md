---
id: REQ-SB-87-US-01-T01
title: vault_manager.py — declarative dynamic (unbounded) child-note primitive
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T01 — vault_manager.py: Declarative Dynamic (Unbounded) Child-Note Primitive

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Extend `Hermes-Provisioning/shared/vault_manager.py`'s `Template.json`-driven
engine with a declarative, unbounded ("dynamic") child-note shape — the real
primitive Thread's own `messages/` folder needs — per `ADR-017`'s Decision.

---

## Starting State → End State

**Before / Inputs:**
- `Template.json`'s existing `root.children` array is FIXED-only: every
  entry is created once, atomically, alongside the root note, at
  `<root-stem>-<suffix>.md` in the SAME folder as the root (`create()`,
  `vault_manager.py` lines ~919-936). There is no notion of a child that
  grows one-at-a-time across the root note's whole lifetime, and no
  idempotent-lookup-before-create mechanism for that shape.
- The engine's own module docstring already anticipates this exact
  extension ("fixed/dynamic children (OKF, Thread's messages/) are a real,
  later addition to this same shape, not built here").

**After / Outputs:**
- `Template.json`'s `root.children` entries gain an optional
  `"growth": "fixed" | "dynamic"` field, **defaulting to `"fixed"`** — every
  existing template (Customer/Partner's `log`/`captures`, Opportunity's
  `log`/`captures`) is byte-identical in behavior with zero edits.
- A `"dynamic"` entry declares:
  - `"folder"` — the subfolder name under the root note's own containing
    folder (e.g. `"messages"`).
  - `"identity_fields"` — a list of frontmatter field names that together
    form the natural key for idempotent lookup (e.g.
    `["conversation_id", "message_id"]`).
  - Its own `"frontmatter_defaults"` / `"sections"` (optional) — the child's
    own note shape, independent of the root's.
- A new engine verb, `create_dynamic_child(vault_path, template, root_id,
  child_name, identity, frontmatter=None, sections=None) -> dict` —
  conceptually:
  1. Resolves the ALREADY-EXISTING root note via `find_by_id` (or, if the
     caller resolves by title/parent, an equivalent already-resolved
     `Path`) — **never fabricates the root**; raises `VaultManagerError` if
     it doesn't exist.
  2. Looks up the named `child_name` entry in `template["root"]["children"]`
     — raises `VaultManagerError` if no such `growth: "dynamic"` entry is
     declared.
  3. Lists existing children under `<root-folder>/<declared-folder>/*.md`;
     reads each one's frontmatter; if one already matches EVERY
     `identity_fields` value given in `identity` (dict), returns
     `{"created": False, "updated": False, "path": str(existing), ...}` —
     genuinely idempotent, no duplicate.
  4. Otherwise creates a new note under that subfolder (a real,
     collision-safe filename — reuse `_unique_dated_path`'s own
     never-overwrite discipline, or an equivalent uniqueness guarantee for
     this shape), writing `identity` merged into `frontmatter_defaults` +
     any caller-supplied `frontmatter`, plus `sections`. Returns
     `{"created": True, "updated": False, "path": str(new_path), ...}`.
  - Exact function/parameter naming is this task's own call (`ADR-017`:
    "exact CLI/JSON shape is decomposer/coder-level") — the names above are
    a strong default, not a rigid contract, as long as the three guarantees
    (never fabricate root, idempotent natural-key lookup, genuinely
    unbounded) hold.
- CLI gains a new `create-child` command (or an equivalent extension of the
  existing `create` command's own argument set — coder's call) exposing the
  same verb: `python vault_manager.py create-child --vault-path P
  --template-id T --id ROOT_ID --child NAME --input-file F` where `F:
  {"identity": {...}, "frontmatter": {...}?, "sections": {...}?}`.
- **Structurally kept separate from the existing FIXED-children mechanism**
  — a dynamic entry is never force-unified into the flat
  `<root-stem>-<suffix>.md` sibling convention (`ADR-017`'s own rejected
  "Alternatives Considered" #2).

---

## Files to Modify

- `Hermes-Provisioning/shared/vault_manager.py` (the canonical source — per
  its own module docstring, edited in exactly ONE place).
- `Hermes-Provisioning/shared/tests/test_vault_manager.py` (new automated
  test coverage for the dynamic-child primitive).

---

## Constraints

- Inherits from parent story.
- `growth` defaults to `"fixed"` — every already-`Done` template stays
  byte-identical in behavior (zero `Template.json` edits needed for any of
  them).
- Never fabricates the root note — a dynamic-child call against a
  non-existent root is a real `VaultManagerError`, never a silent
  auto-create.
- Idempotent lookup is by the declared `identity_fields` natural key, not by
  filename or creation order — the 1st and Nth call with the SAME identity
  values must return the SAME existing path, never a duplicate.
- No ceiling on how many dynamic children a root note can hold — never scan
  a small, fixed-size in-memory structure; always a genuine directory
  listing under the declared subfolder.
- Do not touch any already-`Done` template's own `Template.json` in this
  task — that verification happens in `T06`; this task only builds the
  generic engine capability, proven here against a throwaway scratch
  template fixture (mirroring `test_vault_manager.py`'s own existing
  fixture-template style).

---

## Tests

This file has a real, already-established pytest suite —
`Hermes-Provisioning/shared/tests/test_vault_manager.py` (44/44 passing as
of 2026-08-31). New capability here extends that same suite with real,
automated tests, run via:

```
src\backend\.venv\Scripts\python.exe -m pytest Hermes-Provisioning\shared\tests\test_vault_manager.py -v
```

**Automated tests (new, added to `test_vault_manager.py`):**
1. `[REQ-SB-87-US-01-AC-03]` Using a scratch `Template.json` fixture whose
   `root.children` declares one `growth: "dynamic"` entry (e.g. folder
   `"items"`, `identity_fields: ["external_id"]`), create a root note, then
   call `create_dynamic_child()` for the SAME root 1 time, then again for a
   genuinely DIFFERENT `external_id` value a second and third time (3
   distinct children total). Assert all 3 children exist under
   `<root-folder>/items/`, each a real, separate file — proving the shape
   is genuinely unbounded (never treated as a fixed-size set), for both the
   1st and the Nth call.
2. `[REQ-SB-87-US-01-AC-04]` Call `create_dynamic_child()` twice with the
   SAME `identity` values against the same root. Assert the second call
   returns `{"created": False, ...}` with the SAME `path` as the first
   call's result, and that only ONE file actually exists on disk under the
   declared subfolder — no duplicate.
3. (Unlabeled, supporting) Call `create_dynamic_child()` against a
   `root_id` that does not resolve to any real existing note. Assert a
   `VaultManagerError` is raised — the root is never fabricated.
4. (Unlabeled, regression) Run the full existing `test_vault_manager.py`
   suite; confirm every previously-passing test still passes — the `growth`
   field default and the new verb introduce zero behavior change to any
   existing, already-tested code path.

**Manual verification steps:** none required — this task is fully covered
by the automated suite above (a real, already-scaffolded test stack for
this exact file).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `Template.json`'s `root.children` entries accept an optional
      `growth: "fixed" | "dynamic"` field, defaulting to `"fixed"`
- [x] A `"dynamic"` entry's own `folder`/`identity_fields`/
      `frontmatter_defaults`/`sections` are read and honored
- [x] `create_dynamic_child()` (or equivalently-named verb) never
      fabricates a non-existent root, idempotently looks up by natural key,
      and supports unbounded real children under its own subfolder
- [x] CLI exposes the new verb
- [x] Every pre-existing `test_vault_manager.py` test still passes (zero
      regression)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Per-caller section-write access (`allowed_callers`) — `T02`.
- Resyncing this engine change to any of the nine real deployment
  locations — `T03`.
- Authoring the real `thread`/`raw-message` `Template.json` that actually
  USES this new `growth: "dynamic"` field — `T05`.
- Retrofitting `meeting-capture`'s own `occurrences/` folder onto this
  primitive — explicitly out of scope for the whole requirement (parent
  story's own Non-Goals); this task only builds the generic capability.

---

## Context / Notes

`ADR-017` (`Implementation/Architecture/ADR.md`) and `architecture.md` →
`§vault_manager.py Engine Extensions — Dynamic Children & Per-Caller
Access` are the authoritative design. Read `vault_manager.py`'s own
`create()`/`_unique_dated_path()` directly before writing this task's
code — the dynamic-child naming/collision-avoidance should reuse the SAME
never-overwrite discipline `_unique_dated_path` already provides for fixed
notes, not reinvent a second one.

---

## Implementation Log

**What was built** (`Hermes-Provisioning/shared/vault_manager.py`, the
canonical source only — per its own docstring, "edited in exactly ONE
place"):
- `Template.json` module docstring updated to describe the new
  `growth: "fixed" | "dynamic"` `root.children` shape and the new
  `create-child` CLI command (previously described the dynamic shape as
  "not built here").
- `create()`'s two fixed-children code paths (`children_index_lines`
  comprehension; the atomic sibling-write loop) both now skip any
  `child_spec.get("growth", "fixed") == "dynamic"` entry — never written
  at root-creation time.
- New `_find_dynamic_child_spec(template, child_name)` helper + new
  `create_dynamic_child(vault_path, template, root_id, child_name,
  identity, frontmatter=None, sections=None) -> dict`, inserted between
  `create()` and `update()`.
- CLI gained the `create-child` command (`--id ROOT_ID --child NAME
  --input-file F`, `F: {"identity": {...}, "frontmatter": {...}?,
  "sections": {...}?}`).
- `Hermes-Provisioning/shared/tests/test_vault_manager.py`: 6 new tests
  added (unbounded-growth, idempotent-lookup, missing-root refusal,
  undeclared-child refusal, fixed-children-unaffected-by-default, and a
  mixed fixed+dynamic composition case).

**Scope-internal judgement calls** (logged for human spot-check, per
`## Constraints`'s "exact function/parameter naming is this task's own
call"):
- A `"dynamic"` `root.children` entry is identified by a NEW `"name"`
  key (distinct from a fixed entry's `"suffix"`, which has no meaning
  for a child with no filename-suffix concept). `T05` (the real Thread/
  RawMessage `Template.json`) should declare `"name": "messages"` to
  match.
- `create_dynamic_child()` resolves the root via an UNSCOPED
  `find_by_id(vault_path, root_id)` (no `note_name` hint) — matches the
  task's own End-State ("the caller resolves by title/parent, an
  equivalent already-resolved Path" was the only named alternative, and
  the CLI shape in the task's own End-State takes no `--note-name`
  either). `_iter_real_md_files`'s own archived-folder exclusion (fixed
  2026-08-27) makes an unscoped scan safe; a real vault-wide scan cost
  was accepted as this task's own build, not optimized further here.
- New-child filename slug falls back to `"-".join(identity.values())`
  when no caller-supplied `frontmatter["title"]` is given (a dynamic
  child has no root-level `title` concept) — reuses `_unique_dated_path`
  verbatim, per the task's own Context instruction.

**Verification (automated, `Hermes-Provisioning/shared/tests/
test_vault_manager.py`):**
- `[REQ-SB-87-US-01-AC-03]` PASS —
  `test_dynamic_children_are_genuinely_unbounded`: 3 distinct children
  created (1st/2nd/3rd calls) under the same root's own `items/`
  subfolder; all 3 real files confirmed on disk, filenames matched
  1:1 against the function's own returned paths.
- `[REQ-SB-87-US-01-AC-04]` PASS —
  `test_dynamic_child_idempotent_lookup_by_identity_fields_avoids_duplicate`:
  same `identity` twice → second call returned `created: False` with the
  SAME path as the first; exactly one real file on disk; original
  section content confirmed untouched (a second call's own differing
  content never landed).
- (Unlabeled, supporting) PASS —
  `test_create_dynamic_child_never_fabricates_a_missing_root`: a
  non-existent `root_id` raised `VaultManagerError`, zero files written.
- (Unlabeled, regression) PASS — full `test_vault_manager.py` suite:
  **50/50 passed** (44 pre-existing + 6 new), run via
  `src\backend\.venv\Scripts\python.exe -m pytest
  Hermes-Provisioning\shared\tests\test_vault_manager.py -v`. Zero
  pre-existing test needed modification.

**Additional live verification (real scratch-vault CLI session, per the
operator's own explicit instruction to construct a real scratch template
and confirm real files land on disk)** — a throwaway `thread-scratch`
template (own_folder root, one FIXED `log` child + one DYNAMIC
`messages` child, plus a `parent` declaration) under a scratch vault at
`<session scratchpad>/scratch-vault`, driven via the real
`vault_manager.py` CLI (`create`, `create-child`), not pytest:
1. Created Thread A (`parent_value: "Acme Corp"`, `on_missing:
   "auto_create"`) and Thread B (top-level, `required: false`) — both
   roots created correctly, the fixed `log` sibling written atomically
   alongside each, no `messages/` folder existing yet for either
   (confirms a dynamic entry is genuinely never created at
   root-creation time).
2. `create-child` for Thread A twice with different identities (`msg-1`,
   `msg-2`) — 2 real files landed under Thread A's own
   `.../messages/` folder, each with correct frontmatter (`type`,
   `conversation_id`, `message_id`, `title`, `sender`, `id`, `created`)
   and correct `## Body` section content.
3. `create-child` for Thread A a THIRD time with the SAME identity as
   call 1 (`msg-1`), differing title/body — returned `created: false`,
   same path as call 1; a real directory listing confirmed exactly 2
   files (not 3) under Thread A's `messages/`; the original file's
   `## Body` content was confirmed unchanged (the dupe call's own
   content never landed).
4. `create-child` for Thread B with the SAME identity values as Thread
   A's call 1 — created a genuinely separate real file under Thread B's
   OWN `messages/` folder (a completely different path), proving two
   different roots' dynamic children never collide even on identical
   natural-key values.
5. Composition confirmed with zero regression: Thread A's own
   `customer` frontmatter field and the auto-created "Acme Corp" hub
   note's `## Threads` link-back section were both correct and intact
   after all of the above — the engine's existing `parent`/fixed-
   `children` mechanisms and the new dynamic-child primitive worked
   together on the same template in the same session.

Scratch vault deleted after verification (not a repo artefact). No file
outside `## Files to Modify` was touched.

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this
task** — no new dependency, no shared-interface change beyond what
`ADR-017` already governs, no ADR deviation, no unanticipated file, and
every locked AC (`AC-03`, `AC-04`) verified with a real positive result.
`gate: clear`.

gate: clear 2026-09-01 — no triggers fired (ADR-017 already governs this
task's own scope; no new assumption beyond the two scope-internal
judgement calls logged above; no ESCALATIONS entry; task not oversized;
both locked ACs verified live).
