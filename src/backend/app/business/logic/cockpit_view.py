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
import re

from app.business.cockpit import chat_store, documents, people
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault.vault_manager import VaultManager
from app.obsidian import sections
from app.obsidian.notes import long_path

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


_SUMMARY_HEADER = "## Summary"
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]")


def _summary_links(summary: str | None) -> list[dict]:
    """Which `[[targets]]` in the summary are real notes on this install.

    The screens turn a resolved target into a link into the note view and a
    dangling one into plain text (the vault browser's own rule) -- they cannot
    tell which is which without the index, so the read model says. A summary
    written by a Skill names Customers and People that may or may not have notes
    yet, and showing `[[Masdar]]` as raw brackets is what the operator saw
    (2026-09-24)."""
    if not summary:
        return []
    index = _vault_manager.get_index()
    by_lower_stem = {stem.lower(): stem for stem in index}
    resolved = {}
    for target in _WIKILINK_PATTERN.findall(summary):
        stem = by_lower_stem.get(target.strip().lower())
        if stem:
            resolved[stem] = {"stem": stem}
    return list(resolved.values())


def _note_summary(entry: dict) -> str | None:
    """The subject note's own Summary section, or None when it has none yet.

    Read from the note rather than composed here: a Thread's summary is written
    by the `summarize-and-tag-threads` Skill, and showing it is just surfacing
    what the vault already holds -- this stays an honest reader, never a
    fabricated overview (operator, 2026-09-24: "Thread Summary is not
    loading"). A Meeting note has the same section and nothing writes it yet,
    so meetings keep reading empty until something does.

    `long_path` because a recurring meeting's note sits deep enough to pass
    Windows' 260-character limit, where a plain open() fails."""
    path = entry.get("path")
    if not path:
        return None
    try:
        summary = sections.read_body_section(long_path(path), _SUMMARY_HEADER)
    except OSError as error:
        _logger.warning("could not read the Summary section of %s: %s", entry.get("stem"), error)
        return None
    return summary.strip() or None


def build_cockpit_view(subject_kind: str, subject_note_stem: str) -> dict:
    """Raises UnknownSubjectError if the note isn't indexed."""
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        raise UnknownSubjectError(subject_note_stem)
    summary = _note_summary(entry)
    return {
        "subject": _enriched_subject(subject_kind, entry),
        "people": people.resolve_people_chips(subject_kind, subject_note_stem),
        "overview": {
            "summary": summary,
            "summary_links": _summary_links(summary),
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
