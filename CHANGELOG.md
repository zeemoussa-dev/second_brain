# CHANGELOG

All notable changes to Second Brain.

**2026-08-20:** Previous history (through the Hermes/LangGraph architecture
pivot) archived, not deleted — see `Documentation-Archive-2026-08-20/
CHANGELOG.md`. Starting fresh alongside the backend redesign
(`Implementation/Plans/2026-08-20-backend-architecture-redesign.md`,
`ADR-059`).

<!-- Format:
## YYYY-MM-DD — Sprint NNN / task description
- feat: what was added
- fix: what was fixed
- refactor: what was restructured
- docs: documentation changes
-->

## [Unreleased]

- feat: rebuilt `hermes_client.py`/`hermes_status.py`/`hermes_router.py`
  against Hermes' real, live-verified local API (`hermes serve`,
  `127.0.0.1:9119`, `x-hermes-session-token` auth) — replaces the
  original version, which was built from documentation that didn't match
  the actually-installed Hermes version. Verified end-to-end three layers
  deep against a real running Hermes instance (client → business wrapper
  → a real booted FastAPI app's own `/hermes/status`/`/hermes/sessions`
  routes), all returning real data. See `MEMORY.md` "Constraints" and
  `Implementation/Plans/2026-08-20-backend-architecture-redesign.md`.
- feat: wired the Tools registry into `main.py` and shipped the first
  real Action, `outlook -> email -> gather_emails` (thin wrapper over
  the existing, unmodified `pull_and_stage_emails`). Found and fixed two
  real bugs along the way: a mounted Tool's MCP server never initialized
  without its `session_manager.run()` lifespan entered explicitly
  (mirrors a gap `api/mcp_server.py`'s own mount already worked around);
  and `/mcp/outlook` silently 404'd because it sat inside the pre-existing
  `/mcp` mount's own path space (Starlette registration-order matching)
  -- fixed by moving Tool mounts to their own `/tools/<id>` prefix.
  Verified live: `/tools/outlook/` now answers with the same real MCP
  protocol response as the long-working `/mcp/` mount.
- feat: created the Backend Architecture Redesign skeleton (Data Access
  layer: `vault/`, `system/` incl. `provider/` and `tools/`; Business
  layer: `logic/`, `vault/`, `core/`, `hermes/`, `langgraph/`) alongside a
  real, tested `business/langgraph/proof.py` proving LangGraph works
  end-to-end against real vault data. See the same plan doc for the full
  block-by-block log, schema decisions, and open questions.
- feat: built the full vault-rebuild capture pipeline — 5 Actions
  (`ingest_email`, `rename_thread`, `link_person_to_thread`,
  `capture_attachments`, `capture_file_link`) plus a fetch-only
  `list_recent_emails`, initially exposed via a new `vault` MCP Tool
  alongside the existing `outlook` one, orchestrated by a new
  `email-thread-capture` Hermes Skill + cron job. Found and fixed 4 real
  bugs along the way, the most serious being a duplicate-Thread spawn
  when re-ingesting a message on an already-renamed Thread (wrong,
  rename-blind existence check — fixed by using `resolve_thread_
  directory` consistently everywhere). See the architecture redesign
  plan doc for the full block-by-block log.
- refactor: rewrote the email-thread-capture pipeline as fully
  Hermes-native — 8 standalone scripts (`vault_lib.py`, `outlook_lib.py`,
  one CLI entry point per Action) live directly in the Skill's own
  `scripts/` folder, invoked through Hermes' own `terminal` tool. No MCP
  server, no Second Brain backend dependency at all. Removed the 6 ported
  source files, the `vault` Tool's registry entry, and `list_recent_
  emails` from the `outlook` Tool — single source of truth moved to the
  Skill. Person-note creation in the new scripts is deliberately trimmed
  to bare name+email (no company/Customer/Partner matching or
  hub-linking — Capture-phase scope only; that enrichment stays Second
  Brain's own `retrofit_people_from_emails()` job, run later as a
  separate pass). Smoke-tested end-to-end against a scratch vault before
  the old code was deleted. See `ADR-002` for the full decision and
  alternatives considered.
- fix: message-note readable filenames (`<date> <sender>`) still
  collapsed into indistinguishable names whenever the same sender posted
  more than once in a thread on the same day — the hash-suffix collision
  fallback produced a second filename that still just reads "Name" in
  Obsidian's file view. Found live during the first real vault-rebuild
  pull. Fixed by including time-of-day (`<date> <HH:MM> <sender>`) in
  both `vault_lib.py` (deployed to the live Hermes install, took effect
  mid-run) and `app/data_access/vault_writer.py`'s `raw_message_note_path`
  for consistency. Already-written files from before the fix keep their
  old names for now — a one-time backfill/rename pass is planned once the
  current full-history pull completes, to avoid touching cross-references
  mid-run. See `MEMORY.md` "Patterns."
- feat: view-only backend mirror of Hermes' real Agent/Skill definitions
  — `GET /hermes/agents`, `GET /hermes/agents/{id}`. Reads Hermes' own
  files live on every call (`profile.yaml`, `config.yaml`, `SOUL.md`,
  every `SKILL.md`'s frontmatter) rather than a synced copy, so it can't
  drift from what Hermes actually has configured. New
  `app/data_access/hermes_definitions.py`, first real content in the
  `app/business/hermes/` skeleton folder (`definitions.py`), and
  `app/api/hermes_agents_router.py`. `HermesAgent`/`HermesSkill` naming
  (not bare `Agent`/`Skill`) avoids colliding with two other existing
  concepts in this codebase; every record carries `source: "hermes"`.
  Verified end-to-end against the real local Hermes install (all 4 real
  profiles — `default`/Primary plus `opp-manager`/`notes-manager`/
  `files-manager` — correctly discovered with accurate skill counts and
  config values) and against a real booted FastAPI app (`GET
  /hermes/agents/opp-manager` → 200 with real data; unknown id → 404).
  A scoped exception to ADR-001's "not ours to own" principle — see
  `ADR-003` for the full reasoning, alternatives, and the one open
  discrepancy (78 vs. 82 skills reported for Primary, not yet
  root-caused).
- feat/fix: retired the old Second-Brain-native orchestration agents for
  real (operator: "we're fully on Hermes now") — `agent_registry.py`'s
  10 hardcoded/persisted agents cleared, `main.py`'s lifespan no longer
  recreates the Librarian bootstrap on every app start. Restored Sections
  as Second Brain's own real, Hermes-independent concept — `app/api/
  sections_router.py` (verbatim from archive), real 6-Section taxonomy
  (Customer, Librarian, Industry, Technology, Data Gatherer, Sales),
  schema extended with `icon`/`color`/`subtitle`. Retrofitted
  `features/agents-map/` over the Hermes mirror via a new presentation
  adapter (`app/business/hermes/agents_map_adapter.py`) and fresh,
  view-only `app/api/agents_router.py`/`skills_router.py` at the same URL
  surface the frontend already calls — no frontend changes needed for
  list/detail rendering. Found and fixed a real stale-state bug along the
  way: `.second-brain/agent_sections.json` had already been seeded with
  the old 5-section list by an earlier app run, which the new seed-list
  code couldn't retroactively fix (seeding only fires when the file
  doesn't exist yet) — regenerated by hand. See `ADR-004` for the full
  reasoning, the archived-router alternative considered and rejected, and
  the one known follow-up (`/skills` is accurate but noisy — ~78 generic
  bundled skills on Primary alone — likely needs curation in a later UI
  pass).
- feat: ported the other 2 real Hermes cron jobs as Pipeline definitions —
  `meeting-builder.json` (Fetch Meetings → Resolve Meeting Folder → Build
  Attendees → Link to Thread) and `company-discovery.json` (Scan Threads
  + Scan Meetings for Domains → Filter Known Domains → Add to
  Entities.md — a real fork/merge shape, two parallel scans feeding one
  filter step). Generalized the map's splice mechanism from one
  hardcoded pipeline id to every real Pipeline (`GET /pipelines`,
  `fetchAllPipelineJobTrees`/`spliceAllPipelineJobTrees`) — adding a
  future pipeline is now just a new JSON file, no code change. Verified
  live: "6 sections · 13 agents mapped" (Primary + all 3 pipelines' real
  Step trees, fork/merge shape rendering correctly). See `ADR-005`.
- feat: built the "Hermes Operations" page (`/hermes`) — a read-only
  surface for Hermes' real cron job definitions/schedules (direct
  `cron/jobs.json` read, `hermes_cron.py`), server/gateway status (reused
  the existing `/hermes/status`), per-job run history
  (`cron/executions.db` via sqlite3), and each run's own linked detail: a
  clean per-run markdown report (`cron/output/<job_id>/<timestamp>.md`,
  matched by the run's real `finished_at`) plus the matching raw
  `agent.log` lines (matched by the run's real `started_at`, reconstructed
  into the same `[cron_<job_id>_<YYYYMMDD_HHMMSS>]` session tag Hermes
  itself writes). Also built a full, live two-way chat bridge to any real
  Hermes agent (`hermes_ws_client.py` + a new `/hermes/chat/{agent_id}`
  WebSocket proxy) — Hermes' embedded chat turned out to be a
  newline-delimited JSON-RPC-over-WebSocket protocol (`/api/ws`,
  `session.create` + `prompt.submit` + streaming `message.delta`/
  `message.complete` events, plus `approval.request`/`approval.respond`),
  not a REST call; the exact wire shape was confirmed by hand-driving a
  real session against the live gateway and getting a real model reply
  back before writing the FastAPI integration. Verified live end-to-end
  through the browser UI: cron job list/run history/report+log drill-down
  all render real data, and a chat message sent through the real page
  input got a real streamed reply back from Primary.
- fix: implemented the missing `POST /agents/{agent_id}/chat` endpoint —
  `AgentDetailPanel.tsx`'s own pre-existing per-agent "Chat" tab was
  calling it already, but it had never been built for Hermes-sourced
  agents, so every real agent's Chat tab silently failed ("Chat with Agent
  is not working"). Wired to the same `HermesChatSession` bridge as the
  new `/hermes` page (ADR-006) — no frontend changes needed. Verified live
  through the actual panel.
- refactor: dissolved the standalone `/hermes` page per operator direction
  ("build a top Page Tab to Navigate Different Sections of Health...one
  for App Status, one for Hermes Status" + "The Log of Corn Runs...should
  be instead of Crawlers"). System Health (`/system-health`) now has two
  top-level tabs (`.page-tabs`, a new generic page-tab style in
  `settings.css`) — "App Status" (the original content, unchanged) and
  "Hermes Status" (gateway/server status only). The cron job list + run
  history + linked report/log drill-down moved onto `CrawlersPage.tsx`
  (route `/crawlers` kept, since Crawlers' own original concept —
  Second-Brain-native background agents — has had zero real members since
  ADR-004 set every real Hermes agent `is_background_agent: false`;
  operator: "Just Call the Corn Jobs Crawlers and Bring the stuff here").
  Removed the standalone Chat widget from the old Hermes Operations page
  (operator: "Remove the chat with Agent at the bottom" — real per-agent
  chat already lives in each Agent Panel, fixed the same session) along
  with `hermes_router.py`'s now-unused `WEBSOCKET /hermes/chat/{agent_id}`
  proxy and the frontend's now-unused WS chat client functions.
- feat: Section Hubs are now clickable and have their own detail panel
  (`SectionDetailPanel.tsx`, Overview + Settings tabs — Name, Description,
  Icon, Color) — operator: "the Hub can be clicked and has its own
  Settings, Overview tab... Section Color and Icon, Description and
  Name." Wired into the ONE previously-dead click target this needed:
  `SectionDrilldown.tsx`'s own Hub render never passed `onActivate` (it
  stayed a plain non-interactive `<div>`, "matching today's behavior" per
  its own pre-existing comment) — now it does, opening the new panel,
  while the OVERVIEW Hub keeps its existing "zoom into this Section's
  drill-down" click meaning unchanged. `PATCH /sections/{id}` extended
  from name-only rename into a general update (icon/color/subtitle/
  description, same omitted-vs-empty-string convention as the agent
  Visual tab); `description` is a REAL backend field now — layoutAgents.ts
  had been typing it since 2026-08-15 ("will be used later") with nothing
  backing it. Reused `VisualPicker.tsx` verbatim for icon/color — its own
  comment had anticipated this exact call site ("once Hubs get their own
  settings surface"). Verified live: opened Data Gatherer's real panel,
  saved a real description, picked a real icon, watched the actual map
  Hub icon update in place with no reload, confirmed via a fresh
  `GET /sections`, then reset icon/color back to default via the same
  panel.
- fix: Agent Activity (`/agent-activity`) now shows Hermes' real session
  log — operator: "the Agents Activities Tab should get the Agents Log
  from Hermes." Its old Second-Brain-native "run_event/run_error" activity
  log was already silently dead: `agent_activity_router.py` had been
  removed from `app/api/` with nothing left importing it (the page's own
  `fetchAgentActivity()` call was 404ing), and its data source
  (`agent_registry.list_agents()`) has returned `[]` since agent
  orchestration moved to Hermes this session anyway — deleted the orphaned
  `app/business/agent_activity.py` and `features/agent-activity/client.ts`
  rather than repair a route with nothing real left behind it. Replaced
  with the already-live `/hermes/sessions` (now taking real `limit`/
  `offset` query params) — every genuine Hermes session, cron and
  interactive alike, agent name resolved via the existing agent list,
  source/status badges, title, message count, duration. Verified live: 50
  real sessions rendered correctly, including real WhatsApp conversations,
  cron runs, and CLI sessions.
- feat: each Agent's own Overview tab now shows its own recent real
  Hermes sessions — operator: "the Overview tab should show these Hermes
  sessions per agent too." `hermes_client.list_sessions()` gained a real
  `profile` filter param (confirmed live: an unfiltered call's own `total`
  dropped from 72 to 6 when scoped to `profile=opp-manager`, every
  returned row's own `profile` field matching) — threaded through
  `hermes_status.get_sessions()` and `GET /hermes/sessions?profile=`.
  `AgentDetailPanel.tsx`'s Overview tab passes `agentId` straight through
  as the profile (a real Agent's own id IS its real Hermes profile id) —
  no id-mapping needed. Verified live: Primary and opp-manager's panels
  each show their own distinct, correctly-scoped session list.
- fix: Agents Map/Section Hub connector lines had a real, confirmed bug —
  the Hub's own spoke line was drawn to each pipeline's ENTRY point (the
  root, e.g. "Fetch Emails") instead of its TERMINAL/producer stage (the
  one that actually writes to the vault) — operator: "Link to the Hub
  Should be The Nodes that Actually write to the Vault, I can See The
  nodes that Write to the Hub are the Farest from the Section Hub, Which
  is not Correct." The code had inverted the operator's own original
  2026-08-16 framing ("it should be the last one in the Tree") — fixed in
  both `AgentsMapCanvas.tsx` (overview) and `SectionDrilldown.tsx`
  (Section view) by filtering to agents with no outgoing dependency edge
  (nothing depends on them further) instead of no incoming one. This also
  fixed the reported "zigzag isn't clear, too many intersecting lines"
  complaint as a side effect — verified by writing a real geometric
  segment-intersection check (not eyeballing) against the live rendered
  SVG: the Data Gatherer section's own connector lines went from 5 real
  crossings (overview) / 6 (Section drilldown) to 0/0, since a spoke to
  the terminal stage is short (near the Hub) instead of spanning the
  entire depth range across other chains' territory.
- fix: a genuinely standalone agent (no `depends_on`, and nothing else
  depends on it — Primary, files-manager, notes-manager, opp-manager,
  none of which belong to any real pipeline) was landing at
  `AGENT_RADIUS_MAX`, the single farthest ring on the map — the exact
  same depth-0 branch a pipeline's own entry point uses, when a whole
  Section also contains real pipelines (their non-zero `maxDepth` pulls
  every depth-0 agent in the SAME section out to the outer edge) —
  operator: "the Agents that are solo, They are Far away from the Section
  Hub They need to be Closer." Fixed in `layoutAgents.ts`: a solo agent's
  radius is now a deterministic-per-id (same jitter-hash convention
  already used elsewhere, not `Math.random()`) random point 25%-50% of
  the way from the Hub out to where it would otherwise have landed.
  Verified live: Primary/opp-manager/etc. moved from radius ~56 to the
  computed [29.75, 38.5] band, each landing at a different point within
  it, connector-line crossing count unaffected (still 0).
- fix: closed two more real 404s on `AgentDetailPanel.tsx`, both cases of
  a frontend caller pointing at a backend route archived and never
  rebuilt against the Hermes mirror (same pattern as Chat/Agent Activity
  earlier this session). Settings tab's Provider row was an editable
  `<select>` populated by `GET /providers` (no providers router wired in
  `main.py`) whose own `onChange` (`PATCH /agents/{id}` with
  `provider_id`) would have silently no-opped anyway, since
  `AgentVisualUpdateBody` only ever reads `icon`/`color` — replaced with
  plain read-only text showing `agent.provider_name` (already real data,
  a Hermes agent's own `config.yaml` provider, ADR-004 point 3). History
  tab's `GET /agents/{agent_id}/history` never existed on the current
  router — added, returning `[]` always, matching `/jobs`'s own existing
  "never a 404, never fabricated" contract; the tab's pre-existing
  "Nothing recorded yet" empty state and the Overview tab's
  pending-approval scan (which depended on the same `history` fetch) both
  already degrade cleanly on an empty list, so no further UI changes were
  needed. Found two more, genuinely separate 404s of the same shape while
  investigating (`/agents/{id}/schedules` — the whole Schedule tab; the
  Settings page's own `/providers` CRUD, `ProvidersCard.tsx`) — flagged as
  a follow-up rather than fixed here, out of this fix's own scope.
- refactor: moved the per-agent real Hermes session log from the Overview
  tab to the History tab — operator: "The Hermes Sessions in Agent Should
  be in the History not in Overview." History's own pre-existing
  "Communication history" section (now honestly always-empty, see above)
  stays in place above it, in case a future fix restores real proposal
  data into it; limit raised 10 → 30 sessions now that this is the
  dedicated tab rather than an Overview preview.
- fix: the Vault Browser page (`/browse`) went blank ("Nothing indexed
  yet") after every backend restart — operator: "The Vault Browser page
  shows the wrong notes then when I refresh it is showing no notes."
  Root cause: `vault_indexing.py`'s own index is a plain module-level
  Python dict with zero disk persistence (ADR-024's own explicit,
  accepted tradeoff), silently wiped on every restart (a frequent event
  in dev — `--reload` included) with nothing left to rebuild it
  automatically once Hermes' own capture pipelines moved outside this
  backend process (2026-08-21 self-hosting rewrite removed the last
  in-process trigger). Fixed in `main.py`'s own lifespan: rebuilds
  eagerly on every start now, as a non-blocking background task
  (`asyncio.to_thread`, same "don't block application-startup-complete"
  pattern already used for the default-schedule dispatch). Verified
  live: restarted the backend with zero manual intervention, `GET
  /vault-search/status` came back `indexed: true` within 3s, `/browse`
  showed all 1,126 real notes immediately.
- bug: logged `BUG-036` — while verifying the fix above, found real,
  concrete evidence of a SEPARATE, genuine content bug this same page's
  default (unfiltered, stem-sorted) view surfaces first: several real
  Meeting-series and Person notes are filed under a raw Outlook internal
  identifier (`calendar_series_id` / LegacyExchangeDN) as their own
  filename, even though a real human-readable name (a meeting subject, a
  person's name) is already known and stored right in the same note's
  own frontmatter — this is almost certainly the "wrong notes" half of
  the operator's own report. Root cause lives in Hermes' own self-hosted
  capture skill scripts (outside this repo since the 2026-08-21
  rewrite), not in Second Brain's own read-only `vault_search.py`/
  `vault_indexing.py` (which are correctly reflecting real vault
  content) — logged rather than fixed here, per the operator's own
  separate "log them as bugs" direction this same session.
- fix: The Vault graph screen (`/vault`) only ever showed a small
  fraction of the real vault as nodes — operator: "the View Shows only
  like 20 Node while we have more than 1000 Nodes Something is wrong."
  Root cause, confirmed live by hooking `CanvasRenderingContext2D.arc()`
  (the per-node draw call) and inspecting real coordinates: the
  force-directed simulation (`forceLayout.ts`) is numerically unstable at
  the vault's real current scale (1,126 nodes / 6,032 edges — well past
  its original ~680-node design point, per its own docstring). A node
  caught in a dense, edge-less cluster (many same-kind notes with no
  wikilinks between them) can accumulate repulsion from hundreds of
  simultaneously-close neighbors in one tick; `VELOCITY_DAMPING` alone
  (a flat 15% shrink per tick) doesn't stop that compounding tick over
  tick, and positions diverge exponentially within a few dozen frames —
  measured directly at up to `1e+31`, thousands of orders of magnitude
  off-canvas. Of 1,126 real nodes, only 63 were still at sane coordinates
  by the time a viewer would actually look at the screen; the other
  1,063 were already permanently invisible, with no error and no
  automatic recovery. Fixed with a standard, targeted technique real
  force-layout libraries use for exactly this (e.g. d3-force's own
  velocity-decay + implicit speed clamp): cap each node's per-tick
  velocity magnitude (`MAX_VELOCITY`, `forceLayout.ts`), breaking the
  runaway feedback loop at its source without touching the tuned
  repulsion/spring constants. Verified live: same real 1,126-node graph,
  hooked the same way after the fix, ran the simulation for 8 real
  seconds — 1,126 of 1,126 nodes stayed at sane on-canvas coordinates,
  zero exploded.
- feat: three further Vault graph improvements, same session, operator-
  directed — "The Circle Size Should be Linked to the the Amount of
  links or Mentions for the file, The Lines are very Dense need to think
  about a solution, the more Dense Objects Move towards the Center."
  1. Circle radius now scales with each node's own real degree
     (incoming + outgoing wikilink count, computed client-side from the
     already-fetched edge list — no backend change) via
     `radiusForDegree()`, sqrt-scaled (`NODE_RADIUS_MIN`/`MAX`/
     `_DEGREE_SCALE`) so one extreme hub note doesn't dwarf the screen.
     Click hit-testing (`findNodeNear`) uses each node's own real drawn
     radius now too, not a flat constant.
  2. Density: edges render at a very low base opacity by default
     (`EDGE_ALPHA_BASE`, mirroring Obsidian's own graph view — the
     direct visual precedent for this screen), so dense areas read as a
     soft haze instead of solid clutter; hovering a node now brightens
     ONLY that node's own real edges (`EDGE_ALPHA_HIGHLIGHT`, thicker
     line) while dimming every other edge further
     (`EDGE_ALPHA_DIMMED`) — lets a viewer trace one note's real
     connections out of 6,032 edges on demand. `--graph-edge-color`
     (tokens.css) changed from a baked-in `rgba(..., 0.25)` to fully
     opaque — opacity is now controlled entirely by canvas
     `globalAlpha` in JS, not double-applied.
  3. Centering force (`forceLayout.ts`) is now degree-weighted
     (`DEGREE_CENTERING_FACTOR`, sqrt-scaled same as radius) — a
     heavily-linked hub note gets pulled toward the graph's center
     noticeably harder than a lightly-linked one, while a genuinely
     isolated (degree 0) note keeps the original, unmodified pull and
     drifts naturally outward under repulsion — hubs settle centrally,
     the periphery is real leaf/isolated notes.
  TypeScript typecheck (`tsc --noEmit`) passes clean; left live-browser
  verification to the operator this pass, per their own "let me verify,
  don't do validation yourself" direction.
- feat: four more Vault graph refinements after the operator's own live
  verification of the pass above — "The Nodes Hover Effect should Bring
  the node up front and have the name of the node visible, Nodes with
  more connections should be closer to the center, Nodes are Overlapping
  Massively, Lines on hover are very thick need to be more visually
  Appealing."
  1. Hovering a node now draws it LAST (strictly on top of any
     overlapping neighbor, regardless of paint order), with a thin ring
     around it and its real title drawn as a screen-space-constant-size
     label beside it (`HOVER_LABEL_FONT_PX`/`_OFFSET_PX`, divided by the
     current zoom scale at draw time, same convention as edge width).
  2. `DEGREE_CENTERING_FACTOR` raised 0.35 → 1.1 (`forceLayout.ts`) — the
     first pass was too weak; a hub's own local repulsion from its many
     close neighbors was competing with, not losing to, the centering
     pull.
  3. Added a real collision-resolution pass (`forceLayout.ts`) — a
     direct position correction (not another force) that runs
     unconditionally every tick and guarantees any two circles clear
     `COLLISION_PADDING` apart, using each node's own real drawn
     `radius` (now copied onto `SimulationNode` alongside `degree`).
     Plain inverse-square repulsion never guaranteed non-overlap,
     especially once circle size started varying per node (a large hub
     circle and a small leaf circle need more real separation than two
     equal small ones, which repulsion alone has no way to know).
  4. Highlighted edges softened `0.9`/`2px` → `0.55`/`1.25px`
     (`EDGE_ALPHA_HIGHLIGHT`/`EDGE_WIDTH_HIGHLIGHT`) — a true hub note
     can highlight hundreds of edges fanning from one point; near-opaque
     + double-width read as one solid wedge, not individually legible
     lines.
  TypeScript typecheck passes clean; left live-browser verification to
  the operator again, per their own standing direction this same
  session.
- feat: two more Vault graph refinements — operator: "The Nodes it self
  is very big leaving no Space for the lines to be Visible We need to
  have some room by Shrinking the nodes by 50% while Maintaining there
  Positions... Highlight the connected node with something like hover
  effect but different, think about it."
  1. `NODE_DRAW_SCALE = 0.5` applied only at the two circle-draw call
     sites — deliberately NOT a change to `simNode.radius` itself, which
     still governs collision spacing (`forceLayout.ts`) and click
     hit-testing (`findNodeNear`) unscaled. Shrinking the physics radius
     too would let collision resolution pack circles into the newly
     freed room, moving every node's real position — the opposite of
     "maintaining positions." Each circle now sits smaller inside the
     same personal-space bubble it already had, opening real visible
     gaps for edges.
  2. A hovered node's real neighbors (an edge actually connects them) now
     get their own third visual tier, distinct from both the resting
     state and the hovered node's own treatment: full opacity, a thin
     `--color-accent`-colored ring (deliberately not the same color as
     the hovered node's own text-colored ring, so the two tiers are never
     confusable), and their own title label — but only when the neighbor
     count is small enough to stay legible (`NEIGHBOR_LABEL_MAX_COUNT =
     25`; a true hub can have hundreds of real connections, and
     unconditionally labeling all of them would recreate the exact
     clutter this feature exists to cut through). Every OTHER node dims
     to `NORMAL_NODE_ALPHA_WHEN_HOVERING` while a hover is active, so the
     connected set reads as a lit island against a quiet background —
     the actual "who is this connected to" answer at a glance.
  TypeScript typecheck passes clean; live-browser verification left to
  the operator, per their own standing direction this session.
- fix: background edges weren't dimming at a comparable rate to
  background nodes while hovering — operator: "the not Hover [nodes] and
  the lines that are not connected are mixing... if you gonna Dim the
  nodes we need to dim the lines." `EDGE_ALPHA_DIMMED` dropped
  `0.02 → 0.006` — with most of the graph's 6,032 real edges not
  touching whichever node is hovered, thousands of still-somewhat-visible
  lines kept crossing behind the dimmed nodes, reading as one blended
  mass rather than a clearly quiet background. TypeScript typecheck
  passes clean; live-browser verification left to the operator.
- feat: clicking a Vault graph node (or a Browse & Search result) now
  shows the note's real markdown body, rendered as formatted HTML with
  working links — operator: "when I click on a node The Next View should
  be the MD file it self displayed in a nice HTML formatting with links
  to the Files and Tags etc." `GET /vault-search/notes/{stem}`
  (`vault_search.py::get_note_detail`) now includes real `body` text,
  read fresh from disk (same established pattern `search()` already
  used, ADR-026 — `vault_indexing.py`'s own index entries never cache
  body text). New `NoteBody.tsx`: real `[[wikilink]]`/`[[target|alias]]`
  syntax isn't standard CommonMark, so it's pre-processed into plain
  markdown link syntax before handing off to `react-markdown`
  (`ChatMessageText.tsx`'s own established zero-plugin, safe-by-omission
  convention — no `rehype-raw`, no `dangerouslySetInnerHTML`), resolved
  against the note's own already-backend-resolved `forward_links`
  (matched by STEM case-insensitively, the same key `vault_indexing.py`'s
  real wikilink resolution uses — never by title, which can legitimately
  differ). A target with no match is a real, honest dangling link,
  rendered as plain text, never fabricated. Internal links render via
  `react-router`'s `Link` (no full page reload); external links open in
  a new tab. Tag badges on the note detail page are now clickable too,
  navigating to `/browse?tag=X` (`VaultBrowserPage.tsx` now reads a
  `?tag=` query param on mount to pre-select the filter). New
  `.note-body` CSS block (`vault-browser.css`) reins heading sizes into
  the app's own existing type scale and styles links/code/blockquotes
  consistently with the rest of the UI. TypeScript typecheck and a
  Python compile check both pass clean; live-browser verification left
  to the operator, per their own standing direction this session.
- feat: created a new standalone Hermes agent, `azure-calculator` —
  operator: "I want to Create an Agent to be my Azure Calculator Helper
  ... it need to be simple and very smart, Ask the right Questions to
  get based on the Solution." Provisioned via `hermes profile create
  azure-calculator --clone` (own SOUL.md, config.yaml, `.env`), trimmed
  to a single real Skill (every cloned bundled skill moved aside into
  `_disabled-skills/`, matching the same narrow-mandate pattern already
  used for `opp-manager`/`notes-manager`/`files-manager`). New
  `pricing/azure-cost-calculator` Skill: `lookup_azure_price.py` queries
  Microsoft's own public Azure Retail Prices API
  (`prices.azure.com/api/retail/prices`, no API key needed) for real,
  current prices, with a convenience `estimated_monthly_cost` projection
  for hourly-billed rows. SOUL.md is written to hold a genuine
  back-and-forth conversation (ask what's missing — resource type,
  region, scale — before calculating; don't re-ask what's already been
  given) rather than the one-shot-relay shape `opp-manager` uses, since
  this agent needs real live dialogue to nail down what's actually being
  priced. Found and fixed a real bug while verifying against the live
  API: Azure's own `armSkuName` field is reliably populated for Virtual
  Machines but genuinely blank for Storage (whose real distinguishing
  name lives in `skuName`/`productName` instead) — a single-field
  `contains()` filter silently returned zero matches for every real
  Storage SKU; fixed by OR-ing the search across all three fields.
  Verified live end-to-end: real VM/Storage/PostgreSQL price lookups all
  return correct data with correct monthly-cost math, and the new agent
  is confirmed discoverable via Second Brain's own `GET /hermes/agents`
  (shows up on the Agents Map automatically, no Second Brain code
  changes needed — the map is a live mirror of every real Hermes
  profile).
- fix: `POST /agents/{agent_id}/chat` (`agents_router.py`) now surfaces a
  `clarify.request`/`approval.request` event as the turn's own reply
  instead of silently blocking for the full 180s and 504ing — found
  while verifying the new `azure-calculator` agent's real conversational
  behavior (it correctly tried to ask a clarifying question, but Second
  Brain's own chat endpoint had no handling for that event type at all).
  Confirmed the real wire shape directly against hermes-agent's own
  installed source (`tui_gateway/server.py::_block`/`_clarify_block`/
  `_emit_approval_request`): both event types carry a human-readable
  `question` (or batch `questions`)/`command` field plus the request's
  own `request_id`. This REST endpoint opens a fresh, single-turn
  `HermesChatSession` per call with nowhere to hold that `request_id`
  open across a follow-up HTTP request, so it surfaces the question/
  approval text verbatim as the reply rather than attempting
  `clarify.respond`/`approval.respond` — Hermes' own gateway already
  tolerates an unanswered clarify/approval past its own configured
  timeout (confirmed live: falls back to locked/default answers and the
  agent continues on its own, the same "(clarify timed out after 120s —
  locked answers returned)" behavior already observed in this session's
  one-shot CLI test).
- feat: real per-agent Agents Map Section placement — operator: "more the
  Azure Calculator to Technology Section, Bring the rest of the Corn Jobs
  even if they are competed to the Data Gathering, Move the Customer
  Extraction pipeline to Liberian Section" then "Opp Manager to Sales,
  and Notes and file Manager to Liberian." Previously every individual
  Hermes-mirrored agent (`agents_map_adapter.py`) landed in ONE hardcoded
  Section ("Data Gatherer") regardless of what it actually does — only
  Pipelines had their own real per-pipeline `section` field. Added
  `_AGENT_SECTION`, a real per-agent-id override (same shape as the
  existing `_AGENT_TYPE` map): `azure-calculator` → Technology,
  `opp-manager` → Sales, `notes-manager`/`files-manager` → Librarian. An
  agent id absent from the map (Primary/`default`) falls through to Data
  Gatherer by construction — the operator's own "bring the rest... to
  the Data Gathering" is true automatically, no separate entry needed.
  `list_agent_summaries`/`get_agent_detail` now resolve each agent's
  Section individually instead of computing one shared section_id for
  all of them. Confirmed "Customer Extraction pipeline" wasn't an exact
  registered name (only Company Discovery/Meeting Builder/Threads
  Builder exist) — asked the operator directly rather than guessing;
  confirmed as Company Discovery (scans Threads/Meetings for new company
  domains, files them to Entities.md for review), moved via its own
  `company-discovery.json`'s `section` field from Data Gatherer to
  Librarian. Meeting Builder/Threads Builder stay Data Gatherer,
  unchanged.
- fix: Section Hub icons not rendering in the Agents Map overview or the
  Section drill-down view (`SectionHub.tsx`) — reported live: "The Icons
  in the Section Hub is not Visible in both the Agent Map and Section
  view." Root cause: `SectionHub.tsx` rendered `section.icon` directly as
  the Material Symbols ligature name, but a Section's `icon` can be a
  VisualPicker `id` (e.g. `"compass"`) whose real ligature differs
  (`"explore"`) — the `liga` OpenType feature only substitutes a glyph
  for a real ligature name, so an id/ligature mismatch renders as the
  literal, barely-legible word instead of an icon. `AgentNode.tsx` had
  already hit and fixed this exact bug for Agent icons (2026-08-16,
  "icons still not visible on agents") via `getVisualIconName()`
  (`visualOptions.ts`) — `SectionHub.tsx` never got the same fix applied.
  Now resolves through the same helper. `SectionDrilldown.tsx` reuses
  `SectionHub` directly, so this one fix covers both reported locations.
  Verified live: the Industry Hub's icon text changed from the literal
  `"compass"` to the correct `"explore"` ligature in both the overview
  and its own drill-down, confirmed via direct DOM inspection (computed
  `textContent`) since Material Symbols glyphs aren't distinguishable
  from their name in a raw screenshot. TypeScript typecheck clean.
- fix: Section Hub icons visually clipped at the edges (`agents-map.css`,
  `.hub-node-icon`) — reported live, immediately after the ligature fix
  above: "the Icon Size is Clipped not visible fully." Root cause found
  by rasterizing the actual glyph to a canvas and reading back non-
  transparent pixel bounds (a screenshot can't distinguish "wrong glyph"
  from "right glyph, sliced" — both just look like a small illegible
  mark): Material Symbols Outlined's real ink for these glyphs is ~16x16
  px at the hub's 14px (0.875rem) font-size (its own font metrics —
  ascent 15 + descent 1 — sum to 16px), wider and taller than the plain
  14x14px box a bare `line-height: 1` box provides at that font-size.
  `.hub-node-icon`'s own `overflow: hidden` (added 2026-08-15 for a
  DIFFERENT, unrelated reason — stopping the icon from forcing
  `.hub-node`'s flex container into an oval) was silently slicing ~1-2px
  off every edge of that ink as a side effect. Fixed by giving the icon
  span an explicit `width`/`height: 1.3em` (~18.2px, comfortably bigger
  than the measured ~16x16 ink) with flex-centering — `overflow: hidden`
  on an element with an explicit size still resolves that element's own
  automatic minimum size to 0 (the same CSS mechanism the original
  circularity fix already relies on), so this couldn't reintroduce the
  oval bug; verified live both Hub geometries stayed exactly square
  (30.79x30.79 overview, 30.24x30.24 drill-down) before and after.
  Verified live in both the Agents Map overview and the Section
  drill-down (same shared `SectionHub` component): icon box grew from
  14x14 to a non-clipping 18.2x18.2 in both, hub circularity unaffected.
  TypeScript typecheck clean (CSS-only change).
- fix: Agent node icons on the main Agents Map overview still clipped
  after the Hub fix above — reported live: "The Map Main still have the
  icons clipped." `.agent-node-icon` (individual Agent circles, e.g.
  Primary/azure-calculator/opp-manager) had the exact same font-metrics-
  exceeds-box issue as the Hub icons — confirmed live via the same
  canvas ink-bounds technique: at this element's 6px font-size, most
  glyphs' ink fits a bare 6x6 box, but "hub" (Primary's own icon) paints
  ~8x6px, wider than the box. Applying the SAME `width`/`height: 1.3em` +
  flex-centering fix used for the Hub grew the box's WIDTH correctly
  (6→7.79px, live-measured) but its HEIGHT stayed stuck at 4.36px — a
  second, different cause found live: `.agent-node` is a COLUMN flex
  container with the icon plus TWO sibling text spans
  (`.agent-node-label`/`.agent-node-type`) sharing one ~7.7px-tall
  overview node; default `flex-shrink: 1` let the icon get squeezed on
  the shared vertical axis to make room for those siblings, even though
  live measurement showed both siblings already render at an unreadable
  ~1x1px at this same overview scale (nothing visible lost by
  shrinking them further). Added `flex-shrink: 0` to the icon so it
  keeps its full requested 7.79x7.79 box instead. Verified live: icon
  box now 7.79x7.79 (was 6x4.36) for every real glyph in use
  (hub/conveyor_belt/smart_toy/mail), `.agent-node` itself stayed
  exactly square (7.7x7.7) in the overview and (26.24x26.24) in the
  Technology section's own drill-down — the historical "Agents...
  Oval" regression this container's own `overflow: hidden` exists to
  prevent did not reappear in either view. TypeScript typecheck clean.
- fix: My Day's Emails/Calendar were silently reading a stale, abandoned
  data model — operator: "Now we go to my day, The API is Missing I
  know lets bring it back smarter." Confirmed live: `/my-day/emails`/
  `/my-day/calendar` returned real 200s (not 404s — the actual "missing"
  piece was Approvals, `/pending-approvals`, archived same as
  `BUG-034`/`BUG-035`'s sibling routers) but always empty, because
  `my_day.py` still pointed at `vault_writer.list_notes_in_kind_folder`:
  (1) a flat, non-recursive `glob("*.md")`, so it saw zero of the real
  dated Meeting occurrences (`Work/Meetings/<series>/occurrences/*.md`
  — only the undated series-container note, ADR-048 already fixed this
  exact "nested note kind" blind spot for `list_all_note_paths()`, just
  never propagated here); (2) pointed at `Work/Emails/`, a folder that
  no longer exists — email capture moved to the Threads Builder
  pipeline (2026-08-21) and this projection was never updated to
  follow. Rewired both functions onto `vault_indexing.get_index()`
  (the same already-correct, already-recursive index `vault_search.py`/
  the Vault Graph use), filtering `type == "Thread"`/`type == "Meeting"
  AND start present`. Added real resolution logic, not just a data-
  source swap: `_customer_name_by_tag()` resolves a `customer/<slug>`
  tag back to the real Customer/Partner hub note's own `name` field
  (never guessed by reversing the slug); `_latest_sender_by_conversation
  ()` gives a Thread (which has no single sender of its own) a
  best-effort "most recent real sender" for the UI's existing "from
  {sender}" display; `_meeting_series_lookup()`/`_series_folder_name_
  for()` inherit `customer` onto a dated occurrence from its own parent
  series note, since a real occurrence's own frontmatter carries no
  customer tag at all (confirmed live). Verified live end-to-end:
  17 real emails / 15 real meetings now surface for the current window,
  correctly classified (Core42/Adnoc/Masdar/DGE/Ewec) wherever the
  underlying capture data supports it, honestly `null` where it
  genuinely doesn't (e.g. a real internal meeting with no customer tag
  at all) — clicked through the actual UI (`/my-day/emails?day=
  2026-08-20`), confirmed real subjects/senders/timestamps render
  correctly. Found and logged, but did NOT attempt, a separate blocking
  gap while verifying the click-through: `BUG-037` (Cockpit 404s
  entirely, its own archived router needing a Hermes-chat rewiring on
  the scale of this session's `POST /agents/{id}/chat` rebuild — too
  large/risky to attempt unsupervised overnight).
- feat: created a new standalone Hermes agent, `daily-briefing` —
  operator: "let's bring it back smarter instead of just listing emails
  and meetings... Emails need to be more classified and if I missed
  something during the week bring it up," then, going to sleep: "Yeah
  agent, let's go with that I will go to sleep run this part
  autonomous." Built on top of the same-night `my_day.py` data-model fix
  above (this agent would have had nothing real to reason over
  otherwise). Provisioned via `hermes profile create daily-briefing
  --clone` (own SOUL.md, config.yaml, `.env`), same narrow-mandate
  pattern as `opp-manager`/`notes-manager`/`files-manager`/
  `azure-calculator` (every cloned bundled skill moved aside into
  `_disabled-skills/`). New `day-planning/daily-briefing` Skill, two
  scripts: `my_day_lookup.py` (calls Second Brain's own live `/my-day/*`
  API — summary/emails/calendar/todo, `--day` optional) and
  `note_detail.py` (calls the existing `/vault-search/notes/{stem}` for
  one note's full body, so the agent can check a specific Thread's own
  `## Actions` section for the "did I miss something" ask) — same "call
  the real API, never reimplement its logic" pattern `azure-cost-
  calculator` established. SOUL.md is explicitly, deliberately
  READ-ONLY: never writes to the vault, never fills in `## Actions`
  (a human-owned section, `section_ownership.py`), never takes an action
  — sidesteps the still-undecided Approval question entirely by design
  (operator: "The Approval is something we need to discuss I don't know
  how to handle this part yet"), rather than guessing at a flow the
  operator explicitly hasn't decided on. Verified live: both scripts
  return real, correct data against the actual running backend (17
  emails/15 meetings/82 todos for the current window; a real Thread's
  own empty `## Actions` section correctly surfaced via `note_detail.py`
  as a genuine "might need a look" signal); confirmed discoverable via
  `GET /hermes/agents` with exactly one skill, no Second Brain code
  changes needed (the map is a live mirror of every real Hermes
  profile). Left in the default "Data Gatherer" Section (no explicit
  placement instruction was given for this one, unlike the four agents
  moved earlier the same night) — same fallback every other unassigned
  individual Hermes agent gets.

  **Full live end-to-end verification** (real chat turn, `hermes -p
  daily-briefing chat -q "What's on my plate for August 20th, 2026?
  Give me a prioritized rundown."`, 2m26s / 44 tool calls): the agent
  correctly discovered its own Skill and scripts, called `summary`/
  `emails`/`calendar`/`todo` scoped to the real day, then went one level
  deeper via `note_detail.py` on the 4 threads it judged highest-impact
  (an urgent ADNOC RFP, a Compass ops alert, a GPU-demand COB deadline,
  a Masdar onboarding thread) — all 4 genuinely had an empty `## Actions`
  section, which the agent correctly cited as its own real "unresolved"
  signal rather than a vague guess. Produced a genuinely prioritized
  briefing (critical/time-sensitive/customer-impacting tiers, a meeting-
  prep note, emails triaged high→FYI, tasks pulled forward from the real
  82 open, suggested focus blocks) and explicitly flagged its own
  inference where the data was incomplete ("Customer: not set in the
  note (inference: likely external with Invest Bank based on the
  title)") rather than presenting a guess as fact. Took no write action
  of any kind — exactly the read-only/surfacing-only design this build
  was scoped to.
- feat: new top-level Chat page for talking to Primary directly —
  operator: "move the Primary Chat to be Background Agent, Create a new
  Tab we call Chat where we can Chat with this Agent Since it Talks to
  everything." Primary (`default`) is now excluded from the Agents Map
  ring entirely (`agents_map_adapter.py`'s new `_BACKGROUND_AGENTS`
  override, same `is_background_agent: true` mechanism already
  established for the other specialists — deliberately this time, not
  the earlier accidental exclusion), since the new Chat page is now its
  real, primary way to be reached. Extracted the chat UI out of
  `AgentDetailPanel.tsx`'s own inline Chat tab into a new, genuinely
  reusable `AgentChatPanel.tsx` (`features/chat/`) — same exact
  behavior, just no longer duplicated: the side panel's own Chat tab and
  the new standalone `/chat` route both render this one component now,
  parameterized by `agentId`/`agentName`. New `ChatPage.tsx` route +
  Sidebar nav entry. Verified live end-to-end: sent a real message to
  Primary through the new page and got a real reply; reopened
  azure-calculator's own Chat tab in the side panel afterward to confirm
  the extraction didn't regress the embedded case (panel renders, thread
  fills the panel's own height correctly).
- fix: chat's file-attach control was a raw, plain `<input type="file">`
  — operator: "We need the Upload file Button in Chat to be an Icon to
  look better." The real file input stays in the DOM (real picker
  behavior, its own accessible label) but is now visually hidden; a new
  `.chat-attach-btn` icon button (Material Symbols `attach_file`, same
  icon system already used across the Agents Map) proxies a click onto
  it. Verified live: button renders 36x36px with an 18x18px icon glyph
  (comfortably inside the box, no repeat of the earlier Section Hub
  icon-clipping bug), and a real click correctly triggers the hidden
  input's own click event. Applies everywhere `AgentChatPanel` is used
  (the new Chat page and every agent's own side-panel Chat tab), since
  it's the same one component now.
- feat: chat images/links, real ADR-050 follow-through — operator
  (after asking Primary to generate a picture): "it generated it but It
  showed a link, [1] The Link is not clickable [2] The Image should be
  displayed in the chat clicking on it open it in a pop [3] This goes to
  all chats." Root cause: `ChatMessageText.tsx` used zero remark/rehype
  plugins (ADR-050's own deliberate original choice), and CommonMark's
  base spec does NOT autolink a bare URL — a bare-URL reply (the shape
  a generated-image link actually comes back as, not markdown link
  syntax) rendered as inert plain text. ADR-050 itself named this exact
  gap up front as "a cheap, additive follow-on if a future story needs
  it" — added `remark-gfm` (GFM's autolink-literals) now that one does,
  with ADR-050's own safe-by-omission posture fully intact (still zero
  raw-HTML plugins, no `rehype-raw`, no `dangerouslySetInnerHTML`; GFM
  only changes markdown parsing, never HTML handling). New: any link OR
  markdown image whose URL matches a real image extension
  (png/jpg/jpeg/gif/webp/svg/avif, optional query string for a real
  SAS-token/cache-busting URL) renders INLINE as an actual clickable
  thumbnail instead of link text — covers the real case (a bare/plain
  image URL) as well as proper `![alt](url)` markdown image syntax.
  Clicking a thumbnail opens a real full-viewport lightbox (backdrop
  click or Escape to close, Escape wired at `document` level so it
  works regardless of what currently has focus). Since `ChatMessageText`
  is the one shared component every real chat surface already renders
  through (ADR-050 Decision 3, and this session's own new
  `AgentChatPanel` extraction), this one fix covers the Chat page, every
  agent's own side-panel Chat tab, and both Cockpits at once — directly
  satisfying "this goes to all chats." Verified live end-to-end: asked
  Primary to echo back a real bare image URL, confirmed it rendered as
  an actual loaded thumbnail (not text, not a bare link) in both the
  user's own echoed bubble and Primary's reply, clicked it into the
  lightbox (confirmed via `getBoundingClientRect` — full 1400x900,
  top:0/left:0 — the screenshot tool's own capture scale made it look
  cropped, not a real bug), and confirmed both close paths (backdrop
  click, Escape) work. TypeScript typecheck clean.
- feat/fix: Vault note detail page — operator: "The md file viewer looks
  bad very bad Structure and looks like it was Dumped inside the Page
  uncleaned, Images are not shown (EGA file if the only file with Decent
  Content use it as a Sample to Fix) I need this Page to be Beautiful
  and readable with Jumps to section." Used the real
  `EGA_Updated_HLD_17Mar23_MASTER_DECK` File note (112-slide HLD summary
  with real `## Summary`/`## Details` sections, a long nested bullet
  breakdown, and three `![[slide-N.png]]` Obsidian image embeds) as the
  actual reference case throughout, per the operator's own instruction.
  - **Images now render.** Root cause: this codebase had NO backend
    route to serve a raw vault asset at all — `![[slide-14.png]]` isn't
    standard CommonMark, and even resolved, there was nowhere to fetch
    the bytes from. New `GET /vault-search/notes/{stem}/assets/{filename}`
    (`vault_search.py::resolve_asset_path`) serves a note's own real,
    co-located sibling file (confirmed live: capture writes an image
    into the SAME folder as its own `.md`), with real path-containment
    validation (never serves outside that one folder). `NoteBody.tsx`
    now resolves `![[filename]]` embeds to real `![alt](url)` markdown
    image syntax BEFORE handing text to `react-markdown`, processed
    strictly before plain `[[wikilink]]` resolution (the embed syntax
    contains the wikilink syntax as a literal substring). Verified live:
    all 3 real slide images (1280px each) load and render.
  - **Jump-to-section.** New `tableOfContents.ts` (shared by `NoteBody`
    and `NoteDetailPage`) + `rehype-slug` assign every heading a real
    id and render a sticky ToC rail alongside the note's own body
    (`.note-detail-layout`, collapses to one column under 960px). First
    attempt hand-rolled the id/counter logic and shipped a real bug,
    caught by live testing: a plain counter mutated during React's own
    render desynced under StrictMode's double-invoked renders (Summary
    got `id="details"`, Details got no id at all) — switched to
    `rehype-slug`/`github-slugger` (a pure AST transform, not a
    render-time side effect) for the actual id assignment, with
    `tableOfContents.ts` using the same underlying library so the two
    independently-computed id sets can never disagree. Verified live
    post-fix: correct ids, correct jump (`.main`/`html` both get
    `scroll-behavior: smooth` — confirmed live which element actually
    scrolls varies by page).
  - **Visual structure.** h2 now gets a bottom rule + real top spacing
    (chapters read as chapters, not a wall of text); nested lists get
    real vertical rhythm; images are capped/centered/bordered so a
    1500px+ slide screenshot doesn't dominate the page, with the
    following caption paragraph styled distinctly via `:has()`.
  - **Real bug found and fixed while styling this:** `--space-5` does
    not exist anywhere in `tokens.css` (the scale jumps `--space-4` →
    `--space-6`) — every `var(--space-5)` in the new CSS silently
    resolved to nothing (an undefined custom property makes the whole
    declaration invalid, falling back to the property's own initial
    value), so list `padding-left` computed to a real `0px` despite the
    rule being present and matched — reported live: "The Bullet Points
    appear before the title should have been pushed inside a bit."
    Fixed to `--space-6` (24px) everywhere in the new CSS, and swept
    the WHOLE frontend for the same already-broken pattern: found two
    more real, pre-existing instances in `agents-map.css`
    (`.map-search-input`/`.map-search-empty`, both silently losing
    their entire `padding` shorthand the same way, unrelated to this
    task but the same class of bug, fixed in the same pass rather than
    left known-broken). Verified live: list items now sit a real 24px
    right of their own heading.
  - Also fixed while in this same code: a real Thread/Meeting note that
    genuinely wikilinks the same target twice (e.g. `[[Microsoft]]`
    mentioned in both `## Summary` and `## Details`) listed it TWICE
    under "Forward links" — `_resolve_forward_links` now dedupes by
    resolved stem. TypeScript typecheck + backend compile-check clean.
- fix: three real chat problems in one pass -- operator: "The Context
  disappear every Message no Memory... it didn't know how to show it as
  a picture... The Bullets Structure is missed up... in the Chat and in
  what's app."
  - **Real session continuity.** Root cause confirmed by reading the
    code directly: `POST /agents/{id}/chat` opened a BRAND NEW
    `HermesChatSession` (a genuinely fresh `session.create`, no prior
    `session_id`) on every single call and closed it in `finally` -- so
    Hermes' own gateway, which DOES carry real multi-turn history
    forward keyed by `session_id` (the same mechanism an interactive CLI
    session already relies on), had no way to know two consecutive
    messages were even the same conversation. New
    `app/business/hermes/chat_sessions.py` keeps one live session open
    PER AGENT across requests (a per-agent `asyncio.Lock` serializes
    concurrent turns against it), only replaced when confirmed dead.
    New `POST /agents/{id}/chat/reset` (+ a "New chat" button,
    `AgentChatPanel.tsx`) explicitly ends a conversation on request --
    the only way to make an agent pick up a changed SOUL.md
    mid-conversation too (MEMORY.md's own "session prompt injected once,
    never re-read" constraint). Verified live end-to-end at the network
    level across two genuinely separate HTTP requests: told Primary "my
    favorite number is 42" in one call, asked "what is my favorite
    number" in a completely separate call minutes later -- got back
    "42.". Confirmed the reset endpoint itself works correctly too (a
    real, different session_id before vs. after, verified via a direct
    Python script) -- a *separate*, expected finding along the way:
    Primary still recalled "42" even after a genuine session reset,
    because it had used its own long-term memory tool (it was
    explicitly told "just remember it"), a real feature independent of
    Hermes' own session-scoped conversation continuity -- not a bug in
    the reset.
  - **Real images in chat.** Root cause: Primary reads the vault
    directly (real filesystem tools) and could describe an image's
    existence, but had no way to actually SHOW one -- it didn't know
    Second Brain's own new asset-serving convention (added earlier this
    session) at all. SOUL.md now teaches it both real mechanisms: a
    markdown image link built from the note's own real stem + the
    image's own real filename, pointed at
    `http://127.0.0.1:8001/vault-search/notes/{stem}/assets/{filename}`,
    for this chat's own UI (renders as a real inline image,
    ChatMessageText.tsx's own earlier fix); the real
    `send_message(..., message="... MEDIA:<real local path>")`
    attachment convention for WhatsApp specifically, since a
    `127.0.0.1` URL is meaningless off this machine -- confirmed the
    real mechanism by reading send_message_tool.py's own source
    directly rather than guessing. Verified live end-to-end (reset the
    session first so the SOUL.md change actually took effect -- session
    prompts are injected once, per the constraint above): asked Primary
    "tell me what we know about EGA Architecture, and show me the
    target architecture picture" -- it replied with a real, correctly
    structured summary AND a genuinely loaded 1280px inline image
    (confirmed via naturalWidth/complete), clickable into the same
    lightbox built earlier this session.
  - **Well-structured replies.** Root cause in agent-panel.css:
    `.chat-message` still had `white-space: pre-wrap` -- a leftover from
    BEFORE ADR-050 added real markdown rendering, preserving every
    literal newline in the raw source text on TOP of react-markdown's
    own block-level `<p>`/`<li>` spacing, doubling it; `.chat-message`
    also never styled its own `p`/`ul`/`ol`/`li`/`code`/`pre` output at
    all (bare browser defaults). Removed the stale rule, added the same
    real spacing/list treatment `.note-body` got earlier this session
    (tuned tighter for a narrow bubble). Also added WhatsApp-aware
    guidance to SOUL.md itself (flat lists, one level of nesting at
    most, no markdown headers/tables -- WhatsApp's own renderer doesn't
    support them, `##` just shows as literal characters) since that
    surface can't be fixed with CSS at all. TypeScript typecheck +
    backend compile-check clean; WhatsApp's own rendering not
    independently verified (no live WhatsApp access in this session) --
    the guidance is real and correct per Hermes' own documented
    formatting limits, but flagged here as unverified on that one
    specific surface.
- feat: built the Compass Expert agent family -- operator: "I need to
  build Compass Expert (Since I am Selling it)... He Can talk to
  Multiple Agents Compass Pricing Expert... Compass Solutions... Compass
  Models Expert... How can we build that in Vault, Hermes and Agentic
  Map." A real design discussion preceded the build (relay pattern,
  KB source/refresh cadence, whether the dependency-tree view was
  already free) -- see MEMORY.md for the resolved decisions.
  - **Vault:** `Work/Technology/Compass/` -- a new top-level Technology
    domain (not a flat `Work/Compass/`, corrected live: "technology
    should be a full section... that has Compass under it," leaving
    room for a future technology beyond Compass without restructuring),
    with `Pricing/`/`General/`/`Solutions/`/`Models/` sub-areas, each
    holding real per-topic notes (corrected live: "we might have
    multiple files... it will be massive," not one file per area) plus
    a real `Compass.md` hub note. Models is deliberately ONE list note,
    not a folder of deep files (operator: "its not compass Technology
    its External Models Compass Exposes"), structured so a specific
    model can be promoted to its own note later without restructuring.
    Every doc carries both a real tag (`technology/compass`,
    `compass/<area>`) AND a `[[Compass]]` wikilink back to the hub --
    the same dual pattern already used everywhere else in this vault
    (operator: "We need to be able to support tagging").
  - **Hermes:** 4 new profiles (`compass-expert`,
    `compass-pricing-expert`, `compass-solutions`,
    `compass-models-expert`), same narrow-mandate clone pattern as
    every other specialist this session. `compass-expert` is Primary's
    new relay target (added to `SOUL.md`'s own specialist list) AND
    itself relays to its own 3 specialists the same way Primary relays
    to opp-manager -- a genuine two-level chain, confirmed live end-to-
    end (`hermes -p compass-expert chat -q "..."` correctly relayed to
    `compass-pricing-expert` and reported its reply back). The 3 subs
    never write to the vault or reach WhatsApp directly (operator: "We
    will not Expose all to Whats app") -- `compass-expert` is the SOLE
    real KB writer, via a new `compass-kb-writer` Skill
    (`write_compass_doc.py`, modeled directly on `notes-manager`'s own
    `capture_note.py`) -- verified live with a real write + read-back,
    correct frontmatter/tags/wikilink, then removed (scratch
    verification only). A real recurring cron job
    (`compass-kb-refresh`, `hermes -p compass-expert cron create
    "every 20160m" ...` -- 2 weeks, operator's own real cadence)
    researches Pricing/General/Models via Hermes' own native
    `web_search`/`web_extract` (no new engineering needed there) and
    writes updates through the same script; `compass-expert`'s own
    SOUL.md also covers the manual path (Mahmoud handing it a document/
    tidbit any time, same write mechanism). Gateway isn't running in
    this dev environment, so the cron job won't fire on its own here --
    flagged, not a bug in the registration (confirmed correct: "every
    20160m", not the mis-typed "once in 20160m" a bare `"20160m"`
    schedule string produces without the `every` prefix).
  - **Agents Map:** real discovery while investigating -- the
    depends_on TREE-RENDERING mechanism already existed and was fully
    generic (`layoutAgents.ts`'s own `computeAgentDepth`/
    `assignTreeAngles`/`buildDependencyEdges`, reading `agent.
    depends_on` directly, never Pipeline-specific despite the earlier
    MEMORY.md note suggesting otherwise) -- the ONLY gap was
    `agents_map_adapter.py` hardcoding `depends_on: []` for every real
    Hermes agent. New `_AGENT_DEPENDS_ON` override (same shape as the
    existing `_AGENT_TYPE`/`_AGENT_SECTION` maps) wires the 3
    specialists' own real `depends_on: ["compass-expert"]`. All 4 land
    in Technology (`_AGENT_SECTION`). Verified live: a real, visually
    connected tree renders on the map -- Technology Hub -> azure-
    calculator (separate) and Technology Hub -> compass-expert ->
    its 3 real sub-agents, confirmed via a live screenshot showing the
    actual connecting lines, not just the data being correct.

  **Full relay chain verified live end-to-end** (real `hermes -p
  compass-expert chat -q "What's Compass pricing like?..."`, 3m40s):
  compass-expert correctly relayed to `compass-pricing-expert` via the
  real one-shot mechanism (`hermes -p compass-pricing-expert chat -q
  "..." -Q --create-if-missing -c "compass-pricing-qa"`), which honestly
  checked the (currently empty) Pricing folder and reported that
  plainly rather than fabricating pricing data -- compass-expert then
  synthesized the reply back in its own words and proactively offered
  two real next steps (get official docs added, or research from the
  official Compass/Core42 source). Confirms the two-level relay chain,
  the "never fabricate" discipline, and the "subs report findings back
  rather than acting on them" design all work exactly as specified.
- feat: made the Compass KB refresh actually smart, not just a vague
  "go research and write" instruction -- operator: "we need it to be
  Smart what info to bring what info to skip and how to classify it,"
  then handed the real source: https://www.core42.ai/compass/
  documentation. Fetched it live rather than guessing -- confirmed its
  own real section taxonomy (Get Started, Model Pricing, Model
  Capabilities, How-To's, API Reference, Agents, Chat Enterprise, FAQs,
  Changelog). Added a real "Keeping the KB current" section to
  `compass-expert`'s own SOUL.md: a concrete docs-section -> KB-area
  mapping table (Model Pricing -> Pricing/, Get Started/How-To's/FAQs
  -> General/ as SEPARATE topic notes, API Reference skipped by default
  as pure developer-integration detail, Changelog used to decide what
  to re-check rather than written as its own note, and an explicit
  confirmation that no real "Solutions" section exists in the official
  docs at all -- that area stays empty from automated research by
  design, only a real hand-described pattern from Mahmoud goes there);
  real keep/skip criteria (concrete facts vs. marketing language/
  duplicate content/page furniture/pure API-reference minutiae); and an
  explicit "check for an existing same-topic note before writing" rule
  so a refresh updates in place rather than fragmenting into near-
  duplicate notes. Re-registered the cron job with a tightened prompt
  pointing at the real URL and this new SOUL.md section by name, rather
  than the original generic instruction. Verified live with a scoped
  real test (research just Model Pricing, write one real note) before
  trusting the full recurring job to it.

### 2026-08-24

- fix: Outlook capture never pulled Sent Mail into Threads (operator:
  "We didn't pull the outbox to the threads (I guess its a must)") --
  `email-thread-capture/scripts/outlook_lib.py`'s own `list_recent_mail`
  only ever queried the Inbox folder, so a Thread's own history only
  ever showed the received half of a real conversation, never Mahmoud's
  own replies/forwards. Extracted the existing restrict/iterate/filter
  logic into a new `_list_folder_mail(folder, ...)`, called once for
  Inbox and once for the newly added Sent Mail folder (`_OL_FOLDER_
  SENT_MAIL = 5`), merged and re-sorted by `received`, then trimmed to
  the real `limit` -- confirmed live that `ReceivedTime` is populated on
  a real Sent Item too (no conditional SentOn/ReceivedTime branching
  needed) and that a Sent Item's own `SenderEmailAddress` resolves via
  the same existing EX-type `GetExchangeUser()` path, reused unchanged.
  Verifying this surfaced a separate, real, pre-existing crash --
  `UnicodeEncodeError` on a genuine U+202F character in a real email --
  fixed with `sys.stdout.reconfigure(encoding="utf-8")` in
  `list_recent_emails.py`, plus explicit `encoding="utf-8"` on both
  orchestrators' own `subprocess.run()` calls (`run_delta_capture.py`,
  `run_full_capture.py`) so the parent side decodes the child's own
  UTF-8 output correctly too.
- fix: `BUG-036`/`BUG-038` -- Meeting-series/Person notes filed under a
  raw Outlook internal identifier instead of their real name, which
  turned out to also mean 7 recurring series and 17 one-time meetings
  each existed as a full DUPLICATE note (operator, same message: "I can
  See some meetings are pulled but their titles hasn't been updated").
  Root causes fixed in `meeting-capture/scripts/vault_lib.py` (and the
  identical, hand-kept-in-sync copy in `email-thread-capture/scripts/
  vault_lib.py`): (1) a LegacyExchangeDN returned by a failed
  `GetExchangeUser()` GAL lookup was trusted at face value as a real
  email address -- new `_looks_like_real_email()` guard falls back to a
  name-based dedup key/filename instead, and never writes the raw DN
  into a Person note's own `email` frontmatter field; (2) no self-
  healing rename existed for a Meeting series once its own concept
  folder was created under a raw id, so the dedup scan kept topping up
  the same badly-named folder forever -- new `rename_meeting_series_
  if_needed()` mirrors `rename_thread.py`'s already-proven pattern
  (collision-safe hash-suffix fallback included), called on every
  `ingest_meeting.py` run. Live-testing the rename fix against the real
  vault surfaced the duplicate-note issue itself (`BUG-038`): the old
  pre-`2026-08-21` flat one-time-meeting file shape is structurally
  invisible to the current dedup scan (`list_meeting_concept_notes`
  only globs folder-shaped notes), so a post-rewrite capture pass
  always created a second, correctly-shaped note alongside the old one
  rather than finding and topping it up. Operator chose to archive
  (never delete) the raw-ID/stray-file side of each pair rather than a
  full content merge -- all 24 real instances (7 series folders, 17 flat
  files, 1 broken-DN Person note) moved intact to `_Archived Duplicates
  (2026-08-24)/` subfolders under `Work/Meetings/` and `Work/People/`,
  leaving the correctly-named/foldered copy as the sole live note.
  Also applied the same `encoding="utf-8"` fix found in the email
  scripts to `meeting-capture/scripts/list_recent_meetings.py` and
  `run_full_meeting_capture.py`'s own `run_script()` -- same latent
  crash risk, not yet triggered live, fixed proactively for
  consistency.
- fix (follow-up, same day): reverted the `rename_meeting_series_if_
  needed()` auto-call from `ingest_meeting.py` after live verification
  repeatedly recreated hash-suffixed duplicate folders (e.g. "Weekly
  Forecast l Strategic Clients-6e2f3e06") on runs that should have been
  clean no-ops -- root cause not conclusively pinned down (this vault
  path isn't under OneDrive and isn't itself a git repo, ruling out the
  two most obvious external-restore explanations; something is still
  re-materializing an old raw-id folder between runs). The function
  itself tested correct in isolation and is collision-safe (never
  overwrites), so it's left defined in `vault_lib.py` for manual/on-
  demand use, just not wired into the automatic capture path until the
  real cause is confirmed. `ingest_meeting.py`'s recurring branch is
  back to its original plain resolve-or-create. Every duplicate this
  produced during testing was archived (never deleted) alongside
  `BUG-038`'s own cleanup. `BUG-036` reopened to `Open` (Person-note
  half stays fixed; Meeting-series self-heal is not live) to reflect
  this honestly rather than leave it marked Closed.
- fix: `BUG-039` -- Agents Map's Technology drilldown never drew a line
  from `compass-expert` down to `compass-solutions`, even though its
  real `depends_on` was already correct (confirmed live via `GET
  /agents`). Root cause: `layoutAgents.ts`'s own `MAX_OUTGOING_
  CONNECTIONS = 2` cap, a real 2026-08-15 decision scoped to pipeline
  Job fan-out, silently also capped an individual AGENT's own outgoing
  edges -- `compass-expert` is the first agent with 3 real dependents.
  Raised the cap to 3 (real pipeline Jobs never exceed 2 by the cap's
  own documented data-model constraint, so their rendering is
  unaffected). Verified live: re-read the drilldown's own SVG line/node
  coordinates before and after, confirmed the third edge now renders,
  screenshot taken.
- feat: built the Azure Expert agent family (operator: "We will build now
  Azure Expert Agent, He will have many Agents under it") -- the second
  real "one domain, one Hermes profile" specialist family, one level
  DEEPER than Compass Expert's own two-level chain: `azure-expert` (new
  profile, Primary's own new relay target, sole real owner of
  `Work/Technology/Azure/` writes) relays to `azure-services-expert` (new
  -- Azure's real service catalog, categorized `Services/<Category>/`
  short notes with a live Microsoft Learn link, `web_search`/
  `web_extract` for anything not covered locally) and
  `azure-enterprise-architect` (new -- Landing Zone/Enterprise-Scale
  reference architecture, and itself relays further to `azure-data-
  architect`/`azure-infra-architect`, both new -- data platform and
  infra/compute/network reference architectures respectively). `azure-
  calculator` moved from independently, directly reachable to a plain
  relay-only specialist under `azure-expert`, the same reachability shape
  `compass-pricing-expert` already has under `compass-expert` (SOUL.md
  rewritten accordingly; no longer directly reachable by Mahmoud/Primary).
  New `azure-kb-writer` Skill (`write_azure_doc.py`, adapted from
  `compass-kb-writer`) handles the two real structural differences from
  Compass's own writer: a required `category` for Services, and
  Architecture split into 3 separate real areas rather than one. New hub
  note `Work/Technology/Azure/Azure.md` carries real substantive content
  directly in 3 named sections (What is Azure / Sovereignty in Azure / How
  to start an Enterprise company in Azure) -- a deliberate difference from
  Compass.md's own structure-only hub, per the operator's own explicit
  ask; placeholder text until azure-expert's own first live research pass
  fills them in (never fabricated by hand). Wired
  `agents_map_adapter.py`'s `_AGENT_SECTION`/`_AGENT_DEPENDS_ON` for all 6
  new/moved agents (all Technology, matching the real 3-level relay
  chain), and swapped Primary's own SOUL.md relay-list entry from a
  nonexistent direct `azure-calculator` route to a new `azure-expert`
  entry mirroring `compass-expert`'s own. Verified live: fetched `GET
  /agents` directly and re-derived the drilldown's own SVG line endpoints
  against each node's real on-screen position, confirming all 8 real
  dependency edges render (including hitting `MAX_OUTGOING_CONNECTIONS`
  right at its newly-raised limit of 3 for `azure-expert` itself, without
  tripping `BUG-039` again), screenshot taken.
- feat: `type: "expert"` -- operator: "We need to change the type of
  Agents that Are Experts to be Experts instead of Workers as well".
  `AgentType`'s own `'expert'` value, and a real amount of dedicated
  frontend UI for it (`AgentDetailPanel`'s own "Knowledge gaps" tab,
  `CreateAgentWizardModal`'s own Expert-creation flow), had been built
  ahead of any real data ever using it (module docstring's own "no
  Experts Yet" note, 2026-08-22). Flipped `_AGENT_TYPE` for every real
  domain-knowledge specialist in both families -- `compass-expert` and
  its 3 specialists, `azure-expert` and its 5 (including `azure-
  calculator`) -- from the default `worker` to `expert`; `opp-manager`/
  `notes-manager`/`files-manager` deliberately untouched (pipeline-style
  capture/action agents, a different real category). Verified live: the
  Agents Map now shows a real `expert` badge and a working "Knowledge
  gaps" tab on `azure-expert`'s own detail panel.
- **Found + worked around, not a code fix**: the backend's own `uvicorn
  --reload` did not reliably pick up 3 consecutive edits to
  `agents_map_adapter.py` in this same session -- `GET /agents` kept
  returning pre-edit data for several minutes across multiple confirmed
  "WatchFiles detected changes... Reloading..." log lines, verified both
  through the browser AND a direct `curl` (ruling out a browser-side
  cache). A full `preview_stop`/`preview_start` cycle (a genuinely fresh
  process, not a reload) picked up every accumulated edit correctly on
  the first try. See MEMORY.md's own new entry -- worth a clean restart
  before spending more time debugging "my Python change isn't showing up"
  against this dev setup specifically.
