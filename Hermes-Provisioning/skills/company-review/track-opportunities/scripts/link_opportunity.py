"""CLI entry point: links ONE existing Thread or Meeting note to ONE
existing Opportunity (2026-08-22, operator's own explicit choice:
"Manual only, you say so in chat" -- never a proactive/automatic guess,
since a Customer can have several open Opportunities at once and
guessing which one a Thread/Meeting belongs to is a real risk this
vault's own history already warns against, operator: "the company in
message is the company not the parent" / the earlier person-tagging
cascade bug -- same "never fabricate, never guess" discipline applied
here). The agent parses the operator's own real intent ("link this
thread to the ADNOC HPC Expansion opp") first; this script only ever
applies that decision.

Usage:
    python link_opportunity.py --vault-path P --note-path N --opportunity TITLE [--customer NAME]

N: the Thread's or Meeting's own concept .md path (vault-absolute or
relative -- whatever the agent's own read_file call used).
TITLE: the Opportunity's own title, matched against real Opportunity
notes' own `title`-derived stem or frontmatter `name` -- case-
insensitive, never fuzzy/partial (a wrong-but-plausible match is worse
than reporting "not found"). --customer optionally disambiguates if the
same title genuinely exists under more than one Customer.

Prints {"linked": bool, "note_path": str, "opportunity_path": str} or
{"error": str}.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_RELATED_CALLER = "link_opportunity.link_opportunity"
_CALLER_ALLOW_LISTS = {
    _RELATED_CALLER: frozenset({"## Related"}),
}


def _format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_block = text[4:end]
    body = text[end + 5:]
    frontmatter: dict = {}
    for line in frontmatter_block.splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            frontmatter[match.group(1)] = _parse_frontmatter_value(match.group(2))
    return frontmatter, body


def insert_body_section_if_missing(path: Path, header: str) -> bool:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    if header_line_pattern.search(text) is not None:
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + f"\n{header}\n", encoding="utf-8")
    return True


def read_body_section(path: Path, header: str) -> str:
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return ""
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    return text[region_start:region_end].strip("\n")


def replace_body_section(path: Path, header: str, new_content: str, *, caller: str) -> bool:
    if header not in _CALLER_ALLOW_LISTS.get(caller, frozenset()):
        raise PermissionError(f"caller {caller!r} is not allowed to write {header!r}")
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return False
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = text[:region_start] + "\n\n" + new_content.strip("\n") + "\n\n" + text[region_end:]
    path.write_text(new_text, encoding="utf-8")
    return True


def _iter_opportunity_notes(vault_path: Path):
    customers_root = vault_path / "Work" / "Customers"
    if not customers_root.exists():
        return
    for md_path in customers_root.glob("*/Opportunities/*/*.md"):
        if md_path.is_file() and md_path.parent.name == md_path.stem:
            yield md_path


def resolve_opportunity(vault_path: Path, title: str, customer_name: str | None) -> tuple[Path | None, list[Path]]:
    """Returns (single_match, all_matches) -- all_matches lets the caller
    report a genuine ambiguity (same title under >1 Customer) rather than
    silently picking one."""
    key = title.strip().lower()
    customer_key = customer_name.strip().lower() if customer_name else None
    matches: list[Path] = []
    for md_path in _iter_opportunity_notes(vault_path):
        frontmatter, _ = read_note(md_path)
        if md_path.stem.lower() != key:
            continue
        if customer_key:
            note_customer = (frontmatter.get("customer") or "").strip().lower()
            if note_customer != customer_key:
                continue
        matches.append(md_path)
    if len(matches) == 1:
        return matches[0], matches
    return None, matches


def _resolve_note_path(vault_path: Path, note_path_str: str) -> Path:
    p = Path(note_path_str)
    return p if p.is_absolute() else vault_path / p


def link_opportunity(vault_path: Path, note_path_str: str, opportunity_title: str, customer_name: str | None) -> dict:
    note_path = _resolve_note_path(vault_path, note_path_str)
    if not note_path.exists():
        return {"error": f"note not found: {note_path}"}

    opportunity_path, matches = resolve_opportunity(vault_path, opportunity_title, customer_name)
    if opportunity_path is None:
        if len(matches) > 1:
            return {
                "error": f"{opportunity_title!r} matches more than one Opportunity -- pass --customer to disambiguate",
                "candidates": [str(m) for m in matches],
            }
        return {"error": f"no Opportunity named {opportunity_title!r} exists -- create it first"}

    frontmatter, _ = read_note(note_path)
    existing = list(frontmatter.get("opportunities") or [])
    wikilink = f"[[{opportunity_path.stem}]]"
    changed_frontmatter = False
    if wikilink not in existing:
        merged = existing + [wikilink]
        text = note_path.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4)
        if end != -1:
            frontmatter_block = text[: end + 1]
            rest = text[end + 1:]
            lines = frontmatter_block.splitlines(keepends=True)
            new_line = f"opportunities: {_format_frontmatter_value(merged)}\n"
            replaced = False
            for i, line in enumerate(lines):
                m = _FRONTMATTER_LINE.match(line.rstrip("\n"))
                if m and m.group(1) == "opportunities":
                    lines[i] = new_line
                    replaced = True
                    break
            if not replaced:
                lines.insert(-1, new_line)
            note_path.write_text("".join(lines) + rest, encoding="utf-8")
            changed_frontmatter = True

    insert_body_section_if_missing(note_path, "## Related")
    existing_related = read_body_section(note_path, "## Related")
    changed_related = False
    if wikilink not in existing_related:
        lines = [line for line in existing_related.splitlines() if line.strip()]
        lines.append(f"- {wikilink}")
        replace_body_section(note_path, "## Related", "\n".join(lines), caller=_RELATED_CALLER)
        changed_related = True

    return {
        "linked": changed_frontmatter or changed_related,
        "note_path": str(note_path),
        "opportunity_path": str(opportunity_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--note-path", required=True)
    parser.add_argument("--opportunity", required=True)
    parser.add_argument("--customer", default=None)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    result = link_opportunity(vault_path, args.note_path, args.opportunity, args.customer)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
