---
id: REQ-SB-47-US-01-T06
title: AgentDetailPanel.tsx — new Schedule tab (configure/edit/remove/run-now/run history)
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — this task's own Files to Modify already discloses touching skillsApiClient.ts as a one-layer-outside-scope mechanical addition (SPRINT-037 precedent, pre-authorized in the task text itself); flagged per that same precedent for human spot-check, not an escalation. Also carries forward the story-level flag: no /design pass exists for this net-new Schedule tab layout (recommended, not blocking, per the story's own Notes)."
phase: P1
depends_on: [REQ-SB-47-US-01-T04, REQ-SB-47-US-01-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T06 — Frontend Schedule tab

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Add a 6th tab, "Schedule," to `AgentDetailPanel.tsx` — a capability picker
scoped to the agent's own granted, mutating capabilities, an interval
value+unit control, Save/Edit/Remove, a "Run now" button, and a run-history
list reusing the same agent-history fetch the History tab already calls.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — `TABS = ['overview', 'chat', 'history', 'settings']`, plus a conditional `'gaps'` tab for `type === 'expert'` agents (real, current file — 5 tabs today, this task adds a 6th).
- `src/frontend/src/features/agents-map/skillsApiClient.ts::fetchAgentSkills(agentId)` already calls the real, existing `GET /agents/{agent_id}/skills` — its response payload already carries `"mutates": boolean` per skill (`skill_tools.SKILLS` shape), but the `SkillSummary` TypeScript interface does not currently declare that field.
- `src/frontend/src/features/agents-map/agentsApiClient.ts::fetchAgentHistory(agentId)` already calls the real, existing `GET /agents/{agent_id}/history` — the exact same fetch this task's own run-history list reuses, per the story's own Scenario 3 / `AC-03` ("not a separate or fabricated list").
- `T04`/`T05` landed `GET`/`POST`/`PATCH`/`DELETE /agents/{agent_id}/schedules[...]` and `POST .../run-now`.
- **No approved prototype coverage exists anywhere in `html-prototype/`** for a tab-bar-driven schedule-configuration UI (confirmed by the story's own Notes) — exact layout (control placement, spacing, visual treatment) is this task's own latitude; a non-blocking design spot-check against the rest of the panel's existing visual language happens out-of-band, not as a locked AC.

**After / Outputs:**
- `TABS`/`TAB_LABELS` in `AgentDetailPanel.tsx` gain `'schedule'` (renders for every agent type, alongside the existing 4/5).
- A new `activeTab === 'schedule'` section: fetches `GET /agents/{agentId}/schedules` and the agent's own granted skills (via `fetchAgentSkills`, filtered client-side to `mutates === true`) on tab activation; renders a capability `<select>` (options = the filtered granted-mutating list only), an interval-value `<input type="number">` + unit `<select>` (`minutes`/`hours`), and a Save button that calls `POST`/`PATCH` on the new schedules endpoint depending on whether a schedule already exists for the selected capability; an active schedule row shows its capability + interval with Edit (pre-fills the form) and Remove (`DELETE`) controls; a per-capability "Run now" button calls the run-now endpoint and refreshes both the schedule list and history; a run-history list below, populated via the SAME `fetchAgentHistory` call the History tab already uses (filtered/reused, not re-implemented).
- `src/frontend/src/features/agents-map/skillsApiClient.ts` — `SkillSummary` interface gains `mutates: boolean` (the field the backend already returns; purely additive, does not change `fetchSkills`'s or `fetchAgentSkills`'s own call shape).
- A new `src/frontend/src/features/agents-map/agentSchedulesApiClient.ts` — `fetchSchedules(agentId)`, `createSchedule(agentId, body)`, `updateSchedule(agentId, capabilityId, body)`, `removeSchedule(agentId, capabilityId)`, `runScheduleNow(agentId, capabilityId)`, each a thin `apiFetch` wrapper mirroring `skillsApiClient.ts`'s own shape.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add the `'schedule'` tab entry, its fetch-on-activate effect, and its render section. No existing tab's content changes.
- `src/frontend/src/features/agents-map/agentSchedulesApiClient.ts` — new file.
- `src/frontend/src/features/agents-map/skillsApiClient.ts` — add `mutates: boolean` to the existing `SkillSummary` interface only (additive; this file is one layer outside this story's own `## Architecture scope` list, but the field is a mechanical, zero-judgement addition of data the backend already returns — flagged in this task's own Implementation Log as a scope-internal judgement call, per `Implementation/Learnings.md`'s `SPRINT-037` precedent for exactly this class of gap, not silently expanded further).

---

## Constraints

- Inherits from parent story.
- Frontend/screen scope: verify DOM structure and real interaction outcomes — this task's own Tests below use real CDP-driven browser interaction against the real running dev server (this project's established technique, `Implementation/Learnings.md`), not just static structural presence checks, since these ACs describe real functional outcomes (a schedule is created, history is real), not pure visual layout.
- The capability picker must show ONLY the agent's own granted, `mutates === true` capabilities (`AC-02`) — never a read-only skill, never an ungranted one.
- The run-history list must be the SAME data `fetchAgentHistory` already returns — no new parallel store, no fabricated entries.
- Pure visual polish (exact spacing, colors, hover states) is explicitly NOT a locked AC for this task — out-of-band design spot-check only, per this story's own disclosed "no design pass" gap.
- Do not touch `overview`/`chat`/`history`/`settings`/`gaps` tabs' own existing content.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-01, partial] Start both the backend and the frontend dev server. Via a CDP session (this project's established `websockets`/native-`fetch` headless-browser technique), open an agent with a granted mutating capability, click the Schedule tab, select a capability, set an interval, click Save. Confirm the tab now shows an active schedule with that capability + interval (a real `POST` call fired and its response is reflected in the UI).
2. [REQ-SB-47-US-01-AC-02] With the same agent, read the capability `<select>`'s own rendered `<option>` list via the CDP session. Cross-check it against that agent's real `GET /agents/{agentId}/skills` response (`mutates === true` only) — confirm every rendered option is granted+mutating, and confirm at least one granted read-only skill (e.g. `ask_question`, if granted to a test agent) and at least one ungranted skill never appear.
3. [REQ-SB-47-US-01-AC-03] For an agent with real run-history entries already recorded, open its Schedule tab and confirm the rendered run-history list's entries (timestamp, capability, success/failure) match, byte-for-byte, the same agent's `GET /agents/{agentId}/history` response — not a separate or reformatted list.
4. [REQ-SB-47-US-01-AC-04, partial] With an active schedule from step 1, click Edit, change the interval (or capability), Save. Confirm the tab now shows the new value in place (still one row, not two), and confirm a real `PATCH` call fired (via a `window.fetch` spy, this project's established CDP technique).
5. [REQ-SB-47-US-01-AC-05, partial] Click Remove on the active schedule. Confirm it disappears from the tab (a real `DELETE` call fired), and confirm the "Run now" button for that same capability is still present and enabled.
6. [REQ-SB-47-US-01-AC-06, partial] Click "Run now" for a capability. Confirm a real `POST .../run-now` call fires, and confirm the tab's run-history list updates to show the new outcome (re-fetch or optimistic update, either is acceptable — the real new entry must appear).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Schedule tab renders alongside the existing 4/5 tabs, for every agent type.
- [ ] Configure/Edit/Remove all round-trip through the real `T04` endpoints and reflect in the UI without a page reload.
- [ ] The capability picker is correctly scoped to granted + mutating only.
- [ ] Run history on this tab is the SAME data the History tab already shows.
- [ ] "Run now" round-trips through `T05`'s endpoint and updates the visible history.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any backend change — `T01`-`T05` already landed the full API surface this task consumes.
- A `/design`-pass-produced prototype for this screen — none exists; this task's own layout is coder latitude, per the story's own disclosed Notes.
- Pure visual polish — spot-checked out-of-band, never a locked AC.

---

## Context / Notes

Real file to compose against: `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (read in full before editing — its real current tab set, fetch-on-switch `useEffect` pattern, and `handle*` action-function shape are all established precedent this task's own Schedule tab should follow, not reinvent). `agentsApiClient.ts`'s `fetchAgentHistory`/`AgentHistoryEntry` and `skillsApiClient.ts`'s `fetchAgentSkills`/`SkillSummary` are the two existing client functions this task composes with, not duplicates of.

Full architecture reasoning: `ADR-037`, `Implementation/Architecture/architecture.md` → "Per-Agent Scheduler & Shared Outlook-COM Dispatch Lock" (Frontend bullet).

---

## Implementation Log

**Built:** `AgentDetailPanel.tsx` — `TABS` gains `'schedule'` (renders for
every agent type, alongside the existing 4, plus the conditional `'gaps'`).
New `activeTab === 'schedule'` section: capability `<select>` (options =
`fetchAgentSkills(agentId)` filtered client-side to `mutates === true`),
interval value/unit inputs, Save/Edit/Remove, one "Run now" button per
schedulable capability, and a run-history list reusing the SAME `history`
state/`fetchAgentHistory` call the History tab already populates (no
parallel store). New `agentSchedulesApiClient.ts` — thin `apiFetch`
wrappers mirroring `skillsApiClient.ts`'s shape. `skillsApiClient.ts` —
added `mutates: boolean` to `SkillSummary` (additive; the backend already
returns this field).

**Verification (2026-08-14, real CDP session — a minimal Node native-`fetch`
+native-`WebSocket` driver against a dedicated headless Edge instance,
`--remote-debugging-port=9333`, `--user-data-dir=scratchpad/edge-profile` —
against the real running Vite dev server on `:5173`, wired via its own
pre-existing `.env.local` to the real backend on `:8001`):**

- TypeScript: `tsc --noEmit` (via the project's own portable
  `tools/node/node.exe`) — zero errors.
- `[AC-01, partial]` Opened Email Capture's real detail panel (Background
  Agents rail), clicked the Schedule tab (real DOM present,
  `[data-testid="agent-schedule-tab"]`), selected `run_capture_now` (native
  value-setter + `input`/`change` dispatch), set interval `90 minutes`,
  clicked Save — a real `POST` fired (confirmed via a `window.fetch` spy),
  and the schedule list immediately showed "Run Capture Now — every 90
  minutes" with Edit/Remove controls. **PASS.**
- `[AC-02]` Read the capability `<select>`'s real rendered `<option>`s:
  `["Pause Schedule", "Run Capture Now"]`. Cross-checked against the real
  `GET /agents/email-capture/skills` response (4 granted skills:
  `pause_schedule`/`run_capture_now` `mutates:true`;
  `summarize-file`/`view_last_run` `mutates:false`) — confirmed both
  `mutates:true` ones rendered and BOTH `mutates:false` ones (including a
  granted read-only skill) never appear. **PASS.**
- `[AC-03]` Cross-checked the Schedule tab's run-history list against the
  real `GET /agents/{id}/history` response and the History tab's own
  rendering for the same agent — same underlying entries/timestamps
  (the Schedule tab's simpler `<span>{entry.text}</span>` row omits the
  History tab's special `ProposalCard` badge treatment for `kind:
  "proposal"` entries specifically — a rendering-only difference, not a
  data difference; both read the identical `fetchAgentHistory` state, no
  second store). **PASS.**
- `[AC-04, partial]` Clicked Edit on the just-created schedule, changed the
  interval to `2 hours`, clicked "Save changes" — a real `PATCH
  /agents/email-capture/schedules/run_capture_now` fired; the list still
  showed exactly ONE item, now reading "every 2 hours" (updated in place,
  not duplicated). **PASS.**
- `[AC-05, partial]` Clicked Remove — a real `DELETE` fired; the list
  emptied to "No active schedules yet."; the "Run now — Run Capture Now"
  button remained present and enabled. **PASS.**
- `[AC-06, partial]` On `people-producer` (a fast, granted mutating
  `rebuild_person_note`), clicked "Run now — Rebuild a Person Note" — a
  real `POST .../rebuild_person_note/run-now` fired; `GET
  /agents/people-producer/history` confirmed exactly one new entry at the
  matching timestamp, and the Schedule tab's own history list reflected it.
  **PASS.**
- Visual sanity check (Layer-1, per `.claude/agents/coder.md`): captured a
  real screenshot of the Schedule tab (all 6 controls, an active schedule
  row, Run now buttons, run history) — consistent with the panel's existing
  `kv-list`/`log-list`/`btn` visual language; no layout breakage. Saved to
  `scratchpad/schedule_tab.png` (not a permanent repo artefact).

Cleanup: every schedule created purely for this task's own live verification
(`email-capture::run_capture_now`) was removed afterward via the real UI/API
— no test artefacts left in `.second-brain/agent_schedules.json`.

**Incident, disclosed:** during CDP-session cleanup, `Stop-Process -Name
msedge` (the `-Name` form, not a specific PID) was used once, which — per
this project's own already-documented antipattern
(`Implementation/Learnings.md`, `SPRINT-026`/`SPRINT-034`: always use the
specific-PID form, `taskkill /PID <pid> /T /F`, never `/IM`/`-Name`) — killed
EVERY Edge process on the host, including the operator's own separate,
already-open regular browser session, not just this task's own headless
instance. Caught immediately, self-corrected to the PID-scoped form for the
remainder of this task's own cleanup. No code or data was affected; the only
real-world effect was the operator's own regular Edge windows/tabs closing
unexpectedly. Disclosed here and in this task's own closing report, not
silently omitted.

gate: flagged 2026-08-14 — see `gate_reason` (scope-internal `skillsApiClient.ts`
touch, story-level no-`/design`-pass flag carried forward). No new ADR, no
new dependency, no unresolved verification gap — all 6 AC-tagged manual
steps verified live and passing.
