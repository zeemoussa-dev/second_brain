---
id: REQ-SB-28-US-01-T03
title: New summarize-file Skill — skill_tools.py catalog entry + real handler, skill_registry.py dispatch row
parent_story: REQ-SB-28-US-01
requirement_id: REQ-SB-28
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-28-US-01-T02, REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-28-US-01-T03 — New `summarize-file` Skill

## Parent Story

- Story: [[REQ-SB-28-US-01]] — `../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-28 *File Upload for Agents*

---

## Objective

Register `summarize-file` as a new Skill through the already-`Accepted`
`ADR-015` extensibility path (`ADR-034` point 4) — this project's **first
real (non-stub) Skill**. One new `skill_tools.SKILLS` catalog entry, one
new `@mcp_server.tool()`-decorated handler that calls `T02`'s
`compass_client.summarize_content` and returns an honest result on
failure, and one new `skill_registry._SKILL_HANDLERS` dispatch row.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `compass_client.summarize_content(content,
  source_description) -> dict`.
- `REQ-SB-39-US-01-T01` has landed the `"mutates": bool` field on every
  `skill_tools.SKILLS` entry; `REQ-SB-39-US-01-T02` has landed
  `invoke_skill`'s new required, no-default `trigger: Literal["chat",
  "direct", "hub_routed"]` parameter — **this task's own new catalog
  entry and every `invoke_skill(...)` call this task's own tests make
  must use the post-`REQ-SB-39-US-01` shape**, not the pre-migration one
  the rest of this task's prose otherwise reads like. Read `T01`'s/`T02`'s
  real, as-built `skill_tools.py`/`skill_registry.py` before writing this
  task's own entry — reconcile field/signature names against what those
  tasks actually built.
- `skill_tools.py` has `SKILLS` (`diagram-understanding`, `web-research`,
  plus the 3 migrated read-only ids from `REQ-SB-39-US-01`) and their
  `@mcp_server.tool()`-decorated handler functions.
- `skill_registry.py` has `_SKILL_HANDLERS` (grown to 5 entries by
  `REQ-SB-39-US-01-T02`) and `invoke_skill`, which already threads an
  `args` dict into the resolved handler's keyword arguments
  (`REQ-SB-36-US-01-T05`'s own additive `args` support — unmodified by
  this task).

**After / Outputs:**
- `skill_tools.SKILLS` gains one additive entry:
  ```python
  "summarize-file": {
      "id": "summarize-file",
      "name": "Summarize File",
      "description": (
          "Given a text-bearing uploaded file's extracted content, "
          "produce a Compass-generated summary of its actual content."
      ),
      "mutates": False,
  },
  ```
- `skill_tools.py` gains one additive handler (placed alongside the
  existing two, after `web_research`):
  ```python
  @mcp_server.tool()
  def summarize_file(content: str, source_description: str) -> dict:
      """Summarizes already-extracted text content via Compass
      (compass_client.summarize_content), for a file the user attached to
      an agent chat message. Never raises for ordinary control flow --
      catches CompassError and returns an honest {"status": "error", ...}
      result instead, mirroring invoke_skill's own "never raises" design
      intent (REQ-SB-27-US-01) so the router (T04) can branch on a result
      shape rather than a try/except around invoke_skill itself."""
      try:
          result = compass_client.summarize_content(content, source_description)
          return {"status": "ok", "summary": result["summary"]}
      except compass_client.CompassError as exc:
          return {"status": "error", "message": f"Summarization failed: {exc}"}
  ```
  (Requires a new `from app.data_access import compass_client` import,
  additive alongside `skill_tools.py`'s existing imports.)
- `skill_registry._SKILL_HANDLERS` gains one additive row:
  `"summarize-file": skill_tools.summarize_file,`.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — add the `SKILLS` entry, the
  `summarize_file` handler, and the `compass_client` import, all additive.
  Do not modify `diagram_understanding`, `web_research`, or their own
  `SKILLS` entries.
- `src/backend/app/business/skill_registry.py` — add the
  `"summarize-file"` row to `_SKILL_HANDLERS` only. Do not modify
  `invoke_skill`, `grant_skill_access`, `revoke_skill_access`,
  `has_skill_access`, `list_skills`, or `list_agent_skills`.

---

## Constraints

- Inherits from parent story: never fabricate — `summarize_file` never
  invents a summary; on `CompassError` it returns an honest
  `{"status": "error", ...}` result, never a placeholder `"summary"`.
- Additive only — every existing `SKILLS` entry, existing
  `@mcp_server.tool()` handler, and `_SKILL_HANDLERS` row stays byte-for-
  byte unchanged.
- `summarize_file`'s own two parameters (`content`, `source_description`)
  must match the keys `T04` passes in `invoke_skill(agent_id,
  "summarize-file", {"content": ..., "source_description": ...})`'s
  `args` dict — `invoke_skill`'s existing dispatch threads `args` into the
  handler via `**call_args` (confirmed in `skill_registry.py`); no
  handler-shape change needed there.
- Does not modify `app/data_access/compass_client.py` (read `T02`'s real
  output first — reconcile the return-shape key names, `content` object
  used above assumes `T02`'s own code block was implemented verbatim).

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`; delete any
leftover `.second-brain/agent_skills.json` first):

1. Non-AC smoke check: `skill_registry.list_skills()` includes an entry
   with `id == "summarize-file"`, `name`/`description` populated.
2. **[REQ-SB-28-US-01-AC-02]** `skill_registry.grant_skill_access("email-capture", "summarize-file")`
   → `True`. `skill_registry.invoke_skill("email-capture", "summarize-file",
   {"content": "<real multi-paragraph text>", "source_description": "test fixture"},
   trigger="direct")`
   → `{"status": "ok", "summary": <string>}`; confirm the summary text
   genuinely reflects the real input content (read it by eye), not a
   fabricated/generic placeholder.
3. **[REQ-SB-28-US-01-AC-09]** Induce a real Compass failure (in-process
   monkeypatch of `compass_client.summarize_content` to raise
   `CompassError`, or reuse `T02`'s own induction technique) and call
   `invoke_skill("email-capture", "summarize-file", {"content": "x",
   "source_description": "test"}, trigger="direct")` again — confirm
   `{"status": "error", "message": <string>}`, never a `"summary"` key
   present.
4. Non-AC smoke check: `skill_registry.invoke_skill("meeting-capture",
   "summarize-file", {"content": "x", "source_description": "test"},
   trigger="direct")`
   (never granted) → the existing `{"status": "refused", ...}` shape,
   confirming the new Skill participates in the existing access-gate
   unmodified.
5. Clean-up: delete `.second-brain/agent_skills.json`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `skill_tools.SKILLS` includes a `summarize-file` entry
- [ ] `skill_tools.summarize_file(content, source_description)` returns a
      real Compass summary on success, an honest `{"status": "error", ...}`
      on `CompassError` — never a fabricated summary
- [ ] `skill_registry._SKILL_HANDLERS` dispatches `"summarize-file"` to it
- [ ] Existing `diagram-understanding`/`web-research` entries, handlers,
      and dispatch rows unchanged
- [ ] `invoke_skill`'s existing access-gate (refused vs. dispatched)
      applies to `summarize-file` unmodified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The HTTP endpoint that calls `invoke_skill(..., "summarize-file", ...)`
  and grants access to the requesting agent — `T04`.
- Text extraction from the raw uploaded file — `T01`.
- Any frontend surface — `T05`.

---

## Context / Notes

**Grant-on-first-use is `T04`'s own responsibility, not this task's** —
this task only wires the catalog entry, handler, and dispatch row; it
does not call `grant_skill_access` itself. See the parent story's
Decomposer-pass Notes for why `T04` auto-grants `summarize-file`
(deliberate divergence from `skill_registry.py`'s own "explicit-grant-
only" default, specific to this one mandatory-default-capability Skill).

Read `T02`'s actual, real `compass_client.py` output before writing this
task's `summarize_file` handler — reconcile the `result["summary"]` key
access above against whatever `T02` really returned, do not assume the
code sample above is unchanged from what was actually built (this
project's own standing "compose around the REAL current file" pattern,
`Implementation/Learnings.md`).

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, reconciled
against T02's real, as-built `compass_client.summarize_content` return
shape (`{"summary": str}`, confirmed matching the sample verbatim — no
key-name reconciliation needed).** `skill_tools.py` gained the
`"summarize-file"` `SKILLS` entry (placed after `"write-to-vault-draft"`,
the end of the dict — additive), the `summarize_file` handler (placed
immediately after `web_research`, before `run_capture_now`, per the
task's own placement instruction), and the additive `compass_client`
import (folded into the existing `from app.data_access import
anthropic_client` line as `from app.data_access import anthropic_client,
compass_client`). `skill_registry.py` gained one additive
`"summarize-file": skill_tools.summarize_file` row in `_SKILL_HANDLERS`.
`diagram_understanding`/`web_research` and their own `SKILLS` entries are
byte-for-byte unchanged; `invoke_skill`/`grant_skill_access`/
`revoke_skill_access`/`has_skill_access`/`list_skills`/
`list_agent_skills` unmodified.

**Verification (Python shell, backend `.venv`; the real production
`.second-brain/agent_skills.json` was backed up before this task's own
Tests step 1's "delete any leftover..." instruction, then restored
byte-identical afterward — confirmed by diff — since this file holds
real, live migration-seed grants from `SPRINT-031`, not throwaway smoke
debris):**

- Non-AC smoke check: `skill_registry.list_skills()` includes
  `{"id": "summarize-file", "name": "Summarize File", "description":
  ..., "mutates": False}`. Confirmed.
- **AC-02** (step 2): `grant_skill_access("email-capture",
  "summarize-file")` → `True`. `invoke_skill("email-capture",
  "summarize-file", {"content": <real Atlas-Migration text>,
  "source_description": "test fixture"}, trigger="direct")` →
  `{"status": "ok", "summary": "Atlas Migration project: move the
  legacy billing service from on-premise SQL Server to a managed cloud
  Postgres instance. Key stakeholders: Priya Raman (Engineering Lead)
  and Devon Clarke (Finance Ops). Target cutover date: October 3."}` —
  read by eye against the real input content: genuinely reflects it,
  not fabricated/generic. **Pass.**
- **AC-09** (step 3): in-process monkeypatch of
  `skill_tools.compass_client.summarize_content` to raise
  `CompassError`, reverted immediately after the one call — confirmed
  `invoke_skill(...)` → `{"status": "error", "message": "Summarization
  failed: simulated failure"}`, no `"summary"` key present. **Pass.**
- Non-AC smoke check (step 4): `invoke_skill("meeting-capture",
  "summarize-file", ..., trigger="direct")` (never granted) →
  `{"status": "refused", "reason": "Agent does not have access to this
  skill."}` — the existing access-gate applies unmodified.
- Clean-up (step 5): the real `agent_skills.json` was restored from its
  pre-test backup, confirmed byte-identical to the original (no residual
  test-only grant).

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (every existing
Skill/handler/dispatch row confirmed unchanged; no new dependency beyond
`T02`'s own already-verified `compass_client.summarize_content`; both
locked ACs verified live).
