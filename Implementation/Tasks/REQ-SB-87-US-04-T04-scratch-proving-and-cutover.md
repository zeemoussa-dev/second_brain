---
id: REQ-SB-87-US-04-T04
title: Scratch-vault proving-phase verification, real-vault retrofit check, and cutover
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-04-T03]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T04 — Scratch-Vault Proving-Phase Verification, Real-Vault Retrofit Check, and Cutover

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The one task that proves the fully-migrated `apply_thread_review.py` is
retrofit-safe against the real, already-populated vault, then deploys and
cuts the live `job4-summarize-tag-threads` cron job's own `--vault-path`
over to the real vault.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T03` complete and individually verified against a scratch vault.
- The real vault's own already-summarized AND not-yet-summarized Threads
  predate this migration (a real, confirmed coverage gap exists for at
  least one Thread never processed by `job4` at all — see the parent
  story's own Notes; not this task's job to close).

**After / Outputs:**
- A real, disclosed confirmation that the migrated script, run against the
  REAL vault, correctly tops up every already-existing Thread per the
  Skill's own `last_summarized_at`-based skip rule — no duplicate log
  entries, no lost tags, no already-correct `## Summary` overwritten with
  something different for an unchanged Thread.
- The migrated script deployed to the real, active Hermes profile
  location `job4-summarize-tag-threads` actually runs from.
- The live `job4` cron job's own `--vault-path` now points at the real
  vault (the cutover act).

---

## Files to Modify

- None new — deployment + cutover of the already-migrated file from
  `T01`-`T03`.

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T03` have all already passed
  against a scratch sample** — the real-vault check happens immediately
  before cutover, never instead of scratch-vault proving.
- Never run `job4` concurrently with itself, or with
  `email-thread-capture`, against the same vault during verification.
- Deploy to the real, active Hermes profile location, per this project's
  own standing manual-deploy pattern.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-04-AC-07]` Run the fully-migrated `apply_thread_review.py`
   against the REAL, live vault for a small, real set of already-known
   Threads — at least one already `last_summarized_at`-stamped (should be
   SKIPPED, or if forced to re-run, should not duplicate log entries or
   silently change an already-correct `## Summary`) and, if a real
   never-yet-summarized Thread genuinely exists (per the disclosed
   coverage-gap note), one of those too (should be processed for the first
   time, correctly). Confirm no duplicate log entries, no lost tags, no
   unwanted overwrite.
2. (Unlabeled, supporting) Confirm the deployed script at the real, active
   Hermes profile location matches the fully-migrated repo copy.
3. **Cutover action:** point the live `job4-summarize-tag-threads` cron
   job's own `--vault-path` at the real vault (if not already). Confirm
   the next scheduled or manually-triggered run succeeds against the real,
   live vault.

**Automated tests:** `n/a — real-vault verification is not run against an
isolated fixture, by definition`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Real-vault retrofit-safety confirmed — the existing skip rule
      correctly gates every already-processed Thread, no duplicates, no
      lost content
- [ ] Migrated script deployed to the real, active Hermes profile location
- [ ] Live cron's own `--vault-path` points at the real vault (cutover
      complete)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Backfilling/re-running `job4` against Threads it has never processed —
  a real, disclosed, separate coverage gap, not this task's own job to
  close (see the parent story's own Notes).
- Any further code change.

---

## Context / Notes

Same rollout precedent as `REQ-SB-87-US-02-T05` — the PRD's own
raised-context point 2 confirms the 100-email scratch-sample proving-phase
approach applies to this whole requirement, not just Capture-side stories.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
