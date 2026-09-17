"""A file attached in Chat is handed to the agent, not interpreted here.

The framework saves the file into the install and sends the agent the
operator's message together with the saved file's path, over the same chat
session as any other turn. What the file means, and whether and where it is
filed, is the agent's decision -- Primary files it with the `capture-files`
Skill -- so no document type or business concept is compiled in here.

Replaces the pre-2026-08-20 attachment pipeline whose route was archived with
the old orchestration layer while the Chat paperclip kept calling it.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.data_access import chat_uploads

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
_MAX_FILENAME_LENGTH = 150
_FORBIDDEN_FILENAME_CHARACTERS = set('<>:"|?*')


class AttachmentRejected(ValueError):
    """Why an attachment was not handed to the agent, in words for the operator."""


def safe_filename(name: str) -> str:
    """The attached file's own name as one safe path segment. A browser sends
    a bare name, but a client may send a path; a separator must never choose
    the folder the file lands in, and the extension must survive shortening."""
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    base = "".join(ch for ch in base if ch not in _FORBIDDEN_FILENAME_CHARACTERS and ord(ch) >= 32)
    base = base.strip().strip(".").strip()
    if not base:
        raise AttachmentRejected("The attached file has no usable name, so it was not sent.")
    if len(base) > _MAX_FILENAME_LENGTH:
        stem, extension = os.path.splitext(base)
        base = stem[: _MAX_FILENAME_LENGTH - len(extension)] + extension
    return base


def store_attachment(filename: str, content: bytes) -> Path:
    """Raises AttachmentRejected for a file that must not reach the agent."""
    if not content:
        raise AttachmentRejected("The attached file is empty, so it was not sent.")
    if len(content) > MAX_ATTACHMENT_BYTES:
        limit_mb = MAX_ATTACHMENT_BYTES // (1024 * 1024)
        raise AttachmentRejected(f"The attached file is larger than {limit_mb} MB, so it was not sent.")
    name = safe_filename(filename)
    try:
        return chat_uploads.save_upload(name, content)
    except OSError as exc:
        raise AttachmentRejected(f"The attached file could not be saved, so it was not sent: {exc}") from exc


def compose_agent_message(message: str, saved_path: Path, original_name: str, size_bytes: int) -> str:
    request = message.strip() or "No message came with this file."
    return (
        f"{request}\n\n"
        f"[The operator attached a file in Chat: \"{original_name}\" ({size_bytes} bytes), "
        f"saved at: {saved_path}\n"
        "Read it from that path to answer. If it should be kept in the vault, file it with "
        "the capture-files Skill.]"
    )
