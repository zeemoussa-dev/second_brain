---
id: REQ-SB-39-US-02-T04
title: skill_registry.py — one-time migration-grant retrofit seed for the 5 real agents carrying the 4 migrated mutating ids
parent_story: REQ-SB-39-US-02
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-02-T03, REQ-SB-39-US-01-T05]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-39-US-02-T04 — migration-grant retrofit seed (mutating ids)

## Parent Story

- Story: [[REQ-SB-39-US-02]] — `../UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

**The explicit retrofit task the operator's own directive ("Everything,
including existing shipped agents") requires — its own task, not folded
into `T03`'s catalog/handler plumbing** (mirrors exactly how
`REQ-SB-39-US-01-T05` handled the read-only retrofit as its own separate
task, `ADR-029` point 7). Extend `skill_registry._load_state()`'s
existing migration-grant seed (already carrying `REQ-SB-39-US-01`'s 3
read-only entries) with 4 new id→agent-list entries for the 5 real,
already-shipped agents that carried the equivalent mutating Action before
this migration.

---

## Starting State → End State

**Before / Inputs** (the real shape after `REQ-SB-39-US-01-T05`):
```python
_MIGRATION_GRANT_SEED = {
    "view_last_run": ["email-capture", "meeting-capture", "todo-capture", "people-producer"],
    "ask_question": ["vault-qa"],
    "view_channel_status": ["vault-qa"],
}
```
— applied inside `_load_state()` via `grant_skill_access`, idempotent.

**After / Outputs:**
```python
_MIGRATION_GRANT_SEED = {
    "view_last_run": ["email-capture", "meeting-capture", "todo-capture", "people-producer"],
    "ask_question": ["vault-qa"],
    "view_channel_status": ["vault-qa"],
    "run_capture_now": ["email-capture", "meeting-capture", "todo-capture"],
    "pause_schedule": ["email-capture", "meeting-capture", "todo-capture"],
    "rebuild_person_note": ["people-producer"],
    "build_knowledge": ["compass-expert"],
}
```
— the same `_load_state()` loop applies every mapping via
`grant_skill_access`, unchanged mechanism. After the next `_load_state()`
call, `email-capture`/`meeting-capture`/`todo-capture` show
`run_capture_now` + `pause_schedule` granted; `people-producer` shows
`rebuild_person_note`; `compass-expert` shows `build_knowledge` —
**5 distinct real agents in total** (confirmed by direct reading of
`agent_registry.py`'s own `AGENTS` catalog, `ADR-029` point 7 — 3 agents
share `run_capture_now`+`pause_schedule`, 2 each carry one distinct id).

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — extend the existing
  `_MIGRATION_GRANT_SEED` dict (do not touch the `_load_state()` loop
  logic itself — it is already generic over the dict's own keys/values).

---

## Constraints

- Inherits from parent story and `ADR-029` point 7.
- The 4 new entries are added to the SAME literal `_MIGRATION_GRANT_SEED`
  dict `REQ-SB-39-US-01-T05` created — do not introduce a second,
  parallel seed dict or a second application loop.
- Exactly the 5 named real agents across the 4 named ids — no other
  agent/skill affected. `vault-filing-expert` is explicitly NOT part of
  any of these 4 mappings (it never carried these Action ids).
- Must remain idempotent — calling `_load_state()` repeatedly must never
  create duplicate entries in any agent's granted-skills array (inherited
  for free from the existing loop's own reuse of `grant_skill_access`'s
  already-idempotent "append if not already granted" behaviour — no new
  logic needed here beyond the dict extension).
- This is a **bounded, one-time historical migration backfill**, not a
  general self-healing default-assignment mechanism (`REQ-SB-39-US-01-T05`'s
  own precedent) — it must NOT grow to cover any future Skill without its
  own new, explicit mapping entry.
- Do NOT modify `skill_tools.py`, `agent_registry.py`, `agent_chat.py`, or
  any file outside `skill_registry.py`.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-02-AC-06] Delete `.second-brain/agent_skills.json` if it
   exists (clean slate — this also re-triggers `REQ-SB-39-US-01-T05`'s own
   3 read-only entries, confirming they still coexist correctly with the
   4 new ones). Call `skill_registry.list_agent_skills("email-capture")`
   — confirm it includes both `"run_capture_now"` and `"pause_schedule"`
   **without any explicit grant call having been made in this test**.
   Repeat for `"meeting-capture"` and `"todo-capture"` — same result.
   Call `skill_registry.list_agent_skills("people-producer")` — confirm
   it includes `"rebuild_person_note"`. Call `skill_registry.
   list_agent_skills("compass-expert")` — confirm it includes
   `"build_knowledge"`. This confirms all 5 real, already-shipped agents
   are genuinely retrofitted, not just theoretically grantable.
2. Idempotency: call `list_agent_skills` (or any function that triggers
   `_load_state()`) a second time — inspect `.second-brain/
   agent_skills.json` directly and confirm no duplicate entries appear in
   any agent's assignments array.
3. Non-AC smoke check: confirm `vault-filing-expert` and `vault-qa` have
   NOT been granted any of these 4 new ids by this seed — proves the
   mapping is exactly scoped, not a blanket grant. (`vault-qa` should
   still show only its own `ask_question`/`view_channel_status` grants
   from `REQ-SB-39-US-01-T05`.)
4. Non-AC smoke check: confirm `REQ-SB-39-US-01-T05`'s own 3 read-only
   entries still resolve correctly after this task's own dict extension
   (`email-capture` still shows `view_last_run`; `vault-qa` still shows
   both its own two ids) — proves the two migration passes compose
   cleanly in the same dict.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `_MIGRATION_GRANT_SEED` extended with exactly 4 new id→agent-list
      entries, applied via the existing `grant_skill_access` loop
- [ ] Idempotent — no duplicate grants on repeated `_load_state()` calls
- [ ] Exactly scoped to the 5 named real agents / 4 named ids — no other
      agent/skill affected
- [ ] `REQ-SB-39-US-01-T05`'s own 3 read-only entries still resolve
      correctly (composes, does not regress)
- [ ] No file other than `skill_registry.py` modified
- [ ] `MEMORY.md` updated — this extends the one-time migration-seed
      pattern `REQ-SB-39-US-01-T05` already recorded
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any future Skill's grant defaults — explicitly not generalized.
- The gate (`T01`), Approve branch (`T02`), and catalog/handler migration
  (`T03`) — all hard prerequisites, not built here.

---

## Context / Notes

**Same known, accepted consequence `REQ-SB-39-US-01-T05` already
documented, now applying to these 4 ids too:** because this seed reuses
`grant_skill_access`'s own idempotent behaviour inside `_load_state()`
(which runs on every read, not just the very first), a real operator who
later explicitly revokes one of these 4 migrated ids from one of the 5
named agents via the ordinary grant/revoke mechanism will find it
silently re-granted on the next `_load_state()` call. This is the
literal, already-accepted behavior established by `ADR-028` point 5 and
carried forward unchanged by `ADR-029` point 7 — not a new wrinkle this
task introduces, and not a defect to fix here.

---

## Implementation Log

**2026-08-14 — Built and verified live.** `_MIGRATION_GRANT_SEED` extended
with the 4 new id→agent-list entries exactly per this task's own
End-State sample. No other change to `_load_state()`'s own loop logic. No
file other than `skill_registry.py` touched.

Real `.second-brain/agent_skills.json` backed up before the clean-slate
test, restored (plus `vault-qa`'s real, genuine pre-existing `web-research`
grant, which is outside the seed mapping) afterward — same protocol
`REQ-SB-39-US-01-T05`'s own Implementation Log established.

- **[REQ-SB-39-US-02-AC-06]** Deleted the real `agent_skills.json` for a
  genuine clean-slate test. `list_agent_skills` for `email-capture`,
  `meeting-capture`, `todo-capture` each returned `run_capture_now` AND
  `pause_schedule` present, with **zero explicit grant calls made in the
  test**. `people-producer` → `rebuild_person_note` present.
  `compass-expert` → `build_knowledge` present. Confirmed by reading the
  real regenerated `agent_skills.json` directly afterward, not just the
  in-memory result. **PASS.**
- Idempotency: called `list_agent_skills` a second time; re-inspected the
  file directly — byte-identical assignments, no duplicate entries in any
  agent's array. **PASS.**
- Non-AC smoke check: `vault-filing-expert` → `[]`; `vault-qa` → exactly
  `["ask_question", "view_channel_status"]` from the clean slate (its own
  real `web-research` grant is outside any seed mapping, by design, and
  was restored separately afterward, not part of this check) — confirms
  the mapping is exactly scoped, no blanket grant. **PASS.**
- Non-AC smoke check: `REQ-SB-39-US-01-T05`'s own 3 read-only entries
  (`view_last_run` on the 4 original agents, `ask_question`/
  `view_channel_status` on `vault-qa`) confirmed still resolving correctly
  alongside the 4 new entries in the same regenerated file — the two
  migration passes compose cleanly in the same dict. **PASS.**

**Real-data restoration:** `vault-qa`'s genuine pre-existing `web-research`
grant re-applied via `grant_skill_access` (idempotent) after the
clean-slate test. Final real `.second-brain/agent_skills.json`, confirmed
by direct read: `email-capture`/`meeting-capture`/`todo-capture`:
`["view_last_run", "run_capture_now", "pause_schedule"]`;
`people-producer`: `["view_last_run", "rebuild_person_note"]`;
`compass-expert`: `["build_knowledge"]`; `vault-qa`: `["ask_question",
"view_channel_status", "web-research"]`; `vault-filing-expert`: `[]` —
exactly the 5 named real agents, exactly the 4 named ids, every
pre-existing real grant preserved.

`skill_tools.py` / `agent_registry.py` — confirmed untouched.

gate: clear 2026-08-14 — no new MUST-FLAG trigger fired (no new
assumption, no ADR change, no escalation, the one locked AC this task owns
verified, no ambiguity).
