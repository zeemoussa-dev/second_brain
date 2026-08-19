---
id: REQ-SB-43-US-01-T02
title: New app/business/cockpit/threads.py — shared multi-party thread (get_thread/bring_in_agent/send_user_message), composing ADR-015's run_agent_conversation once per brought-in Expert
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-43-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T02 — `app/business/cockpit/threads.py`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

New sub-package `app/business/cockpit/` (mirrors `agent_orchestration/`'s own "first concern with enough internal structure to warrant one" precedent), first module `threads.py` — the shared, multi-party thread mechanism `ADR-036` point 1 designs: get/seed a `{subject_kind}:{subject_note_stem}`-keyed thread, bring an Expert in, and — on a user message — compose `agent_orchestration.run_agent_conversation` once per currently brought-in Expert, each seeing its OWN relayed view of the shared history, appending every real reply back to the shared thread tagged with its author.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `load_cockpit_threads_state`/`save_cockpit_threads_state`.
- `app.business.agent_orchestration.run_agent_conversation(agent_id, message, history, memory=None) -> dict` is Done (`ADR-015`), returns `{"reply": str, "extracted_facts": list[str]}` or `{"error": str}`.
- `app.business.agent_registry.get_agent(agent_id) -> dict | None` is Done.
- `app.data_access.vault_writer.load_agent_memory(agent_id)`/`append_agent_memory_entries(agent_id, facts)` are Done (`ADR-016`).

**After / Outputs:** new `app/business/cockpit/__init__.py` (empty) and `app/business/cockpit/threads.py`:
```python
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


async def send_user_message(subject_kind: str, subject_note_stem: str, message_text: str) -> dict:
    """Appends the user's own turn, then -- for EACH currently brought-in
    Expert -- calls the real, unmodified run_agent_conversation with that
    Expert's own relayed history view, appending each real reply back to
    the SAME shared thread, tagged with that Expert's own agent_id/
    agent_name for attribution (Scenario 6). Returns the updated thread."""
    thread = get_thread(subject_kind, subject_note_stem)
    thread["messages"].append({
        "speaker": "user", "agent_id": None, "agent_name": None,
        "text": message_text, "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    for agent_id in thread["brought_in_agent_ids"]:
        history = _relayed_history_for(thread, agent_id)
        memory = vault_writer.load_agent_memory(agent_id)
        result = await agent_orchestration.run_agent_conversation(agent_id, message_text, history, memory)
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
```

---

## Files to Modify

- `src/backend/app/business/cockpit/__init__.py` (new, empty).
- `src/backend/app/business/cockpit/threads.py` (new) — per the code block above.

---

## Constraints

- Composes `agent_orchestration.run_agent_conversation` UNMODIFIED — this task does not edit `app/business/agent_orchestration/*`.
- `bring_in_agent` is idempotent (Scenario 5).
- `_relayed_history_for` is the ONE place the "[{agent_name} said]: " relay framing is built — never send another Expert's own reply into `run_agent_conversation`'s `history` as if it were the CALLED agent's own past turn.
- `send_user_message` calls `run_agent_conversation` ONCE PER brought-in Expert, sequentially (not in parallel) — real Provider calls, no need to over-engineer concurrency for this pass; each Expert's own reply is appended to the shared thread before the next Expert's call is built, so a later Expert in the same loop sees an EARLIER Expert's own real reply to this same message in its own relayed history (mirrors a real, live group conversation, not a frozen snapshot).
- `extracted_facts` handling mirrors `agents_router.py::chat`'s own existing persistence shape exactly (a true no-op when empty).
- Genuinely `async def` (the composed `run_agent_conversation` is itself async) — every caller of `send_user_message` must `await` it.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`, `asyncio.run(...)` for the async function; delete any leftover `.second-brain/cockpit_threads.json` first):
1. Non-AC smoke check: `cockpit.threads.get_thread("meeting", "test-stem")` → `{"messages": [], "brought_in_agent_ids": []}` (seeded empty, no file yet).
2. **[REQ-SB-43-US-01-AC-05]** `cockpit.threads.bring_in_agent("meeting", "test-stem", "vault-qa")` — confirm `get_thread(...)["brought_in_agent_ids"] == ["vault-qa"]`. Call it again with the same agent — confirm the list still has exactly one entry (idempotent).
3. **[REQ-SB-43-US-01-AC-05]** `asyncio.run(cockpit.threads.send_user_message("meeting", "test-stem", "What's Acme's renewal history?"))` — confirm the returned thread's `messages` gained a `speaker == "user"` entry AND a `speaker == "agent", agent_id == "vault-qa"` entry (a real reply, or a real honest `{"error": ...}`-derived text if `vault-qa`'s own Provider is unavailable — either is a real, non-fabricated outcome).
4. **[REQ-SB-43-US-01-AC-05]**/**[REQ-SB-43-US-01-AC-06]** `cockpit.threads.bring_in_agent("meeting", "test-stem", "people-producer")` (a second Expert). `asyncio.run(send_user_message("meeting", "test-stem", "Anything about Jordan Lee?"))` — confirm the thread now has TWO new agent-attributed replies (from `vault-qa` AND `people-producer`), each with the correct `agent_id`/`agent_name`, both within the SAME `messages` list (one shared thread, not two).
5. **[REQ-SB-43-US-01-AC-06]** Inspect `_relayed_history_for(thread, "people-producer")`'s own real output (call it directly) — confirm `vault-qa`'s own earlier reply appears as a `chat_user`-kind entry prefixed `"[Vault Q&A said]: "` (or the real agent's own `name`), never as a `chat_agent`-kind entry (which would misattribute it as `people-producer`'s own past words).
6. **[REQ-SB-43-US-01-AC-11]** Confirm `graph.route_cross_section_request`'s own real function is untouched (no import/monkeypatch of it anywhere in this module) — a direct code-read check, not a runtime one: this module never calls it, so bringing an Expert into a Cockpit thread cannot alter Hub-routing's own matching behavior by construction.
7. Clean-up: delete `.second-brain/cockpit_threads.json`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `get_thread`/`bring_in_agent`/`send_user_message`/`append_system_message` exist with the shapes above
- [ ] `bring_in_agent` is idempotent
- [ ] `send_user_message` composes `run_agent_conversation` once per brought-in Expert, appending each real reply to the SAME shared thread, attributed by `agent_id`/`agent_name`
- [ ] `_relayed_history_for` frames another Expert's own turn as relayed context (`chat_user`-kind, prefixed), never as the called Expert's own past `chat_agent` turn
- [ ] `agent_orchestration`'s own module is unmodified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- People-chip resolution — `T03`.
- Quick research / save-discard — `T04`.
- The HTTP router — `T05`.
- Any frontend change.

---

## Context / Notes

Full mechanism/reasoning: `ADR-036` point 1. Read `agent_orchestration/graph.py::run_agent_conversation`'s REAL current signature/return shape before wiring this task's own calls — do not assume the code sample above is unchanged from what was actually built (this project's own standing "compose around the REAL current file" pattern).

---

## Implementation Log

Implemented exactly as spec'd (`app/business/cockpit/threads.py` new, `__init__.py`
empty). Re-read `agent_orchestration/graph.py::run_agent_conversation`'s real,
current signature/return shape before wiring — matches the task's own sample
exactly: `async def run_agent_conversation(agent_id, message, history, memory=None)
-> dict`, `{"reply", "extracted_facts"}` or `{"error"}`. `state.py::
history_entries_to_messages` confirmed to accept exactly the `{"kind": "chat_user"
| "chat_agent", "text": ...}` shape `_relayed_history_for` builds.

**Manual verification (real `.venv`, real vault, real Compass Provider calls via
`vault-qa`/`people-producer`; found an already-running dev-server process on port
8001 from a prior session — reused it read-only for the MCP loopback call this
task's own composed `run_agent_conversation` needs, since this task's own code
makes no router/main.py change that instance could be serving stale — noted for
`T05`, which DOES need a freshly restarted instance once `cockpit_router.py`/
`main.py` change):**

1. Non-AC: `get_thread("meeting", "test-stem")` → `{"messages": [], "brought_in_agent_ids": []}`. Confirmed.
2. **AC-05:** `bring_in_agent("meeting", "test-stem", "vault-qa")` → `["vault-qa"]`; called again → still `["vault-qa"]` (idempotent). Confirmed.
3. **AC-05:** `send_user_message("meeting", "test-stem", "What's Acme's renewal history?")` → real Compass-backed reply from `vault-qa` appended (a real, honest "couldn't find Acme" answer, not fabricated — vault-qa correctly used its own MCP tools and found nothing). Confirmed.
4. **AC-05/AC-06:** brought in `people-producer` as a second Expert; `send_user_message("meeting", "test-stem", "Anything about Jordan Lee?")` → the SAME `messages` list gained two new agent-attributed replies, one from `vault-qa`, one from `people-producer`, in the one shared thread. Confirmed.
5. **AC-06:** `_relayed_history_for(thread, "people-producer")` → `vault-qa`'s own earlier reply appears prefixed `"[Vault Q&A said]: "` as a `chat_user`-kind entry, never as `chat_agent` (which would misattribute it as `people-producer`'s own past words). Confirmed by direct inspection of the real returned list.
6. **AC-11:** direct code-read of `threads.py` — no import/reference of `route_cross_section_request`/`agent_orchestration.graph.route_cross_section_request` anywhere in this module (confirmed via `Grep`, zero matches). Bringing an Expert into a Cockpit thread cannot alter Hub-routing's own matching behavior by construction — this module never calls it.
7. Cleanup: `.second-brain/cockpit_threads.json` deleted, confirmed absent.

gate: clear 2026-08-14 — no triggers fired (composes `ADR-036`'s own already-made
decision exactly, no assumption beyond the reused-stray-server judgment call above,
which is scope-internal, logged for spot-check, not a MUST-FLAG).
