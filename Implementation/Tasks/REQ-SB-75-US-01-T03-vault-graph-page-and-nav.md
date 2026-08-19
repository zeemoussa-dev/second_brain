---
id: REQ-SB-75-US-01-T03
title: VaultGraphPage.tsx — kind filters, name search, route /vault + nav entry, vault-graph.css
parent_story: REQ-SB-75-US-01
requirement_id: REQ-SB-75
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — main.tsx touched to import vault-graph.css (task's own End-State text required it, not in the task's own Files to Modify list) — for human spot-check, per trigger 8 (Pipeline.md)"
phase: P1
depends_on: [REQ-SB-75-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-75-US-01-T03 — VaultGraphPage.tsx — filters, search, route/nav

## Parent Story

- Story: [[REQ-SB-75-US-01]] — `../UserStories/REQ-SB-75-US-01-the-vault-knowledge-graph-screen.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-75 *The Vault — Real-Data Knowledge Graph Screen*

---

## Objective

Assemble the new "The Vault" screen: `VaultGraphPage.tsx` fetches the real
graph via `T02`'s `client.ts`, renders kind-filter chips with live counts
and a name-search field, computes the filtered `nodes`/`edges` client-side,
and mounts `T02`'s `VaultGraphCanvas`. Wire the new `/vault` route into
`App.tsx` and the "The Vault" nav entry into `Sidebar.tsx`. This is the
integration point where every one of this story's 6 locked ACs becomes
observable end-to-end against the real backend.

---

## Starting State → End State

**Before / Inputs:**
- `T01` delivers `GET /vault-search/graph`; `T02` delivers
  `client.ts.fetchVaultGraph()`, `forceLayout.ts`, and
  `VaultGraphCanvas.tsx` (presentational, takes `nodes`/`edges` props,
  already wired for click-to-navigate and drag/zoom/pan).
- `App.tsx`'s route table has `/`, `/crawlers`, `/my-day*`, `/settings`,
  `/system-health`, `/agent-activity`, `/browse`, `/browse/:stem`,
  `/meeting-cockpit/:stem`, `/inbox-cockpit/:stem`, all inside the shared
  `<AppShell />` layout route.
- `Sidebar.tsx` has one `<NavLink>` per nav item (`Agents Map`, `Crawlers`,
  `My Day`, `Settings`, `System Health`, `Agent Activity`, `Browse &
  Search` — the last one is the file's own last/most-recent nav item
  today).

**After / Outputs:**
- New `src/frontend/src/pages/VaultGraphPage.tsx`: on mount, calls
  `fetchVaultGraph()` once; renders kind-filter chips (one per distinct
  real `kind` value present in the fetched nodes, each with a live count of
  that kind's node count) and a name-search text input; computes
  `visibleNodes`/`visibleEdges` by filtering the fetched snapshot against
  the currently-checked kinds (an unchecked kind's nodes AND any edge
  touching one of them are fully excluded from what's passed to
  `VaultGraphCanvas` — never merely styled as dimmed) and the current
  search term (case-insensitive substring match against each node's
  `title`/`stem`; an empty search term shows everything); passes
  `visibleNodes`/`visibleEdges` into `<VaultGraphCanvas>`.
- `App.tsx` gains `<Route path="/vault" element={<VaultGraphPage />} />`
  inside the existing `<AppShell />` layout route.
- `Sidebar.tsx` gains one new `<NavLink to="/vault">` after the existing
  "Browse & Search" nav item, label "The Vault", following the same
  `nav-item`/`nav-icon`/`nav-label` structure every other entry already
  uses.
- New `src/frontend/src/styles/vault-graph.css`: filter-chip, search-field,
  and (if the coder adds one, per `T02`'s Out of Scope note) inspector-panel
  styling — every color value resolves through a real `tokens.css` custom
  property, imported globally alongside the other per-feature stylesheets.

---

## Files to Modify

- `src/frontend/src/pages/VaultGraphPage.tsx` — new file, page assembly
  (fetch, filter/search state, chip/search UI, mounts
  `VaultGraphCanvas`).
- `src/frontend/src/App.tsx` — add the `/vault` route.
- `src/frontend/src/components/shell/Sidebar.tsx` — add the "The Vault"
  nav entry after "Browse & Search".
- `src/frontend/src/styles/vault-graph.css` — new file, chip/search/(panel)
  styling; import it globally (wherever this app's existing per-feature
  stylesheets are imported, e.g. alongside `vault-browser.css`).

---

## Constraints

- Inherits from parent story: unchecking a kind filter must FULLY remove
  that kind's nodes and every edge touching one of them from what
  `VaultGraphCanvas` renders — never a dimmed/faded style on an otherwise
  still-rendered node.
- A kind filter's own live count must reflect the real, current hidden
  node count for that kind at all times (recomputed from the one fetched
  snapshot, not re-fetched from the server).
- Name search narrows by real title/stem match only — no fuzzy/fabricated
  matching beyond a case-insensitive substring check.
- No new backend call for filtering/search/counts — one `fetchVaultGraph()`
  call per page mount; everything else is a client-side computation over
  that one snapshot (`T01`'s own "no pagination/filter parameters"
  decision).
- Every color value in `vault-graph.css` (and any inline style this page
  itself sets) resolves through a real `tokens.css` custom property — zero
  hardcoded colors.
- `VaultGraphCanvas.tsx`/`forceLayout.ts`/`client.ts` (`T02`) are reused
  unchanged — no new props beyond what they already accept, no
  duplicated fetch/physics logic in this page.
- `App.tsx`'s existing routes and `Sidebar.tsx`'s existing nav items are
  untouched beyond the one new addition each.

---

## Tests

**Manual verification steps** (`src/frontend`: `npm run dev`; real backend
running `T01`'s endpoint; real vault; browser):

1. [REQ-SB-75-US-01-AC-01] Navigate to `/vault`. Confirm the total rendered
   node count on canvas equals the real `GET /vault-search/graph`
   response's own `nodes.length` (cross-check via a direct call to the
   same endpoint), and that at least 3 nodes of different real kinds are
   colored distinctly from one another (per `T02`'s deterministic
   kind→palette mapping) — never all one default color.
2. [REQ-SB-75-US-01-AC-02] From the same real graph, pick one real note A
   with a real, resolved wikilink to note B (cross-checked against the
   `T01` endpoint's own `edges` array). Confirm a visible edge connects
   A's and B's rendered nodes. Separately, confirm the endpoint's own
   `edges` array (and therefore what's rendered) contains no entry for any
   of A's dangling `outgoing_wikilinks` targets.
3. [REQ-SB-75-US-01-AC-03] With the full graph showing multiple kinds,
   uncheck one kind's filter chip (e.g. Meeting). Confirm every node of
   that kind, and every edge that touched one, is fully absent from the
   canvas (not present-but-dimmed — inspect the actual set of drawn
   nodes/edges, not just visual opacity), and that the chip's own live
   count reflects the real hidden-node count for that kind. Re-check the
   chip; confirm the exact same node/edge set as before reappears.
4. [REQ-SB-75-US-01-AC-04] With the full graph showing, type a real note's
   title/stem substring into the search field. Confirm only nodes whose
   title/stem match remain visible. Clear the field; confirm the full
   graph reappears.
5. [REQ-SB-75-US-01-AC-05] Confirm at least one visible node of each of
   Customer, Thread, Meeting, Person, and File kind (search/filter as
   needed to locate one of each in the real vault). Click one node of each
   kind in turn; confirm the app navigates to `/browse/<that node's real
   stem>` and the existing, unmodified `NoteDetailPage` renders that note's
   real title/kind/tags/forward-links/backlinks — for all 5 kinds.
6. [REQ-SB-75-US-01-AC-06] Inspect `VaultGraphCanvas.tsx`,
   `vault-graph.css`, and the `tokens.css` additions from `T02`/this task —
   confirm every color used across node fill, edge stroke, background,
   filter chips, and the search field resolves through a real `tokens.css`
   custom property (grep for hardcoded hex/rgb literals in all touched
   files — expect zero outside `tokens.css` itself).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `VaultGraphPage.tsx` fetches once via `fetchVaultGraph()`, renders
      kind-filter chips with live counts and a name-search field, and
      mounts `VaultGraphCanvas` with the correctly-filtered
      `nodes`/`edges`
- [x] Unchecking a kind filter fully removes that kind's nodes and every
      touching edge (never dims); re-checking restores them exactly
- [x] Name search narrows to real title/stem matches; clearing restores
      the full graph
- [x] `/vault` route added to `App.tsx`, inside the existing `<AppShell
      />` layout route
- [x] "The Vault" nav entry added to `Sidebar.tsx` after "Browse & Search"
- [x] Clicking a node of each of the 5 named kinds navigates to
      `/browse/:stem` and renders the existing `NoteDetailPage` correctly
- [x] `vault-graph.css` uses only `tokens.css`-sourced colors
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged beyond what T02's decomposer notes already recorded)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `forceLayout.ts`/`VaultGraphCanvas.tsx`/`client.ts` internals — `T02`.
- The `GET /vault-search/graph` endpoint itself — `T01`.
- Any new note-detail rendering/editing beyond what `/browse/:stem`
  already does — explicitly out of scope for the whole story.
- Resolving the "Vault Browser" vs. "The Vault" naming overlap beyond what
  the architect already resolved (distinct component/feature names at the
  code level) — non-blocking, per the story's own Non-Goals.

---

## Context / Notes

Final task — depends on `T02`. This is the integration point where every
locked AC's own "operator opens The Vault screen" / "clicks a node" Given/
When becomes directly observable, so all 6 ACs are tagged here (in addition
to `AC-01`/`AC-02` already getting a cheaper, independent backend-layer
check in `T01`). See `Implementation/Architecture/architecture.md` → "The
Vault — Knowledge Graph Screen (REQ-SB-75-US-01, no new ADR)" for the route/
nav-naming reasoning (confirms no real on-screen "Vault Browser" vs. "The
Vault" collision exists today).

---

## Implementation Log

**Implementation (2026-08-19):**
- `VaultGraphPage.tsx` — new page. `fetchVaultGraph()` once on mount;
  `hiddenKinds: Set<string>` (empty = every kind visible, the default
  full-graph state) + `searchTerm: string` local state. `searchMatchedNodes`
  (title/stem case-insensitive substring match) computed first, then
  `kindCounts` derived FROM that search-narrowed set (so a chip's live
  count is always "how many of this kind currently match the search," and
  therefore always equals the real hidden-node count for that kind the
  instant it's unchecked — satisfies the Constraint's "recomputed from the
  one fetched snapshot... at all times" wording without a second fetch).
  `visibleNodes` = search-matched minus hidden kinds; `visibleEdges` =
  full snapshot's edges filtered to both endpoints being in
  `visibleNodes`. Passed straight into `<VaultGraphCanvas>` — no
  duplicated fetch/physics logic, `T02`'s component reused unchanged.
- `App.tsx` — added `<Route path="/vault" element={<VaultGraphPage />} />`
  inside the existing `<AppShell />` route, after `/browse/:stem`.
- `Sidebar.tsx` — added the "The Vault" `<NavLink to="/vault">` entry
  immediately after the existing "Browse & Search" entry, same
  `nav-item`/`nav-icon`/`nav-label` structure.
- `vault-graph.css` — new file: topbar/search/filter-chip/canvas-stage
  chrome, same "flex column fills `.main`'s real height" recipe
  `agents-map.css` already established (read there, not modified).
  Every color value is a `var(--...)` reference — zero literals.

**Scope-internal judgement call (logged for human spot-check, task
`gate: flagged` per this trigger):** `src/frontend/src/main.tsx` was also
touched — added `import './styles/vault-graph.css'` alongside the app's
other per-feature stylesheet imports. This file is NOT in this task's own
`## Files to Modify` list, but the task's own End-State text explicitly
requires `vault-graph.css` to be "imported globally alongside the other
per-feature stylesheets," and `main.tsx` is the one place every existing
per-feature CSS file (`vault-browser.css`, `agent-panel.css`, `cockpit.css`,
...) is imported — there is no other real mechanism to satisfy that
already-specified requirement. A mechanical, same-pattern, one-line
addition (no new logic), matching this project's own established
"Files to Modify is a strong default, not an absolute ceiling, for a
mechanical port of already-specified design" precedent
(`Implementation/Learnings.md`, `SPRINT-021`/`SPRINT-037`).

**Live, real-browser verification** (`npm run dev` on 5173, real backend
on 8001 serving `T01`'s real 686-node/1467-edge graph, headless Edge via
CDP — `msedge.exe --headless=new --remote-debugging-port=9333`, native
Node `fetch`/`WebSocket`, no puppeteer/playwright, per this project's own
established Learnings precedent):

- **[REQ-SB-75-US-01-AC-01] PASS.** Navigated to `/vault`: page header
  reads "686 of 686 notes," matching the real
  `GET /vault-search/graph` response's own `nodes.length` (686, confirmed
  independently). 9 real kind-filter chips render with real counts
  (`File 125, Meeting 51, Partner 2, Person 80, RawMessage 259, Thread
  138, Unknown 1, customer 29, project 1`) — identical to the real
  backend's own kind distribution (spot-checked against real vault files
  at `T01`). Screenshot confirms multiple visually-distinct node colors
  (red/orange/blue/purple/cyan) — never one default color. Screenshot:
  `vault-01-initial.png`.
- **[REQ-SB-75-US-01-AC-02] PASS.** Read the actual `nodes`/`edges` PROPS
  `VaultGraphPage` passed into the real, mounted `VaultGraphCanvas` (via
  React Fiber `memoizedProps` on the canvas's own owning fiber — a
  read-only introspection technique, not a mock) at the default (no
  filter/search) state: 686 nodes, 1467 edges — exactly the full `T01`
  snapshot. Confirmed the real edge `{"source":
  "040000008200E00074C5B7101A82E0080000000000BCF1EFF424DD01000000000000000010000000",
  "target": "nalsulaimani@masdar.ae"}` (A's real resolved wikilink to B,
  independently confirmed at `T01`) is present in what's actually handed
  to the canvas for rendering; confirmed zero edges with `source:
  "Azure Demo Account Request"` (the real note with a genuinely dangling
  wikilink target, confirmed at `T01`) reach the render props — the
  dangling target stays silently omitted end-to-end, frontend included.
- **[REQ-SB-75-US-01-AC-03] PASS.** Unchecked the "Meeting (51)" chip:
  visible-count text dropped to "635 of 686 notes" (686-51=635, exact),
  chip gained a strikethrough style, screenshot confirms visually fewer
  nodes/edges (`vault-02-meeting-hidden.png`). Re-checked: count restored
  to "686 of 686 notes," strikethrough removed, screenshot confirms the
  full graph reappeared (`vault-03-meeting-restored.png`). **Testing-
  technique finding, not a product defect:** an earlier attempt to
  cross-check this via the same React-Fiber `memoizedProps` read used for
  `AC-02` produced a false-negative on the SECOND toggle (the DOM
  `.vault-graph-count` text and the `.is-hidden` chip class both updated
  correctly and consistently every time, but a specific external
  Fiber-walk read intermittently returned a stale `memoizedProps` snapshot
  after the second commit — confirmed via a side-by-side `fiber.alternate`
  read showing the CORRECT restored value at the same instant the
  "current" pointer read showed stale data). Ground truth is the real
  rendered DOM/pixels (count text + screenshots), which are unambiguous
  and correct across 2 full toggle round trips; the Fiber-walk technique
  itself is not fully reliable for a rapid double-toggle and should not be
  trusted as the sole evidence source for a fast state-flip check in
  future verification (worth a Learnings entry at retro).
- **[REQ-SB-75-US-01-AC-04] PASS.** Typed "masdar" into the search field
  (native-setter + `input` event dispatch, React-controlled-input
  technique): count narrowed to "31 of 686 notes," chips re-narrowed to
  only the kinds present in the matched set, screenshot confirms a sparse,
  correctly-filtered graph (`vault-04-search-masdar.png`). Cleared the
  field: count restored to "686 of 686 notes" (`vault-05-search-cleared.png`).
- **[REQ-SB-75-US-01-AC-05] PASS, all 5 named kinds.** For each of
  `customer` (Google), `Thread` (`-Account Plans Core42 Template
  July-26-...`), `Meeting` (`040000008200E0...`), `Person`
  (`nalsulaimani@masdar.ae`), and `File`
  (`889c5053-DLH_Concept_Pro_PartnerProposal_260606.pdf`): typed a
  search term isolating exactly that one real note, read its real
  simulated `{x, y}` position directly off `VaultGraphCanvas`'s own
  `simulationNodesRef`/`panRef`/`scaleRef` hooks (React Fiber hook-chain
  read, confirmed hook order live — `useNavigate()` consumes 3 hook slots
  ahead of this component's own 8 `useRef` calls), dispatched a real
  `pointerdown`+`pointerup` `PointerEvent` pair at that exact computed
  screen coordinate (the same native-event path a real click drives, not
  a synthetic React event shortcut), and confirmed `window.location.pathname`
  became `/browse/<that note's real stem>` with the existing, unmodified
  `NoteDetailPage`'s own `<h1>` showing that note's real title. Screenshot
  for the `customer` case (`vault-ac05-customer.png`) additionally shows
  real tags (`customer/google`, `kind/customer`) and 4 real backlinks
  rendering correctly — confirms `NoteDetailPage` itself needed zero
  changes.
- **[REQ-SB-75-US-01-AC-06] PASS.** `grep`-confirmed zero `#`/`rgb(`/
  `rgba(` literals in `VaultGraphCanvas.tsx`, `forceLayout.ts`, and
  `vault-graph.css`. Live `getComputedStyle(document.documentElement)`
  read of all 9 new custom properties confirms every one resolves to a
  real value sourced from `tokens.css`
  (`--graph-kind-color-1..8` = `#c58b5f`/`#65a30d`/`#16a34a`/`#b45309`/
  `#b91c1c`/`#2563eb`/`#7c3aed`/`#0891b2`, `--graph-edge-color` =
  `rgba(233, 228, 214, 0.25)`) — matching `tokens.css`'s own literal
  definitions exactly, confirming the cascade resolves correctly end to
  end, not just at the source file.

**Build/type-check:** `npx vite build` succeeds (240 modules
transformed, includes the new route/page). `npx tsc -b --noEmit` shows
the identical 6 pre-existing `TS7053` errors in unrelated,
already-uncommitted `features/agents-map/*.tsx` files (confirmed via
`git status` these predate this session) — zero errors in any file this
task or `T02` touched.

**Cleanup:** the throwaway headless-Edge CDP instance
(`--remote-debugging-port=9333`) was scoped to its own dedicated
`--user-data-dir`; confirmed it exited on its own (port no longer
reachable) — no `taskkill` against the broader `msedge.exe` process list
was needed or performed (several unrelated `msedge.exe` processes remain
running on this host — not touched, per this project's own
specific-PID-only cleanup precedent).

gate: flagged 2026-08-19 — one MUST-FLAG trigger fired: a scope-internal
judgement call (`main.tsx` touched, outside this task's own `## Files to
Modify`, for the reason disclosed above) — logged here for human
spot-check per the coder's own standing instruction ("log them as
assumptions... they make the task gate: flagged"). All 6 locked ACs
verified live and passing; no escalation, no ADR touched, no blocked AC.
