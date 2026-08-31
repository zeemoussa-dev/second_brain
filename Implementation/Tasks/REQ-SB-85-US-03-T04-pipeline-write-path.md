---
id: REQ-SB-85-US-03-T04
title: PipelineManager gains a real, import-only write path (ADR-015)
parent_story: REQ-SB-85-US-03
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03-T04 — PipelineManager gains a real, import-only write path (ADR-015)

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Add `write_pipeline_json` to `data_access/pipelines.py` and a matching
narrow create/import method to `PipelineManager` — the same-shape sibling
to `T03`'s Template write path, for the same disclosed, scoped
`ADR-015` reversal.

---

## Starting State → End State

**Before / Inputs:**
- `data_access/pipelines.py` has `read_pipeline_json`/`list_pipeline_ids`
  only. `PipelineManager`'s own module docstring states explicitly:
  "Read-only for now... no create/update/delete existed before this and
  none is built here either." `PipelineManager._to_pipeline` already
  resolves the on-disk `section` NAME string into a real `section_id` via
  `SectionManager` — and, per that method's own existing behaviour
  (unchanged by this task), auto-creates a matching Section if the name
  doesn't already exist on this machine (the exact same side effect
  `get_all()`/`get_by_id()` already have today for any hand-edited
  pipeline JSON naming an unknown section — not a new risk this task
  introduces).

**After / Outputs:**
- `data_access/pipelines.py` gains
  `write_pipeline_json(pipeline_id: str, data: dict) -> None` — raw I/O
  only (writes `<second_brain_data_path>/pipelines/<id>.json`, no
  validation, no defaults, `_definitions_dir()` created if missing).
- `PipelineManager` gains `import_pipeline(pipeline_id: str, data: dict)
  -> Pipeline` — validates via the existing `_to_pipeline(pipeline_id,
  data)` parser first (same "round-trip through the real read parser"
  discipline as `T03`'s Template import), then
  `pipelines_data.write_pipeline_json(pipeline_id, data)`, then returns
  `self.get_by_id(pipeline_id)` (read-your-own-write).
- `PipelineManager`'s own module docstring is updated — the existing
  "Read-only for now... no create/update/delete... none is built here
  either" paragraph is replaced with an accurate statement that a real,
  narrowly-scoped `import_pipeline` now exists for import provisioning
  only (`ADR-015`'s own Decision — a stale "read-only" comment next to a
  real writer is a self-contradicting file).

---

## Files to Modify

- `src/backend/app/data_access/pipelines.py`.
- `src/backend/app/business/core/pipelines/pipeline_manager.py`.

---

## Constraints

- Inherits from parent story.
- **Narrowly scoped to import provisioning only** — same "no general
  authoring UI" scope limit as `T03`, per `ADR-015`.
- **`PipelineManager` remains the sole gateway onto Pipeline data.**
- **This task does not provision a real Hermes cron job on the target
  machine** — a bundled Pipeline's own `cron_job_id`/`cron_profile_id`
  fields (if present in the exported JSON) are written as-is; on the
  target machine, `_cron_status` will honestly show no live cron status
  (`{}`) until/unless a matching real cron job is separately configured
  there — out of this story's own scope (the PRD does not ask for cron
  re-provisioning on import), not a defect.
- No new fields, no new validation rules beyond what `_to_pipeline`
  already expects on read.

---

## Tests

**Manual verification steps:**
1. Call `PipelineManager().import_pipeline("sbf-t04-verify-scratch",
   {"id": "sbf-t04-verify-scratch", "name": "Scratch Pipeline",
   "description": "", "section": "Data Gatherer", "steps": []})` (a
   real, well-formed `Pipeline` shape); confirm it returns a real
   `Pipeline` with `id == "sbf-t04-verify-scratch"`, and that
   `PipelineManager().get_by_id("sbf-t04-verify-scratch")` independently
   confirms the same data persisted to disk. No AC tag directly — supports
   `AC-02`, verified end-to-end at `T05`.
2. Call `import_pipeline` with a malformed shape (e.g. `"steps":
   "not-a-list"`); confirm it raises and no `<id>.json` file was written
   for that id (no AC tag — supports "validated before write").
3. Delete the scratch `pipelines/sbf-t04-verify-scratch.json` file
   created in step 1 (cleanup, no AC tag).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `write_pipeline_json` writes raw JSON, zero validation, zero defaults
- [x] `PipelineManager.import_pipeline` validates via the existing
      `_to_pipeline` parser before writing, never writes invalid data
- [x] `import_pipeline` returns the real, freshly-written `Pipeline`
      (read-your-own-write)
- [x] `PipelineManager`'s own module docstring no longer claims
      unconditionally read-only
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling this from the real import orchestrator — `T05`.
- Any general Pipelines create/update/delete UI.
- Real Hermes cron job re-provisioning on the target machine (see
  Constraints).
- The Template write path — `T03` (independent, same-shape sibling).

---

## Context / Notes

`ADR-015` (`Implementation/Architecture/ADR.md`), architecture
`§Template/Pipeline Write-Path Additions & Import Orchestration`, are the
authoritative design for this task.

---

## Implementation Log

**2026-09-01 — built and verified.**

- `src/backend/app/data_access/pipelines.py`: added
  `write_pipeline_json(pipeline_id, data)` — raw I/O only, no validation,
  no defaults, creates `_definitions_dir()` if missing, always overwrites.
  Module docstring extended one sentence to note the new writer and cite
  `ADR-015`.
- `src/backend/app/business/core/pipelines/pipeline_manager.py`: added
  `import_pipeline(pipeline_id, data) -> Pipeline` — round-trips `data`
  through the existing `_to_pipeline` parser first (raises uncaught on a
  malformed shape, before any write happens), then calls
  `pipelines_data.write_pipeline_json`, then returns
  `self.get_by_id(pipeline_id)` (read-your-own-write). Replaced the
  module docstring's "Read-only for now... no create/update/delete
  existed before this and none is built here either" paragraph with an
  accurate statement that `import_pipeline` (`ADR-015`) is a real,
  narrowly-scoped write path for import provisioning only.

**Scope-internal judgement call (for spot-check):** `_to_pipeline`'s own
existing `_section_id_by_name` behaviour (auto-creates a Section on this
machine if the JSON's `section` name string doesn't already match one) is
exercised as a side effect of `import_pipeline`'s own validation step,
exactly as the task's own Before/Inputs note anticipated and explicitly
called "not a new risk this task introduces" — left unchanged, not
special-cased, per the task's own Constraints (no new validation rules
beyond what `_to_pipeline` already expects on read).

**Verification (manual mode, real Python shell against this machine's
real configured `second_brain_data_path`, `src/backend/.venv`):**

- **Test step 1** (supports `AC-02`, full end-to-end coverage deferred to
  `T05` per the task's own Tests block) — PASS. Called
  `PipelineManager().import_pipeline("sbf-t04-verify-scratch", {"id":
  "sbf-t04-verify-scratch", "name": "Scratch Pipeline", "description":
  "", "section": "Data Gatherer", "steps": []})`. Observed: returned a
  real `Pipeline(id='sbf-t04-verify-scratch', name='Scratch Pipeline',
  section_id='data-gatherer', ...)`; a fresh, independent
  `PipelineManager().get_by_id("sbf-t04-verify-scratch")` call returned
  the identical `Pipeline`, confirming real on-disk persistence, not just
  an in-memory echo; the raw JSON on disk at
  `<second_brain_data_path>/pipelines/sbf-t04-verify-scratch.json`
  matched exactly what was passed in (zero defaults injected, per the
  raw-I/O AC).
- **Test step 2** ("validated before write" — no AC tag) — PASS. Called
  `import_pipeline("sbf-t04-verify-bad", {..., "steps":
  "not-a-list"})`. Observed: raised `TypeError: string indices must be
  integers, not 'str'` (from the existing `_to_pipeline` parser iterating
  `data.get("steps", [])` as if each entry were a dict) — propagated
  uncaught, exactly as the parser-round-trip validation is designed to
  do; confirmed no `sbf-t04-verify-bad.json` was ever written to the
  definitions directory.
- **Test step 3** (cleanup — no AC tag) — PASS. Deleted the scratch
  `pipelines/sbf-t04-verify-scratch.json` file created in step 1;
  confirmed it no longer exists on disk.

No locked story-level AC (`REQ-SB-85-US-03-AC-01..09`) is claimed
verified by this task — per the task's own Tests block, this task's
output is infrastructure consumed by `T05`, which performs the real
end-to-end AC verification. Nothing in this task's own scope was left
unverified.

**gate: clear 2026-09-01** — no MUST-FLAG trigger fired at this task: no
material assumption beyond the one explicitly disclosed and logged above
(itself pre-authorized by the task's own Before/Inputs text, not a new
judgement call), `ADR-015` (the controlling ADR for this task) was
authored by the architect pass, not by the coder, and the story's own
`gate: flagged` (trigger-3, `ADR-015`/`ADR-014` pending human review) is
independent of this task and does not block building per Pipeline.md;
`Files to Modify` respected exactly (2 files); both non-story-locked task
ACs and the two manual test steps passed with real, observed evidence.
