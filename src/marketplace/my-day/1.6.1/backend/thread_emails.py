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
_SUMMARY_SECTION = "Summary"
_EXTENDED_PREFIX = "\\\\?\\"

_logger = logging.getLogger(__name__)


class SubjectNotFoundError(LookupError):
    """No indexed note under that stem -- a 404, not an empty thread."""


class MessageNotFoundError(LookupError):
    """No such email inside that Thread's own `messages/` folder."""


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

    def detail_for(self, subject_note_stem: str) -> dict:
        """Everything the Emails tab shows about one captured Thread: what the
        thread is about, the emails it is made of, and the files that came with
        them (operator, 2026-09-25: "the emails tab should include the related
        documents ... as well as the emails it self the thread summary. We need to
        make the email more useful").

        The summary and the attachments come from the host (Plugin API v6) rather
        than being re-derived here: both are vault conventions with traps in them,
        and a second reading of them drifts from the framework's."""
        entry = self._api.vault.index().get(subject_note_stem)
        if entry is None or not entry.get("path"):
            raise SubjectNotFoundError(subject_note_stem)
        frontmatter = entry.get("frontmatter") or {}
        return {
            "stem": subject_note_stem,
            # A Thread carries its subject line as `thread_name`; its own stem is
            # the conversation id, which is not a title anyone wants to read.
            "subject": (frontmatter.get("thread_name") or frontmatter.get("subject")
                        or frontmatter.get("title") or subject_note_stem),
            # None means "no summary written yet", which the screen says out loud;
            # an empty string would read as an empty summary.
            "summary": self._api.vault.read_section(entry["path"], _SUMMARY_SECTION),
            "emails": self.list_for(subject_note_stem),
            "attachments": self._attachments_for(subject_note_stem),
        }

    def _attachments_for(self, subject_note_stem: str) -> list[dict]:
        """The subject's own captured files, each with the stem its note is indexed
        under -- the screen links to the real file through that stem, and cannot
        get it from a path it is not allowed to read."""
        attachments = []
        for attachment in self._api.vault.attachments(subject_note_stem):
            note_path = attachment.get("note_path")
            attachments.append({
                "title": attachment.get("title") or "",
                "filename": attachment.get("filename"),
                "stem": Path(note_path).stem if note_path else "",
            })
        return attachments

    def body_for(self, subject_note_stem: str, message_stem: str) -> dict:
        """One email of this Thread, with the text the capture wrote -- what makes
        the tab a place to read the mail rather than another index of it.

        The message is addressed inside its own Thread's folder, never by stem
        alone: two notes may share a name (framework `BUG-076`), and a stem from a
        URL must not be able to name a note somewhere else in the vault."""
        entry = self._api.vault.index().get(subject_note_stem)
        if entry is None or not entry.get("path"):
            raise SubjectNotFoundError(subject_note_stem)
        messages_root = Path(entry["path"]).parent / _MESSAGES_SUBFOLDER
        note_path = messages_root / f"{Path(message_stem).name}.md"
        if note_path.parent != messages_root or not Path(_long_path(note_path)).is_file():
            raise MessageNotFoundError(message_stem)
        try:
            frontmatter, body = self._api.vault.read_note(note_path)
        except (OSError, ValueError) as error:
            raise MessageNotFoundError(message_stem) from error
        if frontmatter.get("type") != _MESSAGE_NOTE_TYPE:
            raise MessageNotFoundError(message_stem)
        return {
            "stem": note_path.stem,
            "subject": frontmatter.get("subject") or frontmatter.get("title") or note_path.stem,
            "sender": frontmatter.get("sender") or "",
            "sender_email": frontmatter.get("sender_email") or "",
            "received": str(frontmatter.get("received") or ""),
            "body": body,
        }
