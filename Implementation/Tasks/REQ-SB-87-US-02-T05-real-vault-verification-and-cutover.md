---
id: REQ-SB-87-US-02-T05
title: Real-vault retrofit-safety verification and live cron cutover
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-02-T04]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02-T05 — Real-Vault Retrofit-Safety Verification and Live Cron Cutover

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The one and only task that (a) proves the fully-migrated `email-thread-capture`
Skill is retrofit-safe against the real, already-populated vault, and (b)
performs the actual production cutover — pointing the live
`email-delta-capture` cron job's own `--vault-path` at the real vault — per
the operator's own already-locked rollout decision.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T04` have all passed against the scratch vault / real ~100-email
  sample. The migrated scripts are the SAME code path regardless of
  target — no separate "test mode" branch; the cutover IS the
  `--vault-path` argument change, not a redeploy or a code branch (parent
  story's own Constraints).
- The real vault's own already-captured Threads, RawMessages, Person notes,
  and file companions predate this migration.

**After / Outputs:**
- A real, disclosed confirmation that the migrated scripts, run against the
  REAL vault, find and correctly top up every already-existing note — no
  duplicate created, no existing content lost or overwritten.
- The live `email-delta-capture` cron job's own `--vault-path` argument
  now points at the real vault (the actual cutover act).
- The migrated scripts are deployed to the real, active Hermes profile
  location(s) this Skill is actually running from (not only the
  `Hermes-Provisioning/` repo copies).

---

## Files to Modify

- None new — this task deploys the already-migrated files (from `T01`-`T03`)
  to the real, active Hermes profile location, and updates the live cron's
  own `--vault-path` argument (a scheduler/task-definition change, not a
  script-source edit).

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T04` have all already passed
  against the scratch sample** — Scenario 6's own real-vault check happens
  AFTER the scratch-sample proving phase, immediately before cutover, never
  instead of it.
- Never run more than one capture job concurrently against the real vault
  during this verification.
- Deploy to the real, active Hermes profile location(s), per this
  project's own standing manual-deploy pattern.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-02-AC-06]` Run the fully-migrated `ingest_email.py`
   (and, as applicable, `rename_thread.py`/`capture_attachments.py`/
   `capture_file_link.py`/`link_person_to_thread.py`) against the REAL,
   live vault for a small, real, already-known set of Threads/messages
   (re-ingesting already-captured `message_id`s is safe, per Scenario 2's
   idempotency). Confirm every already-existing Thread/RawMessage/Person/
   File note is found and topped up correctly — no duplicate created, no
   existing content lost or overwritten. Spot-check at least one Thread
   that has an existing `## Related` entry, one with a file companion, and
   one whose directory is already renamed to `"<date> <subject>"`.
2. (Unlabeled, supporting) Confirm the deployed scripts at the real, active
   Hermes profile location match the fully-migrated repo copies exactly
   (byte-for-byte, or functionally — coder's disclosed choice).
3. `[REQ-SB-87-US-02-AC-05]` Re-confirm (one final time, against the REAL
   vault, not just the scratch sample) that `run_delta_capture.py`'s own
   external contract (arguments, JSON, exit code, watermark file) is
   unaffected.
4. **Cutover action:** update the live `email-delta-capture` cron job's own
   `--vault-path` argument to point at the real vault (if it does not
   already, e.g. if this Skill was previously being run manually against a
   scratch path during the proving phase). Confirm the next scheduled or
   manually-triggered run succeeds against the real, live vault.

**Automated tests:** `n/a — real-vault verification, by definition, is not
run against an isolated test fixture`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Real-vault retrofit-safety confirmed — no duplicate, no lost/
      overwritten content
- [ ] Migrated scripts deployed to the real, active Hermes profile location
- [ ] Live cron's own `--vault-path` points at the real vault (cutover
      complete)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any further code change — this task is verification + deployment +
  cutover only, building on `T01`-`T04`'s already-complete migration.

---

## Context / Notes

Operator's own real rollout decision (verbatim, `REQ-SB-87-US-02`'s own
Notes): *"Lets Build a small sample of 100 Emails to a new Pipeline we keep
tweaking it when done we change the OutputDirectory and move on."* This
task is that "change the OutputDirectory and move on" step.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
