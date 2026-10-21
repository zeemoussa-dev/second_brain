"""One Hermes session, read as a conversation rather than as rows
(`REQ-SB-100`; operator 2026-10-21: "Build the Bridge of the missing
Pieces from Hermes into Second Brain … for Reaching Second Brain will
have a way better reading as it turns Text info into Business Context").

**What this adds over calling Hermes directly.** Hermes returns a flat
list of messages with 23 fields each, several of them empty most of the
time. The operator's question is never "what is in field 14" -- it is
*what did it decide, what did it actually do, and where did it go
wrong*. So each turn is reduced to what answers that: who spoke, what
they said, what the model was thinking, which tools it called with which
arguments, and what each tool answered.

**Nothing is summarised and nothing is dropped silently.** The raw
message stays reachable; this is a reading, not a replacement. A field
this module does not understand is left out of the reading, and the
count of what it skipped is reported -- an operator debugging a confused
ask must be able to tell "there was nothing else" from "there was
something else and it was not shown".

**A tool call is the unit that matters.** It is the only place a session
touches the world: reading the vault, calling an Action, sending mail.
Everything else is the agent talking. So a tool call is lifted out of
the message it rode in on and given its own entry, paired with the
`tool` message that answered it -- which Hermes stores as a SEPARATE
message joined by `tool_call_id`, and which is therefore unreadable in
the raw list without doing this join by eye.

**Privacy, stated rather than assumed.** These transcripts contain
whatever the agent read: real mail, real names, real customers. The PRD
flagged putting them on a screen as a deliberate decision because it
makes them easier to export by accident. The operator took that decision
on 2026-10-21 -- bring it into Second Brain. This module therefore does
not redact, and that is a choice, not an oversight.
"""
from __future__ import annotations

import json
from typing import Any

# Kept verbatim on every turn. Everything else in a Hermes message row is
# either empty in practice, an internal id, or a duplicate of one of
# these in another encoding.
_INTERESTING = (
    "id", "role", "content", "tool_call_id", "tool_calls", "tool_name",
    "timestamp", "token_count", "finish_reason", "reasoning",
    "reasoning_content", "effect_disposition",
)


def _reasoning_of(message: dict) -> str | None:
    """The model's own account of why, when it recorded one. Hermes has
    three fields for this and they are not interchangeable: `reasoning`
    and `reasoning_content` are text, `reasoning_details` is structured.
    First non-empty text wins; the structured one is left to the raw
    message rather than flattened into prose it is not."""
    for field in ("reasoning_content", "reasoning"):
        value = message.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _tool_calls_of(message: dict) -> list[dict]:
    """Hermes stores `tool_calls` as a list of provider-shaped dicts, or
    as a JSON string when the provider sent one. Both are real and both
    are seen; a string that does not parse is reported as an unreadable
    call rather than dropped, because a tool call nobody can see is the
    exact thing this view exists to surface."""
    raw = message.get("tool_calls")
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return [{"name": None, "arguments": None, "unreadable": raw[:2000]}]
    if isinstance(raw, dict):
        raw = [raw]
    calls = []
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        function = entry.get("function") if isinstance(entry.get("function"), dict) else {}
        arguments = function.get("arguments", entry.get("arguments"))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (ValueError, TypeError):
                pass  # Left as the string it is; a half-parsed argument is worse.
        calls.append({
            "id": entry.get("id") or entry.get("tool_call_id"),
            "name": function.get("name") or entry.get("name") or entry.get("tool_name"),
            "arguments": arguments,
        })
    return calls


def read_transcript(messages: list[dict]) -> dict:
    """Turns Hermes' message rows into turns an operator can read.

    The answer to a tool call arrives as its own `tool` message, joined
    by `tool_call_id`. Those are folded into the call they answer, so a
    reader sees "it called X with these inputs and got this back" as one
    thing instead of two messages apart.
    """
    answers: dict[str, dict] = {}
    for message in messages:
        if message.get("role") == "tool" and message.get("tool_call_id"):
            answers[str(message["tool_call_id"])] = message

    turns: list[dict] = []
    folded = 0
    for message in messages:
        role = message.get("role")
        if role == "tool" and str(message.get("tool_call_id") or "") in answers:
            folded += 1
            continue  # Shown inside the call it answers.

        calls = []
        for call in _tool_calls_of(message):
            answer = answers.get(str(call.get("id") or ""))
            calls.append({
                **call,
                "answered": answer is not None,
                "answer": (answer or {}).get("content"),
                "answered_by_tool": (answer or {}).get("tool_name"),
            })

        turns.append({
            "id": message.get("id"),
            "role": role,
            "said": message.get("content"),
            "thinking": _reasoning_of(message),
            "tool_calls": calls,
            "at": message.get("timestamp"),
            "tokens": message.get("token_count"),
            "finish_reason": message.get("finish_reason"),
            "effect_disposition": message.get("effect_disposition"),
            # The row as Hermes gave it, minus fields that are always
            # empty here. The reading is never the only thing on offer.
            "raw": {k: v for k, v in message.items() if k in _INTERESTING},
        })

    return {
        "turns": turns,
        "what_happened": summarise(turns),
        # Honest arithmetic, so "that is all of it" is checkable rather
        # than trusted.
        "counts": {
            "messages_in": len(messages),
            "turns_out": len(turns),
            "tool_answers_folded_in": folded,
        },
    }


def summarise(turns: list[dict]) -> dict:
    """The shape of the session at a glance: who spoke how often, and
    every tool it reached for, in order. This is the part that answers
    "how did it route" -- the sequence of tools IS the route taken."""
    by_role: dict[str, int] = {}
    tools_in_order: list[str] = []
    unanswered = 0
    for turn in turns:
        role = turn.get("role") or "unknown"
        by_role[role] = by_role.get(role, 0) + 1
        for call in turn["tool_calls"]:
            tools_in_order.append(call.get("name") or "(unnamed tool)")
            if not call.get("answered"):
                unanswered += 1
    return {
        "turns_by_role": by_role,
        "tools_in_order": tools_in_order,
        "distinct_tools": sorted({name for name in tools_in_order}),
        # A call with no answer is a dead end, and a dead end is usually
        # where a confused ask went wrong.
        "tool_calls_without_an_answer": unanswered,
    }


def read_session_transcript(rest: Any, session_id: str, limit: int = 200, offset: int = 0) -> dict:
    """The whole view: the session's own header, plus the read
    transcript. Two Hermes calls, because the header is what tells the
    operator which agent and which chat they are looking at, and a
    transcript with no idea whose it is answers half the question."""
    session = rest.get_session(session_id)
    payload = rest.get_session_messages(session_id, limit=limit, offset=offset)
    messages = payload.get("messages") if isinstance(payload, dict) else payload
    reading = read_transcript(list(messages or []))
    return {
        "session_id": session_id,
        "session": session,
        "pagination": (payload or {}).get("pagination") if isinstance(payload, dict) else None,
        **reading,
    }
