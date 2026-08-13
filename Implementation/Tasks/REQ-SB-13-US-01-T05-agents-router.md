---
id: REQ-SB-13-US-01-T05
title: New app/api/agents_router.py — GET /agents/{id}, POST /agents/{id}/actions/{action_id}, POST /agents/{id}/chat, GET /agents/{id}/history
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T01, REQ-SB-13-US-01-T02, REQ-SB-13-US-01-T03, REQ-SB-13-US-01-T04]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T05 — New app/api/agents_router.py

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add the new `app/api/agents_router.py` (`APIRouter(prefix="/agents")`),
wiring together `T01`'s history primitives, `T02`'s registry, and `T03`'s
chat-matching mechanism into the four endpoints `architecture.md`/`ADR-011`
specify — the single place where the direct-action-trigger endpoint and the
chat endpoint invoke the identical action handler — and register it in
`app/main.py`.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T04` have landed `vault_writer`'s history primitives,
  `agent_registry.get_agent`, `agent_chat.handle_chat_message`, and
  `email_classification.run_capture_and_record_completion`'s history hook.
- `app/main.py` registers `health_check_router`, `email_poc_router`, and
  (once `REQ-SB-12-US-02-T03` lands) `my_day_router`.

**After / Outputs:**
- `app/api/agents_router.py` exists with the four endpoints below.
- `app/main.py` additionally registers `agents_router`.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` (new):
  ```python
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel

  from app.business import agent_chat, agent_registry
  from app.business.email_classification import run_capture_and_record_completion
  from app.data_access import vault_writer

  router = APIRouter(prefix="/agents")

  # Only email-capture's run_capture_now is backed by a real, already-Done
  # pipeline this pass (ADR-011) — every other declared action has no
  # handler yet and returns an honest "not yet available" result rather
  # than a fabricated success.
  _ACTION_HANDLERS = {
      ("email-capture", "run_capture_now"): run_capture_and_record_completion,
  }


  class ChatMessageBody(BaseModel):
      message: str


  def _invoke_action(agent_id: str, action_id: str) -> dict:
      """Shared by both the direct action-trigger endpoint and the chat
      endpoint, so a button click and a matching chat message invoke the
      identical handler and produce the identical history entries."""
      handler = _ACTION_HANDLERS.get((agent_id, action_id))
      if handler is None:
          return {"status": "error", "message": "This action is not yet available."}
      results = handler()
      return {"status": "ok", "message": f"Done — {len(results)} email(s) filed."}


  @router.get("/{agent_id}")
  def get_agent(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      return {
          "id": agent_id,
          "name": agent["name"],
          "type": agent["type"],
          "settings": agent["settings"],
          "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
      }


  @router.post("/{agent_id}/actions/{action_id}")
  def trigger_action(agent_id: str, action_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      result = _invoke_action(agent_id, action_id)
      vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
      return result


  @router.post("/{agent_id}/chat")
  def chat(agent_id: str, body: ChatMessageBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")

      vault_writer.append_agent_history_entry(agent_id, "chat_user", body.message)

      matched = agent_chat.handle_chat_message(agent_id, body.message)
      if matched["matched_action_id"] is not None:
          result = _invoke_action(agent_id, matched["matched_action_id"])
          # _invoke_action's own run_event entry (via trigger_action) is NOT
          # reused here — this path appends its own run_event directly, so
          # the chat-triggered action's history entry is attributed to this
          # call, not a second internal HTTP round-trip.
          vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
          reply = result["message"]
          action_triggered = matched["matched_action_id"]
      else:
          reply = matched["fallback_reply"]
          action_triggered = None

      vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
      return {"reply": reply, "action_triggered": action_triggered}


  @router.get("/{agent_id}/history")
  def get_history(agent_id: str) -> list[dict]:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      return vault_writer.load_agent_history(agent_id)
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.agents_router import router as agents_router
  ...
  app.include_router(agents_router)
  ```
  (Alongside the existing registrations — see `Constraints` below for exact
  ordering guidance if `REQ-SB-12-US-02-T03` has already landed
  `my_day_router`.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this router calls `agent_registry`/`agent_chat`/
  `email_classification`/`vault_writer` only, no direct filesystem access
  of its own.
- `_invoke_action` is the **one shared call site** for actually running a
  handler — both `trigger_action` and `chat` must go through it (or, for
  the chat path, its own equivalent inline call using the same
  `_ACTION_HANDLERS` dict) so a button click and a matching chat message
  produce identical behavior, per the parent story's own Constraints
  ("both paths can invoke the same underlying actions").
- Calling `email-capture`'s `run_capture_now` (via button or chat) triggers
  a **real** capture run (live Outlook COM fetch, Compass classify, vault
  write) — not a mock. Be deliberate about how many times this is invoked
  during manual verification (see Tests below), consistent with
  `MEMORY.md`'s standing dev-server-restart caution.
- Every action other than `email-capture`'s `run_capture_now` returns
  `{"status": "error", "message": "This action is not yet available."}` —
  do not fabricate a success for an action with no real handler.
- `GET /{agent_id}`, `POST /{agent_id}/actions/{action_id}`, and
  `POST /{agent_id}/chat` all 404 for an unknown `agent_id` — do not
  silently return an empty/default agent.

---

## Tests

<!-- This story's locked ACs (Scenarios 1/2/3/3b/4/5/6/7) are user-observable
on the agent detail panel — they are tagged and verified live in T06-T08
(the frontend tasks that actually render/drive this router's endpoints),
per the decomposer's "user-observable outcome" placement rule (mirrors
REQ-SB-08-US-01's T01-T04/T05 split and REQ-SB-12-US-02-T03's own
placement). The steps below are non-AC smoke checks confirming each
endpoint's shape/behavior against the real backend in isolation, before the
frontend tasks build on top. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/agents/email-capture`.
   Confirm the response has `id`/`name`/`type`/`settings`/`actions` keys,
   `settings` is a non-empty `{"key","value"}` list, `actions` is a
   non-empty `{"id","label"}` list (no `trigger_phrases` leaked into the
   response). `GET /agents/not-a-real-agent` — confirm `404`.
2. Non-AC smoke check: `POST http://127.0.0.1:8001/agents/meeting-capture/
   actions/run_capture_now` (an agent with no real handler). Confirm the
   response is `{"status": "error", "message": "This action is not yet
   available."}`. Confirm `GET /agents/meeting-capture/history`'s most
   recent entry reflects this attempt.
3. Non-AC smoke check: `POST http://127.0.0.1:8001/agents/email-capture/
   chat` with body `{"message": "hi there"}` (no trigger-phrase match).
   Confirm the response's `action_triggered` is `null` and `reply` mentions
   Email Capture's available actions.
4. Non-AC smoke check, **exactly once** (this triggers a real Outlook/
   Compass/vault-write capture run): `POST http://127.0.0.1:8001/agents/
   email-capture/chat` with body `{"message": "please run capture now"}`.
   Confirm `action_triggered` is `"run_capture_now"` and `reply` confirms
   emails were filed. Then `GET /agents/email-capture/history`; confirm the
   most recent entries, in order, include a `chat_user` entry (the sent
   message), a `run_event` entry (the triggered capture), and a
   `chat_agent` entry (the reply) — i.e. append order is chronological
   order.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /agents/{agent_id}` returns settings + actions (no
      `trigger_phrases` leaked), `404` for an unknown agent
- [ ] `POST /agents/{agent_id}/actions/{action_id}` invokes the real handler
      when one exists (`email-capture`/`run_capture_now` only this pass),
      else returns an honest "not yet available" result; always appends a
      `run_event` history entry
- [ ] `POST /agents/{agent_id}/chat` appends `chat_user`, then (on a match)
      `run_event`, then `chat_agent` history entries, in that order; returns
      `{"reply", "action_triggered"}`
- [ ] `GET /agents/{agent_id}/history` returns the unified chronological
      list (chat + run events) in append order
- [ ] `agents_router` registered in `app/main.py` without changing any
      existing router's behavior
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls these endpoints — `T06`-`T08`.
- Adding a real handler for any action beyond `email-capture`'s
  `run_capture_now` — future stories, per `ADR-011`'s own Consequences.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

If `REQ-SB-12-US-02-T03` (`my_day_router`) has already landed in
`app/main.py` by the time this task runs, add `agents_router` alongside it
without reordering the existing registrations — router registration order
has no behavioral significance in FastAPI, but keep the diff additive.

---

## Implementation Log

**2026-08-11, coder pass.** Created `app/api/agents_router.py` verbatim
per this task's spec (four endpoints, `_ACTION_HANDLERS`/`_invoke_action`
shared call site). Re-read `app/main.py` fresh before editing — found a
concurrent session (SPRINT-009/REQ-SB-12-US-02) had already added
`my_day_router` registration and a `CORSMiddleware` (allowing
`localhost:5173`/`127.0.0.1:5173`) since this task was authored — purely
additive, no conflict; added `agents_router`'s import and
`app.include_router(agents_router)` alongside the existing registrations,
unchanged order otherwise, per this task's own "keep the diff additive"
guidance.

During live browser-based verification (T06-T08), the frontend's Vite dev
server landed on port 5174 (5173 already bound by a concurrent session) —
extended the CORS middleware's `allow_origins` list with `5174` entries
(additive, does not remove the existing 5173 entries) so the real browser
fetch calls this story's own locked ACs depend on could succeed
cross-origin. Logged here since it is a small, necessary, non-conflicting
edit to a file another concurrent session also owns, not literally named
in this task's own `## Files to Modify` (which only anticipated router
registration) — a scope-internal judgment call, not an escalation, since
it doesn't change any router behavior or any locked AC.

Non-AC smoke checks:
1. `GET /agents/email-capture` — `id`/`name`/`type`/`settings`/`actions`
   present, `settings` non-empty `{"key","value"}` list, `actions`
   non-empty `{"id","label"}` list, no `trigger_phrases` in the response.
   `GET /agents/not-a-real-agent` — `404`. Confirmed.
2. Deviation from the task's literal script: used `todo-capture` (also a
   no-real-handler agent) instead of `meeting-capture` for the
   "no-handler action returns an honest error" check —
   `POST /agents/todo-capture/actions/run_capture_now` returned
   `{"status": "error", "message": "This action is not yet available."}`,
   and `GET /agents/todo-capture/history` reflected it. Substituted
   deliberately (scope-internal judgment, logged for spot-check): this
   task's own check is agent-agnostic (any no-handler agent proves the
   same behavior), and keeping `meeting-capture`'s history genuinely
   untouched was needed so `T08`'s AC-05 (empty-state) verification could
   use `meeting-capture` exactly as `T08`'s own test literally specifies,
   without a same-run collision between this task's smoke check and that
   locked AC's fixture agent.
3. `POST /agents/email-capture/chat` `{"message": "hi there"}` — no
   trigger-phrase match, `action_triggered: null`, `reply` mentions Email
   Capture's available actions. Confirmed.
4. Deviation from the task's literal script: the "exactly once" real
   action-trigger check (`POST /agents/email-capture/chat` with "please
   run capture now") was **not** additionally run as a standalone direct
   HTTP call here — it was instead verified once, live, through the real
   browser UI in `T07`'s own verification pass (same endpoint, same code
   path, invoked via an actual chat send instead of a raw HTTP call),
   confirming `action_triggered: "run_capture_now"`, a confirming reply,
   and the resulting `chat_user` → `run_event` → `chat_agent` (plus a
   second `run_event` from `T04`'s own hook inside the invoked handler —
   see the "Observed, not a defect" note below) append order via
   `GET /agents/email-capture/history`. Consolidated deliberately
   (scope-internal judgment, logged for spot-check) to avoid a second real
   Outlook/Compass/vault-write invocation in immediate succession, per
   this task's and `MEMORY.md`'s own "be deliberate" instruction — one
   live trigger, observed at both the raw-endpoint level (this task's own
   contract) and the UI level (`T07`'s own AC-08), is sufficient evidence
   for both.

Observed, not a defect (logged for spot-check): triggering
`run_capture_now` via chat produces **two** `run_event` history entries
for that single invocation, not one — `T04`'s hook inside
`run_capture_and_record_completion` itself appends
`"Capture run completed — N email(s) filed"`, and this router's own
`chat()` handler separately appends `"Done — N email(s) filed."` right
after `_invoke_action` returns (both per each task's own literal spec).
Scenario 3b/AC-04 only requires chat and run entries to appear together in
one list, not exactly one entry per event, so this does not weaken any
locked AC — recorded as a minor pattern for future action handlers that
already self-report via a `T04`-style completion hook of their own.

- [x] `GET /agents/{agent_id}` returns settings + actions, no `trigger_phrases` leaked, `404` for unknown agent — confirmed live
- [x] `POST /agents/{agent_id}/actions/{action_id}` invokes the real handler when one exists, else an honest error; always appends a `run_event` — confirmed live
- [x] `POST /agents/{agent_id}/chat` appends `chat_user`, then (on match) `run_event`, then `chat_agent`, in order; returns `{"reply","action_triggered"}` — confirmed live (via T07's UI trigger)
- [x] `GET /agents/{agent_id}/history` returns the unified chronological list in append order — confirmed live
- [x] `agents_router` registered in `app/main.py` without changing any existing router's behavior — confirmed (additive only, `my_day_router`/`email_poc_router`/`health_check_router` untouched)
- [x] `MEMORY.md` updated — yes, see Decisions/Patterns/Constraints entries for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes
