"""A chat turn is saved by the backend, not by the page that asked for
it (operator, 2026-10-24: "if before the response arrives I move to a
new chat").

The failure this closes, traced through the real code: `ChatPage` keys
`AgentChatPanel` by conversation id, and the panel saves a thread only
in an effect gated on `!sending`. Switching conversations re-keys the
panel, the old one unmounts while the reply is still streaming,
`sending` never flips false in a live component, and the turn is
written by nobody -- losing the reply AND the question, while Hermes
has both.

So the backend writes it when the reply lands. These tests pin the two
things that make that safe: it must not double a turn the page also
saved, and it must not mistake a genuine repeat for a double.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.business.core.chats.chat_manager import ChatManager


@pytest.fixture(autouse=True)
def chats_are_this_tests_own(tmp_path, monkeypatch):
    """The real manager over a store in `tmp_path`, so what is asserted
    is what the shipped code really wrote -- and nothing here touches
    the operator's own conversations."""
    monkeypatch.setattr(
        "app.data_access.chat_conversations.chats_dir", lambda: tmp_path / "Chats",
    )
    return tmp_path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _a_moment_ago() -> str:
    """A turn-start earlier than anything this test writes afterwards."""
    return (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()


def a_conversation() -> str:
    return ChatManager().create().id


def messages_in(conversation_id: str) -> list[dict]:
    record = ChatManager().get(conversation_id)
    return list((record or {}).get("messages") or [])


def test_a_turn_is_saved_when_nobody_was_watching() -> None:
    """[REQ-SB-102] The whole point: the page has gone and the turn is
    still recorded, question and answer both."""
    conversation = a_conversation()

    ChatManager().append_turn(conversation, "Whats the updates on Adnoc", "Here is the latest.")

    assert messages_in(conversation) == [
        {"role": "user", "text": "Whats the updates on Adnoc"},
        {"role": "agent", "text": "Here is the latest."},
    ]


def test_a_turn_the_page_already_saved_is_not_doubled() -> None:
    """[REQ-SB-102] A mounted page saves the same turn when the stream
    completes. Whichever write lands second must leave one copy.

    Told apart from a genuine repeat by WHEN, not by content: the
    page's save happened after this turn began."""
    conversation = a_conversation()
    began = _a_moment_ago()
    ChatManager().replace_messages(conversation, [
        {"role": "user", "text": "ping"},
        {"role": "agent", "text": "pong"},
    ])

    ChatManager().append_turn(conversation, "ping", "pong", began)

    assert messages_in(conversation) == [
        {"role": "user", "text": "ping"},
        {"role": "agent", "text": "pong"},
    ]


def test_asking_the_same_thing_twice_really_is_two_turns() -> None:
    """[REQ-SB-102] The de-duplication matches the whole exchange, not
    the reply alone. Asking "ping" twice and getting "pong" twice is
    ordinary, and a check that only compared the answer would throw the
    second turn away as a duplicate of the first."""
    conversation = a_conversation()
    ChatManager().append_turn(conversation, "ping", "pong", _a_moment_ago())

    # A SECOND turn, which began after the first was written.
    ChatManager().append_turn(conversation, "ping", "pong", _now_iso())

    assert len(messages_in(conversation)) == 4, (
        "the second genuine exchange was dropped as a false duplicate"
    )


def test_a_turn_appends_after_whatever_the_page_saved_meanwhile() -> None:
    """[REQ-SB-102] The record is re-read immediately before writing.
    A replace built from a copy taken before the page's own save is how
    the other half of a conversation disappears."""
    conversation = a_conversation()
    manager = ChatManager()
    manager.replace_messages(conversation, [
        {"role": "user", "text": "earlier question"},
        {"role": "agent", "text": "earlier answer"},
    ])

    manager.append_turn(conversation, "later question", "later answer")

    assert [message["text"] for message in messages_in(conversation)] == [
        "earlier question", "earlier answer", "later question", "later answer",
    ]


def test_a_conversation_deleted_mid_reply_is_not_resurrected() -> None:
    """[REQ-SB-102] Deleting a chat while its reply is in flight is a
    real race. Recreating it here would bring back something the
    operator deliberately removed, so the turn is dropped and the
    caller is told by a `None`."""
    conversation = a_conversation()
    ChatManager().delete(conversation)

    assert ChatManager().append_turn(conversation, "q", "a") is None
    assert ChatManager().get(conversation) is None
