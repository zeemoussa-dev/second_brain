"""Per-agent free-text keywords describing what an agent knows (ADR-017),
composed alongside app/business/agent_registry.py and
app/business/section_registry.py, not inside either -- agent_registry.py
itself is not modified (ADR-011 point 2's "agent identity/type/actions
stay hardcoded" reasoning stays untouched). Powers Section-Hub
cross-Section keyword-substring routing (REQ-SB-20), reusing ADR-011's
exact matching posture one layer up at the Hub level."""
from app.business import agent_registry, background_agent_registry, section_registry
from app.data_access import vault_writer


def get_agent_keywords(agent_id: str) -> list[str]:
    return vault_writer.load_agent_keywords(agent_id)


def set_agent_keywords(agent_id: str, keywords: list[str]) -> list[str]:
    """Whole-list replace semantics, matching the free-text kv-list
    editing UX the Agent Settings panel already uses for other per-agent
    fields -- no incremental add/remove-one-keyword call is implied or
    required (ADR-017 point 3)."""
    vault_writer.save_agent_keywords(agent_id, keywords)
    return keywords


def list_candidate_agents_for_keyword_match(
    requesting_agent_id: str, need_description: str
) -> list[dict]:
    """Deterministic, case-insensitive keyword-substring matching
    (ADR-011's exact posture, unchanged -- reused one layer up), scanning
    every OTHER agent whose Section differs from the requesting agent's
    own Section (cross-Section only -- this story's own Constraint
    deferring within-Section routing). Returns every matching candidate,
    in agent_registry.list_agents() order, as
    [{"agent_id": str, "section_id": str}, ...] -- first-match-wins
    tie-break (ADR-011's existing convention) is the caller's own
    responsibility (T05's route_hub_request/route_cross_section_request),
    not decided here, so callers can inspect every candidate if ever
    needed. An agent with an empty keyword list is structurally never a
    candidate -- no substring of an empty list ever matches
    need_description (ADR-017 point 4, "satisfied by construction, not
    an explicit exclusion check")."""
    requester_section = section_registry.get_agent_section(requesting_agent_id)
    requester_section_id = requester_section["id"] if requester_section else None
    all_keywords = vault_writer.load_all_agent_keywords()
    need_description_lower = need_description.lower()

    candidates = []
    for agent in agent_registry.list_agents():
        agent_id = agent["id"]
        if agent_id == requesting_agent_id:
            continue
        if background_agent_registry.get_is_background_agent(agent_id):
            continue  # REQ-SB-51-US-01 -- never a Hub-routing candidate
        agent_section = section_registry.get_agent_section(agent_id)
        agent_section_id = agent_section["id"] if agent_section else None
        if agent_section_id == requester_section_id:
            continue  # within-Section routing is out of scope this pass
        agent_own_keywords = all_keywords.get(agent_id, [])
        if any(keyword.lower() in need_description_lower for keyword in agent_own_keywords):
            candidates.append({"agent_id": agent_id, "section_id": agent_section_id})
    return candidates
