"""Real business logic behind the Cockpit's own composed view and
document-upload flow -- moved out of cockpit_router.py (2026-08-28, API
layer holds no business logic): resolving a subject's real customer,
composing the view from several independent sources, and validating an
upload are all business rules, not HTTP concerns.
"""
from __future__ import annotations

from app.business import my_day
from app.business.cockpit import chat_store, documents, people
from app.business.core.vault.vault_manager import VaultManager

_vault_manager = VaultManager()


class UnknownSubjectError(Exception):
    pass


class EmptyUploadError(Exception):
    pass


class UploadTooLargeError(Exception):
    def __init__(self, size_mb: float) -> None:
        self.size_mb = size_mb
        super().__init__(f"File too large ({size_mb:.1f} MB) — the limit is 25 MB.")


def _subject_with_resolved_customer(entry: dict) -> dict:
    """A Thread's own real frontmatter never carries a `customer` field
    (found live 2026-08-27, operator: "Fix the People/Received field gap
    on Threads") -- only a `customer/<slug>` tag, same convention
    `my_day.py`'s own Calendar/Email projections already resolve through
    `customer_name_by_tag`/`customer_from_tags`. A Meeting note that DOES
    carry a real `customer` frontmatter value is left untouched (never
    overwritten by the tag-derived one)."""
    subject = dict(entry["frontmatter"])
    if not subject.get("customer"):
        customer = my_day.customer_from_tags(entry["tags"], my_day.customer_name_by_tag())
        if customer:
            subject["customer"] = customer
    return subject


def build_cockpit_view(subject_kind: str, subject_note_stem: str) -> dict:
    """Raises UnknownSubjectError if the note isn't indexed."""
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        raise UnknownSubjectError(subject_note_stem)
    return {
        "subject": _subject_with_resolved_customer(entry),
        "people": people.resolve_people_chips(subject_kind, subject_note_stem),
        "overview": {
            "summary": None,
            "related_documents": documents.list_documents(subject_note_stem),
            "articles": [],
        },
        "thread": chat_store.get_thread(subject_kind, subject_note_stem),
    }


def upload_document(
    subject_kind: str, subject_note_stem: str, filename: str, content: bytes, caption: str,
) -> dict:
    """Raises UnknownSubjectError / EmptyUploadError / UploadTooLargeError."""
    if _vault_manager.get_index().get(subject_note_stem) is None:
        raise UnknownSubjectError(subject_note_stem)
    if not content:
        raise EmptyUploadError()
    if len(content) > documents.MAX_UPLOAD_SIZE_BYTES:
        raise UploadTooLargeError(len(content) / (1024 * 1024))
    result = documents.save_document(subject_note_stem, filename, content, caption)
    # Real, visible confirmation right in the live chat (operator,
    # 2026-08-27: "I will need to upload a file or a Screenshot while I
    # am in the meeting") -- so attaching something during the meeting
    # reads the same way as any other real event in the conversation,
    # not a silent background write only visible by later checking the
    # Documents tab. "this meeting"/"this email" -- found live
    # 2026-08-27 testing the Inbox Cockpit: this message hardcoded
    # "meeting" regardless of subject_kind, wrong for an email/Thread
    # upload.
    subject_label = "meeting" if subject_kind == "meeting" else "email"
    chat_store.append_message(
        subject_kind, subject_note_stem, speaker="system",
        text=f"📎 Attached “{result['filename']}” to this {subject_label}.",
    )
    return result
