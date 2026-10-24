"""VaultManager -- the sole gateway onto Vault data (mirrors Section/
Agent/Pipeline Manager's own "one real gateway" rule), folding in and
retiring four previously-separate business modules that had no single
owning door: `vault_indexing.py` (the in-memory note index -- rebuild/
read/overview), `vault_index_config.py` (which top-level Work/ folders
the structural indexer walks), `vault_templates.py` (read-only Template
listing), and `vault_entities.py` (Customer/Partner discovery CRUD -- moved
out to the Entities plugin, Entities plan Phase 5).

`Vault` (vault.py) is a genuine singleton -- there is exactly one vault
-- unlike Section/Agent/Pipeline's own real Array<Entity> shape,
`core/__init__.py`'s own stated convention. Forcing a `get_all() ->
list[Vault]` wrapper around a singleton would be artificial busywork
with no real caller, so this Manager exposes `get_overview() -> Vault`
instead, and its other responsibilities (index/config/templates) as
their own dict-returning methods -- a deliberate,
documented deviation from the generic convention, not an oversight.

The in-memory note index (`get_index()`/`rebuild_index()`) is real,
shared, process-wide state -- unlike Section/Agent/Pipeline's own
stateless Managers (which re-read a real file/registry on every call),
this data is rebuilt once and read many times. Kept as MODULE-level
globals here (not instance attributes) for exactly that reason: any
number of `VaultManager()` instances across the app must see the SAME
index, the same way `vault_indexing.py`'s old module-level singleton
always did -- this is a relocation of that same shape, not a redesign
of it (ADR-024 still governs the no-disk-persistence tradeoff).

2026-08-28, operator: full absorb -- every real caller of the four
folded-in modules was migrated onto this Manager; none of them survive
as a second door onto the same data.

2026-08-28, later same day: `vault_templates.py`'s own logic was
further extracted into its own real `TemplateManager`
(business/core/templates/) rather than staying folded in here directly
-- Templates earned a real Manager of its own (an Array<Entity> like
Section/Agent/Pipeline, not a Vault-specific concept). `list_templates()`
below now delegates to it rather than re-reading Template.json itself.

2026-08-28, layering correction (operator: "Managers understand
Entities, Data Access understands stores... I/O always happens in Data
Access"): the index-filtering config's raw file I/O moved out to
`data_access/vault_index_config.py` -- this Manager holds zero raw file
calls of its own now (the note-index rebuild already routed through
`vault_writer.py`, a real data_access module, from the start). The
Entities.md store went with the Entities plugin (Entities plan Phase 5).

2026-08-28, later same day: folded in `vault_search.py` too (browse/
tag-filter/note-detail/ranked-search/graph -- REQ-SB-02-US-01/ADR-026),
its only real caller (`vault_search_router.py`) migrated. It was
already built entirely on top of `get_index()` plus `vault_writer.py`
(a real data_access module) for on-demand body reads -- no raw I/O of
its own to retrofit, a pure logic fold.
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from app.business.core.templates.template import Template
from app.business.core.templates.template_manager import TemplateManager
from app.business.core.vault import snippets
from app.business.core.vault.vault import Vault
from app.config import settings
from app.data_access import vault_index_config as vault_index_config_data
from app.data_access import vault_writer
from app.business.core.vault import note_text
from app.obsidian.notes import long_path

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory note index (folded in from vault_indexing.py) -- module-level
# singleton state, see the module docstring for why.
# ---------------------------------------------------------------------------

class NoteChangedError(Exception):
    """Somebody else wrote this note while it was open. The vault has other
    writers -- the agents -- so this is an ordinary event, not a fault."""


class NoteNotEditableError(Exception):
    """What the API shows for this note is not what is in the file."""


_vault_index: dict[str, dict] = {}
# Every indexed note, including ones whose name another note also has. The map
# above can only hold one per name; this is what "all the notes" means.
_vault_entries: list[dict] = []
# Every `<namespace>/<slug>` tag the vault holds -> the entries carrying it.
# A projection of the list above, rebound in the same pass (ADR-037) -- see
# _build_tag_index for the one tag-shape rule and why this is not an artifact.
_vault_tag_index: dict[str, list[dict]] = {}
_last_rebuilt_at: str | None = None

#: Whether a rebuild has been queued and not yet reported as finished.
#:
#: The index lives in memory, so a restarted process has none until the boot
#: rebuild lands -- and for those seconds every reader asked "is there an
#: index?" and was told no. The Vault screen rendered that as "Nothing indexed
#: yet", which is not slow, it is WRONG, and a note opened in that window
#: answered 404 "no indexed note found" for a note that plainly exists
#: (operator, 2026-10-24, twice). "Not finished" and "nothing there" are
#: different answers and the API has to be able to give both.
#:
#: Owned by whoever SCHEDULES the rebuild, deliberately, rather than set and
#: cleared inside `rebuild_index`: `REQ-SB-95-US-05-AC-04` reads this module's
#: source and requires the tag projection to be rebound directly in that
#: function's body, beside `_vault_entries`. Wrapping the body in a
#: try/finally moved those statements a level deeper and broke the guard that
#: stops the projection drifting from the notes it groups (`BUG-082`).
_rebuild_scheduled: bool = False


def mark_rebuild_scheduled() -> None:
    """Called where a rebuild is QUEUED, synchronously, before the thread it
    will run on gets a turn. Without it the first request after a restart can
    arrive in the gap between scheduling and starting, and be told that
    nothing is building either."""
    global _rebuild_scheduled
    _rebuild_scheduled = True


def mark_rebuild_finished() -> None:
    """Called when that queued rebuild settles, successfully or not. A rebuild
    that raised would otherwise leave every reader waiting forever for an
    index that is never coming."""
    global _rebuild_scheduled
    _rebuild_scheduled = False

_TAG_NAMESPACE_SEPARATOR = "/"


def _frontmatter_wikilink_targets(frontmatter: dict) -> list[str]:
    """`REQ-SB-73-US-01-T01` (`ADR-054` Decision 5) -- generic scan of every
    frontmatter STRING (and list-of-string) value for `[[...]]` targets, via
    the SAME `vault_writer.extract_wikilink_targets` primitive the body scan
    already uses (a pure regex match over any string, agnostic to origin) --
    never a `thread:`-named special case, so any future frontmatter-wikilink
    field is picked up for free."""
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
    already use). `outgoing_wikilinks` scans BOTH the body text and
    every frontmatter string/string-list value (`REQ-SB-73-US-01-T01`,
    `ADR-054` Decision 5)."""
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


def _build_tag_index(entries: list[dict]) -> dict[str, list[dict]]:
    """Every `<namespace>/<slug>` tag in the vault -> the entries carrying it.

    One extra pass over entries already in memory (`ADR-037`): no second disk
    walk, no note re-read, and no stored `Index` artifact. A stored copy would
    need a refresh trigger of its own, and the missing one is how the backend
    served a three-day-stale vault with 250 notes invisible (`BUG-082`). Built
    from the entries list rather than the by-stem map, which cannot hold the
    notes it loses to a shared name (`BUG-076`).

    **The one rule for tag shape, stated rather than left to fall out of the
    code:** a tag is a key when it HAS a namespace -- a separator with text on
    both sides. The namespace is the text before the FIRST separator, the slug
    is everything after it, so a deeper tag (`a/b/c`) keeps its own full name
    as a key instead of being discarded: nothing that carries a namespace is
    ever dropped. A tag with no separator (`urgent`) has no namespace, is not
    an entity tag, and so is not a key -- whole-vault tag counts are what
    `list_tags()` already answers.

    No namespace is matched against any list. A framework that filtered to the
    prefixes it had heard of would be naming a plugin's vocabulary
    (`ADR-022`/`ADR-035`), and this index has to hold on an install with no
    plugins at all. Registration turns a NAME into a tag; it never populates
    this index.
    """
    tag_index: dict[str, list[dict]] = {}
    for entry in entries:
        keys_this_note_already_has: set[str] = set()
        for tag in entry["tags"]:
            if not isinstance(tag, str) or tag in keys_this_note_already_has:
                continue
            namespace, separator, slug = tag.partition(_TAG_NAMESPACE_SEPARATOR)
            if not separator or not namespace or not slug:
                continue
            keys_this_note_already_has.add(tag)
            tag_index.setdefault(tag, []).append(entry)
    return tag_index


# ---------------------------------------------------------------------------
# Browse/search (folded in from vault_search.py) -- pure functions over an
# already-fetched index dict, no `self` needed.
# ---------------------------------------------------------------------------

_DEFAULT_PAGE_SIZE = 20
_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Title/tags outweigh an incidental body mention (ADR-026, the story's
# own worked example) -- tuning constants, adjustable without a
# superseding ADR.
_FIELD_WEIGHTS = {"title": 3.0, "tags": 2.0, "body": 1.0}
_BM25_K1 = 1.5
_BM25_B = 0.75
_DEFAULT_SEARCH_LIMIT = 20


def _title_for(entry: dict) -> str:
    """subject when present (Email/Meeting notes); otherwise the note's
    own filename stem -- Customer/Person/Partner hub notes carry no
    "subject" frontmatter field at all."""
    return entry["frontmatter"].get("subject") or entry["stem"]


def _kind_for(entry: dict) -> str:
    return entry["frontmatter"].get("type", "Unknown")


def _carries_tag(entry: dict, tag: str) -> bool:
    """The tag itself, or anything under it. `customer` matches
    `customer/masdar`; `customer/mas` matches neither, because the boundary is
    a path separator and not a character count."""
    return any(existing == tag or existing.startswith(tag + "/") for existing in entry["tags"])


def _folder_of(entry: dict) -> str:
    """The note's folder, relative to the vault root, with forward slashes.

    Relative because the absolute path is this machine's business: it changes
    when the vault moves, and no screen should show it.
    """
    try:
        relative = Path(entry["path"]).resolve().relative_to(Path(settings.vault_path).resolve())
    except (ValueError, OSError, TypeError):
        return ""
    return relative.parent.as_posix().strip(".")


def _as_tree(counts: dict[str, int], separator: str) -> list[dict]:
    """`{"a": 3, "a/b": 2}` -> a nested list of `{path, name, count, children}`.

    Sorted by count then name at every level, like the tag chips were: the
    branch worth opening first is the one with the most in it.
    """
    children_by_parent: dict[str, list[str]] = {}
    for path in counts:
        parent = path.rsplit(separator, 1)[0] if separator in path else ""
        children_by_parent.setdefault(parent, []).append(path)

    def build(parent: str) -> list[dict]:
        return [
            {
                "path": path,
                "name": path.rsplit(separator, 1)[-1],
                "count": counts[path],
                "children": build(path),
            }
            for path in sorted(
                children_by_parent.get(parent, []), key=lambda path: (-counts[path], path)
            )
        ]

    return build("")


def _modified_at(entry: dict) -> float:
    """The note file's own modified time, or 0 for one that has gone missing
    since it was indexed -- which sorts it last rather than failing the whole
    listing for everything else."""
    try:
        return Path(entry["path"]).stat().st_mtime
    except OSError:
        return 0.0


def _modified_iso(entry: dict) -> str | None:
    """When the note file last changed, ISO-8601, or None for one that has
    gone missing since it was indexed. The file's own time, because a note's
    dates live in whatever frontmatter its Template defines and this is the
    only answer that exists for every note."""
    moment = _modified_at(entry)
    if moment <= 0:
        return None
    return datetime.fromtimestamp(moment, tz=timezone.utc).isoformat()


def _summary(entry: dict) -> dict:
    return {
        "stem": entry["stem"],
        "title": _title_for(entry),
        "kind": _kind_for(entry),
        "tags": entry["tags"],
    }


def _resolve_forward_links(entry: dict, index: dict[str, dict]) -> list[dict]:
    """entry["outgoing_wikilinks"] is deliberately RAW, unresolved target
    text -- resolution only happens here, at read time, against the
    target's own entry, applying the identical case-insensitive
    stem-matching rule the backlink-deriving rebuild pass uses. An
    unresolved target (a dangling link, or a manually-authored free-text
    wikilink) is simply omitted -- no crash, no fabricated entry."""
    stems_by_lower_stem = {stem.lower(): stem for stem in index}
    resolved = []
    seen_stems: set[str] = set()
    for target in entry["outgoing_wikilinks"]:
        matched_stem = stems_by_lower_stem.get(target.lower())
        if matched_stem is None or matched_stem == entry["stem"] or matched_stem in seen_stems:
            continue
        seen_stems.add(matched_stem)
        resolved.append(_summary(index[matched_stem]))
    return resolved


def _resolve_backlinks(entry: dict, index: dict[str, dict]) -> list[dict]:
    """entry["incoming_wikilinks"] is already a list of resolved source
    stems (rebuild_index's own backlink-inversion pass) -- a direct
    lookup, no re-matching needed."""
    return [_summary(index[stem]) for stem in entry["incoming_wikilinks"] if stem in index]


def _resolve_forward_link_stems(entry: dict, index: dict[str, dict]) -> list[str]:
    """Same case-insensitive stem-matching rule as _resolve_forward_links,
    factored out so get_graph() can emit {"source", "target"} edges
    without paying for a full _summary() resolve per target. Dangling/
    self targets are silently omitted -- identical posture to
    _resolve_forward_links, not a new rule."""
    stems_by_lower_stem = {stem.lower(): stem for stem in index}
    matched_stems = []
    for target in entry["outgoing_wikilinks"]:
        matched_stem = stems_by_lower_stem.get(target.lower())
        if matched_stem is None or matched_stem == entry["stem"]:
            continue
        matched_stems.append(matched_stem)
    return matched_stems


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _field_tokens(entry: dict, body_by_stem: dict[str, str]) -> dict[str, list[str]]:
    return {
        "title": _tokenize(_title_for(entry)),
        "tags": _tokenize(" ".join(entry["tags"])),
        "body": _tokenize(body_by_stem.get(entry["stem"], "")),
    }


def _bm25_term_score(term: str, doc_tokens: list[str], avg_len: float, doc_freq: int, total_docs: int) -> float:
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


def _is_preferred(candidate: dict, current: dict) -> bool:
    """Which of two notes sharing a name the by-stem map should hold.

    A note whose folder is named after it is that folder's subject -- the
    meeting, the thread, the customer. A note sitting inside someone else's
    folder (an invitation email under a Thread's `messages/`) is a part of it, so
    it loses. Ties break on depth then alphabetically, so the answer is stable
    across rebuilds rather than an accident of walk order."""
    def rank(entry: dict) -> tuple:
        path = Path(entry["path"])
        return (0 if path.parent.name == path.stem else 1, len(path.parts), str(path))

    return rank(candidate) < rank(current)


class VaultManager:
    def __init__(self) -> None:
        self._template_manager = TemplateManager()

    # -- Index (folded in from vault_indexing.py) ---------------------

    def rebuild_index(self) -> dict[str, dict]:
        """Full, idempotent rebuild (ADR-024) -- walks every real note
        under Work/, builds one entry per note, then a second pass
        inverts each note's outgoing wikilinks into every matched
        target's incoming_wikilinks list. Assembles a brand-new dict end
        to end, then atomically reassigns the module-level reference --
        a single-reference rebind is safe under CPython's GIL, no
        explicit lock needed.

        The tag-keyed projection is rebound here too, in the same
        assignment block and from the same `new_entries` (ADR-037), so it
        can never be newer or older than the notes it groups. That is the
        whole mechanism: there is no second refresh path to forget to
        call, no cron job of its own, and no artifact on disk."""
        global _vault_index, _vault_entries, _vault_tag_index, _last_rebuilt_at
        new_entries: list[dict] = []
        for path in vault_writer.list_all_note_paths():
            # One note that cannot be read -- moved by capture between the walk
            # and the read, held by OneDrive, not UTF-8 -- used to abort the
            # whole rebuild. At boot that left the index EMPTY until the next
            # cron refresh, up to 30 minutes, and every reader showed nothing:
            # My Day read "0 emails" with every email still on disk (`BUG-090`).
            try:
                new_entries.append(_build_entry(path))
            except (OSError, UnicodeDecodeError) as error:
                _logger.warning("vault index: skipped unreadable note %s (%s)", path, error)

        # Every note is kept in `new_entries`; the by-stem map holds one per name
        # (`BUG-076`). Obsidian allows the same name in different folders, and the
        # map used to keep whichever note was walked last -- a meeting and its own
        # invitation email share a name, so the meeting simply vanished from every
        # reader, My Day included. 100 notes across 19 names collide on the
        # reporting install.
        new_index: dict[str, dict] = {}
        for entry in new_entries:
            current = new_index.get(entry["stem"])
            if current is None or _is_preferred(entry, current):
                new_index[entry["stem"]] = entry

        stems_by_lower_stem = {stem.lower(): stem for stem in new_index}
        for entry in new_entries:
            for target in entry["outgoing_wikilinks"]:
                matched_stem = stems_by_lower_stem.get(target.lower())
                if matched_stem is None or matched_stem == entry["stem"]:
                    continue
                backlinks = new_index[matched_stem]["incoming_wikilinks"]
                if entry["stem"] not in backlinks:
                    backlinks.append(entry["stem"])

        new_tag_index = _build_tag_index(new_entries)

        _vault_index = new_index
        _vault_entries = new_entries
        _vault_tag_index = new_tag_index
        _last_rebuilt_at = datetime.now(timezone.utc).isoformat()
        return _vault_index

    def get_index(self) -> dict[str, dict]:
        """Every note by name -- ONE per name, so a lookup by stem (a wikilink
        target, a Cockpit subject in a URL) has a single answer.

        Where two notes share a name, the subject note wins: the one whose folder
        is named after it, then the shallowest path, then alphabetical -- always
        the same note across rebuilds, never "whichever was walked last"
        (`BUG-076`). **Counting or listing notes belongs in `get_entries()`**:
        this map cannot hold the ones it loses to a collision.

        Deliberately not a browse/search API itself (ADR-024's own Non-Goals
        boundary) -- `vault_search.py` builds that on top."""
        return _vault_index

    def get_entries(self) -> list[dict]:
        """Every indexed note, collisions included -- what to iterate over when
        the question is "all the notes" rather than "the note called X"."""
        return _vault_entries

    def get_entries_for_tag(self, tag: str) -> list[dict]:
        """Every note carrying one `<namespace>/<slug>` tag, in index order.

        The dict lookup `ADR-032` asked for, with no per-entity provisioning
        behind it: a brand-new entity is served the moment a note carrying its
        tag is indexed. An empty list for a tag no note carries -- an entity
        nothing has been written about yet is not an error."""
        return _vault_tag_index.get(tag, [])

    def get_tag_index_keys(self) -> list[str]:
        """Every `<namespace>/<slug>` tag the vault actually holds, sorted.

        Registered or not. Registration turns a NAME into a tag; it does not
        populate this index (`ADR-037`), so a key no namespace claims is kept
        here and can be named as unknown rather than silently dropped."""
        return sorted(_vault_tag_index)

    def resolve_wikilink_targets(self, targets: list[str]) -> dict[str, str]:
        """The targets that are real notes, as `<target as asked> -> <real stem>`.

        Matching is case-insensitive because that is how Obsidian resolves a
        `[[wikilink]]`, and what the vault browser has always done. A target that
        is not a note is simply absent: rendering it as a link would promise a
        note the vault does not have (`BUG-079`)."""
        by_lower = {stem.lower(): stem for stem in _vault_index}
        resolved = {}
        for target in targets:
            stem = by_lower.get(target.strip().lower())
            if stem is not None:
                resolved[target] = stem
        return resolved

    def is_rebuilding(self) -> bool:
        """Whether an index is on its way. Lets a caller say "still building"
        instead of "nothing here", which are opposite answers.

        False the moment there IS an index, whatever the flag says: a rebuild
        that finished has nothing left to wait for, so a caller that forgot to
        report it cannot strand the screen on a spinner."""
        return _rebuild_scheduled and _last_rebuilt_at is None

    def get_last_rebuilt_at(self) -> str | None:
        """ISO-8601 UTC timestamp of the most recent successful
        rebuild_index() call this process lifetime, or None if the
        index has never been built yet."""
        return _last_rebuilt_at

    def get_overview(self) -> Vault:
        """Settings > Vault > Overview -- per-top-level-Work-folder note
        counts, derived from the existing in-memory index rather than a
        fresh disk scan."""
        work_root = settings.vault_path / "Work"
        folder_counts: dict[str, int] = {}
        for entry in _vault_entries:
            try:
                relative = Path(entry["path"]).relative_to(work_root)
            except ValueError:
                continue
            top = relative.parts[0] if relative.parts else "(Work root)"
            folder_counts[top] = folder_counts.get(top, 0) + 1
        return Vault(
            total_notes=len(_vault_entries),
            last_rebuilt_at=_last_rebuilt_at,
            folder_counts=dict(sorted(folder_counts.items(), key=lambda kv: -kv[1])),
        )

    # -- Index-filtering config (delegates to data_access/vault_index_config.py) --

    def _load_index_config_raw(self) -> dict:
        data = vault_index_config_data.load_raw()
        if data is None:
            return {"folders": {}}
        data.setdefault("folders", {})
        return data

    def get_index_config(self) -> dict:
        """Every real top-level Work/ folder (from the same live
        folder_counts the Vault Overview already shows), each with its
        current included/excluded state -- True unless explicitly saved
        otherwise."""
        raw = self._load_index_config_raw()
        saved_folders = raw["folders"]
        real_folder_names = self.get_overview().folder_counts.keys()
        return {
            "folders": [
                {"name": name, "included": saved_folders.get(name, {}).get("included", True)}
                for name in sorted(real_folder_names)
            ],
        }

    def set_folder_included(self, folder_name: str, included: bool) -> dict:
        raw = self._load_index_config_raw()
        raw["folders"].setdefault(folder_name, {})["included"] = included
        vault_index_config_data.save_raw(raw)
        return self.get_index_config()

    # -- Templates (delegates to TemplateManager) ----------------------

    def list_templates(self) -> list[Template]:
        """Read-only listing of the Template.json files that already
        control app/vault/vault_manager.py's own (a different thing --
        see TemplateManager's own module docstring) real write behavior.
        Hand-edited JSON with zero UI today; this surfaces what exists
        without adding an edit path yet. Delegates to TemplateManager,
        the real owner of this data -- VaultManager doesn't re-read
        Template.json itself, same as SectionManager delegating to
        AgentManager for a Section's own Hub Agent."""
        return self._template_manager.get_all()

    def get_template_json(self, template_id: str) -> dict | None:
        return self._template_manager.read_json(template_id)

    def update_template(self, template_id: str, data: dict) -> Template:
        return self._template_manager.update(template_id, data)

    # -- Browse/search (folded in from vault_search.py) ----------------

    def list_notes(
        self,
        page: int = 1,
        page_size: int = _DEFAULT_PAGE_SIZE,
        tag: str | None = None,
        kind: str | None = None,
        sort: str = "name",
        folder: str | None = None,
    ) -> dict:
        """Browse all notes, or narrow by tag, kind and/or folder. An empty
        result (no notes at all, or a real filter with zero matches) returns
        "notes": [] honestly.

        `tag` matches the tag itself AND everything under it: this vault's
        tags are paths (`azure/services/compute`), 312 of them across 15
        top-level categories, so "show me azure" has to mean the branch and
        not one leaf nobody would guess the name of.

        `sort` is "name" (by stem, the one field every entry always has) or
        "recent", which is the file's own modified time: a note's dates live in
        whatever frontmatter its Template happens to define, so the filesystem
        is the only answer that exists for every note. It costs one stat per
        note and is therefore only paid when asked for.
        """
        entries = self._filtered_entries(tag=tag, kind=kind, folder=folder)
        if sort == "recent":
            entries.sort(key=lambda entry: (-_modified_at(entry), entry["stem"]))
        else:
            entries.sort(key=lambda entry: entry["stem"])

        total = len(entries)
        start = (page - 1) * page_size
        page_entries = entries[start:start + page_size]
        return {
            "total": total, "page": page, "page_size": page_size,
            # `modified_at` only here, never in `_summary`: it costs a stat per
            # note, and this is the one caller with a bounded page. The graph
            # asks for hundreds of summaries at a time and has no use for it.
            "notes": [
                {**_summary(entry), "modified_at": _modified_iso(entry)}
                for entry in page_entries
            ],
        }

    def _filtered_entries(
        self,
        tag: str | None = None,
        kind: str | None = None,
        folder: str | None = None,
    ) -> list[dict]:
        """The one place the three filters are applied, so the list, the graph
        and every count agree about what "filtered" means. Two screens deriving
        the same filter separately is how a count stops matching its own
        list."""
        entries = list(self.get_entries())
        if tag is not None:
            entries = [entry for entry in entries if _carries_tag(entry, tag)]
        if kind is not None:
            entries = [entry for entry in entries if _kind_for(entry) == kind]
        if folder is not None:
            entries = [entry for entry in entries if _folder_of(entry).startswith(folder)]
        return entries

    def list_tag_tree(self) -> dict:
        """Tags as the tree they already are, not 312 flat chips.

        Every tag in this vault is a path -- `customer/masdar`,
        `azure/services/compute` -- so a flat row of every one of them was a
        screenful of chips before the notes started. A category carries the
        count of everything beneath it, which is the number that makes a
        branch worth opening.
        """
        counts: dict[str, int] = {}
        for entry in self.get_entries():
            # A note tagged `azure/services/compute` counts once towards
            # `azure`, once towards `azure/services` and once towards the leaf.
            # Through a set, so a note carrying two tags in one branch is not
            # counted twice for their shared ancestor.
            for path in {
                "/".join(tag.split("/")[: depth + 1])
                for tag in entry["tags"]
                for depth in range(tag.count("/") + 1)
            }:
                counts[path] = counts.get(path, 0) + 1
        return {"tags": _as_tree(counts, separator="/")}

    def list_folders(self) -> dict:
        """The vault's own folder tree, with a count per folder.

        The other way people know where a note is: `Work/Customers/Masdar`
        says something no tag does, and an operator who filed it there looks
        for it there.
        """
        counts: dict[str, int] = {}
        for entry in self.get_entries():
            folder = _folder_of(entry)
            if not folder:
                continue
            segments = folder.split("/")
            for depth in range(len(segments)):
                path = "/".join(segments[: depth + 1])
                counts[path] = counts.get(path, 0) + 1
        return {"folders": _as_tree(counts, separator="/")}

    def list_kinds(self) -> dict:
        """The note types that actually exist in the index, with counts --
        the same shape as `list_tags`, and for the same reason: the browse
        screen shows a kind on every row, so it should be able to filter on
        one, and the only honest list of kinds is the one the vault has."""
        counts: dict[str, int] = {}
        for entry in self.get_entries():
            kind = _kind_for(entry)
            counts[kind] = counts.get(kind, 0) + 1
        kinds = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return {"kinds": [{"kind": kind, "count": count} for kind, count in kinds]}

    def list_tags(self) -> dict:
        """The real, current list of tags that actually exist in the
        index (with counts), sorted by count descending then tag name."""
        counts: dict[str, int] = {}
        for entry in self.get_entries():
            for tag in entry["tags"]:
                counts[tag] = counts.get(tag, 0) + 1
        tags = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return {"tags": [{"tag": tag, "count": count} for tag, count in tags]}

    def list_scope_suggestions(self) -> dict:
        """Composes list_tags() with vault_writer.list_known_kinds() into
        one combined, un-merged {"tags", "folders"} payload for the
        Agent Settings Vault Scope field's own typeahead. No q= filter --
        always the full current snapshot; keystroke filtering is a
        frontend concern."""
        tags = self.list_tags()["tags"]
        folders = vault_writer.list_known_kinds()
        return {"tags": tags, "folders": folders}

    def get_export_tree(self) -> dict:
        """Settings -> Vault -> Export Data's own real, genuinely
        UNFILTERED filesystem walk of settings.vault_path
        (`REQ-SB-86-US-01-T01`) -- deliberately NOT built on
        get_index()/vault_writer.list_all_note_paths(), which excludes
        OKF-reserved files (index.md/log.md/captures.md) and any
        `_`-prefixed folder (this project's own archive convention). A
        real folder share needs the whole real directory, so this reads
        straight off disk every call -- no caching, unlike the note
        index's own rebuild-once-read-many-times shape (see this
        Manager's own module docstring)."""
        root = settings.vault_path
        return {"root": root.as_posix(), "tree": self._walk_export_tree(root, root)}

    def _walk_export_tree(self, current_dir: Path, root: Path) -> dict:
        # `is_dir()` is computed once per child and reused for both the
        # sort key and the type decision -- a real, host-observed Windows
        # MAX_PATH edge case (paths over ~260 chars) makes `is_file()`
        # and `is_dir()` disagree if called independently, which
        # previously desynced the display order from the actual "file"
        # classification for a handful of deeply-nested real notes.
        children = []
        # Dot-prefixed folders (.git, .obsidian, .second-brain, ...) are
        # real tooling/system directories, never shareable vault content --
        # excluded here, unlike the `_`-prefixed archive convention above
        # (real user content this endpoint deliberately DOES include).
        all_entries = [(child, child.is_dir()) for child in current_dir.iterdir()]
        entries = sorted(
            (pair for pair in all_entries if not (pair[1] and pair[0].name.startswith("."))),
            key=lambda pair: (not pair[1], pair[0].name.lower()),
        )
        for child, child_is_dir in entries:
            relative_path = child.relative_to(root).as_posix()
            if child_is_dir:
                children.append(self._walk_export_tree(child, root))
            else:
                children.append({"name": child.name, "type": "file", "path": relative_path})
        name = current_dir.name if current_dir != root else root.name
        return {
            "name": name,
            "type": "folder",
            "path": "" if current_dir == root else current_dir.relative_to(root).as_posix(),
            "children": children,
        }

    def get_graph(
        self,
        tag: str | None = None,
        kind: str | None = None,
        folder: str | None = None,
        limit: int | None = None,
    ) -> dict:
        """The knowledge graph's {"nodes", "edges"} snapshot, for a SCOPE.

        Unscoped it is the whole vault, which is what it always was and what
        made the screen unusable here: 4,300 nodes drawn at once is a cloud,
        not a graph (operator, 2026-10-24: "The Vault Loads alot of nodes
        Which make it not looking good"). The scope is the same tag / kind /
        folder the browse list uses, so the graph shows what the screen is
        already about rather than a separate world.

        `limit` caps the nodes returned and reports what was left out, so a
        branch with a thousand notes degrades to "the thousand are there, here
        are the most connected" instead of hanging the browser. The edges are
        resolved against the WHOLE index first and then narrowed, so a link
        between two notes in scope survives even when the path between them
        is not.
        """
        index = self.get_index()
        entries = self._filtered_entries(tag=tag, kind=kind, folder=folder)
        in_scope = {entry["stem"] for entry in entries}

        edges = [
            {"source": entry["stem"], "target": matched_stem}
            for entry in index.values()
            if entry["stem"] in in_scope
            for matched_stem in _resolve_forward_link_stems(entry, index)
            if matched_stem in in_scope
        ]

        total = len(entries)
        truncated = False
        if limit is not None and total > limit:
            # The most connected survive: an isolated note tells you nothing
            # about a graph, and the hubs are what a reader is looking for.
            degree: dict[str, int] = {}
            for edge in edges:
                degree[edge["source"]] = degree.get(edge["source"], 0) + 1
                degree[edge["target"]] = degree.get(edge["target"], 0) + 1
            entries = sorted(entries, key=lambda entry: (-degree.get(entry["stem"], 0), entry["stem"]))[:limit]
            kept = {entry["stem"] for entry in entries}
            edges = [edge for edge in edges if edge["source"] in kept and edge["target"] in kept]
            truncated = True

        return {
            "nodes": [_summary(entry) for entry in entries],
            "edges": edges,
            "total": total,
            "truncated": truncated,
        }

    def get_note_detail(self, stem: str) -> dict | None:
        """One note's frontmatter/tags/real body text plus its resolved
        forward-link/backlink lists. None for an unknown stem. `body` is
        read fresh from disk (the index's own entries never store it)."""
        index = self.get_index()
        entry = index.get(stem)
        if entry is None:
            return None
        frontmatter, body = vault_writer.read_note(Path(entry["path"]))
        # A captured email's body is the original HTML, kept faithful on disk and
        # converted on the way out -- which nothing did, so every note view showed
        # the markup (`BUG-081`). The note on disk is untouched.
        kind = note_text.body_kind(frontmatter, body)
        return {
            "stem": entry["stem"], "title": _title_for(entry), "kind": _kind_for(entry),
            "frontmatter": entry["frontmatter"], "tags": entry["tags"],
            "body": note_text.readable_body(frontmatter, body), "body_type": kind,
            # What the editor holds and sends back, so a save can tell "nobody
            # touched this" from "an agent rewrote it while you typed".
            "version": vault_writer.note_version(Path(entry["path"])),
            # An HTML body is shown converted, so what is on screen is not what
            # is in the file and must not be written back over it.
            "editable": kind != "html",
            "forward_links": _resolve_forward_links(entry, index),
            "backlinks": _resolve_backlinks(entry, index),
        }

    def update_note_body(self, stem: str, body: str, expected_version: str) -> dict:
        """Writes a note's body back to its own file, if nobody moved it first.

        **The vault has other writers.** Hermes captures and enriches these
        same notes continuously -- on 2026-10-24 it wrote 230 of them in one
        burst -- so a save that simply overwrote would destroy an agent's
        enrichment, or be destroyed by it, with nothing on screen either way.
        The caller sends the version it opened, and a file that has moved on
        since refuses the save and keeps the operator's text (`NoteChangedError`).

        **An HTML note is not editable here.** A captured email keeps the
        original HTML on disk and the API converts it to readable markdown on
        the way out, so the text on screen is not the text in the file:
        writing it back would replace the original with a rendering of itself.
        """
        entry = self.get_index().get(stem)
        if entry is None:
            return {"ok": False, "detail": f"No indexed note with stem '{stem}'"}
        path = Path(entry["path"])

        frontmatter, current_body = vault_writer.read_note(path)
        if note_text.body_kind(frontmatter, current_body) == "html":
            raise NoteNotEditableError(
                "This note's body is the original HTML of a captured message. What you see "
                "is a rendering of it, so saving would replace the original with the "
                "rendering. Edit it in the vault if you need to change it."
            )

        actual_version = vault_writer.note_version(path)
        if actual_version != expected_version:
            raise NoteChangedError(
                "This note changed on disk since you opened it -- an agent writes these "
                "files too. Nothing was saved, and your text is still here. Reload to see "
                "what it says now."
            )

        vault_writer.replace_note_body(path, body)

        # The note's OWN entry is rebuilt at once, so its tags and the links it
        # points at are right immediately. Backlinks on other notes still come
        # from the full rebuild: inverting every note's wikilinks on each
        # keystroke-save would read the whole vault to record one new link.
        rebuilt = _build_entry(path)
        _vault_index[stem] = rebuilt
        for position, existing in enumerate(_vault_entries):
            if existing["path"] == entry["path"]:
                _vault_entries[position] = rebuilt
                break
        return {"ok": True, "version": vault_writer.note_version(path)}

    def resolve_asset_path(self, stem: str, filename: str) -> Path | None:
        """Resolves a real, co-located asset file (image, etc.) sitting
        next to a note's own .md on disk -- a File note's own Obsidian-
        style `![[slide-14.png]]` embeds resolve exactly this way: capture
        writes the note AND its referenced images into the SAME folder.
        None for an unknown stem, a filename that isn't a real file in
        that EXACT folder, or (defense in depth against a crafted
        `filename` path segment) one that would resolve outside the
        note's own folder -- never serves an arbitrary vault path, only a
        real sibling of a real, already-indexed note."""
        index = self.get_index()
        entry = index.get(stem)
        if entry is None:
            return None
        note_dir = Path(entry["path"]).resolve().parent
        candidate = (note_dir / filename).resolve()
        # A captured attachment's folder repeats the attachment's own name, so a
        # long subject line puts the real file past Windows' 260-character limit,
        # where `is_file()` answers False instead of raising -- the file would
        # simply 404 (`BUG-077`'s shape, on the read side of an asset).
        if candidate.parent != note_dir or not Path(long_path(candidate)).is_file():
            return None
        return candidate

    def search(self, query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> dict:
        """Field-weighted BM25-style ranked search over every currently-
        indexed note's title/tags/body (ADR-026). Body text is read
        fresh from disk per candidate note; title/tags come directly
        from the already-in-memory index. An empty results list for a
        query matching nothing is an honest empty state, not a distinct
        code path."""
        query_tokens = _tokenize(query)
        index = self.get_index()
        entries = list(self.get_entries())
        if not query_tokens or not entries:
            return {"query": query, "results": []}

        body_by_stem = {entry["stem"]: vault_writer.read_note(Path(entry["path"]))[1] for entry in entries}
        field_tokens_by_stem = {entry["stem"]: _field_tokens(entry, body_by_stem) for entry in entries}

        scores: dict[str, float] = {stem: 0.0 for stem in field_tokens_by_stem}
        for field, weight in _FIELD_WEIGHTS.items():
            field_token_lists = {stem: tokens[field] for stem, tokens in field_tokens_by_stem.items()}
            total_docs = len(field_token_lists)
            avg_len = (sum(len(tokens) for tokens in field_token_lists.values()) / total_docs) or 1
            for term in set(query_tokens):
                doc_freq = sum(1 for tokens in field_token_lists.values() if term in tokens)
                for stem, tokens in field_token_lists.items():
                    scores[stem] += weight * _bm25_term_score(term, tokens, avg_len, doc_freq, total_docs)

        ranked_stems = sorted(
            (stem for stem, score in scores.items() if score > 0),
            key=lambda stem: (-scores[stem], stem),
        )[:limit]
        results = [
            {
                **_summary(index[stem]),
                "rank": rank,
                "score": round(scores[stem], 4),
                # Free here: every body was already read above to score it.
                "snippet": snippets.make_snippet(body_by_stem[stem], query),
            }
            for rank, stem in enumerate(ranked_stems, start=1)
        ]
        return {"query": query, "results": results}
