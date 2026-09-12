"""Files ONE engagement capture against its company. The only thing that writes.

The CBO reports an interaction in his own words -- "met the CEO of TAQA
Distribution, positive, we agreed the Q1 scope, they'll send the RFP next
week". The agent turns that into the JSON below; this applies it, deciding
nothing:

    {
      "schema_version": 1,
      "said_at":        "2026-09-12",     # when it happened; today if absent
      "company":        "TAQA Distribution",
      "people":         ["irfan.siddiqui@taqadistribution.com"],
      "history_line":   "Met Irfan Siddiqui (CEO); positive; agreed the Q1 scope",
      "important_info": [{"text": "RFP lands next week"}],
      "actions":        [{"text": "Send revised scope", "owner": "Sherif", "due": "Friday"}]
    }

Where each part lands, and why:

  * `history_line` -> `<Company>-history.md`, a dated line. That file is the
    engagement log; a meeting readout is exactly an event in it.
  * `important_info` -> `<Company>-captures.md` under `## Captured`. Facts that
    outlive the conversation. Never `## Notes`: that is the operator's own
    handwriting and nothing automated writes there.
  * `actions` -> the hub's own `## Actions`, as checkboxes.
  * `people` are wiki-linked into the history line, by the address their note is
    named for, the same way capture links participants.

Every line carries `-- CBO capture` so a fact the operator stated is never
confused with one a model derived from an email. Applying the same capture
twice writes nothing the second time.

    python apply_capture.py --input-file capture.json [--vault-path P] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

def _add_engines_to_path() -> None:
    """Find the shared engines whatever layout this runs in.

    In the repo they are `skills/managers/`; deployed, Hermes puts them in
    `<hermes>/managers/` several levels above the flat Skill folder. Searching
    upward for the folder that actually holds vault_manager.py means a caller
    never has to set PYTHONPATH -- an interactive agent cannot."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "managers" / "vault_manager.py"
        if candidate.is_file():
            if str(candidate.parent) not in sys.path:
                sys.path.insert(0, str(candidate.parent))
            return


_add_engines_to_path()

import company_index as ci  # noqa: E402
import vault_manager as vm  # noqa: E402

_SCHEMA_VERSION = 1
_SOURCE = "CBO capture"
_ENTRY = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+)$")
_WHITESPACE = re.compile(r"\s+")
_CAPTURES_INTRO = (
    "Anything worth remembering about this relationship.\n\n"
    "Write your own notes under **Notes**. Automated captures are appended under\n"
    "**Captured** with their source, and never touch what you wrote.\n"
)


def _clean(text) -> str:
    return _WHITESPACE.sub(" ", str(text or "")).strip()


def _person_links(vault_path: Path, hub_md: Path, people: list[str]) -> tuple[list[str], list[str]]:
    """(wikilinks, names not found). A person nobody has a note for is reported,
    never created -- capture owns creating People, from real message headers."""
    folders = [hub_md.parent / "People", vault_path / "Work" / "People"]
    notes: dict[str, Path] = {}
    for folder in folders:
        if folder.is_dir():
            for note in folder.glob("*.md"):
                notes.setdefault(note.stem.lower(), note)
    links, missing = [], []
    for person in people or []:
        wanted = _clean(person).lower()
        hit = notes.get(wanted)
        if hit is None:
            for stem, note in notes.items():
                frontmatter, _ = vm.read_note(note)
                if wanted and wanted in str(frontmatter.get("name") or "").lower():
                    hit = note
                    break
        if hit is None:
            missing.append(person)
        else:
            links.append(f"[[{hit.stem}]]")
    return links, missing


def _dated_entries(lines: list[str]) -> list[tuple[str, str]]:
    return [m.groups() for line in lines if (m := _ENTRY.match(line.strip()))]


def add_history(hub_md: Path, when: str, line: str, *, dry_run: bool) -> bool:
    """A dated line in the company's History, newest first. The note's header
    and anything written by hand are kept."""
    history = hub_md.parent / f"{hub_md.stem}-history.md"
    if os.path.isfile(vm.long_path(history)):
        frontmatter, body = vm.read_note(history)
    else:
        frontmatter = {"type": "History", "name": f"{hub_md.stem} History",
                       "parent": f"[[{hub_md.stem}]]", "tags": ["kind/history"]}
        body = f"\n# {hub_md.stem}\n"
    lines = body.splitlines()
    entries = _dated_entries(lines)
    if (when, line) in entries:
        return False
    kept = [one for one in lines if not _ENTRY.match(one)]
    entries.append((when, line))
    entries.sort(key=lambda entry: entry[0], reverse=True)
    while kept and not kept[-1].strip():
        kept.pop()
    if not dry_run:
        vm.write_note(history, frontmatter,
                      "\n".join(kept) + "\n\n" + "\n".join(f"- {d}: {t}" for d, t in entries) + "\n")
    return True


def add_captures(hub_md: Path, when: str, facts: list[str], *, dry_run: bool) -> int:
    """Durable facts under `## Captured`, never `## Notes`."""
    if not facts:
        return 0
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
        if not any(line.strip() == "## Notes" for line in lines):
            lines += ["", *_CAPTURES_INTRO.rstrip("\n").splitlines(), "", "## Notes"]
        lines += ["", "## Captured"]
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    section = lines[start + 1:end]
    existing = {(d, t) for d, t in _dated_entries(section)}
    by_hand = [line for line in section if line.strip() and not _ENTRY.match(line.strip())]
    fresh = [(when, fact) for fact in facts if (when, fact) not in existing]
    if not fresh:
        return 0
    entries = sorted(existing | set(fresh), key=lambda entry: entry[0], reverse=True)
    rebuilt = [""] + by_hand + ([""] if by_hand else [])
    rebuilt += [f"- {d}: {t}" for d, t in entries] + [""]
    lines[start + 1:end] = rebuilt
    if not dry_run:
        vm.write_note(note, frontmatter, "\n".join(lines).rstrip("\n") + "\n")
    return len(fresh)


def add_actions(hub_md: Path, actions: list[dict], *, dry_run: bool) -> int:
    """Commitments as checkboxes in the hub's own `## Actions`. There is no
    meeting-notes system yet, so the company is where they belong."""
    wanted = []
    for action in actions or []:
        text = _clean(action.get("text"))
        if not text:
            continue
        suffix = " — ".join(part for part in (_clean(action.get("owner")), _clean(action.get("due"))) if part)
        wanted.append(f"- [ ] {text}" + (f" ({suffix})" if suffix else ""))
    if not wanted:
        return 0
    frontmatter, body = vm.read_note(hub_md)
    lines = body.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Actions")
    except StopIteration:
        lines += ["", "## Actions", ""]
        start = len(lines) - 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    section = [line.strip() for line in lines[start + 1:end]]
    fresh = [one for one in wanted if one not in section]
    if not fresh:
        return 0
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = fresh
    if not dry_run:
        vm.write_note(hub_md, frontmatter, "\n".join(lines) + "\n")
    return len(fresh)


def apply_capture(vault_path: Path, capture: dict, *, dry_run: bool = False) -> dict:
    version = capture.get("schema_version")
    if version != _SCHEMA_VERSION:
        raise SystemExit(
            f"capture schema_version {version!r}, this applier understands "
            f"{_SCHEMA_VERSION}. Refusing rather than writing a shape it may "
            "only partly understand."
        )
    named = _clean(capture.get("company"))
    matches = ci.resolve(vault_path, named)
    if len(matches) != 1:
        raise SystemExit(json.dumps({
            "error": "company did not resolve to exactly one hub -- ask, do not guess",
            "company": named,
            "candidates": [m["name"] for m in matches],
        }, ensure_ascii=False))
    hub_md = Path(matches[0]["path"])

    line = _clean(capture.get("history_line"))
    if not line:
        raise SystemExit("a capture needs a history_line -- what happened, in one line")
    when = _clean(capture.get("said_at")) or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        raise SystemExit(f"said_at {when!r} is not a YYYY-MM-DD date")

    links, missing = _person_links(vault_path, hub_md, capture.get("people") or [])
    if links:
        line = f"{line} (with {', '.join(links)})"
    line = f"{line} -- {_SOURCE}"

    facts = [f"{_clean(item.get('text') if isinstance(item, dict) else item)} -- {_SOURCE}"
             for item in (capture.get("important_info") or [])
             if _clean(item.get("text") if isinstance(item, dict) else item)]

    return {
        "status": "dry-run" if dry_run else "applied",
        "company": matches[0]["name"],
        "hub": str(hub_md),
        "history_written": add_history(hub_md, when, line, dry_run=dry_run),
        "captures_written": add_captures(hub_md, when, facts, dry_run=dry_run),
        "actions_written": add_actions(hub_md, capture.get("actions") or [], dry_run=dry_run),
        "people_linked": len(links),
        "people_not_in_vault": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="File one engagement capture against its company.")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    capture = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    print(json.dumps(apply_capture(Path(args.vault_path), capture, dry_run=args.dry_run),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
