"""VaultManager -- the sole gateway onto Vault data (mirrors Section/
Agent/Pipeline Manager's own "one real gateway" rule), folding in and
retiring four previously-separate business modules that had no single
owning door: `vault_indexing.py` (the in-memory note index -- rebuild/
read/overview), `vault_index_config.py` (which top-level Work/ folders
the structural indexer walks), `vault_templates.py` (read-only Template
listing), and `vault_entities.py` (Customer/Partner discovery CRUD).

`Vault` (vault.py) is a genuine singleton -- there is exactly one vault
-- unlike Section/Agent/Pipeline's own real Array<Entity> shape,
`core/__init__.py`'s own stated convention. Forcing a `get_all() ->
list[Vault]` wrapper around a singleton would be artificial busywork
with no real caller, so this Manager exposes `get_overview() -> Vault`
instead, and its other three responsibilities (index/config/templates/
entities) as their own dict-returning methods -- a deliberate,
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
Access"): the index-filtering config and Entities.md's own raw file I/O
moved out to `data_access/vault_index_config.py`/`data_access/
entities.py` -- this Manager holds zero raw file calls of its own now
(the note-index rebuild already routed through `vault_writer.py`, a
real data_access module, from the start). Only the PARSE/RENDER of
Entities.md's own `### <heading>` format stays here -- that's business
shaping of the store's raw text, not I/O.

2026-08-28, later same day: folded in `vault_search.py` too (browse/
tag-filter/note-detail/ranked-search/graph -- REQ-SB-02-US-01/ADR-026),
its only real caller (`vault_search_router.py`) migrated. It was
already built entirely on top of `get_index()` plus `vault_writer.py`
(a real data_access module) for on-demand body reads -- no raw I/O of
its own to retrofit, a pure logic fold.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path

from app.business.core.templates.template import Template
from app.business.core.templates.template_manager import TemplateManager
from app.business.core.vault.vault import Vault
from app.config import settings
from app.data_access import entities as entities_data
from app.data_access import vault_index_config as vault_index_config_data
from app.data_access import vault_writer

# ---------------------------------------------------------------------------
# In-memory note index (folded in from vault_indexing.py) -- module-level
# singleton state, see the module docstring for why.
# ---------------------------------------------------------------------------

_vault_index: dict[str, dict] = {}
_last_rebuilt_at: str | None = None


class EntityNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"No entity named {name!r}")
        self.name = name


class DuplicateEntityError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"An entity named {name!r} already exists")
        self.name = name


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
        explicit lock needed."""
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

    def get_index(self) -> dict[str, dict]:
        """Plain whole-dict accessor -- no filter/query parameters.
        Deliberately not a browse/search API itself (ADR-024's own
        Non-Goals boundary) -- `vault_search.py` builds that on top."""
        return _vault_index

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
        for entry in _vault_index.values():
            try:
                relative = Path(entry["path"]).relative_to(work_root)
            except ValueError:
                continue
            top = relative.parts[0] if relative.parts else "(Work root)"
            folder_counts[top] = folder_counts.get(top, 0) + 1
        return Vault(
            total_notes=len(_vault_index),
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

    # -- Entities (folded in from vault_entities.py) -------------------

    _ENTITY_KNOWN_FIELDS = {"Company Name", "Aliases", "Affiliate of", "Created", "Ignore", "Domain", "Deleted"}

    def _parse_entities(self, content: str) -> list[dict]:
        section = None
        entries: list[dict] = []
        current: dict | None = None
        for line in content.splitlines():
            if line.startswith("## Companies"):
                section = "customer"
                continue
            if line.startswith("## Partners"):
                section = "partner"
                continue
            if line.startswith("### "):
                if current is not None:
                    entries.append(current)
                current = {"section": section, "heading": line[4:].strip(), "fields": {}}
                continue
            stripped = line.strip()
            if current is not None and stripped and ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                if key in self._ENTITY_KNOWN_FIELDS:
                    current["fields"][key] = value.strip()
        if current is not None:
            entries.append(current)
        return entries

    def _render_entity_entry(self, lines: list[str], entry: dict) -> None:
        f = entry["fields"]
        lines.append(f"### {entry['heading']}")
        lines.append("")
        lines.append(f"\tCompany Name: {f.get('Company Name', '')}")
        lines.append("")
        lines.append(f"\tAliases: {f.get('Aliases', '')}")
        lines.append("")
        lines.append(f"\tAffiliate of: {f.get('Affiliate of', '')}")
        lines.append("")
        lines.append(f"\tCreated: {f.get('Created', 'No')}")
        lines.append("")
        lines.append(f"\tIgnore: {f.get('Ignore', 'No')}")
        lines.append("")
        lines.append(f"\tDomain: {f.get('Domain', '')}")
        lines.append("")
        # A real hard-delete removes the row's own Domain from the
        # "already tracked" set find_new_entities.py checks before
        # appending a new entry -- so a noise domain (SharePoint, Teams
        # notification senders) that gets deleted just gets rediscovered
        # on the next scan. Deleted: Yes keeps the row (and its Domain)
        # in the file instead -- delete_entity() below sets this rather
        # than removing the entry.
        lines.append(f"\tDeleted: {f.get('Deleted', 'No')}")
        lines.append("")
        lines.append("")

    def _render_entities(self, entries: list[dict]) -> str:
        lines = [
            "# Entities",
            "",
            "Step 1 of the company/partner discovery sequence -- mechanical,",
            "domain-based grouping only, no LLM, no judgment about which of",
            "these are real Customers vs. Partners vs. noise.",
            "",
            "**Edit this file by hand.** `Created`/`Ignore` are Yes/No flags a",
            "later pipeline reads -- set `Ignore: Yes` instead of deleting an",
            "entry (a notification sender, a one-off vendor -- not a real",
            "business relationship); leave `Created: No` until that later,",
            "separate pipeline has actually made the hub note for it. Use",
            "`Aliases` to merge a duplicate that slipped through under a",
            "different domain (rare -- domain grouping already prevents most",
            "of this). Move real partners into `## Partners` below.",
            "",
            "## Companies",
            "",
        ]
        for entry in entries:
            if entry["section"] != "customer":
                continue
            self._render_entity_entry(lines, entry)
        lines.append("## Partners")
        lines.append("")
        for entry in entries:
            if entry["section"] != "partner":
                continue
            self._render_entity_entry(lines, entry)
        return "\n".join(lines)

    def _load_entities(self) -> list[dict]:
        raw = entities_data.read_raw()
        if raw is None:
            return []
        return self._parse_entities(raw)

    def _save_entities(self, entries: list[dict]) -> None:
        entities_data.write_raw(self._render_entities(entries))

    def _entity_to_public(self, entry: dict) -> dict:
        f = entry["fields"]
        return {
            "name": f.get("Company Name") or entry["heading"],
            "section": entry["section"],
            "aliases": f.get("Aliases", ""),
            "affiliate_of": f.get("Affiliate of", ""),
            "created": f.get("Created", "No") == "Yes",
            "ignore": f.get("Ignore", "No") == "Yes",
            "domain": f.get("Domain", ""),
        }

    def _entity_is_deleted(self, entry: dict) -> bool:
        return entry["fields"].get("Deleted", "No") == "Yes"

    def _find_entity(self, entries: list[dict], name: str) -> dict | None:
        key = name.strip().lower()
        for entry in entries:
            entry_name = (entry["fields"].get("Company Name") or entry["heading"]).strip().lower()
            if entry_name == key:
                return entry
        return None

    def list_entities(self) -> list[dict]:
        # Soft-deleted rows stay in the file (see delete_entity()) but
        # must never surface in the UI.
        return [self._entity_to_public(entry) for entry in self._load_entities() if not self._entity_is_deleted(entry)]

    def create_entity(
        self, name: str, section: str, domain: str = "", aliases: str = "", affiliate_of: str = "",
    ) -> dict:
        if section not in ("customer", "partner"):
            raise ValueError(f"section must be 'customer' or 'partner', got {section!r}")
        entries = self._load_entities()
        if self._find_entity(entries, name) is not None:
            raise DuplicateEntityError(name)
        entry = {
            "section": section,
            "heading": name.strip(),
            "fields": {
                "Company Name": name.strip(),
                "Aliases": aliases,
                "Affiliate of": affiliate_of,
                "Created": "No",
                "Ignore": "No",
                "Domain": domain,
            },
        }
        entries.append(entry)
        self._save_entities(entries)
        return self._entity_to_public(entry)

    def update_entity(self, name: str, patch: dict) -> dict:
        entries = self._load_entities()
        target = self._find_entity(entries, name)
        if target is None:
            raise EntityNotFoundError(name)
        fields = target["fields"]

        if "name" in patch:
            new_name = patch["name"].strip()
            if new_name and new_name.lower() != (fields.get("Company Name") or target["heading"]).strip().lower():
                if self._find_entity(entries, new_name) is not None:
                    raise DuplicateEntityError(new_name)
                target["heading"] = new_name
                fields["Company Name"] = new_name
        if "section" in patch and patch["section"] in ("customer", "partner"):
            target["section"] = patch["section"]
        if "aliases" in patch:
            fields["Aliases"] = patch["aliases"]
        if "affiliate_of" in patch:
            fields["Affiliate of"] = patch["affiliate_of"]
        if "domain" in patch:
            fields["Domain"] = patch["domain"]
        if "ignore" in patch:
            fields["Ignore"] = "Yes" if patch["ignore"] else "No"

        self._save_entities(entries)
        return self._entity_to_public(target)

    def delete_entity(self, name: str) -> None:
        """Soft delete -- sets Deleted: Yes (and Ignore: Yes, belt-and-
        suspenders for any Hermes script instance that hasn't been
        redeployed with the Deleted field yet) rather than removing the
        row. list_entities() filters Deleted: Yes rows out, so this is
        invisible in the UI despite staying on disk."""
        entries = self._load_entities()
        target = self._find_entity(entries, name)
        if target is None:
            raise EntityNotFoundError(name)
        target["fields"]["Deleted"] = "Yes"
        target["fields"]["Ignore"] = "Yes"
        self._save_entities(entries)

    # -- Browse/search (folded in from vault_search.py) ----------------

    def list_notes(self, page: int = 1, page_size: int = _DEFAULT_PAGE_SIZE, tag: str | None = None) -> dict:
        """Browse all notes, or narrow to one exact tag (case-sensitive
        match against the tag strings this project's own capture
        pipelines already write, e.g. "customer/masdar", "kind/email").
        Sorted by stem -- the one field every entry always has. An empty
        result (no notes at all, or a real tag with zero matches)
        returns "notes": [] honestly."""
        entries = list(self.get_index().values())
        if tag is not None:
            entries = [entry for entry in entries if tag in entry["tags"]]
        entries.sort(key=lambda entry: entry["stem"])

        total = len(entries)
        start = (page - 1) * page_size
        page_entries = entries[start:start + page_size]
        return {
            "total": total, "page": page, "page_size": page_size,
            "notes": [_summary(entry) for entry in page_entries],
        }

    def list_tags(self) -> dict:
        """The real, current list of tags that actually exist in the
        index (with counts), sorted by count descending then tag name."""
        counts: dict[str, int] = {}
        for entry in self.get_index().values():
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

    def get_graph(self) -> dict:
        """The Vault knowledge graph screen's own {"nodes", "edges"}
        snapshot, zero new indexing/caching. Nodes reuse _summary()
        verbatim; edges reuse the same case-insensitive stem-matching
        rule forward-link resolution already applies, dangling/self
        targets silently omitted. No pagination/filter params -- kind-
        filtering and name search are the frontend's own client-side
        concern over this one fetched snapshot."""
        index = self.get_index()
        nodes = [_summary(entry) for entry in index.values()]
        edges = [
            {"source": entry["stem"], "target": matched_stem}
            for entry in index.values()
            for matched_stem in _resolve_forward_link_stems(entry, index)
        ]
        return {"nodes": nodes, "edges": edges}

    def get_note_detail(self, stem: str) -> dict | None:
        """One note's frontmatter/tags/real body text plus its resolved
        forward-link/backlink lists. None for an unknown stem. `body` is
        read fresh from disk (the index's own entries never store it)."""
        index = self.get_index()
        entry = index.get(stem)
        if entry is None:
            return None
        body = vault_writer.read_note(Path(entry["path"]))[1]
        return {
            "stem": entry["stem"], "title": _title_for(entry), "kind": _kind_for(entry),
            "frontmatter": entry["frontmatter"], "tags": entry["tags"], "body": body,
            "forward_links": _resolve_forward_links(entry, index),
            "backlinks": _resolve_backlinks(entry, index),
        }

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
        if candidate.parent != note_dir or not candidate.is_file():
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
        entries = list(index.values())
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
            {**_summary(index[stem]), "rank": rank, "score": round(scores[stem], 4)}
            for rank, stem in enumerate(ranked_stems, start=1)
        ]
        return {"query": query, "results": results}
