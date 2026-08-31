"""Cockpit Chat send/route/reply orchestration (REQ-SB-82-US-04). Composes
already-real primitives, no new session-continuity infrastructure:
`chat_store` (persistence), `moderator.route_question_llm` (PRIMARY
routing, `moderator.route_question`'s deterministic tokenized-overlap
scoring demoted to the explicit degrade path -- REQ-SB-82-US-06-T05,
ADR-012 points 2-3), and `chat_sessions.send_and_await_reply` (the same
persistent-per-agent Hermes turn `agents_router.py`'s own single-agent
Chat tab already uses, factored out there for this exact reuse). Both are
still scoped to the brought-in roster only, same as before this task.

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

Short-reply shortcut (ADR-012 point 1, Scenario 1/Scenario 7,
REQ-SB-82-US-06-T04): a short, low-signal acknowledgment
(`_is_short_low_signal_reply`) is checked BEFORE the `@mention`/moderator
logic below -- when it fires AND `chat_store`'s
`last_answering_agent_id` is already set for this subject, the message
routes straight to that agent with no `moderator.route_question`/LLM
call made at all. Falls through to the existing routing logic unchanged
whenever the shortcut doesn't fire (not low-signal) or there is no prior
answering agent yet (a brand-new thread, Scenario 7). `_dispatch_reply`
persists whoever actually answers via
`chat_store.set_last_answering_agent` on every real dispatch -- Expert,
Research Agent, or Customer-Section fallback alike -- so this shortcut
always has real, current data to read.

LLM-primary routing + reply-to hint (ADR-012 points 2-4,
REQ-SB-82-US-06-T05): once execution reaches "no mention, not a
shortcut, at least one Expert brought in," `moderator.route_question_llm`
is now the PRIMARY routing decision -- the deterministic
`moderator.route_question` moves to being the explicit degrade path,
called ONLY inside the `except compass_client.CompassClientError` branch,
never re-raising and never leaving the user without a routing outcome
(Scenario 6). An optional `reply_to_message_id` on `send_user_message`
resolves against the thread's own CURRENT messages (a stale/unresolvable
id is silently treated as absent, Scenario 8) into `reply_to_text`, fed
into `route_question_llm`'s own prompt as ONE MORE input -- never a
separate branch that could short-circuit routing to whoever sent the
replied-to message (Scenario 5); the deterministic degrade path has no
concept of it and runs exactly as it always has.
"""
from __future__ import annotations

import asyncio
import re
import string

from app.business.cockpit import chat_store, moderator
from app.business.hermes import agents_map_adapter, chat_sessions
from app.business.hermes.client import HermesUnavailableError
from app.data_access import compass_client

# The real Hermes profile REQ-SB-82-US-02 registered under the Librarian
# Section as this app's one designated research fallback -- same kind of
# real, structural (not user-tunable) identifier as moderator.py's own
# _CUSTOMER_SECTION_ID / section_registry.py's _STARTING_SECTION_NAMES.
_RESEARCH_AGENT_ID = "research-agent"

# A leading @mention only -- mirrors ordinary chat-mention UX and avoids
# mis-firing on an unrelated "@" mid-sentence (e.g. a pasted email).
_MENTION_RE = re.compile(r"^@([\w.-]+)\s*")

# Decomposer-authored, pre-authorized detection vocabulary (story's own
# "Decomposer-authored scope-internal judgement calls" section) -- a fixed
# set of low-signal acknowledgments, matched lowercased with trailing
# punctuation stripped.
_SHORT_REPLY_ACKNOWLEDGMENTS = {
    "yes", "y", "yep", "yeah", "ya", "no", "nope", "nah", "ok", "okay", "k", "kk",
    "sure", "fine", "alright", "go ahead", "go on", "please do", "do it",
    "sounds good", "got it", "noted", "understood", "thanks", "thank you",
    "thx", "ty", "will do", "on it", "ack", "roger", "cool", "great", "perfect",
}

# A reasonable bounded window fed into the LLM moderator's own prompt
# (`moderator._format_recent_messages`) -- enough real conversation
# context to reason over without an unbounded prompt as a thread grows.
_RECENT_MESSAGES_WINDOW = 10


def _is_short_low_signal_reply(text: str) -> bool:
    """Decomposer-authored detection rule, implemented exactly as decided
    (not re-derived): trimmed text that does NOT end in '?' (a trailing
    question mark is always treated as substantive) AND EITHER its
    lowercased, trailing-punctuation-stripped form exactly matches the
    fixed acknowledgment vocabulary above, OR its stripped length is
    <= 3 characters (catches a novel ultra-short ack like "np" without
    the question-mark exclusion letting a genuinely short real question
    like "Why?"/"Cost?" slip through the vocabulary gap)."""
    trimmed = text.strip()
    if not trimmed or trimmed.endswith("?"):
        return False
    stripped = trimmed.rstrip(string.punctuation).strip()
    if not stripped:
        return False
    if stripped.lower() in _SHORT_REPLY_ACKNOWLEDGMENTS:
        return True
    return len(stripped) <= 3


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


def _resolve_reply_to_text(thread: dict, reply_to_message_id: str | None) -> str | None:
    """Resolves an optional `reply_to_message_id` against the thread's own
    CURRENT `messages` (looked up before the user's new message is
    appended) into that message's own real `text` -- a stale/unresolvable
    id (Scenario 8) is silently treated as absent, never an error, never a
    special-cased branch."""
    if not reply_to_message_id:
        return None
    for message in thread["messages"]:
        if message.get("id") == reply_to_message_id:
            return message.get("text")
    return None


def _resolve_no_match_agent_id(
    subject_kind: str, subject_note_stem: str, text: str, question_message_id: str, brought_in_agent_ids: list[str],
) -> str | None:
    """The EXISTING "genuinely nobody in the room matched" chain (Phase 5's
    own suggestion/Customer-Section-fallback/Research-Agent shape),
    factored out unchanged so both routing tracks -- the LLM moderator's
    own `None` reply and the deterministic degrade path's own
    `not route["tied"]` case -- reach the identical real behavior
    (REQ-SB-82-US-06-T05). Returns the agent id that should answer, or
    `None` when an honest "no one matches, try X" system message was
    posted instead -- the caller returns immediately in that case,
    matching the original inline shape's own early return."""
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
            reply_to_message_id=question_message_id,
        )
        return None
    return moderator.match_customer_fallback_agent(subject_note_stem) or _RESEARCH_AGENT_ID


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
    chat_store.set_last_answering_agent(subject_kind, subject_note_stem, agent_id, _agent_name(agent_id))


async def send_user_message(
    subject_kind: str, subject_note_stem: str, text: str, reply_to_message_id: str | None = None,
) -> dict:
    """Appends the user's turn, decides who answers, and dispatches that
    reply in the BACKGROUND -- returns almost immediately with
    {"thread": <persisted thread>, "answering": {"agent_id", "agent_name"}
    | None} so the caller can show "X is typing..." without waiting on the
    real Hermes turn. `answering` is None only for the honest no-Experts-
    brought-in case (Scenario 6), which needs no reply dispatch at all.

    `reply_to_message_id` (REQ-SB-82-US-06-T05, optional) is resolved
    against the CURRENT thread's own messages into real text fed into the
    LLM moderator's own prompt as a hint (Scenario 3) -- never a hard
    override (Scenario 5), and silently ignored when unresolvable
    (Scenario 8)."""
    thread = chat_store.get_thread(subject_kind, subject_note_stem)
    reply_to_text = _resolve_reply_to_text(thread, reply_to_message_id)
    user_message = chat_store.append_message(subject_kind, subject_note_stem, speaker="user", text=text)

    # Short-reply shortcut (Scenario 1) -- checked BEFORE the @mention/
    # moderator logic below, structurally guaranteeing no
    # moderator.route_question/LLM call happens for this path. An absence-
    # of-data check (Scenario 7): with no prior answering agent yet, this
    # falls straight through to the unchanged routing logic below instead.
    last_answering_agent_id = thread.get("last_answering_agent_id")
    if last_answering_agent_id and _is_short_low_signal_reply(text):
        asyncio.create_task(
            _dispatch_reply(subject_kind, subject_note_stem, last_answering_agent_id, user_message["id"], text)
        )
        return {
            "thread": chat_store.get_thread(subject_kind, subject_note_stem),
            "answering": {"agent_id": last_answering_agent_id, "agent_name": _agent_name(last_answering_agent_id)},
        }

    mention_match = _MENTION_RE.match(text)
    mentioned_agent_id = _resolve_mention(mention_match.group(1)) if mention_match else None

    brought_in_agent_ids = list(thread["brought_in_agent_ids"])
    if mentioned_agent_id:
        if mentioned_agent_id not in brought_in_agent_ids:
            chat_store.bring_in_agent(subject_kind, subject_note_stem, mentioned_agent_id)
        agent_id = mentioned_agent_id
    elif brought_in_agent_ids:
        # ADR-012 point 2 -- the LLM moderator is now the PRIMARY routing
        # decision for this branch (REQ-SB-82-US-06-T05); `route_question`
        # only runs inside the `except` below, as the explicit degrade
        # path (ADR-012 point 3, Scenario 6).
        candidates = [
            summary for summary in agents_map_adapter.list_agent_summaries()
            if summary["id"] in brought_in_agent_ids
        ]
        recent_messages = thread["messages"][-_RECENT_MESSAGES_WINDOW:]
        try:
            llm_agent_id = moderator.route_question_llm(text, candidates, recent_messages, reply_to_text)
        except compass_client.CompassClientError:
            # A real Compass call failure -- never re-raised, never leaves
            # the user without a routing outcome. Falls back to the
            # EXISTING deterministic chain exactly as it ran before this
            # task, including its own tied handling and the surrounding
            # suggestion/fallback chain.
            route = moderator.route_question(text, brought_in_agent_ids)
            if route["agent_id"]:
                agent_id = route["agent_id"]
            elif not route["tied"]:
                # Genuinely nobody in the room matched (not just an
                # ambiguous tie among brought-in Experts) -- operator,
                # 2026-08-26: "The Research Agent Jumped in and Start
                # Searching the web this is a wrong Behaviour... we can
                # invite Masdar Expert he knows more about it or I can go
                # do a quick Search." Web research is a real fallback,
                # never the FIRST guess when a real, not-yet-brought-in
                # Expert would plausibly know more.
                resolved_agent_id = _resolve_no_match_agent_id(
                    subject_kind, subject_note_stem, text, user_message["id"], brought_in_agent_ids,
                )
                if resolved_agent_id is None:
                    return {"thread": chat_store.get_thread(subject_kind, subject_note_stem), "answering": None}
                agent_id = resolved_agent_id
            else:
                agent_id = _RESEARCH_AGENT_ID
        else:
            if llm_agent_id:
                agent_id = llm_agent_id
            else:
                # The LLM moderator has no "tied" concept -- a `None`
                # reply (nobody currently brought in genuinely fits)
                # reaches the same "genuinely nobody matched" chain
                # directly, same shape as the deterministic degrade
                # path's own `not route["tied"]` case above.
                resolved_agent_id = _resolve_no_match_agent_id(
                    subject_kind, subject_note_stem, text, user_message["id"], brought_in_agent_ids,
                )
                if resolved_agent_id is None:
                    return {"thread": chat_store.get_thread(subject_kind, subject_note_stem), "answering": None}
                agent_id = resolved_agent_id
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
