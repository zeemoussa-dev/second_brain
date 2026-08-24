"""CLI entry point: quick-capture note logging (2026-08-22, operator's own
explicit framing -- "Quick and Dirty where I don't have time to answer so
many Questions"). This is the catch-all for anything relayed to this
specialist: never asks a question, never blocks, never resolves a Customer
or Partner before filing. It just writes the given title/summary/body to
today's date folder under the vault's General Notes area.

Deliberately NOT filed under a specific Customer/Partner hub -- the
operator's own choice: "General Notes will Stay General for now... we will
work on it later" (a future reasoning pass will re-classify/re-file General
Notes; this script's only job is fast, lossless capture today).

The agent (not this script) generates the title and summary -- it already
read and understood the content; this script's job stays purely mechanical:
slugify, place the file, avoid collisions, write it.

Usage:
    python capture_note.py --vault-path P --input-file F

F: {"title": str, "summary": str, "body": str}

Prints {"created": true, "path": str, "linked_mentions": [str, ...]} or
{"error": str}.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "Untitled Note"


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
    only -- never a resolution/validation gate (unlike track-opportunities'
    own strict Customer resolution)."""
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


def _unique_note_path(notes_dir: Path, slug: str) -> Path:
    """Avoid same-day title collisions -- append the current time, then a
    numeric counter, rather than silently overwriting an earlier note."""
    candidate = notes_dir / f"{slug}.md"
    if not candidate.exists():
        return candidate
    time_suffixed = notes_dir / f"{slug} {datetime.now().strftime('%H-%M')}.md"
    if not time_suffixed.exists():
        return time_suffixed
    n = 2
    while True:
        candidate = notes_dir / f"{slug} {datetime.now().strftime('%H-%M')}-{n}.md"
        if not candidate.exists():
            return candidate
        n += 1


def capture_note(vault_path: Path, title: str, summary: str, body: str) -> dict:
    body = (body or "").strip()
    if not body:
        return {"error": "empty note body"}
    title = (title or "").strip() or "Untitled Note"
    summary = (summary or "").strip()

    date_str = datetime.now().strftime("%Y-%m-%d")
    notes_dir = vault_path / "Work" / "Notes" / date_str
    notes_dir.mkdir(parents=True, exist_ok=True)

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_body, linked_mentions = _auto_wikilink(body, entity_names)
    linked_summary, summary_mentions = _auto_wikilink(summary, entity_names) if summary else (summary, [])
    linked_mentions = list(dict.fromkeys(linked_mentions + summary_mentions))

    slug = _slugify(title)
    note_path = _unique_note_path(notes_dir, slug)

    frontmatter = (
        "---\n"
        'type: "Note"\n'
        f'date: "{date_str}"\n'
        'tags: ["kind/notes"]\n'
        "---\n\n"
    )
    content = frontmatter + f"## Summary\n\n{linked_summary}\n\n## Body\n\n{linked_body}\n"
    note_path.write_text(content, encoding="utf-8")

    return {
        "created": True,
        "path": str(note_path),
        "linked_mentions": linked_mentions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

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
