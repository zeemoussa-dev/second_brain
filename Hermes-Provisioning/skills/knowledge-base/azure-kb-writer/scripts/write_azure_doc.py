"""CLI entry point: `vault_manager.py`-based replacement for the original
write_azure_doc.py (Implementation/Plans/2026-08-25-vault-writer-
standardization.md, 2026-08-26 -- operator: "Agents that write stuff").
Same job -- the one real, mechanical write path into the Azure Technology
KB -- but placement/collision/frontmatter is `vault_manager.py`'s real
`create()` (`on_existing_title: "update_section"`, so a same-title call
refreshes the existing reference note in place, never duplicates it)
instead of this file's own hand-rolled logic.

`last_refreshed` is real per-call state (unlike a Meeting's logistics,
this DOES change on every call, by design -- it's a living reference
doc) -- set explicitly via `vm.update()` after either branch, since
`create()`'s own `update_section` path only ever touches the sections
given, never frontmatter.

Dropped from the original: the `**Technology:** [[Azure]]` body preamble
line -- purely redundant given `type: "AzureDoc"` and the note's own real
location under Work/Technology/Azure/ already say so; not a loss of real
information.

Usage: identical real contract --
    python write_azure_doc.py --vault-path P --input-file F
    F: {"area": "services"|"architecture-enterprise"|"architecture-data"|
        "architecture-infra", "category": str (required for "services"),
        "title": str, "summary": str, "details": str,
        "source_url": str|null, "images": [{"local_path","caption"}, ...]}
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import vault_manager as vm

_TEMPLATE_ID = "azure-kb-doc"
_VALID_AREAS = ("services", "architecture-enterprise", "architecture-data", "architecture-infra")
_AREA_SUBPATH = {
    "architecture-enterprise": "Architecture/Enterprise",
    "architecture-data": "Architecture/Data",
    "architecture-infra": "Architecture/Infra",
}


def write_azure_doc(
    vault_path: Path, area: str, category: str | None, title: str, summary: str, details: str,
    source_url: str | None, images: list[dict],
) -> dict:
    if area not in _VALID_AREAS:
        return {"error": f"area must be one of {_VALID_AREAS}, got {area!r}"}
    title = (title or "").strip()
    if not title:
        return {"error": "title is required"}

    tags = ["technology/azure"]
    if area == "services":
        category = (category or "").strip()
        if not category:
            return {"error": "category is required for area 'services'"}
        note_name = f"Technology/Azure/Services/{category}"
        tags.append("azure/services")
        tags.append(f"azure/services/{vm._slugify(category).lower()}")
    else:
        note_name = f"Technology/Azure/{_AREA_SUBPATH[area]}"
        tags.append(f"azure/architecture/{_AREA_SUBPATH[area].rsplit('/', 1)[1].lower()}")

    today = datetime.now().strftime("%Y-%m-%d")
    template = vm.load_template(vault_path, _TEMPLATE_ID)
    result = vm.create(
        vault_path, template, note_name=note_name, title=title,
        frontmatter={"area": area, "tags": tags, "source_url": source_url or "", "last_refreshed": today},
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

    result = write_azure_doc(
        vault_path,
        area=data.get("area", ""),
        category=data.get("category"),
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
