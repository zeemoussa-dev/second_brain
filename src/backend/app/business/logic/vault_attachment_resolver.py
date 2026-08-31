"""Embedded-attachment detection over a real selection of `.md` files
(REQ-SB-86-US-02-T01, ADR-016) -- scans each selected note's own real
body for a genuinely-embedded, on-disk attachment via Obsidian's own two
real embed syntaxes (wikilink-embed `![[...]]`, markdown-image-link
`![...](...)`) and resolves each to a real, existing vault-relative
path. Pure read/resolve, no file writes -- `.sbd`'s own archive
composition (T02) is the only writer that touches this module's output.

Resolution order (this task's own disclosed, scope-internal judgement
call -- neither the PRD nor ADR-016 specifies one):
1. Relative to the referencing note's own containing folder -- confirmed
   live as the real, dominant convention this vault's own notes actually
   use today (e.g. `![[aks-baseline-architecture.svg]]` sitting directly
   next to its own note, `Work/Technology/Azure/Architecture/Infra/`).
2. Every folder level from the note's own containing folder up to the
   vault root, searched for the target's own filename under an
   `attachments/` or `files/` subfolder (the real `write_attachments()`/
   `write_file_companion()` convention, `app/obsidian/attachments.py`) --
   the `subfolder` argument those writers take can be any ancestor of the
   note's own final location, not necessarily its immediate parent, so
   the exact note-slug/message-slug nesting is not replicated here; a
   recursive filename search under each level's own `attachments/`/
   `files/` folder finds the real file regardless of that nesting depth.
3. As a plain vault-root-relative path.

A target resolving at none of these is silently skipped -- never
fabricated into the result, never a hard failure (ADR-016's own
"silently skipped" Decision text).

A target that resolves to a real `.md` file is also silently skipped --
`![[Some Note]]` is syntactically identical to a real image/file embed,
but is Obsidian's own note-TRANSCLUSION syntax, not an attachment;
treating it as one would silently pull an unselected note's own full
content into the export, in tension with REQ-SB-86-US-02's own Scenario
6 ("nothing outside the operator's own selection is ever included").
Logged as a scope-internal judgement call -- the PRD/ADR-016 text names
only images/SVGs/PDFs as the real attachment kinds this feature targets.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from app.config import settings
from app.obsidian.frontmatter import read_note

_WIKILINK_EMBED_PATTERN = re.compile(r"!\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
_MARKDOWN_IMAGE_LINK_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def _candidate_targets(body: str) -> list[str]:
    return _WIKILINK_EMBED_PATTERN.findall(body) + _MARKDOWN_IMAGE_LINK_PATTERN.findall(body)


def _ancestor_levels(note_dir: Path, vault_root: Path) -> list[Path]:
    """Every folder from `note_dir` up to (and including) `vault_root`,
    nearest first. Stops early (without reaching `vault_root`) if
    `note_dir` genuinely isn't under `vault_root` at all -- never walks
    arbitrarily far up an unrelated filesystem tree."""
    levels = []
    current = note_dir
    while True:
        levels.append(current)
        if current == vault_root:
            break
        if vault_root not in current.parents:
            break
        current = current.parent
    return levels


def _first_existing_file(directory: Path, filename: str) -> Path | None:
    if not directory.is_dir():
        return None
    for match in directory.rglob(filename):
        if match.is_file():
            return match
    return None


def _resolve_target(target: str, note_abs_path: Path, vault_root: Path) -> Path | None:
    target = unquote(target.strip())
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None

    note_dir = note_abs_path.parent
    filename = Path(target).name

    direct_candidate = note_dir / target
    if direct_candidate.is_file():
        return direct_candidate

    for level in _ancestor_levels(note_dir, vault_root):
        match = _first_existing_file(level / "attachments", filename) or _first_existing_file(level / "files", filename)
        if match is not None:
            return match

    root_relative_candidate = vault_root / target
    if root_relative_candidate.is_file():
        return root_relative_candidate

    return None


def resolve_embedded_attachments(selected_md_paths: list[str]) -> list[str]:
    """Given a plain list of vault-relative `.md` paths, returns the
    deduplicated, sorted list of vault-relative paths every genuinely-
    embedded, real, on-disk attachment resolves to across the whole
    selection (empty list when none are embedded anywhere)."""
    vault_root = Path(settings.vault_path).resolve()
    resolved: set[str] = set()

    for relative_md_path in selected_md_paths:
        note_abs_path = vault_root / relative_md_path
        if not note_abs_path.is_file():
            continue
        _frontmatter, body = read_note(note_abs_path)

        for target in _candidate_targets(body):
            resolved_path = _resolve_target(target, note_abs_path, vault_root)
            if resolved_path is None or resolved_path.suffix.lower() == ".md":
                continue
            # `.resolve()` collapses any `..` traversal in a match found via
            # the note's own containing folder, so the same real, physical
            # attachment reached via two differently-shaped relative
            # references from two different selected notes still
            # deduplicates to one identical vault-relative string.
            resolved_path = resolved_path.resolve()
            try:
                relative_path = resolved_path.relative_to(vault_root)
            except ValueError:
                continue
            resolved.add(relative_path.as_posix())

    return sorted(resolved)
