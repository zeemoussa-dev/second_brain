"""The sole gateway onto the Chat page's conversations (operator, 2026-10-24:
"Introduce Multiple Chats, An Option to delete a Chat").

Before this the Chat page held its thread in the browser's memory: reloading
the page, or walking to another screen and back, lost the conversation. There
was exactly one, and no way to keep two subjects apart.

**A conversation names itself.** The title is the first thing the operator
said, trimmed to fit a list row. Asking for a title before the first message is
asking someone to name a thing they have not had yet, and "New chat 4" is not a
name either.

**A message is stored as the UI shaped it.** The Manager checks that a message
is an object with a role and text and drops the rest of the client's
bookkeeping, but it does not reinterpret the content: this store exists to put
the same thread back on the screen, not to become a second model of what a
conversation is. `business/cockpit/chat_store.py` is the one that understands
rosters and routing; this one understands a list.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from app.data_access import chat_conversations as chats_data

#: Long enough to be unguessable in a shared install, short enough to read in a
#: URL -- the selected conversation lives in the query string.
_ID_BYTES = 9

#: A list row, not a paragraph. Longer titles are kept whole in the record and
#: truncated here, so widening the row later does not need a migration.
MAX_TITLE_CHARS = 80

UNTITLED = "New chat"

#: What the UI may store on a message. Anything else a client sends is dropped
#: rather than persisted: `localId` is explicitly per-mount and meaningless on
#: the way back in, and an unknown key is far more likely to be a mistake than
#: a feature.
_MESSAGE_FIELDS = ("role", "text", "isError", "activity")

_ROLES = ("user", "agent")


class ChatError(Exception):
    """A refusal the caller should read verbatim."""


@dataclass(frozen=True)
class ConversationSummary:
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ChatManager:
    def list(self) -> list[ConversationSummary]:
        """Most recently used first -- a chat list is a history, and the thing
        you want is almost always the thing you just had."""
        summaries = []
        for path in chats_data.list_conversation_files():
            record = chats_data.read_conversation(path.stem)
            if record is None:
                # Unreadable on disk. Skipped rather than raised: one corrupt
                # file must not cost the operator every other conversation.
                continue
            summaries.append(self._summarise(path.stem, record))
        return sorted(summaries, key=lambda summary: summary.updated_at, reverse=True)

    def create(self) -> ConversationSummary:
        moment = _now()
        conversation_id = secrets.token_urlsafe(_ID_BYTES)
        record = {"title": "", "created_at": moment, "updated_at": moment, "messages": []}
        chats_data.write_conversation(conversation_id, record)
        return self._summarise(conversation_id, record)

    def get(self, conversation_id: str) -> dict | None:
        """The whole thread, or None. The id is echoed back so a caller holding
        only this can still address it."""
        record = chats_data.read_conversation(conversation_id)
        if record is None:
            return None
        summary = self._summarise(conversation_id, record)
        return {
            "id": summary.id,
            "title": summary.title,
            "created_at": summary.created_at,
            "updated_at": summary.updated_at,
            "messages": self._clean_messages(record.get("messages")),
        }

    def replace_messages(self, conversation_id: str, messages: list) -> dict:
        """The whole thread, as the page now has it.

        A replace rather than an append because the page is the one holding the
        live thread: a streamed reply is edited in place as it arrives, so
        "append this message" would need the client to know which of its own
        bubbles had already been sent and which had changed since. Threads are
        small; writing the list is simpler than keeping two copies in step.
        """
        record = chats_data.read_conversation(conversation_id)
        if record is None:
            raise ChatError("That conversation no longer exists.")
        cleaned = self._clean_messages(messages)
        # Emptying a conversation that has something in it is never what the
        # page means. It means the page lost the thread -- a failed load, a
        # panel mounted before its messages arrived -- and saving that would
        # replace the conversation with nothing. Found the hard way on
        # 2026-10-24: a backend restart mid-click emptied two threads on the
        # operator's own install. There is no "clear this chat" feature, so
        # this refuses rather than guessing; if one is ever added it passes
        # its own flag and this stays the default.
        if not cleaned and self._clean_messages(record.get("messages")):
            raise ChatError(
                "Refusing to empty a conversation that has messages in it. "
                "Nothing was changed."
            )
        record["messages"] = cleaned
        record["updated_at"] = _now()
        # The title is set once, from the first thing said, and then left
        # alone: a conversation that wandered elsewhere is still found under
        # the name of what it started as. `UNTITLED` counts as unset -- a save
        # that happened before the first message would otherwise freeze the
        # placeholder as the name forever.
        if not _is_named(record.get("title")):
            record["title"] = self._title_from(cleaned)
        chats_data.write_conversation(conversation_id, record)
        summary = self._summarise(conversation_id, record)
        return {
            "id": summary.id,
            "title": summary.title,
            "created_at": summary.created_at,
            "updated_at": summary.updated_at,
            "message_count": summary.message_count,
        }

    def delete(self, conversation_id: str) -> bool:
        return chats_data.delete_conversation(conversation_id)

    @classmethod
    def _summarise(cls, conversation_id: str, record: dict) -> ConversationSummary:
        stored_title = str(record.get("title") or "").strip()
        messages = record.get("messages")
        return ConversationSummary(
            id=conversation_id,
            # A record whose title never got set still has to render: fall back
            # to the first message, and only then to the placeholder. A stored
            # `UNTITLED` is treated as unset here too, so a conversation whose
            # placeholder was written before its first message recovers its
            # real name on the next read rather than staying "New chat".
            title=(
                stored_title if _is_named(stored_title) else cls._title_from(cls._clean_messages(messages))
            )[:MAX_TITLE_CHARS],
            created_at=str(record.get("created_at") or ""),
            updated_at=str(record.get("updated_at") or record.get("created_at") or ""),
            message_count=len(messages) if isinstance(messages, list) else 0,
        )

    @staticmethod
    def _title_from(messages: list[dict]) -> str:
        first_said = next(
            (message["text"] for message in messages if message.get("role") == "user" and message.get("text")),
            "",
        )
        # One line: a pasted paragraph would otherwise make the row as tall as
        # the paste.
        condensed = " ".join(str(first_said).split())
        if not condensed:
            return UNTITLED
        return condensed[:MAX_TITLE_CHARS - 1] + "…" if len(condensed) > MAX_TITLE_CHARS else condensed

    @staticmethod
    def _clean_messages(messages: object) -> list[dict]:
        if not isinstance(messages, list):
            return []
        cleaned = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in _ROLES:
                continue
            kept = {field: message[field] for field in _MESSAGE_FIELDS if field in message}
            kept["text"] = str(kept.get("text") or "")
            cleaned.append(kept)
        return cleaned


def _is_named(title: object) -> bool:
    """Whether a stored title is a real name rather than the placeholder."""
    cleaned = str(title or "").strip()
    return bool(cleaned) and cleaned != UNTITLED


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
