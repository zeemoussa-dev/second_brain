"""The emails a Thread is made of -- the Inbox Cockpit's own Emails list.

A captured Thread is a folder: the Thread note itself, and a `messages/` folder
holding one note per real email (`type: RawMessage`, written by
`email-thread-capture`). The Cockpit showed the Thread note and its attachments
but never the emails themselves, so the conversation it is a cockpit FOR was the
one thing it could not show (operator, 2026-09-24: "I can't See Related Emails to
the Thread").

A reader only: every field comes from the message note's own frontmatter, and a
message whose note cannot be read is left out rather than guessed at. Each one is
a real note, so the list links straight into the note view.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.business.core.vault.vault_manager import VaultManager
from app.obsidian.notes import long_path
from app.vault import vault_manager as vm

_MESSAGES_SUBFOLDER = "messages"
_MESSAGE_NOTE_TYPE = "RawMessage"

_logger = logging.getLogger(__name__)
_vault_manager = VaultManager()


def list_messages(subject_note_stem: str) -> list[dict]:
    """Every email in this Thread, newest first. Empty for a subject that has no
    `messages/` folder -- a Meeting, or a Thread captured before the folder
    existed."""
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None or not entry.get("path"):
        return []
    messages_root = Path(entry["path"]).parent / _MESSAGES_SUBFOLDER
    if not Path(long_path(messages_root)).is_dir():
        return []

    messages = []
    for note_path in sorted(Path(long_path(messages_root)).glob("*.md")):
        try:
            frontmatter, _ = vm.read_note(note_path)
        except (OSError, ValueError) as error:
            _logger.warning("cockpit: skipping unreadable message note %s: %s", note_path.name, error)
            continue
        if frontmatter.get("type") != _MESSAGE_NOTE_TYPE:
            continue
        messages.append({
            "stem": note_path.stem,
            "subject": frontmatter.get("subject") or frontmatter.get("title") or note_path.stem,
            "sender": frontmatter.get("sender") or "",
            "sender_email": frontmatter.get("sender_email") or "",
            # The frontmatter's own string, untouched: the Cockpit's other times
            # are rendered the same way, and reformatting here would invent a
            # timezone the note does not state.
            "received": str(frontmatter.get("received") or ""),
        })
    messages.sort(key=lambda message: message["received"], reverse=True)
    return messages
