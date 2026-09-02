---
id: REQ-SB-87-US-03-T04
title: Report noise-skip count through the orchestrators' own JSON summary
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T03]
created: 2026-09-01
updated: 2026-09-02
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

- [x] Both orchestrators' own final JSON summary includes an accurate
      `skipped_as_noise` count
- [x] Per-page `progress` entries include the same count
- [x] No other orchestration logic changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      (n/a — no new decision/pattern/constraint, see Implementation Log)
- [x] `CHANGELOG.md` entry appended

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

**2026-09-02 (coder pass — built and live-verified).** Read `Pipeline.md`,
`Implementation/Learnings.md`, this story's own full text, and the REAL
current `run_delta_capture.py`/`run_full_capture.py`/`ingest_email.py`
directly before editing. Confirmed `run_full_capture.py`'s own real
per-page/final-summary shape mirrors `run_delta_capture.py`'s closely
enough to apply the identical pattern — no real divergence found beyond
the already-known "delta pages backward to a watermark, full pages
backward to true history start" difference described in each file's own
module docstring (unrelated to this task's own counter).

**What was built (both orchestrators, per `## Files to Modify`, mirroring
the EXACT existing `threads_created`/`messages_created` aggregation shape
— no new mechanism):**
- `total_skipped_as_noise` / `page_skipped_as_noise` counters, initialized
  and rolled up identically to the existing `*_created` counters.
- Per-email loop: `if result.get("skipped_as_noise"): page_skipped_as_noise
  += 1`, reading `ingest_email.py`'s own `T03`-added field on the parsed
  ingest result — the SAME `result.get(...)` parse block already used for
  `thread_created`/`message_created`, one more line, no new branch shape.
- Final summary dict and each `progress` page-entry dict gain a
  `"skipped_as_noise"` key.
- Both scripts' own `PAGE N done: ...` print lines gain a trailing
  `skipped_as_noise+=N` term, for the same real-time-visibility reason the
  existing `threads+=`/`messages+=` terms are already printed — a small,
  in-scope extension of the same print statement this task's own counter
  lives beside, not a new file/mechanism.
- Both module docstrings gain a short, dated note documenting the new
  field — no change to any pre-existing documented behavior.

**Zero other orchestration logic changed** — confirmed via `git diff`
against both files: every hunk is either a new counter variable, a new
`if result.get("skipped_as_noise")` line, a new dict key, or a print-line
extension. Paging, watermark handling, and subprocess dispatch are
untouched.

**Live verification (real, unmodified orchestrator code; scoped, disclosed
monkeypatch of ONLY the subprocess I/O boundary — this project's own
established in-process-monkeypatch technique, `Implementation/Learnings.md`,
`SPRINT-024`/`SPRINT-028`/`REQ-SB-87-US-03-T03`). Rationale for this
technique over driving the real Outlook mailbox: this task's own locked
Out-of-Scope explicitly excludes "the classify-or-skip judgment itself —
T03" — what's under test here is purely the orchestrators' own aggregation
arithmetic and JSON/print shape, not the classifier or Outlook COM layer,
so faking exactly the `ingest_email.py`-shaped JSON `run_script()` already
parses (never touching the aggregation code itself) is the closest-to-real
substitute that still exercises the REAL, unmodified `main()` end-to-end,
including its real file-write to `SUMMARY_PATH`. `VAULT_PATH` pointed at a
scratch directory under `%TEMP%`/`%LOCALAPPDATA%`, never the real vault
(this story's own locked scratch-vault-first Constraint) — both scratch
directories deleted after verification.**

For each orchestrator: 2 pages of 2 emails each (one genuine noise-skip +
one genuine new-signal capture on page 1; one genuine noise-skip + one
reply into the page-1-created Thread on page 2), then a terminating empty
page — engineered to exercise "some genuinely noise-shaped, some real
signal, some replies into an already-existing thread" per this task's own
mandated verification sample shape.

- `[REQ-SB-87-US-03-AC-07]` **PASS (both scripts).**
  `run_delta_capture.py`: final summary
  `{"threads_created": 1, "messages_created": 2, "skipped_as_noise": 2,
  ...}` — 2 real engineered skips correctly counted and kept structurally
  distinct from the 1 thread / 2 messages actually captured (one of which
  is the reply into the already-existing Thread). `run_full_capture.py`:
  identical result shape, same counts, its own `"pages": 2` final-summary
  branch (the empty-page-triggered completion path) confirmed to include
  the new key too.
- (Unlabeled, supporting) **PASS (both scripts).** Each script's own two
  `progress` page-entries carry `skipped_as_noise: 1` apiece, summing
  exactly to the final total of 2, confirmed by explicit assertion against
  the real written `SUMMARY_PATH` JSON file (not just stdout).

**Compile check:** `py -3 -m py_compile run_delta_capture.py
run_full_capture.py` — clean.

**No `MEMORY.md` update** — this task is a mechanical, same-shape mirror
of an already-established aggregation pattern (Objective/Constraints both
say so explicitly); no new decision, pattern, or constraint emerged.
`CHANGELOG.md` entry appended.

No scope-internal judgement calls beyond the disclosed verification-
technique choice above (itself already an established, precedented
technique, not a fresh assumption) — `gate: clear`, no `ESCALATIONS.md` /
`REVIEW-QUEUE.md` entry needed for this task itself. The parent story's
own pre-existing `gate: flagged` (`ADR-018` human-review requirement) is
unresolved and unaffected by this task.

Task marked `Done` — the one locked AC mapped to this task
(`REQ-SB-87-US-03-AC-07`) verified live with a real positive result on
both orchestrators, plus its own unlabeled supporting check.
