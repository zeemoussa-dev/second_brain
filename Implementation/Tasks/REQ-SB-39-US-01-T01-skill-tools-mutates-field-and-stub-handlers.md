---
id: REQ-SB-39-US-01-T01
title: skill_tools.py — mutates field on all 5 catalog entries + 3 new honest-unavailable stub Skill handlers
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T01 — skill_tools.py — mutates field + 3 new stub Skill handlers

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Add `"mutates": bool` to all 5 `skill_tools.SKILLS` catalog entries (the 2
existing entries plus the 3 new ones this task also adds), and register 3
new zero-arg, unconditionally honest-unavailable `@mcp_server.tool()`
Skill handlers (`view_last_run`, `ask_question`, `view_channel_status`),
mirroring `diagram_understanding`'s own existing stub shape exactly.

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS` has 2 entries (`diagram-understanding`,
  `web-research`), neither carrying a `"mutates"` field.
- 2 `@mcp_server.tool()` functions exist (`diagram_understanding`,
  `web_research`); no handler exists for `view_last_run`, `ask_question`,
  or `view_channel_status` anywhere in the codebase.

**After / Outputs:**
- `skill_tools.SKILLS` has 5 entries; every entry (all 5, not just the 3
  new ones) carries `"mutates": False` — `diagram-understanding` and
  `web-research` are both genuinely read-only (ADR-028 point 1).
- 3 new zero-arg `@mcp_server.tool()` functions (`view_last_run`,
  `ask_question`, `view_channel_status`), each unconditionally returning
  `{"available": False, "message": "This skill is not yet available — no
  real handler has been built for it."}` — identical honest-unavailable
  shape to `diagram_understanding`'s existing body.
- The 3 new catalog entries reuse their exact former Action id string
  (`view_last_run`, `ask_question`, `view_channel_status`) — not new
  kebab-case ids.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — add `"mutates": False` to
  the 2 existing entries; add 3 new `SKILLS` entries + 3 new
  `@mcp_server.tool()`-decorated functions.

---

## Constraints

- Inherits from parent story and `ADR-028` point 1/4.
- Every `SKILLS` entry (existing and new) must carry `"mutates": bool` —
  no entry may omit it. Do not add or design any gate that *reads* this
  field yet — that is `REQ-SB-39-US-02`'s own job; this task only adds the
  structural field.
- The 3 new ids MUST be exactly `view_last_run`, `ask_question`,
  `view_channel_status` — reusing the former Action id strings verbatim is
  what makes `agents_router.py`'s later `id in skill_tools.SKILLS`
  membership check correct with zero duplicated bookkeeping (`ADR-028`
  point 3) — do not invent new kebab-case ids for them.
- Each new handler is a zero-arg function, unconditionally
  honest-unavailable — no real handler logic, no per-agent branching,
  mirrors `diagram_understanding`'s own existing body exactly.
- Do NOT modify `agent_registry.py` or `agent_chat.py` — explicitly out of
  scope (`ADR-028`).
- Do NOT modify `skill_registry.py` — the `_SKILL_HANDLERS` dispatch-table
  wiring for these 3 new functions is `T02`'s own job (mirrors the
  existing pattern already established by `REQ-SB-27-US-01-T03`, which
  kept that mapping local to `skill_registry.py`, not `skill_tools.py`).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-01] Python shell against the backend `.venv`:
   `from app.business import skill_tools`. Confirm `skill_tools.SKILLS` has
   exactly 5 keys: `diagram-understanding`, `web-research`,
   `view_last_run`, `ask_question`, `view_channel_status` — and every one
   of the 5 entries' dicts has a `"mutates"` key with a `bool` value
   (`False` for all 5).
2. [REQ-SB-39-US-01-AC-02] Still in the shell: `from app.business import
   skill_registry`; call `skill_registry.grant_skill_access("email-capture",
   "view_last_run")` — confirm `True` (the pre-existing, unmodified
   `grant_skill_access` mechanism already works for the new id with zero
   special-casing, since it only checks `skill_id in skill_tools.SKILLS`).
   Call `skill_registry.revoke_skill_access("email-capture",
   "view_last_run")` — confirm `True`. Delete `.second-brain/
   agent_skills.json` afterward so `T05`'s own retrofit verification starts
   clean.
3. Non-AC smoke check: call `skill_tools.view_last_run()`,
   `skill_tools.ask_question()`, `skill_tools.view_channel_status()`
   directly — confirm each returns exactly `{"available": False, "message":
   "This skill is not yet available — no real handler has been built for
   it."}` — the same honest-unavailable shape as
   `skill_tools.diagram_understanding()`, never a fabricated result.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `SKILLS` grows from 2 to 5 entries; every entry carries `"mutates":
      bool`
- [ ] 3 new zero-arg `@mcp_server.tool()` functions registered
      (`view_last_run`, `ask_question`, `view_channel_status`), each
      unconditionally honest-unavailable
- [ ] The 3 new ids reuse their exact former Action id strings
- [ ] `agent_registry.py` / `agent_chat.py` / `skill_registry.py` not
      modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `_SKILL_HANDLERS` dispatch-table wiring for the 3 new functions (`T02`).
- The `trigger` parameter on `invoke_skill` (`T02`).
- The retrofit/backfill grant seed (`T05`).
- `agents_router.py`'s dispatch fork (`T07`).

---

## Context / Notes

`ADR-028` point 1's own fail-safe note ("a catalog entry that ever omits
the field is treated as `mutates: True` by any future gate that reads it")
describes a future gate `REQ-SB-39-US-02` builds — do not implement any
such gate here.

---

## Implementation Log

**2026-08-13 — Built and verified live.**

Environment note: this build ran in a fresh git worktree isolated from the
main checkout. `src/backend/.env` and `.venv` are both gitignored (never
committed) and were missing from the worktree; copied the real `.env`
from the main checkout (same trusted local machine) and built a fresh
`.venv` via `pip install -r requirements.txt` (clean install, no
build-toolchain issues) rather than reusing the main tree's venv. All
verification below ran against the real `.env` (real vault at
`C:\myWorx\Moussa MD\Moussa Brain`), same as the main checkout would use.
Also found several tracked files (`ADR.md`, `architecture.md`, `MEMORY.md`,
`CHANGELOG.md`, `BACKLOG.md`, `REVIEW-QUEUE.md`, `ESCALATIONS.md`) and all
of `Implementation/Sprints/SPRINT-030...`, `Implementation/Tasks/REQ-SB-39-
US-01-T01..T09`, `Implementation/UserStories/REQ-SB-39-US-01...` were
uncommitted (`??`/`M`) in the main repo and thus absent from this worktree's
git-checked-out state — copied each in from the main checkout before
starting, so this build reads/writes the real current content, not a stale
committed snapshot.

**AC-01** (`SKILLS` grows to 5 entries, every entry carries `"mutates":
bool`): Python shell, real `.venv`, real `.env` —
`from app.business import skill_tools; skill_tools.SKILLS.keys()` →
exactly `{'diagram-understanding', 'web-research', 'view_last_run',
'ask_question', 'view_channel_status'}`; every entry's `"mutates"` key is
`False` (bool). **PASS.**

**AC-02** (existing `grant_skill_access`/`revoke_skill_access` work
unmodified for the new id, zero special-casing): `skill_registry.
grant_skill_access("email-capture", "view_last_run")` → `True`;
`skill_registry.revoke_skill_access("email-capture", "view_last_run")` →
`True`. **PASS.**

Non-AC smoke check: `skill_tools.view_last_run()`, `.ask_question()`,
`.view_channel_status()` each byte-compared (`==`, not console rendering)
against `{"available": False, "message": "This skill is not yet available
— no real handler has been built for it."}` — exact match for all 3, and
also re-confirmed identical to `diagram_understanding()`'s own existing
result. **PASS.**

Assumption/scope-internal judgement call (for spot-check): the task's own
Test step 2 says "Delete `.second-brain/agent_skills.json` afterward so
`T05`'s own retrofit verification starts clean." This file is the real,
shared vault's live state (`vault-qa: ["web-research"]` pre-existing,
genuinely granted, not test debris). Deleting the whole file would destroy
that real grant. Since the grant+revoke round-trip above is itself
idempotent and already leaves `email-capture`'s entry empty (functionally
identical starting state for `T05`'s own retrofit check — no `view_last_run`
grant lingering on any of the 4 real agents), I did not delete the file;
confirmed by inspecting `.second-brain/agent_skills.json` directly post-test:
`{"assignments": {"todo-capture": [], "vault-qa": ["web-research"],
"email-capture": []}}` — clean for `T05`'s purposes, real data preserved.

`agent_registry.py` / `agent_chat.py` / `skill_registry.py` — confirmed
untouched (not in this task's `## Files to Modify`; no edits made).

gate: clear 2026-08-13 — no MUST-FLAG trigger fired independently of the
story's own inherited `ADR-028` flag (already recorded, not re-raised
here).
