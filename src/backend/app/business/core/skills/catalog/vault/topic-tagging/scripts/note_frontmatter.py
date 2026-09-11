"""Minimal frontmatter read/merge for Thread and Meeting notes.

Deliberately not a YAML library: these notes are machine-written with a
stable inline shape (`tags: ["a", "b"]`), and a full YAML round-trip
would reformat every other field in the block as a side effect of
touching one. Everything except the `tags:` line is preserved byte for
byte.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_EXTENDED_PREFIX = "\\\\?\\"

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
_TAGS_LINE = re.compile(r"^tags:.*$", re.M)
_QUOTED = re.compile(r"""["']([^"']+)["']""")


def long_path(path) -> str:
    """Long-path-safe string form, mirroring the vault manager's own
    helper. Windows silently fails past 260 characters and the vault has
    real paths beyond it (a thread folder plus an attachment filename
    clears it easily), so every open() in this Skill goes through here."""
    absolute = os.path.abspath(str(path))
    if os.name == "nt" and not absolute.startswith(_EXTENDED_PREFIX):
        return _EXTENDED_PREFIX + absolute
    return absolute


def detect_newline(path) -> str:
    """The line ending the file already uses.

    Python reads with universal newlines (everything becomes "\\n" in
    memory) and writes back with os.linesep, which silently converts an
    LF note to CRLF on Windows. The vault is 99% CRLF but it is also
    synced to git, so a converted file shows up as a whole-file diff for
    a one-line change. Mixed endings resolve to CRLF, matching the vault.
    """
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        handle.read()
        seen = handle.newlines
    if isinstance(seen, tuple):
        return "\r\n"
    return seen or "\r\n"


def read_note(path) -> tuple[str, str, str]:
    """Returns (whole_text, frontmatter_block, body). frontmatter_block
    is the inner text between the fences, without them."""
    text = Path(long_path(path)).read_text(encoding="utf-8", errors="replace")
    match = _FRONTMATTER.match(text)
    if not match:
        return text, "", text
    return text, match.group(1), text[match.end():]


def parse_tags(frontmatter_block: str) -> list[str]:
    line = _TAGS_LINE.search(frontmatter_block)
    if not line:
        return []
    return _QUOTED.findall(line.group(0))


def topics_of(tags: list[str]) -> list[str]:
    return [tag for tag in tags if tag.startswith("topic/")]


def read_field(frontmatter_block: str, field: str) -> str:
    match = re.search(
        rf'^{re.escape(field)}:\s*"?([^"\r\n]*)"?\s*$', frontmatter_block, re.M
    )
    return (match.group(1).strip() if match else "")


def section_text(body: str, heading: str) -> str:
    """The text under `## <heading>` up to the next `##`. Empty when the
    section is absent -- the caller decides whether that is fatal."""
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S
    )
    return match.group(1).strip() if match else ""


def write_tags_and_stamp(path, new_tags: list[str], stamp_field: str, stamp_value: str) -> None:
    """Rewrite only the `tags:` line and the stamp field, leaving every
    other frontmatter line and the whole body untouched.

    De-duplicates while preserving first-seen order. Real notes in this
    vault carry the same bare tag repeated up to six times (one per
    attendee), so writing tags back without de-duplicating would preserve
    a defect this script is already rewriting the line to fix.
    """
    text, frontmatter_block, body = read_note(path)
    if not frontmatter_block:
        raise ValueError(f"{path} has no frontmatter fence -- refusing to write")

    ordered: dict[str, None] = {}
    for tag in new_tags:
        ordered.setdefault(tag, None)
    rendered = "tags: [" + ", ".join(f'"{tag}"' for tag in ordered) + "]"

    updated_block = frontmatter_block
    if _TAGS_LINE.search(updated_block):
        updated_block = _TAGS_LINE.sub(lambda _: rendered, updated_block, count=1)
    else:
        updated_block = updated_block.rstrip("\n") + "\n" + rendered

    stamp_line = f'{stamp_field}: "{stamp_value}"'
    existing_stamp = re.compile(rf"^{re.escape(stamp_field)}:.*$", re.M)
    if existing_stamp.search(updated_block):
        updated_block = existing_stamp.sub(lambda _: stamp_line, updated_block, count=1)
    else:
        updated_block = updated_block.rstrip("\n") + "\n" + stamp_line

    # The body is written back byte for byte, including its own leading
    # blank line, and in the file's own line ending. Normalising either
    # would rewrite every note this pipeline touches -- hundreds of
    # whole-file diffs in a synced vault, obscuring the real change.
    with open(long_path(path), "w", encoding="utf-8", newline=detect_newline(path)) as handle:
        handle.write("---\n" + updated_block + "\n---\n" + body)
