---
id: REQ-SB-88-US-01-T02
title: Migrate Thread ## Files log-line update + Details/--append follow-up pass
parent_story: REQ-SB-88-US-01
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-88-US-01-T01]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-01-T02 — Migrate Thread ## Files Log-Line Update + Details/`--append` Follow-Up Pass

## Parent Story

- Story: [[REQ-SB-88-US-01]] — `../UserStories/REQ-SB-88-US-01-summarize-and-tag-files-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Migrate `update_files_log_line()`'s idempotent Thread `## Files` line-replace
and `add_file_detail()`'s `## Details` append onto `vault_manager.py`, and make
the ONE real Template.json data edit this migration requires: adding
`apply_file_review` to the Thread template's `## Files` `allowed_callers`
array.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `apply_file_review.py` (read directly this session):
  `update_files_log_line(thread_path, file_stem, short_summary)` reads the
  Thread's own `## Files` section via the local `read_body_section`,
  rebuilds the line list with the file's bare `- [[stem]]` line replaced
  by `- [[stem]] -- <short_summary>` (idempotent — a rerun with the same
  `short_summary` is a no-op), then writes it back via the local
  `replace_body_section(thread_path, "## Files", ..., caller=
  _FILES_LOG_CALLER)`. `add_file_detail()` appends new content under
  `## Details` via the same local `insert_body_section_if_missing`/
  `read_body_section`/`replace_body_section` primitives, then embeds any
  copied images (`_attach_images`) as `![[...]]` blocks.
- **Real, confirmed access-control gap (architect finding, this session):**
  the real, deployed Thread Template.json's `## Files` section currently
  declares `"allowed_callers": ["capture_attachments",
  "capture_file_link"]` (`ADR-017`) — a migrated `vm.modify_section` call
  with `caller="apply_file_review"` would be REFUSED outright unless
  `apply_file_review` is added to that same array. This is a real
  correctness requirement for this task, not optional hardening —
  Scenario 3's own AC fails without it.

**After / Outputs:**
- `Templates/thread/Template.json`'s `## Files` section
  `allowed_callers` becomes `["capture_attachments", "capture_file_link",
  "apply_file_review"]` — the exact, already-anticipated `ADR-017`
  extension mechanism (Template.json data, not an engine change).
- `update_files_log_line()` keeps its own hand-rolled idempotent
  line-replace ALGORITHM (build the new whole-section content string with
  the target line replaced/appended) but persists it via
  `vm.modify_section(vault_path, thread_template, section="Files",
  content=<rebuilt section text>, mode="replace", note_id=<Thread's own
  id, read/minted the same way T01 established for Files>,
  caller="apply_file_review")` instead of the local
  `replace_body_section`.
- `add_file_detail()`'s `## Details` append migrates onto
  `vm.modify_section(..., section="Details", mode="append", ...)` — the
  engine's own `mode="append"` performs the existing-content-plus-new-
  content merge `add_file_detail()` currently hand-rolls, so the merge
  logic simplifies to composing the new content and letting the engine
  append it (no `read_body_section`+manual-concat needed). Image copy/
  embed (`_attach_images`/`_unique_sibling_path`) is unrelated filesystem
  work — stays hand-written, unchanged.
- `_SUMMARY_CALLER`/`_FILES_LOG_CALLER`/`_DETAILS_CALLER`/
  `_CALLER_ALLOW_LISTS`/`_HUMAN_OWNED_HEADERS` and the local
  `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section`/`merge_tags`/`read_note` are removed once they
  have zero remaining callers in the file (confirm by re-reading the whole
  file before removing — mirrors `REQ-SB-87-US-04-T02`/`T03`'s own
  dead-code-removal precedent). `read_note`/`_format_frontmatter_value`/
  `_parse_frontmatter_value` stay only if still genuinely called
  (`build_company_index`/`resolve_companies` read frontmatter).

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-files/scripts/apply_file_review.py`
- `C:/myWorx/<operator vault>/<operator vault>/.second-brain/data/Templates/thread/Template.json` (real, live deployed template — add `apply_file_review` to `## Files`' `allowed_callers`)

---

## Constraints

- Inherits from parent story.
- The Thread's own `## Files` line-replace convention (idempotent,
  in-place, never a separate log file) must be preserved exactly —
  Threads stay Log/Captures-file-free per `ADR-042`'s own scope-lock.
- Company resolution stays untouched — this task only migrates the
  files-log/Details persistence mechanics.
- `capture_attachments`/`capture_file_link`'s own existing `allowed_callers`
  entries on `## Files` must remain — this is an ADDITIVE edit
  (append `apply_file_review`), never a replacement of the array.
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
`file`/`thread` Template.json files copied byte-identical from the real,
live vault — including this task's own `## Files` `allowed_callers` edit
applied to the SCRATCH copy first):**

1. `[REQ-SB-88-US-01-AC-01]` Re-run the migrated `apply_file_review.py`
   from `T01`'s own scratch scenario; confirm the script still prints
   `{tags_applied, companies_unresolved, files_log_updated}` with the same
   meaning as today, and `files_log_updated` is `true` when the parent
   Thread's `## Files` line actually changed (closes `AC-01` out fully,
   combined with `T01`'s own Summary/tag confirmation).
2. `[REQ-SB-88-US-01-AC-03]` Given a File note whose `source_thread`
   frontmatter links to a real scratch Thread whose `## Files` section
   already has a bare `- [[file-slug]]` line for it, run
   `apply_file_review.py`; confirm the Thread's own `## Files` line
   becomes `- [[file-slug]] -- <short_summary>`, replaced in place.
   Re-run with the SAME `short_summary`; confirm the line is unchanged
   (idempotent, no duplicate line added, `files_log_updated: false`).
   Re-run with a DIFFERENT `short_summary`; confirm the line is replaced
   in place (still one line, not two).
3. `[REQ-SB-88-US-01-AC-04]` Given a File already summarized once, run
   `apply_file_review.py --append` with a genuinely new follow-up detail
   and one or more image attachments (a disposable test image file);
   confirm the new details are appended under `## Details` without
   overwriting the prior pass, and the image(s) are copied into the
   File's own folder and embedded via `![[...]]`.
4. (Unlabeled, supporting) Attempt (via a disposable throwaway script, not
   this Skill's own entry point) a `## Files` write on the SAME scratch
   Thread with `caller="some_other_script"`; confirm it is refused with a
   real `VaultManagerError`, and that a write with
   `caller="apply_file_review"` succeeds — confirms the Template.json edit
   is genuinely load-bearing, not just present in the file.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `apply_file_review` added to the real, deployed Thread Template.json's
      `## Files` `allowed_callers` (additive, `capture_attachments`/
      `capture_file_link` preserved)
- [x] Thread `## Files` line-replace migrated onto `vm.modify_section`,
      idempotent replace-in-place behavior preserved exactly
- [x] `--append` Details pass migrated onto `vm.modify_section(mode="append")`,
      image attach/embed unchanged
- [x] Now-dead local section-write primitives removed (confirmed zero
      remaining callers before removal)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## Summary` write / tag-merge — `T01`.
- Real-vault retrofit verification — `T03`.
- Cron job provisioning — `T04`.

---

## Context / Notes

`architecture.md` → `§Files-Skill vault_manager.py Migration + Cron
Provisioning (REQ-SB-88-US-01)` is authoritative on the Template.json
edit. The live Template.json path is outside the repo (this project's
vault is always external to `src/`/`Hermes-Provisioning/`) — edit it
directly at its real, deployed location, then verify the SCRATCH vault's
own copy carries the same edit before running any scratch-vault test.

---

## Implementation Log

**2026-09-02, coder.** Edited the real, live
`Templates/thread/Template.json`'s `## Files` section, adding
`apply_file_review` to `allowed_callers` alongside the two pre-existing
callers (additive, confirmed by direct read before and after). Migrated
`update_files_log_line()` to persist its own unchanged idempotent
line-replace ALGORITHM via `vm.modify_section(..., section="Files",
mode="replace", note_id=<Thread's own real/minted id>,
caller="apply_file_review")` (id-mint-if-missing, mirroring `T01`'s File
precedent, now applied to Threads too, since a real pre-migration Thread
this Skill hasn't already touched via `apply_thread_review.py` may carry
no `id` yet). Migrated `add_file_detail()`'s `## Details` append onto
`vm.modify_section(..., mode="append", ...)`, removing the manual
read-then-concatenate step (the engine's own append mode already merges).
Removed now-fully-dead local primitives after confirming zero remaining
callers by re-reading the whole file:
`insert_body_section_if_missing`/`read_body_section`/
`replace_body_section`/local `merge_tags`/`_format_frontmatter_value`,
plus their own `_CALLER_ALLOW_LISTS`/`_HUMAN_OWNED_HEADERS`/
`_BODY_SECTION_HEADER_PATTERN` guard constants. `read_note`/
`_parse_frontmatter_value` kept (still called by
`build_company_index`/`resolve_companies`/the `source_thread` frontmatter
read). Company resolution untouched.

**Verification (same scratch vault as `T01`,
`.second-brain/data/Templates/thread/Template.json` re-copied from the
real, live vault including this task's own `## Files` edit):**

- `[REQ-SB-88-US-01-AC-01]` **PASS.** Re-ran `T01`'s own scratch scenario
  (same input, no content change): `{"tags_applied":
  ["customer/acme-corp"], "companies_unresolved":
  ["Nonexistent Widgets Co"], "files_log_updated": false}` — print
  contract fully confirmed with the same meaning as today, combined with
  `T01`'s own Summary/tag confirmation.
- `[REQ-SB-88-US-01-AC-03]` **PASS.** With the Thread's `## Files`
  section already carrying `- [[Scratch File 1]] -- Acme renewal
  proposal draft` (from `T01`'s own run): ran with a genuinely different
  `short_summary` ("Acme renewal proposal, revised pricing", companies
  `["Acme Corp"]`) — `files_log_updated: true`, line replaced in place
  (still exactly one line for this file, not two), a fresh Thread `id`
  minted and persisted (`9587f083-a0e5-4616-ae76-ab6ea70afa6e`,
  confirmed on disk — this scratch Thread had never been touched by
  `apply_thread_review.py`, so it carried no `id` before this run).
  Re-ran with the SAME `short_summary`: `files_log_updated: false`, line
  and `id` both unchanged (idempotent, no duplicate line).
- `[REQ-SB-88-US-01-AC-04]` **PASS.** Ran `apply_file_review.py --append`
  with a genuinely new follow-up detail plus one disposable test image
  (`scratch-diagram.png`); confirmed on disk: the image was copied into
  the File's own folder and embedded via `![[scratch-diagram.png]]`
  under `## Details`, `## Summary` byte-unchanged. Ran a SECOND
  `--append` with a different detail and no image: confirmed the first
  pass's own text and image embed were preserved untouched, the new
  detail appended below (never overwritten) — the "repeat calls append
  further points" contract confirmed live across two real passes.
- (Unlabeled, supporting) **PASS.** A disposable throwaway script (not
  this Skill's own entry point) called `vm.modify_section(..., section=
  "Files", ..., caller="some_other_script")` directly against the same
  scratch Thread — refused with a real `VaultManagerError`
  ("section 'Files' in template 'thread' only allows
  ['capture_attachments', 'capture_file_link', 'apply_file_review'] to
  write it -- caller 'some_other_script' is refused"). The identical call
  with `caller="apply_file_review"` succeeded — confirms the
  Template.json edit is genuinely load-bearing, not just present in the
  file.

**Assumptions (scope-internal, for human spot-check):** none beyond
ordinary scratch-fixture construction.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (all three locked ACs
verified live with a real positive result, the Template.json edit is
additive per the architect's own already-resolved finding, no new
dependency/interface change, no ADR touched).
