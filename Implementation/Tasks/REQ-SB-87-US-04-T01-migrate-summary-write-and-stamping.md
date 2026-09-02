---
id: REQ-SB-87-US-04-T01
title: Deploy vault_manager.py copy + migrate Thread-resolution/## Summary write + stamping
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Done
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

- [x] Fresh `vault_manager.py` copy deployed to
      `summarize-and-tag-threads/scripts/`
- [x] Thread resolution reads the real `id` from the payload's own
      `thread_path`, then resolves through `vault_manager.modify_section`
- [x] `## Summary` write confirmed correct, `caller="apply_thread_review"`
- [x] `last_message_at`/`last_summarized_at` stamping confirmed correct
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

**2026-09-01, coder.**

**What was changed:**
- Deployed a fresh, byte-identical `vault_manager.py` copy from the
  canonical `Hermes-Provisioning/shared/vault_manager.py` to
  `summarize-and-tag-threads/scripts/vault_manager.py` (confirmed via a
  direct `diff`, identical).
- `apply_thread_review.py`: added `import vault_manager as vm` +
  `import uuid`. `apply_thread_review()` now: (1) loads the `thread`
  template once via `vm.load_template`; (2) reads the Thread's own real
  frontmatter via `vm.read_note(thread_path)` to get its `id`; (3) writes
  `## Summary` via `vm.modify_section(..., section="Summary",
  mode="replace", note_id=<id>, caller="apply_thread_review")`; (4)
  stamps `last_message_at`/`last_summarized_at` in one
  `vm.update(vault_path, thread_path, frontmatter={...})` call,
  `last_message_at` only included when a real value was actually derived
  from a message (mirrors the original `if last_message_at:` guard).
  Company resolution, tag merging (`merge_tags`), and log-entry
  append/re-sort are byte-for-byte unchanged, still using this file's own
  hand-rolled `read_note`/`merge_tags`/`append_log_entry` — `T02`'s own
  scope. `_HUMAN_OWNED_HEADERS`/`_CALLER` and the now Summary-write-unused
  `insert_body_section_if_missing`/`replace_body_section` are left
  defined, unused by this path — retiring them is `T03`'s own scope, not
  this task's.

**Scope-internal judgment call (logged for human spot-check, not an
escalation):** the task's own End-State text says the migrated code
"reads the Thread's own real frontmatter `id` ... then calls
`vault_manager.modify_section(..., note_id=<that id>, ...)`" but doesn't
say what to do when that `id` is absent. Read directly against the real,
live vault (2026-09-01): every real Thread note checked (including
already-`job4`-processed ones) carries NO `id` frontmatter field at all —
`vault_manager.py`'s own `identity.strategy: "id"` is a NEW key real
Thread content has never had. Resolved by minting a `uuid4()` and
persisting it via `vm.update(vault_path, thread_path,
frontmatter={"id": ...})` the first time a Thread is touched by this
migrated path, before calling `modify_section` — matches
`vault_manager.py`'s own stated id philosophy verbatim ("a NEW field no
existing content has yet ... an auto-generated uuid4 if the caller
doesn't have one of its own"). Verified live (see below) that a second
run against the same Thread reads the SAME id back rather than minting a
new one each time.

**Live verification (scratch vault, distinct `--vault-path`, seeded from
real Thread/RawMessage shape read directly from
`Work/Threads/2026-08-31 Arabic Contract Translation Risk Tracker.../`
— synthetic company/person names used for the scratch content itself):**
scratch vault at a session-scoped temp directory, `.second-brain/data/
Templates/thread/Template.json` copied byte-identical from the real,
live vault's own Template.json; two scratch Threads, each with one or
more real-shaped `RawMessage` notes under `messages/`:
- **Thread A ("Acme Renewal Discussion")** — no `id`, no prior
  `last_message_at`/`last_summarized_at`, two RawMessage notes
  (2026-06-28 09:00, 2026-07-01 11:30).
- **Thread B ("Beta Corp Contract Update")** — already carries a
  pre-existing `id` (`SCRATCH-EXISTING-ID-0002`) and a stale
  `## Summary`/`last_summarized_at`, simulating a Thread already touched
  by a prior migrated run.

Ran the real, deployed `apply_thread_review.py` (venv Python,
`src/backend/.venv/Scripts/python.exe` — stdlib-only script, any real
Python works) against both, several times:

- `[REQ-SB-87-US-04-AC-02]` **PASS.** Run 1 against Thread A: output
  `last_message_at: "2026-07-01 11:30:00+00:00"` (the LATEST of its two
  real messages, not the first), `last_summarized_at` stamped to the
  real current run time. Confirmed on disk: both fields written to
  frontmatter exactly as printed. Run 2 (same input, ~10s later):
  `last_summarized_at` advanced to the new real run time,
  `last_message_at` unchanged (no new message) — exactly as today. Run
  against Thread B (pre-existing `last_message_at: "2026-06-15
  10:00:00+00:00"`, stale): correctly advanced to its real latest
  message, `"2026-07-02 15:00:00+00:00"`, confirming the stamp reflects
  the REAL current message state each run, not a stale carried-over
  value.
- (Unlabeled, supporting — feeds `REQ-SB-87-US-04-AC-01`) **PASS.** Run 1
  against Thread A: `## Summary` written with the exact agent-supplied
  text, resolved via a freshly-minted `id` written to frontmatter
  (confirmed on disk); `## Personal Notes` ("Do not touch this section,
  ever.") and `## Actions`/`## Related` byte-unchanged. Run 2 (same
  thread, new summary text): confirmed the SAME `id` was reused (no
  duplicate/second id minted) and `## Summary` was fully REPLACED (old
  text gone, no duplication) — `mode="replace"` confirmed live, not just
  assumed. Run against Thread B (pre-existing `id`): confirmed that
  existing `id` was read and reused as-is (frontmatter `id` line
  unchanged), stale `## Summary` fully replaced. Output JSON contract
  unchanged: `{tags_applied, companies_unresolved, messages_tagged,
  log_entries_added, last_message_at, last_summarized_at}` present with
  the same meaning on every run (confirmed `companies_unresolved:
  ["Acme Corp"]` on a run with an unresolvable company name, and
  `messages_tagged: 0`/`tags_applied: []`/`log_entries_added: []`
  correctly empty when no company resolves — company-resolution/tag/log
  code paths untouched by this task ran end-to-end with zero regression).
- **Extra confidence check (beyond the task's own named steps, direct
  `vm.modify_section` calls, not through the CLI):** a wrong-caller write
  to `## Summary` was refused live —
  `VaultManagerError: section 'Summary' in template 'thread' only allows
  ['apply_thread_review'] to write it -- caller 'some_other_script' is
  refused`; a `caller="apply_thread_review"` write to `## Personal Notes`
  was refused live — `VaultManagerError: section 'Personal Notes' is
  'human_only' in template 'thread' -- no automated write is allowed
  here`. Confirmed neither refusal call mutated the file on disk (read
  back unchanged) — the access check genuinely fires before any write,
  not just theoretically declared in the template. Confirms the write is
  genuinely resolving through the template-driven engine's own real
  access control, not bypassing it.
- `python -m py_compile` on both modified/deployed files — clean.
- `git status` confirms only the two `## Files to Modify` files touched
  (plus this task file / CHANGELOG.md / MEMORY.md / story / BACKLOG /
  sprint status, per the coder's standing exception).

**Deferred to later tasks (not this task's own scope, not silently
absorbed):** full `Scenario 1`/`AC-01` confirmation (tag/log-entry code
path migration) is `T02`; retiring `_HUMAN_OWNED_HEADERS`/converging on
template access for `## Personal Notes`/`## Actions`/`## Related`/
`## Files` is `T03`; real-vault retrofit-safety (`AC-07`, including
backfilling `id` onto the real vault's own already-populated Threads at
scale) and the live `job4` cron cutover are `T04`.

gate: clear 2026-09-01 — no MUST-FLAG trigger fired: no new dependency,
no shared-interface change beyond what the story's own Notes already
named, no ADR touched, no contradictory input (the missing-`id` gap was
resolved directly against real vault evidence, not guessed), both locked
verification points (`AC-02` fully, `AC-01`'s Summary-write half) passed
live. The `id`-backfill judgment call above is logged for human
spot-check per hard rule 5, not a flag trigger.
