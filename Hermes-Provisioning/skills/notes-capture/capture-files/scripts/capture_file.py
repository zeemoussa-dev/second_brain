"""CLI entry point: catch-all capture for a file uploaded with no stated
context (2026-08-22, operator's own framing -- mirrors capture-notes, but
for files). The agent reads the actual file (dedicated format skill, never
a placeholder -- see this Skill's own SKILL.md) and writes a real prose
summary; this script's job stays mechanical: place the file in its own
folder, write its companion description note, best-effort wikilink any
real Customer/Partner name the summary mentions.

Folder-per-file (operator, 2026-08-22 -- corrected from an earlier flat
per-day layout): mirrors this vault's own established pattern (Threads,
Meetings, Opportunities all get a folder named after the thing, holding a
same-named .md alongside the real content) --

    Work/Files/<YYYY-MM-DD>/<original filename stem>/
        <original filename>            -- the real file, untouched
        <original filename stem>.md    -- description (Summary, then
                                           optionally Details -- see
                                           add_file_detail())

Deliberately NOT filed under a specific Customer/Partner -- same choice as
capture-notes: capture now, a later reasoning pass re-files/re-classifies.

Two jobs, two CLI modes:

    python capture_file.py --vault-path P --input-file F
        F: {"source_path": str, "summary": str, "filename": str (optional)}
        Prints {"created": true, "file_path": str, "description_path": str,
        "linked_mentions": [...]} or {"error": str}.

    python capture_file.py --vault-path P --append --input-file F
        F: {"file_path": str, "details": str, "images": [{"source_path":
        str, "caption": str}, ...] (optional)} -- file_path is the real
        captured file's own path (as returned by the create job), used to
        locate its sibling description note. `images` lets the agent embed
        an already-rendered diagram/slide/page image (e.g. from
        pptx_render.py or a PDF-to-image tool) alongside the details text --
        each is COPIED into the file's own folder and embedded as Obsidian
        `![[...]]` syntax with its own caption.
        Prints {"appended": true, "description_path": str,
        "linked_mentions": [...], "attached_images": [...]} or
        {"error": str}.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)


def _slugify(text: str, max_len: int = 120) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "Untitled File"


def _parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return raw


def _read_note_name(md_path: Path) -> str | None:
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


def _unique_folder(files_dir: Path, stem_slug: str) -> Path:
    """Avoid same-day folder-name collisions -- append a numeric
    disambiguator rather than merging into an earlier file's own folder."""
    candidate = files_dir / stem_slug
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        candidate = files_dir / f"{stem_slug}-{n}"
        if not candidate.exists():
            return candidate
        n += 1


def capture_file(vault_path: Path, source_path: str, summary: str, filename: str = "") -> dict:
    source = Path(source_path)
    if not source.is_file():
        return {"error": f"source file not found: {source}"}
    summary = (summary or "").strip()
    if not summary:
        return {"error": "empty summary"}

    # Prefer the real original filename the agent was told (e.g. from WhatsApp
    # media metadata) over the local download path's own name -- platform
    # download caches commonly rewrite it (e.g. a "doc_<hash>_" prefix), which
    # is never something the sender actually named the file.
    dest_name = (filename or "").strip() or source.name
    dest_name = dest_name.strip()
    dest_stem = Path(dest_name).stem or "Untitled File"

    date_str = datetime.now().strftime("%Y-%m-%d")
    files_dir = vault_path / "Work" / "Files" / date_str
    files_dir.mkdir(parents=True, exist_ok=True)

    folder = _unique_folder(files_dir, _slugify(dest_stem))
    folder.mkdir(parents=True, exist_ok=False)

    dest_path = folder / dest_name
    shutil.move(str(source), str(dest_path))

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_summary, linked_mentions = _auto_wikilink(summary, entity_names)

    md_path = folder / f"{folder.name}.md"
    frontmatter = (
        "---\n"
        'type: "File"\n'
        f'date: "{date_str}"\n'
        f'original_filename: "{dest_name}"\n'
        'tags: ["kind/file"]\n'
        "---\n\n"
    )
    md_path.write_text(frontmatter + f"## Summary\n\n{linked_summary}\n", encoding="utf-8")

    return {
        "created": True,
        "file_path": str(dest_path),
        "description_path": str(md_path),
        "linked_mentions": linked_mentions,
    }


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


def _attach_images(folder: Path, images: list[dict]) -> tuple[str, list[str]]:
    """Copies each already-rendered image (e.g. a slide/page render showing
    a diagram) into the file's own folder and returns Markdown embed blocks
    (Obsidian ![[...]] syntax, one per image with its own caption) plus the
    list of copied filenames. Images are COPIED, not moved -- the agent's
    own render output may be a shared temp/scratch path it still wants
    around."""
    blocks: list[str] = []
    copied: list[str] = []
    for item in images or []:
        source = Path(str(item.get("source_path", "")))
        caption = (item.get("caption") or "").strip()
        if not source.is_file():
            continue
        dest = _unique_sibling_path(folder, source.name)
        shutil.copy2(str(source), str(dest))
        copied.append(dest.name)
        block = f"![[{dest.name}]]"
        if caption:
            block += f"\n{caption}"
        blocks.append(block)
    return "\n\n".join(blocks), copied


def add_file_detail(vault_path: Path, file_path: str, details: str, images: list[dict] | None = None) -> dict:
    """Appends a follow-up analysis pass to an already-captured file's own
    description note, under '## Details' -- never a new file, never sent
    anywhere; the vault stays the one place this content lives. Repeat
    calls append further points rather than overwriting earlier ones.
    Optionally embeds one or more already-rendered images (e.g. a diagram
    slide/page render) alongside the text -- see _attach_images."""
    details = (details or "").strip()
    if not details and not images:
        return {"error": "empty details"}

    real_file = Path(file_path)
    if not real_file.is_file():
        return {"error": f"captured file not found: {real_file}"}
    md_path = real_file.parent / f"{real_file.parent.name}.md"
    if not md_path.is_file():
        return {"error": f"description note not found: {md_path}"}

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_details, linked_mentions = _auto_wikilink(details, entity_names) if details else ("", [])

    image_blocks, attached_images = _attach_images(real_file.parent, images or [])
    combined = "\n\n".join(part for part in (linked_details, image_blocks) if part)

    text = md_path.read_text(encoding="utf-8")
    header_pattern = re.compile(r"^## Details$", re.MULTILINE)
    header_match = header_pattern.search(text)
    if header_match is None:
        separator = "" if text.endswith("\n") else "\n"
        new_text = text + separator + f"\n## Details\n\n{combined}\n"
    else:
        region_start = header_match.end()
        next_header = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
        region_end = next_header.start() if next_header else len(text)
        existing = text[region_start:region_end].strip("\n")
        merged = (existing + "\n\n" + combined).strip("\n") if existing else combined
        new_text = text[:region_start] + "\n\n" + merged + "\n\n" + text[region_end:]
    md_path.write_text(new_text, encoding="utf-8")

    return {
        "appended": True,
        "description_path": str(md_path),
        "linked_mentions": linked_mentions,
        "attached_images": attached_images,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--append", action="store_true", help="Add a Details pass to an already-captured file instead of capturing a new one.")
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
        result = capture_file(
            vault_path,
            source_path=data.get("source_path", ""),
            summary=data.get("summary", ""),
            filename=data.get("filename", ""),
        )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
