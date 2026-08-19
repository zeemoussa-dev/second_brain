---
id: REQ-SB-51-US-01-T03
title: agent_keywords.py — skip Background Agents in Hub-routing candidacy
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-51-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T03 — agent_keywords.py — skip Background Agents in Hub-routing candidacy

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Add one skip inside `agent_keywords.py::list_candidate_agents_for_keyword_match`'s existing per-agent loop so a Background Agent is never returned as a Hub-routing candidate, even with matching keywords assigned — the confirmed sole real call site (`graph.py::_route_hub_request` calls this function exclusively, per the architect's Notes).

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/business/agent_keywords.py::list_candidate_agents_for_keyword_match` (line 25-59) loops every other agent, skipping only the requesting agent and same-Section agents, then checks keyword substring match.
- `T01`'s `background_agent_registry.get_is_background_agent()` exists and is importable.

**After / Outputs:**
- The same function additionally skips any agent for which `background_agent_registry.get_is_background_agent(agent_id)` is `True`, before the keyword check — so a Background Agent with a matching keyword is treated exactly as if it had no keywords assigned at all.
- A non-Background agent's candidacy is completely unaffected (regression guard).

---

## Files to Modify

- `src/backend/app/business/agent_keywords.py`:
  - Add `background_agent_registry` to the `from app.business import ...` line (line 8).
  - Inside `list_candidate_agents_for_keyword_match`'s loop (line 48-58), add a `continue` when `background_agent_registry.get_is_background_agent(agent_id)` is `True`, positioned after the requesting-agent skip and before (or alongside) the Section skip.

---

## Constraints

- Inherits from parent story.
- Do not change the function's own return shape (`[{"agent_id": str, "section_id": str}, ...]`) or its cross-Section-only scope (unrelated to this task).
- `graph.py::_route_hub_request` is the confirmed sole call site (architect's Notes) — no change needed there; do not touch `graph.py`.
- Read live via `background_agent_registry.get_is_background_agent()` on every call — no caching.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-03] In a Python shell (`src/backend`), assign `email-capture` a keyword that would otherwise match (e.g. `agent_keywords.set_agent_keywords("email-capture", ["invoice"])`), confirm `email-capture` is in a different Section from a real requesting agent (e.g. `vault-qa`), and confirm `background_agent_registry.get_is_background_agent("email-capture")` is `True` (from `T01`'s backfill). Call `agent_keywords.list_candidate_agents_for_keyword_match("vault-qa", "please help with this invoice")` — confirm `email-capture` is absent from the returned candidate list, exactly as if it had no keywords assigned. Restore `email-capture`'s keywords to `[]` afterward.
2. [REQ-SB-51-US-01-AC-04] With `vault-qa` (or another non-Background agent) assigned a real matching keyword in a different Section from the requester, call `list_candidate_agents_for_keyword_match` with a matching need description — confirm the non-Background agent IS returned as a candidate, unchanged from pre-task behaviour.
3. [REQ-SB-51-US-01-AC-09, partial] Call `background_agent_registry.set_is_background_agent("email-capture", False)`, re-assign it the same matching keyword, and re-run `list_candidate_agents_for_keyword_match` from step 1 — confirm `email-capture` now IS returned as a candidate (subject to the keyword match), with no restart required. Restore both the flag (`True`) and keywords (`[]`) afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] A Background Agent with a matching keyword is never returned by `list_candidate_agents_for_keyword_match`.
- [ ] A non-Background agent's candidacy is completely unaffected.
- [ ] Un-marking a Background Agent restores its candidacy live, no restart.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Within-Section routing, or any routing mechanism other than the real cross-Section keyword match (already out of scope per `REQ-SB-20-US-01`'s own boundary).
- `graph.py` — confirmed unmodified.
- Any frontend change (`T04`-`T06`).

---

## Context / Notes

Real file to compose against: `src/backend/app/business/agent_keywords.py` (59 lines, read in full above) — re-read it fresh before editing.

---

## Implementation Log

Re-read the real current `agent_keywords.py` (59 lines, unchanged since
this task's own Context/Notes description). Added
`background_agent_registry` to the import line; added one `continue`
skip inside `list_candidate_agents_for_keyword_match`'s loop, positioned
after the requesting-agent skip and before the Section skip, reading
`background_agent_registry.get_is_background_agent(agent_id)` live on
every call. `graph.py` confirmed unmodified (not touched).

Confirmed real cross-Section pairing from a live `GET /agents`: all 3
capture Workers + `vault-qa`/`people-producer`/`vault-filing-expert` are
in `productivity`; `compass-expert` (+ CDP-test agents) are in
`technical` — used `compass-expert` as the requester for a genuine
cross-Section case throughout.

**[REQ-SB-51-US-01-AC-03] Verified live** (real Python shell,
`src/backend`): assigned `email-capture` (Background, `productivity`)
the keyword `"invoice"`; confirmed `get_is_background_agent("email-capture")`
is `True`; called `list_candidate_agents_for_keyword_match("compass-expert",
"please help with this invoice")` — `email-capture` was absent from the
returned candidates (`[]`), exactly as if it had no keywords. Restored
`email-capture`'s keywords to `[]` afterward. PASS.

**[REQ-SB-51-US-01-AC-04] Verified live:** assigned `vault-qa` (not
Background, `productivity`) the same keyword `"invoice"`; the same call
from `compass-expert` returned `vault-qa` as a candidate
(`{"agent_id": "vault-qa", "section_id": "productivity"}`), unchanged
from pre-task behaviour. Restored `vault-qa`'s original keywords
(`["research", "web research"]`) afterward — confirmed by reading them
back before overwriting. PASS.

**[REQ-SB-51-US-01-AC-09, partial] Verified live:** set
`email-capture`'s flag to `False`, re-assigned the same matching keyword,
re-ran the same candidate call — `email-capture` now WAS returned as a
candidate, with no restart. Restored the flag to `True` and keywords to
`[]` afterward, confirmed by a final read of both. PASS.

gate: clear 2026-08-14 — no triggers fired (single, minimal skip inside
an already-`Done` function's existing loop, no ADR touched, no
`graph.py` change, all 3 tagged verification steps passed live with
state fully restored after each).
