"""Cockpit Chat roster/message persistence (ADR-007) -- one new,
per-subject-keyed JSON store (.second-brain/cockpit_chat.json), same
load/save-whole-file shape as agent_visual_registry.py. Pure roster/
message storage only -- never composes a Hermes call itself; routing a
message to an Expert/the Research Agent is `chat_turn.py`'s concern
(REQ-SB-82-US-04).

This is a genuinely new module, NOT a revival of threads.py/ADR-036 --
it never imports that stale module and never composes its retired
run_agent_conversation call.

`recommended_agent_ids` (ADR-009, REQ-SB-82-US-03-T02) is an additive,
compute-on-first-read field on this SAME per-subject entry -- never a
second store. `get_thread` computes it via `moderator.match_customer_expert`/
`match_domain_experts` (combined, deduplicated) the first time an entry has
no such key yet, then persists it; every later read serves the cached
value, including the honest-empty `[]` case. `bring_in_agent`/`remove_agent`
never read or write this field -- it is a non-authoritative hint list,
separate from `brought_in_agent_ids`.

`append_message` (REQ-SB-82-US-04) gives every message a real `id` and an
optional `reply_to_message_id` -- the threaded-reply mechanism (Scenario 4):
a routed Expert's direct reply threads onto the question that routed it,
same as a delayed Research Agent result does, so the frontend renders both
the same way. Pre-US-04 messages have neither field; the frontend treats a
missing `id` as un-threadable, never crashes on it.

`last_answering_agent_id`/`last_answering_agent_name` (ADR-012 point 1,
REQ-SB-82-US-06-T01) is a third additive field pair on this SAME per-subject
entry -- honest-empty (`None`) until `set_last_answering_agent` is ever
called for that subject, including every entry that predates this field.
Unlike `recommended_agent_ids`, this pair is never computed -- only ever set
explicitly by a caller (`chat_turn.py::_dispatch_reply`, REQ-SB-82-US-06-T04)
whenever a real agent reply is actually dispatched.
"""
import uuid
from datetime import datetime, timezone

from app.business.cockpit import moderator
from app.data_access import vault_writer

_DEFAULT_THREAD = {"brought_in_agent_ids": [], "messages": []}


def _thread_key(subject_kind: str, subject_note_stem: str) -> str:
    return f"{subject_kind}:{subject_note_stem}"


def _ensure_last_answering_agent_fields(entry: dict) -> dict:
    """Guarantees `last_answering_agent_id`/`last_answering_agent_name`
    read as `None` on any entry that predates this field pair -- backward
    compatible, no migration needed, same convention as ADR-009's own
    field addition."""
    entry.setdefault("last_answering_agent_id", None)
    entry.setdefault("last_answering_agent_name", None)
    return entry


def _load_state() -> dict:
    state = vault_writer.load_cockpit_chat_state()
    if state is None:
        state = {}
    return state


def get_thread(subject_kind: str, subject_note_stem: str) -> dict:
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.get(key)
    if entry is None:
        entry = {
            "brought_in_agent_ids": [], "messages": [],
            "last_answering_agent_id": None, "last_answering_agent_name": None,
        }
        state[key] = entry
    _ensure_last_answering_agent_fields(entry)
    if "recommended_agent_ids" not in entry:
        customer_agent_id = moderator.match_customer_expert(subject_note_stem)
        domain_agent_ids = moderator.match_domain_experts(subject_note_stem)
        candidate_agent_ids = ([customer_agent_id] if customer_agent_id else []) + domain_agent_ids
        entry["recommended_agent_ids"] = list(dict.fromkeys(candidate_agent_ids))
        vault_writer.save_cockpit_chat_state(state)
    return entry


def bring_in_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.setdefault(key, {
        "brought_in_agent_ids": [], "messages": [],
        "last_answering_agent_id": None, "last_answering_agent_name": None,
    })
    _ensure_last_answering_agent_fields(entry)
    if agent_id not in entry["brought_in_agent_ids"]:
        entry["brought_in_agent_ids"].append(agent_id)
    vault_writer.save_cockpit_chat_state(state)
    return entry


def remove_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.setdefault(key, {
        "brought_in_agent_ids": [], "messages": [],
        "last_answering_agent_id": None, "last_answering_agent_name": None,
    })
    _ensure_last_answering_agent_fields(entry)
    if agent_id in entry["brought_in_agent_ids"]:
        entry["brought_in_agent_ids"].remove(agent_id)
    vault_writer.save_cockpit_chat_state(state)
    return entry


def append_message(
    subject_kind: str, subject_note_stem: str, speaker: str, text: str,
    agent_id: str | None = None, agent_name: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict:
    """Appends one message with a real `id` (returned to the caller so a
    later reply, e.g. a background Research Agent result, can thread onto
    it via `reply_to_message_id`) and persists immediately. Returns the
    NEW message dict, not the whole thread -- `chat_turn.py`'s own callers
    need the id right away; a fresh `get_thread` gives the updated thread."""
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.setdefault(key, {
        "brought_in_agent_ids": [], "messages": [],
        "last_answering_agent_id": None, "last_answering_agent_name": None,
    })
    _ensure_last_answering_agent_fields(entry)
    message = {
        "id": uuid.uuid4().hex,
        "speaker": speaker,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "text": text,
        "reply_to_message_id": reply_to_message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entry["messages"].append(message)
    vault_writer.save_cockpit_chat_state(state)
    return message


def set_last_answering_agent(
    subject_kind: str, subject_note_stem: str, agent_id: str, agent_name: str,
) -> dict:
    """Sets who most recently answered this subject's thread -- Expert,
    Research Agent, or Customer-Section fallback alike (ADR-012 point 1);
    called by `chat_turn.py::_dispatch_reply` whenever a real agent reply is
    actually dispatched. Mirrors `bring_in_agent`'s own
    load/mutate/save/return shape; safe to call for a subject entry that
    doesn't exist yet."""
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.setdefault(key, {
        "brought_in_agent_ids": [], "messages": [],
        "last_answering_agent_id": None, "last_answering_agent_name": None,
    })
    _ensure_last_answering_agent_fields(entry)
    entry["last_answering_agent_id"] = agent_id
    entry["last_answering_agent_name"] = agent_name
    vault_writer.save_cockpit_chat_state(state)
    return entry
