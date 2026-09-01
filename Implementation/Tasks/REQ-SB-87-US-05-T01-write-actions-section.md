---
id: REQ-SB-87-US-05-T01
title: Accept an actions payload field + write ## Actions (replace-mode, apply_thread_review caller)
parent_story: REQ-SB-87-US-05
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

# REQ-SB-87-US-05-T01 — Accept an `actions` Payload Field + Write `## Actions` (Replace-Mode, `apply_thread_review` Caller)

## Parent Story

- Story: [[REQ-SB-87-US-05]] — `../UserStories/REQ-SB-87-US-05-enrich-pending-action-extraction.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Extend `apply_thread_review.py`'s own input payload shape to accept an
already-agent-decided `actions` field, and mechanically write it into the
Thread's own `## Actions` section through the SAME migrated
`vault_manager.modify_section` call path `REQ-SB-87-US-04` built for `##
Summary` — mode `replace`, caller `apply_thread_review`.

---

## Starting State → End State

**Before / Inputs:**
- Post-`REQ-SB-87-US-04`: `apply_thread_review.py`'s real payload shape is
  `{thread_path, summary, short_summary, companies}` — no `actions` key
  exists anywhere in it. `## Actions` is refused to every caller (now
  enforced by the Thread template's own access declarations,
  `REQ-SB-87-US-01-T05`, which currently declare it `allowed_callers:
  ["apply_thread_review"]` per `ADR-017`).

**After / Outputs:**
- The payload gains an optional `"actions": str` field (or `list[str]` —
  this task's own disclosed shape call; a plain string of the agent's own
  already-composed prose is the simplest match to Scenario 1's own "the
  agent's own real words describing what is actually pending" wording, and
  needs no extra joining/formatting code — the recommended default unless
  a real reason for a list surfaces during build).
- When `data.get("actions")` is present (even an empty string, meaning "no
  pending action"), the script calls
  `vault_manager.modify_section(..., section="## Actions", mode="replace",
  caller="apply_thread_review")` with that content — the EXACT SAME call
  shape `T01`/`US-04` already uses for `## Summary`, just a different
  section name and content.
- When `actions` is ABSENT from the payload entirely (an older caller, or
  a Thread the agent judged as having nothing pending and simply omitted
  the key), `## Actions` is left untouched — never defaulted to a
  fabricated placeholder, never blanked out by accident. **When present as
  an empty string**, it IS written (replacing any prior machine-written
  content with "nothing pending" — an empty section), since Scenario 5
  requires the section to reflect the CURRENT real state, including "no
  longer pending."
- `## Personal Notes` is never read from or written to by this new code
  path — this task's own diff touches only the `actions`/`## Actions`
  handling, nothing else.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`

---

## Constraints

- Inherits from parent story.
- `mode="replace"`, never `"append"` — per `ADR-017`'s own Decision (a
  resolved pending action must actually disappear on re-summarization).
- `caller="apply_thread_review"` — the SAME one identity `## Summary`
  already uses, per `ADR-017`'s own "one caller, two sections" decision.
- Never touch `## Personal Notes` from this code path, in any case.
- This task's own write mechanism is pure application of an
  already-agent-decided value — no new judgment logic belongs in this
  script; that is `T02`'s own prompt-side scope.

---

## Tests

**Manual verification steps (mechanical proof — a hand-constructed
payload, no live agent call required for this task's own steps):**
1. `[REQ-SB-87-US-05-AC-01]` Call `apply_thread_review(vault_path, {...,
   "actions": "Waiting on [[Jane Doe]] to confirm the revised BoQ by
   Friday."})` against a real (or scratch) Thread; confirm `## Actions` is
   written with that exact content, via `vault_manager.modify_section`,
   `mode="replace"`, `caller="apply_thread_review"`.
2. `[REQ-SB-87-US-05-AC-01]` Call it again with a DIFFERENT `actions`
   string; confirm the section's content is fully REPLACED (the first
   string is gone, only the new one remains) — not appended alongside the
   old one.
3. `[REQ-SB-87-US-05-AC-06]` Confirm `## Personal Notes` is byte-for-byte
   unchanged before and after both calls above.
4. (Unlabeled, supporting) Call it with `actions` ABSENT from the payload
   entirely; confirm `## Actions` is left untouched (whatever it held
   before the call, it still holds after).
5. (Unlabeled, supporting) Attempt the SAME `## Actions` write with a
   caller identity OTHER than `apply_thread_review` (a disposable
   throwaway script, not a real Skill entry point); confirm it is refused
   — the section-access mechanism this task depends on (`REQ-SB-87-US-01`)
   is genuinely enforced, not just assumed.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via direct function calls with a hand-constructed payload`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `actions` payload field accepted, mechanically written to
      `## Actions` via `vault_manager.modify_section`, `mode="replace"`,
      `caller="apply_thread_review"`
- [ ] Absent `actions` key leaves `## Actions` untouched; present (even
      empty) replaces it
- [ ] `## Personal Notes` never touched
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The agent-side prompt/judgment for WHAT counts as a genuine pending
  action, resolved-vs-still-open detection, or who it's waiting on — `T02`.
- A dedicated `Work/Tasks/` integration — explicitly ruled out (parent
  story's own Non-Goals).

---

## Context / Notes

`ADR-017`'s own Decision (`## Actions` write-mode + caller-identity) and
`architecture.md` → `§Enrich-Stage Mechanics Migration & Pending-Action
Extraction` are authoritative. Read the real, post-`REQ-SB-87-US-04`
`apply_thread_review.py` directly before editing.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
