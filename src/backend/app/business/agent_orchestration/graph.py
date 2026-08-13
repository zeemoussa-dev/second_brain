"""Compiles Second Brain's own single in-app LangGraph conversation
graph and exposes run_agent_conversation as this package's one public
entry point (ADR-015 point 3). This pass needs a model-call node,
tool-bound from the start (ADR-015 point 3's own explicit decision),
plus the minimal tool-execution mechanics a tool-bound model actually
needs to produce a real reply rather than stalling on an unexecuted tool
call -- confirmed live during this task's own verification: a real,
ordinary vault-query question genuinely triggers a real tool call, not
just a direct text answer, so leaving tool calls unexecuted silently
broke Scenario 1 for exactly the questions the MCP tool integration
exists to answer. REQ-SB-26/ADR-016 extends this SAME graph with two new
nodes -- retrieve_memory (read path, before call_model) and
extract_memory (write path, once call_model has produced a final reply,
same .invoke() call, no second Provider resolution) -- rather than a
second graph, per ADR-015 points 3/9's "grow by adding nodes" pattern.
REQ-SB-20/ADR-017 extends this SAME graph with one more node,
route_hub_request, reached via a conditional branch off the existing
call_model->{execute_tools|extract_memory} routing decision whenever the
model's tool call is specifically request_cross_section_help (never
routed through the generic execute_tools node, which would otherwise
just invoke that tool's own intentionally-NotImplementedError body) --
see _route_after_model, below. REQ-SB-27 is expected to extend this SAME
graph further -- do not build a second graph for a future requirement;
extend this one."""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph

from app.business import agent_keywords, agent_registry, provider_registry, section_registry
from app.business.agent_orchestration import mcp_client, model_factory
from app.business.agent_orchestration.state import (
    AgentConversationState,
    history_entries_to_messages,
)

# A hard ceiling on model<->tool round-trips within THIS turn alone,
# not the replayed conversation history (no new state field needed --
# AgentConversationState, T02's own file, is left unmodified). Guards
# against a pathological non-converging tool call loop; well-behaved real
# calls converge in 1-2 rounds for the four thin, read-only tools this
# pass registers (ADR-015 point 11).
_MAX_MODEL_TOOL_ROUNDS = 5

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


@tool
def request_cross_section_help(need_description: str) -> str:
    """Ask another Section's Hub for help with something outside this
    agent's own assigned keywords. need_description: what kind of help
    is needed, described in the requesting agent's own words.

    Deliberately NOT registered on the shared MCP server (ADR-017 point
    7) -- bound directly to this graph's own model call only, never
    loaded through mcp_client.py. This function's own body is never
    actually invoked -- the graph's conditional edge (see
    _route_after_model, below) intercepts every call to this tool and
    routes to the route_hub_request node instead, which performs the
    real two-hop lookup. LangGraph's tool-execution convention requires
    a real, importable, schema-bearing callable for model.bind_tools to
    generate the tool's name/description/argument-schema from -- this
    body is unreachable in practice."""
    raise NotImplementedError(
        "request_cross_section_help is intercepted by the route_hub_request "
        "graph node -- this function body is never actually invoked."
    )


def _current_turn_tool_round_count(messages: list) -> int:
    """Walks backward from the end of `messages`, counting completed
    model<->tool rounds belonging to THIS turn only -- an AIMessage with
    tool_calls counts as one completed round, a ToolMessage is part of an
    in-progress round (skipped), and anything else (the current turn's
    own HumanMessage, a plain AIMessage with no tool_calls, a
    SystemMessage) marks the true start of this turn and stops the walk.
    Deliberately does NOT just count every AIMessage in `messages` --
    that would also count replayed history's own past "chat_agent" turns
    (state.py's history_entries_to_messages maps each one to a plain,
    tool_calls-less AIMessage), which grows with every prior message in
    the conversation regardless of this turn's own tool activity --
    exactly the bug found live verifying REQ-SB-25-US-01-AC-03 (a second
    turn in an otherwise-ordinary conversation immediately hit a false
    "too many tool calls" error once enough unrelated history existed)."""
    count = 0
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.tool_calls:
            count += 1
        elif isinstance(m, ToolMessage):
            continue
        else:
            break
    return count


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
    if _current_turn_tool_round_count(current_state["messages"]) >= _MAX_MODEL_TOOL_ROUNDS:
        return {"error": "This agent made too many tool calls without producing a reply."}
    try:
        tools = current_state["tools"]
        bound_model = model.bind_tools(tools) if tools else model
        response = bound_model.invoke(current_state["messages"])
        updated_messages = current_state["messages"] + [response]
        if response.tool_calls:
            return {"messages": updated_messages}
        return {"messages": updated_messages, "reply": response.content}
    except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (Scenario 5); never swallowed
        return {"error": f"The request to this agent's Provider failed: {exc}"}


async def _execute_tools(current_state: AgentConversationState) -> dict:
    """Runs every pending tool call the model's last message requested,
    appending each result as a ToolMessage -- the minimal mechanics a
    tool-bound model (ADR-015 point 3) needs to actually use the tools
    it's bound to, rather than the graph ending on an empty reply the
    moment the model chooses to call one.

    Async node (not the earlier `asyncio.run(tool.ainvoke(...))` sync
    bridge) -- found live 2026-08-12 debugging "chat doesn't work at
    all": a nested `asyncio.run()` call made from a graph node that is
    itself reached via `_GRAPH.invoke()` inside a `run_in_threadpool`-
    scheduled sync request handler creates a second event loop, in a
    worker thread, that then tries to loop back into this same server
    process over real HTTP (the MCP client's own loopback call) -- a
    self-connection that reliably fails with `httpcore.ConnectError: All
    connection attempts failed` in that specific nested-event-loop
    configuration on this host, even though the identical MCP client
    call succeeds immediately when run standalone (confirmed via a
    direct isolated script). The MCP-loaded tools (`langchain_mcp_
    adapters`) are async-only -- `tool.invoke()` raises "StructuredTool
    does not support sync invocation" -- so `await tool.ainvoke(...)`
    here (this node now genuinely async, invoked via `_GRAPH.ainvoke()`
    below) is the fix: one event loop for the whole request, no nested
    loop, no self-connection."""
    tools_by_name = {tool.name: tool for tool in current_state["tools"]}
    last_message = current_state["messages"][-1]
    tool_messages: list[ToolMessage] = []
    for tool_call in last_message.tool_calls:
        tool = tools_by_name.get(tool_call["name"])
        if tool is None:
            result = f"Unknown tool: {tool_call['name']}"
        else:
            try:
                result = await tool.ainvoke(tool_call["args"])
            except Exception as exc:  # noqa: BLE001 -- surfaced to the model as the tool's own result, not swallowed
                result = f"Tool call failed: {exc}"
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    return {"messages": current_state["messages"] + tool_messages}


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
    turn", never a propagated error).

    Live-discovered correction vs. this task's own literal code sample
    (recorded in this task's own Implementation Log, gate: flagged for
    human spot-check): the sample builds its completion context as
    current_state["messages"] + [AIMessage(reply), HumanMessage(
    instructions)], written against an earlier, simpler call_model that
    did NOT append its own response onto current_state["messages"]. The
    REAL, already-Done call_model (REQ-SB-25-US-01-T08's own live tool-
    execution-loop correction) DOES append its response -- including the
    final, non-tool-call reply -- onto messages before returning
    (updated_messages = current_state["messages"] + [response]). Re-
    appending AIMessage(current_state["reply"]) here would therefore
    duplicate the model's own final reply message in the extraction
    completion's context. Corrected to append only the extraction
    HumanMessage -- current_state["messages"] already ends with the
    real AIMessage reply by the time this node runs."""
    if current_state.get("error"):
        return {}
    model = current_state["model"]
    try:
        response = model.invoke(
            current_state["messages"] + [HumanMessage(content=_EXTRACTION_INSTRUCTIONS)]
        )
        raw = (response.content or "").strip()
    except Exception:  # noqa: BLE001 -- best-effort; never propagated as a chat-facing error
        return {"extracted_facts": []}
    if not raw or raw.strip().upper() == "NONE":
        return {"extracted_facts": []}
    facts = [line.strip("- ").strip() for line in raw.splitlines()]
    facts = [fact for fact in facts if fact and fact.upper() != "NONE"]
    return {"extracted_facts": facts}


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
        # Intercepted BEFORE the generic execute_tools node -- that node
        # would otherwise invoke this tool's own real (intentionally
        # NotImplementedError) body; the two-hop Hub relay lives in
        # route_hub_request instead (ADR-017 point 5/6).
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


_GRAPH = _build_graph()


async def run_agent_conversation(
    agent_id: str, message: str, history: list[dict], memory: list[dict] | None = None
) -> dict:
    """Returns {"reply": str, "extracted_facts": list[str]} on a real,
    successful conversational reply, or {"error": str} on honest
    unavailability or a failed real Provider call -- never a fabricated
    reply, and never an "extracted_facts" key on the error path. Runs
    statelessly per call -- no LangGraph checkpointer; `history` (the
    conversation's prior turns, NOT including `message`) and the new
    `memory` (ADR-016) are both passed in fresh on every call and
    replayed into the graph's initial state (ADR-015 point 6).

    Genuinely async (not the earlier `asyncio.run()`-wrapped sync
    function) -- see `_execute_tools`'s own docstring for the full
    root-cause writeup of the nested-event-loop self-connection bug this
    fixes. The caller (`agents_router.py::chat`) must now `await` this
    directly as a true async def, not call it from a thread-pooled sync
    handler -- that thread-pool hop is exactly what created the second
    event loop in the first place."""
    agent = agent_registry.get_agent(agent_id)

    model = model_factory.resolve_agent_model(agent_id)
    if model is None:
        provider = provider_registry.get_agent_provider(agent_id)
        provider_name = provider["name"] if provider else "This agent's selected Provider"
        return {"error": f"{provider_name} is not available yet — no client has been built for it."}

    try:
        tools = list(await mcp_client.load_agent_tools(agent_id)) + [request_cross_section_help]

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
            "hub_routing_result": None,
        }
        result = await _GRAPH.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-31 Scenario 8); closes the one remaining unwrapped gap in this function's own body, never left to propagate as a raw 500
        return {"error": f"Something went wrong while processing this message: {exc}"}
    if result.get("error"):
        return {"error": result["error"]}
    return {"reply": result["reply"], "extracted_facts": result.get("extracted_facts", [])}
