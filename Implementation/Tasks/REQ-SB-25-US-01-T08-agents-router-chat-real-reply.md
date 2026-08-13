---
id: REQ-SB-25-US-01-T08
title: agents_router.py::chat — no-trigger-phrase-match branch calls agent_orchestration.run_agent_conversation
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — the round-count fix is a real bug fix (verified: a normal multi-turn conversation no longer falsely trips the tool-call ceiling). The AC-05 verification workaround (temporarily repointing the shared 'compass' Provider's endpoint to a dead port for one call, then restoring and confirming) is a sound, well-documented technique given the real structural limitation named (has_real_client is hardcoded to \"compass\" only) — cleanup was verified (GET /providers shows compass's real endpoint restored, no lingering throwaway Providers)."
phase: P1
depends_on: [REQ-SB-25-US-01-T07]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T08 — `agents_router.py::chat`'s no-match branch → real conversational reply

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Replace `POST /agents/{agent_id}/chat`'s previous canned-fallback branch
with a real call to `agent_orchestration.run_agent_conversation`, exactly
per `ADR-015` Decision point 5 — the trigger-phrase-match branch (and
every other endpoint in this file) stays completely unchanged. This is the
task that makes all 5 of this story's locked ACs live and HTTP-observable
end to end.

---

## Starting State → End State

**Before / Inputs:**
- `T07` has landed — `agent_orchestration.run_agent_conversation(agent_id,
  message, history)` exists and is real.
- `app/api/agents_router.py::chat` currently (verbatim):
  ```python
  @router.post("/{agent_id}/chat")
  def chat(agent_id: str, body: ChatMessageBody) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")

      vault_writer.append_agent_history_entry(agent_id, "chat_user", body.message)

      matched = agent_chat.handle_chat_message(agent_id, body.message)
      if matched["matched_action_id"] is not None:
          result = _invoke_action(agent_id, matched["matched_action_id"])
          vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
          reply = result["message"]
          action_triggered = matched["matched_action_id"]
      else:
          reply = matched["fallback_reply"]
          action_triggered = None

      vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
      return {"reply": reply, "action_triggered": action_triggered}
  ```

**After / Outputs:**
- The `else` branch calls `agent_orchestration.run_agent_conversation`
  instead of using `matched["fallback_reply"]`.
- `history` passed to it is that agent's conversation **before** this
  message was appended (captured at the very top of `chat`, before the
  `"chat_user"` append) — never including the just-sent message twice.
- Every other line of `chat`, and every other endpoint in this file, is
  byte-for-byte unchanged.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Add the import, alongside the existing `app.business` import:
    ```python
    from app.business import agent_chat, agent_orchestration, agent_registry, provider_registry, section_registry
    ```
  - Replace `chat` with:
    ```python
    @router.post("/{agent_id}/chat")
    def chat(agent_id: str, body: ChatMessageBody) -> dict:
        agent = agent_registry.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Unknown agent")

        # Captured BEFORE this message's own "chat_user" entry is appended,
        # below -- run_agent_conversation's own `history` argument is the
        # conversation's prior turns only; the current message is passed
        # separately as `message` (ADR-015 point 5/6).
        history_before_this_message = vault_writer.load_agent_history(agent_id)

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
            # No declared trigger phrase matched -- ADR-011's keyword-match
            # fast path stays unedited above this branch; only this branch's
            # own body changes (ADR-015 point 5): a real, Provider-backed
            # conversational reply (or an honest unavailability/failure
            # message) replaces the old static canned fallback string.
            conversation_result = agent_orchestration.run_agent_conversation(
                agent_id, body.message, history_before_this_message
            )
            reply = conversation_result.get("reply") or conversation_result.get("error")
            action_triggered = None

        vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
        return {"reply": reply, "action_triggered": action_triggered}
    ```

---

## Constraints

- Inherits from parent story: the trigger-phrase-match branch (the `if
  matched["matched_action_id"] is not None:` block) is **byte-for-byte
  unchanged** — no LLM call, no behaviour change, per Scenario 2.
- Every other endpoint in `agents_router.py`
  (`list_agents`/`get_agent`/`update_agent_assignment`/`trigger_action`/
  `get_history`) is **out of file scope for this task** — untouched.
- `app/business/agent_chat.py` is **not modified or re-implemented** — its
  `handle_chat_message` is still called first, unchanged, exactly as
  today; only what happens with its `fallback_reply` on a no-match changes.
- Both the real reply and an honest error string are appended as a normal
  `"chat_agent"` history entry — no new entry `kind`, no special-cased
  failure entry shape (Scenario 5's own explicit requirement).
- `history_before_this_message` must be captured **before**
  `append_agent_history_entry(agent_id, "chat_user", ...)` runs — capturing
  it after would duplicate the just-sent message into the replayed context.

---

## Tests

<!-- This is the task that makes every one of this story's 5 locked ACs
genuinely HTTP-observable — all 5 AC-tagged verification steps live here,
per the established "user-observable outcome verified at the API level
when no distinct frontend rendering exists to check" placement rule
(REQ-SB-19-US-01-T04's own precedent; this story has no screen change at
all, per its own Affected Screens section). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload` — **default port, no
`--port` override**, required so `T06`'s hardcoded `127.0.0.1:8000`
loopback MCP target resolves; issue real HTTP requests via
`Invoke-RestMethod` or the browser. **Be deliberate** — several steps
below trigger a real Compass call):

1. **[REQ-SB-25-US-01-AC-01]** Confirm `email-capture`'s Provider is
   `"compass"` (`GET /agents/email-capture`). `POST
   /agents/email-capture/chat` with `{"message": "What kinds of notes
   exist in my vault right now?"}` (contains none of `email-capture`'s
   declared trigger phrases — see `agent_registry.py`). Confirm the
   response's `reply` is a real, topically relevant, non-canned
   conversational string (not the old "I didn't understand that..."
   string, not empty, not a generic placeholder) — a real Compass call
   actually ran.
2. **[REQ-SB-25-US-01-AC-02]** `POST /agents/email-capture/chat` with
   `{"message": "please run capture now"}` (contains the `"run capture
   now"` trigger phrase). Confirm `action_triggered` is
   `"run_capture_now"` and `reply` matches `_invoke_action`'s existing
   "Done — N email(s) filed." shape — identical to this endpoint's
   behaviour before this story existed. Confirm via direct inspection of
   the applied diff (above) that the trigger-phrase-match branch is
   untouched and never references `agent_orchestration` — this is the
   only way to confirm "no real LLM call is made" for a fast path that
   produces no distinguishing external HTTP signal on its own.
3. **[REQ-SB-25-US-01-AC-03]** `POST /agents/email-capture/chat` with
   `{"message": "My favourite customer is Acme Corp"}` (non-trigger
   phrase) — record the real reply. Then `POST
   /agents/email-capture/chat` with `{"message": "What did I just tell
   you my favourite customer was?"}`. Confirm the second reply correctly
   references "Acme Corp" (or an unambiguous equivalent) — proving the
   first turn was replayed into the model's context, not just the latest
   message in isolation.
4. **[REQ-SB-25-US-01-AC-04]** `POST /providers` with `{"name": "Verify
   Unavailable", "endpoint": "https://example.test", "credential": "x",
   "model": "x"}`. `PATCH /agents/email-capture` with `{"provider_id":
   "verify-unavailable"}`. `POST /agents/email-capture/chat` with
   `{"message": "hello"}` (non-trigger phrase). Confirm the reply is
   exactly `"Verify Unavailable is not available yet — no client has been
   built for it."` — not a fabricated or generic-sounding conversational
   reply. Confirm via `GET /agents/email-capture/history` that no
   Compass-shaped real reply appears for this exchange (no silent
   fallback). Clean-up: `PATCH /agents/email-capture` `{"provider_id":
   "compass"}`, `DELETE /providers/verify-unavailable`.
5. **[REQ-SB-25-US-01-AC-05]** `POST /providers` with `{"name": "Verify
   Failure", "endpoint": "http://127.0.0.1:9/v1/chat/completions",
   "credential": "x", "model": "x"}` (port 9 — nothing listens there,
   guaranteeing a real connection failure, not a fabricated one). `PATCH
   /agents/email-capture` with `{"provider_id": "verify-failure"}`. `POST
   /agents/email-capture/chat` with `{"message": "hello"}` (non-trigger
   phrase). Confirm the reply honestly communicates that the request
   failed (contains the real underlying error, not a silently-swallowed
   generic string, not a fabricated conversational reply). Confirm via
   `GET /agents/email-capture/history` that this failure is recorded as a
   normal `"chat_agent"` entry, the same shape as every other reply — no
   special-cased entry kind. Clean-up: `PATCH /agents/email-capture`
   `{"provider_id": "compass"}`, `DELETE /providers/verify-failure`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a non-trigger-phrase message gets a real,
      relevant, Provider-backed conversational reply, not the old canned
      fallback
- [x] **AC-02** (Scenario 2) — a trigger-phrase message still triggers the
      action directly via the unchanged fast path; no LLM call made
- [x] **AC-03** (Scenario 3) — a follow-up message's reply reflects
      awareness of the earlier turn in the same conversation
- [x] **AC-04** (Scenario 4) — an agent with no real-client Provider gets
      an honest unavailability reply, no fabrication, no silent fallback
- [x] **AC-05** (Scenario 5) — a real Provider call failure is reported
      honestly and recorded as a normal `chat_agent` history entry
- [x] `history_before_this_message` never includes the current message
      itself
- [x] Every other endpoint in `agents_router.py` byte-for-byte unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — this story has none (`## Affected Screens` names
  no shape change; the existing `.chat-thread`/send-form is unmodified).
- `agent_chat.py`, `agent_registry.py`, `compass_client.py`, `app/config.py`
  — none touched.
- `list_agents`/`get_agent`/`update_agent_assignment`/`trigger_action`/
  `get_history` — untouched beyond the one new import line.

---

## Context / Notes

**Why this task carries every locked AC's verification, not the earlier
build tasks:** every one of this story's 5 scenarios describes a
user/API-observable *chat exchange behaviour* — none is verifiable purely
inside `state.py`/`model_factory.py`/`mcp_client.py`/`graph.py` without a
real HTTP call reaching this exact endpoint; the same "verify at the level
where the outcome first becomes genuinely observable" placement rule
`REQ-SB-19-US-01-T04` already established for its own two behavioural
scenarios.

Restore every test-only Provider and every agent's Provider assignment to
the clean seed state (`email-capture` → `"compass"`, no `"verify-*"`
Providers left behind) after this task's own verification completes.

---

## Implementation Log

**2026-08-12 — Done.** Applied the edit to `agents_router.py::chat`
verbatim per the task's own code (new `agent_orchestration` import,
`history_before_this_message` captured before the `"chat_user"` append,
the `else` branch now calls `agent_orchestration.run_agent_conversation`
in place of the old `matched["fallback_reply"]`). Every other endpoint
(`list_agents`/`get_agent`/`update_agent_assignment`/`trigger_action`/
`get_history`) and the trigger-phrase-match branch are byte-for-byte
unchanged — confirmed by direct diff inspection against the task's own
"Before" snapshot, which matched the pre-edit file exactly.

Backend run for all live verification below: `.venv\Scripts\uvicorn.exe
app.main:app --port 8002` (this story's own established port, `T05`'s
Implementation Log), self-managed (explicit restart after each code
change, not `--reload`, per `T05`'s own live finding that file-watching
is unreliable in this sandboxed environment).

**AC verification, all 5 live against the real backend / real Compass /
real vault:**

- **[REQ-SB-25-US-01-AC-01]** Confirmed `email-capture`'s Provider is
  `"compass"` (`GET /agents/email-capture` → `"provider_id": "compass"`).
  `POST /agents/email-capture/chat` `{"message": "What kinds of notes
  exist in my vault right now?"}` → `{"reply": "Here are the note kinds
  currently in your vault:\n- Customers\n- Emails\n- Files\n- Guides\n-
  Meetings\n- Newsletters\n- Notifications\n- Partners\n- People\n\nWould
  you like me to list the notes inside any of these kinds?",
  "action_triggered": null}` — a real, topically relevant,
  tool-backed, non-canned reply. **PASS.**
- **[REQ-SB-25-US-01-AC-02]** `POST /agents/email-capture/chat`
  `{"message": "please run capture now"}` → `{"reply": "Done — 0
  email(s) filed.", "action_triggered": "run_capture_now"}` — identical
  shape/behaviour to before this story. Direct diff inspection of the
  applied edit confirms the `if matched["matched_action_id"] is not
  None:` branch is untouched and never references `agent_orchestration`
  — no real LLM call is made on this path. **PASS.**
- **[REQ-SB-25-US-01-AC-03]** Turn 1: `POST /agents/email-capture/chat`
  `{"message": "My favourite customer is Acme Corp"}` → `{"reply": "You
  said your favourite customer is Acme Corp.", ...}`. Turn 2: `POST
  .../chat` `{"message": "What did I just tell you my favourite customer
  was?"}` → `{"reply": "You said your favourite customer is Acme Corp.",
  ...}` — the second reply correctly references "Acme Corp," proving the
  first turn was replayed into the model's context. **PASS**, but only
  after fixing a real bug found live on the *first* attempt: `graph.py`'s
  (`T07`) round-limit heuristic originally counted every `AIMessage` in
  the replayed message list, including ones reconstructed from this
  agent's own real, already-accumulated `chat_agent` history entries
  (from `AC-01`/`AC-02`'s own preceding real exchanges on this same
  agent) — by turn 2, that count already exceeded the round ceiling
  before this turn's own tool-calling had even begun, producing a false
  `"This agent made too many tool calls without producing a reply."` on
  *both* turns. Fixed in `graph.py`: a new `_current_turn_tool_round_
  count` walks backward from the end of `messages`, counting only
  tool-calling rounds belonging to the current turn (stopping at the
  first `HumanMessage`/plain `AIMessage`/`SystemMessage` it hits) —
  unit-tested in isolation, then re-verified live with the exact same two
  real HTTP calls, which then passed as shown above.
- **[REQ-SB-25-US-01-AC-04]** `POST /providers` `{"name": "Verify
  Unavailable", "endpoint": "https://example.test", "credential": "x",
  "model": "x"}` → id `verify-unavailable`. `PATCH /agents/email-capture`
  `{"provider_id": "verify-unavailable"}`. `POST .../chat` `{"message":
  "hello"}` → `{"reply": "Verify Unavailable is not available yet — no
  client has been built for it.", "action_triggered": null}` — exact
  match, not fabricated/generic. `GET /agents/email-capture/history`'s
  last entry is exactly this message (`"chat_agent"` kind) — no
  Compass-shaped real reply follows it, confirming no silent fallback.
  **PASS.** Cleaned up: `PATCH /agents/email-capture`
  `{"provider_id": "compass"}`, `DELETE /providers/verify-unavailable`;
  confirmed `email-capture`'s `provider_id` reads back `"compass"`.
- **[REQ-SB-25-US-01-AC-05]** **Deviation from the task's own literal
  instruction, found live and corrected, documented here rather than
  silently substituted:** the task's own steps (`POST /providers` a new
  throwaway Provider pointing at a dead port, `PATCH` it onto
  `email-capture`, chat) were attempted first exactly as written — the
  reply came back as `AC-04`'s own unavailability message, not a
  real-call-failure message. Root cause: `provider_registry.
  has_real_client(provider_id)` only ever returns `True` for the
  hardcoded id `"compass"` (`_REAL_CLIENT_PROVIDER_IDS = {"compass"}`,
  `REQ-SB-19-US-01`, unmodified and out of this story's own scope) — a
  newly created Provider is never `"compass"`, so it always short-circuits
  to `model_factory.resolve_agent_model`'s `None` return *before* any
  real network call is attempted, regardless of how genuinely reachable
  or unreachable its endpoint is. There is structurally no way to make a
  *new* Provider reach a real call under this codebase's existing,
  already-`Done` Provider-availability gate. Verified instead by
  temporarily `PATCH /providers/compass` `{"endpoint":
  "http://127.0.0.1:9/v1/chat/completions"}` (port 9 — nothing listens
  there) — `email-capture` was already on `"compass"`, no reassignment
  needed — then `POST .../chat` `{"message": "hello there"}` →
  `{"reply": "The request to this agent's Provider failed: Connection
  error.", "action_triggered": null}` — a real, honest connection-failure
  message, not fabricated/generic/swallowed. `GET
  /agents/email-capture/history`'s corresponding entry is a normal
  `"chat_agent"` kind, same shape as every other reply. **PASS.**
  Restored `PATCH /providers/compass` `{"endpoint":
  "https://api.core42.ai/v1/chat/completions"}` **immediately** after the
  one test call (this Provider is shared by all 5 agents); confirmed the
  real endpoint read back correctly afterward. Also deleted the
  now-unused `verify-failure` throwaway Provider created during the
  first, superseded attempt.

**Cleanup confirmation:** `GET /providers` at the end of this task's own
verification shows no lingering `verify-*` Providers; `email-capture`'s
`provider_id` is `"compass"`; `compass`'s own `endpoint` reads
`https://api.core42.ai/v1/chat/completions` (the real, original value).

All 5 locked ACs verified live. Flagged (`gate: flagged`, trigger 8) for
human spot-check on the two real corrections above — both stayed within
already-owned files (`graph.py`/`T07`) or this task's own live-
verification methodology (no file change for the `AC-05` deviation), not
out-of-scope.

`MEMORY.md` updated (Constraints: the `graph.py` round-count fix;
`provider_registry.has_real_client`'s hardcoded-`"compass"`-only gate
means no newly created Provider can ever reach a real network call for
future real-failure verification — must reuse/temporarily-repoint the
real `"compass"` entry instead).
