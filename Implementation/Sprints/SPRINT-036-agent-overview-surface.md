---
id: SPRINT-036
title: Agent Overview surface
status: Done
gate: flagged
gate_reason: "Coder wrap (2026-08-14) — retrospective drafted below; human skims and propagates patterns/antipatterns into Implementation/Learnings.md per Pipeline.md's sprint-retro human touchpoint. No build blocker; both tasks Done, all 7 locked ACs verified live."
phase: P1
depends_on_sprints: [SPRINT-032, SPRINT-035]
sizing_estimate: "~2 tasks, S"
created: 2026-08-13
started: 2026-08-14
completed: 2026-08-14
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-036 — Agent Overview surface

## Sprint Goal

Add an Overview default-landing tab on the agent detail panel — Purpose,
Guardrails, Working mode, and a graceful "not yet assigned" Vault Scope
region, plus an Expert-only open-gap count — shown before Chat.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-41-US-01` is the only story
  here. Its 2 tasks form a straight chain (`T01 → T02`); `T02` carries two
  real cross-story edges: `REQ-SB-40-US-01-T08` (Knowledge gaps tab, whose
  gap-count summary this Overview tab reuses) and `REQ-SB-29-US-01-T05`
  (Vault scope row, whose field this Overview tab also surfaces).
- **Why NOT folded into `SPRINT-035` (`REQ-SB-40-US-01`):** would produce a
  10-task sprint, past this project's own `L` ceiling (9 tasks, `SPRINT-021`
  precedent). **Why NOT folded into `SPRINT-032` (`REQ-SB-29-US-01`)
  instead:** the two stories share no file surface beyond the one row this
  story reads, and bundling a small backend/scoping story with a small
  frontend-panel story purely to reach a rounder task count is not a
  grouping this project's own sprint history uses. Kept as its own small
  sprint, ordered after both real upstream dependencies via
  `depends_on_sprints`.
- **Sizing estimate:** ~2 tasks, S (matches `SPRINT-029`'s own 2-task, S
  precedent).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-41-US-01](../UserStories/REQ-SB-41-US-01-agent-overview-surface.md) | Agent Overview surface — purpose, Guardrails, and Working mode shown before Chat, with a graceful "not yet assigned" Vault Scope region | P1 | Done |

**Tasks in scope** (dependency order): `T01` (agent_registry.py Purpose
backfill for 7 shipped agents, `depends_on: []`) → `T02`
(AgentDetailPanel.tsx new Overview tab, `depends_on: [T01,
REQ-SB-40-US-01-T08, REQ-SB-29-US-01-T05]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-032` (`REQ-SB-29-US-01`), `SPRINT-035`
  (`REQ-SB-40-US-01`) — both edges mirror `T02`'s own real task-level
  `depends_on`, not an invented dependency.

---

## Out of Scope

- Knowledge-gap tracking itself (`REQ-SB-40-US-01` → `SPRINT-035`); vault
  scoping itself (`REQ-SB-29-US-01` → `SPRINT-032`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, already landed at `/plan-tasks` (`ADR-033`); no further architectural fact changed during the build
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-033`, already `Accepted` at `/plan-tasks`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new decision/pattern/constraint emerged this pass
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~2 tasks, S — **Actual:** 2 tasks, S — matched exactly.
  `T02` (frontend) was correctly the heavier of the two by verification
  effort, not code volume: the actual diff was small (a tab-order/default
  change, one new content block reusing existing classes verbatim), but
  proving all 7 locked ACs live — across 3 different agent-type spot
  checks, a real working-mode change, a real scope assignment surviving a
  panel close/reopen, and a real Expert-only gap-count composition —
  needed a genuinely non-trivial CDP-driven browser session.

### What worked

- **Composing the whole task around the REAL current file caught every
  real drift, none of them blocking.** Three sibling stories had all
  landed real changes to the same shared files ahead of this build
  (`REQ-SB-40-US-01-T08`'s `'gaps'` tab, `REQ-SB-29-US-01-T05`'s `scope`
  field, and — genuinely unanticipated in either task's own "before"
  sample — `REQ-SB-39`'s Skills unification replacing `agent.actions`
  with `agent.capabilities`). None of the three required any deviation
  from this task's own locked diff; the third was simply noted for
  transparency in the Implementation Log, not escalated, since it never
  touched this story's own scope.
- **Reusing already-declared sibling state (`gapsData`/`setGapsData`)
  instead of redeclaring it** kept the Overview's own gap-count fetch a
  true one-line addition, with zero risk of two divergent pieces of state
  going out of sync.
- **A minimal Node+native-`fetch`+native-`WebSocket` CDP client (no
  `puppeteer`/`playwright` dependency, no `ws` package) driving a real
  headless Edge instance** proved a fully adequate, zero-new-dependency
  substitute for a proper visual/e2e harness — real browser, real DOM,
  real network calls to the real backend, real React state, structural
  `data-testid` assertions plus two genuine state mutations (working mode,
  vault scope) verified end-to-end including server-side persistence
  across a panel close/reopen.

### What didn't work

- **Reading a `<select>`/`<input>`'s value in the SAME synchronous
  `Runtime.evaluate` call as the click/dispatch that changes it** raced
  ahead of React's own state-flush-then-rerender cycle and returned the
  stale pre-change value/DOM twice during this session (a `<select>`
  value read immediately after `dispatchEvent('change')`, and an Overview
  region read immediately after a tab-switch click). Both were false
  negatives, not real defects — resolved by adding a short `setTimeout`
  between the mutating call and the read-back call, then reconfirmed
  correct.

### Patterns to carry forward

- **A short (~500-1000ms) real wait between a CDP-dispatched
  state-changing event and reading its resulting DOM back, even for
  ordinary `onClick` tab switches (not just `onBlur`-commit inputs)** —
  extends `SPRINT-020`'s own `onBlur`/Fiber-props-direct-invoke precedent:
  the same "don't read back in the same synchronous evaluate call"
  discipline applies to plain `setState`-driven tab switches too, not just
  synthetic-event-delivery edge cases.
- **Locate a project's own bundled Node install via the actual running
  dev-server process's own `.Path`, rather than assuming `node`/`npx` on
  `PATH`** — a fourth confirmed instance of `PATH` not resolving `node` in
  this session/shell (`SPRINT-027`/`028`); this time resolved directly and
  quickly by reading the already-running Vite process's own executable
  path (`Get-Process -Id <pid> | .Path`) instead of the registry lookup
  used previously — a faster, more direct technique worth trying first.

### Antipatterns to avoid

- No new antipattern beyond the "same-synchronous-evaluate read-back
  race" above, itself resolved within this same session.

### Open follow-ups

- The `ESC-031`/`ADR-033` `REVIEW-QUEUE.md` item (human review of
  `ADR-033`'s navigation-default change and the 7 backfilled Purpose
  lines) is still open — untouched by this build pass, left for the human
  as originally scoped.
- No dedicated `html-prototype/` screen or Layer-1 visual harness exists
  for the Overview tab yet (per the story's own `## Affected Screens`); a
  future `/design` pass may restyle it without touching this story's own
  locked, structural ACs.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** `ESC-031` (the story's
prior net-new-design-needed + unclear-requirement flags) was resolved before
this pass — see the story's own `gate_reason`/Context.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — both cross-sprint edges are
direct mirrors of `T02`'s own real `depends_on`; (2) `REQ-SB-41` is finalized
PRD text; (3) product-owner does not write ADRs; (4) no new `ESCALATIONS.md`
entry from this pass; (5) not oversized (2 tasks, S); not a blocked story;
the 2 cross-sprint dependencies are pre-existing task edges, not introduced
by this pass's own choice; (6) N/A; (7) no contradictory inputs; (8) not
ambiguous — the fold-in-vs-split choice is resolved on a concrete sizing
basis. Advances `Draft → Ready`.
