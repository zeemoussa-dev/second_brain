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
"""
import uuid
from datetime import datetime, timezone

from app.business.cockpit import moderator
from app.data_access import vault_writer

_DEFAULT_THREAD = {"brought_in_agent_ids": [], "messages": []}


def _thread_key(subject_kind: str, subject_note_stem: str) -> str:
    return f"{subject_kind}:{subject_note_stem}"


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
        entry = {"brought_in_agent_ids": [], "messages": []}
        state[key] = entry
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
    entry = state.setdefault(key, {"brought_in_agent_ids": [], "messages": []})
    if agent_id not in entry["brought_in_agent_ids"]:
        entry["brought_in_agent_ids"].append(agent_id)
    vault_writer.save_cockpit_chat_state(state)
    return entry


def remove_agent(subject_kind: str, subject_note_stem: str, agent_id: str) -> dict:
    state = _load_state()
    key = _thread_key(subject_kind, subject_note_stem)
    entry = state.setdefault(key, {"brought_in_agent_ids": [], "messages": []})
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
    entry = state.setdefault(key, {"brought_in_agent_ids": [], "messages": []})
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
