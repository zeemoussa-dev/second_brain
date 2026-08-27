"""Obsidian tag primitives -- slug normalization and a scoped tags-list
swap. Tag SHAPE only (a `customer/<slug>`-style hierarchical tag); what
a given tag namespace means to Second Brain is a business-layer
concern, not this module's."""
from __future__ import annotations

import re
from pathlib import Path

from app.obsidian.frontmatter import _FRONTMATTER_LINE

_TAG_INVALID_CHARS = re.compile(r"[^a-z0-9/]+")


def tag_slug(text: str) -> str:
    """Obsidian tags can't contain spaces -- lowercase, non-alphanumeric
    runs collapsed to a single hyphen, e.g. 'Department of Government
    Enablement' -> 'department-of-government-enablement'."""
    slug = _TAG_INVALID_CHARS.sub("-", text.lower()).strip("-")
    return slug or "untitled"


def swap_tag(path, old_tag: str, new_tag: str) -> bool:
    """Replaces `"old_tag"` with `"new_tag"` within the note's
    frontmatter `tags:` line only -- write_note/format_frontmatter_value
    always render tags as a single-line `tags: ["a", "b"]` list, so a
    scoped, single-line string replace is equivalent to a structural
    list-element swap without needing a real YAML parser. Never touches
    the body or any other frontmatter line. No-op (False) if old_tag is
    not present in that line."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    old_quoted = f'"{old_tag}"'
    new_quoted = f'"{new_tag}"'
    changed = False
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == "tags" and old_quoted in line:
            lines[i] = line.replace(old_quoted, new_quoted)
            changed = True
            break
    if not changed:
        return False
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True
