"""What does this capture refer to? Read-only, writes nothing.

The CBO says "met the CEO of TAQA today, very positive, we agreed the Q1
scope". Before any of that can be filed, two things have to be pinned down
against the vault rather than guessed: WHICH company, and WHICH people. Both
have real traps -- "TAQA" and "TAQA Distribution" are different companies, and
three people can share a first name -- so this reports what it found and says
plainly when the answer is not unique. The agent asks; it never picks.

    python resolve_capture.py --company "TAQA" [--person "Jasim"] ... [--vault-path P]

Prints JSON: {"company": {...}, "people": [...]}, each with a `status` of
"one", "ambiguous" or "none".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
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


def _person_records(vault_path: Path, folders: list[Path]) -> list[dict]:
    people: list[dict] = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for note in sorted(folder.glob("*.md")):
            try:
                frontmatter, _ = vm.read_note(note)
            except OSError:
                continue
            if frontmatter.get("type") != "Person":
                continue
            people.append({
                "name": str(frontmatter.get("name") or note.stem),
                "email": str(frontmatter.get("email") or note.stem),
                "role": str(frontmatter.get("role") or ""),
                "path": str(note),
            })
    return people


_WORD = re.compile(r"[\w']+")


def _match_people(query: str, people: list[dict]) -> list[dict]:
    """Exact email first -- an address is unambiguous. Otherwise match whole
    NAME WORDS, so "Mir" finds "Dawar Ali Mir" and not "Emirates", which is
    what a plain substring match did (2026-09-12). A multi-word query is also
    matched against the whole name, so "Dawar Ali" still works."""
    wanted = str(query or "").strip().lower()
    if not wanted:
        return []
    exact = [p for p in people if p["email"].lower() == wanted]
    if exact:
        return exact
    if " " in wanted:
        return [p for p in people if wanted in p["name"].lower()]
    return [p for p in people
            if any(word == wanted or word.startswith(wanted)
                   for word in _WORD.findall(p["name"].lower()))]


def resolve(vault_path: Path, company: str, persons: list[str]) -> dict:
    records = ci.hubs(vault_path)
    matches = ci.resolve(vault_path, company, records=records)
    company_block = {
        "query": company,
        "status": "one" if len(matches) == 1 else ("ambiguous" if matches else "none"),
        "matches": [{"name": m["name"], "kind": m["kind"], "tag": m["tag"], "path": m["path"],
                     "parent": m["parent"], "affiliates": m["affiliates"]} for m in matches],
    }
    if not matches:
        # Nearly always the affiliate/parent trap or a company nobody has
        # classified yet. Offer the neighbours rather than a silent empty list.
        wanted = ci.normalise_company(company)
        company_block["did_you_mean"] = sorted(
            r["name"] for r in records
            if wanted and (wanted in ci.normalise_company(r["name"])
                           or ci.normalise_company(r["name"]) in wanted)
        )[:5]

    folders: list[Path] = []
    if len(matches) == 1:
        folders.append(Path(matches[0]["path"]).parent / "People")
    folders.append(vault_path / "Work" / "People")
    known = _person_records(vault_path, folders)

    people_blocks = []
    for person in persons:
        found = _match_people(person, known)
        people_blocks.append({
            "query": person,
            "status": "one" if len(found) == 1 else ("ambiguous" if found else "none"),
            "matches": found[:6],
        })
    return {"company": company_block, "people": people_blocks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a capture's company and people.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--person", action="append", default=[],
                        help="Repeatable: a name or an email address, as it was said.")
    parser.add_argument("--vault-path", default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""))
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        print(json.dumps({"error": "SECOND_BRAIN_VAULT_PATH is not set"}))
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(resolve(Path(args.vault_path), args.company, args.person), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
