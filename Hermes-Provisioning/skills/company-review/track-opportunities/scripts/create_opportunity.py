"""CLI entry point: mechanical creation of a new Opportunity note under a
REAL, already-existing Customer hub (2026-08-22, operator's own
conversational-creation flow -- "Create a new Opp" in WhatsApp). The
agent gathers title/customer/expected_consumption/technologies through
real back-and-forth first; this script only ever applies that decision,
same "agent decides, script applies" split as every other pipeline in
this vault.

Never fabricates a new Customer -- if the named customer doesn't resolve
to a real Customer hub note (create-companies-partners.py's own job),
this reports an error instead of guessing or creating one. Opportunities
are scoped to Customers only, not Partners (operator's own framing --
a sales/revenue concept, not a vendor-relationship one).

Usage:
    python create_opportunity.py --vault-path P --input-file F

F: {"title": str, "customer": str, "expected_consumption": str,
    "technologies": [str, ...], "status": str}
(`status` optional, defaults to "Open"; `expected_consumption` and
`technologies` optional, default blank/empty -- "capture then organize",
operator, 2026-08-22: free text now, a later pass structures it once
real patterns are visible.)

Prints {"created": true, "path": str, "customer_hub": str} or
{"error": str}.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)

_OPPORTUNITIES_CALLER = "create_opportunity.link_opportunity_to_customer_hub"
_CALLER_ALLOW_LISTS = {
    _OPPORTUNITIES_CALLER: frozenset({"## Opportunities"}),
}


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "untitled"


def _tag_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9/]+", "-", text.lower()).strip("-")
    return slug or "untitled"


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


def _write_frontmatter_note(path: Path, frontmatter: dict, body: str) -> None:
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {_format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter_lines) + "\n\n" + body, encoding="utf-8")


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


# ── Customer resolution (Customers only -- Opportunities are never
# tracked under Partners, operator's own scoping) ───────────────────────

def _iter_customer_hub_notes(vault_path: Path):
    root = vault_path / "Work" / "Customers"
    if not root.exists():
        return
    for md_path in root.rglob("*.md"):
        if not md_path.is_file():
            continue
        if md_path.stem.endswith("-log") or md_path.stem.endswith("-captures"):
            continue
        if md_path.parent.name != md_path.stem:
            continue
        yield md_path


def resolve_customer_hub(vault_path: Path, customer_name: str) -> Path | None:
    key = customer_name.strip().lower()
    for md_path in _iter_customer_hub_notes(vault_path):
        frontmatter, _ = read_note(md_path)
        name = (frontmatter.get("name") or md_path.stem).strip().lower()
        if name == key:
            return md_path
        for alias in frontmatter.get("aliases") or []:
            if alias.strip().lower() == key:
                return md_path
    return None


def link_opportunity_to_customer_hub(customer_hub_path: Path, opportunity_md: Path) -> bool:
    """Accumulates one wikilink per Opportunity into the Customer hub's
    own "## Opportunities" section -- mirrors link_affiliate_to_parent's
    own accumulate-into-a-section pattern in create_companies_partners.py.
    Idempotent."""
    wikilink = f"[[{opportunity_md.stem}]]"
    insert_body_section_if_missing(customer_hub_path, "## Opportunities")
    existing = read_body_section(customer_hub_path, "## Opportunities")
    if wikilink in existing:
        return False
    lines = [line for line in existing.splitlines() if line.strip()]
    lines.append(f"- {wikilink}")
    replace_body_section(customer_hub_path, "## Opportunities", "\n".join(lines), caller=_OPPORTUNITIES_CALLER)
    return True


def create_opportunity(
    vault_path: Path, title: str, customer_name: str,
    expected_consumption: str = "", technologies: list[str] | None = None, status: str = "Open",
) -> dict:
    customer_hub = resolve_customer_hub(vault_path, customer_name)
    if customer_hub is None:
        return {"error": f"no real Customer hub note matches {customer_name!r} -- create it via create-companies-partners first, or check the spelling"}

    slug = _slugify(title)
    opp_dir = customer_hub.parent / "Opportunities" / slug
    opp_path = opp_dir / f"{slug}.md"
    if opp_path.exists():
        return {"error": f"an Opportunity named {title!r} already exists for {customer_name!r}", "path": str(opp_path)}

    customer_slug = _tag_slug(customer_hub.stem)
    frontmatter = {
        "type": "Opportunity",
        "customer": customer_hub.stem,
        "status": status or "Open",
        "expected_consumption": expected_consumption or "",
        "technologies": technologies or [],
        "created": date.today().isoformat(),
        "tags": [f"customer/{customer_slug}", "kind/opportunity"],
    }
    body = "## Summary\n\n## Log\n\n## Actions\n\n## Related\n\n## Files\n"
    _write_frontmatter_note(opp_path, frontmatter, body)

    link_opportunity_to_customer_hub(customer_hub, opp_path)

    return {"created": True, "path": str(opp_path), "customer_hub": str(customer_hub)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))

    result = create_opportunity(
        vault_path,
        title=data["title"],
        customer_name=data["customer"],
        expected_consumption=data.get("expected_consumption") or "",
        technologies=data.get("technologies") or [],
        status=data.get("status") or "Open",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
