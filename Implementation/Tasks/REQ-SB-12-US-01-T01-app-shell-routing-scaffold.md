---
id: REQ-SB-12-US-01-T01
title: App shell, routing, and base/shell CSS scaffold (react-router + AppShell + Sidebar)
parent_story: REQ-SB-12-US-01
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-01-T01 — App shell, routing, and base/shell CSS scaffold

## Parent Story

- Story: [[REQ-SB-12-US-01]] — `../UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Stand up the first real structure on top of `src/frontend`'s bare `create-vite`
scaffold: install `react-router`, wire three routes (`/`, `/my-day`,
`/settings`) behind a persistent collapsible-sidebar `AppShell`, and port the
approved prototype's global design tokens + shell CSS. This is the foundation
`T02` (Agents Map) and `T03` (Settings) build their page content on top of.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend` is a bare `create-vite` React 19.2 + Vite 8.2 + TypeScript
  scaffold. `package.json` lists only `react`/`react-dom`. `src/App.tsx`,
  `src/main.tsx`, `src/App.css`, `src/index.css` are all the unmodified Vite
  template (counter demo, Vite/React logos) — none of it is real app content.
- `html-prototype/agents-map.html`, `html-prototype/settings.html`, and
  `html-prototype/styles.css` are the approved design source (operator
  sign-off 2026-08-11).
- `ADR-010` (`Implementation/Architecture/ADR.md`) and `architecture.md`'s
  "Frontend Application Architecture" section are the binding architecture
  decisions this task implements.

**After / Outputs:**
- `react-router` (v7.x) added to `package.json`; no other new dependency.
- `src/frontend/src/App.tsx` wraps the app in `<BrowserRouter>` with a layout
  route rendering `<AppShell>` (via `<Outlet/>`) and three child routes: `/`
  → `AgentsMapPage`, `/my-day` → `MyDayPage`, `/settings` → `SettingsPage`.
- `src/frontend/src/components/shell/AppShell.tsx` and `Sidebar.tsx` exist:
  persistent layout (`<Sidebar>` + `<main class="main"><Outlet/></main>`),
  collapsible burger-menu sidebar with `<NavLink>` nav items.
- `src/frontend/src/pages/AgentsMapPage.tsx`, `MyDayPage.tsx`,
  `SettingsPage.tsx` exist as minimal placeholder components (each renders at
  minimum an `<h1>` matching its page name) — `T02` replaces
  `AgentsMapPage.tsx`'s content, `T03` replaces `SettingsPage.tsx`'s content,
  `MyDayPage.tsx` stays a placeholder (REQ-SB-12-US-02's scope).
- `src/frontend/src/api/client.ts` exists (thin `fetch` wrapper convention,
  unused this pass — ADR-010's Consequences require this file to exist as
  part of this pass's source-layout even though nothing calls it yet).
- `src/frontend/src/styles/tokens.css`, `shell.css`, `settings.css` exist,
  ported near-verbatim from `html-prototype/styles.css`, imported once in
  `main.tsx`. The old Vite-template `App.css`/`index.css` content is removed
  (no longer imported).

---

## Files to Modify

- `src/frontend/package.json` — add `react-router` (run
  `npm install react-router` from `src/frontend`, after dot-sourcing
  `tools/use-node.ps1` per ADR-002's portable-Node convention, so the
  install uses the project's own pinned toolchain, not any system Node).
  Do not add any other dependency.

- `src/frontend/src/main.tsx` — replace the `import './index.css'` line with
  imports of the four new global stylesheets (`./styles/tokens.css`,
  `./styles/shell.css`, `./styles/settings.css`, and — once `T02` creates it
  — `./styles/agents-map.css`; for this task, import the three that exist
  after this task: `tokens.css`, `shell.css`, `settings.css`). Leave the
  `createRoot`/`<StrictMode><App /></StrictMode>` body unchanged.

- `src/frontend/src/App.tsx` — replace the entire Vite-template contents
  with:
  ```tsx
  import { BrowserRouter, Routes, Route } from 'react-router';
  import { AppShell } from './components/shell/AppShell';
  import { AgentsMapPage } from './pages/AgentsMapPage';
  import { MyDayPage } from './pages/MyDayPage';
  import { SettingsPage } from './pages/SettingsPage';

  function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<AgentsMapPage />} />
            <Route path="/my-day" element={<MyDayPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    );
  }

  export default App;
  ```

- `src/frontend/src/App.css` — delete the file's contents (no longer
  imported by anything after this task; leave an empty file rather than
  deleting the file itself, to avoid an unrelated file-removal diff).

- `src/frontend/src/index.css` — delete the file's contents (superseded by
  `styles/tokens.css`; same empty-file rationale as `App.css`).

- `src/frontend/src/components/shell/AppShell.tsx` (new):
  ```tsx
  import { useState } from 'react';
  import { Outlet } from 'react-router';
  import { Sidebar } from './Sidebar';

  export function AppShell() {
    const [collapsed, setCollapsed] = useState(false);

    return (
      <div className={collapsed ? 'app-shell sidebar-collapsed' : 'app-shell'}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        <main className="main">
          <Outlet />
        </main>
      </div>
    );
  }
  ```
  (The `.sidebar-collapsed` modifier class lives on `.app-shell` — matching
  `html-prototype/app.js`'s `shell.classList.toggle('sidebar-collapsed')` on
  the same element, so the ported `shell.css` collapsed-state selectors
  apply unchanged.)

- `src/frontend/src/components/shell/Sidebar.tsx` (new):
  ```tsx
  import { NavLink } from 'react-router';

  interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
  }

  export function Sidebar({ collapsed, onToggle }: SidebarProps) {
    return (
      <nav className="sidebar">
        <div className="sidebar-header">
          <button
            type="button"
            className="burger-btn"
            aria-label="Toggle navigation"
            aria-expanded={!collapsed}
            onClick={onToggle}
          >
            ☰
          </button>
          <h2>Second Brain</h2>
        </div>
        <NavLink
          to="/"
          end
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon">◎</span>
          <span className="nav-label">Agents Map</span>
        </NavLink>
        <NavLink
          to="/my-day"
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon">☀</span>
          <span className="nav-label">My Day</span>
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon">⚙</span>
          <span className="nav-label">Settings</span>
        </NavLink>
      </nav>
    );
  }
  ```
  (`end` on the `/` `NavLink` matches `html-prototype`'s exact-match active
  behavior — without it, `/` would also read active while on `/my-day` or
  `/settings` since every path starts with `/`. The burger glyph/icons are
  the same literal characters `html-prototype/agents-map.html` uses
  — `&#9776;`/`&#9678;`/`&#9728;`/`&#9881;` — written directly as their
  Unicode characters `☰`/`◎`/`☀`/`⚙` in JSX, not HTML entities. No
  "Screens (catalog)" nav item — `index.html` is explicitly a reviewer-only
  page per the story's own Notes, not part of the shipped nav.)

- `src/frontend/src/pages/AgentsMapPage.tsx` (new, placeholder — `T02`
  replaces the body): `export function AgentsMapPage() { return <h1>Agents
  Map</h1>; }`

- `src/frontend/src/pages/MyDayPage.tsx` (new, permanent placeholder this
  pass — REQ-SB-12-US-02's scope): `export function MyDayPage() { return
  <h1>My Day</h1>; }`

- `src/frontend/src/pages/SettingsPage.tsx` (new, placeholder — `T03`
  replaces the body): `export function SettingsPage() { return <h1>Settings
  </h1>; }`

- `src/frontend/src/api/client.ts` (new, thin convention per ADR-010,
  unused this pass):
  ```ts
  const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

  export class ApiError extends Error {
    constructor(public status: number, message: string) {
      super(message);
    }
  }

  export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    return response.json() as Promise<T>;
  }
  ```

- `src/frontend/src/styles/tokens.css` (new) — port verbatim from
  `html-prototype/styles.css`, in this order: the `:root { ... }` block
  (lines 6–55: color/type/spacing/shape tokens + the three
  `--agent-color-*` tokens), the `* { box-sizing: border-box; }` and `body
  { ... }` reset (lines 57–66), the `:focus-visible { ... }` rule (lines
  144–147), and the `h1, h2, h3 { ... }` / `h1 { ... }` / `h2 { ... }` /
  `.text-muted { ... }` / `.mono { ... }` rules (lines 159–164). These are
  the truly global, page-agnostic primitives every screen needs — grouped
  here rather than split across `shell.css`/`settings.css`.

- `src/frontend/src/styles/shell.css` (new) — port verbatim from
  `html-prototype/styles.css`: `.app-shell`/`.sidebar`/`.main`/`.nav-item`
  + `.nav-item:hover`/`.nav-item.active` (lines 68–105), and the full
  collapsible-sidebar block — `.app-shell { transition }`,
  `.app-shell.sidebar-collapsed`, `.sidebar-header`, `.burger-btn` +
  `:hover`, `.nav-icon`, and the three collapsed-state nested selectors
  (lines 172–220).

- `src/frontend/src/styles/settings.css` (new) — port verbatim from
  `html-prototype/styles.css`: `.card` (107–112), `.badge` +
  `.badge-success`/`.badge-warning`/`.badge-danger` (114–124), `.btn` +
  `.btn-primary` (126–142), `.input` (149–157), `.empty-state` +
  `.empty-state .empty-state-icon` (250–259), and `.kv-list` / `.kv-list
  .kv-row` / `.kv-list .kv-row:last-child` / `.kv-key` (693–696). Despite
  the filename, this file holds the shared cross-page component
  primitives per `architecture.md`'s own grouping ("settings.css plus
  shared `.card`/`.badge`/`.btn`/`.input`/`.kv-list` primitives ...
  imported once, application-wide") — it is imported globally, not scoped
  to the Settings page, so `.empty-state` (needed by `T02`'s Agents Map
  first-run state) belongs here rather than duplicated into
  `agents-map.css`.

  Do **not** port `.state-switcher`, `[data-state-panel]`, or the
  `fadeIn` keyframe (lines 229–244) — these are `html-prototype`'s own
  reviewer-only state-toggle tooling (a static-HTML demo aid for switching
  between populated/empty/error states in a browser), not part of the
  shipped app; this story's real app derives which state to render from
  real (mocked) data, never a manual UI toggle. Do not port the
  `.side-panel*`/`.chat-*`/`.action-list`/`.log-*` block (lines 622–761,
  REQ-SB-13's scope) or the `.day-section-*`/`.item-list`/`.item-row`
  block (lines 763–809, REQ-SB-12-US-02's scope) — out of this story.

---

## Constraints

- Inherits from parent story: ADR-010 (routing/styling/data-fetching/
  component-structure), `architecture.md`'s "Frontend Application
  Architecture" section, and the Source Layout tree naming these exact
  paths.
- `react-router`'s **declarative** mode only (`<BrowserRouter>`, `<Routes>`,
  `<Route>`, `<NavLink>`) — not the data-router/loader API (ADR-010
  Decision 1).
- Class names must match the approved prototype's own class names exactly
  (`.agent-node--worker`, `.app-shell`, `.sidebar-collapsed`, ...) — no
  renaming/translation step (ADR-010 Decision 3).
- No CSS Modules, Tailwind, or CSS-in-JS. No data-fetching library. No
  dependency beyond `react-router`.
- `npm install` must run via the portable Node toolchain
  (`tools/use-node.ps1`, ADR-002) — do not rely on any system-installed
  Node/npm.

---

## Tests

**Manual verification steps** (run from `src/frontend`; dot-source
`tools/use-node.ps1` first per ADR-002, then `npm run dev`, and use the
browser preview tool to load the served URL):

1. **[REQ-SB-12-US-01-AC-04]** Load the app in the browser. Confirm the
   sidebar renders expanded (burger button's `aria-expanded="true"`).
   Click the burger-menu toggle button. Confirm the app shell's root
   `<div>` gains the `sidebar-collapsed` class and the button's
   `aria-expanded` attribute flips to `"false"` (inspect via the browser
   preview tool's element inspector, or React DevTools if available).
   Click the toggle again; confirm the class is removed and
   `aria-expanded` returns to `"true"`.
2. **[REQ-SB-12-US-01-AC-05]** With the sidebar expanded, click the "My
   Day" nav item. Confirm the browser URL becomes `/my-day` and the page
   renders the `MyDayPage` placeholder (`<h1>My Day</h1>`); confirm the
   sidebar (with all three nav items) is still rendered. Click the
   "Settings" nav item. Confirm the URL becomes `/settings`, the
   `SettingsPage` placeholder renders, and the sidebar is still rendered.
3. Non-AC smoke check: click the "Agents Map" nav item from `/settings`;
   confirm the URL returns to `/` and the `AgentsMapPage` placeholder
   renders — confirms all three routes round-trip correctly before `T02`/
   `T03` build real page content on top.
4. Non-AC smoke check: confirm no console errors/warnings appear in the
   browser preview tool's console output on initial load or after each
   navigation click (a broken `react-router` wiring would typically throw
   here first).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `react-router` installed via the portable Node toolchain; no other new
      dependency
- [x] `App.tsx` renders `<BrowserRouter>` + a layout route (`<AppShell>` via
      `<Outlet/>`) with child routes `/`, `/my-day`, `/settings`
- [x] `AppShell`/`Sidebar` reproduce the prototype's collapsible-sidebar
      behavior and class names exactly; `NavLink`'s `isActive` drives the
      `.active` class (no hand-rolled path comparison)
- [x] `tokens.css`/`shell.css`/`settings.css` are ported near-verbatim per
      the selector groups above and imported once in `main.tsx`; the old
      Vite-template `App.css`/`index.css` content is removed
- [x] `api/client.ts` exists per ADR-010's convention, unused this pass
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `AgentsMapPage`'s real content (KB/hub/agent nodes, mock data, polar-grid
  visualization) — `T02`.
- `SettingsPage`'s real (reachability-only) content — `T03`.
- `MyDayPage`'s real content — REQ-SB-12-US-02, a separate story.
- `agents-map.css` — created by `T02`.
- Any use of `api/client.ts` — reserved for a future story that wires a real
  backend endpoint.

---

## Context / Notes

`html-prototype/app.js`'s burger-toggle logic
(`shell.classList.toggle('sidebar-collapsed')` + `aria-expanded`
mirroring) is the exact behavior to reproduce in React state — `AppShell`
owns the `collapsed` boolean (not `Sidebar`) since the class needs to land
on `.app-shell`, the same element the prototype's vanilla-JS toggles.

`html-prototype/index.html` (the reviewer screen catalog) is explicitly out
of scope per the story's own Notes — do not add a nav item or route for it.

---

## Implementation Log

**Built 2026-08-11.** All files created/modified exactly as specified in
`## Files to Modify`. `react-router` installed via the portable Node
toolchain (`tools/use-node.ps1`, per ADR-002).

**Assumption (scope-internal, logged for spot-check, not an escalation):**
`npm install react-router` (no version pin) initially resolved to `^8.3.0`
(latest), not the `v7.x` ADR-010 explicitly names. Re-installed pinned to
`react-router@^7.0.0`, which resolved to `^7.18.2` — matches ADR-010's
decision text exactly. Declarative-mode API (`BrowserRouter`/`Routes`/
`Route`/`NavLink`/`Outlet`) used here is stable across both majors, so this
would likely have worked unpinned too, but pinning avoids silently
shipping on an architecture generation the ADR never analyzed.

**Verification tooling note:** no Playwright/Puppeteer/test-runner exists
in this project yet (first frontend build, no test-stack ADR). Verified
live via a minimal Chrome DevTools Protocol driver script (headless
Chrome + Node's built-in `WebSocket`/`fetch`, no new project dependency —
the script lives in the coder's scratch space, not the repo) driving the
real `npm run dev` server and inspecting the live DOM/console, per the
manual-mode verification the pipeline requires. This is the coder's
"browser preview tool" for this session.

**AC-04 (burger menu collapse/expand) — PASS.** Loaded `/`. Initial state:
`aria-expanded="true"`, `.app-shell` has no `sidebar-collapsed` class.
Clicked `.burger-btn`: `aria-expanded` flipped to `"false"`,
`.app-shell.sidebar-collapsed` applied. Clicked again: `aria-expanded`
returned to `"true"`, `sidebar-collapsed` removed. Screenshot confirms
sidebar renders exactly per the prototype (nav icons, active-item green
highlight on "Agents Map").

**AC-05 (nav reaches My Day/Settings, sidebar persists) — PASS.** From
`/`, clicked "My Day": URL became `/my-day`, `<h1>My Day</h1>` placeholder
rendered, all 3 `.nav-item`s still present. Clicked "Settings": URL became
`/settings`, `<h1>Settings</h1>` placeholder rendered, sidebar still
present.

**Non-AC smoke checks — PASS.** Clicked "Agents Map" from `/settings`:
URL returned to `/`, `AgentsMapPage` placeholder rendered — all three
routes round-trip correctly. Zero console errors/warnings across the
entire sequence (only Vite HMR connect/React DevTools informational
messages, both expected in dev mode).

gate: clear 2026-08-11 — no triggers fired beyond the logged
scope-internal react-router version assumption above (resolved by pinning
to match ADR-010's own text, not a material deviation from it).
