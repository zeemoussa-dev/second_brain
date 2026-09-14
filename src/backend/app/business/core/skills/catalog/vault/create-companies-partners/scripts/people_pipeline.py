"""The People pipeline: every Person note filed under the company it belongs to,
exactly once (operator, 2026-09-11: "The Pipeline Move the Notes if the note
already exists It should Delete if the data in the person changed it should go
for a log").

Capture writes every Person note to the flat `Work/People/` folder, and writes
it there AGAIN on the next message from someone already filed -- so a filed
person keeps growing a flat duplicate. This pass handles both halves:

  MOVE    a flat Person whose email domain (or an alias of one) belongs to a
          Customer/Partner hub goes into that hub's `People/` folder, with the
          company link line and tag.

  MERGE   a flat Person who is ALREADY filed is a duplicate capture recreated.
          Blank fields on the filed note are filled from it. A field where the
          two DISAGREE is recorded in the filed note's `## History` -- the value
          already there is kept, and the newer one is logged rather than
          silently overwriting it or silently dropping it. Then the duplicate is
          deleted.

A duplicate carrying text someone WROTE -- anything beyond the company link
line capture adds -- is never deleted: it is reported for review instead. A
Person whose domain matches no hub (internal staff, personal addresses, a
company not yet created) stays where it is.

A note another process has open is SKIPPED, never fatal. On Windows a rename
or delete fails while any process holds the file, and capture opens Person
notes constantly -- the first live run died on one busy file and left the
rest unfiled. A skipped person is simply filed on the next run.

Moves are one `os.replace`, so an interrupted run cannot leave a person in two
places. Every path goes through `long_path`: a hub's `Affiliates/<name>/People/`
folder is deep.

    python people_pipeline.py [--vault-path P] [--dry-run] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import vault_manager as vm

import create_companies_partners as ccp

# `email` is the note's identity and its filename; it is never compared.
_FIELDS = ("name", "department", "role", "company", "phone", "linkedin")
_SPACES = re.compile(r"\s+")
_LINK_LINE = re.compile(r"^\*\*(Customer|Partner):\*\* \[\[.+\]\]$")


def _norm(value) -> str:
    return _SPACES.sub(" ", str(value or "")).strip()


def _hub_by_domain(vault_path: Path) -> dict[str, tuple[Path, str]]:
    """domain -> (hub note, "customer"|"partner"), from each hub's domain AND
    aliases. First hub claiming a domain keeps it -- a domain on two hubs is an
    Entities.md curation error, not something to resolve by guessing."""
    index: dict[str, tuple[Path, str]] = {}
    for hub_md, kind in ccp._iter_hub_notes(vault_path):
        frontmatter, _ = vm.read_note(hub_md)
        aliases = frontmatter.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        for domain in (ccp._split_domains(frontmatter.get("domain") or "")
                       + ccp._split_domains(",".join(str(a) for a in aliases))):
            index.setdefault(domain, (hub_md, kind))
    return index


def _written_by_someone(body: str) -> bool:
    """True when a note carries anything beyond the link line capture adds."""
    return any(line.strip() and not _LINK_LINE.match(line.strip())
               for line in body.splitlines())


def _change_key(entry: str) -> str:
    """An entry minus its date, so the same change is recognised on a retry."""
    return entry.split(" · ", 1)[-1].strip()


def _append_history(note: Path, entries: list[str]) -> int:
    """Appends to the END of the note's `## History` section, creating it when
    absent -- never into whatever section happens to come last. Skips an entry
    already logged: a merge interrupted between logging and deleting the
    duplicate is retried on the next run, and must not log the change twice.
    Returns how many entries were actually written."""
    frontmatter, body = vm.read_note(note)
    lines = body.rstrip("\n").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## History")
    except StopIteration:
        lines += ["", "## History", ""]
        start = len(lines) - 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    already = {_change_key(line) for line in lines[start + 1:end] if line.strip()}
    fresh = [e for e in entries if _change_key(e) not in already]
    if not fresh:
        return 0
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = fresh
    vm.write_note(note, frontmatter, "\n".join(lines) + "\n")
    return len(fresh)


def run(vault_path: Path, *, dry_run: bool = False) -> dict:
    today = date.today().isoformat()
    hubs = _hub_by_domain(vault_path)
    flat_dir = vault_path / "Work" / "People"
    moved = duplicates_removed = fields_filled = changes_logged = left_flat = 0
    needs_review: list[str] = []
    busy: list[str] = []
    changes_sample: list[str] = []

    for person in sorted(flat_dir.glob("*.md")) if flat_dir.is_dir() else []:
        try:
            frontmatter, body = vm.read_note(person)
        except OSError:
            busy.append(person.name)
            continue
        if frontmatter.get("type") != "Person":
            continue
        email = _norm(frontmatter.get("email") or person.stem).lower()
        hit = hubs.get(email.rsplit("@", 1)[1]) if "@" in email else None
        if hit is None:
            left_flat += 1
            continue
        hub_md, kind = hit
        target_dir = hub_md.parent / "People"
        target = target_dir / person.name
        label = "Customer" if kind == "customer" else "Partner"

        if not os.path.isfile(vm.long_path(target)):
            if not dry_run:
                try:
                    os.makedirs(vm.long_path(target_dir), exist_ok=True)
                    os.replace(vm.long_path(person), vm.long_path(target))
                except OSError:
                    busy.append(person.name)
                    continue
                try:
                    vm.insert_body_line_if_missing(target, f"**{label}:** [[{hub_md.stem}]]")
                    vm.merge_tags(target, [f"{kind}/{ccp._tag_slug(hub_md.stem)}"])
                except OSError:
                    pass  # the move landed; the nightly retag adds the link and tag
            moved += 1
            continue

        # Already filed: this flat copy is one capture recreated.
        if _written_by_someone(body):
            needs_review.append(person.name)
            continue
        filed, _ = vm.read_note(target)
        fills: dict[str, str] = {}
        changes: list[str] = []
        for key in _FIELDS:
            newer, kept = _norm(frontmatter.get(key)), _norm(filed.get(key))
            if not newer:
                continue
            if not kept:
                fills[key] = newer
            elif newer.casefold() != kept.casefold():
                changes.append(f'- {today} · {key}: "{kept}" → "{newer}" '
                               "(seen in a newer capture; the existing value was kept)")
        logged = len(changes)
        if not dry_run:
            try:
                if fills:
                    vm.update(vault_path, target, frontmatter=fills)
                new_tags = [t for t in (frontmatter.get("tags") or [])
                            if t not in (filed.get("tags") or [])]
                if new_tags:
                    vm.merge_tags(target, new_tags)
                logged = _append_history(target, changes) if changes else 0
                os.remove(vm.long_path(person))
            except OSError:
                busy.append(person.name)
                continue
        duplicates_removed += 1
        fields_filled += len(fills)
        changes_logged += logged
        changes_sample.extend(f"{person.stem}: {c[2:]}" for c in changes[:1])

    return {
        "status": "dry-run" if dry_run else "complete",
        "moved_into_hubs": moved,
        "duplicates_removed": duplicates_removed,
        "fields_filled": fields_filled,
        "changes_logged": changes_logged,
        "changes_sample": changes_sample[:5],
        "needs_review": needs_review[:20],
        "needs_review_total": len(needs_review),
        # Open in another process at the time; filed on the next run.
        "busy_skipped": len(busy),
        "busy_sample": busy[:5],
        "left_flat_no_hub": left_flat,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="File every Person under its company.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quiet", action="store_true",
                        help="Print nothing when nothing moved, merged or needs review.")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    result = run(Path(args.vault_path), dry_run=args.dry_run)
    # Busy alone stays quiet: it is transient and retried every hour.
    if args.quiet and not (result["moved_into_hubs"] or result["duplicates_removed"]
                           or result["needs_review_total"]):
        return 0
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
