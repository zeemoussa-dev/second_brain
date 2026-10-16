---
id: REQ-SB-95-US-02-T06
title: Actions catalogue screen + Action editor, Settings card, route, and the sixth Artifacts tab
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T03, REQ-SB-95-US-02-T04, REQ-SB-95-US-02-T05]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T06 — Actions Catalogue Screen + Action Editor

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give the operator the one screen the catalogue is for: a list of Actions with
their broken/resolving state, and an editor for one Action — plus the Settings
card, the route, and the sixth kind tab on the Artifacts page.

---

## Starting State → End State

**Before / Inputs:**

- `src/frontend/src/pages/SettingsPage.tsx` holds a `SETTINGS_SECTIONS` const
  array rendered as an icon-card grid (`card settings-card`), ten entries today.
- `src/frontend/src/App.tsx` declares one flat `<Route path="/settings/...">`
  per settings page.
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` holds `KIND_NAV` (five
  entries: template / skill / agent / pipeline / index) plus a `KIND_ORDER`-built
  per-kind record, and renders `.item-row` / `.item-row-main` /
  `.item-row-title` / `.item-row-meta` rows with `data-testid` attributes.
- The frontend has **no test runner** (it does not declare `vitest`), so this
  task verifies structurally in a real browser, not with a unit test runner.

**After / Outputs:**

- `src/frontend/src/pages/SettingsActionsPage.tsx` — the catalogue list
  (`.item-list` / `.item-row` family) showing per Action: id, description,
  implementation kind, the contributing plugin id where there is one, and a
  broken badge naming what no longer resolves; plus the one-Action editor
  (`.input` / `.btn` / `Save changes` conventions) with typed-input rows each
  carrying a required toggle, an `allowed_callers` field, a
  `needs_confirmation` toggle and a single implementation picker that allows
  exactly one of skill / http / ui.
- `src/frontend/src/features/settings/actionsApiClient.ts` — the API client,
  same shape as the existing `artifactsApiClient.ts`.
- One more `SETTINGS_SECTIONS` entry and one more `<Route>`.
- `SettingsArtifactsPage.tsx` gains the sixth `KIND_NAV` entry (`action`).
- A refused save renders the backend's own message naming the cause; the screen
  never invents its own wording for it.

---

## Files to Modify

- `src/frontend/src/pages/SettingsActionsPage.tsx` (new)
- `src/frontend/src/features/settings/actionsApiClient.ts` (new)
- `src/frontend/src/pages/SettingsPage.tsx` (one `SETTINGS_SECTIONS` entry)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (sixth `KIND_NAV` entry + the `ArtifactKind` union)
- `src/frontend/src/features/settings/artifactsApiClient.ts` (the `ArtifactKind` type, if the union lives there)

---

## Constraints

- Inherits from parent story.
- **Functional-first on already-approved conventions** (story Notes → Prototype
  parity): reuse the live `.item-list`/`.item-row` and `.input`/`Save changes`
  families; introduce no new visual system. Visual polish is an out-of-band
  spot-check, never a locked AC.
- Every assertion below is on **DOM structure**, not on computed CSS, colour or
  hover state.
- The implementation picker enforces exactly one choice in the UI, but the
  backend refusal is still rendered when it fires — the screen is not the
  enforcement point.
- Plugin-contributed Actions render read-only (no edit/delete controls), matching
  the backend refusal from `T05`.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP screenshot and DOM reads are this project's established
technique — read the DOM back at least ~500ms after any dispatched state
change):

1. `[REQ-SB-95-US-02-AC-01]` Open `/settings` and confirm an Actions card is
   present in the `settings-grid`; click it and confirm it routes to the Actions
   page. Create an Action through the editor with two typed inputs (one
   required, one optional), an `allowed_callers` value and the confirmation
   toggle on; save; confirm a new `.item-row` renders with its id, description
   and implementation kind, and that reopening it shows exactly the inputs,
   required flags, callers and confirmation setting that were saved.
2. `[REQ-SB-95-US-02-AC-02]` Save an Action naming an implementation that does
   not resolve; confirm an error region renders carrying the backend's own
   message naming what did not resolve, and that no new `.item-row` appears.
   Correct the implementation, save, confirm the row appears.
3. `[REQ-SB-95-US-02-AC-03]` Attempt to save with no implementation selected and
   confirm the save is refused with the exactly-one message rendered; confirm
   the picker structurally cannot hold two implementations at once (assert on
   the DOM that selecting a second clears the first).
4. `[REQ-SB-95-US-02-AC-04]` Open `/settings/artifacts`; confirm an
   `[data-testid="artifacts-tab-action"]` nav item is present beside the five
   existing tabs, that selecting it lists the real Actions as `.item-row`
   entries, and that each pre-existing tab still lists exactly what it listed
   before.
5. `[REQ-SB-95-US-02-AC-06]` With a plugin installed that registers an Action,
   confirm its row renders in the same list, shows the contributing plugin id,
   and exposes no edit/delete control.
6. `[REQ-SB-95-US-02-AC-07]` Break a saved Action's implementation (undeploy the
   Skill it names), reload the catalogue, and confirm the row renders a broken
   indicator naming what no longer resolves — without anything having called the
   Action.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Actions catalogue page + one-Action editor on existing approved conventions
- [ ] Settings card and route added; sixth `KIND_NAV` tab on the Artifacts page
- [ ] Backend refusal messages rendered verbatim
- [ ] Broken state and plugin attribution visible in the list
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Workflows screen and the seventh Artifacts tab — `REQ-SB-95-US-04-T07`.
- Any confirmation / call surface — `REQ-SB-95-US-03`.
- Visual polish beyond reusing the approved families (out-of-band spot-check).

---

## Context / Notes

`architecture.md` → **§Action Catalogue — the Sixth Artifact Kind**, final
bullet: a new Settings page on the already-approved `.item-list`/`.item-row` +
`.input`/`Save changes` families plus one more card in the live
`SETTINGS_SECTIONS` grid. The story's Notes record the operator's own
2026-08-31 functional-first precedent that makes this the right order.

---

## Implementation Log

_(Filled in by the coder.)_
