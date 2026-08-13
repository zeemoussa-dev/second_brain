---
id: REQ-SB-12-US-01-T03
title: Settings page (minimal, reachability-only placeholder)
parent_story: REQ-SB-12-US-01
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-01-T03 — Settings page (minimal, reachability-only placeholder)

## Parent Story

- Story: [[REQ-SB-12-US-01]] — `../UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Replace `T01`'s bare `SettingsPage` placeholder with the minimal,
reachability-only page the story actually scopes: a page that renders
without error at `/settings` and reads clearly as "Settings," with no
Vault/Connections card content (explicitly deferred — see the story's own
Notes and Non-Goals).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `pages/SettingsPage.tsx` as `<h1>Settings</h1>` and
  wired the `/settings` route + the "Settings" `NavLink`.

**After / Outputs:**
- `pages/SettingsPage.tsx` renders a heading and a short explanatory
  paragraph (matching `html-prototype/settings.html`'s own scope-note
  paragraph), reusing already-ported primitives — no new CSS file, no
  Vault/Connections card markup.

---

## Files to Modify

- `src/frontend/src/pages/SettingsPage.tsx` — replace `T01`'s placeholder
  body:
  ```tsx
  export function SettingsPage() {
    return (
      <>
        <h1>Settings</h1>
        <p className="text-muted">
          Full settings content (vault path, Hermes connection status) is
          not built yet — this page is reachable from the sidebar, per
          REQ-SB-12's acceptance criteria.
        </p>
      </>
    );
  }
  ```
  (`.text-muted` already exists in `styles/tokens.css`, ported by `T01` —
  no new stylesheet needed for this task.)

---

## Constraints

- Inherits from parent story: full Settings content (vault path editing,
  Hermes connection management) is explicitly out of scope — do not add
  the prototype's Vault/Connections `.card` markup.
- Must not modify `T01`'s routing, `AppShell`, or `Sidebar`.
- No new CSS file or dependency.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`, use the
browser preview tool):

1. **[REQ-SB-12-US-01-AC-06]** From any page, click the "Settings" nav
   item in the sidebar. Confirm the URL becomes `/settings`, the page
   renders (`<h1>Settings</h1>` + the explanatory paragraph) with no
   thrown error and no console error in the browser preview tool's
   console output. Confirm the "Settings" `NavLink` carries
   `aria-current="page"` (react-router's `isActive`-driven attribute) and
   the rendered `.nav-item` for Settings shows the `.active` class, while
   neither the "Agents Map" nor "My Day" nav item does.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `SettingsPage` renders at `/settings` without error, reusing only
      already-ported primitives (no new CSS)
- [x] No Vault/Connections card content added (deferred per story scope)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Vault path display/editing, Hermes connection status — future work, not
  yet backed by any requirement beyond reachability.
- Any new CSS file — reuses `T01`'s `tokens.css`.

---

## Context / Notes

`html-prototype/settings.html`'s own design-rationale comment scopes this
identically: "REQ-SB-12's acceptance only requires Settings be reachable
from the shell nav, not that this batch design its full content." This
task is the real-app equivalent of that same scope line, not a fuller
build of the prototype's Vault/Connections cards.

---

## Implementation Log

**Built 2026-08-11.** `SettingsPage.tsx` replaced exactly per `## Files to
Modify`. No new CSS file, no dependency, no Vault/Connections card markup
added.

**AC-06 (Settings reachable, active nav item) — PASS.** From `/`, clicked
the "Settings" nav item. Confirmed URL became `/settings`, `<h1>Settings</h1>`
plus the explanatory paragraph rendered, no thrown error. Confirmed the
Settings `NavLink` carries `aria-current="page"` and its rendered
`.nav-item` shows the `.active` class, while "Agents Map" and "My Day" do
not (`agentsMapHasActive: false`, `myDayHasActive: false`). Zero console
errors/warnings.

**Verification tooling:** same headless-Chrome-CDP driver script noted in
`T01`'s Implementation Log.

gate: clear 2026-08-11 — no triggers fired.
