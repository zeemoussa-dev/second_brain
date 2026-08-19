---
id: REQ-SB-72-US-01-T02
title: Migrate the 3 real callers that directly compose thread_directory_paths off the stale-path risk
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-72-US-01-T01, REQ-SB-72-US-01-T03]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-72-US-01-T02 — Migrate the 3 real callers off directly composing `thread_directory_paths`

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Thread lookup — frontmatter-based, again" (`ADR-049` Decision 1, Context point 2)

---

## Objective

Fix the real, materially-broken blast radius `ADR-049`'s own direct-reading pass found: 3 real callers compose `thread_directory_paths(conversation_id)` directly (bypassing `resolve_thread_note_path`), so each one silently resolves to the WRONG, stale, since-renamed path the first time a Thread is renamed (`T03`). Migrate all 3 so a renamed Thread is found correctly by every real, going-forward caller — this is the concrete mechanism Scenario 2 requires.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/pipelines/raw_message_capture.py` line 97 (`capture_raw_thread_messages`'s own "does the Thread concept file exist yet" check): `concept_path = vault_writer.thread_directory_paths(conversation_id)["concept"]` / `if not concept_path.exists(): ...`
- `app/business/email_classification.py` line 479 (`synthesize_thread`'s own `messages/` directory read): `messages_dir = vault_writer.thread_directory_paths(conversation_id)["messages"]`
- `app/business/meeting_classification.py` line 324 (`_synthesize_history_entry`'s own linked-Thread `## Summary` read): `thread_concept_path = vault_writer.thread_directory_paths(linked_conversation_id)["concept"]`

**After / Outputs:**
- `raw_message_capture.py`: existence check swapped for `vault_writer.resolve_thread_note_path(conversation_id) is None`, matching Stage 2's own existing semantics exactly (zero behavior change for a not-yet-renamed Thread; correct behavior for a renamed one).
- `email_classification.py`: `synthesize_thread`'s `messages/` read is REORDERED to derive from the ALREADY-resolved `existing_path`'s own parent directory (`existing_path.parent / "messages"`) on the update branch; only on the genuinely-new-Thread (`created`) branch does it fall back to the deterministic `thread_directory_paths(conversation_id)["messages"]` (the directory `create_thread_note_baseline` just created it at). This requires moving the `messages_dir`/`message_paths` resolution to AFTER the `existing_path = vault_writer.resolve_thread_note_path(conversation_id)` / create-vs-update branch, not before it — the create-vs-update decision must happen first.
- `meeting_classification.py`: linked-Thread `## Summary` read swapped for `vault_writer.resolve_thread_note_path(linked_conversation_id)`, so a Meeting linked to a since-renamed Thread still finds its real, current `## Summary` instead of silently falling back to `""`.

---

## Files to Modify

- `src/backend/app/business/pipelines/raw_message_capture.py`
- `src/backend/app/business/email_classification.py`
- `src/backend/app/business/meeting_classification.py`

---

## Constraints

- Inherits from parent story.
- Zero change to any of the three functions' own external behavior for a NOT-YET-RENAMED Thread — this task only changes behavior for an ALREADY-RENAMED one.
- `synthesize_thread`'s own create-vs-update branch ordering must not change — only WHERE the `messages/` directory is read from.
- Do not touch `thread_match_merge`/`email_capture_pipeline.py` — out of this story's `## Files to Modify` (`ESC-050`).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-72-US-01-AC-02]` Direct Python-shell check against the real vault: take the real, already-renamed Thread from `T03`'s own verification (or rename a fresh disposable Thread via `librarian_housekeeping.rename_threads()`). Simulate a further real message in the SAME conversation (write a new raw message note for the same `conversation_id` via `vault_writer.create_raw_message_note`, guarded by `raw_message_note_exists` as Stage 1 already does), then call `email_classification.synthesize_thread(conversation_id)`. Confirm: (a) the EXISTING, renamed Thread directory is updated in place — no second, duplicate `Work/Threads/<slug-of-conversation_id>/` directory is created; (b) the update is found via `resolve_thread_note_path`'s frontmatter-based match, not a deterministic path-based check (confirm by reading the real code path exercised, or by independently deleting the stale deterministic-path location first and re-confirming the update still lands correctly); (c) the new message's own content is reflected in the regenerated `## Summary`.
2. Confirm `raw_message_capture.capture_raw_thread_messages`'s own existence check no longer creates a duplicate, empty Thread baseline for an already-renamed Thread's `conversation_id` — call it against a staged email for the SAME `conversation_id` as the renamed Thread from step 1, and confirm no new `Work/Threads/<slug-of-conversation_id>/` directory is created.
3. Confirm `meeting_classification._synthesize_history_entry` reads the real, current `## Summary` of an already-renamed, linked Thread (not an empty fallback) — construct or reuse a real Meeting linked to the renamed Thread from step 1, run the History-entry synthesis, and confirm the synthesized content reflects the Thread's real, current `## Summary` text.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `raw_message_capture.py`'s Stage 1 existence check uses `resolve_thread_note_path`
- [x] `synthesize_thread`'s `messages/` read derives from the already-resolved `existing_path` on the update branch
- [x] `meeting_classification._synthesize_history_entry`'s linked-Thread Summary read uses `resolve_thread_note_path`
- [x] No duplicate Thread directory is ever created for an already-renamed conversation_id
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Rename Job itself — `T03` (this task's own dependency, built first).
- Any change to `thread_match_merge`/`email_capture_pipeline.py` — disclosed, out-of-scope finding, see `ESC-050`.

---

## Context / Notes

Built AFTER `T03` deliberately — this task's own AC-02 verification requires a real, already-renamed Thread to exist as its test fixture, which only `T03`'s `rename_threads()` Job can produce.

---

## Implementation Log

**2026-08-18, coder pass.** Migrated all 3 real callers off directly
composing `thread_directory_paths(conversation_id)`:
`raw_message_capture.capture_raw_thread_messages`'s existence check now
uses `vault_writer.resolve_thread_note_path(conversation_id) is None`;
`email_classification.synthesize_thread`'s create-vs-update resolution
(`existing_path = resolve_thread_note_path(...)`) was reordered to happen
BEFORE the `messages/` directory read, which now derives from `existing_
path.parent / "messages"` on the update branch (falling back to the
deterministic path only on the `created` branch);
`meeting_classification._synthesize_history_entry`'s linked-Thread Summary
read now uses `resolve_thread_note_path(linked_conversation_id)`.

**Real, live-vault verification (`REQ-SB-72-US-01-AC-02`)**, using the real,
already-renamed Thread from `T03`'s own verification
(`004771620DBD604FAE3D2CE2A3404608`, now at `Work/Threads/2026-08-12 Your
Core42 Compass Portal account verification code/`):

1. Wrote a real further raw message note for the SAME `conversation_id`
   (via `create_raw_message_note`, guarded by `raw_message_note_exists`) —
   confirmed it landed under the RENAMED directory's own `messages/`
   (`raw_message_note_path` correctly resolved via `resolve_thread_
   directory`), not a stale deterministic location. Called `synthesize_
   thread(conversation_id)`: result `created: false` (the existing, renamed
   Thread was updated in place), `message_count: 2`; directory count before
   vs. after `synthesize_thread` unchanged (126 -> 126), zero directories
   matching the raw `conversation_id` slug — no duplicate ever created. The
   regenerated `## Summary` demonstrably reflected the new message's own
   real content. PASS (a/b/c).
2. Verified `raw_message_capture.capture_raw_thread_messages`'s own
   existence check directly: staged one fake email for the SAME
   `conversation_id` (via `email_staging.stage_email`, `email_pull.
   pull_and_stage_emails` scoped-monkeypatched to a no-op so this check
   exercises real Stage-1 logic without a real Outlook-COM fetch — reverted
   automatically via `unittest.mock.patch.object`'s own context-manager
   scope) and called the real function. Confirmed the new raw message note
   was written under the renamed directory's `messages/` and NO new
   `Work/Threads/004771620DBD604FAE3D2CE2A3404608/` directory was created
   (126 real Thread directories before and after). PASS.
3. Called `meeting_classification._synthesize_history_entry` directly with
   a disposable event dict and `linked_conversation_id` set to the renamed
   Thread's own `conversation_id`. Confirmed the returned synthesis
   genuinely incorporated the Thread's real, CURRENT `## Summary` content
   (quoted the test follow-up message's own real text) — not an empty
   fallback. PASS.

**Real-vault hygiene (disclosed, not a scope change):** the two disposable
raw messages added for step 1/2 verification were REMOVED after capturing
evidence, and the Thread's own concept file frontmatter/body was reset and
`synthesize_thread` re-run once more against only the one real, original
raw message — restoring `participants`/`last_message_at`/`## Summary` to
reflect ONLY genuine, real content (the original raw message note itself
was never touched — confirmed byte-identical via SHA-256 before/after this
whole task's verification). The Thread now carries a real, honest `##
Summary` for the first time (it had none before this task's own
verification pass touched it) — a genuine, disclosed side effect of running
the real Stage 2 pipeline against real content, not fabricated or left as
test pollution.

`gate: clear 2026-08-18` — no MUST-FLAG trigger fired: zero external
behavior change for any not-yet-renamed Thread (confirmed — every other
call site's own contract is unchanged), no new dependency, no ADR
deviation.
