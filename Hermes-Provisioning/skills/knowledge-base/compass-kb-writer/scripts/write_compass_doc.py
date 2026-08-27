"""CLI entry point: `vault_manager.py`-based replacement for the original
write_compass_doc.py (Implementation/Plans/2026-08-25-vault-writer-
standardization.md, 2026-08-26 -- operator: "Agents that write stuff").
Same job -- the one real, mechanical write path into the Compass
Technology KB -- but placement/collision/frontmatter is `vault_manager.py`'s
real `create()` instead of this file's own hand-rolled logic. See
write_azure_doc.py's own header for the shared reasoning (last_refreshed
set explicitly per call; the old `**Technology:** [[Compass]]` body
preamble dropped as redundant with `type: "CompassDoc"`).

Usage: identical real contract --
    python write_compass_doc.py --vault-path P --input-file F
    F: {"area": "pricing"|"general"|"models"|"solutions", "title": str,
        "summary": str, "details": str, "source_url": str|null,
        "images": [{"local_path","caption"}, ...]}
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import vault_manager as vm

_TEMPLATE_ID = "compass-kb-doc"
_VALID_AREAS = ("pricing", "general", "models", "solutions")
_AREA_FOLDER = {"pricing": "Pricing", "general": "General", "models": "Models", "solutions": "Solutions"}


def write_compass_doc(
    vault_path: Path, area: str, title: str, summary: str, details: str,
    source_url: str | None, images: list[dict],
) -> dict:
    if area not in _VALID_AREAS:
        return {"error": f"area must be one of {_VALID_AREAS}, got {area!r}"}
    title = (title or "").strip()
    if not title:
        return {"error": "title is required"}

    note_name = f"Technology/Compass/{_AREA_FOLDER[area]}"
    today = datetime.now().strftime("%Y-%m-%d")
    template = vm.load_template(vault_path, _TEMPLATE_ID)
    result = vm.create(
        vault_path, template, note_name=note_name, title=title,
        frontmatter={"area": area, "tags": ["technology/compass", f"compass/{area}"], "source_url": source_url or "", "last_refreshed": today},
        sections={"Summary": summary or "", "Details": details or ""},
    )
    if result["updated"]:
        vm.update(vault_path, Path(result["path"]), frontmatter={"last_refreshed": today, "source_url": source_url or ""})

    folder = Path(result["folder"])
    copied_images: list[str] = []
    for image in images or []:
        local_path = Path(image["local_path"])
        if not local_path.is_file():
            continue
        dest = folder / local_path.name
        shutil.copyfile(local_path, dest)
        copied_images.append(dest.name)
    if copied_images:
        image_blocks = "\n\n".join(
            f"![[{name}]]" + (f"\n{img.get('caption', '').strip()}" if img.get("caption") else "")
            for name, img in zip(copied_images, images)
        )
        vm.modify_section(vault_path, template, note_id=vm.read_note(Path(result["path"]))[0]["id"], section="Details", content=image_blocks, mode="append", note_name=note_name)

    return {"created": result["created"], "path": result["path"], "updated": result["updated"], "images_copied": copied_images}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))

    result = write_compass_doc(
        vault_path,
        area=data.get("area", ""),
        title=data.get("title", ""),
        summary=data.get("summary", ""),
        details=data.get("details", ""),
        source_url=data.get("source_url"),
        images=data.get("images", []),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
