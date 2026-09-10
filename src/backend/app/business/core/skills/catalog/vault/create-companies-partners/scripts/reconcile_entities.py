"""Makes the vault's folders agree with Entities.md.

Creation already handles "this entity has no folder yet". This handles the
three ways an entity that ALREADY has a folder can drift out of place, all of
them caused by the operator editing Entities.md after the fact -- which is the
intended way to reclassify (operator, 2026-09-10: "I am thinking of a task that
runs once ever night to scan and re tag / Moving Partner to Customer and Vis
Versa Should move throw the vault not creating double").

  1. RECLASSIFY -- the entry moved between the `## Companies` and `## Partners`
     sections, but its folder is still under the old root. The whole folder
     moves (People, History, Captures, Affiliates and all), the stale
     `partner/<slug>` tag is removed vault-wide, `customer/<slug>` replaces it,
     and every Person note's `**Partner:**` line becomes `**Customer:**`.

  2. RE-PARENT -- `Affiliate of` was filled in (or changed) after the entity was
     already created top-level. The folder moves under
     `<parent>/Affiliates/<name>`, the new parent's `## Affiliates` section gains
     the back-link and the old parent's loses it.

  3. DELETE -- `Deleted: Yes`. The folder goes; the tags stay (operator,
     2026-09-10: "Moving Partner or Customer to Delete should delete their
     Folder tags can Still exist its find"). People are moved back to
     `Work/People/` FIRST, never deleted with the folder: capture would recreate
     the note but not the department or job title enrichment had filled in, so
     deleting them destroys work that a folder deletion was never asked to
     touch.

A move is `os.replace` of the directory -- one atomic rename, not a copy-then-
delete, so an interrupted run cannot leave the same entity in two places. That
is the whole point of "should move throw the vault not creating double".

    python reconcile_entities.py [--vault-path P] [--entities-name Entities.md]
                                 [--dry-run] [--allow-delete]

Deletion needs `--allow-delete` explicitly. Everything else is a move, which is
recoverable by moving back; a deletion is not, and the nightly pass runs
unattended.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import vault_manager as vm

import create_companies_partners as ccp

_CALLER = "reconcile_entities"


def _entity_folders(vault_path: Path) -> dict[str, tuple[Path, str, str | None]]:
    """slug -> (folder, "customer"|"partner", parent slug or None).

    Found by walking, not by asking Entities.md where a folder ought to be --
    the whole job here is finding folders that are NOT where the file says."""
    found: dict[str, tuple[Path, str, str | None]] = {}
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        base = vault_path / "Work" / root_name
        if not base.is_dir():
            continue
        for top in sorted(p for p in base.iterdir() if p.is_dir()):
            if (top / f"{top.name}.md").is_file():
                found[top.name] = (top, kind, None)
            affiliates = top / "Affiliates"
            if affiliates.is_dir():
                for child in sorted(p for p in affiliates.iterdir() if p.is_dir()):
                    if (child / f"{child.name}.md").is_file():
                        found[child.name] = (child, kind, top.name)
    return found


def _retag_vault(vault_path: Path, old_tag: str, new_tag: str) -> int:
    """Swaps one company tag for another everywhere it appears.

    Deliberately NOT `merge_tags` plus a separate cleanup: leaving the old tag
    behind is exactly the "double" the operator asked this to avoid -- a
    reclassified company would answer to both `partner/x` and `customer/x`
    forever, and every tag-driven view would show it twice."""
    changed = 0
    for note in vm.iter_md_files(vault_path):
        frontmatter, _ = vm.read_note(note)
        tags = frontmatter.get("tags") or []
        if old_tag not in tags:
            continue
        rebuilt = [new_tag if t == old_tag else t for t in tags]
        # dict.fromkeys, not set(): a note that already carried BOTH tags must
        # not have its remaining tag order shuffled as a side effect.
        vm.update(vault_path, note, frontmatter={"tags": list(dict.fromkeys(rebuilt))})
        changed += 1
    return changed


def _relabel_people(folder: Path, old_label: str, new_label: str, hub_stem: str) -> int:
    """`**Partner:** [[X]]` -> `**Customer:** [[X]]` on every Person note under
    a reclassified entity. The line is what a reader sees; leaving it stale
    makes the note contradict its own tag."""
    changed = 0
    for person in folder.rglob("*.md"):
        if not person.is_file():
            continue
        text = person.read_text(encoding="utf-8")
        old_line = f"**{old_label}:** [[{hub_stem}]]"
        if old_line not in text:
            continue
        person.write_text(text.replace(old_line, f"**{new_label}:** [[{hub_stem}]]"),
                          encoding="utf-8")
        changed += 1
    return changed


def _move_folder(source: Path, target: Path, *, dry_run: bool) -> bool:
    if target.exists():
        return False
    if dry_run:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)
    return True


def _set_affiliate_link(hub_md: Path, child_stem: str, *, present: bool) -> bool:
    """Adds or removes one wikilink in a hub's `## Affiliates` section."""
    if not hub_md.is_file():
        return False
    link = f"- [[{child_stem}]]"
    text = hub_md.read_text(encoding="utf-8")
    has = any(line.strip() == link for line in text.splitlines())
    if has == present:
        return False
    if present:
        return vm.insert_body_line_if_missing(hub_md, link)
    kept = [line for line in text.splitlines() if line.strip() != link]
    hub_md.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return True


def reconcile(vault_path: Path, entities_path: Path, *, dry_run: bool = False,
              allow_delete: bool = False) -> dict:
    entries = ccp.parse_entities(entities_path.read_text(encoding="utf-8"))
    folders = _entity_folders(vault_path)

    reclassified: list[str] = []
    reparented: list[str] = []
    deleted: list[str] = []
    people_rescued = 0
    notes_retagged = 0
    people_relabelled = 0
    refused: list[str] = []

    for entry in entries:
        name = ccp._entry_name(entry)
        slug = ccp._slugify(name)
        placed = folders.get(slug)
        if placed is None:
            continue                       # nothing on disk yet -- creation's job
        folder, actual_kind, actual_parent = placed
        fields = entry["fields"]
        wanted_kind = entry["section"]
        wanted_parent_name = (fields.get("Affiliate of") or "").strip()
        wanted_parent = ccp._slugify(wanted_parent_name) if wanted_parent_name else None
        is_deleted = (fields.get("Deleted") or "").strip().lower().startswith("y")

        if is_deleted:
            if not allow_delete:
                refused.append(f"{name}: marked Deleted, needs --allow-delete")
                continue
            flat_people = vault_path / "Work" / "People"
            for person in list((folder / "People").glob("*.md")) if (folder / "People").is_dir() else []:
                destination = flat_people / person.name
                if destination.exists():
                    continue
                if not dry_run:
                    flat_people.mkdir(parents=True, exist_ok=True)
                    os.replace(person, destination)
                people_rescued += 1
            if not dry_run:
                shutil.rmtree(folder)
            deleted.append(name)
            continue

        # Reclassification and re-parenting resolve to ONE target path, so they
        # are computed together -- an entity can change both in the same edit,
        # and moving twice would leave the first move's back-links dangling.
        target_root = vault_path / "Work" / ccp._hub_root(wanted_kind)
        if wanted_parent:
            parent_placed = folders.get(wanted_parent)
            if parent_placed is None:
                refused.append(f"{name}: parent {wanted_parent_name!r} has no folder yet")
                continue
            target = parent_placed[0] / "Affiliates" / slug
        else:
            target = target_root / slug

        if target == folder:
            continue

        if not _move_folder(folder, target, dry_run=dry_run):
            refused.append(f"{name}: {target} already exists, refusing to merge")
            continue

        if actual_kind != wanted_kind:
            old_tag = f"{actual_kind}/{ccp._tag_slug(slug)}"
            new_tag = f"{wanted_kind}/{ccp._tag_slug(slug)}"
            old_label = "Customer" if actual_kind == "customer" else "Partner"
            new_label = "Customer" if wanted_kind == "customer" else "Partner"
            if not dry_run:
                notes_retagged += _retag_vault(vault_path, old_tag, new_tag)
                people_relabelled += _relabel_people(target, old_label, new_label, slug)
                hub_md = target / f"{slug}.md"
                if hub_md.is_file():
                    vm.update(vault_path, hub_md,
                              frontmatter={"type": new_label})
            reclassified.append(f"{name}: {actual_kind} -> {wanted_kind}")

        if actual_parent != wanted_parent:
            if not dry_run:
                if actual_parent:
                    _set_affiliate_link(folder.parent.parent / f"{actual_parent}.md",
                                        slug, present=False)
                if wanted_parent:
                    _set_affiliate_link(target.parent.parent / f"{wanted_parent}.md",
                                        slug, present=True)
                vm.update(vault_path, target / f"{slug}.md",
                          frontmatter={"affiliate_of": wanted_parent_name})
            reparented.append(f"{name}: {actual_parent or 'top-level'} -> "
                              f"{wanted_parent_name or 'top-level'}")
        # The index is now stale for this slug; a later entry pointing at it as
        # a parent must see where it actually landed.
        folders[slug] = (target, wanted_kind, wanted_parent)

    return {
        "status": "dry-run" if dry_run else "complete",
        "reclassified": reclassified,
        "reparented": reparented,
        "deleted": deleted,
        "people_rescued_from_deleted_folders": people_rescued,
        "notes_retagged": notes_retagged,
        "people_relabelled": people_relabelled,
        "refused": refused,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Make vault folders agree with Entities.md.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--entities-name", default="Entities.md")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-delete", action="store_true",
                        help="Actually remove the folder of an entry marked Deleted. "
                             "Without it such an entry is reported and skipped.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    vault_path = Path(args.vault_path)
    entities_path = vm.data_root(vault_path) / "Settings" / args.entities_name
    if not entities_path.is_file():
        print(json.dumps({"error": f"no {entities_path}"}))
        return 2
    print(json.dumps(reconcile(vault_path, entities_path, dry_run=args.dry_run,
                               allow_delete=args.allow_delete), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
