---
id: REQ-SB-85-US-01-T02
title: SettingsArtifactsPage.tsx — cross-type browse + multi-select, new Settings landing-page card
parent_story: REQ-SB-85-US-01
requirement_id: REQ-SB-85
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-85-US-01-T01]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-01-T02 — SettingsArtifactsPage.tsx: cross-type browse + multi-select, new Settings landing-page card

## Parent Story

- Story: [[REQ-SB-85-US-01]] — `../UserStories/REQ-SB-85-US-01-artifact-browser.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Build the new `SettingsArtifactsPage.tsx` — a cross-type list of every
real artifact `T01`'s `GET /artifacts` returns, grouped by kind, with a
multi-select selection that accumulates across kinds — and wire it in
from a new "Artifacts" card on the Settings landing page.

---

## Starting State → End State

**Before / Inputs:**
- `SettingsPage.tsx`'s own `SETTINGS_SECTIONS` array drives the
  `.card.settings-card` grid — 5 entries today (System/Sections/Vault/
  Config/UI).
- `SettingsVaultTemplatesPage.tsx`/`SettingsSectionsPage.tsx` both already
  render a real, approved `.item-list`/`.item-row`/`.item-row-title`/
  `.item-row-meta` list — the per-row shape to reuse here. No cross-type
  grouping or multi-select/checkbox affordance exists anywhere in this
  app today — genuinely new interaction (`net-new-design-needed`,
  functional-first per the story's own frontmatter override).
- No route exists for `/settings/artifacts`.

**After / Outputs:**
- `src/frontend/src/features/settings/artifactsApiClient.ts` (new) —
  `interface ArtifactSummary { kind: 'skill' | 'template' | 'agent' |
  'pipeline'; id: string; name: string; description: string }`,
  `fetchArtifacts(): Promise<ArtifactSummary[]>` (`GET /artifacts`, same
  `apiFetch` helper every other client uses).
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (new) —
  - Fetches `fetchArtifacts()` on mount, groups the flat list into 4
    fixed sections in a fixed order (Skills, Templates, Agents,
    Pipelines) — every section header renders even when that kind's own
    group is empty (Scenario 3): an empty group renders its own
    `[data-role="artifact-empty-<kind>"]` row (e.g. "No Pipelines yet")
    instead of being omitted.
  - Each real artifact renders as an `.item-list`/`.item-row` (existing
    approved family) with a leading checkbox
    (`data-testid="artifact-checkbox-<kind>-<id>"`), `.item-row-title`
    (name), `.item-row-meta` (kind badge + description).
  - Selection state: `Record<string, Set<string>>` keyed by kind (or an
    equivalent shape) — ephemeral `useState`, never persisted/round-
    tripped anywhere until an Export/Import action is taken (out of this
    task's own scope — `REQ-SB-85-US-02`/`US-03`'s own frontend tasks
    read/write this same state, wired from here).
  - A selection-summary strip (`data-role="artifact-selection-summary"`)
    renders the total selected count plus a per-kind breakdown (e.g.
    "3 selected — 2 Skills, 1 Agent") whenever at least one artifact is
    selected.
  - A `data-testid="clear-selection"` control, enabled only when the
    selection is non-empty, resets every kind's selection to empty
    without refetching/mutating the underlying list.
- `src/frontend/src/pages/SettingsPage.tsx` — `SETTINGS_SECTIONS` gains
  one more entry: `{ key: 'artifacts', icon: 'inventory_2', label:
  'Artifacts', desc: 'Export or import Skills, Templates, Agents, and
  Pipelines as a portable bundle.', href: '/settings/artifacts' }` —
  reuses the exact live `.card.settings-card` pattern, no new component.
- `src/frontend/src/App.tsx` — new route: `<Route path="/settings/artifacts"
  element={<SettingsArtifactsPage />} />`, same flat-sibling-route shape
  every other Settings drill-down page already uses.

---

## Files to Modify

- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (new).
- `src/frontend/src/pages/SettingsPage.tsx`.
- `src/frontend/src/features/settings/artifactsApiClient.ts` (new).
- `src/frontend/src/App.tsx`.

---

## Constraints

- Inherits from parent story.
- **Read-only browsing/selection only** — no create/edit/delete of any
  artifact from this screen.
- **DOM-structural ACs only, no locked assertion on exact visual
  styling** — per this project's own "structural ACs for screens"
  convention: lock only that the grouped list renders, that selection
  accumulates/displays counts, that an empty kind renders its own honest
  empty row, and that clearing empties the selection — never pixel-level/
  colour/hover assertions. This screen's exact visual treatment is
  `net-new-design-needed` (functional-first per the story's own
  frontmatter override) — a non-blocking design spot-check is expected
  later, not a locked AC here.
- Reuse the existing `.item-list`/`.item-row` family and
  `.card.settings-card` grid unchanged — no new list/card component.
- Selection state is ephemeral, client-side only — never persisted or
  sent to the backend from this task's own code (Export/Import, `US-02`/
  `US-03`, are the first real consumers of it).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-01-AC-01]` With real Skills/Templates/Agents/Pipelines
   present, render `SettingsArtifactsPage`; confirm every real id `T01`'s
   endpoint returns appears as its own row, correctly grouped under its
   own kind heading with its own name/id visible.
2. `[REQ-SB-85-US-01-AC-02]` Check one checkbox in the Skills group and
   one in the Agents group; confirm
   `[data-role="artifact-selection-summary"]` renders a combined count
   (e.g. "2 selected") with a correct per-kind breakdown for both kinds.
3. `[REQ-SB-85-US-01-AC-03]` For a kind with zero real artifacts on the
   test deployment (or a mocked empty `GET /artifacts` response filtered
   to 3 kinds), confirm that kind's own section renders
   `[data-role="artifact-empty-<kind>"]` (an honest empty state, not a
   fabricated row, not an omitted section) while the other 3 kinds still
   render their own real rows normally.
4. `[REQ-SB-85-US-01-AC-04]` With 2+ artifacts selected across 2+ kinds,
   click `[data-testid="clear-selection"]`; confirm every checkbox
   unchecks, the selection-summary strip disappears (or reads zero), and
   a subsequent re-render of the same underlying list still shows every
   real artifact (the list itself was never mutated by clearing).
5. `[REQ-SB-85-US-01-AC-05]` Render `SettingsPage`; confirm a new
   "Artifacts" card is present in the grid alongside the 5 existing
   cards; click it; confirm navigation lands on `SettingsArtifactsPage`
   (`/settings/artifacts`).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 4 kinds render grouped, each real artifact labeled with its own
      kind and name/id, reflecting the real current `GET /artifacts` response
- [x] Multi-select accumulates across kinds with a visible per-kind count
- [x] An empty kind renders an honest empty state, never hidden or fabricated
- [x] Clearing selection empties every checkbox without mutating the list
- [x] A new "Artifacts" card on the Settings landing page navigates to
      `/settings/artifacts`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      (n/a — no new decision/pattern/constraint; the one real environment
      finding hit during verification, dev backend port 8001 vs. the
      generic 8000 default, is already documented in `MEMORY.md`'s
      2026-08-27 entry)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Export/Import actions themselves — `REQ-SB-85-US-02`/`REQ-SB-85-US-03`'s
  own frontend tasks wire their own trigger buttons onto this page's
  selection state, not built here.
- Any create/edit/delete of a Skill/Template/Agent/Pipeline.
- Persisting a selection across sessions/reloads.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

Architecture `§Artifact Inventory Composition` (`REQ-SB-85-US-01`),
`Implementation/Architecture/architecture.md`, is the authoritative design
for this task. The parent story's own frontmatter `gate_reason` records
the operator's direct override: build functional-first, a real `/design
REQ-SB-85` pass covering this screen (alongside `US-02`/`US-03`'s own new
screens) happens later, after the functional build — do not block this
task on it.

Expose the selection state in a way `US-02`/`US-03`'s own frontend tasks
can read/consume when they wire their Export/Import trigger buttons onto
this page (e.g. lift the selection `useState` to `SettingsArtifactsPage`
itself and pass it down, or an equivalent shape) — those two tasks were
decomposed assuming this page's selection state is the real hand-off
point described in the story's own Story section ("a real selection to
hand to the Export flow... or to review against an imported bundle's own
contents").

---

## Implementation Log

**Coder pass (2026-08-31).** Built `src/frontend/src/features/settings/artifactsApiClient.ts`
(new, thin `fetchArtifacts()` over the real `T01` `GET /artifacts`),
`src/frontend/src/pages/SettingsArtifactsPage.tsx` (new — fetch on mount,
groups the flat response into the 4 fixed kinds in fixed order, checkbox
multi-select accumulating in a `Record<ArtifactKind, Set<string>>`,
selection-summary strip, clear-selection control, empty-kind honest row),
one new entry in `SettingsPage.tsx`'s `SETTINGS_SECTIONS`, one new route in
`App.tsx`. Reused the existing `.item-list`/`.item-row`/`.item-row-main`/
`.item-row-actions`/`.card`/`.card.settings-card` classes verbatim — no new
CSS, per the story's own functional-first override; the checkbox sits in
the existing `.item-row-actions` slot (already used for action buttons on
other rows) rather than inventing a new row region.

**Environment note (not a code defect):** the real dev backend on this box
answers on port 8001 (`src/frontend/.env.local`'s `VITE_API_BASE_URL`),
not the generic FastAPI/uvicorn default of 8000 — already documented in
`MEMORY.md`'s 2026-08-27 entry. First verification attempt started a
backend on 8000 and hit the same `BootGate` "Connecting to backend…"
symptom that entry describes; restarting on 8001 resolved it immediately.
No `MEMORY.md` edit needed since the fact is already recorded there.

**Live verification (real running app, real data, headless-Edge CDP
driver — no puppeteer/playwright, this project's own established
technique).** Backend started on `127.0.0.1:8001` (`.venv/Scripts/
python.exe -m uvicorn app.main:app`), frontend on `localhost:5173`
(`npm run dev`), a headless `msedge.exe --headless=new --remote-debugging-
port=9333` instance driven via a minimal Node `ws` CDP client
(`Runtime.evaluate`/`Page.navigate`/`Page.captureScreenshot`). Real
current deployment counts cross-checked directly against `GET /artifacts`
before verifying: 17 Skills, 10 Templates, 40 Agents, 3 Pipelines (70
total) — all 4 kinds genuinely non-empty on this deployment, so `AC-03`
needed the task's own named alternative technique.

- `[REQ-SB-85-US-01-AC-01]` PASS. Navigated to `/settings/artifacts`,
  read the real DOM after the real fetch resolved:
  `{"skillRows":17,"templateRows":10,"agentRows":40,"pipelineRows":3,
  "headings":["Second Brain","Skills","Templates","Agents","Pipelines"]}`
  — every real id from `GET /artifacts` rendered under its own correct
  kind heading with its own name/id/description visible (screenshot
  reviewed directly, not just DOM-counted).
- `[REQ-SB-85-US-01-AC-02]` PASS. Invoked the real React `onChange`
  handlers (Fiber-props direct-invoke, this project's own established
  technique for a headless-CDP session) on one Skill checkbox and one
  Agent checkbox. `[data-role="artifact-selection-summary"]` read
  `"2 selected — 1 Skills, 1 Agents"` — combined count with a correct
  per-kind breakdown across two different kinds (screenshot reviewed).
- `[REQ-SB-85-US-01-AC-03]` PASS. The task's own Tests block explicitly
  permits "a mocked empty `GET /artifacts` response filtered to 3 kinds"
  for a deployment with no naturally-empty kind — used an in-page
  `window.fetch` override (`Page.addScriptToEvaluateOnNewDocument`,
  injected before any app script ran) that calls through to the REAL
  `/artifacts` response and filters out `kind: "pipeline"` client-side
  only (no backend file touched, nothing in this task's own files
  permanently changed). Result:
  `{"pipelineEmptyRow":true,"pipelineEmptyText":"No Pipelines yet.",
  "skillRows":17,"templateRows":10,"agentRows":40,"pipelineRows":0}` —
  Pipelines rendered its own honest `[data-role="artifact-empty-
  pipeline"]` row, the other 3 kinds still rendered their full real
  counts, unaffected.
- `[REQ-SB-85-US-01-AC-04]` PASS. With the Skill+Agent selection from
  `AC-02` still active, invoked the real `onClick` handler (Fiber-props
  direct-invoke) on `[data-testid="clear-selection"]`. Result:
  `{"summaryPresent":false,"anyChecked":false,
  "totalRowsStillPresent":70,"clearBtnDisabled":true}` — every checkbox
  unchecked, the summary strip gone, all 70 real rows still present
  (list never mutated by clearing), the control itself correctly
  disabled once the selection is empty.
- `[REQ-SB-85-US-01-AC-05]` PASS. Loaded `/settings`, confirmed the new
  "Artifacts" card is present alongside the 5 existing cards
  (`hrefs: ["/settings/system","/settings/sections","/settings/vault",
  "/settings/config","/settings/ui","/settings/artifacts"]`, screenshot
  reviewed), invoked the real `<a>` element's `.click()`, confirmed
  `window.location.pathname === "/settings/artifacts"` after navigation.

No MUST-FLAG trigger fired. One scope-internal judgement call, logged for
spot-check: reused `.item-row-actions` (an existing class already used for
action-button clusters elsewhere) as the checkbox's container rather than
inventing a new class, since the task's own Constraints require reusing
the existing `.item-row` family unchanged and no new class was needed to
satisfy any locked AC. `gate: clear 2026-08-31` — no assumption filled a
PRD gap, no ADR touched, no locked AC left unverified, requirement not
Draft, no contradictory inputs, not oversized.
