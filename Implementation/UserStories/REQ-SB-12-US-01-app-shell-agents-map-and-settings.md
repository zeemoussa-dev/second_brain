---
id: REQ-SB-12-US-01
title: App shell navigation with Agents Map as the default home page, and a reachable Settings page
requirement_ids: [REQ-SB-12]
requirement_section: "REQ-SB-12: Primary Application UI Shell — Agents Map & My Day"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-008"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-01 — App shell navigation with Agents Map as the default home page, and a reachable Settings page

## Story

**As a** Second Brain user
**I want** a persistent, collapsible navigation shell that lands me on an Agents
Map visualizing my Knowledge Base and every configured background agent
(color-coded by type), with a Settings page reachable from the same
navigation
**So that** I can see, at a glance, what agents are working with my vault and
find my way around the app without hunting for a menu

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-12: Primary Application UI Shell —
  Agents Map & My Day* — "The user opens Second Brain to a persistent app
  shell: a collapsible burger-menu sidebar for navigating between pages, and a
  default home page ('Agents Map') that visualizes the Knowledge Base at the
  center with every background agent that reads from or writes to it arranged
  around it, color-coded by agent type (starting with Worker/Producer/Expert;
  more types will be added later without requiring a redesign) ... a Settings
  page." Acceptance (this story's portion): "Launching Second Brain lands the
  user on the Agents Map, which shows the Knowledge Base and every configured
  agent, each visually distinguished by its type; the burger menu
  opens/collapses site navigation to the Agents Map, My Day, and Settings; ...
  Settings is reachable from the same navigation."
- **This story covers the shell/navigation, the Agents Map screen itself, and
  Settings' reachability only.** REQ-SB-12's acceptance text also covers the
  My Day dashboard and its four drill-down pages — that portion is a separate
  story, **REQ-SB-12-US-02**, because it is a self-contained, independently
  shippable feature area (My Day's own screens and data) with real open
  product questions of its own (see that story). The agent detail/chat panel
  that opens when an Agents Map node is clicked is **REQ-SB-13**'s own
  requirement, covered by **REQ-SB-13-US-01**, not this story — Agents Map
  renders the clickable nodes here, but what happens on click is out of this
  story's scope. This mirrors the "no independent value alone" split test
  already used for prior stories this session (e.g. `REQ-SB-08-US-01`): the
  shell + Agents Map + Settings-reachability form one coherent, independently
  valuable slice on their own (a user can open the app, see the Agents Map,
  navigate, and reach Settings, without My Day or the chat panel existing
  yet), which is exactly the acceptance text's own first sentence.
- **Design authority:** `html-prototype/` — approved by the operator
  2026-08-11 ("for now, modifications will happen later"). This story
  reconciles against `html-prototype/agents-map.html` (default/home page),
  `html-prototype/settings.html` (minimal placeholder, explicitly scoped to
  "reachable" only per its own design-rationale comment), and the shared
  `.app-shell`/`.sidebar`/burger-menu markup + `app.js` behaviour (collapsible
  sidebar, reused by every screen). `html-prototype/index.html` is a reviewer
  catalog page only, not part of the shipped navigation.
- **Agent type taxonomy — starting set, extensible.** The PRD explicitly says
  "starting with Worker/Producer/Expert; more types will be added later
  without requiring a redesign" — this story implements exactly those three
  types (matching the prototype's `.agent-node--worker/--producer/--expert`
  classes and its polar-grid layout: Worker ring outermost, Expert middle,
  Producer innermost, around a central Knowledge Base node), and the
  implementation must remain extensible to new types later. It does not
  invent or decide any additional agent types now — that remains future
  scope, per the PRD's own phrasing, not a gap this story needs to resolve.
- **Second Brain's own agent-type taxonomy is distinct from Hermes's
  internal one** — `MEMORY.md`'s 2026-08-11 Constraint records Hermes's own
  internal agent categorization (Type: Expert/Worker/Hub, plus Section/
  Department) as context only; this story's Worker/Producer/Expert grouping
  is Second Brain's own UI concept and is not required to match Hermes's.
  Recorded here so `/plan-tasks` doesn't conflate the two.
- The prototype's "populated" Agents Map state renders 5 concrete agents
  (Email/Meeting/To-Do Capture, People Notes, Vault Q&A) mapped to
  REQ-SB-07/08/09/10/03 — "none invented for this pass" per its own
  design-rationale comment. This story's acceptance criteria are written
  generically ("every configured agent"), not hardcoded to that specific
  five, since which agents are actually configured/reachable depends on
  which capture/Q&A pipelines exist in the running backend at any given
  time (some of those five are still `Draft`/not yet built).
- No backend endpoint currently exists to list configured agents or their
  types — this is the first real page built on the scaffolded
  TypeScript/React/Vite frontend (`architecture.md`'s Tech Stack; no pages
  built yet before this story). The exact new API surface is an
  architecture-level decision for `/plan-tasks`, not decided here.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Launching the app lands on the Agents Map

```gherkin
Given the user opens Second Brain (navigates to the app's root URL, "/")
When the app finishes loading
Then the Agents Map page is rendered at "/" by default, with no additional
    navigation click or redirect required
```
<!-- AC-ID: REQ-SB-12-US-01-AC-01 -->

### Scenario 2: The Agents Map shows the Knowledge Base and every configured agent, distinguished by type

```gherkin
Given the backend has one or more agents configured (reading from or writing
    to the Knowledge Base) — this story renders local mock agent data
    standing in for that backend state (no "list configured agents"
    endpoint exists yet)
When the user views the Agents Map ("/")
Then a single Knowledge Base element is rendered at the center of the map
  And every configured agent is rendered as its own node around it
  And each agent node carries a CSS class identifying its type (starting
    with .agent-node--worker, .agent-node--producer, .agent-node--expert)
```
<!-- AC-ID: REQ-SB-12-US-01-AC-02 -->

### Scenario 3: First run — no agents configured yet

```gherkin
Given the mock agent data represents the first-run state (no agents
    configured yet, e.g. Hermes is not wired up)
When the user views the Agents Map ("/")
Then the Knowledge Base element is still rendered
  And an empty-state element is rendered explaining that no agents are
    connected yet
  And no agent or hub nodes are rendered (nothing agent-related to interact
    with)
```
<!-- AC-ID: REQ-SB-12-US-01-AC-03 -->

### Scenario 4: The burger menu collapses and expands the sidebar

```gherkin
Given the sidebar navigation is expanded (the default state)
When the user clicks the burger-menu toggle button
Then the app shell's collapsed state is applied (the toggle button's
    aria-expanded attribute flips to "false")
  And clicking the toggle again removes the collapsed state (aria-expanded
    returns to "true")
```
<!-- AC-ID: REQ-SB-12-US-01-AC-04 -->

### Scenario 5: Sidebar navigation reaches My Day and Settings

```gherkin
Given the user is on the Agents Map ("/") with the sidebar visible
When the user clicks the "My Day" navigation item
Then the app navigates to "/my-day"
When the user then clicks the "Settings" navigation item
Then the app navigates to "/settings"
  And the sidebar and its navigation items are still rendered on both pages
```
<!-- AC-ID: REQ-SB-12-US-01-AC-05 -->

### Scenario 6: Settings is reachable from the navigation

```gherkin
Given the user is anywhere in the app with the sidebar visible
When the user clicks the "Settings" navigation item
Then the Settings page renders at "/settings" without a thrown error
  And the "Settings" navigation item carries the active-item indicator
    (react-router's NavLink isActive state) while on that page
```
<!-- AC-ID: REQ-SB-12-US-01-AC-06 -->

## Affected Screens

- `html-prototype/agents-map.html` — default/home page: Knowledge Base +
  configured agents, color-coded by type (starting set); populated and
  first-run states. Agent-node click behaviour (opening the detail panel) is
  explicitly **not** in this story's scope — see REQ-SB-13-US-01.
- `html-prototype/settings.html` — reachability only; full settings content
  (vault path, Hermes connection status) is out of this story's scope per the
  prototype's own design-rationale comment.
- Shared shell (`.app-shell`/`.sidebar`/burger-menu markup, reused by every
  screen in `html-prototype/`) — the collapsible navigation itself is built
  here, then reused as-is by REQ-SB-12-US-02's My Day pages.
- `html-prototype/index.html` — reviewer catalog only, not part of the
  shipped app; no behaviour to build from it.

## Dependencies

- **Blocked by:** none — this is the foundational first story for the
  frontend application (nothing yet built on `src/frontend`'s scaffold).
- **Related to:** REQ-SB-12-US-02 (My Day dashboard + drill-downs) — reuses
  the shell/nav built here; not blocking in the other direction (this story
  does not need My Day's content to be complete).
- **Related to:** REQ-SB-13-US-01 (embedded agent chat & communication
  history) — that story is blocked by this one (it opens its panel from
  agent nodes rendered here).
- **Related to:** REQ-SB-07 (`Done`), REQ-SB-08 (`Draft`, flagged), REQ-SB-09
  (not yet specced), REQ-SB-10 (`Done`), REQ-SB-03 (not yet specced) — these
  are the capture/Q&A pipelines that would populate the "configured agents"
  list in a real deployment; none of them are rebuilt or required to be
  `Done` for this story (the empty/first-run state, Scenario 3, is exactly
  what covers the case where few or none of them are wired up yet).
- **External:** none beyond the already-provisioned portable Node.js
  toolchain (ADR-002).

## Constraints

- Reconciled against `html-prototype/agents-map.html` and
  `html-prototype/settings.html` as approved 2026-08-11 — do not invent new
  visual patterns without cause; reuse `styles.css`'s existing tokens/
  components.
- Agent type color-coding starts with exactly Worker/Producer/Expert; the
  underlying data model/rendering must be extensible to additional types
  later without requiring a redesign (per the PRD's explicit phrasing) —
  informs `/plan-tasks`'s data-model decision, not implemented as new types
  now.
- No backend endpoint currently returns "configured agents" data — a new API
  surface is required; its exact shape (REST route, payload fields) is an
  architecture-level decision left to `/plan-tasks`, not decided here.
- Second Brain's own Worker/Producer/Expert agent-type taxonomy must not be
  conflated with Hermes's internal Expert/Worker/Hub taxonomy (`MEMORY.md`
  constraint).
- Frontend is TypeScript + React + Vite (ADR-002) — this is the first real
  page/route built on that scaffold; routing/shell architecture decisions
  belong to `/plan-tasks`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-12-US-01-T01 | frontend | App shell, routing, and base/shell CSS scaffold (react-router + AppShell + Sidebar) | `src/frontend/src/{App.tsx,main.tsx,components/shell/,pages/,api/,styles/tokens.css,styles/shell.css,styles/settings.css}`, `package.json` | `REQ-SB-12-US-01-T01-app-shell-routing-scaffold.md` |
| REQ-SB-12-US-01-T02 | frontend | Agents Map polar-grid visualization (mock data, polarLayout, canvas + node components) | `src/frontend/src/features/agents-map/`, `src/frontend/src/pages/AgentsMapPage.tsx`, `styles/agents-map.css` | `REQ-SB-12-US-01-T02-agents-map-visualization.md` |
| REQ-SB-12-US-01-T03 | frontend | Settings page (minimal, reachability-only placeholder) | `src/frontend/src/pages/SettingsPage.tsx` | `REQ-SB-12-US-01-T03-settings-page-reachability.md` |
| REQ-SB-12-US-01-T04 | frontend | End-to-end app assembly and full acceptance verification (all 6 scenarios, real browser) | Whichever `T01`/`T02`/`T03` file needs an integration fix, if any | `REQ-SB-12-US-01-T04-end-to-end-verification.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no
      test-stack ADR exists yet; verified live in manual mode per the pipeline's
      default (see `T01`–`T04` Implementation Logs)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The My Day dashboard and its four drill-down pages** — REQ-SB-12-US-02,
  a separate story.
- **The agent detail/chat/communication-history side panel** —
  REQ-SB-13-US-01; Agents Map's agent nodes are rendered here, but clicking
  one to open a detail panel is not built in this story.
- **Full Settings page content** (vault path editing, Hermes connection
  management) — only reachability is in scope here; content is future work,
  not yet scoped by any requirement beyond "reachable."
- **Defining or building support for agent types beyond Worker/Producer/
  Expert** — explicitly deferred by the PRD's own phrasing.
- **Any Hermes integration work** — Hermes remains an external dependency,
  not built here.

## Notes

**Prototype parity (agents-map.html, settings.html, index.html):**

- Collapsible burger-menu sidebar (nav items: Agents Map, My Day, Settings) —
  **Specced** (Scenario 4, 5).
- Knowledge Base element (center of the Agents Map) — **Specced** (Scenario
  2, 3).
- Configured agents, visually distinguished by type (Worker/Producer/Expert
  rings, agent-type legend) — **Specced** (Scenario 2); the prototype's exact
  polar-grid geometry (section boundaries, ring radii, Hub nodes) is approved
  visual design to be matched at implementation time, not independently
  re-specified as separate Gherkin behaviour beyond "visually distinguished
  by type."
- First-run/empty state (no agents connected yet) — **Specced** (Scenario 3).
- Agent nodes as clickable elements that open a detail panel — **Deferred**
  to REQ-SB-13-US-01 (a separate requirement/story; this story only renders
  the nodes).
- Settings page reachability (nav item + page renders) — **Specced**
  (Scenario 6).
- Settings page content (Vault card, Connections card, vault-path
  input/error states) — **Deferred** (reason: REQ-SB-12's acceptance only
  requires Settings be reachable, and the prototype's own design-rationale
  comment scopes this batch the same way; full settings content is future
  work, not yet backed by any requirement beyond reachability).
- `index.html` (screen catalog) — **N/A**, a reviewer aid, not part of the
  shipped navigation.

gate: clear 2026-08-11 — no triggers fired: REQ-SB-12 is finalised in the PRD
(no `<!-- Draft -->` marker on the requirement itself; its breadcrumb's open
questions — additional agent types beyond Worker/Producer/Expert, and My Day
drill-down content — are explicitly out of this story's scope, handled by the
PRD's own "starting with"/"more added later" phrasing and by the separate
REQ-SB-12-US-02 story respectively, not left ambiguous here); the prototype
was approved by the operator 2026-08-11 and every scenario above is grounded
directly in it; no contradictory inputs; no ADR created or changed by this
role; not oversized (scope deliberately narrowed to shell + Agents Map +
Settings-reachability, with My Day and the chat panel split into their own
stories).

---

**Architect pass, `/plan-tasks` step 1, 2026-08-11 — `gate: flagged`
(trigger 3, ADR-010 created).**

**Architecture scope:** `architecture.md` → Tech Stack (Frontend row) and
the new "Frontend Application Architecture" section (Routing / Styling /
Data-fetching / Source structure subsections), plus the Source Layout
paragraph naming `src/frontend/src`'s new top-level folders. The
decomposer/coder are bounded by exactly those sections and
[ADR-010](../Architecture/ADR.md) — no other `architecture.md` section
(the backend Data Model subsections) is in scope for this story.

This story's four architecture-level questions (not decided by the analyst,
per its own Context/Constraints) are now resolved, full reasoning in
[ADR-010](../Architecture/ADR.md):

1. **Routing:** `react-router` (v7, declarative mode) — `App.tsx` wraps
   `<BrowserRouter>` + three routes (`/` Agents Map default, `/my-day`,
   `/settings`); `<NavLink>` drives the active-nav-item styling.
2. **Data-fetching:** no library added this pass. This story ships local
   mock agent data (`features/agents-map/mockAgents.ts`) — no HTTP call —
   per its own Non-Goals/Context ("UI shell + static/mocked agent data...
   not real backend wiring"). A thin `api/client.ts` (native `fetch`, no
   library) is established as the convention for whichever future story
   wires a real "list configured agents" endpoint; that story still owns
   the endpoint's exact route/payload shape.
3. **Styling:** reuse the approved prototype's plain global CSS, ported
   near-verbatim (same class names) into `src/frontend/src/styles/` — no
   CSS Modules/Tailwind/CSS-in-JS.
4. **Component structure:** `AgentsMapCanvas` (one connected SVG background
   layer, matching the prototype's own single `<svg class="agents-map-
   lines">`) plus `KnowledgeBaseNode`/`SectionHub`/`AgentNode` children, and
   a pure `polarLayout.ts` geometry function replacing the prototype's
   hand-derived per-node percentages.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-010 created)`. A
`REVIEW-QUEUE.md` pointer has been added for a human to review ADR-010
before the build starts. Per the pipeline contract, this does **not** halt
`/plan-tasks` — the decomposer proceeds so the human reviews ADR-010 and
the resulting task breakdown together in one pass. No `ESCALATIONS.md`
entry was needed: none of the four decisions contradicts an Accepted ADR,
the PRD, or a `MEMORY.md` constraint — each is a genuine open architecture
question this story's own Constraints deferred to this pass ("routing/shell
architecture decisions belong to `/plan-tasks`"), resolved with recorded
reasoning and alternatives, not a dispute.

---

**Decomposer pass, `/plan-tasks` step 2, 2026-08-11.**

**ACs locked:** all 6 of the analyst's untagged scenarios are now
`REQ-SB-12-US-01-AC-01` through `AC-06`, wording tightened for buildability
(concrete DOM/attribute signals — CSS class names, `aria-expanded`,
`aria-current`/`isActive` — in place of the analyst's higher-level prose)
and locked by default (no non-locked ACs this pass).

**Tasks written (4, flat root, all `status: Ready`):**
- `REQ-SB-12-US-01-T01` — app shell, routing, base/shell CSS scaffold
  (`react-router` install, `App.tsx`/`AppShell.tsx`/`Sidebar.tsx`,
  `tokens.css`/`shell.css`/`settings.css`, placeholder pages, `api/client.ts`).
  `depends_on: []`.
- `REQ-SB-12-US-01-T02` — Agents Map polar-grid visualization
  (`mockAgents.ts`, `polarLayout.ts`, `AgentsMapCanvas`/`KnowledgeBaseNode`/
  `SectionHub`/`AgentNode`, `agents-map.css`). `depends_on:
  [REQ-SB-12-US-01-T01]`.
- `REQ-SB-12-US-01-T03` — Settings page (minimal, reachability-only).
  `depends_on: [REQ-SB-12-US-01-T01]`.
- `REQ-SB-12-US-01-T04` — end-to-end app assembly + full acceptance
  verification against a fresh browser session (closes `AC-01`, which
  cannot be genuinely checked until `T01`–`T03` all exist together).
  `depends_on: [REQ-SB-12-US-01-T01, REQ-SB-12-US-01-T02,
  REQ-SB-12-US-01-T03]`. Acyclic; no cross-sprint dependency.

**AC → task verification mapping** (every locked AC has at least one
AC-tagged manual step; frontend verification runs the real Vite dev server
and inspects the rendered app via the coder's browser preview tooling, not
static code review):
- `AC-01` (launch lands on Agents Map) — `T04` step 1.
- `AC-02` (populated state: KB + typed agent nodes) — `T02` step 1, re-run
  as full-app regression in `T04` step 2.
- `AC-03` (first-run empty state) — `T02` step 2, re-run in `T04` step 3.
- `AC-04` (burger collapse/expand) — `T01` step 1, re-run in `T04` step 4.
- `AC-05` (nav reaches My Day/Settings, sidebar persists) — `T01` step 2
  (against placeholder pages), re-run against real pages in `T04` step 5.
- `AC-06` (Settings reachable + active nav item) — `T03` step 1, re-run in
  `T04` step 6.

**Status:** story advances `Draft → Ready` (all 6 ACs locked, every locked
AC has a tagged verification step, `depends_on` graph is acyclic) and all 4
tasks are set `status: Ready` in lockstep, per this role's mandatory
behaviour. **`gate` stays `flagged`** (`gate_reason` unchanged —
`trigger-3, ADR-010 created`) per this role's own rule: an architect
ADR-creation flag from step 1 is left set so the human reviews ADR-010 and
this task breakdown together in one pass; the `REVIEW-QUEUE.md` entry for
this story has been updated to reflect that tasks are now written and the
story is `Ready` (nothing further is blocked on that review except the
coder actually starting `T01`). No new `ESCALATIONS.md` entry — no
backward step or out-of-scope event occurred at this stage. No MUST-FLAG
trigger fired independently at decomposition time (no new material
assumption beyond what ADR-010 already resolved, no unfinalised
requirement, no contradictory input, no locked AC left unverifiable, no
oversized task — each of the 4 tasks fits one working session, and no
genuinely unclear/multiple-equally-valid breakdown — the routing/shell vs.
Agents Map vs. Settings vs. wiring-and-verification split follows directly
from ADR-010's own component/file boundaries).

---

**Product-owner pass (`/plan-sprints`), 2026-08-11.** Grouped into
**SPRINT-008** as a single-story sprint — see that sprint file for full
grouping rationale and sizing. `sprint: SPRINT-008` written above
(bidirectional link). ADR-010 was reviewed and approved by the operator
2026-08-11, per the sprint's own gating note; `gate: flagged` left
unchanged on this story per this role's own scope (resetting it is not
this role's job). Note for `/implement-sprint`: `REQ-SB-12-US-02` and
`REQ-SB-13-US-01` both name this story as a dependency but are **not**
grouped into any sprint yet — both are still `status: Draft`
(decomposition incomplete: `REQ-SB-12-US-02` has drafted-but-unlocked
tasks and no locked ACs; `REQ-SB-13-US-01` has no task files at all yet).
They will become eligible for `/plan-sprints` once `/plan-tasks` step 2
finishes for each.

---

**Coder pass (`/implement-sprint`), 2026-08-11 — `SPRINT-008`.** All 4
tasks (`T01`–`T04`) built and verified live against a real `npm run dev`
server, one continuous fresh browser session for the final `T04` pass
(headless Chrome via the Chrome DevTools Protocol — no test-stack ADR
exists yet, so this is this session's "browser preview tool", per the
pipeline's manual-verification default). All 6 locked ACs
(`AC-01`–`AC-06`) verified PASS, zero console errors/warnings, zero
integration defects found at `T04`. `react-router` installed pinned to
`^7.18.2` (matching ADR-010's `v7.x` decision text — `npm install
react-router` unpinned would have resolved to the newer `v8.x` line; see
`T01`'s Implementation Log). `gate` reset `flagged -> clear`: the
`REVIEW-QUEUE.md` entry this story's `gate_reason` referenced (ADR-010
human review) is no longer present in the live queue — already resolved
by the operator (per the sprint file's own Dependencies note: "`ADR-010`
... was reviewed and approved by the operator 2026-08-11 — not an open
blocker") — so closing the story out with a stale `flagged` value would
misrepresent its state. No new `ESCALATIONS.md` entry — no backward step
or out-of-scope event occurred during the build; two scope-internal
assumptions were made and logged in `T01`/`T02`'s own Implementation Logs
for human spot-check (the react-router version pin, and the `main.tsx`/
`People`-section-title task-boundary judgment calls), neither weakening a
locked AC. Status: `Ready -> Done`.
