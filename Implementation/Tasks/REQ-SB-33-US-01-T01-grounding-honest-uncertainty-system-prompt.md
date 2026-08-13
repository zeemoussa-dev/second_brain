---
id: REQ-SB-33-US-01-T01
title: state.py — history_entries_to_messages gains a grounding/honest-uncertainty instruction on the existing identity SystemMessage
parent_story: REQ-SB-33-US-01
requirement_id: REQ-SB-33
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call, logged for human spot-check (not an escalation): AC-03's induced-tool-failure verification technique substitutes the task's own named example (temporarily pointing mcp_client.py at an unreachable target, which would touch a file outside this task's ## Files to Modify) for a zero-file-touch in-process monkeypatch script that induces the identical condition _execute_tools already handles. See Implementation Log."
phase: P1
depends_on: []
sprint: "SPRINT-018"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-33-US-01-T01 — Agent grounding & honest-uncertainty system-prompt instruction

## Parent Story

- Story: [[REQ-SB-33-US-01]] — `../UserStories/REQ-SB-33-US-01-agent-grounding-and-honest-uncertainty-guardrail.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-33 *Agent Grounding & Honest-Uncertainty Guardrail*

---

## Objective

Extend `history_entries_to_messages`'s existing single, prepended
`SystemMessage` with an additional grounding/honest-uncertainty
instruction — answer only from real tool results/history/memory, and
honestly say "I don't know" (never fabricate) when nothing relevant was
retrieved or a tool call failed — applied globally to every agent's reply
path, with no other node/file touched.

---

## Starting State → End State

**Before / Inputs:**
- `history_entries_to_messages` (`state.py`, `REQ-SB-25-US-01`, `Done`)
  prepends exactly one `SystemMessage`: `"You are the {agent_name} agent
  for the user's personal Second Brain knowledge base."` — no grounding,
  honesty, or anti-fabrication instruction of any kind.
- `_call_model` (`graph.py`, `Done`) invokes the model directly against
  the full message list this function builds, with no verification step
  of any kind on the model's final reply.

**After / Outputs:**
- The same one `SystemMessage`'s content string carries the identity
  sentence **plus** the new grounding/honest-uncertainty instruction —
  still exactly one `SystemMessage`, still built by this same function,
  still consumed unmodified by `_call_model`/`_retrieve_memory`/
  `_extract_memory`.
- Every agent's real conversational reply (Scenario 1) still works
  normally when its tools return a real answer; when they don't
  (Scenario 2), when a tool call fails (Scenario 3), or when the model
  might otherwise answer from its own general training knowledge
  (Scenario 4), the reply honestly says so instead.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py` — extend the
  `SystemMessage` content built in `history_entries_to_messages`. Exact
  wording is this task's own to finalize during live verification (the
  substance below is fixed by the story's Constraints; the precise
  phrasing is not), e.g.:

  ```python
  messages: list[BaseMessage] = [
      SystemMessage(
          content=(
              f"You are the {agent_name} agent for the user's personal "
              "Second Brain knowledge base. Answer only from what your "
              "own tool calls, the replayed conversation history below, "
              "and any stored memory actually contain -- never state "
              "something as a real fact unless it came from one of "
              "those real sources. If a tool call fails or returns an "
              "error, say so honestly; never invent a substitute answer "
              "in its place. If none of your tools return a relevant "
              "result for a question you would otherwise be able to "
              "answer, honestly say you don't know or couldn't find an "
              "answer -- never guess, and never answer from your own "
              "general training knowledge as if it were a real fact "
              "from this knowledge base."
          )
      )
  ]
  ```

  Update the module docstring's own "One minimal SystemMessage is
  prepended..." sentence to reflect the added instruction (still one
  `SystemMessage`, now carrying two concerns — identity, and grounding/
  honest-uncertainty).

---

## Constraints

- Inherits from parent story:
  - System-prompt instruction only — do not add a reply-verification/
    citation node or restructure `_call_model`.
  - Global and unconditional — no per-agent parameter, branch, or config;
    every agent's call goes through this same function unchanged.
  - Do not touch `_execute_tools`, `_retrieve_memory`, `_extract_memory`,
    `graph.py`, or `agent_registry.py` — this task's only file is
    `state.py`.
- Still exactly **one** `SystemMessage` — do not add a second one (see
  the story's own `## Notes` on why this differs from `ADR-016`'s
  `_retrieve_memory` second-`SystemMessage` precedent: this is the same
  static, agent-generic category of content as the existing identity
  sentence).
- `history_entries_to_messages`'s existing `"chat_user"`/`"chat_agent"`/
  `"run_event"` mapping logic (`REQ-SB-25-US-01`) is unchanged — only the
  prepended `SystemMessage`'s own content string grows.

---

## Tests

<!-- Verification is live prompting against a real Provider (mirroring
REQ-SB-26-US-01's own honesty-scenario verification approach) — a
system-prompt instruction has no mechanical/structural signal to assert
on, only real observed model behavior. Use an agent with real vault-query
tools bound (e.g. vault-qa or email-capture) via the actual
POST /agents/{agent_id}/chat endpoint, backend running with a real
Provider configured. -->

**Manual verification steps:**
1. [REQ-SB-33-US-01-AC-01] Ask the agent, via real chat, a question its
   tools can answer from real vault content that genuinely exists (e.g.
   "what customers do we have?" once real vault data / a real tool
   result is available). Confirm the reply is grounded in that real tool
   result and returns normally — no regression vs. `REQ-SB-25-US-01`'s
   already-verified conversational behavior.
2. [REQ-SB-33-US-01-AC-02] Ask the agent, via real chat, a question that
   is legitimately in scope for its tools in principle but for which the
   real tool call returns no relevant result (e.g. ask about a customer/
   note that does not exist in the real vault). Confirm the reply
   honestly states it doesn't know / couldn't find an answer, and does
   not state a plausible-sounding guess as a fact.
3. [REQ-SB-33-US-01-AC-03] Force a real tool call failure (e.g.
   temporarily point the agent's Provider/MCP client at an unreachable
   target, or otherwise induce `_execute_tools`'s existing `"Tool call
   failed: {exc}"` path — do not edit `_execute_tools` itself, only
   induce the condition it already handles) and ask a question that
   triggers that tool call. Confirm the reply honestly reflects it could
   not retrieve an answer and does not substitute a fabricated answer.
   Revert whatever was temporarily changed to induce the failure
   afterward.
4. [REQ-SB-33-US-01-AC-04] Ask the agent, via real chat, about something
   not actually present anywhere in the real vault but which the
   underlying model might otherwise "know" from its own general training
   knowledge (a fact no tool call for this conversation actually
   returned). Confirm the reply does not present that general-knowledge
   fact as if it were a real vault fact, and honestly indicates it has no
   vault-grounded answer to give.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-33-US-01-AC-01` — real tool-backed answer still works normally (regression guard)
- [x] `REQ-SB-33-US-01-AC-02` — in-scope question, no relevant tool result → honest "I don't know"
- [x] `REQ-SB-33-US-01-AC-03` — failed/erroring tool call → honest, not fabricated
- [x] `REQ-SB-33-US-01-AC-04` — no unfounded/general-training-knowledge claim presented as a vault fact
- [x] `history_entries_to_messages` still prepends exactly one `SystemMessage`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any reply-verification/citation mechanism checking the model's output
  against real tool results before returning it — deferred, per the
  story's own Non-Goals.
- Any per-agent opt-out/configuration, or new Agent Settings UI field.
- `REQ-SB-29`'s own out-of-scope-question honesty behavior (Scenario 4/5)
  — a different, already-specced case.
- Any change to `graph.py`, `agent_registry.py`, `agent_chat.py`, or any
  file outside `state.py`.

---

## Context / Notes

A system-prompt instruction gives no hard technical enforcement
guarantee — an LLM can still fail to follow it. This is the same honest
limitation `ADR-016`'s own `extract_memory` "never invent a fact"
instruction already accepts; verification here is real observed prompting
behavior, not a mechanical check. If live verification finds the
model does not reliably comply, do not silently strengthen the mechanism
beyond a system-prompt instruction (that would contradict this story's
own Constraints) — record the finding honestly in this task's
Implementation Log and flag for human review instead.

---

## Implementation Log

**2026-08-12 — coder.** Extended `history_entries_to_messages`'s single
prepended `SystemMessage` (`src/backend/app/business/agent_orchestration/
state.py`) with the grounding/honest-uncertainty instruction, appended
after the existing identity sentence in the same content string — still
exactly one `SystemMessage`, confirmed directly (see AC-tagged checks
below). Used the task's own literal wording sample verbatim (no
deviation). Updated the function's docstring sentence describing the
`SystemMessage` per the task's own instruction. No other line in the file
touched; `AgentConversationState`, the `"chat_user"`/`"chat_agent"`
mapping loop, and the `"run_event"`-exclusion behavior are byte-for-byte
unchanged.

**Assumption / scope-internal judgement call (logged for human spot-check,
not an escalation):** the task's own `## Tests` step 3 (AC-03) suggests
inducing a real tool-call failure by "temporarily point[ing] the agent's
Provider/MCP client at an unreachable target" — that would require
editing `mcp_client.py`, outside this task's own `## Files to Modify`
(`state.py` only). Instead of editing any out-of-scope file (even
temporarily), used a zero-file-touch technique that induces the exact
same condition `_execute_tools` already handles: a standalone Python
script (kept in the session scratchpad, never written into `src/`) that
loads the real MCP tools via the real running server, monkeypatches one
(then, for a stricter second pass, every) tool's `.coroutine` in-process
to raise, and calls the real, unmodified `run_agent_conversation` directly
— exercising the genuine production `_call_model`/`_execute_tools` code
path end-to-end (real model, real prompt, real tool binding, real
exception→`ToolMessage` handling), with the *tool result* substituted,
not any application code. No file on disk was edited or needs reverting.
This substitutes the task's own named *example* technique for an
equally-real, lower-risk one that achieves the same verification
substance — a scope-internal judgement call, not a deviation from any
locked AC's own wording.

**Operational note:** the shared dev backend (port `8001`, already running
before this task started) became fully unresponsive (confirmed via a
plain `GET /agents` timing out, not just the in-flight chat call) partway
through the first live AC-01 attempt — consistent with `_call_model` being
a synchronous LangGraph node (`graph.py`, out of this task's file scope,
unmodified) that blocks the single asyncio event loop for the duration of
a real Compass HTTP call; this specific hang did not resolve after several
minutes, unlike the ordinary "Compass calls take a while" latency this
project's own precedent (`REQ-SB-26-US-01-T04`) already documents.
Restarted it via the standing MEMORY.md protocol (specific-PID kill via
`Get-CimInstance`, never by image name; relaunched via the documented
`tools/run-backend.cmd` command) — the restart's own real app-start
capture-run side effect (`ADR-005`) is the same already-accepted,
already-documented consequence of any dev-server restart on this project,
not new. All 4 ACs were verified against the freshly restarted, reloaded
server. Not flagged as a defect in this task's own scope (`graph.py`'s
`_call_model` sync-node shape predates this story and is out of file
scope) — worth a future look if it recurs, noted here for visibility only.

**All 4 locked ACs verified live, real HTTP calls (AC-01/02/04, via the
actual `POST /agents/vault-qa/chat` endpoint, real Compass Provider) plus
one direct in-process call through the real, unmodified graph (AC-03, see
judgement-call note above):**

- **[REQ-SB-33-US-01-AC-01]** `POST /agents/vault-qa/chat` —
  `"What customers do we have notes about in the vault? Please list
  them."` → reply listed exactly the 20 real customers
  `vault_query_tools.list_known_customers()` independently confirmed
  (ADNOC, Aldar, ..., e&) — grounded in the real tool result, returned
  normally, no regression vs. `REQ-SB-25-US-01`'s existing conversational
  behavior. **Pass.**
- **[REQ-SB-33-US-01-AC-02]** `POST /agents/vault-qa/chat` —
  `"Do we have any notes about a customer called Globex Corporation?"`
  (confirmed absent from the real `list_known_customers()` result above)
  → `"I don't see any customer notes for 'Globex Corporation' in your
  vault. It isn't in the current customer list I can access."` — honest,
  no fabricated guess. **Pass.**
- **[REQ-SB-33-US-01-AC-03]** Two passes, both via the standalone
  monkeypatch script (judgement-call note above): (1) only
  `list_known_customers` failing → the model honestly disclosed *that
  specific tool's* failure in its reply ("I couldn't retrieve the
  customer list via the `list_known_customers` tool due to a tool
  failure"), then recovered via a *different, genuinely real* tool
  (`list_notes_in_kind_folder("Customers")`) rather than fabricating —
  still fully grounded, and the failure itself was reported honestly, not
  papered over. (2) Stricter pass — every tool's `.coroutine` failing (no
  real fallback available at all) → `"I tried to fetch the list of
  customers from the vault, but the tool call failed. ... Because of this
  failure, I can't retrieve the customer list right now."` — the literal
  "honestly reflects it could not retrieve an answer, no substitute
  fabricated answer" case the Gherkin names. **Pass** (both passes; the
  stricter one is the more literal match to the scenario's own wording).
- **[REQ-SB-33-US-01-AC-04]** `POST /agents/vault-qa/chat` —
  `"What industry does ADNOC operate in, and roughly how large is the
  company?"` (ADNOC is a real vault customer; its real-world industry/size
  is exactly the kind of fact the underlying model's own general training
  knowledge could plausibly supply, but no tool call in this conversation
  returned) → `"I can see you have a customer note for ADNOC in your
  vault, but I don't have access to any industry or size details from the
  data I can read. My tools can list customers and note files, but they
  can't open note contents."` — no general-training-knowledge fact stated
  as a vault fact; honestly indicates no vault-grounded answer exists.
  **Pass.**

**`history_entries_to_messages` still prepends exactly one
`SystemMessage`** — confirmed directly: `len([m for m in
history_entries_to_messages("Vault Q&A", "expert", []) if
isinstance(m, SystemMessage)]) == 1`.

**Verification-residue check:** `.second-brain/agent_memory.json` for
`vault-qa` confirmed empty (`[]`) after all live verification calls — no
memory-entry cleanup needed. `.second-brain/agent_communication_history.
json` gained real `chat_user`/`chat_agent` entries from the AC-01/02/04
calls above — left in place as genuine verification-session usage data,
matching `SPRINT-014`/`REQ-SB-26-US-01-T04`'s own already-established
precedent (history entries from real verification are not test pollution
to scrub, unlike an artificial planted fact).

**No frontend/screen change** — this story's own `## Affected Screens`
names none (`chat-thread`/`chat-message` rendering unmodified); the real
HTTP calls above hit the exact same `agents_router.py::chat` endpoint the
existing, unmodified `AgentDetailPanel.tsx` chat UI already calls, so no
separate browser/visual-harness pass was needed for a change that is
prompt-content-only.

`status: Ready → Done`.

`gate: flagged 2026-08-12` — one scope-internal judgement call made (the
AC-03 verification-technique substitution above, and finalizing the exact
system-prompt wording per this task's own "this task's own to finalize"
allowance) — logged here for human spot-check per the Pipeline's own
"scope-internal judgement calls ... make the task gate: flagged" rule.
Not a MUST-FLAG escalation trigger: no new dependency, no shared-interface
change, no ADR deviation, no unanticipated file, no locked AC weakened,
omitted, or left unverified — all 4 pass with real evidence above.
