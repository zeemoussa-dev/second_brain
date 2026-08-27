"""Person-note "Personal Notes" append (operator, 2026-08-25: "Notes
about the person during the meeting, saved to their note is needed").
Scoped narrowly to this one real need -- NOT a general note-editing
capability, which doesn't exist anywhere in this app yet and is real,
separate, bigger scope the operator flagged but hasn't asked for."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import HTTPException

from app.business import vault_indexing
from app.data_access import vault_writer

_PERSONAL_NOTES_HEADER = "## Personal Notes"


def add_person_note(subject_note_stem: str, text: str) -> dict:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    line = f"- **{date.today().isoformat()}:** {text}"
    vault_writer.append_body_section_line(Path(entry["path"]), _PERSONAL_NOTES_HEADER, line)
    return {"line": line}
