---
id: REQ-SB-48-US-01-T02
title: Collapsible, icon-bearing, multi-select Tool tree in the Capabilities section
parent_story: REQ-SB-48-US-01
requirement_id: REQ-SB-48
type: frontend
status: Done
gate: flagged
gate_reason: "live verification found BUG-013, a genuine pre-existing bug in an out-of-scope shared function — see Implementation Log"
phase: P1
depends_on: [REQ-SB-48-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-48-US-01-T02 — Collapsible, icon-bearing, multi-select Tool tree in the Capabilities section

## Parent Story

- Story: [[REQ-SB-48-US-01]] — `../UserStories/REQ-SB-48-US-01-skills-grouped-by-tool-collapsible-tree.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-48 *Skills Grouped by Tool — Collapsible Multi-Select Tree with Icons*

---

## Objective

Replace `AgentDetailPanel.tsx`'s flat Capabilities `kv-list` with a
collapsible tree grouped by Tool (Outlook/Vault/Web/Compass), each group and
Skill row carrying a fixed Tool icon, supporting multi-select-and-bulk-
grant/revoke within one expanded group — while Built-in (`action`-kind)
capabilities keep rendering exactly as today, outside the tree.

---

## Starting State → End State

**Before / Inputs:**
- `skillsApiClient.ts`'s `SkillSummary` interface: `{id, name, description}`
  — no `tool` field (T01 adds it server-side; this task consumes it).
- `agentsApiClient.ts`'s `AgentCapability` interface: `{id, label, kind}` —
  no `tool` field.
- `AgentDetailPanel.tsx`'s Settings tab → Capabilities section (lines
  ~449-487, confirmed by direct read): one flat `<div className="kv-list">`
  rendering `agent.capabilities` (action rows: static "Built-in" label, no
  button; skill rows: per-row Revoke button) followed by every catalog Skill
  not yet granted (per-row Grant button). `handleGrantSkill`/
  `handleRevokeSkill` each call `grantAgentSkill`/`revokeAgentSkill`
  (`skillsApiClient.ts`) for exactly one skill id, then `fetchAgent` to
  refresh `agent` state. `skillCatalog` is fetched once per agent switch via
  `fetchSkills()`.
- `Sidebar.tsx`'s existing icon convention: plain Unicode glyphs in a
  `<span className="nav-icon">…</span>`, no icon library/SVG pipeline.

**After / Outputs:**
- `SkillSummary` gains `tool: string`; `AgentCapability` gains `tool?:
  string` (optional — action-kind rows never carry it, per T01's Constraints).
- The Capabilities section's skill-kind rows (both granted and
  not-yet-granted) render nested under 4 Tool group headers — Outlook,
  Vault, Web, Compass — each expanded by default, each with a collapse/
  expand toggle that is a pure client-side display state (never fires a
  grant/revoke call).
- Every Tool group header and every Skill row under it shows that Tool's
  fixed icon (one glyph per Tool, 4 total, inherited by every Skill row
  under that Tool — no per-Skill icon).
- Within one expanded Tool group, the user can select more than one Skill
  row of the SAME current grant state (all not-yet-granted, or all
  granted) and trigger one Grant or one Revoke action that issues N
  sequential single-Skill `POST`/`DELETE
  /agents/{agentId}/skills/{skillId}` calls (reusing
  `grantAgentSkill`/`revokeAgentSkill` unchanged) — never a new batch
  endpoint. Selecting a row of the opposite grant state clears the prior
  selection and starts a new one, flipping the available bulk action.
- Built-in (`action`-kind) capability rows render exactly as today — a
  plain row, "Built-in" label, no button — outside the new tree, with no
  Tool icon and no checkbox.

---

## Files to Modify

- `src/frontend/src/features/agents-map/skillsApiClient.ts` — `SkillSummary`
  gains `tool: string`.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` —
  `AgentCapability` gains `tool?: string`.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — replace the
  Capabilities section's flat `kv-list` (lines ~449-487) with the new
  collapsible/icon/multi-select Tool tree, rendered via the new shared
  component below in `mode="manage"`.
- **`src/frontend/src/features/agents-map/SkillsTree.tsx` (new, standalone
  file — this filename and its standalone existence are no longer this
  task's own latitude; they are load-bearing for a sibling story).**
  `REQ-SB-46-US-01` (Agent Creation Wizard Redesign, `ADR-039` point 2,
  `Ready`, its own `T04` depends directly on this exact file) reuses this
  SAME component in `mode="select"` for its own Step 3 Skills picker — a
  real, already-wired cross-story `depends_on` edge. Build it as a
  standalone, mode-parameterized component from the start: `<SkillsTree
  mode="manage" | "select" tools={...} skills={...} ...mode-specific
  props />`. `mode="manage"` is this task's own scope (grant/revoke
  buttons, wired to `grantAgentSkill`/`revokeAgentSkill`); leave a clear,
  documented seam for `mode="select"` (multi-select checkboxes,
  `selectedIds`/`onChange` props, no API call) even though building that
  branch itself is `REQ-SB-46-US-01-T04`'s own job, not this task's — do
  not ship a fully-inlined, non-extractable implementation inside
  `AgentDetailPanel.tsx`, since that would force `REQ-SB-46-US-01-T04`
  into an escalation per its own documented contingency plan.

---

## Constraints

- Inherits from parent story: no new backend endpoint; multi-select must
  compose N sequential single-Skill `grantAgentSkill`/`revokeAgentSkill`
  calls, never a new bulk call.
- **Fixed 4-icon set (Unicode glyphs, mirroring `Sidebar.tsx`'s `.nav-icon`
  convention)** — one icon per Tool (`Outlook`, `Vault`, `Web`, `Compass`),
  inherited by every Skill row under that Tool. Do not source a distinct
  icon per individual Skill, and do not introduce an icon library/SVG asset
  pipeline.
- Tool groups are expanded by default (parent story's disclosed default,
  confirmed final by the architect).
- Selection model is same-grant-state-only within a group: selecting a row
  of the opposite grant state clears the prior selection rather than
  allowing a mixed Grant+Revoke selection in one action (Scenario 7 / AC-07).
- Collapsing/expanding a Tool group is a pure client-side toggle — it must
  never itself call `grantAgentSkill`/`revokeAgentSkill`.
- `action`-kind (Built-in) capabilities stay entirely outside the Tool tree
  — no grouping, no icon, no checkbox, no Grant/Revoke button; keep
  rendering their existing plain row exactly as today.
- Read the real current `AgentDetailPanel.tsx` before editing — do not
  apply a stale diff against an assumed shape; this file has had multiple
  sibling stories land additive changes to it.

---

## Tests

<!-- FRONTEND / SCREEN task: verify DOM structure and interaction sequencing
only (jsdom/CDP sees no computed CSS, layout, colour, or :hover — pure
visual polish is not a locked AC and is spot-checked against the prototype
out-of-band, per parent story's own Notes: no prototype exists for this
screen region, so this spot-check is deferred, not blocking). -->

**Manual verification steps:**
1. [REQ-SB-48-US-01-AC-01] Open the Settings tab → Capabilities section for
   an agent that has at least one granted and one not-yet-granted Skill in
   more than one Tool group. Expect exactly 4 Tool group container elements
   (Outlook, Vault, Web, Compass), each expanded by default and showing its
   own Skill rows; expect exactly 11 Skill rows total across the 4 groups
   (3 Outlook + 4 Vault + 1 Web + 3 Compass), no Skill row duplicated across
   groups, no Skill row omitted.
2. [REQ-SB-48-US-01-AC-02] Click a Tool group's collapse toggle. Expect its
   Skill row elements to no longer be present/visible in the DOM. Using a
   `window.fetch` spy (or the CDP-driven native-fetch-interception
   technique already used elsewhere in this project), confirm zero
   `grantAgentSkill`/`revokeAgentSkill` calls fired as a result of the
   collapse click, and confirm (via re-expanding, see step 3, or via the
   underlying `agent.capabilities` state) that no Skill's grant state
   changed.
3. [REQ-SB-48-US-01-AC-03] Click the same Tool group's toggle again to
   expand it. Expect the same Skill rows to reappear, each showing the same
   Grant/Revoke affordance (i.e. the same granted/not-granted state) it had
   immediately before step 2's collapse.
4. [REQ-SB-48-US-01-AC-04] Inspect the DOM: expect every one of the 4 Tool
   group headers to contain a glyph/icon element, and expect every Skill
   row nested under a given Tool group to render that exact same glyph
   character as its own icon (byte-identical per group, distinct across
   the 4 groups).
5. [REQ-SB-48-US-01-AC-05] In an expanded Tool group showing 2+
   not-yet-granted Skill rows, select two of them and trigger the group's
   Grant action. Using a `window.fetch` spy, expect exactly 2
   `POST /agents/{agentId}/skills/{skillId}` calls (one per selected
   Skill id, no batch endpoint hit). Refetch the agent and confirm both
   selected Skills now render as granted, and confirm no unselected Skill
   anywhere in the tree changed state.
6. [REQ-SB-48-US-01-AC-06] In an expanded Tool group showing 2+ granted
   Skill rows, select two of them and trigger the group's Revoke action.
   Using a `window.fetch` spy, expect exactly 2
   `DELETE /agents/{agentId}/skills/{skillId}` calls. Refetch the agent and
   confirm neither selected Skill renders as granted afterward, and confirm
   no unselected Skill anywhere in the tree changed state.
7. [REQ-SB-48-US-01-AC-07] With one or more not-yet-granted rows selected
   in a Tool group (bulk action showing "Grant"), click an already-granted
   row in the same group. Expect the prior selection to clear, the newly-
   clicked granted row to become the sole selected row, and the bulk-action
   control to now read "Revoke".
8. [REQ-SB-48-US-01-AC-08] On one real agent, grant Skill A then Skill B
   one at a time via the existing per-row Grant button (already-shipped
   mechanism, unchanged by this task). On an otherwise-identical second
   agent, select Skill A and Skill B together in the same Tool group and
   grant them via this task's new multi-select action. Fetch both agents'
   final `capabilities` lists and confirm they contain the exact same set
   of granted Skill ids, with no other capability differing between the two
   agents.
9. [REQ-SB-48-US-01-AC-09] For an agent with at least one still-real
   Built-in (`action`-kind) capability, confirm its row renders outside the
   4 Tool group containers — same plain-row/"Built-in"-label/no-button
   shape as before this task — with no Tool icon and no checkbox rendered
   on it. Confirm the Tool tree itself (the 4 group containers combined)
   contains only `kind: "skill"` rows.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Capabilities section renders 4 Tool groups (Outlook/Vault/Web/Compass), expanded by default, covering all 11 Skills with no omission/duplication
- [x] Collapse/expand is a pure display toggle — never fires a grant/revoke call, always preserves grant state
- [x] Every Tool group header and every Skill row under it shows that Tool's fixed icon
- [x] Multi-select within one expanded group supports Grant (2+ not-yet-granted) and Revoke (2+ granted) as N sequential existing single-Skill calls, never a new batch endpoint
- [x] Selecting a row of the opposite grant state clears the prior selection and flips the bulk action
- [x] Multi-select and one-at-a-time mechanisms produce identical resulting granted-Skill sets
- [x] Built-in (action-kind) rows stay outside the tree, ungrouped, with no icon/checkbox/button
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- A new bulk grant/revoke API endpoint.
- Per-individual-Skill icons.
- Grouping/treeing `action`-kind (Built-in) capabilities.
- Cross-Tool-group multi-select (selecting Skills spanning more than one Tool group in one action).
- A self-classifying mechanism for future new Skills' Tool placement.
- `REQ-SB-37-US-02`'s own separate Worker-creation flat Skills multi-select (a different screen).
- Any visual-polish/spacing/hover-animation decision — not a locked AC, spot-checked out-of-band (deferred here since no prototype exists for this region).

---

## Context / Notes

- Depends on `REQ-SB-48-US-01-T01` — the `"tool"` field must exist on both
  `SkillSummary`/`AgentCapability` payloads before this tree can group by
  it; do not start this task against a backend that hasn't shipped T01.
- The parent story's Notes record that no `html-prototype/` screen has ever
  covered this region — there is no approved visual reference to reconcile
  against structurally beyond the locked ACs above. Visual polish is
  explicitly out of scope for this task's locked ACs.
- **Update, 2026-08-14.** `REQ-SB-46-US-01`'s decomposer pass found this
  task's original text left `SkillsTree.tsx`'s standalone existence/
  filename as free coder latitude, while `ADR-039` (written after this
  task) and `REQ-SB-46-US-01-T04` both assume a specific, real,
  mode-parameterized component — a genuine cross-story coordination gap,
  correctly flagged rather than silently guessed past (see the
  `REVIEW-QUEUE.md` entry it filed). Resolved directly, since this story
  is `Ready` but not yet `Done`: `## Files to Modify` above now specifies
  the exact filename and mode-parameterized shape. Build accordingly —
  this removes the coordination risk at the source rather than leaving
  `REQ-SB-46-US-01-T04` to discover and adapt to whatever this task
  happened to ship.

---

## Implementation Log

Read the real current `AgentDetailPanel.tsx` (Capabilities section at lines
449-487, flat `kv-list`, confirmed), `skillsApiClient.ts` (`SkillSummary`
had no `tool` field pre-T01), `agentsApiClient.ts` (`AgentCapability` had
no `tool` field pre-T01), and `Sidebar.tsx`'s `.nav-icon` Unicode-glyph
convention before writing any code — no stale sample trusted. `T01` was
already `Done` in this same session, so `SkillSummary`/`AgentCapability`
both already carry real `"tool"` data server-side.

**Built exactly per the amended `## Files to Modify`'s mandate:**
`src/frontend/src/features/agents-map/SkillsTree.tsx` — new, standalone,
mode-parameterized (`mode: 'manage' | 'select'`, a discriminated union
prop type), never imported/used anywhere but `AgentDetailPanel.tsx` this
task. `mode="manage"` (this task's real scope): 4 fixed Tool groups
(`SKILLS_TREE_TOOL_ORDER`), each with a collapse toggle (pure client
`useState<Set<string>>`, never calls a grant/revoke prop), a fixed Unicode
icon per Tool (✉ Outlook, 🗄 Vault, 🌐 Web, 🧭 Compass — inherited by every
Skill row under it), a per-row checkbox + the EXISTING unchanged per-row
Grant/Revoke button (`onGrantSkill`/`onRevokeSkill` props, wired straight
to `AgentDetailPanel.tsx`'s pre-existing, byte-unchanged
`handleGrantSkill`/`handleRevokeSkill`), and a same-grant-state-only
multi-select (`ManageSelection { tool, granted, ids }`) driving one bulk
action button that composes N sequential calls via new
`onGrantSkills`/`onRevokeSkills` props (`handleBulkGrantSkills`/
`handleBulkRevokeSkills`, new functions in `AgentDetailPanel.tsx`, each a
`for` loop of the exact same single-Skill `grantAgentSkill`/
`revokeAgentSkill` calls T01's own catalog reads compose against, followed
by ONE combined `fetchAgent` refetch — never a batch endpoint).
`mode="select"` is built minimally, literally per this task's own `##
Files to Modify` prose (checkboxes + `selectedIds`/`onChange`, no API
call) as the documented seam `REQ-SB-46-US-01-T04`/`SPRINT-043` depends
on — explicitly commented as provisional, not that story's own final
answer. `AgentDetailPanel.tsx`'s Capabilities section now renders the
existing action-kind `kv-list` (filtered to `kind === 'action'` only) plus
`<SkillsTree mode="manage" .../>` fed by a new `buildSkillsTreeItems`
helper (all 11 catalog Skills, each marked `granted` from
`agent.capabilities`).

`npx tsc -p . --noEmit` (project's own bundled Node, `tools/node/`) — zero
type errors, confirmed after every edit.

**Live verification** — real backend (`uvicorn --port 8001`) + real Vite
dev server (`VITE_API_BASE_URL=http://127.0.0.1:8001`, port 5173, inside
`CORSMiddleware`'s allow-list) + a real headless-Edge/CDP session (no
Playwright/Puppeteer in this repo — this project's own established
from-scratch Node `fetch`+`WebSocket` CDP driver, `SPRINT-033`/`036`/`038`
precedent), driving the real, unmodified running app end-to-end. A
`window.fetch` spy confirmed exact call counts/URLs/methods throughout.

**[REQ-SB-48-US-01-AC-01] PASS.** Opened `email-capture`'s Settings tab:
exactly 4 Tool group containers (Outlook/Vault/Web/Compass), each expanded
by default, 3+4+1+3 = 11 Skill rows total, no duplication/omission
(`skills-tree-row-*` `data-testid`s enumerated and diffed against the full
11-id catalog).

**[REQ-SB-48-US-01-AC-02/AC-03] PASS.** Recorded Outlook group's 3 rows
(all granted, "Revoke" buttons). Clicked the collapse toggle: rows no
longer present in the DOM; the `window.fetch` spy recorded ZERO calls
during the collapse click. Clicked expand again: the identical 3 rows
reappeared with byte-identical grant state (`JSON.stringify` before/after
equal).

**[REQ-SB-48-US-01-AC-04] PASS.** Every one of the 4 group headers' and
every nested row's `.skills-tree-icon` text was read directly: all 3
Outlook elements render `✉`, all 5 Vault elements (1 header + 4 rows)
render `🗄`, all 2 Web elements render `🌐`, all 4 Compass elements render
`🧭` — byte-identical within a Tool, distinct across Tools.

**[REQ-SB-48-US-01-AC-05] PASS.** `email-capture`'s Vault group (4
not-yet-granted rows): selected `ask_question` + `view_channel_status` via
checkbox, clicked the bulk action ("Grant (2)"). Fetch spy recorded
EXACTLY 2 calls: `POST /agents/email-capture/skills/ask_question`, `POST
.../view_channel_status` (plus one ordinary `GET` refetch) — no batch
endpoint. Refetch confirmed both now granted; `rebuild_person_note`/
`write-to-vault-draft` (unselected, same group) and every other group
unaffected.

**[REQ-SB-48-US-01-AC-06] PASS — with one real, disclosed, out-of-scope
finding along the way (see below).** First attempt selected 2
already-granted Outlook rows (`view_last_run`, `run_capture_now`) —
DELETE calls fired with the right URLs/count, but a durability re-check
found both skills silently reappeared as granted moments later. Root-
caused via a UI-free, direct `skill_registry.revoke_skill_access(...)`
Python-shell call (zero frontend involvement) to a genuine, PRE-EXISTING
bug in `skill_registry._load_state`/`_MIGRATION_GRANT_SEED`
(`REQ-SB-39-US-02`/`SPRINT-031`, unrelated to this task, and a function
this task's own `## Files to Modify` does not include) — it re-applies
the ENTIRE migration seed on every state read, so a revoke of any of the
7 migration-seeded Skill/agent pairs never actually sticks, regardless of
whether the revoke came via this task's own new multi-select, the
pre-existing per-row button, or a raw Python call. **Captured as `BUGS.md`
→ `BUG-013` (`Open`) and `ESCALATIONS.md` → `ESC-035`; not fixed here (out
of scope for both `T01`/`T02`).** Re-verified `AC-06` honestly using a
Skill/agent pair NOT in `_MIGRATION_GRANT_SEED` instead (`email-capture`'s
Vault group, which has no migration seed at all): granted `ask_question` +
`view_channel_status` via multi-select (reusing `AC-05`'s own mechanism),
then multi-select-revoked both — fetch spy recorded EXACTLY 2 `DELETE`
calls, both rows immediately AND durably (+1s recheck) showed
not-granted, matching the locked AC's own guarantee.

**[REQ-SB-48-US-01-AC-07] PASS.** On `people-producer` (Vault group: 1
granted `rebuild_person_note`, 3 not-yet-granted), selected 2 not-yet-
granted rows (bulk bar read "Grant (2)"), then clicked the granted
`rebuild_person_note` row's checkbox. Bulk bar flipped to "Revoke (1)"
with only `rebuild_person_note` selected (prior 2-item selection cleared)
— confirmed the `window.fetch` spy recorded ZERO calls during this
selection-only interaction (no accidental grant/revoke fired).

**[REQ-48-US-01-AC-08] PASS.** `meeting-capture` (per-row, one-at-a-time,
UNCHANGED existing mechanism): clicked `ask_question`'s then
`view_channel_status`'s own per-row Grant button — 2 separate `POST`
calls, each followed by its own refetch (existing behavior, confirmed
unmodified). `todo-capture` (this task's new multi-select): selected both
in the Vault group, one bulk Grant — exactly 2 `POST` calls, one combined
refetch. Independent `GET` calls to both agents afterward: capability-id
sets byte-identical
(`["ask_question","pause_schedule","run_capture_now","view_channel_status","view_last_run"]`
for both, sorted) — no other capability differed. Both agents then
reverted to their exact original 3-Skill Outlook-only state (per-row
Revoke on `meeting-capture`, multi-select Revoke on `todo-capture`),
independently reconfirmed via `GET` — both back to
`["pause_schedule","run_capture_now","view_last_run"]`.

**[REQ-SB-48-US-01-AC-09] PASS.** No real, current agent has any
still-real Built-in (action-kind) capability today (same finding as
`T01`'s own `AC-09` — every one migrated into `skill_tools.SKILLS` in
`SPRINT-031`). Verified structurally via a scoped `window.fetch` response
override on `GET /agents/people-producer` (injects one synthetic
action-kind capability into the real response, reverted after the check)
— confirmed the synthetic Built-in row rendered in the existing plain
`.kv-row`/"Built-in"-label shape, structurally OUTSIDE
`[data-testid="skills-tree"]` (`.contains()` check `false`), with no
`.skills-tree-icon` and no checkbox on it; confirmed
`[data-testid="skills-tree"]` itself never contained a row for the
synthetic id — the tree renders only `kind: "skill"` rows, by
construction (`buildSkillsTreeItems` only ever reads `skillCatalog`, never
`agent.capabilities`'s action-kind rows).

**Visual spot-check (screenshot, no approved prototype exists for this
region per the story's own Notes — not a locked AC):** captured a real
1400×1000 screenshot of `email-capture`'s Settings tab via
`Page.captureScreenshot`. All 4 Tool groups, icons, checkboxes, and
Grant/Revoke buttons render and are structurally correct; spacing/hover
polish is unstyled (no new CSS file in `## Files to Modify`, and the
story's own Notes explicitly defer visual polish as out-of-band/non-AC)
— disclosed here, not silently left unexamined.

**Real state left clean.** Every agent touched during live verification
(`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`)
was independently reconfirmed via a direct `GET` at the end of this
session to match its exact pre-verification capability set byte-for-byte
— zero net state change to the real running app.

**Scope-internal judgement calls (for human spot-check, per this task's
own `gate: flagged`):**
1. `mode="select"` was given a minimal, real, working implementation
   (not a no-op stub) — literally matching the task's own prose ("multi-
   select checkboxes, `selectedIds`/`onChange` props, no API call"), on
   the reasoning that a genuinely non-functional placeholder would be a
   weaker "extractable" seam for `REQ-SB-46-US-01-T04` than a small,
   explicitly-labeled-provisional working implementation. `T04` remains
   free to change this branch's own selection semantics.
2. `BUG-013` (see `AC-06` above) — a real, disclosed, out-of-scope
   finding, not fixed as part of this task; recommended for `/triage`.

gate: flagged 2026-08-14 — MUST-FLAG trigger 6 analog (a locked AC's own
straightforward verification path hit a genuine external/pre-existing
defect, resolved via a disclosed, honest technique substitution, not by
weakening the AC) plus the 2 scope-internal judgement calls above, both
logged for human spot-check per the coder's own convention. No
`ESCALATIONS.md` new-dependency/shared-interface/ADR-deviation trigger
fired — `ESC-035` records the bug finding itself, not a scope dispute.
