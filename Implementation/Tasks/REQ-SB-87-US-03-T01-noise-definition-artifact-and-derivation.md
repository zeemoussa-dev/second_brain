---
id: REQ-SB-87-US-03-T01
title: Noise-definition artifact + out-of-band derivation mechanism
parent_story: REQ-SB-87-US-03
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-03-T01 — Noise-Definition Artifact + Out-of-Band Derivation Mechanism

## Parent Story

- Story: [[REQ-SB-87-US-03]] — `../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Create the real, structured, persisted noise-definition artifact under the
vault's own `.second-brain/data/` tree, plus a genuinely separate,
out-of-band derivation mechanism to (re)generate it — per `ADR-018`'s
Decision.

---

## Starting State → End State

**Before / Inputs:**
- No noise-definition artifact exists anywhere.
- `ADR-018`: the artifact is a real, structured, persisted file under
  `.second-brain/data/` (a new sibling to `Templates/`), never a
  Skill-`scripts/`-folder file, never baked into a profile's static system
  prompt — every Capture script already receives `--vault-path`, so it
  reads with zero deploy step.

**After / Outputs:**
- `.second-brain/data/EmailCapture/noise_definition.json` (exact path —
  this task's own naming call, matching `ADR-018`'s illustrative example):
  a real, structured JSON document describing what content counts as
  "noise" — e.g. a list of natural-language rules/criteria (not a
  hand-written keyword list — the definition's own CONTENT is LLM-derived
  prose/criteria, per PRD point 7's prompt-driven-not-hardcoded-heuristic
  principle; only the FILE FORMAT/persistence mechanism is this task's own
  mechanical code).
- A derivation mechanism — a new, standalone script (e.g.
  `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/
  derive_noise_definition.py`, or an equivalent out-of-band process; this
  task's own naming/shape call) that:
  - Takes a real sample of email content (e.g. a batch pulled via the
    already-real `list_recent_emails.py`/`run_full_capture.py` paging, or a
    hand-curated set for the initial derivation).
  - Invokes real LLM reasoning (a one-shot `hermes -p <profile> chat -q
    "..."` relay call, or an interactive Hermes session — this task's own
    disclosed choice; either is legitimate per `ADR-018`'s own "a dedicated
    one-off script, a live interactive Hermes agent session" allowance) to
    derive/refine the noise definition's own real content from that
    sample.
  - Writes/overwrites the persisted artifact above.
  - Is invoked ON-DEMAND only (e.g. during the 100-email scratch-sample
    proving phase, and again whenever the operator wants to retune it) —
    NEVER auto-triggered from inside the recurring capture tick.

---

## Files to Modify

- `.second-brain/data/EmailCapture/noise_definition.json` (new, initial
  content — a real, first derivation, not a placeholder).
- A new derivation script (path per the coder's own disclosed choice,
  documented in the Implementation Log).

---

## Constraints

- Inherits from parent story.
- **Prompt-driven, minimal code (PRD point 7):** the definition's own
  CONTENT comes from real LLM reasoning over real sample content — never a
  hand-written keyword/sender heuristic invented directly in this task's
  own code.
- The artifact must be plainly readable/inspectable independently of any
  capture run (a plain JSON file, human- and script-readable).
- Derivation is decoupled from the recurring 30-minute capture tick — never
  triggered automatically from inside `ingest_email.py`/
  `run_delta_capture.py`.
- No change to any Capture-stage script's own code is required to re-tweak
  the definition's content — only the artifact file itself changes.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-03-AC-04]` Run the derivation mechanism once against a
   real sample of email content (or a representative curated set); confirm
   `.second-brain/data/EmailCapture/noise_definition.json` is written with
   real, structured, genuinely LLM-derived content (not a placeholder, not
   a hand-written keyword list). Read the file directly, independently of
   any capture run, and confirm it is inspectable/legible.
2. (Unlabeled, supporting) Re-run the derivation mechanism a second time
   with a genuinely different sample; confirm the artifact's content
   updates to reflect the new derivation (proves it isn't a one-time,
   frozen file).

**Automated tests:** `n/a — no existing pytest harness for this Skill; the
artifact's own content is LLM-derived, not deterministic code output`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Noise-definition artifact exists at a real, structured,
      `.second-brain/data/`-tree path
- [ ] A genuinely separate, out-of-band derivation mechanism exists and
      produces real, LLM-derived content
- [ ] Derivation never auto-triggers from the recurring capture tick
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Provisioning the classifier Hermes profile that CONSUMES this artifact
  at capture time — `T02`.
- Wiring the classify-or-skip relay call into `ingest_email.py` — `T03`.
- The real 100-email scratch-sample proving-phase RETUNE pass — `T05` (this
  task's own derivation run only needs to prove the mechanism works, not
  perform the final production-quality tune).

---

## Context / Notes

`ADR-018` (`Implementation/Architecture/ADR.md`) — read the full Decision
and "Alternatives Considered" (the rejected static-system-prompt option)
before implementing.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
