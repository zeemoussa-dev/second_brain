---
id: REQ-SB-13-US-01-T02
title: New app/business/agent_registry.py — static agent/settings/actions/trigger-phrases dict
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T02 — New app/business/agent_registry.py

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add the new `app/business/agent_registry.py` — a small, static, hardcoded
dict of the five known agents (settings, available actions, and each
action's `trigger_phrases`), keyed by the same `data-agent-id` values the
approved prototype and `REQ-SB-12-US-01`'s `mockAgents.ts` already use, per
`ADR-011`'s decision to keep this deliberately **not** vault-derived.

---

## Starting State → End State

**Before / Inputs:**
- No agent/settings/actions registry exists anywhere in `src/backend`.
- The approved prototype (`html-prototype/agents-map.html`'s side panel)
  and `REQ-SB-12-US-01`'s `mockAgents.ts` already establish the five agent
  IDs: `email-capture`, `meeting-capture`, `todo-capture`, `people-producer`,
  `vault-qa`.

**After / Outputs:**
- `app/business/agent_registry.py` exists, exporting `AGENTS: dict[str,
  dict]` and `get_agent(agent_id: str) -> dict | None`.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` (new):
  ```python
  """Static, hardcoded known-agent/settings/actions/trigger-phrases registry
  (ADR-011) — deliberately NOT vault-derived, unlike list_known_customers/
  list_known_kinds (see ADR-011's own reasoning: which agents exist is
  app/deployment configuration, not open-ended vault content). Only
  email-capture's run_capture_now has a real handler this pass — every
  other declared action has none yet (see app/api/agents_router.py, T05)."""

  AGENTS: dict[str, dict] = {
      "email-capture": {
          "name": "Email Capture",
          "type": "worker",
          "settings": [
              {"key": "Schedule", "value": "Hourly + once on app start"},
              {"key": "Vault target", "value": "Work/Emails/"},
              {"key": "Classifier", "value": "Compass (GPT-5)"},
              {"key": "Missed-run catch-up", "value": "Enabled"},
          ],
          "actions": [
              {
                  "id": "run_capture_now",
                  "label": "Run capture now",
                  "trigger_phrases": ["run capture now", "run capture", "capture now"],
              },
              {
                  "id": "view_last_run",
                  "label": "View last run",
                  "trigger_phrases": ["view last run", "last run"],
              },
              {
                  "id": "pause_schedule",
                  "label": "Pause schedule",
                  "trigger_phrases": ["pause schedule", "pause capture"],
              },
          ],
      },
      "meeting-capture": {
          "name": "Meeting Capture",
          "type": "worker",
          "settings": [
              {"key": "Schedule", "value": "Hourly + once on app start"},
              {"key": "Vault target", "value": "Work/Meetings/"},
              {"key": "Classification", "value": "By customer (shared with Email Capture)"},
              {"key": "Duplicate handling", "value": "Skipped on rerun"},
          ],
          "actions": [
              {
                  "id": "run_capture_now",
                  "label": "Run capture now",
                  "trigger_phrases": ["run capture now", "run capture", "capture now"],
              },
              {
                  "id": "view_last_run",
                  "label": "View last run",
                  "trigger_phrases": ["view last run", "last run"],
              },
              {
                  "id": "pause_schedule",
                  "label": "Pause schedule",
                  "trigger_phrases": ["pause schedule", "pause capture"],
              },
          ],
      },
      "todo-capture": {
          "name": "To-Do Capture",
          "type": "worker",
          "settings": [
              {"key": "Schedule", "value": "Hourly + once on app start"},
              {"key": "Task source", "value": "Open question — resolved at /spec (REQ-SB-09)"},
          ],
          "actions": [
              {
                  "id": "run_capture_now",
                  "label": "Run capture now",
                  "trigger_phrases": ["run capture now", "run capture", "capture now"],
              },
              {
                  "id": "view_last_run",
                  "label": "View last run",
                  "trigger_phrases": ["view last run", "last run"],
              },
              {
                  "id": "pause_schedule",
                  "label": "Pause schedule",
                  "trigger_phrases": ["pause schedule", "pause capture"],
              },
          ],
      },
      "people-producer": {
          "name": "People Notes",
          "type": "producer",
          "settings": [
              {"key": "Triggers on", "value": "New sender / meeting attendee"},
              {"key": "Vault target", "value": "Work/People/"},
              {"key": "Manual-edit protection", "value": "Preserves user-added content"},
          ],
          "actions": [
              {
                  "id": "rebuild_person_note",
                  "label": "Rebuild a person note",
                  "trigger_phrases": ["rebuild person note", "rebuild a person note"],
              },
              {
                  "id": "view_last_run",
                  "label": "View last run",
                  "trigger_phrases": ["view last run", "last run"],
              },
          ],
      },
      "vault-qa": {
          "name": "Vault Q&A",
          "type": "expert",
          "settings": [
              {"key": "Grounding", "value": "Indexed vault (REQ-SB-01/02)"},
              {"key": "Reachable via", "value": "This panel + Hermes channels"},
              {"key": "Write access", "value": "Read-only here (see REQ-SB-04 for write scope)"},
          ],
          "actions": [
              {
                  "id": "ask_question",
                  "label": "Ask a question",
                  "trigger_phrases": ["ask a question", "ask question"],
              },
              {
                  "id": "view_channel_status",
                  "label": "View channel status",
                  "trigger_phrases": ["view channel status", "channel status"],
              },
          ],
      },
  }


  def get_agent(agent_id: str) -> dict | None:
      return AGENTS.get(agent_id)
  ```

---

## Constraints

- Inherits from parent story: `ADR-011`'s decision that this registry is a
  static hardcoded dict, **not** vault-derived (do not add any filesystem/
  `vault_writer` read here).
- Agent IDs, action IDs, and `trigger_phrases` values are this task's own
  reasonable choices grounded in the approved prototype's shown labels
  (`html-prototype/agents-map.html`'s side panel) — not asserted as a fixed
  final action set (per the parent story's own Notes: "the exact action set
  per agent shown in the prototype is illustrative of the surface, not
  asserted as a fixed final list").
- Only `email-capture`'s `run_capture_now` gets a real handler — that wiring
  happens in `T05` (the router), not here; this task declares data only, no
  handler logic.

---

## Tests

<!-- Exercised end-to-end, live, by T05's router endpoint (GET
/agents/{agent_id}), where this story's locked ACs are tagged. The smoke
check below confirms the registry in isolation first. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (cwd
   `src/backend`), call `agent_registry.get_agent("email-capture")`.
   Confirm it returns a dict with `name`/`type`/`settings`/`actions` keys,
   `settings` is a non-empty list of `{"key", "value"}` dicts, and
   `actions` is a non-empty list where each entry has `id`/`label`/
   `trigger_phrases`. Call `agent_registry.get_agent("not-a-real-agent")`;
   confirm it returns `None`. Confirm `len(agent_registry.AGENTS) == 5`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `AGENTS` declares all five agents (`email-capture`, `meeting-capture`,
      `todo-capture`, `people-producer`, `vault-qa`) with `name`/`type`/
      `settings`/`actions`
- [ ] Every action declares `id`/`label`/`trigger_phrases`
- [ ] `get_agent(agent_id)` returns `None` for an unknown ID
- [ ] No filesystem/vault read anywhere in this module
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring any action to a real handler — `T05`.
- The chat keyword-matching mechanism itself — `T03`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

Per `ADR-011`'s own Consequences, this registry is expected to go stale the
moment REQ-SB-08/09/03 actually ship real, callable pipelines — each of
those future stories' own `/plan-tasks` pass should add a real handler
entry, not rewrite this one.

---

## Implementation Log

**2026-08-11, coder pass.** Created `app/business/agent_registry.py` with
`AGENTS` (all 5 agents: `email-capture`, `meeting-capture`, `todo-capture`,
`people-producer`, `vault-qa`) and `get_agent()`, verbatim per this task's
spec. No filesystem/vault read anywhere in the module.

Live confirmation (superseding the isolated Python-shell smoke check, via
T05's real `GET /agents/{agent_id}` endpoint instead — same reasoning as
T01's Log): `GET /agents/email-capture` returned `name`/`type`/`settings`/
`actions` with non-empty lists, `GET /agents/not-a-real-agent` returned
`404` (via `agent_registry.get_agent()` returning `None`, checked in T05's
router). `len(AGENTS) == 5` confirmed by direct code inspection of the
module (all 5 top-level keys present) rather than a separate shell
invocation.

- [x] `AGENTS` declares all five agents with `name`/`type`/`settings`/`actions` — confirmed
- [x] Every action declares `id`/`label`/`trigger_phrases` — confirmed by code review
- [x] `get_agent(agent_id)` returns `None` for an unknown ID — confirmed live via T05
- [x] No filesystem/vault read anywhere in this module — confirmed by code review (no `open`/`Path`/`vault_writer` import)
- [x] `MEMORY.md` updated — yes, see Decisions entry for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes

Assumption (scope-internal, logged for spot-check): same live-endpoint
substitution as T01, for the same reason (avoids a redundant isolated
shell invocation once T05's router exists in the same pass).
