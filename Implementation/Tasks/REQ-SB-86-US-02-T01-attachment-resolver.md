---
id: REQ-SB-86-US-02-T01
title: vault_attachment_resolver.py — embedded-attachment detection over a real selection of .md files
parent_story: REQ-SB-86-US-02
requirement_id: REQ-SB-86
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-86-US-02-T01 — vault_attachment_resolver.py: embedded-attachment detection over a real selection of .md files

## Parent Story

- Story: [[REQ-SB-86-US-02]] — `../UserStories/REQ-SB-86-US-02-vault-export-data-archive-writer.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-86 *Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)*

---

## Objective

Build the new `vault_attachment_resolver.py` composition module: given a
list of already-selected `.md` file paths, scan each file's own real body
for a genuinely-embedded, on-disk attachment (wikilink-embed and
markdown-image-link syntax) and return the real, deduplicated list of
resolved attachment paths — per `ADR-016`.

---

## Starting State → End State

**Before / Inputs:**
- No attachment-detection module exists anywhere for real vault DATA
  (`REQ-SB-85`'s own `artifact_dependency_resolver.py` is a category
  error here — it resolves capability-artifact dependency edges, not a
  note's own embedded-file references — see `ADR-016`'s own "Alternatives
  Considered").
- `app/obsidian/frontmatter.py::read_note(path) -> tuple[dict, str]`
  already exists and is the real primitive for reading a note's own
  frontmatter+body text.
- Real attachments land under a note's own
  `<subfolder>/attachments/<note-slug>/<message-slug>/<filename>` or
  `<subfolder>/files/<slug>/<original-filename>` convention
  (`app/obsidian/attachments.py`) and/or under `_`-prefixed folders like
  `_assets`.
- **This module's own input is a plain `list[str]` of real,
  vault-relative `.md` paths — a data contract, not a runtime call to
  `REQ-SB-86-US-01`'s own tree endpoint.** However the operator's
  selection was built (this story's own picker, or a hand-constructed
  list for verification), this module never needs that endpoint to exist
  or run — independently buildable and testable.

**After / Outputs:**
- `app/business/logic/vault_attachment_resolver.py` (new) exposes:
  - `resolve_embedded_attachments(selected_md_paths: list[str]) -> list[str]`
    — for each real `.md` path (vault-relative), reads its real body via
    `read_note()`, scans it for:
    - wikilink-embed syntax: `![[<target>]]` (optionally with a
      `|alias`/`#heading` suffix, matching Obsidian's own real embed
      syntax).
    - markdown-image-link syntax: `![<alt>](<target>)`.
    For each match, resolves `<target>` to a real, existing on-disk path
    (checked relative to the note's own containing folder first, then
    against the note's own `attachments/<note-slug>/**` /
    `files/<slug>/**` convention paths, then as a vault-root-relative
    path — the exact resolution order is this task's own disclosed,
    scope-internal judgement call, since neither the PRD nor `ADR-016`
    specifies one). A reference that does not resolve to any real,
    existing file on disk is silently skipped — never fabricated into the
    result, never a hard failure (`ADR-016`'s own "silently skipped"
    Decision text).
    Returns the deduplicated list of real, vault-relative attachment
    paths found across every selected `.md` file (empty list when none
    are embedded anywhere in the selection).

---

## Files to Modify

- `src/backend/app/business/logic/vault_attachment_resolver.py` (new).

---

## Constraints

- Inherits from parent story.
- **Never a dependency-closure resolution, never a secret-scan pass** —
  per `ADR-016`'s own explicit posture divergence from `ADR-013`.
- **A referenced attachment that doesn't resolve to a real file is
  silently skipped** — never raises, never included as a fabricated
  entry.
- **Both real embed syntaxes are scanned** (`![[...]]` and `![...](...)`)
  — a single-syntax scan is explicitly rejected by `ADR-016`'s own
  "Alternatives Considered".
- Pure function, no file writes — this module only reads and resolves,
  never mutates vault content.
- Deduplicates the returned list (the same attachment referenced by two
  different selected files is returned once).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-86-US-02-AC-04]` Call `resolve_embedded_attachments([...])`
   with a real, currently-existing `.md` file in the vault whose own
   content genuinely embeds a real, on-disk attachment (an image, an SVG,
   or a PDF) via either real syntax; confirm the returned list contains
   that attachment's own real, resolved path.
2. `[REQ-SB-86-US-02-AC-04]` Repeat with a selected `.md` file engineered
   (in a disposable scratch note, cleaned up after) to reference an
   attachment path via the OTHER real syntax than step 1 used (i.e. cover
   both `![[...]]` and `![...](...)` across the two steps); confirm both
   are correctly resolved.
3. `[REQ-SB-86-US-02-AC-05]` Call `resolve_embedded_attachments([...])`
   with a real `.md` file whose content embeds no attachment at all;
   confirm the returned list is empty — nothing fabricated.
4. Call `resolve_embedded_attachments([...])` with a real `.md` file
   engineered to reference a target path that does NOT exist on disk;
   confirm it is silently skipped (absent from the result, no exception
   raised) (no AC tag — supports the "silently skipped" Constraint, an
   `ADR-016` decision point, not itself a separately-locked story AC).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `resolve_embedded_attachments()` correctly resolves both real embed
      syntaxes to real, existing on-disk attachment paths
- [x] A non-resolving reference is silently skipped, never fabricated,
      never a hard failure
- [x] A selection with no embedded attachments returns an empty list
- [x] Result is deduplicated
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing the `.sbd` archive itself, flat/hierarchy extraction,
  collision disambiguation — `T02`.
- Any dependency-closure resolution or secret-shaped-string scanning —
  `ADR-016` explicitly excludes both from this whole story.
- Reading the operator's own selection from `REQ-SB-86-US-01`'s own tree
  endpoint — this module's input is a plain path list, never that
  endpoint's own response shape.

---

## Context / Notes

`ADR-016` (`Implementation/Architecture/ADR.md`) and architecture
`§Vault Data Export → §Embedded-Attachment Resolution & .sbd Archive
Writer` (`Implementation/Architecture/architecture.md`) are the
authoritative design for this task. **Decomposer's own cross-story
dependency call:** this task carries `depends_on: []` — it does NOT
depend on `REQ-SB-86-US-01-T01`/`T02` — because its own input contract is
a plain `list[str]` of real vault-relative `.md` paths, decoupled from
however that list was produced. Build and verify it against a
hand-constructed selection list; no real picker UI or tree endpoint is
required to exist for this task to be complete.

---

## Implementation Log

**Built:** `src/backend/app/business/logic/vault_attachment_resolver.py`
(new) — `resolve_embedded_attachments(selected_md_paths: list[str]) ->
list[str]`. Scans each selected note's real body (via
`app/obsidian/frontmatter.py::read_note`) for both real embed syntaxes
(`![[...]]`, `![...](...)`) and resolves each target to a real,
existing on-disk vault-relative path, or silently skips it.

**Scope-internal judgement calls (logged for human spot-check, per
`Implementation/Learnings.md`'s established pattern — none blocking,
none weakening a locked AC):**
1. **Resolution order** (never specified by the PRD or `ADR-016`,
   explicitly delegated to this task): (1) relative to the referencing
   note's own containing folder — confirmed live as this vault's real,
   dominant convention today; (2) every ancestor folder level from the
   note's own folder up to the vault root, recursively searched for the
   target's own filename under an `attachments/`/`files/` subfolder
   (the real `write_attachments()`/`write_file_companion()` convention);
   (3) as a plain vault-root-relative path.
2. **A target that resolves to a real `.md` file is treated as an
   Obsidian note-transclusion, not an attachment, and is skipped** —
   `![[Some Note]]` is syntactically identical to a real file embed, but
   including it would silently pull an unselected note's own content
   into a future export, in tension with the parent story's own
   Scenario 6 ("nothing outside the operator's own selection is ever
   included"). The PRD/`ADR-016` text names only images/SVGs/PDFs as the
   real attachment kinds this feature targets.
3. **Path canonicalization for dedup** — a genuine bug found live during
   verification (not a design call): a target reached via a `../`
   relative traversal from the note's own folder produced a
   non-normalized vault-relative string (`Work/_scratch-test/../
   Technology/...`) that failed to dedup against the SAME physical file
   reached directly by a sibling note. Fixed by resolving both the
   matched attachment path and the vault root via `Path.resolve()`
   before computing the vault-relative string — confirmed live, see
   below.

**Live verification (real vault at `settings.vault_path`, 2026-09-01):**
Ran a throwaway script (`src/backend/scripts/_scratch_verify_attachment_
resolver.py`, deleted immediately after this pass — never committed)
against the real, live vault. Two disposable scratch notes were created
directly in the vault under `Work/_scratch-test/` for the cases the real
vault's own current content couldn't otherwise exercise (a
markdown-image-link embed, a non-resolving reference, and the
`attachments/<note-slug>/**` convention path — a real, empty scratch
`.png` file was also created for this last case); every scratch
artefact (notes, the scratch attachment file, and the `_scratch-test`
folder itself) was deleted immediately after this verification pass —
confirmed absent via `Test-Path` (`False`/`False`) after cleanup.

- `[REQ-SB-86-US-02-AC-04]` **Step 1 (real wikilink-embed, real vault
  content, no engineering needed):** called `resolve_embedded_
  attachments(["Work/Technology/Azure/Architecture/Infra/AKS Baseline
  Architecture.md"])` — this real note's own real body genuinely
  contains `![[aks-baseline-architecture.svg]]`, a real sibling SVG.
  **Observed:** `['Work/Technology/Azure/Architecture/Infra/aks-
  baseline-architecture.svg']` — the real attachment's real path,
  correctly resolved. **PASS.**
- `[REQ-SB-86-US-02-AC-04]` **Step 2 (engineered scratch note, the
  OTHER real syntax — markdown-image-link):** a disposable scratch note
  at `Work/_scratch-test/attachment-resolver-test.md` referenced the
  same real SVG via `![Sample AKS architecture diagram](../Technology/
  Azure/Architecture/Infra/aks-baseline-architecture.svg)`. **Observed
  (after the path-normalization fix):**
  `['Work/Technology/Azure/Architecture/Infra/aks-baseline-
  architecture.svg']` — correctly resolved to the same real,
  normalized path. **PASS.**
- `[REQ-SB-86-US-02-AC-05]` Called `resolve_embedded_attachments(
  ["Work/Customers/G42/G42.md"])` — a real Customer note with no
  embedded attachment anywhere in its real body. **Observed:** `[]`.
  **PASS.**
- Unlabeled step (`ADR-016`'s "silently skipped" Constraint, supporting
  evidence, not itself a locked AC): a disposable scratch note
  referencing `![[this-file-does-not-exist-anywhere.png]]` (a target
  that genuinely does not exist on disk anywhere in the vault).
  **Observed:** `[]`, no exception raised. **PASS.**
- Deduplication (`## Acceptance Criteria` bullet, not separately
  AC-tagged): called with the wikilink-embed note twice plus the
  scratch markdown-image-link note (both real-resolving to the SAME
  physical SVG). **Observed:** a single-element list — the same real
  attachment referenced two different ways across two different
  selected files still deduplicates to one entry. **PASS** (this is the
  case that surfaced and confirmed the fix for the path-normalization
  bug above).
- Extra coverage beyond the task's own named steps (the
  `attachments/<note-slug>/**` ancestor-level convention path — no real
  data exists yet in the live vault to exercise this branch, since
  `write_attachments()` has no real caller wired up yet per this
  codebase's own current state): a real, disposable
  `Work/_scratch-test/attachments/attachment-resolver-conv-test/msg-1/
  conv-test.png` file plus a scratch note referencing it via
  `![[conv-test.png]]` (bare filename, no path). **Observed:**
  `['Work/_scratch-test/attachments/attachment-resolver-conv-test/
  msg-1/conv-test.png']` — correctly resolved via the ancestor-level
  `attachments/` search. **PASS** — confirms the convention-path branch
  works, though it remains unexercised against genuine production data
  until a real caller of `write_attachments()` exists.

gate: clear 2026-09-01 — no MUST-FLAG trigger fired (no new dependency,
no shared-interface change, no ADR deviation — this task builds exactly
what `ADR-016`/the parent story's Notes already authorized; both locked
ACs verified live with a real positive result; the three items above are
scope-internal judgement calls, logged for spot-check, not escalations).
