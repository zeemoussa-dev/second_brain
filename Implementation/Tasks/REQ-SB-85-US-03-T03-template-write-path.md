---
id: REQ-SB-85-US-03-T03
title: TemplateManager gains a real, import-only write path (ADR-015)
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

# REQ-SB-85-US-03-T03 — TemplateManager gains a real, import-only write path (ADR-015)

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Add `write_template_json` to `data_access/templates.py` and a matching
narrow create/import method to `TemplateManager` — a disclosed, scoped
reversal of that module's own previously-documented read-only stance
(`ADR-015`), built only to let `T05`'s import orchestrator write a real
`Template.json` onto the target machine.

---

## Starting State → End State

**Before / Inputs:**
- `data_access/templates.py` has `read_template_json` only, no write
  function; its own module docstring states "Zero business
  interpretation here: no defaults applied, no error swallowed, no shape
  validated — that's TemplateManager's own job... Pure I/O." No comment
  claims read-only explicitly there, but `TemplateManager`'s own module
  docstring does: "Real, narrow scope... currently has zero real callers
  of its own... get_by_id()" (confirmed read-only-only shape by direct
  reading, no `create`/`update`/`delete` method exists).

**After / Outputs:**
- `data_access/templates.py` gains
  `write_template_json(template_id: str, data: dict) -> None` — same
  raw-I/O-only discipline as `read_template_json` (creates the
  `templates_root() / template_id` directory if missing, writes
  `Template.json` as `json.dumps(data, indent=2)`, no validation, no
  defaults filled).
- `TemplateManager` gains `import_template(template_id: str, data: dict)
  -> Template` — validates `data` by round-tripping it through the
  EXISTING `_to_template(template_id, data)` parser first (the same
  shape-check the read side already performs — a `KeyError`/`TypeError`
  there means `data` doesn't match the real `Template`/`TemplateSection`
  shape, propagated uncaught rather than writing invalid JSON to disk),
  then calls `templates_data.write_template_json(template_id, data)`,
  then returns `self.get_by_id(template_id)` (read-your-own-write, same
  convention `AgentManager.create`/`update` already use).
- `TemplateManager`'s own module docstring is updated to remove/qualify
  the "currently read-only" framing — per `ADR-015`'s own Decision, a
  "read-only for now" comment left in place after adding a real writer
  would be a live, self-contradicting file.

---

## Files to Modify

- `src/backend/app/data_access/templates.py`.
- `src/backend/app/business/core/templates/template_manager.py`.

---

## Constraints

- Inherits from parent story.
- **Narrowly scoped to import provisioning only** — `import_template` is
  the ONLY new write entry point; no general Templates authoring
  create/update/delete UI is built here (`ADR-015`'s own Alternatives
  Considered explicitly rejects that scope growth).
- **`TemplateManager` remains the sole gateway onto Template data** —
  `T05`'s orchestrator calls `TemplateManager.import_template(...)`,
  never `data_access.templates.write_template_json` directly.
- **No new fields, no new validation rules beyond what `_to_template`
  already expects on read** — the round-trip-through-the-read-parser
  check IS the validation; do not add a second, separate schema.
- The module docstring update (both files) is part of this task's own
  Definition of Done, not optional polish.

---

## Tests

**Manual verification steps:**
1. Call `TemplateManager().import_template("sbf-t03-verify-scratch",
   {"id": "sbf-t03-verify-scratch", "note_name": "Scratch Note",
   "sections": [{"name": "Body"}], "frontmatter_defaults": {}})` (a
   real, well-formed `Template` shape); confirm it returns a real
   `Template` with `id == "sbf-t03-verify-scratch"`, and that
   `TemplateManager().get_by_id("sbf-t03-verify-scratch")` independently
   confirms the same data was actually persisted to disk (read-your-own-
   write). No AC tag directly — this task has no Gherkin scenario of its
   own naming an externally-observable outcome; supports `AC-02`/`AC-05`,
   verified end-to-end at `T05`.
2. Call `import_template` with a deliberately malformed shape (e.g.
   `"sections": "not-a-list"`); confirm it raises (a real `TypeError`/
   similar from the existing `_to_template` parser) and that NO
   `Template.json` was written to disk for that id (no AC tag — supports
   the "validated before write, never a corrupt file left behind"
   Constraint).
3. Delete the scratch Template directory created in step 1 (cleanup, no
   AC tag).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `write_template_json` writes raw JSON, zero validation, zero defaults
- [x] `TemplateManager.import_template` validates via the existing
      `_to_template` parser before writing, never writes invalid data
- [x] `import_template` returns the real, freshly-written `Template`
      (read-your-own-write)
- [x] Both files' own module docstrings no longer claim read-only-only
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling this from the real import orchestrator — `T05`.
- Any general Templates create/update/delete UI.
- The Pipeline write path — `T04` (independent, same-shape sibling).

---

## Context / Notes

`ADR-015` (`Implementation/Architecture/ADR.md`), architecture
`§Template/Pipeline Write-Path Additions & Import Orchestration`, are the
authoritative design for this task — read `ADR-015` in full before
starting, including its own explicit "why not full CRUD" Alternatives
Considered reasoning.

---

## Implementation Log

**2026-09-01 — Coder.**

Built exactly per `ADR-015`'s own Decision, no deviation:

- `src/backend/app/data_access/templates.py`: added
  `write_template_json(template_id, data)` — creates
  `templates_root() / template_id` if missing, writes `Template.json` as
  `json.dumps(data, indent=2)`, zero validation/defaults, always
  overwrites. Module docstring updated to mention the new writer and its
  scope.
- `src/backend/app/business/core/templates/template_manager.py`: added
  `import_template(template_id, data) -> Template` — calls
  `self._to_template(template_id, data)` first (uncaught on failure, the
  same parser the read side already uses), then
  `templates_data.write_template_json(...)`, then returns
  `self.get_by_id(template_id)` (read-your-own-write). Never applies a
  conflict decision itself — always writes unconditionally; the future
  import orchestrator (`T05`) is the one that must decide
  overwrite/skip/keep-both before calling this. Module docstring updated
  to drop the "zero real callers"/read-only framing and note the new,
  narrowly-scoped write path.

**Verification (manual mode, no AC-ID tags on this task per its own
Tests block — this task has no Gherkin scenario of its own; it supports
story-level `AC-02`/`AC-05`, which are verified end-to-end at `T05` once
the import orchestrator composes this primitive):**

1. Ran `TemplateManager().import_template("sbf-t03-verify-scratch",
   {...well-formed Template shape...})` directly against the real,
   configured `second_brain_data_path` (via the project's own
   `.venv/Scripts/python.exe`, since the default `python`/`py` aliases on
   this machine resolve to the Microsoft Store stub — see `MEMORY.md`'s
   existing 2026-08-31 Constraint on this). Observed: returned a real
   `Template(id='sbf-t03-verify-scratch', note_name='Scratch Note',
   sections=[TemplateSection(name='Body', ...)], ...)`. A SECOND,
   independent `TemplateManager().get_by_id("sbf-t03-verify-scratch")`
   call (fresh instance) returned the identical data, confirming it was
   actually persisted to disk, not just returned in-memory. **PASS.**
2. Called `import_template` with a deliberately malformed shape
   (`"sections": "not-a-list"`). Observed: raised
   `TypeError: app.business.core.templates.template.TemplateSection()
   argument after ** must be a mapping, not str` — the real, existing
   `_to_template` parser correctly rejects it before any write is
   attempted. Confirmed independently: `get_by_id()` for that id returned
   `None` and `Template.json` does not exist on disk for it. **PASS.**
3. Deleted the scratch Template directory
   (`<second_brain_data_path>/data/Templates/sbf-t03-verify-scratch/`)
   created in step 1. Confirmed removed. No cleanup needed for step 2
   (nothing was ever written).

**Scope-internal judgement call (not an escalation, logged for spot-check
per Pipeline.md hard rule 5):** the task's own Acceptance Criteria
checklist has no `MEMORY.md`-entry content — this task is a literal,
zero-deviation implementation of `ADR-015`'s own already-Accepted
Decision (no new decision/pattern/constraint emerged beyond what
`ADR-015` and the story's existing Context already document, and the
existing 2026-08-28 Constraint on `data_access`/Manager layering already
covers the shape used here), so `MEMORY.md` was read but intentionally
NOT appended to — the DoD checkbox is satisfied by that determination,
not by an entry.

gate: clear 2026-09-01 — no triggers fired (ADR-015 already Accepted and
followed exactly as written, no new assumption beyond the one logged
above, no new dependency/shared-interface change/unanticipated file, both
locked-checklist items and the two manual verification steps all
verified live and passing).
