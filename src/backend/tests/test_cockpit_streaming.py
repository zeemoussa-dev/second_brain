"""The Cockpit turn streams: routing first, then the reply as it is written.

Operator, 2026-09-24: "The Cockpit Gets Stuck at Sending Now Streaming like the rest
of the System". Routing asks the LLM moderator who should answer, and that ran inside
the POST, so the composer sat on "Sending…" for a whole model round-trip; the reply
then arrived in one lump via 5-second polling.

The agent turn itself is stubbed here -- these tests are about the frames the Cockpit
emits and what ends up persisted, not about Hermes."""
import asyncio
import json

import pytest

from app.business.cockpit import chat_turn


def collect(subject_kind="meeting", stem="a-meeting", text="what is the plan?"):
    """Drives the turn to completion and returns its frames, decoded. Plain
    asyncio rather than a pytest plugin: this suite has no async plugin, and one
    generator does not justify a new dependency."""
    async def run():
        frames = []
        async for frame in chat_turn.stream_user_message(subject_kind, stem, text):
            assert frame.startswith("data: ") and frame.endswith("\n\n")
            frames.append(json.loads(frame[len("data: "):]))
        return frames

    return asyncio.run(run())


@pytest.fixture()
def turn(monkeypatch):
    """A routed turn whose agent streams two chunks and completes."""
    state = {"persisted": [], "last_answering": None, "thread": {"messages": [], "brought_in_agent_ids": []}}

    async def routed(subject_kind, stem, text, reply_to_message_id=None, dispatch=True):
        assert dispatch is False, "the streaming turn must own the reply, not a background task"
        return {"thread": state["thread"], "answering": {"agent_id": "compass-expert", "agent_name": "Compass Expert"},
                "question_message_id": "q1"}

    async def stream_chat_turn(agent_id, message):
        yield 'data: {"type": "activity", "text": "searching"}\n\n'
        yield 'data: {"type": "delta", "text": "Pay as you "}\n\n'
        yield 'data: {"type": "delta", "text": "go means..."}\n\n'
        yield 'data: {"type": "complete", "text": "Pay as you go means..."}\n\n'

    monkeypatch.setattr(chat_turn, "send_user_message", routed)
    monkeypatch.setattr(chat_turn.agent_chat_stream, "stream_chat_turn", stream_chat_turn)
    monkeypatch.setattr(chat_turn, "_agent_name", lambda agent_id: "Compass Expert")
    monkeypatch.setattr(chat_turn.chat_store, "append_message",
                        lambda *a, **kw: state["persisted"].append(kw) or {"id": "r1"})
    monkeypatch.setattr(chat_turn.chat_store, "set_last_answering_agent",
                        lambda *a, **kw: state.__setitem__("last_answering", a[2]))
    monkeypatch.setattr(chat_turn.chat_store, "get_thread", lambda *a, **kw: state["thread"])
    return state


def test_routing_is_announced_before_any_model_call(turn):
    frames = collect()

    assert frames[0] == {"type": "routing"}
    assert frames[1]["type"] == "answering"
    assert frames[1]["answering"]["agent_name"] == "Compass Expert"


def test_the_reply_is_forwarded_as_it_is_written(turn):
    kinds = [frame["type"] for frame in collect()]

    assert kinds == ["routing", "answering", "activity", "delta", "delta", "complete", "done"]


def test_the_finished_reply_is_persisted_once_onto_the_question(turn):
    collect()

    assert len(turn["persisted"]) == 1
    persisted = turn["persisted"][0]
    assert persisted["text"] == "Pay as you go means..."
    assert persisted["agent_id"] == "compass-expert"
    assert persisted["reply_to_message_id"] == "q1"
    assert turn["last_answering"] == "compass-expert"


def test_a_turn_nobody_can_answer_still_ends_cleanly(monkeypatch):
    """Scenario 6: no Experts in the room and no fallback. The thread already
    carries the system message saying so, and no reply is invented."""
    thread = {"messages": [], "brought_in_agent_ids": []}

    async def routed(*args, **kwargs):
        return {"thread": thread, "answering": None, "question_message_id": "q1"}

    monkeypatch.setattr(chat_turn, "send_user_message", routed)
    monkeypatch.setattr(chat_turn.chat_store, "append_message",
                        lambda *a, **kw: pytest.fail("nothing should be persisted"))

    frames = collect()

    assert [f["type"] for f in frames] == ["routing", "answering", "done"]
    assert frames[1]["answering"] is None


def test_a_failed_turn_is_recorded_as_a_real_message_not_silence(monkeypatch):
    """A stream that errors before any text must not leave the thread with an
    empty agent message -- the operator has to be able to see what happened."""
    persisted = []

    async def routed(*args, **kwargs):
        return {"thread": {"messages": []}, "answering": {"agent_id": "x", "agent_name": "X"},
                "question_message_id": "q1"}

    async def failing(agent_id, message):
        yield 'data: {"type": "error", "detail": "Hermes is not running"}\n\n'

    monkeypatch.setattr(chat_turn, "send_user_message", routed)
    monkeypatch.setattr(chat_turn.agent_chat_stream, "stream_chat_turn", failing)
    monkeypatch.setattr(chat_turn, "_agent_name", lambda agent_id: "X")
    monkeypatch.setattr(chat_turn.chat_store, "append_message", lambda *a, **kw: persisted.append(kw) or {"id": "r"})
    monkeypatch.setattr(chat_turn.chat_store, "set_last_answering_agent", lambda *a, **kw: None)
    monkeypatch.setattr(chat_turn.chat_store, "get_thread", lambda *a, **kw: {"messages": []})

    frames = collect()

    assert [f["type"] for f in frames] == ["routing", "answering", "error", "done"]
    assert "Hermes is not running" in persisted[0]["text"]
