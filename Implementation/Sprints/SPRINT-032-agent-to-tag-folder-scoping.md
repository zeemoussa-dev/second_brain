---
id: SPRINT-032
title: Agent-to-tag/folder vault scoping
status: Done
gate: flagged
gate_reason: "Sprint retro drafted by the coder — human to skim and propagate patterns/learnings into Implementation/Learnings.md, per Pipeline.md's sprint-retro gate."
phase: P1
depends_on_sprints: []
sizing_estimate: "~5 tasks, S"
created: 2026-08-13
started: 2026-08-14
completed: 2026-08-14
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-032 — Agent-to-tag/folder vault scoping

## Sprint Goal

Let an agent be assigned a tag/folder vault scope on the Agent Settings
surface, and expose scope-bounded retrieval via a scope-aware MCP tool.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-29-US-01` is the only story
  here. Its 5 tasks form one straight internal chain (`T01 → T02 → {T03,
  T04} → T05`); verified directly against every task file's real frontmatter
  that none carries a cross-story `depends_on` edge — this story is a true
  independent root, not just "assumed independent."
- **Why NOT bundled with any other independent story in this batch
  (`REQ-SB-39-US-01`, `REQ-SB-40-US-01`, `REQ-SB-38-US-01`):** no shared
  file surface and no dependency edge to any of them; combining unrelated
  stories purely for task-count padding is not a grouping this project's own
  sprint history uses (`SPRINT-029`'s own precedent). Kept standalone so it
  can build in parallel with `SPRINT-030`/`033`/`035`/`037`, while feeding
  two real downstream consumers (`REQ-SB-37-US-02`, `REQ-SB-41-US-01`) via
  `depends_on_sprints` edges recorded on *their* sprints.
- **Sizing estimate:** ~5 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-29-US-01](../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md) | Agent-to-tag/folder vault scoping — assignment on the Agent Settings surface, and scope-bounded retrieval on request | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (vault_writer.py scope
primitives, `depends_on: []`) → `T02` (scope_registry.py business module,
`depends_on: [T01]`) → `T03` (agents_router.py scope field, `depends_on:
[T02]`), `T04` (scope-aware MCP tool, `depends_on: [T01, T02]`) → `T05`
(AgentDetailPanel.tsx Vault scope row, `depends_on: [T03]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.

---

## Out of Scope

- Every downstream story that consumes this scope field
  (`REQ-SB-37-US-02`'s Worker-flow Vault Scope picker, `REQ-SB-41-US-01`'s
  Overview tab) — scheduled in their own sprints, ordered after this one.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — `n/a`, the architect's own pre-existing "Agent-to-Tag/Folder Vault Scoping" section already covered this sprint's shape; no new architectural fact emerged during the build
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `n/a`, no new ADR (confirmed at `/plan-tasks`, held true through the build)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  No task was split, dropped, or merged. `T04` (the scope-aware MCP tool)
  and `T05` (the frontend row) were correctly the two heaviest by
  verification effort — not code volume, both built in under 40 lines —
  but by the real live-verification techniques each demanded (a headless-
  browser/CDP round trip for `T05`; a live chat round-trip plus an honest
  real-vault-vs-schema finding for `T04`).

### What worked

- **Composing every touched shared file around its REAL current state,
  every time** (`agents_router.py`, `AgentDetailPanel.tsx`/
  `agentsApiClient.ts`) caught real, material drift beyond each task's
  own "Before" sample — most notably `T05`'s own sample still assumed the
  pre-Skills-migration `actions: {...}[]` shape, when the real file had
  already moved to `capabilities: AgentCapability[]` (`SPRINT-030`/`031`).
  Reconciling additively against the real shape, not the stale sample,
  avoided silently reverting or conflicting with already-shipped sibling
  work. Reconfirms this project's own long-standing Learnings pattern a
  further time.
- **Honestly verifying the retrieval scenarios against the vault's own
  real current content, not fabricating a positive result for a schema
  that doesn't have real data yet** — directly confirmed
  `Work/Pipeline`/`Agreements`/`Consumption` don't exist in the real
  vault at all, then used the closest real substitute (the
  `customer/<slug>` tag dimension of the same schema, which DOES have
  real content) for `AC-03`'s positive-result half, while independently
  confirming a literal `["Pipeline"]` scope correctly produces the honest
  `"empty"` result today. This is a genuine, disclosed finding recorded
  in both `T04`'s own Implementation Log and the story's own `## Notes`,
  not silently glossed over.
- **The headless-Edge-via-CDP technique, driven by a Python `websockets`
  script (no `node`/`npx` needed)** — a new, reusable combination of two
  already-separately-established patterns (`SPRINT-027`'s headless-Edge
  substitute, `SPRINT-026`'s React-controlled-input Fiber-props direct
  invoke) — successfully drove a real click-to-open-panel → tab-switch →
  type-and-commit → close/reopen-persistence round trip against the real
  running frontend, with zero `node`/`npx` dependency at all (this
  session's shell couldn't resolve either, consistent with prior
  sprints' own documented antipattern).

### What didn't work

- **A first headless-Edge launch attempt via PowerShell's
  `Start-Process`, backgrounded, silently exited within ~1s** with no
  usable diagnostic (`--remote-debugging-port` never opened) — cost one
  investigation cycle before switching to a foregrounded, output-
  redirected invocation (via the Bash tool's own `run_in_background`),
  which worked immediately. Worth trying the foregrounded/output-captured
  form first next time a headless launch needs debugging, rather than a
  fire-and-forget `Start-Process`.
- **Attempting to layer a separate `Runtime.exceptionThrown`/`Console`
  event-listening loop on the SAME `websockets` connection already being
  used for synchronous `Runtime.evaluate` request/response calls** hit a
  `ConcurrencyError` (two coroutines both calling `recv()` on one
  connection) — abandoned in favor of relying on each `Runtime.evaluate`
  response's own `exceptionDetails` field (present only when the
  evaluated JS itself threw), which was sufficient for this task's own
  "zero console errors" smoke check but is narrower than true console-API
  error-log capture. A future task needing genuine console-error
  monitoring during a live CDP session should open a SECOND WebSocket
  connection to the same target for event listening, not share one
  connection for both request/response and event-stream duties.

### Patterns to carry forward

- Real-file-drift reconciliation, honest empty-vs-fabricated retrieval
  verification, and the headless-Edge-via-Python-CDP technique (all
  above) — each generalizes beyond this sprint.

### Antipatterns to avoid

- Fire-and-forget `Start-Process` for a headless browser launch meant to
  be debugged; sharing one CDP WebSocket connection for both synchronous
  RPC and event-stream listening (both above).

### Open follow-ups

- `ESC-026` (`vault_write_tools._is_within_assigned_scope`'s fail-closed
  seam) stays `Open` — this sprint exposed the stable
  `scope_registry.get_agent_scope(agent_id)` contract that seam needs,
  but wiring it is explicitly `REQ-SB-04-US-01`'s own future task, not
  this sprint's (per the story's own Constraints/architecture scope).
- The Customer/Pipeline/Agreements/Consumption schema still has zero real
  ingested notes under `Pipeline`/`Agreements`/`Consumption` specifically
  — this sprint's own retrieval mechanism is proven correct and ready for
  when real data lands there, but the PRD's own literal "get me the
  pipeline for Masdar" example remains untestable against real Pipeline
  content until a future ingestion story populates it.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** This story's prior
`ESC-026`/`ESC-018` history (referenced from `SPRINT-024`/`SPRINT-029`) named
it as the blocker several already-`Done` sprints deliberately excluded work
pending on; it is now decomposed and scheduled here.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption — zero cross-story deps confirmed directly off real task
frontmatter; (2) `REQ-SB-29` is finalized PRD text; (3) product-owner does
not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (5
tasks, S); not a blocked story; no cross-sprint dependency needed for this
sprint itself; (6) N/A; (7) no contradictory inputs; (8) not ambiguous — no
genuine alternative grouping exists (no shared file surface or dependency
edge to any sibling story in this batch). Advances `Draft → Ready`.
