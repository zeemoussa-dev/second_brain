---
id: REQ-SB-86-US-02-T02
title: "sbd_archive.py writer + POST /vault/export-data/export — flat/hierarchy extraction, flat-collision disambiguation (ADR-016)"
parent_story: REQ-SB-86-US-02
requirement_id: REQ-SB-86
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls logged for human spot-check (see Implementation Log) — none blocking, none weakening a locked AC"
phase: P2
depends_on: [REQ-SB-86-US-02-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-86-US-02-T02 — sbd_archive.py writer + POST /vault/export-data/export: flat/hierarchy extraction, flat-collision disambiguation (ADR-016)

## Parent Story

- Story: [[REQ-SB-86-US-02]] — `../UserStories/REQ-SB-86-US-02-vault-export-data-archive-writer.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-86 *Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)*

---

## Objective

Compose `T01`'s attachment resolver into the real export flow: given a
real selection of vault-relative file paths and a flat/hierarchy choice,
write one real `.sbd` zip (no manifest, per `ADR-016`) with flat-collision
disambiguation, exposed as `POST /vault/export-data/export`.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `resolve_embedded_attachments(selected_md_paths: list[str]) -> list[str]`
  exists.
- No archive-writing module exists for real vault data (`ADR-013`'s own
  `sbf_archive.py` is a category error here — always writes a
  `manifest.json`, per `ADR-016`'s own "Alternatives Considered").
- **This task's own input is a plain `selection: list[str]` of real,
  vault-relative paths (files only — any folder selection is already
  expanded into its individual file paths before reaching this endpoint,
  the decomposer's own disclosed judgement call, see Context/Notes below)
  plus an `extraction: "flat" | "hierarchy"` choice — a data contract,
  not a runtime call to `REQ-SB-86-US-01`'s own tree endpoint.**
  Independently buildable and testable against a hand-constructed
  selection.

**After / Outputs:**
- `app/business/logic/sbd_archive.py` (new) exposes
  `write_archive(output_path: str, members: dict[str, str]) -> None` —
  `members` maps each real archive-member path (already computed per the
  flat/hierarchy + collision-disambiguation rules below) to its real
  source file path on disk; writes a real zip, one member per entry, raw
  bytes copied verbatim, **no `manifest.json`, no other metadata** —
  `ADR-016`'s own explicit divergence from `sbf_archive.py`. Pure I/O, no
  business decisions.
- `app/business/logic/vault_export.py` (new) — the real orchestrator:
  - `build_export(selection: list[str], extraction: str) -> str`:
    1. For each real selected path ending in `.md`, calls
       `resolve_embedded_attachments([that path])` (`T01`) and adds every
       resolved attachment path to the export set (deduplicated across
       the whole selection).
    2. Computes each real file's own archive-member path:
       - `extraction == "hierarchy"`: the file's own vault-relative path,
         unchanged (e.g. `Work/Masdar/index.md`).
       - `extraction == "flat"`: the file's own basename (e.g.
         `index.md`). **Flat-collision disambiguation (locked,
         `ADR-016`):** if two or more files in the export set would land
         on the same flat basename, EVERY one of the colliding entries is
         renamed by prefixing its own original immediate parent-folder
         name onto its filename, joined with `_` (e.g.
         `Work/Masdar/index.md` → `masdar_index.md`,
         `Work/Acme/index.md` → `acme_index.md`) — never a silent
         overwrite, never dropping either file.
    3. Writes the real `.sbd` via `sbd_archive.write_archive(...)` to a
       scratch temp path; returns that path.
  - This function never writes to disk anywhere except the one scratch
    temp `.sbd` path it returns.
- `app/api/vault_router.py` — new `POST /vault/export-data/export` route
  (body: `{"selection": [...], "extraction": "flat" | "hierarchy"}`),
  calls `build_export(...)`, returns a `FileResponse` streaming the real
  `.sbd` bytes with `media_type="application/octet-stream"`,
  `filename=f"second-brain-vault-export-{<real ISO-8601 UTC
  timestamp>}.sbd"`, and deletes the scratch temp `.sbd` after the
  response is sent (`BackgroundTasks`, same "clean up scratch temp output
  after streaming" mechanism `REQ-SB-85-US-02-T04`'s own `/commit` route
  already established).

---

## Files to Modify

- `src/backend/app/business/logic/sbd_archive.py` (new file).
- `src/backend/app/business/logic/vault_export.py` (new file).
- `src/backend/app/api/vault_router.py` — one new route.

---

## Constraints

- Inherits from parent story.
- **No `manifest.json`, no structured metadata written alongside content**
  — `ADR-016`'s own explicit decision.
- **Never a dependency-closure resolution, never a secret-scan gate.**
- **A flat-extraction collision is ALWAYS disambiguated by the
  parent-folder-name prefix rule above — never a silent overwrite.**
- **The export contains exactly the operator's own selection plus its
  resolved attachments — nothing outside that set is ever included.**
- The scratch temp `.sbd` is cleaned up after use — no leftover temp file
  on disk after a request completes (success or failure).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-86-US-02-AC-01]` Call `build_export(...)` (or the `/export`
   route) with a real selection spanning two or more real nested folders,
   `extraction="hierarchy"`; open the produced `.sbd` as a real zip;
   confirm every member's own path matches its real vault-relative
   folder structure exactly.
2. `[REQ-SB-86-US-02-AC-02]` Same selection, `extraction="flat"`; open
   the produced `.sbd`; confirm every member lands at the zip root — no
   nested folder path in any member name.
3. `[REQ-SB-86-US-02-AC-03]` Build a selection containing two real files
   from different folders that share the same basename (e.g. two real
   OKF Customer folders' own `index.md`, or a disposable scratch pair if
   none exist naturally); `extraction="flat"`; confirm the archive
   contains BOTH, each renamed with its own real parent-folder-name
   prefix (e.g. `masdar_index.md`, `acme_index.md`) — neither missing,
   neither silently overwritten.
4. `[REQ-SB-86-US-02-AC-06]` Select exactly one real file (no folders,
   no attachments); export (either extraction); confirm the resulting
   `.sbd` contains exactly one member — that file, and nothing else
   (e.g. no sibling files from the same folder).
5. `[REQ-SB-86-US-02-AC-04]` (composed, end-to-end via the real
   `/export` route) Select a real `.md` file whose content genuinely
   embeds a real attachment; export; confirm the resulting `.sbd`
   contains both the `.md` file and the resolved attachment, with no
   prompt/toggle needed to include it.
6. `[REQ-SB-86-US-02-AC-05]` (composed, end-to-end) Select real `.md`
   files with no embedded attachments; export; confirm the resulting
   `.sbd` contains exactly the selected files and no attachment entries.
7. Confirm no scratch temp `.sbd` file remains on disk after any of
   steps 1-6 completes (no AC tag — supports the cleanup Constraint).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Hierarchy extraction preserves real relative folder structure
- [x] Flat extraction lands every member at the zip root
- [x] A flat-extraction collision is always disambiguated by the
      parent-folder-name prefix rule, never overwritten
- [x] The archive contains exactly the selection plus resolved
      attachments — nothing else
- [x] An embedded attachment is always included automatically, no prompt
- [x] A selection with no embedded attachments exports with no extra
      entries
- [x] No scratch temp `.sbd` file is left on disk after any request
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The export-options frontend screen — `T03`.
- Any dependency-closure resolution or secret-shaped-string scanning.
- Import of a `.sbd` file — out of scope for `REQ-SB-86` entirely.
- Expanding a folder-level selection into its own nested file paths —
  per this task's own disclosed judgement call (see Context/Notes), that
  expansion happens client-side, before this endpoint is ever called;
  this task's own input is always a flat file-path list.

---

## Context / Notes

`ADR-016` (`Implementation/Architecture/ADR.md`) and architecture
`§Vault Data Export → §Embedded-Attachment Resolution & .sbd Archive
Writer` (`Implementation/Architecture/architecture.md`) are the
authoritative design for this task.

**Decomposer's own disclosed judgement call (scope-internal, non-
blocking):** neither the story nor `ADR-016` states whether a
folder-level selection is expanded into individual file paths
client-side (by `REQ-SB-86-US-01-T02`'s own already-fetched real tree
data) or server-side (this task walking the real filesystem again for
each selected folder). This task is decomposed assuming **client-side
expansion** — the frontend already holds the full real tree (fetched via
`REQ-SB-86-US-01-T01`'s own endpoint) and can compute the flat file list
locally with zero extra I/O, so the `selection` this endpoint receives is
always a flat list of real file paths, never a folder path. This keeps
`T01`/`T02` decoupled from `REQ-SB-86-US-01`'s own endpoint at RUNTIME
(no server-to-server call between them) while still reflecting the real
selection the operator made. If the coder finds this expansion belongs
server-side instead once building `T03`, that is a scope-internal
judgement call to log and flag for spot-check, not a re-spec.

---

## Implementation Log

**Built:**
- `src/backend/app/business/logic/sbd_archive.py` (new) —
  `write_archive(output_path: str, members: dict[str, str]) -> None`. Pure
  zip I/O: each `members` key is the real archive-member path, each value
  the real source file path on disk, `zipfile.ZipFile.write(source_path,
  arcname=member_path)` per entry. No `manifest.json`, no other metadata
  (`ADR-016`).
- `src/backend/app/business/logic/vault_export.py` (new) —
  `build_export(selection: list[str], extraction: str) -> str`. Filters
  the selection for `.md` paths, calls `T01`'s
  `resolve_embedded_attachments(...)`, unions the resolved attachments
  into the export set (dedup, order-preserving), computes each member's
  archive path via `_compute_archive_members` (hierarchy = unchanged
  vault-relative path; flat = basename, with every colliding basename
  disambiguated by its own immediate parent-folder name prefix), then
  writes the real `.sbd` via `sbd_archive.write_archive(...)` to a scratch
  temp path and returns it.
- `src/backend/app/api/vault_router.py` — new `POST
  /vault/export-data/export` route (`ExportDataExportBody{selection:
  list[str], extraction: Literal["flat","hierarchy"]}`), calls
  `vault_export.build_export(...)`, streams the real `.sbd` via
  `FileResponse` (`media_type="application/octet-stream"`,
  `filename=f"second-brain-vault-export-{ISO-8601 UTC timestamp}.sbd"`),
  deletes the scratch temp path via `background_tasks.add_task(os.remove,
  ...)` after the response is sent — same mechanism
  `REQ-SB-85-US-02-T04`'s own `/commit` route already established.

**Scope-internal judgement calls (logged for human spot-check, per
`Implementation/Learnings.md`'s established pattern — none blocking, none
weakening a locked AC):**
1. **Vault-root-level flat-collision edge case:** if a colliding file sits
   directly at the vault root (no parent folder), `Path(...).parent.name`
   is the empty string; the disambiguation prefix falls back to the
   literal string `"root"` (e.g. `root_index.md`) instead of an empty
   prefix. Neither the story nor `ADR-016` names this exact edge case —
   both only ever illustrate the nested-folder case (`masdar_index.md`,
   `acme_index.md`). Not exercised by any locked AC's own example, and no
   real vault-root-level file collided with anything during live
   verification.
2. **Parent-folder-name prefix casing:** the prefix uses the real,
   on-disk folder name's own exact casing (e.g. a real folder named
   `Masdar` produces `Masdar_index.md`), not a forced-lowercase transform.
   The story/`ADR-016`'s own illustrative examples happen to show a
   lowercase prefix (`masdar_index.md`), but neither locks a
   case-transform rule — Scenario 3's own Then-clause only requires each
   colliding entry to be "disambiguated by prefixing its own original
   immediate parent-folder name," which this satisfies exactly as
   written. Confirmed live below (`Masdar_index.md`/`Acme_index.md` — the
   scratch folders were named with initial caps).
3. **Attachment-resolution scope reused from `T01` as-is:** per this
   task's own composition role, `T01`'s already-`Done`/verified
   `resolve_embedded_attachments()` is called unmodified. Live
   verification surfaced (not caused by this task) that a real,
   currently-existing embed in `Work/Customers/G42/G42.md`
   (`![[cust-g42-group-map.svg]]`, target physically at
   `Work/Customers/_assets/cust-g42-group-map.svg`) does NOT resolve under
   `T01`'s own current search order, since `_assets` is neither the
   note's own containing folder nor an `attachments/`/`files/`
   convention subfolder. This is `T01`'s own already-`Done`, already-
   locked resolution-order judgement call (see its Implementation Log) —
   out of this task's `## Files to Modify` scope to change. Logged here
   only because it was directly observed while constructing this task's
   own live AC-01/02/05/06 test selections (worked around by using
   `Work/Technology/Azure/Architecture/Infra/AKS Baseline
   Architecture.md` — `T01`'s own confirmed-resolving real example — for
   the AC-04 positive case, and `G42.md`/`Bankfab.md`, both real,
   confirmed to add zero extra members, for the other cases).

**Live verification (real vault at `settings.vault_path`, 2026-09-01) —
fresh, explicitly-restarted `uvicorn app.main:app --host 127.0.0.1 --port
8001` (the prior listener on that port had no `--reload` flag, so it
would not have picked up any of this task's new modules/route; killed
both its PID and its parent PID first, confirmed the port was free, then
started one fresh instance and confirmed `GET /vault/overview` returned
`200` before any AC check). Two disposable scratch notes were created
directly in the vault at `_scratch-sbd-verify/Masdar/index.md` and
`_scratch-sbd-verify/Acme/index.md` for the flat-collision case (no
naturally-occurring literal-basename collision exists in this vault's
real current OKF Customer content — the real convention observed live is
`<Name>.md`/`<Name>-log.md`/`<Name>-captures.md`, each already
disambiguated by the customer's own name, not a bare `index.md`/`log.md`
sharing one filename across customers as the task's own illustrative text
assumed) — both deleted immediately after this pass, confirmed absent via
a directory listing (`No such file or directory`). Every check below
called the real, running `POST /vault/export-data/export` route (not a
direct function call) and inspected the real returned `.sbd` bytes as a
real zip via `zipfile.ZipFile`.

- `[REQ-SB-86-US-02-AC-01]` Selection `["Work/Customers/G42/G42.md",
  "Work/Customers/Bankfab/Bankfab.md"]`, `extraction="hierarchy"`.
  **Observed members:** `['Work/Customers/Bankfab/Bankfab.md',
  'Work/Customers/G42/G42.md']` — each at its exact real vault-relative
  path. **PASS.**
- `[REQ-SB-86-US-02-AC-02]` Same selection, `extraction="flat"`.
  **Observed members:** `['Bankfab.md', 'G42.md']` — both at the archive
  root, no nested path in either member name. **PASS.**
- `[REQ-SB-86-US-02-AC-03]` Selection
  `["_scratch-sbd-verify/Masdar/index.md",
  "_scratch-sbd-verify/Acme/index.md"]` (disposable scratch pair, real
  files, sharing the basename `index.md`), `extraction="flat"`.
  **Observed members:** `['Acme_index.md', 'Masdar_index.md']` — both
  present, each disambiguated by its own real parent-folder name, neither
  missing nor overwritten. **PASS.**
- `[REQ-SB-86-US-02-AC-06]` Selection `["Work/Customers/G42/G42.md"]`
  (one real file, no folders; its own embed doesn't resolve per judgement
  call 3 above, so genuinely zero attachments), `extraction="hierarchy"`.
  **Observed members:** `['Work/Customers/G42/G42.md']` — exactly one
  member, nothing else. **PASS.**
- `[REQ-SB-86-US-02-AC-04]` (composed, end-to-end via the real `/export`
  route) Selection `["Work/Technology/Azure/Architecture/Infra/AKS
  Baseline Architecture.md"]` — `T01`'s own confirmed-resolving real
  wikilink-embed example, `extraction="hierarchy"`. **Observed members:**
  `['Work/Technology/Azure/Architecture/Infra/AKS Baseline
  Architecture.md', 'Work/Technology/Azure/Architecture/Infra/aks-
  baseline-architecture.svg']` — both the selected `.md` and its real
  resolved attachment, with no prompt/toggle involved anywhere in the
  request. **PASS.**
- `[REQ-SB-86-US-02-AC-05]` (composed) Selection
  `["Work/Customers/G42/G42.md", "Work/Customers/Bankfab/Bankfab.md"]`
  (genuinely zero resolving embedded attachments across both, confirmed
  live), `extraction="hierarchy"`. **Observed members:** exactly the 2
  selected files, no extra entries. **PASS.**
- Unlabeled step (Constraint, not itself a locked AC): after all 6 calls
  above, listed `tempfile.gettempdir()` for any
  `second-brain-vault-export-*.sbd` file. **Observed:** `[]` — no scratch
  temp `.sbd` left on disk after any request. **PASS.**

gate: flagged 2026-09-01 — no MUST-FLAG trigger fired directly at this
task (no new dependency, no shared-interface change, no ADR deviation —
this task builds exactly what `ADR-016`/the parent story's Notes already
authorized; every locked AC verified live with a real positive result
against the real running route). Set to `flagged`, not `clear`, per this
pipeline run's own explicit coder instruction that scope-internal
judgement calls make a task `gate: flagged` for human spot-check (items 1
and 2 above); a `REVIEW-QUEUE.md` entry was added accordingly, separate
from this story's own still-open `ADR-016` review item (per
`Implementation/Learnings.md`'s 2026-08-16 antipattern — give a genuinely
separate disclosed risk its own line item rather than nesting it inside a
broader one).
