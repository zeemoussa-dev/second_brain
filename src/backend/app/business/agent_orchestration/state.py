"""The LangGraph conversation graph's state schema (ADR-015 point 3),
and the mapping from this project's own existing agent_communication_
history.json shape into the graph's replayed LangChain message list
(architecture.md's 2026-08-12 Addendum — REQ-SB-25-US-01
architecture-scoping confirmation). REQ-SB-26/ADR-016 additively extends
this state with memory (input, stored facts folded in by retrieve_memory)
and extracted_facts (output, produced by extract_memory) -- see graph.py.
REQ-SB-20/ADR-017 additively extends this state with hub_routing_result
(output, produced by graph.py's route_hub_request node) -- see graph.py."""
from typing import TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


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


def history_entries_to_messages(
    agent_name: str, agent_type: str, history: list[dict]
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
    scope)."""
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
    for entry in history:
        if entry["kind"] == "chat_user":
            messages.append(HumanMessage(content=entry["text"]))
        elif entry["kind"] == "chat_agent":
            messages.append(AIMessage(content=entry["text"]))
        # "run_event" entries are intentionally excluded — see docstring.
    return messages
