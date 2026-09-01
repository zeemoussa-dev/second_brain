---
id: REQ-SB-87-US-03-T04
title: Report noise-skip count through the orchestrators' own JSON summary
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T03]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03-T04 — Report Noise-Skip Count Through the Orchestrators' Own JSON Summary

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Add a real, aggregated `skipped_as_noise` count to
`run_full_capture.py`/`run_delta_capture.py`'s own already-real per-page
and final JSON summary, so the operator can always tell why a
captured-email count looks lower than the real mailbox.

---

## Starting State → End State

**Before / Inputs:**
- Real, confirmed current shape (`run_delta_capture.py`, direct read,
  2026-09-01): each per-email loop iteration parses `ingest_email.py`'s own
  returned JSON (`result.get("thread_created")`/`result.get(
  "message_created")`) into `page_threads_created`/`page_messages_created`
  counters, rolled up into `total_threads_created`/`total_messages_created`
  in the final summary dict (`{"status", "pages", "watermark_before",
  "watermark_after", "total_new_emails", "threads_created",
  "messages_created", "attachments_captured", "progress"}`), plus a
  matching per-page entry in `progress`. `run_full_capture.py`'s own real
  shape mirrors this (confirmed by name in the parent story's own
  Constraints; read the real current file directly before editing).

**After / Outputs:**
- Both orchestrators gain a `page_skipped_as_noise` counter (reads `T03`'s
  new `result.get("skipped_as_noise")` field from `ingest_email.py`'s own
  JSON), rolled up into `total_skipped_as_noise` in the final summary dict,
  plus a matching `"skipped_as_noise"` key in each `progress` page entry —
  the SAME aggregation pattern already used for `threads_created`/
  `messages_created`, not a new mechanism.
- The final printed/returned summary's own `skipped_as_noise` count is
  accurate — the sum across every page equals the real number of emails
  the classify-or-skip judgment marked as noise during that run.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/run_delta_capture.py`
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/run_full_capture.py`

---

## Constraints

- Inherits from parent story.
- Mirror the EXACT existing aggregation pattern (`threads_created`/
  `messages_created`) — a new counter variable, incremented per-email,
  rolled into the page entry and the final total, nothing more elaborate.
- Zero change to any other part of either orchestrator's own logic
  (paging, watermark, subprocess dispatch) — this task's own `## Files to
  Modify` is a narrow, disclosed exception to the parent story's own
  Constraint that orchestration logic isn't touched, limited strictly to
  this one new counter.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
~100-email sample with at least one genuine noise email present or
engineered):**
1. `[REQ-SB-87-US-03-AC-07]` Run `run_full_capture.py` (or
   `run_delta_capture.py`) against a scratch sample containing at least
   one email the current noise definition marks as noise; confirm the
   final printed/returned JSON summary includes a `skipped_as_noise` count
   that accurately reflects how many were skipped.
2. (Unlabeled, supporting) Confirm each per-page `progress` entry's own
   `skipped_as_noise` value sums correctly to the final total.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Both orchestrators' own final JSON summary includes an accurate
      `skipped_as_noise` count
- [ ] Per-page `progress` entries include the same count
- [ ] No other orchestration logic changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any other change to either orchestrator.
- The classify-or-skip judgment itself — `T03`.

---

## Context / Notes

Read the real current `run_delta_capture.py`/`run_full_capture.py`
directly before editing (the aggregation shape reproduced in Starting
State above is from a 2026-09-01 read of `run_delta_capture.py`; confirm
`run_full_capture.py`'s own real shape matches closely enough to mirror the
identical pattern, or disclose any real divergence found).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
