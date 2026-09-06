"""build_vault_index.py -- Phase 1 of the vault structural index
(Implementation/Plans/2026-08-27-vault-index-and-section-agents.md).

Standalone, stdlib-only (mirrors vault_manager.py's own "no Second Brain
backend dependency" deployment model -- physically copied into whichever
Hermes profile needs it, same as vault_manager.py). Walks Work/ ONCE,
writing:
  - one JSON file per real top-level Work/ folder (Threads, Meetings,
    Customers, ...) -- a flat list of every note under it (id, filename,
    path, tags, frontmatter)
  - one whole-vault JSON file merging all of them, for a consumer that
    needs a global id -> path lookup rather than one scoped to a folder

Reuses vault_manager.py's own read_note() (sibling import, same folder)
rather than reimplementing frontmatter parsing a third time.

Fixes a real, confirmed production slowdown: find_by_id/find_by_filename/
find_in_folder (this same shared vault_manager.py, plus every per-Skill
copy of it) currently do a fresh root.rglob("*.md") + per-file frontmatter
parse on EVERY call -- this script lets those become a single JSON load
plus an in-memory dict lookup instead (2026-08-26 incident:
ingest_meeting.py's own unscoped find_by_id "fell back to scanning the
ENTIRE Work/ tree").

Usage:
    python build_vault_index.py --vault-path P --data-path D

D is Second Brain's own App Database Folder (System settings page,
2026-08-27) -- NOT necessarily <vault>/.second-brain, though that's the
default until the operator relocates it. This script has no knowledge of
that backend setting, so the caller (cron job / app's Rebuild button)
must always pass the real, current value explicitly.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from vault_manager import read_note

_WORK_ROOT = "Work"

# Same three exclusions app/data_access/vault_writer.py's own canonical
# list_all_note_paths() applies (mirrored here, not imported -- this
# script is standalone/backend-independent) -- skipping any of these
# would let this index disagree with the app's own real index, and
# specifically could reintroduce the "I can see the same meeting twice"
# bug class (an archived duplicate resurfacing) that scan was fixed for.
_RESERVED_FILENAMES = {
    "index.md", "log.md", "captures.md",
    "pre_migration_summary.md", "pre_migration_summary.consumed.md",
}


def _has_underscore_folder(relative_parts: tuple[str, ...]) -> bool:
    # Every path component except the filename itself -- any `_`-prefixed
    # folder anywhere in the path (not just a top-level "_archive") means
    # excluded, matching the leading-underscore-means-excluded idiom this
    # ecosystem already uses elsewhere.
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


def _load_excluded_folders(data_path: Path) -> set[str]:
    """Settings > Vault > Index Filtering (2026-08-27, operator: "Index
    Filtering a new settings feature... instead of Hardcoding files") --
    reads the SAME index_config.json the backend's own
    vault_index_config.py writes (settings.second_brain_data_path /
    "index_config.json"), directly off disk since this script has no
    backend dependency. A folder absent from the file, or the file itself
    absent, defaults to included -- matches the backend's own default so
    an unconfigured folder behaves identically on both sides."""
    config_path = data_path / "index_config.json"
    if not config_path.exists():
        return set()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        name for name, settings_ in data.get("folders", {}).items()
        if settings_.get("included", True) is False
    }


def build_index(vault_path: Path, data_path: Path) -> dict[str, list[dict]]:
    """folder name -> list of note entries, for every real, non-excluded
    top-level Work/ folder that actually has at least one real
    (non-archived, non-reserved) .md note under it. An unreadable file is
    skipped, never aborts the whole rebuild."""
    work_root = vault_path / _WORK_ROOT
    folders: dict[str, list[dict]] = {}
    if not work_root.is_dir():
        return folders
    excluded = _load_excluded_folders(data_path)
    for top in sorted(p for p in work_root.iterdir() if p.is_dir()):
        if top.name.startswith("_"):
            continue
        if top.name in excluded:
            continue
        notes = []
        for md_path in sorted(top.rglob("*.md")):
            if not md_path.is_file():
                continue
            if md_path.name in _RESERVED_FILENAMES:
                continue
            relative_parts = md_path.relative_to(work_root).parts
            if _has_underscore_folder(relative_parts):
                continue
            try:
                notes.append(_note_entry(vault_path, md_path))
            except OSError:
                continue
        if notes:
            folders[top.name] = notes
    return folders


def write_index(data_path: Path, folders: dict[str, list[dict]]) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()
    index_root = data_path / "index"
    folders_dir = index_root / "folders"
    folders_dir.mkdir(parents=True, exist_ok=True)

    # A folder that had notes on a previous run but none now (renamed,
    # emptied, deleted) must not leave a stale JSON file behind implying
    # notes still exist there.
    current_names = {f"{name}.json" for name in folders}
    for existing in folders_dir.glob("*.json"):
        if existing.name not in current_names:
            existing.unlink()

    whole_vault: list[dict] = []
    for folder_name, notes in folders.items():
        folder_payload = {"generated_at": generated_at, "folder": folder_name, "notes": notes}
        (folders_dir / f"{folder_name}.json").write_text(
            json.dumps(folder_payload, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        for note in notes:
            whole_vault.append({**note, "folder": folder_name})

    whole_vault_payload = {"generated_at": generated_at, "notes": whole_vault}
    (index_root / "vault_index.json").write_text(
        json.dumps(whole_vault_payload, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return {
        "generated_at": generated_at,
        "folders": {name: len(notes) for name, notes in folders.items()},
        "total_notes": len(whole_vault),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--data-path", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data_path = Path(args.data_path)
    folders = build_index(vault_path, data_path)
    result = write_index(data_path, folders)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
