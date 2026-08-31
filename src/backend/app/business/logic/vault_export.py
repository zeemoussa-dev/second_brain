"""Real vault-data export orchestrator (`REQ-SB-86-US-02-T02`, `ADR-016`)
-- composes `T01`'s embedded-attachment resolver and `sbd_archive.py`'s
writer into one real `.sbd` archive over a plain, already-flattened
selection of vault-relative file paths (no folder expansion, no runtime
call to `REQ-SB-86-US-01`'s own tree endpoint -- see this task's own
Context/Notes for that disclosed judgement call).

Never a dependency-closure resolution, never a secret-scan gate (`ADR-
016`) -- the export set is exactly the operator's own selection plus its
resolved attachments, nothing else.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.business.logic import sbd_archive
from app.business.logic.vault_attachment_resolver import resolve_embedded_attachments
from app.config import settings


def _compute_archive_members(export_set: list[str], extraction: str) -> dict[str, str]:
    """Maps each real export-set member to its archive-member path, per
    the operator's flat/hierarchy choice. Flat-extraction collisions
    (locked, `ADR-016`) are disambiguated by prefixing EVERY colliding
    entry's own original immediate parent-folder name onto its filename,
    joined with `_` -- never a silent overwrite. A file selected directly
    at the vault root (no parent folder) prefixes with `root` instead of
    an empty string -- this task's own scope-internal judgement call; the
    story/ADR only ever illustrate the nested-folder case."""
    vault_root = Path(settings.vault_path).resolve()

    if extraction == "hierarchy":
        return {relative_path: str(vault_root / relative_path) for relative_path in export_set}

    basename_counts: dict[str, int] = {}
    for relative_path in export_set:
        basename = Path(relative_path).name
        basename_counts[basename] = basename_counts.get(basename, 0) + 1

    members: dict[str, str] = {}
    for relative_path in export_set:
        basename = Path(relative_path).name
        if basename_counts[basename] > 1:
            parent_name = Path(relative_path).parent.name or "root"
            member_name = f"{parent_name}_{basename}"
        else:
            member_name = basename
        members[member_name] = str(vault_root / relative_path)
    return members


def build_export(selection: list[str], extraction: str) -> str:
    """Given a real, already-flattened `selection` of vault-relative file
    paths and the operator's `extraction` choice, resolves every selected
    `.md` file's own genuinely-embedded attachments (`T01`), writes one
    real `.sbd` zip to a scratch temp path, and returns that path. Never
    writes to disk anywhere except that one returned scratch temp path --
    the router owns deleting it after the response is sent."""
    md_paths = [path for path in selection if path.lower().endswith(".md")]
    resolved_attachments = resolve_embedded_attachments(md_paths)

    export_set = list(selection)
    for attachment_path in resolved_attachments:
        if attachment_path not in export_set:
            export_set.append(attachment_path)

    members = _compute_archive_members(export_set, extraction)

    file_descriptor, scratch_sbd_path = tempfile.mkstemp(suffix=".sbd", prefix="second-brain-vault-export-")
    os.close(file_descriptor)
    sbd_archive.write_archive(scratch_sbd_path, members)
    return scratch_sbd_path
