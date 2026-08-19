---
id: REQ-SB-66-US-01-T05
title: AgentDetailPanel.tsx Settings tab — Prompt + Guardrails kv-list rows for every real Agent Type
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-66-US-01-T04]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T05 — `AgentDetailPanel.tsx` Prompt + Guardrails rows

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Add two new editable `kv-list` rows — Prompt and Guardrails — to
`AgentDetailPanel.tsx`'s existing Settings tab, shown unconditionally for every
real Agent Type (Worker/Producer/Expert), on the SAME existing tab, reusing the
already-established free-text-input-with-onBlur-commit UX pattern the Keywords/
Vault-scope rows already use — never a new tab, never a new screen. `/design` is
explicitly skipped for this story (operator-directed) — build directly against the
existing `kv-list` visual language.

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetailPanel.tsx`'s Settings tab (`activeTab === 'settings'`) already
  renders a `kv-list` with Section/Provider/Working mode/Background Agent/Keywords/
  Vault scope rows, the last two using a free-text `<input>` bound to a local draft
  state (`keywordsDraft`/`scopeDraft`), committed on `onBlur` via
  `handleKeywordsCommit`/`handleScopeCommit`, which call `updateAgentAssignment`
  and re-sync the draft from the response.
- `agentsApiClient.ts`'s `AgentDetail` interface does not yet carry `prompt`/
  `guardrails`; `T04` has landed both fields on the real `GET`/`PATCH
  /agents/{agent_id}` endpoint.
- `AgentDetailPanel.tsx`'s own Overview tab already renders an UNRELATED, hardcoded,
  non-editable `GUARDRAILS_STATEMENT` kv-row (`REQ-SB-33-US-01`) — left
  byte-for-byte unchanged by this task; this task's own new Guardrails row is a
  DIFFERENT field, in the Settings tab, editable and persisted.

**After / Outputs:**
- `agentsApiClient.ts`'s `AgentDetail` interface gains `prompt: string | null` and
  `guardrails: string`; `updateAgentAssignment`'s own body type gains optional
  `prompt?: string` / `guardrails?: string`.
- `AgentDetailPanel.tsx`'s Settings tab gains a Prompt row (a free-text `<input>` or
  `<textarea>` — coder's choice, given Prompt text is typically longer than a
  Keywords/Vault-scope entry; either is a valid `kv-list` row) and a Guardrails row
  (same input shape), each bound to its own local draft state, committed on
  `onBlur`, mirroring the Keywords/Vault-scope rows' own exact commit pattern —
  shown unconditionally for every real Agent Type, on the SAME Settings tab.
- Saving a new Prompt/Guardrails value persists across a reload (re-fetching
  `GET /agents/{agent_id}` shows the saved value).

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts`:
  - `AgentDetail` interface gains `prompt: string | null;` and `guardrails:
    string;`.
  - `updateAgentAssignment`'s body parameter type gains `prompt?: string;` and
    `guardrails?: string;`.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`:
  - Add `promptDraft`/`guardrailsDraft` local state (mirrors `keywordsDraft`/
    `scopeDraft`), reset on agent switch (the existing `useEffect` that resets
    `keywordsDraft`/`scopeDraft` on `[agentId]` change), and synced from
    `fetchAgent(agentId)`'s response the same way `keywordsDraft`/`scopeDraft`
    already are.
  - Add `handlePromptCommit`/`handleGuardrailsCommit` handlers, mirroring
    `handleKeywordsCommit`/`handleScopeCommit`'s own exact shape (call
    `updateAgentAssignment(agentId, { prompt: promptDraft })` /
    `{ guardrails: guardrailsDraft }`, `setAgent(updated)`, re-sync the draft from
    the response).
  - Add the two new `kv-row`s inside the existing Settings tab's `kv-list`
    (alongside the existing Keywords/Vault-scope rows) — unconditional on
    `agent.type`, matching the requirement's own "Prompt + Guardrails show for
    every Type" bar.

---

## Constraints

- Inherits from parent story: `/design` is explicitly skipped (operator-directed) —
  build directly against the existing `kv-list` visual language; no new visual
  affordance/component library entry.
- Prompt/Guardrails rows are shown UNCONDITIONALLY for every real Agent Type
  (Worker/Producer/Expert) — never gated behind `agent.type === 'expert'` or any
  other per-Type conditional (unlike Domain-for-Expert/Purpose-for-Producer).
- These two new rows land on the SAME existing Settings tab — never a new tab entry
  in `TABS`, never a new top-level screen.
- This task does NOT touch the Overview tab's own existing, hardcoded
  `GUARDRAILS_STATEMENT` row — that row (and its `data-testid="overview-
  guardrails"`) is left byte-for-byte unchanged; this task's new Guardrails row
  gets its own, different `data-testid` in the Settings tab.
- This task touches `AgentDetailPanel.tsx` for real Agents only — a Job's own
  Settings-only view is a genuinely SEPARATE component, `T07`'s own scope (per
  `ADR-044`); this task does not add any Job-awareness to `AgentDetailPanel.tsx`.
- Commit-on-blur, whole-value replace — mirrors Keywords/Vault-scope's own exact
  UX, no new interaction pattern.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-66-US-01-AC-05]** Open a real Agent's Settings tab for a Worker, a
   Producer, and an Expert (3 separate agents) — confirm a Guardrails row is
   present and shows the currently stored value (empty by default) for all 3.
   Type a new Guardrails value into one agent's own row, blur the field, reload the
   page, re-open that same agent's Settings tab — confirm the saved value persists
   across the reload. Confirm NO part of this build wires the stored value into any
   enforcement behavior (no new validation/blocking logic anywhere in this task's
   own diff).
2. **[REQ-SB-66-US-01-AC-06]** Confirm the Prompt and Guardrails rows render on the
   SAME Settings tab as Section/Provider/Working mode/Keywords/Vault scope — no new
   tab button appears in the `side-panel-tabs` list, and the Overview/Chat/History/
   Schedule/Visual tabs are all still present and unaffected for a real Agent.
   Confirm the existing per-Type convention (e.g. Expert's own `'gaps'` tab) is
   unaffected by this task's changes.
3. Regression: open the SAME real Agent's Overview tab — confirm the pre-existing
   `GUARDRAILS_STATEMENT` row (`data-testid="overview-guardrails"`) still shows its
   own original, hardcoded, non-editable sentence, byte-for-byte unchanged, and is
   visually/structurally distinct from this task's new Settings-tab Guardrails row.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `AgentDetail`/`updateAgentAssignment` gain `prompt`/`guardrails` typing in
      `agentsApiClient.ts`
- [x] Prompt + Guardrails rows render unconditionally in the Settings tab for every
      real Agent Type, committed on blur, mirroring Keywords/Vault-scope's own
      exact UX
- [x] A saved value persists across a reload
- [x] The Overview tab's pre-existing `GUARDRAILS_STATEMENT` row is byte-for-byte
      unchanged
- [x] No new tab, no new screen, no enforcement behavior wired to the stored value
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Implementation Log

**Built as specced, no deviations.** Read the REAL current `AgentDetailPanel.tsx`
and `agentsApiClient.ts` fresh before editing (not assumed from this task's own
illustrative prose): `AgentDetail`/`updateAgentAssignment`'s body type matched the
task's prose one-for-one, and the Settings tab's Keywords/Vault-scope kv-rows'
exact free-text-input/local-draft-state/`onBlur`-commit/re-sync-from-response shape
was confirmed by direct reading before mirroring it for Prompt/Guardrails.

- `agentsApiClient.ts`: `AgentDetail` gained `prompt: string | null;` and
  `guardrails: string;` (after `color`); `updateAgentAssignment`'s body type gained
  optional `prompt?: string;` / `guardrails?: string;` (after `color`).
- `AgentDetailPanel.tsx`: new `promptDraft`/`guardrailsDraft` local state, reset on
  agent switch in the same `useEffect` that resets `keywordsDraft`/`scopeDraft`,
  synced from `fetchAgent(agentId)`'s response (`detail.prompt ?? ''` /
  `detail.guardrails`) alongside `keywordsDraft`/`scopeDraft`'s own sync. New
  `handlePromptCommit`/`handleGuardrailsCommit`, mirroring
  `handleKeywordsCommit`/`handleScopeCommit`'s exact shape (whole-value replace, no
  comma-splitting — Prompt/Guardrails are free text, not lists). Two new
  unconditional `kv-row`s added to the Settings tab's `kv-list`, immediately after
  the existing Vault scope row: Prompt as a `<textarea className="input kv-select">`
  (coder's choice per the task's own "coder's choice" framing — Prompt text is
  typically longer than a Keywords/Vault-scope entry), Guardrails as a plain
  `<input type="text" className="input kv-select">` (mirrors Keywords/Vault-scope's
  own input shape verbatim). Each carries its own `data-testid`
  (`settings-prompt-input` / `settings-guardrails-input`), distinct from the
  Overview tab's pre-existing `data-testid="overview-guardrails"` row, which was not
  touched.

**Verification — no real browser/screenshot tool was available in this coding
session's own tool-set** (only Read/Glob/Grep/Edit/Write/Bash/PowerShell — no
Layer-1 visual harness exists in this repo yet, confirmed by direct reading of
`src/frontend/package.json`'s own `scripts` block: `dev`/`build`/`lint`/`preview`
only, no `visual` script). Verification instead combined (a) direct reading of the
final rendered JSX to confirm the two new rows are wired identically to the already-
approved Keywords/Vault-scope rows, (b) a clean `npx tsc --noEmit` pass, (c) a live
Vite HMR fetch of the edited module (`200`, no compile-error overlay), and (d) the
exact real HTTP round trip the `onBlur` handlers themselves perform, run directly
against the real running backend (`http://127.0.0.1:8001`) with real agent ids —
this is a genuine environment-gap disclosure, not a silently-skipped verification
step; the underlying user-observable behavior (render, edit, blur-commit, reload-
persist) was verified as thoroughly as the available tools allow.

1. **[REQ-SB-66-US-01-AC-05] PASS.** `GET /agents/{id}` for a Worker
   (`todo-capture`), a Producer (`people-producer`), and an Expert (`vault-qa`)
   each returned `"guardrails": ""` (and `"prompt": null`) — the Guardrails row's
   default-empty state is present for all 3 real Agent Types. `PATCH
   /agents/todo-capture` with `{"guardrails": "Never auto-send without human
   review."}` (the exact call `handleGuardrailsCommit` makes on blur) returned the
   new value immediately; a subsequent `GET /agents/todo-capture` (simulating a
   page reload re-opening that agent's Settings tab) confirmed it persisted,
   unchanged. Confirmed no enforcement/validation logic was added anywhere in this
   task's own diff — the two new handlers only call `updateAgentAssignment`/
   `setAgent`, nothing else.
2. **[REQ-SB-66-US-01-AC-06] PASS.** Direct reading confirms the two new rows sit
   inside the SAME Settings-tab `kv-list` (`activeTab === 'settings'`) as
   Section/Provider/Working mode/Keywords/Vault scope — no new entry was added to
   the `TABS` constant or `side-panel-tabs` list; Overview/Chat/History/Schedule/
   Visual all remain exactly as before, and the Expert-only `'gaps'` tab's own
   `agent.type === 'expert'` conditional is untouched. `PATCH
   /agents/people-producer` with `{"prompt": "You are the People Notes producer.
   Draft concise contact summaries."}` (the exact call `handlePromptCommit` makes
   on blur) persisted across a re-`GET`; a follow-up `GET /agents/todo-capture`
   confirmed its own previously-saved Guardrails value was completely unchanged by
   the `people-producer` edit (no cross-id bleed) — same underlying mechanism
   `AC-05`/`AC-06` both rely on.
3. **Regression, PASS.** Direct reading of the Overview tab's
   `data-testid="overview-guardrails"` row confirms `GUARDRAILS_STATEMENT`'s own
   sentence text is byte-for-byte identical to the pre-existing file (`"Replies are
   grounded in what this agent's own tools actually find in the vault — it
   honestly says it doesn't know rather than guessing."`) — this task's `Edit`
   calls never touched that row; `git diff` shows the Overview tab's own JSX block
   is untouched by this task's own changes.

**Assumption logged for human spot-check (scope-internal judgement call, not an
escalation):** the real PATCH calls above left non-default Prompt/Guardrails
values stored against `todo-capture`/`people-producer` in the real vault's
`.second-brain/agent_prompts.json`. Left in place rather than reverted, mirroring
`T04`'s own established precedent (verification run directly against the real
configured vault, no scratch-vault isolation). Harmless for this story's own real
scope — neither id is one of `T02`/`T03`'s four owning call sites this pass
wires a runtime override into.

- MEMORY.md — no new decision/pattern/constraint. This task is a mechanical,
  same-shape repetition of the already-established Keywords/Vault-scope
  free-text/`onBlur`-commit `kv-row` pattern (already documented multiple times in
  `MEMORY.md`, e.g. the Vault-scope-row and Keywords-row entries), not a new UX
  pattern.
- CHANGELOG.md — entry appended.

---

## Out of Scope

- Any Job-Settings surface, or any Job-awareness in `AgentDetailPanel.tsx` — `T07`.
- Any backend change — `T04` (already `Ready`, this task's own dependency).
- A `/design` pass — explicitly, deliberately skipped for this whole story.
- Any change to the Overview tab's own `GUARDRAILS_STATEMENT` row.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see
ADR-044)" → "Settings-tab extension for real Agents" bullet ("the only piece of this
story that touches `AgentDetailPanel.tsx` itself").

Compose around the REAL current `AgentDetailPanel.tsx`/`agentsApiClient.ts` as they
actually exist today — do not assume exact variable/state names from this task's
own illustrative prose without reading the real files first (this codebase's own
established "compose around the real current file" precedent, `Learnings.md`).

**No `/design` pass, operator-directed, 2026-08-16** — "no more designer we will do
it later build the needed ui we will fix it later." Build directly against the
existing Settings `kv-list` visual language; visual polish is a non-blocking,
disclosed follow-up, not a locked AC.
