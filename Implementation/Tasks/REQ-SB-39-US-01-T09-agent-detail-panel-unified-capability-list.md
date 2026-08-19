---
id: REQ-SB-39-US-01-T09
title: AgentDetailPanel.tsx — unified capability list with real grant/revoke control; new skillsApiClient.ts
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: frontend
status: Done
gate: flagged
gate_reason: "environment gap — Node.js is not installed anywhere on this host (confirmed via registry + filesystem search), so npm run build/tsc and a live browser check could not be run; code built and manually type-reviewed instead, both locked ACs this task touches (AC-02, AC-07) are already independently verified live at the API layer by T03/T08"
phase: P1
depends_on: [REQ-SB-39-US-01-T08]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T09 — AgentDetailPanel.tsx — unified capability list

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Replace the agent detail side panel's static "Available actions" button
list with a unified capability list sourced from `agent.capabilities`
(`T08`'s new response shape), with a real grant/revoke control for every
Skill-shaped item — reusing the already-existing `GET /skills`,
`GET/POST/DELETE /agents/{agent_id}/skills[/{id}]` endpoints via a new
`skillsApiClient.ts` (mirrors `settingsApiClient.ts`'s thin fetch-wrapper
shape). **No new backend endpoint is needed.** Built directly against the
established Section/Provider/Keywords/Working-mode `kv-list` row pattern
— the operator explicitly decided to skip a `/design` pass for this
surface (`REVIEW-QUEUE.md`, 2026-08-13 update on `REQ-SB-29-US-01`'s own
entry).

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetail` (`agentsApiClient.ts`) has `actions: {id, label}[]`.
- `AgentDetailPanel.tsx`'s Settings tab renders a static "Available
  actions" block: `agent.actions.map(...)` as plain, non-interactive
  `<button className="btn">` elements — no grant/revoke affordance.

**After / Outputs:**
- `AgentDetail`'s `actions` field is replaced with `capabilities:
  {id, label, kind: 'action' | 'skill'}[]` (matching `T06`/`T08`'s real
  chosen shape — reconcile against `T06`'s own Context/Notes before
  writing this file, do not assume).
- `AgentDetailPanel.tsx`'s Settings tab renders a single "Capabilities"
  block from `agent.capabilities`:
  - a `kind: 'skill'` item carries a real, working grant/revoke control
    (e.g. a checkbox/toggle) wired to `skillsApiClient.ts`'s
    `grantAgentSkill`/`revokeAgentSkill`.
  - a `kind: 'action'` item renders as a plain, non-interactive list item
    — unchanged posture from today (this story does not make Actions
    revocable; that's `REQ-SB-39-US-02`'s own scope).
  - the full Skill catalog (`GET /skills`) is fetched once to offer any
    ungranted catalog Skill as a grantable option (not just the agent's
    already-granted ones).
- New `src/frontend/src/features/agents-map/skillsApiClient.ts`:
  ```typescript
  import { apiFetch } from '../../api/client';

  export interface SkillSummary {
    id: string;
    name: string;
    description: string;
  }

  export function fetchSkills(): Promise<SkillSummary[]> {
    return apiFetch<SkillSummary[]>('/skills');
  }

  export function fetchAgentSkills(agentId: string): Promise<SkillSummary[]> {
    return apiFetch<SkillSummary[]>(`/agents/${agentId}/skills`);
  }

  export function grantAgentSkill(agentId: string, skillId: string): Promise<{ granted: boolean }> {
    return apiFetch<{ granted: boolean }>(`/agents/${agentId}/skills/${skillId}`, { method: 'POST' });
  }

  export function revokeAgentSkill(agentId: string, skillId: string): Promise<{ revoked: boolean }> {
    return apiFetch<{ revoked: boolean }>(`/agents/${agentId}/skills/${skillId}`, { method: 'DELETE' });
  }
  ```

---

## Files to Modify

- `src/frontend/src/features/agents-map/skillsApiClient.ts` (new).
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — the
  Settings tab's "Available actions" block.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` — `AgentDetail`
  type's `actions` field replaced with `capabilities` (matching `T06`/
  `T08`'s real chosen shape).

---

## Constraints

- Inherits from parent story. Renders from `agent.capabilities` — the
  `"actions"` field no longer exists on the response (`T08`).
- Only catalog Skills (present in `GET /skills`) get a real grant/revoke
  control; a still-real Action-shaped capability (`kind: 'action'`)
  renders as a plain, non-interactive item exactly as today — no
  fabricated grant/revoke affordance for something this story does not
  make revocable.
- **No new backend endpoint** — reuses `GET /skills`,
  `GET/POST/DELETE /agents/{agent_id}/skills[/{id}]` exactly as-is.
- Must not otherwise change any other tab/section of
  `AgentDetailPanel.tsx` (Chat/History tabs, and the Section/Provider/
  Keywords/Working-mode `kv-list` rows, are specced elsewhere and
  unaffected — per the parent story's own `## Notes`).
- Structural, not visual-polish — reuse existing tokens/classes
  (`kv-list`/`kv-row`, `action-list`, `btn`/`btn-primary`/`btn-danger`
  patterns already in `styles.css`); no new CSS framework, no hardcoded
  colours. Pure visual polish (exact spacing/hover) is out of scope for
  any locked AC — spot-checked out-of-band, never blocking.
- `npm run build` / `npx tsc --noEmit` must stay clean.

---

## Tests

<!-- Structural DOM verification only -- this project's established
headless-Chrome-via-CDP technique (no test-stack ADR exists yet). -->

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-07] Open the Agents Map in a real browser, click
   `vault-qa` (post-retrofit — mixed migrated-Skill capabilities), open
   its Settings tab — confirm a single capability-list region renders all
   of that agent's current capabilities together, and confirm there is
   **no separate "Available actions" region and a separate "Skills"
   region both present** — only one unified list/section.
2. [REQ-SB-39-US-01-AC-02] For a Skill-shaped item (e.g. grant
   `web-research` to a test agent, or use an already-granted one), confirm
   a real, working revoke control is rendered (not a static button) —
   click it, confirm a real `DELETE /agents/{agent_id}/skills/{skill_id}`
   network call fires (Network tab / CDP), and the item disappears from
   the list on refresh. Then grant a currently-ungranted catalog Skill via
   its own grant control — confirm a real `POST` call fires and the item
   appears. Revert any test-only grants/revokes made to real agents'
   state afterward.
3. Non-AC smoke check: confirm a still-real Action-shaped capability
   (e.g. `run_capture_now` on `email-capture`) renders as a plain list
   item with no grant/revoke control.
4. Non-AC smoke check: `npm run build` (or `npx tsc --noEmit` if `npm`
   isn't resolvable on `PATH` in this session — see
   `Implementation/Learnings.md`'s own `npx`/`node`-on-PATH antipattern
   entries — locate the real install via the registry if it recurs) —
   confirm clean, zero new type errors.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `AgentDetailPanel.tsx`'s Settings tab renders `agent.capabilities`
      as one unified list (no separate Actions/Skills sections)
- [ ] Skill-shaped items carry a real, working grant/revoke control wired
      to `skillsApiClient.ts`
- [ ] Action-shaped items remain plain, non-interactive (unchanged
      posture)
- [ ] `agentsApiClient.ts`'s `AgentDetail` type updated (`actions` →
      `capabilities`)
- [ ] No new backend endpoint added
- [ ] `npm run build` / `tsc` clean
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any visual polish/styling beyond reusing existing tokens/classes.
- Building grant/revoke for still-real (mutating) Actions —
  `REQ-SB-39-US-02`'s own scope.
- A standalone Skills Repository browsing screen (a list of all
  registered Skills independent of any one agent) — not in scope per the
  parent story's own `## Notes` (`REQ-SB-27-US-01` never built one
  either).

---

## Context / Notes

**Resolves an apparent tension with the parent story's own `## Non-Goals`
("Designing or building the concrete Skills grant/revoke UI... this
story's Acceptance Criteria are written at the mechanism/observable-
behavior level and do not presume a specific screen shape"), written by
the analyst before the operator's later, same-day decision to skip
`/design` for this batch and build directly (`REVIEW-QUEUE.md`,
2026-08-13 update; `Implementation/Architecture/ADR.md` → `ADR-028`'s own
Context, "Frontend" bullet under the parent story's `## Notes`
Architecture-scope list).** The locked ACs (`AC-02`, `AC-07`) are
themselves still written at the mechanism/observable-behavior level and
do not require this specific screen to exist to be independently
satisfied at the API layer (`T03`, `T08`) — this task is additive
architecture-scope coverage, not a reinterpretation of either locked AC's
own wording, and its own Tests above are supplementary structural checks,
not the sole verification path for either AC.

---

## Implementation Log

**2026-08-13 — Built; verification partially environment-blocked, disclosed
honestly, not silently skipped.**

Built exactly as spec'd: new `skillsApiClient.ts` (verbatim per the task's
own sample, matching `settingsApiClient.ts`'s import-path depth exactly);
`agentsApiClient.ts`'s `AgentDetail.actions` replaced with a new
`AgentCapability[]` `capabilities` field (`{id, label, kind: 'action' |
'skill'}`, reconciled against `T06`'s real chosen shape, confirmed
identical); `AgentDetailPanel.tsx`'s "Available actions" block replaced
with a single "Capabilities" `kv-list` region — `kind: 'action'` items
render as a plain, non-interactive row (label + "Built-in", no control);
`kind: 'skill'` items (already granted) get a real, wired `Revoke`
button; the full `GET /skills` catalog is fetched once and any
not-yet-granted catalog Skill renders as its own row with a `Grant`
button — both wired to the new `skillsApiClient.ts` functions, both
refetch the full agent afterward (`fetchAgent`) so the rendered list
reflects real server state, not an optimistic local guess.
`grep`-confirmed no other frontend file references `agent.actions` /
`AgentDetail.actions` — zero other consumers to fix.

**Environment gap, disclosed (not silently worked around):** this
worktree/host has **no Node.js installation anywhere** — confirmed via
`HKLM:\SOFTWARE\Node.js` (absent), the Node.js uninstall-registry entry
search (absent), `Get-Command node`/`npm` (absent), and a filesystem
search of the usual install locations (`Program Files\nodejs`, `%APPDATA%
\npm`, `%LOCALAPPDATA%\Volta`, `~\.volta`, `scoop`, plus a `cursor`-bundled
Node search) — all absent. This is a genuine step beyond this project's
own already-documented "`npx`/`node` not resolvable on `PATH`" antipattern
(`Implementation/Learnings.md`, `SPRINT-027`/`SPRINT-028`) — those found
Node installed-but-off-PATH and worked around it; this host does not have
it installed at all. Consequence: **`npm run build`/`npx tsc --noEmit`
could not be run, and the Vite dev server could not be started, so the
real-browser DOM checks (this task's own Test steps 1–3) could not be
performed either.**

**Best-available substitute performed instead:** a careful, full manual
re-read of the changed file plus every file that imports/consumes it
(`grep`-confirmed zero other `AgentDetail.actions`/`agent.actions`
consumers) — types line up (`AgentCapability.kind` union narrowing,
`skillsApiClient.ts`'s return types matching each handler's usage,
`SkillSummary`/`AgentCapability`'s `id: string` matching both
`handleGrantSkill`/`handleRevokeSkill`'s parameter types), all imports
used, no orphaned references to the removed `actions` field anywhere.
This is weaker evidence than a real compiler pass and is named explicitly
as such, not conflated with one.

**Why this does not block the task:** both locked ACs this task touches
(`AC-02`, `AC-07`) are already independently, fully verified live at the
mechanism/API layer by `T03` and `T08` respectively — the parent story's
own `## Notes` explicitly frames this task's own Tests as "supplementary
structural checks, not the sole verification path for either AC." No
locked AC is left unverified by this environment gap; only this task's
own non-AC structural/visual checks are.

Non-AC smoke check confirmed by code inspection (not live click, per the
gap above): an action-shaped capability (e.g. `run_capture_now`) renders
via the `kind === 'action'` branch, which has no `onClick`/button at all
— structurally non-interactive, matching the Constraint.

`npm run build`/`tsc` clean — **not verified, environment-blocked, see
above.**

gate: flagged 2026-08-13 — the environment gap above, for a human to
either provision Node.js on this host or re-run the browser/build check
from an environment that has it, before treating this screen as fully
signed off end-to-end (independent of the fact that no locked AC is
actually blocked by this gap).
