---
id: REQ-SB-82-US-06-T06
title: cockpit_router.py — accept optional reply_to_message_id on POST .../message
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-06-T05]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T06 — cockpit_router.py: accept optional reply_to_message_id on POST .../message

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Let the Cockpit's `POST /cockpit/{subject_kind}/{subject_note_stem}/message`
endpoint accept an optional, caller-supplied `reply_to_message_id`, threaded
straight to `chat_turn.send_user_message`'s new parameter (`T05`).

---

## Starting State → End State

**Before / Inputs:**
- `cockpit_router.py`'s `SendMessageBody` is `{"text": str}` only;
  `send_message` calls `chat_turn.send_user_message(subject_kind,
  subject_note_stem, body.text)`. `T05` has added an optional
  `reply_to_message_id` parameter to `send_user_message`.

**After / Outputs:**
- `SendMessageBody` gains `reply_to_message_id: str | None = None`.
- `send_message` passes it straight through:
  `chat_turn.send_user_message(subject_kind, subject_note_stem, body.text,
  reply_to_message_id=body.reply_to_message_id)`.
- No new validation beyond FastAPI/Pydantic's own type coercion — an
  unresolvable/stale id is `T05`'s own defensive-read concern (Scenario 8),
  not this endpoint's.

---

## Files to Modify

- `src/backend/app/api/cockpit_router.py` — `SendMessageBody` and
  `send_message`.

---

## Constraints

- Inherits from parent story.
- Purely additive, optional field — no existing caller (frontend not yet
  updated at this point in the dependency chain) breaks by omitting it.
- No business logic in this file (this project's own established "API
  layer holds no business logic" rule, `cockpit_router.py`'s own module
  docstring) — this task is a pure passthrough.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-03]` Using `httpx.ASGITransport(app=app)` (or an
   equivalent real, in-process ASGI call) against the real, unmodified
   FastAPI app, `POST` to `/cockpit/{subject_kind}/{stem}/message` with a
   JSON body containing both `text` and a real `reply_to_message_id` value
   for an existing message in that subject's thread; confirm (via a spy/
   monkeypatch on `chat_turn.send_user_message` capturing its call
   arguments, OR by observing the downstream effect from `T05`'s own
   monkeypatched-Compass setup) that `reply_to_message_id` reaches
   `send_user_message` unchanged.
2. `POST` the same endpoint with no `reply_to_message_id` field in the
   body at all; confirm the request still succeeds (`422` is NOT returned)
   and `send_user_message` receives `None` for that parameter (no AC tag —
   backward-compatibility sanity check for existing callers).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST .../message` accepts an optional `reply_to_message_id` and
      passes it through to `chat_turn.send_user_message` unchanged
- [x] Omitting the field is still a valid request (backward-compatible)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T07`.
- Resolving the reference against the thread — already `T05`'s concern.

---

## Context / Notes

`ADR-012` point 4 (`Implementation/Architecture/ADR.md`) names this
endpoint change explicitly as additive to the field
`chat_store.append_message` already accepts internally for auto-threaded
replies.

---

## Implementation Log

**Change:** `src/backend/app/api/cockpit_router.py` — `SendMessageBody` gained
`reply_to_message_id: str | None = None`; `send_message` now calls
`chat_turn.send_user_message(subject_kind, subject_note_stem, body.text,
reply_to_message_id=body.reply_to_message_id)`. Confirmed `send_user_message`'s
real current signature (`app/business/cockpit/chat_turn.py:242-244`) already
carries the matching `reply_to_message_id: str | None = None` parameter (`T05`,
Done) before wiring the passthrough — no drift from the task's own "Before"
description. Pure passthrough, zero business logic added, per the file's own
"API layer holds no business logic" module docstring rule.

No deviations from the plan. No scope-internal judgement calls needed —
mechanical, zero-ambiguity passthrough exactly as specced.

**Verification (manual mode, in-process ASGI, real unmodified `app` object via
`httpx.ASGITransport`):**

- `[REQ-SB-82-US-06-AC-03]` **PASS.** Monkeypatched `chat_turn.send_user_message`
  in-process to capture its call arguments (spy), and `cockpit_router.
  _require_known_note` to bypass the unrelated vault-lookup precondition (not
  what this AC verifies). `POST /cockpit/person/jane-doe/message` with
  `{"text": "Following up on that", "reply_to_message_id": "msg-1234"}` against
  the real app returned `200`; the spy captured
  `reply_to_message_id="msg-1234"` unchanged (and `text="Following up on
  that"` unchanged) as the exact keyword argument received by
  `send_user_message`. Confirms the endpoint passes the caller-supplied id
  through unchanged to `T05`'s real parameter.
- (No AC tag — backward-compatibility sanity check) **PASS.** Same setup,
  `POST` with `{"text": "Just a plain message"}` (no `reply_to_message_id` key
  at all) returned `200` (not `422`); the spy captured
  `reply_to_message_id=None`. Confirms omitting the field is still a valid
  request and defaults to `None` exactly as `T05`'s own defensive-read
  contract (Scenario 8) expects.

Both steps run together via a single throwaway verification script
(`httpx.ASGITransport(app=app)` against the real, unmodified `app.main.app`,
Python 3.14.6, `src/backend/.venv`), reverting the in-process monkeypatches
implicitly (process exit, no persistent state changed — no vault write
occurred since `_require_known_note` was bypassed entirely for this endpoint
call).

gate: clear 2026-08-31 — no triggers fired (no ADR change, no assumption
beyond the task's own pre-authorized scope, requirement/story/task all
finalised, both steps verified with a real positive result, no out-of-scope
file touched).
