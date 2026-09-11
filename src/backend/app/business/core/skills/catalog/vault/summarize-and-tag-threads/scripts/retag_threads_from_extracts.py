"""Re-applies company tags to Threads from their SAVED extractions -- no model.

Every extraction is persisted before it is applied, precisely so an applier
change can be re-applied from disk instead of re-reading thousands of Threads
through a model. This is that re-apply, for company tags, and it is needed
twice over:

  - enrichment does not tag. Tagging is its own pipeline, and this is its
    content step for Threads; and
  - a company named before its hub or alias existed ("ADCB" before the alias
    was added) could not resolve at the time, and can now.

Additive and idempotent: tags are only ever added, and a second run adds
nothing. Safe to re-run after any alias or hub is added.

    python retag_threads_from_extracts.py [--vault-path P] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import vault_manager as vm

import apply_thread_extract as ate


def run(vault_path: Path, *, dry_run: bool = False) -> dict:
    index = ate._company_index(vault_path)            # once, not per Thread
    extracts = sorted(ate._extracts_dir().glob("*.json"))
    threads_tagged = tags_added = missing = 0
    unresolved: set[str] = set()

    for path in extracts:
        extraction = json.loads(path.read_text(encoding="utf-8"))
        companies = [c for c in (extraction.get("companies") or []) if c and c.strip()]
        if not companies:
            continue
        thread = Path(extraction.get("thread_path") or "")
        if not thread.is_absolute():
            thread = vault_path / thread
        if not os.path.isfile(vm.long_path(thread)):
            # Renamed since it was read. The extraction is keyed on the id.
            thread = vm.find_by_id(vault_path, path.stem, note_name="Threads")
            if thread is None:
                missing += 1
                continue
        unresolved.update(c for c in companies if c.strip().lower() not in index)
        wanted = {index[c.strip().lower()] for c in companies if c.strip().lower() in index}
        new = sorted(wanted - set(vm.read_note(thread)[0].get("tags") or []))
        if new and not dry_run:
            vm.merge_tags(thread, new)
        if new:
            threads_tagged += 1
            tags_added += len(new)

    return {
        "status": "dry-run" if dry_run else "complete",
        "extractions_read": len(extracts),
        "threads_tagged": threads_tagged,
        "tags_added": tags_added,
        "threads_not_found": missing,
        "names_still_unresolved": len(unresolved),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-apply company tags from saved extractions.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    print(json.dumps(run(Path(args.vault_path), dry_run=args.dry_run), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
