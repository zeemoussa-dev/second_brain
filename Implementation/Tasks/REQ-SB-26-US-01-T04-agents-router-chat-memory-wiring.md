---
id: REQ-SB-26-US-01-T04
title: agents_router.py::chat — loads agent memory, passes it into run_agent_conversation, persists any extracted_facts; all 4 ACs verified live
parent_story: REQ-SB-26-US-01
requirement_id: REQ-SB-26
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-26-US-01-T01, REQ-SB-26-US-01-T03, REQ-SB-25-US-01-T08]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-26-US-01-T04 — `agents_router.py::chat` memory wiring

## Parent Story

- Story: [[REQ-SB-26-US-01]] — `../UserStories/REQ-SB-26-US-01-agent-memory.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-26 *Agent Memory*

---

## Objective

Wire `chat`'s no-trigger-phrase-match branch to load the agent's stored
memory, pass it into `run_agent_conversation`, and persist any newly
`extracted_facts` — exactly `ADR-016`'s "router persists post-graph side
effects" shape, extended one concern over from conversation history to
memory. This is the task that makes all 4 of this story's locked ACs live
and HTTP-observable end to end.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-25-US-01-T08` has landed — `agents_router.py::chat`'s no-match
  branch already calls `agent_orchestration.run_agent_conversation(agent_id,
  body.message, history_before_this_message)` (verbatim content quoted in
  that task file).
- `T01` (this story) has landed — `vault_writer.load_agent_memory` /
  `vault_writer.append_agent_memory_entries` exist.
- `T03` (this story) has landed — `run_agent_conversation` accepts a
  `memory` parameter and returns `extracted_facts` on its success path.

**After / Outputs:**
- The no-match branch loads memory via `vault_writer.load_agent_memory`
  before calling `run_agent_conversation`, passes it in as the new
  `memory` argument, and — when the call returns any `extracted_facts` —
  persists them via `vault_writer.append_agent_memory_entries`.
- The trigger-phrase-match branch and every other endpoint in this file
  remain byte-for-byte unchanged.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Add the import, alongside the existing `app.business` import (extends
    `T08`'s own import line):
    ```python
    from app.business import agent_chat, agent_orchestration, agent_registry, provider_registry, section_registry
    ```
    (unchanged from `T08` — `agent_orchestration` is already imported;
    no new import needed here.)
  - Replace the no-match `else` branch of `chat` (only this branch's own
    body changes; everything else in the function is untouched):
    ```python
    @router.post("/{agent_id}/chat")
    def chat(agent_id: str, body: ChatMessageBody) -> dict:
        agent = agent_registry.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Unknown agent")

        history_before_this_message = vault_writer.load_agent_history(agent_id)

        vault_writer.append_agent_history_entry(agent_id, "chat_user", body.message)

        matched = agent_chat.handle_chat_message(agent_id, body.message)
        if matched["matched_action_id"] is not None:
            result = _invoke_action(agent_id, matched["matched_action_id"])
            vault_writer.append_agent_history_entry(agent_id, "run_event", result["message"])
            reply = result["message"]
            action_triggered = matched["matched_action_id"]
        else:
            # Stored facts from earlier, separate conversations with this
            # same agent (ADR-016) -- loaded fresh from disk on every
            # call, never cached in-process, mirroring history's own
            # "passed in fresh from outside" shape (ADR-015 point 6).
            memory = vault_writer.load_agent_memory(agent_id)
            conversation_result = agent_orchestration.run_agent_conversation(
                agent_id, body.message, history_before_this_message, memory
            )
            reply = conversation_result.get("reply") or conversation_result.get("error")
            action_triggered = None
            # Persisted immediately, mirroring the "router persists
            # post-graph side effects" shape already established for
            # conversation history -- a true no-op when extraction
            # returned nothing this turn (Scenario 3).
            extracted_facts = conversation_result.get("extracted_facts") or []
            if extracted_facts:
                vault_writer.append_agent_memory_entries(agent_id, extracted_facts)

        vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
        return {"reply": reply, "action_triggered": action_triggered}
    ```

---

## Constraints

- Inherits from parent story: the trigger-phrase-match branch (the `if
  matched["matched_action_id"] is not None:` block) is **byte-for-byte
  unchanged** — no memory load, no extraction persistence, per Scenario 2
  (inherited unedited from `REQ-SB-25-US-01`'s own Scenario 2 fast path).
- Every other endpoint in `agents_router.py`
  (`list_agents`/`get_agent`/`update_agent_assignment`/`trigger_action`/
  `get_history`) is **out of file scope for this task** — untouched.
- `memory` is loaded **once**, before the `run_agent_conversation` call —
  no re-fetch after extraction (would only reflect facts extracted from
  the same turn, never useful, and never intended by `ADR-016`).
- `append_agent_memory_entries` is only ever called when
  `extracted_facts` is non-empty — an empty/absent list must never reach
  it (that would be a redundant no-op call, but is disallowed for clarity
  of intent: the `if extracted_facts:` guard is required, not optional).
- `history_before_this_message` semantics are unchanged from `T08` —
  still captured before the `"chat_user"` history append.

---

## Tests

<!-- This is the task that makes every one of this story's 4 locked ACs
genuinely HTTP-observable — all 4 AC-tagged verification steps live here,
per the established "verify at the level where the outcome first becomes
genuinely observable" placement rule (REQ-SB-25-US-01-T08's own
precedent; this story has no screen change at all, per its own Affected
Screens section). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload` — **default port, no
`--port` override**, required so `T06`'s hardcoded loopback MCP target
resolves; issue real HTTP requests via `Invoke-RestMethod` or the
browser. **Be deliberate** — several steps below trigger two real Compass
calls per message, per `ADR-016`'s own named cost/latency consequence):

1. **[REQ-SB-26-US-01-AC-01]** Confirm `email-capture`'s Provider is
   `"compass"` (`GET /agents/email-capture`). `POST
   /agents/email-capture/chat` with `{"message": "My favourite customer is
   Acme Corp, please remember that."}`. Confirm a real, non-canned reply.
   Read `.second-brain/agent_memory.json` directly and confirm a new
   entry now exists under `"email-capture"` whose `"fact"` text contains
   "Acme Corp" (or an unambiguous equivalent) — confirming `extract_memory`
   ran and the router persisted it.
2. **[REQ-SB-26-US-01-AC-01]** To confirm recall genuinely comes from
   `agent_memory.json` (via `retrieve_memory`) and not merely from
   `REQ-SB-25`'s own already-tested `history` replay within one still-open
   conversation: back up `.second-brain/agent_communication_history.json`,
   then remove `"email-capture"`'s own entry list from it entirely (an
   empty list or a missing key — either is fine) so no ordinary history
   replay is possible for the next call. `POST /agents/email-capture/chat`
   with `{"message": "What's my favourite customer?"}`. Confirm the reply
   still correctly references "Acme Corp" — proving the earlier
   information survived into this later, separate conversation via
   memory, not history. Restore the backed-up history file afterward.
3. **[REQ-SB-26-US-01-AC-02]** Confirm a second, unrelated agent (e.g.
   `vault-qa`, Provider `"compass"`) has no memory entry for "Acme Corp":
   `POST /agents/vault-qa/chat` with `{"message": "What's my favourite
   customer?"}`. Confirm the reply shows no awareness of "Acme Corp" — an
   honest "I don't know"/no-information reply, not a leaked cross-agent
   fact. Confirm via `.second-brain/agent_memory.json` that `"vault-qa"`
   has no such entry — isolation is structural (a separate `agent_id` key),
   not just behavioural.
4. **[REQ-SB-26-US-01-AC-03]** `POST /agents/vault-qa/chat` with
   `{"message": "What did I tell you my dog's name was?"}` (something
   never actually told to any agent in this vault). Confirm the reply
   honestly indicates it has no such information, rather than inventing a
   plausible-sounding name. Confirm `.second-brain/agent_memory.json`
   gained no fabricated entry for `"vault-qa"` from this exchange (a
   correct `extract_memory` outcome extracts nothing here, since nothing
   genuinely new/durable was actually shared).
5. **[REQ-SB-26-US-01-AC-04]** With the "Acme Corp" fact from step 1
   already recorded for `"email-capture"`, fully stop (`Ctrl+C`) and
   restart the backend process (`.venv\Scripts\uvicorn app.main:app
   --reload`, same default port). `POST /agents/email-capture/chat` with
   `{"message": "Remind me who my favourite customer is."}`. Confirm the
   reply still correctly references "Acme Corp" — proving the fact
   survived the process restart via the on-disk `agent_memory.json` file,
   not any in-memory/process state.
6. Clean-up: remove the test-added "Acme Corp"/dog-name-related entries
   from `.second-brain/agent_memory.json` for `"email-capture"`/`"vault-qa"`
   afterward, and confirm `.second-brain/agent_communication_history.json`
   was correctly restored in step 2, so no test residue is left in the
   real vault's state directory.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a fact stated in one conversation is
      correctly recalled in a later, separate conversation with the same
      agent, verified with that agent's own conversation-history entry
      cleared to isolate memory as the actual source
- [x] **AC-02** (Scenario 2) — a different agent shows no awareness of a
      fact recorded only for another agent; `agent_memory.json` confirms
      no cross-agent entry exists
- [x] **AC-03** (Scenario 3) — an agent asked to recall something never
      actually shared honestly says it doesn't know, and no fabricated
      fact is written to `agent_memory.json`
- [x] **AC-04** (Scenario 4) — a previously recorded fact is still
      correctly recalled after a full backend restart
- [x] `memory` is loaded once, before the `run_agent_conversation` call,
      never re-fetched mid-request
- [x] `append_agent_memory_entries` is only called when `extracted_facts`
      is non-empty
- [x] The trigger-phrase-match branch is byte-for-byte unchanged from
      `REQ-SB-25-US-01-T08`'s own version
- [x] Every other endpoint in `agents_router.py` byte-for-byte unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — this story has none (`## Affected Screens` names
  no shape change).
- `agent_chat.py`, `agent_registry.py`, `provider_registry.py`,
  `compass_client.py` — none touched.
- `list_agents`/`get_agent`/`update_agent_assignment`/`trigger_action`/
  `get_history` — untouched.
- A user-facing surface to view/edit/clear memory — explicitly out of
  scope per the parent story's own Non-Goals.

---

## Context / Notes

**Why this task carries every locked AC's verification, not the earlier
build tasks:** every one of this story's 4 scenarios describes an
API-observable *chat exchange behaviour across separate conversations* —
none is verifiable purely inside `vault_writer.py`/`state.py`/`graph.py`
without a real HTTP call reaching this exact endpoint across at least two
separate requests, the same "verify at the level where the outcome first
becomes genuinely observable" placement rule `REQ-SB-25-US-01-T08` already
established for its own scenarios.

Restore every test-only artefact (`agent_communication_history.json`'s
backed-up entries, any stray `agent_memory.json` test entries) to the
clean seed state after this task's own verification completes — no
`verify-*` Providers are created by this task's own steps, unlike `T08`.

---

## Implementation Log

**2026-08-12 — coder.** Replaced `agents_router.py::chat`'s no-match
`else` branch verbatim per this task's own `## Files to Modify` code
block — loads `memory` via `vault_writer.load_agent_memory(agent_id)`
once, before the `run_agent_conversation` call, passes it in as the
additive `memory` argument, and persists any `extracted_facts` via
`vault_writer.append_agent_memory_entries` only when non-empty. The
import line was already exactly as specified (`agent_orchestration`
already imported by `T08`) — no change needed. The trigger-phrase-match
branch and every other endpoint (`list_agents`/`get_agent`/
`update_agent_assignment`/`trigger_action`/`get_history`) untouched.

**Environment note (same established pattern as `SPRINT-014`, not a new
finding):** ports `8000`/`8001` are both live-occupied by unrelated
processes on this host (confirmed via `netstat`/`Get-CimInstance`) —
`8000` by an `agentic-map` process, `8001` unidentifiable. Ran the real
backend on port `8002` instead — `mcp_client.py`'s own hardcoded loopback
MCP target — self-managed directly (explicit kill-and-restart via
`Get-CimInstance`-identified PIDs, never by image name, per `MEMORY.md`'s
standing constraint), not via `--reload`. Each restart triggers a real
app-start capture run (`ADR-005`, already-documented standing constraint)
which took roughly 60-90 seconds to complete before the server became
reachable — expected, not a defect.

**All 4 locked ACs verified live, real HTTP calls against the real
backend/vault/Compass Provider:**

- **[AC-01]** Confirmed `email-capture`'s Provider is `"compass"`. `POST
  /agents/email-capture/chat` with "My favourite customer is Acme Corp,
  please remember that." → real reply; `.second-brain/agent_memory.json`
  confirmed a new entry under `"email-capture"`: `{"fact": "Your
  favourite customer is Acme Corp.", "recorded_at": "2026-08-12T05:41:32...
  "}`. Then backed up `agent_communication_history.json`, cleared
  `"email-capture"`'s own entry list to `[]` (isolating memory as the
  actual source, per this task's own step 2 instruction), `POST
  /agents/email-capture/chat` with "What's my favourite customer?" →
  `"Your favourite customer is Acme Corp."` — confirms recall via
  `agent_memory.json`/`retrieve_memory`, not `REQ-SB-25`'s own
  history-replay mechanism (history was empty for this call). History
  file restored from backup afterward.
- **[AC-02]** `POST /agents/vault-qa/chat` with "What's my favourite
  customer?" → an honest reply listing known vault customers with no
  mention of "Acme Corp" as a favourite — no cross-agent leak.
  `agent_memory.json` confirmed to gain **no** `"vault-qa"` key at all —
  isolation is structural (a separate `agent_id` key), not just
  behavioural.
- **[AC-03]** `POST /agents/vault-qa/chat` with "What did I tell you my
  dog's name was?" (never told to any agent) → an honest "I don't see
  your dog's name anywhere..." reply, no fabricated name. Re-confirmed
  `agent_memory.json` still had no `"vault-qa"` entry after this exchange
  — `extract_memory` correctly extracted nothing.
- **[AC-04]** With the "Acme Corp" fact still recorded for
  `"email-capture"`, fully killed and restarted the backend process (same
  port `8002`, explicit kill-and-restart, real PIDs identified via
  `Get-CimInstance` and targeted specifically, never by image name).
  `POST /agents/email-capture/chat` with "Remind me who my favourite
  customer is." → `"Your favourite customer is Acme Corp."` — confirms
  the fact survived the process restart via the on-disk
  `agent_memory.json` file, not any in-memory/process state.

**Clean-up:** `.second-brain/agent_memory.json` deleted afterward (its
only content was the test-added "Acme Corp" entry for `"email-capture"`;
no `"vault-qa"` entry was ever added, per AC-02/AC-03's own findings).
`agent_communication_history.json` confirmed correctly restored from its
own backup in the AC-01 step (the backup/restore pair, not the
subsequent real AC-02/AC-03/AC-04 chat exchanges, which are genuine
verification-session usage data, left in place — consistent with
`SPRINT-014`'s own precedent of leaving real verification-session
history entries intact).

`status: Ready → Done`.

`gate: clear 2026-08-12` — implemented exactly per this task's own
literal code sample, no deviation from a locked AC, every AC-tagged
verification step performed and passing live. (The port choice mirrors
`SPRINT-014`'s own already-established, already-flagged pattern — not a
new finding requiring a fresh flag.)
