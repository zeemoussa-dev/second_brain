"""Re-applies company tags to attachments from the companies their summaries name.

The applier tags only what resolves AT APPLY TIME. A company that gained a hub
or an alias afterwards ("ADCB" before the alias existed) stayed untagged on
every attachment summarized before then. File reviews are not persisted the way
thread extractions are -- but the summary the model wrote wiki-links every
company it recognised, so those links can be resolved now, against today's
hubs and aliases, without the model reading a single file again.

Only notes whose `type` is Customer or Partner count as companies. The file
applier's own index tests folder shape alone, and an Opportunity nested under a
Customer has the same shape.

Additive and idempotent: tags are only ever added, and a second run adds
nothing. Safe to re-run after any alias or hub is added.

    python retag_files_from_summaries.py [--vault-path P] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import vault_manager as vm

import select_files as s

_WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def _tag_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _company_index(vault_path: Path) -> dict[str, str]:
    """Hub name and aliases, lowercased -> the hub's company tag."""
    index: dict[str, str] = {}
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        base = vault_path / "Work" / root_name
        if not base.is_dir():
            continue
        for hub_dir in list(base.glob("*")) + list(base.glob("*/Affiliates/*")):
            hub_md = hub_dir / f"{hub_dir.name}.md"
            if not hub_md.is_file():
                continue
            frontmatter, _ = vm.read_note(hub_md)
            if frontmatter.get("type") not in ("Customer", "Partner"):
                continue
            tag = f"{kind}/{_tag_slug(hub_dir.name)}"
            aliases = frontmatter.get("aliases") or []
            if isinstance(aliases, str):
                aliases = [aliases]
            for name in [frontmatter.get("name") or hub_dir.name, *aliases]:
                key = str(name).strip().lower()
                if key:
                    index.setdefault(key, tag)
    return index


def run(vault_path: Path, *, dry_run: bool = False) -> dict:
    index = _company_index(vault_path)
    summarized = files_tagged = tags_added = 0
    for _thread, folder in s._attachment_folders(vault_path):
        notes = sorted(e.name for e in s._scan(folder)
                       if e.is_file() and e.name.lower().endswith(".md"))
        if not notes:
            continue
        note = folder / notes[0]
        summary = vm.get_section_content(note, "Summary") or ""
        if not summary.strip():
            continue
        summarized += 1
        wanted = {index[name.strip().lower()] for name in _WIKILINK.findall(summary)
                  if name.strip().lower() in index}
        new = sorted(wanted - set(vm.read_note(note)[0].get("tags") or []))
        if new:
            if not dry_run:
                vm.merge_tags(note, new)
            files_tagged += 1
            tags_added += len(new)
    return {"status": "dry-run" if dry_run else "complete",
            "summarized_files": summarized, "files_tagged": files_tagged,
            "tags_added": tags_added}


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-apply company tags from file summaries.")
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
