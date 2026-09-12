"""Files each Thread's important facts in the right company's Captures -- no model.

The Company pipeline's Captures step. The reader of a Thread records the facts
worth remembering about a relationship beyond that conversation -- a budget
approved, a reorganisation, a new decision-maker -- each naming the company it
belongs to. This files them, from the SAVED extraction, into that company's
captures note:

    ## Captured
    - 2026-06-18: Budget approved for the Q1 pilot -- [[<Thread>]]

Only ever the `## Captured` section. `## Notes` is the operator's own and is
never touched. Newest first. A Thread's facts for a company are REPLACED as a
set when it is read again, never accumulated, so this is idempotent. A fact that
names no company, or one with no hub, is counted -- never guessed at.

    python captures_from_extracts.py [--vault-path P] [--dry-run]
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

_ENTRY = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")
_WHITESPACE = re.compile(r"\s+")

# The words migrate_hub_children.py gives a captures note, so a note this
# structures reads the same as one it did.
_CAPTURES_INTRO = (
    "Anything worth remembering about this relationship.\n\n"
    "Write your own notes under **Notes**. Automated captures are appended under\n"
    "**Captured** with their source, and never touch what you wrote.\n"
)


def _captures_update(hub_md: Path, date: str, facts: list[str], thread_link: str):
    """(captures note, frontmatter, new body) -- or None when nothing changes."""
    note = hub_md.parent / f"{hub_md.stem}-captures.md"
    if os.path.isfile(vm.long_path(note)):
        frontmatter, body = vm.read_note(note)
    else:
        frontmatter = {"type": "Captures", "name": f"{hub_md.stem} Captures",
                       "parent": f"[[{hub_md.stem}]]", "tags": ["kind/captures"]}
        body = f"\n# {hub_md.stem}\n"
    lines = body.rstrip("\n").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Captured")
    except StopIteration:
        # A hub created after the migration ran has a bare captures note. It
        # gets the operator's Notes section too, so there is somewhere to write
        # that nothing here will ever touch.
        if not any(line.strip() == "## Notes" for line in lines):
            lines += ["", *_CAPTURES_INTRO.rstrip("\n").splitlines(), "", "## Notes"]
        lines += ["", "## Captured"]
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    section = lines[start + 1:end]
    entries = [m.groups() for line in section if (m := _ENTRY.match(line.strip()))]
    # Anything in Captured that is not an entry was written by someone -- kept.
    written_by_hand = [line for line in section if line.strip() and not _ENTRY.match(line.strip())]
    suffix = f" -- {thread_link}"
    updated = [(d, t) for d, t in entries if not t.endswith(suffix)]
    updated += [(date, f"{fact}{suffix}") for fact in facts]
    updated = list(dict.fromkeys(updated))
    if set(updated) == set(entries):
        return None
    updated.sort(key=lambda entry: entry[0], reverse=True)
    new_section = [""] + written_by_hand + ([""] if written_by_hand else [])
    new_section += [f"- {d}: {t}" for d, t in updated] + [""]
    lines[start + 1:end] = new_section
    return note, frontmatter, "\n".join(lines).rstrip("\n") + "\n"


def run(vault_path: Path, *, dry_run: bool = False) -> dict:
    hubs = ate._company_hub_notes(vault_path)            # once, not per Thread
    extracts = sorted(ate._extracts_dir().glob("*.json"))
    notes_written = facts_filed = facts_unresolved = missing = 0
    today = datetime.now(timezone.utc).date().isoformat()

    for path in extracts:
        extraction = json.loads(path.read_text(encoding="utf-8"))
        items = [item for item in (extraction.get("important_info") or [])
                 if isinstance(item, dict) and _WHITESPACE.sub(" ", str(item.get("text") or "")).strip()]
        if not items:
            continue
        thread = ate.resolve_thread(vault_path, extraction, path.stem)
        if thread is None:
            missing += 1
            continue
        frontmatter, _ = vm.read_note(thread)
        date = str(frontmatter.get("last_message_at") or "")[:10] or today
        by_hub: dict[Path, list[str]] = {}
        for item in items:
            named = str(item.get("company") or "").strip()
            hub_md = hubs.get(named.lower()) or hubs.get(ate.normalise_company(named))
            if hub_md is None:
                facts_unresolved += 1
                continue
            fact = _WHITESPACE.sub(" ", str(item["text"])).strip().rstrip(".")
            by_hub.setdefault(hub_md, []).append(fact)
        for hub_md, facts in by_hub.items():
            update = _captures_update(hub_md, date, list(dict.fromkeys(facts)), f"[[{thread.stem}]]")
            if update is None:
                continue
            if not dry_run:
                vm.write_note(*update)
            notes_written += 1
            facts_filed += len(facts)

    return {"status": "dry-run" if dry_run else "complete",
            "extractions_read": len(extracts), "captures_notes_written": notes_written,
            "facts_filed": facts_filed, "facts_unresolved": facts_unresolved,
            "threads_not_found": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description="File saved important facts into company Captures.")
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
