"""Multiple chats, and deleting one (operator, 2026-10-24: "Introduce Multiple
Chats, An Option to delete a Chat").

The Chat page used to hold its thread in the browser's memory: a reload lost
it, and there was only ever one. These pin what a stored conversation is.
"""
from __future__ import annotations

import pytest

from app.business.core.chats.chat_manager import UNTITLED, ChatError, ChatManager
from app.config import settings
from app.data_access import chat_conversations as chats_data


@pytest.fixture
def chats(monkeypatch, tmp_path) -> ChatManager:
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return ChatManager()


def _said(text: str) -> dict:
    return {"role": "user", "text": text, "localId": "msg-1"}


def _answered(text: str) -> dict:
    return {"role": "agent", "text": text, "localId": "msg-2"}


def test_an_install_starts_with_no_conversations(chats) -> None:
    assert chats.list() == []


def test_conversations_are_kept_apart(chats) -> None:
    """The whole point: two subjects, two threads, neither in the other."""
    first = chats.create()
    second = chats.create()

    chats.replace_messages(first.id, [_said("about the renewal")])
    chats.replace_messages(second.id, [_said("about hiring")])

    assert chats.get(first.id)["messages"][0]["text"] == "about the renewal"
    assert chats.get(second.id)["messages"][0]["text"] == "about hiring"
    assert {summary.id for summary in chats.list()} == {first.id, second.id}


def test_a_conversation_names_itself_from_the_first_thing_said(chats) -> None:
    """Asking for a title before the first message is asking someone to name a
    thing they have not had yet."""
    conversation = chats.create()
    assert conversation.title == UNTITLED

    chats.replace_messages(conversation.id, [_said("What did Masdar say about the renewal?")])

    assert chats.get(conversation.id)["title"] == "What did Masdar say about the renewal?"


def test_the_title_is_set_once_and_then_left_alone(chats) -> None:
    """A conversation that wandered elsewhere is still found under the name of
    what it started as."""
    conversation = chats.create()
    chats.replace_messages(conversation.id, [_said("first thing")])

    chats.replace_messages(conversation.id, [_said("first thing"), _said("something else entirely")])

    assert chats.get(conversation.id)["title"] == "first thing"


def test_an_agent_speaking_first_does_not_name_the_conversation(chats) -> None:
    """The title is what the OPERATOR said; a greeting from Primary names
    nothing."""
    conversation = chats.create()

    chats.replace_messages(conversation.id, [_answered("Hello"), _said("the real question")])

    assert chats.get(conversation.id)["title"] == "the real question"


def test_a_pasted_paragraph_does_not_become_a_paragraph_long_row(chats) -> None:
    conversation = chats.create()

    chats.replace_messages(conversation.id, [_said("word " * 200)])

    title = chats.get(conversation.id)["title"]
    assert len(title) <= 80
    assert "\n" not in title


def test_the_most_recently_used_conversation_is_first(chats) -> None:
    """A chat list is a history, and the thing you want is almost always the
    thing you just had."""
    older = chats.create()
    newer = chats.create()
    chats.replace_messages(newer.id, [_said("newer")])
    chats.replace_messages(older.id, [_said("older, but touched last")])

    assert [summary.id for summary in chats.list()][0] == older.id


def test_deleting_one_leaves_the_others(chats) -> None:
    kept = chats.create()
    doomed = chats.create()

    assert chats.delete(doomed.id) is True

    assert chats.get(doomed.id) is None
    assert [summary.id for summary in chats.list()] == [kept.id]


def test_deleting_a_conversation_that_is_already_gone_is_not_an_error(chats) -> None:
    """Idempotent: that is the state the caller wanted."""
    assert chats.delete("never-existed") is False


def test_writing_to_a_deleted_conversation_is_refused(chats) -> None:
    """Two tabs, one deleted in the other. The refusal is better than silently
    recreating a conversation the operator threw away."""
    conversation = chats.create()
    chats.delete(conversation.id)

    with pytest.raises(ChatError):
        chats.replace_messages(conversation.id, [_said("still typing")])


def test_an_id_can_never_escape_the_chats_folder(chats, tmp_path) -> None:
    """The id becomes a filename. A caller passing `../../x` must not write
    outside the data folder, whatever the Manager does upstream."""
    assert chats_data.conversation_path("../../escape") is None
    assert chats_data.read_conversation("../../escape") is None
    assert chats_data.delete_conversation("../../escape") is False
    assert chats_data.write_conversation("../../escape", {"messages": []}) is False


def test_the_clients_own_bookkeeping_is_not_stored(chats) -> None:
    """`localId` is per-mount and meaningless on the way back in; an unknown
    key is far more likely to be a mistake than a feature."""
    conversation = chats.create()

    chats.replace_messages(conversation.id, [{"role": "user", "text": "hi", "localId": "msg-1", "nonsense": 1}])

    stored = chats.get(conversation.id)["messages"][0]
    assert stored == {"role": "user", "text": "hi"}


def test_a_message_that_is_not_one_is_dropped(chats) -> None:
    conversation = chats.create()

    chats.replace_messages(
        conversation.id,
        ["just a string", {"role": "nobody", "text": "x"}, {"text": "roleless"}, _said("real")],
    )

    assert [message["text"] for message in chats.get(conversation.id)["messages"]] == ["real"]


def test_streaming_flags_survive_a_round_trip(chats) -> None:
    """An error bubble and its activity lines are part of what the thread
    looked like; reloading should show the same conversation, not a tidied
    one."""
    conversation = chats.create()

    chats.replace_messages(
        conversation.id,
        [{"role": "agent", "text": "it failed", "isError": True, "activity": ["looked it up"]}],
    )

    stored = chats.get(conversation.id)["messages"][0]
    assert stored["isError"] is True
    assert stored["activity"] == ["looked it up"]


def test_one_corrupt_conversation_does_not_cost_the_others(chats) -> None:
    """A file hand-edited into invalid JSON is skipped, not raised: one broken
    thread must not take the whole list down."""
    good = chats.create()
    broken = chats_data.chats_dir() / "broken.json"
    broken.write_text("{not json", encoding="utf-8")

    assert [summary.id for summary in chats.list()] == [good.id]


def test_a_conversation_with_messages_cannot_be_emptied(chats) -> None:
    """The bug this exists for: the page saves whatever thread the panel is
    holding, and a panel that mounted on a failed load is holding nothing.
    That wrote `[]` over two real conversations on the operator's own install
    (2026-10-24). Emptying is never what the page means -- there is no "clear
    this chat" -- so it is refused rather than guessed at."""
    conversation = chats.create()
    chats.replace_messages(conversation.id, [_said("something worth keeping")])

    with pytest.raises(ChatError):
        chats.replace_messages(conversation.id, [])

    assert chats.get(conversation.id)["messages"][0]["text"] == "something worth keeping"


def test_an_empty_conversation_may_still_be_saved_empty(chats) -> None:
    """Only a LOSS is refused. A conversation that has nothing in it saving
    nothing is a no-op, not an error to show anyone."""
    conversation = chats.create()

    chats.replace_messages(conversation.id, [])

    assert chats.get(conversation.id)["messages"] == []


def test_a_placeholder_title_is_not_a_name(chats) -> None:
    """A save that landed before the first message used to freeze "New chat"
    as the title forever, because the title is only set when it is unset. The
    placeholder counts as unset."""
    conversation = chats.create()
    chats.replace_messages(conversation.id, [])
    assert chats.get(conversation.id)["title"] == UNTITLED

    chats.replace_messages(conversation.id, [_said("the real first question")])

    assert chats.get(conversation.id)["title"] == "the real first question"


def test_a_record_already_stuck_on_the_placeholder_recovers_on_read(chats) -> None:
    """Conversations written by the broken version are on disk now. They show
    their real name again without anyone repairing the files."""
    conversation = chats.create()
    stored = chats_data.read_conversation(conversation.id)
    stored["title"] = UNTITLED
    stored["messages"] = [{"role": "user", "text": "Tell me about the renewal"}]
    chats_data.write_conversation(conversation.id, stored)

    assert chats.get(conversation.id)["title"] == "Tell me about the renewal"
