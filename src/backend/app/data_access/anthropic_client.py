"""Client for Anthropic's own Messages API, using its server-side
web-search tool (ADR-022 point 2) — the operator-confirmed mechanism
for real web research. A plain anthropic SDK client, mirroring
compass_client.py's own "plain client, no framework wrapper" shape
(ADR-003) for a fixed-purpose external call; NOT routed through
model_factory.py/LangChain, since this call never touches
run_agent_conversation's own graph (ADR-022's own Non-Goals)."""
from __future__ import annotations

import anthropic


class AnthropicResearchError(Exception):
    """The Anthropic call failed or returned an unparseable response."""


def web_search(api_key: str, model: str, query: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            # Exact current tool-type identifier / API version confirmed
            # against the real, installed anthropic SDK (0.121.0) at
            # build time (this project's established
            # "pin-then-verify-at-real-install" precedent, ADR-015
            # point 6) -- adapt the literal "type" string below if it
            # has since changed, logging the deviation in the
            # Implementation Log, not grounds for escalation on its own.
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": query}],
        )
    except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel
        raise AnthropicResearchError(f"Anthropic web-search call failed: {exc}") from exc

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    summary = "\n".join(text_blocks).strip()
    sources = _extract_sources(response)

    if not summary:
        return {"found": False, "summary": "", "sources": []}
    return {"found": True, "summary": summary, "sources": sources}


def _extract_sources(response) -> list[str]:
    """Pulls citation/source URLs out of the response's own text-block
    citations (each a TextCitation; CitationsWebSearchResultLocation is
    the variant carrying a real .url, confirmed against the real,
    installed anthropic SDK version at build time -- see the module
    docstring's own caveat); returns [] rather than raising if no source
    metadata is present, never fabricating a URL."""
    sources: list[str] = []
    for block in getattr(response, "content", []):
        for citation in getattr(block, "citations", None) or []:
            url = getattr(citation, "url", None)
            if url:
                sources.append(url)
    return sources
