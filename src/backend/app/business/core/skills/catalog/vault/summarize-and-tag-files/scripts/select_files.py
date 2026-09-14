"""Picks the next batch of captured attachments to summarize, and nothing else.

Same reason as `select_threads.py`: which files a run touches is decided once,
in code. An agent choosing its own batch re-picks, skips or widens it, and the
batch size is the only thing bounding a scheduled run.

A file is due when its companion note's `## Summary` is empty. That is a
COMPLETE freshness rule here, unlike for Threads: an attachment's content never
changes after capture, so once summarized it is done.

Also counts attachment folders with NO companion note. Those cannot be
summarized -- there is nowhere to write the summary -- and every other pass
walks notes, not folders, so without this count they are simply invisible.
The first 256 found were empty folders left by a MAX_PATH failure in capture.

Every directory is scanned through `vault_manager.long_path`: attachment paths
routinely pass Windows' 260-character MAX_PATH, and past it a plain
iterdir/is_file silently returns nothing -- which would report a file that
exists as missing.

    python select_files.py [--vault-path P] [--limit 10] [--newest-first]

Prints JSON: {"total_files", "summarized", "due", "orphans_without_note",
"selected": [{"file_note", "original_filename", "ext", "bytes",
"file_present", "thread"}]}.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import vault_manager as vm


def _scan(folder: Path) -> list[os.DirEntry]:
    with os.scandir(vm.long_path(folder)) as entries:
        return list(entries)


def _attachment_folders(vault_path: Path):
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.is_dir():
        return
    for thread in sorted((e for e in _scan(threads_root) if e.is_dir()), key=lambda e: e.name):
        files_dir = threads_root / thread.name / "files"
        if not os.path.isdir(vm.long_path(files_dir)):
            continue
        for folder in sorted((e for e in _scan(files_dir) if e.is_dir()), key=lambda e: e.name):
            yield thread.name, files_dir / folder.name


def select(vault_path: Path, *, limit: int = 10, newest_first: bool = False) -> dict:
    due: list[dict] = []
    total = summarized = orphans = 0
    for thread_name, folder in _attachment_folders(vault_path):
        entries = [e for e in _scan(folder) if e.is_file()]
        notes = sorted(e.name for e in entries if e.name.lower().endswith(".md"))
        if not notes:
            orphans += 1
            continue
        note = folder / notes[0]
        frontmatter, _ = vm.read_note(note)
        if frontmatter.get("type") != "File":
            continue
        total += 1
        if (vm.get_section_content(note, "Summary") or "").strip():
            summarized += 1
            continue
        originals = [e for e in entries if not e.name.lower().endswith(".md")]
        name = frontmatter.get("original_filename") or (originals[0].name if originals else "")
        due.append({
            "file_note": str(note),
            "original_filename": name,
            "ext": Path(name).suffix.lower(),
            "bytes": originals[0].stat().st_size if originals else 0,
            "file_present": bool(originals),
            "thread": thread_name,
        })

    # Thread folders are named "<YYYY-MM-DD> <subject>", so the name sorts by
    # date. Oldest first, matching the thread pipeline, so an interrupted run
    # leaves a contiguous summarized span rather than holes.
    due.sort(key=lambda f: f["thread"], reverse=newest_first)
    return {"total_files": total, "summarized": summarized, "due": len(due),
            "orphans_without_note": orphans,
            "selected": due[:limit] if limit > 0 else due}


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick the next attachments to summarize.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--limit", type=int, default=10,
                        help="Maximum files to return. 0 for all -- reporting only.")
    parser.add_argument("--newest-first", action="store_true")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    print(json.dumps(select(Path(args.vault_path), limit=args.limit,
                            newest_first=args.newest_first), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
