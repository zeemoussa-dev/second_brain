"""Shared, multi-party Cockpit thread (ADR-036 point 1) -- composes
ADR-015's existing, UNMODIFIED per-agent run_agent_conversation once per
currently brought-in Expert on every user message, never a new
orchestration layer. Backed by .second-brain/cockpit_threads.json
(T01), this codebase's first multi-party (not per-agent) conversation
store."""
from __future__ import annotations

from datetime import datetime, timezone

from app.business import agent_registry
from app.business.agent_orchestration import graph as agent_orchestration
from app.data_access import vault_writer


def _thread_key(subject_kind: str, subject_note_stem: str) -> str:
    return f"{subject_kind}:{subject_note_stem}"


def get_thread(subject_kind: str, subject_note_stem: str) -> dict:
    state = vault_writer.load_cockpit_threads_state() or {}
    key = _thread_key(subject_kind, subject_note_stem)
    return state.get(key) or {"messages": [], "brought_in_agent_ids": []}


def _save_thread(subject_kind: str, subject_note_stem: str, thread: dict) -> None:
    state = vault_writer.load_cockpit_threads_state() or {}
    state[_thread_key(subject_kind, subject_note_stem)] = thread
    vault_writer.save_cockpit_threads_state(state)


def save_thread(subject_kind: str, subject_note_stem: str, thread: dict) -> None:
    """Public wrapper around _save_thread -- lets sibling cockpit/
    modules (person_note_proposals.py, REQ-SB-49-US-02) persist a
    thread they mutated via their own get_thread() read, without
    reaching into this module's private name."""
    _save_thread(subject_kind, subject_note_stem, thread)


def bring_in_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    """Idempotent -- bringing in an already-brought-in agent is a no-op
    (Scenario 5's own repeatable "+ Bring in" affordance)."""
    thread = get_thread(subject_kind, subject_note_stem)
    if agent_id not in thread["brought_in_agent_ids"]:
        thread["brought_in_agent_ids"].append(agent_id)
        _save_thread(subject_kind, subject_note_stem, thread)
    return thread


def _relayed_history_for(thread: dict, for_agent_id: str) -> list[dict]:
    """Builds for_agent_id's OWN view of the shared thread (ADR-036 point 1):
    the user's own turns map to chat_user unchanged; every OTHER Expert's
    own turn maps to a chat_user-kind entry prefixed "[{agent_name} said]: "
    (relayed context, never as if for_agent_id once said it itself); this
    Expert's own prior turns map to chat_agent unchanged."""
    history: list[dict] = []
    for message in thread["messages"]:
        if message["speaker"] == "user":
            history.append({"kind": "chat_user", "text": message["text"]})
        elif message["agent_id"] == for_agent_id:
            history.append({"kind": "chat_agent", "text": message["text"]})
        else:
            history.append({
                "kind": "chat_user",
                "text": f"[{message['agent_name']} said]: {message['text']}",
            })
    return history


async def send_user_message(
    subject_kind: str, subject_note_stem: str, message_text: str,
    addressed_agent_ids: list[str] | None = None,
) -> dict:
    """Appends the user's own turn, then -- for each addressed Expert when
    addressed_agent_ids is given, otherwise for EACH currently brought-in
    Expert -- calls the real, unmodified run_agent_conversation with that
    Expert's own relayed history view, appending each real reply back to
    the SAME shared thread, tagged with that Expert's own agent_id/
    agent_name for attribution (Scenario 6). Returns the updated thread."""
    thread = get_thread(subject_kind, subject_note_stem)
    thread["messages"].append({
        "speaker": "user", "agent_id": None, "agent_name": None,
        "text": message_text, "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    for agent_id in (addressed_agent_ids or thread["brought_in_agent_ids"]):
        history = _relayed_history_for(thread, agent_id)
        memory = vault_writer.load_agent_memory(agent_id)
        result = await agent_orchestration.run_agent_conversation(
            agent_id, message_text, history, memory,
            cockpit_subject_kind=subject_kind, cockpit_subject_note_stem=subject_note_stem,
        )
        agent = agent_registry.get_agent(agent_id)
        agent_name = agent["name"] if agent else agent_id
        reply_text = result.get("reply") or result.get("error") or "No reply."
        thread["messages"].append({
            "speaker": "agent", "agent_id": agent_id, "agent_name": agent_name,
            "text": reply_text, "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        extracted_facts = result.get("extracted_facts") or []
        if extracted_facts:
            vault_writer.append_agent_memory_entries(agent_id, extracted_facts)
    # Real, live-discovered save race (REQ-SB-49-US-02-T05): a mutating
    # Skill dispatched mid-loop above (propose_person_note_update's own
    # already_approved=False branch) does its OWN independent
    # get_thread()/save_thread() round trip via person_note_proposals.
    # create_proposal, persisting a NEW pending proposal to disk BEFORE
    # this function's own single end-of-call save below runs. This
    # function's own in-memory `thread` was read at the very start of
    # this call (before that nested write existed) and therefore never
    # carries the new proposal in its own "person_note_proposals" key --
    # saving it unmodified would silently overwrite (lose) that
    # just-recorded proposal. Re-reads the CURRENTLY persisted
    # "person_note_proposals" list (the one field this function does not
    # itself own/mutate) immediately before the final save, so a nested
    # Skill-created proposal from this same turn survives.
    thread["person_note_proposals"] = get_thread(
        subject_kind, subject_note_stem
    ).get("person_note_proposals", thread.get("person_note_proposals", []))
    _save_thread(subject_kind, subject_note_stem, thread)
    return thread


def append_system_message(subject_kind: str, subject_note_stem: str, text: str) -> dict:
    """A plain, user-attributed turn appended WITHOUT triggering any
    Expert reply -- used by research.py (T04, quick-research's own
    "Quick research: {query}" line) and, for REQ-SB-44, attachment
    hand-off's own summary line. Never calls run_agent_conversation
    itself; the NEXT real send_user_message call is what any brought-in
    Expert actually responds to."""
    thread = get_thread(subject_kind, subject_note_stem)
    thread["messages"].append({
        "speaker": "user", "agent_id": None, "agent_name": None,
        "text": text, "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_thread(subject_kind, subject_note_stem, thread)
    return thread
