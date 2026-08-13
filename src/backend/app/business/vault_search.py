"""Read-only browse/tag-filter/note-detail query logic over
vault_indexing.get_index() (REQ-SB-02-US-01) -- composes vault_indexing
only, never vault_writer/filesystem directly (ADR-003), mirroring
my_day.py's/system_health.py's own "one-module-per-feature, read-only
aggregation" shape. Ranked search (search()) is added by T02, in this
same module -- see ADR-026."""
from __future__ import annotations

import math
import re
from pathlib import Path

from app.business import vault_indexing
from app.data_access import vault_writer

_DEFAULT_PAGE_SIZE = 20


def _title_for(entry: dict) -> str:
    """subject when present (Email/Meeting notes); otherwise the note's
    own filename stem -- Customer/Person/Partner hub notes carry no
    "subject" frontmatter field at all. Ordinary projection, not a new
    naming convention."""
    return entry["frontmatter"].get("subject") or entry["stem"]


def _kind_for(entry: dict) -> str:
    return entry["frontmatter"].get("type", "Unknown")


def _summary(entry: dict) -> dict:
    return {
        "stem": entry["stem"],
        "title": _title_for(entry),
        "kind": _kind_for(entry),
        "tags": entry["tags"],
    }


def list_notes(
    page: int = 1,
    page_size: int = _DEFAULT_PAGE_SIZE,
    tag: str | None = None,
) -> dict:
    """Scenarios 1, 2, 6 -- browse all notes, or narrow to one exact tag
    (case-sensitive match against the tag strings this project's own
    capture pipelines already write, e.g. "customer/masdar",
    "kind/email"). Sorted by stem -- the one field every entry always
    has; no note-kind-specific date field is universal across every
    indexed kind. An empty result (no notes at all, or a real tag with
    zero matches) returns "notes": [] honestly -- Scenario 6 is this
    same function returning a correctly-empty list, not a distinct code
    path."""
    entries = list(vault_indexing.get_index().values())
    if tag is not None:
        entries = [entry for entry in entries if tag in entry["tags"]]
    entries.sort(key=lambda entry: entry["stem"])

    total = len(entries)
    start = (page - 1) * page_size
    page_entries = entries[start:start + page_size]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "notes": [_summary(entry) for entry in page_entries],
    }


def list_tags() -> dict:
    """Scenario 2's own prerequisite -- the real, current list of tags
    that actually exist in the index (with counts), sorted by count
    descending then tag name. The frontend's tag-filter UI renders this
    real list rather than requiring the user to already know an exact
    tag string to type (the approved prototype's own fixed chip buttons
    are illustrative-only, not a real discovery mechanism)."""
    counts: dict[str, int] = {}
    for entry in vault_indexing.get_index().values():
        for tag in entry["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    tags = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return {"tags": [{"tag": tag, "count": count} for tag, count in tags]}


def _resolve_forward_links(entry: dict, index: dict[str, dict]) -> list[dict]:
    """entry["outgoing_wikilinks"] is deliberately RAW, unresolved
    target text (REQ-SB-01-US-01-T02's own shape) -- resolution only
    happens in ADR-024's backlink-deriving pass, against the *target*'s
    own entry, never stored back onto the source. Applies the identical
    case-insensitive stem-matching rule a second time, at read time, to
    resolve each raw target for display. An unresolved target (a
    dangling link, or a manually-authored free-text wikilink -- ADR-024's
    own documented honest-handling case) is simply omitted -- no crash,
    no fabricated entry, the same posture ADR-024 already applies to
    backlink derivation, not a new rule."""
    stems_by_lower_stem = {stem.lower(): stem for stem in index}
    resolved = []
    for target in entry["outgoing_wikilinks"]:
        matched_stem = stems_by_lower_stem.get(target.lower())
        if matched_stem is None or matched_stem == entry["stem"]:
            continue
        resolved.append(_summary(index[matched_stem]))
    return resolved


def _resolve_backlinks(entry: dict, index: dict[str, dict]) -> list[dict]:
    """entry["incoming_wikilinks"] is already a list of resolved source
    stems (ADR-024 point 3) -- a direct lookup, no re-matching needed."""
    return [_summary(index[stem]) for stem in entry["incoming_wikilinks"] if stem in index]


def get_note_detail(stem: str) -> dict | None:
    """Scenario 3 -- one note's frontmatter/tags plus its resolved
    forward-link/backlink lists. None for an unknown stem -- T03's
    router translates this to a 404."""
    index = vault_indexing.get_index()
    entry = index.get(stem)
    if entry is None:
        return None
    return {
        "stem": entry["stem"],
        "title": _title_for(entry),
        "kind": _kind_for(entry),
        "frontmatter": entry["frontmatter"],
        "tags": entry["tags"],
        "forward_links": _resolve_forward_links(entry, index),
        "backlinks": _resolve_backlinks(entry, index),
    }


_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Title/tags outweigh an incidental body mention (ADR-026, the story's
# own worked example) -- tuning constants, adjustable without a
# superseding ADR.
_FIELD_WEIGHTS = {"title": 3.0, "tags": 2.0, "body": 1.0}
_BM25_K1 = 1.5
_BM25_B = 0.75
_DEFAULT_SEARCH_LIMIT = 20


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _field_tokens(entry: dict, body_by_stem: dict[str, str]) -> dict[str, list[str]]:
    return {
        "title": _tokenize(_title_for(entry)),
        "tags": _tokenize(" ".join(entry["tags"])),
        "body": _tokenize(body_by_stem.get(entry["stem"], "")),
    }


def _bm25_term_score(
    term: str,
    doc_tokens: list[str],
    avg_len: float,
    doc_freq: int,
    total_docs: int,
) -> float:
    """Standard BM25 term score for one field of one document -- see
    ADR-026 for the full mechanism/alternatives reasoning."""
    if total_docs == 0 or doc_freq == 0:
        return 0.0
    term_freq = doc_tokens.count(term)
    if term_freq == 0:
        return 0.0
    idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
    doc_len = len(doc_tokens) or 1
    numerator = term_freq * (_BM25_K1 + 1)
    denominator = term_freq + _BM25_K1 * (1 - _BM25_B + _BM25_B * doc_len / avg_len)
    return idf * (numerator / denominator)


def search(query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> dict:
    """Scenarios 4, 5 -- field-weighted BM25-style ranked search over
    every currently-indexed note's title/tags/body (ADR-026). Body text
    is read fresh from disk per candidate note via vault_writer.
    read_note() -- vault_indexing's own index entries never store it
    (ADR-026's own documented reasoning); title/tags come directly from
    the already-in-memory index. An empty results list for a query
    matching nothing is Scenario 5's own honest empty state, not a
    distinct code path."""
    query_tokens = _tokenize(query)
    index = vault_indexing.get_index()
    entries = list(index.values())
    if not query_tokens or not entries:
        return {"query": query, "results": []}

    body_by_stem = {
        entry["stem"]: vault_writer.read_note(Path(entry["path"]))[1]
        for entry in entries
    }
    field_tokens_by_stem = {
        entry["stem"]: _field_tokens(entry, body_by_stem) for entry in entries
    }

    scores: dict[str, float] = {stem: 0.0 for stem in field_tokens_by_stem}
    for field, weight in _FIELD_WEIGHTS.items():
        field_token_lists = {
            stem: tokens[field] for stem, tokens in field_tokens_by_stem.items()
        }
        total_docs = len(field_token_lists)
        avg_len = (
            sum(len(tokens) for tokens in field_token_lists.values()) / total_docs
        ) or 1
        for term in set(query_tokens):
            doc_freq = sum(1 for tokens in field_token_lists.values() if term in tokens)
            for stem, tokens in field_token_lists.items():
                scores[stem] += weight * _bm25_term_score(
                    term, tokens, avg_len, doc_freq, total_docs
                )

    ranked_stems = sorted(
        (stem for stem, score in scores.items() if score > 0),
        key=lambda stem: (-scores[stem], stem),
    )[:limit]

    results = [
        {**_summary(index[stem]), "rank": rank, "score": round(scores[stem], 4)}
        for rank, stem in enumerate(ranked_stems, start=1)
    ]
    return {"query": query, "results": results}
