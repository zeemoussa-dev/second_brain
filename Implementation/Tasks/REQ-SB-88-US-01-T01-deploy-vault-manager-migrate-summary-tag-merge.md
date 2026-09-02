---
id: REQ-SB-88-US-01-T01
title: Deploy vault_manager.py copy + migrate ## Summary write + tag-merge
parent_story: REQ-SB-88-US-01
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-01-T01 — Deploy vault_manager.py Copy + Migrate ## Summary Write + Tag-Merge

## Parent Story

- Story: [[REQ-SB-88-US-01]] — `../UserStories/REQ-SB-88-US-01-summarize-and-tag-files-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Deploy a fresh `vault_manager.py` copy into `summarize-and-tag-files/scripts/`
(first-time deployment — this Skill has never had one) and migrate
`apply_file_review.py`'s own `## Summary` write and tag-merge call onto it.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `apply_file_review.py` (396 lines, read directly this
  session) has its OWN fully duplicated `read_note`/`merge_tags`/
  `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section` primitives and zero `vault_manager.py` presence.
  `apply_file_review()` currently: resolves companies
  (`resolve_companies`), calls `insert_body_section_if_missing` +
  `replace_body_section(file_path, "## Summary", summary,
  caller=_SUMMARY_CALLER)`, then `merge_tags(file_path, tags)` when any
  company resolved.
- `summarize-and-tag-files/scripts/` has never had a `vault_manager.py`
  copy (confirmed via `Glob`: only `apply_file_review.py`/
  `render_pptx_slide_win32.py` exist there, in both the repo and the real,
  deployed Hermes profile location).
- The real, deployed `file` Template.json (`.second-brain/data/Templates/
  file/Template.json`) already declares `## Summary`/`## Details` as
  `"access": "machine_write"` with **no `allowed_callers` key** — open to
  any machine-write caller today, confirmed directly, zero Template.json
  edit needed for this task.

**After / Outputs:**
- `summarize-and-tag-files/scripts/vault_manager.py` — a fresh copy,
  byte-identical to the canonical, current `Hermes-Provisioning/shared/
  vault_manager.py`.
- `apply_file_review()` now: (1) loads the `file` template once via
  `vm.load_template(vault_path, "file")`; (2) reads the File's own real
  frontmatter via `vm.read_note(file_path)` to get its `id`, minting and
  persisting a fresh `uuid4()` via `vm.update(vault_path, file_path,
  frontmatter={"id": ...})` the first time a File with no `id` is touched
  (same already-proven pattern `REQ-SB-87-US-04-T01` established for
  Threads — real pre-migration File notes carry no `id` yet); (3) writes
  `## Summary` via `vm.modify_section(vault_path, template, section=
  "Summary", content=summary, mode="replace", note_id=<id>,
  caller="apply_file_review")`; (4) merges resolved-company tags via
  `vm.merge_tags(file_path, tags)` instead of the local `merge_tags`.
- Company resolution (`build_company_index`/`resolve_companies`) stays
  entirely hand-written, untouched — real, company-specific business
  logic, not mechanics.
- The Thread's own `## Files` line update (`update_files_log_line`) and
  the `--append` Details pass (`add_file_detail`) are UNTOUCHED by this
  task — `T02`'s own scope.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-files/scripts/apply_file_review.py`
- `Hermes-Provisioning/skills/company-review/summarize-and-tag-files/scripts/vault_manager.py` (new copy, sourced from `Hermes-Provisioning/shared/vault_manager.py`)

---

## Constraints

- Inherits from parent story.
- `build_company_index`/`resolve_companies` stay hand-written, unchanged —
  identical contract to `apply_thread_review.py`'s own copy.
- `update_files_log_line`, `add_file_detail`, `_attach_images`,
  `_unique_sibling_path` stay untouched by THIS task — still use the
  file's own existing local primitives until `T02`.
- Verify against a scratch vault, distinct `--vault-path` — never the real
  vault for this task.
- Never run this Skill concurrently with `capture-files`/
  `email-thread-capture`/`summarize-and-tag-threads` against the same
  vault during verification.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
`file` Template.json copied byte-identical from the real, live vault; a
scratch File note with a real, empty `## Summary` and a real Customer/
Partner hub note pair to resolve against):**

1. `[REQ-SB-88-US-01-AC-01]` Run the migrated `apply_file_review.py`
   against a scratch File note with an empty `## Summary` and a payload
   naming one or more real, resolvable companies; confirm `## Summary` is
   written with the agent-supplied summary content, resolved via a
   freshly-minted `id` (confirmed on disk), and every resolved company's
   `customer/<slug>`/`partner/<slug>` tag is merged onto the File's own
   `tags` via `vm.merge_tags`. (`files_log_updated`'s own print contract
   fully closes out at `T02` — this step confirms the Summary/tag half.)
2. `[REQ-SB-88-US-01-AC-02]` Include a company name in the payload that
   does not match any real Customer/Partner hub note; confirm it is
   reported in `companies_unresolved` and no hub note is fabricated
   (`resolve_companies` untouched by this task, exercised here end-to-end).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Fresh `vault_manager.py` copy deployed to
      `summarize-and-tag-files/scripts/`
- [x] `## Summary` write migrated onto `vm.modify_section`,
      `caller="apply_file_review"`, resolved via a real/minted `id`
- [x] Tag-merge migrated onto `vm.merge_tags`
- [x] Company resolution (`build_company_index`/`resolve_companies`)
      byte-for-byte unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Thread `## Files` line update, `--append` Details pass — `T02`.
- Real-vault retrofit verification — `T03`.
- Cron job provisioning — `T04`.

---

## Context / Notes

`architecture.md` → `§Files-Skill vault_manager.py Migration + Cron
Provisioning (REQ-SB-88-US-01)` and `ADR-017` are authoritative. Read the
real current `apply_file_review.py` directly before editing (reproduced
in Starting State above from this session's own read). Mirrors
`REQ-SB-87-US-04-T01`'s already-proven shape (id-mint-if-missing, then
`modify_section`) adapted for the File template.

---

## Implementation Log

**2026-09-02, coder.** Deployed a fresh, byte-identical copy of the
canonical `Hermes-Provisioning/shared/vault_manager.py` into
`summarize-and-tag-files/scripts/vault_manager.py` (this Skill's first
copy ever). Migrated `apply_file_review()`'s `## Summary` write and tag
merge onto `vm.modify_section(..., section="Summary", mode="replace",
note_id=<real/minted id>, caller="apply_file_review")` and
`vm.merge_tags`, mirroring `apply_thread_review.py`'s own
`REQ-SB-87-US-04-T01` precedent exactly (id-mint-if-missing via
`vm.update`, then `modify_section`). `build_company_index`/
`resolve_companies` untouched. `update_files_log_line`/`add_file_detail`
still use the file's own local primitives, unchanged (T02 scope).
Removed the now-dead `_SUMMARY_CALLER` entry from `_CALLER_ALLOW_LISTS`
(the old local `replace_body_section("## Summary", ...)` call site it
gated is gone) — a scope-internal, in-file cleanup of a name this same
edit made dead, not a broader dead-code sweep (that's T02/T03's own
scope for the Files-log/Details primitives).

**Verification (scratch vault at
`<scratchpad>/sb85-us01-vault`, `.second-brain/data/Templates/file`+
`thread` Template.json copied byte-identical from the real, live vault;
one scratch Customer hub note `Acme Corp` with `aliases: ["Acme"]`; one
scratch Thread `Scratch Thread A` with a bare `- [[Scratch File 1]]`
`## Files` line; one scratch File `Scratch File 1` with empty
`## Summary`/`## Details` and `source_thread: "[[Scratch Thread A]]"`).
Ran the real, deployed `apply_file_review.py` (venv Python,
`src/backend/.venv/Scripts/python.exe`) against a payload naming
`["Acme Corp", "Nonexistent Widgets Co"]`:**

- `[REQ-SB-88-US-01-AC-01]` **PASS.** Run 1: output
  `{"tags_applied": ["customer/acme-corp"], "companies_unresolved":
  ["Nonexistent Widgets Co"], "files_log_updated": true}`. Confirmed on
  disk: `## Summary` written with the exact agent-supplied text; a fresh
  `id` (`f3a5bd44-74f2-4948-86db-07905b55dfbf`) minted and persisted to
  frontmatter; `tags` gained `customer/acme-corp` via `vm.merge_tags`
  (existing `kind/file` tag preserved, not overwritten). Run 2 (same
  input): output `files_log_updated: false`, `## Summary` still exactly
  one copy of the same text (no duplication, `mode="replace"` confirmed
  live), the SAME `id` reused (no second uuid minted, confirmed by
  reading the file's frontmatter directly before/after), `tags` unchanged
  (no duplicate tag entry). Print contract's `tags_applied`/
  `companies_unresolved` half confirmed with the same meaning as today;
  `files_log_updated`'s own full contract closes out at `T02`, per this
  task's own Tests note — its value was directly observed here too
  (`true` then `false`) since `update_files_log_line` (T02 scope, still
  on its old local primitives) ran unmodified end-to-end as a side
  effect of this same real script invocation.
- `[REQ-SB-88-US-01-AC-02]` **PASS.** `"Nonexistent Widgets Co"` (no
  matching Customer/Partner hub note) reported in `companies_unresolved`
  on every run; no hub note was fabricated (confirmed:
  `Work/Customers/`/`Work/Partners/` under the scratch vault gained no
  new folder/file).

**Assumptions (scope-internal, for human spot-check):** none beyond
ordinary scratch-fixture construction — the scratch File/Thread/Customer
shapes were built directly from this task's own Starting State and the
real, deployed Template.json files, not guessed.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (both locked ACs
verified live with a real positive result, no new dependency/interface
change, no ADR touched, no contradictory inputs).
