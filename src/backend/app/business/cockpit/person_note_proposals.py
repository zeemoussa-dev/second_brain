"""In-thread, confirmable/discardable Person-note-edit proposals
(ADR-038 point 7, REQ-SB-49-US-02) -- mirrors cockpit/research.py's own
scoped-list-plus-direct-action shape, one layer over for a new proposal
kind that (unlike a research result) is created SERVER-SIDE by a
Manual/Autonomous dispatch (T02's own Skill handler), not client-
triggered. Stored inside the owning thread's own cockpit_threads.json
record (a new "person_note_proposals" list alongside "messages"/
"brought_in_agent_ids") rather than a new top-level .second-brain/
file -- ephemeral, thread-scoped state with no standing audit
requirement once confirmed or discarded."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.business.cockpit import threads
from app.data_access import vault_writer


def _find_proposal(thread: dict, proposal_id: str) -> dict | None:
    return next(
        (p for p in thread.get("person_note_proposals", []) if p["id"] == proposal_id),
        None,
    )


def create_proposal(
    subject_kind: str, subject_note_stem: str, note_path: str, person_name: str, instruction: str,
) -> dict:
    """Called server-side by T02's own propose_person_note_update
    handler on an already_approved=False dispatch (Manual/Autonomous) --
    NEVER client-triggered. Returns the new pending proposal record."""
    thread = threads.get_thread(subject_kind, subject_note_stem)
    thread.setdefault("person_note_proposals", [])
    proposal = {
        "id": str(uuid.uuid4()),
        "note_path": note_path,
        "person_name": person_name,
        "instruction": instruction,
        "status": "pending",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    thread["person_note_proposals"].append(proposal)
    threads.save_thread(subject_kind, subject_note_stem, thread)
    return proposal


def list_pending_proposals(subject_kind: str, subject_note_stem: str) -> list[dict]:
    thread = threads.get_thread(subject_kind, subject_note_stem)
    return [p for p in thread.get("person_note_proposals", []) if p["status"] == "pending"]


def confirm_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict | None:
    """Returns None if proposal_id is unknown or already resolved
    (idempotent-safe no-op, mirrors pending_approval_registry's own
    "already {status}" guard shape one layer over). The user's own
    explicit confirm click is the ONLY trigger that ever writes here --
    exactly ADR-036 point 4's "the user's own explicit Save click is the
    only trigger" precedent, reused for this new proposal kind."""
    thread = threads.get_thread(subject_kind, subject_note_stem)
    proposal = _find_proposal(thread, proposal_id)
    if proposal is None or proposal["status"] != "pending":
        return None
    vault_writer.append_person_note_update_line(proposal["note_path"], f"- {proposal['instruction']}")
    proposal["status"] = "confirmed"
    threads.save_thread(subject_kind, subject_note_stem, thread)
    return proposal


def discard_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict | None:
    """Returns None if proposal_id is unknown or already resolved. Never
    touches vault_writer -- discarding is a pure status flip, the real
    Person note is left completely untouched."""
    thread = threads.get_thread(subject_kind, subject_note_stem)
    proposal = _find_proposal(thread, proposal_id)
    if proposal is None or proposal["status"] != "pending":
        return None
    proposal["status"] = "discarded"
    threads.save_thread(subject_kind, subject_note_stem, thread)
    return proposal
