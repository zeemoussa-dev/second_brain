"""Meeting Moderator roster recommendation (ADR-009, REQ-SB-82-US-03) --
two independent, purely deterministic matching tracks; no LLM call, no
Hermes profile involvement.

`match_customer_expert` -- the subject note's own real customer signal
(`customer:` frontmatter, per customer_hub_linking.py's own established
convention, OR a `customer/<slug>` tag -- confirmed live against the real
vault that a Thread/RawMessage note can carry ONLY the tag with no
`customer:` field at all, e.g. "2026-08-19 1531 Compass Access for
Masdar") mapped to a real, already-registered `<slug>-expert` agent in the
real "Customer" Section (REQ-SB-83's Masdar/Adnoc/TAQA today) -- `None`,
never fabricated, when no such agent is actually registered. Customer is
never expressed as a folder for any subject note kind this Cockpit serves
(Meeting/Thread) -- confirmed by direct inspection of
email_classification.py's own module docstring ("customer is frontmatter
+ a tag only, never a folder"); the PRD/ADR's own "tag/folder" phrasing is
read as covering the two REAL signals above, not a literal third folder
check. Logged as a scope-internal judgement call, not an escalation.

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

from app.business import section_registry, vault_indexing
from app.business.hermes import agents_map_adapter
from app.data_access import vault_writer

_CUSTOMER_SECTION_ID = vault_writer.tag_slug("Customer")

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


def _subject_customer(entry: dict) -> str | None:
    customer = entry["frontmatter"].get("customer")
    if customer:
        return str(customer)
    for tag in entry["tags"]:
        if tag.startswith("customer/"):
            return tag.split("/", 1)[1]
    return None


def match_customer_expert(subject_note_stem: str) -> str | None:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        return None
    customer = _subject_customer(entry)
    if not customer:
        return None
    candidate_agent_id = f"{vault_writer.tag_slug(customer)}-expert"
    for summary in agents_map_adapter.list_agent_summaries():
        if summary["id"] == candidate_agent_id and summary["section_id"] == _CUSTOMER_SECTION_ID:
            return candidate_agent_id
    return None


def match_customer_fallback_agent(subject_note_stem: str) -> str | None:
    """The Section-level fallback (Phase 5, Implementation/Plans/
    2026-08-27-vault-index-and-section-agents.md, operator: "Talking to
    Customers Hub will help fix that") for a customer-tagged subject with
    NO dedicated `<slug>-expert` registered -- returns the Customer
    Section's own configured `fallback_agent_id`, or `None` (never
    fabricated) when: the subject carries no customer signal at all (this
    conversation isn't about a Customer -- Fallback-only means Section
    fallback never engages for something it wasn't asked about), a
    dedicated Expert already covers this exact customer (checked via
    `match_customer_expert` first -- the dedicated Expert always wins,
    matching the operator's own "Fallback-only" call), or the Section has
    no fallback agent configured yet. Kept as its own function rather
    than folded into `match_customer_expert` since the caller
    (`chat_turn.py`) must distinguish "route to the dedicated Expert"
    from "route to the Section fallback" -- two different real agents,
    never conflated."""
    if match_customer_expert(subject_note_stem) is not None:
        return None
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None or not _subject_customer(entry):
        return None
    section = next(
        (s for s in section_registry.list_sections() if s["id"] == _CUSTOMER_SECTION_ID), None,
    )
    return (section or {}).get("fallback_agent_id") or None


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
    for summary in agents_map_adapter.list_agent_summaries():
        if summary["type"] != "expert" or summary["id"] in exclude_agent_ids:
            continue
        agent_tokens = _tokenize(f"{summary['name']} {summary['description'] or ''}")
        overlap = len(question_tokens & agent_tokens)
        if overlap > best_score:
            best_score = overlap
            best_agent_id = summary["id"]
    return best_agent_id


def match_domain_experts(subject_note_stem: str) -> list[str]:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        return []
    subject_tokens = _tokenize(entry["stem"])
    for tag in entry["tags"]:
        subject_tokens |= _tokenize(tag.replace("/", " "))
    if not subject_tokens:
        return []
    matched_agent_ids: list[str] = []
    for summary in agents_map_adapter.list_agent_summaries():
        if summary["type"] != "expert":
            continue
        agent_tokens = _tokenize(f"{summary['name']} {summary['description'] or ''}")
        if subject_tokens & agent_tokens:
            matched_agent_ids.append(summary["id"])
    return matched_agent_ids
