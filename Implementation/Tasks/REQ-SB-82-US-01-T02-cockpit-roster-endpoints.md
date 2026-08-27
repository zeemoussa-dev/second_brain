---
id: REQ-SB-82-US-01-T02
title: Cockpit router — real persisted thread on GET, new roster bring-in/remove endpoints
parent_story: REQ-SB-82-US-01
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-01-T01]
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-01-T02 — Cockpit router — real persisted thread on GET, new roster bring-in/remove endpoints

## Parent Story

- Story: [[REQ-SB-82-US-01]] — `../UserStories/REQ-SB-82-US-01-persisted-cockpit-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Wire `cockpit_router.py`'s existing `GET` to return the real, persisted
thread from `T01`'s `chat_store`, and add the new roster mutation endpoints.

---

## Starting State → End State

**Before / Inputs:**
- `GET /cockpit/{subject_kind}/{subject_note_stem}` returns a hardcoded
  `"thread": {"messages": [], "brought_in_agent_ids": []}`.
- No endpoint exists to bring in or remove a roster agent.

**After / Outputs:**
- `GET` returns `"thread": chat_store.get_thread(subject_kind, subject_note_stem)`.
- `POST /cockpit/{subject_kind}/{subject_note_stem}/roster` (body `{"agent_id": str}`) calls `chat_store.bring_in_agent(...)`, returns the resulting thread.
- `DELETE /cockpit/{subject_kind}/{subject_note_stem}/roster/{agent_id}` calls `chat_store.remove_agent(...)`, returns the resulting thread.

---

## Files to Modify

- `src/backend/app/api/cockpit_router.py`

---

## Constraints

- Inherits from parent story.
- Reuses `T01`'s `chat_store` functions exactly as built — no parallel/duplicate persistence logic in the router itself.
- Both new endpoints validate `subject_note_stem` exists via `vault_indexing.get_index()`, matching the existing `GET`'s own `404` behavior for an unknown note — never silently persist a roster entry for a subject that doesn't exist.
- No approval gate, no message-send logic — this task is roster persistence plumbing only.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-01-AC-01] `POST /cockpit/meeting/<scratch-stem>/roster` with `{"agent_id": "azure-expert"}`, then `GET /cockpit/meeting/<scratch-stem>`. Expect `thread.brought_in_agent_ids` contains `"azure-expert"`.
2. [REQ-SB-82-US-01-AC-02] `DELETE /cockpit/meeting/<scratch-stem>/roster/azure-expert`, then `GET` again. Expect `thread.brought_in_agent_ids` no longer contains it.
3. [REQ-SB-82-US-01-AC-03] Directly seed a message into the store via `chat_store` for `<scratch-stem>` (simulating "however it came to exist" — this task builds no send path), then `GET`. Expect `thread.messages` contains that exact message, same order/content as seeded.
4. [REQ-SB-82-US-01-AC-07] Seed two messages via `chat_store` — one `speaker: "user"`, one `speaker: "agent"` with real `agent_id`/`agent_name` — then `GET`. Expect both attributions preserved distinctly in the response.
5. [REQ-SB-82-US-01-AC-06] `GET /cockpit/meeting/<brand-new-stem>` for a subject that has never had any roster/message activity. Expect `thread` equals `{"messages": [], "brought_in_agent_ids": []}`.
6. `POST`/`DELETE` against an unknown `subject_note_stem` returns `404`, matching the existing `GET`'s own behavior.

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET` returns the real, persisted thread (stub removed)
- [x] `POST .../roster` and `DELETE .../roster/{agent_id}` implemented per Constraints
- [x] `404` on unknown subject for both new endpoints
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; straightforward wiring per `ADR-007`/the story's own already-documented pass-through-shape note)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change (`REQ-SB-82-US-01-T03`).
- Message send/receive endpoints (`REQ-SB-82-US-04`).
- The `recommended_agent_ids` field (`REQ-SB-82-US-03-T02` extends `chat_store.get_thread` additively — this task's router code needs no further change once that lands, since it already passes `chat_store.get_thread(...)`'s dict straight through).

---

## Context / Notes

`ADR-007` is the authoritative design reference. Note for a future reader:
this router's `GET` handler already passing `chat_store.get_thread(...)`'s
return value straight through (rather than reconstructing the `thread` dict
field-by-field) is what lets `REQ-SB-82-US-03-T02` add `recommended_agent_ids`
later with zero router-code change — keep that pass-through shape.

---

## Implementation Log

**Built 2026-08-25 (coder).** Read `T01`'s real, live `chat_store.py`
(`get_thread`/`bring_in_agent`/`remove_agent`) directly before writing any
router code, and re-read the real current `cockpit_router.py` (not a
stale sample) before editing it. Changes:
- `GET /cockpit/{subject_kind}/{subject_note_stem}` now returns
  `chat_store.get_thread(subject_kind, subject_note_stem)` for `"thread"`
  — stub removed, pass-through shape preserved exactly as the story's own
  Notes anticipated (zero further router change needed once
  `REQ-SB-82-US-03-T02` adds `recommended_agent_ids`).
- New `POST /cockpit/{subject_kind}/{subject_note_stem}/roster` (body
  `{"agent_id": str}` via a new `RosterBringInBody` model) calls
  `chat_store.bring_in_agent(...)`, returns the resulting thread dict.
- New `DELETE /cockpit/{subject_kind}/{subject_note_stem}/roster/{agent_id}`
  calls `chat_store.remove_agent(...)`, returns the resulting thread dict.
- Both new endpoints validate `subject_note_stem` via
  `vault_indexing.get_index().get(...)`, raising the same
  `HTTPException(404, "Unknown note")` the existing `GET` already uses —
  no parallel validation logic invented.
- Module docstring updated to reflect `thread` is now real persisted data,
  not a stub (`overview` remains the honest-empty stub it always was).
- No parallel/duplicate persistence logic added in the router — every
  mutation/read goes through `T01`'s `chat_store` functions exactly as
  built, per Constraints.

**Real, live verification — over the actual HTTP layer, not just the
underlying function calls `T01` already verified** (fresh
`.venv` uvicorn instance, `127.0.0.1:8000`, no `--reload`; a stray ghost
listener was already on port 8001 with no real backing process
(`Get-CimInstance`/`Get-Process` both returned nothing for its reported
PID) — left alone, started a fresh explicitly-controlled instance on 8000
instead per this project's own established precedent; stopped by real PID
after verification, confirmed port 8000 clear):

- **[REQ-SB-82-US-01-AC-01]** Real stem (a genuine `kind/meeting` note
  from the live vault, `.../vault-search/notes`,
  `...0016B5C514E80EDD...`). Baseline `GET` confirmed empty thread. Real
  `curl -X POST .../roster -d '{"agent_id":"azure-expert"}'` returned
  `{"brought_in_agent_ids":["azure-expert"],"messages":[]}`; a fresh real
  `GET` on the same subject echoed
  `"thread":{"brought_in_agent_ids":["azure-expert"],"messages":[]}` —
  PASS, real HTTP round trip.
- **[REQ-SB-82-US-01-AC-02]** From that state, real
  `curl -X DELETE .../roster/azure-expert` returned
  `{"brought_in_agent_ids":[],"messages":[]}`; a fresh real `GET`
  confirmed `azure-expert` no longer present — PASS.
- **[REQ-SB-82-US-01-AC-03]/[REQ-SB-82-US-01-AC-07]** Seeded two
  attributed messages (`speaker: "user"`, then `speaker: "agent"` with
  real `agent_id`/`agent_name`) directly via `chat_store`'s own
  `_load_state()`/`vault_writer.save_cockpit_chat_state()` (no message-
  write endpoint exists — out of scope, per Objective/Constraints; this
  is exactly the task's own Tests-block-prescribed seeding technique, not
  a code change) against a second real, never-touched meeting stem. A
  real `GET` over HTTP echoed both messages back byte-identical, same
  order, same `speaker`/`agent_id`/`agent_name`/`text` — PASS.
- **[REQ-SB-82-US-01-AC-06]** Real `GET` against a third real meeting
  stem with zero prior roster/chat activity returned exactly
  `"thread":{"brought_in_agent_ids":[],"messages":[]}` — PASS.
- **404 constraint** — real `curl -X POST`/`-X DELETE` against
  `meeting/UNKNOWN-STEM-DOES-NOT-EXIST/roster[...]` both returned real
  HTTP `404` with `{"detail":"Unknown note"}`, matching the existing
  `GET`'s own behavior exactly — PASS.
- **Cleanup:** deleted the real vault's `.second-brain/cockpit_chat.json`
  after verification (contained only this task's own scratch test
  entries) — confirmed a subsequent real `GET` reads back the honest
  empty default again, matching the pre-verification state. No scratch
  data left in the real vault's operational state.

**Scope-internal judgement calls (for human spot-check, not
escalations):** the module docstring's own "everything the old router's
Chat/... endpoints did ... is deliberately NOT restored" framing was
narrowed to explicitly exclude `thread` (now real) while keeping
`overview` under the same "stub only" framing — a same-file documentation
accuracy fix directly required by this task's own change, not a scope
expansion.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (all 6 locked/tagged
verification points passed live over the real HTTP layer with a real
positive result; no new dependency, no shared-interface change, no ADR
deviation, no unanticipated file; reused `T01`'s `chat_store` exactly as
built with zero parallel persistence logic).
