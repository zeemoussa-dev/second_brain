---
id: REQ-SB-12-US-01-T04
title: End-to-end app assembly and full acceptance verification (all 6 scenarios, real browser)
parent_story: REQ-SB-12-US-01
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-01-T01, REQ-SB-12-US-01-T02, REQ-SB-12-US-01-T03]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-01-T04 — End-to-end app assembly and full acceptance verification

## Parent Story

- Story: [[REQ-SB-12-US-01]] — `../UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

With `T01`–`T03` all landed, run the fully assembled app in a real browser
and verify every one of this story's 6 locked ACs end-to-end from a fresh
load — closing the one AC (`AC-01`, "launching the app lands on the Agents
Map") that only becomes checkable once routing, the Agents Map's real
content, and the Settings page all exist together. Fix any integration
issue found (a wiring gap between `T01`/`T02`/`T03`'s independently-built
pieces) — this task's only allowed changes are minimal, targeted fixes
inside the files `T01`–`T03` already own; it introduces no new component,
page, or dependency.

---

## Starting State → End State

**Before / Inputs:**
- `T01` (shell/routing scaffold), `T02` (Agents Map visualization), `T03`
  (Settings page) are each independently built and manually verified for
  their own scope.

**After / Outputs:**
- Every one of this story's 6 locked ACs (`AC-01`–`AC-06`) is verified
  against one continuous, fresh browser session of the fully assembled
  app — not just each task's own isolated check.
- Any integration bug found during this pass is fixed in place (in
  whichever `T01`/`T02`/`T03` file the fix belongs to) and logged.

---

## Files to Modify

- Any file already listed under `T01`'s, `T02`'s, or `T03`'s own `Files to
  Modify` — **only** if this task's verification pass finds an actual
  integration defect (e.g. a route mismatch, a missing import, a class-name
  typo that breaks the active-nav-item styling). If no defect is found, no
  file is modified by this task at all — it is then purely a verification
  pass with an empty diff.

---

## Constraints

- Inherits from parent story and `T01`/`T02`/`T03`'s own constraints.
- No new component, page, dependency, or CSS file — this task assembles
  and verifies what already exists; it does not add new build surface.
- Any fix must stay inside the fixed task's own established scope/shape
  (e.g. a `Sidebar.tsx` class-name fix must still match
  `html-prototype`'s class names) — not a redesign.

---

## Tests

**Manual verification steps** (from `src/frontend`: dot-source
`tools/use-node.ps1`, `npm run dev`, use the browser preview tool — start
from a **fresh** load, i.e. navigate directly to the served root URL
rather than continuing a session left open from `T01`/`T02`/`T03`):

1. **[REQ-SB-12-US-01-AC-01]** Navigate directly to the app's root URL
   (`/`) in a fresh browser tab/session. Confirm the Agents Map page (KB
   element + 5 typed agent nodes, per `T02`) renders immediately on load,
   with no visible intermediate page, no client-side redirect, and no
   extra click required.
2. **[REQ-SB-12-US-01-AC-02]** On that same load, confirm again (as a
   full-app regression, not just `T02`'s isolated check) that the
   Knowledge Base element and all 5 correctly-type-classed agent nodes
   are present.
3. **[REQ-SB-12-US-01-AC-03]** Re-confirm `T02`'s first-run empty-state
   swap still behaves correctly now that the full app (shell + routing +
   Settings) surrounds it — repeat `T02`'s step 2 (temporarily swap in
   `FIRST_RUN_SECTIONS`/`FIRST_RUN_AGENTS`, reload, confirm the KB element
   + empty-state message render with zero agent/hub nodes, then revert).
4. **[REQ-SB-12-US-01-AC-04]** From the root load, click the burger-menu
   toggle; confirm the sidebar collapses (`aria-expanded="false"`,
   `.sidebar-collapsed` class applied). Click again; confirm it expands
   back.
5. **[REQ-SB-12-US-01-AC-05]** Click "My Day"; confirm the URL becomes
   `/my-day` and the sidebar (all 3 nav items) is still rendered. Click
   "Settings"; confirm the URL becomes `/settings` and the sidebar is
   still rendered.
6. **[REQ-SB-12-US-01-AC-06]** While on `/settings` (continuing from step
   5), confirm the page renders with no thrown error and the "Settings"
   nav item shows the `.active` class / `aria-current="page"`, while
   "Agents Map" and "My Day" do not. Click "Agents Map" to return to `/`
   and confirm its nav item becomes the active one instead.
7. Non-AC smoke check: with the sidebar collapsed (step 4), repeat the
   step-5/6 navigation clicks; confirm navigation and active-item styling
   still work correctly in the collapsed layout (the prototype's collapsed
   state hides labels but nav items remain clickable).
8. Non-AC smoke check: confirm zero console errors/warnings across the
   entire sequence above (steps 1–7, one continuous session).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 6 of this story's locked ACs (`AC-01`–`AC-06`) verified against
      one continuous, fresh-load browser session of the fully assembled app
- [x] Any integration defect found is fixed in place, inside the owning
      `T01`/`T02`/`T03` file(s), and logged in this task's Implementation Log
- [x] Zero console errors/warnings across the full verification sequence
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any new feature, page, or component — this task verifies and, if
  needed, patches what `T01`–`T03` already built.
- REQ-SB-13's agent detail panel, REQ-SB-12-US-02's My Day content,
  Settings' full content — all out of this story's scope entirely.

---

## Context / Notes

This task exists because `AC-01` ("launching the app lands on the Agents
Map, with no additional navigation step required") and the cross-page
regression it implies (sidebar persists correctly across all three real
pages, not just placeholders) can only be genuinely verified once `T01`'s
shell, `T02`'s real Agents Map content, and `T03`'s real Settings page are
all present together — each of `T01`–`T03`'s own `## Tests` sections
verify their own scope in isolation (some against placeholder pages), not
the final assembled app.

---

## Implementation Log

**Verified 2026-08-11, one continuous fresh browser session** (headless
Chrome via CDP, new browser target per run — same driver noted in `T01`'s
Implementation Log; `npm run dev` served the fully-assembled app on
`http://localhost:5183`). **No AC-blocking runtime defect found** —
`T01`/`T02`/`T03` composed cleanly at runtime; this task's diff to
`AgentsMapPage.tsx` is empty except for the two already-logged,
already-reverted temporary source swaps used to exercise `AC-03` (see
below), which leave the shipped files identical to their post-`T02`/`T03`
state.

**One build-time defect found and fixed (in `T01`'s own
`src/frontend/src/api/client.ts`).** Running this project's own
`npm run build` (`tsc -b && vite build`) as a final consistency check
(beyond the dev-server runtime checks the manual verification steps
above call for) surfaced a real TypeScript error:
`ApiError`'s constructor used a parameter-property shorthand
(`constructor(public status: number, message: string)`) — exactly as
`T01`'s own `## Files to Modify` code block prescribes — which this
project's pre-existing `tsconfig.app.json` (`erasableSyntaxOnly: true`,
part of the bare `create-vite` scaffold `T01` built on top of, not
introduced by this story) rejects (`TS1294`). Fixed in place, inside
`T01`'s own file, per this task's explicit mandate ("fix any integration
issue found... inside the files `T01`–`T03` already own"): rewrote to a
plain field assignment (`status: number;` + `this.status = status` in the
constructor body) — identical public API (`ApiError.status`), no
behavior change, just erasable-syntax-compliant. Confirmed
`npx tsc -b` and `npm run build` both succeed cleanly after the fix.
`api/client.ts` is unused by any page this pass (per ADR-010's own
Consequences), so this had no runtime-visible effect on any of the 6
ACs — dev-server verification (which uses esbuild's looser transform, not
full `tsc`) would never have surfaced it, which is exactly why this
task's own build-check step matters.

**AC-01 (launch lands on Agents Map) — PASS.** Navigated directly to `/`
in a fresh session. Agents Map (1 `.kb-node`, 5 `.agent-node`) rendered
immediately — no intermediate page, no redirect, no extra click.

**AC-02 (KB + 5 typed agent nodes, full-app regression) — PASS.**
Re-confirmed on the same fresh load: 1 `.kb-node`, 5 `.agent-node`
elements with classes `agent-node--worker` (×3), `agent-node--producer`
(×1), `agent-node--expert` (×1).

**AC-03 (first-run empty state, full-app regression) — PASS.** Repeated
`T02`'s step-2 swap (`AgentsMapPage.tsx` temporarily pointed at
`FIRST_RUN_SECTIONS`/`FIRST_RUN_AGENTS`) now that the full app (shell +
routing + real Settings page) surrounds it. Reloaded: `.kb-node` still
renders, zero `.agent-node`/`.hub-node`, `.empty-state` message renders.
Reverted back to `POPULATED_SECTIONS`/`POPULATED_AGENTS`; a final fresh
session re-confirmed the shipped populated state (5 agent nodes, 3 hub
nodes) is restored — `AgentsMapPage.tsx`'s content is byte-identical to
its post-`T02` state.

**AC-04 (burger collapse/expand) — PASS.** From the root load: initial
`aria-expanded="true"`, no `sidebar-collapsed`. Clicked burger: flipped to
`aria-expanded="false"` + `.sidebar-collapsed` applied.

**AC-05 (nav reaches My Day/Settings, sidebar persists) — PASS.** Clicked
"My Day": URL → `/my-day`, all 3 nav items still rendered. Clicked
"Settings": URL → `/settings`, all 3 nav items still rendered.

**AC-06 (Settings reachable + active nav item) — PASS.** While on
`/settings` (sidebar still collapsed from step 4): no thrown error,
Settings `NavLink` carries `aria-current="page"` + `.active`, neither
"Agents Map" nor "My Day" carries `.active`. Clicked "Agents Map": URL
returned to `/`, its nav item became the active one instead.

**Non-AC smoke check 7 (collapsed-layout navigation) — PASS.** Screenshot
confirms the collapsed sidebar (icon-only, no labels) still shows the
correct active-item highlight on Settings, and all navigation clicks in
steps 5/6 worked correctly while collapsed — the layout the prototype's
own collapsed state describes.

**Non-AC smoke check 8 (zero console errors/warnings) — PASS.** Across
the entire sequence (steps 1–7 above, one continuous session, plus a
final independent fresh-session re-run to confirm the shipped-state
revert), the only console output was Vite HMR connect/React DevTools
informational messages — zero errors, zero warnings.

**Verification tooling note (applies to `T01`–`T04`):** this project has
no test-stack ADR/runner yet (first frontend build), so "the coder's
browser preview tool" for this sprint was a small headless-Chrome CDP
driver script (Node's built-in `WebSocket`/`fetch`, zero new project
dependencies) kept in the coder's scratch space, not committed to the
repo. Recommended follow-up for whichever future story first adds a
frontend test-stack ADR: formalize this into a proper
Playwright/Puppeteer-based `npm run visual`-equivalent script so this
verification approach doesn't have to be reconstructed ad hoc each sprint.

gate: clear 2026-08-11 — no triggers fired; all 6 locked ACs verified
live, zero integration defects, zero console errors.
