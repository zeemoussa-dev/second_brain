---
id: REQ-SB-87-US-04-T01
title: Deploy vault_manager.py copy + migrate Thread-resolution/## Summary write + stamping
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T05]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T01 — Deploy vault_manager.py Copy + Migrate Thread-Resolution / ## Summary Write + Stamping

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Deploy a fresh `vault_manager.py` copy into
`summarize-and-tag-threads/scripts/` (first-time deployment) and migrate
`apply_thread_review.py`'s own Thread-note resolution, `## Summary` write,
and `last_message_at`/`last_summarized_at` stamping onto it.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `apply_thread_review.py` (read directly, 2026-09-01): the
  agent's own payload already carries a real, resolved `thread_path` (its
  own `read_file` call already found it — no lookup-by-id happens today).
  `insert_body_section_if_missing`/`replace_body_section(..., "##
  Summary", caller=_CALLER)` writes the summary; `upsert_frontmatter_key`
  stamps `last_message_at`/`last_summarized_at`. Its own separate
  `_HUMAN_OWNED_HEADERS`/`_CALLER` constants gate the write (retired in
  `T03`, not this task).
- `summarize-and-tag-threads/scripts/` has never had a `vault_manager.py`
  copy.

**After / Outputs:**
- `summarize-and-tag-threads/scripts/vault_manager.py` — a fresh copy,
  sourced from the canonical, fully-extended
  `Hermes-Provisioning/shared/vault_manager.py`.
- Since the agent's own payload gives a real path, not an `id`, the
  migrated code reads the Thread's own real frontmatter `id`
  (`vault_manager.read_note(thread_path)`) first, then calls
  `vault_manager.modify_section(..., note_id=<that id>, section="##
  Summary", mode="replace", caller="apply_thread_review")` — genuinely
  resolving through the template-driven engine, not bypassing it with a
  raw path write.
- `last_message_at`/`last_summarized_at` stamping goes through
  `vault_manager.update(vault_path, thread_path, frontmatter={...})` (the
  generic, path-based frontmatter writer) — same real values, same
  advances-only-where-applicable semantics.
- Company resolution (`build_company_index`/`resolve_companies`), tag
  merging, log-entry logic, and Person-note-never-tagged rule are
  UNTOUCHED by this task — `T02`'s own scope.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`
- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/vault_manager.py` (new copy)

---

## Constraints

- Inherits from parent story.
- Company resolution, the never-tag-Person-notes rule, and log-entry
  re-sort logic stay hand-written and untouched by THIS task (they still
  use the file's own existing primitives until `T02`).
- Verify against a scratch vault, distinct `--vault-path` — never the live
  vault for this task.
- Never run `job4` concurrently with itself or `email-thread-capture`
  against the same vault during verification.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, seeded
from real Thread content):**
1. `[REQ-SB-87-US-04-AC-02]` Run the migrated `apply_thread_review.py`
   against a real (or scratch, copied from real) Thread with one or more
   RawMessage notes; confirm `last_message_at` is stamped from the Thread's
   own latest message's real `received` value, and `last_summarized_at` is
   stamped to the current time, exactly as today.
2. (Unlabeled, supporting — feeds `REQ-SB-87-US-04-AC-01`, whose full
   confirmation completes at `T02`) Confirm `## Summary` is written with
   the agent's real summary content, resolved via `note_id` (read from the
   Thread's own real frontmatter `id`), through `vault_manager.
   modify_section`, `caller="apply_thread_review"`.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Fresh `vault_manager.py` copy deployed to
      `summarize-and-tag-threads/scripts/`
- [ ] Thread resolution reads the real `id` from the payload's own
      `thread_path`, then resolves through `vault_manager.modify_section`
- [ ] `## Summary` write confirmed correct, `caller="apply_thread_review"`
- [ ] `last_message_at`/`last_summarized_at` stamping confirmed correct
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Tag-merging, company log-entry logic — `T02`.
- Retiring `_HUMAN_OWNED_HEADERS`/converging on template access — `T03`.
- Real-vault verification / cutover — `T04`.

---

## Context / Notes

`architecture.md` → `§Canonical vault_manager.py Source & Deployment`,
`§Enrich-Stage Mechanics Migration & Pending-Action Extraction`, and
`ADR-017` are authoritative. Read the real current
`apply_thread_review.py` directly before editing (reproduced in Starting
State above from a 2026-09-01 read).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
