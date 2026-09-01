---
id: REQ-SB-87-US-03-T05
title: Scratch-vault proving-phase verification, noise-definition retune pass, and cutover
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-03-T04]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03-T05 — Scratch-Vault Proving-Phase Verification, Noise-Definition Retune Pass, and Cutover

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The final closing task: prove the full classify-or-skip + classification
mechanism end-to-end against the real ~100-email scratch-sample proving
phase, demonstrate the noise definition can be retuned without any
Capture-stage code change, confirm Sent+Inbox regression-free, then
participate in the same `--vault-path` cutover `REQ-SB-87-US-02-T05`
performs (this story's own new judgment step rides along with that same
cutover — it is layered onto the SAME `ingest_email.py`, not a separate
deploy).

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T04` complete: noise-definition artifact + derivation, classifier
  profile, the wired relay call, and skip-count reporting all exist and
  individually verify against the scratch sample.

**After / Outputs:**
- A real, disclosed confirmation that the WHOLE mechanism (definition →
  relay call → skip-or-classify → skip-count reporting) works correctly
  end-to-end against the real 100-email sample, including a real retune
  cycle and Sent+Inbox regression check.
- This story's own code changes are included in whatever real, active
  Hermes profile / `--vault-path` cutover `REQ-SB-87-US-02-T05` performs
  (same script, same deploy — no separate cutover action of this story's
  own).

---

## Files to Modify

- None — verification-only, plus (as needed) re-running `T01`'s derivation
  mechanism against real feedback from this pass.

---

## Constraints

- Inherits from parent story.
- Same rollout/verification posture as `REQ-SB-87-US-02`: prove against the
  scratch sample first; the real-vault cutover happens together with that
  sibling story's own `T05`, not independently.
- Never run more than one capture job concurrently against the same vault.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
~100-email sample):**
1. `[REQ-SB-87-US-03-AC-04]` Read the currently-persisted noise-definition
   artifact directly (independent of any capture run); confirm it is real,
   structured, and was genuinely derived (not invented fresh mid-run) —
   cross-check against a capture run's own classify-or-skip decisions to
   confirm they trace back to this SAME persisted content.
2. `[REQ-SB-87-US-03-AC-05]` Deliberately broaden or narrow the noise
   definition (e.g. re-run `T01`'s derivation mechanism with adjusted
   sample/guidance, or a direct, disclosed manual edit for a quick,
   observable test); confirm the VERY NEXT capture run classifies against
   the updated definition, with zero change to any Capture-stage script's
   own code required.
3. `[REQ-SB-87-US-03-AC-06]` Run a full capture pass across the scratch
   sample; confirm real Sent Mail items are still combined with their
   Inbox counterparts into the same Thread exactly as before this story's
   own changes — a real, side-by-side regression check against a
   pre-classification-step baseline capture of the SAME sample (captured
   before `T03`'s edits, kept for comparison).
4. (Unlabeled, closing) Run the full scratch-sample capture one final
   time, end-to-end, confirming all 7 of this story's own locked ACs hold
   together in one real, combined run — not just individually.

**Automated tests:** `n/a — real-vault/scratch-vault verification`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Full end-to-end mechanism confirmed against the real scratch sample
- [ ] Noise-definition retune cycle confirmed with zero code change
- [ ] Sent+Inbox regression-free
- [ ] All 7 locked ACs hold together in one combined real run
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The actual `--vault-path` cutover action itself — performed once,
  jointly, by `REQ-SB-87-US-02-T05` (this story's own code rides along in
  the same `ingest_email.py` file that task cuts over).

---

## Context / Notes

This task exists to give the FULL, combined classify-or-skip mechanism its
own final, honest end-to-end pass, distinct from `T01`-`T04`'s own
individual-capability verifications.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
