"""CLI entry point: the mechanical half of Job 5 (files-summarize).
Mirrors apply_thread_review.py's own "the agent decides, the script
applies" split exactly -- reading and understanding a real file
(PDF/DOCX/PPTX/XLSX/image) is real judgment no script can do; this
script only ever applies a summary/short_summary/companies decision the
agent already made.

Given one captured File's already-agent-written summary + short_summary
+ a list of company names/aliases it's genuinely about, this script:

  1. Writes the summary (already wikilinked by the agent, same
     convention apply_thread_review.py uses for Threads) into the
     File's own "## Summary".
  2. Resolves each company name/alias against the REAL Customer/
     Partner/Affiliate hub notes create-companies-partners.py already
     created (matching each hub note's own `name`/`aliases`
     frontmatter) -- an unresolvable name is skipped and reported,
     never used to fabricate a new hub note.
  3. Adds `customer/<slug>`/`partner/<slug>` tags (one per resolved
     company) to the File note -- merged into its existing `tags`,
     never overwriting.
  4. Updates the File's own PARENT Thread's "## Files" section
     (operator, 2026-08-22: "create a log in every thread with files
     and the summary (shorter one)") -- the existing bare
     `- [[file-slug]]` line becomes `- [[file-slug]] -- <short_summary>`,
     replacing the line in place (never duplicated on a rerun) rather
     than a separate log file -- Threads don't get their own Log/
     Captures companion files (ADR-042's own Customer/Partner-only
     scope-lock), so the Thread's own existing "## Files" section IS
     this Job's own log, per the operator's own request.

Usage:
    python apply_file_review.py --vault-path P --input-file F

F: {"file_path": str, "summary": str, "short_summary": str,
    "companies": [str, ...]}
(file_path is the File's own concept .md path, vault-absolute or
relative.)

Prints {"tags_applied": [...], "companies_unresolved": [...],
"files_log_updated": bool}.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)
_WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

_SUMMARY_CALLER = "apply_file_review.apply_file_review"
_FILES_LOG_CALLER = "apply_file_review.update_files_log_line"
_DETAILS_CALLER = "apply_file_review.add_file_detail"
_CALLER_ALLOW_LISTS = {
    _SUMMARY_CALLER: frozenset({"## Summary"}),
    _FILES_LOG_CALLER: frozenset({"## Files"}),
    _DETAILS_CALLER: frozenset({"## Details"}),
}
_HUMAN_OWNED_HEADERS = frozenset({"## Personal Notes"})


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


def merge_tags(path: Path, new_tags: list[str]) -> bool:
    frontmatter, _ = read_note(path)
    existing = list(frontmatter.get("tags") or [])
    merged = existing + [tag for tag in new_tags if tag not in existing]
    if merged == existing:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    new_line = f"tags: {_format_frontmatter_value(merged)}\n"
    replaced = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "tags":
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(-1, new_line)
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


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
    if header in _HUMAN_OWNED_HEADERS or header not in _CALLER_ALLOW_LISTS.get(caller, frozenset()):
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


# ── company resolution (identical contract to apply_thread_review.py's
# own copy) ───────────────────────────────────────────────────────────

def _iter_hub_notes(vault_path: Path):
    for root_name, kind in (("Customers", "customer"), ("Partners", "partner")):
        root = vault_path / "Work" / root_name
        if not root.exists():
            continue
        for md_path in root.rglob("*.md"):
            if not md_path.is_file():
                continue
            if md_path.stem.endswith("-log") or md_path.stem.endswith("-captures"):
                continue
            if md_path.parent.name != md_path.stem:
                continue
            yield md_path, kind


def build_company_index(vault_path: Path) -> dict[str, tuple[str, str, Path]]:
    index: dict[str, tuple[str, str, Path]] = {}
    for md_path, kind in _iter_hub_notes(vault_path):
        frontmatter, _ = read_note(md_path)
        name = frontmatter.get("name") or md_path.stem
        slug = _tag_slug(md_path.stem)
        entry = (kind, slug, md_path)
        index[name.strip().lower()] = entry
        for alias in frontmatter.get("aliases") or []:
            index[alias.strip().lower()] = entry
    return index


def resolve_companies(vault_path: Path, company_names: list[str]) -> tuple[list[tuple[str, str, Path]], list[str]]:
    index = build_company_index(vault_path)
    resolved: list[tuple[str, str, Path]] = []
    unresolved: list[str] = []
    seen_slugs: set[str] = set()
    for name in company_names:
        entry = index.get(name.strip().lower())
        if entry is None:
            unresolved.append(name)
            continue
        kind, slug, hub_md = entry
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        resolved.append((kind, slug, hub_md))
    return resolved, unresolved


# ── Thread's own "## Files" section update ──────────────────────────────

def _resolve_thread_path(vault_path: Path, thread_wikilink: str) -> Path | None:
    match = _WIKILINK_PATTERN.match(thread_wikilink.strip())
    stem = match.group(1) if match else thread_wikilink.strip()
    threads_root = vault_path / "Work" / "Threads"
    if not threads_root.exists():
        return None
    candidate = threads_root / stem / f"{stem}.md"
    return candidate if candidate.exists() else None


def update_files_log_line(thread_path: Path, file_stem: str, short_summary: str) -> bool:
    """Replaces (never duplicates) this file's own bare `- [[stem]]` line
    in the Thread's own "## Files" section with `- [[stem]] --
    <short_summary>`. Idempotent -- a rerun with the same short_summary
    is a no-op; a genuinely different one (re-summarized) replaces the
    line in place."""
    insert_body_section_if_missing(thread_path, "## Files")
    existing = read_body_section(thread_path, "## Files")
    wikilink = f"[[{file_stem}]]"
    new_entry_line = f"- {wikilink} -- {short_summary.strip()}"
    lines = [line for line in existing.splitlines() if line.strip()]
    found = False
    changed = False
    new_lines = []
    for line in lines:
        if line.strip() == wikilink or line.strip().startswith(f"- {wikilink}"):
            found = True
            if line.strip() != new_entry_line:
                changed = True
            new_lines.append(new_entry_line)
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(new_entry_line)
        changed = True
    if changed:
        replace_body_section(thread_path, "## Files", "\n".join(new_lines), caller=_FILES_LOG_CALLER)
    return changed


# ── deeper follow-up pass + diagram attachment (2026-08-22, ported from
# capture-files' own add_file_detail() -- operator's own explicit choice
# to reuse the same engine for Thread attachments, not just standalone
# uploads) ────────────────────────────────────────────────────────────

def _unique_sibling_path(folder: Path, name: str) -> Path:
    candidate = folder / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    n = 2
    while True:
        candidate = folder / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _attach_images(folder: Path, images: list[dict]) -> list[str]:
    """Copies each already-rendered image (e.g. a diagram slide/page render)
    into the File's own folder and returns the list of copied filenames --
    embedding is the caller's own job (the details text already carries the
    ![[...]] blocks, same convention as this script's existing wikilink-
    in-the-summary contract)."""
    copied: list[str] = []
    for item in images or []:
        source = Path(str(item.get("source_path", "")))
        if not source.is_file():
            continue
        dest = _unique_sibling_path(folder, source.name)
        shutil.copy2(str(source), str(dest))
        copied.append(dest.name)
    return copied


def add_file_detail(vault_path: Path, file_path: str, details: str, images: list[dict] | None = None) -> dict:
    """Appends a deeper follow-up pass to an already-summarized File's own
    note, under '## Details' -- never a new file, never sent anywhere.
    Repeat calls append further points. `images` are ALREADY-rendered
    diagram/slide/page images (this script only places and embeds them --
    rendering is the agent's own job, same split as everywhere else in this
    vault's Skills)."""
    details = (details or "").strip()
    if not details and not images:
        return {"error": "empty details"}

    real_file = Path(file_path)
    if not real_file.is_absolute():
        real_file = vault_path / real_file
    if not real_file.is_file():
        return {"error": f"file not found: {real_file}"}
    md_path = real_file.parent / f"{real_file.parent.name}.md"
    if not md_path.is_file():
        return {"error": f"File note not found: {md_path}"}

    attached_images = _attach_images(real_file.parent, images or [])
    image_blocks = "\n\n".join(f"![[{name}]]" for name in attached_images)
    combined = "\n\n".join(part for part in (details, image_blocks) if part)

    insert_body_section_if_missing(md_path, "## Details")
    existing = read_body_section(md_path, "## Details")
    merged = (existing + "\n\n" + combined).strip("\n") if existing else combined
    replace_body_section(md_path, "## Details", merged, caller=_DETAILS_CALLER)

    return {
        "appended": True,
        "description_path": str(md_path),
        "attached_images": attached_images,
    }


# ── main ─────────────────────────────────────────────────────────────────

def apply_file_review(vault_path: Path, data: dict) -> dict:
    file_path = Path(data["file_path"])
    if not file_path.is_absolute():
        file_path = vault_path / file_path
    summary = data["summary"]
    short_summary = data["short_summary"]
    company_names = data.get("companies") or []

    resolved, unresolved = resolve_companies(vault_path, company_names)
    tags = [f"{kind}/{slug}" for kind, slug, _ in resolved]

    insert_body_section_if_missing(file_path, "## Summary")
    replace_body_section(file_path, "## Summary", summary, caller=_SUMMARY_CALLER)
    if tags:
        merge_tags(file_path, tags)

    files_log_updated = False
    frontmatter, _ = read_note(file_path)
    source_thread = frontmatter.get("source_thread") or ""
    if source_thread:
        thread_path = _resolve_thread_path(vault_path, source_thread)
        if thread_path is not None:
            files_log_updated = update_files_log_line(thread_path, file_path.stem, short_summary)

    return {
        "tags_applied": tags,
        "companies_unresolved": unresolved,
        "files_log_updated": files_log_updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--append", action="store_true", help="Add a Details pass (optionally with diagram images) to an already-summarized File instead of applying an initial review.")
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    if args.append:
        result = add_file_detail(
            vault_path,
            file_path=data.get("file_path", ""),
            details=data.get("details", ""),
            images=data.get("images") or [],
        )
    else:
        result = apply_file_review(vault_path, data)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
