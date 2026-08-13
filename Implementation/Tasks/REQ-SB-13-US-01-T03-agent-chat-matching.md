---
id: REQ-SB-13-US-01-T03
title: New app/business/agent_chat.py — keyword/substring trigger-phrase matching mechanism
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T01, REQ-SB-13-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T03 — New app/business/agent_chat.py

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add `app/business/agent_chat.py::handle_chat_message(agent_id, message) ->
dict` — the exact-phrase/keyword substring-matching mechanism `ADR-011`
decided on: lowercase the incoming message, check it against the agent's
declared `trigger_phrases` in registry-declared order, first match wins.
Pure matching logic only — actually invoking the matched action's handler
and appending history entries is `T05`'s job (the router), so both the
direct-action-trigger endpoint and the chat endpoint invoke the exact same
handler.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `agent_registry.get_agent(agent_id)` →
  `{"name", "type", "settings", "actions": [{"id", "label",
  "trigger_phrases"}]}`.

**After / Outputs:**
- `app/business/agent_chat.py` exists with `handle_chat_message(agent_id:
  str, message: str) -> dict`, returning `{"matched_action_id": str | None,
  "fallback_reply": str | None}`.

---

## Files to Modify

- `src/backend/app/business/agent_chat.py` (new):
  ```python
  """Agent chat trigger-phrase matching mechanism (ADR-011) — exact-phrase/
  keyword substring matching against a small, per-agent-declared trigger
  phrase set, NOT an NLU/LLM pipeline (ADR-007 keeps that class of
  capability out of Second Brain's own stack). Pure matching only — the
  caller (app/api/agents_router.py, T05) is responsible for actually
  invoking the matched action's handler and appending history entries, so
  both the direct-action-trigger endpoint and the chat endpoint invoke the
  identical handler."""
  from app.business import agent_registry


  def handle_chat_message(agent_id: str, message: str) -> dict:
      """Returns {"matched_action_id": <action id> | None,
      "fallback_reply": <str> | None}. Exactly one of the two is non-None:
      a match sets matched_action_id and leaves fallback_reply None (the
      caller composes the real confirmation reply after invoking the
      handler); no match sets fallback_reply to a canned, honestly
      non-conversational message listing the agent's available actions,
      and leaves matched_action_id None."""
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          return {"matched_action_id": None, "fallback_reply": "Unknown agent."}

      lowered_message = message.lower()
      for action in agent["actions"]:
          for phrase in action["trigger_phrases"]:
              if phrase in lowered_message:
                  return {"matched_action_id": action["id"], "fallback_reply": None}

      action_labels = ", ".join(action["label"] for action in agent["actions"])
      fallback_reply = (
          f"I didn't understand that. {agent['name']} can: {action_labels}."
      )
      return {"matched_action_id": None, "fallback_reply": fallback_reply}
  ```

---

## Constraints

- Inherits from parent story: `ADR-011`'s decision — substring matching,
  registry-declared order, first match wins; explicitly not an NLU/LLM call
  (no Compass call anywhere in this module).
- Pure function — no `vault_writer` call, no history append, no action
  invocation. `T05` (the router) owns invoking the matched handler and
  appending history, so the exact same code path serves both the direct
  action-trigger endpoint and the chat endpoint.
- Must not modify `agent_registry.py` (`T02`) — read-only consumer of it.

---

## Tests

<!-- Exercised end-to-end, live, by T05's chat endpoint (Scenarios 2, 7),
where this story's locked ACs are tagged. The smoke check below confirms
this matching function in isolation first. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (cwd
   `src/backend`), call `agent_chat.handle_chat_message("email-capture",
   "please run capture now for me")`. Confirm it returns
   `{"matched_action_id": "run_capture_now", "fallback_reply": None}`
   (substring match on "run capture now"). Call
   `agent_chat.handle_chat_message("email-capture", "what's the weather
   today")`. Confirm it returns `{"matched_action_id": None,
   "fallback_reply": <a string mentioning Email Capture's available
   actions>}`. Call `agent_chat.handle_chat_message("email-capture",
   "capture now")`. Confirm it still matches `run_capture_now` (substring
   match on the shorter declared phrase).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `handle_chat_message` substring-matches the lowercased message against
      the agent's declared `trigger_phrases`, in registry-declared order,
      first match wins
- [ ] A match returns `{"matched_action_id": <id>, "fallback_reply": None}`
- [ ] No match returns `{"matched_action_id": None, "fallback_reply": <a
      message listing the agent's available action labels>}`
- [ ] No handler invocation, no history append, anywhere in this module
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually invoking `run_capture_now`'s (or any action's) real handler —
  `T05`.
- Appending chat/run_event history entries — `T05`.
- The `POST /agents/{agent_id}/chat` HTTP endpoint itself — `T05`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**2026-08-11, coder pass.** Created `app/business/agent_chat.py` with
`handle_chat_message(agent_id, message)`, verbatim per this task's spec —
pure function, no `vault_writer` call, no handler invocation.

Live confirmation (via T05's real `POST /agents/{agent_id}/chat` endpoint,
same substitution reasoning as T01/T02): `POST /agents/email-capture/chat`
`{"message": "hi there"}` returned `action_triggered: null` and a
`reply` mentioning Email Capture's available actions (substring-match
miss, correctly falls through to the fallback reply). `POST
/agents/email-capture/chat` `{"message": "please run capture now"}`
(exercised live via T07/T08's browser-driven verification, see those
Logs) returned `action_triggered: "run_capture_now"` — confirms the
shorter declared phrase (`"run capture now"` is itself the first listed
phrase and also a substring of the longer typed message) matches
correctly, in registry-declared order.

- [x] Substring-matches lowercased message against declared `trigger_phrases`, registry order, first match wins — confirmed live
- [x] A match returns `{"matched_action_id": <id>, "fallback_reply": None}` — confirmed live (`action_triggered` reflects this at the router)
- [x] No match returns `{"matched_action_id": None, "fallback_reply": <message>}` — confirmed live
- [x] No handler invocation, no history append, anywhere in this module — confirmed by code review (module has no `vault_writer`/handler import)
- [x] `MEMORY.md` updated — yes, see Decisions entry for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes

Assumption (scope-internal, logged for spot-check): same live-endpoint
substitution as T01/T02.
