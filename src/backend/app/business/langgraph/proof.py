"""Standalone proof that LangGraph is real, working infrastructure in this
codebase (2026-08-20, operator: "we need Proof... Deploy... LangGraph So
Now our Backend infrastructure is there") -- deliberately decoupled from
the old, archived-adjacent agent_orchestration/graph.py (which is tightly
bound to provider_registry/agent_registry/section_registry/skill_registry,
the exact machinery this redesign is retiring). Uses langgraph.prebuilt.
create_react_agent (the standard, idiomatic tool-calling loop) with a
real Compass-backed model and one real tool bound straight to Second
Brain's own data -- not a mock, not a fabricated response. Live-verified
end-to-end (2026-08-20): the full message trace shows a real tool_call to
list_known_customers, a real (empty, matching actual current vault state)
ToolMessage, then a real final reply -- not the model answering from
guesswork.

Known, disclosed gap: langgraph.prebuilt.create_react_agent is deprecated
as of LangGraph v1.0 (confirmed live via a real runtime warning), moved to
langchain.agents.create_agent -- but the `langchain` package itself isn't
an installed dependency here (only langgraph/langchain_core/
langchain_openai are), so switching would mean adding a new dependency,
not a drop-in import change. Left as-is for this proof since it still
works correctly today; worth fixing before this becomes real production
code, not before.
"""
from __future__ import annotations

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.config import settings
from app.data_access import vault_writer


@tool
def list_known_customers() -> list[str]:
    """List every distinct customer value currently used across the
    vault's notes."""
    return vault_writer.list_known_customers()


def run_proof_graph(message: str) -> str:
    """Builds a fresh ReAct agent graph (model + the one real tool above),
    invokes it with `message`, and returns the model's final text reply.
    Every call constructs the model straight from app.config.settings
    (Compass) -- no dependency on provider_registry or any other
    to-be-retired registry."""
    model = ChatOpenAI(
        base_url=settings.compass_base_url.removesuffix("/chat/completions"),
        api_key=settings.compass_api_key,
        model=settings.compass_model,
    )
    graph = create_react_agent(model, tools=[list_known_customers])
    result = graph.invoke({"messages": [{"role": "user", "content": message}]})
    return result["messages"][-1].content
