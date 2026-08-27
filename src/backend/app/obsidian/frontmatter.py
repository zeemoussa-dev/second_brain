"""Frontmatter (YAML-ish `key: value` block) read/write primitives.
Parses only the simple `key: "value"` shape this codebase's own writers
produce -- not a general YAML parser. Every function here operates on an
already-resolved note `path`; none of them need to know where the vault
root is."""
from __future__ import annotations

import re
from pathlib import Path

_FRONTMATTER_LINE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s?(.*)$")
_LIST_ITEM_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"')


def format_frontmatter_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(format_frontmatter_value(v) for v in value) + "]"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def parse_frontmatter_value(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw.startswith("[") and raw.endswith("]"):
        # Every list-shaped frontmatter value this codebase writes (tags,
        # via format_frontmatter_value's own list branch) is always a
        # list of quoted strings -- still not a general YAML parser, only
        # this one recognized literal shape.
        inner = raw[1:-1]
        return [
            match.group(1).replace('\\"', '"').replace("\\\\", "\\")
            for match in _LIST_ITEM_PATTERN.finditer(inner)
        ]
    return raw


def read_note(path) -> tuple[dict, str]:
    """Splits a note into (frontmatter dict, body text)."""
    text = Path(path).read_text(encoding="utf-8")
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
            frontmatter[match.group(1)] = parse_frontmatter_value(match.group(2))
    return frontmatter, body


def write_frontmatter_note(path: Path, frontmatter: dict, body: str) -> None:
    """Unconditional full-file write of a frontmatter+body note at an
    already-resolved path."""
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        frontmatter_lines.append(f"{key}: {format_frontmatter_value(value)}")
    frontmatter_lines.append("---")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter_lines) + "\n\n" + body, encoding="utf-8")


def insert_frontmatter_key_if_missing(path, key: str, value) -> bool:
    """Surgical insert of one `key: value` line just before the closing
    `---`, leaving every other line byte-for-byte untouched. Returns True
    if inserted, False if the key was already present (no write
    performed)."""
    path = Path(path)
    frontmatter, _ = read_note(path)
    if key in frontmatter:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    insertion = f"{key}: {format_frontmatter_value(value)}\n"
    path.write_text(text[: end + 1] + insertion + text[end + 1:], encoding="utf-8")
    return True


def upsert_frontmatter_key(path, key: str, value) -> bool:
    """Ensures key: value is present with EXACTLY this value -- inserts
    if missing, or overwrites in place if already present but holding a
    different value. Returns True if the file was written (inserted OR
    changed), False if the key was already present with an identical
    value (a true no-op)."""
    path = Path(path)
    frontmatter, _ = read_note(path)
    if key not in frontmatter:
        return insert_frontmatter_key_if_missing(path, key, value)
    if frontmatter[key] == value:
        return False
    return rename_frontmatter_key(path, key, key, new_value=value)


def rename_frontmatter_key(path, old_key: str, new_key: str, new_value=None) -> bool:
    """Renames old_key to new_key, preserving the existing value unless
    new_value is given explicitly. No-op (returns False, no write) if
    old_key is not present. Scoped strictly to the frontmatter block."""
    path = Path(path)
    frontmatter, _ = read_note(path)
    if old_key not in frontmatter:
        return False
    value = new_value if new_value is not None else frontmatter[old_key]
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    lines = frontmatter_block.splitlines(keepends=True)
    for i, line in enumerate(lines):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == old_key:
            lines[i] = f"{new_key}: {format_frontmatter_value(value)}\n"
            break
    path.write_text("".join(lines) + rest, encoding="utf-8")
    return True


def remove_frontmatter_key_if_present(path, key: str) -> bool:
    """Drops a frontmatter key's line entirely if present. Scoped
    strictly to the frontmatter block. No-op (False) if the key is
    already absent -- idempotent by construction."""
    path = Path(path)
    frontmatter, _ = read_note(path)
    if key not in frontmatter:
        return False
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    frontmatter_block = text[: end + 1]
    rest = text[end + 1:]
    kept_lines = []
    for line in frontmatter_block.splitlines(keepends=True):
        match = _FRONTMATTER_LINE.match(line.rstrip("\n"))
        if match and match.group(1) == key:
            continue
        kept_lines.append(line)
    path.write_text("".join(kept_lines) + rest, encoding="utf-8")
    return True


def insert_tags_line(path, tags: list[str]) -> None:
    """Surgical insert, not a full frontmatter rewrite -- adds a single
    `tags: [...]` line just before the closing `---`, leaving every
    other line byte-for-byte untouched. Used for backfilling notes
    written before `tags` existed."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return
    insertion = f'tags: {format_frontmatter_value(tags)}\n'
    path.write_text(text[: end + 1] + insertion + text[end + 1:], encoding="utf-8")
