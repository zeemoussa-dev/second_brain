---
id: REQ-SB-66-US-01-T04
title: agents_router.py — GET/PATCH /agents/{agent_id} gains Prompt + Guardrails fields for every real Agent
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-66-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T04 — `agents_router.py` Prompt + Guardrails surface for real Agents

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Extend the existing `GET`/`PATCH /agents/{agent_id}` verb pair with `prompt` and
`guardrails` fields, per `ADR-014`'s established shared-verb pattern (the same
endpoint `REQ-SB-18/19/20/21/29`-US-01 already extended for `section_id`/
`provider_id`/`keywords`/`working_mode`/`scope`) — composed at the router layer via
`T01`'s `agent_prompts.py`, without modifying `agent_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `agents_router.py`'s real current `AgentAssignmentUpdateBody`, `get_agent`, and
  `update_agent_assignment` (already carrying `section_id`/`provider_id`/
  `keywords`/`scope`/`working_mode`/`is_background_agent`/`icon`/`color`) — read the
  REAL current file before applying this task's diff (it has been touched by
  multiple sibling stories since; do not overwrite with a stale sample).
- `T01` has landed `agent_prompts.get_prompt(id) -> str | None` /
  `agent_prompts.set_prompt(id, prompt) -> None` / `agent_prompts.get_guardrails(id)
  -> str` / `agent_prompts.set_guardrails(id, guardrails) -> None`.

**After / Outputs:**
- `GET /agents/{agent_id}` → the existing merged shape plus `"prompt": str | None`
  and `"guardrails": str` — `prompt` is the STORED override only (`None` when
  unset), never the resolved effective default text (mirrors `ADR-044`'s own
  Alternatives Considered: the Job-Settings endpoint deliberately returns the
  stored value only, not a resolved-effective-text; this real-Agent endpoint stays
  consistent with that same choice).
- `PATCH /agents/{agent_id}` (body gains `prompt?: str`, `guardrails?: str`) —
  whole-value-replaces the agent's own Prompt/Guardrails when supplied, returns the
  same merged detail shape.
- `GET /agents` (list) is **unchanged** — `prompt`/`guardrails` are detail-only
  fields, matching `keywords`/`scope`'s own precedent.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - Extend the existing `from app.business import (...)` block to include
    `agent_prompts` (alphabetical).
  - Extend the existing `AgentAssignmentUpdateBody`:
    ```python
    class AgentAssignmentUpdateBody(BaseModel):
        section_id: str | None = None
        provider_id: str | None = None
        keywords: list[str] | None = None
        working_mode: str | None = None
        scope: list[str] | None = None
        is_background_agent: bool | None = None
        icon: str | None = None
        color: str | None = None
        prompt: str | None = None
        guardrails: str | None = None
    ```
  - In `get_agent`, add two more fields to the returned dict, alongside the
    existing `"scope"` key:
    ```python
    "prompt": agent_prompts.get_prompt(agent_id),
    "guardrails": agent_prompts.get_guardrails(agent_id),
    ```
  - In `update_agent_assignment`, add two more branches, mirroring the existing
    `keywords`/`scope` branches:
    ```python
    if body.prompt is not None:
        agent_prompts.set_prompt(agent_id, body.prompt)
    if body.guardrails is not None:
        agent_prompts.set_guardrails(agent_id, body.guardrails)
    ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering (`ADR-003`);
  `agent_registry.py` is NOT modified by this task.
- `GET /agents/{agent_id}`'s pre-existing fields must be unchanged in shape and
  value — this is an additive-fields-only change.
- `GET /agents` (list) is explicitly **untouched** — no `prompt`/`guardrails` field
  added there this pass.
- `PATCH /agents/{agent_id}` with `prompt`/`guardrails` omitted (`null`/absent) must
  be a no-op for that field — mirrors `keywords`/`scope`'s own existing
  omitted-means-unchanged convention.
- `prompt` returned by `GET` is the STORED value only (`None` when unset) — this
  task must NOT resolve/return the call site's own hardcoded default text; that
  distinction is `T02`/`T03`'s own runtime concern, not this endpoint's.
- Do not touch `trigger_action`, `chat`, `get_history`, or `get_jobs` — out of scope
  for this task.
- This task applies ONLY to real Agents (the existing `/agents/{agent_id}`
  resource) — a Job's own Settings surface is a genuinely separate endpoint,
  `T06`'s own scope, per `ADR-044`.

---

## Tests

<!-- This story's Scenario 5 (AC-05) and Scenario 6 (AC-06) are user-observable on
the Agent Settings surface — their full verification lives in T05
(AgentDetailPanel.tsx, the actual kv-rows), per the established "user-observable
outcome verifies in the frontend task" rule (REQ-SB-29-US-01-T03/T05 precedent).
The steps below are non-AC smoke checks confirming this endpoint's shape/behavior
in isolation, ahead of T05's UI wiring. -->

**Manual verification steps** (from `src/backend`, real running backend or FastAPI
`TestClient`):
1. `GET /agents/{a_real_agent_id}` — confirm the response includes `"prompt": null`
   and `"guardrails": ""` for an id with no saved override yet, alongside every
   pre-existing field unchanged.
2. `PATCH /agents/{a_real_agent_id}` with `{"prompt": "Custom instructions.",
   "guardrails": "Draft only, never auto-send."}` — confirm the response reflects
   both new values immediately; re-`GET` and confirm they persist. `PATCH` again
   with `{}` (both omitted) — confirm both values are unchanged (no-op).
3. Confirm `GET /agents` (the list endpoint) response shape is byte-for-byte
   unchanged — no `prompt`/`guardrails` key present on any list entry.
4. Confirm `agent_registry.py`'s own source file is unmodified (`git diff` shows no
   change to it) after these writes/reads.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /agents/{agent_id}` returns `prompt`/`guardrails` (stored values only,
      `None`/`""` defaults) alongside every pre-existing field, unchanged
- [x] `PATCH /agents/{agent_id}` accepts optional `prompt`/`guardrails`, whole-value
      replace, omission is a no-op
- [x] `GET /agents` (list) is byte-for-byte unchanged
- [x] `agent_registry.py` is not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Implementation Log

**Built as specced, no deviations.** Read the REAL current `agents_router.py`
fresh before editing (last touched by `REQ-SB-29-US-01`'s `scope` field) —
its import block, `AgentAssignmentUpdateBody`, `get_agent`, and
`update_agent_assignment` matched this task's own illustrative prose
one-for-one, so the diff applied exactly as described: `agent_prompts` added
to the `from app.business import (...)` block (alphabetical, between
`agent_orchestration` and `agent_registry`); `prompt`/`guardrails` added to
`AgentAssignmentUpdateBody` (after `color`); `"prompt":
agent_prompts.get_prompt(agent_id)` / `"guardrails":
agent_prompts.get_guardrails(agent_id)` added to `get_agent`'s returned dict
(after `"color"`); two `if body.prompt is not None` / `if body.guardrails is
not None` branches added to `update_agent_assignment` (after the
`icon`/`color` branch, mirroring `keywords`/`scope`'s own
omitted-means-unchanged convention). `list_agents`/`GET /agents` was not
touched at all, per the task's own explicit scope bound.

This task carries no AC tags of its own — per the parent story's Decomposer
Notes ("`T04`/`T06`... therefore carry no AC tags of their own, by the same
established rule"), Scenario 5/6 (`AC-05`/`AC-06`) verify fully in `T05`
(`AgentDetailPanel.tsx`'s actual kv-rows), against the real running app.
The four numbered steps below are this task's own **non-AC smoke checks**,
run directly against the real backend venv (`src/backend/.venv`) via
FastAPI's `TestClient`, real `agent_registry`/`vault_writer` wiring, real
configured vault (`VAULT_PATH=C:\myWorx\Moussa MD\Moussa Brain`) — not a
persisted pytest file (repo has no test suite for this layer yet, matching
`T01`'s own "Automated tests: n/a — test tooling pending" precedent).

1. **PASS.** `GET /agents/email-capture-pipeline` (no prior override for
   this id) returned `"prompt": null` and `"guardrails": ""` in the response
   body, alongside every pre-existing field (`capabilities`, `color`,
   `icon`, `id`, `is_background_agent`, `keywords`, `name`, `provider_id`,
   `provider_name`, `provider_available`, `scope`, `section_id`,
   `section_name`, `settings`, `type`, `working_mode`) present and
   unchanged in shape.
2. **PASS.** `PATCH /agents/email-capture-pipeline` with `{"prompt":
   "Custom instructions.", "guardrails": "Draft only, never auto-send."}`
   returned both new values immediately in the response. A subsequent `GET`
   confirmed both persisted. A follow-up `PATCH` with `{}` (both fields
   omitted) left both values unchanged — confirmed no-op.
3. **PASS.** `GET /agents` (list) response keys before and after the
   PATCH above are identical
   (`branch_target_agent_id`/`color`/`depends_on`/`icon`/`id`/
   `is_background_agent`/`name`/`provider_id`/`section_id`/`type`/
   `working_mode`) — no `prompt`/`guardrails` key present on any list
   entry, byte-for-byte unchanged shape.
4. **PASS.** `git status`/`git diff --stat` for
   `src/backend/app/business/agent_registry.py` shows no NEW change
   attributable to this task — this task's own `Edit` calls only ever
   targeted `agents_router.py`. Note: `agent_registry.py` already carried
   an unrelated, pre-existing uncommitted diff at session start (visible in
   this session's opening `git status`, predating this task) — this task
   did not add to it.

**Assumption logged for human spot-check (scope-internal judgement call, not
an escalation):** step 2's smoke-check PATCH left a real, non-default
Prompt/Guardrails override stored against the `email-capture-pipeline` id in
the real vault's `.second-brain/agent_prompts.json` (`"Custom
instructions."` / `"Draft only, never auto-send."`). Left in place rather
than reverted, mirroring `T01`'s own established precedent (its own
Implementation Log: verification run directly against the real configured
vault, "no scratch-vault isolation was needed"). Harmless for this story's
own real scope — `email-capture-pipeline` is the pipeline's root agent id,
not one of the four owning identities `T02`/`T03` wire a real call site to.

- MEMORY.md — no new decision/pattern/constraint; this task is a mechanical,
  same-shape repetition of the already-established `keywords`/`scope`
  additive-field router pattern (`ADR-011` point 2/`ADR-030`), already
  recorded once for `T01`.
- CHANGELOG.md — entry appended.

## Out of Scope

- The actual `AgentDetailPanel.tsx` Settings-tab rows that consume this endpoint —
  `T05`.
- Any Job-Settings endpoint — `T06`.
- Resolving the stored value into the call site's own effective default text — not
  this endpoint's concern (`T02`/`T03`'s own runtime scope).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see
ADR-044)" → "Settings-tab extension for real Agents" bullet ("the only piece of this
story that touches `AgentDetailPanel.tsx` itself" refers to `T05`; this task is the
backend half that piece depends on).

Compose around the REAL current `agents_router.py` as it actually exists today — it
has been touched by many sibling stories; do not assume the exact field order/import
list from this task's own illustrative prose without reading the real file first
(this codebase's own established "compose around the real current file" precedent,
`Learnings.md`).
