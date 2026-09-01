---
id: REQ-SB-87-US-02-T01
title: Migrate ingest_email.py onto vault_manager.py (Thread + first RawMessage)
parent_story: REQ-SB-87-US-02
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

# REQ-SB-87-US-02-T01 — Migrate ingest_email.py onto vault_manager.py

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Deploy a fresh `vault_manager.py` copy into `email-thread-capture/scripts/`
(first-time deployment) and migrate `ingest_email.py`'s own Thread
resolve/create and first-RawMessage-creation mechanics onto it, preserving
its exact real output contract and business logic.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `ingest_email.py` (read directly, 2026-09-01): resolves the
  Thread via `vault_lib.resolve_thread_directory`; if `None`, creates it via
  `vault_lib.create_thread_note_baseline(vault_path, conversation_id,
  thread_name=subject, tags=[])`; ensures a bare Person note per unique
  participant email (`vault_lib.ensure_bare_person_note` — untouched by
  this migration, stays hand-written); creates the RawMessage via
  `vault_lib.create_raw_message_note(...)` if `raw_message_note_exists()`
  says it doesn't yet; always stamps `last_message_at` (advances-only) via
  `vault_lib.update_thread_last_message_at`. Returns `{thread_created,
  message_created, thread_path, message_path}`.
- `email-thread-capture/scripts/` has never had a `vault_manager.py` copy.

**After / Outputs:**
- `email-thread-capture/scripts/vault_manager.py` — a fresh copy, sourced
  from the canonical `Hermes-Provisioning/shared/vault_manager.py`
  (post-`REQ-SB-87-US-01`'s own engine extensions).
- `ingest_email.py`'s own Thread resolve/create now goes through
  `vault_manager.find_by_id`/`vault_manager.create` against the `thread`
  template (`REQ-SB-87-US-01-T05`), passing `caller="ingest_email"` on
  every mutating call.
- First-RawMessage creation now goes through the dynamic-child verb
  (`REQ-SB-87-US-01-T01`) against the Thread's own `messages` declared
  child, natural key `(conversation_id, message_id)`.
- `ensure_bare_person_note`, participant-link accumulation, and the
  `last_message_at` advances-only stamping logic stay EXACTLY as they are
  today, entirely hand-written — this task only swaps the underlying
  note/section read-write mechanics.
- The function's own real return shape (`{thread_created, message_created,
  thread_path, message_path}`) is unchanged in meaning.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py`
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/vault_manager.py` (new copy)

---

## Constraints

- Inherits from parent story.
- `ensure_bare_person_note`'s own dedup-key, ignore-list, and GAL-derived
  department/role/company logic is untouched — this task never edits that
  function.
- The Thread's own `id` (a real, stable frontmatter key `vault_manager.py`
  now maintains) must be usable for future lookups without breaking
  `resolve_thread_directory`-style callers elsewhere (`rename_thread.py`,
  `link_person_to_thread.py`, etc. — `T02`/`T03`'s own scope to migrate,
  but this task's own Thread-creation must produce a note those siblings
  can still find).
- **Do not point `--vault-path` at the real, live vault for this task's own
  verification** — use a scratch vault seeded with a real ~100-email
  sample, per the Constraints' proving-phase rollout (see Tests below).

---

## Tests

**Manual verification steps (all against a SCRATCH vault, distinct
`--vault-path`, seeded with a real ~100-email sample pulled via
`list_recent_emails.py`/`run_full_capture.py`'s own real paging — never the
live vault for this task):**
1. `[REQ-SB-87-US-02-AC-01]` Pick a genuinely first-seen `conversation_id`
   from the real 100-email sample; run the migrated `ingest_email.py`
   against it. Confirm a new Thread concept note and its first RawMessage
   note are written with the exact same real frontmatter, body-section, and
   file/folder layout `email-thread-capture` produces today (per
   `REQ-SB-87-US-01-T05`'s own disclosed `## Files`-at-creation
   normalization, which is NOT treated as a violation here). Confirm the
   script still returns `{thread_created: true, message_created: true,
   thread_path, message_path}`.
2. `[REQ-SB-87-US-02-AC-02]` Re-run `ingest_email.py` for the SAME
   `message_id` from step 1. Confirm no duplicate Thread or RawMessage note
   is created (`{thread_created: false, message_created: false}`), and that
   `last_message_at` only ever advances, never regresses — repeat with a
   real message whose `received` timestamp is EARLIER than the Thread's
   current `last_message_at` and confirm it does NOT regress.
3. (Unlabeled, supporting) Confirm `ensure_bare_person_note`'s own real
   behavior (dedup key, ignore list, GAL fields) is byte-for-byte unchanged
   — same Person notes created/topped-up as an un-migrated run would
   produce, verified by comparing against a pre-migration baseline run on
   the SAME scratch sample (captured before this task's own edits, kept for
   comparison).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via real scratch-vault CLI runs, per this codebase's own
established pattern`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Fresh `vault_manager.py` copy deployed to `email-thread-capture/scripts/`
- [ ] Thread create/find and first-RawMessage creation go through
      `vault_manager.py`, `caller="ingest_email"`
- [ ] Exact real frontmatter/section/output-shape parity confirmed against
      the scratch sample
- [ ] Idempotency (re-ingest same message) and advances-only
      `last_message_at` confirmed
- [ ] `ensure_bare_person_note` unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `rename_thread.py`, `capture_attachments.py`/`capture_file_link.py`,
  `link_person_to_thread.py` — `T02`/`T03`.
- `run_full_capture.py`/`run_delta_capture.py`'s own orchestration logic —
  never edited by this migration.
- Any real-vault run or cutover — `T05`.
- The Capture-time classify-or-skip judgment layered onto this same branch
  — `REQ-SB-87-US-03`, sequenced strictly after this task.

---

## Context / Notes

`architecture.md` → `§Canonical vault_manager.py Source & Deployment`,
`ADR-017` are authoritative for the engine/template shape this task
consumes. Read the REAL current `ingest_email.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read — confirm it
hasn't drifted further by build time).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
