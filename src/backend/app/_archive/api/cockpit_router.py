from fastapi import APIRouter, HTTPException

from app.business import vault_indexing
from app.business.cockpit import attachments, people, person_note_proposals, research, threads

router = APIRouter(prefix="/cockpit")


def _subject_frontmatter(subject_note_stem: str) -> dict:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    return entry["frontmatter"]


@router.get("/{subject_kind}/{subject_note_stem}")
def get_cockpit(subject_kind: str, subject_note_stem: str) -> dict:
    frontmatter = _subject_frontmatter(subject_note_stem)
    return {
        "subject": frontmatter,
        "people": people.resolve_people_chips(subject_kind, subject_note_stem),
        "thread": threads.get_thread(subject_kind, subject_note_stem),
        "research_results": research.list_research_results(subject_kind, subject_note_stem),
        "person_note_proposals": person_note_proposals.list_pending_proposals(subject_kind, subject_note_stem),
    }


@router.post("/{subject_kind}/{subject_note_stem}/bring-in")
def bring_in(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return threads.bring_in_agent(subject_kind, subject_note_stem, body["agent_id"])


@router.post("/{subject_kind}/{subject_note_stem}/message")
async def send_message(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return await threads.send_user_message(
        subject_kind, subject_note_stem, body["message"],
        addressed_agent_ids=body.get("addressed_agent_ids"),
    )


@router.post("/{subject_kind}/{subject_note_stem}/research")
async def trigger_research(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return await research.trigger_research(
        subject_kind, subject_note_stem, body["requesting_agent_id"], body["query"]
    )


@router.post("/{subject_kind}/{subject_note_stem}/research/save")
def save_research(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return research.save_research_result(subject_kind, subject_note_stem, body["query"], body["summary"])


@router.post("/{subject_kind}/{subject_note_stem}/person-note-proposals/{proposal_id}/confirm")
def confirm_person_note_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict:
    result = person_note_proposals.confirm_proposal(subject_kind, subject_note_stem, proposal_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Unknown or already-resolved proposal")
    return result


@router.post("/{subject_kind}/{subject_note_stem}/person-note-proposals/{proposal_id}/discard")
def discard_person_note_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict:
    result = person_note_proposals.discard_proposal(subject_kind, subject_note_stem, proposal_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Unknown or already-resolved proposal")
    return result


# Email-only attachment review routes (REQ-SB-44-US-01, ADR-036 points 5/6)
# -- registered ONLY at /cockpit/email/..., never generalized to
# /cockpit/{subject_kind}/... -- a Meeting Cockpit has no attachment concept.
@router.get("/email/{subject_note_stem}/attachments")
def list_email_attachments(subject_note_stem: str) -> list[dict]:
    return attachments.list_attachments(subject_note_stem)


@router.post("/email/{subject_note_stem}/attachments/{filename}/hand-off")
def hand_off_attachment(subject_note_stem: str, filename: str) -> dict:
    return attachments.hand_off_attachment_to_chat(subject_note_stem, filename)
