---
id: REQ-SB-85-US-03-T02
title: artifact_import_conflicts.py — per-artifact id-conflict detection against the target machine's real state
parent_story: REQ-SB-85-US-03
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-85-US-03-T01]
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03-T02 — artifact_import_conflicts.py: per-artifact id-conflict detection against the target machine's real state

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Given a parsed bundle's own manifest `artifacts` list (`T01`), check each
one against the target machine's own real current state, across all 4
kinds — real id existence only, no silent auto-resolution.

---

## Starting State → End State

**Before / Inputs:**
- `T01` returns a real manifest whose `artifacts` list names every
  bundled artifact's `kind`/`id`. `SkillManager().get_by_id(id)`/
  `TemplateManager().get_by_id(id)`/`AgentManager().get_by_id(id)`/
  `PipelineManager().get_by_id(id)` each already return `None` for an id
  that doesn't exist on THIS machine.

**After / Outputs:**
- `app/business/logic/artifact_import_conflicts.py` (new) exposes
  `detect_conflicts(artifacts: list[dict]) -> list[dict]` — returns the
  same list, each entry augmented with `"conflicts": bool` (`True` iff
  the target machine's own matching-kind Manager's `get_by_id(id)`
  returns non-`None` today). Pure read-only check — never mutates
  anything, never resolves a conflict itself (that's `T05`'s own job,
  once the operator has actually decided). Dispatch table: `{"skill":
  SkillManager, "template": TemplateManager, "agent": AgentManager,
  "pipeline": PipelineManager}` — a `kind` value outside this set is
  itself a real error (`ValueError`, never silently treated as
  "no conflict").

---

## Files to Modify

- `src/backend/app/business/logic/artifact_import_conflicts.py` (new file).

---

## Constraints

- Inherits from parent story.
- **Read-only — never resolves anything itself.** This module answers
  "does this id already exist," nothing more; the operator's own explicit
  overwrite/skip/keep-both choice (Scenario 3) and its actual application
  are `T05`'s job.
- **Checked independently per artifact, never batched/short-circuited** —
  every real artifact in the list gets its own real existence check
  against its own kind's Manager, even if an earlier one already
  conflicted.
- Never import `app.hermes` directly — only through the already-real
  `AgentManager`/`SkillManager`.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-03-AC-03]` Build an `artifacts` list containing one
   real, already-existing Skill id (any real Skill on this deployment)
   and one real, already-existing Agent id; call `detect_conflicts(...)`;
   confirm both entries come back `"conflicts": True`.
2. Build an `artifacts` list containing a real, deliberately-fabricated
   id (guaranteed not to exist on this deployment, e.g.
   `"skill": "sbf-t02-verify-nonexistent-skill"`) for each of the 4
   kinds; call `detect_conflicts(...)`; confirm all 4 come back
   `"conflicts": False` (no AC tag directly — supports `AC-02`'s own
   "no id conflict" precondition, verified end-to-end at `T05`).
3. Call `detect_conflicts(...)` with a `kind` value outside the real 4
   (e.g. `"kind": "provider"`); confirm `ValueError` is raised, not a
   silently-`False` result (no AC tag — defensive correctness, no
   Gherkin scenario names this directly).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `detect_conflicts` correctly flags a real, already-existing id per
      kind as `True`, and a genuinely-new id as `False`
- [x] Every artifact is checked independently, never short-circuited
- [x] An unrecognized `kind` raises, never silently reports "no conflict"
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually resolving a conflict (overwrite/skip/keep-both) — `T05`.
- The conflict-resolution UI — `T06`.

---

## Context / Notes

Architecture `§Template/Pipeline Write-Path Additions & Import
Orchestration` (`Implementation/Architecture/architecture.md`) names this
step as part of `T05`'s own orchestrator narrative; this task splits it
into its own small, independently-testable module per the story's own
pre-sketched Implementation Tasks table (real, separate concern from
`T05`'s own deployment mechanics).

---

## Implementation Log

Built `src/backend/app/business/logic/artifact_import_conflicts.py` (new
file) — `detect_conflicts(artifacts: list[dict]) -> list[dict]`, dispatch
table `{"skill": SkillManager, "template": TemplateManager, "agent":
AgentManager, "pipeline": PipelineManager}`. For each artifact entry, a
freshly-constructed Manager (all 4 are zero-arg constructible — confirmed
by direct reading before writing) calls its real `get_by_id(id)`; the
entry is returned with `"conflicts": existing is not None`. An unrecognized
`kind` raises `ValueError` before any Manager is touched. Confirmed
manifest entries use `"kind"`/`"id"` keys by reading `T01`'s real sibling,
`artifact_export.py` (the manifest producer). Read-only by construction —
no write call anywhere in the module.

Manual verification (real deployment, `src/backend/.venv/Scripts/python.exe`,
live against this machine's real Registry/Skill/Template/Pipeline state —
real ids enumerated first via each Manager's own `get_all()`):

- **`REQ-SB-85-US-03-AC-03`** — Built `[{"kind": "skill", "id":
  "azure-cost-calculator"}, {"kind": "agent", "id": "default"}]` (both
  real, already-existing ids on this deployment) and called
  `detect_conflicts(...)`. Observed: both entries returned
  `"conflicts": True` — `[{'kind': 'skill', 'id':
  'azure-cost-calculator', 'conflicts': True}, {'kind': 'agent', 'id':
  'default', 'conflicts': True}]`. PASS.
- (No AC tag — supports `AC-02`'s own "no id conflict" precondition, per
  the task's own Tests block) Built one deliberately-fabricated,
  guaranteed-nonexistent id per all 4 kinds
  (`sbf-t02-verify-nonexistent-{skill,template,agent,pipeline}`) and
  called `detect_conflicts(...)`. Observed: all 4 entries returned
  `"conflicts": False`. PASS.
- (No AC tag — defensive correctness, per the task's own Tests block)
  Called `detect_conflicts([{"kind": "provider", "id": "anything"}])`.
  Observed: `ValueError: unrecognized artifact kind 'provider' -- expected
  one of ['agent', 'pipeline', 'skill', 'template']` raised, no silent
  `False` result. PASS.
- "Every artifact checked independently, never short-circuited" (2nd
  unchecked AC bullet) is a structural property of the module (a plain
  `for` loop with no early `return`/`break`, no batching) — directly
  confirmed above: the 4-kind fabricated-id list (step 2) returned all 4
  independent results in one call, and a single shared per-artifact
  Manager instantiation never happens (a fresh `manager_class()` is
  constructed inside the loop body, per artifact).

No new dependency, shared-interface change, or ADR deviation. No
scope-internal judgement call beyond what's already disclosed in this
log (manifest key names confirmed against the real writer, not guessed).

gate: clear 2026-09-01 — no triggers fired (no new ADR, no assumption
beyond the disclosed manifest-shape confirmation above, requirement/story
finalised, all 3 locked-AC-relevant manual steps verified live and
passing).
