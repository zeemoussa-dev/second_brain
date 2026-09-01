---
id: REQ-SB-87-US-05-T03
title: Scratch-vault proving-phase verification (real live agent pass)
parent_story: REQ-SB-87-US-05
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-05-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-05-T03 — Scratch-Vault Proving-Phase Verification (Real Live Agent Pass)

## Parent Story

- Story: [[REQ-SB-87-US-05]] — `../UserStories/REQ-SB-87-US-05-enrich-pending-action-extraction.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Run the fully-built pending-action extraction mechanism (`T01`'s
mechanical write path + `T02`'s prompt guidance) as a real, live
`summarize-and-tag-threads` agent pass against real Thread content in a
scratch vault, proving the judgment-quality ACs a mechanical test alone
cannot: no fabrication, resolved items dropped, current-state reflected on
re-processing.

---

## Starting State → End State

**Before / Inputs:**
- `T01` (mechanical write) and `T02` (prompt guidance) both complete and
  individually verified.

**After / Outputs:**
- A real, disclosed, live-verified confirmation that the whole mechanism
  works end-to-end: a genuinely pending item gets written, a purely
  informational Thread gets nothing fabricated, an already-resolved item
  is dropped, a re-processed Thread reflects the current real state, and
  `## Personal Notes` stays untouched throughout.

---

## Files to Modify

- None — verification only, same rollout posture as `REQ-SB-87-US-04-T04`
  (prove against a scratch-vault sample before this capability rides along
  in the next real `job4` cutover).

---

## Constraints

- Inherits from parent story.
- Real live agent session(s) against real or scratch-copied Thread
  content — a hand-constructed payload alone (as `T01` used) is not
  sufficient here; this task specifically needs genuine agent judgment.
- Never run `job4` concurrently with itself or `email-thread-capture`
  against the same vault during verification.

---

## Tests

**Manual verification steps (scratch vault, real Thread content — either
copied-from-real or a real, disposable scratch Thread engineered for each
specific case):**
1. `[REQ-SB-87-US-05-AC-01]` Run a real, live `summarize-and-tag-threads`
   pass against a Thread whose messages genuinely contain a still-pending
   ask (a direct question, an unresolved request, a "let me know by X").
   Confirm that pending item is written into `## Actions`, in the agent's
   own real words, naming who it's waiting on where identifiable.
2. `[REQ-SB-87-US-05-AC-02]` Run the same pass against a purely
   informational Thread (an FYI, a closed/resolved item, a notification)
   with nothing genuinely pending. Confirm `## Actions` is left empty — no
   fabricated or vague "follow up" placeholder.
3. `[REQ-SB-87-US-05-AC-03]` Run against a Thread where an earlier message
   asks something and a LATER message in the SAME thread already
   answers/resolves it. Confirm that resolved item is NOT written into
   `## Actions` as if still open.
4. `[REQ-SB-87-US-05-AC-04]` Confirm the existing skip rule
   (`last_summarized_at >= last_message_at`) still applies — an
   already-reviewed Thread with a real `## Actions` entry and no new
   message since is skipped by a later pass, `## Actions` not re-written
   or duplicated.
5. `[REQ-SB-87-US-05-AC-05]` Take a Thread with an existing `## Actions`
   entry, add a genuinely new message that resolves it (or adds a further
   pending item), and re-run the review pass. Confirm `## Actions`
   reflects the CURRENT real state — the resolved item is gone, any new
   genuine pending item is present.
6. `[REQ-SB-87-US-05-AC-06]` Confirm `## Personal Notes` is untouched
   across every run above (compare before/after content for each Thread
   used).

**Automated tests:** `n/a — real, live agent judgment verification`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] All 6 locked ACs verified live with a real positive result
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code or prompt change — this task is verification-only, building on
  `T01`/`T02`.
- The actual live-cron cutover for this capability — it rides along with
  `REQ-SB-87-US-04-T04`'s own cutover (same script, same deploy), not a
  separate cutover of this story's own.

---

## Context / Notes

This is the closing task for `REQ-SB-87-US-05` — once all 6 locked ACs
verify clean here, the story's own Definition of Done is satisfied.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
