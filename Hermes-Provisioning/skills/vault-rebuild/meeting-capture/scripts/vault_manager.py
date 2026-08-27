"""vault_manager.py -- the one real, template-driven vault write/read
engine (Implementation/Plans/2026-08-25-vault-writer-standardization.md).

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
Template.json. A Template controls note_name/filename shape, whether a
same-title call updates in place or always makes a new file, per-section
write access (machine vs. a human-owned section no automated call may
ever touch), and frontmatter defaults -- so a NEW Section/note-type is a
new Template.json, never new code.

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
        F: {"id": str?, "note_name": str, "title": str,
            "frontmatter": {...}?, "sections": {"Summary": "...", ...}?}
    python vault_manager.py update --vault-path P --template-id T --id X --input-file F
        F: {"title": str?, "frontmatter": {...}?}
    python vault_manager.py get-section --vault-path P --template-id T --id X --section NAME
    python vault_manager.py modify-section --vault-path P --template-id T --id X \\
        --section NAME --mode replace|append --input-file F
        F: {"content": str,
            # optional -- present only when this call should ALSO create
            # the note if `id` doesn't resolve yet ("Create if not Exist,
            # If Exists Update Section", operator, 2026-08-25):
            "note_name": str?, "title": str?, "frontmatter": {...}?}

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
    folder: Path, date_str: str, title_slug: str, own_folder: bool = False, plain_filename: bool = False,
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
    is ever written. `plain_filename` (only meaningful with `own_folder`,
    operator, 2026-08-25: "the md for the Series shoud not have a date
    Just the Series name") names the FILE from `title_slug` alone while
    the wrapping FOLDER still gets the dated stem -- lets a container
    note (a recurring series) sort by date in a file browser via its own
    folder while its own filename/wikilink target never has to change.

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

    def _candidate(stem: str) -> Path:
        if not own_folder:
            return folder / f"{stem}.md"
        filename = title_slug if plain_filename else stem
        return folder / stem / f"{filename}.md"

    def _taken(stem: str) -> bool:
        return (folder / stem).exists() if own_folder else _candidate(stem).exists()

    stem = f"{date_str}-{title_slug}"
    if not _taken(stem):
        return _candidate(stem)
    stem = f"{date_str}-{title_slug} {datetime.now().strftime('%H-%M')}"
    if not _taken(stem):
        return _candidate(stem)
    n = 2
    while True:
        stem = f"{date_str}-{title_slug} {datetime.now().strftime('%H-%M')}-{n}"
        if not _taken(stem):
            return _candidate(stem)
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
    template_path = vault_path.joinpath(*_TEMPLATES_SUBPATH, template_id, "Template.json")
    if not template_path.is_file():
        raise VaultManagerError(f"unknown template: {template_id!r} ({template_path} not found)")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template.setdefault("on_missing", "create")
    template.setdefault("on_existing_title", "update_section")
    template.setdefault("frontmatter_defaults", {})
    template.setdefault("sections", [])
    template.setdefault("note_own_folder", False)
    template.setdefault("note_filename_plain", False)
    return template


def _section_access(template: dict, section: str) -> str:
    for entry in template["sections"]:
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


# ── create / update ──────────────────────────────────────────────────

def create(
    vault_path: Path,
    template: dict,
    note_name: str,
    title: str,
    note_id: str | None = None,
    frontmatter: dict | None = None,
    sections: dict[str, str] | None = None,
    folder_date: str | None = None,
) -> dict:
    """`folder_date` (YYYY-MM-DD) overrides the FOLDER's own dated stem --
    only meaningful with `note_own_folder` -- so a container note (a
    recurring series) can seed its own sort date from a real related
    event (e.g. its first occurrence) rather than defaulting to today,
    an artifact of whenever this call happened to run. `created`
    frontmatter always stays the real today's-date regardless -- a
    genuinely different concept ("when this note object was made") from
    the folder's own sort key. See `bump_folder_date` for moving it
    forward later."""
    title = (title or "").strip()
    if not title:
        raise VaultManagerError("title is required")

    if template["on_existing_title"] == "update_section":
        existing = _find_by_title(vault_path, note_name, title)
        if existing is not None:
            existing_frontmatter, _ = read_note(existing)
            for section_name, content in (sections or {}).items():
                _require_machine_write(template, section_name)
                _set_section_content(existing, section_name, content, mode="replace")
            return {
                "created": False, "updated": True, "path": str(existing),
                "folder": str(existing.parent), "id": existing_frontmatter.get("id"),
            }

    folder = _notes_root(vault_path, note_name)
    folder.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    note_path = _unique_dated_path(
        folder, folder_date or today_str, _slugify(title),
        own_folder=bool(template.get("note_own_folder")),
        plain_filename=bool(template.get("note_filename_plain")),
    )

    resolved_id = note_id or str(uuid.uuid4())
    full_frontmatter = dict(template["frontmatter_defaults"])
    full_frontmatter.update(frontmatter or {})
    full_frontmatter["id"] = resolved_id
    full_frontmatter["title"] = title
    full_frontmatter.setdefault("created", today_str)

    body_parts = []
    for entry in template["sections"]:
        name = entry["name"]
        content = (sections or {}).get(name, "")
        body_parts.append(f"{_section_header(name)}\n\n{content}\n")
    write_note(note_path, full_frontmatter, "\n" + "\n".join(body_parts))

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
    note_id: str,
    section: str,
    content: str,
    mode: str,
    note_name: str | None = None,
    title: str | None = None,
    frontmatter: dict | None = None,
) -> dict:
    """"Create if not Exist, If Exists Update Section" (operator,
    2026-08-25) -- one call. `note_name`/`title` are only required when
    this specific call might need to create the note; omit them to get
    template['on_missing']='error' behavior (person-lookup's own real
    guard: never silently create a note that must already exist)."""
    existing = find_by_id(vault_path, note_id, note_name)
    if existing is None:
        if template["on_missing"] == "error" or not note_name or not title:
            raise VaultManagerError(f"no note with id={note_id!r} exists, and this call is not allowed to create one")
        created = create(vault_path, template, note_name, title, note_id=note_id, frontmatter=frontmatter, sections={section: content})
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
                note_name=data["note_name"], title=data["title"],
                note_id=data.get("id"), frontmatter=data.get("frontmatter"),
                sections=data.get("sections"),
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
                vault_path, template, note_id=args.id, section=args.section,
                content=data["content"], mode=args.mode,
                note_name=data.get("note_name") or args.note_name, title=data.get("title"),
                frontmatter=data.get("frontmatter"),
            )

        print(json.dumps(out, ensure_ascii=False))
        return 0
    except VaultManagerError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
