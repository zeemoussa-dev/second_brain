"""Section-ownership enforcement -- which caller may write which
`## `-level body-section header. Two independent, structural rules:

1. `_HUMAN_OWNED_HEADERS` -- header text ALONE is the key (not file/note-
   kind-scoped); checked FIRST and UNCONDITIONALLY in is_header_allowed,
   never overridable by any caller's own registered allow-list.
2. `_CALLER_ALLOW_LISTS` -- deny-by-default per-caller registry, granularity
   is the calling FUNCTION (module.function), not the calling module
   (least-privilege).
"""
from __future__ import annotations

_HUMAN_OWNED_HEADERS: frozenset[str] = frozenset({
    "## Personal Notes",
    "## Actions",
})

_CALLER_ALLOW_LISTS: dict[str, frozenset[str]] = {
    # meeting_classification.classify_recent_meetings, every
    # librarian_housekeeping.* entry, and every email_classification.*/
    # thread_summary_backfill.*/project_customer_synthesizer.* entry
    # retired 2026-08-27 along with those now-deleted modules -- email/
    # meeting capture, Librarian housekeeping, and thread/customer
    # synthesis moved fully to Hermes-native Skills, nothing in this
    # backend calls them anymore.
}


class SectionWriteNotAllowed(PermissionError):
    """Raised by replace_body_section when `caller` may not write
    `header` -- a real, observable, honest failure, never a silent no-op
    indistinguishable from replace_body_section's own separate,
    unchanged 'header not found in THIS file' contract."""


def is_header_allowed(caller: str, header: str) -> bool:
    """Rule 1 (human-owned headers) is checked FIRST and unconditionally
    -- no caller's own registry entry can ever override it, by
    construction. Rule 2 (_CALLER_ALLOW_LISTS) is deny-by-default: a
    caller id absent from the dict may write nothing."""
    if header in _HUMAN_OWNED_HEADERS:
        return False
    return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())
