---
id: REQ-SB-40-US-01-T04
title: agent_orchestration/graph.py — record_knowledge_gap tool + _record_knowledge_gap node + routing branch
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T02, REQ-SB-40-US-01-T03]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T04 — `graph.py`'s `record_knowledge_gap` tool + `_record_knowledge_gap` node

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Extend `graph.py`'s SAME compiled `StateGraph` (`ADR-015`'s "grow by node, not by new graph" convention, already used by `ADR-016`/`ADR-017`) with a second interceptable bound tool, `record_knowledge_gap(topic: str)`, intercepted before generic tool execution EXACTLY like `request_cross_section_help`/`route_hub_request` (`ADR-017`, `ADR-032` point 1) — this is this graph's second, not first, tool-interception mechanism, so this task extends an already-real, already-working pattern, not a novel one.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `knowledge_gap_tracking.record_gap(agent_id, question, topic) -> dict`.
- `T03` has landed `AgentConversationState`'s new `gap_recorded: dict | None` key and the system prompt's new `record_knowledge_gap` instruction.
- Real current `graph.py` already has (verbatim, relevant excerpts — **read the REAL current file before applying this diff**, per this project's own repeatedly-confirmed Learnings finding that `graph.py` is its most actively-extended shared file):
  ```python
  @tool
  def request_cross_section_help(need_description: str) -> str:
      """... intercepted by the route_hub_request graph node ..."""
      raise NotImplementedError(
          "request_cross_section_help is intercepted by the route_hub_request "
          "graph node -- this function body is never actually invoked."
      )


  def _route_hub_request(current_state: AgentConversationState) -> dict:
      last_message = current_state["messages"][-1]
      tool_call = next(
          tc for tc in last_message.tool_calls if tc["name"] == "request_cross_section_help"
      )
      need_description = tool_call["args"]["need_description"]
      result = route_cross_section_request(current_state["agent_id"], need_description)
      tool_message = ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
      return {
          "messages": current_state["messages"] + [tool_message],
          "hub_routing_result": result,
      }


  def _route_after_model(current_state: AgentConversationState) -> str:
      if current_state.get("error") is not None or current_state.get("reply") is not None:
          return "extract_memory"
      last_message = current_state["messages"][-1]
      tool_calls = getattr(last_message, "tool_calls", None) or []
      if any(tc["name"] == "request_cross_section_help" for tc in tool_calls):
          return "route_hub_request"
      return "execute_tools"


  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("retrieve_memory", _retrieve_memory)
      builder.add_node("call_model", _call_model)
      builder.add_node("execute_tools", _execute_tools)
      builder.add_node("route_hub_request", _route_hub_request)
      builder.add_node("extract_memory", _extract_memory)
      builder.set_entry_point("retrieve_memory")
      builder.add_edge("retrieve_memory", "call_model")
      builder.add_conditional_edges(
          "call_model", _route_after_model, ["execute_tools", "route_hub_request", "extract_memory"]
      )
      builder.add_edge("execute_tools", "call_model")
      builder.add_edge("route_hub_request", "call_model")
      builder.add_edge("extract_memory", END)
      return builder.compile()


  async def run_agent_conversation(
      agent_id: str, message: str, history: list[dict], memory: list[dict] | None = None
  ) -> dict:
      ...
      tools = list(await mcp_client.load_agent_tools(agent_id)) + [request_cross_section_help]
      ...
      initial_state: AgentConversationState = {
          "agent_id": agent_id,
          "messages": messages,
          "model": model,
          "tools": tools,
          "reply": None,
          "error": None,
          "memory": memory or [],
          "extracted_facts": [],
          "hub_routing_result": None,
      }
      result = await _GRAPH.ainvoke(initial_state)
      ...
  ```

**After / Outputs:**
- `graph.py` gains: the `record_knowledge_gap` tool definition; the `_record_knowledge_gap` node; one more branch in `_route_after_model` (checked AFTER the existing `request_cross_section_help` check, per `ADR-032`'s own documented "only one branch fires" limitation); the new node wired into `_build_graph` with a loop-back edge to `call_model`; `run_agent_conversation`'s tools list and `initial_state` literal extended.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py`:
  - Add import: `from app.business import knowledge_gap_tracking` (alongside the existing `from app.business import agent_keywords, agent_registry, provider_registry, section_registry` line — merge, do not duplicate).
  - Add the new tool definition, placed immediately after `request_cross_section_help`:
    ```python
    @tool
    def record_knowledge_gap(topic: str) -> str:
        """Call this BEFORE giving an honest "I don't know" reply, when
        none of your tools/history/memory can answer the user's question.
        topic: a short label for what you don't know, in your own words.

        Deliberately NOT registered on the shared MCP server, mirroring
        request_cross_section_help (ADR-017 point 7) -- bound directly to
        this graph's own model call only. This function's own body is
        never actually invoked -- the graph's conditional edge (see
        _route_after_model, below) intercepts every call to this tool and
        routes to the _record_knowledge_gap node instead, which records
        the gap using the turn's REAL originating question, never this
        tool's own topic argument alone (models can paraphrase) -- see
        ADR-032 point 1."""
        raise NotImplementedError(
            "record_knowledge_gap is intercepted by the _record_knowledge_gap "
            "graph node -- this function body is never actually invoked."
        )
    ```
  - Add the node, placed after `_route_hub_request`:
    ```python
    def _record_knowledge_gap(current_state: AgentConversationState) -> dict:
        last_message = current_state["messages"][-1]
        tool_call = next(
            tc for tc in last_message.tool_calls if tc["name"] == "record_knowledge_gap"
        )
        topic = tool_call["args"]["topic"]
        # Never trust the model's own topic argument as the durable
        # question text (ADR-032 point 1, models can paraphrase) --
        # deterministically read the turn's real originating HumanMessage
        # instead: this graph replays the full, untruncated history on
        # every call (state.py's own documented no-truncation-this-pass
        # design), so the LAST HumanMessage in current_state["messages"]
        # is reliably this turn's real question.
        question = next(
            m.content for m in reversed(current_state["messages"]) if isinstance(m, HumanMessage)
        )
        record = knowledge_gap_tracking.record_gap(current_state["agent_id"], question, topic)
        tool_message = ToolMessage(
            content=json.dumps({"recorded": True, "gap_id": record["id"]}),
            tool_call_id=tool_call["id"],
        )
        return {
            "messages": current_state["messages"] + [tool_message],
            "gap_recorded": record,
        }
    ```
  - Extend `_route_after_model` with one more branch, checked AFTER the existing `request_cross_section_help` check:
    ```python
    def _route_after_model(current_state: AgentConversationState) -> str:
        if current_state.get("error") is not None or current_state.get("reply") is not None:
            return "extract_memory"
        last_message = current_state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if any(tc["name"] == "request_cross_section_help" for tc in tool_calls):
            return "route_hub_request"
        if any(tc["name"] == "record_knowledge_gap" for tc in tool_calls):
            # Intercepted BEFORE the generic execute_tools node, exactly
            # like request_cross_section_help above -- see
            # record_knowledge_gap's own NotImplementedError body.
            return "record_knowledge_gap"
        return "execute_tools"
    ```
  - Extend `_build_graph`:
    ```python
    def _build_graph():
        builder = StateGraph(AgentConversationState)
        builder.add_node("retrieve_memory", _retrieve_memory)
        builder.add_node("call_model", _call_model)
        builder.add_node("execute_tools", _execute_tools)
        builder.add_node("route_hub_request", _route_hub_request)
        builder.add_node("record_knowledge_gap", _record_knowledge_gap)
        builder.add_node("extract_memory", _extract_memory)
        builder.set_entry_point("retrieve_memory")
        builder.add_edge("retrieve_memory", "call_model")
        builder.add_conditional_edges(
            "call_model",
            _route_after_model,
            ["execute_tools", "route_hub_request", "record_knowledge_gap", "extract_memory"],
        )
        builder.add_edge("execute_tools", "call_model")
        builder.add_edge("route_hub_request", "call_model")
        builder.add_edge("record_knowledge_gap", "call_model")
        builder.add_edge("extract_memory", END)
        return builder.compile()
    ```
  - Extend `run_agent_conversation`'s tools list and `initial_state` literal:
    ```python
        tools = list(await mcp_client.load_agent_tools(agent_id)) + [
            request_cross_section_help,
            record_knowledge_gap,
        ]

        ...

        initial_state: AgentConversationState = {
            "agent_id": agent_id,
            "messages": messages,
            "model": model,
            "tools": tools,
            "reply": None,
            "error": None,
            "memory": memory or [],
            "extracted_facts": [],
            "hub_routing_result": None,
            "gap_recorded": None,
        }
    ```
    (Only the `tools` line and the `initial_state` literal change — every other line of `run_agent_conversation` stays byte-for-byte unchanged.)

---

## Constraints

- Inherits from parent story: this is `ADR-015`'s SAME graph, extended by one node/one conditional-edge branch/one local tool — never a second `StateGraph`.
- `record_knowledge_gap` must NOT be registered on `app/api/mcp_server.py`, and must NOT be loaded via `mcp_client.py` — bound directly in `run_agent_conversation`'s own `tools` list only (`ADR-032` point 1, mirrors `ADR-017` point 7).
- `_record_knowledge_gap` must read the question from the real last `HumanMessage` in `current_state["messages"]`, never from the tool call's own `topic` argument — this is the load-bearing correction `ADR-032` point 1 explicitly calls out ("models can paraphrase").
- If the model's own tool_calls list contains BOTH `request_cross_section_help` and `record_knowledge_gap` in the same turn, only one branch fires (the existing `request_cross_section_help` check stays first) — a known, accepted limitation `ADR-017` already lives with for its own single-interceptable-tool design (`ADR-032`'s own Consequences); not grounds for a third branch or additional logic this pass.
- `_call_model`'s pre-existing exception handling, tool-round-count guard, and Provider-unavailable short-circuit must be preserved unchanged.
- `run_agent_conversation`'s own public signature (`agent_id, message, history, memory`) and return shape (`{"reply": str, "extracted_facts": list[str]}` / `{"error": str}`) are unchanged.
- Do not modify `_retrieve_memory`, `_execute_tools`, `_extract_memory`, `route_cross_section_request`, or `_route_hub_request`.

---

## Tests

<!-- AC-01 (a gap is recorded from the real question, honest reply still
produced) and AC-06 (a normally-answered question records nothing) are
both fully verifiable here via a real Compass-backed run_agent_conversation
call against a real Expert agent (vault-qa) and real vault content -- no
mock. -->

**Manual verification steps:**

1. **[REQ-SB-40-US-01-AC-01]** In a Python shell against the backend `.venv` (real configured `vault_path`, real Compass Provider). Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` is `0` (clean starting state, per `T02`'s own clean-up). Call `await agent_orchestration.run_agent_conversation("vault-qa", "What is the vault's own internal policy on quarterly headcount planning for the Marketing department in 2027?", [])` (a real, in-scope-sounding question with no genuinely relevant vault content — chosen per this project's own Learnings pattern "frame a fabrication test around real vault topics, not an obviously-irrelevant one"). Confirm the reply honestly declines (no fabricated policy). Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` is now `1`. Confirm via `knowledge_gap_tracking.list_agent_gaps("vault-qa")` that the recorded gap's `question` field is the REAL question text sent above (not a short paraphrase) and its `topic` field is a short label — proving the node read the real `HumanMessage`, not the model's own `topic` tool argument, for the durable question text.
2. **[REQ-SB-40-US-01-AC-06]** Call `await agent_orchestration.run_agent_conversation("vault-qa", "What kinds of notes exist in my vault right now?", [])` (a real, answerable question — reuses `T05` of `REQ-SB-20-US-01`'s own confirmed-working smoke-check question). Confirm the reply is a real, non-empty, on-topic answer (not a decline). Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` is UNCHANGED from its value immediately before this call — no spurious gap recorded for a normally answered question.
3. Non-AC smoke check: confirm `graph._GRAPH.get_graph().nodes` includes `'record_knowledge_gap'` alongside all 5 pre-existing nodes (`retrieve_memory`, `call_model`, `execute_tools`, `route_hub_request`, `extract_memory`) plus `__start__`/`__end__` — one graph, new node present, nothing dropped.
4. Static check: confirm `record_knowledge_gap` appears only in `graph.py` across the entire `src/backend/app` tree — never registered on `mcp_server.py`, never loaded via `mcp_client.py`.
5. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`, restoring a clean starting state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1) — an honest decline records a real, id-bearing open gap capturing the turn's real `HumanMessage` as `question` (never the model's `topic` argument alone); the honest decline reply is still produced to the user
- [ ] **AC-06** (Scenario 6) — a normally answered question records no gap; the agent's open-gap count is unchanged
- [ ] `record_knowledge_gap` is bound into `run_agent_conversation`'s own `tools` list, never registered on `mcp_server.py`/loaded via `mcp_client.py`
- [ ] `_build_graph` compiles with the new node/conditional-edge branch/loop-back edge, on the SAME `StateGraph` — no second graph, no pre-existing node/edge removed
- [ ] `run_agent_conversation`'s public signature/return shape unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The two closing paths (`T05`/`T06`) and the list endpoint (`T07`) — this task only records gaps, never closes or lists them via HTTP.
- `AgentDetailPanel.tsx` — `T08`'s own scope.
- The "both tool calls in one turn" edge case beyond the existing `if`/`elif`-shaped single-interception behavior — explicitly accepted per `ADR-032`'s own Consequences, not built further this pass.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**This is this graph's SECOND tool-interception mechanism, not its first** — `request_cross_section_help`/`route_hub_request` (`REQ-SB-20-US-01-T05`, `ADR-017`) already proved this exact pattern out live; this task is a same-shape extension, not a novel mechanism. If the real, current `graph.py` has drifted further since the excerpt above (per this project's own repeated Learnings finding on this specific file), compose this diff around the REAL current file, not this task's own possibly-stale sample — log any such reconciliation as a scope-internal judgement call, not an escalation, mirroring `REQ-SB-20-US-01-T05`'s own Implementation Log precedent for the identical situation.

---

## Implementation Log

Read the REAL current `graph.py` first (matched the task's own "Before" sample verbatim — no sibling-story drift since the sample was authored). Added: `record_knowledge_gap` bound tool (placed after `request_cross_section_help`, `NotImplementedError` body, never registered on `mcp_server.py`/loaded via `mcp_client.py` — confirmed via a static grep across the whole `app` tree that `record_knowledge_gap` appears only in `graph.py`/`state.py`, the latter only in the instruction-text string, not a registration); `_record_knowledge_gap` node (reads the real last `HumanMessage` from `current_state["messages"]`, never the tool's own `topic` argument, per `ADR-032` point 1); one more `_route_after_model` branch, checked after the existing `request_cross_section_help` check; wired into `_build_graph` with a loop-back edge to `call_model`; `run_agent_conversation`'s `tools` list and `initial_state` literal extended with `record_knowledge_gap`/`gap_recorded: None`. Every other line of `run_agent_conversation` and every pre-existing node/edge/`_call_model`/`_execute_tools`/`_extract_memory`/`route_cross_section_request`/`_route_hub_request` left byte-for-byte unchanged.

**[REQ-SB-40-US-01-AC-01] — verified live** against the real running app (`uvicorn --port 8001`), real Compass Provider, real vault: `count_open_gaps("vault-qa")` confirmed `0` (clean start). Called `run_agent_conversation("vault-qa", "What is the vault's own internal policy on quarterly headcount planning for the Marketing department in 2027?", [])` — the model honestly declined (no fabricated policy: *"I couldn't find anything in the vault about a 2027 quarterly headcount planning policy for the Marketing department..."*). `count_open_gaps("vault-qa")` became `1`. `list_agent_gaps("vault-qa")` showed the recorded gap's `question` field is the REAL, full question text sent (not a paraphrase) and `topic` is a short model-chosen label ("Marketing department 2027 quarterly headcount planning policy") — proving the node read the real `HumanMessage`, not the tool's own `topic` argument, for the durable question text. PASS.

**[REQ-SB-40-US-01-AC-06] — verified live**, same session: `run_agent_conversation("vault-qa", "What kinds of notes exist in my vault right now?", [])` produced a real, on-topic, non-empty answer (a live vault-kind listing) — not a decline. `count_open_gaps("vault-qa")` stayed at `1`, unchanged from immediately before this call — no spurious gap recorded. PASS.

Non-AC smoke checks: `graph._GRAPH.get_graph().nodes` includes `'record_knowledge_gap'` alongside all 5 pre-existing nodes + `__start__`/`__end__` — one graph, new node present, nothing dropped. Static grep confirmed `record_knowledge_gap` never appears in `mcp_server.py`/`mcp_client.py`. Cleaned up (`save_knowledge_gaps_state({"gaps": []})`) before T05.

**Post-graph-change regression check (sprint-level, beyond this task's own scope, mandated by the sprint runner):** confirmed ordinary chat — an agent answering something it genuinely knows — still works completely unaffected, on 2 different existing agents, via the real `POST /agents/{id}/chat` HTTP endpoint (not just the direct `run_agent_conversation` call above): `vault-qa` answered "What kinds of notes exist in my vault right now?" correctly; `compass-expert` answered "what is your role and what subject are you meant to know about?" with a real, grounded, non-fabricated reply describing its own real settings/history. Both real, non-error `200` replies, no regression from the graph change.

gate: flagged (carried, trigger-3). No new trigger fired — every mechanism built is `ADR-032`'s own already-made Decision, not an assumption.

status: Done
