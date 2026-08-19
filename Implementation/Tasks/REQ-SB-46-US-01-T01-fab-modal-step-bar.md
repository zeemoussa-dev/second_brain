---
id: REQ-SB-46-US-01-T01
title: Agents Map FAB + popup modal shell + visual step-bar container; retire Settings entry point
parent_story: REQ-SB-46-US-01
requirement_id: REQ-SB-46
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01-T01 — Agents Map FAB + popup modal shell + visual step-bar container; retire Settings entry point

## Parent Story

- Story: [[REQ-SB-46-US-01]] — `../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-46 *Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar*

---

## Objective

Add a bottom-right floating action button to the Agents Map that opens a new,
centered popup modal with a 4-step visual progress bar (structural shell
only — no per-step fields yet), and retire the Settings-page `+ Create
agent` entry point entirely.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/pages/AgentsMapPage.tsx` (read directly, confirmed
  current) mounts `AgentsMapCanvas` and `AgentDetailPanel` only — no
  Create Agent affordance anywhere on this page today.
- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (read
  directly, confirmed current) is one file containing a `step: 'type' |
  'expert' | 'worker' | 'producer'` state machine and all three types'
  full forms + submit handlers, today only ever mounted from
  `CreateAgentCard.tsx`.
- `src/frontend/src/features/settings/CreateAgentCard.tsx` (read directly,
  confirmed current) renders a `<details data-testid="create-agent-
  affordance">` disclosure containing `<CreateAgentWizard onCreated={...}
  />`, mounted on `SettingsPage.tsx`.
- `src/frontend/src/styles/agents-map.css` already defines
  `.map-overflow-marker` (circular dashed-border/tinted-glow badge,
  `--color-accent`-based) and `.hub-node`/`.agent-node`'s shared
  `color-mix(...)` glow idiom — the FAB's visual language reuses this, not
  a new button style. `.side-panel-overlay`/`.side-panel` exist for the
  agent-detail panel (edge-anchored slide-in) — explicitly NOT reused for
  this new centered popup modal (`ADR-039` point 1; Scenario 2 requires
  visual distinctness from the side panel).

**After / Outputs:**
- `AgentsMapPage.tsx` renders a new `.map-fab` button, fixed
  `bottom-right`, `data-testid="map-fab-create-agent"`. Clicking it sets a
  local `isWizardOpen` boolean to `true`, conditionally mounting the new
  modal (`{isWizardOpen && <CreateAgentWizardModal ... />}` — unmount-on-
  close is the mechanism that makes Scenario 11's draft-discard true by
  construction for whatever step state later tasks add, mirroring
  `AgentDetailPanel`'s own `{selectedAgentId && <AgentDetailPanel .../>}`
  pattern already in this file).
- `CreateAgentWizard.tsx` renamed to
  `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx`. Its
  existing internal form logic (all three types' state/handlers) is
  preserved unchanged in this task — do not delete or rewrite it yet,
  later tasks (`T02`-`T05`) regroup it into the 4-step structure. This
  task's own job is ONLY the new outer shell: a `data-testid="wizard-
  modal-overlay"` backdrop, a `data-testid="wizard-modal"` centered panel,
  and a `data-testid="wizard-step-bar"` containing 4 elements
  (`data-testid="wizard-step-1"` … `wizard-step-4"`), the current step
  visually/structurally marked (e.g. `aria-current="step"` plus a
  `.wizard-step--current` class) via a new `currentStep: 1 | 2 | 3 | 4`
  state, defaulting to `1`. Wrap the modal's existing (still-unregrouped)
  content inside this new shell so the file continues to render/compile;
  `T02` is the task that actually starts replacing that content
  step-by-step.
- `CreateAgentWizardModal` accepts an `onClose: () => void` prop (wired by
  `AgentsMapPage` to set `isWizardOpen` back to `false`) and an
  `onCreated: (agent: AgentDetail) => void` prop (wired by `AgentsMapPage`
  to close the modal and re-run the same `fetchAgentList`/`layoutAgents`
  refresh sequence its own mount `useEffect` already runs, so a newly
  created agent appears on the map immediately — `T05` is what actually
  invokes this prop on real submission, once Step 4 exists; this task only
  wires the prop through).
- A `data-testid="wizard-modal-close"` close control (e.g. an `×` button
  or backdrop click) calls `onClose` — no confirmation dialog, matching
  Scenario 11's "closes... no agent is created" wording.
- New `agents-map.css` classes: `.wizard-modal-overlay`, `.wizard-modal`,
  `.wizard-step-bar`, `.wizard-step`, `.wizard-step--current`, `.map-fab`
  — built from this codebase's own existing tokens
  (`--color-surface`, `--color-accent`, `--color-border`, `--space-*`,
  `--radius-*`, the same `color-mix(...)` idiom `.hub-node`/
  `.map-overflow-marker` already use). `.map-fab` reuses
  `.map-overflow-marker`'s own circular dashed-border/glow treatment,
  repositioned `position: fixed` bottom-right instead of map-relative.
- `CreateAgentCard.tsx` deleted; `SettingsPage.tsx` no longer imports or
  renders it. No replacement affordance remains on Settings (Scenario 1).

---

## Files to Modify

- `src/frontend/src/pages/AgentsMapPage.tsx` — new `.map-fab` button,
  `isWizardOpen` state, conditional modal mount, `onClose`/`onCreated`
  wiring.
- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` → renamed
  to `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx` —
  new outer overlay/modal/step-bar shell wrapping the existing
  (unregrouped) internal content; new `currentStep` state; new
  `onClose`/`onCreated` props.
- `src/frontend/src/styles/agents-map.css` — new `.wizard-modal-overlay`,
  `.wizard-modal`, `.wizard-step-bar`, `.wizard-step`,
  `.wizard-step--current`, `.map-fab` classes.
- `src/frontend/src/features/settings/CreateAgentCard.tsx` — delete.
- `src/frontend/src/pages/SettingsPage.tsx` — remove `CreateAgentCard`
  import and render.

---

## Constraints

- Inherits from parent story: no new backend endpoint; the resulting
  created agent must stay functionally identical to today's — this task
  touches presentation only, not any submit logic (untouched in this
  task).
- The new modal/step-bar CSS must NOT reuse `.side-panel-overlay`/
  `.side-panel`'s class names or edge-anchored slide-in behavior — Scenario
  2 requires visual distinctness from the existing agent-detail panel.
- The Agents Map FAB is the sole entry point after this task — no
  duplicate "+ Create agent" affordance may remain on Settings.
- Read the real current `AgentsMapPage.tsx`/`CreateAgentWizard.tsx` before
  editing — do not apply a stale diff; confirm the file shapes above still
  match at task start.
- Do not regroup or rewrite the existing per-type form fields in this task
  — that is `T02`/`T03`/`T04`/`T05`'s own scope. This task's only job is
  the outer shell (FAB, overlay, modal, step-bar, close/discard
  mechanics).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-46-US-01-AC-01] Load the Agents Map (`/`). Expect a
   `[data-testid="map-fab-create-agent"]` element present, positioned
   fixed at the bottom-right (confirm via its CSS class, not computed
   pixel position). Load the Settings page; expect zero
   `[data-testid="create-agent-affordance"]` elements anywhere on it.
2. [REQ-SB-46-US-01-AC-02] Click the FAB. Expect a
   `[data-testid="wizard-modal-overlay"]` and, nested inside it, a
   `[data-testid="wizard-modal"]` to mount, distinct in class name from
   `.side-panel-overlay`/`.side-panel` (open the agent-detail side panel
   separately and confirm the two overlays use non-overlapping class
   names). Inside the modal, expect `[data-testid="wizard-step-bar"]`
   containing exactly 4 elements (`wizard-step-1` … `wizard-step-4`), with
   `wizard-step-1` carrying `aria-current="step"` (or the
   `.wizard-step--current` class) and the other 3 not carrying it.
3. Click `[data-testid="wizard-modal-close"]`. Expect the modal/overlay to
   unmount from the DOM entirely (confirming the conditional-mount
   mechanism this task relies on for later discard-on-close verification
   in `T05`).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] A `.map-fab` button renders fixed bottom-right on the Agents Map; no `+ Create agent` affordance remains on Settings
- [ ] Clicking the FAB mounts a centered `.wizard-modal` inside a `.wizard-modal-overlay`, structurally distinct from `.side-panel-overlay`/`.side-panel`
- [ ] The modal's top renders a `.wizard-step-bar` with exactly 4 step elements, step 1 marked current by default
- [ ] Closing the modal fully unmounts it (conditional render, not a hidden/display:none toggle)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Regrouping any of the existing per-type form fields into the new 4-step
  structure (`T02`-`T05`).
- Any backend change (no task in this story before `T05` touches the
  backend at all).
- The shared `SkillsTree.tsx` component (`T04`, cross-story dependency on
  `REQ-SB-48-US-01-T02`).
- Visual polish (exact spacing, hover animation, transition timing) — not
  a locked AC; spot-checked out-of-band against this codebase's own
  existing visual language per the architect's direction, not against a
  prototype (none exists for this screen).

---

## Context / Notes

- `ADR-039` (`Implementation/Architecture/ADR.md`) is this task's
  architectural authority for the container's own visual language — reuse
  `.hub-node`/`.map-overflow-marker`'s existing token-based glow/dashed-
  border idiom rather than inventing new visual primitives.
- The FAB and modal/step-bar shell are combined into ONE task rather than
  split, per the parent story's own decomposer Notes — they are one
  inseparable interaction unit (a FAB with nothing behind it to open is
  not independently testable against any locked AC).
- `onCreated` is wired through in this task but not yet invoked by
  anything real — `T05` is the task that calls it from real Step 4
  submission. Do not stub a fake call to it here.

---

## Implementation Log

**Implemented (2026-08-14):** `CreateAgentWizard.tsx` renamed to
`CreateAgentWizardModal.tsx`, now taking `onClose`/`onCreated` props and
rendering a new outer `.wizard-modal-overlay` > `.wizard-modal` shell with
a `.wizard-modal-header` (title + `.wizard-modal-close` button) and a new
`.wizard-step-bar` (4 `.wizard-step` circles, `currentStep` state
defaulting to `1`, `aria-current="step"` + `.wizard-step--current` on the
active one) — the existing, still-unregrouped `step: 'type' | 'expert' |
'worker' | 'producer'` state machine and all three per-type forms are
preserved byte-identical inside a new `.wizard-modal-body` wrapper, per
this task's own explicit "wrap, don't rewrite" scope. `AgentsMapPage.tsx`
gained a `.map-fab` button (`data-testid="map-fab-create-agent"`) and an
`isWizardOpen` boolean gating a conditional `{isWizardOpen &&
<CreateAgentWizardModal .../>}` mount, mirroring the file's own existing
`{selectedAgentId && <AgentDetailPanel .../>}` pattern; the prior
fetch/layout `useEffect` body was extracted into a `refreshAgents`
`useCallback` so `onCreated` (wired through, not yet invoked by anything
real — `T05`'s job) can re-run the identical map refresh sequence.
`agents-map.css` gained `.map-fab` (reusing `.map-overflow-marker`'s own
dashed-border/`color-mix` glow idiom, repositioned `position: fixed`
bottom-right) and `.wizard-modal-overlay`/`.wizard-modal`/
`.wizard-modal-header`/`.wizard-modal-close`/`.wizard-modal-body`/
`.wizard-step-bar`/`.wizard-step-item`/`.wizard-step`/
`.wizard-step--current`/`.wizard-step-connector` — all token-based, zero
new hex values, and deliberately NOT reusing `.side-panel-overlay`/
`.side-panel`'s class names (those live in `agent-panel.css`, confirmed
by direct read, untouched). `CreateAgentCard.tsx` deleted;
`SettingsPage.tsx` no longer imports/renders it — confirmed by
`grep`-ing the whole `src/frontend/src` tree for `CreateAgentWizard\b`/
`CreateAgentCard` post-edit: zero remaining references outside the new
file itself.

**Verification — real backend (`uvicorn`, port 8001, no `--reload` this
task) + real frontend (Vite, port 5173) + a from-scratch Node
native-`fetch`/`WebSocket` CDP driver against a real headless Edge
(`msedge.exe --headless=new --remote-debugging-port=9333`), per this
project's own established Learnings pattern (no Playwright/Puppeteer in
this repo):**

- **[REQ-SB-46-US-01-AC-01]** PASS. Loaded `/` (confirmed real mounted
  route per `App.tsx`, not a guessed `/agents-map`, per this project's own
  prior finding): `[data-testid="map-fab-create-agent"]` present with
  `className="map-fab"` (fixed bottom-right via its CSS class, matching
  Constraint's "confirm via class, not computed pixel position").
  Navigated to `/settings`:
  `document.querySelectorAll('[data-testid="create-agent-affordance"]').length`
  === `0`.
- **[REQ-SB-46-US-01-AC-02]** PASS. Clicked the FAB — a
  `[data-testid="wizard-modal-overlay"]` (`className="wizard-modal-overlay"`)
  mounted, nesting a `[data-testid="wizard-modal"]`
  (`className="wizard-modal"`). `[data-testid="wizard-step-bar"]` contains
  exactly 4 `[data-testid^="wizard-step-"]` elements;
  `wizard-step-1.getAttribute('aria-current')` === `"step"` and carries
  `.wizard-step--current`; `wizard-step-2.getAttribute('aria-current')`
  === `null`. Independently opened the real agent-detail side panel (a
  real `.agent-node` click) and confirmed live, via
  `document.querySelector('.wizard-modal-overlay, .wizard-modal').className`,
  that neither `side-panel-overlay` nor `side-panel` appears anywhere in
  the wizard's own class list (empty-array result) — genuinely distinct,
  not just differently named markup reusing the same visual mechanism.
- **Close mechanism (Tests step 3, feeds `T05`'s later AC-11):** PASS.
  Clicked `[data-testid="wizard-modal-close"]` — both
  `[data-testid="wizard-modal"]` and `[data-testid="wizard-modal-overlay"]`
  fully unmount from the DOM (`!!document.querySelector(...)` → `false`
  for both), confirming the conditional-mount mechanism, not a
  hidden/`display:none` toggle.

No deviations from the task's own plan. No scope-internal judgement calls
beyond ordinary implementation detail (exact header markup/close-button
glyph — not a locked AC, matched this codebase's own `.side-panel-header`/
`.side-panel-close` sibling pattern for consistency, without reusing its
class names). `gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (no
new ADR, no assumption beyond ordinary implementation detail, no
out-of-scope file touched).
