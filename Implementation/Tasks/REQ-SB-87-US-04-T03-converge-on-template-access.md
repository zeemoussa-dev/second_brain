---
id: REQ-SB-87-US-04-T03
title: Converge apply_thread_review.py onto the Thread template's own section-access declarations
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-04-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T03 — Converge apply_thread_review.py Onto the Thread Template's Own Section-Access Declarations

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Retire `apply_thread_review.py`'s own separate `_HUMAN_OWNED_HEADERS`/
`_CALLER`/`replace_body_section` access-control constants and function,
relying exclusively on `vault_manager.py`'s template-declared per-caller
access for every section write this script performs.

---

## Starting State → End State

**Before / Inputs:**
- `apply_thread_review.py`'s own real, separate guard (read directly,
  2026-09-01): `_HUMAN_OWNED_HEADERS = frozenset({"## Personal Notes", "##
  Actions"})`, `_CALLER = "apply_thread_review.apply_thread_review"`,
  enforced inside its own local `replace_body_section()` — `if header in
  _HUMAN_OWNED_HEADERS or caller != _CALLER: raise PermissionError(...)`.
  This local guard is now fully superseded by `T01`'s migration onto
  `vault_manager.modify_section`, which already enforces access via the
  Thread template's own declarations (`REQ-SB-87-US-01-T05`).

**After / Outputs:**
- The local `_HUMAN_OWNED_HEADERS`/`_CALLER`/`replace_body_section`/
  `insert_body_section_if_missing` functions and constants are removed
  from `apply_thread_review.py` — every section write already goes
  through `vault_manager.modify_section` (`T01`), which enforces access
  purely from the Thread template's own `allowed_callers` declarations.
- `## Summary` write succeeds (caller `apply_thread_review` is on its
  `allowed_callers` list); any attempt to write `## Personal Notes`
  through this code path is refused with a real, explicit
  `VaultManagerError` — enforced by `vault_manager.py`'s own
  template-declared access control, never by any code local to this
  script anymore.
- `read_note`/`merge_tags`/`upsert_frontmatter_key`'s own now-dead local
  copies (superseded by `T01`/`T02`'s migration onto the shared engine)
  are also removed if no longer called by anything in this file — a real,
  disclosed dead-code cleanup, not a behavior change.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`

---

## Constraints

- Inherits from parent story.
- Zero behavior change to any already-working write path — this task only
  removes the now-redundant local guard/primitives, it does not change
  WHAT gets written or WHO may write it (the Thread template's own
  declarations already reproduce the exact same real restrictions).
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-04-AC-06]` Confirm `## Summary` is still written
   successfully through the migrated code path (caller
   `apply_thread_review`, on the Thread template's own `allowed_callers`
   for that section).
2. `[REQ-SB-87-US-04-AC-06]` Attempt (via a disposable throwaway script,
   not this Skill's own real entry point) a `## Personal Notes` write
   through the migrated code path; confirm it is refused with a real,
   explicit `VaultManagerError`, and confirm — by reading the finished
   `apply_thread_review.py` directly — that this refusal is enforced by
   `vault_manager.py`'s own template-declared access control, not by any
   `_HUMAN_OWNED_HEADERS`-shaped constant still present in this file.
3. (Unlabeled, supporting) Confirm `_HUMAN_OWNED_HEADERS`/`_CALLER`/the
   local `replace_body_section`/`insert_body_section_if_missing` are no
   longer present in the file (or, if any function name is kept for a
   real, disclosed reason, confirm it is no longer load-bearing for access
   control).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `_HUMAN_OWNED_HEADERS`/local `_CALLER`-based guard removed
- [ ] `## Summary` write succeeds; `## Personal Notes` write refused, both
      enforced solely by `vault_manager.py`'s template-declared access
- [ ] Zero behavior change to any already-working write path
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `REQ-SB-87-US-05`'s own new `## Actions` write — this task only proves
  `## Summary`/`## Personal Notes` per its own locked Scenario 6; `##
  Actions` access is enabled by this same template but not exercised
  until `REQ-SB-87-US-05` actually writes to it.
- Real-vault verification / cutover — `T04`.

---

## Context / Notes

Read the real current `apply_thread_review.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
