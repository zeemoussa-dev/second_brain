"""CLI entry point: `vault_manager.py`-based replacement for the original
capture_note.py (Implementation/Plans/2026-08-25-vault-writer-
standardization.md's second real deployment, 2026-08-26 -- operator:
"handle the Notes files uploads"). Same job -- quick-capture note logging,
never asks a question, never blocks -- but the note itself is placed/
written by `vault_manager.py`'s real template-driven `create()` instead of
this file's own hand-rolled slugify/collision/frontmatter logic.

Auto-wikilinking known Customer/Partner names (`_iter_known_entity_names`/
`_auto_wikilink`) is UNCHANGED, reused as-is -- a real, working, generic
vault-scanning helper, not part of the write-mechanics problem
`vault_manager.py` solves.

Real shape, reverted 2026-08-30 (operator: "Notes are organized in
folders by Date") back to the original: `Work/Notes/<date>/<slug>.md`,
date as its own parent folder, no date repeated in the filename -- the
2026-08-26 pass had briefly folded the date into the filename instead
(`Work/Notes/<date>-<title>.md`); that shape is gone now, this file
always writes the folder-per-date shape.

Usage: identical real contract --
    python capture_note.py --vault-path P --input-file F
    F: {"title": str, "summary": str, "body": str}
"""
from __future__ import annotations

import argparse
import os
import json
import re
from datetime import datetime
from pathlib import Path

import vault_manager as vm

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_NOTE_TEMPLATE_ID = "note"
_NOTE_ROOT = "Notes"


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return raw


def _read_note_name(md_path: Path) -> str | None:
    """Best-effort real hub name for auto-linking -- frontmatter `name`, else
    the file's own stem. Returns None on any read failure (never blocks
    capture over a malformed hub note elsewhere in the vault)."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return md_path.stem
    end = text.find("\n---\n", 4)
    if end == -1:
        return md_path.stem
    for line in text[4:end].splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match and match.group(1) == "name":
            return _parse_frontmatter_value(match.group(2)) or md_path.stem
    return md_path.stem


def _iter_known_entity_names(vault_path: Path):
    """Real Customer + Partner hub note names, for best-effort auto-linking
    only -- never a resolution/validation gate."""
    for root_name in ("Customers", "Partners"):
        root = vault_path / "Work" / root_name
        if not root.exists():
            continue
        for md_path in root.glob("*/*.md"):
            if md_path.parent.name != md_path.stem:
                continue
            name = _read_note_name(md_path)
            if name:
                yield name


def _auto_wikilink(text: str, entity_names) -> tuple[str, list[str]]:
    """Best-effort: wrap the first mention of each known Customer/Partner
    name in [[...]]. Longest names first so "Adnoc Gas" doesn't get
    shadowed by a shorter "Adnoc" match. Skips a name already wikilinked
    anywhere in the text. Never raises -- worst case, text passes through
    unlinked."""
    linked: list[str] = []
    ordered = sorted({n for n in entity_names if n}, key=len, reverse=True)
    for name in ordered:
        if f"[[{name}]]" in text:
            continue
        pattern = re.compile(r"(?<!\[\[)\b" + re.escape(name) + r"\b(?!\]\])", re.IGNORECASE)
        new_text, count = pattern.subn(f"[[{name}]]", text, count=1)
        if count:
            text = new_text
            linked.append(name)
    return text, linked


def capture_note(vault_path: Path, title: str, summary: str, body: str) -> dict:
    body = (body or "").strip()
    if not body:
        return {"error": "empty note body"}
    title = (title or "").strip() or "Untitled Note"
    summary = (summary or "").strip()

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_body, linked_mentions = _auto_wikilink(body, entity_names)
    linked_summary, summary_mentions = _auto_wikilink(summary, entity_names) if summary else (summary, [])
    linked_mentions = list(dict.fromkeys(linked_mentions + summary_mentions))

    # Work/Notes/<date>/<slug>.md (2026-08-30, operator: "Notes are
    # organized in folders by Date") -- the date lives in the FOLDER,
    # via this date-scoped note_name; the note template's own
    # `plain_filename: true` keeps the date out of the filename itself.
    note_name = f"{_NOTE_ROOT}/{datetime.now().strftime('%Y-%m-%d')}"
    template = vm.load_template(vault_path, _NOTE_TEMPLATE_ID)
    result = vm.create(
        vault_path, template, note_name=note_name, title=title,
        sections={"Summary": linked_summary, "Body": linked_body},
    )

    return {"created": True, "path": result["path"], "linked_mentions": linked_mentions}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault-path",
        # Defaults to what Second Brain's setup wizard writes into Hermes'
        # own .env, so a Skill never has to name a machine-specific
        # absolute path and a bundle never has to have one rewritten on
        # import. Pass it only to override.
        default=os.environ.get("SECOND_BRAIN_VAULT_PATH", ""),
    )
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()
    if not (args.vault_path or "").strip():
        # An empty value would become Path("") -> the CWD, which is exactly the
        # silent-wrong-folder failure this whole change exists to remove.
        raise SystemExit(
            "No vault path. Set SECOND_BRAIN_VAULT_PATH in Hermes' own .env "
            "(Second Brain's setup wizard writes it) or pass --vault-path."
        )

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))

    result = capture_note(
        vault_path,
        title=data.get("title", ""),
        summary=data.get("summary", ""),
        body=data.get("body", ""),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
