"""Real business logic behind the Cockpit's own composed view and
document-upload flow -- moved out of cockpit_router.py (2026-08-28, API
layer holds no business logic): filling in a subject's missing fields,
composing the view from several independent sources, and validating an
upload are all business rules, not HTTP concerns.

Cockpit is a framework component (`ADR-022`, `BUG-063`): it must not know a
business concept such as Customer, nor import a plugin. It asks the plugin
host's subject enrichers to fill in what a note does not carry itself.
"""
from __future__ import annotations

import logging

from app.business.cockpit import chat_store, documents, people
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault.vault_manager import VaultManager

_vault_manager = VaultManager()
_plugin_manager = PluginManager()
_logger = logging.getLogger(__name__)


class UnknownSubjectError(Exception):
    pass


class EmptyUploadError(Exception):
    pass


class UploadTooLargeError(Exception):
    def __init__(self, size_mb: float) -> None:
        self.size_mb = size_mb
        super().__init__(f"File too large ({size_mb:.1f} MB) — the limit is 25 MB.")


def _enriched_subject(subject_kind: str, entry: dict) -> dict:
    """The note's own frontmatter, plus what installed subject enrichers can
    add. A Thread's frontmatter never carries a `customer` field, only a
    `customer/<slug>` tag (found live 2026-08-27), so that value arrives from
    an enricher.

    An enricher only fills a field the note leaves empty: a Meeting note's own
    real `customer` is never overwritten by a tag-derived one. An enricher that
    raises or returns something other than a dict is skipped, so one plugin's
    bug cannot take down a framework screen."""
    subject = dict(entry["frontmatter"])
    tags = list(entry["tags"])
    for enrich in _plugin_manager.get_subject_enrichers():
        try:
            additions = enrich(subject_kind, dict(subject), tags)
        except Exception:
            _logger.exception("subject enricher %r failed for a %s; skipped",
                              getattr(enrich, "__qualname__", enrich), subject_kind)
            continue
        if not isinstance(additions, dict):
            continue
        for field, value in additions.items():
            if value and not subject.get(field):
                subject[field] = value
    return subject


def build_cockpit_view(subject_kind: str, subject_note_stem: str) -> dict:
    """Raises UnknownSubjectError if the note isn't indexed."""
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        raise UnknownSubjectError(subject_note_stem)
    return {
        "subject": _enriched_subject(subject_kind, entry),
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
