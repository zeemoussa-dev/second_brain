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
`overview.summary`/`overview.articles` -- see business/cockpit/notes.py."""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.business import my_day, vault_indexing
from app.business.cockpit import chat_store, chat_turn, documents, notes, people

router = APIRouter(prefix="/cockpit")


def _subject_with_resolved_customer(entry: dict) -> dict:
    """A Thread's own real frontmatter never carries a `customer` field
    (found live 2026-08-27, operator: "Fix the People/Received field gap
    on Threads") -- only a `customer/<slug>` tag, same convention
    `my_day.py`'s own Calendar/Email projections already resolve through
    `customer_name_by_tag`/`customer_from_tags`. A Meeting note that DOES
    carry a real `customer` frontmatter value is left untouched (never
    overwritten by the tag-derived one)."""
    subject = dict(entry["frontmatter"])
    if not subject.get("customer"):
        customer = my_day.customer_from_tags(entry["tags"], my_day.customer_name_by_tag())
        if customer:
            subject["customer"] = customer
    return subject


@router.get("/{subject_kind}/{subject_note_stem}")
def get_cockpit(subject_kind: str, subject_note_stem: str) -> dict:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    return {
        "subject": _subject_with_resolved_customer(entry),
        "people": people.resolve_people_chips(subject_kind, subject_note_stem),
        "overview": {
            "summary": None,
            "related_documents": documents.list_documents(subject_note_stem),
            "articles": [],
        },
        "thread": chat_store.get_thread(subject_kind, subject_note_stem),
    }


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
    if vault_indexing.get_index().get(subject_note_stem) is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    return chat_store.bring_in_agent(subject_kind, subject_note_stem, body.agent_id)


@router.delete("/{subject_kind}/{subject_note_stem}/roster/{agent_id}")
def remove_roster_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    if vault_indexing.get_index().get(subject_note_stem) is None:
        raise HTTPException(status_code=404, detail="Unknown note")
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
    if vault_indexing.get_index().get(subject_note_stem) is None:
        raise HTTPException(status_code=404, detail="Unknown note")
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
    folder)."""
    if vault_indexing.get_index().get(subject_note_stem) is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > documents.MAX_UPLOAD_SIZE_BYTES:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f} MB) — the limit is 25 MB.")
    result = documents.save_document(subject_note_stem, file.filename or "upload", content, caption)
    # Real, visible confirmation right in the live chat (operator, 2026-08-27:
    # "I will need to upload a file or a Screenshot while I am in the
    # meeting") -- so attaching something during the meeting reads the
    # same way as any other real event in the conversation, not a silent
    # background write only visible by later checking the Documents tab.
    # "this meeting"/"this email" -- found live 2026-08-27 testing the
    # Inbox Cockpit: this message hardcoded "meeting" regardless of
    # subject_kind, wrong for an email/Thread upload.
    subject_label = "meeting" if subject_kind == "meeting" else "email"
    chat_store.append_message(
        subject_kind, subject_note_stem, speaker="system",
        text=f"📎 Attached “{result['filename']}” to this {subject_label}.",
    )
    return result
