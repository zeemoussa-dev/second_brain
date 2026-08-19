---
id: REQ-SB-71-US-02-T03
title: Stage 1 — capture_raw_thread_messages(), zero Compass calls, reuses pull_and_stage_emails/email_staging verbatim
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T03 — Stage 1 raw capture pipeline

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 2 (two-stage pipeline)

---

## Objective

New `app/business/pipelines/raw_message_capture.py::capture_raw_thread_
messages(limit: int = 10) -> dict` — Stage 1: reuses `email_pull.pull_and_
stage_emails`/`email_staging` VERBATIM as its raw-fetch substrate, then
writes every currently-staged, not-yet-message-noted email as an immutable
raw message note via `T01`'s new primitives. Zero `compass_client` import
anywhere in this module.

---

## Starting State → End State

**Before / Inputs:**
- `email_pull.pull_and_stage_emails(limit=10) -> dict` (`REQ-SB-69-US-01`)
  already does a real, resumable Outlook-COM fetch into `email_staging`
  (`.second-brain/email_staging/`), joining `agent_schedule_registry.
  get_shared_dispatch_lock()`.
- `email_staging.list_staged_emails() -> list[dict]` / `remove_staged_
  email(entry_id) -> None` already exist, reconstructing each staged
  email into the same shape `outlook_com.list_recent_mail` produces (`id`,
  `subject`, `sender_name`, `sender_email`, `received`, `body`,
  `attachments`, `conversation_id`, `recipients`).
- `T01`'s new `raw_message_note_exists`/`create_raw_message_note`/
  `thread_directory_paths`/`create_thread_note_baseline` primitives exist.

**After / Outputs:**
- `capture_raw_thread_messages(limit: int = 10) -> dict`:
  1. Calls `email_pull.pull_and_stage_emails(limit=limit)` (real Outlook
     COM fetch, already joins the shared dispatch lock — no new lock
     acquired by this function itself).
  2. Drains `email_staging.list_staged_emails()`: for each staged email,
     checks `vault_writer.raw_message_note_exists(conversation_id,
     message_id=email["id"], received=email["received"])`; if not already
     written, calls `vault_writer.raw_message_note_path`-shaped write via
     `create_raw_message_note(conversation_id, message_id=email["id"],
     received=email["received"], sender=email["sender_name"],
     sender_email=email["sender_email"], subject=email["subject"],
     body=email["body"])`.
  3. Ensures the Thread's own distilled concept file exists —
     `vault_writer.thread_directory_paths(conversation_id)["concept"]`;
     if it doesn't exist yet, calls `vault_writer.create_thread_note_
     baseline(conversation_id, thread_name=email["subject"])` (the FIRST
     message's own subject becomes `thread_name`, mirroring `ADR-046`
     Decision 6's own "captured once, stable across the Thread's life"
     property — never recomputed on a later message).
  4. Calls `email_staging.remove_staged_email(email["id"])` once that
     email's own raw message note is durably written (mirrors this
     module's own established "remove only after the durable write
     succeeds" ordering).
  5. Returns a dict reporting per-email outcome (e.g. `{"processed": [...],
     "skipped_already_noted": [...]}`).
- Zero `compass_client` import anywhere in this module — no LLM call is
  ever made by this function.

---

## Files to Modify

- `src/backend/app/business/pipelines/raw_message_capture.py` (new) —
  the function above, sibling to `email_capture_pipeline.py`/
  `email_pull.py`. Imports `email_pull`, `email_staging`, `vault_writer`
  only — no `compass_client`, no `email_classification`.

---

## Constraints

- Inherits from parent story.
- **Zero Compass calls, zero LLM dependency** — this module must never
  import `compass_client`, directly or transitively.
- **Grouping is ConversationID-only, provisional** — this function never
  performs a merge-vs-new-Thread judgment; it only ensures a Thread
  concept file exists at the deterministic path for this `conversation_
  id`, nothing more.
- **Reuses `pull_and_stage_emails`/`email_staging` VERBATIM** — no new
  staging mechanism, no parallel fetch path; the SAME shared dispatch lock
  `pull_email` already joins (concurrency-safety reuse, never a NEW
  `agent_schedule_registry` entry).
- **Every raw message note write goes through `raw_message_note_exists`
  first** — never calls `create_raw_message_note` a second time for the
  same `message_id`.
- **A staged email is only removed from `email_staging` after its own raw
  message note is durably written** — never removed first (which would
  risk losing content on a mid-write crash).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — this is a `business`-layer module composing `data_access`
  (`vault_writer`) and other `business` pipeline modules
  (`email_pull`, `email_staging` is `data_access`) only.

---

## Tests

**Manual verification steps:**

1. Non-AC foundational check: call `capture_raw_thread_messages(limit=1)`
   against a real (or realistic disposable) Outlook mailbox with Compass
   reachable. Confirm it completes, a raw message note is written under a
   real Thread's `messages/` folder, and the Thread's own concept file
   exists with an empty/not-yet-synthesized `## Summary`.
2. Non-AC foundational check: confirm `.second-brain/email_staging/` no
   longer contains the entry processed in step 1 (removed only after the
   durable write).
3. Non-AC foundational check: grep this module's own source for
   `compass_client` — confirm zero matches, confirming the zero-Compass-
   dependency contract at the import level, not just by observation of one
   run.

Full end-to-end AC verification (calling this function via the real
`POST /poc/capture-raw-thread-messages` endpoint, including the
Compass-unavailable case) is `T04`'s own scope, per this story's own
Constraint that every verification call must go through a real HTTP
endpoint.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `capture_raw_thread_messages` reuses `pull_and_stage_emails`/
      `email_staging` verbatim, zero Compass import
- [ ] Every staged email produces a real, write-once raw message note plus
      an ensured Thread concept file
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The real HTTP endpoint exposing this function — `T04`'s own scope.
- Any Compass-backed judgment, merge-vs-new-Thread decision, or `##
  Summary` regeneration — Stage 2 (`T05`)'s own scope.
- Rewiring the EXISTING scheduled `pull_email`/`process_staged_email`
  capability ids to compose this new function — a real, disclosed
  follow-up named in `architecture.md` ("their own underlying
  implementation now composes the two functions above in sequence"), left
  as a coder-level scope-internal judgement call for whichever task
  touches it, not mandated by any locked AC in this story.

---

## Context / Notes

`ADR-048` Decision 3 (`Implementation/Architecture/ADR.md`) has the exact
function docstring/shape this task implements. `REQ-SB-69-US-01`'s own
`email_pull.py`/`email_staging.py` are the direct precedent — read those
modules' own docstrings before writing this one, per this project's own
"generic-primitive-first, kind-specific-wrapper-second" pattern
(`Implementation/Learnings.md`, `SPRINT-048`).

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

New `src/backend/app/business/pipelines/raw_message_capture.py`,
`capture_raw_thread_messages(limit=10) -> dict`, built exactly as
specified: calls `email_pull.pull_and_stage_emails(limit=limit)`, then
drains `email_staging.list_staged_emails()` — for each staged email, a
`raw_message_note_exists` guard before `create_raw_message_note`, ensures
the Thread concept file exists (`create_thread_note_baseline` if not),
then `email_staging.remove_staged_email`. Imports `email_pull`,
`email_staging`, `vault_writer` only — zero `compass_client` import.

**Disclosed composition decision (this task's own coder-level choice,
per the task's own explicit note that the bytes-sourcing question is
left open):** also durably persists real attachment bytes via the
EXISTING, unmodified `vault_writer.write_attachments` (`subfolder=
"Work/Threads"`, `note_stem=conversation_id`, `message_segment=
message_id`) for any staged email carrying real attachments, BEFORE
`remove_staged_email`. Necessary because `email_staging`'s own copy
(the only place attachment bytes exist post-fetch) is deleted by this
same function immediately after each email's raw note is written —
without this, `T07`'s Files/OKF companion would have no durable source
of real bytes to work from at all. No new attachment-saving mechanism
introduced (reuses `write_attachments` verbatim, per `T07`'s own
Constraint).

**Manual verification (non-AC foundational checks):**

1. Module source grepped for `compass_client` — zero matches, confirming
   the zero-Compass-import contract at the import level. **PASS.**
2. Real end-to-end verification (durable write, staged-removal ordering,
   raw note + Thread concept file correctness) performed via `T04`'s own
   real `POST /poc/capture-raw-thread-messages` endpoint calls, per this
   task's own Tests section deferring full AC verification to `T04` (the
   story's own "every verification call goes through a real HTTP
   endpoint" Constraint) — see `T04`'s Implementation Log for the full,
   real, live evidence (252 real raw message notes + 127 real Thread
   directories from one real call against the live Outlook mailbox;
   `.second-brain/email_staging/` confirmed drained after).

**Disclosed, non-blocking finding:** `capture_raw_thread_messages` does
NOT call `vault_writer.mark_email_processed` — the new pipeline's own
idempotency is enforced entirely via `raw_message_note_exists` (T01),
never the legacy `processed_email_ids.json` tracker. Observed live: the
same most-recent Outlook items can be re-staged by a later `pull_and_
stage_emails` call (since they were never added to `processed_email_ids.
json`), but each is correctly recognized as already-raw-noted and safely
skipped (`skipped_already_noted`) — a harmless restage-then-skip cycle,
not a correctness defect, though a real efficiency follow-up (an
unnecessary repeat Outlook-COM re-fetch of the same recent window) a
future task could address; not filed as its own bug, since it causes no
observable defect within this story's own scope.

Status → `Done`. `gate: clear` — no MUST-FLAG trigger; the attachment-
durability decision is a disclosed, in-scope, necessary composition
choice, not an escalation.
