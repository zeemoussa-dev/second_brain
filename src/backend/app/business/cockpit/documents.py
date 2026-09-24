"""Cockpit Documents tab -- upload a file/screenshot during a live
meeting, stored attached to that meeting (operator, 2026-08-27: "I will
need to upload a file or a Screenshot while I am in the meeting and I
will need this to be Stored in the meeting").

Deliberately NOT a bespoke writer -- uses `vault_manager.py` (the ONE
real, template-driven vault write engine this whole session has been
consolidating everything onto) exactly like `capture-files` already does
for a standalone upload, same `file` Template, same real shape (folder-
per-file + a companion `.md` holding a Summary/Details, `note_own_folder`
so a real attachment has somewhere to live alongside its own note).
Operator, 2026-08-27, correcting an earlier bespoke-writer attempt:
"we built a full Architecture to avoid creating a new file everytime."

The one real difference from `capture-files`' own top-level `Work/Files/`
placement: this lands under the SUBJECT's OWN already-existing folder
(operator: "Do Files Folder... in the meetings") -- `note_name` is
computed from the subject note's real relative path (via `vault_indexing`,
not reconstructed/guessed) plus `/Files`, so uploads land inside
`Work/Meetings/<date>-<Subject>/Files/<date>-<upload stem>/`, not a
separate top-level tree. Second Brain's own backend previously never
imported `vault_manager.py` (it was Hermes-Skill-side only); this module
is that same standalone, stdlib-only file copied here as a normal
in-process consumer -- same "prepare here, apply where it's needed"
convention every other copy of it already follows, just applied to
Second Brain's own backend this time.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.business.core.vault.vault_manager import VaultManager
from app.config import settings
from app.vault import vault_manager as vm

_logger = logging.getLogger(__name__)

# What `vault_manager.long_path()` puts in front of a path to get past Windows'
# 260-character limit; stripped again before a path leaves this module.
_EXTENDED_PREFIX = "\\\\?\\"

_FILE_TEMPLATE_ID = "file"

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB -- generous for a screenshot/PDF, not unbounded

_vault_manager = VaultManager()


def _subject_note_name(subject_note_stem: str) -> str | None:
    """The subject note's own real relative note_name under Work/ (e.g.
    "Meetings/2026-10-13-PSS Team Get together") -- derived from its
    REAL indexed path, never reconstructed/guessed from the stem, so this
    stays correct even if a folder name carries a collision suffix."""
    entry = _vault_manager.get_index().get(subject_note_stem)
    if entry is None:
        return None
    folder = Path(entry["path"]).parent
    return folder.relative_to(settings.vault_path / vm._NOTES_ROOT).as_posix()


def _modified_at(path: Path) -> float:
    """The note's mtime, or 0 when it cannot be stat'd -- an unreachable file
    sorts last instead of taking the listing down with it."""
    try:
        return path.stat().st_mtime
    except OSError as error:
        _logger.warning("cockpit: could not stat %s: %s", path.name, error)
        return 0.0


def _plain(path: Path) -> str:
    """The ordinary form of a path walked through the extended-length prefix, so
    what leaves this module still compares against `vault_path` like any other."""
    text = str(path)
    return text[len(_EXTENDED_PREFIX):] if text.startswith(_EXTENDED_PREFIX) else text


def list_documents(subject_note_stem: str) -> list[dict]:
    """Every attachment captured under this subject's own `Files/` folder.

    Walked through `long_path` (`BUG-077`): an attachment's folder repeats the
    attachment's own name (`Files/<name>/<name>.md`), so a subject with a long
    subject line puts that note past Windows' 260-character limit. Without the
    prefix `stat()` raised `FileNotFoundError` and the whole Cockpit read
    returned 500 -- no summary, no people, no chat, for 171 of the reporting
    install's subjects. A document that still cannot be read is skipped, never
    fatal: a missing attachment row is worth far less than the Cockpit."""
    subject_note_name = _subject_note_name(subject_note_stem)
    if subject_note_name is None:
        return []
    files_root = Path(vm.long_path(settings.vault_path / vm._NOTES_ROOT / subject_note_name / "Files"))
    if not files_root.is_dir():
        return []
    documents = []
    for description_note in sorted(files_root.glob("*/*.md"), key=_modified_at, reverse=True):
        folder = description_note.parent
        if folder.name != description_note.stem:
            continue
        try:
            frontmatter, _ = vm.read_note(description_note)
            real_files = [p.name for p in folder.iterdir() if p.is_file() and p != description_note]
        except OSError as error:
            _logger.warning("cockpit: skipping unreadable attachment %s: %s", description_note.name, error)
            continue
        documents.append({
            "title": frontmatter.get("title", description_note.stem),
            "filename": real_files[0] if real_files else None,
            "note_path": _plain(description_note),
        })
    return documents


def save_document(subject_note_stem: str, filename: str, content: bytes, caption: str | None = None) -> dict:
    subject_note_name = _subject_note_name(subject_note_stem)
    if subject_note_name is None:
        raise FileNotFoundError(f"Unknown note: {subject_note_stem!r}")

    filename = (filename or "upload").strip()
    title = Path(filename).stem or "Untitled Upload"
    caption = (caption or "").strip()
    summary = caption or "Uploaded during the meeting — no caption given."

    # The engine derives the App Database Folder itself (data_root); it wants
    # the VAULT path. Passing the data path here was a workaround for the
    # retired fork resolving Templates relative to the vault.
    template = vm.load_template(settings.vault_path, _FILE_TEMPLATE_ID)
    result = vm.create(
        settings.vault_path, template, note_name=f"{subject_note_name}/Files", title=title,
        sections={"Summary": summary},
    )

    folder = Path(result["folder"])
    dest_path = folder / filename
    dest_path.write_bytes(content)

    return {"filename": filename, "note_path": result["path"], "size": len(content)}
