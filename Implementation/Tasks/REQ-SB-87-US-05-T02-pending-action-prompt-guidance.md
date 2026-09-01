---
id: REQ-SB-87-US-05-T02
title: Update the Thread-review pass's own prompt guidance for genuine pending-action extraction
parent_story: REQ-SB-87-US-05
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-05-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-05-T02 — Update the Thread-Review Pass's Own Prompt Guidance for Genuine Pending-Action Extraction

## Parent Story

- Story: [[REQ-SB-87-US-05]] — `../UserStories/REQ-SB-87-US-05-enrich-pending-action-extraction.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Extend `summarize-and-tag-threads/SKILL.md`'s own real per-Thread judgment
steps and payload-shape documentation to instruct the agent to identify
genuine pending actions — never a hand-written keyword/regex heuristic,
real agent-prompt reasoning only, matching how it already handles
Summary/company-tagging.

---

## Starting State → End State

**Before / Inputs:**
- `SKILL.md`'s own real "The real per-Thread judgment" section (steps 1-6)
  covers reading the Thread, writing the summary, wiki-tagging companies,
  listing every company genuinely involved, using the specific entity not
  its parent, and writing a short one-line summary. No step addresses
  pending actions at all. Its own "Applying it" section documents the real
  payload shape (`{thread_path, summary, short_summary, companies}`).

**After / Outputs:**
- A new step added to "The real per-Thread judgment" (after step 6, or
  wherever reads most naturally): identify any genuine pending action —
  "a direct question, an unresolved ask, a 'let me know by X'" — by
  reading the WHOLE Thread (not just the newest message), checking whether
  a LATER message already resolved an earlier one before treating it as
  still open, and describing it in the agent's own real words, naming who
  it's waiting on where identifiable. Explicit instruction: **never
  fabricate or write a vague "follow up" placeholder just to have
  something there** — if nothing is genuinely pending, `actions` is
  omitted or left empty.
- The "Applying it" section's own documented payload shape gains the new
  optional `"actions": str` field, with the SAME real-words guidance
  restated inline (mirroring how `"companies"` documents its own expected
  input shape today).
- A note on re-processing: since a re-summarize pass (per the Skill's own
  existing skip rule) re-reads the WHOLE Thread every time, the agent's own
  `actions` value on a re-pass must reflect the CURRENT state — a
  previously-listed item that a new message resolved is dropped, a newly
  arisen one is added — never a blind carry-forward of the prior pass's
  own value.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/SKILL.md`

---

## Constraints

- Inherits from parent story.
- Prompt-only change — no script edits in this task (that was `T01`).
- Never instruct a hand-written keyword/regex heuristic ("look for '?' or
  'please'") — real reasoning over the Thread's own content only.
- Explicit, unambiguous "never fabricate" instruction — Scenario 2's own
  locked requirement.

---

## Tests

**Manual verification steps:**
1. (Unlabeled — prompt content is not independently testable without a
   real LLM call; `T03`'s own live pass is where the judgment quality ACs
   actually verify) Read the finished `SKILL.md`; confirm the new step
   explicitly instructs: (a) reading the whole Thread before judging what's
   pending, (b) checking whether a later message already resolved an
   earlier ask, (c) describing a genuine pending item in the agent's own
   real words, naming who it's waiting on where identifiable, (d) never
   fabricating a placeholder when nothing is genuinely pending, (e)
   reflecting the CURRENT state (drop resolved, add new) on every
   re-summarize pass.
2. Confirm the documented payload shape in "Applying it" now includes
   `"actions"` with matching guidance.

**Automated tests:** `n/a — prompt-only content, verified by direct read
and by `T03`'s own real live agent pass`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] New pending-action judgment step added, matching the guidance above
- [ ] Documented payload shape updated with `"actions"`
- [ ] Explicit never-fabricate instruction present
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any script change — `T01`.
- The real, live proof that the agent actually follows this guidance
  correctly — `T03`.

---

## Context / Notes

Read the real current `SKILL.md` directly before editing (its own "The
real per-Thread judgment" and "Applying it" sections, reproduced in
Starting State above from a 2026-09-01 read) — match its own existing
voice/style (direct, operator-quote-anchored, concrete examples) rather
than introducing a different tone.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
