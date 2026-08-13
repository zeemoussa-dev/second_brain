"""The skill repository's code-level catalog (ADR-015 points 3/7/9) --
a new sibling module to app/business/vault_query_tools.py, both siblings
of app/business/agent_orchestration/. A skill's actual specialized-task
logic is necessarily code: an @mcp.tool()-decorated Python function
registered on Second Brain's shared MCP server, never a runtime
user-created entry (REQ-SB-27-US-01's own Constraints). This pass
registers exactly one illustrative stub skill whose body unconditionally
returns the honest "not yet available" response -- no real handler is
built (see the parent story's own Non-Goals). SKILLS is the single source
of truth app/business/skill_registry.py reads directly, never derived by
introspecting the MCP server's full live tool list (which would also
surface vault_query_tools.py's non-skill tools)."""
from app.api.mcp_server import mcp_server
from app.business import provider_registry
from app.data_access import anthropic_client

SKILLS: dict[str, dict] = {
    "diagram-understanding": {
        "id": "diagram-understanding",
        "name": "Diagram Understanding",
        "description": (
            "Given an uploaded image, identify and describe the "
            "components in an architecture/engineering diagram."
        ),
    },
    "web-research": {
        "id": "web-research",
        "name": "Web Research",
        "description": (
            "Given a research subject or query, gather real, current "
            "information from the web -- using the invoking agent's own "
            "linked Provider's real web-search capability (Anthropic "
            "Claude's own server-side web-search tool, today)."
        ),
    },
}


@mcp_server.tool()
def diagram_understanding() -> dict:
    """Given an uploaded image, identify and describe the components in
    an architecture/engineering diagram. Not yet available -- no
    multimodal-capable Provider exists yet (REQ-SB-27-US-01's own
    Non-Goals); this stub always returns an honest "not available"
    response, never a fabricated or guessed result."""
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }


_ANTHROPIC_PROVIDER_ID = "anthropic-claude"


@mcp_server.tool()
def web_research(query: str, agent_id: str) -> dict:
    """Given a research subject or query, gather real, current
    information from the web -- via whichever real Provider the
    INVOKING AGENT is itself linked to (operator correction, 2026-08-12,
    superseding ADR-022 point 3's original fixed-"anthropic-claude"-id
    design -- see ADR-022's own Correction addendum), not a single
    hardcoded Provider id. Only Anthropic Claude has a genuine, hosted
    server-side web-search tool (confirmed live against this codebase's
    own compass_client.py and the sibling agentic-map project's own
    gateway, which uses a dedicated Perplexity Sonar provider for real
    web search specifically because Compass/GPT-5 has none) -- an agent
    linked to any other Provider (Compass, or no Provider at all)
    honestly reports unavailability, exactly Scenario 4's existing
    shape, rather than fabricating a "researched" result from a plain,
    ungrounded completion (REQ-SB-33's own grounding guardrail).
    Honestly reports no results if a real Anthropic search genuinely
    finds nothing relevant -- never a fabricated result in any branch."""
    provider = provider_registry.get_agent_provider(agent_id)
    if (
        provider is not None
        and provider["id"] == _ANTHROPIC_PROVIDER_ID
        and provider_registry.has_real_client(_ANTHROPIC_PROVIDER_ID)
    ):
        return anthropic_client.web_search(provider["credential"], provider["model"], query)
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }
