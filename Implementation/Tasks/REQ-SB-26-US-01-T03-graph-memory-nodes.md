---
id: REQ-SB-26-US-01-T03
title: agent_orchestration/graph.py — retrieve_memory + extract_memory nodes; run_agent_conversation gains memory param / extracted_facts return
parent_story: REQ-SB-26-US-01
requirement_id: REQ-SB-26
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — the correction properly composed around REQ-SB-25's already-verified tool-calling loop instead of regressing it, and fixed a real duplicate-message bug in the extraction context. Live-verified (real fact extraction, retrieval, honest unavailability)."
phase: P1
depends_on: [REQ-SB-26-US-01-T02, REQ-SB-25-US-01-T07]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-26-US-01-T03 — `graph.py` gains `retrieve_memory`/`extract_memory`

## Parent Story

- Story: [[REQ-SB-26-US-01]] — `../UserStories/REQ-SB-26-US-01-agent-memory.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-26 *Agent Memory*

---

## Objective

Add `ADR-016`'s two new nodes — `retrieve_memory` (read path, before
`call_model`) and `extract_memory` (write path, after `call_model`, same
`.invoke()` call, no second Provider resolution) — to the **same** compiled
graph `REQ-SB-25-US-01-T07` built, and extend
`run_agent_conversation`'s public signature/return shape additively.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-25-US-01-T07` has landed — `graph.py` builds/compiles a single
  `call_model`-only graph and exposes `run_agent_conversation(agent_id,
  message, history) -> dict` (verbatim content quoted in that task file).
- `T02` (this story) has landed — `AgentConversationState` has `memory`/
  `extracted_facts` fields available.

**After / Outputs:**
- `graph.py`'s compiled graph is `retrieve_memory → call_model →
  extract_memory → END` (three nodes, not one).
- `run_agent_conversation(agent_id, message, history, memory=None) -> dict`
  — one new parameter, additive; return shape gains `"extracted_facts"`
  on the success path (`{"reply": str, "extracted_facts": list[str]}`),
  unchanged (`{"error": str}`, no `"extracted_facts"` key) on any failure/
  unavailable path.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py` — full replacement:
  ```python
  """Compiles Second Brain's own single in-app LangGraph conversation
  graph and exposes run_agent_conversation as this package's one public
  entry point (ADR-015 point 3). REQ-SB-26/ADR-016 extends this SAME graph
  with two new nodes -- retrieve_memory (read path) and extract_memory
  (write path) -- rather than a second graph, per ADR-015 points 3/9's
  "grow by adding nodes" pattern. REQ-SB-20/27 are each expected to extend
  this SAME graph further -- do not build a second graph for a future
  requirement; extend this one."""
  import asyncio

  from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
  from langgraph.graph import END, StateGraph

  from app.business import agent_registry, provider_registry
  from app.business.agent_orchestration import mcp_client, model_factory
  from app.business.agent_orchestration.state import (
      AgentConversationState,
      history_entries_to_messages,
  )

  _EXTRACTION_INSTRUCTIONS = (
      "Review the user's most recent message and your own reply above. "
      "Identify any new, durable fact about the user or their work that is "
      "worth remembering for a future, separate conversation (for example "
      "a stated preference, name, or recurring detail) -- something "
      "genuinely worth recalling later, not small talk or a one-off "
      "request. Reply with each such fact as a short, standalone "
      "sentence, one per line, with no other commentary. If nothing is "
      "worth remembering, reply with exactly the single word NONE -- "
      "never invent a fact that was not actually stated."
  )


  def _retrieve_memory(current_state: AgentConversationState) -> dict:
      """Read path (ADR-016 point 2): folds any stored facts for this
      agent into the graph's own message list as a second SystemMessage,
      inserted immediately after the existing agent-identity SystemMessage
      history_entries_to_messages already prepends -- no file I/O here,
      `memory` arrives already loaded from run_agent_conversation's own
      new parameter (mirrors `history`'s existing "passed in fresh from
      outside" shape, ADR-015 point 6). A no-op (no state update at all)
      when there is no stored memory for this agent yet."""
      memory = current_state.get("memory") or []
      if not memory:
          return {}
      facts_text = "\n".join(f"- {entry['fact']}" for entry in memory)
      memory_message = SystemMessage(
          content=(
              "The following facts were extracted from earlier, separate "
              "conversations with this same user and are worth "
              "remembering for this conversation too:\n" + facts_text
          )
      )
      messages = list(current_state["messages"])
      messages.insert(1, memory_message)
      return {"messages": messages}


  def _call_model(current_state: AgentConversationState) -> dict:
      model = current_state["model"]
      if model is None:
          # model_factory.resolve_agent_model already returned None before
          # this node ever ran -- the honest "unavailable" message was
          # already placed on current_state["error"] by
          # run_agent_conversation, below. This branch should be
          # unreachable in practice (run_agent_conversation short-circuits
          # before invoking the graph at all when the model is
          # unavailable) but is kept as a defensive fallback, never a
          # fabricated reply.
          return {"error": current_state.get("error") or "This agent's selected Provider is not available."}
      try:
          tools = current_state["tools"]
          bound_model = model.bind_tools(tools) if tools else model
          response = bound_model.invoke(current_state["messages"])
          return {"reply": response.content}
      except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (Scenario 5); never swallowed
          return {"error": f"The request to this agent's Provider failed: {exc}"}


  def _extract_memory(current_state: AgentConversationState) -> dict:
      """Write path (ADR-016 point 2): reuses the already-resolved model
      instance on state (no second model_factory.resolve_agent_model
      call, no second Provider-availability check) for one additional,
      narrowly-scoped completion -- unbound (no bind_tools), since this
      completion asks for plain extracted-fact text, not vault-query tool
      use. Skipped entirely (empty dict -- no extracted_facts key
      produced) whenever call_model itself errored, matching the existing
      short-circuit-on-unavailable-Provider shape ADR-015 already
      established, and whenever the completion itself fails -- extraction
      is best-effort and must never surface as a user-visible chat error
      (Scenario 3's own "honest, not fabricated" posture one layer
      over: a failed/empty extraction always means "no new fact this
      turn", never a propagated error)."""
      if current_state.get("error"):
          return {}
      model = current_state["model"]
      try:
          response = model.invoke(
              current_state["messages"]
              + [
                  AIMessage(content=current_state["reply"]),
                  HumanMessage(content=_EXTRACTION_INSTRUCTIONS),
              ]
          )
          raw = (response.content or "").strip()
      except Exception:  # noqa: BLE001 -- best-effort; never propagated as a chat-facing error
          return {"extracted_facts": []}
      if not raw or raw.strip().upper() == "NONE":
          return {"extracted_facts": []}
      facts = [line.strip("- ").strip() for line in raw.splitlines()]
      facts = [fact for fact in facts if fact and fact.upper() != "NONE"]
      return {"extracted_facts": facts}


  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("retrieve_memory", _retrieve_memory)
      builder.add_node("call_model", _call_model)
      builder.add_node("extract_memory", _extract_memory)
      builder.set_entry_point("retrieve_memory")
      builder.add_edge("retrieve_memory", "call_model")
      builder.add_edge("call_model", "extract_memory")
      builder.add_edge("extract_memory", END)
      return builder.compile()


  _GRAPH = _build_graph()


  def run_agent_conversation(
      agent_id: str, message: str, history: list[dict], memory: list[dict] | None = None
  ) -> dict:
      """Returns {"reply": str, "extracted_facts": list[str]} on a real,
      successful conversational reply, or {"error": str} on honest
      unavailability or a failed real Provider call -- never a fabricated
      reply, and never an "extracted_facts" key on the error path. Runs
      statelessly per call -- no LangGraph checkpointer; `history` and the
      new `memory` (ADR-016) are both passed in fresh on every call, never
      cached in-process."""
      agent = agent_registry.get_agent(agent_id)

      model = model_factory.resolve_agent_model(agent_id)
      if model is None:
          provider = provider_registry.get_agent_provider(agent_id)
          provider_name = provider["name"] if provider else "This agent's selected Provider"
          return {"error": f"{provider_name} is not available yet — no client has been built for it."}

      tools = asyncio.run(mcp_client.load_vault_query_tools())

      messages = history_entries_to_messages(agent["name"], agent["type"], history)
      messages.append(HumanMessage(content=message))

      initial_state: AgentConversationState = {
          "agent_id": agent_id,
          "messages": messages,
          "model": model,
          "tools": tools,
          "reply": None,
          "error": None,
          "memory": memory or [],
          "extracted_facts": [],
      }
      result = _GRAPH.invoke(initial_state)
      if result.get("error"):
          return {"error": result["error"]}
      return {"reply": result["reply"], "extracted_facts": result.get("extracted_facts", [])}
  ```

---

## Constraints

- Inherits from parent story: exactly one public entry point
  (`run_agent_conversation`) — `agents_router.py::chat` (`T04`) is the
  only caller.
- `memory`/`history` are both loaded and passed in fresh by the router on
  every call — no LangGraph checkpointer, no in-process caching (`ADR-015`
  point 6, extended to `memory` by `ADR-016`).
- `_extract_memory` reuses `current_state["model"]` **unbound** (no
  `bind_tools`) — do not layer the extraction completion's own prompt
  onto the tool-bound model `_call_model` builds locally; that binding is
  never stored back onto state.
- `extracted_facts` must never appear in the return dict on the `{"error":
  ...}` path (neither the pre-graph unavailable-Provider short-circuit nor
  a `call_model` failure inside the graph) — mirrors `ADR-016`'s own
  "extraction skipped entirely" Decision point 2.
- A failed extraction completion must degrade to `{"extracted_facts": []}`
  — never raise, never surface as a chat-facing `{"error": ...}`.
- The unavailable-Provider message text must still match
  `_invoke_action`'s existing phrasing **verbatim** (inherited from
  `REQ-SB-25-US-01-T07`, unchanged by this task).

---

## Tests

<!-- This task has no locked AC of its own — run_agent_conversation is not
directly HTTP-reachable by itself; every one of this story's 4 locked ACs
is genuinely observable only once T04 wires it into agents_router.py::chat
and a real HTTP request can be issued (mirrors REQ-SB-25-US-01-T07's own
precedent). This task's own verification is a non-AC smoke check calling
the function directly, ahead of T04's full end-to-end AC verification. -->

**Manual verification steps:**
1. Non-AC smoke check: with the backend running on the default port, in a
   throwaway interpreter against `src/backend`'s `.venv`, call
   `run_agent_conversation("email-capture", "My favourite colour is teal.", [], [])`
   directly. Confirm the return value has both a non-empty `"reply"`
   string and an `"extracted_facts"` key present (a list — may be empty
   or may contain a colour-preference fact; either is acceptable at this
   task's own level, full recall correctness is `T04`'s AC-01).
2. Non-AC smoke check: call `run_agent_conversation("email-capture",
   "hello", [], [{"fact": "The user's favourite colour is teal.",
   "recorded_at": "2026-01-01T00:00:00Z"}])`. Confirm no exception is
   raised and the return value still has the `{"reply":
   ..., "extracted_facts": [...]}` shape — confirming `retrieve_memory`'s
   message-list insertion does not break the graph when non-empty memory
   is supplied.
3. Non-AC smoke check: temporarily reassign `email-capture` to a Provider
   with no real client (same pattern as `REQ-SB-25-US-01-T07`'s own
   verification), then call `run_agent_conversation("email-capture",
   "hello", [], [])`. Confirm the return value is exactly `{"error": "..."}`
   with **no** `"extracted_facts"` key present. Restore `email-capture` to
   `"compass"` afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Compiled graph is `retrieve_memory → call_model → extract_memory →
      END` (three named nodes plus the pre-existing `execute_tools` tool-
      loop node — see Implementation Log for the real graph shape this
      task extends, not the task's own simpler literal sample)
- [x] `retrieve_memory` inserts a facts `SystemMessage` at index 1
      (immediately after the identity `SystemMessage`) only when `memory`
      is non-empty; a true no-op otherwise
- [x] `extract_memory` reuses `current_state["model"]` — no second
      `model_factory.resolve_agent_model` call anywhere in this file
- [x] `extract_memory` returns `{"extracted_facts": []}` (not an error,
      not a raised exception) whenever `call_model` errored or the
      extraction completion itself fails
- [x] `run_agent_conversation` gains the additive `memory: list[dict] |
      None = None` parameter; every pre-existing parameter unchanged
- [x] Return shape gains `"extracted_facts"` on the success path only —
      never present on the `{"error": ...}` path
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `agents_router.py` — `T04`.
- `vault_writer.py` primitives — `T01`.
- Any dedup/consolidation/relevance-ranking of stored facts (`ADR-016`
  point 3/4) — not this task's concern; `retrieve_memory` replays the full
  list it is handed, unfiltered.
- A second graph, or additional nodes for `REQ-SB-20`/`27` — untouched.
- A LangGraph checkpointer of any kind.

---

## Context / Notes

`_extract_memory` builds its own completion context from
`current_state["messages"] + [AIMessage(reply), HumanMessage(extraction
instructions)]` rather than mutating `current_state["messages"]` itself —
the extraction instructions/prompt must never leak into the conversation's
own replayed message list on any later turn (there is none, since this is
a stateless, per-call graph, but the construction is deliberately
local/throwaway to avoid ever conflating the two concerns).

---

## Implementation Log

**2026-08-12 — coder. Real, live-discovered correction vs. this task's own
literal `## Files to Modify` code sample — flagged for human spot-check,
same pattern `SPRINT-014` used for its own five corrections.**

This task's own code sample was a "full replacement" written against an
earlier, simpler shape of `graph.py` (a single `call_model` node, no tool-
execution loop). The REAL, already-`Done` `graph.py`
(`REQ-SB-25-US-01-T08`'s own live correction, landed after this task file
was authored) has a materially different, more complex shape: a
`call_model` ⇄ `execute_tools` loop (`_route_after_model` conditionally
routing to `"execute_tools"` or `END`, `_execute_tools` running pending
MCP tool calls and looping back to `call_model`), plus a per-turn
`_current_turn_tool_round_count` guard. Blindly overwriting the file with
this task's own literal sample would have **regressed
`REQ-SB-25-US-01`'s own already-verified, `Done` tool-calling mechanism**
— a locked-AC regression on a sibling story, not an acceptable outcome.

**What was actually done instead:** extended the REAL current `graph.py`
in place — added `retrieve_memory` as the new entry point (edge to
`call_model`, unchanged), added `extract_memory` as the new terminal node
before `END`, and changed only `_route_after_model`'s "done" branch to
return `"extract_memory"` instead of `END` (the `execute_tools` branch and
the `execute_tools → call_model` loop-back edge are untouched). Compiled
shape: `retrieve_memory → call_model → {execute_tools loop, or
extract_memory → END}` — `retrieve_memory`/`extract_memory` are the two
new nodes `ADR-016` names; `call_model`/`execute_tools` are
`REQ-SB-25-US-01`'s own unmodified tool-calling mechanism, correctly
composed alongside them, not replaced.

**Second, related correction, inside `_extract_memory` itself:** the
task's own sample builds the extraction completion's context as
`current_state["messages"] + [AIMessage(current_state["reply"]),
HumanMessage(extraction_instructions)]` — correct only against the older,
simpler `call_model` that did NOT append its own response onto
`messages`. The REAL `call_model` (`REQ-SB-25-US-01-T08`'s own fix) DOES
append its response — including the final, non-tool-call reply — onto
`messages` before returning
(`updated_messages = current_state["messages"] + [response]`). Re-adding
`AIMessage(current_state["reply"])` would have duplicated the model's own
final reply message inside the extraction completion's own context.
Corrected to `current_state["messages"] + [HumanMessage(content=
_EXTRACTION_INSTRUCTIONS)]` only — `messages` already ends with the real
final `AIMessage` reply by the time `extract_memory` runs. Full reasoning
recorded directly in `graph.py`'s own `_extract_memory` docstring.

Neither correction weakens, omits, or changes any locked AC's own
observable contract — both are `graph.py`-internal shape corrections that
make the task's own stated Objective/`## Constraints` genuinely true
against the real codebase, not a scope change. No file outside this
task's own `## Files to Modify` (`graph.py`) was touched.

**Non-AC smoke checks (all pass, run against a real backend on port 8002 —
see this sprint's own port note below):**
1. `run_agent_conversation("email-capture", "My favourite colour is teal.",
   [], [])` → real, non-empty `"reply"`; `"extracted_facts"` present and
   contained `"The user's favourite colour is teal."` — `extract_memory`
   genuinely ran and extracted a real fact.
2. `run_agent_conversation("email-capture", "hello", [],
   [{"fact": "The user's favourite colour is teal.", ...}])` → no
   exception, same `{"reply": ..., "extracted_facts": [...]}` shape —
   `retrieve_memory`'s message-list insertion does not break the graph
   with non-empty memory supplied.
3. Temporarily created a throwaway Provider with no real client
   (`POST /providers`, `has_real_client: false`), reassigned
   `email-capture` to it (`PATCH /agents/email-capture`), called
   `run_agent_conversation("email-capture", "hello", [], [])` → exactly
   `{"error": "..."}` with **no** `"extracted_facts"` key present
   (`set(result.keys()) == {"error"}` confirmed programmatically).
   Restored `email-capture` to `"compass"` and deleted the throwaway
   Provider afterward (`DELETE /providers/verify-no-client-t03`).

**Port note (same pattern `SPRINT-014` established, not re-litigated
here):** the backend was run on port `8002` — `mcp_client.py`'s own
hardcoded loopback MCP target — not this task's own literal "default
port" instruction, since ports `8000`/`8001` are both live-occupied by
unrelated processes on this host (confirmed via `netstat`) and `8002` is
this project's own established working fallback. `run_agent_conversation`
makes a real loopback HTTP call to `127.0.0.1:8002/mcp` to load vault
tools, so the backend had to actually be running and reachable there for
these smoke checks to execute at all — not a bypassable detail.

**No stray memory state left behind:** `run_agent_conversation` itself
never persists anything (persistence is `T04`'s own concern via
`vault_writer.append_agent_memory_entries`) — confirmed no
`.second-brain/agent_memory.json` file was created by this task's own
smoke checks at all.

`status: Ready → Done`. `gate: flagged` — both corrections above are
real, live-discovered technical corrections beyond this task's own
literal code sample, same MUST-FLAG-adjacent spot-check pattern
`SPRINT-014` used (Pipeline.md trigger-adjacent judgement call, not a
locked-AC weakening or an escalation); parked for a human skim, not a
blocker — `T04` proceeds on top of this corrected, verified code.
