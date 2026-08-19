---
id: REQ-SB-49-US-02-T03
title: New "cockpit_mention" trigger literal on skill_registry.invoke_skill
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T03 — New `"cockpit_mention"` Trigger Literal

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Widen `skill_registry.invoke_skill`'s `trigger` parameter's `Literal[...]` type to include a fifth value, `"cockpit_mention"` — a new, honestly-named dispatch SOURCE for the first LLM-interpreted (not deterministic/caller-fixed) `invoke_skill` call site this codebase has (`ADR-038` point 5, mirrors `ADR-037` point 8's own `"scheduled"` precedent). Requires zero new gate branches — confirmed directly: `invoke_skill`'s own two `if` branches (`mode == "manual" and trigger == "hub_routed"`; `mode == "supervised" and mutates`) both already compose correctly with any `trigger` value, including this new one.

---

## Starting State → End State

**Before / Inputs:**
- `skill_registry.invoke_skill`'s real, current signature: `trigger: Literal["chat", "direct", "hub_routed"]` (confirmed by direct reading — `ADR-037`'s own `"scheduled"` addition has NOT yet landed in the real file as of this pass; if it has by build time, per this project's own "compose around the real current file" discipline, add `"cockpit_mention"` as the NEXT value after whatever the real current `Literal[...]` list already contains, not by reverting anyone else's landed addition).

**After / Outputs:**
- `trigger: Literal["chat", "direct", "hub_routed", "cockpit_mention"]` (or, if `ADR-037`'s `"scheduled"` has already landed by build time, `Literal["chat", "direct", "hub_routed", "scheduled", "cockpit_mention"]`) — every existing real call site (`skills_router.py`, `agents_router.py`, `knowledge_bootstrap.py`, `research.py`, and `capture_scheduler.py`/`agent_schedule_registry.py` if `ADR-037` has landed) is unaffected.

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — the single line:
  ```python
  def invoke_skill(
      agent_id: str,
      skill_id: str,
      args: dict | None,
      trigger: Literal["chat", "direct", "hub_routed", "cockpit_mention"],
  ) -> dict:
  ```
  (Read the real current signature FIRST — insert `"cockpit_mention"` as the last element of whatever the real current tuple already is; do not otherwise alter the function's own docstring/body.)

---

## Constraints

- Inherits from parent story.
- This is a pure type-hygiene/audit-trail addition — `Literal[...]` is not runtime-enforced by Python, so this change alone has zero effect on `invoke_skill`'s own actual dispatch behaviour for any trigger value, old or new (confirmed by direct reading of the function body — neither `if` branch inspects the type annotation).
- Do NOT add any new `if`/branch to `invoke_skill`'s own gate logic in this task — `ADR-038` point 5 explicitly confirms zero new branches are needed; adding one would be unauthorized scope creep for this specific task.
- Do NOT reuse `"chat"`, `"direct"`, or `"hub_routed"` for this story's own dispatch — `"cockpit_mention"` must be a genuinely new, distinct literal (per `ADR-038` point 5's own full reasoning, restated in the parent story's Notes).

---

## Tests

<!-- This task's own change has no independently observable runtime
behaviour on its own (a type-hint-only widening) -- its Tests are
therefore static/structural, not tied to any single locked AC in
isolation. AC-01/AC-02/AC-03 (which all exercise a real invoke_skill call
with trigger="cockpit_mention") are tagged and verified at T02's/T04's own
layer, once a real Skill exists to dispatch through this trigger value --
this task supplies the literal those calls type-correctly pass. -->

**Manual verification steps:**

1. Static check: read `skill_registry.py`'s real `invoke_skill` signature after the edit; confirm `"cockpit_mention"` is present in the `Literal[...]` tuple alongside every value that was already there before this task's edit (nothing removed).
2. Regression check: confirm every existing real `invoke_skill` call site (`grep -rn "invoke_skill(" src/backend/app` — `skills_router.py`, `agents_router.py`, `knowledge_bootstrap.py`, `research.py`) still passes one of its own existing `trigger` values unchanged — this task edits no call site, only the type annotation.
3. Confirm (Python shell) that `skill_registry.invoke_skill(<any real agent_id>, <any real skill_id the agent has access to>, None, trigger="cockpit_mention")` does not raise a `TypeError`/runtime error attributable to the trigger value itself (Python does not enforce `Literal` at call time) — any refusal/dispatch outcome returned is governed entirely by the existing gate logic, unaffected by this task.

**Automated tests:** `n/a — no backend test runner scaffolded yet (no pytest suite exists under src/backend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `invoke_skill`'s `trigger` parameter's `Literal[...]` includes `"cockpit_mention"`, with every prior value preserved
- [ ] No new `if`/branch added to `invoke_skill`'s own gate logic
- [ ] Every existing real `invoke_skill` call site unaffected (no call-site edits in this task)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any real call site that actually PASSES `trigger="cockpit_mention"` — that is `T02`'s (direct-call Tests) and `T05`'s (the real graph node) own scope. This task only widens the type.
- The `_dispatch_skill(..., already_approved=...)` seam — `T04`'s scope, unrelated to this task's own single-line change.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why this is its own task despite having no independent runtime dependency on anything else:** the parent story's own instruction named it as one of the six explicit task areas to decompose, and `ADR-038` point 5 gives it real, standalone reasoning (an honest, distinguishable audit-trail record of "an LLM's own interpretation of an `@mention` triggered this mutating dispatch") independent of any other task's own code — it is small enough (one line) to build in isolation, in any order relative to the other five tasks, with zero risk of file-content conflict beyond the ordinary "read the real current file first" discipline this project already applies to every task touching a shared file (`skill_registry.py` is also touched by `T02`/`T04`).

---

## Implementation Log

Read the REAL current `invoke_skill` signature first, per this task's own
Context: `ADR-037`'s `"scheduled"` had already landed
(`Literal["chat", "direct", "hub_routed", "scheduled"]`). Appended
`"cockpit_mention"` as the fifth/last value:
`Literal["chat", "direct", "hub_routed", "scheduled", "cockpit_mention"]`
— no other line of the function touched.

**Verification:**
1. Static check — PASS: real file read post-edit confirms all 5 values
   present, nothing removed.
2. Regression check — PASS: grepped every real `invoke_skill(` call site
   (`skills_router.py`, `agents_router.py`, `knowledge_bootstrap.py`,
   `research.py`, `agent_schedules_router.py`/`capture_scheduler.py`) —
   none edited by this task, all pass their own existing `trigger` value
   unchanged.
3. Runtime check — PASS (exercised live many times over by `T02`'s/`T04`'s/
   `T05`'s own real `invoke_skill(..., trigger="cockpit_mention")` calls
   throughout this story's verification): no `TypeError`/runtime error
   attributable to the trigger value; outcome governed entirely by the
   existing, unmodified gate logic.

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired (single-line type-hygiene addition, zero new
gate branches, no call-site edits, no `ESCALATIONS.md` entry).
