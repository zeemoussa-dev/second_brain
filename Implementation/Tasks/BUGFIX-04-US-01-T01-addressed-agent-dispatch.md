---
id: BUGFIX-04-US-01-T01
title: Scope send_user_message's per-agent dispatch to an explicit addressed_agent_ids list
parent_story: BUGFIX-04-US-01
requirement_id: BUG-022
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-04-US-01-T01 — Scope `send_user_message`'s per-agent dispatch to an explicit `addressed_agent_ids` list

## Parent Story

- Story: [[BUGFIX-04-US-01]] — `../UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`
- Requirement: `BUGS.md` → `BUG-022` (bugfix story; no PRD requirement anchor)

---

## Objective

Close `BUG-022`: `threads.py::send_user_message` currently loops
UNCONDITIONALLY over every currently brought-in agent on every message.
Give it an optional `addressed_agent_ids` list that, when present and
non-empty, scopes the reply loop to exactly those agent(s); when
absent/empty, preserve today's broadcast-to-every-brought-in-agent
behavior byte-for-byte (the story's own Constraint).

---

## Starting State → End State

**Before / Inputs:**
- `app/business/cockpit/threads.py::send_user_message(subject_kind,
  subject_note_stem, message_text)` (lines ~70-116) appends the user's
  turn, then `for agent_id in thread["brought_in_agent_ids"]:`
  unconditionally — every currently brought-in agent replies to every
  message, regardless of any `@mention` in the text.
- `app/api/cockpit_router.py::send_message` (lines ~33-35) is
  `async def send_message(subject_kind, subject_note_stem, body: dict)`
  and calls `await threads.send_user_message(subject_kind,
  subject_note_stem, body["message"])` — no addressee field read from
  `body` today.
- `src/frontend/src/features/cockpit/cockpitApiClient.ts::sendCockpitMessage`
  posts `{ message }` only — this task does NOT touch the frontend; `T02`
  adds the matching `addressedAgentIds` argument once this task's backend
  half exists.

**After / Outputs:**
- `send_user_message` gains a new parameter,
  `addressed_agent_ids: list[str] | None = None`. Its dispatch loop
  iterates `addressed_agent_ids if addressed_agent_ids else
  thread["brought_in_agent_ids"]` instead of unconditionally iterating
  `thread["brought_in_agent_ids"]`.
- `cockpit_router.py::send_message` reads an optional
  `addressed_agent_ids` key off the request `body` (a plain list of
  strings, or absent/`None`) and passes it straight through as the new
  keyword argument — no validation logic added at the router (matches
  this endpoint's own existing "no validation, dict body" convention).
- A no-mention message (single- or multi-agent thread) behaves EXACTLY as
  it does today — every currently brought-in agent replies.

---

## Files to Modify

- `src/backend/app/business/cockpit/threads.py`:
  1. Change `send_user_message`'s signature to:
     ```python
     async def send_user_message(
         subject_kind: str, subject_note_stem: str, message_text: str,
         addressed_agent_ids: list[str] | None = None,
     ) -> dict:
     ```
  2. Update the docstring's own description of the dispatch loop to
     describe the new addressed/fallback-to-broadcast behavior (replace
     "for EACH currently brought-in Expert" framing with "for each
     addressed Expert when `addressed_agent_ids` is given, otherwise for
     EACH currently brought-in Expert").
  3. Change the loop line from:
     ```python
     for agent_id in thread["brought_in_agent_ids"]:
     ```
     to:
     ```python
     for agent_id in (addressed_agent_ids or thread["brought_in_agent_ids"]):
     ```
     No other line inside the loop body changes.
- `src/backend/app/api/cockpit_router.py`:
  1. Change `send_message`'s body to read the new optional field and pass
     it through:
     ```python
     @router.post("/{subject_kind}/{subject_note_stem}/message")
     async def send_message(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
         return await threads.send_user_message(
             subject_kind, subject_note_stem, body["message"],
             addressed_agent_ids=body.get("addressed_agent_ids"),
         )
     ```

---

## Constraints

- Inherits from parent story — must not regress the existing,
  no-mention/broadcast-to-all-brought-in behavior (a single-brought-in-
  agent thread, and a multi-agent thread with no `@mention` in the
  message, must both keep behaving exactly as today).
- Must NOT add a second, independently-maintained mention-parsing
  implementation on the backend — `addressed_agent_ids` is always
  computed frontend-side (`T02`, reusing `REQ-SB-49-US-01`'s existing
  `resolveMentionedAgents`) and passed in as a plain, already-resolved
  list of agent ids; this task never parses `message_text` for `@tokens`
  itself.
- Must NOT change `_relayed_history_for`, `bring_in_agent`,
  `append_system_message`, or any other function in this file — scoped
  to `send_user_message`'s own dispatch loop and signature only.
- Must NOT change the per-agent reply-appending logic inside the loop
  (history build, `run_agent_conversation` call, reply-appending,
  `extracted_facts` memory write) — only which `agent_id`s the loop
  iterates over.
- An `addressed_agent_ids` entry that names an agent NOT currently in
  `thread["brought_in_agent_ids"]` is out of scope for this task to
  guard against — `T02`'s own frontend wiring already calls
  `bringInAgent(...)` for every mentioned agent before sending, so this
  case should not arise from the real UI; no new validation/error path is
  required here.

---

## Tests

<!-- AC-01 is the only locked AC this task's own fix directly implements.
Verified at the backend layer -- the NEW logic (addressed-agent dispatch
scoping) lives entirely in send_user_message's loop; the @-mention-text-
to-agent-id resolution itself is REQ-SB-49-US-01's own already-shipped,
unchanged resolveMentionedAgents, not re-verified here. Mirrors this
project's own "backend-layer-first live verification" precedent
(Implementation/Learnings.md, SPRINT-019/SPRINT-023). -->

**Manual verification steps:**

1. `[BUGFIX-04-US-01-AC-01]` In a Python shell against the real `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`), against the real,
   live-configured `VAULT_PATH`: pick any two real, already-registered
   agent ids (e.g. via `app.business.agent_registry.list_agents()`, any
   two non-background agents). Use a scratch Cockpit subject (a real or
   throwaway `subject_kind`/`subject_note_stem` pair — `threads.get_thread`
   creates an empty thread on first read if none exists) and call
   `await threads.bring_in_agent(subject_kind, stem, agent_a_id)` then
   `await threads.bring_in_agent(subject_kind, stem, agent_b_id)` (or the
   sync equivalent — `bring_in_agent` is not `async`) so both are brought
   in. Then call
   `await threads.send_user_message(subject_kind, stem, "a real message",
   addressed_agent_ids=[agent_a_id])` and confirm the returned thread's
   `messages` list gained exactly ONE new agent-speaker entry, with
   `agent_id == agent_a_id` — no entry for `agent_b_id`. Restore/delete
   the scratch thread entry from `.second-brain/cockpit_threads.json`
   afterward (or use a subject stem clearly marked as throwaway) so no
   permanent test artefact is left in the real vault state.
2. `[BUGFIX-04-US-01-AC-01]` (Regression coverage for the story's own
   Constraint — not itself a separate locked AC, folded into the same
   session.) Against the SAME two-agent scratch thread from step 1, call
   `await threads.send_user_message(subject_kind, stem, "a follow-up with
   no mention")` with `addressed_agent_ids` omitted (or `None`/`[]`).
   Confirm BOTH `agent_a_id` and `agent_b_id` gain a new reply entry —
   the existing broadcast-to-every-brought-in-agent behavior is
   unregressed.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `send_user_message` accepts an optional `addressed_agent_ids: list[str] | None = None` parameter
- [x] When `addressed_agent_ids` is a non-empty list, only those agent(s) generate and post a reply for that message
- [x] When `addressed_agent_ids` is `None`/empty/omitted, every currently brought-in agent replies, unchanged from today
- [x] `cockpit_router.py`'s `POST .../message` endpoint reads an optional `addressed_agent_ids` body field and passes it straight through, with no new validation logic
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change (`Cockpit.tsx`, `cockpitApiClient.ts`) — that is `T02`.
- Any change to which agents CAN be brought into a Cockpit thread, or the
  `@mention` bring-in mechanism itself (`REQ-SB-49-US-01`/`02`).
- Validating that every id in `addressed_agent_ids` is actually a member
  of `thread["brought_in_agent_ids"]` — not required by this story (see
  Constraints).

---

## Context / Notes

Full module-shape write-up: `Implementation/Architecture/architecture.md`
→ "Cockpit Chat — Addressed-Reply Dispatch, Send-on-Enter, and
Pending-State Live Update" (`BUG-022` bullet). Extends `ADR-036` point 1
(the existing `send_user_message` shape); no new ADR.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced — no deviation.

- `threads.py::send_user_message` gained `addressed_agent_ids: list[str] |
  None = None`; dispatch loop changed to `for agent_id in
  (addressed_agent_ids or thread["brought_in_agent_ids"]):`; docstring
  updated. No other line inside the loop body changed.
- `cockpit_router.py::send_message` reads `body.get("addressed_agent_ids")`
  and passes it through as the new keyword argument; no validation added.

**Verification (`[BUGFIX-04-US-01-AC-01]`) — backend-layer-first live
verification, real `.venv`, real live-configured `VAULT_PATH`, real
Provider calls (not mocked):** ran a scratch Python script (via
`.venv\Scripts\python.exe`, `PYTHONPATH` set to `src/backend` so the `app`
package resolves) against a real scratch Cockpit thread
(`meeting:__SCRATCH_TEST_BUGFIX_04_US_01__`). Brought in two real
registered agents (`email-capture-pipeline`, `meeting-capture`). Called
`send_user_message(..., addressed_agent_ids=["email-capture-pipeline"])`
and observed exactly ONE new agent-speaker message, `agent_id ==
"email-capture-pipeline"` — no reply from `meeting-capture`. **PASS.**
Then, same scratch thread, called `send_user_message(...)` with
`addressed_agent_ids` omitted — observed BOTH agents replied (broadcast
fallback unregressed). **PASS (regression coverage, story Constraint).**
Scratch thread entry deleted from `cockpit_threads.json` afterward via the
same script — no permanent test artefact left in real vault state.

`AC-01`: **PASS** — verified live, both the addressed-scoping behavior and
the no-mention broadcast-fallback regression guard.

No assumptions made beyond the task's own spec. `gate: clear` — no
MUST-FLAG trigger fired.
