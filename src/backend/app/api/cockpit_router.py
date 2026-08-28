"""Meeting/Inbox Cockpit read model (REQ-SB-43/44) -- minimal stub
rebuild after the Hermes pivot archived the old router (BUG-037). Only
`people.resolve_people_chips` is reused from the old business/cockpit/
package: it's self-contained (vault-only, no dependency on the retired
agent model) and still correct. `overview` remains an honest empty stub
(never fabricated) until the Research Expert is designed (separate, later
discussion). `thread` is now real, persisted data (REQ-SB-82-US-01,
`ADR-007`) via `business/cockpit/chat_store.py`. `overview.related_documents`
is also real now (2026-08-27) -- see `business/cockpit/documents.py`;
`overview.summary`/`overview.articles` remain honest empty stubs until the
Research Expert is designed (separate, later discussion).

`POST /person/{stem}/notes` (2026-08-25, operator: "Notes about the
person during the meeting, saved to their note is needed") is a real,
narrowly-scoped exception to the "stub only" rule that still applies to
`overview.summary`/`overview.articles` -- see business/cockpit/notes.py.

The real view composition and upload validation live in
business/logic/cockpit_view.py, not here (2026-08-28, API layer holds
no business logic)."""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.business.cockpit import chat_store, chat_turn, notes
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import cockpit_view

router = APIRouter(prefix="/cockpit")
_vault_manager = VaultManager()


def _require_known_note(subject_note_stem: str) -> None:
    if _vault_manager.get_index().get(subject_note_stem) is None:
        raise HTTPException(status_code=404, detail="Unknown note")


@router.get("/{subject_kind}/{subject_note_stem}")
def get_cockpit(subject_kind: str, subject_note_stem: str) -> dict:
    try:
        return cockpit_view.build_cockpit_view(subject_kind, subject_note_stem)
    except cockpit_view.UnknownSubjectError:
        raise HTTPException(status_code=404, detail="Unknown note")


class AddPersonNoteBody(BaseModel):
    text: str


@router.post("/person/{subject_note_stem}/notes")
def add_person_note(subject_note_stem: str, body: AddPersonNoteBody) -> dict:
    return notes.add_person_note(subject_note_stem, body.text)


class RosterBringInBody(BaseModel):
    agent_id: str


@router.post("/{subject_kind}/{subject_note_stem}/roster")
def bring_in_roster_agent(
    subject_kind: str, subject_note_stem: str, body: RosterBringInBody
) -> dict:
    _require_known_note(subject_note_stem)
    return chat_store.bring_in_agent(subject_kind, subject_note_stem, body.agent_id)


@router.delete("/{subject_kind}/{subject_note_stem}/roster/{agent_id}")
def remove_roster_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    _require_known_note(subject_note_stem)
    return chat_store.remove_agent(subject_kind, subject_note_stem, agent_id)


class SendMessageBody(BaseModel):
    text: str


@router.post("/{subject_kind}/{subject_note_stem}/message")
async def send_message(subject_kind: str, subject_note_stem: str, body: SendMessageBody) -> dict:
    """Live per-question routing (with an explicit @mention override) +
    async reply dispatch + threaded reply (REQ-SB-82-US-04) -- see
    `business/cockpit/chat_turn.py` for the actual routing/dispatch logic;
    this endpoint only validates the subject exists and hands off. Returns
    fast (never waits on the real Hermes turn) — `{"thread": ..., "answering":
    {"agent_id", "agent_name"} | None}` — so the caller can show the user's
    own message and an "X is typing..." indicator immediately."""
    _require_known_note(subject_note_stem)
    return await chat_turn.send_user_message(subject_kind, subject_note_stem, body.text)


@router.post("/{subject_kind}/{subject_note_stem}/documents")
async def upload_document(
    subject_kind: str, subject_note_stem: str,
    file: UploadFile = File(...), caption: str = Form(""),
) -> dict:
    """Upload a file/screenshot during a live meeting, stored attached to
    it (operator, 2026-08-27) -- see `business/cockpit/documents.py` for
    the real write path (vault_manager's own `file` Template, same shape
    `capture-files` already uses, nested under this subject's own real
    folder). Validation and the chat-confirmation side effect live in
    business/logic/cockpit_view.py; this endpoint only reads the
    uploaded bytes off the request and maps the outcome to HTTP."""
    content = await file.read()
    try:
        return cockpit_view.upload_document(
            subject_kind, subject_note_stem, file.filename or "upload", content, caption,
        )
    except cockpit_view.UnknownSubjectError:
        raise HTTPException(status_code=404, detail="Unknown note")
    except cockpit_view.EmptyUploadError:
        raise HTTPException(status_code=400, detail="Empty file")
    except cockpit_view.UploadTooLargeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
