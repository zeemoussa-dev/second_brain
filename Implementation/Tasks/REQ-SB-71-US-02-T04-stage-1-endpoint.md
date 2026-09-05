---
id: REQ-SB-71-US-02-T04
title: POST /poc/capture-raw-thread-messages — Stage 1 endpoint, operator-triggered, no scheduler wiring
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T03]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T04 — Stage 1 endpoint

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 2 (two-stage pipeline)

---

## Objective

Expose `T03`'s `capture_raw_thread_messages()` as a real, directly-callable
`POST /poc/capture-raw-thread-messages` endpoint in the existing
`email_poc_router.py` — no new sibling router (mirrors this router's own
already-established "general home for flat, operator-triggered one-off
`/poc/*` operations" convention). This is the task whose own `## Tests`
carries the AC-tagged, real-endpoint verification for Scenarios 1-3.

---

## Starting State → End State

**Before / Inputs:**
- `T03`'s `raw_message_capture.capture_raw_thread_messages(limit=10) ->
  dict` exists and is directly callable in Python, but not yet reachable
  over HTTP.

**After / Outputs:**
- `POST /poc/capture-raw-thread-messages?limit=10` (query parameter,
  default `10`, mirroring `classify_emails`'s own `limit` query-parameter
  convention) calls `capture_raw_thread_messages(limit=limit)` and returns
  its result dict.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py` — import
  `raw_message_capture.capture_raw_thread_messages`; add:
  ```python
  @router.post("/capture-raw-thread-messages")
  def capture_raw_thread_messages_endpoint(limit: int = 10) -> dict:
      return capture_raw_thread_messages(limit=limit)
  ```
  placed near the other email-pipeline `/poc/*` endpoints in this file.

---

## Constraints

- Inherits from parent story.
- **No scheduler wiring, no `agent_schedule_registry` entry, no cron-style
  recurring tick** — this endpoint is reachable ONLY via a direct HTTP
  call, operator- or Claude-Code-triggered.
- **This endpoint shares no lock with the Stage 2 endpoint (`T06`)** —
  this task itself introduces no new lock; `T03`'s own function already
  only joins the pre-existing shared dispatch lock via `pull_and_stage_
  emails`, and Stage 2 must never be made to join that same lock either
  (verified end-to-end in `T06`).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-02-AC-01]` Call `POST /poc/capture-raw-thread-messages`
   for a real, newly-arrived email. Confirm the response is a 2xx success.
   Confirm a new, verbatim raw message note exists at `Work/Threads/
   <thread-slug>/messages/<date>-<hash8>.md`, and confirm the Thread's own
   distilled note (`Work/Threads/<thread-slug>/<thread-slug>.md`) exists
   with an empty or not-yet-synthesized `## Summary` — confirm this call
   alone never wrote any real content into `## Summary`.
2. `[REQ-SB-71-US-02-AC-02]` Call the same endpoint again for a SECOND,
   later real email in the SAME conversation. Confirm a NEW, second raw
   message note is written under the same `messages/` folder, and confirm
   the FIRST raw message note's own content (read back) is byte-for-byte
   unchanged from step 1.
3. `[REQ-SB-71-US-02-AC-03]` With Compass deliberately made unavailable or
   slow (e.g. point `COMPASS_BASE_URL`/equivalent config at an unreachable
   address, or stop the local Compass server if applicable), call `POST
   /poc/capture-raw-thread-messages` again for a real email. Confirm the
   call still completes successfully — the raw message note is written and
   the email is provisionally grouped by `conversation_id` alone, with no
   LLM call made. Restore Compass reachability afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-71-US-02-AC-01` — a real email produces its own immutable,
      verbatim raw message note; Stage 1 never generates `## Summary`
- [ ] `REQ-SB-71-US-02-AC-02` — a second message in the same conversation
      never modifies an earlier raw message note
- [ ] `REQ-SB-71-US-02-AC-03` — Stage 1 groups purely by `conversation_id`,
      zero Compass calls, never fails when Compass is unavailable
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any `agent_schedule_registry`/scheduler wiring.
- Registering this capability id against `skill_registry.py`'s own
  chat-agent tool-exposure/capability-tier dicts (`_CAPABILITY_TOOLS`,
  `run_capture_now`, `pause_schedule`, etc.) — no locked AC in this story
  requires this endpoint be callable AS an agent chat tool, only that it
  be a real, directly-callable HTTP endpoint; a future story may wire
  chat-agent exposure if wanted, not decided here.
- Stage 2 (`T05`/`T06`) — this task's own endpoint never triggers Stage 2.

---

## Context / Notes

`ADR-048` Decision 3 (`Implementation/Architecture/ADR.md`): *"Exposed as
`POST /poc/capture-raw-thread-messages` — a NEW, independent capability id
... of the SAME existing `"email-capture-pipeline"` Agent-tier identity...
never a new Agent, no new Map node."*

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

`POST /poc/capture-raw-thread-messages` added to `email_poc_router.py`
exactly as specified, calling `capture_raw_thread_messages(limit=limit)`.

**Real, live AC verification — every call a real HTTP request against
the real backend server (`uvicorn`, `127.0.0.1:8000`) and the real,
live operator Outlook mailbox/vault (`<OPERATOR_VAULT_OLD>`):**

**`[REQ-SB-71-US-02-AC-01]` PASS.** `POST /poc/capture-raw-thread-
messages?limit=10` → `200 OK`. This one real call drained a large
pre-existing backlog of already-staged-but-not-yet-message-noted mail
(`.second-brain/email_staging/`, left over from earlier `SPRINT-060`
migration work) plus fresh Outlook fetch: **252 real, verbatim raw
message notes written** under **127 real Thread directories**, each
Thread's own concept file created with an empty/not-yet-synthesized `##
Summary` (confirmed by direct read of several, e.g. `Work/Threads/
059EC2A1E82879429DFF7124FD5F836F/059EC2A1E82879429DFF7124FD5F836F.md`:
body was exactly `## Summary\n\n## Personal Notes\n\n## Actions\n\n##
Related\n` immediately after this call, before any Stage 2 call ever
touched it). Confirmed `.second-brain/email_staging/` correctly drained
(only 12 pre-existing, `email.json`-less corrupted directories remained
— a real, pre-existing, unrelated staging-hygiene artifact from before
this session, correctly and safely skipped by `email_staging.list_
staged_emails()`'s own existing guard; not caused by or fixed by this
story).
**`[REQ-SB-71-US-02-AC-02]` PASS.** Direct inspection of a real
multi-message Thread (`059EC2A1E82879429DFF7124FD5F836F`, 12 real raw
messages from the same real EWEC/Compass conversation) confirmed
distinct, real, byte-different raw message notes coexisting under the
same `messages/` folder (`2026-08-13-0d25671f.md`,
`2026-08-13-2126c02a.md`, ... `2026-08-14-dfcbbd09.md`) — read two of
them directly: different `message_id`/`sender`/`subject`/`received`
frontmatter and different real body content, confirming no note was ever
overwritten by a later message. `raw_message_note_exists`'s write-once
guard was additionally re-confirmed live: a follow-up `POST /poc/
capture-raw-thread-messages?limit=3` re-staged the same 3 most-recent
items (since the new pipeline never calls `mark_email_processed` — see
`T03`'s own disclosed finding) and correctly reported them all under
`skipped_already_noted`, never re-writing or duplicating their already-
existing raw notes.
**`[REQ-SB-71-US-02-AC-03]` PASS.** `COMPASS_BASE_URL` temporarily
repointed to a deliberately unreachable address
(`http://127.0.0.1:1/deliberately-unreachable-for-AC-03-verification`)
in `src/backend/.env`, server restarted, then `POST /poc/capture-raw-
thread-messages?limit=5` called: **`200 OK` in 1.3 real seconds**
(`{"pulled": {"fetched": 5, "newly_staged": 5, ...}, ...}`), zero LLM
call attempted (fast completion time itself confirms no Compass timeout/
retry occurred), grouping done purely by `conversation_id`. `.env`
restored to the real Compass URL and the server restarted again
immediately after, confirmed healthy (`GET /agents/email-capture-
pipeline` → `200`).

Status → `Done`. `gate: clear` — no MUST-FLAG trigger; all 3 locked ACs
verified with real, live evidence, exactly as required.
