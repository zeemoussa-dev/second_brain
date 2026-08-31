"""Real-time SSE interpretation and orchestration for one streamed
per-agent Hermes chat turn -- moved out of agents_router.py (2026-08-28,
API layer holds no business logic): deciding which Hermes event types
are "real activity" vs noise, stripping Hermes' own kaomoji branding,
and the lock/session/error-handling orchestration around a turn are all
business rules, not HTTP concerns. The router's own job is only to
404-guard the agent id and hand the resulting async generator to a
StreamingResponse.
"""
from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator

from app.business.hermes import chat_sessions
from app.business.hermes.client import HermesUnavailableError

# Real event types seen live on a Hermes chat session besides the ones
# chat_sessions.send_and_await_reply already handles (app/hermes/
# chat_session.py's own module docstring): thinking.delta/status.update/
# reasoning.available carry the model's own in-progress "what it's
# doing" signal, distinct from the actual reply text -- session.info/
# session.title are pure metadata, not a human-readable progress
# signal, deliberately excluded here rather than surfaced as noise.
#
# tool.start/tool.complete (2026-08-30, operator: "the UI is telling
# Working I don't know WHich step its in... Agents should be Responsive
# with Which Agent it called and What's the current Status") -- these
# were ALREADY arriving on this exact socket, real and live (Hermes'
# own `tui_gateway/server.py::_on_tool_start`/`_on_tool_complete`,
# `_session_tool_progress_mode` defaults to "all", never opted out of
# here), just silently dropped. This is the real signal that shows
# agent-to-agent delegation happening: the Primary Agent relays to
# another Profile via a plain `terminal(command="hermes -p <profile>
# chat -q ...")` tool call (confirmed, MEMORY.md), so a `tool.start` for
# `terminal` carries that exact command in its own `context` field
# (Hermes' own 80-char preview, built once there -- not reimplemented
# here). Does NOT give visibility into the DELEGATE's own internal
# steps -- that one-shot CLI relay is a separate process, invisible on
# the parent's own session; this only shows that a call is in flight
# and what it is, which is what was actually missing.
_ACTIVITY_EVENT_TYPES = frozenset(
    {"thinking.delta", "status.update", "reasoning.available", "tool.start", "tool.complete"}
)

# A real status line often arrives as a Hermes-branded kaomoji plus a
# word ("(°ロ°) cogitating...", "( ˘⌣˘)♡ reasoning...", "(｡•́︿•̀｡)
# computing...") -- real Hermes personality, but operator: "fix the
# Icons added next to computing, collaborating etc it looks like it's
# not ours". Strips every leading character that isn't a plain ASCII
# letter, up to the first one -- covers the real kaomoji shapes seen
# live without hand-listing each one. Falls back to the original text
# if stripping would empty it out entirely (a real line that's ALL
# symbols, no trailing word) rather than ever showing a blank activity
# line.
_LEADING_NON_LETTER_RE = re.compile(r"^[^a-zA-Z]+")


def _strip_kaomoji_prefix(text: str) -> str:
    stripped = _LEADING_NON_LETTER_RE.sub("", text)
    return stripped if stripped else text


# The `terminal(command="hermes -p <profile> chat -q \"...\"")` real
# cross-Profile relay shape (MEMORY.md, confirmed live) -- matched
# against `args.command` (2026-08-30, Hermes' own `agent/display.py`::
# `build_tool_preview`'s `primary_args` map confirms `terminal`'s real
# arg key is `command`, FULL text, not the 80-char `context` preview,
# which could truncate mid-quote for a long delegated instruction).
# Tolerant of `--profile` as well as `-p`, and either quote style,
# since nothing pins the exact flag/quoting a future SOUL.md revision
# might use -- a non-match just falls through to the generic terminal
# phrasing below, never an error.
_DELEGATION_COMMAND_RE = re.compile(
    r"hermes\s+(?:-p|--profile)\s+(\S+)\s+chat\s+-q\s+([\"'])(.*)\2", re.DOTALL,
)

# Present/past tense pairs for the tool names actually seen live
# (2026-08-30, operator: "I don't need to show the user many technical
# stuff") -- `agent/display.py`'s own `primary_args` map is where these
# real tool names come from, not guessed. Anything not listed here
# falls back to a generic phrasing rather than silently doing nothing
# for a real tool this list hasn't caught up to yet.
_FRIENDLY_TOOL_VERBS: dict[str, tuple[str, str]] = {
    "search_files": ("Searching the vault", "Searched the vault"),
    "read_file": ("Reading a note", "Read a note"),
    "write_file": ("Writing a note", "Wrote a note"),
    "patch": ("Editing a note", "Edited a note"),
    "skill_view": ("Checking a skill", "Checked a skill"),
    "skills_list": ("Checking available skills", "Checked available skills"),
    "web_search": ("Searching the web", "Searched the web"),
    "web_extract": ("Reading a webpage", "Read a webpage"),
}


def _friendly_profile_name(profile_id: str) -> str:
    return profile_id.replace("-", " ").replace("_", " ").strip().title() or profile_id


def _friendly_task_preview(text: str, max_len: int = 70) -> str:
    """Collapses real whitespace/newlines from a long delegated
    instruction into one line, truncated for a status line, not a
    transcript."""
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= max_len else collapsed[: max_len - 1].rstrip() + "…"


def _delegation_activity_text(event_type: str, command: str) -> str | None:
    match = _DELEGATION_COMMAND_RE.search(command)
    if match is None:
        return None
    profile = _friendly_profile_name(match.group(1))
    if event_type == "tool.complete":
        return f"{profile} finished"
    task = _friendly_task_preview(match.group(3))
    return f"Asking {profile} to: {task}" if task else f"Asking {profile} for help"


def _extract_tool_activity_text(event_type: str, payload: dict) -> str | None:
    """`tool.start`/`tool.complete`'s own real payload shape (Hermes'
    `_on_tool_start`/`_on_tool_complete`, `tui_gateway/server.py`) is
    NOT the free-text `text`/`status`/`message` shape the other activity
    events use -- `name` is the real tool (e.g. "terminal"), `context`
    (start only) is Hermes' own 80-char raw command preview ("never a
    phrased label", its own docstring), `args` (both, when non-empty)
    carries the tool's own real, full arguments, `summary` (complete
    only) is a real human-readable line for a FEW tools (web_search/
    web_extract) -- None for most, including `terminal`.

    2026-08-30 (operator: "make that more user Friendly like calling
    another Agent 'Asking Opp Manager to create the opp' I don't need
    to show the user many technical stuff") -- this used to just echo
    Hermes' own raw command/tool-name text verbatim. Now: a real
    cross-Profile delegation (the ONE case the operator's own example
    named) reads as "Asking <Profile> to: <task>"/"<Profile> finished";
    a handful of other real, commonly-seen tools get a plain-English
    verb pair instead of their raw tool name; anything else still falls
    back to the previous raw-text phrasing rather than showing nothing
    for a real tool this hasn't been taught about yet."""
    name = payload.get("name") or "a tool"
    args = payload.get("args") or {}

    if name == "terminal":
        command = str(args.get("command") or payload.get("context") or "")
        delegated = _delegation_activity_text(event_type, command)
        if delegated is not None:
            return delegated
        # A real, non-delegation terminal call -- still avoid dumping
        # raw shell syntax into the user-facing trace.
        return "Running a command" if event_type == "tool.start" else "Finished running a command"

    verbs = _FRIENDLY_TOOL_VERBS.get(name)
    if event_type == "tool.start":
        if verbs:
            return verbs[0]
        context = payload.get("context")
        return f"Calling {name}: {context}" if context else f"Calling {name}"

    summary = payload.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary if verbs is None else f"{verbs[1]} ({summary})"
    if verbs:
        return verbs[1]
    duration = payload.get("duration_s")
    if isinstance(duration, (int, float)):
        return f"Finished {name} ({duration:.1f}s)"
    return f"Finished {name}"


def _extract_activity_text(event_type: str, payload: dict) -> str | None:
    if event_type in ("tool.start", "tool.complete"):
        return _extract_tool_activity_text(event_type, payload)
    for key in ("text", "status", "message", "summary"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            # Found live, 2026-08-24: a real `status.update`/`reasoning.
            # available` event can carry an unrelated internal warning
            # (e.g. "Auxiliary title generation failed: HTTP 400...") --
            # Hermes' own session-title generation misfiring, nothing to
            # do with the actual conversation. It reads exactly like a
            # real thinking step if shown, so anything starting with
            # Hermes' own "⚠" warning marker is dropped here rather than
            # surfaced as if it were genuine agent activity.
            if value.lstrip().startswith("⚠"):
                continue
            return _strip_kaomoji_prefix(value)
    return None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_reply(session) -> AsyncIterator[str]:
    """Mirrors `chat_sessions.send_and_await_reply`'s own event handling
    exactly (same event types, same clarify/approval formatting, same
    errors) but YIELDS as it goes instead of only returning the final
    text (2026-08-24, operator: "is there a way to stream the output...
    at least I will feel Agents are doing something"). Real SSE frames,
    one JSON object per line: `{"type": "activity", "text": ...}` for an
    in-progress thinking/status signal, `{"type": "delta", "text": ...}`
    per streamed reply chunk, `{"type": "complete", "text": ...}` with
    the FULL final reply once (matches message.complete's own real
    payload shape, not just the last chunk), or `{"type": "error",
    "detail": ...}`."""
    async for event in session.events():
        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "message.delta":
            yield _sse({"type": "delta", "text": payload.get("text", "")})
        elif event_type == "message.complete":
            yield _sse({"type": "complete", "text": payload.get("text", "")})
            return
        elif event_type == "turn.error":
            yield _sse({"type": "error", "detail": f"Hermes turn failed: {payload}"})
            return
        elif event_type == "clarify.request":
            yield _sse({"type": "complete", "text": chat_sessions.format_clarify_request(payload)})
            return
        elif event_type == "approval.request":
            yield _sse({"type": "complete", "text": chat_sessions.format_approval_request(payload)})
            return
        elif event_type == "connection.closed":
            yield _sse({"type": "error", "detail": "Hermes closed the connection"})
            return
        elif event_type in _ACTIVITY_EVENT_TYPES:
            text = _extract_activity_text(event_type, payload)
            if text:
                yield _sse({"type": "activity", "text": text})
    yield _sse({"type": "error", "detail": "Hermes closed the connection before replying"})


async def stream_chat_turn(agent_id: str, message: str) -> AsyncIterator[str]:
    """The full orchestration for one streamed chat turn: acquire this
    agent's own chat lock, send the prompt over a kept-alive Hermes
    session, and yield real SSE frames as the reply streams in --
    releasing the lock when done regardless of outcome. NOT used for
    agent-to-agent relays (operator: "Streaming to me Agent to Agent
    they need that mood of All message at once") -- those go through
    the completely separate `terminal(command="hermes -p ... chat -q
    ...")` one-shot CLI relay, never this path at all.

    No outer timeout around the whole stream -- a slow turn now shows
    real, visible progress (an `activity`/`delta` frame) instead of dead
    silence; the underlying `HermesChatSession._call`'s own 30s per-RPC
    timeout (app/hermes/chat_session.py) still bounds any single
    request/response leg of the turn."""
    lock = chat_sessions.get_lock(agent_id)
    await lock.acquire()
    try:
        try:
            session = await chat_sessions.get_or_create_session(agent_id)
            await session.send_prompt(message)
        except HermesUnavailableError as exc:
            await chat_sessions.discard_session(agent_id)
            yield _sse({"type": "error", "detail": str(exc)})
            return
        async for frame in _stream_reply(session):
            yield frame
    finally:
        lock.release()
