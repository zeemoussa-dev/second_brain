"""Meeting Moderator roster recommendation (ADR-009, REQ-SB-82-US-03) and
live per-question routing (REQ-SB-82-US-04/-06) -- three independent
routing/matching tracks live in this module: two purely deterministic
(`match_domain_experts`, `route_question`) and one
LLM-based (`route_question_llm`, ADR-012 point 2, composing `compass_client`
for real reasoning over the brought-in roster/history/message, demoted-to-
degrade-path relationship with `route_question` owned by `chat_turn.py`,
ADR-012 point 3).

Business-specific matching -- which Expert fits a subject because of a
concept the framework does not know, such as its Customer -- comes from
installed plugins' agent matchers (`recommended_experts`/`fallback_agent`,
`BUG-063`, Entities plan Phase 5).

`match_domain_experts` -- tokenized keyword overlap (operator's own
"lightweight... refine later if too coarse" resolution, ADR-009) between
the subject's own tags/subject text and every real `type: "expert"`
agent's already-exposed `GET /agents` `name`/`description` fields
(`agents_map_adapter.list_agent_summaries()`) -- `[]` when nothing
overlaps. `_OVERLAP_STOPWORDS` excludes generic vocabulary this project's
own real, currently-mirrored profile descriptions all repeat regardless of
topic (e.g. "real", "specialist", "for", "customer", tag-namespace prefixes
like "kind/"/"partner/") -- without it, boilerplate phrasing shared by
every profile ("Customer Expert for <X>") would coarsely match ANY
customer-tagged subject against EVERY Customer Expert, not just its own.
"""
from __future__ import annotations

import re

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes import agents_map_adapter
from app.data_access import compass_client

_agent_manager = AgentManager()
_vault_manager = VaultManager()

# Real bug, found live 2026-08-26 (REQ-SB-82-US-04's own live-question
# routing/suggestion): the original list here was curated for matching
# against TAGS/STEMS (terse noun phrases) -- fine for `match_domain_experts`'
# original use, but `route_question`/`suggest_expert_for_question` score
# against a user's own free-text QUESTION too, and ordinary English
# sentence words ("what", "these", "days"...) showing up incidentally in a
# profile's own prose description ("...what it is, its services...")
# produced a spurious 1-token match ("what") that routed a Masdar question
# to Azure Expert instead of triggering the "nobody here matches, try X"
# suggestion. Merged in a standard, compact English stopword set --
# removing more non-domain noise can only reduce false positives here,
# never a genuine domain-term match.
_OVERLAP_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "its", "it", "own", "real", "expert", "experts", "specialist",
    "customer", "kind", "partner", "engagement", "type", "that", "this",
    "agent", "agents",
    # Standard English function/question words -- generic noise wherever
    # they show up (a profile's own prose, or a user's own question).
    "what", "when", "where", "who", "whom", "which", "why", "how",
    "these", "those", "there", "here", "am", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "doing", "will",
    "would", "shall", "should", "can", "could", "may", "might", "must",
    "about", "above", "after", "again", "against", "all", "any", "as",
    "at", "because", "before", "below", "between", "both", "but", "by",
    "down", "during", "each", "few", "from", "further", "he", "her",
    "hers", "him", "his", "i", "if", "into", "just", "me", "more", "most",
    "my", "no", "nor", "not", "now", "off", "once", "only", "other",
    "our", "out", "over", "same", "she", "so", "some", "such", "than",
    "then", "them", "they", "up", "us", "very", "we", "you", "your",
    "day", "days", "today", "currently", "current", "please", "know",
})

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return {
        token for token in _TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in _OVERLAP_STOPWORDS
    }


def _plugin_matches(subject_kind: str, subject_note_stem: str) -> list[dict] | None:
    """What installed plugins' agent matchers say about this subject (`BUG-063`
    seam), or None when no plugin registered a matcher. A matcher that raises
    or answers something other than a dict is skipped, like a failing
    subject enricher."""
    matchers = PluginManager().get_agent_matchers()
    if not matchers:
        return None
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        return []
    subject = {"stem": entry["stem"], "frontmatter": dict(entry["frontmatter"]), "tags": list(entry["tags"])}
    matches = []
    for matcher in matchers:
        try:
            match = matcher(subject_kind, subject)
        except Exception:
            continue
        if isinstance(match, dict):
            matches.append(match)
    return matches


def recommended_experts(subject_kind: str, subject_note_stem: str) -> list[str]:
    """The agents plugins recommend for a conversation about this subject, in
    plugin order, limited to agents that are really registered. None without
    a plugin matcher: the framework itself knows no business concept to match
    a subject by (`BUG-063`)."""
    matches = _plugin_matches(subject_kind, subject_note_stem)
    if matches is None:
        return []
    registered = {agent.id for agent in _agent_manager.get_expert_agents()}
    experts = [
        agent_id for match in matches for agent_id in (match.get("experts") or [])
        if isinstance(agent_id, str) and agent_id in registered
    ]
    return list(dict.fromkeys(experts))


def fallback_agent(subject_kind: str, subject_note_stem: str) -> str | None:
    """Who answers when nobody brought in fits: the first registered agent a
    plugin names, or None -- including when no plugin matcher is installed."""
    matches = _plugin_matches(subject_kind, subject_note_stem)
    if matches is None:
        return None
    registered = {agent.id for agent in _agent_manager.get_all()}
    for match in matches:
        agent_id = match.get("fallback_agent_id")
        if isinstance(agent_id, str) and agent_id in registered:
            return agent_id
    return None


def route_question(question_text: str, candidate_agent_ids: list[str]) -> dict:
    """Live per-question routing (REQ-SB-82-US-04) -- reuses this same
    deterministic tokenized-overlap scoring `match_domain_experts` already
    uses for roster recommendation (ADR-009's own "lightweight... refine
    later if too coarse" resolution), scored against the QUESTION's own
    text instead of the subject note, and scoped to ONLY
    `candidate_agent_ids` (the currently brought-in roster) instead of
    every registered Expert -- Scenario 1's "not broadcast to everyone
    I've brought in" is enforced by construction: at most one agent_id
    ever comes back.

    Returns {"agent_id": <the one highest-scoring candidate> | None,
    "tied": bool}. `agent_id` is None either when nothing overlaps
    (`tied=False`) or when 2+ candidates share the single highest nonzero
    score (`tied=True`, operator-confirmed tie-break: never guess between
    them, fall back to the Research Agent same as a genuine no-match)."""
    question_tokens = _tokenize(question_text)
    if not question_tokens or not candidate_agent_ids:
        return {"agent_id": None, "tied": False}

    candidates = {summary["id"]: summary for summary in agents_map_adapter.list_agent_summaries()}
    scores: dict[str, int] = {}
    for agent_id in candidate_agent_ids:
        summary = candidates.get(agent_id)
        if summary is None:
            continue
        agent_tokens = _tokenize(f"{summary['name']} {summary['description'] or ''}")
        overlap = len(question_tokens & agent_tokens)
        if overlap:
            scores[agent_id] = overlap

    if not scores:
        return {"agent_id": None, "tied": False}
    best_score = max(scores.values())
    winners = [agent_id for agent_id, score in scores.items() if score == best_score]
    if len(winners) > 1:
        return {"agent_id": None, "tied": True}
    return {"agent_id": winners[0], "tied": False}


def suggest_expert_for_question(question_text: str, exclude_agent_ids: list[str]) -> str | None:
    """The real gap `route_question` alone can't see: a question that
    matches NO brought-in Expert isn't automatically a job for the
    Research Agent -- it might just mean the RIGHT Expert isn't in the
    room yet (operator, 2026-08-26, live: asked about Masdar with no
    Masdar-relevant Expert brought in -- "The Research Agent Jumped in and
    Start Searching the web this is a wrong Behaviour... we can invite
    Masdar Expert he knows more about it or I can go do a quick Search").
    Same tokenized-overlap scoring as `route_question`/`match_domain_experts`,
    but scanning every REGISTERED Expert (not just the brought-in roster)
    against the QUESTION's own text -- returns the single highest-scoring
    real match not already in `exclude_agent_ids`, or None when nothing
    genuinely overlaps (a real internal gap, not a guess -- the caller
    falls back to the Research Agent only in that honest-empty case)."""
    question_tokens = _tokenize(question_text)
    if not question_tokens:
        return None
    best_agent_id = None
    best_score = 0
    for agent in _agent_manager.get_expert_agents():
        if agent.id in exclude_agent_ids:
            continue
        agent_tokens = _tokenize(f"{agent.name} {agent.description or ''}")
        overlap = len(question_tokens & agent_tokens)
        if overlap > best_score:
            best_score = overlap
            best_agent_id = agent.id
    return best_agent_id


def match_domain_experts(subject_note_stem: str) -> list[str]:
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        return []
    subject_tokens = _tokenize(entry["stem"])
    for tag in entry["tags"]:
        subject_tokens |= _tokenize(tag.replace("/", " "))
    if not subject_tokens:
        return []
    matched_agent_ids: list[str] = []
    for agent in _agent_manager.get_expert_agents():
        agent_tokens = _tokenize(f"{agent.name} {agent.description or ''}")
        if subject_tokens & agent_tokens:
            matched_agent_ids.append(agent.id)
    return matched_agent_ids


def _format_recent_messages(recent_messages: list[dict]) -> str:
    lines = [
        f"{message.get('agent_name') or message.get('speaker') or 'unknown'}: {message.get('text', '')}"
        for message in recent_messages
    ]
    return "\n".join(lines) if lines else "(no prior messages in this thread yet)"


def _build_routing_prompt(
    question_text: str,
    candidates: list[dict],
    recent_messages: list[dict],
    reply_to_text: str | None,
) -> list[dict[str, str]]:
    """Builds the OpenAI-compatible `messages` payload for the LLM-based
    routing pass (`ADR-012` point 2) -- the brought-in roster's own real
    `name`/`description`, the thread's own recent history, and the new
    question, with an optional reply-to hint folded in as ONE MORE prompt
    input alongside everything else, never a separate branch that could
    short-circuit the reasoning (`ADR-012` point 4, Scenario 5's own
    "moderator retains final say")."""
    roster_block = "\n".join(
        f'- id="{candidate["id"]}" name="{candidate["name"]}" '
        f'description="{candidate.get("description") or ""}"'
        for candidate in candidates
    )
    history_block = _format_recent_messages(recent_messages)
    reply_to_block = (
        f'\nThe new message is a reply to this earlier message: "{reply_to_text}"\n'
        if reply_to_text else ""
    )
    system_content = (
        "You are the moderator of a multi-Expert chat thread. Below is the "
        "roster of Experts currently brought into this conversation. Given "
        "the recent conversation history and the user's new message, decide "
        "which ONE Expert from the roster should answer -- reason genuinely "
        "about which Expert's own domain (per their name/description) the "
        "new message actually belongs to; never guess or default to the "
        "first Expert listed.\n\n"
        f"Roster:\n{roster_block}\n\n"
        "Respond with EXACTLY the chosen Expert's id from the roster above, "
        "on its own line, and nothing else. If none of the roster's Experts "
        "genuinely fit the new message, respond with exactly: NONE"
    )
    user_content = (
        f"Recent conversation:\n{history_block}\n"
        f"{reply_to_block}"
        f"\nNew message: {question_text}"
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _parse_routing_reply(reply_text: str, candidates: list[dict]) -> str | None:
    """Extracts exactly one candidate id from the model's raw reply text, or
    `None` when the reply names no candidate id, an id outside
    `candidates`, or can't be parsed at all -- never a fabricated/guessed id
    (this function's own Constraint, `route_question_llm`'s "never returns
    an id outside the given candidates list")."""
    matched_ids = {
        candidate["id"] for candidate in candidates
        if re.search(r"\b" + re.escape(candidate["id"]) + r"\b", reply_text)
    }
    if len(matched_ids) == 1:
        return matched_ids.pop()
    return None


def route_question_llm(
    question_text: str,
    candidates: list[dict],
    recent_messages: list[dict],
    reply_to_text: str | None = None,
) -> str | None:
    """The LLM-based routing track (`ADR-012` point 2) -- reasons over the
    brought-in roster's own real `name`/`description`, the thread's own
    recent history, the new message's own text, and an optional reply-to
    hint (one more prompt input, never a separate override branch --
    `ADR-012` point 4) via `compass_client`, deciding which ONE brought-in
    Expert should answer. `candidates` is `[{"id": ..., "name": ...,
    "description": ...}, ...]` (the brought-in roster, same shape
    `agents_map_adapter.list_agent_summaries()` already returns per entry);
    `recent_messages` is the thread's own recent `messages` list
    (speaker/agent_name/text). Returns exactly one of the given
    `candidates`' own ids, or `None` when the model finds no good match or
    its reply can't be parsed into one of the given ids -- never a
    fabricated id outside `candidates`.

    Raises `CompassClientError` on any real Compass call failure --
    deliberately NOT caught here; the degrade decision (falling back to the
    existing deterministic `route_question`) belongs to the caller
    (`chat_turn.py`, `ADR-012` point 3), not this function."""
    if not candidates:
        return None
    prompt_messages = _build_routing_prompt(question_text, candidates, recent_messages, reply_to_text)
    reply_text = compass_client.request_chat_completion(prompt_messages)
    return _parse_routing_reply(reply_text, candidates)
