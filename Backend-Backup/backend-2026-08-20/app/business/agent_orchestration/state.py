"""The LangGraph conversation graph's state schema (ADR-015 point 3),
and the mapping from this project's own existing agent_communication_
history.json shape into the graph's replayed LangChain message list
(architecture.md's 2026-08-12 Addendum — REQ-SB-25-US-01
architecture-scoping confirmation). REQ-SB-26/ADR-016 additively extends
this state with memory (input, stored facts folded in by retrieve_memory)
and extracted_facts (output, produced by extract_memory) -- see graph.py.
REQ-SB-20/ADR-017 additively extends this state with hub_routing_result
(output, produced by graph.py's route_hub_request node) -- see graph.py.
REQ-SB-40/ADR-032 additively extends this state with gap_recorded
(output, produced by graph.py's _record_knowledge_gap node) -- see
graph.py.
REQ-SB-66-US-01-T03/ADR-044 additively extends history_entries_to_
messages with an optional, per-agent Prompt override lookup -- see the
function's own docstring below."""
from typing import TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.business import agent_prompts


class AgentConversationState(TypedDict):
    agent_id: str
    messages: list[BaseMessage]
    model: BaseChatModel | None
    tools: list
    reply: str | None
    error: str | None
    memory: list[dict]
    extracted_facts: list[str]
    hub_routing_result: dict | None
    gap_recorded: dict | None
    cockpit_subject_kind: str | None
    cockpit_subject_note_stem: str | None


def history_entries_to_messages(
    agent_name: str, agent_type: str, history: list[dict], agent_id: str | None = None
) -> list[BaseMessage]:
    """Maps agent_communication_history.json's existing entry shape
    ({"kind": "chat_user" | "chat_agent" | "run_event", "text": str,
    "timestamp": iso8601}) into the graph's replayed message list:
    "chat_user" -> HumanMessage, "chat_agent" -> AIMessage. "run_event"
    entries are deliberately excluded -- they are action-trigger audit-log
    entries (ADR-011/REQ-SB-13-US-01's own shape), not conversational
    turns, and presenting one to the model as something the user or agent
    "said" would be actively misleading. One SystemMessage is prepended
    from the agent's own registry name/type, carrying both the identity
    sentence and a grounding/honest-uncertainty instruction
    (REQ-SB-33-US-01) -- still exactly one SystemMessage, not two. No
    history window/truncation this pass -- the full list is replayed on
    every call (a token-budget concern is REQ-SB-24's own separate
    scope).

    agent_id (REQ-SB-66-US-01-T03/ADR-044, optional, additive) -- when
    given, agent_prompts.get_prompt(agent_id) is resolved and, when a
    stored override exists, its text REPLACES this SystemMessage's own
    hardcoded default text verbatim. The honest-uncertainty/grounding
    MECHANISM (the record_knowledge_gap tool call graph.py's own nodes
    wire up) is untouched either way -- only this DEFAULT TEXT becomes
    overridable (REQ-SB-33-US-01 stays intact regardless of override
    text). agent_id=None (or an id with no stored override) reproduces
    today's byte-for-byte hardcoded sentence -- the Scenario 4/AC-04
    regression bar."""
    default_identity_and_grounding_text = (
        f"You are the {agent_name} agent for the user's personal "
        "Second Brain knowledge base. Answer only from what your "
        "own tool calls, the replayed conversation history below, "
        "any stored memory, or any Customer/Project Glimpse/Background "
        "context provided to you below, when present, actually "
        "contain -- never state something as a real fact unless it "
        "came from one of those real sources. If a tool call fails or "
        "returns an error, say so honestly; never invent a substitute answer "
        "in its place. If none of your tools return a relevant "
        "result for a question you would otherwise be able to "
        "answer, honestly say you don't know or couldn't find an "
        "answer -- never guess, and never answer from your own "
        "general training knowledge as if it were a real fact "
        "from this knowledge base. Whenever you determine that "
        "an honest \"I don't know\" is the right reply, first "
        "call the record_knowledge_gap tool with a short topic "
        "label describing what you don't know, then give that "
        "honest reply as normal."
    )
    prompt_override = agent_prompts.get_prompt(agent_id) if agent_id is not None else None
    system_message_text = (
        prompt_override if prompt_override is not None else default_identity_and_grounding_text
    )
    messages: list[BaseMessage] = [SystemMessage(content=system_message_text)]
    for entry in history:
        if entry["kind"] == "chat_user":
            messages.append(HumanMessage(content=entry["text"]))
        elif entry["kind"] == "chat_agent":
            messages.append(AIMessage(content=entry["text"]))
        # "run_event" entries are intentionally excluded — see docstring.
    return messages
