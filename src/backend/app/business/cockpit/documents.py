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

from pathlib import Path

from app.business import vault_indexing
from app.config import settings
from app.vault import vault_manager as vm

_FILE_TEMPLATE_ID = "file"

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB -- generous for a screenshot/PDF, not unbounded


def _subject_note_name(subject_note_stem: str) -> str | None:
    """The subject note's own real relative note_name under Work/ (e.g.
    "Meetings/2026-10-13-PSS Team Get together") -- derived from its
    REAL indexed path, never reconstructed/guessed from the stem, so this
    stays correct even if a folder name carries a collision suffix."""
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        return None
    folder = Path(entry["path"]).parent
    return folder.relative_to(settings.vault_path / vm._NOTES_ROOT).as_posix()


def list_documents(subject_note_stem: str) -> list[dict]:
    subject_note_name = _subject_note_name(subject_note_stem)
    if subject_note_name is None:
        return []
    files_root = settings.vault_path / vm._NOTES_ROOT / subject_note_name / "Files"
    if not files_root.is_dir():
        return []
    documents = []
    for description_note in sorted(files_root.glob("*/*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        folder = description_note.parent
        if folder.name != description_note.stem:
            continue
        frontmatter, _ = vm.read_note(description_note)
        real_files = [p.name for p in folder.iterdir() if p.is_file() and p != description_note]
        documents.append({
            "title": frontmatter.get("title", description_note.stem),
            "filename": real_files[0] if real_files else None,
            "note_path": str(description_note),
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

    template = vm.load_template(settings.second_brain_data_path, _FILE_TEMPLATE_ID)
    result = vm.create(
        settings.vault_path, template, note_name=f"{subject_note_name}/Files", title=title,
        sections={"Summary": summary},
    )

    folder = Path(result["folder"])
    dest_path = folder / filename
    dest_path.write_bytes(content)

    return {"filename": filename, "note_path": result["path"], "size": len(content)}
