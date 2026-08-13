---
id: REQ-SB-21-US-01-T09
title: agent_registry.py — new "mutates" bool field on every action definition + new get_action(agent_id, action_id) lookup helper (ADR-020 point 1)
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-21-US-01-T09 — agent_registry.py mutates classification + get_action

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add a `"mutates": bool` field to every action definition dict in
`app/business/agent_registry.py`'s static `AGENTS` catalog, classified from
each action's real current behaviour (`ADR-020` point 1) — not guessed from
its id/label. Add a new `get_action(agent_id, action_id) -> dict | None`
lookup helper so `T04`'s gate has one place to resolve an action's
`mutates` flag without duplicating the nested-list search inline. This task
is the one piece of `ADR-020`'s design no task in this story's original
(`ADR-018`-only) `T01`-`T08` breakdown ever covered — genuinely new scope,
not a rewrite of existing work.

---

## Starting State → End State

**Before / Inputs:**
- `agent_registry.py`'s `AGENTS` dict has 5 agents, 12 action entries across
  6 distinct action ids (`run_capture_now` ×3, `view_last_run` ×4,
  `pause_schedule` ×3, `rebuild_person_note` ×1, `ask_question` ×1,
  `view_channel_status` ×1) — each action dict currently carries only `id`,
  `label`, `trigger_phrases`.
- `agent_registry.py` exposes `get_agent(agent_id)`/`list_agents()` only —
  no per-action lookup helper exists yet.

**After / Outputs:**
- Every action dict in `AGENTS` gains a `"mutates": bool` key, classified
  per `ADR-020` point 1's own table (below).
- New `get_action(agent_id: str, action_id: str) -> dict | None` — returns
  the action's own dict (including its new `mutates` key) if found on that
  agent, else `None`.
- `AGENTS`, `get_agent`, `list_agents` are otherwise byte-for-byte
  unchanged — this task is purely additive.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — add a `"mutates"` key to
  every action dict, per this exact classification (`ADR-020` point 1,
  read from `app/api/agents_router.py`'s real `_ACTION_HANDLERS` mapping
  and each agent's own PRD-sourced `settings`, not guessed from the id
  string alone):

  | `action_id` | Agents | `mutates` | Why |
  |---|---|---|---|
  | `run_capture_now` | email-capture, meeting-capture, todo-capture | `True` | Files new notes into the vault |
  | `pause_schedule` | email-capture, meeting-capture, todo-capture | `True` | A control-plane state mutation (the agent's own future scheduled behaviour), even though it has no real handler yet — classified conservatively as a write, not read-only |
  | `view_last_run` | email-capture, meeting-capture, todo-capture, people-producer | `False` | Reads and reports the last recorded run outcome, writes nothing |
  | `rebuild_person_note` | people-producer | `True` | Writes (overwrites/regenerates) a Person note in the vault |
  | `ask_question` | vault-qa | `False` | A read-only query — the agent's own declared `settings` say so explicitly ("Write access: Read-only here") |
  | `view_channel_status` | vault-qa | `False` | A read-only status check |

  Concretely, each action dict becomes (example — `email-capture`'s
  `run_capture_now`):
  ```python
  {
      "id": "run_capture_now",
      "label": "Run capture now",
      "trigger_phrases": ["run capture now", "run capture", "capture now"],
      "mutates": True,
  },
  ```
  Apply the same additive `"mutates": <bool per the table above>` key to
  every one of the 12 action entries across all 5 agents — do not reorder,
  rename, or otherwise touch `id`/`label`/`trigger_phrases` on any entry.

  Append the new helper at the end of the file, after `list_agents`:
  ```python
  def get_action(agent_id: str, action_id: str) -> dict | None:
      """Resolves one action's own definition dict (including its
      "mutates" classification) by agent_id + action_id — the one place
      app/api/agents_router.py's working-mode gate (ADR-020 point 2)
      reads an action's own read-only-vs-mutating nature, so the nested-
      list search isn't duplicated inline at every call site."""
      agent = AGENTS.get(agent_id)
      if agent is None:
          return None
      return next((a for a in agent["actions"] if a["id"] == action_id), None)
  ```

---

## Constraints

- Inherits from parent story and `ADR-020` point 1's exact classification
  table above — do not reclassify any action differently from the table,
  even if a different reading seems equally plausible; the table is the
  architect's own resolved decision, not this task's to second-guess.
- `agent_registry.py` stays a fully static, hardcoded module — `mutates` is
  a plain literal `bool` on each dict, never computed, derived from a
  naming convention, or read from any persisted/mutable state file
  (`ADR-020`'s own explicit rejection of a persisted-per-agent-action
  property, "Alternatives Considered").
- `AGENTS`'s existing `id`/`label`/`trigger_phrases`/`name`/`type`/
  `settings` values, and `get_agent`/`list_agents`'s own existing return
  shapes, must be byte-for-byte unchanged — this task only adds the new
  `mutates` key and the new `get_action` function.
- `get_action` must never raise for an unknown `agent_id`/`action_id` —
  returns `None` in both cases.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `get_action("email-capture", "run_capture_now")` — confirm the returned
   dict has `"mutates": True`. Call `get_action("email-capture",
   "view_last_run")` — confirm `"mutates": False`. Call
   `get_action("vault-qa", "ask_question")` — confirm `"mutates": False`.
   Call `get_action("people-producer", "rebuild_person_note")` — confirm
   `"mutates": True`.
2. Non-AC smoke check: call `get_action("email-capture", "pause_schedule")`
   — confirm `"mutates": True` (the one deliberately-conservative
   classification — `pause_schedule` has no real handler yet, but is still
   correctly classified as a write per this task's own table).
3. Non-AC smoke check: call `get_action("email-capture",
   "not-a-real-action")` — confirm `None`, no error raised. Call
   `get_action("not-a-real-agent", "run_capture_now")` — confirm `None`, no
   error raised.
4. Non-AC smoke check: confirm every one of the 12 action entries across
   all 5 agents (`email-capture` ×3, `meeting-capture` ×3, `todo-capture`
   ×3, `people-producer` ×2, `vault-qa` ×2) now carries a `"mutates"` key —
   iterate `AGENTS` directly and assert no action dict is missing the key.
   Confirm `list_agents()`'s own return shape (`id`/`name`/`type` only) is
   unchanged — it does not surface `actions`/`mutates` at all, matching its
   pre-this-task contract.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Every one of the 12 action entries across all 5 agents carries a
      `"mutates": bool` key, classified per this task's own table
- [ ] `get_action(agent_id, action_id)` returns the action's own dict
      (including `mutates`) when found, `None` when not — never raises
- [ ] `AGENTS`'s existing fields and `get_agent`/`list_agents`'s existing
      return shapes are byte-for-byte unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reading/using `mutates`/`get_action` from the working-mode gate — `T04`
  (`agents_router.py::_invoke_action`).
- Any persisted/mutable per-agent-action property — explicitly rejected by
  `ADR-020`'s own "Alternatives Considered"; `mutates` stays a static
  literal on the hardcoded catalog.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-020` created at the
prior `/plan-tasks` pass, superseding `ADR-018` points 3/5 — this task's
own scope, the `mutates` classification and `get_action` helper, is
`ADR-020` point 1's concrete design) — the human reviews `ADR-020` and this
task breakdown together; the pipeline does not halt, so this task proceeds
to `Ready` alongside the rest of the story.

This task carries no AC-tagged step of its own — its locked-AC consumers
(`T04`'s Supervised-mutates-gates / Supervised-read-only-proceeds
scenarios, `REQ-SB-21-US-01-AC-03`/`AC-05`) verify this module's real
classification behaviour live, against the real gate, in `T04`.

No task in this story's original (`ADR-018`-only) `T01`-`T08` breakdown ever
touched `agent_registry.py` at all — `ADR-018`'s own design gated purely by
trigger source, so no action-level classification was ever needed. This
task exists solely because `ADR-020` introduced that new axis.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** `agent_registry.py`
gained a `"mutates": bool` key on all 12 action entries across the 5
agents, per this task's own classification table, plus the new
`get_action(agent_id, action_id)` helper — exactly as specified.

No locked AC of its own — verified via the Tests block's non-AC smoke
checks, live, against the real backend `.venv`:
1. `get_action("email-capture", "run_capture_now")["mutates"]` → `True`;
   `get_action("email-capture", "view_last_run")["mutates"]` → `False`;
   `get_action("vault-qa", "ask_question")["mutates"]` → `False`;
   `get_action("people-producer", "rebuild_person_note")["mutates"]` →
   `True`. PASS.
2. `get_action("email-capture", "pause_schedule")["mutates"]` → `True`
   (the deliberately-conservative classification). PASS.
3. `get_action("email-capture", "not-a-real-action")` → `None`;
   `get_action("not-a-real-agent", "run_capture_now")` → `None`; no
   error raised either time. PASS.
4. Iterated all 12 action entries across all 5 agents directly — zero
   missing the `"mutates"` key. `list_agents()`'s own return shape
   (`id`/`name`/`type` only) confirmed unchanged. PASS.

Later, live end-to-end at `T04`'s own verification pass, this
classification was the load-bearing input to the Supervised gate's
mutates-vs-read-only branch (`AC-03`/`AC-05`), confirmed correct for
both `run_capture_now` (proposes) and `view_last_run` (proceeds).

Gate: `clear` — no MUST-FLAG trigger fired; the classification table
was applied exactly as `ADR-020` point 1 specified, no reinterpretation.
