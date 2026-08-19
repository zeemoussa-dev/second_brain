"""First real, persistent, re-runnable index of the vault's notes --
frontmatter, tags, outgoing/incoming wikilinks (REQ-SB-01-US-01). A
module-level, in-memory-only singleton, rebuilt wholesale (never
incrementally diffed) and atomically swapped in on every trigger -- see
ADR-024 for the full storage/rebuild-shape reasoning (no .second-brain/
persistence, no database this pass)."""
from __future__ import annotations

from datetime import datetime, timezone

from app.data_access import vault_writer

_vault_index: dict[str, dict] = {}
_last_rebuilt_at: str | None = None


def _frontmatter_wikilink_targets(frontmatter: dict) -> list[str]:
    """`REQ-SB-73-US-01-T01` (`ADR-054` Decision 5) -- generic scan of every
    frontmatter STRING (and list-of-string) value for `[[...]]` targets, via
    the SAME `vault_writer.extract_wikilink_targets` primitive the body scan
    already uses (a pure regex match over any string, agnostic to origin) --
    never a `thread:`-named special case, so any future frontmatter-wikilink
    field is picked up for free. Strictly additive: a note with no
    wikilink-shaped frontmatter value contributes zero targets, byte-
    identical to today's body-only result."""
    targets: list[str] = []
    for value in frontmatter.values():
        if isinstance(value, str):
            targets.extend(vault_writer.extract_wikilink_targets(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    targets.extend(vault_writer.extract_wikilink_targets(item))
    return targets


def _build_entry(path) -> dict:
    """One note -> one index entry, keyed later by path.stem (the same
    filename-stem identity write_note()/this project's own wikilinks
    already use). tags defaults to [] when the frontmatter has no tags
    field at all, or when T01's list-parsing fix still can't make it a
    list for some unexpected raw shape -- never a crash, never the raw
    unparsed string leaking through (Scenario 6).

    `outgoing_wikilinks` scans BOTH the body text and every frontmatter
    string/string-list value (`REQ-SB-73-US-01-T01`, `ADR-054` Decision 5)
    -- until this pass, only the body was scanned, which left a frontmatter-
    only wikilink field (e.g. `thread:`) silently invisible to the
    backlinks panel/graph view."""
    frontmatter, body = vault_writer.read_note(path)
    tags = frontmatter.get("tags")
    if not isinstance(tags, list):
        tags = []
    return {
        "path": str(path),
        "stem": path.stem,
        "frontmatter": frontmatter,
        "tags": tags,
        "outgoing_wikilinks": (
            vault_writer.extract_wikilink_targets(body) + _frontmatter_wikilink_targets(frontmatter)
        ),
        "incoming_wikilinks": [],
    }


def rebuild_index() -> dict[str, dict]:
    """Full, idempotent rebuild (ADR-024) -- walks every real note under
    Work/ (vault_writer.list_all_note_paths(), Scenario 7's exclusion is
    already satisfied by that existing primitive), builds one entry per
    note, then a second pass inverts each note's outgoing wikilinks into
    every matched target's incoming_wikilinks list (Scenario 2).
    Wikilink target text is matched against each note's own filename
    stem, case-insensitively -- the same identity this project's own
    capture pipelines already write wikilinks against
    (upsert_attendee_links, record_conversation_note/
    find_related_note_stems). An unresolved target (a dangling link, or
    a manually-authored note's free-text wikilink that doesn't match) is
    simply never added to any incoming_wikilinks list -- no crash, no
    fabricated entry (Scenario 5's "handled honestly" requirement falls
    out for free here: a deleted note's own former target simply cannot
    appear in this fresh rebuild at all).

    Assembles a brand-new dict end to end, then atomically reassigns the
    module-level reference -- a single-reference rebind is safe under
    CPython's GIL, no explicit lock needed. Discarding the old dict
    wholesale (never patching it in place) is what gives deletions/edits
    their honest reconciliation for free (Scenarios 3, 4, 5) -- there is
    no separate add/edit/delete code path, every re-run is the exact same
    full rebuild."""
    global _vault_index, _last_rebuilt_at
    new_index: dict[str, dict] = {}
    for path in vault_writer.list_all_note_paths():
        entry = _build_entry(path)
        new_index[entry["stem"]] = entry

    stems_by_lower_stem = {stem.lower(): stem for stem in new_index}
    for entry in new_index.values():
        for target in entry["outgoing_wikilinks"]:
            matched_stem = stems_by_lower_stem.get(target.lower())
            if matched_stem is None or matched_stem == entry["stem"]:
                continue
            backlinks = new_index[matched_stem]["incoming_wikilinks"]
            if entry["stem"] not in backlinks:
                backlinks.append(entry["stem"])

    _vault_index = new_index
    _last_rebuilt_at = datetime.now(timezone.utc).isoformat()
    return _vault_index


def get_index() -> dict[str, dict]:
    """Plain whole-dict accessor -- no filter/query parameters. Internal/
    test use, and the substrate REQ-SB-02's browse/search will build on;
    deliberately not a browse/search API itself (ADR-024's own Non-Goals
    boundary)."""
    return _vault_index


def get_last_rebuilt_at() -> str | None:
    """ISO-8601 UTC timestamp of the most recent successful
    rebuild_index() call this process lifetime, or None if the index
    has never been built yet -- REQ-SB-02-US-01 Scenario 7's own
    honest "nothing indexed yet" check. A second, independent
    accessor alongside get_index() -- extends ADR-024, does not
    reopen its "no filter/query parameters on get_index()" decision
    (this is a separate function, not a parameter)."""
    return _last_rebuilt_at
