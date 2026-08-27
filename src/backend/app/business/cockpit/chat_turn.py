"""Cockpit Chat send/route/reply orchestration (REQ-SB-82-US-04). Composes
three already-real primitives, no new session-continuity infrastructure:
`chat_store` (persistence), `moderator.route_question` (deterministic
routing, scoped to the brought-in roster), and
`chat_sessions.send_and_await_reply` (the same persistent-per-agent
Hermes turn `agents_router.py`'s own single-agent Chat tab already uses,
factored out there for this exact reuse).

Routing (Scenarios 1, 5), with an explicit override (operator, 2026-08-26:
"give me the Ability to Force Redirection to Agent if the one Answering is
the wrong one with @"):
- A leading `@mention` in the message text always wins over the
  deterministic routing score -- an explicit human correction outranks a
  heuristic guess. Matched against every real registered agent (not just
  the brought-in roster), same as mentioning someone new in any chat app;
  mentioning an agent not already in the room brings them in first (the
  same real `bring_in_agent` the roster panel itself uses).
- Otherwise: unique highest-scoring match among the brought-in roster ->
  that Expert. A genuine tie among brought-in Experts -> falls back to
  the Research Agent (Scenario 5's own "never guess between them").
- A GENUINE zero-match (nobody in the room is even plausibly relevant) is
  NOT automatically handed to the Research Agent (operator, 2026-08-26,
  live: asked about Masdar with no Masdar-relevant Expert in the room --
  "The Research Agent Jumped in and Start Searching the web this is a
  wrong Behaviour... we can invite Masdar Expert he knows more about it
  or I can go do a quick Search"). First checks whether a real,
  not-yet-brought-in registered Expert would plausibly know more
  (`moderator.suggest_expert_for_question`) -- if so, surfaces that as an
  honest system suggestion and dispatches nothing; only when NO real
  Expert (brought-in or not) looks relevant does it check for a Section-
  level fallback next, and only then the Research Agent (Scenario 2).
- Phase 5 (2026-08-27, operator: "Talking to Customers Hub will help fix
  that"): before that final Research Agent fallback, checks whether this
  conversation's own subject is a Customer with no dedicated Expert
  registered at all (`moderator.match_customer_fallback_agent`) -- if the
  Customer Section has its own configured fallback agent, that answers
  instead of the generic Research Agent. Never brought into the roster,
  same one-off-answer shape as the Research Agent fallback itself. Only
  Customer conversations carry this signal today (a Meeting/Thread's own
  `customer:`/`customer/<slug>` tag); Technology/Sales/Industry get the
  same mechanism once they have an equivalent subject-tagging convention.
  Checked in BOTH the "roster has agents but none match" case above AND
  the "no Experts brought in at all yet" case below -- a brand-new
  conversation about a Customer with no dedicated Expert is the exact
  motivating case (operator: "only a few that are Important"), so the
  fallback must not require bringing someone in first.
- No Experts brought in at all, and no @mention, and no Section fallback
  configured for this subject either (Scenario 6) -> an honest system
  message; never a fabricated reply, never a silent no-op.

Every reply -- a routed Expert or the Research Agent fallback -- is now
dispatched as a background asyncio task (operator, 2026-08-26: "The
Message Don't get added to the chat until Something happen so it sticks
on Sending for a while... show me what's happening (Expert x is
typing..)"). `send_user_message` returns as soon as the ROUTING decision
is made, never waiting on the real Hermes turn itself, so the caller can
persist+render the user's own message and an "X is typing..." indicator
immediately instead of blocking the whole Send action on a slow LLM turn.
The reply lands later via the same `reply_to_message_id` threading
mechanism (Scenario 4) the caller already polls for.
"""
from __future__ import annotations

import asyncio
import re

from app.business.cockpit import chat_store, moderator
from app.business.hermes import agents_map_adapter, chat_sessions
from app.business.hermes.client import HermesUnavailableError

# The real Hermes profile REQ-SB-82-US-02 registered under the Librarian
# Section as this app's one designated research fallback -- same kind of
# real, structural (not user-tunable) identifier as moderator.py's own
# _CUSTOMER_SECTION_ID / section_registry.py's _STARTING_SECTION_NAMES.
_RESEARCH_AGENT_ID = "research-agent"

# A leading @mention only -- mirrors ordinary chat-mention UX and avoids
# mis-firing on an unrelated "@" mid-sentence (e.g. a pasted email).
_MENTION_RE = re.compile(r"^@([\w.-]+)\s*")


def _agent_name(agent_id: str) -> str:
    detail = agents_map_adapter.get_agent_detail(agent_id)
    return detail["name"] if detail else agent_id


def _mention_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _resolve_mention(token: str) -> str | None:
    """Matches a leading @mention against every real agent's id or display
    name -- never just the brought-in roster, so mentioning someone new
    works the same as bringing them in manually. Returns None on no
    match (never a fabricated/guessed agent), leaving normal routing to
    decide instead."""
    key = _mention_key(token)
    if not key:
        return None
    for summary in agents_map_adapter.list_agent_summaries():
        if _mention_key(summary["id"]) == key or _mention_key(summary["name"]) == key:
            return summary["id"]
    return None


async def _reply_via_agent(agent_id: str, question_text: str) -> str:
    try:
        return await chat_sessions.send_and_await_reply(agent_id, question_text)
    except HermesUnavailableError as exc:
        return f"{_agent_name(agent_id)} couldn't be reached: {exc}"
    except asyncio.TimeoutError:
        return f"{_agent_name(agent_id)} didn't reply in time."


async def _dispatch_reply(
    subject_kind: str, subject_note_stem: str, agent_id: str, question_message_id: str, question_text: str,
) -> None:
    """Fire-and-forget -- the ONE real reply path for both a routed Expert
    and the Research Agent fallback (which agent it is is the only
    difference, not the mechanism). Never awaited by the caller
    (Scenario 3: never blocks the live chat)."""
    reply_text = await _reply_via_agent(agent_id, question_text)
    chat_store.append_message(
        subject_kind, subject_note_stem, speaker="agent", text=reply_text,
        agent_id=agent_id, agent_name=_agent_name(agent_id),
        reply_to_message_id=question_message_id,
    )


async def send_user_message(subject_kind: str, subject_note_stem: str, text: str) -> dict:
    """Appends the user's turn, decides who answers, and dispatches that
    reply in the BACKGROUND -- returns almost immediately with
    {"thread": <persisted thread>, "answering": {"agent_id", "agent_name"}
    | None} so the caller can show "X is typing..." without waiting on the
    real Hermes turn. `answering` is None only for the honest no-Experts-
    brought-in case (Scenario 6), which needs no reply dispatch at all."""
    thread = chat_store.get_thread(subject_kind, subject_note_stem)
    user_message = chat_store.append_message(subject_kind, subject_note_stem, speaker="user", text=text)

    mention_match = _MENTION_RE.match(text)
    mentioned_agent_id = _resolve_mention(mention_match.group(1)) if mention_match else None

    brought_in_agent_ids = list(thread["brought_in_agent_ids"])
    if mentioned_agent_id:
        if mentioned_agent_id not in brought_in_agent_ids:
            chat_store.bring_in_agent(subject_kind, subject_note_stem, mentioned_agent_id)
        agent_id = mentioned_agent_id
    elif brought_in_agent_ids:
        route = moderator.route_question(text, brought_in_agent_ids)
        if route["agent_id"]:
            agent_id = route["agent_id"]
        elif not route["tied"]:
            # Genuinely nobody in the room matched (not just an ambiguous
            # tie among brought-in Experts) -- operator, 2026-08-26: "The
            # Research Agent Jumped in and Start Searching the web this is
            # a wrong Behaviour... we can invite Masdar Expert he knows
            # more about it or I can go do a quick Search." Web research
            # is a real fallback, never the FIRST guess when a real,
            # not-yet-brought-in Expert would plausibly know more.
            suggested_agent_id = moderator.suggest_expert_for_question(text, exclude_agent_ids=brought_in_agent_ids)
            if suggested_agent_id:
                chat_store.append_message(
                    subject_kind, subject_note_stem, speaker="system",
                    text=(
                        f"No one currently in this chat looks like a strong match for that. "
                        f"{_agent_name(suggested_agent_id)} (@{suggested_agent_id}) might know more — "
                        f"bring them in from the panel and ask again, or start your message with "
                        f"@{_RESEARCH_AGENT_ID} to search the web instead."
                    ),
                    reply_to_message_id=user_message["id"],
                )
                return {"thread": chat_store.get_thread(subject_kind, subject_note_stem), "answering": None}
            # Phase 5 (Implementation/Plans/2026-08-27-vault-index-and-
            # section-agents.md, operator: "Talking to Customers Hub will
            # help fix that") -- before giving up to the generic Research
            # Agent, check whether this conversation's own subject is a
            # Customer with NO dedicated Expert, and whether the Customer
            # Section has its own configured fallback agent. Never brought
            # into the roster (mirrors _RESEARCH_AGENT_ID's own existing
            # one-off-answer behavior below, not a permanent join).
            agent_id = moderator.match_customer_fallback_agent(subject_note_stem) or _RESEARCH_AGENT_ID
        else:
            agent_id = _RESEARCH_AGENT_ID
    else:
        # Phase 5: a brand-new conversation (nobody brought in yet) about a
        # Customer with no dedicated Expert is EXACTLY the operator's own
        # motivating case ("only a few that are Important") -- the honest
        # "bring in an Expert" message below is unhelpful here since there
        # is no dedicated Expert TO bring in. Same fallback check as the
        # non-empty-roster branch above, just reached from a different
        # starting state.
        fallback_agent_id = moderator.match_customer_fallback_agent(subject_note_stem)
        if fallback_agent_id:
            agent_id = fallback_agent_id
        else:
            chat_store.append_message(
                subject_kind, subject_note_stem, speaker="system",
                text="Bring in an Expert before asking a question — use the panel on the right, or @mention one.",
                reply_to_message_id=user_message["id"],
            )
            return {"thread": chat_store.get_thread(subject_kind, subject_note_stem), "answering": None}

    asyncio.create_task(
        _dispatch_reply(subject_kind, subject_note_stem, agent_id, user_message["id"], text)
    )
    return {
        "thread": chat_store.get_thread(subject_kind, subject_note_stem),
        "answering": {"agent_id": agent_id, "agent_name": _agent_name(agent_id)},
    }
