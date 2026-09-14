"""Fills People notes from what each Thread's reader saw -- no model.

The Company pipeline's People step (operator, 2026-09-11: "The Company pipeline
should pull the people as well"). A reader records what a Thread reveals about
the people on it -- almost always from a signature: job title, department,
phone, LinkedIn, employer. This applies it, from the SAVED extraction, to each
person's note wherever the People pipeline has filed them.

The operator's rule for People data applies unchanged: a blank field is FILLED;
a field that already holds a DIFFERENT value keeps it, and the newer one is
logged to that person's `## History` -- never silently overwritten, never
silently dropped:

    - 2026-06-18 · role: "Director" → "VP Engineering" (read in [[<Thread>]]; the existing value was kept)

`name` and `email` are never written: they are the note's identity, set by
capture from real message headers. A person the vault has never seen is counted
and skipped -- capture owns creating People, not a reading of a signature.
Idempotent: a filled field is no longer blank, and a logged change is not
logged twice.

    python people_from_extracts.py [--vault-path P] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import vault_manager as vm

import apply_thread_extract as ate

_WHITESPACE = re.compile(r"\s+")


def _norm(value) -> str:
    return _WHITESPACE.sub(" ", str(value or "")).strip()


def _change_key(entry: str) -> str:
    """An entry minus its date and its source, so the same change is logged
    once -- not again on a re-run, and not once more for every Thread whose
    signature repeats it."""
    return entry.split(" · ", 1)[-1].split(" (", 1)[0].strip()


def _people_index(vault_path: Path) -> dict[str, Path]:
    """Every Person note by lowercased filename, built ONCE per run: a lookup
    per person globbed every hub's People folder, for every person of every
    Thread. Flat folder first -- where capture writes -- then filed under a
    company, Affiliates included, the same order `_person_note` searches."""
    work = vault_path / "Work"
    index: dict[str, Path] = {}
    searches = [(work / "People", "*.md")] + [
        (work / root, pattern) for root in ("Customers", "Partners")
        for pattern in ("*/People/*.md", "*/Affiliates/*/People/*.md")]
    for base, pattern in searches:
        if base.is_dir():
            for note in base.glob(pattern):
                index.setdefault(note.name.lower(), note)
    return index


def _append_history(note: Path, entries: list[str], *, dry_run: bool) -> int:
    """Appends to the END of the person's `## History` section, creating it when
    absent, skipping any entry already there. Returns how many it wrote."""
    frontmatter, body = vm.read_note(note)
    lines = body.rstrip("\n").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## History")
    except StopIteration:
        lines += ["", "## History", ""]
        start = len(lines) - 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    already = {_change_key(line) for line in lines[start + 1:end] if line.strip()}
    fresh = [entry for entry in entries if _change_key(entry) not in already]
    if fresh and not dry_run:
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines[end:end] = fresh
        vm.write_note(note, frontmatter, "\n".join(lines) + "\n")
    return len(fresh)


def apply_people(vault_path: Path, extraction: dict, thread_link: str, date: str,
                 *, dry_run: bool = False) -> dict:
    people_filled = fields_filled = changes_logged = not_in_vault = 0
    for person in extraction.get("people") or []:
        note = ate._person_note(vault_path, person.get("email") or "")
        if note is None:
            not_in_vault += 1
            continue
        frontmatter, _ = vm.read_note(note)
        fills: dict[str, str] = {}
        changes: list[str] = []
        for source_key, note_key in ate._PERSON_FIELD_MAP.items():
            newer, kept = _norm(person.get(source_key)), _norm(frontmatter.get(note_key))
            if not newer:
                continue
            if not kept:
                fills[note_key] = newer
            elif newer.casefold() != kept.casefold():
                changes.append(f'- {date} · {note_key}: "{kept}" → "{newer}" '
                               f"(read in {thread_link}; the existing value was kept)")
        if fills:
            if not dry_run:
                vm.update(vault_path, note, frontmatter=fills)
            people_filled += 1
            fields_filled += len(fills)
        if changes:
            changes_logged += _append_history(note, changes, dry_run=dry_run)
    return {"people_filled": people_filled, "fields_filled": fields_filled,
            "changes_logged": changes_logged, "people_not_in_vault": not_in_vault}


def run(vault_path: Path, *, dry_run: bool = False) -> dict:
    extracts = sorted(ate._extracts_dir().glob("*.json"))
    totals = {"people_filled": 0, "fields_filled": 0, "changes_logged": 0, "people_not_in_vault": 0}
    today = datetime.now(timezone.utc).date().isoformat()
    for path in extracts:
        extraction = json.loads(path.read_text(encoding="utf-8"))
        if not extraction.get("people"):
            continue
        thread = ate.resolve_thread(vault_path, extraction, path.stem)
        if thread is not None:
            date = str(vm.read_note(thread)[0].get("last_message_at") or "")[:10] or today
            link = f"[[{thread.stem}]]"
        else:
            # The fields are about the person, not the Thread; a Thread renamed
            # beyond finding still names its people truthfully.
            date, link = today, f"[[{Path(extraction.get('thread_path') or path.stem).stem}]]"
        result = apply_people(vault_path, extraction, link, date, dry_run=dry_run)
        for key in totals:
            totals[key] += result[key]
    return {"status": "dry-run" if dry_run else "complete",
            "extractions_read": len(extracts), **totals}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill People notes from saved extractions.")
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
