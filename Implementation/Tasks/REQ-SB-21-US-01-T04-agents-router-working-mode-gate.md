---
id: REQ-SB-21-US-01-T04
title: agents_router.py — corrected two-axis working-mode gate (ADR-020) — split _invoke_action into the gate + _execute_action, trigger param incl. hub_routed, merged working_mode field, PATCH working_mode
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T02, REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T09]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-21-US-01-T04 — agents_router.py corrected two-axis working-mode gate

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Rewritten in place, 2026-08-12 (re-derived against `ADR-020`)

This task is rewritten around `ADR-020`'s corrected two-axis gate
(supersedes `ADR-018` point 3 in full) — the story's own re-spec
(`ESCALATIONS.md` → `ESC-013`) found the original `ADR-018`-only design
gated Supervised uniformly by trigger source; the corrected design gates
Supervised by the action's own `mutates` classification (`T09`) and Manual
by trigger source only. **The original `ADR-018`-only version of this task
is kept, unedited, at the bottom of this file as an honest record** — do
NOT build against it; mirrors `REQ-SB-08-US-01-T06`'s own `ADR-013`→
`ADR-019` precedent.

**A second, independent finding drove this rewrite, not just the ADR
correction:** the real `src/backend/app/api/agents_router.py` has
structurally drifted from the original `T04`'s own stale code sample.
`chat` is now `async def` and calls `await agent_orchestration.
run_agent_conversation(...)` with real conversation-history/memory loading
and fact-extraction persistence (`REQ-SB-25-US-01`/`REQ-SB-26-US-01`, both
shipped in `SPRINT-014`/`SPRINT-015` — after the original `T01`-`T08`
decomposition, which predates both). The rewritten sample below is composed
around the REAL current file (the async chat/memory logic is preserved
byte-for-byte, untouched) — never overwrite it with the stale sample below
this line, per `MEMORY.md`'s own `REQ-SB-26-US-01-T03` Pattern entry
("compose the new change around the REAL current file... re-derive any node
logic that implicitly assumed the file's old shape").

---

## Objective

Split `_invoke_action` into the corrected two-axis working-mode gate and
the existing unconditional dispatch, renamed `_execute_action` (`ADR-020`
point 2, structurally the same split `ADR-018` point 3 already established
— only the gate's own internal decision logic changes). Both
`trigger_action` (the direct Available Actions button) and `chat`'s
matched-action branch call the gate with an explicit `trigger` (`"direct"` /
`"chat"`) — `"hub_routed"` is a third valid value, reserved for a future
story, no call site produces it yet (`ADR-020` point 3). Merge
`working_mode` into `GET /agents`/`GET /agents/{agent_id}`; extend `PATCH
/agents/{agent_id}` to accept `working_mode` (`400` for an invalid enum
value).

---

## Starting State → End State

**Before / Inputs (the REAL current file, confirmed by direct read this
pass — not the original `T04`'s own now-stale "Before" narrative):**
- `agents_router.py`'s `AgentAssignmentUpdateBody` has `section_id`/
  `provider_id` only.
- `_invoke_action(agent_id, action_id) -> dict` is today's **unconditional**
  dispatch (handler lookup → Provider-availability check → dispatch) — no
  working-mode gate exists anywhere in this file yet, confirming
  `ESCALATIONS.md` → `ESC-017`'s own direct-inspection finding.
- `trigger_action` calls `_invoke_action(agent_id, action_id)` directly and
  unconditionally appends a `run_event` history entry from the result.
- `chat` is `async def`. It appends a `chat_user` history entry, then calls
  `agent_chat.handle_chat_message(agent_id, body.message)`. If matched, it
  calls `_invoke_action(agent_id, matched["matched_action_id"])` directly
  and unconditionally appends its own `run_event` entry. If NOT matched, it
  loads `agent_memory` and calls `await agent_orchestration.
  run_agent_conversation(agent_id, body.message, history_before_this_
  message, memory)` (the real `REQ-SB-25`/`REQ-SB-26` LangGraph
  conversational path), persisting any `extracted_facts` afterward. Either
  way, it appends a `chat_agent` reply entry at the end.
- `T02` has landed `working_mode_registry.get_agent_working_mode`/
  `set_agent_working_mode`/`VALID_WORKING_MODES`.
- `T03` has landed `pending_approval_registry.create_pending_approval`.
- `T09` has landed `agent_registry.get_action(agent_id, action_id)` (which
  returns each action's own new `"mutates"` field).
- `T01` has landed `vault_writer.append_agent_history_entry`'s optional
  `pending_approval_id` parameter.

**After / Outputs:**
- `_execute_action(agent_id, action_id)` — today's unconditional dispatch,
  renamed, internal logic byte-for-byte unchanged.
- `_invoke_action(agent_id, action_id, trigger)` — the corrected two-axis
  gate: **Manual + `trigger == "hub_routed"`** refuses outright (`{"status":
  "refused", ...}`, no pending record, no execution). **Supervised +
  `mutates is True`** short-circuits into a pending-approval record +
  `"proposal"` history entry, returns `{"status": "pending", ...}` —
  **never** calls `_execute_action`, regardless of `trigger`. **Supervised +
  `mutates is False`**, **Autonomous** (any trigger), and **Manual**
  (`"chat"`/`"direct"` trigger) all fall straight through to
  `_execute_action`, byte-for-byte unchanged from today's behaviour.
- `trigger_action`/`chat`'s matched-action branch call the gate with
  `trigger="direct"` / `trigger="chat"` respectively, and only append their
  own `run_event` history entry when the result's `status` is `"ok"` or
  `"error"` (not `"pending"` or `"refused"` — the gate itself already
  appended the `"proposal"` entry for `"pending"`; `"refused"` needs no
  history entry at all, mirroring Manual's own silent-skip posture on the
  background trigger, `ADR-018` point 4).
- `chat`'s own no-match conversational fallback branch (the real
  `agent_orchestration.run_agent_conversation` call) is **completely
  untouched** — this task's gate only wraps the matched-action branch, per
  `ADR-011`'s "kept, unedited" fast path (`ADR-015`'s own stated
  compatibility claim, confirmed correct by this task).
- `GET /agents`/`GET /agents/{agent_id}` additionally merge `working_mode`.
  `PATCH /agents/{agent_id}` additionally accepts `working_mode`, `400` if
  invalid.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — composed around the REAL current
  file (confirmed by direct read this pass), preserving the async
  chat/memory logic exactly:
  ```python
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel

  from app.business import (
      agent_chat,
      agent_orchestration,
      agent_registry,
      pending_approval_registry,
      provider_registry,
      section_registry,
      working_mode_registry,
  )
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


  class AgentAssignmentUpdateBody(BaseModel):
      section_id: str | None = None
      provider_id: str | None = None
      working_mode: str | None = None


  def _execute_action(agent_id: str, action_id: str) -> dict:
      """Today's unconditional dispatch — renamed from _invoke_action
      (ADR-018 point 3; ADR-020 does not change this function's own body
      at all). Never itself checks working mode — called only by
      _invoke_action's fall-through branches below, and by
      app/api/pending_approvals_router.py's Approve endpoint (T06),
      deliberately bypassing the gate entirely (the approval itself is
      the authorization; re-entering the gate would find the agent still
      Supervised and defer forever, ADR-018 point 6)."""
      handler = _ACTION_HANDLERS.get((agent_id, action_id))
      if handler is None:
          return {"status": "error", "message": "This action is not yet available."}
      provider = provider_registry.get_agent_provider(agent_id)
      if provider is None or not provider_registry.has_real_client(provider["id"]):
          provider_name = provider["name"] if provider else "This agent's selected Provider"
          return {
              "status": "error",
              "message": f"{provider_name} is not available yet — no client has been built for it.",
          }
      results = handler()
      return {"status": "ok", "message": f"Done — {len(results)} email(s) filed."}


  def _action_label(agent_id: str, action_id: str) -> str:
      agent = agent_registry.get_agent(agent_id)
      action = next((a for a in agent["actions"] if a["id"] == action_id), None) if agent else None
      return action["label"] if action else action_id


  def _invoke_action(agent_id: str, action_id: str, trigger: str) -> dict:
      """The corrected, two-axis working-mode gate (ADR-020 point 2 —
      supersedes ADR-018 point 3 in full). trigger is "chat" | "direct" |
      "hub_routed" (background never reaches this function — it has its
      own separate, structurally-unchanged gate, app/business/
      email_classification.py, T05).

      Checked BEFORE _execute_action's own handler-lookup/Provider-
      availability checks, so neither a refusal nor a proposal ever
      reveals an execute-time detail (e.g. a Provider error) the human
      hasn't earned yet by approving.

      1. Manual + trigger == "hub_routed": refuse outright — no pending
         record, no execution (REQ-SB-21-US-01 Scenario 5b / AC-07).
         Today unreachable via any real call site (ADR-017's Hub-routing
         node never itself invokes a target agent's action yet) — kept
         as named forward-looking correctness per ADR-020, not dead code.
      2. Supervised + the resolved action's own "mutates" flag is True
         (or unresolvable — fail-safe to True, ADR-020 point 1):
         short-circuits into a pending-approval record — now regardless
         of trigger (chat, direct, or hub_routed), not only a specific
         trigger value the way ADR-018 point 3 gated.
      3. Supervised + "mutates" is False: falls straight through to
         _execute_action, identical to Autonomous — the corrected
         behaviour ADR-018 point 3 did not have (it gated every chat/
         direct action uniformly, read-only or not).
      4. Autonomous (any trigger), Manual ("chat"/"direct" trigger): fall
         straight through to _execute_action, unchanged from ADR-018
         point 5's own conclusion — a matched chat message or an
         Available-Actions button press remains this codebase's one
         mechanism for "the user explicitly asking" (ADR-007/ADR-011, no
         NLU), so Manual still executes immediately on either, regardless
         of whether the action reads or writes.
      """
      mode = working_mode_registry.get_agent_working_mode(agent_id)

      if mode == "manual" and trigger == "hub_routed":
          return {
              "status": "refused",
              "message": "This agent is in Manual mode — it does not act on another agent's request.",
          }

      action = agent_registry.get_action(agent_id, action_id)
      mutates = action["mutates"] if action is not None and "mutates" in action else True

      if mode == "supervised" and mutates:
          action_label = _action_label(agent_id, action_id)
          agent = agent_registry.get_agent(agent_id)
          agent_name = agent["name"] if agent else agent_id
          approval = pending_approval_registry.create_pending_approval(
              agent_id=agent_id,
              trigger=trigger,
              action_id=action_id,
              description=f"{action_label} ({agent_name})",
          )
          message = f"Proposed — {action_label}. Awaiting your approval."
          vault_writer.append_agent_history_entry(
              agent_id, "proposal", message, pending_approval_id=approval["id"],
          )
          return {"status": "pending", "message": message, "pending_approval_id": approval["id"]}

      return _execute_action(agent_id, action_id)


  @router.get("")
  def list_agents() -> list[dict]:
      agents = agent_registry.list_agents()
      for agent in agents:
          section = section_registry.get_agent_section(agent["id"])
          agent["section_id"] = section["id"] if section else None
          provider = provider_registry.get_agent_provider(agent["id"])
          agent["provider_id"] = provider["id"] if provider else None
          agent["working_mode"] = working_mode_registry.get_agent_working_mode(agent["id"])
      return agents


  @router.get("/{agent_id}")
  def get_agent(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      section = section_registry.get_agent_section(agent_id)
      provider = provider_registry.get_agent_provider(agent_id)
      return {
          "id": agent_id,
          "name": agent["name"],
          "type": agent["type"],
          "settings": agent["settings"],
          "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
          "section_id": section["id"] if section else None,
          "section_name": section["name"] if section else None,
          "provider_id": provider["id"] if provider else None,
          "provider_name": provider["name"] if provider else None,
          "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
          "working_mode": working_mode_registry.get_agent_working_mode(agent_id),
      }


  @router.patch("/{agent_id}")
  def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      if body.section_id is not None:
          if not section_registry.set_agent_section(agent_id, body.section_id):
              raise HTTPException(status_code=404, detail="Unknown section")
      if body.provider_id is not None:
          if not provider_registry.set_agent_provider(agent_id, body.provider_id):
              raise HTTPException(status_code=404, detail="Unknown provider")
      if body.working_mode is not None:
          if not working_mode_registry.set_agent_working_mode(agent_id, body.working_mode):
              raise HTTPException(
                  status_code=400,
                  detail="Invalid working_mode — must be one of: autonomous, supervised, manual",
              )
      return get_agent(agent_id)


  @router.post("/{agent_id}/actions/{action_id}")
  def trigger_action(agent_id: str, action_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      result = _invoke_action(agent_id, action_id, trigger="direct")
      if result["status"] not in ("pending", "refused"):
          vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
      return result


  @router.post("/{agent_id}/chat")
  async def chat(agent_id: str, body: ChatMessageBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")

      # Captured BEFORE this message's own "chat_user" entry is appended,
      # below -- run_agent_conversation's own `history` argument is the
      # conversation's prior turns only; the current message is passed
      # separately as `message` (ADR-015 point 5/6). UNCHANGED by this task.
      history_before_this_message = vault_writer.load_agent_history(agent_id)

      vault_writer.append_agent_history_entry(agent_id, "chat_user", body.message)

      matched = agent_chat.handle_chat_message(agent_id, body.message)
      if matched["matched_action_id"] is not None:
          result = _invoke_action(agent_id, matched["matched_action_id"], trigger="chat")
          if result["status"] not in ("pending", "refused"):
              vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
          reply = result["message"]
          action_triggered = matched["matched_action_id"]
      else:
          # UNCHANGED by this task — the real REQ-SB-25/REQ-SB-26
          # conversational fallback (ADR-011's "kept, unedited" fast path;
          # ADR-015's own stated compatibility claim, confirmed here).
          memory = vault_writer.load_agent_memory(agent_id)
          conversation_result = await agent_orchestration.run_agent_conversation(
              agent_id, body.message, history_before_this_message, memory
          )
          reply = conversation_result.get("reply") or conversation_result.get("error")
          action_triggered = None
          extracted_facts = conversation_result.get("extracted_facts") or []
          if extracted_facts:
              vault_writer.append_agent_memory_entries(agent_id, extracted_facts)

      vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
      return {"reply": reply, "action_triggered": action_triggered}


  @router.get("/{agent_id}/history")
  def get_history(agent_id: str) -> list[dict]:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      return vault_writer.load_agent_history(agent_id)
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`); `agent_registry.py` (beyond reading it — `T09` owns writing
  it), `compass_client.py`, `app/config.py`, `agent_orchestration/*` NOT
  modified by this task.
- `_execute_action`'s own internal logic (handler lookup, Provider gate,
  dispatch, success message) must be byte-for-byte unchanged from today's
  `_invoke_action` — this task only renames it and moves the call sites, it
  does not alter its behaviour.
- `chat`'s own no-match conversational fallback branch (the
  `agent_orchestration.run_agent_conversation` call, its memory
  loading/fact-extraction persistence) must be **byte-for-byte unchanged**
  — this task's gate wraps only the matched-action branch.
- The working-mode gate must run **before** any Provider-availability
  check — a Supervised proposal must never reveal a Provider-unavailable
  error ahead of the human's own approval decision.
- Autonomous and Manual (`"chat"`/`"direct"` trigger) must produce
  **identical** `trigger_action`/`chat` responses and history entries to
  today's pre-this-task behaviour — no regression
  (`REQ-SB-21-US-01-AC-02`/`AC-06`).
- A Supervised gate short-circuit (mutating action) must never call
  `_execute_action` — the handler must not run, no Outlook/Compass/
  vault-write side effect at all, until a real `POST
  /pending-approvals/{id}/approve` call (`T06`).
- A Supervised gate pass-through (non-mutating action) and a Manual +
  `"hub_routed"` refusal must both leave zero pending-approval record and
  zero `"proposal"` history entry behind — only the true Supervised-
  mutating branch creates one.
- `list_agents`/`get_agent`'s pre-existing fields (including
  `REQ-SB-19-US-01-T04`'s own `provider_id`/`provider_name`/
  `provider_available`) must be unchanged — purely additive.
- `PATCH /agents/{agent_id}` with only `{"working_mode": ...}` must not
  touch `section_id`/`provider_id`, and vice versa — each field
  independently optional, no-op-safe, per the existing contract.

---

## Tests

<!-- REQ-SB-21-US-01-AC-02 (Autonomous unaffected, chat/direct),
AC-03 (Supervised mutating proposes+waits, chat/direct half — T05 covers
the background half), AC-05 (Supervised read-only proceeds immediately,
NEW this ADR-020 pass), AC-06 (Manual == Autonomous for chat/direct,
regardless of read/write), and AC-07 (Manual excludes hub_routed, NEW this
ADR-020 pass) are all verified here, live, against the real backend — the
only currently-real handler is ("email-capture", "run_capture_now"), so
email-capture is temporarily reassigned across Autonomous/Supervised/Manual
to prove every branch. AC-05/AC-07's own trigger values ("chat"/"direct"
read-only, and "hub_routed") have no dedicated HTTP call site for
hub_routed specifically (no real caller produces it yet, per ADR-020's own
Context) -- that one step calls _invoke_action directly via a Python shell,
matching this codebase's existing precedent for verifying an
otherwise-unreachable-via-HTTP code path (T05's own background-gate
verification already calls internal functions directly the same way).
Deliberate: several steps below trigger a real Outlook/Compass/vault-write
capture run; be careful, per MEMORY.md's standing caution. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
requests via the browser or `Invoke-RestMethod`; the one direct-Python-shell
step is called out explicitly):

1. **[REQ-SB-21-US-01-AC-02]** Confirm `email-capture`'s `working_mode` is
   `"autonomous"` (the untouched default — `GET /agents/email-capture`).
   `POST /agents/email-capture/actions/run_capture_now` (**exactly once**).
   Confirm the response is `{"status": "ok", "message": "Done — N email(s)
   filed."}` — identical in shape to this endpoint's pre-this-task
   behaviour, proving Autonomous is unaffected by the new gate for a direct
   trigger. Confirm via `GET /agents/email-capture/history` that the newest
   entry is a `"run_event"` (not `"proposal"`).
2. **[REQ-SB-21-US-01-AC-02]** With `email-capture` still `"autonomous"`,
   `POST /agents/email-capture/chat` with `{"message": "run capture now"}`.
   Confirm the response's `reply` reads `"Done — N email(s) filed."` and
   `action_triggered: "run_capture_now"` — identical to pre-this-task
   chat-triggered behaviour, proving Autonomous is unaffected for a chat
   trigger too. Separately, send `{"message": "hello, can you help me?"}`
   (no matched trigger phrase) — confirm the conversational fallback
   (`agent_orchestration.run_agent_conversation`) still runs and replies
   normally, proving this task did not disturb the no-match branch at all.
3. **[REQ-SB-21-US-01-AC-03]** (chat/direct half — `T05` covers the
   background half) `PATCH /agents/email-capture` with `{"working_mode":
   "supervised"}`. `POST /agents/email-capture/actions/run_capture_now`.
   Confirm the response is `{"status": "pending", "message": "Proposed —
   Run capture now. Awaiting your approval.", "pending_approval_id":
   "<12-hex-char id>"}` — **critically, confirm no real Outlook/Compass call
   happened** (`GET /agents/email-capture/history`'s newest entry is
   `"proposal"`, not a `"Done — N email(s) filed"` `run_event`). `GET
   /pending-approvals/<that id>` — confirm `status: "pending"`, `trigger:
   "direct"`, `action_id: "run_capture_now"`.
4. **[REQ-SB-21-US-01-AC-05]** With `email-capture` still `"supervised"`,
   `POST /agents/email-capture/actions/view_last_run` (a real,
   `"mutates": False` action per `T09`'s classification — no real handler
   exists for it, so the expected outcome is the honest `{"status":
   "error", "message": "This action is not yet available."}`, **not**
   `"pending"`). Confirm via `GET /pending-approvals?agent_id=email-
   capture&status=pending` that the count is unchanged from step 3's end
   state (no new record created) and via `GET
   /agents/email-capture/history` that no new `"proposal"` entry was
   appended — proving the gate passed a read-only action straight through
   to `_execute_action` even though the agent is Supervised, identical to
   how Autonomous would handle it.
5. **[REQ-SB-21-US-01-AC-06]** `PATCH /agents/email-capture` with
   `{"working_mode": "manual"}`. `POST
   /agents/email-capture/actions/run_capture_now` (**exactly once**).
   Confirm the response is `{"status": "ok", "message": "Done — N email(s)
   filed."}` — Manual executes a mutating action immediately for a direct
   trigger, identical to Autonomous. `POST
   /agents/email-capture/actions/view_last_run` — confirm the same honest
   `{"status": "error", "message": "This action is not yet available."}` as
   step 4 (Manual executes a **read-only** action immediately too — "manual
   mode does not depend on the action's own nature," `AC-06`'s own "whether
   the action is read-only or write/mutating" text). Confirm via history
   that no `"proposal"` entry was created for either call.
6. **[REQ-SB-21-US-01-AC-07]** With `email-capture` still `"manual"`, open a
   Python shell against the backend `.venv` (real `vault_path`) and call
   `app.api.agents_router._invoke_action("email-capture", "run_capture_now",
   trigger="hub_routed")` **directly** (no HTTP call site produces this
   trigger value yet, per `ADR-020`'s own Context — this is the one place
   this task's own gate logic is exercised via a direct function call
   rather than a real endpoint). Confirm the return value is exactly
   `{"status": "refused", "message": "This agent is in Manual mode — it
   does not act on another agent's request."}` — no pending-approval record
   created (`GET /pending-approvals?agent_id=email-capture&status=pending`
   count unchanged), no history entry appended at all (`GET
   /agents/email-capture/history` length unchanged before/after this call).
   Separately, call `_invoke_action("email-capture", "run_capture_now",
   trigger="hub_routed")` again with `email-capture` reset to
   `"autonomous"` — confirm it now executes immediately (`{"status": "ok",
   ...}`), proving the refusal is specific to Manual + hub_routed, not a
   blanket block on the trigger value itself.
7. Clean-up: `PATCH /agents/email-capture` with `{"working_mode":
   "autonomous"}`, restoring the seed default before later tasks'
   verification. Leave the `"pending"` approval record from step 3 in
   place — `T06`'s own verification approves/declines it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (partial — chat/direct triggers) — an Autonomous agent's
      chat- and direct-triggered actions are byte-for-byte unchanged from
      today's pre-this-task behaviour; the conversational no-match fallback
      is unaffected
- [ ] **AC-03** (partial — chat/direct triggers; `T05` covers background) —
      a Supervised agent's **mutating** chat/direct-triggered action
      creates a pending-approval record and a `"proposal"` history entry,
      never calls `_execute_action`
- [ ] **AC-05** (full — no background-pipeline analog exists for a
      read-only action today) — a Supervised agent's **read-only** action
      executes immediately for a chat/direct trigger, identical to
      Autonomous, creating no pending-approval record
- [ ] **AC-06** (partial — chat/direct triggers) — a Manual agent's chat/
      direct-triggered action executes immediately, identical to
      Autonomous, whether the action reads or writes
- [ ] **AC-07** (full) — a Manual agent refuses a `trigger="hub_routed"`
      invocation outright, creating no pending-approval record and no
      history entry
- [ ] `_execute_action`'s internal logic unchanged from today's
      `_invoke_action`
- [ ] `chat`'s own no-match conversational fallback branch unchanged
- [ ] `GET /agents`/`GET /agents/{agent_id}` additionally merge
      `working_mode`, purely additive
- [ ] `PATCH /agents/{agent_id}` accepts `{"working_mode"?}` independently
      of `{"section_id"?, "provider_id"?}`, `400` for an invalid value
- [ ] `agent_registry.py` (writing), `compass_client.py`, `app/config.py`,
      `agent_orchestration/*` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component — `T07` (`AgentDetailPanel.tsx`).
- The background-pipeline gate — `T05`
  (`email_classification.py::run_capture_and_record_completion`) — no
  change needed there per `ADR-020` point 4.
- `POST /pending-approvals/{id}/approve|decline` — `T06`
  (`pending_approvals_router.py`); this task only creates the pending
  record, it does not resolve it.
- The Section/Provider portions of `PATCH /agents/{agent_id}` and
  `list_agents`/`get_agent` — already landed, untouched here beyond the
  additive `working_mode` extension shown above.
- Adding/classifying the `"mutates"` field itself, or `get_action` — `T09`
  (`agent_registry.py`); this task only reads them.
- Any real call site that produces `trigger="hub_routed"` — none exists
  yet (`ADR-017`'s Hub-routing node never invokes a target agent's action);
  this task only makes the gate correctly handle that value if/when a
  future story adds one.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-020` created at
`/plan-tasks` step 1, superseding `ADR-018` points 3/5) — the human reviews
`ADR-020` and this task breakdown together; the pipeline does not halt, so
this task proceeds to `Ready` alongside the rest of the story.

**A decomposer-level implementation choice, not a new product decision:**
the `{"status": "refused", "message": "..."}` response shape for the Manual
+ `hub_routed` refusal is new — neither `ADR-018` nor `ADR-020` names a
literal status string for it, only that the gate "refuses outright." A
third status value (distinct from `"ok"`/`"error"`/`"pending"`) keeps the
three outcomes unambiguous to any future caller; `trigger_action`/`chat`
both already need to special-case `"pending"` to avoid a double history
entry, so extending that same check to `"refused"` is the minimal,
consistent extension, not a new pattern.

`REQ-SB-21`'s only currently-real, non-LLM-independent handler this pass is
`email-capture`'s `run_capture_now` (`ADR-011`) — this is why every step
above reassigns `email-capture` itself rather than an agent with no real
handler at all (which would already short-circuit via the pre-existing
"not yet available" branch, proving nothing new about this task's own
gate). Step 4/5's `view_last_run` checks intentionally accept the honest
"not yet available" outcome as success criteria — the AC being verified is
the *gate's* pass-through decision, not whether a real handler exists for
that specific action (no task in this story builds one).

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** Read the REAL
current `src/backend/app/api/agents_router.py` before writing anything,
confirming this task's own top-of-file drift note: `chat` is `async
def` and calls `await agent_orchestration.run_agent_conversation(...)`,
**and** a second, un-anticipated drift the task file itself did not
know about — `SPRINT-020` (`REQ-SB-20-US-01`, built after this task was
authored) had already added `agent_keywords` import, a `keywords` field
on `AgentAssignmentUpdateBody`, and a `"keywords"` key on `GET
/agents/{agent_id}`'s response. Composed the corrected two-axis gate
around the REAL current file, preserving both the async chat/memory
logic and the keywords support byte-for-byte, rather than overwriting
with the task's own stale sample — the same "never overwrite with a
stale sample" pattern `MEMORY.md`'s `REQ-SB-26-US-01-T03` Pattern entry
and this task's own top note already named. `_invoke_action`/
`_execute_action` split exactly as designed; `working_mode` merged
additively alongside the pre-existing `keywords`/`section_id`/
`provider_id` fields on `GET`/`PATCH`.

**Live verification** (real backend, port 8002 — the project's usual
8001 dev port was found already occupied by a stale, still-live
`--reload` process from before this session; a fresh instance was
started on 8002 rather than force-killing an unrelated live process —
see this task's own "Assumptions" note below):

- **[AC-02]** (chat/direct, Autonomous unaffected) `email-capture`
  confirmed `"autonomous"`. `POST .../actions/run_capture_now` →
  `{"status": "ok", "message": "Done — 0 email(s) filed."}`, newest
  history entry `"run_event"` — byte-identical shape to pre-task
  behaviour. Chat `"run capture now"` → `reply: "Done — 0 email(s)
  filed."`, `action_triggered: "run_capture_now"`. Chat `"hello, can
  you help me?"` (no match) → real conversational fallback replied
  normally, confirming the no-match branch is untouched. PASS.
- **[AC-03]** (chat/direct half) `PATCH working_mode: "supervised"`.
  `POST .../actions/run_capture_now` →
  `{"status": "pending", "message": "Proposed — Run capture now.
  Awaiting your approval.", "pending_approval_id": "6097ea1dc9bf"}` —
  confirmed via history (newest entry `"proposal"`, no `"Done — ..."`
  entry) that no real Outlook/Compass call happened; `GET
  /pending-approvals/6097ea1dc9bf` confirmed `status: "pending"`,
  `trigger: "direct"`, `action_id: "run_capture_now"`. PASS.
- **[AC-05]** (Supervised read-only proceeds immediately) Still
  Supervised, `POST .../actions/view_last_run` (a real `mutates: False`
  action, no real handler) → the honest `{"status": "error", "message":
  "This action is not yet available."}`, **not** `"pending"`; pending
  count for `email-capture` unchanged (1→1), no new `"proposal"` entry
  appended. Confirms the gate passed a read-only action straight
  through to `_execute_action` even while Supervised. PASS.
- **[AC-06]** (Manual == Autonomous for chat/direct) `PATCH
  working_mode: "manual"`. `POST .../actions/run_capture_now` →
  `{"status": "ok", ...}` (executes a mutating action immediately).
  `POST .../actions/view_last_run` → the same honest "not yet
  available" (executes a read-only action immediately too — Manual
  does not depend on the action's own nature for a direct/chat ask). No
  `"proposal"` entries created for either. PASS.
- **[AC-07]** (Manual excludes `hub_routed`; full) Direct Python-shell
  call (no real HTTP call site produces `trigger="hub_routed"` yet, per
  `ADR-020`'s own Context): with `email-capture` explicitly set
  `"manual"`, `_invoke_action("email-capture", "run_capture_now",
  trigger="hub_routed")` → exactly `{"status": "refused", "message":
  "This agent is in Manual mode — it does not act on another agent's
  request."}` — pending count unchanged (1→1), history length unchanged
  (113→113, zero entries appended). With the same agent reset to
  `"autonomous"`, the identical call → `{"status": "ok", ...}` —
  confirming the refusal is specific to Manual+hub_routed, not a
  blanket block on the trigger value. PASS. **Deviation from the task's
  own script, corrected during verification, recorded honestly:** the
  first attempt at this check was killed mid-flight by this shell's own
  2-minute default timeout (during the real `autonomous`+`hub_routed`
  capture call), which left `email-capture`'s mode already flipped to
  `"autonomous"` by the time a second, naively-labelled "manual" check
  ran against it — a false-negative-shaped, invalid run, caught before
  being reported as a pass (the printed "manual" label did not match
  the real, already-autonomous mode). Rewritten with an explicit
  `set_agent_working_mode("email-capture", "manual")` at the top and
  `flush=True` output, then re-run backgrounded with a longer effective
  timeout — the PASS recorded above is from that corrected run.
- Cleanup (step 7): `email-capture` and `meeting-capture` both reset to
  `"autonomous"`; the step-3 pending record was left in place for `T06`
  to approve, per this task's own instruction (later resolved during
  `T06`/`T07`'s own verification, see their Implementation Logs).

**Assumptions logged for human spot-check (scope-internal judgement
calls, not escalations):**
- Verified against a second `uvicorn` instance on port **8002**, not
  the project's usual 8001, because an already-running `--reload`
  process (PID `5648`, started before this session) was found bound to
  8001. `Get-Process`/`taskkill` both reported that PID as not
  existing, yet `Get-NetTCPConnection` continued to show it as the
  socket's owner even after — an apparent OS-level stale-listener
  condition on this host, not a normal "surviving reloader child"
  (`MEMORY.md`'s own precedent for that antipattern). Not force-killed
  (nothing to force-kill); a second, independent instance on 8002 was
  used instead so verification was not blocked. Both instances end up
  serving the same edited code (8001's own `--reload` picked up the
  same file changes independently), so no incorrect-code risk, but two
  concurrent `APScheduler` background-tick jobs were briefly live
  against the same vault during this session — a real environmental
  finding, not a code defect; see `MEMORY.md`.
- The `{"status": "refused", ...}` response shape for the Manual +
  `hub_routed` refusal (already flagged as a decomposer-level, not
  product-level, choice in this task's own Notes) was built and
  verified exactly as specified — no change.

Gate: `clear` — every locked AC this task carries was verified live; no
MUST-FLAG trigger fired (the second file-drift finding is a
scope-internal composition detail, not an out-of-scope event — no new
dependency, no shared-interface change beyond what `ADR-020` already
specified, no ADR deviation).

---

---

## SUPERSEDED — original `ADR-018`-only version of this task (2026-08-12)

**Kept unedited below, for history only — do NOT build against this
section.** Rewritten in full above, against `ADR-020`'s corrected two-axis
gate and the REAL current (drifted) `agents_router.py`, per this task's own
"Rewritten in place" note at the top of this file.

### Objective (superseded)

Split `_invoke_action` into a thin working-mode gate and the existing
unconditional dispatch, renamed `_execute_action` (`ADR-018` point 3).
Both `trigger_action` (the direct Available Actions button) and `chat`'s
matched-action branch now call the gate with an explicit `trigger`
(`"direct"` / `"chat"`) instead of calling dispatch directly. Merge
`working_mode` into `GET /agents`/`GET /agents/{agent_id}`; extend `PATCH
/agents/{agent_id}` to accept `working_mode` (`400` for an invalid enum
value).

### Files to Modify (superseded — stale sample, predates REQ-SB-25/26's
real async chat/memory logic; do not use)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import (
    agent_chat,
    agent_registry,
    pending_approval_registry,
    provider_registry,
    section_registry,
    working_mode_registry,
)
from app.business.email_classification import run_capture_and_record_completion
from app.data_access import vault_writer

router = APIRouter(prefix="/agents")

_ACTION_HANDLERS = {
    ("email-capture", "run_capture_now"): run_capture_and_record_completion,
}


class ChatMessageBody(BaseModel):
    message: str


class AgentAssignmentUpdateBody(BaseModel):
    section_id: str | None = None
    provider_id: str | None = None
    working_mode: str | None = None


def _execute_action(agent_id: str, action_id: str) -> dict:
    handler = _ACTION_HANDLERS.get((agent_id, action_id))
    if handler is None:
        return {"status": "error", "message": "This action is not yet available."}
    provider = provider_registry.get_agent_provider(agent_id)
    if provider is None or not provider_registry.has_real_client(provider["id"]):
        provider_name = provider["name"] if provider else "This agent's selected Provider"
        return {
            "status": "error",
            "message": f"{provider_name} is not available yet — no client has been built for it.",
        }
    results = handler()
    return {"status": "ok", "message": f"Done — {len(results)} email(s) filed."}


def _action_label(agent_id: str, action_id: str) -> str:
    agent = agent_registry.get_agent(agent_id)
    action = next((a for a in agent["actions"] if a["id"] == action_id), None) if agent else None
    return action["label"] if action else action_id


def _invoke_action(agent_id: str, action_id: str, trigger: str) -> dict:
    mode = working_mode_registry.get_agent_working_mode(agent_id)
    if mode == "supervised":
        action_label = _action_label(agent_id, action_id)
        agent = agent_registry.get_agent(agent_id)
        agent_name = agent["name"] if agent else agent_id
        approval = pending_approval_registry.create_pending_approval(
            agent_id=agent_id,
            trigger=trigger,
            action_id=action_id,
            description=f"{action_label} ({agent_name})",
        )
        message = f"Proposed — {action_label}. Awaiting your approval."
        vault_writer.append_agent_history_entry(
            agent_id, "proposal", message, pending_approval_id=approval["id"],
        )
        return {"status": "pending", "message": message, "pending_approval_id": approval["id"]}
    return _execute_action(agent_id, action_id)


@router.get("")
def list_agents() -> list[dict]:
    agents = agent_registry.list_agents()
    for agent in agents:
        section = section_registry.get_agent_section(agent["id"])
        agent["section_id"] = section["id"] if section else None
        provider = provider_registry.get_agent_provider(agent["id"])
        agent["provider_id"] = provider["id"] if provider else None
        agent["working_mode"] = working_mode_registry.get_agent_working_mode(agent["id"])
    return agents


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    section = section_registry.get_agent_section(agent_id)
    provider = provider_registry.get_agent_provider(agent_id)
    return {
        "id": agent_id,
        "name": agent["name"],
        "type": agent["type"],
        "settings": agent["settings"],
        "actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
        "section_id": section["id"] if section else None,
        "section_name": section["name"] if section else None,
        "provider_id": provider["id"] if provider else None,
        "provider_name": provider["name"] if provider else None,
        "provider_available": provider_registry.has_real_client(provider["id"]) if provider else False,
        "working_mode": working_mode_registry.get_agent_working_mode(agent_id),
    }


@router.patch("/{agent_id}")
def update_agent_assignment(agent_id: str, body: AgentAssignmentUpdateBody) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    if body.section_id is not None:
        if not section_registry.set_agent_section(agent_id, body.section_id):
            raise HTTPException(status_code=404, detail="Unknown section")
    if body.provider_id is not None:
        if not provider_registry.set_agent_provider(agent_id, body.provider_id):
            raise HTTPException(status_code=404, detail="Unknown provider")
    if body.working_mode is not None:
        if not working_mode_registry.set_agent_working_mode(agent_id, body.working_mode):
            raise HTTPException(
                status_code=400,
                detail="Invalid working_mode — must be one of: autonomous, supervised, manual",
            )
    return get_agent(agent_id)


@router.post("/{agent_id}/actions/{action_id}")
def trigger_action(agent_id: str, action_id: str) -> dict:
    agent = agent_registry.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")
    result = _invoke_action(agent_id, action_id, trigger="direct")
    if result["status"] != "pending":
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
        result = _invoke_action(agent_id, matched["matched_action_id"], trigger="chat")
        if result["status"] != "pending":
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

(The rest of the superseded version's Constraints/Tests/Acceptance
Criteria — tagged against the OLD `AC-02`/`AC-03`/`AC-06` numbering, from
before the 2026-08-12 re-spec added Scenarios 4/5b — are omitted here for
brevity; the live git history of this file (prior commit) carries the full
original text if ever needed. The rewritten version above, and the current
`REQ-SB-21-US-01-AC-02`/`AC-03`/`AC-05`/`AC-06`/`AC-07` numbering, are the
only ones to build against.)
