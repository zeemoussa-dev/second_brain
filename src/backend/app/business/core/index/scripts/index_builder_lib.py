"""index_builder_lib.py -- shared, standalone, stdlib-only vault-index
build engine (generalizes build_vault_index.py's own single, global
structural index into a reusable, parameterized one). Second Brain's own
IndexManager (app/business/core/index/) deploys a tiny per-Index stub
script alongside a copy of this file (and a copy of vault_manager.py,
whose read_note() this reuses via a sibling import) into whichever
Hermes profile owns that Index's own cron job; the stub reads its own
real Index.json definition and calls build_index()/write_index() here
with the real folders/tags/depth/storage_path. No Second Brain backend
dependency -- same "prepare here, apply where it's needed" convention
vault_manager.py itself already established.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from vault_manager import iter_md_files, long_path, read_note

_WORK_ROOT = "Work"

# Same exclusions build_vault_index.py's own single global index already
# applies -- an Index that disagreed with those would resurface the
# exact "duplicate/archived note" bug class that scan was fixed for.
_RESERVED_FILENAMES = {
    "index.md", "log.md", "captures.md",
    "pre_migration_summary.md", "pre_migration_summary.consumed.md",
}


def _has_underscore_folder(relative_parts) -> bool:
    return any(part.startswith("_") for part in relative_parts[:-1])


def _note_entry(vault_path: Path, path: Path) -> dict:
    frontmatter, _ = read_note(path)
    tags = frontmatter.get("tags")
    if not isinstance(tags, list):
        tags = []
    return {
        "path": str(path.relative_to(vault_path)).replace("\\", "/"),
        "filename": path.name,
        "id": frontmatter.get("id"),
        "tags": tags,
        "frontmatter": frontmatter,
    }


def _matches_tags(entry: dict, tags) -> bool:
    """A note matches if it carries ANY of the listed tags -- no filter
    (every note in the folder scope matches) when `tags` is falsy."""
    if not tags:
        return True
    return bool(set(entry.get("tags") or []) & set(tags))


def build_index(vault_path: Path, *, folders=None, tags=None, depth=None) -> dict:
    """folder name -> list of matching note entries under Work/.
    `folders` (None/[] = every real top-level folder), `tags` (None/[] =
    no tag filter), `depth` (None = unlimited subfolder recursion under
    each included top-level folder; 0 = that folder's own direct files
    only)."""
    work_root = vault_path / _WORK_ROOT
    result: dict[str, list[dict]] = {}
    if not work_root.is_dir():
        return result
    wanted_folders = set(folders) if folders else None
    for top in sorted(p for p in work_root.iterdir() if p.is_dir()):
        if top.name.startswith("_"):
            continue
        if wanted_folders is not None and top.name not in wanted_folders:
            continue
        notes = []
        # iter_md_files, not rglob: it walks the extended-length form and
        # prunes `_` folders during the walk. rglob descends into a folder
        # before anything can reject it, so one archived note past Windows'
        # 260-char MAX_PATH raised FileNotFoundError mid-iteration and
        # abandoned the entire top-level folder (live, 2026-09-06 --
        # index-adnoc/masdar/taqa). No is_file() guard here either: past
        # MAX_PATH it silently returns False, which would drop exactly the
        # notes this fix is meant to recover, and os.walk already yields
        # files only.
        walk_root = long_path(top)
        for md_path in sorted(top / os.path.relpath(str(found), walk_root)
                              for found in iter_md_files(top)):
            if md_path.name in _RESERVED_FILENAMES:
                continue
            relative_parts = md_path.relative_to(top).parts
            if _has_underscore_folder((top.name, *relative_parts)):
                continue
            if depth is not None and (len(relative_parts) - 1) > depth:
                continue
            try:
                entry = _note_entry(vault_path, md_path)
            except OSError:
                continue
            if not _matches_tags(entry, tags):
                continue
            notes.append(entry)
        if notes:
            result[top.name] = notes
    return result


def write_index(storage_path: Path, folders: dict) -> dict:
    """Writes ONE combined JSON file at storage_path -- unlike
    build_vault_index.py's own per-folder-plus-whole-vault split (that
    shape served the one, fixed, global structural index; a real
    per-Index storage_path is a single real location the operator
    configures, so one file is the right shape here)."""
    generated_at = datetime.now(timezone.utc).isoformat()
    whole: list[dict] = []
    for folder_name, notes in folders.items():
        for note in notes:
            whole.append({**note, "folder": folder_name})
    payload = {"generated_at": generated_at, "notes": whole}
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "generated_at": generated_at,
        "folders": {name: len(notes) for name, notes in folders.items()},
        "total_notes": len(whole),
    }
