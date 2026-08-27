"""Durable, per-email staging store (ADR-046 Decision 1) --
one directory per staged email under <app database folder>/email_staging/<entry_id>/,
holding a JSON metadata record plus each attachment's own real bytes on
disk. A dedicated data_access sibling to vault_writer.py -- mirrors
upload_storage.py's own explicit "raw pre-note buffer, not a vault note,
kept structurally separate" boundary reasoning (ADR-034), applied here to
Outlook-fetched-but-not-yet-processed email content instead of user
uploads. Never imports outlook_com -- this module only stores/reconstructs
plain dicts shaped exactly like outlook_com.list_recent_mail's own return
value; it has no COM dependency of its own. Not a staging/promotion gate
on vault content (MEMORY.md's standing constraint) -- a staged email is
not yet a note at all; this store exists solely so a real Outlook-COM
stall can't lose already-fetched content.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings

def _staging_root() -> Path:
    return settings.second_brain_data_path / "email_staging"


def _entry_dir(entry_id: str) -> Path:
    return _staging_root() / entry_id


def _email_json_path(entry_id: str) -> Path:
    return _entry_dir(entry_id) / "email.json"


def _attachments_dir(entry_id: str) -> Path:
    return _entry_dir(entry_id) / "attachments"


def stage_email(email: dict) -> None:
    """Writes one email's own directory. email is exactly the dict shape
    outlook_com.list_recent_mail already produces. Idempotent -- re-
    staging the same id overwrites its own directory cleanly (a Pull
    re-run against an overlapping recent-N window must not create a
    second, duplicate staged copy of the same email). Attachment bytes
    are written to their own file on disk, never base64-inflated into
    email.json -- mirrors upload_storage.py's own blob-on-disk precedent
    (ADR-034); the recipients/attendees JSON-encoded-STRING workaround
    (ADR-042 point 3) is for small structured values, not multi-megabyte
    binaries, and is deliberately not used here."""
    entry_id = email["id"]
    entry_dir = _entry_dir(entry_id)
    shutil.rmtree(entry_dir, ignore_errors=True)
    attachments_dir = _attachments_dir(entry_id)
    attachments_dir.mkdir(parents=True, exist_ok=True)

    staged_attachments = []
    for attachment in email.get("attachments", []):
        staged_attachment = {
            "filename": attachment["filename"],
            "size": attachment["size"],
        }
        content = attachment.get("content")
        # outlook_com.list_recent_mail already sets "content" to None for
        # an oversized attachment (see _MAX_ATTACHMENT_BYTES) -- there is
        # no real byte payload to persist for that case, so no file is
        # written and no relative_path is recorded; None round-trips as
        # None through list_staged_emails below.
        if content is not None:
            attachment_path = attachments_dir / attachment["filename"]
            attachment_path.write_bytes(content)
            staged_attachment["relative_path"] = f"attachments/{attachment['filename']}"
        staged_attachments.append(staged_attachment)

    record = dict(email)
    record["attachments"] = staged_attachments
    _email_json_path(entry_id).write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )


def list_staged_emails() -> list[dict]:
    """Enumerates every staged directory under
    .second-brain/email_staging/, reconstructing each into the exact
    list_recent_mail-shaped dict -- attachment bytes re-read from their
    own files back into each attachment's own "content" key -- so every
    downstream Job sees the identical shape it already consumes today.
    Returns [] if the staging directory doesn't exist yet, mirroring
    list_notes_in_kind_folder's own "not-yet-created-folder is a valid,
    honest empty state" convention."""
    staging_root = _staging_root()
    if not staging_root.exists():
        return []

    staged_emails = []
    for entry_dir in sorted(staging_root.iterdir()):
        email_json_path = entry_dir / "email.json"
        if not email_json_path.exists():
            continue
        record = json.loads(email_json_path.read_text(encoding="utf-8"))
        reconstructed_attachments = []
        for staged_attachment in record.get("attachments", []):
            reconstructed_attachment = {
                "filename": staged_attachment["filename"],
                "size": staged_attachment["size"],
            }
            relative_path = staged_attachment.get("relative_path")
            if relative_path is not None:
                reconstructed_attachment["content"] = (
                    entry_dir / relative_path
                ).read_bytes()
            else:
                reconstructed_attachment["content"] = None
            reconstructed_attachments.append(reconstructed_attachment)
        record["attachments"] = reconstructed_attachments
        staged_emails.append(record)
    return staged_emails


def remove_staged_email(entry_id: str) -> None:
    """Deletes a staged entry's own directory (metadata + attachments)
    once its own graph run has completed successfully. Idempotent --
    removing an already-absent entry_id is a no-op, never raises."""
    shutil.rmtree(_entry_dir(entry_id), ignore_errors=True)
