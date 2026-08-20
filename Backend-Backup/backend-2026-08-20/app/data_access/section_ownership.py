"""Section-ownership enforcement (REQ-SB-71-US-01, see ADR-048 Decision 2 in
Implementation/Architecture/ADR.md) -- a new, composed-alongside module
(data_access layer, never business: ADR-003's layer boundary means
vault_writer.replace_body_section itself, which performs this check, cannot
depend on anything in app/business), mirroring ADR-014's own "compose
alongside, don't reopen" precedent rather than growing vault_writer.py
itself further.

Two independent, structural rules, per the operator's own explicit scope
choice ("1 and 2 is enough" -- no snapshot-before-write safety net, no extra
approval gate beyond REQ-SB-57's existing Background-amendment flow):

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
    "email_classification.thread_match_merge": frozenset({"## Summary", "## Related"}),
    "thread_summary_backfill.backfill_thread_summaries": frozenset({"## Summary"}),
    "project_customer_synthesizer.synthesize_project": frozenset({"## Glimpse"}),
    "project_customer_synthesizer.synthesize_customer": frozenset({"## Glimpse"}),
    "project_customer_synthesizer.finalize_background_amendment_proposal": frozenset({"## Background"}),
    # REQ-SB-71-US-02-T05 -- Stage 2's real Compass-backed judgment, full
    # reconstruction from every raw message on every call. Narrowed
    # (REQ-SB-72-US-01-T06, ADR-049 Decision 4) -- "## Related" ownership
    # transferred wholesale to librarian_housekeeping.populate_thread_
    # related_links, below, in the SAME change -- never a window where
    # both callers could write "## Related" simultaneously.
    "email_classification.synthesize_thread": frozenset({"## Summary"}),
    # REQ-SB-71-US-02-T07 -- the Files/OKF companion's own `## Summary` write.
    "email_classification.write_file_companion": frozenset({"## Summary"}),
    # REQ-SB-71-US-03-T01 -- the redesigned Meeting Capture's own `## Summary`
    # regeneration (one-time vs. recurring, frontmatter-only logistics).
    "meeting_classification.classify_recent_meetings": frozenset({"## Summary"}),
    # REQ-SB-72-US-01-T04 -- the Librarian's Files/OKF backfill Job, the
    # sole owner of a Thread's own structured ## Files section.
    "librarian_housekeeping.backfill_files": frozenset({"## Files"}),
    # REQ-SB-72-US-01-T06 -- the Librarian's sole ownership of ## Related
    # going forward, registered in the SAME change that narrows
    # email_classification.synthesize_thread's own entry above.
    "librarian_housekeeping.populate_thread_related_links": frozenset({"## Related"}),
    # REQ-SB-73-US-01-T01 -- the Librarian's new Bidirectional Thread <->
    # Message Linking Job, the sole owner of a Thread's own structured
    # ## Messages section (ADR-054 Decision 3).
    "librarian_housekeeping.link_thread_messages": frozenset({"## Messages"}),
}


class SectionWriteNotAllowed(PermissionError):
    """Raised by replace_body_section when `caller` may not write `header`
    -- a real, observable, honest failure, never a silent no-op
    indistinguishable from replace_body_section's own separate, unchanged
    'header not found in THIS file' contract."""


def is_header_allowed(caller: str, header: str) -> bool:
    """Rule 1 (human-owned headers) is checked FIRST and unconditionally --
    no caller's own registry entry can ever override it, by construction.
    Rule 2 (_CALLER_ALLOW_LISTS) is deny-by-default: a caller id absent from
    the dict may write nothing."""
    if header in _HUMAN_OWNED_HEADERS:
        return False
    return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())
