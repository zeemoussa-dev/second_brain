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

from app.business import (
    agent_keywords,
    agent_registry,
    glimpse_first_qa,
    knowledge_gap_tracking,
    people_extraction,
    provider_registry,
    section_registry,
    skill_registry,
)
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


@tool
def propose_person_note_update(person_name: str, instruction: str) -> str:
    """Call this when a person-directed Cockpit instruction names a
    real person and describes a specific change to make to their
    Person note (e.g. "@AhmedMoussa is leaving for Core42, update his
    note"). person_name: the mentioned person's name, as written (e.g.
    "Ahmed Moussa" or "AhmedMoussa"). instruction: the specific change
    to propose, in your own words. Only call this once you have
    identified a REAL, SPECIFIC change to propose -- a bare mention
    with no discernible instruction must never trigger this tool.

    Deliberately NOT registered on the shared MCP server, mirroring
    request_cross_section_help/record_knowledge_gap (ADR-017 point 7,
    ADR-032 point 1) -- bound directly to this graph's own model call
    only, and ONLY when the calling agent has a real
    skill_registry.has_skill_access grant for the
    "propose_person_note_update" Skill (ADR-038 point 2 -- this
    graph's first CONDITIONALLY bound tool). This function's own body
    is never actually invoked -- the graph's conditional edge (see
    _route_after_model, below) intercepts every call to this tool and
    routes to the _propose_person_note_update node instead, which
    resolves the real Person note read-only first, then dispatches
    through skill_registry.invoke_skill's full working-mode gate
    (ADR-038 point 4)."""
    raise NotImplementedError(
        "propose_person_note_update is intercepted by the "
        "_propose_person_note_update graph node -- this function body "
        "is never actually invoked."
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


def _glimpse_first_context(current_state: AgentConversationState) -> dict:
    """New node (REQ-SB-58), wired retrieve_memory ->
    glimpse_first_context -> call_model (both edges unconditional,
    mirrors _retrieve_memory's own "always runs, a no-op most of the
    time" shape). Gated to agent_id == "vault-qa" ONLY -- the first
    literal agent-identity gate in this graph (every existing
    conditional gate so far is skill-based or Cockpit-context-based,
    never a hardcoded agent id) -- deliberately narrow: the story's
    own Constraint locks this to an extension of the existing
    vault-qa Expert only; an ungated version would silently change
    every OTHER already-Done agent's chat behavior. Reads the turn's
    real question from the last HumanMessage in current_state[
    "messages"] (mirrors _record_knowledge_gap's own "never trust a
    model-paraphrased arg, read the real originating message"
    precedent, ADR-032 point 1). On a real match, inserts ONE new
    SystemMessage at position 1 -- runs AFTER _retrieve_memory in
    this graph's own edge order, so inserting at position 1 here
    pushes any already-inserted memory SystemMessage back one slot --
    final order [identity, glimpse-context, memory, ...], purely
    additive, no collision. On no match -- an unresolved question, OR
    any agent other than vault-qa -- returns {}, a genuine no-op;
    every existing behavior (Scenario 6, every other agent) stays
    byte-for-byte unchanged. No new AgentConversationState field."""
    if current_state["agent_id"] != "vault-qa":
        return {}
    question = next(
        m.content for m in reversed(current_state["messages"]) if isinstance(m, HumanMessage)
    )
    context = glimpse_first_qa.resolve_glimpse_first_context(question)
    if context is None:
        return {}
    context_message = SystemMessage(
        content=(
            f"The following is the current, synthesized status "
            f"(Glimpse) and durable background (Background) for the "
            f"{context['entity_type']} \"{context['entity_name']}\", "
            f"which this question appears to be about. Prefer this "
            f"content as your primary answer; only fall back to your "
            f"other tools if the operator asks for more detail or a "
            f"citation back to the original evidence.\n\n"
            f"## Glimpse\n{context['glimpse']}\n\n"
            f"## Background\n{context['background']}"
        )
    )
    messages = list(current_state["messages"])
    messages.insert(1, context_message)
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


def _propose_person_note_update(current_state: AgentConversationState) -> dict:
    last_message = current_state["messages"][-1]
    tool_call = next(
        tc for tc in last_message.tool_calls if tc["name"] == "propose_person_note_update"
    )
    person_name = tool_call["args"]["person_name"]
    instruction = tool_call["args"]["instruction"]
    match = people_extraction.find_person_note_by_name(person_name)
    if match is None:
        # No gate involvement at all -- an honest "not found" reply,
        # never a fabricated match, never a created note (Scenario 4,
        # ADR-038 point 4).
        tool_message = ToolMessage(
            content=json.dumps({
                "found": False,
                "message": f"No matching Person note found for {person_name}.",
            }),
            tool_call_id=tool_call["id"],
        )
        return {"messages": current_state["messages"] + [tool_message]}
    result = skill_registry.invoke_skill(
        current_state["agent_id"],
        "propose_person_note_update",
        args={
            "note_path": match["note_path"],
            "person_name": match["name"],
            "instruction": instruction,
            "subject_kind": current_state.get("cockpit_subject_kind"),
            "subject_note_stem": current_state.get("cockpit_subject_note_stem"),
        },
        trigger="cockpit_mention",
    )
    tool_message = ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
    return {"messages": current_state["messages"] + [tool_message]}


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
    if any(tc["name"] == "record_knowledge_gap" for tc in tool_calls):
        # Intercepted BEFORE the generic execute_tools node, exactly
        # like request_cross_section_help above -- see
        # record_knowledge_gap's own NotImplementedError body.
        return "record_knowledge_gap"
    if any(tc["name"] == "propose_person_note_update" for tc in tool_calls):
        # Intercepted BEFORE the generic execute_tools node, exactly
        # like the two existing bound tools above -- see
        # propose_person_note_update's own NotImplementedError body.
        return "propose_person_note_update"
    return "execute_tools"


def _build_graph():
    builder = StateGraph(AgentConversationState)
    builder.add_node("retrieve_memory", _retrieve_memory)
    builder.add_node("glimpse_first_context", _glimpse_first_context)
    builder.add_node("call_model", _call_model)
    builder.add_node("execute_tools", _execute_tools)
    builder.add_node("route_hub_request", _route_hub_request)
    builder.add_node("record_knowledge_gap", _record_knowledge_gap)
    builder.add_node("propose_person_note_update", _propose_person_note_update)
    builder.add_node("extract_memory", _extract_memory)
    builder.set_entry_point("retrieve_memory")
    builder.add_edge("retrieve_memory", "glimpse_first_context")
    builder.add_edge("glimpse_first_context", "call_model")
    builder.add_conditional_edges(
        "call_model",
        _route_after_model,
        [
            "execute_tools", "route_hub_request", "record_knowledge_gap",
            "propose_person_note_update", "extract_memory",
        ],
    )
    builder.add_edge("execute_tools", "call_model")
    builder.add_edge("route_hub_request", "call_model")
    builder.add_edge("record_knowledge_gap", "call_model")
    builder.add_edge("propose_person_note_update", "call_model")
    builder.add_edge("extract_memory", END)
    return builder.compile()


_GRAPH = _build_graph()


async def run_agent_conversation(
    agent_id: str,
    message: str,
    history: list[dict],
    memory: list[dict] | None = None,
    cockpit_subject_kind: str | None = None,
    cockpit_subject_note_stem: str | None = None,
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
        tools = list(await mcp_client.load_agent_tools(agent_id)) + [
            request_cross_section_help,
            record_knowledge_gap,
        ]
        if skill_registry.has_skill_access(agent_id, "propose_person_note_update"):
            tools.append(propose_person_note_update)

        messages = history_entries_to_messages(agent["name"], agent["type"], history, agent_id)
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
            "gap_recorded": None,
            "cockpit_subject_kind": cockpit_subject_kind,
            "cockpit_subject_note_stem": cockpit_subject_note_stem,
        }
        result = await _GRAPH.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-31 Scenario 8); closes the one remaining unwrapped gap in this function's own body, never left to propagate as a raw 500
        return {"error": f"Something went wrong while processing this message: {exc}"}
    if result.get("error"):
        return {"error": result["error"]}
    return {"reply": result["reply"], "extracted_facts": result.get("extracted_facts", [])}
