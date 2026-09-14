"""Writes each company's History from the SAVED extractions -- no model.

The Company pipeline's History step. Every Thread a company is named in gets a
dated line in that company's History, linking back to it. Enrichment saves each
read before anything is applied, so this never needs the model; an extraction
saved before `history_line` existed uses the first sentence of its summary.

One entry per Thread per company, replaced rather than repeated, so this is
idempotent and safe to re-run -- after a hub or alias is added, a company named
before it existed gets its entry too.

    python history_from_extracts.py [--vault-path P] [--dry-run]
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
    hubs = ate._company_hub_notes(vault_path)          # once, not per Thread
    extracts = sorted(ate._extracts_dir().glob("*.json"))
    threads_logged = entries_written = missing = 0

    for path in extracts:
        extraction = json.loads(path.read_text(encoding="utf-8"))
        if not extraction.get("companies"):
            continue
        thread = ate.resolve_thread(vault_path, extraction, path.stem)
        if thread is None:
            missing += 1
            continue
        frontmatter, _ = vm.read_note(thread)
        written = ate.write_history(vault_path, thread, frontmatter, extraction,
                                    hubs=hubs, dry_run=dry_run)
        if written:
            threads_logged += 1
            entries_written += len(written)

    return {"status": "dry-run" if dry_run else "complete",
            "extractions_read": len(extracts), "threads_logged": threads_logged,
            "history_entries_written": entries_written, "threads_not_found": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description="Write company History from saved extractions.")
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
