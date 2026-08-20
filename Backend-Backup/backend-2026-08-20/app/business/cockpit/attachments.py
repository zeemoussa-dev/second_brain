"""Inbox Cockpit attachment review (ADR-036 points 5/6) -- lists an
email's own already-vault-saved attachment files, and hands one off to
the shared Cockpit thread by composing REQ-SB-28's own upload_storage
(extract) + summarize-file Skill DIRECTLY against the real vault-saved
bytes -- never REQ-SB-28's own chat-upload HTTP endpoint (which ends in
an unwanted Vault-Filing-Expert auto-file for THIS use case)."""
from __future__ import annotations

from pathlib import Path

from app.business import skill_tools
from app.business.cockpit import threads
from app.config import settings
from app.data_access import upload_storage

_EMAIL_ATTACHMENTS_ROOT = "Work/Emails/attachments"


def _attachments_dir(email_note_stem: str) -> Path:
    """No re-slugification needed here -- confirmed by direct reading of
    vault_writer.py::write_attachments/write_note: both compute the
    attachments-directory name and the note's own filename stem via the
    identical `_slugify(filename_stem)` call on the identical raw input,
    so an Email note's own real `path.stem` (what list_email_items
    surfaces as "stem", and what the Cockpit route is keyed on) IS
    already byte-identical to write_attachments' own `note_slug` --
    confirmed live against real vault fixtures. Deliberately does not
    reach into vault_writer.py's own private `_slugify` (the task's own
    Constraint: prefer a cleaner path when one exists over a private
    reach-through)."""
    return settings.vault_path / _EMAIL_ATTACHMENTS_ROOT / email_note_stem


def _iter_attachment_files(email_note_stem: str):
    """BUG-FIX 2026-08-17 (ESC-043): `vault_writer.write_attachments`
    now nests saves one level deeper by `message_segment`
    (`BUGFIX-03-US-01-T02`) -- files no longer sit directly in
    `_attachments_dir()`, they sit in a per-message-segment
    subdirectory beneath it. Supports BOTH shapes: real, already-saved
    historical attachments still sit flat (confirmed live against the
    real vault -- this fix never moves anything already on disk), while
    any email captured from now on saves nested. `classify_recent_emails`
    writes exactly one `message_segment` (the email's own id) per email
    note, so this yields every real file across whichever segment
    subdirectories exist, without needing to know the exact segment
    value used at write time."""
    directory = _attachments_dir(email_note_stem)
    if not directory.exists():
        return
    for entry in sorted(directory.iterdir()):
        if entry.is_file():
            yield entry
        elif entry.is_dir():
            for path in sorted(entry.iterdir()):
                if path.is_file():
                    yield path


def list_attachments(email_note_stem: str) -> list[dict]:
    return [
        {"filename": path.name, "size": path.stat().st_size}
        for path in _iter_attachment_files(email_note_stem)
    ]


def hand_off_attachment_to_chat(email_note_stem: str, filename: str) -> dict:
    path = next(
        (p for p in _iter_attachment_files(email_note_stem) if p.name == filename),
        None,
    )
    if path is None:
        return {"status": "not_found"}
    content = path.read_bytes()
    upload_id = upload_storage.save_upload(filename, content)
    try:
        extracted_text = upload_storage.extract_text_content(upload_id, filename)
    except ValueError as exc:
        threads.append_system_message("email", email_note_stem, f"Couldn't read {filename}: {exc}")
        return {"status": "extraction_failed"}
    finally:
        upload_storage.delete_upload(upload_id, filename)

    summary_result = skill_tools.summarize_file(extracted_text, f"Email attachment: {filename}")
    if summary_result.get("status") != "ok":
        message = summary_result.get("message", "Summarization failed.")
        threads.append_system_message("email", email_note_stem, f"[Attachment: {filename}] {message}")
        return {"status": "summarization_failed"}

    threads.append_system_message(
        "email", email_note_stem, f"[Attachment: {filename}] {summary_result['summary']}",
    )
    return {"status": "ok", "summary": summary_result["summary"]}
