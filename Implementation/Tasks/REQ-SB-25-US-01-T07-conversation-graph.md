---
id: REQ-SB-25-US-01-T07
title: agent_orchestration/graph.py — compiled StateGraph exposing run_agent_conversation(agent_id, message, history)
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — both corrections (tool-execution loop, base_url suffix fix) are real, necessary for genuine tool-calling to work at all, well-verified live (a real tool-backed Compass reply, a real honest-unavailability short-circuit), and stayed within already-owned files."
phase: P1
depends_on: [REQ-SB-25-US-01-T02, REQ-SB-25-US-01-T03, REQ-SB-25-US-01-T06]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T07 — `agent_orchestration/graph.py`

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Build and compile **one** `langgraph.graph.StateGraph` (a single,
tool-bound model-call node this pass) and expose
`run_agent_conversation(agent_id, message, history) -> dict` as the
module's one public entry point — the seam every other requirement
(`REQ-SB-20`/`26`/`27`) is expected to extend with additional nodes later
(`ADR-015` points 3, 9).

---

## Starting State → End State

**Before / Inputs:**
- `T02` (`state.py`), `T03` (`model_factory.py`), `T06` (`mcp_client.py`)
  have all landed.
- `app/business/agent_registry.py` already exists (`Done`):
  `get_agent(agent_id) -> dict | None` with `"name"`/`"type"` fields.
- `app/business/provider_registry.py` already exists (`Done`):
  `get_agent_provider(agent_id) -> dict | None`.

**After / Outputs:**
- `app/business/agent_orchestration/graph.py` exists: builds/compiles the
  graph once at import time, exposes `run_agent_conversation`.
- `app/business/agent_orchestration/__init__.py` re-exports
  `run_agent_conversation`, so callers use
  `agent_orchestration.run_agent_conversation(...)`.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py` (new):
  ```python
  """Compiles Second Brain's own single in-app LangGraph conversation
  graph and exposes run_agent_conversation as this package's one public
  entry point (ADR-015 point 3). This pass needs only a single model-call
  node, tool-bound from the start. REQ-SB-20/26/27 are each expected to
  extend this SAME graph with additional nodes/conditional edges -- do not
  build a second graph for a future requirement; extend this one."""
  import asyncio

  from langchain_core.messages import HumanMessage
  from langgraph.graph import END, StateGraph

  from app.business import agent_registry, provider_registry
  from app.business.agent_orchestration import mcp_client, model_factory
  from app.business.agent_orchestration.state import (
      AgentConversationState,
      history_entries_to_messages,
  )


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


  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("call_model", _call_model)
      builder.set_entry_point("call_model")
      builder.add_edge("call_model", END)
      return builder.compile()


  _GRAPH = _build_graph()


  def run_agent_conversation(agent_id: str, message: str, history: list[dict]) -> dict:
      """Returns {"reply": str} on a real, successful conversational reply,
      or {"error": str} on honest unavailability or a failed real Provider
      call -- never a fabricated reply. Runs statelessly per call -- no
      LangGraph checkpointer; `history` (the conversation's prior turns,
      NOT including `message`) is passed in fresh on every call and
      replayed into the graph's initial state (ADR-015 point 6)."""
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
      }
      result = _GRAPH.invoke(initial_state)
      if result.get("error"):
          return {"error": result["error"]}
      return {"reply": result["reply"]}
  ```

- `src/backend/app/business/agent_orchestration/__init__.py` — replace the
  empty file `T02` created with:
  ```python
  from app.business.agent_orchestration.graph import run_agent_conversation

  __all__ = ["run_agent_conversation"]
  ```

---

## Constraints

- Inherits from parent story: exactly one public entry point
  (`run_agent_conversation`) — no other function in this package is
  imported directly by `agents_router.py` (`T08`).
- The unavailable-Provider message text
  (`f"{provider_name} is not available yet — no client has been built for
  it."`) must match `agents_router.py::_invoke_action`'s existing phrasing
  **verbatim** — this is the "same honesty posture already established for
  actions" the story's own Scenario 4 requires, not a new message shape.
- `history` is the conversation's turns **strictly before** `message` — the
  caller (`T08`) is responsible for capturing history before appending the
  current message to `agent_communication_history.json`; this module does
  not append `message` onto `history` itself before mapping, it appends the
  current `HumanMessage(message)` after `history_entries_to_messages`
  already ran.
- No LangGraph checkpointer (`MemorySaver`/`SqliteSaver`) — `.invoke()`
  only, stateless per call (`ADR-015` point 6).
- Real exceptions from the model call must be caught and turned into an
  honest `{"error": ...}` — never re-raised past `run_agent_conversation`,
  never silently swallowed into a fabricated `{"reply": ...}`.

---

## Tests

<!-- This task has no locked AC of its own — run_agent_conversation is not
directly HTTP-reachable by itself; every one of this story's 5 locked ACs
is genuinely observable only once T08 wires it into agents_router.py::chat
and a real HTTP request can be issued. This task's own verification is a
non-AC smoke check calling the function directly, ahead of T08's full
end-to-end AC verification. -->

**Manual verification steps:**
1. Non-AC smoke check: with the backend running on the default port (per
   `T05`'s convention, so `T06`'s loopback client resolves), in a
   throwaway interpreter against `src/backend`'s `.venv`, call
   `run_agent_conversation("email-capture", "What kinds of notes exist in
   my vault right now?", [])` directly. Confirm the return value is
   `{"reply": <a real, non-empty string>}` — a real Compass call
   completing successfully — not an error, not an empty string.
2. Non-AC smoke check: temporarily reassign `email-capture` to a Provider
   with no real client (reuse the pattern from `T03`'s own verification),
   then call `run_agent_conversation("email-capture", "hello", [])`
   directly. Confirm the return value is exactly `{"error": "Verify
   Unavailable is not available yet — no client has been built for it."}`
   (or whatever throwaway Provider name was used) — confirming the graph
   is never even invoked in this branch. Restore `email-capture` to
   `"compass"` afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `run_agent_conversation(agent_id, message, history)` returns
      `{"reply": str}` on a successful real Provider call
- [x] Returns `{"error": str}`, verbatim-matching `_invoke_action`'s
      unavailable-Provider phrasing, when the agent's Provider has no real
      client — without ever invoking the graph/model
- [x] Returns `{"error": str}` (not a raised exception, not a fabricated
      reply) when the real Provider call itself fails
- [x] `history`'s turns are replayed into the model's context ahead of the
      current `message`
- [x] `app/business/agent_orchestration/__init__.py` re-exports
      `run_agent_conversation` as this package's one public symbol
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `agents_router.py` — `T08`.
- A second graph, or additional nodes for `REQ-SB-20`/`26`/`27` — those
  stories' own future `/plan-tasks` passes extend this same graph, not
  this task.
- A LangGraph checkpointer of any kind.

---

## Context / Notes

`bind_tools` is only called when `tools` is non-empty — if `T06`'s
loopback MCP round-trip ever returns an empty list (e.g. transient
failure), the model still runs unbound rather than erroring out, since a
tool-binding failure is not one of this story's own locked failure modes
(Scenario 5 is specifically about the *Provider* call failing, not the
*tool-loading* step) — do not conflate the two failure classes.

---

## Implementation Log

**2026-08-12 — Done, with two real, live-discovered corrections beyond
this task's own literal code (documented, not silently patched):**

**1. `model_factory.py` (`T03`'s own file) base_url mismatch, found via
this task's own first live smoke check:** a real call through
`run_agent_conversation` initially failed with `404 Not Found`.
Root-caused live: `provider_registry`'s `endpoint` field is the FULL
Compass completions URL (`https://api.core42.ai/v1/chat/completions`) —
exactly the shape `app/data_access/compass_client.py`'s own plain
`httpx.post(url, ...)` call expects directly — but `langchain_openai.
ChatOpenAI` wraps the OpenAI Python SDK client, which itself appends
`/chat/completions` onto whatever `base_url` it's given, expecting a root
URL (`.../v1`). Passing the full endpoint unmodified double-appended the
suffix. Fixed in `model_factory.py`
(`provider["endpoint"].removesuffix("/chat/completions")`) — confirmed
live: a direct `ChatOpenAI(base_url=stripped, ...).invoke(...)` call
against the real Compass endpoint returned `'pong'` for a one-word test
prompt after the fix, having 404'd before it. No change to
`provider_registry.py`'s own stored shape — `compass_client.py`'s
existing, unrelated call path is unaffected.

**2. `graph.py` needed a minimal tool-execution loop, not literally the
task's own single "call_model → END" edge:** with tools bound (`ADR-015`
point 3's own explicit decision), a real Compass/GPT-5 call for the
task's own exact smoke-check question ("What kinds of notes exist in my
vault right now?") genuinely chose to call the `list_known_kinds` tool
rather than answer directly — real, correct LLM behaviour given
tool-binding, not a fluke. The task's own literal single-node code left
that tool call unexecuted, so `response.content` was `''` — an empty,
non-conversational reply that would fail `AC-01` for exactly the kind of
vault-query question the MCP tool integration exists to answer. Added a
second node (`execute_tools`) and one conditional edge
(`call_model` → `execute_tools` on a pending tool call, else → `END`,
`execute_tools` → back to `call_model`) — the minimal machinery a
tool-bound single reply-generation node needs to actually use what it's
bound to, not a second graph and not one of `REQ-SB-20`/`26`/`27`'s own
future, structurally distinct nodes (Hub-routing/memory/skill-invocation)
this task's own Out of Scope names. `AgentConversationState` (`T02`'s own
file) was **not** touched — round-tracking is computed from
`current_state["messages"]`'s existing `AIMessage` count
(`_MAX_MODEL_TOOL_ROUNDS = 5`), no new state field added. A second real
bug surfaced fixing this: the MCP-loaded tools (`T06`,
`langchain_mcp_adapters`) are **async-only** — `tool.invoke(args)` raised
`"StructuredTool does not support sync invocation"`, live-confirmed via a
5-round manual trace (identical tool call repeated every round, never
converging, until the round ceiling above was hit). Fixed by
`asyncio.run(tool.ainvoke(tool_call["args"]))`, mirroring
`run_agent_conversation`'s own already-existing `asyncio.run(mcp_client.
load_vault_query_tools())` sync/async bridging pattern one level down.

**Non-AC smoke checks (this task carries no locked AC of its own), final
outcomes, with the backend running on port 8002 (`T05`/`T06`'s own
established convention this pass):**
1. `run_agent_conversation("email-capture", "What kinds of notes exist in
   my vault right now?", [])` → `{"reply": "Here are the note kinds
   currently in your vault:\n- Customers\n- Emails\n- Files\n- Guides\n-
   Meetings\n- Newsletters\n- Notifications\n- Partners\n- People"}` — a
   real, successful, tool-backed Compass reply. PASS.
2. Created a throwaway Provider (`"Verify Unavailable"` →
   `verify-unavailable`, no real client), assigned it to `email-capture`,
   called `run_agent_conversation("email-capture", "hello", [])` →
   returned exactly `{"error": "Verify Unavailable is not available yet —
   no client has been built for it."}`. PASS — confirms the graph is never
   invoked in this branch (no Compass call was made; the error came
   straight from `run_agent_conversation`'s own pre-graph short-circuit).
   Cleaned up: restored `email-capture` → `"compass"`, removed the
   throwaway Provider; confirmed restored.

**Scope note:** both corrections landed inside already-owned files
(`model_factory.py`/`T03`, `graph.py`/`T07`) — no new file, no file
outside either task's own declared scope, no change to
`AgentConversationState`'s schema (`T02`). Flagged (`gate: flagged`,
trigger 8) for human spot-check since both go beyond the task's own
literal code sample, not because either is out-of-scope.

`MEMORY.md` updated (Constraints: `ChatOpenAI`/OpenAI-SDK base_url suffix
convention vs. `provider_registry`'s stored shape; MCP-loaded tools are
async-only).
