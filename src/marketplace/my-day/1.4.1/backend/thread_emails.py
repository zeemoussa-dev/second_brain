"""The emails one captured Thread is made of -- My Day's Cockpit tab.

A captured Thread is a folder: the Thread note, and a `messages/` folder holding
one note per real email (`type: RawMessage`, written by `email-thread-capture`).
The Cockpit is the framework's generic component for chatting with agents about a
subject; knowing what a Thread IS, and that its emails live in that folder, is
this plugin's business (operator, 2026-09-24: "Cockpit is the framework Peice as
Component for Agents to chat its Used inside myDay which understands Emails and
Calendar"). So the reader lives here, and the tab is contributed through the host's
`cockpitTabs` contract (framework API v3).

A reader only: every field comes from the message note's own frontmatter, and a
message whose note cannot be read is left out rather than guessed at.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

_MESSAGES_SUBFOLDER = "messages"
_MESSAGE_NOTE_TYPE = "RawMessage"
_EXTENDED_PREFIX = "\\\\?\\"

_logger = logging.getLogger(__name__)


def _long_path(path: Path) -> str:
    """A recurring meeting or a deep Thread folder passes Windows' 260-character
    limit, where a plain open() fails. Same treatment the framework's own readers
    apply; done here rather than imported, since a plugin may import only
    `app.plugin_api`."""
    absolute = os.path.abspath(str(path))
    if os.name == "nt" and not absolute.startswith(_EXTENDED_PREFIX):
        return _EXTENDED_PREFIX + absolute
    return absolute


class ThreadEmails:
    def __init__(self, api) -> None:
        self._api = api

    def list_for(self, subject_note_stem: str) -> list[dict]:
        """Every email in this Thread, newest first. Empty for a subject with no
        `messages/` folder -- a Meeting, or a Thread captured before it existed."""
        entry = self._api.vault.index().get(subject_note_stem)
        if entry is None or not entry.get("path"):
            return []
        messages_root = Path(entry["path"]).parent / _MESSAGES_SUBFOLDER
        if not Path(_long_path(messages_root)).is_dir():
            return []

        emails = []
        for note_path in sorted(Path(_long_path(messages_root)).glob("*.md")):
            try:
                frontmatter, _ = self._api.vault.read_note(note_path)
            except (OSError, ValueError) as error:
                _logger.warning("my-day: skipping unreadable message note %s: %s", note_path.name, error)
                continue
            if frontmatter.get("type") != _MESSAGE_NOTE_TYPE:
                continue
            emails.append({
                "stem": note_path.stem,
                "subject": frontmatter.get("subject") or frontmatter.get("title") or note_path.stem,
                "sender": frontmatter.get("sender") or "",
                "sender_email": frontmatter.get("sender_email") or "",
                # The frontmatter's own string, untouched: reformatting here would
                # invent a timezone the note does not state.
                "received": str(frontmatter.get("received") or ""),
            })
        emails.sort(key=lambda email: email["received"], reverse=True)
        return emails
