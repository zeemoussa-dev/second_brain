---
id: REQ-SB-82-US-03-T02
title: Compute-on-first-read, cache recommended_agent_ids on the persisted roster entry
parent_story: REQ-SB-82-US-03
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-03-T01, REQ-SB-82-US-01-T01, REQ-SB-82-US-01-T02]
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-03-T02 — Compute-on-first-read, cache recommended_agent_ids on the persisted roster entry

## Parent Story

- Story: [[REQ-SB-82-US-03]] — `../UserStories/REQ-SB-82-US-03-meeting-moderator-roster-pre-assembly.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Wire `T01`'s two matching tracks into `chat_store.get_thread` so the FIRST
real read for a subject with no `recommended_agent_ids` entry yet computes
and persists both tracks' combined result; every subsequent read serves
the cached value.

---

## Starting State → End State

**Before / Inputs:**
- `chat_store.get_thread(subject_kind, subject_note_stem)` (`REQ-SB-82-US-01-T01`) returns `{"brought_in_agent_ids": [...], "messages": [...]}` with no recommendation field.
- `cockpit_router.py`'s `GET` (`REQ-SB-82-US-01-T02`) already passes `chat_store.get_thread(...)`'s dict straight through as `"thread"`.

**After / Outputs:**
- `chat_store.get_thread` additively returns `"recommended_agent_ids": [str, ...]` — computed via `moderator.match_customer_expert`/`match_domain_experts` (combined, deduplicated) the FIRST time a subject's persisted entry has no such key, then persisted into that same entry; every later call reads the cached value without recomputing.
- No router-code change needed (the existing pass-through already surfaces the new field).

---

## Files to Modify

- `src/backend/app/business/cockpit/chat_store.py`

---

## Constraints

- Inherits from parent story.
- `recommended_agent_ids` is a non-authoritative hint list, separate from `brought_in_agent_ids` — never mutated by `bring_in_agent`/`remove_agent`, and bringing a recommended agent in uses the exact same `bring_in_agent` path as any manual bring-in.
- Compute-once-then-cache: a subject whose entry already has a `recommended_agent_ids` key (even `[]`, an honest "computed, nothing matched" result) must NOT be recomputed on a later read.
- Both matching tracks always run together and combine (never one suppressing the other) — reuse `T01`'s functions directly, no reimplementation.
- No new Hermes profile, cron job, or scheduled task — this stays synchronous, inside the existing read path.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-03-AC-03] Call `get_thread` for a scratch subject matching BOTH a real customer (e.g. Masdar) AND a real domain expert (e.g. Azure-tagged). Expect `recommended_agent_ids` contains BOTH `"masdar-expert"` and the matched domain expert id together.
2. Call `get_thread` a SECOND time for the same subject; confirm (e.g. via a call-count monkeypatch on `moderator.match_customer_expert`/`match_domain_experts`) that neither matching function is invoked again — the cached value is served as-is.
3. Confirm a subject matching neither track persists `recommended_agent_ids: []` (not recomputed on a later read either) — the honest-empty case is cached too, not treated as "not yet computed."

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_thread` additively returns `recommended_agent_ids`, computed-once-then-cached
- [x] `bring_in_agent`/`remove_agent` never touch `recommended_agent_ids`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The matching logic itself (`T01`).
- Any frontend rendering (`T03`).
- Any router-code change (the existing pass-through already surfaces the field).

---

## Context / Notes

`ADR-009` is the authoritative design reference — read its "Trigger" and
"Persisted schema" Decision points before starting. This is an ADDITIVE
schema change to `T01`(`US-01`)'s own per-subject entry shape — do not
introduce a second store or file.

---

## Implementation Log

**Build, 2026-08-25 (coder):** `chat_store.py::get_thread` now, when an
entry has no `recommended_agent_ids` key yet (a brand-new subject entry,
or an existing entry pre-dating this task), calls `moderator.match_
customer_expert`/`match_domain_experts` (both real, unmodified `T01`
functions), combines the results (`([customer_id] if any) +
domain_ids`), deduplicates order-preservingly (`dict.fromkeys`), and
persists onto the SAME `ADR-007` per-subject entry via the existing
`vault_writer.save_cockpit_chat_state` primitive — matching `ADR-009`
Decision 3/4 exactly. `bring_in_agent`/`remove_agent` were not touched
(they already only read/write `brought_in_agent_ids`).

**Scope-internal judgement call (for human spot-check, not an
escalation):** the pre-existing `get_thread` for a subject with NO
existing entry returned an ephemeral dict with zero disk write. Making
`recommended_agent_ids` compute-once-then-cache required this first-read
case to also create and persist a real entry (otherwise the honest `[]`
result would be recomputed every read, violating the AC). Logged as
`MEMORY.md` Constraint (`get_thread` is no longer side-effect-free on
first read) rather than silently left undocumented.

**Verification (manual mode, live, no mocks for the matching logic
itself):**

- **[REQ-SB-82-US-03-AC-03]** Created two real scratch Meeting notes in
  the real, configured vault (`Work/Meetings/`): one tagged/foldered
  `customer: "Masdar"` + `tags: ["customer/masdar", "kind/meeting"]`
  with "Azure" in its own title (for the domain-match track), one with
  no customer signal and no domain-overlapping vocabulary (for the
  neither-track case). Backed up the real, pre-existing
  `.second-brain/cockpit_chat.json` first. Rebuilt the vault index and
  called `chat_store.get_thread("meeting", "...Masdar Azure Meeting")`
  directly (Python shell, per this project's own "skip the HTTP layer
  when it isn't load-bearing" precedent — the Tests block's own step 2
  needs a call-count monkeypatch, which is a Python-level check anyway).
  **Observed:** `recommended_agent_ids` contained BOTH `"masdar-expert"`
  AND `"azure-expert"` (plus every other real Azure-domain expert whose
  `name`/`description` tokens overlapped the subject's own "Azure"
  token, per `T01`'s own already-verified keyword-overlap behavior —
  out of this task's scope to narrow). **PASS.**
- Step 2 (cache — no recompute on second read): monkeypatched
  `moderator.match_customer_expert`/`match_domain_experts` with
  call-counting wrappers around the real functions, then called
  `get_thread` a second time for the same subject. **Observed:**
  `call_counts == {"customer": 0, "domain": 0}` and the returned
  `recommended_agent_ids` was byte-identical to the first read. **PASS.**
- Step 3 (honest empty, also cached): called `get_thread` for the
  neither-track scratch subject. **Observed:** `recommended_agent_ids
  == []` on the first read; a second read with the same call-count
  monkeypatch showed `{"customer": 0, "domain": 0}` — the empty result
  was cached, not left "not yet computed." **PASS.**
- Additional check (Constraint: `bring_in_agent`/`remove_agent` never
  touch the field): called both against the Masdar+Azure scratch
  subject; `recommended_agent_ids` was byte-identical before and after
  each call, while `brought_in_agent_ids` correctly round-tripped.
  **PASS.**
- Bonus, real HTTP-layer reconfirmation (no router code was touched, per
  Out of Scope): restarted the backend cleanly on an alternate port
  (port 8001 was held by a genuinely zombie socket — see below), forcing
  a fresh vault-index rebuild that picked up the scratch notes, then
  called the real, unmodified `GET /cockpit/meeting/...Masdar Azure
  Meeting` endpoint. **Observed:** the JSON response's `"thread"` field
  included the identical, already-persisted `recommended_agent_ids` —
  confirms the existing pass-through needed zero changes, exactly as the
  task's End-State claimed.

All verification artefacts (the two scratch notes, the throwaway
verification script) were deleted afterward; the real
`.second-brain/cockpit_chat.json` was restored to its exact
pre-verification byte content (confirmed via a fresh read after
restore — only the one real, pre-existing `"meeting:2026-08-17 1500
Discuss with Mousa"` entry remains, unchanged).

**Environment note (not a code finding):** port 8001 (this project's own
usual backend dev port) was held by a listening socket attributed to a
PID that no process-enumeration tool (`Get-Process`, `Get-CimInstance
Win32_Process`) could find alive — a genuinely zombie kernel socket, not
a recoverable orphaned process. Per this project's own documented
antipattern precedent (pivot to an alternate port once multiple
independent tools agree a reported PID doesn't exist), verification ran
against port 8002 instead; the throwaway verification backend instance
was killed by its own real PID afterward, leaving nothing running.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (no new dependency,
no shared-interface change beyond the task's own declared additive
schema field, no ADR deviation, no unanticipated file; the one
scope-internal judgement call above is disclosed for spot-check, not an
escalation).
