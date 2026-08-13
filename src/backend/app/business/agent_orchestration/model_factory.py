"""Resolves a per-agent langchain_openai.ChatOpenAI instance from that
agent's selected Provider (REQ-SB-19's provider_registry), the single
source of LLM connection configuration for this new conversational
surface too (ADR-015 point 4). Returns None -- an explicit "unavailable"
signal -- before any model is constructed or called, when the Provider
has no real client -- mirrors agents_router.py::_invoke_action's existing
"declared but not yet backed by a real handler -> honest unavailability,
no silent fallback, no fabricated response" funnel-gate shape (ADR-011
point 3 / ADR-014 point 7), applied one layer over for conversational
replies (ADR-015 point 3, REQ-SB-25 Scenario 4)."""
from langchain_openai import ChatOpenAI

from app.business import provider_registry


def resolve_agent_model(agent_id: str) -> ChatOpenAI | None:
    provider = provider_registry.get_agent_provider(agent_id)
    if provider is None or not provider_registry.has_real_client(provider["id"]):
        return None
    return ChatOpenAI(
        # provider["endpoint"] is the FULL completions URL (e.g.
        # ".../v1/chat/completions") -- the shape app/data_access/
        # compass_client.py's own plain httpx.post(url, ...) call expects
        # directly. langchain_openai.ChatOpenAI wraps the OpenAI Python
        # SDK client, which appends "/chat/completions" onto base_url
        # itself -- passing the full endpoint unmodified double-appends
        # the suffix and 404s (confirmed live during this task's own
        # verification: a real Compass call failed with "404 Not Found"
        # until this strip was added, then succeeded). Stripping the
        # known suffix recovers the root the SDK actually expects,
        # without changing provider_registry's own stored shape (which
        # compass_client.py still consumes unmodified).
        base_url=provider["endpoint"].removesuffix("/chat/completions"),
        api_key=provider["credential"],
        model=provider["model"],
    )
