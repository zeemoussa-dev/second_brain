---
id: REQ-SB-48-US-01-T01
title: Add "tool" field to the Skills catalog and pass it through capabilities
parent_story: REQ-SB-48-US-01
requirement_id: REQ-SB-48
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — AC-09 verification technique deviation, see Implementation Log"
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-48-US-01-T01 — Add "tool" field to the Skills catalog and pass it through capabilities

## Parent Story

- Story: [[REQ-SB-48-US-01]] — `../UserStories/REQ-SB-48-US-01-skills-grouped-by-tool-collapsible-tree.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-48 *Skills Grouped by Tool — Collapsible Multi-Select Tree with Icons*

---

## Objective

Give every entry in `skill_tools.SKILLS` a `"tool"` field carrying this
story's resolved taxonomy value (`"Outlook" | "Vault" | "Web" | "Compass"`),
and make sure `skill_registry.list_agent_capabilities`'s skill-kind branch
passes that field through — the single source of truth the frontend tree
(T02) groups by.

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS` — 11 entries, no `"tool"` key on any of them
  (confirmed by direct read: `diagram-understanding`, `web-research`,
  `view_last_run`, `ask_question`, `view_channel_status`, `run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`,
  `write-to-vault-draft`, `summarize-file`).
- `skill_registry.list_agent_capabilities`'s skill-kind branch (the
  `granted_skills` list comprehension) reshapes each granted Skill into
  `{"id", "label", "kind": "skill"}` only — no `"tool"` key.
- `skill_registry.list_skills()` already returns `list(skill_tools.SKILLS.values())`
  verbatim — it needs no code change; it will automatically carry the new
  `"tool"` field the moment `SKILLS` entries gain it.

**After / Outputs:**
- Every one of the 11 `SKILLS` entries carries a `"tool"` key, per this
  story's resolved taxonomy (see Constraints) — no handler-body changes.
- `list_agent_capabilities`'s skill-kind branch includes `"tool":
  skill["tool"]` in each returned dict.
- `list_agent_capabilities`'s action-kind branch is untouched — Built-in
  Action dicts still carry no `"tool"` key (this story's Constraints; T02's
  AC-09 depends on this staying true).
- `GET /skills` (`skills_router.py`, unmodified — already calls
  `list_skills()`) now returns the `"tool"` field for free.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — add a `"tool"` key to each of
  the 11 dict literals inside `SKILLS`. No changes to any `@mcp_server.tool()`
  handler function body, docstring intent, or the module-level import list.
- `src/backend/app/business/skill_registry.py` — `list_agent_capabilities`'s
  `granted_skills` list comprehension gains `"tool": skill["tool"]` in its
  returned dict shape. No other function in this file changes.

---

## Constraints

- Inherits from parent story: no new backend behavior, no endpoint changes,
  no ADR triggered (additive field on an already-`Accepted` catalog shape,
  per the architect's Notes).
- **Exact taxonomy to assign (fixed by the parent story, do not re-derive):**
  - `"tool": "Outlook"` — `view_last_run`, `run_capture_now`, `pause_schedule`
  - `"tool": "Vault"` — `ask_question`, `view_channel_status`,
    `rebuild_person_note`, `write-to-vault-draft`
  - `"tool": "Web"` — `web-research`
  - `"tool": "Compass"` — `build_knowledge`, `diagram-understanding`,
    `summarize-file`
- Every one of the 11 real entries gets exactly one of these 4 values — no
  entry left without a `"tool"` key, no 5th value introduced.
- `list_agent_capabilities`'s action-kind (`still_real_actions`) branch must
  NOT gain a `"tool"` key — Built-in capabilities are explicitly out of this
  story's Tool tree (Scenario 9 / AC-09).
- Read the real current file before editing — do not apply a stale diff;
  `skill_tools.py`/`skill_registry.py` are both actively-extended shared
  files in this project's own history (see `Implementation/Learnings.md`).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-48-US-01-AC-01] In a Python shell (`cd src/backend`, import
   `app.business.skill_registry as skill_registry`), call
   `skill_registry.list_skills()`. Assert the returned list has exactly 11
   entries and every entry's `"tool"` value matches the taxonomy above
   exactly (Outlook: 3 ids, Vault: 4 ids, Web: 1 id, Compass: 3 ids — no
   entry missing a `"tool"` key, no entry carrying an unlisted value, no
   entry double-counted across two tool values).
2. [REQ-SB-48-US-01-AC-09] Call `skill_registry.list_agent_capabilities(<a
   real agent_id that has at least one still-real Action>)`. Assert every
   `kind: "action"` dict in the result has no `"tool"` key, while every
   `kind: "skill"` dict has a `"tool"` key equal to
   `skill_tools.SKILLS[<that skill's id>]["tool"]`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 11 `SKILLS` entries carry a correct `"tool"` field per the fixed taxonomy
- [x] `list_agent_capabilities`'s skill-kind branch passes `"tool"` through unchanged
- [x] `list_agent_capabilities`'s action-kind branch carries no `"tool"` key
- [x] `list_skills()` / `GET /skills` carry the new field with zero code change to either
- [x] No `@mcp_server.tool()` handler body or existing docstring intent changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to a Skill handler's real behavior (grant/revoke logic,
  dispatch, working-mode gate) — this task only adds a static taxonomy field.
- A new endpoint, or any change to `skills_router.py`'s own route wiring.
- Frontend consumption of the new field — that's `REQ-SB-48-US-01-T02`.

---

## Context / Notes

- This task is a pure precondition for T02's frontend tree — the tree groups
  by exactly this field's value, so a wrong or missing `"tool"` on any of the
  11 entries would silently misgroup or drop a Skill row in T02's UI. Verify
  the taxonomy exactly before marking this task Done.
- `list_skills()` needs no code change — its existing
  `list(skill_tools.SKILLS.values())` passthrough already carries whatever
  keys the dict literals carry, confirmed by direct read of the real file.

---

## Implementation Log

Read the real current `skill_tools.py` (11-entry `SKILLS` dict, no `"tool"`
key on any entry — confirmed) and `skill_registry.py` (`list_agent_capabilities`'s
existing action/skill split — confirmed) before editing; no stale diff
applied. Added a `"tool"` key to all 11 `SKILLS` dict literals, exactly per
the fixed taxonomy in Constraints (Outlook: 3, Vault: 4, Web: 1, Compass: 3
— no handler-body/docstring changes). Added `"tool": skill["tool"]` to
`list_agent_capabilities`'s `granted_skills` list comprehension only; the
`still_real_actions` comprehension is untouched.

**[REQ-SB-48-US-01-AC-01] PASS.** Python-shell call to
`skill_registry.list_skills()`: 11 entries returned, grouped exactly
Outlook=3 (`pause_schedule`, `run_capture_now`, `view_last_run`),
Vault=4 (`ask_question`, `rebuild_person_note`, `view_channel_status`,
`write-to-vault-draft`), Web=1 (`web-research`), Compass=3 (`build_knowledge`,
`diagram-understanding`, `summarize-file`) — byte-identical to the taxonomy
dict compared programmatically (`actual == expected` → `True`). No entry
missing a `"tool"` key, none double-counted, none carrying an unlisted value.

**[REQ-SB-48-US-01-AC-09] PASS, via a disclosed verification-technique
deviation.** Live-checked every one of the 7 real, current agents
(`agent_registry.list_agents()` → `list_agent_capabilities` per id) and
found **zero** currently have any still-real action-kind capability at all:
`SPRINT-031`'s `REQ-SB-39-US-02` (already `Done`, prior to this task)
migrated every one of the 7 real agents' formerly-hardcoded mutating Action
ids (`run_capture_now`, `view_last_run`, `pause_schedule`,
`rebuild_person_note`, `ask_question`, `view_channel_status`,
`build_knowledge`) into `skill_tools.SKILLS` itself — so
`list_agent_capabilities`'s own `still_real_actions` filter (excludes any
action id already in `SKILLS`) now empties to `[]` for every real agent,
confirmed directly by reading each seed agent's real `actions` list. This
task's own Tests block names "a real agent_id that has at least one
still-real Action" as the precondition — that precondition is no longer
satisfiable against the current, real codebase state (an honest,
disclosed environmental finding, not a defect in this task's own change).
Verified instead via a scoped, in-process, fully-reverted monkeypatch of
the real `agent_registry.get_agent` (this project's own established
Learnings pattern, `SPRINT-018`): patched `get_agent` to return a real
agent's real dict plus one fabricated `action`-kind entry, called the real,
unmodified `list_agent_capabilities('vault-qa')`, and confirmed (a) the
action-kind result dict carries no `"tool"` key at all, and (b) every
skill-kind dict in the same result carries a `"tool"` value equal to
`skill_tools.SKILLS[<id>]["tool"]` — both true. Reverted `get_agent`
immediately after and independently reconfirmed `agent_registry.get_agent
is real_get_agent` afterward. Flagging `gate: flagged` for this technique
substitution per the coder's own scope-internal-judgement-call convention
(the task's own named precondition agent no longer exists), not because
the AC itself failed.

gate: clear-except-one-technique-substitution 2026-08-14 — flagged above
for human spot-check per the disclosed AC-09 verification deviation; no
ESCALATIONS.md entry warranted (no out-of-scope file touched, no new
dependency, no ADR deviation — a verification-technique substitution
against an honestly-changed precondition, fully disclosed).
