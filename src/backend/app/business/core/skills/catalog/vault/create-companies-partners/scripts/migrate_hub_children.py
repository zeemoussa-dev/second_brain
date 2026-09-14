"""Migrates existing hub notes to the current template shape.

Covers every folder that can own a `-log` child: Customer and Partner hubs,
their Affiliates, and the Opportunities filed under a Customer (2026-09-14 --
the traversal previously reached 21 of this vault's 58 such notes, see
`_note_folders`).

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

import vault_manager as vm

_CAPTURES_INTRO = (
    "Anything worth remembering about this relationship.\n\n"
    "Write your own notes under **Notes**. Automated captures are appended under\n"
    "**Captured** with their source, and never touch what you wrote.\n"
)

# The order the templates declare.
_SECTION_ORDER = ("Summary", "Personal Notes", "Actions", "Related",
                  "Affiliates", "History & Captures")

_SECTION_SPLIT = re.compile(r"^## ", re.M)


# Every filesystem call below goes through vault_manager.long_path. This
# vault really does hold notes past Windows' 260-char MAX_PATH -- an
# Opportunity under an Affiliate with a long title -- and there the two
# failure modes differ: os.rename RAISES (it killed this migration partway
# on 2026-09-14, after 26 of 58 notes), while Path.is_file() silently
# returns False, which would be worse: those notes would be reported as
# migrated without ever being touched.
def _read(path: Path) -> str:
    with open(vm.long_path(path), encoding="utf-8") as handle:
        return handle.read()


def _write(path: Path, text: str) -> None:
    with open(vm.long_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _exists(path: Path) -> bool:
    return os.path.isfile(vm.long_path(path))


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


def _note_folders(vault_path: Path):
    """Every folder holding a `<name>/<name>.md` note that can own a `-log`
    child, as `(folder, is_entity_hub)`.

    Three real shapes, enumerated rather than discovered by a recursive walk
    -- a blind walk would also sweep up `Files/<anything>/` and any future
    nested folder, and a migration that renames notes must only ever touch
    what it was pointed at.

    The list this replaced named `Work/Opportunities` as a top-level root.
    No such folder exists or ever did: an Opportunity lives under the entity
    it belongs to, so that entry could never match and all 26 Opportunity
    `-log.md` notes in this vault were silently skipped. The same loop also
    only ever read each root's DIRECT children, so `*/Affiliates/` was
    missed too -- 21 of this vault's 58 such notes covered.
    """
    work = vault_path / "Work"
    for root_name in ("Customers", "Partners"):
        base = work / root_name
        if not base.is_dir():
            continue
        for hub_dir in sorted(_subfolders(base)):
            yield from _entity_with_descendants(hub_dir)


def _subfolders(base: Path):
    """Real child folders -- `_`-prefixed ones are this vault's own
    excluded/archive convention and must never be migrated."""
    return (p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_"))


def _entity_with_descendants(entity_dir: Path):
    """One entity hub, its Opportunities, and its Affiliates -- recursively,
    because an Affiliate is itself an entity that can own both.

    Recursion is not over-engineering here: this vault really does hold
    `Partners/G42/Affiliates/M42/Affiliates/Diaverum` and seven
    Opportunities filed under an Affiliate rather than under the top-level
    Customer. A fixed two-level walk left exactly those 8 notes behind.
    """
    yield entity_dir, True
    opportunities = entity_dir / "Opportunities"
    if opportunities.is_dir():
        for opportunity_dir in sorted(_subfolders(opportunities)):
            yield opportunity_dir, False
    affiliates = entity_dir / "Affiliates"
    if affiliates.is_dir():
        for affiliate_dir in sorted(_subfolders(affiliates)):
            yield from _entity_with_descendants(affiliate_dir)


def migrate(vault_path: Path, *, dry_run: bool) -> dict:
    renamed = sections_renamed = links_repointed = 0
    captures_structured = sections_reordered = hubs_seen = 0

    for hub_dir, is_entity_hub in _note_folders(vault_path):
        hub_md = hub_dir / f"{hub_dir.name}.md"
        if not _exists(hub_md):
            continue
        hubs_seen += 1

        old_log = hub_dir / f"{hub_dir.name}-log.md"
        new_log = hub_dir / f"{hub_dir.name}-history.md"
        if _exists(old_log) and not _exists(new_log):
            if not dry_run:
                os.rename(vm.long_path(old_log), vm.long_path(new_log))
                text = _read(new_log)
                text = text.replace('type: "Log"', 'type: "History"')
                text = text.replace(f"{hub_dir.name} Log", f"{hub_dir.name} History")
                text = text.replace('"kind/log"', '"kind/history"')
                text = re.sub(r"^# .*Log\s*$", f"# {hub_dir.name} History",
                              text, count=1, flags=re.M)
                _write(new_log, text)
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
            _write(hub_md, updated)

        # Entity hubs only. An Opportunity also has a captures note, but
        # giving it the Notes/Captured split is a change to how that note is
        # written, not part of renaming log to history -- it belongs to
        # whoever decides that, not to this retrofit.
        captures = hub_dir / f"{hub_dir.name}-captures.md"
        if is_entity_hub and _exists(captures):
            text = _read(captures)
            if "## Captured" not in text:
                if not dry_run:
                    body = text.rstrip("\n")
                    if "## Notes" not in body:
                        body += "\n\n" + _CAPTURES_INTRO + "\n## Notes\n"
                    body += "\n## Captured\n"
                    _write(captures, body + "\n")
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
