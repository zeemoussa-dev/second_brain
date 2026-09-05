---
id: REQ-SB-82-US-01-T01
title: Cockpit chat store — real, per-subject-keyed persistence for roster + messages
parent_story: REQ-SB-82-US-01
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-01-T01 — Cockpit chat store — real, per-subject-keyed persistence for roster + messages

## Parent Story

- Story: [[REQ-SB-82-US-01]] — `../UserStories/REQ-SB-82-US-01-persisted-cockpit-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Build the real, per-subject-keyed persistence module (`ADR-007`) backing the
Cockpit Chat tab's brought-in roster and message history, replacing the
honest-empty-stub read path with genuine, file-backed storage.

---

## Starting State → End State

**Before / Inputs:**
- No real Cockpit chat persistence exists. `cockpit_router.py`'s `GET`
  returns a hardcoded `{"messages": [], "brought_in_agent_ids": []}` stub.
- `app/data_access/vault_writer.py` already has `load_cockpit_threads_state`/
  `save_cockpit_threads_state` (backing `.second-brain/cockpit_threads.json`)
  — these are the STALE, pre-Hermes-pivot `ADR-036` functions. **Do not
  reuse, import, or extend them** — `ADR-007` explicitly rejects reviving
  that design; they belong to `business/cockpit/threads.py`, which stays
  untouched and dead.
- The established sibling-function precedent to mirror is
  `load_agent_visuals_state`/`save_agent_visuals_state` (same file,
  `_agent_visuals_state_path`) — read-whole-file, `None` if missing,
  write-whole-file, no locking layer.

**After / Outputs:**
- A brand-new `app/business/cockpit/chat_store.py` module with
  `get_thread(subject_kind, subject_note_stem) -> dict`,
  `bring_in_agent(subject_kind, subject_note_stem, agent_id) -> dict`,
  `remove_agent(subject_kind, subject_note_stem, agent_id) -> dict`
  (each returns the resulting `CockpitThread`-shaped dict).
- A brand-new pair of sibling functions in `vault_writer.py`:
  `load_cockpit_chat_state() -> dict | None` / `save_cockpit_chat_state(state: dict) -> None`,
  backed by a NEW file, `.second-brain/cockpit_chat.json`.

---

## Files to Modify

- `src/backend/app/business/cockpit/chat_store.py` (new file)
- `src/backend/app/data_access/vault_writer.py` — add `_COCKPIT_CHAT_FILE = "cockpit_chat.json"`, `_cockpit_chat_state_path()`, `load_cockpit_chat_state()`, `save_cockpit_chat_state()` as new sibling functions (do not touch the existing `_cockpit_threads_state_path`/`load_cockpit_threads_state`/`save_cockpit_threads_state` — leave them exactly as-is, dead code belonging to the stale module)

---

## Constraints

- Inherits from parent story.
- The per-subject entry key is exactly `"{subject_kind}:{subject_note_stem}"`
  in one flat top-level dict — never a separate file per subject (`ADR-007`).
- Entry shape: `{"brought_in_agent_ids": [str, ...], "messages": [{"speaker": "user"|"agent", "agent_id": str|None, "agent_name": str|None, "text": str}, ...]}` — exactly `cockpitApiClient.ts`'s existing `CockpitThread` TS contract. Do not add a `recommended_agent_ids` key in this task — `REQ-SB-82-US-03-T02` adds that field additively, later.
- `get_thread` on a subject key with no prior entry returns the honest-empty default (`{"brought_in_agent_ids": [], "messages": []}`), never `None`/an error — never fabricate content.
- `bring_in_agent`/`remove_agent` only ever mutate `brought_in_agent_ids` — never touch `messages` (no send/receive logic here; that is `REQ-SB-82-US-04`'s concern, out of scope).
- `chat_store.py` never composes a Hermes call itself — pure roster/message storage only.
- Follow the load/save pattern exactly: read-whole-file, default-if-missing, write-whole-file, no locking layer (matches every other single-key JSON store in this app).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-01-AC-01] Call `chat_store.bring_in_agent("meeting", "<scratch-stem>", "azure-expert")`, then — in a FRESH call (re-read from disk, not the same in-memory object) — call `chat_store.get_thread("meeting", "<scratch-stem>")`. Expect `"azure-expert"` present in `brought_in_agent_ids`, proving real, file-backed persistence, not just in-memory state.
2. [REQ-SB-82-US-01-AC-02] From the state left by step 1, call `chat_store.remove_agent("meeting", "<scratch-stem>", "azure-expert")`, then a fresh `get_thread(...)`. Expect `brought_in_agent_ids` no longer contains it.
3. [REQ-SB-82-US-01-AC-05] Bring a different agent into TWO different subject keys (e.g. `("meeting", "stem-a")` and `("email", "stem-b")`). Confirm `get_thread` for each key returns ONLY its own agent — never the other subject's roster.
4. [REQ-SB-82-US-01-AC-06] Call `get_thread` for a brand-new subject key that has never had any activity. Expect `{"brought_in_agent_ids": [], "messages": []}` — no exception, no fabricated content.
5. Confirm `.second-brain/cockpit_chat.json` is the real file written (inspect its contents directly) and that `.second-brain/cockpit_threads.json` (the old, stale file) is untouched by any of the above — proves no accidental reuse of the old store.

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `chat_store.get_thread`/`bring_in_agent`/`remove_agent` implemented per Constraints
- [x] `vault_writer.load_cockpit_chat_state`/`save_cockpit_chat_state` implemented, backed by `.second-brain/cockpit_chat.json`
- [x] Old `load_cockpit_threads_state`/`save_cockpit_threads_state`/`cockpit_threads.json` left untouched, not reused
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any HTTP endpoint (`REQ-SB-82-US-01-T02`).
- Any frontend change (`REQ-SB-82-US-01-T03`).
- Message send/receive logic (`REQ-SB-82-US-04`).
- The `recommended_agent_ids` field (`REQ-SB-82-US-03-T02`).

---

## Context / Notes

`ADR-007` (`Implementation/Architecture/ADR.md`) is the authoritative design
reference — read it before starting. The stale `business/cockpit/threads.py`
composes a function (`run_agent_conversation`) that no longer exists
post-Hermes-pivot; do not open that file as a starting point for this task.

---

## Implementation Log

**Built 2026-08-25 (coder).** New module `app/business/cockpit/
chat_store.py` (`get_thread`/`bring_in_agent`/`remove_agent`), mirroring
`agent_visual_registry.py`'s `_load_state`/getter/setter shape exactly
(`_load_state()` defaults to `{}` on `None`, per-key default entry via
`setdefault`). New sibling functions `_cockpit_chat_state_path`/
`load_cockpit_chat_state`/`save_cockpit_chat_state` added to
`vault_writer.py` immediately after the existing (untouched)
`save_cockpit_threads_state`, mirroring `_agent_visuals_state_path`'s
own read-whole-file/default-if-missing/write-whole-file shape, no
locking layer. Never imports `business/cockpit/threads.py`.

**Real, live verification (`.venv` python, real vault at the real
`VAULT_PATH`, NOT a mock/in-memory stub):**

- **[REQ-SB-82-US-01-AC-01]** Called `chat_store.bring_in_agent("meeting",
  "SCRATCH-TEST-STEM-T01", "azure-expert")`, then a fresh
  `chat_store.get_thread("meeting", "SCRATCH-TEST-STEM-T01")` in the same
  process but re-reading `cockpit_chat.json` from disk on every call
  (no in-memory cache anywhere in `chat_store.py`/`vault_writer.py`).
  Observed: `{"brought_in_agent_ids": ["azure-expert"], "messages": []}`
  — PASS.
- **[REQ-SB-82-US-01-AC-02]** From that state, called
  `chat_store.remove_agent("meeting", "SCRATCH-TEST-STEM-T01",
  "azure-expert")`, then a fresh `get_thread(...)`. Observed:
  `{"brought_in_agent_ids": [], "messages": []}` — `azure-expert` no
  longer present — PASS.
- **[REQ-SB-82-US-01-AC-05]** Brought `"compass-expert"` into
  `("meeting", "stem-a")` and `"notes-manager"` into `("email",
  "stem-b")`. `get_thread("meeting", "stem-a")` returned only
  `["compass-expert"]`; `get_thread("email", "stem-b")` returned only
  `["notes-manager"]` — no cross-subject leakage — PASS.
- **[REQ-SB-82-US-01-AC-06]** Called `get_thread("meeting",
  "NEVER-TOUCHED-STEM")` for a subject key with zero prior activity.
  Observed exactly `{"brought_in_agent_ids": [], "messages": []}`, no
  exception — PASS.
- **File-on-disk confirmation:** read `.second-brain/cockpit_chat.json`
  directly off the real vault path
  (`<OPERATOR_VAULT_OLD>\.second-brain\cockpit_chat.json`)
  after the calls above — contained exactly the 3 real per-subject
  entries written (`meeting:SCRATCH-TEST-STEM-T01`, `meeting:stem-a`,
  `email:stem-b`), confirming genuine file-backed persistence, not
  in-memory state. Confirmed `.second-brain/cockpit_threads.json` (the
  old, stale file) does NOT exist on disk before or after — no
  accidental read/write of the old store. `cockpit_chat.json` did not
  exist before this run either (this is genuinely new storage); deleted
  it after verification to leave no scratch test data in the real
  vault's operational state (the file legitimately does not exist again
  until a real Chat bring-in happens, matching the honest-empty-default
  behaviour of `get_thread` itself).
- `AC-03`/`AC-04`/`AC-07` (message-log ordering/persistence-on-navigation/
  message attribution) are NOT verified by this task — this task's own
  Constraints explicitly exclude message send/receive logic
  (`REQ-SB-82-US-04`'s concern); those three ACs are verified by later
  tasks in this story once a router/frontend exist to actually produce a
  message. No message-log code beyond the empty `"messages": []` default
  exists yet in this task's scope.

**Scope-internal judgement calls (for human spot-check, not
escalations):** none beyond what's disclosed above — the module was
built exactly to the task's own Constraints/End-State, no ambiguity
encountered.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (all 4 in-scope
locked ACs verified live with a real positive result; no new
dependency, no shared-interface change, no ADR deviation, no
unanticipated file).
