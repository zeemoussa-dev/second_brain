"""`## `-level body-section primitives -- read/insert/replace/append a
bounded region between one `## ` header and the next (or end of file).
Write access is gated through `app.obsidian.permissions` before any
file I/O happens."""
from __future__ import annotations

import re
from pathlib import Path

from app.obsidian import permissions

_BODY_SECTION_HEADER_PATTERN = re.compile(r"^## .+$", re.MULTILINE)


def insert_body_line_if_missing(path, line: str) -> bool:
    """Surgical insert of a single line as the first line of a note's
    body if it is not already present anywhere in the file. Returns True
    if inserted, False if the line was already present (no write
    performed)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if line in text:
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        # No frontmatter block found -- prepend at the very top as a
        # fallback.
        path.write_text(line + "\n\n" + text, encoding="utf-8")
        return True
    # A note written via write_frontmatter_note always has "---\n\n<body>"
    # -- end points at the leading "\n" of the closing "\n---\n"; body
    # starts 6 chars later (past "---\n" itself, plus the blank-line
    # separator).
    body_start = end + 6
    new_text = text[:body_start] + line + "\n\n" + text[body_start:]
    path.write_text(new_text, encoding="utf-8")
    return True


def replace_body_line(path, old_line: str, new_line: str) -> bool:
    """Replaces the exact line old_line with new_line wherever it
    appears in the note. No-op (False) if old_line is not present --
    idempotent by construction."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if old_line not in text:
        return False
    path.write_text(text.replace(old_line, new_line), encoding="utf-8")
    return True


def append_body_line(note_path, line: str) -> None:
    """Unconditionally appends one line to a note's own body. Deliberately
    NOT insert_body_line_if_missing's idempotent-if-already-present shape
    -- each call is its own new fact to record, even if coincidentally
    identical text to an existing line, so it must always append, never
    silently no-op on a textual coincidence."""
    path = Path(note_path)
    text = path.read_text(encoding="utf-8")
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + line + "\n", encoding="utf-8")


def insert_body_section_if_missing(path, header: str) -> bool:
    """Idempotent "top up only if absent" primitive for a whole `## `-
    level header -- appends `f"\\n\\n{header}\\n"` to the end of the
    file's own body if `header` is not already present anywhere in the
    file. Returns True if inserted, False if already present. Never
    touches an already-present header's own content -- this function
    only ever appends a bare header line at the very end; populating its
    content is replace_body_section's own job, called separately
    afterward."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    if header_line_pattern.search(text) is not None:
        return False
    separator = "" if text.endswith("\n") else "\n"
    path.write_text(text + separator + f"\n{header}\n", encoding="utf-8")
    return True


def replace_body_section(path, header: str, new_content: str, *, caller: str) -> bool:
    """Header-scoped full-region regeneration: replaces everything
    strictly between `header`'s own line and the next `##`-level header
    line (or end of file) with new_content, leaving everything outside
    that bounded region -- frontmatter, other sections, and both header
    lines themselves -- byte-for-byte untouched. A nested `###` (or
    deeper) subheader inside the same section is NOT a boundary and
    stays part of the replaced region. No-op (returns False, no write
    performed) if `header` is not found anywhere in the file.

    `caller` is a REQUIRED keyword-only parameter, checked against
    `permissions.is_header_allowed(caller, header)` BEFORE any file I/O;
    raises `permissions.SectionWriteNotAllowed` when `caller` may not
    write `header`."""
    if not permissions.is_header_allowed(caller, header):
        raise permissions.SectionWriteNotAllowed(
            f"caller {caller!r} is not allowed to write header {header!r}"
        )
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return False
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = (
        text[:region_start]
        + "\n\n"
        + new_content.strip("\n")
        + "\n\n"
        + text[region_end:]
    )
    path.write_text(new_text, encoding="utf-8")
    return True


def read_body_section(path, header: str) -> str:
    """Header-scoped reader -- the read counterpart to
    replace_body_section's own write, using the identical header/next-
    header location logic. Returns the stripped text strictly between
    `header`'s own line and that boundary, or "" if `header` is not
    found anywhere in the file. Never writes to the file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        return ""
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    return text[region_start:region_end].strip("\n")


def replace_body_opening_line(path, new_line: str) -> bool:
    """Opening-region full regeneration -- the same bounded-region-
    replace mechanism replace_body_section uses, with a DIFFERENT
    region-start rule: the region starts right after the frontmatter's
    closing `---`, and ends at the FIRST `## `-level header line (or end
    of file if the note has none) -- the note's own "opening region",
    ahead of its first real section. Regenerates that region WHOLESALE
    on every call. Returns False (no write performed) only when the file
    has no parseable frontmatter-closing boundary at all (a malformed
    note)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    region_start = end + 6
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    new_text = (
        text[:region_start]
        + new_line.strip("\n")
        + "\n\n"
        + text[region_end:]
    )
    path.write_text(new_text, encoding="utf-8")
    return True


def append_body_section_line(path, header: str, line: str) -> None:
    """Header-SCOPED, growing body-section append -- the generalization
    of replace_body_section's own header/next-header location logic from
    full-region REPLACE to insert-just-before-the-region's-own-end. If
    `header` is not found anywhere in the file, it is CREATED at the end
    of the file, containing exactly `line`. If `header` IS found, `line`
    is appended as the new last line of that header's own bounded
    region, leaving every other section completely untouched. Never
    idempotent-if-already-present -- each call is its own new fact even
    if coincidentally identical text to an existing line."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    header_line_pattern = re.compile(r"^" + re.escape(header) + r"$", re.MULTILINE)
    header_match = header_line_pattern.search(text)
    if header_match is None:
        base = text.rstrip("\n")
        new_text = base + "\n\n" + header + "\n\n" + line + "\n"
        path.write_text(new_text, encoding="utf-8")
        return
    region_start = header_match.end()
    next_header_match = _BODY_SECTION_HEADER_PATTERN.search(text, region_start)
    region_end = next_header_match.start() if next_header_match else len(text)
    existing_region = text[region_start:region_end].strip("\n")
    new_region = f"{existing_region}\n{line}" if existing_region else line
    new_text = (
        text[:region_start]
        + "\n\n"
        + new_region
        + "\n\n"
        + text[region_end:]
    )
    path.write_text(new_text, encoding="utf-8")
