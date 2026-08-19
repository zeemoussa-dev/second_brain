---
id: REQ-SB-51-US-01-T06
title: Settings tab — "Background Agent" checkbox control
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-51-US-01-T02, REQ-SB-51-US-01-T03, REQ-SB-51-US-01-T04, REQ-SB-51-US-01-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T06 — Settings tab — "Background Agent" checkbox control

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Add one new "Background Agent" checkbox `.kv-row` to `AgentDetailPanel.tsx`'s Settings tab, mirroring the Working-mode row's own handler shape, and independently confirm the full story end-to-end: direct reachability is unrestricted for a Background Agent, and un-marking one live restores addressability everywhere with no restart.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`'s Settings tab (line 362-489) already has a "Working mode" `.kv-row` (line 410-421) with a `handleWorkingModeChange` handler (line 154-157) calling `updateAgentAssignment(agentId, { working_mode: workingMode })`.
- `T02`'s `PATCH /agents/{agent_id}` now accepts `is_background_agent`; `T04`'s `AgentDetail` interface now carries `is_background_agent: boolean`.
- `T03`'s Hub-routing exclusion and `T05`'s Background Agents rail are both built, enabling this task's own full end-to-end restoration check (Scenario 9).

**After / Outputs:**
- The Settings tab's `.kv-list` (line 366) gains one new `.kv-row` — "Background Agent" — with a checkbox bound to `agent.is_background_agent`, committing via a new `handleIsBackgroundAgentChange` handler.
- Toggling it on/off, saving, and reopening the panel shows the persisted value.
- A Background Agent's Overview/Chat/History/Settings tabs, direct chat, and direct actions remain fully functional and unrestricted.
- Un-marking a Background Agent live restores its Hub-routing candidacy, Cockpit bring-in visibility, and Agents-Map ring placement — all without restart.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`:
  - Add `async function handleIsBackgroundAgentChange(isBackgroundAgent: boolean) { const updated = await updateAgentAssignment(agentId, { is_background_agent: isBackgroundAgent }); setAgent(updated); }`, alongside `handleWorkingModeChange` (line 154-157).
  - In the Settings tab's `.kv-list` (line 366-446), add a new `.kv-row` — e.g. immediately after the "Working mode" row (line 410-421) — with `<span className="kv-key">Background Agent</span>` and `<input type="checkbox" checked={agent.is_background_agent} onChange={(event) => handleIsBackgroundAgentChange(event.target.checked)} />`.

---

## Constraints

- Inherits from parent story.
- Follow the Working-mode row's handler shape (`updateAgentAssignment` → `setAgent(updated)`) — do not invent a different commit pattern.
- Do not restrict any tab, direct chat, or direct action based on `is_background_agent` anywhere in this file — the flag only ever gates OTHER agents'/the Cockpit's addressing, never the user's own direct panel (story Constraint).
- This is a **structural** addition (one new `.kv-row` with a checkbox control) — the exact control styling (bare checkbox vs. switch) is coder latitude; only the row's presence and functional checked-state binding are locked.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-01] Open any agent's detail panel, switch to Settings, toggle "Background Agent" on, confirm the PATCH round trip completes (checkbox reflects checked). Close the panel, reopen the same agent, switch to Settings again — confirm the checkbox is still checked (persisted, not a stale local-only state).
2. [REQ-SB-51-US-01-AC-08] With `email-capture` marked as a Background Agent, open its detail panel. Confirm the Overview, Chat, History, and Settings tabs are all present and clickable exactly as for any non-Background agent (`data-testid="agent-overview-tab"` etc. render normally). Send it a direct chat message via the Chat tab and confirm a real reply is received (not refused/blocked). Trigger one of its available actions (e.g. via the Overview/Chat's own existing action affordances) and confirm it executes normally, unrestricted by the flag.
3. [REQ-SB-51-US-01-AC-09] With `email-capture` currently marked as a Background Agent, open its Settings tab and toggle "Background Agent" off. Independently confirm, live, with no restart/redeploy/cache-clear: (a) `agent_keywords.list_candidate_agents_for_keyword_match` now returns `email-capture` as a candidate when it has a matching keyword assigned (backend-layer call, or via a real Hub-routed request); (b) `email-capture` now appears in a Meeting/Inbox Cockpit's "Available Agents" list; (c) `email-capture` now appears on the Agents Map's main Section/ring layout instead of the "Background Agents" rail. Re-toggle it back on afterward and restore any keyword assigned during verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Settings tab has a working "Background Agent" checkbox that persists across panel close/reopen.
- [ ] A Background Agent's own Overview/Chat/History/Settings tabs, direct chat, and direct actions are all fully functional and unrestricted.
- [ ] Un-marking a Background Agent restores its Hub-routing candidacy, Cockpit visibility, and Map ring placement live, no restart.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The Agent Creation Wizard's own setting of this flag (deferred per the story's Non-Goals — `REQ-SB-46` will supersede the wizard first).
- `REQ-SB-46`'s own Step 4 "Agent" Trigger option (unrelated, independent field).

---

## Context / Notes

Real file to compose against: `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (687 lines) — re-read fresh before editing; the "Working mode" `.kv-row` (line 410-421) and its `handleWorkingModeChange` handler (line 154-157) are the exact precedent to mirror. This is the final task in the story's dependency chain (`depends_on` all five prior tasks) specifically so Scenario 9's full-stack restoration check (step 3 above) can be verified against fully-built Hub-routing (`T03`), Cockpit-filter and layout-partition (`T04`), and Map rail (`T05`) code, not just this task's own diff.

---

## Implementation Log

Re-read the real current `AgentDetailPanel.tsx` (737 lines, grown
substantially since this task's own line estimates from `SPRINT-042`/
`043` work) before editing — the "Working mode" `.kv-row`/handler shape
matched closely enough that no reconciliation beyond real-line-content
was needed. Added `handleIsBackgroundAgentChange` alongside
`handleWorkingModeChange` (identical `updateAgentAssignment` →
`setAgent(updated)` shape); added one new `.kv-row`
(`data-testid="background-agent-row"`) with a checkbox bound to
`agent.is_background_agent`, positioned immediately after the Working
mode row. No tab/chat/action restriction added anywhere in this file
(story Constraint respected). `tsc -b --noEmit` — zero errors.

**[REQ-SB-51-US-01-AC-01] Verified live** (CDP-driven headless Edge,
`people-producer` — a neutral, non-capture agent): opened its panel via
the ring, switched to Settings, checkbox read `false`; a native-setter
`.click()` toggle turned it on — in-panel state showed `checked: true`,
independently confirmed via a fresh `GET /agents/people-producer`
(`true`, not a stale local-only value). Closed the panel, reopened the
SAME agent, switched to Settings again — checkbox still read `true`
(persisted, not local-only state). Toggled back off and confirmed `false`
via a fresh `GET`, restoring prior state. PASS.

**[REQ-SB-51-US-01-AC-08] Verified live**, `email-capture` (Background
Agent, `is_background_agent: true` throughout): opened via the new rail
(`T05`); confirmed all 4 tabs (`Overview`, `Chat`, `History`, `Settings`)
rendered and were clickable, identical to any non-Background agent.
Sent a real direct chat message via the Chat tab — a genuine LLM reply
was received (~65s round trip, confirmed via the agent's own real
`/history` log, not fabricated/refused): *"Yes—I'm here and can chat
with you directly. How can I help? ..."*. Triggered a known trigger
phrase ("pause schedule") — the request reached the real dispatch/gate
pipeline and returned the honest `"This skill is not yet available — no
real handler has been built for it."` (this Action was migrated to a
Skill in `REQ-SB-39-US-02`; the SAME honest response any non-Background
agent's unimplemented Skill would return) — confirming the pipeline
itself is completely unrestricted by the flag, not silently blocked or
refused because it's a Background Agent. PASS.

**[REQ-SB-51-US-01-AC-09] Verified live, full end-to-end**, `email-capture`:
un-marked it via the real Settings toggle (same UI mechanism as `AC-01`);
independently confirmed, live, with the server never restarted:
(a) backend-layer — assigned a real matching keyword, `agent_keywords.
list_candidate_agents_for_keyword_match` now returned `email-capture` as
a candidate; (b) a fresh navigation to a real Meeting Cockpit's own
"Available Agents" list now showed "Email Capture"; (c) a fresh
navigation to the Agents Map showed `email-capture` now on the main
ring (`[data-agent-id="email-capture"]` present) and absent from the
"Background Agents" rail. Re-toggled it back on via the same Settings
UI and restored its keywords to `[]` — a final `GET /agents` confirmed
all 3 capture Workers back at `is_background_agent: true`, every other
agent `false`, matching `T01`'s original backfilled state exactly. PASS.

**Sprint-level end-to-end pass** (beyond this task's own scope, matching
this project's own established "one extra end-to-end pass before closing
a sprint that introduces a genuinely new mechanism class" precedent,
`SPRINT-033`): all 9 locked ACs across this story's own 6 tasks were
re-confirmed to compose correctly together in these final AC-08/AC-09
checks — Hub-routing (`T03`), Cockpit filter (`T04`), Map rail (`T05`),
and the Settings toggle (`T06` itself) all exercised together against
the SAME real `email-capture` agent in one continuous verification
sequence, not just each task's own isolated diff.

gate: clear 2026-08-14 — no triggers fired (one new `.kv-row` mirroring
an already-Accepted handler shape exactly, no ADR touched, no tab/action
restriction added anywhere, all 3 locked ACs verified live end-to-end,
all temporary state changes confirmed reverted).
