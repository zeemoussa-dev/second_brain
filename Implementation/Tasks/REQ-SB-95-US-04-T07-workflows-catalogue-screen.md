---
id: REQ-SB-95-US-04-T07
title: Workflows catalogue screen + ordered-step editor, Settings card, route, and the seventh Artifacts tab
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T03, REQ-SB-95-US-04-T04, REQ-SB-95-US-02-T06]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-04-T07 — Workflows Catalogue Screen + Ordered-Step Editor

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Let the operator actually document a Workflow: a catalogue list, an ordered-step
editor whose step picker offers only real catalogued Actions, the Settings card
and route, and the seventh kind tab on the Artifacts page.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-02-T06` has added the Actions page, its Settings card, its route
  and the sixth `KIND_NAV` tab — re-read those real files; this task extends the
  same three shared files.
- The frontend declares no test runner, so verification is structural, in a real
  browser.

**After / Outputs:**

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` — the Workflows catalogue
  (`.item-list`/`.item-row` family) and the one-Workflow editor: the kind of
  request it handles, an ordered list of step rows each picking a real
  catalogued Action from a fetched list, a per-step confirmation toggle, plain
  move-up/move-down reordering controls (no bespoke drag-and-drop), and the
  report-back definition.
- `src/frontend/src/features/settings/workflowsApiClient.ts`.
- One more `SETTINGS_SECTIONS` entry and one more `<Route>`.
- `SettingsArtifactsPage.tsx` gains the seventh `KIND_NAV` entry (`workflow`).
- A refused save renders the backend's own message naming the step and the
  unknown action id; a blocked Action delete renders the referencing Workflows.

---

## Files to Modify

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` (new)
- `src/frontend/src/features/settings/workflowsApiClient.ts` (new)
- `src/frontend/src/pages/SettingsPage.tsx` (one `SETTINGS_SECTIONS` entry)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (seventh `KIND_NAV` entry + the `ArtifactKind` union)
- `src/frontend/src/pages/SettingsActionsPage.tsx` (render the blocked-delete message naming referencing Workflows)

---

## Constraints

- Inherits from parent story.
- **Functional-first on already-approved conventions** (story Notes → Prototype
  parity): reordering is built plainly with existing controls, not a bespoke
  drag-and-drop system. Visual polish is an out-of-band spot-check, never a
  locked AC.
- Every assertion below is on **DOM structure**, not computed CSS or layout.
- The step picker is populated from the live Actions API — never a hardcoded
  list — so the invalid state is hard to reach; the backend refusal is still
  rendered when it fires.
- No change to how Pipelines render anywhere.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP, reading the DOM back at least ~500ms after any dispatched
state change):

1. `[REQ-SB-95-US-04-AC-01]` Open `/settings`, confirm a Workflows card is
   present in the `settings-grid` and routes to the Workflows page. Create a
   Workflow with a request kind and three steps (the second marked as needing
   confirmation); save; confirm the row renders, and that reopening it shows the
   same three steps in the same order with the same confirmation flags and the
   same report definition.
2. `[REQ-SB-95-US-04-AC-01]` Reorder two steps with the move controls, save,
   reopen; confirm the new order persisted and no step was dropped or
   duplicated.
3. `[REQ-SB-95-US-04-AC-02]` Confirm the step picker's options are exactly the
   real catalogued Actions fetched from the API (assert the option values
   against `GET /actions`), so an unknown action id is not reachable through the
   screen. Then force a refusal (e.g. delete an Action in another tab and save a
   stale step) and confirm the backend's message naming the step and the unknown
   id renders.
4. `[REQ-SB-95-US-04-AC-04]` Open `/settings/artifacts`; confirm an
   `[data-testid="artifacts-tab-workflow"]` nav item is present beside the six
   existing tabs, that selecting it lists the real Workflows as `.item-row`
   entries, and that every pre-existing tab still lists exactly what it listed
   before.
5. `[REQ-SB-95-US-04-AC-06]` On the Actions page, attempt to delete an Action a
   Workflow references; confirm the screen renders the refusal naming the
   referencing Workflow(s) and that the Action row is still present afterwards.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Workflows catalogue page + ordered-step editor on existing approved conventions
- [ ] Settings card and route added; seventh `KIND_NAV` tab on the Artifacts page
- [ ] Step picker populated from the live Actions API
- [ ] Backend refusals (bad step, blocked Action delete) rendered verbatim
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- A screen over workflow runs — not in this story.
- Drag-and-drop reordering, visual polish (out-of-band spot-check).

---

## Context / Notes

The story's Affected Screens and its Prototype-parity Notes are authoritative,
including the operator's own 2026-08-31 functional-first precedent that makes
plain move controls the right first build for reordering.

---

## Implementation Log

_(Filled in by the coder.)_
