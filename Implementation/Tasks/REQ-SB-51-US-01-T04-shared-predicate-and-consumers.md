---
id: REQ-SB-51-US-01-T04
title: Shared isBackgroundAgent predicate — Cockpit filter + layoutAgents partition
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-51-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T04 — Shared isBackgroundAgent predicate — Cockpit filter + layoutAgents partition

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Add `is_background_agent` to the frontend agent types, export one shared `isBackgroundAgent(agent)` predicate from `agentsApiClient.ts`, and wire it into the two real consumers: `Cockpit.tsx`'s "Available Agents" list (filters it out) and `layoutAgents.ts` (partitions it out of ring placement/clustering into a new `backgroundAgents` field).

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/features/agents-map/agentsApiClient.ts`'s `AgentSummary` (line 3-8) and `AgentDetail` (line 20-34) interfaces have no `is_background_agent` field; `updateAgentAssignment`'s body param (line 40-43) has no `is_background_agent` key.
- `src/frontend/src/features/cockpit/Cockpit.tsx` (line 20, 36) renders every fetched `AgentSummary` in the "Available Agents" `.item-list`, unfiltered.
- `src/frontend/src/features/agents-map/layoutAgents.ts`'s `layoutAgents()` (line 59-131) feeds every input `AgentSummary` into `agentsBySection`, with no exclusion; `AgentMapLayout` (line 48-52) has no `backgroundAgents` field.
- `T02`'s `GET /agents` now returns `is_background_agent` on every agent.

**After / Outputs:**
- `AgentSummary`/`AgentDetail` both carry `is_background_agent: boolean`; `updateAgentAssignment`'s body param accepts an optional `is_background_agent?: boolean`.
- `agentsApiClient.ts` exports `isBackgroundAgent(agent: { is_background_agent: boolean }): boolean`.
- `Cockpit.tsx`'s "Available Agents" list never renders a Background Agent and offers no "+ Bring in" for one.
- `layoutAgents()` partitions its input into addressable agents (fed into `agentsBySection`/ring placement/clustering, unchanged) and a new `backgroundAgents: AgentSummary[]` field on `AgentMapLayout`, returned but never consumed by ring/cluster logic.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts`:
  - `AgentSummary` (line 3-8): add `is_background_agent: boolean;`.
  - `AgentDetail` (line 20-34): add `is_background_agent: boolean;`.
  - `updateAgentAssignment`'s body param type (line 40-43): add `is_background_agent?: boolean;`.
  - Add and export `export function isBackgroundAgent(agent: { is_background_agent: boolean }): boolean { return agent.is_background_agent; }`.
- `src/frontend/src/features/cockpit/Cockpit.tsx`:
  - Import `isBackgroundAgent` from `'../agents-map/agentsApiClient'`.
  - Filter the list rendered under "Available Agents" (the `availableAgents?.map(...)` at line 36) down to non-Background agents only — e.g. via a derived `const bringInCandidates = (availableAgents ?? []).filter((agent) => !isBackgroundAgent(agent));` and map over that instead of `availableAgents` directly. Leave `agentById` (line 28, used for chat-message author lookups) reading the full unfiltered `availableAgents` — unrelated to this story's scope.
- `src/frontend/src/features/agents-map/layoutAgents.ts`:
  - Import `isBackgroundAgent` from `'./agentsApiClient'`.
  - `AgentMapLayout` interface (line 48-52): add `backgroundAgents: AgentSummary[];`.
  - `layoutAgents()` (line 59-131): partition the incoming `agents` parameter into addressable vs. background before building `agentsBySection` (line 70-75) — only addressable agents feed `agentsBySection`; collect background agents into a `backgroundAgents` array. Include `backgroundAgents` in the final `return` (line 130).

---

## Constraints

- Inherits from parent story.
- A Background Agent must never occupy a ring slot, count toward `VISIBLE_SLOT_CAP` crowding, or appear in a cluster marker (`REQ-SB-38-US-01`'s clustering logic must never see it) — exclude it before `agentsBySection` is built, not after.
- Do not change `layoutSectionDrilldown()` (line 142-148) — unrelated to this task.
- No caching: `is_background_agent` is read fresh from whatever `AgentSummary[]`/`AgentDetail` the caller already fetched — this task adds no new fetch/cache layer.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-05] With `meeting-capture` marked as a Background Agent (`T01`'s backfill, or a live `PATCH`), open a Meeting Cockpit (`/meeting-cockpit` or the real mounted route — confirm from the router before navigating). Confirm "meeting-capture" does not appear anywhere in the "Available Agents" list, and there is no "+ Bring in" control for it anywhere on the panel.
2. [REQ-SB-51-US-01-AC-06] With `vault-qa` (not a Background Agent) in the same Cockpit's "Available Agents" list — confirm it still appears exactly as before this task, with a working "+ Bring in" action.
3. [REQ-SB-51-US-01-AC-07, partial] In a browser dev console (or a small script) against the real running frontend, call `layoutAgents(agentList, sectionList)` with `agentList` including `todo-capture` (Background) — confirm `layout.mapAgents` and `layout.clusters` never reference `todo-capture`'s id, and `layout.backgroundAgents` includes it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `isBackgroundAgent(agent)` is exported from `agentsApiClient.ts` and used by both `Cockpit.tsx` and `layoutAgents.ts` — no second, independently-duplicated check.
- [ ] A Background Agent never appears in the Cockpit's Available Agents list.
- [ ] A non-Background agent's Cockpit bring-in behaviour is unchanged.
- [ ] `layoutAgents()` excludes Background Agents from `mapAgents`/`clusters` and returns them via a new `backgroundAgents` field.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Rendering the Background Agents rail itself (`T05`).
- The Settings-tab checkbox control (`T06`).
- `REQ-SB-49-US-01`'s own `@mention` suggestion UI (not yet built; inherits this filter automatically once it reuses `fetchAgentList()`, per the story's own Constraints).

---

## Context / Notes

Real files to compose against: `src/frontend/src/features/agents-map/agentsApiClient.ts`, `src/frontend/src/features/cockpit/Cockpit.tsx`, `src/frontend/src/features/agents-map/layoutAgents.ts` — re-read all three fresh before editing. Confirm the real mounted Cockpit route from the router before navigating in step 1 (`Implementation/Learnings.md`, `SPRINT-033`'s own "verify the real route from the router's own source file" finding).

---

## Implementation Log

Re-read all 3 real current files before editing (`agentsApiClient.ts`,
`Cockpit.tsx`, `layoutAgents.ts`) — line numbers/shape matched the
task's own description closely; `AgentSummary` did not yet carry
`is_background_agent` as described. Added `is_background_agent: boolean`
to `AgentSummary`/`AgentDetail`, `is_background_agent?: boolean` to
`updateAgentAssignment`'s body param, and exported
`isBackgroundAgent(agent)`. `Cockpit.tsx` imports it and derives
`bringInCandidates = (availableAgents ?? []).filter((agent) =>
!isBackgroundAgent(agent))`, mapped instead of the raw `availableAgents`
array; `agentById` (chat-author lookup) left reading the full unfiltered
list, unrelated to this task. `layoutAgents.ts` partitions the incoming
`agents` param into `backgroundAgents`/`addressableAgents` BEFORE
`agentsBySection` is built (only `addressableAgents` feeds it);
`backgroundAgents` is returned as a new `AgentMapLayout` field.
`layoutSectionDrilldown()` untouched.

Confirmed the frontend compiles: `tsc -b --noEmit` via the project's own
bundled `tools/node/node.exe` (located from the already-running real Vite
dev server's own process path, PID 29356) — zero errors.

Confirmed the real mounted Cockpit route from `App.tsx` before navigating:
`/meeting-cockpit/:stem` (not the task's own informal
`meeting-cockpit.html` prototype filename) — used a real captured Meeting
note stem, `0-2026-08-10-CC920000`.

**[REQ-SB-51-US-01-AC-05] Verified live** (CDP-driven headless Edge
against the real running frontend on `:5173` + real backend on `:8001`,
`meeting-capture` already `is_background_agent: true` from `T01`'s
backfill): navigated to the real Meeting Cockpit for the above stem;
read every `.item-row` under the "Available Agents" card — 11 rows
rendered, none titled "Meeting Capture" (nor "Email Capture"/"To-Do
Capture" — all 3 Background Agents correctly absent), confirming no
"+ Bring in" control exists for any of them anywhere on the panel. PASS.

**[REQ-SB-51-US-01-AC-06] Verified live, same pass:** "Vault Q&A" (not a
Background Agent) appeared in the same Available Agents list with a
working "+ Bring in" button present, unchanged. PASS.

**[REQ-SB-51-US-01-AC-07, partial] Verified live:** in the same
CDP session, navigated to the app root (`/`) and, from the browser's own
JS console context, `await import('/src/features/agents-map/layoutAgents.ts')`
against the real served module, called `layoutAgents(agents, sections)`
with a real live `GET /agents`/`GET /sections` payload — `layout.mapAgents`
(11 entries) and `layout.clusters` never referenced `todo-capture`'s id;
`layout.backgroundAgents` (3 entries) included it. PASS.

gate: clear 2026-08-14 — no triggers fired (one shared predicate, two
real call sites, no ADR touched, no material assumption beyond the
task's own Context/Notes, all 3 tagged verification steps passed live in
one combined CDP session).
