---
id: REQ-SB-20-US-01-T05
title: agent_orchestration/graph.py — route_hub_request node + request_cross_section_help tool + conditional edge + route_cross_section_request(...)
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-25-US-01-T07, REQ-SB-20-US-01-T02, REQ-SB-20-US-01-T04]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T05 — `agent_orchestration/graph.py`'s `route_hub_request` node

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Extend `REQ-SB-25-US-01-T07`'s already-compiled `StateGraph` (`ADR-015` points 3/9/12's "grow by node, not by new graph" convention) with ONE new node, `route_hub_request`, a new local (never-MCP-registered) tool `request_cross_section_help`, and a new conditional edge off `call_model` — this codebase's first real tool-execution loop (`ADR-017` point 5) — plus a directly-callable `route_cross_section_request(...)` public entry point wrapping the same logic, so this story's own locked ACs are verifiable without first wiring a live, model-driven tool-call trigger end-to-end.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-25-US-01-T07` has landed — `app/business/agent_orchestration/graph.py` exists (verbatim, that task's own code block):
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
          return {"error": current_state.get("error") or "This agent's selected Provider is not available."}
      try:
          tools = current_state["tools"]
          bound_model = model.bind_tools(tools) if tools else model
          response = bound_model.invoke(current_state["messages"])
          return {"reply": response.content}
      except Exception as exc:
          return {"error": f"The request to this agent's Provider failed: {exc}"}


  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("call_model", _call_model)
      builder.set_entry_point("call_model")
      builder.add_edge("call_model", END)
      return builder.compile()


  _GRAPH = _build_graph()


  def run_agent_conversation(agent_id: str, message: str, history: list[dict]) -> dict:
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
- `T02` has landed `agent_keywords.list_candidate_agents_for_keyword_match(requesting_agent_id, need_description) -> list[dict]`.
- `T04` has landed `AgentConversationState`'s new `hub_routing_result: dict | None` key.

**After / Outputs:**
- `graph.py` gains: the `request_cross_section_help` tool definition; the `_route_hub_request` node; a routing decision function `_route_after_call_model`; the `route_hub_request` node wired via a new conditional edge from `call_model`; `route_cross_section_request(requesting_agent_id, need_description) -> dict`, a second public module-level function alongside `run_agent_conversation`.
- `_call_model` is extended to append its own response message onto the replayed message list and to short-circuit (skip setting `reply`) when the model's response carries a tool call — required so the loop-back turn (after `route_hub_request` returns) has the full message history, including the tool call and its real result, to compose a final reply from.
- `run_agent_conversation`'s `tools` list gains `request_cross_section_help`, alongside the existing MCP-loaded vault-query tools; its `initial_state` literal gains `"hub_routing_result": None`.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py` — add imports:
  ```python
  import json

  from langchain_core.messages import HumanMessage, ToolMessage
  from langchain_core.tools import tool
  from langgraph.graph import END, StateGraph

  from app.business import agent_keywords, agent_registry, provider_registry, section_registry
  ```
  (`agent_keywords`/`section_registry` are new; `HumanMessage`/`langgraph.graph` imports already exist — merge, do not duplicate.)

  Add the new tool definition, placed after the imports, before `_call_model`:
  ```python
  @tool
  def request_cross_section_help(need_description: str) -> str:
      """Ask another Section's Hub for help with something outside this
      agent's own assigned keywords. need_description: what kind of help
      is needed, described in the requesting agent's own words.

      Deliberately NOT registered on the shared MCP server (ADR-017 point
      7) -- bound directly to this graph's own model call only, never
      loaded through mcp_client.py. This function's own body is never
      actually invoked -- the graph's conditional edge (see
      _route_after_call_model, below) intercepts every call to this tool
      and routes to the route_hub_request node instead, which performs the
      real two-hop lookup. LangGraph's tool-execution convention requires
      a real, importable, schema-bearing callable for model.bind_tools to
      generate the tool's name/description/argument-schema from -- this
      body is unreachable in practice."""
      raise NotImplementedError(
          "request_cross_section_help is intercepted by the route_hub_request "
          "graph node -- this function body is never actually invoked."
      )
  ```

  Extend `_call_model` (replacing the existing function body):
  ```python
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
          messages = current_state["messages"] + [response]
          if getattr(response, "tool_calls", None):
              # A tool call means the model is not done this turn -- do not
              # set "reply" yet. The conditional edge (below) routes to
              # route_hub_request, which loops back here with the tool's
              # real result appended as a ToolMessage, so THIS SAME
              # function composes the final natural-language reply on the
              # next pass through this node (ADR-017 point 5).
              return {"messages": messages}
          return {"messages": messages, "reply": response.content}
      except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel; never swallowed
          return {"error": f"The request to this agent's Provider failed: {exc}"}
  ```

  Add the routing-decision helper and node, placed after `_call_model`:
  ```python
  def route_cross_section_request(requesting_agent_id: str, need_description: str) -> dict:
      """Directly callable public entry point wrapping the exact same
      routing logic as the route_hub_request graph node, below (ADR-017
      point 5) -- lets this story's own tasks verify the routing decision
      directly, without first wiring a live, model-driven tool-call trigger
      end-to-end, mirroring run_agent_conversation's own "public entry
      point, directly testable" precedent (T07). Represents the mandatory
      "own Hub, then target Hub" two-hop relay as two sequential lookups
      (ADR-017 point 6): (a) the requester's own Section, via
      section_registry.get_agent_section -- the first hop; (b)
      agent_keywords.list_candidate_agents_for_keyword_match -- the second
      hop, scanning every agent outside that Section for a keyword-
      substring match. Both hops are recorded as explicit fields on the
      returned result -- a real, inspectable property that the relay went
      through both Hubs, never agent-to-agent directly, not just a
      narrative description of the code path."""
      requester_section = section_registry.get_agent_section(requesting_agent_id)
      from_section_id = requester_section["id"] if requester_section else None
      candidates = agent_keywords.list_candidate_agents_for_keyword_match(
          requesting_agent_id, need_description
      )
      if candidates:
          match = candidates[0]  # first-match-wins, ADR-011's existing tie-break convention
          return {
              "matched": True,
              "agent_id": match["agent_id"],
              "from_section_id": from_section_id,
              "matched_section_id": match["section_id"],
          }
      return {"matched": False, "from_section_id": from_section_id, "matched_section_id": None}


  def _route_hub_request(current_state: AgentConversationState) -> dict:
      last_message = current_state["messages"][-1]
      tool_call = last_message.tool_calls[0]
      need_description = tool_call["args"]["need_description"]
      result = route_cross_section_request(current_state["agent_id"], need_description)
      tool_message = ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
      return {
          "messages": current_state["messages"] + [tool_message],
          "hub_routing_result": result,
      }


  def _route_after_call_model(current_state: AgentConversationState) -> str:
      last_message = current_state["messages"][-1]
      tool_calls = getattr(last_message, "tool_calls", None)
      if tool_calls and tool_calls[0]["name"] == "request_cross_section_help":
          return "route_hub_request"
      return "end"
  ```

  Replace `_build_graph`:
  ```python
  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("call_model", _call_model)
      builder.add_node("route_hub_request", _route_hub_request)
      builder.set_entry_point("call_model")
      builder.add_conditional_edges(
          "call_model",
          _route_after_call_model,
          {"route_hub_request": "route_hub_request", "end": END},
      )
      builder.add_edge("route_hub_request", "call_model")
      return builder.compile()
  ```

  Extend `run_agent_conversation`'s tool list and initial state:
  ```python
      tools = list(asyncio.run(mcp_client.load_vault_query_tools())) + [request_cross_section_help]

      messages = history_entries_to_messages(agent["name"], agent["type"], history)
      messages.append(HumanMessage(content=message))

      initial_state: AgentConversationState = {
          "agent_id": agent_id,
          "messages": messages,
          "model": model,
          "tools": tools,
          "reply": None,
          "error": None,
          "hub_routing_result": None,
      }
  ```
  (Only the `tools` line and the `initial_state` literal change — everything else in `run_agent_conversation` stays byte-for-byte unchanged.)

---

## Constraints

- Inherits from parent story: this is `ADR-015`'s SAME graph, extended by one node/one conditional edge/one local tool — never a second `StateGraph`.
- `request_cross_section_help` must NOT be registered on `app/api/mcp_server.py`, and must NOT be loaded via `mcp_client.py` — it is bound directly in `run_agent_conversation`'s own `tools` list only (`ADR-017` point 7).
- The routing decision itself (`route_cross_section_request`) must stay deterministic — no LLM call inside it; the LLM's only role is deciding *whether* to call the tool and how to phrase the eventual reply, never deciding the match itself.
- The mandatory "own Hub, then target Hub" two-hop relay is represented as two sequential lookups inside ONE node (`_route_hub_request`), never two separate graph nodes (`ADR-017` point 6 — diverges from `ADR-016`'s two-node split deliberately; see that ADR's own Alternatives for why).
- `_call_model`'s pre-existing exception handling, Provider-unavailable short-circuit, and its exact error-message text must be preserved unchanged.
- `run_agent_conversation`'s own public signature (`agent_id, message, history`) and return shape (`{"reply": str}` / `{"error": str}`) are unchanged — this task's own routing capability is reachable only through the model's own tool-calling decision inside the graph, never a new parameter on `run_agent_conversation` itself.
- Both relay hops must be recorded as explicit fields on `route_cross_section_request`'s own return dict (`from_section_id`, and `matched_section_id`/`agent_id` on a match) — this is what makes "went through both Hubs, never agent-to-agent" a real, inspectable property, not just a narrative.
- Do not add an `agent_communication_history.json` audit-log entry for a routed request in this task — `ADR-017` point 6 explicitly leaves that as ordinary future latitude, not mandated by this story's own locked ACs; adding it unprompted would be scope creep beyond what's needed to satisfy the Gherkin.

---

## Tests

<!-- AC-02/AC-03/AC-04 (the routing DECISION itself) are verified here via
route_cross_section_request, the directly-callable entry point ADR-017
point 5 explicitly created for exactly this purpose ("so this story's own
future tasks can verify the routing decision directly without first wiring
a live, model-driven tool-call trigger end-to-end") -- real calls against
the real backend .venv, real section_registry/agent_keywords data, not a
mock. AC-01 (keyword assignment + Hub access) is verified in T06, where the
UI and the persisted-value read-back both exist. -->

**Manual verification steps:**

1. **[REQ-SB-20-US-01-AC-02]** In a Python shell against the backend
   `.venv` (real configured `vault_path`, seeded Sections). Reassign
   `people-producer` to a different Section than `email-capture`'s (default
   `"technical"`) — e.g. `section_registry.set_agent_section("people-
   producer", "customers")`. Assign it keywords:
   `agent_keywords.set_agent_keywords("people-producer", ["people",
   "contacts", "attendee bios"])`. Call
   `graph.route_cross_section_request("email-capture", "I need help
   finding an attendee's bio")`. Confirm the result is exactly `{"matched":
   True, "agent_id": "people-producer", "from_section_id": "technical",
   "matched_section_id": "customers"}` — both hops (the requester's own
   Section, then the target's) are explicit, inspectable fields on the
   result. Confirm via direct inspection of `route_cross_section_request`'s
   own body (the diff applied above) that it never calls any per-agent
   function other than `section_registry.get_agent_section` and
   `agent_keywords.list_candidate_agents_for_keyword_match` — no direct
   call to `people-producer`'s own chat/action/history functions anywhere
   in this path, confirming the relay is genuinely Hub-mediated, never
   agent-to-agent.
2. **[REQ-SB-20-US-01-AC-03]** Call
   `graph.route_cross_section_request("email-capture", "a completely
   unrelated request about deep-sea marine biology")` (no agent's assigned
   keywords match this). Confirm the result is exactly `{"matched": False,
   "from_section_id": "technical", "matched_section_id": None}` — an
   honest, deterministic no-match, not a fabricated or unrelated
   `"agent_id"`. Re-run the identical call 3 more times; confirm the result
   is byte-identical every time (deterministic, no randomness/LLM
   involvement in the decision itself).
3. **[REQ-SB-20-US-01-AC-04]** Confirm `todo-capture` has no keywords
   assigned (`agent_keywords.get_agent_keywords("todo-capture")` returns
   `[]`, the real starting state — never set otherwise in this task's own
   verification). Reassign it to a Section different from `email-capture`'s
   (e.g. `section_registry.set_agent_section("todo-capture",
   "customers")`), so it would otherwise be a same-Section-excluded case
   too — confirming the exclusion is about its **empty keyword list**, not
   coincidentally about Section placement. Call
   `graph.route_cross_section_request("email-capture", "todo capture task
   list scheduling")` (a need description that textually overlaps
   `todo-capture`'s own name/type, to confirm matching is genuinely
   keyword-based, never name-based) 5 times with different, varied need
   descriptions. Confirm `todo-capture` never appears as the `"agent_id"`
   in any result, across all 5 calls — structurally guaranteed by its
   empty keyword list, not a coincidence of what was asked.
4. Non-AC smoke check: confirm `run_agent_conversation("email-capture",
   "What kinds of notes exist in my vault right now?", [])` (a message with
   no plausible reason to trigger `request_cross_section_help`) still
   returns `{"reply": <non-empty string>}` exactly as `REQ-SB-25-US-01-T07`'s
   own smoke check already confirmed — proving this task's graph extension
   does not disturb the existing non-tool-calling path.
5. Clean-up: `agent_keywords.set_agent_keywords("people-producer", [])`,
   `agent_keywords.set_agent_keywords("todo-capture", [])` (already `[]`,
   confirm still so), `section_registry.set_agent_section("people-producer",
   "technical")`, `section_registry.set_agent_section("todo-capture",
   "technical")` — restore the clean seed state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-02** (Scenario 2) — `route_cross_section_request` resolves the
      requester's own Section first, then the target Section via
      cross-Section keyword matching, both hops explicit fields on the
      result; no per-agent function is ever called directly
- [x] **AC-03** (Scenario 3) — an unmatched request returns a deterministic
      `{"matched": False, ...}`, never a fabricated or unrelated match
- [x] **AC-04** (Scenario 4) — an agent with `[]` keywords is never
      selected as a target, regardless of the need description or its own
      Section placement
- [x] `request_cross_section_help` is bound into `run_agent_conversation`'s
      own `tools` list, never registered on `mcp_server.py`/loaded via
      `mcp_client.py`
- [x] `_build_graph` compiles with the new node/conditional edge/loop-back
      edge, on the SAME `StateGraph` `REQ-SB-25-US-01-T07` built — no second graph
- [x] `run_agent_conversation`'s public signature/return shape unchanged;
      its own non-tool-calling smoke check (`T07`'s own AC-01 shape) still passes
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `agents_router.py::chat` wiring the live model-driven tool-call path
  through a real `POST /agents/{id}/chat` HTTP request — that seam is
  `REQ-SB-25-US-01-T08`'s own scope (a sibling story's task, already
  `Ready`); once it lands, this task's tool binding becomes reachable from
  a real chat turn automatically, with no further change needed here. This
  task's own locked-AC verification does not require `T08` to be `Done`
  (see Tests, above — `route_cross_section_request` is the verification
  seam `ADR-017` explicitly designed for this purpose).
- Within-Section routing — explicitly deferred, this story's own Non-Goals.
- An `agent_communication_history.json` audit-log entry for a routed
  request — `ADR-017`'s own explicitly-left latitude, not built this pass
  (see Constraints).
- `model_factory.py`, `mcp_client.py` — untouched.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at
`/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Why AC verification does not require `REQ-SB-25-US-01-T08`:** Scenarios
2–4 describe the routing *decision* itself (who gets asked, honestly,
Hub-mediated) — `ADR-017` point 5 explicitly built
`route_cross_section_request` as a directly-callable public function
specifically "so this story's own future tasks can verify the routing
decision directly without first wiring a live, model-driven tool-call
trigger end-to-end," mirroring `T07`'s own precedent for
`run_agent_conversation`. The LLM-composed final reply's own wording
(whether it "honestly" narrates a no-match to the end user) is a
reply-composition concern layered on top of this deterministic decision
(`ADR-017`'s own Context) — genuinely live-testable only once
`REQ-SB-25-US-01-T08` also lands and wires `chat`'s own no-match branch to
this graph, which is real future work but not required to satisfy this
story's own locked ACs as tightened at `/plan-tasks`.

**This is this codebase's first LangGraph conditional edge / tool-execution
loop** (`ADR-017`'s own Consequences) — if the installed `langgraph`
version's exact `add_conditional_edges`/tool-call inspection API differs in
naming from what's specified above (e.g. `response.tool_calls` shape), adapt
to match the real, installed API exactly and log the deviation as a
scope-internal assumption in the Implementation Log, per
`Implementation/Pipeline.md`'s "scope-internal judgement calls go in the
Implementation Log" rule — this is not grounds for escalation on its own,
mirroring `REQ-SB-25-US-01-T06`'s own identical caveat for
`MultiServerMCPClient`.

---

## Implementation Log

**Built 2026-08-12 (coder).** **Composed around the REAL current
`graph.py`, not this task's own stale "Before" sample — logged here as a
scope-internal judgement call per this project's own established Learnings
pattern ("compose the new change around the REAL current file, never
overwrite it with the stale sample"), not an escalation.** By this point in
the build sequence, `REQ-SB-26-US-01`/`ADR-016` (memory) and the live
tool-execution-loop correction (`REQ-SB-25-US-01-T08`/`REQ-SB-31-US-01`)
had already landed a materially more advanced graph than this task's own
sample assumed: 4 nodes (`retrieve_memory` → `call_model` ⇄
`execute_tools` → `extract_memory`), a **generic** `_execute_tools` node
that already invokes *any* tool call by name via `tools_by_name.get(...)`,
and a `_route_after_model` conditional-edge function that already branches
`call_model`'s output between `execute_tools`/`extract_memory`. This task's
own literal sample (an `_execute_tools`-less, single-tool-round shape) was
written against an earlier version of the file and, applied verbatim,
would have silently regressed both already-`Done` sibling mechanisms.

**Real composition applied instead (same intent, real shape):**
- Added `request_cross_section_help` (verbatim per this task's own code
  block) and the new imports (`json`, `langchain_core.tools.tool`,
  `agent_keywords`, `section_registry`).
- Did **not** need to touch `_call_model` at all — the REAL current
  `_call_model` is already fully generic (binds whatever tools are on
  state, appends its own response to `messages`, sets `reply` only when
  there's no tool call) — this task's own sample only needed to extend
  `_call_model` because the OLDER version it was written against did not
  yet have this generality. No change was the correct change here.
- Added `route_cross_section_request` (verbatim) and a new node,
  `_route_hub_request` (adapted: finds the specific
  `request_cross_section_help` tool call by name within
  `last_message.tool_calls`, rather than assuming index `[0]`, since the
  real generic `_execute_tools` node already establishes the precedent that
  a single AIMessage can carry more than one tool call).
- Extended `_route_after_model` (the REAL current file's actual routing
  function — this task's own sample named a same-purpose function
  `_route_after_call_model`, written against the file's earlier,
  differently-named routing function) with one new branch: when the
  model's tool call is specifically `request_cross_section_help`, route to
  `route_hub_request` **instead of** the generic `execute_tools` node —
  this is the load-bearing correction: the real generic `_execute_tools`
  would otherwise have genuinely invoked `request_cross_section_help`'s own
  intentionally-`NotImplementedError` body (it does a real `tools_by_name`
  lookup and calls `await tool.ainvoke(...)` for *any* tool call), which
  `ADR-017` point 5's whole design depends on never happening — the
  conditional edge must intercept this specific tool call before the
  generic path.
- Extended `_build_graph` with the new `route_hub_request` node and a
  `route_hub_request` → `call_model` loop-back edge, alongside the 3
  pre-existing edges (`execute_tools` → `call_model`, the conditional
  branch, `extract_memory` → `END`) — all pre-existing edges/nodes
  untouched.
- Extended `run_agent_conversation`'s real current tools list (`list(await
  mcp_client.load_vault_query_tools()) + [request_cross_section_help]`) and
  its real current `initial_state` literal (`"hub_routing_result": None`
  added to the real 8-key literal, not the 6-key one this task's own
  sample showed) — every other line byte-for-byte unchanged.

**Live verification (real backend `.venv`, real `section_registry`/
`agent_keywords` data):**

- Graph compiles: `graph._GRAPH.get_graph().nodes` →
  `['__start__', 'retrieve_memory', 'call_model', 'execute_tools',
  'route_hub_request', 'extract_memory', '__end__']` — new node present,
  all 3 pre-existing nodes intact, one graph (not a second). **PASS.**
- **[AC-02]** Reassigned `people-producer` to `"customers"` (a different
  Section than `email-capture`'s own real seed `"productivity"` — the real
  seed state has all 5 agents in Productivity, not Technical, adapting the
  task's own illustrative example accordingly), assigned keywords
  `["people", "contacts", "attendee bios"]`. **Same corrected
  need-description as `T02`'s own Implementation Log** (`"I need help with
  attendee bios for this customer meeting"` — the task's own literal
  example string does not contain any of the 3 keywords as a substring
  under the exact deterministic algorithm; logged there, reused here for
  consistency). `route_cross_section_request("email-capture", ...)` →
  `{"matched": True, "agent_id": "people-producer", "from_section_id":
  "productivity", "matched_section_id": "customers"}` exactly — both hops
  explicit fields. Direct source inspection of `route_cross_section_request`
  confirmed it calls only `section_registry.get_agent_section` and
  `agent_keywords.list_candidate_agents_for_keyword_match` — no
  `agent_chat`/`agents_router`/`.chat(`/`trigger_action`/
  `append_agent_history_entry` reference anywhere in its body — genuinely
  Hub-mediated, never agent-to-agent. **PASS.**
- **[AC-03]** `route_cross_section_request("email-capture", "a completely
  unrelated request about deep-sea marine biology")` called 4 times →
  `{"matched": False, "from_section_id": "productivity",
  "matched_section_id": None}` every time, byte-identical across all 4 —
  honest, deterministic no-match. **PASS.**
- **[AC-04]** Confirmed `todo-capture` has `[]` keywords (real, never-set
  starting state). Reassigned it to `"customers"` (a Section different from
  the requester's too, isolating the empty-keyword-list exclusion from a
  same-Section exclusion). Called `route_cross_section_request` 5 times
  with 5 varied need-descriptions, including ones textually overlapping
  `todo-capture`'s own name (`"todo capture task list scheduling"`,
  `"capture todo now please"`, etc.) — `todo-capture` never appeared as
  `agent_id` in any of the 5 results, confirming the exclusion is
  structurally keyword-based, not name-based or Section-based. **PASS.**
- Non-AC smoke check: `run_agent_conversation("email-capture", "What kinds
  of notes exist in my vault right now?", [])` still returned a real,
  non-empty `{"reply": ...}` (real Compass call, real MCP vault-query tool
  invocation — listed 9 real note kinds from the vault) — confirms this
  task's graph extension does not disturb the pre-existing non-Hub-routing
  path. **PASS.**
- Static check: `request_cross_section_help` appears only in `graph.py`
  across the entire `src/backend/app` tree (`grep`-confirmed) — never
  registered on `mcp_server.py`, never loaded via `mcp_client.py`. **PASS.**
- Clean-up: `people-producer` keywords reset to `[]`; `people-producer`/
  `todo-capture` Sections restored to `"productivity"` — confirmed via
  `section_registry.get_agent_section` on both, matching real seed state.

Every locked AC (`AC-02`/`AC-03`/`AC-04`) verified live against
`route_cross_section_request`, the directly-callable entry point `ADR-017`
point 5 built specifically for this purpose — no dependency on
`REQ-SB-25-US-01-T08`'s live chat-wiring, per this task's own Context.

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note; the composition-around-the-real-file deviation above
is a scope-internal judgement call, logged for human spot-check, not a new
escalation).
