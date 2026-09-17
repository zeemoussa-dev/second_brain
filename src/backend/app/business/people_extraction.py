"""Read-only Person lookup for Cockpit's people chips (`business/cockpit/people.py`).

The Person-note creation, company matching and Customer/Partner hub linking
that used to live here had no callers left and was removed (Entities plan
Phase 1, `Implementation/Plans/2026-09-14-entities-plugin.md`). Person notes
are written by the capture Skills, which are Agent-owned.
"""
from __future__ import annotations

from app.data_access import vault_writer


def find_existing_person_note(email: str) -> dict | None:
    """Read-only -- returns {"note_path": str, "name": str} if a Person
    note already exists for this email, else None. NEVER creates a
    Person note -- the Cockpit must not mutate the vault as a side effect
    of merely opening (ADR-036 point 7). Uses
    person_note_dedup_key/find_person_note_path's vault-wide scan, so a
    Person note is found wherever it is nested."""
    if not email:
        return None
    dedup_key = vault_writer.person_note_dedup_key("", email)
    note_path = vault_writer.find_person_note_path(dedup_key)
    if note_path is None:
        return None
    frontmatter, _ = vault_writer.read_note(note_path)
    return {"note_path": str(note_path), "name": frontmatter.get("name") or frontmatter.get("subject") or email}
