"""CLI entry point: `vault_manager.py`-based replacement for the original
write_research_doc.py (Implementation/Plans/2026-08-25-vault-writer-
standardization.md, 2026-08-26 -- operator: "Agents that write stuff").
Same job -- the one real, mechanical write path into the Research
knowledge area, ADR-008's own "never edits or overwrites any existing
note" rule intact -- but placement/collision/frontmatter is
`vault_manager.py`'s real `create()` (`research-kb-doc` Template's
`on_existing_title: "always_new"`) instead of this file's own hand-rolled
logic. `vault_manager.py`'s own `always_new` path already IS the same
never-overwrite guarantee ADR-008 required, just enforced centrally now.

**2026-08-26 update, operator: "in the research folder ... Researchs
arrives as a flat file without a folder if i want to do more research
about a t[opic] it's gonna be a mess in this folder so Separate Researches
with folder and Add Keywords in the Front Matter about this Research"**
-- `note_name` is now computed from the real topic (`Research/<topic>`)
instead of the fixed `"Research"`, reusing `vault_manager`'s own existing
hierarchical note_name mechanism (the same "/"-nested placement
azure-kb-writer/compass-kb-writer already use) -- deliberately NOT
`note_own_folder` (that wraps EVERY call in its own folder, one per call,
which would still scatter repeat research on the SAME topic across
sibling folders). This way every call on the SAME topic string lands
under the SAME folder, each pass a new dated file inside it (still never
overwriting an earlier pass, `always_new` untouched) -- while a genuinely
different topic gets its own, separate folder. A new optional `keywords`
list is written into frontmatter when given, for filtering/browsing.

Usage: identical real contract, plus one addition --
    python write_research_doc.py --vault-path P --input-file F
    F: {"topic": str, "summary": str, "details": str, "source_url": str|null,
        "keywords": [str, ...]|null}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import vault_manager as vm

_TEMPLATE_ID = "research-kb-doc"


def write_research_doc(
    vault_path: Path, topic: str, summary: str, details: str,
    source_url: str | None, keywords: list[str] | None = None,
) -> dict:
    topic = (topic or "").strip()
    if not topic:
        return {"error": "topic is required"}
    summary = (summary or "").strip()
    if not summary:
        return {"error": "summary is required"}

    template = vm.load_template(vault_path, _TEMPLATE_ID)
    frontmatter = {"topic": topic}
    if source_url:
        frontmatter["source_url"] = source_url
    clean_keywords = [k.strip() for k in (keywords or []) if k and k.strip()]
    if clean_keywords:
        frontmatter["keywords"] = clean_keywords
    result = vm.create(
        vault_path, template, note_name=f"Research/{topic}", title=topic,
        frontmatter=frontmatter, sections={"Summary": summary, "Details": (details or "").strip()},
    )
    return {"created": True, "path": result["path"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    data = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))

    result = write_research_doc(
        vault_path,
        topic=data.get("topic", ""),
        summary=data.get("summary", ""),
        details=data.get("details", ""),
        source_url=data.get("source_url"),
        keywords=data.get("keywords"),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
