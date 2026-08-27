"""Whole-vault and generic note-file primitives -- everything that needs
to know the vault ROOT (unlike frontmatter.py/sections.py/tags.py, which
operate on an already-resolved single note path). `vault_path` is always
an explicit parameter here, never read from app.config -- this package
has zero Second Brain awareness, matching app/hermes/'s own "config
injected, not imported" convention."""
from __future__ import annotations

import re
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

_OKF_RESERVED_FILENAMES = {"index.md", "log.md", "captures.md"}
_THREAD_SIDECAR_RESERVED_FILENAMES = {
    "pre_migration_summary.md", "pre_migration_summary.consumed.md",
}


def slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def write_note(vault_path: Path, subfolder: str, filename_stem: str, frontmatter: dict, body: str) -> str:
    from app.obsidian.frontmatter import write_frontmatter_note
    note_path = Path(vault_path) / subfolder / f"{slugify(filename_stem)}.md"
    write_frontmatter_note(note_path, frontmatter, body)
    return str(note_path)


def list_all_note_paths(vault_path: Path, work_root_name: str = "Work") -> list:
    """Every real, normally-frontmattered note anywhere under `<vault>/
    Work/`, at ANY depth -- a single bounded recursive scan.
    `index.md`/`log.md`/`captures.md` are OKF-reserved/append-only files
    with no ordinary key: value frontmatter shape, excluded so every
    caller's read_note(path) contract keeps holding. Also excludes any
    path with a `_`-prefixed folder component anywhere under Work/ (this
    project's own "keep on disk, hide from live app" archive
    convention), and Thread-directory migration sidecars."""
    work_root = Path(vault_path) / work_root_name
    if not work_root.exists():
        return []
    return sorted(
        path for path in work_root.rglob("*.md")
        if path.name not in _OKF_RESERVED_FILENAMES
        and path.name not in _THREAD_SIDECAR_RESERVED_FILENAMES
        and path.is_file()
        and not any(part.startswith("_") for part in path.relative_to(work_root).parent.parts)
    )


def list_notes_in_kind_folder(vault_path: Path, kind: str, work_root_name: str = "Work") -> list:
    """Same shape as list_all_note_paths(), scoped to one `<vault>/Work/
    <kind>/` folder -- avoids reading and discarding every note of every
    other kind just to filter down to one. Returns [] if the kind folder
    doesn't exist yet."""
    kind_root = Path(vault_path) / work_root_name / kind
    if not kind_root.exists():
        return []
    return sorted(kind_root.glob("*.md"))


def extract_wikilink_targets(body: str) -> list[str]:
    """Every [[target]] wikilink target found anywhere in a note's body
    text, in first-seen order. Resolving a target against another
    note's own filename stem is the caller's job -- this is a raw
    text-extraction primitive only."""
    return WIKILINK_PATTERN.findall(body)


def remove_empty_dirs(root) -> None:
    root = Path(root)
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if root.is_dir() and not any(root.iterdir()):
        root.rmdir()


def move_note_and_attachments(note_path, target_dir) -> str:
    """Moves a note and its sibling attachments/<note_slug>/ folder (if
    any) into target_dir, preserving the note's own filename. Refuses to
    silently overwrite an existing file at the destination."""
    note_path = Path(note_path)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    note_slug = note_path.stem
    new_note_path = target_dir / note_path.name
    if new_note_path.exists():
        raise FileExistsError(f"would overwrite existing note at {new_note_path}")
    note_path.rename(new_note_path)

    old_attachments_dir = note_path.parent / "attachments" / note_slug
    if old_attachments_dir.exists():
        new_attachments_dir = target_dir / "attachments" / note_slug
        new_attachments_dir.parent.mkdir(parents=True, exist_ok=True)
        old_attachments_dir.rename(new_attachments_dir)

    return str(new_note_path)
