---
id: REQ-SB-88-US-01-T03
title: Scratch-vault proving-phase verification + real-vault retrofit check
parent_story: REQ-SB-88-US-01
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-88-US-01-T02]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-01-T03 — Scratch-Vault Proving-Phase Verification + Real-Vault Retrofit Check

## Parent Story

- Story: [[REQ-SB-88-US-01]] — `../UserStories/REQ-SB-88-US-01-summarize-and-tag-files-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

The one task that proves the fully-migrated `apply_file_review.py` is
retrofit-safe against a real, already-summarized captured File, deploys the
migrated script to the real, active Hermes profile location, and confirms the
real Thread Template.json edit is live there too — the last checkpoint before
`T04` provisions the cron job against real data.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T02` complete and individually verified against a scratch vault.
- The real, active Hermes profile location for this Skill
  (`profiles/files-manager/skills/company-review/summarize-and-tag-files/
  scripts/`) still holds only the OLD, pre-migration `apply_file_review.py`
  and no `vault_manager.py` copy (confirmed live this session).
- The real vault's own `Templates/thread/Template.json` needs `T02`'s own
  `## Files` `allowed_callers` edit applied at its real, live location
  (`T02` edits it directly — this task confirms it's actually there, not
  a scratch-only copy).

**After / Outputs:**
- A real, disclosed confirmation that the migrated script, run against a
  real, already-summarized captured File with the SAME summary/
  short_summary/companies it already carries, leaves its `## Summary`,
  tags, and parent Thread's `## Files` line all byte-identical.
- The migrated `apply_file_review.py` + the new `vault_manager.py` copy
  deployed to the real, active Hermes profile location.

---

## Files to Modify

- None new — deployment of the already-migrated files from `T01`-`T02` to
  the real, active Hermes profile location. No further code changes.

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T02` have both already passed
  against a scratch sample** — the real-vault check happens immediately
  before deployment, never instead of scratch-vault proving.
- Never run this Skill concurrently with `capture-files`/
  `email-thread-capture`/`summarize-and-tag-threads` against the same
  vault during verification.
- Read-then-compare technique only against the real vault — snapshot
  before, run, diff after; no fabricated judgment content is ever written
  for a real File this task doesn't already have a real prior summary for.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-88-US-01-AC-05]` Pick a real, already-summarized captured File
   (non-empty `## Summary`, at least one resolved company tag, and a
   parent Thread whose `## Files` line already carries its
   `short_summary`). Snapshot the File note, its parent Thread note, and
   the File's own frontmatter tags to the scratchpad before running
   anything. Build an `--input-file` payload reusing that File's own
   already-applied `summary`/`short_summary`/`companies` verbatim (read
   directly off its current `## Summary` and the Thread's own `## Files`
   line). Run the newly-deployed, migrated `apply_file_review.py` against
   the real vault. Confirm on disk: `## Summary`, tags, and the parent
   Thread's `## Files` line are all byte-identical before/after — no
   content lost, no duplicate tag, no duplicate log line.
2. (Unlabeled, supporting) Confirm the deployed script + `vault_manager.py`
   copy at the real, active Hermes profile location are byte-identical to
   the fully-migrated repo copies (`Compare-Object`).
3. (Unlabeled, supporting) Confirm the real, live `Templates/thread/
   Template.json`'s `## Files` `allowed_callers` array includes
   `apply_file_review` alongside the two pre-existing callers (this is
   `T02`'s own edit — confirm it's present at the real, live path, not
   just a scratch copy).

**Automated tests:** `n/a — real-vault verification is not run against an
isolated fixture, by definition`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Real-vault retrofit-safety confirmed — an already-summarized File's
      `## Summary`, tags, and parent Thread `## Files` line are all left
      byte-identical on a forced re-run with the same content
- [x] Migrated script + `vault_manager.py` deployed to the real, active
      Hermes profile location
- [x] Real, live Thread Template.json confirmed to carry `T02`'s own
      `## Files` `allowed_callers` edit
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any further code change.
- Cron job provisioning / real-backlog processing — `T04`.

---

## Context / Notes

Mirrors `REQ-SB-87-US-04-T04`'s own real-vault retrofit-check shape
(read-then-compare, snapshot-before, bounded to already-known real
content — no genuinely new judgment performed by this task).

---

## Implementation Log

**2026-09-02, coder.** Concurrency check performed before touching the
real vault: confirmed `REQ-SB-87-US-02-T05` (the sibling email-thread-
capture real-vault retrofit + cron cutover) is still `status: Ready`
(not started), the `email-delta-capture` cron job is `enabled: false`/
`paused`, and no `capture-files`/`email-thread-capture`/`summarize-and-
tag-threads`/`apply_thread_review`/`ingest_email` process was running
(`Get-CimInstance Win32_Process` scan, zero matches). No other real-vault
job was imminent (`create-companies-partners`/`new-company-discovery`
both several hours out). Proceeded with this task's own single real-vault
touch, sequenced alone (not concurrent with `REQ-SB-88-US-02-T03`'s own
later real-vault touch).

**Real-vault retrofit-safety check
(`[REQ-SB-88-US-01-AC-05]`):** picked a real, already-summarized captured
File: `Work/Threads/2026-07-20 Masdar Presentation Intial Idea/files/
2026-07-20 f4b90f65-Core42_Masdar_DataLake.pptx/2026-07-20 f4b90f65-
Core42_Masdar_DataLake.pptx.md` (non-empty `## Summary`, tags
`partner/core42`/`customer/masdar`/`partner/presight`, parent Thread's
own `## Files` line already `- [[2026-07-20 f4b90f65-Core42_Masdar_
DataLake.pptx]] -- Core42_Masdar_DataLake.pptx`). Snapshotted both the
File note and its parent Thread note to the scratchpad before running
anything. Built an `--input-file` payload reusing the File's own
already-applied `summary` (read verbatim off its current `## Summary`,
byte-for-byte via a Python read, not retyped), `short_summary`
(`"Core42_Masdar_DataLake.pptx"`, off the Thread's own `## Files` line),
and `companies` (`["Core42", "Masdar", "Presight"]`, the real hub notes'
own `name` frontmatter values whose stems slugify to the File's existing
`core42`/`masdar`/`presight` tags). Ran the newly-deployed, migrated
`apply_file_review.py` against the REAL vault:
`{"tags_applied": ["partner/core42", "customer/masdar",
"partner/presight"], "companies_unresolved": [], "files_log_updated":
false}`. **PASS.** Confirmed on disk via direct `diff` against the
snapshots: the Thread note is byte-IDENTICAL, zero diff (`files_log_
updated: false` — no change needed since the line already matched). The
File note's `## Summary` and `tags` are byte-identical; the ONLY diff is
one new frontmatter line, `id: "bcbe5e0a-2c95-4a57-8eb2-a4cce07c08f8"` —
the disclosed, expected id-mint-if-missing side effect of this migration
touching a real File for the first time, not a content change. This is
the exact same accepted shape `REQ-SB-87-US-04-T04`'s own real-vault
retrofit check already established and locked as the precedent for
"byte-identical" scoped to Summary/tags/Files-line, not the whole
frontmatter block (a fresh `id` is expected on first migrated touch).

**Deployment + Template.json confirmation:** copied the fully-migrated
`apply_file_review.py` and `vault_manager.py` from the repo to the real,
active Hermes profile location (`C:\Users\<operator>\AppData\Local\
hermes\profiles\files-manager\skills\company-review\summarize-and-tag-
files\scripts\`), which previously held only the pre-migration script and
no `vault_manager.py` copy at all (confirmed via `Compare-Object` before
the copy). Re-ran `Compare-Object`/`diff` after: both files
byte-identical to the repo copies. Confirmed the real, live `Templates/
thread/Template.json`'s `## Files` `allowed_callers` array is
`["capture_attachments", "capture_file_link", "apply_file_review"]` at
its real, live path (this is `T02`'s own edit, live-confirmed here as
the last checkpoint before `T04`).

**Assumptions (scope-internal, for human spot-check):** none — the real
File/Thread/company data used were read directly, never guessed.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (the one locked AC
this task owns verified live with a real positive result against real
vault data, no new dependency/interface change, no ADR touched, the
concurrent-write constraint was explicitly checked and respected).
