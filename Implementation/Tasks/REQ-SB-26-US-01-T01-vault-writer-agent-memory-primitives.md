---
id: REQ-SB-26-US-01-T01
title: vault_writer.py — load_agent_memory / append_agent_memory_entries primitives + agent_memory.json state file
parent_story: REQ-SB-26-US-01
requirement_id: REQ-SB-26
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-26-US-01-T01 — `vault_writer.py` agent-memory primitives

## Parent Story

- Story: [[REQ-SB-26-US-01]] — `../UserStories/REQ-SB-26-US-01-agent-memory.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-26 *Agent Memory*

---

## Objective

Add the two new `vault_writer.py` primitives `ADR-016` names —
`load_agent_memory(agent_id)` / `append_agent_memory_entries(agent_id,
facts)` — mirroring `load_agent_history`/`append_agent_history_entry`'s
exact shape, backed by a new sibling `.second-brain/agent_memory.json`
state file.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `_agent_history_path` /
  `_load_agent_history_index` / `append_agent_history_entry` /
  `load_agent_history` (`ADR-011`) as the pattern to mirror.
- No `agent_memory.json` file or memory-related function exists yet.

**After / Outputs:**
- `vault_writer.py` gains `load_agent_memory(agent_id) -> list[dict]` and
  `append_agent_memory_entries(agent_id, facts: list[str]) -> None`.
- `.second-brain/agent_memory.json` is created on first write, shape
  `{agent_id: [{"fact": str, "recorded_at": iso8601}, ...]}` (`ADR-016`
  point 3).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add, immediately after
  the existing `_AGENT_PROVIDERS_FILE` constant declaration:
  ```python
  _AGENT_MEMORY_FILE = "agent_memory.json"
  ```
  and, appended at the end of the file:
  ```python
  def _agent_memory_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_MEMORY_FILE


  def _load_agent_memory_index() -> dict[str, list[dict]]:
      path = _agent_memory_path()
      if not path.exists():
          return {}
      return json.loads(path.read_text(encoding="utf-8"))


  def load_agent_memory(agent_id: str) -> list[dict]:
      return _load_agent_memory_index().get(agent_id, [])


  def append_agent_memory_entries(agent_id: str, facts: list[str]) -> None:
      """Appends one entry per fact string to agent_id's growing memory
      list (ADR-016 point 3) -- a no-op (no file write at all, no file
      created) when facts is empty, so a reply that extracted nothing
      worth remembering (Scenario 3's own honest "no fact" outcome) never
      touches agent_memory.json. Flat, append-only -- no dedup/merge/
      consolidation this pass (ADR-016 point 3), mirroring
      append_agent_history_entry's own "already chronological because
      callers append at the moment the event happens" contract, extended
      to a list of facts arriving from one extraction call at once instead
      of one entry at a time."""
      if not facts:
          return
      path = _agent_memory_path()
      index = _load_agent_memory_index()
      recorded_at = datetime.now(timezone.utc).isoformat()
      index.setdefault(agent_id, []).extend(
          {"fact": fact, "recorded_at": recorded_at} for fact in facts
      )
      path.write_text(json.dumps(index, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story: this is a pure `data_access`-layer mirror of
  `load_agent_history`/`append_agent_history_entry`'s exact shape
  (`ADR-016` point 2/3) — no business logic (no dedup, no consolidation,
  no relevance filtering) belongs here.
- `append_agent_memory_entries` takes a **list** of fact strings (not one
  fact at a time) — `extract_memory` (`T03`) can return zero, one, or
  several facts from a single completion; do not narrow the signature to
  accept a single string.
- No other function in `vault_writer.py` is modified.
- `api → business → data_access` layering (`ADR-003`): no HTTP concerns,
  no LangGraph/graph-state imports here.

---

## Tests

<!-- This task has no locked AC of its own — these primitives are internal
data_access building blocks with no directly observable HTTP outcome by
themselves; every locked AC is verified end-to-end in T04 once the full
chain is wired. This task's own verification is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv`, call `vault_writer.append_agent_memory_entries("smoke-test-agent",
   ["fact one", "fact two"])`, then `vault_writer.load_agent_memory("smoke-test-agent")`.
   Confirm the returned list has exactly 2 entries, each with `"fact"`
   matching the input strings (in order) and a non-empty ISO-8601
   `"recorded_at"`. Confirm `.second-brain/agent_memory.json` now exists
   on disk with the `{agent_id: [...]}` shape.
2. Non-AC smoke check: call `vault_writer.append_agent_memory_entries("smoke-test-agent-2", [])`.
   Confirm `vault_writer.load_agent_memory("smoke-test-agent-2")` returns
   `[]` and that no `"smoke-test-agent-2"` key was added to
   `agent_memory.json` — confirming the empty-list no-op.
3. Clean-up: remove the `"smoke-test-agent"`/`"smoke-test-agent-2"` test
   keys from `.second-brain/agent_memory.json` afterward (or delete the
   file if it contains nothing else yet) so no test residue is left in the
   real vault's state directory.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_agent_memory(agent_id)` returns `[]` when no entries exist yet
      for that agent, else that agent's stored fact-entry list
- [x] `append_agent_memory_entries(agent_id, facts)` appends one
      `{"fact": str, "recorded_at": iso8601}` entry per string in `facts`,
      preserving order
- [x] `append_agent_memory_entries(agent_id, [])` is a true no-op — no
      file write, no key added
- [x] `.second-brain/agent_memory.json` shape matches `ADR-016` point 3
      exactly: `{agent_id: [{"fact": str, "recorded_at": iso8601}, ...]}`
- [x] No other `vault_writer.py` function modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `state.py` / `graph.py` changes — `T02`/`T03`.
- `agents_router.py` wiring — `T04`.
- Any dedup, consolidation, relevance-ranking, or pruning of stored facts
  — explicitly out of scope this pass (`ADR-016` point 3).

---

## Context / Notes

Mirrors `load_agent_history`/`append_agent_history_entry` deliberately —
do not invent a different file shape or a different function signature
style than the existing agent-history pair already established.

---

## Implementation Log

**2026-08-12 — coder.** Added `_AGENT_MEMORY_FILE` constant and
`_agent_memory_path`/`_load_agent_memory_index`/`load_agent_memory`/
`append_agent_memory_entries` to `src/backend/app/data_access/vault_writer.py`,
verbatim per this task's own `## Files to Modify` code block — no deviation.

**Non-AC smoke checks (both pass):**
1. `append_agent_memory_entries("smoke-test-agent", ["fact one", "fact two"])`
   then `load_agent_memory("smoke-test-agent")` returned exactly 2 entries,
   `"fact"` matching the input strings in order, each with a non-empty
   ISO-8601 `"recorded_at"`. `.second-brain/agent_memory.json` confirmed
   created on disk with the `{agent_id: [...]}` shape.
2. `append_agent_memory_entries("smoke-test-agent-2", [])` — confirmed
   `load_agent_memory("smoke-test-agent-2")` returns `[]` and no
   `"smoke-test-agent-2"` key was added — empty-list no-op confirmed.
3. Clean-up: both test keys removed from `agent_memory.json` afterward
   (file was empty of other content and was deleted).

No other `vault_writer.py` function modified. `status: Ready → Done`.

`gate: clear 2026-08-12` — no MUST-FLAG trigger fired: implemented exactly
per the task's own literal code sample, no deviation, no assumption.
