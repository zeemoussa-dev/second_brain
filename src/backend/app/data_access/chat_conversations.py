"""Raw storage for the Chat page's conversations (operator, 2026-10-24: "we
need to edit the Chat Page, Introduce Multiple Chats, An Option to delete a
Chat").

`<SECOND_BRAIN_DATA_PATH>/chats/<id>.json`: one file per conversation, its own
top-level child of the config folder like `auth/` and `branding/`.

**One file each, not one file of all of them.** A chat grows every turn, and a
single document would be rewritten in full on every message of every
conversation -- and a delete would rewrite every surviving chat to remove one.
Per-file makes a delete an unlink and an append a write of only the thread that
changed.

This is NOT the Cockpit's chat store (`business/cockpit/chat_store.py`). That
one is keyed by the note a conversation is ABOUT and carries a roster of agents
brought in; these are free-standing conversations with Primary, which have no
subject and no roster. Two stores because they are two things, not because
nobody noticed.

Zero business interpretation, the same contract as every module here: no title
is derived, no shape is validated, no ordering is applied. `ChatManager` owns
all of that.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings

_CHATS_DIR = "chats"

#: What an id is allowed to look like ON DISK. The id becomes a filename, so a
#: caller that passed `../../something` would otherwise write outside the data
#: folder entirely. The Manager generates ids, but this module is what the
#: filesystem actually trusts.
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def chats_dir() -> Path:
    return settings.second_brain_data_path / _CHATS_DIR


def conversation_path(conversation_id: str) -> Path | None:
    """The file for this id, or None when the id could never name one."""
    if not _SAFE_ID.match(conversation_id or ""):
        return None
    return chats_dir() / f"{conversation_id}.json"


def list_conversation_files() -> list[Path]:
    directory = chats_dir()
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def read_conversation(conversation_id: str) -> dict | None:
    """None for an unknown or unreadable id. A file that does not parse is
    treated as absent rather than raising: one corrupt conversation must not
    take the whole list down with it."""
    path = conversation_path(conversation_id)
    if path is None or not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return record if isinstance(record, dict) else None


def write_conversation(conversation_id: str, record: dict) -> bool:
    path = conversation_path(conversation_id)
    if path is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def delete_conversation(conversation_id: str) -> bool:
    """True when there was one to delete."""
    path = conversation_path(conversation_id)
    if path is None or not path.is_file():
        return False
    path.unlink()
    return True
