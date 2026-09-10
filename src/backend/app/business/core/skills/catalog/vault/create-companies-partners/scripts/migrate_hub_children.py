"""Migrates existing hub notes to the current template shape.

Three changes the templates now declare, which a hub created earlier cannot get
on its own -- a template only shapes notes created AFTER it changed:

  1. `<Name>-log.md` -> `<Name>-history.md`. "Log" reads as machine output;
     "History" is what the note actually holds (operator, 2026-09-11). The
     section indexing it, `## Log & Captures`, becomes `## History & Captures`,
     and its wikilink is repointed.

  2. The captures note gains structure, so a HUMAN can write in it without an
     agent overwriting them and an agent knows where its own entries belong:

         ## Notes      <- the operator's own
         ## Captured   <- appended by agents

     Separating by section rather than by convention is deliberate: it is the
     same human_only / machine_write split the templates already use, so the
     boundary is structural instead of a rule someone has to remember.

  3. Section ORDER. Sections added to an existing hub were appended, leaving
     Summary below Affiliates. Reordered to match the template.

    python migrate_hub_children.py [--vault-path P] [--dry-run]

Idempotent -- a hub already migrated reports zero changes, so this is safe to
leave in the nightly pass.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_CAPTURES_INTRO = (
    "Anything worth remembering about this relationship.\n\n"
    "Write your own notes under **Notes**. Automated captures are appended under\n"
    "**Captured** with their source, and never touch what you wrote.\n"
)

# The order the templates declare.
_SECTION_ORDER = ("Summary", "Personal Notes", "Actions", "Related",
                  "Affiliates", "History & Captures")

_SECTION_SPLIT = re.compile(r"^## ", re.M)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _reorder_sections(text: str) -> str:
    """Puts a hub note's sections into template order, content untouched.

    Every block moves WITH its own content, so nothing can be dropped or
    re-attached to the wrong heading. A heading not in the known order is kept,
    after the known ones -- an unrecognised section is far more likely to be
    something a human added than something safe to discard."""
    parts = _SECTION_SPLIT.split(text)
    if len(parts) < 2:
        return text
    head = parts[0]
    blocks: dict[str, str] = {}
    seen: list[str] = []
    for chunk in parts[1:]:
        name, _, body = chunk.partition("\n")
        name = name.strip()
        if name in blocks:            # duplicate heading: keep the first
            continue
        blocks[name] = body.rstrip("\n")
        seen.append(name)

    ordered = [n for n in _SECTION_ORDER if n in blocks]
    ordered += [n for n in seen if n not in _SECTION_ORDER]
    if ordered == seen:
        return text

    rebuilt = head.rstrip("\n")
    for name in ordered:
        body = blocks[name]
        rebuilt += "\n\n## " + name + "\n" + body + "\n"
    return rebuilt.rstrip("\n") + "\n"


def migrate(vault_path: Path, *, dry_run: bool) -> dict:
    renamed = sections_renamed = links_repointed = 0
    captures_structured = sections_reordered = hubs_seen = 0

    for root_name in ("Customers", "Partners", "Opportunities"):
        base = vault_path / "Work" / root_name
        if not base.is_dir():
            continue
        for hub_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            hub_md = hub_dir / f"{hub_dir.name}.md"
            if not hub_md.is_file():
                continue
            hubs_seen += 1

            old_log = hub_dir / f"{hub_dir.name}-log.md"
            new_log = hub_dir / f"{hub_dir.name}-history.md"
            if old_log.is_file() and not new_log.is_file():
                if not dry_run:
                    old_log.rename(new_log)
                    text = _read(new_log)
                    text = text.replace('type: "Log"', 'type: "History"')
                    text = text.replace(f"{hub_dir.name} Log", f"{hub_dir.name} History")
                    text = text.replace('"kind/log"', '"kind/history"')
                    text = re.sub(r"^# .*Log\s*$", f"# {hub_dir.name} History",
                                  text, count=1, flags=re.M)
                    new_log.write_text(text, encoding="utf-8")
                renamed += 1

            hub_text = _read(hub_md)
            updated = hub_text
            if "## Log & Captures" in updated:
                updated = updated.replace("## Log & Captures", "## History & Captures")
                sections_renamed += 1
            # The index line the engine wrote at creation: `- [[X-log|Log]]`.
            if f"[[{hub_dir.name}-log|" in updated:
                updated = updated.replace(f"[[{hub_dir.name}-log|Log]]",
                                          f"[[{hub_dir.name}-history|History]]")
                links_repointed += 1
            reordered = _reorder_sections(updated)
            if reordered != updated:
                sections_reordered += 1
                updated = reordered
            if updated != hub_text and not dry_run:
                hub_md.write_text(updated, encoding="utf-8")

            captures = hub_dir / f"{hub_dir.name}-captures.md"
            if captures.is_file():
                text = _read(captures)
                if "## Captured" not in text:
                    if not dry_run:
                        body = text.rstrip("\n")
                        if "## Notes" not in body:
                            body += "\n\n" + _CAPTURES_INTRO + "\n## Notes\n"
                        body += "\n## Captured\n"
                        captures.write_text(body + "\n", encoding="utf-8")
                    captures_structured += 1

    return {
        "status": "dry-run" if dry_run else "complete",
        "hubs_seen": hubs_seen,
        "log_notes_renamed": renamed,
        "sections_renamed": sections_renamed,
        "index_links_repointed": links_repointed,
        "captures_structured": captures_structured,
        "sections_reordered": sections_reordered,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    print(json.dumps(migrate(Path(args.vault_path), dry_run=args.dry_run), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
