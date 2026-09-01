---
id: REQ-SB-87-US-02-T04
title: Verify run_full_capture.py / run_delta_capture.py orchestration contract is unaffected
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-02-T03]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02-T04 — Verify run_full_capture.py / run_delta_capture.py Orchestration Contract Is Unaffected

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Confirm, with real evidence, that `run_full_capture.py`/
`run_delta_capture.py`'s own external CLI contract (arguments, printed
JSON, exit codes, watermark state file) is completely unaffected by
`T01`-`T03`'s migration of the five per-email scripts they orchestrate —
this task makes NO code changes of its own.

---

## Starting State → End State

**Before / Inputs:**
- `run_full_capture.py`/`run_delta_capture.py` invoke `ingest_email.py`,
  `rename_thread.py`, `capture_attachments.py`, `capture_file_link.py`,
  `link_person_to_thread.py` as separate subprocess calls, parsing each
  one's own printed JSON — untouched by `T01`-`T03`, which only edited the
  INTERNALS of those five scripts, never their own CLI arg/stdout/exit-code
  shape.

**After / Outputs:**
- A real, disclosed confirmation that both orchestrators still run
  end-to-end against the migrated per-email scripts, with the exact same
  external contract as before this migration — no code change required or
  made.

---

## Files to Modify

- None — verification only. `run_full_capture.py`/`run_delta_capture.py`'s
  own orchestration logic (paging, watermark, subprocess dispatch) is
  explicitly NOT part of this migration's own `## Files to Modify`, per the
  parent story's own Constraints.

---

## Constraints

- Inherits from parent story.
- Zero code edits in this task.
- Verify against the SAME scratch vault/100-email sample `T01`-`T03` used —
  never the live vault for this task.
- Never run more than one capture job concurrently against the same vault
  during verification.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-02-AC-05]` Run `run_full_capture.py` end-to-end against
   the scratch vault's own real ~100-email sample (or a representative
   subset); confirm it still accepts the same real CLI arguments, still
   prints the same real JSON summary shape, still exits 0 on success, and
   the watermark state file is written/updated in its same real location
   and shape.
2. `[REQ-SB-87-US-02-AC-05]` Run `run_delta_capture.py` once more (a
   second, incremental pass) against the same scratch vault; confirm its
   own watermark-based delta logic still correctly picks up only the
   genuinely new/changed items since the prior run, with the same real
   external contract.
3. (Unlabeled, supporting) Confirm neither orchestrator's own source file
   required any edit to make steps 1-2 pass — a real, observed zero-diff
   confirmation, not just an assumption.

**Automated tests:** `n/a — orchestration verified via real scratch-vault
CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_full_capture.py` external contract confirmed unchanged
- [ ] `run_delta_capture.py` external contract confirmed unchanged,
      including watermark-based delta correctness
- [ ] Zero code edits made in this task
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change to either orchestrator.
- Real-vault cutover — `T05`.

---

## Context / Notes

This task exists specifically to give Scenario 5 ("the live cron-facing
orchestration contract is unaffected") its own dedicated, disclosed
verification pass, separate from the per-script migration tasks, since the
orchestrators themselves are deliberately untouched.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
