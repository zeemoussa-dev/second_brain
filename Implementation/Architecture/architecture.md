# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**Last reviewed:** 2026-08-13 (REQ-SB-09-US-01 To-Do Task Capture Pipeline
architecture pass, ADR-027 — see "Task Notes & Outlook-Tasks Capture" under
Data Model, the "To-Do real data" amendment under My Day APIs, and the
`todo-capture` working-mode-gate update, below + REQ-SB-11-US-01 Agent Activity & Error
Observability architecture pass, no new ADR — honest-failure-recording
fix inside `email_classification.py::run_capture_and_record_completion`
(meeting-capture success-entry parity, a per-capture-step honest-failure-
funnel extending `ADR-015` to a new call site, a new `"run_error"`
history-entry kind), new read-only `app/business/agent_activity.py`/
`app/api/agent_activity_router.py` mirroring `system_health.py`'s shape,
a new `outlook_com.py::check_reachable()` reachability check, and a new
`AgentActivityPage.tsx` top-level nav page + REQ-SB-04-US-01 Agent Vault Write Access —
`/mcp` shared-secret authentication for non-loopback callers plus a
write-capable MCP tool that never writes directly, always routing through
a new `trigger="hermes"` Pending Approval dispatched via `ADR-021`'s own
Tier-2 `action_id` mechanism, scope-gated by a fail-closed seam pending
`REQ-SB-29-US-01` (real, load-bearing, unresolved dependency —
`ESCALATIONS.md` → `ESC-026`), architecture pass, ADR-025 — shares its
`/mcp` auth mechanism with `REQ-SB-03-US-01`'s own still-unbuilt
Constraint + REQ-SB-01-US-01 Vault Indexing — the first
real, persistent, re-runnable vault index (frontmatter/tags/wikilink graph)
architecture pass, ADR-024 — new `app/business/vault_indexing.py`
module-level in-memory rebuild-and-swap cache, new `app/api/
vault_index_router.py` on-demand rebuild endpoint, unconditional
scheduler-tick wiring into `email_classification.
run_capture_and_record_completion` (zero changes to `capture_scheduler.py`
itself), and a same-shape `vault_writer.read_note()` frontmatter list-value
round-trip fix mirroring REQ-SB-30-US-01's own boolean-value fix precedent
+ REQ-SB-08 meeting-notes-from-calendar-capture architecture pass + REQ-SB-14 vault-graph-connectivity + REQ-SB-15 manual-entry-templates + REQ-SB-10 people-notes-from-email-capture + BUGFIX-01 email-to-person-wikilink pass + REQ-SB-16 partner-hub-notes-and-migration architecture pass + REQ-SB-17 research-notes-template-and-guide architecture pass + REQ-SB-12-US-01 app-shell/Agents Map frontend architecture pass + REQ-SB-12-US-02 My Day dashboard API architecture pass + REQ-SB-13-US-01 agent detail panel (settings/actions/chat/history) architecture pass, ADR-011 + REQ-SB-16-US-01-T04 migration-scan correction pass, ADR-012 + REQ-SB-08-US-01-T06 meeting-occurrence-dedup-key correction pass, ADR-013 — resolves ESC-002 + REQ-SB-18-US-01 dynamic agent Sections/agent-to-section-assignment + REQ-SB-19-US-01 global LLM Provider CRUD/per-agent provider picker architecture pass, ADR-014 + REQ-SB-22-US-01 My Day rolling 7-day window date-filtering architecture pass + LangGraph in-app agent orchestration & shared MCP server architecture pass (REQ-SB-20/25/26/27), ADR-015 — supersedes ADR-007 + REQ-SB-25-US-01 architecture-scoping confirmation pass (ADR-015 already covers this story in full; `run_agent_conversation` history-to-message-shape addendum, no ADR change) + REQ-SB-27-US-01 Skills Repository registration/per-agent-access plumbing architecture pass, no new ADR — applies ADR-015 + REQ-SB-26-US-01 Agent Memory extraction-mechanism architecture pass, ADR-016 — extends ADR-015 point 13, does not reopen it + BUGFIX-02-US-01 Agents Map semantic-zoom/drill-down containment fix architecture pass (BUG-002), no new ADR — applies ADR-010/ADR-014 + REQ-SB-20-US-01 Section-Hub cross-Section routing keyword-storage/routing-node architecture pass, ADR-017 — extends ADR-015 point 12, does not reopen it, resolves ESC-010 + REQ-SB-21-US-01 per-agent working modes (Autonomous/Supervised/Manual) + Pending Approvals workflow architecture pass, ADR-018 — extends ADR-005/ADR-008/ADR-011, does not reopen any of them + REQ-SB-08-US-01-T06 second meeting-occurrence-dedup-key correction pass, ADR-019 — supersedes ADR-013 points 1/2, resolves ESC-002 and ESC-012 + REQ-SB-21-US-01 working-mode gate correction pass, ADR-020 — supersedes ADR-018 points 3/5 only, resolves ESC-013 + REQ-SB-30-US-01 Compass-judged email importance filtering architecture pass, no new ADR — extends the existing `classify_email` capture-time call, fixes a `vault_writer.py` frontmatter boolean round-trip gap, extends `my_day.py`'s read-path filter, and scopes a new in-window-only retrofit, all as same-shape extensions of already-Accepted structure + REQ-SB-33-US-01 agent grounding & honest-uncertainty guardrail architecture pass, no new ADR — extends `history_entries_to_messages`'s existing single identity `SystemMessage` with an additional grounding/honest-uncertainty instruction appended to its own content, applies ADR-015 + REQ-SB-31-US-01 System Health View read-only status-aggregation + chat-path crash-gap fix architecture pass, no new ADR — new `system_health.py`/`system_health_router.py` mirror `my_day.py`'s "read-only, no new persisted state" shape (extends ADR-003), new `SystemHealthPage.tsx`/nav item apply ADR-010, `run_agent_conversation`'s Scenario 8 fix applies ADR-015's existing honest-failure-funnel pattern to a second call site) + REQ-SB-35-US-01 Vault Filing Expert (new registry agent, methodology-grounded placement/write decision, Tier-2 new-top-level-area approval override) architecture pass, ADR-021 + REQ-SB-36-US-01 real Anthropic Provider integration & web-research skill architecture pass, ADR-022 — closes a live-discovered skill-access tool-binding gap in ADR-015's conversational graph + REQ-SB-36-US-02 delegated knowledge-bootstrap orchestration (Hub-routing match → real invocation) architecture pass, ADR-023 — extends ADR-017, does not reopen it. **Live-discovered, not silently patched:** `REQ-SB-35-US-01`'s and `REQ-SB-36-US-02`'s own `## Dependencies` sections both wrongly assert `REQ-SB-21-US-01`/`ADR-020` is "(Done)" — direct code and story-file inspection during this pass found `REQ-SB-21-US-01` is actually `status: Draft`, unbuilt, with zero real code for its Pending-Approvals/working-mode mechanism; `ADR-021`'s Tier 2 and `ADR-023`'s Autonomous-mode check both carry a real, currently unmet blocking prerequisite on it shipping — see `ESCALATIONS.md` → `ESC-017` + REQ-SB-02-US-01 Browse & Search architecture pass, ADR-026 — new `app/business/vault_search.py` (read-only browse/tag-filter/note-detail/ranked-search, composes `vault_indexing.get_index()` only) + new `app/api/vault_search_router.py` + new `VaultBrowserPage.tsx`/`NoteDetailPage.tsx` frontend, plus a small additive `vault_indexing.py` index-readiness accessor (`get_last_rebuilt_at()`) — extends ADR-024, does not reopen it + REQ-SB-09-US-01 To-Do (Outlook Tasks) capture architecture pass, ADR-027 — new `outlook_com.py::list_outlook_tasks` (Tasks-folder COM read, no `IncludeRecurrences`-equivalent exists for Tasks, structurally unlike Calendar), a new load-bearing `.second-brain/task_note_index.json` EntryID-keyed lookup (not a recomputed-path check, diverging from Meeting's own `ADR-019` mechanism — Task's own Scenario 6 requires a due-date/status change to still resolve to the same note), new `compass_client.classify_task` (customer-only, not a reuse of `classify_email`), new `app/business/todo_classification.py` mirroring `meeting_classification.py`, a third gated block in `run_capture_and_record_completion` (extends ADR-005/ADR-008 point 4/ADR-018, reopens none — and resolves ADR-008's own explicitly-anticipated "revisit if a third pipeline..." fork with "no orchestration-module extraction this pass"), plus My Day's `GET /my-day/todo` real-data amendment (no new ADR needed for that piece — same-shape extension of already-Accepted `my_day.py` structure)

## System Overview

Second Brain indexes and serves the user's Obsidian vault (markdown notes with
frontmatter and wikilinks) directly — no staging/promotion gate, since it's the
user's own trusted personal data, not agent-written scratch data. Standalone
project; Hermes (an external MCP-based multi-channel communication tool) is a
planned integration point, not something this project builds. Future integration
with `agentic-map`'s agents is a deliberately separate, later decision.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14 + FastAPI (see [ADR-001](ADR.md)) |
| Frontend | TypeScript + React + Vite, portable Node.js toolchain (see [ADR-002](ADR.md)); `react-router` for client-side navigation, plain global CSS, native `fetch` (no data-fetching library yet) — see [ADR-010](ADR.md) |
| Scheduling | APScheduler (`AsyncIOScheduler`), in-process, wired into FastAPI's `lifespan` (see [ADR-005](ADR.md)) |
| Agent orchestration | LangGraph (`langgraph`), bounded to Second Brain's own in-app Agents Map agent behavior (chat, Hub routing, memory, skill invocation) — not Hermes's own external orchestration, which stays untouched; see [ADR-015](ADR.md) (supersedes [ADR-007](ADR.md)) |
| Tool protocol | Model Context Protocol — official `mcp` Python SDK, one shared server exposing vault-query tools to both the in-app LangGraph agents and Hermes's external orchestration; see [ADR-015](ADR.md) |
| External LLM APIs | Compass (OpenAI-wire-compatible, `langchain_openai.ChatOpenAI` via `model_factory.py`) for conversational replies; Anthropic (official `anthropic` SDK, plain client in `data_access/anthropic_client.py`, not LangChain-wrapped) for the web-research skill's server-side web-search tool specifically — see [ADR-022](ADR.md) |

## Source Layout

```
src/
  backend/
    .venv/            — Python 3.14 virtual environment (not committed)
    app/
      api/             — FastAPI routers; HTTP-only, delegates to business/
      business/        — domain logic and orchestration; no HTTP, no direct filesystem access
      data_access/     — reads/writes the Obsidian vault (and any other storage); no business rules
      scheduling/      — in-process recurring/catch-up scheduler (APScheduler); a trigger
                          source parallel to api/, calls into business/ only, never
                          data_access/ directly (see ADR-005)
      main.py          — FastAPI app instantiation, router wiring, scheduler lifespan wiring
    tests/
    requirements.txt
  frontend/            — TypeScript + React + Vite SPA (scaffolded via `create-vite`;
                          see "Frontend Application Architecture" below for the
                          `src/frontend/src` internal structure, ADR-010)
tools/
  node/                — portable Node.js runtime + npm (not committed; see ADR-002)
  use-node.ps1         — dot-source to put tools/node on PATH for a shell session
```

Layer boundary (see [ADR-003](ADR.md)): `api` → `business` → `data_access`, one
direction only. A router must not reach into `data_access` directly, and
`business` must not perform HTTP or filesystem I/O of its own. `scheduling/`
(see [ADR-005](ADR.md)) is a second trigger source structurally parallel to
`api/`: it translates timer/lifecycle events (app startup, hourly interval,
in-process missed-run catch-up) into calls against `business/`, under the same
"never reach `data_access/` directly" rule — it does not sit *below* `api/` in
the request path, it sits *beside* it as an alternative entry point into
`business/`.

`app/business/customer_hub_linking.py` (REQ-SB-14, new) is the shared "ensure
the customer's hub note exists, then link this note to it" orchestration, used
by both the one-time retrofit and the going-forward capture-pipeline hook —
the same one-module-per-maintenance-operation shape as the existing
`tag_backfill.py` / `vault_restructure.py` modules already in `app/business/`.
See Data Model → "Customer Hub Notes & Graph Linking", below, for the full
layering breakdown.

`app/business/people_extraction.py` (REQ-SB-10, new) is the parallel "ensure
this email sender's Person note exists and is up to date, linking it to their
company's Customer hub note when that company is a known customer"
orchestration — same one-module-per-maintenance-operation shape, and the
first business module that composes another business module
(`customer_hub_linking.py`'s granular hub-note primitives) rather than only
`data_access`. See Data Model → "Person Notes & Email-Sender Extraction",
below, for the full layering breakdown and the load-bearing carve-out on how
it reuses (not blindly calls) `customer_hub_linking`.

`app/business/meeting_classification.py` (REQ-SB-08, new — see
[ADR-008](ADR.md)) mirrors `email_classification.py`'s shape exactly (fetch
→ derive customer via attendees → write note → link customer hub +
attendee Person notes → dedup), composing `people_extraction.py` (attendee
Person notes, extended from "sender" to "attendee") and
`customer_hub_linking.py` (the same granular-primitives-only-after-a-
confirmed-match carve-out `people_extraction.py` already established) as-is
— no changes to either module's existing public functions. `app/
data_access/outlook_com.py` gains a new calendar-read function,
`list_calendar_events`, alongside the existing `list_recent_mail`. See
Data Model → "Meeting Notes & Calendar-Attendee Extraction", below.

`app/business/todo_classification.py` (REQ-SB-09, new — see
[ADR-027](ADR.md)) mirrors `meeting_classification.py`'s shape (fetch →
classify by customer → write/top-up Task note → link customer hub after a
confirmed match only → dedup), composing `people_extraction`/
`customer_hub_linking`'s same granular-primitives-only carve-out — no
Person/attendee linking, since a Task has no attendee list. `app/
data_access/outlook_com.py` gains a third read function,
`list_outlook_tasks`, alongside `list_recent_mail`/`list_calendar_events`.
`app/data_access/compass_client.py` gains a second classification prompt
function, `classify_task` (customer-only, not a reuse of `classify_email`).
See Data Model → "Task Notes & Outlook-Tasks Capture", below.

`app/business/partner_hub_linking.py` (REQ-SB-16, new — see
[ADR-009](ADR.md)) is a **parallel sibling** to `customer_hub_linking.py`,
not an extension of it: the same two-granular-primitives shape
(`ensure_partner_hub_note`, `link_note_to_partner_hub`) applied to the new,
mutually-exclusive `partner/<slug>` tag namespace, plus the one-time
`migrate_customer_to_partner` retrofit that moves Microsoft's hub note and
retags every already-mistagged note. `customer_hub_linking.py` itself is
untouched. See Data Model → "Partner Hub Notes & Mutually-Exclusive Company
Taxonomy", below, for the full layering breakdown and why a sibling module
was chosen over extending the existing one.

`src/frontend/src` (REQ-SB-12-US-01, new — see [ADR-010](ADR.md)) gains its
first real structure beyond the bare `create-vite` scaffold: `pages/`
(route-level screens), `components/shell/` (the persistent collapsible-
sidebar app shell, reused by every page), `features/agents-map/` (the
Agents Map's polar-grid canvas and its child nodes, plus a pure layout-
geometry function and this pass's mock agent data), `api/` (a thin `fetch`
client convention, unused by this story but established for whenever a
later story wires a real backend call), and `styles/` (the approved
prototype's CSS, ported near-verbatim). See "Frontend Application
Architecture", below, for the full tree and reasoning.

`app/business/my_day.py` (REQ-SB-12-US-02, new) is a read-only aggregation
module — composes only `vault_writer` (no other business module, no vault
writes) to build My Day's dashboard summary counts and drill-down lists
from already-captured Email/Meeting notes. `app/api/my_day_router.py`
(new) is the first router outside the `/poc` migration-endpoint family —
My Day is an ongoing feature surface, not a one-off maintenance operation.
See "My Day & Agent Panel APIs", below.

`app/business/agent_registry.py` and `app/business/agent_chat.py`
(REQ-SB-13-US-01, new — see [ADR-011](ADR.md)) hold, respectively, a
small static known-agent registry (settings/available-actions/trigger-
phrases per agent) and the keyword/phrase-matching chat-to-action
mechanism. `app/api/agents_router.py` (new) exposes per-agent settings/
actions/chat-send/history. See "My Day & Agent Panel APIs", below, and
[ADR-011](ADR.md) for the full mechanism reasoning.

`app/business/section_registry.py` and `app/business/provider_registry.py`
(REQ-SB-18-US-01/REQ-SB-19-US-01, new — see [ADR-014](ADR.md)) each own one
new persisted, user-mutable concern (agent Sections; LLM Providers) layered
*alongside* `agent_registry.py`, not inside it — `agent_registry.py` and
`agent_chat.py` are unmodified, and `ADR-011`'s "agent identity/type/actions
stay hardcoded" reasoning is untouched. New `app/api/sections_router.py`
and `app/api/providers_router.py` expose Section/Provider CRUD;
`agents_router.py` gains `PATCH /agents/{agent_id}` for per-agent
reassignment. See "My Day & Agent Panel APIs", below, and
[ADR-014](ADR.md) for the full mechanism reasoning.

`app/business/skill_registry.py` and `app/business/skill_tools.py`
(REQ-SB-27-US-01, new — applies [ADR-015](ADR.md), no new ADR) split the
same way `ADR-015` already resolved: `skill_tools.py` (sibling to
`vault_query_tools.py`) holds the code-registered `@mcp.tool()` skill
capability itself; `skill_registry.py` owns the new persisted,
per-agent skill-*access* concern, composed alongside `skill_tools.py`'s
catalog the same way `section_registry.py`/`provider_registry.py` compose
alongside `agent_registry.py`. New `app/api/skills_router.py` exposes the
skill catalog, per-agent grant/revoke, and a plumbing-only invocation
endpoint. See "Skills Repository — registration & per-agent access",
below.

`app/business/vault_indexing.py` (REQ-SB-01-US-01, new — see
[ADR-024](ADR.md)) is the first module in this codebase to hold a
module-level, in-memory, rebuild-and-swap cache rather than either doing
stateless pass-through I/O (`vault_writer`/`vault_query_tools`) or reading/
writing a `.second-brain/*.json` file (every other cross-request store so
far). New `app/api/vault_index_router.py` exposes the on-demand rebuild
trigger; `app/business/email_classification.py::
run_capture_and_record_completion` gains one unconditional call into it, so
the existing `REQ-SB-07` hourly/app-start scheduler tick refreshes the
index too, with zero changes to `app/scheduling/capture_scheduler.py`
itself. See "Vault Indexing Layer", below, and [ADR-024](ADR.md) for the
full storage/rebuild-shape reasoning.

`app/business/vault_filing_expert.py` (REQ-SB-35-US-01, new — see
[ADR-021](ADR.md)) is the Vault Filing Expert's own placement/write
mechanism, composed by a new `"vault-filing-expert"` `agent_registry.py`
entry (data only) — deterministic-context-injected LLM placement decision,
a generic `vault_writer.write_note`-based Tier-1 write, and a Tier-2
new-top-level-area approval path that bypasses the working-mode gate by
construction, extending (not editing) `ADR-018`'s unedited-by-`ADR-020`
Pending-Approvals schema with an additive `payload` field. `app/data_access/
anthropic_client.py` (REQ-SB-36-US-01, new — see [ADR-022](ADR.md)) is a
plain `anthropic` SDK client, sibling to `compass_client.py`, backing a new
`web_research` entry in `app/business/skill_tools.py`'s catalog; `app/
business/agent_orchestration/mcp_client.py` gains `load_agent_tools(
agent_id)`, closing a live-discovered skill-access tool-binding gap (every
agent's chat previously could reach any registered skill tool
unconditionally). `app/business/agent_orchestration/knowledge_bootstrap.py`
(REQ-SB-36-US-02, new — see [ADR-023](ADR.md)) is the delegated
knowledge-bootstrap chain's own orchestration, composing `ADR-017`'s
`route_cross_section_request`, `ADR-022`'s `skill_registry.invoke_skill`,
and `ADR-021`'s `vault_filing_expert.determine_placement_and_file`
deterministically — the first code path in this project that actually
acts on a Hub-routing match rather than only reporting it. See
"Vault Filing Expert", "Real Anthropic Provider integration & web-research
skill", and "Delegated knowledge-bootstrap orchestration", below (all
under "In-App Agent Orchestration").

## Frontend Application Architecture

`src/frontend` is a Vite + React + TypeScript SPA (ADR-002). This section
describes how its `src/` is structured as pages/features are built on top
of the bare scaffold — see [ADR-010](ADR.md) for the routing/styling/
data-fetching/component-structure decisions this codifies.

### Routing (REQ-SB-12)

`react-router` (v7, declarative mode) drives all page-to-page navigation.
`App.tsx` wraps the tree in `<BrowserRouter>` with three routes: `/` (Agents
Map — the default/home page), `/my-day`, `/settings`. The sidebar's nav
items are `<NavLink>`s; `<NavLink>`'s built-in `isActive` state drives which
nav item renders as active, rather than hand-rolled path comparison.

### Styling

Global plain CSS, ported near-verbatim from the approved
`html-prototype/styles.css`, split by concern under
`src/frontend/src/styles/` (`tokens.css` — the `:root` custom-property
tokens; `shell.css` — `.app-shell`/`.sidebar`/nav/burger-menu; `agents-
map.css` — KB/hub/agent-node/ring/radar classes; `settings.css` plus shared
`.card`/`.badge`/`.btn`/`.input`/`.kv-list` primitives — grown as further
screens are built), imported once, application-wide. Class names are kept
identical to the prototype's own (`.agent-node--worker`, `.hub-node`,
`.kb-node`, `.app-shell`, ...) so components reference exactly the classes
the approved design already validated, with no renaming/translation step.
No CSS Modules, Tailwind, or CSS-in-JS — see [ADR-010](ADR.md) for why.

### Data-fetching

No data-fetching library. A thin `src/frontend/src/api/client.ts` wraps
native `fetch` for whenever a page needs a real backend call. REQ-SB-12-
US-01 itself makes no HTTP call at all — its Agents Map renders local, typed
mock data (`features/agents-map/mockAgents.ts`) mirroring the approved
prototype's 5-agent populated state and its first-run/empty state, since no
"list configured agents" endpoint exists in `src/backend` yet. The exact
route/payload shape for that future endpoint is not decided here — left to
whichever story actually builds it.

### Source structure

```
src/frontend/src/
  main.tsx                     — entry point; mounts <App />
  App.tsx                      — <BrowserRouter> + <Routes>; wraps every
                                  page in <AppShell>
  pages/
    AgentsMapPage.tsx           — default/home route ("/"); composes
                                  <AgentsMapCanvas>
    MyDayPage.tsx                — "/my-day" (REQ-SB-12-US-02; content out
                                  of this story's scope)
    SettingsPage.tsx             — "/settings" (reachability only this
                                  pass; content deferred)
  components/
    shell/
      AppShell.tsx               — persistent layout: <Sidebar> + <main>
      Sidebar.tsx                 — collapsible burger-menu nav, reused by
                                  every page
  features/
    agents-map/
      AgentsMapCanvas.tsx         — the polar-grid SVG background (radar
                                  spokes, rings, boundary, section-
                                  boundaries, Hub->KB spoke-lines, Hub->agent
                                  cluster-lines, ring-label text) plus the
                                  KB/Hub/agent-node children it positions.
                                  section-boundary divider lines are
                                  computed at each pair of adjacent hub
                                  angles' midpoint (REQ-SB-18-US-01,
                                  ADR-014), not 3 fixed positions. Owns the
                                  overview<->drill-down zoom/containment
                                  state (BUGFIX-02-US-01, BUG-002 fix — see
                                  "Agents Map — semantic zoom / drill-down
                                  containment fix", below): a local
                                  `activeSectionId: string | null` plus a
                                  transient zoom-transition flag, driving a
                                  `zooming-out` CSS class + an
                                  `onTransitionEnd` handler (React's
                                  declarative equivalent of the approved
                                  prototype's own CSS-transition +
                                  `transitionend`-listener swap — no new
                                  animation mechanism). When set, renders
                                  `SectionDrilldown` in place of its own
                                  overview markup instead of the prototype's
                                  DOM-hide/CSS-`display:none` toggle.
      KnowledgeBaseNode.tsx        — the central KB element + its brain SVG
      SectionHub.tsx                — one per section, arbitrary N
                                  (REQ-SB-18-US-01: user-created, includes
                                  zero-agent sections), neutral-colored
                                  (ADR-014 — a Section can hold agents of
                                  any Type, so it no longer tints per-Type).
                                  Gains an optional `onActivate` prop
                                  (BUGFIX-02-US-01, BUG-002 fix): when
                                  supplied (the overview's own usage),
                                  renders as a real `<button>` that opens
                                  that section's drill-down; when omitted
                                  (reused as-is inside `SectionDrilldown`),
                                  stays the original non-interactive `<div>`
                                  — one component, two call sites, no
                                  branch-by-view-name prop
      AgentNode.tsx                  — one per configured agent; rendering
                                  only (click-to-open-detail-panel is
                                  REQ-SB-13-US-01's scope); ring placement
                                  still driven by the agent's Type only
                                  (ADR-014 does not touch ring geometry).
                                  Gains two optional props (BUGFIX-02-US-01,
                                  BUG-002 fix): `compact` (applies the
                                  already-present-but-previously-unused
                                  `.agent-node--compact` CSS modifier —
                                  ADR-010's own "scale-to-~100-agents
                                  primitive, defined and ready to apply, not
                                  instantiated" — unconditionally at the
                                  overview level, replacing the never-built
                                  density-threshold branch BUG-002's root
                                  cause made necessary) and `radiusOverride`
                                  (lets `SectionDrilldown` place an agent at
                                  its own fixed drill-down radius instead of
                                  `polarLayout.ts`'s Type-keyed
                                  `RING_RADIUS`, without duplicating
                                  `AgentNode`'s rendering/click-through
                                  logic for a second, drill-down-specific
                                  node component)
      SectionDrilldown.tsx           — NEW (BUGFIX-02-US-01, BUG-002 fix):
                                  one Section's own full-360°, fully-labeled
                                  "Agents Tree" — a Hub (via `SectionHub`,
                                  no `onActivate`, non-interactive; CSS-
                                  scoped narrower via the ported
                                  `.explore-drilldown .hub-node` rule, no
                                  new size prop needed) at the visual
                                  center, that Section's own agents (via
                                  `AgentNode`, `compact` omitted,
                                  `radiusOverride={DRILLDOWN_AGENT_RADIUS}`,
                                  same `onSelectAgent` passed straight
                                  through so click-to-detail keeps working
                                  identically to the overview), Hub->agent
                                  cluster-lines only (no KB, no rings, no
                                  radar — the drill-down's own reduced SVG,
                                  matching the approved prototype's markup),
                                  the already-established `.empty-state`
                                  pattern for a 0-agent Section (no
                                  regression of REQ-SB-18-US-01's Done
                                  empty-Section handling), and a "Back to
                                  Agents Map" control. A same-shape sibling
                                  of `AgentsMapCanvas.tsx`'s own existing
                                  "container composes KB/Hub/agent-node
                                  children" pattern (ADR-010 Decision 4),
                                  one view over — not a new component
                                  pattern.
      AgentDetailPanel.tsx           — settings/actions/chat/history side
                                  panel (REQ-SB-13-US-01); Settings block
                                  gains Section/Provider <select> kv-rows
                                  (REQ-SB-18-US-01/REQ-SB-19-US-01, ADR-014)
      polarLayout.ts                  — pure ring-radius + angle -> {x, y}
                                  geometry (Producer r=30, Expert r=45,
                                  Worker r=50, Hub band r=32, boundary r=58,
                                  KB edge ~r=17 on a 0-100 viewBox);
                                  unchanged by ADR-014 — hub *count*/angle
                                  computation lives in layoutAgents.ts, ring
                                  radii stay Type-driven. Gains
                                  `DRILLDOWN_AGENT_RADIUS = 40`
                                  (BUGFIX-02-US-01, BUG-002 fix) — the
                                  drill-down's own single, Type-independent
                                  ring, co-located with this file's other
                                  geometry constants rather than
                                  hand-derived in a component
      layoutAgents.ts                  — real `GET /agents` + `GET
                                  /sections` -> the {sections, mapAgents}
                                  shape AgentsMapCanvas renders. Section
                                  membership comes from each agent's own
                                  `section_id` (no longer derived from
                                  `type`); N sections' hub angles are spaced
                                  evenly around the full circle, replacing
                                  the fixed 3-entry `SECTION_META`/
                                  `TYPE_TO_SECTION` lookup (REQ-SB-18-US-01,
                                  ADR-014). Gains `layoutSectionDrilldown`
                                  (BUGFIX-02-US-01, BUG-002 fix): takes the
                                  overview's own already-filtered
                                  `MockAgent[]` for one Section and returns
                                  a fresh `MockAgent[]` with new `angleDeg`
                                  values evenly spread across the full 360°
                                  (`idx/n * 360 - 90`, matching the approved
                                  prototype's own `renderSectionTree()`
                                  trigonometry) — a sibling, drill-down-only
                                  geometry function next to `layoutAgents`
                                  itself, not a branch inside it, since the
                                  two views' angular models are genuinely
                                  different (per-Section wedge fan-out vs.
                                  full-circle spread) and conflating them
                                  into one function/one fixed `SECTION_ARC_
                                  SPAN_DEG` constant is BUG-002's own root
                                  cause
      mockAgents.ts                    — shared type definitions only
                                  (`AgentSection`/`MockAgent`); `SectionId`
                                  is a plain `string` and `AgentSection` has
                                  no `type` field as of ADR-014 (arbitrary
                                  user-created sections, no longer 1:1 with
                                  Type)
      agentsApiClient.ts               — `/agents` HTTP calls; gains
                                  `updateAgentAssignment(agentId, {
                                  section_id?, provider_id? })` (`PATCH
                                  /agents/{id}`, REQ-SB-18-US-01/
                                  REQ-SB-19-US-01, ADR-014)
    settings/
      SectionsCard.tsx                — Settings' Sections area
                                  (create/rename/delete), REQ-SB-18-US-01
      ProvidersCard.tsx                — Settings' Providers area
                                  (add/edit/remove, Compass pre-seeded),
                                  REQ-SB-19-US-01
      settingsApiClient.ts             — `/sections` and `/providers` HTTP
                                  calls (list/create/rename-or-edit/delete),
                                  shared by SectionsCard/ProvidersCard and
                                  by AgentDetailPanel (to populate its
                                  Section/Provider picker options) —
                                  REQ-SB-18-US-01/REQ-SB-19-US-01, ADR-014
  api/
    client.ts                    — thin fetch wrapper convention; unused by
                                  this story, established for the first
                                  story that calls a real backend endpoint
  styles/
    tokens.css, shell.css, agents-map.css, settings.css — ported from
    html-prototype/styles.css, imported globally. `agents-map.css` gains
    (BUGFIX-02-US-01, BUG-002 fix) the zoom-transition/drill-down-scoping
    rules already sitting, unused, in `html-prototype/styles.css`'s own
    additive Option-D section (`.explore-zoom-overview`/`.zooming-out`,
    `.explore-drilldown` + its narrower `.explore-drilldown .hub-node`
    scope) — ported now that they are actually instantiated. The
    `.agent-node--compact` rule this file already carries needs no
    porting — ADR-010 already shipped it, unused until this fix applies
    it. The same section's entrance-animation-only rules
    (`.agent-node--intro-move`, `.agents-intro-fade`, `@keyframes
    kbGrowIn`) are **not** ported by this story — see "Agents Map —
    semantic zoom / drill-down containment fix", below.
```

## Agents Map — semantic zoom / drill-down containment fix (BUGFIX-02-US-01, BUG-002)

**No new ADR** — this closes `BUG-002` by porting an already-approved,
already-live-browser-verified prototype design (`html-prototype/
agents-map.html`/`agents-map.js`, "Option D," accepted 2026-08-12 — see
`REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry for the full
approval history) into the real React components, entirely within
`ADR-010`'s already-`Accepted` component-decomposition shape (container
composes small presentational children, a pure geometry module computes
positions) and `ADR-014` point 6's already-`Accepted` N-section-generic
layout. Nothing here introduces a new tool, framework, state-management
library, or structural boundary — it is ordinary component/prop/function
decomposition, so no ADR is warranted; recorded here (architecture.md, not
ADR.md) purely because there is no other durable home for "why these
specific files/props/functions" once this bugfix story is `Done`.

- **Root cause (confirmed live, not guessed):** `layoutAgents.ts`'s
  `SECTION_ARC_SPAN_DEG = 80` is a fixed angular budget every Section's
  agents fan across, regardless of how many Sections exist (`ADR-014`
  point 6 already made hub angle spacing N-generic, `360/N` per Section)
  or how many agents share one Section — at today's real `N=5` a Section
  only owns 72°, already narrower than the fixed 80° span before any
  agent-count crowding is even considered.
- **The fix changes *rendering density and interaction*, not the
  overview's underlying per-agent polar position.** Every agent still
  renders at `layoutAgents()`'s existing computed `angleDeg`/ring
  position — this bugfix does not touch that fan-out math at all. It
  instead (a) makes every overview agent dot **always** compact/unlabeled
  (`AgentNode`'s existing-but-previously-unapplied `.agent-node--compact`
  modifier, per Option D — not a density threshold, since "always" is
  what makes crowding structurally unable to read as label collision at
  any count) and (b) gives each Section's own Hub a click-to-drill-down
  interaction into a dedicated, full-360°, fully-labeled view of just
  that Section's agents (`SectionDrilldown`, a new sibling component to
  `AgentsMapCanvas`'s existing KB/Hub/agent-node children, per `ADR-010`
  Decision 4's own "separate component per visual concern" shape).
- **State ownership: local to `AgentsMapCanvas.tsx`, not lifted to
  `AgentsMapPage.tsx`.** Unlike `selectedAgentId` (which the page needs,
  to conditionally mount `AgentDetailPanel`), which Section is currently
  drilled into is a concern entirely internal to the map widget — no
  sibling of `AgentsMapCanvas` needs to observe or react to it. Ordinary
  React local `useState`, the same mechanism `AgentsMapPage.tsx` already
  uses for its own state — not a new state-management pattern, and not
  a new architectural question.
- **The click-to-zoom CSS transition is ported (in scope); the flat-row
  entrance animation is not (out of scope, confirmed).** The approved
  prototype's Option D bundles two effects behind one `agents-map.js`:
  the Hub-click zoom-transition (`.explore-zoom-overview`/`.zooming-out`,
  a `transitionend`-driven swap to the drill-down) and a separate,
  independently-toggleable entrance animation (flat-row → circular glide
  on initial load/state-switch/manual replay). Only the former is load-
  bearing for `BUG-002`'s own containment/drill-down defect — the
  story's own Non-Goals already deferred the latter as a polish/motion
  affordance, not a design gap, and its own repro/expected text
  (`BUGS.md`) never mentions entrance motion. Confirmed here, not
  reopened: this story's scope stays exactly what its Non-Goals already
  said. `AgentsMapCanvas.tsx`'s `onTransitionEnd` handler is React's
  declarative equivalent of the prototype's imperative
  `transitionend`-listener + `style.display = 'none'` swap — conditional
  rendering replaces the DOM-hide step, consistent with how this
  codebase's frontend already prefers React's own idioms over a literal
  DOM-manipulation port (`ADR-010`).
- **Geometry: a second, drill-down-only layout function, not a branch in
  the existing one.** `layoutAgents()`'s per-Section wedge fan-out and
  the drill-down's own full-360°-spread-at-a-fixed-radius model are
  genuinely different angular systems — conflating them into one
  function (or one shared constant) is exactly `BUG-002`'s own root
  cause shape (a single fixed span serving two different needs). The new
  `layoutSectionDrilldown()` sits beside `layoutAgents()` in the same
  file, and a new `DRILLDOWN_AGENT_RADIUS` constant sits beside
  `polarLayout.ts`'s existing `RING_RADIUS`/`HUB_RADIUS`/
  `BOUNDARY_RADIUS` — extending the existing "one shared geometry
  module" convention (`ADR-010` Decision 4) rather than hand-deriving
  positions inside a component.
- **Reuse over duplication for `SectionHub`/`AgentNode`.** Both
  components gain small, optional props (`SectionHub`'s `onActivate`;
  `AgentNode`'s `compact`/`radiusOverride`) rather than the drill-down
  growing its own parallel Hub/agent-node components — one interactive-
  vs-non-interactive Hub, one compact-vs-labeled/type-ring-vs-fixed-
  radius agent node, each reused at both call sites. This keeps
  `AgentNode`'s existing `onSelect` click-through to `AgentDetailPanel`
  (`REQ-SB-13-US-01`) working identically in the drill-down with zero
  extra wiring, per the story's own Constraint that this behaviour must
  not regress.
- **No regression of `REQ-SB-18-US-01`'s empty-Section handling.** A
  0-agent Section's drill-down reuses the exact `.empty-state` pattern
  already established elsewhere in this codebase (e.g.
  `AgentsMapPage.tsx`'s own first-run empty state) — not a new empty-
  state component or convention.
- **CSS: port only the load-bearing subset of the prototype's additive
  Option-D styles.** `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`/`.explore-drilldown .hub-node` are ported into
  `src/frontend/src/styles/agents-map.css` verbatim (class names
  unchanged, per `ADR-010` Decision 3's "no renaming/translation step"
  convention); `.agent-node--intro-move`/`.agents-intro-fade`/
  `@keyframes kbGrowIn` (entrance-animation-only) are not — see the
  Non-Goals point, above.

## My Day & Agent Panel APIs (REQ-SB-12-US-02, REQ-SB-13-US-01)

Both features follow the existing `api → business → data_access` layering
(ADR-003) exactly — no new layer, no new trigger source. Neither wires up a
frontend page itself; both settle the backend surface a later frontend
task calls, the same "backend surface now, frontend wiring next" split
already used across this codebase's earlier stories.

### My Day dashboard & drill-downs (REQ-SB-12-US-02)

- **New router `app/api/my_day_router.py`**, `APIRouter(prefix="/my-day")`,
  registered in `app/main.py` alongside `health_check_router`/
  `email_poc_router`. This is the first router outside the `/poc`
  migration-endpoint family — `/poc/...` names a one-off maintenance
  operation (backfills/retrofits/migrations); My Day is an ongoing feature
  surface a user visits repeatedly, not a migration, so it does not belong
  under `/poc`.
  - `GET /my-day/summary` → `{"emails": {"count": int}, "calendar":
    {"count": int}, "todo": {"count": 0}}` (Scenarios 1, 2). The frontend
    derives "show a count" vs. "nothing captured yet" purely from whether
    `count == 0` — there is no separate has-a-pipeline-ever-run flag. A
    section that ran and genuinely found zero items today is
    indistinguishable from one that has never run; nothing in this story's
    ACs requires telling those two apart, so adding a flag to distinguish
    them would be unrequested surface.
  - `GET /my-day/emails` → `[{"subject": str, "sender": str, "customer":
    str | null}]` (Scenarios 4, 5). `customer` is `null` when the note's
    `customer` frontmatter is `"Unsorted"` or absent — reusing
    `vault_writer.list_known_customers()`'s existing `!= "Unsorted"`
    convention for "not really classified" rather than inventing a second
    one; the frontend renders "unclassified" for `null`.
  - `GET /my-day/calendar` → `[{"subject": str, "start": str, "customer":
    str | null}]` (Scenarios 6, 7) — same `customer` convention as Emails.
    Backed by `Work/Meetings/` notes (REQ-SB-08's resolved schema); since
    REQ-SB-08 is not yet `Done`, `Work/Meetings/` does not exist in the
    real vault yet, so this list resolves to `[]` today with no
    special-casing needed — the same "kind folder doesn't exist yet"
    handling `list_all_note_paths()` already has.
  - `GET /my-day/todo` → always `[]`, hardcoded, no vault read at all
    (Scenario 8). REQ-SB-09's task source and kind-folder name are still
    unresolved (this story's own Non-Goals) — guessing a folder name to
    glob against would itself be exactly the kind of material assumption
    this story explicitly declined to make. Replace the hardcoded `[]`
    with a real read once REQ-SB-09 resolves its schema; not this story's
    or this pass's job.
- **New business module `app/business/my_day.py`** — read-only
  aggregation. `list_email_items()` / `list_calendar_items()` both call
  one shared helper that reads every note under a given kind folder and
  projects it down to the response's whitelisted fields; `todo` is not
  routed through this helper at all, per the point above.
- **New `vault_writer.py` primitive, `list_notes_in_kind_folder(kind:
  str) -> list`**, mirroring `list_all_note_paths()`'s exact existing
  shape (`work_root / kind`, glob `*.md`, sorted, `[]` if the kind folder
  doesn't exist) but scoped to one kind folder — avoids reading and
  discarding every Customer/Person/Partner/Notification/File note just to
  filter down to Emails/Meetings. A same-shape extension of an existing
  read-only primitive, not a new pattern.
- **No ADR.** A straight extension of already-`Accepted` structural
  decisions (ADR-003's layering; the one-module-per-feature `business/`
  shape already established by `tag_backfill.py`/`customer_hub_linking.py`/
  `people_extraction.py`; a `vault_writer` read primitive mirroring an
  existing one's shape exactly) — no new tool, framework, storage
  mechanism, or trust-surface decision, and nothing here contradicts any
  Accepted ADR, the PRD, or a `MEMORY.md` constraint.

#### Amendment — rolling 7-day window date-filtering (REQ-SB-22-US-01)

As shipped for REQ-SB-12-US-02, `list_email_items()`/`list_calendar_items()`
returned **every** note ever written under their kind folder, unfiltered by
date — there was no "only today," "only this window," or any other
date-scoping in the read path at all. REQ-SB-22-US-01 is the first story to
add date-range filtering to My Day's read path. Filtering is applied
**backend, at query time**, inside `app/business/my_day.py` — not
client-side over an already-fetched full list — because the unfiltered list
this endpoint already returns only grows over time (every note ever
captured), so pushing the full set to the browser on every request and
filtering there does not scale and duplicates the date-window logic on both
sides of the HTTP boundary for no benefit; the endpoints exist specifically
so the frontend never has to reason about vault-note shape itself.

- `GET /my-day/emails` response shape gains one field: `[{"subject": str,
  "sender": str, "customer": str | null, "received": str}]` — `received` is
  the note's existing `received` frontmatter field (written by
  `email_classification.py`), now surfaced for the first time; not a new
  data source, an existing captured field the response previously omitted
  (`architecture.md`'s own Constraints note, carried from the story). Both
  `/my-day/emails` and `/my-day/calendar` now return only items whose date
  field falls inside the current 7-day window (3 days before today through
  3 days after today) — items outside the window are excluded from the
  list entirely, not flagged or dimmed.
- `GET /my-day/summary` counts (`emails.count`, `calendar.count`) are
  derived from the same windowed lists (`len(list_email_items())`/
  `len(list_calendar_items())`, unchanged internally) — so the dashboard's
  counts and each drill-down's own item count are always consistent by
  construction, never two separately-computed numbers.
- **"Today" is computed backend-side, once per request, from the app/server
  host's local clock** (`datetime.now()` — naive local time, no timezone
  library, no per-user timezone preference; single-user, single-host app,
  per this story's own Non-Goals) — never a client-supplied or cached
  value. Both drill-down pages already re-fetch their list on every page
  visit (`useEffect` with an empty dependency array, `MyDayEmailsPage.tsx`/
  `MyDayCalendarPage.tsx`), which is what makes the window advance
  automatically as days pass (Scenario 4) with zero additional
  polling/refresh mechanism — a plain page reload already recomputes
  "today" on the backend.
- Each note's date field (`received` for Emails, `start` for Meetings) is
  an ISO-8601-prefixed string (`YYYY-MM-DD...`); the window comparison
  uses the first 10 characters (the calendar date) against the computed
  window's own `YYYY-MM-DD` bounds, string-compared — ISO date strings
  sort/compare correctly as plain strings, the same `received[:10]`/
  `start[:10]` slicing precedent `email_classification.py` and
  `vault_writer.meeting_note_filename_stem()` already use elsewhere in this
  codebase. No `datetime.fromisoformat()` parsing/timezone conversion is
  introduced by this pass.
- Frontend changes are additive only, within the already-`Done`
  `MyDayEmailsPage.tsx`/`MyDayCalendarPage.tsx`/`features/my-day/client.ts`:
  `MyDayEmailItem` gains a `received: string` field, rendered in the
  existing `.item-row-meta` line (Calendar already renders `start` there
  today, unchanged). No new component, region, or route — the same flat
  `.item-list`/`.item-row` pattern, narrowed by a smaller, already-filtered
  response instead of a client-side filter step.
- **Still no ADR.** Same reasoning as the original REQ-SB-12-US-02 pass
  above: a query-time filter added inside an existing `business/` module,
  behind an already-`Accepted` `api → business → data_access` layering
  (ADR-003), with no new tool, framework, storage mechanism, endpoint
  contract *shape* (only an additive field and a narrower result set), or
  trust-surface decision. Nothing here contradicts any `Accepted` ADR, the
  PRD, or a `MEMORY.md` constraint.

#### Amendment — Compass-judged email importance filtering (REQ-SB-30-US-01)

My Day's Emails list (drill-down + dashboard count) narrows further: from
"every captured Email note inside the window" to "every captured Email
note inside the window that Compass judged important." This threads
through three already-`Accepted` layers — the capture-time Compass call,
the vault frontmatter serialization primitive, and My Day's own read
path — as an ordinary same-shape extension of each; no new layer, tool,
or storage mechanism, so **no new ADR** (see "No ADR" note at the end of
this amendment).

- **Capture-time judgment: one more key on the existing `classify_email`
  JSON object, not a second Compass call.** `app/data_access/
  compass_client.py::classify_email`'s prompt already classifies one
  email along two axes (`customer`, `kind`) in a single JSON response;
  this amendment adds a third axis, `important` (boolean), to the same
  prompt and the same response object — one more paragraph in the same
  voice as the existing CUSTOMER/KIND instructions ("IMPORTANT — whether
  this specific email genuinely needs the recipient's attention: a direct
  ask, a real back-and-forth needing a response or decision,
  time-sensitive information, or something from a real customer/company
  relationship; not a notification, automated alert, FYI, newsletter, or
  routine share notification — reason about the actual content, not
  sender or keyword"), and one more key in the response JSON template
  (`"important": <true|false>`). `classify_email`'s return dict gains
  `"important": bool(parsed.get("important", True))` — defaulting to
  `True` even for a *parseable* response that happens to omit the key,
  the same fail-open posture applied one step earlier than the "field
  missing on read" case below. No new HTTP round-trip, no new Compass
  endpoint, no new parsing path beyond one more dict key — the same
  reasoning `email_classification.py`'s own docstring already gives for
  why `customer`+`kind` share one call.
  `app/business/email_classification.py::classify_recent_emails`'s
  written frontmatter dict gains one key, `"important":
  classification["important"]`, alongside the existing `customer`/`kind`/
  `classification_confidence` keys — same write, same call site, no new
  code path. **Failure mode unchanged:** `classify_email` raising
  `CompassError` is already caught per-email by `classify_recent_emails`
  before any note is written for that email (the whole note is skipped,
  an error result recorded) — a Compass failure can never produce a note
  with a fabricated `important` value, satisfying Scenario 6 with zero
  additional error-handling code.
- **Frontmatter boolean round-trip — a real gap this is the first story
  to hit, fixed in `app/data_access/vault_writer.py`, not worked around
  in `business/`.** `important` is the first-ever boolean frontmatter
  field in this codebase. `_format_frontmatter_value`'s existing fallback
  (`str(value)`) would serialize Python's `True`/`False` as the *literal
  strings* `"True"`/`"False"` (capitalized, not valid lowercase
  YAML/Obsidian boolean syntax), and `_parse_frontmatter_value` has no
  matching read-side conversion — reading the note back would return the
  *string* `"False"`, which is truthy in Python, silently defeating the
  entire filter (an email marked not-important would still evaluate as
  important on every subsequent read). Confirmed by direct reading of
  both functions, not assumed. **Fix, scoped to these two functions
  only:** `_format_frontmatter_value` gains an `isinstance(value, bool)`
  branch (checked before the generic fallback — `bool` is not `str`, so
  the existing `isinstance(value, str)` branch does not already catch
  it) writing lowercase `true`/`false`; `_parse_frontmatter_value` gains
  a matching `raw == "true"` / `raw == "false"` check (after the existing
  quoted-string check, before the generic passthrough) returning real
  `True`/`False`. A one-time-forward-compatible, surgical fix to an
  existing `data_access` primitive — not a new serialization format, not
  a migration (every other frontmatter value already written is a string
  or number and round-trips unchanged through the new branches, which
  only ever match the literal tokens `true`/`false`).
- **My Day read path: fail-open filter, plus a new `captured_count` for
  the two-empty-states distinction — additive only, no endpoint shape
  break.** `app/business/my_day.py::list_email_items(day)` gains one more
  condition after the existing window check:
  `frontmatter.get("important", True)` — a genuinely absent field (an
  email captured before this story, not yet backfilled) or an explicit
  `True` is shown; only an explicit `False` is excluded. This is the
  general-case fail-open behavior the story's own Notes record (not just
  the retrofill-window special case, below). `list_email_items`'s
  response shape is unchanged (`[{"subject", "sender", "customer",
  "received"}]`) — same "additive field or narrower result set, never a
  reshape" precedent as the REQ-SB-22-US-01 amendment above. To
  distinguish Scenario 4 ("captured but filtered out") from Scenario 5
  ("nothing captured at all") without reshaping `GET /my-day/emails`
  itself, `summary()`'s `emails` object gains one additive field:
  `{"count": int, "captured_count": int}` — `count` stays
  `len(list_email_items(day))` (post-importance-filter, unchanged
  meaning), `captured_count` is the same window-scoped count *before* the
  importance filter (every Email note inside the window regardless of
  `important`). The frontend empty-state decision
  (`MyDayEmailsPage.tsx`, T03's scope) is then a pure comparison of the
  two counts already available from `GET /my-day/summary` (which the
  page already needs to fetch, or now additionally fetches, alongside
  `GET /my-day/emails`) — `captured_count > 0 && count === 0` renders
  Scenario 4's "captured but filtered" copy, `captured_count === 0`
  renders Scenario 5's existing "nothing captured yet" copy. No new
  endpoint. `list_calendar_items`/the Calendar drill-down are untouched —
  REQ-SB-30 is Emails-only per the story's own Non-Goals.
- **Retrofit: scoped to the ~22 in-window emails only, reusing My Day's
  own window definition — not a full-181-note batch.** A new function,
  living in `app/business/email_classification.py` alongside
  `classify_recent_emails` (the module that already owns the Compass
  email-classification call and the frontmatter-write path this retrofit
  extends), iterates only `Work/Emails/` notes whose `received` falls
  inside `my_day._compute_window()`/`_within_window()` — reusing My Day's
  own window functions directly (the same cross-module reach
  `my_day_router.py::_validate_day` already established for
  `my_day._compute_window()`) so "in window" here can never drift from
  what My Day itself means by it. **Idempotent**, mirroring
  `retrofit_customer_hub_links`/`retrofit_people_from_emails`'s exact
  shape: a note that already carries an `important` key is skipped
  (`status: "already_classified"`), never re-classified. For each
  still-unclassified in-window note, it calls
  `compass_client.classify_email` with that note's own already-stored
  `subject`/`sender_email`/body (read via `vault_writer.read_note`,
  which already returns the note's own body text) and writes **only**
  the resulting `important` value back — the same-call `customer`/`kind`
  judgment is deliberately discarded; this is an importance backfill,
  not a re-classification, so a note's already-filed `customer`/`kind`
  can never drift from a retrofit rerun. Writing the single new key
  reuses `insert_tags_line`'s existing "surgical single-line insert just
  before the closing `---`" shape in `vault_writer.py` — either a small
  new sibling primitive (e.g. `insert_frontmatter_field(path, key,
  value)`, generalizing `insert_tags_line`'s body to one arbitrary key)
  or a narrow `important`-specific variant is implementation latitude
  left to the decomposer/coder, not an architectural fork; either way it
  is additive to `vault_writer.py`, not a rewrite of `insert_tags_line`
  itself. A note whose Compass call errors during the retrofit is left
  with no `important` field at all (`status: "skipped_compass_error"`),
  never a fabricated value — `list_email_items`'s own fail-open default
  then shows it, exactly the general-case behavior described above.
  Exposed the same way every existing retrofit is — a new
  `POST /poc/retrofit-email-importance` endpoint in
  `app/api/email_poc_router.py`, matching `retrofit_customer_hub_links_endpoint`'s
  existing response-shape convention (`{"notes_checked", "<verb>ed", "results"}`).
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the capture-time Compass call
  (one prompt, one response object, one more key — the mechanism ADR-015
  point "Model integration" explicitly left `compass_client.py`'s
  existing linear-pipeline shape untouched by *that* pass, and this
  amendment does not reopen or contradict that framing, since
  `classify_email` remains the one fixed-shape function called only by
  the linear email-classification pipeline, unedited in kind — only
  extended in the number of keys it returns); the `data_access`
  frontmatter-serialization primitive (a bugfix-shaped extension for the
  first boolean field, not a new storage format); the `my_day.py`
  query-time filter and additive `summary()` field (identical reasoning
  to the REQ-SB-22-US-01 amendment directly above — no new endpoint
  contract shape, only an additive field and a narrower result set); and
  the retrofit (the exact one-module-per-maintenance-operation,
  idempotent, `/poc`-exposed shape already established by
  `retrofit_customer_hub_links`/`retrofit_people_from_emails`/
  `retrofit_email_sender_links`). No new tool, framework, storage
  mechanism, or trust-surface decision; nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.

#### Amendment — To-Do real data replaces the hardcoded-0 stub (REQ-SB-09-US-01)

`GET /my-day/todo` moves from "always `[]`, hardcoded, no vault read at
all" (REQ-SB-12-US-02's own deliberate placeholder — see that section's
own bullet, above) to a real read over `Work/Tasks/` notes, now that
REQ-SB-09 has resolved the Task source/schema/kind-folder question the
original placeholder was explicitly waiting on. Same shape as the
REQ-SB-22-US-01/REQ-SB-30-US-01 amendments above — an ordinary extension
of already-`Accepted` `my_day.py` structure, not a new one.

- **New `app/business/my_day.py::list_todo_items()`**, mirroring
  `list_email_items()`/`list_calendar_items()`'s existing shape exactly:
  reads every note under `vault_writer.list_notes_in_kind_folder("Tasks")`,
  projects down to `[{"subject": str, "customer": str | null, "due": str |
  null}]`. `customer` follows the same `_customer_or_null` convention
  already shared by Emails/Calendar. **Filters to still-open tasks only**
  (`frontmatter.get("status") != "Completed"`) — Scenario 8's own text
  ("lists each still-open captured task"); a completed task is still a
  real, captured Task note (Scenario 5), it is simply excluded from this
  particular read projection, the same "captured but filtered" shape
  REQ-SB-30-US-01's `important` filter already established for Emails (no
  `captured_count`-style second field is needed here, since no AC asks
  this pass' empty state to distinguish "nothing captured" from "captured
  but all complete" the way REQ-SB-30 needed to for importance-filtering).
  **No date-window filtering** — unlike `list_email_items`/
  `list_calendar_items`'s rolling-7-day window (REQ-SB-22-US-01), a Task
  has no natural "occurred near now" framing (mirroring
  `list_outlook_tasks`'s own no-date-window design, [ADR-027](ADR.md)); a
  far-future or undated task stays listed until it is completed, not until
  it ages out of a window.
- **`summary()`'s `todo` object** moves from the hardcoded `{"count": 0}`
  to `{"count": len(list_todo_items())}` — internally unchanged shape,
  now naturally reflecting real data, mirroring how `emails`/`calendar`
  already compute their own counts from their own list functions.
- **`GET /my-day/todo` response shape** is unchanged from
  `REQ-SB-12-US-02`'s own originally-declared placeholder shape
  (`[{"subject", "customer", "due"}]`) — the endpoint contract itself was
  already correctly speculated even before this story resolved what would
  actually populate it; only the underlying data source changes, from a
  hardcoded empty list to a real read.
- **No ADR.** A straight extension of already-`Accepted` structural
  decisions — the same `api → business → data_access` layering (ADR-003),
  the same `list_notes_in_kind_folder` primitive Emails/Calendar already
  use, and no new endpoint contract shape (the response shape was already
  declared, just previously unpopulated). Nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint — the capture-side
  half of this same story (the Tasks-folder read pipeline itself) is what
  needed [ADR-027](ADR.md); this read-path half does not.

### Agent detail panel — settings, actions, chat, unified history (REQ-SB-13-US-01, see [ADR-011](ADR.md))

- **New router `app/api/agents_router.py`**, `APIRouter(prefix="/agents")`,
  registered in `app/main.py`:
  - `GET /agents/{agent_id}` → `{"id", "name", "type", "settings":
    [{"key", "value"}], "actions": [{"id", "label"}]}` (Scenario 1).
  - `POST /agents/{agent_id}/actions/{action_id}` → triggers that action's
    registered handler synchronously (the Available Actions buttons —
    the direct-trigger surface, alongside chat, per the story's own
    Constraints), appends a `run_event` history entry, returns
    `{"status": "ok" | "error", "message": str}`.
  - `POST /agents/{agent_id}/chat` → body `{"message": str}` (Scenarios 2,
    7): matches the message against the agent's known action
    trigger-phrases (mechanism: [ADR-011](ADR.md)); on a match, invokes
    the same handler the direct-action endpoint would, appends both a
    `chat` and a `run_event` history entry, and replies confirming what
    was done; on no match, replies with a canned, honestly
    non-conversational fallback listing that agent's available actions.
    Returns `{"reply": str, "action_triggered": str | null}`.
  - `GET /agents/{agent_id}/history` → the unified chronological list
    (chat + run events merged) — Scenarios 3, 3b, 4.
- **New `app/business/agent_registry.py`** — a small, static, hardcoded
  dict of known agents (id/name/type/settings/actions + trigger-phrases),
  keyed by the same `data-agent-id` values the approved prototype and
  `REQ-SB-12-US-01`'s planned `mockAgents.ts` already use
  (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`,
  `vault-qa`). **Deliberately not vault-derived**, unlike
  `list_known_customers`/`list_known_kinds` — full reasoning: ADR-011.
  Only `email-capture`'s `run_capture_now` action has a real handler this
  pass, wired to the already-`Done` `email_classification.
  run_capture_and_record_completion` — the only capture pipeline that
  actually exists today. Every other declared action (Meeting/To-Do
  Capture's "Run capture now", People Notes' "Rebuild a person note",
  Vault Q&A's actions) has no handler this pass — invoking one (button or
  chat) returns an honest `status: "error"`/"not yet available" response,
  not a fabricated success. This story does not invent functionality for
  REQ-SB-08/09/03's own not-yet-built pipelines.
- **New `app/business/agent_chat.py::handle_chat_message(agent_id,
  message) -> dict`** — the keyword/phrase-matching mechanism itself.
  Full reasoning: ADR-011.
- **New `vault_writer.py` primitives, `append_agent_history_entry(agent_id:
  str, kind: str, text: str) -> None` / `load_agent_history(agent_id: str)
  -> list[dict]`**, backed by a new `.second-brain/
  agent_communication_history.json` (one file, `{agent_id: [{"kind":
  "chat_user" | "chat_agent" | "run_event", "text": str, "timestamp":
  iso8601}, ...]}`) — extends the existing `.second-brain/` flat-JSON-
  file state convention (`processed_email_ids.json`,
  `conversation_index.json`, `last_capture_run.json`) to a fourth concern,
  not a new storage mechanism. `email_classification.
  run_capture_and_record_completion` gains one additional call,
  `vault_writer.append_agent_history_entry("email-capture", "run_event",
  ...)`, alongside its existing `record_capture_run_completed()` call —
  so a capture run started by the hourly scheduler, the app-start
  trigger, `/poc/classify-emails`, or this story's new action/chat
  triggers all produce the exact same history entry, through the one
  shared entry point already established by ADR-005/ADR-008.

### Agent Sections & LLM Providers — mutable, persisted agent configuration (REQ-SB-18-US-01, REQ-SB-19-US-01, see [ADR-014](ADR.md))

Both stories give the user runtime, restart-surviving control over two new
per-agent properties — which Section an agent belongs to, and which LLM
Provider it uses — **without** making `app/business/agent_registry.py`
itself mutable. `ADR-011` point 2's reasoning ("which agents exist is
app/deployment configuration, not vault content") is preserved exactly:
`agent_registry.py` and `agent_chat.py` are untouched by this pass. Section
and Provider are two new, independent, persisted concerns composed
*alongside* the static registry, not inside it.

- **Two new sibling `.second-brain/` state files**, extending the existing
  flat-JSON-file convention to a fifth and sixth concern:
  - `.second-brain/agent_sections.json` — `{"sections": [{"id", "name"}],
    "assignments": {<agent_id>: <section_id>}}`. `id` is a slug
    (`vault_writer.tag_slug(name)`) fixed at creation and never
    regenerated on rename, so a rename only ever updates `name` in place —
    every existing `assignments` entry stays correct automatically
    (REQ-SB-18 Scenario 3's "the rename does not change assignment," true
    by construction).
  - `.second-brain/agent_providers.json` — `{"providers": [{"id", "name",
    "endpoint", "credential", "model"}], "assignments": {<agent_id>:
    <provider_id>}}`. Same slug-id-stable-across-edit shape.
  - `app/data_access/vault_writer.py` gains the paired
    `load_sections_state()`/`save_sections_state()` and
    `load_providers_state()`/`save_providers_state()` primitives — pure
    JSON I/O, no business rules, mirroring every existing state-file
    primitive's shape (`load_processed_email_ids()`/`mark_email_processed`,
    etc.).
- **Two new business modules own seeding, self-healing default assignment,
  CRUD, and the block-until-unused check:**
  - `app/business/section_registry.py` — seeds the starting 5 sections
    (Technical, Sales, Productivity, Customers, Products, per the PRD
    breadcrumb) on first read, persisting immediately; any known agent
    (`agent_registry.list_agents()`) absent from `assignments` is
    self-healingly assigned to the first section in creation order
    (`"technical"`) and persisted. Exposes `list_sections()`,
    `create_section(name)`, `rename_section(section_id, name)`,
    `delete_section(section_id) -> {"deleted": bool,
    "blocked_by_agent_ids": [str]}`, `get_agent_section(agent_id)`,
    `set_agent_section(agent_id, section_id)`.
  - `app/business/provider_registry.py` — seeds the pre-populated
    "Compass" Provider entry on first read, reading `app.config.settings.
    compass_base_url`/`compass_api_key`/`compass_model` once; any known
    agent absent from `assignments` is self-healingly assigned
    `"compass"`. Exposes the equivalent `list_providers()`,
    `create_provider(...)`, `update_provider(provider_id, ...)` (an
    omitted `credential` leaves the stored value untouched),
    `remove_provider(provider_id) -> {"deleted": bool,
    "blocked_by_agent_ids": [str]}`, `get_agent_provider(agent_id)`,
    `set_agent_provider(agent_id, provider_id)`, and
    `has_real_client(provider_id) -> bool` (a small hardcoded set,
    `{"compass"}`, mirroring `ADR-011` point 3's "declared but not yet
    backed by a real handler" pattern one layer up).
  - **The pre-seeded "Compass" Provider entry is a CRUD-editable
    representation only — editing it from Settings does not change the
    live Compass call path.** `app/data_access/compass_client.py`
    continues reading `app.config.settings.compass_*` directly and
    unconditionally, per REQ-SB-19's own Non-Goal against touching that
    `.env`-sourced mechanism, and per Scenario 6 ("no change in
    behaviour, endpoint, or credential used"). A known, explicit
    limitation for this pass, not a silent gap — see `ADR-014`.
  - Neither module imports the other; both import `agent_registry` only
    (to enumerate known agent ids) — the same "one business module
    composing another" shape already established
    (`people_extraction.py` → `customer_hub_linking.py`;
    `meeting_classification.py` → `people_extraction.py`).
- **Composition happens at the router, not inside `agent_registry.py`.**
  `app/api/agents_router.py`'s `GET /agents` and `GET /agents/{agent_id}`
  call `agent_registry.list_agents()`/`get_agent()` (unchanged) plus
  `section_registry.get_agent_section(agent_id)` and
  `provider_registry.get_agent_provider(agent_id)`, merging results:
  `GET /agents` → `[{"id", "name", "type", "section_id"}]`;
  `GET /agents/{agent_id}` → the existing `{"id", "name", "type",
  "settings", "actions"}` shape plus `"section_id"`, `"section_name"`,
  `"provider_id"`, `"provider_name"`, `"provider_available"`.
- **New API surface:**
  - `app/api/sections_router.py`, `APIRouter(prefix="/sections")`:
    `GET /sections` → `[{"id", "name", "agent_ids"}]`; `POST /sections`
    (`{"name"}`); `PATCH /sections/{section_id}` (`{"name"}`);
    `DELETE /sections/{section_id}` → `409` with a name-resolved message
    if `agent_ids` is non-empty (REQ-SB-18 Scenario 4b).
  - `app/api/providers_router.py`, `APIRouter(prefix="/providers")`:
    `GET /providers` → `[{"id", "name", "endpoint", "model",
    "credential_set", "is_default", "has_real_client", "agent_ids"}]` —
    **never a `credential` field**, in any response; `POST /providers`
    (`{"name", "endpoint", "credential", "model"}`); `PATCH /providers/
    {provider_id}` (any subset; an omitted `credential` preserves the
    stored value); `DELETE /providers/{provider_id}` → `409` with a
    name-resolved message if `agent_ids` is non-empty (REQ-SB-19
    Scenario 4b).
  - `app/api/agents_router.py` gains `PATCH /agents/{agent_id}` (body: any
    subset of `{"section_id", "provider_id"}`) → validates each supplied
    id exists (`404` otherwise), updates the assignment(s), returns the
    same merged detail shape as `GET /agents/{agent_id}`. One endpoint
    serves both REQ-SB-18's section-reassignment and REQ-SB-19's
    provider-picker, since both live on the same Agent Settings panel.
  - All three routers registered in `app/main.py`, matching the existing
    `app.include_router(...)` pattern.
- **Block-until-empty/unused: business layer returns a result dict, the
  router raises `409`.** `delete_section`/`remove_provider` never raise for
  ordinary control flow — they return `{"deleted": bool,
  "blocked_by_agent_ids": [str]}`, mirroring the existing `_invoke_action`/
  `trigger_action` result-dict convention. The router composes the `409`
  message by resolving each blocking id's display name via
  `agent_registry.get_agent(id)["name"]`.
- **Credential handling: plaintext at rest (the same trust boundary
  `compass_api_key` already lives inside), never returned by any
  endpoint.** No new encryption mechanism — no Accepted requirement asks
  for one, and `compass_api_key` is already plaintext in `.env` with no
  prior objection. `GET /providers` never includes a `credential` field,
  not even masked/partial; the approved prototype's masked
  `sk-live-••••••••••••` display is frontend-only decoration shown once
  `credential_set` is `true`.
- **Provider-availability enforcement for chat/action triggering** lives
  at the one shared funnel both the direct-action-trigger and
  chat-triggered paths already go through, `agents_router.py::
  _invoke_action`: before its existing `_ACTION_HANDLERS.get(...)` lookup,
  it resolves the agent's Provider and checks
  `provider_registry.has_real_client(provider_id)`; if unavailable, it
  short-circuits with an honest `{"status": "error", "message": "<Provider
  name> is not available yet — no client has been built for it."}`
  **without invoking the handler at all** — no silent fallback to Compass,
  no fabricated response (REQ-SB-19 Scenario 7). Safe for this pass since
  the only currently-real handler is itself LLM-backed via Compass; a
  future non-LLM-backed real action would need to revisit this blanket
  gate.
- **`layoutAgents.ts` becomes N-section-generic** — see "Frontend
  Application Architecture", above, and `ADR-014` point 6 for the full
  hub-angle/divider-line/neutral-hub-color reasoning.
- **Full reasoning, alternatives considered, and every consequence:**
  [ADR-014](ADR.md).

### Skills Repository — registration & per-agent access (REQ-SB-27-US-01, plumbing only — applies [ADR-015](ADR.md), no new ADR)

This story is the first concrete implementation of `ADR-015` point 9's
"`REQ-SB-27`'s skills become new `@mcp.tool()` entries" extensibility
path, resolved as an ordinary CRUD-pattern extension of `ADR-014`'s
already-`Accepted` "new persisted concern composed alongside a hardcoded
registry" shape, one concept over (skill *access*, not agent Sections/
Providers). `ADR-015` already settles the one genuinely architectural
question here ("what is a skill") — everything below is ordinary
`/plan-tasks` implementation latitude the ADR itself explicitly left open
(its own text: "the exact enforcement point is ordinary `/plan-tasks`
implementation latitude, not a further open architectural fork"). This
story is plumbing only — see the story's own `## Non-Goals` for what is
deliberately deferred (the first real skill's implementation).

- **Skill catalog: code-level, sourced from a new sibling module,
  `app/business/skill_tools.py`** (parallel to `app/business/
  vault_query_tools.py`, both siblings of `app/business/
  agent_orchestration/`, per `ADR-015` point 3's "a general capability,
  not orchestration-specific" placement) — holds the actual
  `@mcp.tool()`-decorated skill functions. This story registers exactly
  one illustrative stub skill (exact name/description left to the
  decomposer/coder, mirroring `ADR-015` point 11's "first tools are
  illustrative, not mandated by this pass" framing for
  `vault_query_tools.py`) whose body unconditionally returns the honest
  "not yet available" response (the story's own `## Constraints`
  stub-body pattern, mirroring `model_factory.py`'s / `ADR-011` point 3's
  / `ADR-014` point 7's same honesty shape one layer over) — demonstrating
  Scenario 1 (registration) and Scenario 4 (honest non-fabrication)
  without building the first real skill. `app/api/mcp_server.py` registers
  `skill_tools.py`'s functions as `@mcp.tool()`s the same way it already
  registers `vault_query_tools.py`'s — one shared server (`ADR-015` point
  9), two source modules feeding it.
- **The catalog is not derived by introspecting the MCP server's live,
  full tool list** (which would also surface `vault_query_tools.py`'s
  non-skill tools). `skill_tools.py` additionally exposes its own small,
  literal, enumerable registry of skill metadata (`id`, `name`,
  `description`), mirroring `agent_registry.py`'s own `AGENTS: dict` shape
  one concept over, that `skill_registry.py` reads directly — this
  sidesteps relying on any MCP SDK-level tagging/namespacing feature this
  project hasn't verified exists, per `ADR-015` point 2's own "genuinely
  unverified fact, not silently assumed" discipline.
- **New business module, `app/business/skill_registry.py`** — the new,
  persisted, user-mutable concern (mirrors `section_registry.py`/
  `provider_registry.py`'s `ADR-014` shape exactly): `list_skills()`
  (reads `skill_tools.py`'s catalog, unaffected by agent-access state),
  `list_agent_skills(agent_id)`, `grant_skill_access(agent_id, skill_id)
  -> bool`, `revoke_skill_access(agent_id, skill_id) -> bool`,
  `has_skill_access(agent_id, skill_id) -> bool` (the one reusable
  primitive both this story's own invocation entry point, below, and a
  future `agent_orchestration/` tool-binding step are expected to call —
  per the story's own Constraints, that graph-level tool-binding step is
  "most plausibly" where enforcement additionally lives once `REQ-SB-25`/
  `REQ-SB-20` are further along; designed now so that future integration
  reuses this exact check rather than duplicating it), and
  `invoke_skill(agent_id, skill_id) -> dict` (Scenarios 3/4's
  plumbing-only invocation path, below). **Deliberately no self-healing
  default-assignment** (unlike `section_registry.py`/`provider_registry.py`,
  which self-heal every known agent onto a default) — Scenario 2's
  explicit-grant-only model is this story's own scoped ACs, and which
  skills (if any) should default to all-agents access is an open question
  the story's own `## Non-Goals` explicitly leaves unresolved; no agent is
  auto-granted any skill by this pass.
- **New persisted state, `.second-brain/agent_skills.json`** —
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}`, extending the
  established flat-JSON-file convention to a further concern (alongside
  `processed_email_ids.json`, `conversation_index.json`,
  `last_capture_run.json`, `processed_meeting_ids.json`,
  `agent_communication_history.json`, `agent_sections.json`/
  `agent_providers.json`). **No top-level catalog list** in this file
  (unlike `agent_sections.json`'s `"sections"` array) — unlike Sections,
  the skill catalog itself is never user-created or persisted; it is
  `skill_tools.py`'s own code-level registry, above. New
  `vault_writer.py` primitives, `load_skills_state()`/`save_skills_state()`,
  mirror `load_sections_state()`/`save_sections_state()`'s exact pure-I/O
  shape.
- **New API surface, `app/api/skills_router.py`**:
  - `GET /skills` → `[{"id", "name", "description"}]` — the catalog
    (Scenario 1).
  - `GET /agents/{agent_id}/skills` → that agent's granted skills
    (Scenario 2).
  - `POST /agents/{agent_id}/skills/{skill_id}` → grants access (Scenario
    2); `404` if either id is unknown.
  - `DELETE /agents/{agent_id}/skills/{skill_id}` → revokes access
    (Scenario 5).
  - `POST /agents/{agent_id}/skills/{skill_id}/invoke` → the plumbing-only
    invocation entry point (Scenarios 3, 4): `skill_registry.invoke_skill`
    checks `has_skill_access` first — no access returns a refusal result
    distinct from "not available" (Scenario 3); granted access invokes
    `skill_tools.py`'s stub function in-process and returns its honest
    "not yet available" result (Scenario 4) verbatim, never a fabricated
    one. **Chosen over extending `agent_registry.py`'s static per-agent
    action/trigger-phrase mechanism** (`ADR-011`) — skills are
    cross-cutting and dynamically grantable to any agent, unlike
    `agent_registry.py`'s fixed per-agent action list, and this keeps
    `agent_registry.py`/`agent_chat.py` untouched (`ADR-011` point 2's
    "agent identity/actions stay hardcoded" reasoning, undisturbed).
    Satisfies the story's own Constraint that an invocation entry point
    can "reuse whatever mechanism already triggers agent actions today...
    the exact entry point is an implementation detail left to
    `/plan-tasks`" — this is that `/plan-tasks` decision. Registered in
    `app/main.py` alongside the existing routers.
- **Relationship to `app/business/agent_orchestration/` — not built by
  this story, genuinely depended on.** As of this pass, `agent_
  orchestration/`/`app/api/mcp_server.py` do not yet exist in code
  (`ADR-015`'s own scaffolding, expected to land as part of
  `REQ-SB-25-US-01`); this story's `skill_tools.py` registration onto the
  shared MCP server, and `skills_router.py`'s invocation path, both
  require that scaffolding to exist first. This is an ordinary task-level
  `depends_on` for the decomposer to wire, not a new architectural
  question — already named in the story's own `## Dependencies`.
- **No ADR.** Every decision above is a direct, same-shape extension of
  already-`Accepted` structural decisions — `ADR-003`'s layering,
  `ADR-014`'s "new persisted concern composed alongside a hardcoded
  registry" pattern, and `ADR-015`'s own already-settled "skill capability
  = code-registered `@mcp.tool()` entry; skill access = a new persisted,
  per-agent concern" resolution (see the story's own `## Context`/
  `## Constraints`) — with no new tool, framework, storage mechanism, or
  trust-surface decision, and nothing here contradicts any `Accepted`
  ADR, the PRD, or a `MEMORY.md` constraint.

### Agent Working Modes & Pending Approvals (REQ-SB-21-US-01, see [ADR-018](ADR.md) + [ADR-020](ADR.md))

Every agent gains a third new mutable, persisted property — its working
mode (Autonomous/Supervised/Manual) — composed *alongside*
`agent_registry.py` exactly the way Sections/Providers already are
(`ADR-014`), plus a genuinely new concern neither of those introduced: a
**Pending Approvals workflow**, since "Supervised" means a proposed
action must be durably held, visible, and separately resolved (approved
or declined), not just read/written like a simple property. Full
reasoning, every alternative considered, and every consequence:
[ADR-018](ADR.md) (state files, registries, Approve/Decline endpoints,
background-pipeline gate, `"proposal"` history kind, merged
`working_mode` field — all still current) and
[ADR-020](ADR.md) (the chat/direct-action gate's corrected two-axis
design, superseding `ADR-018` points 3 and 5 only, `ESCALATIONS.md` →
`ESC-013`).

- **`app/business/agent_registry.py` gains a `"mutates": bool` field on
  every action definition** (still a fully static, hardcoded module,
  `ADR-011` point 2 unaffected) plus a new `get_action(agent_id,
  action_id) -> dict | None` lookup helper. Today's real classification:
  `run_capture_now` and `rebuild_person_note` → `True` (write to the
  vault); `pause_schedule` → `True` (a control-plane state mutation, even
  though it has no real handler yet); `view_last_run`, `ask_question`,
  `view_channel_status` → `False` (read-only). An action id the gate
  cannot resolve defaults fail-safe to `True` (see [ADR-020](ADR.md)).

- **Two new sibling `.second-brain/` state files (8th, 9th):**
  `agent_working_modes.json` (`{"assignments": {<agent_id>: "autonomous" |
  "supervised" | "manual"}}` — a fixed 3-value enum, no user-created
  catalog half the way Sections/Providers have one) and
  `agent_pending_approvals.json` (`{"pending": [{"id", "agent_id",
  "trigger": "chat" | "direct" | "background" | "hub_routed", "action_id",
  "description", "status": "pending" | "approved" | "declined",
  "created_at", "resolved_at"}, ...]}` — `"hub_routed"` added by
  [ADR-020](ADR.md), reserved for a future story; no code path produces it
  yet). `app/data_access/vault_writer.py` gains the
  paired `load_working_modes_state()`/`save_working_modes_state()` and
  `load_pending_approvals_state()`/`save_pending_approvals_state()`
  primitives, pure I/O, mirroring every existing state-file primitive's
  shape.
- **`app/business/working_mode_registry.py`** (new) — self-healing
  default assignment (`"autonomous"`, the operator-resolved,
  behavior-preserving default) for any known agent absent from
  `assignments`, folded into one `_load_state()` (no separate seed step —
  there is no non-trivial starting catalog to compute, unlike Sections).
  Exposes `get_agent_working_mode(agent_id) -> str` (never `None`) and
  `set_agent_working_mode(agent_id, mode) -> bool`.
- **`app/business/pending_approval_registry.py`** (new, a separate
  concern from working mode itself — a workflow record with a lifecycle,
  not a settable property) — `list_pending_approvals(status=None,
  agent_id=None)`, `get_pending_approval(approval_id)`,
  `create_pending_approval(agent_id, trigger, action_id, description)`
  (idempotent for `trigger="background"` only — reuses an existing
  unresolved record for that agent rather than piling up a duplicate
  every scheduler tick; `"chat"`/`"direct"` proposals are never
  deduplicated), `resolve_pending_approval(approval_id, status)`. `id`s
  are `uuid.uuid4().hex[:12]` — this project's first `uuid` usage
  (stdlib only, no new dependency).
- **The chat/direct-action gate: `agents_router.py::_invoke_action` split
  into a thin gate plus the existing unconditional dispatch, renamed
  `_execute_action`.** The gate takes a new `trigger: "chat" | "direct" |
  "hub_routed"` parameter (`trigger_action` passes `"direct"`, `chat`'s
  matched-action branch passes `"chat"`, `"hub_routed"` is reserved for a
  future story — no call site produces it yet, see below; the story's own
  Available-Actions-button question is resolved here: yes, same gate,
  since both already share this one funnel per `ADR-011`). **Corrected
  two-axis check ([ADR-020](ADR.md), supersedes `ADR-018` point 3):**
  resolves both `mode = working_mode_registry.get_agent_working_mode(...)`
  and `action = agent_registry.get_action(agent_id, action_id)`. **Manual
  + `trigger == "hub_routed"`** refuses outright (no pending record, no
  execution — currently unreachable in practice, since `ADR-017`'s routing
  node never invokes a target agent's action, but recorded for when a
  future story adds that). **Supervised + `action["mutates"] is True`**
  short-circuits before the existing Provider-availability check
  (`ADR-014` point 7) or the handler dispatch — creates a pending-approval
  record and returns `{"status": "pending", "message": ...,
  "pending_approval_id": ...}` — **regardless of `trigger`** (chat,
  direct, or hub_routed). **Supervised + `action["mutates"] is False`**
  (a read-only action), **Autonomous** (any trigger), and **Manual** with
  `trigger` in `("chat", "direct")` all fall straight through to
  `_execute_action`, unchanged from today's behaviour.
- **Manual vs. Supervised, corrected ([ADR-020](ADR.md), supersedes
  `ADR-018` point 5):** the two modes now gate on genuinely different
  axes, not the same trigger-source switch. **Manual** gates on **trigger
  source only** — a direct human ask (a trigger-phrase match or an
  Available Actions click, the one mechanism this codebase has for
  "explicitly asking," `ADR-011`; no NLU exists, `ADR-007`) always
  executes immediately, whether the action reads or writes; neither a
  background/scheduled trigger (below) nor another agent's Hub-routed
  request ever executes. **Supervised** gates on the **action's own
  read-only-vs-mutating nature only** — a read-only action (`view_last_run`,
  `ask_question`, `view_channel_status`) proceeds immediately for any
  trigger, identical to Autonomous; a write/mutating action always
  proposes-and-waits, for any trigger (chat, direct, or background). The
  two modes' behaviour happens to coincide for the background trigger
  today (both real background pipelines only ever run mutating actions —
  see below), but for the chat/direct funnel they now genuinely diverge
  by action nature, not by whether the trigger was background or not.
- **The background-pipeline gate: two explicit per-agent checks inside
  `email_classification.py::run_capture_and_record_completion`** (not a
  generic dispatch loop — matches this codebase's explicit-sibling-code
  style), one for `"email-capture"` before its `classify_recent_emails`
  call, one for `"meeting-capture"` before its
  `meeting_classification.classify_recent_meetings()` call. Autonomous
  runs the step (via a new shared `run_capture_for_agent(agent_id, limit)`
  helper, reused by the approval path below); Supervised creates a
  `trigger="background"` pending-approval record instead of running it;
  Manual skips silently — no record, no history entry at all. **Unchanged
  by [ADR-020](ADR.md):** both gated steps are always `"mutates": True`
  actions today, so the corrected mutates-based Supervised rule and the
  original trigger-based rule produce the identical outcome here by
  construction — the behavioural change from `ADR-020` is confined to the
  chat/direct funnel, above. `app/scheduling/capture_scheduler.py`
  requires **zero changes** — this conditionality lives entirely inside
  the one function it already treats as an opaque unit, extending (not
  reopening) `ADR-005`/`ADR-008` point 4. **Amendment (REQ-SB-09-US-01,
  [ADR-027](ADR.md)):** `"todo-capture"` gains this same third gated
  block, structurally identical to the two above — see "Task Notes &
  Outlook-Tasks Capture", below, and [ADR-027](ADR.md) point 5 for the
  full reasoning. This sentence previously read "`todo-capture` has no
  real background pipeline yet" — no longer current, corrected in place
  rather than left stale.
- **New API surface, `app/api/pending_approvals_router.py`**,
  `APIRouter(prefix="/pending-approvals")`: `GET /pending-approvals`
  (optional `status`/`agent_id` filters), `GET /pending-approvals/{id}`,
  `POST /pending-approvals/{id}/approve` (`404`/`409` guards; executes
  the deferred action **directly** via `_execute_action`/
  `run_capture_for_agent` — bypassing the working-mode gate entirely,
  since re-entering it would find the agent still Supervised and defer
  forever instead of ever running), `POST /pending-approvals/{id}/decline`
  (same guards; discards, no action taken). Both are agent-agnostic and
  shared by every UI surface that can trigger them — the approved
  prototype's inline chat `.chat-proposal` state-switcher and the
  standalone Pending Approvals page call the identical two endpoints.
  Registered in `app/main.py`.
- **Communication history gains one new entry kind, `"proposal"`**
  (additive to `ADR-011`'s `"chat_user" | "chat_agent" | "run_event"`
  enum), carrying an optional `pending_approval_id`. Created by both
  gates above at the moment a Supervised proposal is created. The
  frontend renders it as the approved prototype's `.chat-proposal` card,
  resolving its **live** Pending/Approved/Declined state via `GET
  /pending-approvals/{id}` (the history entry's own text never changes
  after creation — history stays append-only).
- **`GET /agents`/`GET /agents/{agent_id}` gain a merged `working_mode`
  field; `PATCH /agents/{agent_id}` gains an optional `working_mode`
  body field** (`400` on an invalid enum value — distinct from the
  existing `404 Unknown section/provider` lookup-failure pattern).
  Composition happens at the router, exactly like `section_id`/
  `provider_id` — `agent_registry.py` stays fully unmodified.
- **`app/business/my_day.py`/`app/api/my_day_router.py` are untouched.**
  The new My Day "Pending Approvals" 5th dashboard card and its
  `/my-day/approvals` drill-down page fetch `GET /pending-approvals`
  directly — Pending Approvals is a cross-agent workflow concept, not a
  read-only projection over Email/Meeting notes the way My Day's existing
  three sections are, so it does not belong inside `my_day.py`'s
  aggregation.
- **Frontend:** `AgentDetailPanel.tsx` gains a Working-mode `<select>`
  kv-row (same pattern as the Section/Provider rows) and a `.chat-proposal`
  card renderer for `"proposal"`-kind history entries (Approve/Decline
  buttons calling the new endpoints, live-polling the record's own
  status); `agentsApiClient.ts`'s shared assignment call gains
  `working_mode?`, plus new `fetchPendingApprovals()`/
  `approvePendingApproval(id)`/`declinePendingApproval(id)` calls (new
  `pendingApprovalsApiClient.ts`, co-located under `features/agents-map/`,
  reused by both the detail panel and the new My Day page); a new
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` at route
  `/my-day/approvals` (mirroring `MyDayCalendarPage.tsx`'s exact
  `.item-list`/`.item-row` shape, `.item-row-actions` holding
  Approve/Decline buttons), added to `App.tsx`'s route table and
  `MyDayPage.tsx`'s card grid as a 5th `SECTIONS` entry.

## System Health View — read-only status aggregation + chat-path crash-gap fix (REQ-SB-31-US-01)

A new top-level nav page surfacing whether Second Brain's own moving
pieces are genuinely working — MCP/agent-orchestration reachability,
per-agent Provider availability, last capture run completion — plus a
separate, backend-only robustness fix closing a real gap in the chat
path's own exception handling. **No new ADR** — see "No ADR" note at the
end of this section for the full reasoning; every piece below is an
ordinary, same-shape extension of already-`Accepted` structural
decisions.

- **New business module `app/business/system_health.py`** — a **read-only
  aggregation** module, the same shape as `app/business/my_day.py`
  (REQ-SB-12-US-02): it writes no new persisted state at all, composing
  only already-existing signals:
  - `mcp_mount_reachable() -> bool` — the one real (but local, in-process,
    zero-external-cost) HTTP call this story adds: a bare `GET` against
    the same hardcoded loopback `http://127.0.0.1:8001/mcp` URL
    `agent_orchestration/mcp_client.py` already calls (this project's own
    documented port convention — `tools/run-backend.cmd --port 8001`,
    `.claude/launch.json` — reused as-is, not a new port-discovery
    mechanism). `True` only on an `HTTP 406` response (the mount's own
    proven "alive" signal, confirmed live 2026-08-12 per the story's own
    Context); any other status code, connection error, or timeout →
    `False`. A short `httpx.get(..., timeout=...)` call, mirroring
    `compass_client.py`'s existing synchronous `httpx` usage — no new HTTP
    library.
  - Provider availability is **not recomputed** — `provider_registry.
    list_providers()` (`REQ-SB-19-US-01`, `Done`) already returns each
    Provider rolled up with `has_real_client`/`agent_ids`, exactly the
    "per distinct Provider, from each agent's own selection" shape this
    story's Context calls for. `system_health.py` calls it directly
    (business-to-business composition, the same shape
    `people_extraction.py` already uses to compose
    `customer_hub_linking.py`'s primitives) rather than re-deriving
    anything from `GET /agents`.
  - `list_disabled_agents() -> list[dict]` — iterates
    `agent_registry.list_agents()`, and for each agent whose
    `provider_registry.get_agent_provider()` is `None` or fails
    `has_real_client()`, includes it as `{"agent_id", "agent_name",
    "provider_name"}`. This is the one new roll-up direction Providers
    CRUD didn't already need — "which agents are Disabled," not "which
    Provider serves which agents" — computed here, not added to
    `provider_registry.py` itself (which stays exactly `REQ-SB-19`'s
    `Done` shape, unmodified).
  - `last_capture_run() -> dict | None` — a thin passthrough to
    `vault_writer.load_last_capture_run()` (`REQ-SB-07-US-01`, `Done`),
    unchanged, returning its existing `{"finished_at": iso8601}` or `None`
    as-is — no new interpretation, no staleness/pass-fail judgment added
    (the story's own Non-Goals).
  - `get_system_health() -> dict` composes the four signals above into one
    response, recomputed **fresh on every call** — no caching layer, the
    same "recomputes fresh on every call, never cached" precedent already
    established for My Day's rolling window (`REQ-SB-22-US-01`), satisfying
    Scenario 7 by construction (nothing to invalidate).
- **New router `app/api/system_health_router.py`**,
  `APIRouter(prefix="/system-health")`, one endpoint, `GET
  /system-health`, returning `system_health.get_system_health()` verbatim.
  Registered in `app/main.py` alongside the existing routers — the same
  `api → business → data_access` layering (`ADR-003`) every other router
  already follows; this router calls `system_health.py` only, no direct
  `data_access`/`provider_registry`/`agent_registry` reach-around.
- **Frontend:** a new page, `src/frontend/src/pages/SystemHealthPage.tsx`,
  at route `/system-health` (added to `App.tsx`'s route table, wrapped in
  the existing `<AppShell>` like every other page), plus a new
  `src/frontend/src/features/system-health/client.ts` (`fetchSystemHealth()`
  wrapping `GET /system-health` via the existing `api/client.ts` `fetch`
  convention, `ADR-010`). `Sidebar.tsx` gains one new `<NavLink>` ("System
  Health"), positioned after Settings — matching the approved prototype's
  own sidebar order across every prototype page. Renders the four regions
  the approved prototype (`html-prototype/system-health.html`) already
  validates — Health Issues (composed client-side from `mcp.reachable ===
  false` plus each entry in `disabled_agents`, mirroring the prototype's
  own "two different reasons render two different rows" framing), MCP
  status, Providers status, and Last capture run — reusing only
  already-ported classes (`.card`, `.badge*`, `.kv-list`, `.item-list`,
  `.empty-state`) with **zero new CSS**, per the prototype's own "composed
  entirely from existing tokens/components" header note. A manual Refresh
  affordance re-calls `fetchSystemHealth()`; no polling/auto-refresh
  interval (the story's own Non-Goals).
- **Separate, backend-only fix: `app/business/agent_orchestration/
  graph.py::run_agent_conversation`'s own body** (`REQ-SB-25-US-01`,
  `Done`) had one remaining, real gap — its own `await mcp_client.
  load_vault_query_tools()` and `await _GRAPH.ainvoke(initial_state)`
  calls were not wrapped in the honest-failure-funnel pattern `_call_model`
  (the graph's own node, inside `_GRAPH`) already uses (`ADR-015`'s
  mechanism decision). Scenario 8 closes this by wrapping both remaining
  calls in the identical `try/except Exception as exc: return {"error":
  f"..."}` shape — applying an already-`Accepted` pattern to a second call
  site in the same function, not inventing a new one. This is unrelated to
  the System Health page's own read path (no new region reads this fix's
  outcome — the story's own Non-Goals: no persisted "last unhandled
  exception" signal exists yet) and has no dependency on
  `system_health.py`/`system_health_router.py` — it can be built
  independently, first if desired.
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the aggregation module mirrors
  `my_day.py`'s exact "read-only, composes existing business/data_access
  signals, no new persisted state" shape (`REQ-SB-12-US-02`'s own "No ADR"
  reasoning applies here even more directly, since this module persists
  *nothing* new at all, not even an additive field); the router is a
  straight `ADR-003`-layered addition, the same shape as `my_day_router.py`/
  `agents_router.py`; the frontend page is an ordinary new route/page/nav
  item within `ADR-010`'s already-`Accepted` routing/styling/component
  conventions (the same shape `BUGFIX-02-US-01`'s new `SectionDrilldown.tsx`
  page-level component added without a new ADR); and the `graph.py` fix
  applies `ADR-015`'s already-established honest-failure-funnel pattern to
  a second call site, the same "extends, does not reopen" shape
  `REQ-SB-33-US-01`'s grounding-guardrail pass used on the same function
  family. No new tool, framework, storage mechanism, external round-trip,
  or trust-surface decision; nothing here contradicts any `Accepted` ADR,
  the PRD, or a `MEMORY.md` constraint. This also does not reopen or edit
  `ADR-011` point 3 / `ADR-014` point 7 — the Disabled/Health-Issue display
  override is a per-view UI presentation decision (this story's own
  Constraints/Notes), not a change to either ADR's underlying honesty
  convention or to any other screen relying on it.

## Agent Activity & Error Observability (REQ-SB-11-US-01)

A new top-level nav page — related to, but explicitly not overlapping,
System Health (above): System Health is a current-snapshot status board
("is each piece healthy right now"); this page is a chronological
history/log ("every background capture run, in order, with its own
recorded outcome"), plus one net-new channel-status check System Health
does not cover (direct Outlook COM reachability). **No new ADR** — see
"No ADR" note at the end of this section; every piece below is an
ordinary, same-shape extension of already-`Accepted` structural
decisions, the same class of "no new ADR" call `REQ-SB-31-US-01`'s own
architect pass made for its structurally identical read-only status page.

- **Honest-failure-recording fix — `app/business/email_classification.py::
  run_capture_and_record_completion`, this file only.** Two confirmed,
  real gaps (the story's own Context, grounded in direct code reading):
  (1) meeting-capture's Autonomous branch calls `run_capture_for_agent(
  "meeting-capture")` and discards the result with no history entry at
  all — the only capture step of the two that had no success-recording
  parity; (2) neither capture step's call inside this function is wrapped
  in a `try/except` — an exception escaping `classify_recent_emails`'s or
  `classify_recent_meetings`'s own per-item handling (e.g.
  `outlook_com.OutlookUnavailable` if Outlook desktop isn't running)
  propagates all the way up through `capture_scheduler.run_capture_if_idle`
  uncaught, with zero history entry ever written.
  - **Fix site: the call site inside `run_capture_and_record_completion`,
    not inside `classify_recent_emails`/`classify_recent_meetings`
    themselves.** This mirrors `ADR-015`'s own established
    honest-failure-funnel shape exactly — `run_agent_conversation`'s
    `REQ-SB-31-US-01` Scenario-8 fix wraps the *call* to
    `mcp_client.load_vault_query_tools()`/`_GRAPH.ainvoke(...)` at the
    orchestrating function's own body, not inside those callees — never
    changing either capture function's own `list[dict]`-of-per-item-
    results return contract. Each of the two capture steps (email,
    meeting) gets its own independent `try/except Exception as exc:` around
    its `run_capture_for_agent(...)` call, so one agent's failure this
    tick can never suppress the other's success being recorded (Scenario
    3) — the same "independent per-branch funnel" shape, not one
    all-or-nothing `try` around the whole function.
  - **Clarifies the story's own Constraints wording.** "Each capture
    pipeline's own top-level entry point (`email_classification.py`,
    `meeting_classification.py`)" names the two *pipelines*/files this
    scope covers (as distinct from, say, a future to-do-capture pipeline),
    not a mandate to edit both files — `run_capture_and_record_completion`
    is the one genuine top-level orchestration entry point for both
    pipelines today, and it already lives entirely in
    `email_classification.py`. `meeting_classification.py` itself needs no
    change: its `classify_recent_meetings()` keeps its existing shape
    unedited, exactly as `REQ-SB-31-US-01`'s own Non-Goal ("no general
    exception-catching/logging middleware") already establishes as the
    right boundary — the funnel closes the gap one level up, at the one
    place both pipelines are already orchestrated, not by adding
    unrelated error-handling inside a pipeline's own per-item loop.
  - **New `kind` value: `"run_error"`**, alongside the existing
    `"run_event"` / `"chat_user"` / `"chat_agent"` / `"proposal"` set
    (`vault_writer.append_agent_history_entry`, unmodified signature) —
    chosen over adding an `"outcome"` field to the existing `"run_event"`
    shape because it needs zero changes to either existing consumer of
    `"kind"`: `agent_orchestration/state.py::history_entries_to_messages`
    already excludes every kind it doesn't explicitly match
    (`"chat_user"`/`"chat_agent"` only — confirmed by direct reading, a
    new kind falls through its existing no-op case unchanged), and
    `AgentDetailPanel.tsx`'s Communication History tab already renders any
    non-`"proposal"` kind via its existing generic `entry.text` +
    timestamp fallback (confirmed by direct reading — no `switch`/kind
    check beyond the `"proposal"` branch). Both of `REQ-SB-13-US-01`'s own
    consumers of this file are therefore genuinely unaffected, confirming
    that story's own Dependencies claim ("its per-agent panel is
    unaffected/unchanged by this story") without needing to touch either
    file.
  - **`vault_writer.record_capture_run_completed()`'s existing
    "only reached when nothing raised" semantics are deliberately
    preserved, not silently broken by this fix.** `REQ-SB-31-US-01`'s own
    Context already documents `last_capture_run.json`'s `finished_at` as a
    proxy failure signal precisely *because* an escaping exception used to
    mean this call was never reached — a currently-failing run shows up as
    an "increasingly stale timestamp," per that already-`Done` story's own
    recorded reasoning. Now that both capture steps' exceptions are
    funneled into a recorded history entry instead of propagating, this
    call would otherwise fire unconditionally every tick regardless of a
    funneled failure, quietly invalidating that already-documented System
    Health signal. Fix: `run_capture_and_record_completion` tracks whether
    either step's own `try/except` fired this tick (two local booleans) and
    calls `vault_writer.record_capture_run_completed()` only when neither
    did — the exact same observable `last_capture_run.json` behavior as
    before this fix, on top of the new, additional `"run_error"` history
    entry REQ-SB-11 needs. This is a considered design choice (grounded in
    a real, already-`Done` story's own documented reliance on the prior
    behavior), not an assumption filling an unaddressed gap — recorded here
    for durability since neither story's own Acceptance Criteria says so
    explicitly.
- **New business module `app/business/agent_activity.py`** — a **read-only
  aggregation** module, the same shape as `app/business/system_health.py`/
  `app/business/my_day.py`: writes no new persisted state, composes only
  already-existing signals, recomputes fresh on every call (Scenario 7):
  - `list_activity_log() -> list[dict]` — iterates every known agent via
    `agent_registry.list_agents()` (the same "discover ids generically,
    don't hardcode two capture agents" precedent the story's own
    Dependencies section calls for, so a future `todo-capture` agent's
    entries appear with zero code change here), reads each one's
    `vault_writer.load_agent_history(agent_id)`, keeps only `"run_event"`/
    `"run_error"`-kind entries (excluding `"chat_user"`/`"chat_agent"`/
    `"proposal"`, per the story's own Constraints scope), attaches
    `agent_name` (resolved via `agent_registry.get_agent`, the same
    display-name-resolution shape `system_health.py::
    _providers_with_agent_names` already established), and merges/sorts
    the combined list newest-first by `timestamp` — matching the approved
    prototype's own "newest first" ordering.
  - `get_agent_activity() -> dict` composes `list_activity_log()` and one
    new Outlook-reachability read (below) into `{"activity_log": [...],
    "outlook_channel": {"reachable": bool, "detail": str | None}}`.
- **New `outlook_com.py::check_reachable() -> dict`** — the one new,
  lightweight, real (but local, zero-external-cost) check this story
  needs, mirroring `system_health.py::mcp_mount_reachable()`'s own "reuse
  an already-proven connection mechanism, one cheap new check" precedent:
  attempts the exact same `Dispatch("Outlook.Application")` →
  `GetNamespace("MAPI")` connection every existing Outlook read (mail,
  calendar) already makes via the module's own `_connect_namespace()`,
  purely to report reachability. Returns `{"reachable": True, "detail":
  None}` on success, or `{"reachable": False, "detail": str(exc)}` — the
  real `OutlookUnavailable` message, e.g. "couldn't connect to Outlook —
  is it running? (...)" — on failure; never raises past its own body,
  same "honest, never left to propagate" discipline `mcp_mount_reachable()`
  already established. Sited in `data_access` (not composed ad hoc from
  `agent_activity.py` reaching into `outlook_com.py`'s private
  `_connect_namespace`) because every other Outlook COM mechanic
  (`pythoncom.CoInitialize()`, the `Dispatch`/`GetNamespace` calls, and
  now their honest failure-message construction) already lives there —
  `agent_activity.py` calls this one new public function only, the
  ordinary `api → business → data_access` layering (`ADR-003`) every
  other business module already follows.
- **New router `app/api/agent_activity_router.py`**,
  `APIRouter(prefix="/agent-activity")`, one endpoint, `GET
  /agent-activity`, returning `agent_activity.get_agent_activity()`
  verbatim. Registered in `app/main.py` alongside the existing routers —
  calls `agent_activity.py` only, no direct `data_access`/
  `agent_registry`/`outlook_com` reach-around.
- **Frontend:** a new page, `src/frontend/src/pages/AgentActivityPage.tsx`,
  at route `/agent-activity` (added to `App.tsx`'s route table, wrapped in
  the existing `<AppShell>`), plus a new `src/frontend/src/features/
  agent-activity/client.ts` (`fetchAgentActivity()` wrapping `GET
  /agent-activity` via the existing `api/client.ts` `fetch` convention,
  `ADR-010`). `Sidebar.tsx` gains one new `<NavLink>` ("Agent Activity"),
  positioned after System Health — matching the approved prototype's own
  sidebar order across every prototype page. Renders the two regions the
  approved prototype (`html-prototype/agent-activity.html`) already
  validates — the chronological Activity log (each entry's own
  success/error badge driven by `kind === "run_error"`, an error entry's
  detail rendered as a muted line beneath its summary, an honest
  empty-state when the log is empty) and the Outlook channel-status card
  (`.badge-success`/`.badge-danger` off `outlook_channel.reachable`, the
  real `detail` message shown on the unreachable state) — reusing only
  already-ported classes (`.log-list`/`.log-item`, `.badge*`, `.kv-list`,
  `.empty-state`) with **zero new CSS**, per the prototype's own "composed
  entirely from existing tokens/components" header note. A manual Refresh
  affordance re-calls `fetchAgentActivity()`; no polling/auto-refresh
  interval (the story's own Non-Goals).
- **No ADR.** Every piece above is an ordinary, same-shape extension of
  already-`Accepted` structural decisions: the honest-failure-recording
  fix applies `ADR-015`'s already-established call-site honest-failure-
  funnel pattern to a second orchestration function (extending, not
  reopening, `ADR-015` — the same "extends, does not reopen" shape
  `REQ-SB-31-US-01`'s own Scenario-8 fix and `REQ-SB-33-US-01`'s grounding-
  guardrail pass both already used on the same function family); the
  aggregation module mirrors `system_health.py`/`my_day.py`'s exact
  "read-only, composes existing business/data_access signals, no new
  persisted state" shape; `outlook_com.check_reachable()` is a same-shape
  sibling to `mcp_mount_reachable()`'s "one new lightweight in-process
  check reusing an already-proven mechanism" precedent, sited in
  `data_access` per `ADR-003`'s existing layering (Outlook COM mechanics
  already live there, nowhere else); the router is a straight
  `ADR-003`-layered addition, the same shape as `system_health_router.py`/
  `my_day_router.py`; the frontend page is an ordinary new route/page/nav
  item within `ADR-010`'s already-`Accepted` routing/styling/component
  conventions. No new tool, framework, storage mechanism, external
  round-trip, or trust-surface decision; nothing here contradicts any
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint. This also does not
  reopen or edit `ADR-011`'s `"kind"` enum — `"run_error"` is an additive
  value, the same "grow the set, don't redefine it" shape `ADR-018` point
  7 already used when it added `"proposal"` to the same field.

## In-App Agent Orchestration (LangGraph) & Shared MCP Server (REQ-SB-20, REQ-SB-25, REQ-SB-26, REQ-SB-27, see [ADR-015](ADR.md))

`ADR-007`'s original "no agent-orchestration framework in Second Brain's
own stack" stance is superseded by [ADR-015](ADR.md), **bounded
specifically to Second Brain's own in-app Agents Map agent behavior** —
chat (`REQ-SB-25`), Section-Hub routing (`REQ-SB-20`), agent memory
(`REQ-SB-26`), and skill invocation (`REQ-SB-27`). Hermes's own
orchestration for its external-channel integration (`REQ-SB-03`, not yet
built) is untouched — `ADR-007`'s "Hermes owns orchestration on its own
side of the integration boundary" claim carries forward unchanged. This
section describes the mechanism this pass settles; the concrete node/
tool-level detail for each of the four requirements above is left to
their own future `/plan-tasks` passes, the same "settled home, not
pre-designed pipeline" shape `ADR-005` already established for
`app/scheduling/`.

### LangGraph — where it lives, what it composes with

- **New sub-package, `app/business/agent_orchestration/`** — the first
  sub-package under `business/` (every existing module there is a flat
  file; this is the first concern with enough internal structure to
  warrant one): `state.py` (the graph's state schema), `model_factory.py`
  (resolves a per-agent `langchain_openai.ChatOpenAI` from
  `provider_registry.get_agent_provider`/`has_real_client` — an honest
  "unavailable" signal before any model is constructed, mirroring
  `agents_router.py::_invoke_action`'s existing funnel-gate shape one
  layer over), `mcp_client.py` (a `langchain_mcp_adapters.client.
  MultiServerMCPClient` pointed at Second Brain's own MCP server, below),
  and `graph.py` (compiles **one** `langgraph.graph.StateGraph`, exposing
  `run_agent_conversation(agent_id, message, history) -> dict` as the
  module's one public entry point).
- **One graph, extended by node, not replaced per requirement.** This
  pass needs only a single model-call node (reply, tool-bound from the
  start per the operator's "build now" directive). `REQ-SB-20`/`26`/`27`
  are each expected to extend this **same** graph with additional nodes/
  conditional edges (a Hub-routing decision node; a memory-retrieval
  node; skill-invocation tool nodes) — mirroring, one layer over, the MCP
  server's own "grow by registering, not by spinning up a new instance"
  extensibility story, below.
- **Model integration: `langchain_openai.ChatOpenAI`, not an extension of
  `app/data_access/compass_client.py`.** `compass_client.py` is
  **untouched** — it keeps its one existing fixed-shape `classify_email`
  function, called only by the linear email-classification pipeline
  (`ADR-007`'s original "simple linear pipelines stay outside any
  orchestration framework" carve-out, unaffected and unreconsidered by
  `ADR-015`). `ChatOpenAI` is instantiated per-call with `base_url`/
  `api_key`/`model` sourced from the agent's resolved Provider record —
  `REQ-SB-19`'s Provider registry stays the single source of LLM
  connection configuration for this new surface too. Confirmed
  compatible with Compass by `compass_client.py`'s own docstring
  ("Compass speaks the same wire format as OpenAI's `/chat/completions`")
  — the same reason `ChatOpenAI`'s `base_url` override works against it.
- **`ADR-011`'s keyword-match fast path is kept, unedited — coexistence,
  not supersession.** `app/business/agent_chat.py` is **not modified**.
  Only `app/api/agents_router.py::chat`'s no-trigger-phrase-match branch
  changes: instead of returning the old static canned fallback string, it
  calls `agent_orchestration.run_agent_conversation(agent_id, message,
  history)` and returns its real reply (or an honest unavailability/
  failure message) in its place. A trigger-phrase match still bypasses
  this entirely, exactly as today — no LLM call, no behaviour change.
- **Conversation-state source of truth stays `.second-brain/
  agent_communication_history.json` — no LangGraph persistent
  checkpointer for cross-request state.** `agents_router.py::chat` reads
  that agent's existing history (`vault_writer.load_agent_history`,
  already used for `GET /agents/{id}/history`) and passes the relevant
  recent turns into `run_agent_conversation`'s `history` argument as the
  graph's initial state on every call; the graph itself runs statelessly
  per HTTP request (`.invoke()`), not via a persistent, thread-ID-keyed
  checkpoint. This deliberately avoids a second, potentially-divergent
  conversation-history store — consistent with this project's repeated
  rejection of adding a database/SQLite for local state (`ADR-005`,
  `ADR-011`, `ADR-014`). No entry-`kind` schema change to
  `agent_communication_history.json` results.
- **Package: `langgraph` (`>=1,<2`, pinned to the current stable major —
  pin-then-verify-at-real-install, per this project's own established
  `react-router` pattern), plus `langchain-openai` and
  `langchain-mcp-adapters`.** Python floor `>=3.10`, comfortably inside
  this project's Python 3.14 (`ADR-001`). The genuinely open,
  honestly-flagged risk — whether every transitive compiled dependency
  (chiefly `pydantic-core`) has a prebuilt Windows `cp314` wheel — is
  partially de-risked already: `pydantic-core` (via the already-installed
  `pydantic-settings`) already works on this exact host's real `.venv`
  today. The remaining surface must be confirmed by the coder task's own
  real `pip install`, not assumed. Full reasoning: [ADR-015](ADR.md).

### Shared MCP server — vault-query tools, one implementation reused both ways

- **New `app/business/vault_query_tools.py`** — the actual tool
  *implementations*, thin business-layer functions over already-existing
  read-only `vault_writer` primitives (`list_known_customers`,
  `list_known_kinds`, `list_known_partners`, `list_notes_in_kind_folder`)
  — no new `data_access` reads, per `ADR-003`. Sibling to
  `agent_orchestration/`, not nested inside it — a general capability,
  not orchestration-specific.
- **New `app/api/mcp_server.py`**, api-adjacent (a protocol/transport-
  translation layer, analogous to a router but mounted, not included) —
  builds an `mcp.server.fastmcp.FastMCP` instance, registers
  `vault_query_tools.py`'s functions as `@mcp.tool()`s, and is wired into
  `app/main.py` via `app.mount("/mcp", ...)` (Streamable HTTP transport)
  alongside the existing `app.include_router(...)` calls — no new port,
  no new process, the same single-process precedent `ADR-005` already
  established. Hermes reaches this MCP server over the same host:port as
  every other Second Brain HTTP surface.
- **The in-app LangGraph agents consume the *same* server, not a second
  parallel tool-registration path.** `agent_orchestration/mcp_client.py`'s
  `MultiServerMCPClient` connects to the same mounted `/mcp` endpoint
  over a loopback HTTP call — the in-app agent is simply another MCP
  client, indistinguishable in principle from Hermes — rather than
  importing `vault_query_tools.py`'s functions directly and re-wrapping
  them a second time with LangChain's own `@tool` decorator. A tool's
  name/description/argument-schema is therefore declared **exactly
  once**, in the MCP server's own registration, consumed identically by
  both callers.
- **Extensibility: register new tools on the same server, not a new
  server per capability.** `REQ-SB-27`'s skills, once that story resolves
  its own "what is a skill" question, become new `@mcp.tool()` entries on
  this same server — a second MCP server is the exception (a genuinely
  separate concern), not the default extension path.
- **Relation to the existing REST API — parallel, not a replacement.**
  `agents_router.py`'s existing endpoints are unchanged in shape (only
  the chat fallback body, above) and continue to serve the in-app
  frontend's own settings/actions/chat/history UI. The MCP server exposes
  read/query-style vault tools using MCP's own tool-invocation semantics
  for LLM/agent tool-calling — a structurally different consumer, at a
  distinct path prefix, in the same process.
- **First tools are illustrative, not mandated by this pass** — since
  `REQ-SB-01`/`REQ-SB-02` (Vault Indexing & Browse/Search) don't exist
  yet, the first genuinely useful tools are thin wrappers over the
  read-only primitives named above. Exact task-level sequencing is each
  implementing story's own `/plan-tasks` decision.
- **Package: the official `mcp` Python SDK** (`mcp`, PyPI) — its
  `FastMCP` high-level API, over a hand-rolled JSON-RPC/protocol
  implementation, per this project's repeated "prefer an already-solved
  library" precedent (`ADR-005`, `ADR-008`). Python floor `>=3.10`.

### Addendum (REQ-SB-04-US-01, 2026-08-13) — `/mcp` shared-secret authentication + a write-capable MCP tool that always routes through Pending Approvals, see [ADR-025](ADR.md)

`REQ-SB-04-US-01` (Agent Vault Write Access) is the first story to (a) put
any authentication at all on `/mcp` and (b) register a write-capable tool on
the shared MCP server. Both extend, rather than reopen, the "Shared MCP
server" subsection directly above.

- **New `app/api/mcp_auth.py`** — a small ASGI middleware,
  `require_hermes_shared_secret(app)`, wrapping only the `/mcp` mount (not
  the whole FastAPI app — `app.mount()` takes a raw ASGI app and has no
  `Depends()`-style hook to attach to). Loopback callers
  (`scope["client"][0]` in `{"127.0.0.1", "::1"}`) pass through unchecked —
  Second Brain's own in-app LangGraph agent (`agent_orchestration/
  mcp_client.py`, already live since `REQ-SB-25-US-01`) is unaffected by
  construction, not by a conditional exemption. Any other caller must
  present a matching `X-Hermes-Shared-Secret` header or is rejected `401`
  before the underlying FastMCP app ever sees the request. `app/main.py`
  now mounts `require_hermes_shared_secret(mcp_server.streamable_http_app())`
  in place of the bare app. New `Settings.hermes_mcp_shared_secret: str`
  (`.env`-sourced), mirroring `compass_api_key`/`anthropic_api_key`'s
  existing shape exactly. **This mechanism is shared infrastructure, not
  `REQ-SB-04`-specific** — `REQ-SB-03-US-01`'s own future `/plan-tasks` pass
  (still `status: Draft`, unbuilt) inherits it as already-decided; see
  `ADR-025` point 3.
- **New `app/business/vault_write_tools.py`** (sibling to
  `vault_query_tools.py`) — `propose_vault_write(agent_id, subfolder,
  filename_stem, frontmatter, body) -> dict`, registered as a fifth
  `@mcp_server.tool()` on the same shared FastMCP instance (`ADR-015`
  point 9's "register, never a new server" rule). It **never writes
  directly.** An unknown `agent_id` (not resolvable via `agent_registry.
  get_agent`) is rejected outright. A known agent's proposed target is
  checked against its `REQ-SB-29`-assigned scope via a seam function,
  `_is_within_assigned_scope(...)` — **fail-closed**: since
  `REQ-SB-29-US-01` has no real scope registry yet (still `status: Draft`,
  never decomposed), this seam's body is `return False` until that story
  ships one, so every write is honestly rejected as out-of-scope for now,
  never silently allowed. Once in scope, `pending_approval_registry.
  create_pending_approval(agent_id, trigger="hermes", action_id=
  "hermes_vault_write", payload={...})` is called — a new `trigger` value,
  added the same way `ADR-020` added `"hub_routed"` — and the tool returns
  a `pending` status with the new record's id. **This check is
  unconditional, regardless of the agent's own working mode** — it never
  consults `working_mode_registry`, extending `ADR-021` point 5's own
  Tier-2 "bypasses the working-mode gate by construction" precedent to a
  second, independent case (a materially bigger trust surface than in-app
  actions, per the story's own Context).
- **`pending_approvals_router.py`'s existing `_APPROVAL_HANDLERS` table
  gains one entry**, `"hermes_vault_write":
  vault_write_tools.finalize_hermes_write` — calls `vault_writer.write_note`
  with the record's stored `payload` and returns `{"path": ...}`, matching
  `finalize_new_top_level_area`'s own return shape (`ADR-021` point 5). No
  new collision-avoidance/merge primitive — reuses `write_note`'s existing
  unconditional-overwrite semantics as-is, matching the story's own
  Scenario 1 text ("a new *or modified* note appears"). Decline needs no
  new code — the existing decline endpoint already handles any
  `"pending"` record regardless of `action_id`/`trigger`.
- **Full reasoning, alternatives, and consequences:** `ADR-025`.
  `REQ-SB-04-US-01`'s own scope-enforcement (Scenarios 1/2) cannot be
  live-verified until `REQ-SB-29-US-01` ships a real scope registry — a
  real, load-bearing, honestly-recorded blocker (`ESCALATIONS.md` →
  `ESC-026`), not silently worked around.

### Addendum (REQ-SB-25-US-01 architecture-scoping confirmation, 2026-08-12) — message shape for `run_agent_conversation`, no ADR change

At `/plan-tasks` for `REQ-SB-25-US-01`, the architect confirmed `ADR-015`
already covers everything that story's own build needs — package set,
`agent_orchestration/` layering, the `model_factory.py` unavailability
funnel-gate (Scenario 4), the coexistence-not-supersession composition
with `ADR-011` and the exact `agents_router.py::chat` edit (Decision
point 5), the `agent_communication_history.json`-as-source-of-truth
call (Scenario 3, Scenario 5's honest-failure-recording), and the
broad/reusable-over-narrow reusability decision the story's own flagged
sub-question raised. **No new or changed ADR resulted.** One genuine,
narrower gap remained — `ADR-015`'s own `run_agent_conversation(agent_id,
message, history: list[dict]) -> dict` signature settles the *interface*
but not how `history` (already exactly `vault_writer.load_agent_history(
agent_id)`'s existing shape — `[{"kind": "chat_user" | "chat_agent" |
"run_event", "text": str, "timestamp": iso8601}, ...]`) becomes the
graph's replayed LangChain message list. Resolved now, as an ordinary
mechanism-filling detail within `ADR-015`'s already-decided shape (not a
new tool/framework/structural-boundary choice, so no ADR is warranted):

- `state.py`'s history-to-messages step maps `"chat_user"` entries to
  `HumanMessage(content=text)` and `"chat_agent"` entries to
  `AIMessage(content=text)`; `"run_event"` entries are **excluded** from
  the replayed message list — they are action-trigger audit-log entries
  (`ADR-011`/`REQ-SB-13-US-01`'s own shape), not conversational turns, and
  presenting one to the model as something the user or agent "said" would
  be actively misleading, not merely noisy.
- One `SystemMessage` is prepended, sourced from
  `agent_registry.get_agent(agent_id)`'s existing `name`/`type` fields
  (e.g. "You are the {name} agent for the user's personal Second Brain
  knowledge base.") — minimal identity/purpose grounding only; nothing in
  `REQ-SB-25`'s acceptance text asks for a longer persona/instruction
  prompt, so none is invented.
- **No history window/truncation this pass** — the full existing history
  list for that agent is replayed on every call, matching Scenario 3's
  "aware of the earlier turns" literally. A token-budget/cost concern is
  `REQ-SB-24`'s own separate, not-yet-built scope (per-agent token/cost
  tracking) — not pre-empted here; revisit if a real conversation's
  length becomes a genuine problem in practice.

### Addendum (REQ-SB-33-US-01 agent grounding & honest-uncertainty guardrail, 2026-08-12) — system-prompt instruction only, no ADR change

`REQ-SB-33-US-01` extends `history_entries_to_messages`'s existing
prepended `SystemMessage` (the exact one the REQ-SB-25-US-01 addendum
above already settles the shape of) with one additional instruction,
appended to that same message's own content string — **not** a second
`SystemMessage`. This is a deliberate distinction from the
`_retrieve_memory`/`ADR-016` precedent (which *does* insert a second
`SystemMessage`, because stored per-agent memory is a genuinely separate,
per-conversation-varying concern): grounding/honest-uncertainty guidance
is the same *category* of content as the existing identity/purpose
sentence — static, agent-generic, present on every call — so it belongs
in the one static identity `SystemMessage`, not a second message. Ordinary
mechanism-filling detail within `ADR-015`'s already-decided shape — no new
node, no new state file, no new tool/framework/structural boundary — so no
ADR is warranted, confirming the story's own `## Notes` resolution trail
(the analyst's own reasoning is independently concurred with here, not
merely accepted on faith).

- The instruction's substance (exact coder-owned wording is a task-level
  detail, not fixed here): answer only from what this conversation's own
  tool results, replayed history, and stored memory actually contain;
  when nothing relevant was retrieved for an in-scope question, say so
  honestly rather than answering from the model's own general training
  knowledge as if it were a vault fact; a failed/erroring tool call
  (surfaced to the model as a `ToolMessage` reading `"Tool call failed:
  ..."`, per `_execute_tools`'s existing shape) is not license to
  fabricate a substitute answer — the model must instead honestly report
  that it could not retrieve one.
- **Global, not agent-specific — no new parameter, no new branch.**
  `history_entries_to_messages` is the one shared function every agent's
  conversation already runs through (`REQ-SB-25`); the added instruction
  text is unconditional, present in the one `SystemMessage` on every call
  for every agent, matching the story's own "every agent's... grounded"
  requirement-text reading. No per-agent opt-out field, no new
  `agent_registry.py`/Agent Settings surface — `ADR-011` point 2's "which
  agents exist is app/deployment configuration, not vault content"
  boundary is untouched.
- **No verification/citation node; `_call_model` itself is not
  restructured.** This story's own Constraints explicitly scope the
  mechanism to the prompt input only — a real check-the-reply-against-
  real-tool-results step is named, explicitly, as legitimate future
  escalation, not this pass's scope. `_execute_tools`, `_retrieve_memory`,
  `_extract_memory` are unmodified; only `history_entries_to_messages`'s
  own `SystemMessage` construction changes.
- **Honest limitation carried forward, not newly invented:** a
  system-prompt instruction is not a hard technical enforcement
  guarantee — this mirrors the exact same limitation `ADR-016`'s own
  `extract_memory` "never invent a fact" instruction already accepts for
  memory extraction; verification for both is live prompting behavior,
  not a mechanical check.

### What this pass does not decide

- **`REQ-SB-20`'s per-agent keyword storage and routing-node mechanism** —
  **now resolved, 2026-08-12, by [ADR-017](ADR.md)** (`REQ-SB-20-US-01`'s
  own architecture pass) — see "Section-Hub cross-Section routing —
  keyword storage & routing-node mechanism," below. Its own Context/
  Constraints text (recorded before `ADR-015` existed, "keyword
  matching... no `ADR-007` tension... no superseding ADR needed") has
  been reconciled in its own `## Notes`, closing `ESCALATIONS.md` →
  `ESC-010`. Its externally observable Acceptance Criteria remain
  unaffected by either ADR.
- **`REQ-SB-26`'s memory extraction/summarization mechanism** — was only
  the storage location this ADR settled (a new sibling `.second-brain/
  agent_memory.json`, consumed by a graph memory-retrieval node). **Now
  resolved, 2026-08-12, by [ADR-016](ADR.md)** (`REQ-SB-26-US-01`'s own
  architecture pass) — see "Agent Memory — extraction mechanism," below.
- **`REQ-SB-27`'s "what is a skill" architectural shape** (`ESC-006`,
  still `Open`) — this ADR only settles that whatever shape it resolves
  to plugs into this same graph and MCP server as additional nodes/tools,
  not a separate mechanism. **Update, 2026-08-12:** the registration/
  per-agent-access plumbing half of `REQ-SB-27` is now scoped — see
  "Skills Repository — registration & per-agent access", above; the first
  real skill's implementation remains deferred, and `ESC-006`'s
  default-vs-explicit-access and `REQ-SB-28` sub-questions remain `Open`.
- **`REQ-SB-21`'s Supervised working-mode/approval interaction** with a
  graph-based conversational surface (e.g. LangGraph's own `interrupt()`
  primitive) — genuinely relevant, not resolved here.

Full reasoning, every alternative considered, and every consequence:
[ADR-015](ADR.md).

### Agent Memory — extraction mechanism (`REQ-SB-26`, see [ADR-016](ADR.md))

`REQ-SB-26-US-01`'s own architecture pass resolves the one question
`ADR-015` point 13 deliberately left open — *what* the memory-retrieval
node actually stores/reads, not just *where*. Extraction is **LLM-based**
(a real Provider-backed completion extracting durable facts), not a
hand-rolled heuristic — the acceptance text places no constraint on what
shape of information a user might share, the same "prefer the real
mechanism over a hand-rolled heuristic for open-ended natural language"
reasoning `REQ-SB-25`/`ADR-015` already applied to conversational replies
themselves.

- **Two new nodes on `ADR-015`'s single existing compiled graph**
  (`app/business/agent_orchestration/graph.py`) — not a second graph:
  - **`retrieve_memory`** (read path, before `call_model`): performs no
    file I/O itself — `agents_router.py::chat` loads the agent's stored
    memory via a new `vault_writer.load_agent_memory(agent_id) ->
    list[dict]` primitive (mirrors `load_agent_history`) and passes it
    into `run_agent_conversation` as a new `memory: list[dict]`
    parameter, alongside the existing `history` parameter.
    `retrieve_memory` folds those facts into the graph's initial message
    list (a second `SystemMessage`, appended after the existing
    agent-identity one) before `call_model` runs.
  - **`extract_memory`** (write path, after `call_model`, same graph,
    same `.invoke()` call — no second Provider resolution): reuses the
    already-resolved/bound model to issue one additional, narrowly-scoped
    completion identifying any new durable fact(s) worth remembering from
    the latest exchange (explicitly instructed to return none rather than
    inventing one — Scenario 3's "honest, not fabricated" posture one
    layer over), producing `extracted_facts: list[str]` on graph state —
    not written to disk by the graph. Skipped entirely when `call_model`
    itself errors. `run_agent_conversation`'s return shape gains
    `extracted_facts` (additive to the existing `{"reply"} | {"error"}`
    shape). `agents_router.py::chat` persists any returned facts via a
    new `vault_writer.append_agent_memory_entries(agent_id, facts:
    list[str]) -> None` primitive, called alongside its existing
    `append_agent_history_entry` calls — the same "router persists
    post-graph side effects" shape already established for conversation
    history.
- **New state, `.second-brain/agent_memory.json`** (`ADR-015` point 13's
  already-settled location): `{agent_id: [{"fact": str, "recorded_at":
  iso8601}, ...]}` — a flat, append-only list of short extracted-fact
  strings per agent, not raw message objects. No dedup/merge/
  consolidation this pass; a growing list, not a maintained profile.
- **Retrieval is unfiltered** — the full stored fact list for that
  `agent_id` is folded into every call, no similarity search/ranking/
  vector index, mirroring the "no truncation this pass" precedent already
  established for conversation-history replay. Revisit only once real
  memory volume is observed to strain a real Provider's context window.
- **A second real LLM completion now happens on every successful
  conversational reply** (extraction, alongside the reply) — a genuine
  cost/latency consequence, named explicitly, accepted for a personal
  single-user assistant at today's expected volume.
- Full reasoning, alternatives considered (including why raw
  cross-conversation replay, a hand-rolled heuristic extractor, a
  separate out-of-graph LLM call, a single combined structured-output
  call, and embedding-similarity retrieval were each rejected), and every
  consequence: [ADR-016](ADR.md).

### Section-Hub cross-Section routing — keyword storage & routing-node mechanism (`REQ-SB-20`, see [ADR-017](ADR.md))

`REQ-SB-20-US-01`'s own architecture pass resolves the two questions
`ADR-015` point 12 deliberately left open — per-agent keyword storage
shape, and the concrete node/edge design implementing "how a Hub
decides." The routing **algorithm** itself is unchanged from that
story's own original operator resolution: deterministic, case-insensitive
keyword-substring matching, first-match-wins, exactly `ADR-011`'s
existing posture — no LLM is involved in the match. Only the algorithm's
*housing* moves onto `ADR-015`'s graph.

- **New sibling `.second-brain/agent_keywords.json`**, `{agent_id:
  [keyword: str, ...]}` — a flat, per-agent-id-keyed list, mirroring
  `agent_communication_history.json`/`agent_memory.json`'s existing
  shape (`ADR-011`/`ADR-016`), not `agent_sections.json`/
  `agent_providers.json`'s registry+assignments shape — keywords carry no
  separate, shared, renameable identity the way a Section or Provider
  does, so the simpler per-agent-list mirror is the closer fit. New
  `vault_writer.py` primitives: `load_agent_keywords(agent_id)`,
  `save_agent_keywords(agent_id, keywords)`, and a new whole-file read,
  `load_all_agent_keywords() -> dict[str, list[str]]` (needed by the
  routing node's cross-agent scan — no existing primitive reads an entire
  per-agent-keyed store at once).
- **New `app/business/agent_keywords.py`** (sibling to
  `section_registry.py`/`provider_registry.py`, composed *alongside*
  `agent_registry.py`, unmodified): `get_agent_keywords`/
  `set_agent_keywords` (whole-list replace, matching the free-text
  kv-list editing UX already used elsewhere on the Agent Settings panel),
  and `list_candidate_agents_for_keyword_match(requesting_agent_id,
  need_description)` — composes `section_registry.get_agent_section`/
  `list_sections` (to exclude the requester's own Section — cross-Section
  only, per this story's own Constraint deferring within-Section routing)
  and `agent_registry.list_agents`. An agent with an empty keyword list
  is structurally never a match candidate (Scenario 4, satisfied by
  construction).
- **One new node, `route_hub_request`, on `ADR-015`'s SAME compiled
  `app/business/agent_orchestration/graph.py` `StateGraph`** — not a
  second graph — reached via a new conditional edge from the existing
  `call_model` node, triggered by a new, **orchestration-internal**
  LangChain tool, `request_cross_section_help(need_description: str)`,
  bound to the model alongside the existing vault-query tools. This is
  this codebase's first real tool-execution loop (today's `call_model`
  binds tools but has no conditional edge/loop-back at all): on a tool
  call, the graph routes to `route_hub_request` instead of `END`, then
  loops back to `call_model` with the routing outcome as a `ToolMessage`
  so the requesting agent's own model composes its final reply around it
  (Scenario 3's honest-no-fabrication bar). The module also exposes
  `route_cross_section_request(requesting_agent_id, need_description) ->
  dict` directly, the same "public entry point, directly testable"
  convention `T07` already established for `run_agent_conversation`.
- **The mandatory "own Hub, then target Hub" two-hop relay is two
  sequential lookups inside the ONE node**, not two separate nodes
  (unlike `ADR-016`'s `retrieve_memory`/`extract_memory` split — the
  "own Hub" hop here has no real branch/failure mode of its own, unlike
  each of `ADR-016`'s two genuinely separate LLM completions): (a)
  `section_registry.get_agent_section(requesting_agent_id)` — the first
  hop; (b) `agent_keywords.list_candidate_agents_for_keyword_match(...)`
  — the second hop, cross-Section only. Returns `{"matched": True,
  "agent_id", "section_id"}` on the first match, or `{"matched": False}`
  on an exhaustive no-match (Scenario 3) — both hops recorded as explicit
  result fields, a real inspectable property, not just a narrative
  description of the code path.
- **`request_cross_section_help` is deliberately NOT registered on the
  shared MCP server** (`app/api/mcp_server.py`) — it stays a local,
  `agent_orchestration`-internal LangChain tool, never loaded through
  `mcp_client.py`'s loopback client. The shared server's whole purpose
  (`ADR-015` points 7-9) is one tool surface reused identically by Hermes
  and the in-app agents; Hermes has its own, separate, external Section/
  Department/Hub concept (`MEMORY.md`), and this story's own Non-Goals
  explicitly reject syncing with it — registering this tool on the
  shared server would hand Hermes a callable into Second Brain's own
  internal agent-routing machinery.
- Full reasoning, alternatives considered (including why the literal
  `agent_sections.json` mirror, an MCP-server-registered tool, an
  LLM-based match, a standalone non-graph function, and a two-node hop
  split were each rejected), and every consequence: [ADR-017](ADR.md).

### Vault Filing Expert — placement decision, Tier-1 write, Tier-2 approval override (`REQ-SB-35`, see [ADR-021](ADR.md))

**A new registry agent, `"vault-filing-expert"`** (type `expert`), a plain
new `app/business/agent_registry.py` entry — reached exclusively via
`ADR-017`'s already-real `graph.route_cross_section_request(...)`, never a
shared skill (operator-confirmed, "This is an Agent"). Its own placement/
write mechanism lives in a new `app/business/vault_filing_expert.py`:

- `determine_placement_and_file(content, source_description,
  requesting_agent_id) -> dict` pre-fetches `list_known_kinds()`/
  `list_known_customers()`/`list_known_partners()` deterministically (plain
  Python calls, not a bound-tool reasoning loop), embeds them plus the
  vault's own design-methodology guidance into one `model_factory.
  resolve_agent_model("vault-filing-expert")` completion, and gets back a
  structured `{"kind", "is_new_top_level_area", "tags", "filename_stem",
  "body", "confidence", "uncertainty_note"}` decision. `is_new_top_level_
  area` is re-checked in Python (`kind in list_known_kinds()`), never
  trusted from the model's own boolean alone.
- **Tier 1** (existing `kind`, or a new tag/subfolder within one) writes
  immediately via the already-fully-generic `vault_writer.write_note(
  f"Work/{kind}", ...)` — no new low-level write primitive needed, since
  `write_note`'s own `mkdir(parents=True, exist_ok=True)` already handles a
  brand-new folder transparently. Low-confidence decisions are prefixed
  with a visible uncertainty marker (Scenario 6), independent of the Tier
  axis.
- **Tier 2** (genuinely new top-level area) never reaches
  `agents_router.py::_invoke_action`'s working-mode-gated funnel at all —
  it unconditionally calls `pending_approval_registry.
  create_pending_approval(agent_id="vault-filing-expert", trigger="direct",
  action_id="propose_new_top_level_area", description=...)`, bypassing the
  working-mode gate **by construction**, not by an override flag on it —
  the concrete mechanism behind the operator's "not a change to the
  agent's own general working-mode assignment" framing. `ADR-018`'s
  `agent_pending_approvals.json` schema (unedited by `ADR-020`) gains one
  additive `"payload": dict | null` field carrying the proposed
  `kind`/`tags`/`filename_stem`/`body`; `pending_approvals_router.py`'s
  Approve path gains a small `_APPROVAL_HANDLERS` dispatch table
  (mirrors `agents_router.py`'s `_ACTION_HANDLERS`/`skill_registry.py`'s
  `_SKILL_HANDLERS`) mapping `"propose_new_top_level_area"` to a second
  public function, `vault_filing_expert.finalize_new_top_level_area(
  payload)`, which performs the actual `write_note` call only once
  approved. Decline takes no further action — the content is never filed
  under the declined area, never silently retried elsewhere.

**A real, currently unmet blocking prerequisite, not silently assumed
satisfied:** Tier 2's own coder task needs `REQ-SB-21-US-01`'s Pending-
Approvals mechanism (`pending_approval_registry.py`,
`agent_pending_approvals.json`, `pending_approvals_router.py`) to actually
exist in code. Direct inspection during this pass found `REQ-SB-21-US-01`
is `status: Draft`, `gate: flagged`, and none of that mechanism has been
built — see [ADR-021](ADR.md)'s own Context and `ESCALATIONS.md` →
`ESC-017`. Tier 1 (Scenarios 1, 2, 5, 6, 7, 8) has no such dependency.

Full reasoning, every alternative considered, and every consequence:
[ADR-021](ADR.md).

### Real Anthropic Provider integration & web-research skill (`REQ-SB-36-US-01`, see [ADR-022](ADR.md))

`app/business/provider_registry.py`'s `_REAL_CLIENT_PROVIDER_IDS` gains
`"anthropic-claude"`; `_seed_state()` additionally auto-seeds an
`"Anthropic Claude"` Provider entry (mirrors the existing `"Compass"`
self-seed) from two new required `Settings` fields, `anthropic_api_key`/
`anthropic_model` (`.env.example` gains `ANTHROPIC_API_KEY`/
`ANTHROPIC_MODEL`). A new `app/data_access/anthropic_client.py`
(sibling to `compass_client.py`, plain `anthropic` SDK client, **not**
`langchain-anthropic`/`model_factory.py` — this skill is never routed
through `run_agent_conversation`'s LangGraph loop) exposes `web_search(
api_key, model, query) -> {"found": bool, "summary": str, "sources":
list[str]}`, calling Anthropic's own server-side web-search tool (the
operator-confirmed mechanism). `app/business/skill_tools.py` gains
`web_research(query: str, agent_id: str) -> dict` (`@mcp_server.tool()`,
same catalog shape `REQ-SB-27-US-01` established) — resolves the
**invoking agent's own linked Provider**
(`provider_registry.get_agent_provider(agent_id)`, corrected mid-build,
2026-08-12, operator-directed — supersedes this section's original
fixed-`"anthropic-claude"`-id design, see `ADR-022`'s own "Correction"
addendum) and `has_real_client`, dispatching to `anthropic_client.
web_search` only when that Provider is `"anthropic-claude"` — honestly
unavailable (Scenario 4) for any other linked Provider (Compass has no
real hosted web-search, confirmed live) or before the real client exists,
honestly empty (Scenario 3) when the search finds nothing relevant, never
fabricated. `skill_registry.invoke_skill` additively injects `agent_id`
into the handler call whenever the resolved handler's own signature
declares it, so `skills_router.py`'s own request-body contract and
`diagram-understanding`'s zero-arg call are both unaffected.

`skill_registry.invoke_skill(agent_id, skill_id, args: dict | None =
None)` gains an additive `args` parameter (existing zero-arg callers
unaffected) and `skills_router.py`'s invoke endpoint gains an optional
JSON body — the mechanism Scenario 1's "invokes the skill with a research
subject/query" needs. The web-research skill is invoked exclusively
through this existing REST/`invoke_skill` plumbing (directly, by
`ADR-023`'s orchestration, or via the router) — not bound into the
conversational tool loop this pass (general chat-triggered web search is
out of scope, `REQ-SB-36-US-01`'s own Non-Goals).

**A live-discovered, load-bearing gap closed by this pass:** `app/business/
agent_orchestration/mcp_client.py::load_vault_query_tools()` was found,
by direct reading, to return **every** tool on the shared MCP server with
no filtering — meaning any agent's ordinary chat turn could already reach
`skill_tools.py`'s catalog (harmlessly, while it held only the
`diagram_understanding` stub) regardless of `skill_registry.
has_skill_access`. This would have silently falsified `REQ-SB-36-US-01`
Scenario 2 the moment `web_research` became real. Fixed now: `mcp_client.py`
gains `load_agent_tools(agent_id: str) -> list`, filtering the full server
tool list so a skill-catalog tool is only included when
`skill_registry.has_skill_access(agent_id, skill_id)` is `True` (the four
core vault-query tools stay always-available, never gated);
`graph.py::run_agent_conversation` calls this in place of the old
`load_vault_query_tools()` (removed, no other caller existed). Both
`web_research` and `diagram_understanding` are correctly gated in the
conversational path as a result, reusing `has_skill_access` exactly as
`skill_registry.py`'s own docstring already anticipated.

Full reasoning, every alternative considered, and every consequence:
[ADR-022](ADR.md).

### Delegated knowledge-bootstrap orchestration (`REQ-SB-36-US-02`, see [ADR-023](ADR.md))

A new `app/business/agent_orchestration/knowledge_bootstrap.py` (sibling
to `graph.py`), exposing `async def bootstrap_agent_knowledge(agent_id,
subject) -> dict` — the delegation chain's one public entry point,
composing already-real (or already-designed) pieces deterministically
rather than a second layer of recursive, model-driven agent-to-agent
conversation:

1. Hop 1 — `graph.route_cross_section_request(agent_id, need_description=
   f"real web research about {subject}")` (`ADR-017`) finds a Research
   Expert candidate, or honestly reports no match (Scenario 4).
2. A working-mode check (`working_mode_registry.get_agent_working_mode(...)
   == "autonomous"`, `REQ-SB-21`) gates unattended completion.
3. Research — `skill_registry.invoke_skill(research_expert_agent_id,
   "web-research", {"query": subject})` (`ADR-022`) gathers real content,
   or honestly reports no results (Scenario 5).
4. Hop 2 — `graph.route_cross_section_request(research_expert_agent_id,
   need_description="file this content into the vault")` finds a Vault
   Filing Expert candidate.
5. Filing — `vault_filing_expert.determine_placement_and_file(...)`
   (`ADR-021`) writes immediately (Tier 1) or creates a pending-approval
   record and the chain honestly reports `"status": "pending_approval"`
   (Tier 2, Scenario 2).

**Hub routing is used to identify *who*; the specific capability invoked
at each hop is composed directly by this module** (`invoke_skill(...,
"web-research", ...)`, `determine_placement_and_file(...)`) — not a
generic role-name-keyed dynamic dispatch (deliberately not built; see
[ADR-023](ADR.md)'s Alternatives Considered). Triggered through the
existing action-trigger funnel: a new pilot Expert agent (e.g.
`"compass-expert"`, a plain code-level `agent_registry.AGENTS` addition,
`ADR-011` point 2) declares one new action, `"build_knowledge"`, dispatched
through the existing `_ACTION_HANDLERS`/`_invoke_action` mechanism
(`ADR-011`) — reachable by chat trigger phrase or a direct Available-
Actions button, identically to every existing action. Any future pilot
Expert agent reuses the identical one-line registry addition (Scenario 6).
The whole chain's outcome is recorded as one `run_event` history entry on
the originating agent, via the existing `vault_writer.
append_agent_history_entry`.

**Two real, currently unmet blocking prerequisites, inherited from
`ADR-021`'s own finding, not new to this pass:** the working-mode check
(step 2) needs `working_mode_registry.py`, and Tier 2's own resolution
(step 5) needs `pending_approval_registry.py`/`pending_approvals_router.py`
— neither exists in code yet (`REQ-SB-21-US-01` is `status: Draft`,
unbuilt). See `ESCALATIONS.md` → `ESC-017`.

Full reasoning, every alternative considered, and every consequence:
[ADR-023](ADR.md).

## Vault Indexing Layer (REQ-SB-01-US-01, see [ADR-024](ADR.md))

The first **real, persistent, re-runnable index** of the vault's notes —
frontmatter, tags, and outgoing/incoming wikilinks. Before this story, every
vault-query primitive (`vault_writer.list_all_note_paths`/
`list_known_customers`/`list_known_kinds`/`list_known_partners` and their
`vault_query_tools.py` pass-throughs, built for `REQ-SB-25`'s agent
tool-calling) re-scanned the filesystem fresh on every call — stateless,
request-scoped I/O, never a cached or persisted structure. No wikilink graph
(forward or backward) existed anywhere in this codebase; this is the first.
Full storage/rebuild reasoning, every alternative considered, and every
consequence: [ADR-024](ADR.md).

- **New `app/business/vault_indexing.py`** — a module-level, in-memory-only
  singleton (`_vault_index: dict[str, dict]`, keyed by each note's filename
  stem — the same identity `write_note()`/wikilinks this project already
  writes use), rebuilt wholesale on every trigger by `rebuild_index()`
  (walks `vault_writer.list_all_note_paths()` — unchanged, already scoped
  to `Work/*/*.md`, so `.obsidian/`/`Templates/` are excluded with zero new
  filtering code — reads each note via `vault_writer.read_note()`, derives
  each note's tags and outgoing wikilink targets, then a second pass
  inverts outgoing links into incoming/backlinks). Assembles a brand-new
  dict, then atomically reassigns the module-level reference — no explicit
  lock (a single-reference rebind is GIL-safe), and discarding the old
  dict wholesale is what gives deletions honest reconciliation for free.
  `get_index()` is a plain whole-dict accessor (no filter/query
  parameters) — internal/test use and the substrate `REQ-SB-02`'s
  browse/search will build on, deliberately **not** a browse/search API
  itself (this story's own Non-Goals boundary).
- **New `app/api/vault_index_router.py`**, `APIRouter(prefix="/vault-index")`,
  registered in `app/main.py`: `POST /vault-index/rebuild` → calls
  `rebuild_index()` synchronously, returns rebuild stats (notes indexed,
  timestamp) — the explicit on-demand re-index path (Scenario 8, `ESC-021`'s
  resolved trigger design). Independent of `capture_scheduler.py`'s
  `_capture_run_lock` — that lock guards overlapping *vault-writing* capture
  runs, a concern this read-only, side-effect-free rebuild does not share.
- **Scheduler-tick wiring: one new, unconditional call, zero scheduler-layer
  changes (Scenario 9).** `app/business/email_classification.py::
  run_capture_and_record_completion` (the function `app/scheduling/
  capture_scheduler.py` already treats as an opaque unit, per `ADR-005`)
  gains one additional call to `vault_indexing.rebuild_index()` —
  **unconditional**, not gated by `email-capture`'s or `meeting-capture`'s
  own working mode (`ADR-018`/`ADR-020`), since vault indexing is core
  plumbing, not an Agents Map agent action. `capture_scheduler.py` itself
  needs no changes, mirroring the precedent `REQ-SB-08`'s meeting capture
  already set for adding a second concern to the same tick.
- **A real, pre-existing gap in `vault_writer.read_note()`, fixed as part
  of this story, in `data_access`:** `_parse_frontmatter_value` had no
  branch for a bracketed list value — a `tags: ["a", "b"]` line read back
  as the literal unparsed string, not a Python list, silently breaking
  "correctly captures that note's tags." Fixed with one more branch,
  mirroring `REQ-SB-30-US-01`'s already-shipped boolean-value branch
  precedent exactly — still not a general YAML parser (unchanged
  docstring caveat), just one more recognized literal shape. No new ADR
  for this fix — same-shape extension of an already-`Accepted` primitive.
- **Wikilink resolution:** a wikilink target is matched against each
  indexed note's own filename stem, case-insensitively — the identity this
  project's own capture pipelines already use when writing wikilinks
  (`upsert_attendee_links`, `record_conversation_note`/
  `find_related_note_stems`). An unresolved target (dangling link, or a
  manually-authored note's free-text wikilink that doesn't match) is kept
  as an outgoing-only entry — no crash, no fabricated target, satisfying
  Scenario 5's "handled honestly" requirement for a deleted note's
  now-dangling incoming reference.
- **No browse/search/query surface added by this story** — confirmed
  against the story's own Non-Goals (`REQ-SB-02`'s job) and Acceptance
  text (indexing only). `vault_indexing.get_index()` is the only read
  accessor this pass adds.

## Browse & Search (REQ-SB-02-US-01, see [ADR-026](ADR.md))

The first browse/search/query surface over `vault_indexing.get_index()` —
`REQ-SB-01-US-01`'s own Non-Goals deliberately left this to `REQ-SB-02`.
List/browse all indexed notes, filter/navigate by tag, a note's own
forward-link/backlink list (textual, clickable — not a visual graph canvas,
`ESC-022` Resolved), and ranked keyword/full-text search (field-weighted
BM25-style, not a bare substring match, not embeddings — `ADR-026`, below,
for the full ranking-mechanism reasoning). Read-only throughout — no new
vault-write capability, no staging/promotion gate on any of it (standing
`MEMORY.md` constraint).

### Index-readiness signal — a small, additive extension of `vault_indexing.py`, not a reopening of `ADR-024`

`ADR-024`'s own `_vault_index: dict[str, dict]` starts empty at module load
and is only ever populated by a call to `rebuild_index()` — there was no way,
before this story, to distinguish "the index has never been rebuilt this
process lifetime" (Scenario 7 — an honest "nothing indexed yet" state) from
"the index was rebuilt and is genuinely empty." `app/business/
vault_indexing.py` gains one small additive piece: a module-level
`_last_rebuilt_at: str | None = None`, set to an ISO-8601 UTC timestamp at
the end of every successful `rebuild_index()` call, plus a new
`get_last_rebuilt_at() -> str | None` accessor. This does not touch
`get_index()`'s own signature or `ADR-024`'s "no filter/query parameters"
decision (a second, independent accessor, not a parameter on the existing
one) — no new ADR; the same "extends X, does not reopen it" posture already
used elsewhere in this file. In practice, `REQ-SB-01-US-01-T04`'s own
unconditional app-start scheduler-tick wiring means the index has almost
always already been rebuilt at least once by the time this story's UI is
reachable — the honest "not indexed yet" state exists for correctness (the
brief startup window, or a future deployment shape without that tick), not
because it is the expected common case.

### `app/business/vault_search.py` (new) — read-only, composes `vault_indexing.get_index()` (and, for `search()` only, `vault_writer.read_note()`)

Mirrors `my_day.py`'s/`system_health.py`'s own "one-module-per-feature,
read-only aggregation, no vault writes" shape. `list_notes`/
`get_note_detail` compose `vault_indexing` only. `search()` additionally
composes `vault_writer.read_note()` directly, one call per candidate note,
to read body text for BM25 scoring — `vault_indexing`'s own index entries
(`ADR-024`, `REQ-SB-01-US-01-T02`) deliberately never store a note's raw
body, only `outgoing_wikilinks` already extracted from it, so there is
nothing to compose *from* `vault_indexing` for the body field. This
directly mirrors `my_day.py`'s own already-`Accepted` precedent of
composing `vault_writer` directly, read fresh on every request, no
caching (`ADR-026` for the full reasoning/cost tradeoff).

- **`list_notes(page, page_size, tag=None) -> {"total", "page",
  "page_size", "notes"}`** — Scenarios 1, 2, 6. Reads the current
  `get_index()` snapshot, optionally narrowed to entries whose `tags` list
  contains the given `tag` (exact, case-sensitive match against the tag
  strings this project's own capture pipelines already write, e.g.
  `customer/masdar`, `kind/email`), sorted by stem (a stable, deterministic
  default ordering — no note-kind-specific date field is universal across
  every indexed kind, so stem is the one field every entry always has),
  then paginated. An empty result (no notes at all, or a tag with zero
  matches) returns `"notes": []` honestly — Scenario 6 is this same
  function returning a correctly-empty list, not a distinct code path.
- **`get_note_detail(stem) -> dict | None`** — Scenario 3. Looks up one
  entry by stem; returns its `frontmatter`/`tags` plus two resolved link
  lists:
  - **Backlinks** — `entry["incoming_wikilinks"]` is already a list of
    resolved source stems (`ADR-024` point 3 derives these at rebuild
    time) — each is looked up directly in the index for its own
    title/kind.
  - **Forward links** — `entry["outgoing_wikilinks"]` is deliberately
    *raw, unresolved* wikilink target text (`REQ-SB-01-US-01-T02`'s own
    shape — resolution happens only in the backlink-deriving pass, against
    the *target*'s entry, not stored back onto the source).
    `get_note_detail` applies the identical case-insensitive
    stem-matching rule `ADR-024` point 3 already established, a second
    time, at read time, to resolve each raw forward-link target to its own
    entry for display (title/kind); a target that doesn't resolve to any
    indexed note (a dangling link, or a manually-authored free-text
    wikilink — `ADR-024`'s own documented honest-handling case) is simply
    omitted from the shown forward-links list, the same "no crash, no
    fabricated entry" posture `ADR-024` already applies to backlink
    derivation, not a new rule.
  - **Title/kind display convention** — `title = frontmatter.get("subject")
    or stem`; `kind = frontmatter.get("type", "Unknown")`. Ordinary
    projection (not every kind's frontmatter carries `subject` — a
    Customer/Person/Partner hub note doesn't — falling back to the note's
    own filename stem, which this project's own filename convention
    already makes a reasonable display name).
- **`search(query, limit=20) -> {"query", "results"}`** — Scenarios 4, 5.
  Field-weighted BM25-style ranking over the current `get_index()`
  snapshot — `ADR-026` for the full mechanism/alternatives reasoning. An
  empty `results` list for a query matching nothing is Scenario 5's own
  honest empty state, not an error — the same function, not a distinct
  code path, mirroring `list_notes`'s own empty-tag-filter handling above.
- **`list_tags() -> {"tags": [{"tag", "count"}]}`** — Scenario 2's own
  prerequisite: the frontend's tag-filter UI needs a real list of tags
  that actually exist in the index to offer the user (the approved
  prototype's own fixed chip buttons are illustrative-only, not a real
  tag-discovery mechanism) rather than requiring the user to already know
  an exact tag string to type. A simple aggregation over the current
  `get_index()` snapshot (a plain per-tag count over every entry's `tags`
  list), sorted by count descending then tag name — no new storage, no new
  mechanism, an ordinary read-only projection alongside `list_notes`.

  <!-- Not a locked-AC-bearing function on its own -- it is the concrete,
  real mechanism the frontend's own AC-02 tag-filter UI needs to be more
  than a mockup; the decomposer's own task split records this explicitly
  rather than leaving it an implicit gap for the coder to discover
  mid-build. -->

### `app/api/vault_search_router.py` (new), `APIRouter(prefix="/vault-search")`

Registered in `app/main.py` alongside the other routers (`ADR-003`
layering — this router calls `vault_search`/`vault_indexing` only, never
`vault_writer`/filesystem directly).

- **`GET /vault-search/status`** → `{"indexed": bool, "last_rebuilt_at":
  str | null}`, reading `vault_indexing.get_last_rebuilt_at()` directly.
  The frontend calls this first, on page load; `indexed: false` replaces
  the **entire** browse/search surface with the honest "nothing indexed
  yet" state (Scenario 7), matching the approved prototype's own top-level
  state-switcher shape (`vault-browser.html`'s
  `data-group="vault-index-state"`) — not a per-endpoint empty-vs-not-
  indexed distinction duplicated three times over.
- **`GET /vault-search/notes?tag=&page=&page_size=`** → `list_notes(...)`
  (Scenarios 1, 2, 6). `tag` omitted = all notes; `page`/`page_size`
  default to `1`/`20` (implementation-internal defaults, not locked by any
  AC).
- **`GET /vault-search/notes/{stem}`** → `get_note_detail(stem)`
  (Scenario 3); `404` for an unknown stem.
- **`GET /vault-search/search?q=&limit=`** → `search(...)` (Scenarios 4, 5).
- **`GET /vault-search/tags`** → `list_tags()` — the real, current tag list
  (with counts) the frontend's tag-filter chip row renders, so Scenario 2's
  filter offers real, discoverable tags rather than requiring the user to
  already know an exact tag string.

### Frontend — `pages/VaultBrowserPage.tsx` + `pages/NoteDetailPage.tsx` (new), routes `/browse` and `/browse/:stem`

New `features/vault-browser/client.ts` (fetch wrapper over the four
`/vault-search/...` endpoints above, same thin-`fetch`-client convention as
`features/my-day/client.ts`). `App.tsx` gains the two new routes;
`Sidebar.tsx` gains a new "Browse & Search" nav item (matching the approved
prototype's own sidebar placement, after the existing nav items — the
prototype's own trailing "Screens (catalog)" entry has no equivalent in the
real shell, so it is not ported).

`VaultBrowserPage.tsx` composes a search box (Scenarios 4, 5), a
tag-filter chip row + paginated browse list (Scenarios 1, 2, 6), and —
first — the `/vault-search/status` not-indexed check (Scenario 7) gating
the rest of the page, matching `vault-browser.html` region-for-region.
`NoteDetailPage.tsx` (route param `:stem`) renders one note's
frontmatter/tags plus its forward-links/backlinks lists as real, clickable
`<Link>`s to `/browse/:stem` (`react-router`'s own client-side navigation
standing in for the prototype's own `button[data-state-target]`/hash-
deep-link mechanic — a real route param plus `react-router`'s own
navigation *is* this project's already-`Accepted` client-side navigation
mechanism, `ADR-010`, not a new one), matching `note-detail.html`
region-for-region — an empty forward-links or backlinks list renders
inline, honestly, exactly as `ADR-024` Scenario 6 already established for
an empty-links index entry.

**CSS: two small additive rules ported verbatim from
`html-prototype/styles.css`** into a new `src/frontend/src/styles/
vault-browser.css` (imported globally, alongside the existing per-feature
stylesheets) — `a.item-row`/`button.item-row` (a real clickable variant of
the existing plain-`<div>` `.item-row`) and `.tag-chip` (a clickable,
pill-shaped tag button) — both already ported into `html-prototype/
styles.css` itself during the `/design` pass; no new class invented here,
no renaming (`ADR-010` Decision 3's own "no renaming/translation step"
convention). Every other visible region reuses existing tokens/primitives
(`.card`, `.badge*`, `.item-list`, `.kv-list`/`.kv-row`, `.empty-state`,
`.input`/`.btn`/`.btn-primary`, `.mono`, `.text-muted`) already ported for
earlier stories — no other new CSS.

**No ADR for the query/API/frontend shape above** — an ordinary, same-shape
extension of already-`Accepted` structural decisions: `ADR-003`'s
layering, the one-module-per-feature `business/`/`api/` pattern already
established repeatedly (`my_day.py`/`system_health.py` and their routers),
and `ADR-010`'s frontend routing/styling/data-fetching conventions. The one
genuinely new mechanism decision — ranked search — is `ADR-026`, below /
[ADR.md](ADR.md).

## Data Model

The vault has three top-level roots: `Personal/` (untouched by Second Brain),
`Work/` (everything Second Brain's backend writes lands here — see
[MEMORY.md](../../MEMORY.md)), and `Templates/` (Obsidian core-Templates-plugin
template files — human-authored vault content, not backend-written; see
[ADR-006](ADR.md) / REQ-SB-15, below). Vault structure and note-writing conventions
follow *Beyond the Second Brain* (Mo Elkholy), adopted as a standing
architecture reference — see `Documentation/References/beyond-the-second-
brain-methodology.md` for the full summary and `ADR-004` for the concrete
folder-vs-tag decision it drove. Current state, not full adoption:

- **Folder level:** `Kind` only — `Work/<Kind>/` (`Emails`, `Files`,
  `Notifications`, and any new kind Compass proposes; see `list_known_kinds`
  in `app/data_access/vault_writer.py`). No `Customer` folder level.
- **Frontmatter, per note:** `type` (= kind), `customer`, `tags`
  (`customer/<slug>`, `kind/<slug>`), `classification_confidence`, plus
  source metadata (`subject`, `sender`, `sender_email`, `received`,
  `outlook_entry_id`, `conversation_id`).
- **Linking:** same-thread notes (matched on Outlook `conversation_id`) get
  a `## Related Emails` section with `[[wikilinks]]` to prior notes in the
  thread — Obsidian computes the reverse link automatically, so only the
  newer note needs to link forward. No reference/conceptual/tension link
  taxonomy yet (the book's Chapter 6 distinction) — everything so far is a
  reference-style link.
- **Attachments:** real (non-inline) files saved to `<subfolder>/
  attachments/<note-slug>/`, linked from the note body. Inline signature/
  logo images are filtered at capture time, never saved (`app/data_access/
  outlook_com.py`'s `_is_inline_attachment`).
- **Filename convention:** `<date>-<subject>-<entry-id-suffix>.md` — the
  EntryID suffix is required (same-subject/same-day items collide without
  it; see `MEMORY.md`).

### Customer Hub Notes & Graph Linking (REQ-SB-14)

- **Hub note per customer:** `Work/Customers/<Customer>.md` — `Customers` is a
  `kind` folder like any other (`Work/Emails/`, `Work/Files/`, ...), holding
  one `Customer`-type note per customer/affiliate; not a reversal of ADR-004
  (`customer` still never becomes a folder level for *content* classification
  — this folder holds the hub notes themselves, not customer-classified
  email/file content). Schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- **Wikilink placement — inline body, not frontmatter.** Every customer-tagged
  note gets a single line near the top of its body, e.g.
  `**Customer:** [[ADNOC]]`, linking to its hub note — extending the existing
  inline-body-wikilink convention already used for same-thread email linking
  (`## Related Emails`, above) rather than introducing a frontmatter-property
  link. Frontmatter-resolved wikilinks are a newer, version-dependent Obsidian
  behaviour; inline body links have always reliably driven the graph view,
  matching this project's established durable-over-clever preference
  (ADR-001, ADR-002). This is a direct extension of the linking convention
  already documented above, not a new structural boundary — no ADR.
- **"Ensure hub note exists, then link" logic lives in
  `app/business/customer_hub_linking.py`** (new module — see Source Layout,
  above), following ADR-003's layering and the existing `tag_backfill.py` /
  `vault_restructure.py` precedent of a dedicated business module per
  maintenance operation:
  - `app/data_access/vault_writer.py` gains the file-I/O primitives (hub-note
    path resolution, existence check, baseline-frontmatter creation reusing
    `write_note`, and a surgical "insert this body line if not already
    present" helper mirroring `insert_tags_line`'s "surgical insert, not full
    rewrite" precedent) — it does the actual reading/writing, no business
    rules.
  - `app/business/customer_hub_linking.py` orchestrates "ensure the hub note
    exists, then link this note to it" as one reusable operation, called from
    two places: the one-time retrofit (batch, over every existing
    customer-tagged note) and `email_classification.py`'s per-write hook
    (going forward) — the same shared mechanism the story requires, not two
    parallel implementations.
  - The retrofit is exposed as a new one-off endpoint,
    `POST /poc/retrofit-customer-hub-links`, in `app/api/email_poc_router.py`
    — matching the existing `/poc/backfill-tags` and
    `/poc/flatten-customer-folders` one-off-migration-endpoint precedent.
- **Preserving manually-added hub-note content (REQ-SB-10 pattern, extended).**
  "Baseline fields" are concretely the hub note's frontmatter keys only —
  `type`, `customer`, `tags`, `affiliate_of` — never its body. On first
  creation, `write_note` writes the full baseline (frontmatter + a short
  auto-generated body stub inviting the user to add their own overview). On
  every later touch (retrofit rerun, or a new note for that customer
  captured), the hub note is **never** rewritten wholesale again: each
  baseline frontmatter key is inserted only if missing (mirroring
  `insert_tags_line`'s surgical-line-insert precedent, generalized to "insert
  this line if this key is absent"), and `affiliate_of` is only ever written
  when absent — never reset to `""` once a real value exists. The body is
  never programmatically touched past initial creation, so user-added
  overview/contacts/focus content is preserved absolutely, not merely
  diffed-and-merged.

### Vault Content Conventions — Templates & In-Vault Guide (REQ-SB-15)

- **A third top-level vault root, `Templates/`** (sibling to `Personal/` and
  `Work/` — see [ADR-006](ADR.md)), holding exactly the four Obsidian
  core-Templates-plugin template files (`Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`), each pre-filling its resolved schema
  from `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
  field-for-field, plus the customer wikilink placement convention above.
  Configuring Obsidian's Settings → Templates → "Template folder location" to
  point at `Templates/` is a one-time manual step in the user's own Obsidian
  install — not code, not automated or tracked by `src/backend`.
- **The in-vault guide note lives at `Work/Guides/Manual-Entry-Guide.md`** —
  a new, dynamically-discoverable `kind` folder under the existing
  `Work/<Kind>/` convention (`list_known_kinds` already scans folder names, no
  code change needed for it to be found) — deliberately **not** inside
  `Templates/`, since Obsidian's Templates feature lists every file in the
  configured template folder as insertable; a guide note living there would
  wrongly appear in the "Insert Template" picker. See [ADR-006](ADR.md).
- This entire story is vault-content authoring — four template files and one
  guide note, written directly into the real vault at `VAULT_PATH` — not
  `src/backend`/`src/frontend` code; no source-layout or tech-stack change
  results from it.
- **A fifth template, `Templates/Research.md` (REQ-SB-17), and a fifth
  guide-note entry — a direct extension of this same mechanism, no new
  ADR.** `Templates/` (ADR-006) gains one more file, pre-filling the
  resolved Research schema (`Implementation/Plans/2026-08-10-vault-
  taxonomy-draft.md` → "Researches"): `type: Research`, `title:`, `author:`,
  `tags: [kind/research]` — placeholder values follow the same
  `REPLACE_WITH_...` convention the existing four templates already use
  (e.g. `Templates/Customer.md`'s `REPLACE_WITH_CUSTOMER_NAME`), and the
  body is left free-form (no forced headings), matching the schema
  resolution's own "frontmatter stays deliberately thin" framing.
  **Deliberately no customer/company wikilink or tag** — a book/read isn't
  inherently tied to a customer relationship (the same reasoning already
  applied to a Person note with no known company); this is a real absence
  of a link target, not an overlooked one, per `MEMORY.md`'s standing
  tags-and-wikilinks rule. `Work/Guides/Manual-Entry-Guide.md` (ADR-006)
  gains a fifth `## Research` section, matching the existing four sections'
  exact shape (`**Folder:** ... · **Template:** ...` line plus a short
  explanatory paragraph), and its opening paragraph's "four note types"
  count is updated to five — additive only, the four existing entries are
  untouched (append-only extension of vault content, not a rewrite of the
  `Done` REQ-SB-15-US-01 story's own file). Both files live in the real
  vault at `VAULT_PATH`, not `src/backend`/`src/frontend`.

### Person Notes & Email-Sender Extraction (REQ-SB-10)

- **Person notes** — `Work/People/<slug-of-email-address>.md` (`People` is
  another dynamically-discovered `kind` folder, per `list_known_kinds`, no
  code change needed). Schema resolved in `Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "People": `type`, `name`, `email`,
  `phone`, `linkedin`, `tags` frontmatter; an inline body wikilink to the
  sender's company's Customer hub note when (and only when) the company
  matches a known customer, extending the same inline-body-link convention
  `customer_hub_linking.py` established (see "Customer Hub Notes & Graph
  Linking", above) rather than a new linking mechanism.
- **Filename / dedup key: the sender's email address, lowercased and
  slugified — never the display name.** Two people can share an identical
  display name; email addresses are the schema's own dedup key ("deduped by
  email address (names vary in formatting, addresses don't)" per the
  resolved schema). Lowercasing before slugifying prevents a second,
  spurious Person note when the same address is captured with different
  casing across different emails (e.g. Exchange does not guarantee
  consistent `sender_email` casing). This is a straight reuse of the
  existing `_slugify` filename-safety helper already used for
  `hub_note_path`/`write_note` — email addresses do not contain any of the
  characters `_slugify` strips, so this is effectively a lossless,
  collision-safe identity mapping (per `MEMORY.md`'s filename-uniqueness
  constraint). The `email:` frontmatter field itself still stores the
  sender's address exactly as captured (not lowercased), so the filename
  normalization is a lookup-key concern only, not a display-value edit.
- **Company derivation from the sender's email domain** (`app/business/
  people_extraction.py::derive_company_from_email`): take the substring
  after `@` in `sender_email`, lowercase it, and check it against a small
  **hardcoded** set of well-known personal/free email-provider domains
  (`gmail.com`, `googlemail.com`, `outlook.com`, `hotmail.com`, `live.com`,
  `msn.com`, `yahoo.com`, `ymail.com`, `icloud.com`, `me.com`, `aol.com`,
  `protonmail.com`, `proton.me`, `gmx.com`, `mail.com`, `yandex.com`,
  `zoho.com`). A domain on that list yields no company at all (Scenario 5 —
  tag/link both absent). Otherwise the company slug/name is derived from the
  domain's first label — `core42.ai` → slug `core42`, display name
  `Core42` (`slug[0].upper() + slug[1:]`) — matching the resolved schema's
  own worked example verbatim. **This blocklist is deliberately fixed, not
  vault-derived like `list_known_customers`/`list_known_kinds`.** Those two
  lists enumerate values that are genuinely open-ended per-vault content (a
  new customer or a new Compass-proposed kind can appear any day); the
  universe of major personal/free email providers is a small, well-known,
  externally-stable set that has nothing to do with this vault's own
  content — there is no vault signal that could ever grow or shrink it the
  way real customer/kind values do, so hardcoding it is not the same
  shortcut `list_known_customers` deliberately replaced. Revisit only if a
  real captured sender surfaces a personal-domain provider missing from
  this list (extend the constant then — no architecture change needed).
- **Company-to-known-customer matching** (`app/business/
  people_extraction.py::find_matching_customer`): compares the derived
  company name against every name `vault_writer.list_known_customers()`
  returns, **not** by exact string equality but by comparing each side's
  tag-slug form (`core42` vs `Core42` vs `CORE42` must all match). This
  reuses the exact slugging rule tags already use rather than inventing a
  second normalization scheme: `vault_writer`'s previously-private
  `_tag_slug` helper is promoted to a public `tag_slug(text: str) -> str`
  (pure rename, no behaviour change, existing internal call sites updated)
  so business-layer code has one shared, public normalization function
  instead of duplicating slug logic outside `data_access`. Returns the
  matching known-customer's original (non-slugified) name — the exact
  string `customer_hub_linking`'s hub-note primitives expect — or `None`.
- **Layering — new Person-note primitives in `data_access`, orchestration in
  a new `app/business/people_extraction.py`,** following ADR-003 and the
  same one-module-per-maintenance-operation shape as `tag_backfill.py` /
  `vault_restructure.py` / `customer_hub_linking.py`:
  - `app/data_access/vault_writer.py` gains: `person_note_path(email)`,
    `person_note_exists(email)`, `build_person_tags(company: str | None)`
    (returns `["kind/person"]` alone, or `["company/<slug>", "kind/person"]`
    when a company was derived — mirrors `build_tags`'s shape but for the
    People schema's separate `company/` tag namespace), and
    `create_person_note_baseline(name, email, tags)` /
    `ensure_person_note_baseline_frontmatter(path, name, email, tags)`
    (baseline keys: `type`, `name`, `email`, `phone`, `linkedin`, `tags` —
    same surgical insert-if-missing contract as the hub-note baseline
    functions). The existing generic `insert_body_line_if_missing` is
    reused as-is for the company wikilink line — no Person-specific
    variant needed, it already takes an arbitrary `path`/`line`.
  - `app/business/people_extraction.py` (new) owns
    `derive_company_from_email`, `find_matching_customer`, and
    `ensure_person_note(name, email)` — the shared "ensure this sender's
    Person note exists and is up to date" operation, called once as a
    one-time batch (`retrofit_people_from_emails`, iterating
    `vault_writer.list_all_note_paths()` and reading each note's `sender`/
    `sender_email` frontmatter — Person and Customer hub notes are silently
    skipped by construction, since neither carries a `sender_email` field)
    and once as a per-write hook
    (`ensure_person_note_for_captured_email(sender_name, sender_email)`).
    Both entry points skip (no error) when `sender_email` is blank
    (Scenario 9).
  - **`ensure_person_note` calls `customer_hub_linking`'s two granular
    primitives directly (`ensure_customer_hub_note`,
    `link_note_to_customer_hub`), never the combined
    `ensure_hub_note_and_link`, and only after `find_matching_customer`
    confirms a real match.** This is the load-bearing carve-out the story's
    Constraints require: `ensure_hub_note_and_link` unconditionally creates
    a Customer hub note for whatever string it's given, correct for email
    classification (every classified note already belongs to a real
    customer) but wrong for an arbitrary derived company name, most of
    which are not customers at all. Gating on `find_matching_customer`
    first, then calling only the two granular primitives, reuses
    REQ-SB-14's actual file-I/O work (hub note creation/top-up, idempotent
    body-line insertion) without its unconditional-creation entry point —
    a company with no match gets its `company/<slug>` tag and nothing else,
    per `MEMORY.md`'s standing tags-and-wikilinks rule ("a tag with no link
    target is a real absence, not an overlooked link").
  - **This is the first time one `business/` module calls into another
    `business/` module** (`people_extraction.py` → `customer_hub_linking.py`).
    ADR-003 constrains `business/` to no HTTP and no direct filesystem/data
    I/O of its own — it does not forbid one business module composing
    another's already-layered orchestration. This is a horizontal call
    within the same layer, not a boundary violation, and is recorded here
    explicitly so it reads as an intentional, permitted shape rather than an
    unreviewed precedent for future stories.
  - The retrofit is exposed as a new one-off endpoint,
    `POST /poc/retrofit-people-from-emails`, in `app/api/
    email_poc_router.py` — matching the existing `/poc/backfill-tags`,
    `/poc/flatten-customer-folders`, and `/poc/retrofit-customer-hub-links`
    one-off-migration-endpoint precedent. One endpoint is sufficient; the
    retrofit is a single operation over all already-captured Email notes,
    the same shape as REQ-SB-14's own single retrofit endpoint.
  - **Going-forward hook:** `app/business/email_classification.py`'s
    `classify_recent_emails` gains one additional call,
    `people_extraction.ensure_person_note_for_captured_email(email["sender_name"],
    email["sender_email"])`, placed immediately after the existing
    `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`
    call (REQ-SB-14) — added alongside it, not replacing it; the two hooks
    serve different note types (Customer hub notes keyed by the email's own
    customer classification; Person notes keyed by the email's sender) and
    are independently idempotent.
- **Preserving manually-added Person-note content** follows the exact
  baseline-preservation contract already established for Customer hub notes
  (see above): baseline frontmatter keys (`type`, `name`, `email`, `phone`,
  `linkedin`, `tags`) are inserted only if missing, never overwritten once a
  real value exists; the body, once created, is never programmatically
  rewritten wholesale — only the company wikilink line may be surgically
  inserted later if a company becomes a known customer after the Person
  note already existed (Scenario 8), reusing `insert_body_line_if_missing`
  exactly as `customer_hub_linking.link_note_to_customer_hub` already does.
- **Meeting-attendee-based extraction is explicitly out of scope for this
  pass** (blocked on REQ-SB-08, which does not yet exist) — `ensure_person_note`
  is written generically enough (`name`, `email` in, no email-specific
  parameters beyond the two call sites' own inputs) that a future
  meeting-attendee story can call it the same way, but that wiring is not
  built here.
- **Email → Person wikilink, the inbound direction (`BUGFIX-01`, closes
  `BUG-001`).** The per-write hook and the original retrofit above only ever
  created/updated the sender's Person note as a side effect — the Email
  note's own body never linked back to it, so a Person note rendered as a
  disconnected graph node relative to every Email that actually mentions it
  despite existing (`MEMORY.md`'s 2026-08-11 standing constraint: a
  referencing note must link out, not just cause the referenced note to be
  created). This is closed with the exact same inline-body-wikilink
  mechanism already in place for Customer hub links, not a new one:
  - `app/business/people_extraction.py` gains one small primitive,
    `link_email_to_person(email_note_path, person_note_path) -> bool`,
    mirroring `customer_hub_linking.link_note_to_customer_hub`'s shape —
    it derives the Person note's filename stem and inserts a
    `**Sender:** [[PersonStem]]` line into the Email note's own body via
    the same `vault_writer.insert_body_line_if_missing` primitive the
    Email note's existing `**Customer:** [[Hub]]` line already uses (a
    second surgical first-line insertion into the same note, not a new
    mechanism). Because `insert_body_line_if_missing` always inserts at the
    top of the body, calling it a second time places the newer line above
    the one inserted by the earlier call in the same write — the Email
    note ends up with `**Sender:** [[...]]` above `**Customer:** [[...]]`
    given the two calls' existing order; cosmetic only, no AC depends on
    relative line order.
  - `app/business/email_classification.py`'s `classify_recent_emails`
    captures the already-existing return value of its
    `people_extraction.ensure_person_note_for_captured_email(...)` call
    (previously discarded) and, when it is not `None`, calls
    `people_extraction.link_email_to_person(note_path, person_result["note_path"])`
    — `note_path` is the just-written Email note's own path, already in
    scope at that call site (`note_path = vault_writer.write_note(...)`,
    above). No new plumbing, no signature change to
    `ensure_person_note_for_captured_email` itself (left untouched so any
    future caller, e.g. a `REQ-SB-08` meeting-attendee hook, is
    unaffected).
  - A new one-time batch, `people_extraction.retrofit_email_sender_links`,
    mirrors `retrofit_customer_hub_links`'s and
    `retrofit_people_from_emails`'s exact shape: iterate
    `vault_writer.list_all_note_paths()`, skip a note with no
    `sender_email` (Person/Customer-hub notes are skipped by construction,
    same as the existing retrofits), otherwise call `ensure_person_note`
    (guaranteeing the Person note exists/is current — safe and idempotent
    to call again even if `retrofit_people_from_emails` already ran) then
    `link_email_to_person`. Exposed as a new one-off endpoint,
    `POST /poc/retrofit-email-sender-links`, in
    `app/api/email_poc_router.py`, matching the three existing
    one-off-migration-endpoint precedents
    (`/poc/retrofit-customer-hub-links`, `/poc/retrofit-people-from-emails`,
    `/poc/backfill-tags`).
  - No new structural boundary, tool, or framework decision — this closes a
    coverage gap in the already-Accepted inline-body-wikilink convention
    (established for Customer hub links, already reused as-is for
    Person→Company), applied to a relationship direction the original
    `REQ-SB-10` pass didn't check. No ADR.

### Meeting Notes & Calendar-Attendee Extraction (REQ-SB-08)

- **Meeting notes** — `Work/Meetings/<subject>-<date>-<suffix>.md` (the
  8-hex-char suffix's source changed 2026-08-11, [ADR-013](ADR.md); see
  below) (`Meetings` is another dynamically-discovered `kind` folder, per
  `list_known_kinds`, no code change needed). Schema resolved in
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "Meetings":
  `type`, `customer`, `subject`, `start`, `end`, `location`, `organizer`,
  `tags` frontmatter; inline body `**Customer:** [[Hub]]` (when an
  attendee's company matches a known customer) followed by `**Attendees:**
  [[Person1]], [[Person2]], ...`. One note per meeting — no separate
  Meeting-Minutes type; free-form minutes/notes live below the
  auto-populated baseline, never programmatically rewritten once added,
  same living-document rule as Person/Customer-hub notes.
- **Calendar read — `app/data_access/outlook_com.py::list_calendar_events`
  (new, [ADR-008](ADR.md)).** Ports agentic-map's
  `list_upcoming_events`/`list_calendar_since` COM mechanics
  (`ns.GetDefaultFolder(9)`, `items.IncludeRecurrences = True`) into this
  codebase's own `list_recent_mail`-shaped conventions (plain sync
  function, `pythoncom.CoInitialize`/`CoUninitialize`, best-effort
  per-item skip). **The sync window is one bounded date range around
  "now"** (`[now - days_back, now + days_ahead]`) rather than either of
  agentic-map's two narrower semantics alone — this is what "the sync
  window" in the PRD's acceptance text concretely means for this project.
  Per-event fields: `id` (EntryID), `subject`, `start`/`end`, `location`,
  `organizer`, `attendees: list[{"name", "email"}]` (`To` + `Cc` merged
  into one flat list — the resolved schema makes no required/optional
  distinction). Full reasoning, including the alternatives rejected:
  [ADR-008](ADR.md).
- **Occurrence dedup key: a SHA-256 hash of `subject` + the occurrence's
  own full, precise start timestamp — no Outlook-provided identity field
  at all ([ADR-019](ADR.md), 2026-08-12, supersedes [ADR-013](ADR.md)
  points 1 and 2).** This is the **third** dedup-key mechanism this project
  has tried, named plainly rather than glossed over: `ADR-008` originally
  chose `EntryID`, live-confirmed non-unique per occurrence
  (`ESCALATIONS.md` → `ESC-002`); `ADR-013` then replaced it with
  `AppointmentItem.GlobalAppointmentID` (Outlook's own documented
  guaranteed-unique-per-occurrence identifier), which live verification
  found has the **exact same defect** on this Outlook installation —
  identical across every real occurrence of two separate recurring series,
  with its documented `PropertyAccessor`/DASL fallback erroring on every
  occurrence too (`ESCALATIONS.md` → `ESC-012`). Rather than search for a
  third Outlook-native identity field to trust empirically, `ADR-019` stops
  depending on Outlook-provided identity altogether: the filename/dedup
  suffix is an **8-hex-char prefix of a SHA-256 hash of
  `f"{subject}|{start}"`**, where `start` is the full precise timestamp
  string `list_calendar_events` already returns (not the coarse
  `start[:10]` date-only slice the filename's own display component still
  uses). This is a **structural**, not empirical, uniqueness guarantee —
  two distinct real occurrences of the same recurring series cannot share
  an identical exact start moment; the subject is combined in so two
  different, unrelated meetings that happen to start at the same instant
  still get distinct notes. `list_calendar_events` no longer resolves or
  depends on any per-occurrence identity field for dedup purposes (the
  `GlobalAppointmentID`-resolution helper and its DASL fallback, added by
  the now-superseded `ADR-013` fix, are removed); `id` (`EntryID`) is still
  returned, load-bearing again for one narrow purpose only — the
  legacy-path lookup below. `.second-brain/processed_meeting_ids.json`
  still mirrors `processed_email_ids.json`'s flat-set-of-IDs shape
  (`load_processed_meeting_ids()`/`mark_meeting_processed(marker)`), now
  recording the resolved note's own filename stem as its `marker` value;
  its existing heterogeneous `EntryID`-era and `GlobalAppointmentID`-era
  entries (written before this fix) are left untouched — it remains an
  append-only audit trail, never a schema-enforced lookup structure.
  **No migration of the 39 already-captured Meeting notes** — note-existence
  resolution checks the new precise-timestamp-hash path first, then falls
  back to the original pre-`ADR-013` legacy `EntryID`-suffix path;
  whichever is found on disk gets topped up. **`ADR-013`'s own middle
  `GlobalAppointmentID`-hash fallback tier is deliberately dropped, not
  carried forward** — confirmed live that zero real notes were ever
  created under that scheme, so keeping it would be dead code carrying a
  live-confirmed defect rather than a genuine safety net. Full reasoning,
  every alternative considered, and the one honestly-named residual risk
  the legacy-path fallback still does **not** fully close (unchanged from
  `ADR-013`, a bounded, shrinking-over-time edge case limited to the
  38/39 already-known dates): [ADR-019](ADR.md); `ADR-013` itself is
  `Status: Superseded by ADR-019` (points 1/2), its point 3 unmodified and
  reused.
- **Customer derivation tie-break: majority vote among attendee-company
  matches, first-encountered match as the tie-break.** For each attendee
  (after the vault-owner self-email exclusion, below), `meeting_
  classification.py` calls the existing, unchanged
  `people_extraction.derive_company_from_email` /
  `find_matching_customer` per attendee email and tallies how many
  attendees matched each known customer; the customer with the most
  matches wins, and a tie is broken by whichever matched customer was
  first encountered in Outlook's own attendee order (`To` then `Cc`). No
  match among any attendee means no `customer` tag/wikilink (per the
  resolved schema). **Majority, not organizer-priority or first-match, and
  why:** majority correctly reflects "who this meeting is really about"
  when several attendees share one company (the common real case — a
  customer meeting typically has multiple people from the customer's
  side), where a pure first-match would key off whichever attendee
  Outlook happens to return first (an ordering artifact, not a real
  signal). Organizer-priority was also considered and rejected: Outlook's
  `Organizer` COM property is a display-name string with no readily
  available email address to run `derive_company_from_email` against
  (unlike attendees, resolved to real addresses via `Recipients`/
  `GetExchangeUser`) — reliably resolving an organizer's own address would
  be new, unproven COM mechanism this story's port-don't-design-fresh
  constraint discourages. This is a business-rule/algorithm decision
  within already-established primitives, not a new tool/framework/
  structural-boundary choice — recorded here, not as its own ADR.
- **Vault-owner self-email exclusion (Scenario 11, operator-confirmed
  behaviour) — sourced from a new `Settings.self_email` config value, not
  a dynamic Outlook COM lookup.** `app/config.py`'s `Settings` gains a
  required `self_email: str` field (`.env`-sourced, alongside
  `VAULT_PATH`/`COMPASS_*`). `meeting_classification.py` filters
  `self_email` (case-insensitive) out of `list_calendar_events`'s
  attendee list before any attendee reaches
  `people_extraction.ensure_person_note` or customer derivation — no
  Person note about the vault owner, and their own company (if any) never
  participates in the majority vote above. Full reasoning (why config over
  a `Session.CurrentUser` COM lookup): [ADR-008](ADR.md).
- **Attendee Person notes — direct reuse, no new mechanism.** Every
  attendee (post-exclusion) gets the exact `people_extraction.
  ensure_person_note(name, email)` treatment already built for email
  senders (REQ-SB-10) — the function was already written generically
  enough for this (`architecture.md`'s own prior note); this story calls
  it once per attendee, unchanged. Customer-hub linking for a meeting's
  derived customer reuses the same granular-primitives-only-after-a-
  confirmed-match carve-out `people_extraction.ensure_person_note` already
  established for company matches — `meeting_classification.py` must not
  call `customer_hub_linking.ensure_hub_note_and_link` directly for an
  unconfirmed match, per the story's Constraints.
- **Scheduler wiring — rides REQ-SB-07's existing hourly job, no new job.**
  `email_classification.run_capture_and_record_completion` gains one
  additional call, `meeting_classification.classify_recent_meetings()`,
  alongside its existing `classify_recent_emails()` call, before the one
  shared `vault_writer.record_capture_run_completed()` call.
  `app/scheduling/capture_scheduler.py` requires zero code changes — it
  already treats `run_capture_and_record_completion` as an opaque unit.
  Extends ADR-005 (which explicitly anticipated "generalizing the one job
  to run multiple pipelines" as the intended path) without rewriting or
  contradicting it. Full reasoning: [ADR-008](ADR.md).
- **New vault_writer primitives (data_access, REQ-SB-08).** Meeting-note
  path resolution and baseline-frontmatter create/top-up follow the exact
  same insert-only-if-missing contract already established for
  Person/Customer-hub notes. The `**Attendees:** [[P1]], [[P2]], ...]`
  body line needs a **new** primitive, distinct from the single-target
  `insert_body_line_if_missing` reused as-is for the `**Customer:**
  [[Hub]]` line: unlike a single-target link (present or not), the
  Attendees line can legitimately grow across reruns as new attendees are
  confirmed (Scenario 6), so it needs a per-attendee-wikilink upsert, not
  a whole-line insert-if-missing. Exact function shape left to the
  decomposer/coder; this generalizes the existing "insert this line/key if
  absent" philosophy already applied twice (frontmatter keys, then a
  single body line) rather than introducing a new one.

### Task Notes & Outlook-Tasks Capture (REQ-SB-09, see [ADR-027](ADR.md))

- **Task notes — `Work/Tasks/<subject>-<capture-date>-<entry-id-
  suffix>.md`.** `Tasks` is another fixed, dynamically-discovered `kind`
  folder (per `list_known_kinds`, no code change needed), mirroring
  `Work/Meetings/`'s own shape — Task, like Meeting, is its own note type,
  never a Compass-classified `kind`. Schema (confirmed by the story, see
  `REQ-SB-09-US-01`'s own `## Context`): `type: Task`, `customer` (present
  only when a match is found), `subject`, `due` (omitted, not written as a
  placeholder, when Outlook has no due date set), `status: Not Started |
  In Progress | Completed` (three-value mapping from Outlook's own
  `Complete`/`Status` fields — see [ADR-027](ADR.md) point 2), `tags`,
  `source: outlook-task`, `outlook_entry_id`. Body starts with `**Customer:**
  [[Hub]]` when a match exists (reusing `insert_body_line_if_missing` as-is,
  the same single-target line Email/Meeting already use for their own
  Customer line), followed by free-form space for the user's own notes —
  never programmatically rewritten once added, the same living-document
  rule every other captured note type already follows. **Unlike Meeting
  notes, a Task note links no Person** — an Outlook Task has no attendee/
  contact list, so there is no natural entity relationship to wikilink
  beyond the optional customer match; this is an intentional absence
  (the story's own Constraints), not a gap in the standing tags-and-
  wikilinks rule.
- **`capture-date` in the filename is the date the note was FIRST
  captured — never recomputed from Outlook's own (mutable) `due` field on
  a later run.** This is the load-bearing reason Task's own dedup mechanism
  (below) genuinely diverges from Meeting's: Scenario 6 requires a due-date
  change between runs to still resolve to the *same* note, which a
  recompute-from-`due` filename (Meeting's own `ADR-019` pattern,
  substituted field-for-field) would break.
- **Tasks-folder read — `app/data_access/outlook_com.py::
  list_outlook_tasks` (new, [ADR-027](ADR.md)).** `ns.GetDefaultFolder(13)`
  (`_OL_FOLDER_TASKS`), no date-window parameters (unlike
  `list_calendar_events`) — a flat `limit`, mirroring `list_recent_mail`'s
  simpler shape, since a task has no natural "occurs near now" framing.
  Per-item fields: `id` (`EntryID`), `subject`, `due` (`None` when
  Outlook's own "no date set" sentinel is detected — a defensive guard,
  not optional polish, since it is what makes the schema's "omitted if
  none is set" possible), `status`, `body`. **No `IncludeRecurrences`-
  equivalent exists on the Tasks folder's `Items` collection at all** — a
  structural fact about the Outlook Object Model (that property is
  Calendar-folder-specific), and the reason a recurring Task never expands
  into multiple simultaneously-returned occurrence-items the way a
  recurring meeting does — the specific mechanism that broke `EntryID`/
  `GlobalAppointmentID` for Calendar (`ESC-002`, `ESC-012`) structurally
  does not apply to Tasks. Full reasoning, including the alternatives
  rejected: [ADR-027](ADR.md).
- **Dedup/top-up key: `EntryID`, looked up through a new load-bearing
  `.second-brain/task_note_index.json` (`{entry_id: note_filename_stem}`),
  consulted BEFORE any path is computed from current Outlook fields —
  not a recomputed-deterministic-path check the way Meeting's
  `resolve_meeting_note_path` works.** A first-time-seen `entry_id` (not
  yet in the index) creates a new note and records the mapping; a
  known `entry_id` tops up whichever note the index already names,
  regardless of what `due`/`status`/`subject` now read as in Outlook. This
  is a genuine, reasoned divergence from Meeting's own `ADR-019`
  mechanism, forced by Scenario 6's own AC text — full reasoning,
  including the honestly-disclosed residual risk (EntryID stability was
  not live-verified this pass — the architect had no live-Outlook
  execution capability available in this environment) and the coder's own
  assigned live-verification step: [ADR-027](ADR.md).
- **Customer classification: `app/data_access/compass_client.py::
  classify_task(subject, body, known_customers)` (new, [ADR-027](ADR.md)),
  customer-only, not a reuse of `classify_email`.** A Task has no sender
  and needs no `kind` axis (folder placement is fixed, above) —
  `classify_email`'s combined customer+kind, sender-framed prompt does not
  fit without discarding half its own output and misrepresenting an absent
  sender. `classify_task` lives alongside `classify_email` in the same
  module, one more classification prompt function, not a new client.
- **Scheduler/working-mode wiring — rides `REQ-SB-07`'s existing hourly
  job, no new job.** `email_classification.run_capture_and_record_completion`
  gains a third gated block (mirroring the existing `"meeting-capture"`
  one exactly), calling a new `todo_classification.classify_recent_todos()`
  via `run_capture_for_agent("todo-capture", ...)`. `"todo-capture"` is
  already a registered agent (`agent_registry.py`, pre-seeded ahead of this
  story); `working_mode_registry`'s existing self-healing default already
  covers it. `app/scheduling/capture_scheduler.py` requires zero code
  changes — the third pipeline in a row to ride the same opaque
  `run_capture_and_record_completion` unit. Full reasoning, including why
  `run_capture_and_record_completion` stays inside `email_classification.py`
  rather than being extracted into a dedicated orchestration module (an
  explicit fork `ADR-008` itself flagged for revisit at exactly this
  point): [ADR-027](ADR.md). **Extends `REQ-SB-11-US-01`'s honest-failure-
  funnel to a third branch, per that story's own already-established
  pattern, not a new one:** the new `"todo-capture"` gated block gets its
  own independent `try/except Exception as exc:` around its
  `run_capture_for_agent("todo-capture", ...)` call (mirroring the
  existing email/meeting branches exactly, per "Agent Activity & Error
  Observability", above) — one branch's failure this tick must never
  suppress another's success being recorded, the same reasoning that
  section already documents for the first two branches.
- **New `vault_writer.py` primitives (data_access, REQ-SB-09).** Task-note
  path resolution (via the index above, not a recompute-and-check),
  baseline-frontmatter create/top-up, and the EntryID-keyed index's own
  load/lookup/record primitives follow the existing insert-only-if-missing/
  paired-state-file-primitive contracts already established
  (Person/Customer-hub/Meeting, and `conversation_index.json`'s own
  real key→value lookup shape, respectively) — no new philosophy, two
  existing ones combined for a genuinely new load-bearing (not merely
  audit) lookup shape. Exact function names left to the decomposer/coder.

### Partner Hub Notes & Mutually-Exclusive Company Taxonomy (REQ-SB-16)

- **Partner hub note per partner:** `Work/Partners/<Partner>.md` —
  `Partners` is a `kind` folder like `Work/Customers/`, holding one
  `Partner`-type note per partner. Schema (`Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Partners"):
  `type: Partner`, `partner: <Name>`, `tags: [partner/<slug>, kind/partner]`
  — deliberately **no** `affiliate_of` key (Partner has no Affiliate
  concept) and **no** Pipeline/Agreements/Consumption-Snapshot-equivalent
  sub-entities (operator's explicit scoping — a partner relationship isn't
  a sales/Azure-consumption relationship). Body: the same living-document
  convention as the Customer hub note (auto-generated baseline stub, then
  user-added overview/contacts never programmatically rewritten again).
- **`partner/<slug>` is mutually exclusive with `customer/<slug>`.** A
  company is a Customer, a Partner, or neither, never both (operator's
  explicit choice, `MEMORY.md` 2026-08-11). `people_extraction.
  ensure_person_note` checks `find_matching_customer(company)` first
  (unchanged) and only calls the new `find_matching_partner(company)` when
  no Customer match was found — at most one of `customer_matched`/
  `partner_matched` is ever non-`None` on a given call. `find_matching_partner`
  mirrors `find_matching_customer` exactly (tag-slug comparison via
  `vault_writer.tag_slug`, against a new vault-derived
  `vault_writer.list_known_partners()` mirroring `list_known_customers()`'s
  frontmatter-scan pattern — never hardcoded).
- **New module, `app/business/partner_hub_linking.py` — a parallel sibling
  to `customer_hub_linking.py`, not an extension of it** (full reasoning:
  [ADR-009](ADR.md)). Structurally mirrors `customer_hub_linking.py`'s two
  granular primitives exactly:
  - `ensure_partner_hub_note(partner: str) -> dict` — mirrors
    `ensure_customer_hub_note`: creates the hub note if missing, tops up
    missing baseline frontmatter keys (`type`, `partner`, `tags`) if it
    already exists, never touches the body.
  - `link_note_to_partner_hub(note_path, partner: str) -> bool` — mirrors
    `link_note_to_customer_hub`: inserts a `**Partner:** [[Hub]]` inline
    body line (same `vault_writer.insert_body_line_if_missing` primitive,
    same idempotent insert-if-not-present contract), replacing the
    `**Customer:**`-labelled line the linking mechanism would otherwise
    have written for a company later reclassified as a Partner.
  - `ensure_person_note` calls these two granular primitives directly on a
    confirmed Partner match — the exact same "granular primitives only,
    never a combined unconditional-creation entry point, only after a
    confirmed match" carve-out already established for Customer (see
    "Person Notes & Email-Sender Extraction", above). No
    `ensure_hub_note_and_link`-equivalent combined function is added for
    Partner, and no per-write capture-pipeline hook is wired into
    `email_classification.py`/`meeting_classification.py` for it — the
    story's own Non-Goals scope Partner linking to the Person-note
    orchestration only, mirroring how Customer linking is reached from
    `ensure_person_note` today.
  - **New `vault_writer.py` primitives**, mirroring the Customer hub-note
    baseline family exactly but with Partner's shorter baseline-key set
    (`type`, `partner`, `tags` — no `affiliate_of`): `partner_hub_note_path`,
    `partner_hub_note_exists`, `create_partner_hub_note_baseline`,
    `ensure_partner_hub_note_baseline_frontmatter`, `build_partner_tags`
    (returns `[f"partner/{tag_slug(partner)}", "kind/partner"]`, mirroring
    `build_tags`'s shape), and `list_known_partners`.
- **One-time migration: `Work/Customers/Microsoft.md` → `Work/Partners/
  Microsoft.md`, plus a generic vault-wide retag** —
  `partner_hub_linking.migrate_customer_to_partner(customer_name: str)`
  (parameterised, not hardcoded to "Microsoft", even though Microsoft is
  the only real data today). Two steps:
  1. **Move the hub note** — `vault_writer.move_note_and_attachments`
     (already exists, used by `vault_restructure.flatten_customer_folders`)
     moves `Work/Customers/<name>.md` to `Work/Partners/<name>.md`, then its
     frontmatter is rewritten: `type: Customer` → `Partner`, `customer:
     <name>` → `partner: <name>` (the `affiliate_of` key is dropped —
     Partner has no such key), `tags` swaps `customer/<slug>` →
     `partner/<slug>` and `kind/customer` → `kind/partner`. Obsidian
     resolves `[[wikilinks]]` by filename, not full path, so existing
     `[[Microsoft]]` links elsewhere keep resolving unchanged.
  2. **Generic retag pass — matches on a union of two signals, not
     frontmatter alone.** Iterates every vault note via the existing
     `list_all_note_paths()`/`read_note()` scan (the same pattern
     `retrofit_customer_hub_links`/`retrofit_people_from_emails` already
     use). A note is in scope if **either**:
     - **Signal A (frontmatter):** its `customer` frontmatter equals
       `customer_name` — the original `ADR-009` point 4 condition, still
       correct for the hub note itself and every Email/Newsletter/
       Notification note that was actually given a `customer:` field; or
     - **Signal B (inline body wikilink, [ADR-012](ADR.md)):** its body
       contains the exact line `**Customer:** [[<hub note filename
       stem>]]`, regardless of whether `customer` frontmatter is present
       at all.

     Both signals are read from the **same** `read_note(path)` call already
     made once per note in the existing loop — no second vault scan, no
     extra file I/O. For an in-scope note the pass then: renames the
     `customer` frontmatter key to `partner` (same value; a no-op for a
     note with no `customer` key), swaps the `customer/<slug>` tag for
     `partner/<slug>` (no-op if absent), and — only where the inline
     `**Customer:** [[<name>]]` body line is present — relabels it to
     `**Partner:** [[<name>]]` (this is the only change that fires for a
     Signal-B-only note). **This is a generic scan, not a hardcoded list of
     specific notes** — live vault inspection during the original
     architecture pass found the mistagged set is larger than the story's
     own illustrative count (1 Newsletter note, 4 Notification notes also
     carry `customer: Microsoft`/`customer/microsoft`), and a second live
     inspection (`ESC-001`, during `REQ-SB-16-US-01-T04`'s pre-migration
     sanity check) found the 5 real `Work/People/*.md` Microsoft Person
     notes carry **no** `customer` frontmatter or tag at all — Person notes
     were never designed to carry one (`REQ-SB-10`'s schema only ever gives
     them a `company/<slug>` tag) — only the inline `**Customer:**
     [[Microsoft]]` wikilink Signal B now catches. Full reasoning:
     [ADR-009](ADR.md) (original generic-scan design, points 1–3/5
     unaffected and still `Accepted`) and [ADR-012](ADR.md) (the Signal-B
     extension to point 4's match predicate).
  3. **Idempotency.** Three new **generic** (not Partner-specific)
     `vault_writer.py` primitives make reruns safe: a frontmatter-key
     rename (no-op once the old key is already absent), a tags-list swap
     (no-op once the old tag is already absent), and a body-line-label
     replace (no-op once the old line is already absent) — each mirrors the
     existing insert-if-missing family's "return whether it did anything"
     contract, generalized from "insert if absent" to "replace if present."
  4. **Endpoint:** `POST /poc/migrate-customer-to-partner` (accepts a
     `customer_name` parameter) in `app/api/email_poc_router.py`, matching
     the existing one-off-migration-endpoint precedent
     (`/poc/flatten-customer-folders`, `/poc/retrofit-customer-hub-links`,
     `/poc/retrofit-people-from-emails`, `/poc/retrofit-email-sender-links`).
- **`ensure_person_note`'s return dict gains a `partner_matched` key**
  alongside the existing `company`/`customer_matched`/`linked` keys —
  additive only; existing callers reading the prior keys are unaffected.

**Explicitly not yet adopted** from the book (tracked as open questions, not
silent gaps): atomic notes (today's notes are full raw captures, not
one-idea distillations), output-oriented structure (organized around
`Customer`, an input entity, not around what gets produced from the vault),
and the AI Staging review gate for AI-generated classification (deferred by
the operator 2026-08-10 — direct-write stands until real misclassifications
justify revisiting it).

## Authentication & Authorisation

[Describe the auth approach — likely none/local-only for a single-user tool, to be
confirmed at `/plan-tasks`.]

## Local Development

Backend (from `src/backend`):

```
.venv\Scripts\pip.exe install -r requirements.txt   # first time / after changes
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.venv\Scripts\python.exe -m pytest -q
```

Frontend (from `src/frontend`, after dot-sourcing `tools/use-node.ps1` once per
shell session so `npm`/`npx` resolve to the portable toolchain):

```
. ..\..\tools\use-node.ps1
npm install     # first time / after dependency changes
npm run dev
```

No admin rights are available on the development host, so neither toolchain is
system-installed — see [ADR-001](ADR.md) and [ADR-002](ADR.md).

**Scheduler runs automatically with the app (see [ADR-005](ADR.md)):** once
`app/scheduling/` is wired into `app/main.py`'s `lifespan`, every
`uvicorn app.main:app --reload` start (including each dev-server reload) fires
one real capture run immediately, then continues on an hourly interval for as
long as that process stays up. This hits the real Outlook/Compass integration
the same way `POST /poc/classify-emails` already does — be aware of this when
restarting the dev server repeatedly during REQ-SB-07 work.

Vault path is already configurable via `VAULT_PATH` in `.env`
(`app/config.py::Settings.vault_path`, used by every capture pipeline and,
as of `REQ-SB-01-US-01`, the vault indexing layer — see [ADR-024](ADR.md)).
Correcting a stale note left from before that config value existed in code.

## External Services

Hermes (MCP-based multi-channel communication) — planned integration, not yet
built.
