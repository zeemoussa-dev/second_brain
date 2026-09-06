"""CLI entry point: `vault_manager.py`-based replacement for the original
capture_file.py (Implementation/Plans/2026-08-25-vault-writer-
standardization.md's third real deployment, 2026-08-26 -- operator:
"handle the Notes files uploads"). Same job -- catch-all capture for a
file uploaded with no stated context, folder-per-file so attachments have
somewhere real to live -- but the note/folder itself is placed by
`vault_manager.py`'s real `create()` (`note_own_folder`) instead of this
file's own hand-rolled slugify/collision/frontmatter logic. The real
uploaded file is moved into the SAME folder `create()` already returns.

Auto-wikilinking known Customer/Partner names is UNCHANGED, reused as-is
from `capture_note.py`'s own copy (this codebase's established per-Skill
self-containment convention -- duplicated, not shared).

Real shape change from the original (matching the meeting-capture
rebuild's own precedent): `Work/Files/<date>/<stem>/` (date as a separate
parent folder) becomes `Work/Files/<date>-<stem>/` (date folded into the
folder name) -- old captures are untouched; only NEW ones use the new
shape.

Usage: identical real two-mode contract --
    python capture_file.py --vault-path P --input-file F
        F: {"source_path": str, "summary": str, "filename": str (optional)}
    python capture_file.py --vault-path P --append --input-file F
        F: {"file_path": str, "details": str, "images": [...] (optional)}
"""
from __future__ import annotations

import argparse
import os
import json
import re
import shutil
from pathlib import Path

import vault_manager as vm

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_FILE_TEMPLATE_ID = "file"
_NOTE_NAME = "Files"


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
    dest_stem = Path(dest_name).stem or "Untitled File"

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_summary, linked_mentions = _auto_wikilink(summary, entity_names)

    template = vm.load_template(vault_path, _FILE_TEMPLATE_ID)
    result = vm.create(vault_path, template, note_name=_NOTE_NAME, title=dest_stem, sections={"Summary": linked_summary})

    folder = Path(result["folder"])
    dest_path = folder / dest_name
    shutil.move(str(source), str(dest_path))

    return {
        "created": True,
        "file_path": str(dest_path),
        "description_path": result["path"],
        "linked_mentions": linked_mentions,
    }


def add_file_detail(vault_path: Path, file_path: str, details: str, images: list[dict] | None = None) -> dict:
    """Appends a follow-up analysis pass to an already-captured file's own
    description note, under 'Details' -- never a new file. Repeat calls
    append further points (`mode="append"`) rather than overwriting
    earlier ones."""
    details = (details or "").strip()
    if not details and not images:
        return {"error": "empty details"}

    real_file = Path(file_path)
    if not real_file.is_file():
        return {"error": f"captured file not found: {real_file}"}
    md_path = real_file.parent / f"{real_file.parent.name}.md"
    if not md_path.is_file():
        return {"error": f"description note not found: {md_path}"}

    frontmatter, _ = vm.read_note(md_path)
    note_id = frontmatter.get("id")
    if not note_id:
        return {"error": f"description note has no real id: {md_path}"}

    try:
        entity_names = list(_iter_known_entity_names(vault_path))
    except OSError:
        entity_names = []
    linked_details, linked_mentions = _auto_wikilink(details, entity_names) if details else ("", [])

    image_blocks, attached_images = _attach_images(real_file.parent, images or [])
    combined = "\n\n".join(part for part in (linked_details, image_blocks) if part)

    note_name = md_path.parent.parent.relative_to(vault_path / vm._NOTES_ROOT).as_posix()
    template = vm.load_template(vault_path, _FILE_TEMPLATE_ID)
    vm.modify_section(vault_path, template, note_id=note_id, section="Details", content=combined, mode="append", note_name=note_name)

    return {
        "appended": True,
        "description_path": str(md_path),
        "linked_mentions": linked_mentions,
        "attached_images": attached_images,
    }


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
    parser.add_argument("--append", action="store_true", help="Add a Details pass to an already-captured file instead of capturing a new one.")
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
