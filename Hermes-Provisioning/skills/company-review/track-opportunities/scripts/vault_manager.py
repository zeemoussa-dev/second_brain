"""vault_manager.py -- the one real, template-driven vault write/read
engine (Implementation/Plans/2026-08-25-vault-writer-standardization.md,
Implementation/Plans/2026-08-30-vault-manager-template-trees.md).

Replaces N per-Skill hand-written writer scripts (azure-kb-writer,
compass-kb-writer, research-kb-writer, capture-notes, capture-files,
track-opportunities, summarize-and-tag-*) with ONE canonical file. Read
directly against those real scripts (2026-08-25): the same low-level
primitives (slugify, frontmatter format/parse, find-a-##Header/replace-
its-region, unique-path collision avoidance) were independently
reimplemented, with real drift, in at least four of them. This file is
that primitive set, written once.

Deployment model (operator, 2026-08-25): this file is standalone (stdlib
only, no Second Brain backend dependency -- a vault-writing Skill must
keep working even if the backend is down) and gets PHYSICALLY COPIED into
whichever Skill's own scripts/ folder needs it, same "prepare here, apply
to a real Hermes install" workflow this repo already uses for everything
else under Hermes-Provisioning/. Editing the engine happens in exactly
ONE place (this file, then re-copy); extending what it can write happens
by adding a Template.json, never by writing a new script ("we don't need
to edit 2000 places, max is 2" -- operator, 2026-08-25).

Templates live in the SAME data/ tree the RegistryLoader already reads
(REQ-SB-80): <vault>/.second-brain/data/Templates/<template_id>/
Template.json -- so a NEW Section/note-type is a new Template.json, never
new code. Template.json v2 (2026-08-30-vault-manager-template-trees.md)
splits a template into two layers -- a real, deliberate reframe: "Template
is not just a file, Sometimes actually most of the time it should be the
full Structure Parameterized" (operator, 2026-08-30). Top level describes
the RECORD as a whole: `identity.strategy` (how an existing record is
looked up -- "id" today; "tag"/"filename" strategies land when Person/
Customer actually need them, not built yet), `on_missing`,
`allow_create_folder` (can this record's own containing folder be
auto-vivified, or is that an error -- a Thread's messages/ folder not
existing yet is normal; a Customer's own folder not existing is a bug,
not a state to paper over). `root` is today's entire old flat schema,
unchanged in substance, just nested one level: `type`, `own_folder`,
`plain_filename`, `on_existing_title`, `frontmatter_defaults`, `sections`
(per-section write access -- machine vs. a human-owned section no
automated call may ever touch). `root` is a single md node for every real
template today; fixed multi-node children (OKF: index/slug/log/captures)
and a dynamic child slot (Thread's messages/) are a real, later extension
of this same shape -- not built here, nothing today needs them yet.

A template may also declare `parent` -- the external-required-parent
link (Opportunity -> Customer is the first real one, 2026-08-30):
`{"note_name": str, "match_fields": [str, ...], "alias_field": str?,
"frontmatter_field": str, "link_back_section": str?}`. `create()` then
REQUIRES a `parent_value`, resolves it via `resolve_parent()` against
the declared fields (case-insensitive), and refuses (a real
VaultManagerError, before anything is written) if no match exists --
never fabricates the parent. `frontmatter_field` names where the
resolved parent's own filename stem lands in the new child's own
frontmatter; `link_back_section`, if declared, idempotently accumulates
a wikilink to the new child into that section on the PARENT note
itself.

Real path convention (operator's own explicit shape, 2026-08-25):
    Notes/<note_name>/<YYYY-MM-DD>-<Title>.md
    Notes/<note_name>/<any other real file attached alongside it>

Identity: `id` in frontmatter is the real, stable key (a caller-supplied
external id, e.g. a calendar event id, or an auto-generated uuid4 if the
caller doesn't have one of its own) -- renaming a note is just `update
(id, title=...)`, nothing has to move, no backlink breaks. `id` is a NEW
field no existing content has yet, so `find` also supports `filename`/
`folder` lookup, which work against every note that already exists today
with zero backfill required.

CLI (one process per call, matching every existing Skill script's own
`--vault-path`/`--input-file` JSON-scratch-file convention):

    python vault_manager.py find --vault-path P --template-id T \\
        --by id|filename|folder --value X
    python vault_manager.py create --vault-path P --template-id T --input-file F
        F: {"id": str?, "title": str,
            # required UNLESS this template declares "parent" -- then
            # auto-derived from the resolved parent + parent.child_subpath
            # (2026-08-30) so the caller never has to compute it by hand.
            "note_name": str?,
            "frontmatter": {...}?, "sections": {"Summary": "...", ...}?,
            # required iff this template declares "parent" -- the value
            # to resolve an already-existing parent record by (e.g. a
            # Customer's own name, for an Opportunity); never fabricated.
            "parent_value": str?}
    python vault_manager.py update --vault-path P --template-id T --id X --input-file F
        F: {"title": str?, "frontmatter": {...}?}
    python vault_manager.py get-section --vault-path P --template-id T --id X --section NAME
    python vault_manager.py modify-section --vault-path P --template-id T \\
        [--id X] --section NAME --mode replace|append --input-file F
        F: {"content": str,
            # identify the target ONE of two ways (2026-08-30) -- a real
            # `id` (--id or "id" here), or "title" + "parent_value" (or a
            # plain "note_name" for a parent-less template) to resolve it
            # by name instead, the same way `create`'s own required-parent
            # handling does -- no separate script needed to "find it by
            # title, then modify a section" anymore:
            "id": str?, "title": str?, "parent_value": str?, "note_name": str?,
            # optional -- present only when this call should ALSO create
            # the note if it doesn't resolve yet ("Create if not Exist,
            # If Exists Update Section", operator, 2026-08-25) AND the
            # template's own on_missing allows it:
            "frontmatter": {...}?}

Every command prints one JSON object to stdout: the real result, or
{"error": str} (exit code 1) -- never raises an uncaught traceback for an
ordinary, expected failure (missing note, disallowed section, bad
template id).
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

# Operator, 2026-08-26: "It should go Back to Work Meetings I deleted it
# completely for a Reason" -- the vault's own REAL root for every existing
# content kind is "Work/" (Work/Threads, Work/Customers, Work/Technology,
# Work/Research, and capture-notes' own real "Work/Notes/<date>/" already)
# -- "Notes" as the TOP-LEVEL root was this module's own assumption from
# an illustrative example, not the vault's actual structure.
_NOTES_ROOT = "Work"
_TEMPLATES_SUBPATH = (".second-brain", "data", "Templates")


class VaultManagerError(Exception):
    pass


# ── slugs / frontmatter formatting -- the same shape every real Skill
# script already independently reimplements, written once here ──────────

def _slugify(text: str, max_len: int = 120) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", (text or "").strip())
    return slug[:max_len] if slug else "Untitled"


def _format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path: Path) -> tuple[dict, str]:
    """(frontmatter, body) -- {} / whole-file-as-body if no real
    frontmatter fence is present, never raises on a malformed shape."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_block = text[4:end]
    body = text[end + 5:]
    frontmatter: dict = {}
    for line in frontmatter_block.splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            frontmatter[match.group(1)] = _parse_frontmatter_value(match.group(2))
    return frontmatter, body


def write_note(path: Path, frontmatter: dict, body: str) -> None:
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter_lines) + "\n" + body, encoding="utf-8")


def _unique_dated_path(
    folder: Path, date_str: str, title_slug: str, own_folder: bool = False,
    plain_filename: bool = False, plain_folder: bool = False,
) -> Path:
    """Never overwrite -- same time/counter disambiguation technique
    every `always_new` real Skill script already uses (write_research_doc.py/
    capture_note.py), written once here.

    `own_folder` (a template's own `note_own_folder: true`, operator,
    2026-08-25: meetings "sometimes... will have Attachements, so we
    might have files") wraps the note in a folder named after itself --
    `<stem>/<stem>.md` instead of a bare `<stem>.md` -- the SAME "folder
    named after the thing, holding a same-named .md alongside real
    content" shape Threads/capture-files already use, so a real
    attachment has somewhere to live as a sibling of the note. Collision
    is checked against the FOLDER, not just the file, since a folder can
    legitimately exist with an attachment dropped in before its own note
    is ever written. `plain_filename` (operator, 2026-08-25: "the md for
    the Series shoud not have a date Just the Series name") names the
    FILE from `title_slug` alone. Combined with `own_folder`, the
    wrapping FOLDER still gets the dated stem -- lets a container note
    (a recurring series) sort by date in a file browser via its own
    folder while its own filename/wikilink target never has to change.
    WITHOUT `own_folder` (2026-08-30, operator: "Notes are organized in
    folders by Date") it means there's no date anywhere in this
    function's own output at all -- the caller is expected to have
    already folded the date into `folder` itself (a date-scoped
    `note_name`, e.g. Notes/2026-08-30), giving Work/Notes/<date>/
    <slug>.md with the date living in the folder, never repeated in the
    filename.

    `plain_folder` (2026-08-30, Opportunity's own real
    Opportunities/<slug>/<slug>.md -- no date ANYWHERE, unlike Meeting/
    File's dated folder or meeting-series' dated-folder-plain-file) only
    means anything combined with `own_folder`: the WRAPPING FOLDER's own
    name drops the date too, not just the file inside it. A durable,
    name-keyed entity (an Opportunity, found again by its own title, not
    by when it happened) has no real use for a creation-date sort key in
    its path the way a daily capture (Meeting, File) does.

    Real bug, found live 2026-08-25: a genuinely long real title (a
    corporate meeting subject well past 80 characters is normal) combined
    with `own_folder` -- the same stem appearing TWICE in one path
    (`.../<stem>/<stem>.md`) -- blew past Windows' classic 260-character
    MAX_PATH and crashed with a plain FileNotFoundError, not any error
    naming the real cause. Budget computed from the REAL resolved
    `folder` path length (not a fixed guess) -- a vault nested several
    directories deep eats into the same 260-character ceiling before the
    stem even starts."""
    if own_folder:
        # Full real path = folder + "/" + stem + "/" + stem + ".md", and
        # stem itself = "YYYY-MM-DD-" (11 chars) + title_slug -- appears
        # TWICE (the wrapping folder AND the file). Solve for the max
        # title_slug that keeps the whole real path under 260.
        # Real bug, found live 2026-08-26: the original budget assumed
        # the FIRST candidate always wins -- with zero headroom for the
        # " HH-MM"/" HH-MM-N" retry suffix _taken() can force on a real
        # collision, every retry was already over budget by construction
        # and failed the same way, every time, compounding (see MEMORY.md
        # for how an orphaned folder from one failed attempt then falsely
        # blocked every later retry too). Reserve room for the longest
        # realistic suffix (" HH-MM-99", 10 chars) on BOTH copies of the
        # stem up front, so a genuine collision retry still fits.
        fixed = len(str(folder.resolve())) + 2 + 3 + 2 * (11 + 10)
        max_title_len = max(10, (260 - fixed) // 2)
        if len(title_slug) > max_title_len:
            # Real bug, found live 2026-08-25 (a second time, a different
            # way): rsplit(" ", 1)[0].rstrip("-") only strips a trailing
            # HYPHEN -- a truncation landing exactly on/after a space can
            # still leave the word-boundary trim's OWN result ending in
            # whitespace (e.g. "...ADNOC - EDGE " survived, then hit
            # Windows' same trailing-space-in-a-path-segment rejection
            # `_sanitize_note_name` already exists to prevent, just not
            # here). Unconditional trailing .strip() as the real, final
            # guarantee, not just the word-boundary heuristic alone.
            truncated = title_slug[:max_title_len].rsplit(" ", 1)[0].rstrip("-").strip()
            title_slug = truncated or title_slug[:max_title_len].strip()

    def _candidate(name: str) -> Path:
        if not own_folder:
            return folder / f"{name}.md"
        filename = title_slug if plain_filename else name
        return folder / name / f"{filename}.md"

    def _taken(name: str) -> bool:
        return (folder / name).exists() if own_folder else _candidate(name).exists()

    # The basis for retry-suffix construction is whichever name this
    # shape actually checks for collision -- the FOLDER's own name when
    # `own_folder`, otherwise the file's own name. `plain_filename`
    # WITHOUT `own_folder` (2026-08-30, operator: "Notes are organized
    # in folders by Date") -- Work/Notes/<date>/<slug>.md, the date
    # living in the FOLDER (the caller's own date-scoped `note_name`),
    # never repeated in the filename. `plain_folder` WITH `own_folder`
    # is the same idea one level up (Opportunity's own dateless path).
    is_plain = plain_folder if own_folder else plain_filename
    base = title_slug if is_plain else f"{date_str}-{title_slug}"
    name = base
    if not _taken(name):
        return _candidate(name)
    name = f"{base} {datetime.now().strftime('%H-%M')}"
    if not _taken(name):
        return _candidate(name)
    n = 2
    while True:
        name = f"{base} {datetime.now().strftime('%H-%M')}-{n}"
        if not _taken(name):
            return _candidate(name)
        n += 1


# ── named-section read/replace/append -- the SAME primitive
# create_opportunity.py, apply_thread_review.py, and capture_file.py's
# own add_file_detail each independently reimplemented (with real drift
# between them, confirmed by direct reading, 2026-08-25) ────────────────

def _section_header(name: str) -> str:
    return name if name.startswith("## ") else f"## {name}"

def get_section_content(path: Path, section: str) -> str:
    text = path.read_text(encoding="utf-8")
    header_pattern = re.compile(r"^" + re.escape(_section_header(section)) + r"$", re.MULTILINE)
    match = header_pattern.search(text)
    if match is None:
        return ""
    region_start = match.end()
    next_header = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header.start() if next_header else len(text)
    return text[region_start:region_end].strip("\n")


def _set_section_content(path: Path, section: str, content: str, mode: str) -> None:
    header = _section_header(section)
    text = path.read_text(encoding="utf-8")
    header_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    match = header_pattern.search(text)

    if match is None:
        separator = "" if text.endswith("\n") else "\n"
        new_text = text + separator + f"\n{header}\n\n{content.strip()}\n"
        path.write_text(new_text, encoding="utf-8")
        return

    region_start = match.end()
    next_header = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header.start() if next_header else len(text)

    if mode == "append":
        existing = text[region_start:region_end].strip("\n")
        merged = (existing + "\n\n" + content).strip("\n") if existing else content.strip()
    else:
        merged = content.strip()

    new_text = text[:region_start] + "\n\n" + merged + "\n\n" + text[region_end:]
    path.write_text(new_text, encoding="utf-8")


# ── templates ─────────────────────────────────────────────────────────

def load_template(vault_path: Path, template_id: str) -> dict:
    """Template.json v2 (Implementation/Plans/2026-08-30-vault-manager-
    template-trees.md) -- a template is TWO layers, not one flat object:
    top-level fields describe the RECORD as a whole (`identity`: how an
    existing record is looked up -- `id` today, `tag`/`filename` land when
    Customer/Person actually need them; `on_missing`; `allow_create_folder`
    -- can this record's own containing folder be auto-vivified, or is
    that an error -- defaults `True` so today's 7 real templates are
    unaffected, a real `False` case lands with Customer), and `root`
    (today's entire old flat schema, unchanged in substance, just nested:
    `type`, `own_folder`, `plain_filename`, `on_existing_title`,
    `frontmatter_defaults`, `sections`). `root` is a single md node today
    -- fixed/dynamic `children` (OKF, Thread's messages/) are a real,
    later addition to this same shape, not built here (nothing today
    needs them)."""
    template_path = vault_path.joinpath(*_TEMPLATES_SUBPATH, template_id, "Template.json")
    if not template_path.is_file():
        raise VaultManagerError(f"unknown template: {template_id!r} ({template_path} not found)")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    identity = template.setdefault("identity", {})
    identity.setdefault("strategy", "id")
    template.setdefault("on_missing", "create")
    template.setdefault("allow_create_folder", True)
    root = template.setdefault("root", {})
    root.setdefault("type", "md")
    root.setdefault("on_existing_title", "update_section")
    root.setdefault("frontmatter_defaults", {})
    root.setdefault("sections", [])
    root.setdefault("own_folder", False)
    root.setdefault("plain_filename", False)
    root.setdefault("plain_folder", False)
    return template


def _section_access(template: dict, section: str) -> str:
    for entry in template["root"]["sections"]:
        if entry["name"] == section:
            return entry.get("access", "machine_write")
    return "machine_write"  # an undeclared section defaults open, same as today's real scripts


def _require_machine_write(template: dict, section: str) -> None:
    access = _section_access(template, section)
    if access != "machine_write":
        raise VaultManagerError(
            f"section {section!r} is {access!r} in template {template['id']!r} -- "
            "no automated write is allowed here"
        )


# ── notes root / lookup ──────────────────────────────────────────────

def _sanitize_note_name(note_name: str) -> str:
    """Real bug, found live 2026-08-25: `note_name` used to be joined onto
    the vault path RAW -- a real Outlook meeting subject can carry a
    trailing space ("PSS Team Get together ") or other characters Windows
    silently disallows in a path segment, which `_slugify` (used
    everywhere else in this file) already exists to handle. Segment-wise
    so a hierarchical note_name ("Azure/Services/Storage") keeps its real
    "/" structure -- only each individual segment gets sanitized, never
    the separator itself."""
    return "/".join(_slugify(segment) for segment in note_name.split("/") if segment.strip())


def _notes_root(vault_path: Path, note_name: str | None) -> Path:
    root = vault_path / _NOTES_ROOT
    return root / _sanitize_note_name(note_name) if note_name else root


def _load_scoped_index_notes(vault_path: Path, root: Path) -> list[dict] | None:
    """Best-effort fast path over build_vault_index.py's own per-folder
    structural index (Implementation/Plans/2026-08-27-vault-index-and-
    section-agents.md) -- fixes the real, confirmed 2026-08-26 slowdown
    where find_by_id fell back to scanning the entire Work/ tree.

    Returns None whenever it can't confidently answer (no index file for
    this folder, unreadable/corrupt, or root isn't under a single
    indexed top-level folder) -- callers below MUST fall back to the
    original rglob scan whenever this returns None, AND whenever the
    index simply doesn't contain what they're looking for. A stale or
    incomplete index can only ever make a lookup SLOWER (falls through
    to the real scan), never WRONG (silently reports "doesn't exist"
    when it actually does, which would let a capture pipeline create a
    real duplicate note).

    Assumes the index lives at <vault_path>/.second-brain/index/ (the
    App Database Folder's own default location) -- a disclosed
    limitation shared with every other Hermes-side .second-brain
    consumer: if the operator relocates the App Database Folder from
    Second Brain's own System settings page, this stays looking at the
    old default until this literal path is updated to match."""
    try:
        relative_to_work = root.relative_to(vault_path / _NOTES_ROOT)
    except ValueError:
        return None
    parts = relative_to_work.parts
    if not parts:
        return None  # root IS Work/ itself -- no single per-folder index covers the whole vault
    index_path = vault_path / ".second-brain" / "index" / "folders" / f"{parts[0]}.json"
    if not index_path.is_file():
        return None
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    notes = data.get("notes")
    if not isinstance(notes, list):
        return None
    if len(parts) == 1:
        return notes
    prefix = "/".join(("Work",) + parts) + "/"
    return [n for n in notes if isinstance(n, dict) and str(n.get("path", "")).startswith(prefix)]


def _iter_real_md_files(vault_path: Path, root: Path):
    """Fallback filesystem walk shared by find_by_id/find_by_filename/
    find_in_folder below -- skips any path with a `_`-prefixed folder
    anywhere under vault_path (this project's own established archive-
    exclusion convention, matching build_vault_index.py's build_index())
    and never lets one unreadable file abort the whole scan. Real,
    confirmed bug found live 2026-08-27: an UNSCOPED (`note_name=None`)
    call previously crashed with an unhandled FileNotFoundError reading a
    real file under `Work/_archive/Meetings/_Archived Duplicates
    (2026-08-24)/...` -- dormant today (no real caller passes
    `note_name=None`), but a real landmine for any future one that does.
    Excluding archived folders here also avoids surfacing a stale
    archived duplicate as a real match, not just avoiding the crash."""
    for md_path in sorted(root.rglob("*.md")):
        if not md_path.is_file():
            continue
        try:
            relative_parts = md_path.relative_to(vault_path).parts
        except ValueError:
            relative_parts = ()
        if any(part.startswith("_") for part in relative_parts[:-1]):
            continue
        yield md_path


def find_by_id(vault_path: Path, note_id: str, note_name: str | None = None) -> Path | None:
    root = _notes_root(vault_path, note_name)
    if not root.is_dir():
        return None
    indexed = _load_scoped_index_notes(vault_path, root)
    if indexed is not None:
        for entry in indexed:
            if str(entry.get("id", "")) == str(note_id):
                candidate = vault_path / entry["path"]
                if candidate.is_file():
                    return candidate
                break  # stale index entry (moved/deleted since last rebuild) -- fall through to the real scan
    for md_path in _iter_real_md_files(vault_path, root):
        try:
            frontmatter, _ = read_note(md_path)
        except OSError:
            continue
        if str(frontmatter.get("id", "")) == str(note_id):
            return md_path
    return None


def find_by_filename(vault_path: Path, filename: str, note_name: str | None = None) -> Path | None:
    root = _notes_root(vault_path, note_name)
    if not root.is_dir():
        return None
    name = filename if filename.endswith(".md") else f"{filename}.md"
    indexed = _load_scoped_index_notes(vault_path, root)
    if indexed is not None:
        for entry in indexed:
            if entry.get("filename") == name:
                candidate = vault_path / entry["path"]
                if candidate.is_file():
                    return candidate
                break
    for md_path in _iter_real_md_files(vault_path, root):
        if md_path.name == name:
            return md_path
    return None


def find_in_folder(vault_path: Path, note_name: str) -> list[Path]:
    root = _notes_root(vault_path, note_name)
    if not root.is_dir():
        return []
    indexed = _load_scoped_index_notes(vault_path, root)
    if indexed is not None:
        candidates = sorted(vault_path / entry["path"] for entry in indexed if "path" in entry)
        if candidates and all(path.is_file() for path in candidates):
            return candidates
        # empty, or at least one indexed entry is stale -- the index
        # can't be trusted as a complete, accurate listing right now.
    return list(_iter_real_md_files(vault_path, root))


def find(vault_path: Path, by: str, value: str, note_name: str | None = None):
    if by == "id":
        return find_by_id(vault_path, value, note_name)
    if by == "filename":
        return find_by_filename(vault_path, value, note_name)
    if by == "folder":
        return find_in_folder(vault_path, value)
    raise VaultManagerError(f"find: 'by' must be id/filename/folder, got {by!r}")


def _find_by_title(vault_path: Path, note_name: str, title: str) -> Path | None:
    """Scoped to one note_name folder -- used by create()'s own
    on_existing_title='update_section' path (azure-kb-writer/compass-
    kb-writer's real overwrite-same-title behavior)."""
    root = _notes_root(vault_path, note_name)
    if not root.is_dir():
        return None
    for md_path in root.rglob("*.md"):
        frontmatter, _ = read_note(md_path)
        if str(frontmatter.get("title", "")) == title:
            return md_path
    return None


def resolve_parent(vault_path: Path, parent_config: dict, value: str) -> Path | None:
    """The external-required-parent link (2026-08-30-vault-manager-
    template-trees.md) -- a DIFFERENT lookup than `_find_by_title`: real
    parent records (Customer hub notes today, hand-written by
    create_companies_partners.py, not yet on this engine) are matched
    case-insensitively against one or more declared frontmatter fields
    (`match_fields`, e.g. ["name", "title"] -- ported directly from
    create_opportunity.py's own real `resolve_customer_hub`, which
    checked `name` first), PLUS an optional alias list field
    (`alias_field`) -- a customer known by more than one real name.
    Generic and reusable: any future template can declare its own
    `parent` this way, not just Opportunity->Customer. Returns None on
    no match -- the caller (`create()`) is what turns that into a real
    "refuse to fabricate" error; this function only answers the lookup."""
    note_name = parent_config["note_name"]
    match_fields = parent_config.get("match_fields", ["title"])
    alias_field = parent_config.get("alias_field")
    root = _notes_root(vault_path, note_name)
    if not root.is_dir():
        return None
    key = value.strip().lower()
    if not key:
        return None
    for md_path in _iter_real_md_files(vault_path, root):
        frontmatter, _ = read_note(md_path)
        for field in match_fields:
            candidate = str(frontmatter.get(field, "")).strip().lower()
            if candidate and candidate == key:
                return md_path
        if alias_field:
            for alias in frontmatter.get(alias_field) or []:
                if str(alias).strip().lower() == key:
                    return md_path
    return None


def _tag_slugify(text: str) -> str:
    """The real tag-slug convention every hand-rolled Skill script already
    used its own copy of (`_tag_slug` in create_opportunity.py,
    create_companies_partners.py) -- lowercase, `[a-z0-9/]` only. A
    GENERIC primitive now, not per-entity code: `parent.derived_tag`
    (below) is what makes a caller not have to reimplement this."""
    return re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-") or "untitled"


def _child_note_name(vault_path: Path, parent_config: dict, parent_path: Path) -> str:
    """Where a child of this resolved parent lives -- `parent.child_subpath`
    appended to the PARENT's own note_name (its folder, relative to
    Work/). 2026-08-30 (operator: "Why we need to create script everytime
    we add a skill We Generalized so we don't do that") -- this is what
    lets `create()`/`modify_section()` derive note_name THEMSELVES from a
    resolved parent, instead of every calling script re-deriving this
    exact path math by hand (create_opportunity.py's own real
    `customer_hub.parent / "Opportunities"`, ported here as the one
    generic version)."""
    parent_note_name = parent_path.parent.relative_to(vault_path / _NOTES_ROOT).as_posix()
    return f"{parent_note_name}/{parent_config['child_subpath']}"


def _link_child_into_parent_section(parent_path: Path, section: str, child_wikilink: str) -> None:
    """Idempotently accumulates one wikilink line into the PARENT's own
    named section (create_opportunity.py's own real
    `link_opportunity_to_customer_hub`, generalized off any template's
    `parent.link_back_section`) -- a real cross-entity write the child's
    OWN template can never express as one of its own sections, since the
    section being written lives on a completely different note. No
    access-policy check here (unlike `modify_section`'s own
    `_require_machine_write`) -- the PARENT's own template isn't even
    loaded at this call site; a real access guard on a parent's own
    section is a disclosed gap, not silently ignored (see
    2026-08-30-vault-manager-template-trees.md's "Open, not decided")."""
    existing = get_section_content(parent_path, section)
    if child_wikilink in existing:
        return
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {child_wikilink}")
    _set_section_content(parent_path, section, "\n".join(lines), mode="replace")


# ── create / update ──────────────────────────────────────────────────

def create(
    vault_path: Path,
    template: dict,
    title: str,
    note_name: str | None = None,
    note_id: str | None = None,
    frontmatter: dict | None = None,
    sections: dict[str, str] | None = None,
    folder_date: str | None = None,
    parent_value: str | None = None,
) -> dict:
    """`folder_date` (YYYY-MM-DD) overrides the FOLDER's own dated stem --
    only meaningful with `note_own_folder` -- so a container note (a
    recurring series) can seed its own sort date from a real related
    event (e.g. its first occurrence) rather than defaulting to today,
    an artifact of whenever this call happened to run. `created`
    frontmatter always stays the real today's-date regardless -- a
    genuinely different concept ("when this note object was made") from
    the folder's own sort key. See `bump_folder_date` for moving it
    forward later.

    `parent_value` (2026-08-30, Opportunity's own real "resolve an
    existing Customer, refuse to fabricate one" guard, generalized) --
    REQUIRED whenever `template["parent"]` is declared; resolved via
    `resolve_parent()` and never fabricated (a missing parent is a real
    `VaultManagerError`, checked BEFORE anything is written, not a
    silent no-op or an auto-created stand-in). The resolved parent's own
    filename stem is auto-populated into `template["parent"]
    ["frontmatter_field"]` -- the child never has to know or repeat how
    its own parent was found. If the template also declares
    `parent.link_back_section`, a wikilink to the newly-created child is
    idempotently accumulated into that section on the PARENT note itself
    (create_opportunity.py's own real `link_opportunity_to_customer_hub`,
    now generic) -- this only ever runs on a genuine new creation, never
    on the `on_existing_title="update_section"` path below, since that
    path means the child already exists and was already linked once.

    `note_name` is now OPTIONAL (2026-08-30, operator: "Why we need to
    create script everytime we add a skill We Generalized so we don't do
    that") -- when omitted and the template declares `parent`, it's
    auto-derived from the resolved parent + `parent.child_subpath`
    (`_child_note_name`) instead of the CALLING SCRIPT having to
    reimplement that same path math by hand (create_opportunity.py's own
    original `customer_hub.parent / "Opportunities"`). Still overridable
    by passing `note_name` explicitly, and still required outright for a
    template with no `parent` declared. `parent.derived_tag` (a
    `{slug}`-templated string, e.g. `"customer/{slug}"`) is the same
    generalization for a tag built FROM the resolved parent's own name --
    computed here via `_tag_slugify` and merged into `tags`, so a
    per-entity tag-slug helper doesn't need reinventing per script
    either."""
    title = (title or "").strip()
    if not title:
        raise VaultManagerError("title is required")

    root = template["root"]
    parent_config = template.get("parent")
    parent_path: Path | None = None
    if parent_config is not None:
        parent_value = (parent_value or "").strip()
        if not parent_value:
            raise VaultManagerError(
                f"template {template['id']!r} requires a parent_value (declares a "
                "required parent) -- none was given"
            )
        parent_path = resolve_parent(vault_path, parent_config, parent_value)
        if parent_path is None:
            raise VaultManagerError(
                f"no real {parent_config['note_name']!r} record matches {parent_value!r} -- "
                "it must already exist; this template never fabricates its own parent"
            )
        if note_name is None:
            note_name = _child_note_name(vault_path, parent_config, parent_path)

    if note_name is None:
        raise VaultManagerError(
            f"template {template['id']!r} has no declared parent, so note_name is required "
            "(nothing to auto-derive it from)"
        )

    if root["on_existing_title"] in ("update_section", "error"):
        existing = _find_by_title(vault_path, note_name, title)
        if existing is not None:
            if root["on_existing_title"] == "error":
                # create_opportunity.py's own real guard ("an Opportunity
                # named X already exists for this Customer") -- a
                # genuinely different intent than `always_new`'s time-
                # suffix disambiguation: a duplicate TITLE here is a real
                # mistake to refuse, not a filename collision to work
                # around.
                raise VaultManagerError(
                    f"a note titled {title!r} already exists in {note_name!r} "
                    f"({existing}) -- this template refuses to create a duplicate"
                )
            existing_frontmatter, _ = read_note(existing)
            for section_name, content in (sections or {}).items():
                _require_machine_write(template, section_name)
                _set_section_content(existing, section_name, content, mode="replace")
            return {
                "created": False, "updated": True, "path": str(existing),
                "folder": str(existing.parent), "id": existing_frontmatter.get("id"),
            }

    folder = _notes_root(vault_path, note_name)
    if not folder.is_dir() and not template.get("allow_create_folder", True):
        raise VaultManagerError(
            f"folder {folder} does not exist and template {template['id']!r} "
            "does not allow auto-creating it (allow_create_folder: false)"
        )
    folder.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    note_path = _unique_dated_path(
        folder, folder_date or today_str, _slugify(title),
        own_folder=bool(root.get("own_folder")),
        plain_filename=bool(root.get("plain_filename")),
        plain_folder=bool(root.get("plain_folder")),
    )

    resolved_id = note_id or str(uuid.uuid4())
    full_frontmatter = dict(root["frontmatter_defaults"])
    full_frontmatter.update(frontmatter or {})
    full_frontmatter["id"] = resolved_id
    full_frontmatter["title"] = title
    full_frontmatter.setdefault("created", today_str)
    if parent_config is not None and parent_path is not None:
        full_frontmatter[parent_config["frontmatter_field"]] = parent_path.stem
        if parent_config.get("derived_tag"):
            tag = parent_config["derived_tag"].format(slug=_tag_slugify(parent_path.stem))
            tags = list(full_frontmatter.get("tags") or [])
            if tag not in tags:
                tags.append(tag)
            full_frontmatter["tags"] = tags

    body_parts = []
    for entry in root["sections"]:
        name = entry["name"]
        content = (sections or {}).get(name, "")
        body_parts.append(f"{_section_header(name)}\n\n{content}\n")
    write_note(note_path, full_frontmatter, "\n" + "\n".join(body_parts))

    if parent_config is not None and parent_path is not None and parent_config.get("link_back_section"):
        _link_child_into_parent_section(parent_path, parent_config["link_back_section"], f"[[{note_path.stem}]]")

    return {"created": True, "updated": False, "path": str(note_path), "folder": str(note_path.parent), "id": resolved_id}


def update(vault_path: Path, note_path: Path, title: str | None = None, frontmatter: dict | None = None) -> dict:
    existing_frontmatter, body = read_note(note_path)
    if title is not None:
        existing_frontmatter["title"] = title
    if frontmatter:
        existing_frontmatter.update(frontmatter)
    write_note(note_path, existing_frontmatter, body)
    return {"updated": True, "path": str(note_path)}


_DATED_FOLDER_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def bump_folder_date(vault_path: Path, note_path: Path, new_date_str: str) -> Path:
    """Moves a `note_own_folder`-wrapped note's own FOLDER forward to a
    newer real date (operator, 2026-08-25: a recurring series' folder
    should sort by its LAST real meeting date, even though the series
    .md file's own name -- `note_filename_plain` -- never carries a date
    at all). A plain directory rename, so any real attachment already
    inside moves with it untouched. No-op (returns `note_path` unchanged)
    if `new_date_str` isn't actually later than what the folder name
    already encodes, or if the folder isn't dated at all (this note's own
    template doesn't wrap it in a dated folder -- nothing to bump)."""
    folder = note_path.parent
    match = _DATED_FOLDER_NAME.match(folder.name)
    if match is None:
        return note_path
    current_date_str, rest = match.groups()
    if new_date_str <= current_date_str:
        return note_path
    new_folder = folder.parent / f"{new_date_str}-{rest}"
    if new_folder.exists():
        return note_path  # a genuine, rare real collision -- leave alone rather than merge/overwrite silently
    folder.rename(new_folder)
    return new_folder / note_path.name


def modify_section(
    vault_path: Path,
    template: dict,
    section: str,
    content: str,
    mode: str,
    note_id: str | None = None,
    note_name: str | None = None,
    title: str | None = None,
    parent_value: str | None = None,
    frontmatter: dict | None = None,
) -> dict:
    """"Create if not Exist, If Exists Update Section" (operator,
    2026-08-25) -- one call. `note_name`/`title` are only required when
    this specific call might need to create the note; omit them to get
    template['on_missing']='error' behavior (person-lookup's own real
    guard: never silently create a note that must already exist).

    Two ways to identify the target note, not just one (2026-08-30,
    operator: "Why we need to create script everytime we add a skill We
    Generalized so we don't do that" -- this is the fix: an "update an
    existing child-of-parent record by its real name" flow used to be
    only reachable by writing a whole new script, because this function
    could only look a note up by `note_id`, which the caller (a human
    or an agent, not a database) never actually has memorized):
    - `note_id` (a real UUID) -- the original, still-supported path.
    - `title` + `parent_value` -- resolves the target the SAME way
      `create()`'s own required-parent handling does (`resolve_parent`,
      never fabricated, `_child_note_name` derives where to look) and
      finds it by title within that scope. `note_name` can still be
      passed directly instead, for a template with no `parent` at all.
    Exactly one of `note_id` or `title` must be given.

    `on_missing` still governs the create-if-missing fallback either
    way -- a template like `opportunity` (`on_missing: "error"`) refuses
    to fabricate a record via this call regardless of which identity
    path was used to look for it."""
    parent_config = template.get("parent")
    if note_name is None and parent_config is not None:
        parent_value_stripped = (parent_value or "").strip()
        if not parent_value_stripped:
            raise VaultManagerError(
                f"template {template['id']!r} requires a parent_value to resolve where its "
                "records live -- none was given"
            )
        parent_path = resolve_parent(vault_path, parent_config, parent_value_stripped)
        if parent_path is None:
            raise VaultManagerError(
                f"no real {parent_config['note_name']!r} record matches {parent_value_stripped!r} -- "
                "it must already exist; this template never fabricates its own parent"
            )
        note_name = _child_note_name(vault_path, parent_config, parent_path)

    if note_id is not None:
        existing = find_by_id(vault_path, note_id, note_name)
    elif title is not None:
        if note_name is None:
            raise VaultManagerError("modify_section by title requires note_name (or a resolvable parent_value)")
        existing = _find_by_title(vault_path, note_name, title)
        if existing is not None:
            existing_frontmatter, _ = read_note(existing)
            note_id = existing_frontmatter.get("id")
    else:
        raise VaultManagerError("modify_section requires either note_id or title to identify the target note")

    if existing is None:
        if template["on_missing"] == "error" or not note_name or not title:
            raise VaultManagerError(
                f"no matching note exists (id={note_id!r}, title={title!r}), and this call is not allowed to create one"
            )
        created = create(
            vault_path, template, title=title, note_name=note_name, note_id=note_id,
            frontmatter=frontmatter, sections={section: content}, parent_value=parent_value,
        )
        return {"created": True, "updated": False, "path": created["path"], "folder": created["folder"], "id": created["id"]}

    _require_machine_write(template, section)
    _set_section_content(existing, section, content, mode=mode)
    frontmatter_now, _ = read_note(existing)
    return {"created": False, "updated": True, "path": str(existing), "folder": str(existing.parent), "id": frontmatter_now.get("id")}


# ── CLI ───────────────────────────────────────────────────────────────

def _load_input(args) -> dict:
    if not args.input_file:
        return {}
    return json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--id")
    parser.add_argument("--by", choices=["id", "filename", "folder"])
    parser.add_argument("--value")
    parser.add_argument("--note-name")
    parser.add_argument("--section")
    parser.add_argument("--mode", choices=["replace", "append"], default="replace")
    parser.add_argument("--input-file")
    parser.add_argument("command", choices=["find", "create", "update", "get-section", "modify-section"])
    args = parser.parse_args()

    vault_path = Path(args.vault_path)

    try:
        template = load_template(vault_path, args.template_id)

        if args.command == "find":
            result = find(vault_path, args.by, args.value, args.note_name)
            if isinstance(result, list):
                out = {"notes": [str(p) for p in result]}
            else:
                out = {"path": str(result)} if result else {"path": None}

        elif args.command == "create":
            data = _load_input(args)
            out = create(
                vault_path, template,
                title=data["title"], note_name=data.get("note_name"),
                note_id=data.get("id"), frontmatter=data.get("frontmatter"),
                sections=data.get("sections"), parent_value=data.get("parent_value"),
            )

        elif args.command == "update":
            data = _load_input(args)
            note_path = find_by_id(vault_path, args.id, args.note_name)
            if note_path is None:
                raise VaultManagerError(f"no note with id={args.id!r}")
            out = update(vault_path, note_path, title=data.get("title"), frontmatter=data.get("frontmatter"))

        elif args.command == "get-section":
            note_path = find_by_id(vault_path, args.id, args.note_name)
            if note_path is None:
                raise VaultManagerError(f"no note with id={args.id!r}")
            out = {"content": get_section_content(note_path, args.section)}

        else:  # modify-section
            data = _load_input(args)
            out = modify_section(
                vault_path, template, section=args.section,
                content=data["content"], mode=args.mode,
                note_id=args.id or data.get("id"),
                note_name=data.get("note_name") or args.note_name, title=data.get("title"),
                parent_value=data.get("parent_value"),
                frontmatter=data.get("frontmatter"),
            )

        print(json.dumps(out, ensure_ascii=False))
        return 0
    except VaultManagerError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
