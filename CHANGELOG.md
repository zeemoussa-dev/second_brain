# CHANGELOG

All notable changes to Second Brain.

<!-- Format:
## YYYY-MM-DD — Sprint NNN / task description
- feat: what was added
- fix: what was fixed
- refactor: what was restructured
- docs: documentation changes
-->

## [Unreleased]

## 2026-08-13 — SPRINT-028 — REQ-SB-09-US-01 (To-Do Task Capture Pipeline)

- feat: **`src/backend/app/data_access/outlook_com.py` (additive)** —
  `list_outlook_tasks(limit=100)`, this codebase's first Outlook
  Tasks-folder read (`GetDefaultFolder(13)`, no date-window params),
  plus `_map_task_status`/`_normalize_task_due_date` helpers. Live-COM
  correction: the real "no due date" sentinel on this installation reads
  as `"4501-01-01 00:00:00+00:00"`, not the originally-guessed
  `"1/1/4501"` — corrected before verification.
- feat: **`src/backend/app/data_access/vault_writer.py` (additive)** —
  `upsert_frontmatter_key` (the codebase's first genuine upsert-not-
  insert-only-if-missing baseline primitive), the Task-note
  create/top-up primitives (`create_task_note_baseline`,
  `ensure_task_note_baseline_frontmatter`, `build_task_tags`,
  `task_note_filename_stem`, `task_note_path_for_stem`,
  `task_note_exists_for_stem`), and the load-bearing
  `.second-brain/task_note_index.json` dedup/top-up lookup index
  (`load_task_note_index`/`lookup_task_note_stem`/`record_task_note`).
- feat: **`src/backend/app/data_access/compass_client.py` (additive)** —
  `classify_task`, a customer-only sibling to `classify_email` (no
  `kind` axis, no sender).
- feat: **`src/backend/app/business/todo_classification.py` (new)** —
  `classify_recent_todos`: fetch Outlook Tasks → classify by customer
  (Compass) → write/top-up via the EntryID-keyed dedup index → link the
  matched customer hub after a confirmed match only.
- feat: **`src/backend/app/business/email_classification.py`** — third
  gated `todo_mode` block in `run_capture_and_record_completion`
  (Autonomous/Supervised/Manual, its own independent `try/except` and
  `todo_capture_failed` boolean extending the trailing completion gate),
  a new `"todo-capture"` branch in `run_capture_for_agent`. Zero changes
  to `app/scheduling/capture_scheduler.py`.
- feat: **`src/backend/app/business/agent_registry.py`** —
  `"todo-capture"`'s "Task source" setting resolved to `"Outlook Tasks
  folder"` (was a placeholder pending this story).
- feat: **`src/backend/app/business/my_day.py` +
  `app/api/my_day_router.py`** — `list_todo_items()` (real, unwindowed
  read over `Work/Tasks/`, still-open tasks only) replaces the
  hardcoded-0 `todo` stub in `summary()`; `GET /my-day/todo` now returns
  real data.
- feat: **`src/frontend/src/pages/MyDayTodoPage.tsx` +
  `features/my-day/client.ts`** — populated To-Do drill-down
  (`.item-list`/`.item-row`, subject/customer-or-"No customer"/
  due-or-"No due date", `.badge`/`.badge-warning` for "Due today"/
  "Upcoming"), matching the approved `my-day-todo.html` prototype. No
  new CSS. `MyDayPage.tsx`'s dashboard card needed zero code change.
- verified: all 8 locked ACs (`AC-01`–`AC-08`) live against the real
  Outlook mailbox (235-item Tasks folder), real Compass, and the real
  vault (100 real items processed by a real app-start scheduler trigger,
  82 real notes on disk) — including a real induced-failure/independent-
  branch-funnel/recovery cycle, a real Supervised-mode gate check, and a
  real screenshot-verified populated drill-down with both badge states.
  `ADR-027`'s own disclosed-but-unverified `EntryID`-stability claim is
  now empirically confirmed (no superseding ADR needed).
- disclosed: one real, non-blocking finding — `BUG-011`'s pre-existing
  `_slugify` 80-char-truncation defect also affects Task notes, with a
  worse (same-subfolder literal overwrite) consequence than its own
  documented case, since Task notes share one flat `Work/Tasks/`
  subfolder. `ESCALATIONS.md` → `ESC-028`; recommend extending `BUG-011`'s
  own `BUGS.md` entry, not a new bug.
- docs: `MEMORY.md`, `REVIEW-QUEUE.md`, `BACKLOG.md` updated; sprint
  retrospective drafted (`Implementation/Sprints/SPRINT-028-todo-notes-
  from-outlook-tasks-capture.md`).

## 2026-08-13 — SPRINT-026 — REQ-SB-02-US-01 (Browse & Search)

- feat: **`src/backend/app/business/vault_indexing.py` (additive)** —
  `get_last_rebuilt_at() -> str | None` (`REQ-SB-02-US-01-T01`), a second,
  independent accessor alongside `get_index()`; a new module-level
  `_last_rebuilt_at` timestamp is set (ISO-8601 UTC) at the end of every
  `rebuild_index()` call. `rebuild_index()`'s own rebuild/backlink logic
  is otherwise untouched.
- feat: **`src/backend/app/business/vault_search.py` (new)** — read-only
  browse/tag-filter/note-detail/ranked-search query logic over
  `vault_indexing.get_index()` (`REQ-SB-02-US-01-T01`/`T02`): `list_notes`
  (paginated, optional exact-tag filter), `list_tags` (real tag list with
  counts, feeds the frontend's tag-filter chip row), `get_note_detail`
  (a note's resolved forward-links/backlinks), and `search` — a
  field-weighted BM25-style ranked keyword search (title=3x/tags=2x/
  body=1x, per `ADR-026`), computed fresh at query time with no persisted
  ranking index; body text is read fresh via `vault_writer.read_note()`
  per candidate note since `vault_indexing`'s own index entries never
  store it.
- feat: **`src/backend/app/api/vault_search_router.py` (new)** —
  `GET /vault-search/status|notes|notes/{stem}|search|tags`
  (`REQ-SB-02-US-01-T03`), registered in `app/main.py`. `/status` surfaces
  index readiness for the frontend's honest "nothing indexed yet" state;
  `/notes/{stem}` returns `404` for an unknown stem.
- feat: **`src/frontend/src/pages/VaultBrowserPage.tsx` +
  `NoteDetailPage.tsx` (new)** — the Browse & Search UI
  (`REQ-SB-02-US-01-T04`): a search box + ranked results, a tag-filter
  chip row + paginated browse list, a note-detail view with clickable
  forward-link/backlink navigation, and the honest "nothing indexed yet"
  state gating the whole page. New `features/vault-browser/client.ts` API
  client, new `styles/vault-browser.css` (`a.item-row`/`button.item-row`,
  `.tag-chip`, ported verbatim from the approved prototype). New
  `/browse`/`/browse/:stem` routes in `App.tsx`, new `Browse & Search` nav
  item in `Sidebar.tsx`.
- Verified live end-to-end against the real vault (503 unique-stem notes;
  `BUG-011`'s already-disclosed filename-stem collision, unaffected) and a
  real browser: all 7 locked ACs pass, including the ranking-relevance
  guarantee (`AC-04` — a note with only an incidental repeated body
  mention ranks strictly below a note with a real title/tag match) and
  genuine multi-hop wikilink click-through navigation. Full detail: each
  task's own Implementation Log under `Implementation/Tasks/
  REQ-SB-02-US-01-T01`..`T04`; `Implementation/Architecture/ADR.md` →
  `ADR-026`.

## 2026-08-13 — SPRINT-027 — REQ-SB-11-US-01 (Agent Activity & Error Observability)

- fix: **`src/backend/app/business/email_classification.py::
  run_capture_and_record_completion`** — honest-failure-recording fix
  (`REQ-SB-11-US-01-T01`). Meeting-capture's Autonomous branch now
  appends its own `"run_event"` success entry ("Capture run completed —
  N meeting(s) filed") — parity with email-capture, closing the gap
  where meeting-capture's successful runs were never recorded at all.
  Both capture steps' `run_capture_for_agent(...)` calls are now
  independently wrapped in their own `try/except`; an exception escaping
  either step's own per-item handling is caught and recorded as a new
  `"run_error"`-kind history entry ("Capture run failed — {exc}") instead
  of propagating uncaught — one step's failure never suppresses the
  other's own independent success/failure recording.
  `record_capture_run_completed()` now fires only when neither step
  failed this tick, preserving `last_capture_run.json`'s existing "only
  reached when nothing raised" semantics. Composed around the real
  current file (SPRINT-025's own `vault_indexing.rebuild_index()` call,
  landed after this task was authored, is preserved unconditionally).
- feat: **`src/backend/app/data_access/outlook_com.py::check_reachable()`
  (new)** — a lightweight, real, in-process Outlook COM reachability
  check (`REQ-SB-11-US-01-T02`), reusing `_connect_namespace()`'s already-
  proven connection mechanism; never raises past its own body, returns
  `{"reachable": bool, "detail": str | None}`.
- feat: **`src/backend/app/business/agent_activity.py` (new)** — read-only
  cross-agent activity-log aggregation (`REQ-SB-11-US-01-T02`).
  `list_activity_log()` composes every known agent's
  `"run_event"`/`"run_error"` history entries (via
  `agent_registry.list_agents()` + `vault_writer.load_agent_history()`),
  newest-first, excluding `"chat_user"`/`"chat_agent"`/`"proposal"`
  entries. `get_agent_activity()` returns `{"activity_log",
  "outlook_channel"}`, recomputed fresh on every call — no caching, no
  new persisted state.
- feat: **`src/backend/app/api/agent_activity_router.py` (new)** — `GET
  /agent-activity` (`REQ-SB-11-US-01-T03`), a thin passthrough to
  `agent_activity.get_agent_activity()`. Registered in
  **`src/backend/app/main.py`**.
- feat: **`src/frontend/src/pages/AgentActivityPage.tsx` (new)** — the
  Agent Activity page (`REQ-SB-11-US-01-T04`), per the approved prototype
  (`html-prototype/agent-activity.html`): a chronological Activity log
  card (per-entry Success/Failed badge, a failed entry's error detail
  shown inline, an honest empty state when nothing has run yet) and a
  Communication channels card (Outlook COM reachable/unreachable, with
  the real detail message on failure), plus a manual Refresh button.
  **`src/frontend/src/features/agent-activity/client.ts` (new)** —
  `fetchAgentActivity()`. New route (`/agent-activity`) in **`App.tsx`**
  and new nav item in **`Sidebar.tsx`**, positioned after System Health.
  Zero new CSS — composed entirely from already-ported `.card`/
  `.badge*`/`.log-list`/`.kv-list`/`.empty-state`/`.btn` classes.
- Verified live end-to-end against the real backend/vault/Outlook, no
  mocks: the real app-start scheduler tick alone produced the first-ever
  `meeting-capture` success entry; a real in-process-monkeypatched
  email-capture failure proved the `"run_error"` path, Scenario 3's
  cross-agent independence, and the `record_capture_run_completed()`
  gating (`finished_at` unchanged on the failed tick, advancing again on
  a genuine successful one). All 7 locked ACs (`AC-01`..`AC-07`) plus the
  nav-item structural check confirmed with real, live browser
  screenshots (OS-installed Edge headless mode) against real data,
  including a real, screenshot-confirmed Outlook-unreachable state
  (achieved via a temporary, port-identical, immediately-reverted backend
  swap, since physically closing Outlook silently auto-relaunches it on
  this machine via Windows COM). Full verification detail: each task's
  own Implementation Log under `Implementation/Tasks/REQ-SB-11-US-01-T01`
  ..`T04`.

## 2026-08-13 — SPRINT-029 — REQ-SB-04-US-01-T01/T02 (Agent Vault Write Access — buildable scope)

- feat: **`src/backend/app/api/mcp_auth.py` (new)** — per `ADR-025` point
  1: `require_hermes_shared_secret(app: ASGIApp) -> ASGIApp`, an ASGI
  middleware wrapping only the `/mcp` mount. Non-`"http"` ASGI scopes pass
  through unchanged (preserves Streamable HTTP's own SSE/streaming
  framing); an HTTP request whose real TCP peer (`scope["client"][0]`) is
  `127.0.0.1`/`::1` passes through unchanged (Second Brain's own in-app
  loopback MCP client stays unaffected); any other HTTP request must
  present a matching `X-Hermes-Shared-Secret` header or receives a plain
  `401`, with the underlying FastMCP app never invoked.
- feat: **`src/backend/app/config.py`** — new
  `Settings.hermes_mcp_shared_secret: str` field, `.env`-sourced,
  mirroring `compass_api_key`/`anthropic_api_key`'s existing shape.
  **`src/backend/.env.example`** gained a matching `HERMES_MCP_SHARED_SECRET=`
  line.
- feat: **`src/backend/app/main.py`** — the `/mcp` mount now wraps
  `mcp_server.streamable_http_app()` with `require_hermes_shared_secret(...)`;
  `mcp_server.py` itself untouched by this change.
- feat: **`src/backend/app/business/vault_write_tools.py` (new)** — per
  `ADR-025` points 4-6: `propose_vault_write(agent_id, subfolder,
  filename_stem, frontmatter, body)` rejects an unknown `agent_id`
  outright; for a known agent, checks `_is_within_assigned_scope` (a
  deliberate fail-closed stub, **always returns `False`** — no
  `REQ-SB-29-US-01` scope registry exists yet, so every write is honestly
  rejected as out of scope today, never silently allowed); if in scope
  (structurally unreachable until `REQ-SB-04-US-01-T03`), creates a new
  `trigger="hermes"` Pending Approval via
  `pending_approval_registry.create_pending_approval` and returns
  `{"status": "pending", ...}` — never writes directly. New
  `finalize_hermes_write(payload)` — the only function in this module
  that calls `vault_writer.write_note`, invoked exclusively via the
  Approve endpoint's dispatch table.
- feat: **`src/backend/app/api/mcp_server.py`** — registers
  `propose_vault_write` as a fifth `@mcp_server.tool()` (growing the same
  shared server, per `ADR-015` point 9 — no second server instance).
- feat: **`src/backend/app/api/pending_approvals_router.py`** —
  `_APPROVAL_HANDLERS` gains `"hermes_vault_write":
  vault_write_tools.finalize_hermes_write`; Decline needed no new code
  (the existing endpoint already resolves any `"pending"` record
  regardless of `action_id`/`trigger`).
- Verified live against the real backend/vault: `T01`'s 4 non-AC smoke
  checks (real loopback chat-triggered tool call unaffected; a simulated
  non-loopback caller — `httpx.ASGITransport(client=...)` — rejected `401`
  with no header, rejected `401` with a wrong secret, reached the real
  FastMCP app and completed a real tool call with the correct secret);
  `T02`'s locked `AC-03`/`AC-04` (a seeded `"hermes"` pending record's
  real Approve landed a real note with the exact supplied
  frontmatter/body and a real `run_event` history entry; a second seeded
  record's real Decline created no file and appended a real "Declined —
  no action taken" history entry); plus one additional real end-to-end
  MCP tool call against the live `propose_vault_write` front door,
  confirming the fail-closed scope seam honestly rejects every real
  invocation today with a clear message, never fabricated as `"pending"`.
  Full transcripts: each task's own Implementation Log.
- `REQ-SB-04-US-01-T03` (real scope enforcement, `AC-01`/`AC-02`) remains
  `Draft`/blocked on `REQ-SB-29-US-01`'s own decomposition (`ESC-026`,
  `Open`, unchanged) — the story stays `status: In Progress`, not `Done`;
  `SPRINT-029` itself reaches `Done` per its own deliberately-scoped
  Definition of Done.

## 2026-08-13 — SPRINT-025 — REQ-SB-01-US-01 (Vault Indexing)

- feat: **`src/backend/app/data_access/vault_writer.py`** —
  `_parse_frontmatter_value` gained a bracketed-list-value parsing branch
  (`tags: ["a", "b"]` now round-trips into a real `list[str]`, not the
  raw unparsed string); new public `extract_wikilink_targets(body) ->
  list[str]`, reusing the existing `_WIKILINK_PATTERN` constant.
- feat: **`src/backend/app/business/vault_indexing.py` (new)** — the
  project's first real, persistent, re-runnable vault index, per
  `ADR-024`: an in-memory, module-level singleton (`rebuild_index()`,
  `get_index()`), full-rebuild-and-atomic-swap on every trigger, deriving
  incoming-wikilink backlinks from every note's outgoing wikilinks.
- feat: **`src/backend/app/api/vault_index_router.py` (new)** —
  `POST /vault-index/rebuild`, an explicit on-demand re-index trigger
  (`ESC-021` resolved trigger path (a)), registered in `main.py`.
- feat: **`src/backend/app/business/email_classification.py`** — one new,
  unconditional `vault_indexing.rebuild_index()` call inside
  `run_capture_and_record_completion` (`ESC-021` resolved trigger path
  (b)) — the vault index now refreshes on every existing hourly-plus-
  app-start capture tick, with zero changes to
  `app/scheduling/capture_scheduler.py`.
- fix (finding, not this sprint's own scope): a real, pre-existing
  filename-stem collision was found live during `AC-01` verification —
  two distinct real notes (`Work/Emails/...SimplAI...md`,
  `Work/Notifications/...SimplAI...md`) share an identical 80-character-
  truncated filename stem, because `vault_writer._slugify`'s truncation
  silently discards `email_classification.py`'s trailing disambiguating
  id-suffix when the subject alone fills the 80-char budget. Not fixed
  here (out of this sprint's own file scope) — escalated as
  `ESCALATIONS.md` → `ESC-027` (Open), recommended for `/bug` capture.
- docs: `REQ-SB-01-US-01`, `SPRINT-025`, all 4 tasks (`T01`-`T04`) marked
  `Done`; `BACKLOG.md` REQ-SB-01/SPRINT-025 rows updated; `ESCALATIONS.md`
  → `ESC-027` (new); `REVIEW-QUEUE.md` pointers added (`ESC-027`,
  `SPRINT-025` retro harvest).

## 2026-08-13 — REQ-SB-02 (Browse & Search) — /design pass

- design: **`html-prototype/vault-browser.html` (new)** — a new top-level
  nav page: lists/browses all indexed notes (grounded in the real vault's
  own 496-note breakdown from `REQ-SB-01-US-01`'s direct inspection — 204
  Email, 134 Person, 51 Meeting, 6 Customer, 1 Partner), filters by tag
  (a real match and a genuine zero-match example), and runs a ranked
  keyword/full-text search — NOT a bare substring match, NOT
  embeddings/semantic search (`REQ-SB-06`, P2, stays deferred) — with an
  example result set where a note ranks last despite literally containing
  the query text as an incidental body substring, demonstrating
  relevance-over-substring directly. A top-level state-switcher
  demonstrates the honest "vault not indexed yet" state, visibly distinct
  from "indexed, but zero matches."
- design: **`html-prototype/note-detail.html` (new)** — a note's forward
  (outgoing) wikilinks and backlinks (incoming wikilinks) as a real,
  clickable LIST — explicitly NOT a visual/interactive graph canvas
  (resolved out of scope this pass, `ESC-022` `Resolved` 2026-08-13,
  matching `ADR-011`'s "proportionate first" precedent). A small, closed,
  three-note demo graph (an Email, a Customer hub, and a Meeting note, all
  tagged `customer/masdar` — the story's own example tag) makes every
  forward-link/backlink row a genuinely working click in a browser,
  including two honest empty-list edge cases grounded in
  `REQ-SB-01-US-01` Scenario 6's "empty list, not an error" index
  behavior.
- design: added two small additive CSS primitives to `styles.css`,
  composed entirely from existing tokens (no new hex, no framework):
  `a.item-row`/`button.item-row` (a real clickable variant of the
  existing plain-`<div>` `.item-row`) and `.tag-chip` (a pill-shaped
  clickable tag button reusing the existing `.state-switcher` click
  delegation in `app.js` — the tag filter and note-graph navigation both
  needed zero new shared JS). `note-detail.html` carries one small
  page-scoped inline script, not added to the shared `app.js`, that
  honors a `#hash` deep link from `vault-browser.html`'s note rows.
- design: added the new "Browse & Search" `.nav-item` to the shared
  sidebar on every existing prototype page (`index.html`,
  `agents-map.html`, `agents-map-exploration.html`, `my-day.html` + its 4
  drill-downs + `my-day-approvals.html`, `settings.html`,
  `system-health.html`, `agent-activity.html`), matching System
  Health/Agent Activity's own rollout precedent; added a new catalog card
  to `index.html`.
- docs: flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not
  yet approved; do not run `/plan-tasks REQ-SB-02` until it is (and until
  `REQ-SB-01-US-01` has reached `Ready`).

## 2026-08-13 — REQ-SB-11 (Agent Activity & Error Observability) — /design pass

- design: **`html-prototype/agent-activity.html` (new)** — a new
  top-level nav page (placement previously resolved, `ESC-025`
  `Resolved`) showing a chronological, cross-agent activity log (every
  completed background capture run, newest first, with its own
  success/failure outcome and — for a failure — its error detail visible
  inline, never dropped) plus a current status indicator for the Outlook
  communication channel, reported honestly as direct COM reachability
  (not "Hermes-wrapped" — no live Hermes connection exists in this
  codebase yet). Two independent `.state-switcher` groups demonstrate all
  7 Gherkin scenarios: "Activity recorded" (a mix of successes across
  both configured capture agents plus one real failure with detail) vs.
  "No runs yet" (the honest empty state), and "Outlook reachable" vs.
  "Outlook unreachable". Deliberately does not duplicate System Health's
  own MCP-mount, Provider-availability, or last-capture-run checks.
- design: reused `styles.css`'s existing `.log-list`/`.log-item`/
  `.log-item-meta` chronological-log primitive verbatim (already live on
  Agents Map's per-agent Communication History panel; this is its first
  cross-agent use) and System Health's `.kv-list`/`.badge-success`/
  `.badge-danger` shape for the channel-status card. Zero new CSS — a
  failed run's error detail is composed from existing `.text-muted` +
  a line break inside the same `.log-item`, not a new class.
- design: added the new "Agent Activity" `.nav-item` to the shared
  sidebar on every prototype page (`index.html`, `agents-map.html`,
  `agents-map-exploration.html`, `my-day.html` + its 4 drill-downs +
  `my-day-approvals.html`, `settings.html`, `system-health.html`),
  matching System Health's own rollout precedent; added a new catalog
  card to `index.html`.
- docs: flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not
  yet approved; do not run `/plan-tasks REQ-SB-11` until it is.

## 2026-08-13 — REQ-SB-38 (Agents Map Density Clustering) — /design pass

- design: **`html-prototype/agents-map.html`** gains a new 5th
  state-switcher option, "Density clustering (REQ-SB-38 demo)" —
  demonstrates a new clickable cluster marker ("+N" circle, per the
  operator's own literal request) that collapses a Section's own overflow
  agents once a proposed `VISIBLE_SLOT_CAP = 6` (per Section x Type-ring,
  designer's own proposal, flagged for sign-off) is exceeded, instead of
  rendering every agent at a fixed position regardless of count. A
  synthetic 15-agent "Illustrative Worker" dataset in the Technical
  Section (marked illustrative throughout, not real/planned agents)
  stress-tests the pattern since today's real ~7-agent roster never
  reaches it. Clicking the marker opens a NEW narrower drill-down scoped
  to just the clustered subset (10 agents), reusing the existing
  `.explore-drilldown`/`.hub-node`/`.agent-node`/`.cluster-line` "Agents
  Tree" pattern BUG-002's Option D already established — the same
  click-to-zoom mechanic applied one level deeper, wired through
  `agents-map.js`'s existing generic `wireDrilldown()` with only a
  widened element selector, no new interaction code. Clicking the
  Section's own Hub still shows the full, unclustered 15-agent drill-down
  (an intentional, explicitly-flagged open question — whether
  `layoutSectionDrilldown`'s own full-360° view also needs clustering is
  left undecided, per the PRD's own open question 2).
- design: **`html-prototype/styles.css`** — `.map-overflow-marker`
  (defined since REQ-SB-12's first pass, never instantiated until now)
  is now a real, clickable `<button>` — dashed-accent border + tinted
  glow at rest (matching `.hub-node`), hover-lift (matching
  `.agent-node`) — with two new inner spans,
  `.map-overflow-marker-count`/`-label`, mirroring `.hub-node`'s own
  bold-text + muted-subtext structure. No new hex, no new component
  family — the marker itself already existed as an unused primitive.
- design: **`html-prototype/agents-map.js`** — `wireDrilldown()`'s Hub
  click selector and `playIntro()`'s Hub-treatment selector each widened
  by one clause to also match `.map-overflow-marker[data-section-id]` —
  no new functions.
- docs: **new shared side-panel stand-in**
  (`[data-agent-detail="illustrative-worker"]` in `agents-map.html`'s
  `#agentPanel`) — every synthetic "Illustrative Worker" node shares one
  explanatory panel instead of 15 near-duplicate real ones; REQ-SB-13's
  real per-agent panel contract is unaffected for every real agent.
  Flagged for human browser sign-off — see `REVIEW-QUEUE.md`. Not yet
  approved; do not run `/spec REQ-SB-38` until it is.

## 2026-08-13 — Agents Map overview: BUG-009/BUG-010 fixes

- fix: **BUG-009** — agents could fan out past their own Section's wedge
  boundary into a neighboring Section on the Agents Map overview.
  `layoutAgents.ts`'s `SECTION_ARC_SPAN_DEG` was a fixed 80° fan-out
  applied regardless of section count; with 5 sections evenly spaced
  (72° wedges), a section with enough agents overflowed by 4°+ per side.
  Replaced with a span computed as `min(80deg, (360/n) * 0.8)`, capping
  the fan-out at 80% of the section's own wedge width. Verified live:
  `Email Capture` moved from -58° (inside Customers' wedge) to -47°
  (inside Productivity's own wedge); `Vault Filing Expert` moved from
  22° to 11°.
- fix: **BUG-010** — on hover, an agent's Type and Name labels rendered
  at the identical position on the Agents Map overview, directly
  overlapping and illegible. `.agent-node--compact:hover`'s label and
  type rules shared the same `top: 100%` anchor with no vertical offset
  between them. Type's rule now offsets to `top: calc(100% + 1.9em)`,
  clearing the label's own reveal box. Verified live with real rendered
  text — label and type now render with a clean 3px gap, zero overlap.

## 2026-08-13 — REQ-SB-36-US-01 (T04/T05) re-verification — SPRINT-022 follow-up

- docs: **Live re-verification of `REQ-SB-36-US-01`'s `AC-01`/`AC-03`
  (web-research skill), closing the real-credential gap flagged in
  `REVIEW-QUEUE.md` since `SPRINT-022`.** No source code changed. The
  operator provisioned a genuine `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` in
  `src/backend/.env`. `AC-01` confirmed: a real, non-fabricated web-search
  result with real citations (`python.org`, Wikipedia) for a real,
  checkable query. `AC-03` confirmed: two queries engineered to have no
  real answer both honestly refused to fabricate a result (`sources: []`)
  — though the real observed shape (`found: true` + honest refusal text)
  differs from the `found: false` shape originally documented in `T04`, a
  live-discovered nuance recorded for human review, not a defect.
- fix (operational, not code): found and resolved a genuine root cause
  blocking re-verification — `.second-brain/agent_providers.json` had
  been seeded during `SPRINT-022`'s own original build with the inert
  placeholder credential, and `provider_registry` never auto-resyncs an
  already-persisted Provider's credential from `.env`. Resolved by
  deleting the stale state file to force the already-documented clean
  re-seed. See `MEMORY.md` → `## Constraints` for the standing rule this
  produced.
- docs: updated `Implementation/Tasks/REQ-SB-36-US-01-T04-web-research-
  skill-tool.md`, `...-T05-invoke-skill-args-and-router-body.md`,
  `Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md`, and
  `REVIEW-QUEUE.md`'s `SPRINT-022` entry with the re-verification results.

## 2026-08-13 — SPRINT-024 / REQ-SB-36-US-02 (T01-T03)

- feat: **Agent knowledge bootstrapping — delegated-research chain,
  Compass Expert pilot** (`REQ-SB-36`, `ADR-023`). New pilot Expert
  agent, `"compass-expert"` (`src/backend/app/business/agent_registry.py`
  — data only, no shape change), with one new declared action,
  `"build_knowledge"` (`"mutates": True`, trigger phrases "build my
  knowledge" / "build knowledge" / "research my subject").
- feat: **New `src/backend/app/business/agent_orchestration/
  knowledge_bootstrap.py`** — `async def bootstrap_agent_knowledge(
  agent_id, subject) -> dict`, a deterministic (never recursive/model-
  driven) three-hop composition of four already-real functions: Hop 1
  `graph.route_cross_section_request` (Hub routing to a Research
  Expert) → an Autonomous-mode check
  (`working_mode_registry.get_agent_working_mode`) → research
  (`skill_registry.invoke_skill(..., "web-research", {"query": ...})`)
  → Hop 2 `route_cross_section_request` (Hub routing to the Vault Filing
  Expert) → filing (`vault_filing_expert.determine_placement_and_file`,
  Tier 1 writes / Tier 2 defers to a real pending-approval record).
  Every branch (`written`/`pending_approval`/`no_match`/`no_results`/
  `not_autonomous`/`unavailable`) records one real `run_event` history
  entry; a `try/except` around the research call converts a genuine
  external-API failure (a bad/absent Provider credential) into the
  honest `no_results` outcome instead of crashing the chain — a real,
  live-verified finding (a genuine `401` from a real, unmocked Anthropic
  call was caught correctly), not a theoretical safeguard. Fully
  generic over `agent_id`/`subject` — never references `"compass"`
  anywhere in its own body, confirmed live with a second, throwaway
  pilot agent.
- feat: **`src/backend/app/api/agents_router.py`** — `"build_knowledge"`
  wired into the existing `_ACTION_HANDLERS`/`_invoke_action` funnel (no
  new endpoint): a new `_run_build_knowledge(agent_id)` handler resolves
  `subject` from the matched agent's own `"Subject"` setting and
  translates `bootstrap_agent_knowledge`'s own richer status shape into
  the shared `{"status", "message"}` envelope. Since the existing
  `_execute_action`'s own handler-calling convention (`handler()`,
  `len(results)`) is hardcoded to `run_capture_now`'s own shape and does
  not generalize to an async, `agent_id`-taking handler, added a NEW
  sibling `_execute_async_action` (mirrors `_execute_action`'s own
  Provider-availability gate) rather than modifying `_execute_action`
  itself, which `app/api/pending_approvals_router.py`'s own synchronous
  Approve dispatch still relies on unchanged. `_invoke_action` is now
  `async def` (its only two call sites, `trigger_action`/`chat`, both
  already `async def`, updated to `await` it); a new, generic
  `"history_recorded"` envelope flag prevents the existing generic
  post-call history append from double-recording an outcome the handler
  already recorded itself.
- Verified live end-to-end against the real backend, real vault, and
  real Compass Provider: `AC-01` (Scenario 1) via both the real chat
  trigger and the direct Available-Actions endpoint; `AC-02` (Scenario
  2, Tier-2 pause) — a real pending-approval record created for a
  genuinely new top-level area, both Hub hops and research already
  completed by the pause, per the real `vault_filing_expert` mechanism;
  `AC-04` (Scenario 4, no-match); `AC-05` (Scenario 5, honest failure) —
  two independent real paths, including a genuine live `401` from the
  real (provably-inert-credentialed) `"anthropic-claude"` Provider;
  `AC-06` (Scenario 6, generic capability) via a second, throwaway pilot
  agent and subject. `vault-qa` configured (real runtime data, not code)
  as this pilot's Research-Expert candidate (keywords, `web-research`
  skill access); `vault-filing-expert` gained one additional real
  keyword (`"vault"`) so Hop 2's routing genuinely matches it. **Honest,
  disclosed verification gap:** no real `ANTHROPIC_API_KEY` exists in
  this environment (provably-inert placeholder, per `SPRINT-022`'s own
  finding); the Tier-1 "written" and Tier-2 "pending_approval" full
  chain-composition outcomes (real Vault Filing Expert invocation, real
  Compass LLM placement call, real vault write / real pending-approval
  record) were proven live via the established, disclosed, reverted
  in-process-monkeypatch technique substituting only the externally-
  credential-gated research step. `REQ-SB-36-US-02-T04` (Scenario 3,
  "draw on afterward") remains `Draft`/blocked on `REQ-SB-29-US-01`'s
  own decomposition (`ESC-018`, still `Open`) — out of this sprint's own
  scope by design. Full reasoning: `Implementation/Architecture/ADR.md`
  → `ADR-023`; each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-36-US-02-T01`..`T03`.

## 2026-08-12 — SPRINT-022 / REQ-SB-36-US-01 (T01-T06)

- feat: **Real Anthropic Provider integration + `web-research` skill**
  (`REQ-SB-36`, `ADR-022`, corrected mid-build — see below). New
  `anthropic` dependency (`requirements.txt`, resolved `0.121.0`); new
  required `Settings.anthropic_api_key`/`anthropic_model`
  (`src/backend/app/config.py`, `.env.example`). New
  `src/backend/app/data_access/anthropic_client.py` — plain `anthropic`
  SDK client (not LangChain-wrapped), `web_search(api_key, model, query)
  -> {"found": bool, "summary": str, "sources": list[str]}`, calling
  Anthropic's own server-side web-search tool
  (`web_search_20250305`/`web_search`, confirmed current against the
  real, installed SDK). `src/backend/app/business/provider_registry.py`
  extended (not reworked): `_REAL_CLIENT_PROVIDER_IDS` gains
  `"anthropic-claude"`, `_seed_state()` additionally auto-seeds an
  `"Anthropic Claude"` Provider entry, new `get_provider(provider_id) ->
  dict | None` by-id lookup added.
- feat: **`src/backend/app/business/skill_tools.py`** gains a third real
  skill, `web-research` — `web_research(query: str, agent_id: str) ->
  dict`. Resolves the **invoking agent's own linked Provider**
  (`provider_registry.get_agent_provider(agent_id)`) and dispatches to
  the real Anthropic call only when that Provider is `"anthropic-claude"`
  with a real client; any other linked Provider (Compass, or none)
  returns the same honest "not yet available" shape `diagram-
  understanding` already established — never a fabricated result.
  `src/backend/app/business/skill_registry.py::invoke_skill` gains an
  additive `args` parameter, plus automatic `agent_id` injection for any
  handler whose own signature declares it (`diagram-understanding`'s
  zero-arg call is unaffected). `src/backend/app/api/skills_router.py`'s
  invoke endpoint gains an optional JSON body (`{"query": ...}`).
- fix: **Live-discovered skill-access tool-binding gap closed**
  (`ADR-022` point 6) — `src/backend/app/business/agent_orchestration/
  mcp_client.py::load_vault_query_tools()` returned every tool on the
  shared MCP server with no per-agent filtering, meaning any agent's
  ordinary chat turn could already reach `skill_tools.py`'s catalog
  regardless of `skill_registry.has_skill_access`. Replaced with
  `load_agent_tools(agent_id)`, which gates every `skill_tools.SKILLS`
  entry by `has_skill_access` while always keeping the four core
  vault-query tools; `graph.py::run_agent_conversation`'s call site
  updated accordingly (composed around the real, current file — matched
  `REQ-SB-20-US-01-T05`'s own already-landed shape exactly, no
  reconciliation needed).
- **Mid-build operator correction (`ESCALATIONS.md` → `ESC-019`,
  `ADR-022`'s own "Correction" addendum):** `ADR-022` point 3's original
  fixed-`"anthropic-claude"`-Provider-id design was reversed at the
  operator's own direct instruction — confirmed live first (not assumed)
  that Compass/GPT-5 has no real hosted web-search capability, so a
  Compass-linked agent must honestly report unavailable rather than
  fabricate a result from a plain completion.
- **Verified live** against the real running backend (real HTTP + direct
  calls): dependency install, `Settings` fail-fast, `provider_registry`
  seeding/credential-edit-takes-effect, the corrected Provider-resolution
  dispatch (Compass-linked → honest unavailable; Anthropic-linked → real
  dispatch attempt, confirmed via a real, honest `401` since no genuine
  API key is provisioned in this environment), `AC-02`'s `403` access
  refusal distinct from both the `200` honest-unavailable and the
  real-dispatch-attempt responses, and `load_agent_tools`'s own filtering
  logic (in-process monkeypatch, since this project's documented
  MCP-loopback port `8001` was held by an unkillable stale listener this
  session's tooling could not clear). **Open gap, honestly flagged, not
  hidden:** `AC-01`/`AC-03`'s own "produces a real relevant result" /
  "produces a real honest-empty result" branches could not be exercised —
  no genuine `ANTHROPIC_API_KEY` was available; a clearly-labeled,
  provably-inert placeholder was added to the real, gitignored `.env`
  purely so the app could boot for all other verification. See
  `REVIEW-QUEUE.md` for the follow-up.

## 2026-08-12 — SPRINT-023 / REQ-SB-35-US-01 (T01-T03)

- feat: **Vault Filing Expert — new registry agent, methodology-grounded
  placement/write, two-tier approval** (`REQ-SB-35`, `ADR-021`). New
  `"vault-filing-expert"` entry (`type: "expert"`, `actions: []`) in
  `src/backend/app/business/agent_registry.py`, reachable only via
  `REQ-SB-20`'s Hub-to-Hub cross-Section routing — real, persisted
  keywords assigned (`filing`, `tags`, `vault placement`, `categorize`,
  `new category`).
- feat: **`src/backend/app/business/vault_filing_methodology.py`** (new)
  — `build_placement_prompt(...)`, grounding a placement decision in a
  condensed excerpt of `Documentation/References/beyond-the-second-brain-
  methodology.md` plus `ADR-004`'s tag/folder split, alongside the three
  deterministically pre-fetched `list_known_kinds`/`list_known_customers`/
  `list_known_partners` lists (never left to the model to tool-call).
- feat: **`src/backend/app/business/vault_filing_expert.py`** (new) —
  `determine_placement_and_file(content, source_description,
  requesting_agent_id)`: one `model_factory.resolve_agent_model(
  "vault-filing-expert")` completion for a structured placement decision;
  `is_new_top_level_area` is always re-checked in Python
  (`kind not in known_kinds`), never trusted from the model's own
  boolean. **Tier 1** (existing category, or a new tag/subfolder within
  an existing top-level area) writes immediately via `vault_writer.
  write_note`, with a numeric-suffix collision guard
  (`_unique_filename_stem`) and a visible uncertainty marker on
  low-confidence placements (never silently dropped, placement never
  pauses). **Tier 2** (a genuinely new top-level area) unconditionally
  calls `pending_approval_registry.create_pending_approval(...)` —
  `working_mode_registry` is never referenced anywhere in this module,
  bypassing the working-mode gate by construction, not a conditional
  check — and returns `{"status": "pending_approval", ...}`; content is
  written only once `finalize_new_top_level_area(payload)` runs on
  Approve. A written note's `customer`/`partner` frontmatter field plus a
  real `[[wikilink]]` to the referenced entity's hub note (via
  `customer_hub_linking`/`partner_hub_linking`, reused as-is) are added
  mechanically whenever the model names one — required for the new
  entity to be discoverable via `list_known_customers()`/
  `list_known_partners()`, not just tagged.
- feat: **Tier-2 approval resolution** — `pending_approval_registry.
  create_pending_approval` gained an additive `payload: dict | None =
  None` parameter, stored verbatim on the record (every existing
  zero-payload caller unaffected). `src/backend/app/api/
  pending_approvals_router.py`'s Approve endpoint gained a new
  `_APPROVAL_HANDLERS` dispatch table (`{"propose_new_top_level_area":
  vault_filing_expert.finalize_new_top_level_area}`), consulted before
  the existing `_execute_action`/`run_capture_for_agent` re-dispatch.
  Decline needed no new code — `resolve_pending_approval(id, "declined")`
  alone is sufficient; `finalize_new_top_level_area` is never called for
  a declined record.
- Verified live end-to-end against the real backend `.venv`, real vault,
  and a real Compass Provider call, against all 8 locked ACs: an
  existing-category placement (`AC-01`); a genuinely new customer tag
  within an existing kind folder, discoverable via
  `list_known_customers()` (`AC-02`); real methodology + live-vault
  grounding, with real tags/wikilinks (`AC-05`); an honest, visible
  low-confidence marker that never pauses placement (`AC-06`); real
  Hub-routing discoverability with no separate write path elsewhere
  (`AC-07`); a numeric-suffix filename-collision guard that never
  overwrites (`AC-08`); a genuinely-new-top-level-area proposal that
  creates an identical pending-approval outcome regardless of the
  agent's own working mode — `autonomous` and `supervised` both tested —
  and writes only on Approve (`AC-03`); and an honestly-recorded decline
  that never files the content and is never silently retried elsewhere
  (`AC-04`).

## 2026-08-12 — SPRINT-021 / REQ-SB-21-US-01 (T01-T09)

- feat: **Agent Working Modes — Autonomous / Supervised / Manual**
  (`REQ-SB-21`, `ADR-018`/`ADR-020`). New sibling `.second-brain/
  agent_working_modes.json` (self-healing default `"autonomous"`),
  owned by new `src/backend/app/business/working_mode_registry.py`
  (`get_agent_working_mode`/`set_agent_working_mode`/
  `VALID_WORKING_MODES`), composed alongside `agent_registry.py`
  (unmodified).
- feat: **Pending Approvals workflow store** — new sibling
  `.second-brain/agent_pending_approvals.json` (this project's first
  use of `uuid`), owned by new `src/backend/app/business/
  pending_approval_registry.py` (`list_pending_approvals`/
  `get_pending_approval`/`create_pending_approval`/
  `resolve_pending_approval`; idempotent per `agent_id`+
  `trigger="background"` only).
- feat: **Corrected two-axis working-mode gate** — `src/backend/app/
  business/agent_registry.py` gained a static `"mutates": bool` field
  on every action definition plus a new `get_action(agent_id,
  action_id)` lookup helper (`ADR-020` point 1, fail-safe to `True` for
  an unresolvable action). `src/backend/app/api/agents_router.py`'s
  `_invoke_action` was split into the gate + the existing unconditional
  dispatch (renamed `_execute_action`): **Supervised** gates on the
  action's own `mutates` classification, regardless of trigger; a
  read-only action proceeds immediately even while Supervised, only a
  mutating one proposes-and-waits. **Manual** gates on trigger source —
  a direct chat/button ask always executes immediately; a new
  `"hub_routed"` trigger value is refused outright (currently a no-op,
  forward-looking correctness for a future cross-agent action-invoke
  story). `GET`/`PATCH /agents/{agent_id}` gained an additive
  `working_mode` field. `src/backend/app/business/
  email_classification.py::run_capture_and_record_completion` gained
  the paired background-pipeline gate (new shared
  `run_capture_for_agent(agent_id, limit)` helper) — Autonomous runs
  unchanged, Supervised creates a `trigger="background"` pending
  approval instead of running, Manual skips silently, no record.
- feat: **`Pending Approvals` HTTP surface** — new `src/backend/app/api/
  pending_approvals_router.py` (`GET /pending-approvals[?status&
  agent_id]`, `GET /pending-approvals/{id}`, `POST /pending-approvals/
  {id}/approve|decline`); Approve calls `_execute_action`/
  `run_capture_for_agent` directly, bypassing the gate (the approval
  itself is the authorization — re-entering the gate would infinite-
  defer). Registered in `src/backend/app/main.py`.
- feat: **Agent Settings working-mode picker + live `.chat-proposal`
  card** — `src/frontend/src/features/agents-map/agentsApiClient.ts`
  (`AgentDetail`/`updateAgentAssignment`/`AgentHistoryEntry` gained
  `working_mode`/`"proposal"` kind/`pending_approval_id`, additive);
  new `pendingApprovalsApiClient.ts`; `AgentDetailPanel.tsx` gained a
  Working-mode `<select>` kv-row and renders a `"proposal"`-kind
  Communication History entry as a `.chat-proposal` card with live-
  resolved Pending/Approved/Declined status and working Approve/
  Decline. `src/frontend/src/styles/agent-panel.css` gained the
  `.chat-proposal*` rules, ported verbatim from the approved
  `html-prototype/styles.css`.
- feat: **Standalone Pending Approvals page** — new
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` (route
  `/my-day/approvals`), a new `App.tsx` route, and a new "Pending
  Approvals" card on `MyDayPage.tsx` with its own live pending count
  (fetches `GET /pending-approvals` directly — `my_day.py`/
  `my_day_router.py` untouched).
- fix: an unresolvable `pending_approval_id` on a `"proposal"`-kind
  history entry (live-discovered, leftover smoke-check debris) produced
  an unhandled promise rejection in `AgentDetailPanel.tsx`'s new
  card-resolving effect — fixed with `.catch(() => {})`.
  Verified live end-to-end against all 8 locked ACs (`AC-01`..`AC-08`)
  via the real backend, real frontend (headless-Chrome-via-CDP), the
  real vault, and real Outlook/Compass integration — including several
  genuine capture runs and a live Approve click driving a real
  39-meeting sweep. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-21-US-01-T01`..`T09`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-21-US-01-agent-working-
  modes.md`; `Implementation/Architecture/ADR.md` → `ADR-018`/`ADR-020`.

## 2026-08-12 — SPRINT-020 / REQ-SB-20-US-01 (T01-T06)

- feat: **Section Hub Intelligence & Cross-Section Routing** — per-agent
  free-text keywords and Hub-mediated cross-Section request routing
  (`REQ-SB-20`, `ADR-017`). `src/backend/app/data_access/vault_writer.py`
  gained `load_agent_keywords`/`save_agent_keywords`/
  `load_all_agent_keywords` (new sibling `.second-brain/
  agent_keywords.json`, `{agent_id: [keyword, ...]}`); new
  `src/backend/app/business/agent_keywords.py` (`get_agent_keywords`/
  `set_agent_keywords`/`list_candidate_agents_for_keyword_match` —
  deterministic, case-insensitive, cross-Section-only keyword-substring
  matching, `ADR-011`'s posture one layer up); `src/backend/app/api/
  agents_router.py`'s `GET`/`PATCH /agents/{agent_id}` gained an additive
  `keywords` field (explicit `[]` clears, omitted is a no-op).
- feat: **`route_hub_request` LangGraph node + `request_cross_section_help`
  tool** — `src/backend/app/business/agent_orchestration/graph.py` gained
  one new node on the same compiled graph, a new local (never-MCP-
  registered) tool intercepted before the graph's own generic
  `_execute_tools` path, and a directly-callable
  `route_cross_section_request(requesting_agent_id, need_description)`
  public entry point representing the mandatory "own Hub, then target Hub"
  two-hop relay as two sequential lookups, both hops recorded as explicit
  result fields (`from_section_id`/`matched_section_id`). `src/backend/app/
  business/agent_orchestration/state.py`'s `AgentConversationState` gained
  `hub_routing_result: dict | None`.
- feat: **Agent Settings Keywords row** —
  `src/frontend/src/features/agents-map/agentsApiClient.ts` (`AgentDetail`/
  `updateAgentAssignment` gained `keywords`, additive) and
  `AgentDetailPanel.tsx` (new commit-on-blur free-text Keywords kv-row,
  comma-separated, whitespace/empty entries dropped on commit).
  Verified live end-to-end against all 4 locked ACs: a real cross-Section
  match with both relay hops explicit and inspectable; an honest,
  byte-identical-across-4-repeats no-match; an empty-keyword agent
  structurally never selected across 5 varied need-descriptions (including
  one textually overlapping its own name); the Keywords field's full
  round-trip (empty state with placeholder → commit → persisted across a
  real panel close/reopen → independent backend `GET`), via headless-
  Chrome-via-CDP. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-20-US-01-T01`..`T06`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-20-US-01-section-hub-
  intelligence-and-cross-section-routing.md`.

## 2026-08-12 — SPRINT-019 / REQ-SB-31-US-01 (T01-T04)

- fix: **`run_agent_conversation` crash-gap fix (T01, Scenario 8)** —
  `src/backend/app/business/agent_orchestration/graph.py`'s outer body
  (`await mcp_client.load_vault_query_tools()` through `await
  _GRAPH.ainvoke(initial_state)`) is now wrapped in the same
  honest-failure-funnel `try/except Exception as exc: return {"error":
  ...}` pattern `_call_model` already used — an unexpected exception in
  MCP tool loading or graph invocation itself now returns an honest
  `{"error": ...}` instead of propagating as a raw, unhandled 500.
  Verified live via an in-process monkeypatch inducing a real exception
  for an agent whose Provider is otherwise available, then a reverted
  normal call confirmed to still succeed.
- feat: **System Health View (T02-T04)** — new read-only status
  aggregation surface (`REQ-SB-31`). `src/backend/app/business/
  system_health.py` (new — `get_system_health()`, `mcp_mount_reachable()`,
  `list_disabled_agents()`, composing `provider_registry`/
  `agent_registry`/`vault_writer` as-is, plus one local `GET /mcp`
  loopback reachability check); `src/backend/app/api/
  system_health_router.py` (new — `GET /system-health`), registered in
  `app/main.py`; `src/frontend/src/features/system-health/client.ts` +
  `src/frontend/src/pages/SystemHealthPage.tsx` (new — Health Issues / MCP
  path / Providers / Last capture run cards, zero new CSS), wired into
  `App.tsx` (`/system-health` route) and `Sidebar.tsx` (new nav item),
  per the approved prototype `html-prototype/system-health.html`.
  Verified live end-to-end: the real "everything healthy" state (MCP
  reachable, all 5 agents on Compass, a real completed capture run); a
  real induced "issues present" state (MCP mount pointed at an
  unreachable port + a throwaway no-real-client Provider assigned to one
  agent) showing both as Health Issues simultaneously, then reverted; the
  real vault's `last_capture_run.json` temporarily moved aside and
  restored to prove the honest "no run has completed yet" empty state
  (never a fabricated timestamp); every state change confirmed to reflect
  on the very next call/reload with no caching. One real, live-discovered
  bug found and fixed in-scope: `mcp_mount_reachable()`'s `httpx.get()`
  call needed `follow_redirects=True` — the real `/mcp` mount 307-redirects
  `GET /mcp` → `GET /mcp/` before answering its documented 406 "alive"
  signal, and `httpx.get()`'s own default (`follow_redirects=False`)
  stopped at the redirect, which would have falsely shown MCP as
  unreachable even when healthy. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-31-US-01-T01`..`T04`'s own Implementation
  Logs; `Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md`.

## 2026-08-12 — SPRINT-018 / REQ-SB-33-US-01-T01

- feat: **Agent grounding & honest-uncertainty guardrail** —
  `history_entries_to_messages`'s single prepended `SystemMessage`
  (`src/backend/app/business/agent_orchestration/state.py`) now carries a
  grounding/honest-uncertainty instruction alongside the existing identity
  sentence: answer only from real tool results/history/memory, honestly
  report a failed tool call rather than inventing a substitute, and say
  "I don't know" rather than answering from the model's own general
  training knowledge as if it were a vault fact. Still exactly one
  `SystemMessage`, applied globally to every agent's real conversational
  reply path (`REQ-SB-25`), unconditional, no per-agent config. Verified
  live against all 4 locked ACs: a real tool-backed question still answers
  normally (exact match against the real vault's known-customer list); a
  real vault-scoped question with no matching data gets an honest "I don't
  see it"; two real induced tool-call-failure passes (one tool failing
  with a real fallback recovery, then every tool failing with no
  fallback) both produce an honest failure report, never a fabricated
  substitute; a question inviting a general-knowledge fact about a real
  vault entity (ADNOC) is honestly declined rather than answered from
  training knowledge. Full reasoning and transcripts:
  `Implementation/Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md`.

- design: **System Health View prototype (`REQ-SB-31`)** — new
  `html-prototype/system-health.html` top-level nav page (operator-directed
  placement, 2026-08-12), wired into the shared sidebar `.nav-item` list on
  every prototype page. Shows a Health Issues list (empty "No Health
  Issues" state, or the MCP/agent-orchestration path plus any agent whose
  Provider has no real client — shown `Disabled`, listed as a Health Issue,
  per the operator's scoped 2026-08-12 override), an MCP/agent-orchestration
  status row (`GET /mcp` reachable/unreachable), a Providers status list
  rolled up per distinct Provider (unchanged, neutral "no real client"
  honesty language — the override applies to the affected agent, not the
  Provider row), and a last-capture-run status row reading
  `.second-brain/last_capture_run.json`'s recorded completion time or its
  honest absence. Two state-switcher groups demonstrate all 8 Gherkin
  scenarios from `REQ-SB-31-US-01`; Scenario 8 (backend-only crash-gap fix)
  has no UI region, per the story's own Non-Goals. Composed entirely from
  existing tokens/components — `.card`, `.badge-*`, `.kv-list`/`.kv-row`,
  `.item-list`/`.item-row`, `.state-switcher`, `.empty-state` (its first
  real use). No new CSS. Always flagged for human browser sign-off — see
  `REVIEW-QUEUE.md`. **Approved 2026-08-12** after live verification via a
  new temporary static-file preview server (`tools/run-prototype.cmd`,
  registered in `.claude/launch.json` as `second-brain-html-prototype`,
  port 8088) — needed because this environment's `file://` preview renders
  `html-prototype/` as a static, non-interactive snapshot, so the
  state-switcher toggle JS couldn't be exercised without a real HTTP
  server.

- feat: Agent detail panel (`AgentDetailPanel.tsx`) — restructured into
  Chat/History/Settings tabs, per direct operator feedback ("the Chat
  Window is very small... My Recommendations is to have a Tab System").
  Previously all three sections stacked in one scrolling column, with
  the chat thread capped at a fixed `220px` (`.chat-thread`'s old
  `max-height`) squeezed between Settings/Actions above and
  Communication history below. Now: panel widened `440px` → `560px`
  (`.side-panel`), Chat is the default tab and its thread fills the
  panel's full remaining height (`.side-panel-section--chat`, `flex: 1`
  chain from `.side-panel-body` down). Also added, addressing "I don't
  have any indication that something is happening in the background":
  a `sending` state disables the input/Send button and shows an
  animated three-dot typing indicator (`.chat-message--pending`,
  `.chat-typing-dot`) in the thread itself while waiting for a real
  Compass reply (now several seconds, per the async chat fix above);
  auto-scrolls to the newest message/indicator. Also added real error
  handling — `handleSend` previously had no `try`/`catch` at all, so a
  failed request silently did nothing; now shows an honest inline error
  message (`.chat-message--error`) and always re-enables the input,
  never leaving the panel stuck. Live-verified end-to-end: sent a real
  question, watched the typing indicator for its full ~14s duration,
  received and rendered a genuinely useful, vault-grounded reply.

- fix: **Real conversational agent chat was completely broken in the real
  running app** (every message either silently hung or 500'd) — found
  live while investigating the operator's "chat is still not working"
  report, 2026-08-12. Root cause: `agents_router.py::chat` was a sync
  `def`, so FastAPI scheduled it via `run_in_threadpool` (a worker
  thread); inside that thread, `run_agent_conversation` called
  `asyncio.run(...)` to bridge into the MCP client's async loopback
  call — a **second event loop, in a worker thread, trying to connect
  back into the same single-process server**. That self-connection
  reliably failed with `httpcore.ConnectError: All connection attempts
  failed`, even though the identical MCP client call succeeded instantly
  when run as a standalone script (confirmed via a direct isolated
  test — proved the MCP server itself was fine, the bug was specifically
  in the nested-event-loop self-connection). Separately, and compounding
  it: `agent_orchestration/mcp_client.py`'s loopback URL was hardcoded to
  port `8002` — a workaround an earlier build session left in place for
  a *different*, session-local problem (port 8001 stuck due to an
  orphaned `uvicorn --reload` worker) — restored to this project's real
  documented port, `8001`. **Fix:** made the whole chain genuinely
  async — `agents_router.py::chat` is now `async def` and `await`s
  `run_agent_conversation` directly (no thread pool); `graph.py`'s
  `run_agent_conversation` is now `async def`, using `await
  mcp_client.load_vault_query_tools()` and `await _GRAPH.ainvoke(...)`
  instead of `asyncio.run()`/`.invoke()`; `_execute_tools` (the graph's
  tool-execution node) is now an async node using `await
  tool.ainvoke(...)` instead of its own nested `asyncio.run()`. One
  event loop for the whole request, start to finish — no self-connection
  possible. Live-verified: a real question ("What kinds of notes exist
  in my vault right now?") now returns a real Compass-backed reply in
  ~7 seconds, confirmed both via direct API call and through the actual
  chat UI.

- feat: My Day — added a day-navigator (← Wed, Aug 12 → / "Jump to
  today") to the dashboard, per direct operator request ("I meant to
  have a My Day view but I can have a Calendar or a Slider or something
  on the top where I can move between different days"). Backend:
  `app/business/my_day.py`'s `summary()`/`list_email_items()`/
  `list_calendar_items()` gain an optional `day` parameter — narrows
  results to that single date instead of the full 7-day window when
  provided; `window` in the summary response always reflects the full
  navigable range regardless of `day`, so the frontend can render both
  "which day is selected" and "what range can I navigate within"
  simultaneously. `app/api/my_day_router.py`'s three endpoints accept an
  optional `?day=YYYY-MM-DD` query param, validated (`400`) against the
  current window bounds — a day outside the real navigable range is
  rejected, not silently clamped or ignored. Frontend: `MyDayPage.tsx`
  defaults to today, steps by whole days, disables Previous/Next at the
  window edges, and passes the selected day through to each section's
  drill-down link (`?day=...`). `MyDayEmailsPage.tsx`/
  `MyDayCalendarPage.tsx` now read that `day` search param
  (`useSearchParams`) and pass it through to their own fetch calls,
  re-fetching when it changes — clicking through from a selected day
  shows that day's items, not the whole week's, closing the loop between
  the dashboard and its drill-downs. Live-verified end-to-end: stepping a
  day changes the dashboard counts (Aug 12: 1 email/6 meetings; Aug 11: 6
  emails/2 meetings), the boundary correctly clamps at `Aug 9` with
  Previous disabled, and `/my-day/calendar?day=2026-08-12` shows exactly
  that day's 6 meetings, chronologically sorted.

- fix: My Day — `app/business/my_day.py`'s `list_email_items()`/
  `list_calendar_items()` now sort their results chronologically
  (`items.sort(key=...)` on `received`/`start`) — previously returned in
  vault-scan order, which read as arbitrary/unrelated to time on both the
  Emails and Calendar drill-down pages. `summary()` now also returns a
  `window: {start, end}` field (the same `_compute_window()` value
  already computed on every call, just never surfaced) — the frontend
  (`MyDayPage.tsx`) now displays "Showing Aug 9 – Aug 15" so the active
  rolling-7-day range is actually visible, not just correctly applied
  invisibly. `MyDaySummary` (`features/my-day/client.ts`) widened to
  match. Live-verified: calendar items now return in strict chronological
  order; the date range renders correctly on the real page.

- fix: Agents Map — Section Hub node resized and repositioned
  (`src/frontend/src/features/agents-map/polarLayout.ts`'s `HUB_RADIUS`
  32 → 21; `.hub-node`'s CSS width 11% → 6%, `src/frontend/src/styles/
  agents-map.css`), per direct operator request: the Hub was sitting
  almost exactly on top of the Producer ring (radius 30 vs. the Hub's own
  32), so its own visual disk physically overlapped the entire Producer
  ring band — freeing that space lets Ring 3 (Producer, innermost) be
  used exclusively for agent nodes going forward, and incidentally fixes
  `BUG-004` (a Producer-type agent rendering on top of a neighboring
  Section's Hub) as a direct consequence. Live-verified: Hub visual size
  now 42px (was 77px) at the real canvas scale, placement now 147px from
  center (was 224px), zero DOM-rect overlaps between any agent node and
  any Hub across all 5 real seeded agents. `RING_RADIUS` itself
  (Worker/Expert/Producer) is unchanged — this is a Hub-only adjustment.

- fix: `REQ-SB-08-US-01-T06` (`SPRINT-017`) rebuilt exactly per `ADR-019`
  and live-verified — the **second** Meetings-occurrence dedup/filename-key
  fix for the same finding class, and the one that actually holds up under
  live testing. `src/backend/app/data_access/outlook_com.py`:
  `_resolve_global_appointment_id`/`_PR_GLOBAL_APPOINTMENT_ID_DASL` removed
  (dead code); `list_calendar_events` no longer resolves, returns, or skips
  on any per-occurrence Outlook identity field, reverted to appending every
  successfully-read item; docstring rewritten. `src/backend/app/
  data_access/vault_writer.py`: `meeting_note_filename_stem`/
  `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`
  drop the trailing identifier parameter entirely — the filename/dedup
  suffix is now an 8-hex-char SHA-256 prefix of `f"{subject}|{start}"`
  (full precise `start` timestamp, not any Outlook identity field, not a
  raw slice); `resolve_meeting_note_path` drops to two tiers (new scheme,
  then the legacy `EntryID`-suffix scheme, `ADR-013` point 3 reused
  unmodified) — the `GlobalAppointmentID`-hash middle tier is not carried
  forward; `mark_meeting_processed`'s parameter renamed `global_
  appointment_id` → generic `marker`, now fed the resolved note's own
  filename stem. `src/backend/app/business/meeting_classification.py`:
  `classify_recent_meetings` updated to match — no longer reads or threads
  `event["global_appointment_id"]` anywhere. Live-verified against the
  real Outlook calendar and vault: the real recurring series that
  originally triggered `ESCALATIONS.md` → `ESC-002`/`ESC-012` ("Weekly
  Forecast l Strategic/Major Clients") now produces 6 distinct filename
  suffixes for its 6 real occurrences; zero of the 39 originally-named
  pre-existing Meeting notes touched (confirmed via real `LastWriteTime`
  comparison across all 40 pre-existing files). `ESC-002`/`ESC-012` both
  flipped to `Resolved`. One honestly-flagged, non-blocking live discovery
  — a 40th pre-existing Meeting note (created between sessions by the
  then-still-live old code) plus a genuine mid-session calendar reschedule
  produced one real, bounded, recoverable duplicate note outside the 39
  named notes — recorded in full in `Implementation/Tasks/
  REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md`'s own
  Implementation Log and flagged in `REVIEW-QUEUE.md` for human spot-check.
  `SPRINT-017` closes `Done`.

- docs: `ADR-019` written (`Implementation/Architecture/ADR.md`) — the
  **second** superseding ADR for the Meetings-occurrence dedup/filename key
  in two days. Live verification of `ADR-013`'s own fix
  (`REQ-SB-08-US-01-T06`, `SPRINT-017`) found `AppointmentItem.
  GlobalAppointmentID` has the exact same non-uniqueness defect on this
  Outlook installation that `EntryID` had (`ESCALATIONS.md` → `ESC-012`).
  `ADR-019` supersedes `ADR-013`'s Decision points 1 and 2 (`ADR-013`'s own
  `Status:` updated to `Superseded by ADR-019`, point 3 unmodified and
  reused): the new dedup/filename key is an 8-hex-char SHA-256 hash of
  `subject` + the occurrence's own full, precise start timestamp
  (`list_calendar_events`'s existing `start` field, previously only used
  coarsely as the filename's date component) — a structural uniqueness
  guarantee (two distinct calendar occurrences cannot share an identical
  start moment), not an empirical claim about any Outlook COM property's
  behaviour. `ADR-013`'s own middle `GlobalAppointmentID`-hash fallback
  tier is deliberately dropped (confirmed live that zero real Meeting
  notes were ever created under it); `ADR-013`'s legacy-`EntryID`-path
  coexistence check is reused unmodified — none of the 39 already-captured
  real Meeting notes needs migrating. `architecture.md`'s "Meeting Notes &
  Calendar-Attendee Extraction (REQ-SB-08)" → "Occurrence dedup key" bullet
  rewritten a third time to match. `REQ-SB-08-US-01-T06`'s own task file is
  redesigned in place around `ADR-019` (its prior `ADR-013`-based spec and
  live-verification Implementation Log kept, unedited, as history) —
  `status:` reset `Blocked → Ready`. `ESCALATIONS.md` → `ESC-012` flipped to
  `Resolved` (design-level; `T06` still needs rebuild + live re-verification
  to close operationally), `ESC-002` updated with a pointer to the same
  resolution. `REVIEW-QUEUE.md`'s `REQ-SB-08-US-01-T06`/`SPRINT-017` entry
  updated in place to carry the new review pointer. No code changed yet in
  this pass — this is the architect-stage design correction;
  `REQ-SB-08-US-01-T06` still needs to be rebuilt against this new design.

- feat: `REQ-SB-26-US-01` (Agent Memory, `SPRINT-015`) shipped end-to-end
  and verified live, per `ADR-016`. `src/backend/app/data_access/
  vault_writer.py` gained `load_agent_memory(agent_id)`/
  `append_agent_memory_entries(agent_id, facts)` (new
  `.second-brain/agent_memory.json`, `{agent_id: [{"fact": str,
  "recorded_at": iso8601}, ...]}`, mirroring `load_agent_history`/
  `append_agent_history_entry`'s exact shape). `app/business/
  agent_orchestration/state.py`'s `AgentConversationState` gained
  additive `memory: list[dict]`/`extracted_facts: list[str]` fields.
  `app/business/agent_orchestration/graph.py`'s compiled graph gained two
  new nodes on `REQ-SB-25-US-01`'s same graph — `retrieve_memory` (read
  path, folds stored facts into the message list as a second
  `SystemMessage` before `call_model`) and `extract_memory` (write path,
  reuses the already-resolved model for one additional, narrowly-scoped
  completion after a final reply, honestly returning no facts rather than
  inventing one) — composed around the real `call_model`⇄`execute_tools`
  tool-calling loop, not a blind replacement of it (a live-discovered
  correction vs. `T03`'s own literal code sample — see `T03`'s own
  Implementation Log and `REVIEW-QUEUE.md`). `run_agent_conversation`
  gained an additive `memory` parameter and an `"extracted_facts"` key on
  its success-path return (never present on the `{"error": ...}` path).
  `app/api/agents_router.py::chat`'s no-trigger-phrase-match branch now
  loads memory once before calling `run_agent_conversation` and persists
  any `extracted_facts` afterward. Verified live end-to-end against the
  real backend/vault/Compass Provider, all 4 locked ACs: a fact stated in
  one conversation ("My favourite customer is Acme Corp") correctly
  recalled in a later, separate conversation (isolated from
  `REQ-SB-25`'s own history-replay mechanism by clearing that agent's
  history entry beforehand); a second, unrelated agent showed no
  awareness of it (`agent_memory.json` confirmed no cross-agent entry);
  an agent asked to recall something never actually shared honestly said
  it didn't know, with no fabricated entry written; and the fact
  survived a full backend process restart. Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-016`.
- feat: `REQ-SB-27-US-01` (Skills Repository — registration and
  per-agent access, plumbing only, `SPRINT-015`) shipped end-to-end and
  verified live, per `ADR-015`. New `app/business/skill_tools.py` (a
  sibling to `vault_query_tools.py`) holds a small, literal `SKILLS`
  catalog (`id`/`name`/`description`) and one illustrative,
  `@mcp.tool()`-decorated stub skill (`diagram_understanding`) registered
  on the same shared `FastMCP` instance `app/api/mcp_server.py` exposes
  for `vault_query_tools.py` — its body unconditionally returns an honest
  "not yet available" response, never a fabricated result. New `app/
  data_access/vault_writer.py` primitives `load_skills_state()`/
  `save_skills_state(state)` (new `.second-brain/agent_skills.json`,
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}`, mirroring
  `load_sections_state`/`save_sections_state`). New `app/business/
  skill_registry.py` (mirrors `section_registry.py`/`provider_registry.py`'s
  `ADR-014` shape one concept over): `list_skills`, `list_agent_skills`,
  `grant_skill_access`, `revoke_skill_access`, `has_skill_access`,
  `invoke_skill` — deliberately **no self-healing default assignment**,
  an agent gets skill access only via an explicit grant. New `app/api/
  skills_router.py` (`GET /skills`, `GET /agents/{id}/skills`, `POST`/
  `DELETE /agents/{id}/skills/{skill_id}`, `POST .../invoke`), registered
  in `app/main.py` additively. Verified live end-to-end against the real
  backend, all 5 locked ACs: `GET /skills` returns the registered
  catalog; granting an agent access is reflected in its own skills list;
  invoking for an ungranted agent returns a `403` refusal; invoking for a
  granted agent with no real handler yet returns an honest `200`
  "not yet available" body, distinct in both status and shape from the
  refusal; revoking access removes it and the refusal shape re-applies.
  This story is plumbing only — the first real skill's implementation and
  any UI are explicit follow-on work, per its own Non-Goals. Full
  reasoning: `Implementation/Architecture/ADR.md` → `ADR-015`.
- fix: `BUG-002` closed (`BUGFIX-02-US-01`, `SPRINT-016`) — "Agents Map:
  sections with 4+ agents visually spill into neighboring sections."
  Ported the already-approved, already-live-browser-verified Option D
  (semantic zoom / drill-down) design from `html-prototype/agents-map.html`/
  `agents-map.js` into the real React app. `src/frontend/src/features/
  agents-map/polarLayout.ts` gained `DRILLDOWN_AGENT_RADIUS = 40`;
  `layoutAgents.ts` gained a new sibling `layoutSectionDrilldown()`
  (full-360° evenly-spaced angle per agent), deliberately not a branch
  inside the existing `layoutAgents()`/`SECTION_ARC_SPAN_DEG` overview fan-
  out — both left unchanged. `AgentNode.tsx` gained optional `compact`
  (applies the already-shipped-but-unused `.agent-node--compact` CSS
  modifier — every overview agent now always renders as a small, unlabeled
  dot, hover/focus reveals its label, never a density threshold) and
  `radiusOverride` props. `SectionHub.tsx` gained optional `onActivate`
  (renders a real `<button>` at the overview call site; omitted at the
  drill-down's own call site, which stays the original non-interactive
  `<div>`) and `radiusOverride` (lets the drill-down's own Hub render at
  the canvas's literal center via `radius=0`) props. New
  `SectionDrilldown.tsx` renders one Section's own full-360°, fully-labeled
  "Agents Tree" — centered Hub, that Section's agents, Hub→agent cluster-
  lines only, the established `.empty-state` pattern for a 0-agent Section,
  and a "Back to Agents Map" control. `agents-map.css` gained the
  prototype's own `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`/`.explore-drilldown .hub-node` rules plus
  `@keyframes fadeIn`, ported verbatim (class names unchanged).
  `AgentsMapCanvas.tsx` wires it all together: local `activeSectionId`/
  `zoomTargetSectionId` `useState` (not lifted), every overview `AgentNode`
  now renders `compact`, every `SectionHub` is a clickable button that
  plays the zoom-out CSS transition then mounts that Section's
  `SectionDrilldown` on `transitionend`; a `<>...</>` fragment return keeps
  `AgentsMapPage.tsx`'s existing call site source-compatible, zero edit
  needed there. Verified live end-to-end via headless-Chrome-over-CDP
  against the real running app (real seed data: "Productivity" Section, 4
  agents — the real assignment drifted from `BUG-002`'s original
  "Technical, 5 agents" filing, still today's real 4+-agents-in-one-Section
  repro condition): compact dots render with zero real visual (bounding-
  box) overlap against any neighboring Hub/agent/section-title; hover/
  focus reveals a label without moving the dot; Hub-click zooms into a
  fully-labeled drill-down with a correctly-smaller (8% vs 10% width) Hub
  node; Back restores the overview unchanged; the empty-Section drill-down
  and the overview agent-dot's existing click-to-detail-panel behavior are
  both unregressed. Full evidence: `Implementation/Tasks/BUGFIX-02-US-01-
  T06-agents-map-canvas-drilldown-wiring.md`'s Implementation Log.
- feat: `REQ-SB-25-US-01-T01` (`SPRINT-014`) — `src/backend/requirements.txt`
  gains `langgraph>=1,<2`, `langchain-openai`, `mcp`,
  `langchain-mcp-adapters` (`ADR-015`). Real `pip install` against the real
  `.venv` confirmed clean on this Windows/`cp314` host — resolved versions
  `langgraph==1.2.11`, `langchain-openai==1.4.3`, `mcp==1.29.0`,
  `langchain-mcp-adapters==0.3.2`; every transitive compiled dependency
  (`pydantic-core`, `cryptography`, `cffi`, `rpds-py`, `orjson`, `tiktoken`,
  and others) resolved a prebuilt wheel — `ADR-015`'s own honestly-flagged
  wheel-availability risk is now confirmed clear, not just hoped for.

- feat: `REQ-SB-25-US-01-T02` (`SPRINT-014`) — new `app/business/
  agent_orchestration/` package (first sub-package under `business/`,
  `ADR-015`), `state.py`: `AgentConversationState` TypedDict (the
  LangGraph conversation graph's state) and `history_entries_to_messages`
  (maps `agent_communication_history.json`'s existing entry shape into the
  graph's replayed LangChain message list — `"chat_user"`→`HumanMessage`,
  `"chat_agent"`→`AIMessage`, `"run_event"` excluded, one `SystemMessage`
  prepended from the agent's own name, per `architecture.md`'s 2026-08-12
  Addendum).

- feat: `REQ-SB-25-US-01-T03` (`SPRINT-014`) — new `agent_orchestration/
  model_factory.py`: `resolve_agent_model(agent_id)` resolves a per-agent
  `langchain_openai.ChatOpenAI` from `provider_registry`, returning an
  explicit `None` — never a constructed-then-broken model — before any
  model is built when the agent's Provider has no real client, mirroring
  `agents_router.py::_invoke_action`'s existing honest-unavailability
  funnel-gate one layer over for conversational replies (`ADR-015` point
  3, Scenario 4).

- feat: `REQ-SB-25-US-01-T04` (`SPRINT-014`) — new `app/business/
  vault_query_tools.py`: thin pass-through business-layer wrappers over
  already-existing read-only `vault_writer` primitives
  (`list_known_customers`/`list_known_kinds`/`list_known_partners`/
  `list_notes_in_kind_folder`, the last projecting `Path`→`str` for JSON
  serializability) — the tool *implementations* the new shared MCP server
  (`T05`) registers.

- feat: `REQ-SB-25-US-01-T05` (`SPRINT-014`) — new `app/api/mcp_server.py`:
  Second Brain's own shared MCP server (`ADR-015` points 7-11), an `mcp`
  SDK `FastMCP` instance registering `vault_query_tools.py`'s four
  functions as `@mcp.tool()`s, mounted at `/mcp` in `main.py`
  (`streamable_http_app()`, Streamable HTTP transport) alongside the six
  existing `include_router` calls. Two real, live-discovered corrections
  beyond a naive mount (see the task's own Implementation Log for full
  detail): `FastMCP(..., streamable_http_path="/")` avoids an unreachable
  `/mcp/mcp` double-mount nesting; `main.py`'s `lifespan` now explicitly
  composes `mcp_server.session_manager.run()` alongside the existing
  `capture_scheduler.lifespan` via `AsyncExitStack`, since a `Mount()`-ed
  sub-app's own lifespan is not invoked automatically by FastAPI/Starlette
  — without it, every real MCP request 500'd with "Task group is not
  initialized." Live-verified: `GET /mcp` now returns a correct `406 Not
  Acceptable` (protocol-level content-negotiation rejection of a bare GET,
  not a 404/500), and all six pre-existing REST endpoints are unaffected.

- feat: `REQ-SB-25-US-01-T06` (`SPRINT-014`) — new `agent_orchestration/
  mcp_client.py`: an async `load_vault_query_tools()` wrapping
  `langchain_mcp_adapters.client.MultiServerMCPClient`, pointed at Second
  Brain's own mounted `/mcp` endpoint over a real loopback HTTP call — the
  in-app agent is simply another MCP client, indistinguishable in
  principle from Hermes (`ADR-015` point 8); never re-wraps
  `vault_query_tools.py`'s functions directly. Live-verified: a real
  loopback round-trip returned all 4 of `T05`'s registered tools.

- feat: `REQ-SB-25-US-01-T07` (`SPRINT-014`) — new `agent_orchestration/
  graph.py`: a compiled `langgraph.graph.StateGraph` exposing
  `run_agent_conversation(agent_id, message, history) -> {"reply": str} |
  {"error": str}`, re-exported as `agent_orchestration`'s one public
  symbol (`__init__.py`). Two model-call/tool-execution nodes with one
  conditional edge (`call_model` ↔ `execute_tools`) — not literally the
  originally-sketched single node — since a real Compass/GPT-5 call
  genuinely chose to call a bound tool for an ordinary vault-query
  question, and the tool result has to actually be executed and fed back
  for a real, non-empty reply (found + fixed live, see the task's own
  Implementation Log); no LangGraph checkpointer, stateless per call
  (`ADR-015` point 6). Also fixed live in `agent_orchestration/
  model_factory.py` (`T03`): `ChatOpenAI`'s `base_url` needs
  `provider["endpoint"]` with its `/chat/completions` suffix stripped
  (the OpenAI SDK appends it itself) — `provider_registry`'s own stored
  shape is unchanged. Live-verified: a real vault-query question now
  returns a real, tool-backed Compass reply; a Provider with no real
  client short-circuits before the graph is ever invoked, returning the
  exact `_invoke_action`-matching unavailability message.

- feat: `REQ-SB-25-US-01-T08` (`SPRINT-014`, story `REQ-SB-25-US-01`
  complete) — `agents_router.py::chat`'s no-trigger-phrase-match branch
  now calls `agent_orchestration.run_agent_conversation(agent_id,
  body.message, history_before_this_message)` in place of the old static
  canned `fallback_reply`; the trigger-phrase-match branch and every
  other endpoint are byte-for-byte unchanged (`ADR-015` point 5). Agent
  chat is now genuinely conversational, Provider-backed, and
  vault-tool-aware for any message that isn't a recognized trigger
  phrase, with the existing keyword-match action fast path fully
  preserved. **All 5 locked ACs verified live** against the real backend/
  real Compass/real vault: a real, relevant, tool-backed reply for an
  ordinary question (`AC-01`); the fast path unchanged, no LLM call
  (`AC-02`); a second turn correctly recalling the first turn's own
  content (`AC-03`, after fixing a real round-count bug in `graph.py` —
  see `T08`'s own Implementation Log); honest unavailability for a
  no-real-client Provider, no silent fallback (`AC-04`); and an honest,
  real connection-failure message, recorded as a normal `chat_agent`
  history entry (`AC-05`, verified by temporarily repointing the real
  `"compass"` Provider's own endpoint at a dead port, then restoring it —
  a newly created Provider can never reach a real call at all under
  `provider_registry`'s own existing `"compass"`-only availability gate,
  see `MEMORY.md`). `REQ-SB-25-US-01` and `SPRINT-014` are `Done`.

- fix (partial, blocked): `REQ-SB-08-US-01-T06` (`SPRINT-017`) — replaces
  Outlook `EntryID` with a SHA-256 hash of `AppointmentItem.
  GlobalAppointmentID` as the Meeting-occurrence dedup/filename key, per
  `ADR-013`, with a legacy-`EntryID`-path coexistence fallback so none of
  the 39 already-captured real Meeting notes needed migrating or renaming.
  `app/data_access/outlook_com.py` gained `_resolve_global_appointment_id`
  (native COM property + `PropertyAccessor`/DASL fallback, never falls
  back to `EntryID`) and a `global_appointment_id` field on
  `list_calendar_events`'s per-event results; `app/data_access/
  vault_writer.py`'s meeting-note filename/dedup functions re-parametrized
  from `entry_id` to `global_appointment_id` (hashed, not sliced), plus a
  new `resolve_meeting_note_path` (new-scheme-then-legacy-path lookup,
  replacing the orchestrator's old two-call `meeting_note_path()`/
  `meeting_note_exists()` pattern); `app/business/meeting_classification.py`
  threads `global_appointment_id` through accordingly. **Live verification
  against the real Outlook calendar/vault found `ADR-013`'s own core
  premise — `GlobalAppointmentID` is unique per occurrence — is itself
  false on this Outlook installation**, for the exact real recurring
  series that originally motivated this fix (`ESC-002`): the native COM
  property returns an identical value across all 3 real occurrences of two
  separate recurring series, and its documented DASL fallback errors on
  every occurrence. The coexistence/no-duplicate mechanism and the hash-
  suffix logic are independently verified correct and non-regressive (39
  real notes, zero renamed/altered/duplicated), but the task's own
  regression check re-verifying distinct dedup keys for the trigger series
  fails. `REQ-SB-08-US-01-T06` is left `status: Blocked`, not `Done`;
  `SPRINT-017` stays `In Progress`. See `ESCALATIONS.md` → `ESC-012` (new)
  and `ESC-002`'s 2026-08-12 update; `REVIEW-QUEUE.md` carries the human
  decision point needed to resume.
- design: `BUG-002` fix ported into the canonical `html-prototype/
  agents-map.html` (Option D, semantic zoom / drill-down, plus both
  operator-approved refinements — operator approved the design 2026-08-12;
  see `REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry, updated in
  place, for the full history). Replaces the screen's old fixed-position-
  only rendering with the approved fix: every agent now always renders as a
  small, unlabeled `.agent-node--compact` dot at the overview level (hover/
  focus reveals its label); each Section's Hub is now a clickable button
  that zooms into that Section's own dedicated "Agents Tree" drill-down view
  (agents there spread across the full 360°, always fully labeled, with a
  "Back to Agents Map" button) — reusing `.explore-zoom-overview`/
  `.zooming-out`/`.explore-drilldown`/`.explore-drilldown .hub-node` verbatim
  from `agents-map-exploration.html`'s own additive `styles.css` section, no
  new CSS needed. A replayable overview entrance animation (flat row → hold
  → glide into real circular positions, Knowledge Base growing in at center)
  plays once on load and again on state-switch, via each state's own new
  "Replay intro" button. New page-scoped script `html-prototype/
  agents-map.js` (parallel to `app.js`) wires both. A new fourth state,
  "Dense section (BUG-002 fix demo)", was added to `agents-map.html`
  mirroring BUG-002's own literal original repro (all 5 real agents in one
  Section) — neither of the prior two agents-having states ever actually
  reached the bug's own 4-plus-agents-in-one-Section trigger condition, so
  this is the first state in the prototype to visibly exercise the fix.
  Hub coloring in the "Populated" state is now neutral (was per-Type), a
  called-out consequence of porting Option D's own approved rendering
  uniformly, resolving an earlier REQ-SB-18-pass debt item as a side effect.
  `html-prototype/agents-map-exploration.html` is untouched (kept as
  historical comparison, no longer the design-of-record for BUG-002 —
  `agents-map.html` is); `html-prototype/index.html`'s catalog card and
  `styles.css`'s BUG-002 CSS-section header comment updated to match. Always
  flagged (designer never auto-advances) — fresh `REVIEW-QUEUE.md` sign-off
  needed on this canonical port before `/triage` runs.
- design: Agents Map layout exploration (`BUG-002`) sign-off pass — the
  operator picked **Option D (semantic zoom / drill-down)** as the accepted
  direction (Options A/B/C stay as comparison history only); two refinements
  built directly inside the existing `html-prototype/agents-map-
  exploration.html`/`.js`: (1) rebalanced the drill-down "Agents Tree"
  Hub's size against the agent nodes it groups (`.explore-drilldown
  .hub-node` now 8% width vs the agent nodes' 10%, down from 11% before —
  confirmed at both today's scale and the stress dataset), scoped CSS only,
  no JS change; (2) a new, replayable overview entrance animation
  (`playIntro()`/`wireIntroDemo()`) — agents render first in a flat row,
  hold ~0.9s, then transition into their real circular positions while the
  Knowledge Base grows/fades in at center (new `@keyframes kbGrowIn`,
  `.agent-node--intro-move`, `.agents-intro-fade`), plain CSS
  transitions/keyframes only, no animation library. Page default tab and
  intro copy updated to reflect Option D as accepted; `html-prototype/
  index.html`'s catalog card updated to match. Still exploration-only — no
  story/task/sprint/requirement file touched, both refinements flagged for
  human browser sign-off before this becomes a real `BUGFIX-NN-US-01` fix
  story (`REVIEW-QUEUE.md`'s existing BUG-002 entry updated in place, not
  duplicated).
- design: Agents Map layout exploration for `BUG-002` (sections with 4+
  agents visually spill into neighboring sections, labels collide) — new
  `html-prototype/agents-map-exploration.html` + `agents-map-exploration.js`
  compare 4 genuinely different candidate fixes (dynamic angular budget;
  multi-ring wedge expansion; communication-affinity clustering grounded in
  REQ-SB-20's real keyword data; semantic zoom/drill-down, the operator's
  own suggested direction), each at today's real scale and a synthetic
  13-agent/6-section stress case, computed client-side from real
  `polarLayout.ts`-matching constants rather than hand-placed. Exploratory
  only — no direction picked, no story/task/sprint/requirement file touched.
  New additive CSS in `html-prototype/styles.css`: `.affinity-line`/
  `.affinity-line.active`, `.explore-zoom-overview`/`.zooming-out`/
  `.explore-drilldown`. `html-prototype/index.html` gained a clearly-marked
  catalog pointer to the new file (not added to the main sidebar nav, since
  it isn't a real application screen). Flagged to `REVIEW-QUEUE.md` for
  human sign-off on a direction before this becomes a real `BUGFIX-NN-US-01`
  fix story via `/triage`.
- docs: initial scaffold created
- feat: backend layered structure (`app/api`, `app/business`, `app/data_access`)
  with a `/health` endpoint, `.venv` on Python 3.14, and a passing pytest suite
- feat: frontend scaffolded via `create-vite` (React + TypeScript) under
  `src/frontend`
- chore: portable Node.js v24.19.0 LTS toolchain added at `tools/node/`
  (git-ignored) with a `tools/use-node.ps1` PATH helper, since no admin rights
  are available to install Node system-wide
- docs: `architecture.md` and `ADR.md` updated — Python 3.14 target
  (ADR-001), portable Node.js toolchain (ADR-002), layered backend
  architecture (ADR-003)
- docs: `Documentation/PRD.md` populated with real MVP/P1/P2 requirements
  (REQ-SB-01..06), replacing the placeholder — seeded by classifying all 76
  entries in agentic-map's `REQUIREMENTS.md` against Second Brain's actual
  scope; full reasoning in
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`;
  `BACKLOG.md` indexed accordingly
- feat: email-classification POC (`POST /poc/classify-emails`) — fetches
  recent mail via a ported `outlook_com` COM-automation data access
  (`app/data_access/outlook_com.py`, from agentic-map's ADR-0018 precedent),
  classifies each by customer via a Compass API client
  (`app/data_access/compass_client.py`), and files the result as a note under
  `Customers/<Customer>/Emails/` in the vault (`app/data_access/
  vault_writer.py`), orchestrated by `app/business/email_classification.py`.
  Verified live against a real inbox (3 emails, correctly split across two
  known customers and one low-confidence `Unsorted` bucket)
- chore: `src/backend/.env`/`.env.example` added (Compass credentials, vault
  path) — `.env` git-ignored, never committed
- feat: extensible item-kind classification — Compass now returns a `kind`
  (e.g. `Emails`, `Files`, `Notifications`) alongside `customer`, read
  dynamically from existing vault subfolders (`vault_writer.list_known_kinds`)
  the same way customers are; new kinds need no code change. Real meeting
  invites are excluded before ever reaching Compass, via Outlook's
  `MessageClass` (`IPM.Schedule.Meeting.*`)
- feat: attachment extraction — email/file-share attachments are saved into
  `attachments/<note>/` next to their note and linked from the note body
  (ported from agentic-map's save-to-temp/read/delete technique, 20MB cap,
  oversized files recorded but not written)
- fix: filenames now include a slice of the Outlook EntryID — two same-
  subject, same-day items (e.g. a duplicate share notification) were
  colliding on `date-subject.md` and the second silently overwrote the
  first; found live (`ADNOC_Azure_MACC_Review` shared twice 2026-08-07),
  fixed, and the lost note was recovered by re-fetching both EntryIDs
  directly from Outlook and reprocessing
- feat: thread linking — notes from the same Outlook conversation
  (`ConversationID`) now get a `## Related Emails` section with wikilinks to
  prior notes in the same thread (`vault_writer.find_related_note_stems` /
  `record_conversation_note`, backed by `.second-brain/conversation_index.json`);
  Obsidian computes the reverse links automatically
- fix: inline signature/body images (e.g. a logo pasted into a signature)
  were being extracted as real attachments — Outlook has no reliable COM
  flag for this (agentic-map's own outlook_com.py docstring notes the same
  limitation and deliberately keeps them for its signature-mining use case);
  Second Brain's use case doesn't need that noise, so `_is_inline_attachment`
  filters on `PR_ATTACH_CONTENT_ID` plus an `imageNNN.ext` filename fallback
- feat: hierarchical Obsidian tags (`customer/<slug>`, `kind/<slug>`) added
  to every note's frontmatter (`vault_writer.build_tags`), so notes stay
  findable by customer/kind independent of which folder they physically sit
  in — surfaces in Obsidian's tag pane/search even before a note is
  physically moved
- chore: `POST /poc/backfill-tags` — one-off, idempotent migration that
  added `tags` to all 35 pre-existing notes via a surgical line-insert
  (`vault_writer.insert_tags_line`), not a full frontmatter rewrite, so
  every other field's exact formatting (e.g. unquoted numbers) was left
  untouched
- docs: `Documentation/References/beyond-the-second-brain-methodology.md`
  added — condensed reference summary of *Beyond the Second Brain* (Mo
  Elkholy), supplied by the operator as a standing architecture reference.
  Flags real tensions with the email-classification POC (folder-heavy
  structure vs. link-based structure, no AI-output review gate vs. the
  book's AI Staging principle, non-atomic notes) for operator decision
- refactor: flattened `Work/Customers/<Customer>/<Kind>/` to `Work/<Kind>/`
  — customer is no longer a folder level, only frontmatter + a
  `customer/<slug>` tag, per the book's "folders are the enemy of
  thinking" principle (`vault_writer.list_known_customers` now reads
  frontmatter instead of scanning folder names; `POST /poc/
  flatten-customer-folders` migrated all 35 existing notes + their
  attachments with zero collisions). This also resolves the earlier
  Unsorted→Affiliate reorg question — reclassifying a note's customer is
  now a tag edit, not a file move
- fix: inline signature/logo images that didn't match the `imageNNN.ext`
  pattern (a recurring `thumbnail_emailsignature_new-02_*.jpg`) were still
  being saved as real attachments — `_is_inline_attachment` now also
  matches filenames containing signature/thumbnail/logo keywords.
  Retroactively swept 13 signature-file instances and 52 pre-fix
  `imageNNN.ext` files (captured before the original inline-image filter
  existed) from already-written notes, including their link lines and any
  now-empty attachment folders
- docs: formalized the book's principles across the three-way knowledge
  split — `ADR-004` (customer-as-tag decision, in `Implementation/
  Architecture/ADR.md`), `architecture.md`'s `## Data Model` (the vault's
  actual current structure + explicitly what's not yet adopted), and a
  provisional (non-sprint-retro) entry in `Implementation/Learnings.md`,
  clearly marked as deviating from that file's normal retro-only protocol
  at the operator's explicit request
- docs: `Documentation/PRD.md`/`BACKLOG.md` — five new P1 requirements
  (REQ-SB-07..11): Scheduled Recurring Agent Capture, Meetings Capture
  Pipeline, To-Do Task Capture Pipeline, People Living Documents, Agent
  Activity & Error Observability. Hermes's own agent-type/section taxonomy
  and multi-LLM-provider plan recorded as context in `MEMORY.md`, not new
  Second Brain requirements — Hermes stays a dependency this project
  doesn't build, per the existing constraint
- feat: last-successful-capture-run persistence
  (`REQ-SB-07-US-01-T01`) — `vault_writer.record_capture_run_completed`/
  `load_last_capture_run` add a `.second-brain/last_capture_run.json`
  convention (`{"finished_at": "<ISO-8601 UTC>"}`), mirroring the existing
  `processed_email_ids.json`/`conversation_index.json` state-file pattern;
  `load_last_capture_run` returns `None` until the first run completes.
  Not yet called from anywhere — this is the persistence primitive T02–T04
  build the scheduler on top of
- feat: `run_capture_and_record_completion` (`REQ-SB-07-US-01-T02`) —
  thin orchestration entry point in `app/business/email_classification.py`
  that calls the existing `classify_recent_emails` unchanged, then records
  completion via `vault_writer.record_capture_run_completed()`
  unconditionally, even when no new emails were found; the single call the
  future `app/scheduling/` layer (T03/T04) makes per capture run. The
  manual `POST /poc/classify-emails` endpoint keeps calling
  `classify_recent_emails` directly and is untouched. Verified live against
  a real Outlook/Compass/vault session
- docs: `Documentation/PRD.md`/`BACKLOG.md` — two new P1 requirements
  (REQ-SB-12, REQ-SB-13) capturing the operator's UI vision: a burger-menu
  app shell with an "Agents Map" default page (Knowledge Base at the center,
  agents arranged around it, color-coded by type) and a "My Day" dashboard
  (REQ-SB-12), plus an embedded in-app agent chat and communication-history
  panel (REQ-SB-13) — written so `/design` has requirement IDs to scope
  against, per `.claude/agents/designer.md`'s "bare invocation not
  supported" rule
- feat: new `app/scheduling/` package (`REQ-SB-07-US-01-T03`, ADR-005 point
  5) — `capture_scheduler.run_capture_if_idle()` wraps
  `email_classification.run_capture_and_record_completion` in a module-level
  `asyncio.Lock` non-blocking concurrency guard, so a trigger arriving while
  a capture run is already in progress skips immediately (logged) rather
  than queuing or overlapping. `app/scheduling/` imports only from
  `app/business/`, never `app/data_access/` directly. Not yet wired to any
  trigger source (app-start / hourly interval — T04's scope). Verified live:
  a second, overlapping call returned in under 1ms while the first call's
  real Outlook/Compass/vault run (~20s) completed uninterrupted, and
  `.second-brain/last_capture_run.json` recorded exactly one completion, not
  two
- design: first `html-prototype/` screens (`/design` against REQ-SB-12,
  REQ-SB-13) — `agents-map.html` (default/home page: Knowledge Base node at
  the center, agent nodes arranged and color-coded by type
  Worker/Producer/Expert via new `--agent-color-<type>` tokens, so a future
  type is a new color, never a layout change), `my-day.html` plus its four
  drill-down pages (`my-day-emails.html`, `my-day-calendar.html`,
  `my-day-todo.html`, `my-day-reads.html`), and `settings.html`. Clicking an
  agent node opens a right-side `.side-panel` overlay (REQ-SB-13, not a page
  nav) with that agent's settings, available actions, an embedded
  `.chat-thread` demo chat, and a `.log-list` communication history — one
  panel per agent, grounded in existing requirements (REQ-SB-03/07/08/09/10).
  New reusable `styles.css` patterns: the collapsible burger sidebar
  (`.sidebar-header`/`.burger-btn`/`.app-shell.sidebar-collapsed`), the
  `.state-switcher` buildable-state demo control (used on every new screen to
  show empty/populated/error states in one file), `.item-list`/`.item-row`
  (shared by all four My Day drill-downs), and CSS-only motion (KB pulse
  glow, staggered agent-node fade-in, node hover-scale, sidebar collapse
  transition, sliding side panel). New shared `html-prototype/app.js` for the
  sidebar toggle, state switcher, and agent-panel/chat-demo interactions
  (no framework, no backend calls). `index.html` updated from the "no
  screens yet" placeholder to a catalog of the new screens. Flagged to
  `REVIEW-QUEUE.md` for mandatory human browser sign-off before `/spec`
  reconciles stories against it — never marked "clear," per
  `.claude/agents/designer.md`
- feat: APScheduler wired into FastAPI's `lifespan`
  (`REQ-SB-07-US-01-T04`, ADR-005 points 1–2) — completes REQ-SB-07 end to
  end. `capture_scheduler.build_scheduler()` registers one `AsyncIOScheduler`
  job (`IntervalTrigger(hours=1)`, `coalesce=True`, `misfire_grace_time=None`,
  `max_instances=1`) against `run_capture_if_idle`; `capture_scheduler.
  lifespan(app)` starts the scheduler, fires one unconditional
  `run_capture_if_idle()` call on every app start/restart regardless of how
  recently the previous run finished, then shuts the scheduler down cleanly
  on exit. `app/main.py` passes `lifespan=lifespan` into the `FastAPI(...)`
  constructor. `requirements.txt` gains `apscheduler>=3.10`. Verified live:
  job registration matched ADR-005 verbatim; two consecutive server
  starts/restarts each fired an immediate capture run
  (`.second-brain/last_capture_run.json`'s `finished_at` updated both times,
  the second within ~90s of the first, proving the app-start trigger is
  unconditional). This closes `REQ-SB-07-US-01` — all five ACs now
  exercised end-to-end by a running process
- chore: **SPRINT-001 Done** (2026-08-10) — first sprint completed in this
  project, first `/spec → /plan-tasks → /plan-sprints → /implement-sprint`
  pipeline run end to end. REQ-SB-07 closed. Sizing estimate (~4 tasks, S)
  matched actual exactly. Retrospective drafted in the sprint file, flagged
  for human harvest into `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- design: `html-prototype/` revision pass (round 2, still pre-approval) on the
  REQ-SB-12/REQ-SB-13 screens, after operator browser review of round 1.
  Two changes: (1) **light theme, green accent** — `styles.css` `:root` color
  tokens swapped from dark/blue-accent to white/near-white surfaces with a
  green `--color-accent` (`#15803d`); `--color-success/-warning/-danger`
  darkened for legibility on white (the dark-theme pastel values would fail
  contrast against it); new `--color-on-accent` token replaces the two
  places that hardcoded `#0f1115` as text-on-accent-background
  (`.btn-primary`, `.chat-message--user`); `.nav-item.active` now uses the
  accent explicitly (green text/wash) instead of a neutral highlight; added
  a generic `:focus-visible` outline. Cascades to every screen from this one
  token-level edit — no screen had a hardcoded color, so no per-screen
  markup changed. Agent-type colors (`--agent-color-worker/producer/expert`)
  were deliberately moved off the green family (now blue/violet/pink) so
  they stay visually distinct from the new brand accent. (2) **Agents Map
  rebuilt as a wheel** — replaced the single ring of individually
  KB-spoked agent nodes with a pie-wedge wheel: 3 sections grouped from the
  same 5 agents established in round 1 (Capture/Worker: Email+Meeting+To-Do
  Capture; People/Producer: People Notes; Q&A/Expert: Vault Q&A), each with
  a new dashed, non-clickable `.hub-node` at the wheel's rim that is the
  only thing connecting inward to the KB (topology: KB → Hub →
  agents-in-section; agents within a section connect to each other, not
  each individually back to the KB). The Knowledge Base itself is now a
  small neuron-mesh "brain" (`.kb-brain-svg`/`.kb-neuron` — SVG circles +
  connecting lines with a staggered pulse) instead of a plain labeled
  circle. `.agents-map-canvas` is now forced square via `aspect-ratio` so
  the wheel renders as a true circle instead of the ellipse the earlier
  non-square box stretched it into. REQ-SB-13's per-agent click → side-panel
  behavior (settings/actions/embedded chat/communication history) is
  unchanged — only the map's visual structure and the color theme moved
  this round. Every changed screen's breadcrumb comment updated to record
  this revision; `REVIEW-QUEUE.md`'s existing (still-open) entry amended in
  place to describe what's now on disk, rather than left stale. Still
  flagged for mandatory human browser sign-off before `/spec` — never
  marked "clear"
- docs: Customer structured-data schema resolved
  (`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`) — Customer hub
  notes, atomic Pipeline/Agreement notes, and one-note-per-snapshot Azure
  Consumption tracking, all following `ADR-004`'s kind-folder/customer-tag
  pattern. Reverses the earlier port-classification "Drop" on agentic-map's
  REQ-079/080/081 now that real captured data confirms the same Azure
  MACC/consumption domain (see `MEMORY.md`). Structure only — no
  ingestion/agent code yet
- design: `html-prototype/agents-map.html` revision pass (round 3, still
  pre-approval), after operator browser review of round 2 found the
  wedge/hub structure wrong (read as one Hub per section near the KB —
  backwards). Rebuilt as a true polar/radial grid, implemented close to the
  operator's exact spec: **angular axis = sections** (same 3 as round 2:
  Capture/People/Q&A) — now purely a virtual boundary, a faint dashed
  `.section-boundary` guide line at each edge, round 2's filled
  `.wedge-fill` removed entirely; **radial axis = 3 concentric rings,
  global across every section, one per agent type** (`.ring-circle` at a
  fixed radius each) — Worker outermost, Expert middle, Producer innermost
  (closest to the KB) — every section's angular span is cut through by all
  3 rings, rings are not per-section. Each `.hub-node` now sits at the
  wheel's outer rim (the `.boundary-circle`'s radius), not near the KB —
  exactly one `.spoke-line` per Hub runs inward to the KB (the section's
  single KB-facing connector); agents (placed at their type's ring, within
  their section's angular span) connect to each other and to their Hub via
  `.cluster-line`, never individually to the KB. Added a 12-line faint
  `.radar-spoke` background grid (renders even in the first-run/empty
  state — ambient chrome, not a configured entity) plus `.ring-label`s
  (Producer/Expert/Worker) and `.section-title`s (Capture/People/Knowledge
  Q&A — HTML labels outside the outer boundary at each section's angular
  midpoint, larger/letter-spaced typography with a type-colored accent
  bar). Knowledge Base rebuilt denser: 14 neurons (was 8, varied
  size/opacity for depth), ~26 crossing synapse lines (was a simple
  ring+spokes), two traveling pulse dots via SVG `animateMotion` along
  synapse paths, plus a static soft outer glow (CSS `drop-shadow`) layered
  under the existing pulsing halo. General visual-polish pass: bigger
  canvas via a new padded `.agents-map-stage` wrapper (reserves room for
  the outside labels so nothing clips), soft ambient shadow under the whole
  wheel, per-node glow/shadow keyed to agent-type color, hover now lifts
  (translateY, not just scale). Documented — not instantiated, still only
  ~5 real agents — a scale-to-~100-agents pattern in both the file's
  breadcrumb and `styles.css`: `.agent-node--compact` (unlabeled dot,
  label/type revealed on hover/focus only) and `.map-overflow-marker`
  ("+N") for an overcrowded ring/section arc segment, both defined and
  ready to apply. REQ-SB-13's per-agent click → side-panel behavior
  (settings/actions/embedded chat/communication history) is byte-for-byte
  unchanged — only the map's own structure/visuals were in scope this
  round; the round-2 light/green theme is unchanged. `REVIEW-QUEUE.md`'s
  existing (still-open) entry amended in place again to describe what's
  now on disk. Still flagged for mandatory human browser sign-off before
  `/spec` — never marked "clear"
- fix: `html-prototype/agents-map.html` container-sizing bug (round 4, still
  pre-approval) — a targeted bug fix, not a redesign; round 3's polar-grid
  math (ring-by-type radial axis, virtual section boundaries, hub-at-rim
  trigonometry, the brain, the radar background, section titles) was
  untouched and confirmed correct. Root cause, confirmed by the operator via
  `getBoundingClientRect()` measurement rather than visual inspection:
  `.agents-map-stage`'s `padding: 130px 110px` (`box-sizing: border-box`)
  consumed a fixed 220px of horizontal width regardless of the container's
  actual size — on a realistic (non-ultrawide) window this collapsed
  `.agents-map-canvas`'s content-box width to double digits (a measured
  274px stage produced a 54px canvas), so the entire wheel — KB, all 3
  hubs, all 5 agents — rendered inside a ~54x54px circle. That crowding,
  not a positioning-math error, is what read as "hubs next to the KB."
  Fixed in `styles.css` by decoupling canvas size from stage padding:
  `.agents-map-stage` now reserves only a small fixed `24px` margin;
  `.agents-map-canvas` caps its own width explicitly (`width: min(100%,
  700px)`, centered) instead of inheriting 100% of a padding-starved stage.
  The outside section-title/hub labels don't need reserved padding to stay
  visible — they already position via percentages beyond the 0-100% range
  against `.agents-map-canvas`, which already has `overflow: visible`; they
  just need nothing clipping them, which the small margin provides.
  Hand-verified (no browser available) for stage widths ~500px/~700px/
  ~1000px: canvas content-box comes out to ~452px/~652px/~700px(capped) —
  comfortably several-hundred-px at every width checked, never collapsing.
  Breadcrumb in `agents-map.html` updated to record this as a sizing fix;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- design: `html-prototype/agents-map.html` Hub reposition (round 5, still
  pre-approval) — a genuine direction change, not another sizing fix; the
  round-4 canvas-sizing fix was independently re-verified by the operator
  (226px measured in a narrow test viewport, up from the broken 54px) and
  is untouched. Moved every `.hub-node` from round 3's outer-rim placement
  (r=54, the wheel's edge) to the inner band (r=19 — just outside the
  Producer ring, r=18, leaving clearance from the KB's own ~r=11 edge),
  computed with the same angle×radius trigonometry round 3 used: Capture
  Hub stays at its section's true midpoint (-30°) — its own Worker-ring
  agent sits 23 units further out, no collision; Q&A Hub stays at its
  section's true midpoint (210°) — 11-unit clearance to its own
  Expert-ring agent at r=30; People Hub is deliberately offset to 45°
  (off its section's 90° midpoint) because People Notes, a real
  Producer-type agent, already occupies that exact ring/angle — offsetting
  the Hub's angle (not overlapping it) was explicit in the requested fix.
  All three re-checked for KB clearance (~2.5-3.5 units) and hub-to-hub
  separation (>20 units, no risk). Recomputed every `.spoke-line` (Hub ->
  KB, now short, matching the near-center Hub positions) and every
  `.cluster-line` (Hub -> its section's agents, from the new Hub
  coordinates — the Capture section's now reach *outward* to the Worker
  ring at r=42 instead of round 3's short outward reach).
  `.section-boundary` guide lines and `.section-title` labels are
  untouched (never tied to Hub radius). Legend/intro copy updated from "at
  the rim" to "on the inner ring, close to the KB." REQ-SB-13's per-agent
  click -> side-panel behavior is unchanged; the round 2 light/green theme
  and the round 4 canvas-sizing fix are both unchanged. Breadcrumbs in
  both `agents-map.html` and `styles.css` updated to record this as a Hub
  reposition, explicitly distinct from the round 4 sizing bug fix;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- design: `html-prototype/agents-map.html` KB growth + full radial-scale
  rebalance (round 6, still pre-approval) — a scale/spacing rebalance, not
  another direction change; round 5's inner-ring Hub placement is
  preserved, it now just has real breathing room, and the round-4
  canvas-sizing fix is untouched (independently re-verified by the
  operator, 226px measured, before this round started). Root cause
  confirmed by the operator via direct `getBoundingClientRect()`
  measurement: the KB was correctly centered and exactly 22% wide as
  coded (no centering bug) — the real problem was that round 5's Hubs at
  r=19 sat only ~2.5%-of-canvas-radius from the KB's edge (~5.6px measured
  on a 226px canvas), three 11%-wide Hub nodes crowding a KB too small
  (22%) to read as dominant. Fixed as one coordinated rebalance: (1) grew
  `.kb-node` from 22% to 34% of canvas width (`styles.css`) and rebuilt the
  brain substantially denser in `agents-map.html` — 23 neurons (16 outer +
  6 mid + 1 center), up from 14, ~42 crossing synapse lines (up from ~26),
  varied neuron size/opacity across 3 depth layers, a stronger glow
  (`.kb-node`'s `drop-shadow` blur 16px→26px, `kbPulse`'s peak spread
  28px→42px); (2) recomputed the entire radial scale outward — by the same
  angle×radius trigonometry every prior round used, not eyeballed — so
  nothing collides now the KB is bigger: Hub band r=19→32 (edge-to-edge
  KB-Hub gap is now ~9.5 units, ~19% of the canvas radius, the explicit
  "comfortable double-digit percentage" target), Producer ring r=18→30,
  Expert ring r=30→45, Worker ring r=42→50, boundary r=54→58; every
  dependent coordinate recomputed from the new radii — all 3 `.hub-node`
  positions, all 5 `.agent-node` positions, every `.spoke-line`, every
  `.cluster-line`, the `.ring-label`/`.section-title` positions — none left
  pointing at stale round-5 coordinates. Hand-verified (no browser
  available): KB-edge-to-Hub-edge ~9.5 units (19%); KB-edge-to-
  Producer-ring-agent-edge ~8 units (16%); both same-angle Hub-vs-its-
  section's-own-agent pairs (Capture, Q&A) re-checked with positive
  clearance beyond the 10.5-unit combined-radii minimum (7.5 and 2.5 units
  respectively). `.section-boundary` guide lines and `.section-title`
  labels moved only incidentally with the slightly larger boundary —
  never tied to Hub or KB radius directly. REQ-SB-13's per-agent click ->
  side-panel behavior is unchanged; the round 2 light/green theme is
  unchanged. Breadcrumbs in both `agents-map.html` and `styles.css`
  updated to record this as a scale/spacing rebalance;
  `REVIEW-QUEUE.md`'s existing (still-open) entry amended in place again.
  Still flagged for mandatory human browser sign-off before `/spec` —
  never marked "clear"
- feat: hub-note file-I/O primitives added to `vault_writer.py`
  (`REQ-SB-14-US-01-T01`) — `hub_note_path`/`hub_note_exists` resolve/check
  `Work/Customers/<Customer>.md` (same `_slugify()` `write_note()` uses
  internally, so the two always agree on the file); `create_customer_hub_note_baseline`
  writes a new hub note's baseline frontmatter (`type`, `customer`, `tags`,
  `affiliate_of`) plus a short auto-generated body stub, via the existing
  `write_note`; `insert_frontmatter_key_if_missing` generalizes
  `insert_tags_line`'s surgical-insert precedent from a single hardcoded
  `tags` key to any key/value pair; `ensure_hub_note_baseline_frontmatter`
  tops up only the baseline keys an existing hub note is missing (never
  resets a real `affiliate_of`, never touches the body); `insert_body_line_if_missing`
  generalizes the same surgical-insert idea to the note body, idempotently
  inserting a line (e.g. the inline `**Customer:** [[Hub]]` wikilink) only
  if not already present. Purely additive — no existing function's behavior
  changed. Verified live against the real `.venv` and real configured vault:
  AC-01 (baseline creation + path/exists resolution) passed, plus two non-AC
  smoke checks (baseline top-up preserving existing keys/body, idempotent
  body-line insert); all throwaway test notes deleted afterward. This is the
  file-I/O layer `app/business/customer_hub_linking.py` (T02) will
  orchestrate on top of — no business logic (which customer, which note)
  lives here
- feat: new `app/business/customer_hub_linking.py` orchestration module
  (`REQ-SB-14-US-01-T02`) — `ensure_customer_hub_note` creates a
  customer's hub note baseline if missing or tops up only missing
  baseline frontmatter keys if it already exists; `link_note_to_customer_hub`
  idempotently inserts the inline `**Customer:** [[Hub]]` wikilink into a
  note's body; `ensure_hub_note_and_link` is the single shared operation
  (skips the `Unsorted` placeholder pseudo-customer and blank customers)
  that both the one-time retrofit and the future per-write capture hook
  call; `retrofit_customer_hub_links` iterates every vault note, skips
  notes with no real `customer:` frontmatter, and never links a hub note
  to itself. Built entirely on T01's `vault_writer` primitives — no direct
  filesystem I/O in this module (ADR-003 layering), mirroring
  `tag_backfill.py`/`vault_restructure.py`'s one-module-per-maintenance-
  operation shape. Non-AC smoke check run live against the real `.venv`
  and real configured vault (this story's locked ACs are exercised by
  T03/T04, which build on this module): created a throwaway note under
  `Work/Emails/` with `customer: 'Verify-T02-Customer'`, called
  `ensure_hub_note_and_link` — first call returned
  `hub_created: True, linked: True` and created
  `Work/Customers/Verify-T02-Customer.md`; second call with identical
  arguments returned `hub_created: False, linked: False` (idempotent);
  a call with `customer="Unsorted"` returned `skipped: True`. Throwaway
  note and hub note deleted afterward, leaving the real vault unchanged
- feat: wired the per-write customer hub-linking hook into
  `app/business/email_classification.py` (`REQ-SB-14-US-01-T03`) — after a
  captured note is written and marked processed,
  `classify_recent_emails` now calls
  `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`
  before returning, so every newly captured note is written with its
  customer's `[[wikilink]]` already in place and the customer's hub note
  is created automatically if missing — no separate manual linking step.
  Two-line addition only (one import, one call); `run_capture_and_record_completion`,
  the manual endpoint, and the function's return shape are all unchanged.
  Verified live (AC-03) against the real Outlook desktop client and the
  real configured vault: `Work/Customers/` did not exist beforehand
  (confirming no hub note pre-existed for any customer); probed
  increasing `limit` values on `classify_recent_emails` until reaching a
  genuinely unprocessed email (`limit=10` reached one: "Re: Workshop
  slides"); the real call classified it as customer `Masdar`, created
  `Work/Customers/Masdar.md` matching the Scenario-1 schema, and the
  written note's body already began with `**Customer:** [[Masdar]]`
  immediately after the call returned, with no separate edit
- feat: new `POST /poc/retrofit-customer-hub-links` endpoint
  (`REQ-SB-14-US-01-T04`) — thin wrapper around T02's
  `retrofit_customer_hub_links`, matching the existing `/poc/backfill-tags`/
  `/poc/flatten-customer-folders` one-off-migration-endpoint shape exactly;
  tallies `linked`/`hub_notes_created` counts from the results list. This
  closes `REQ-SB-14-US-01` — all five ACs now verified (AC-03 live in T03;
  AC-01/AC-02/AC-04/AC-05 verified live here). Verified live against the
  real configured vault: first call against customer `TAQA` (multiple
  existing customer-tagged notes, no hub note yet) created
  `Work/Customers/TAQA.md` matching the Scenario-1 schema and added
  `**Customer:** [[TAQA]]` to a pre-existing, previously-unlinked TAQA note
  (AC-01, AC-02); a manually-added `## My Notes` line was then appended to
  the hub note simulating user content, and a second call left it and the
  hub note's baseline frontmatter unchanged (AC-04), created no duplicate
  hub note (AC-01 idempotency half), and left the previously-linked note
  byte-for-byte unchanged, confirmed via matching SHA-256 hashes before/
  after (AC-05)
- chore: **SPRINT-002 Done** (2026-08-11) — REQ-SB-14 closed. Sizing
  estimate (~4 tasks, S) matched actual exactly, second sprint in a row.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- docs: authored the four Obsidian core-Templates note-type templates
  (`REQ-SB-15-US-01-T01`) — `Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`, written vault-relative at
  `VAULT_PATH` (per ADR-006's new third top-level vault root, sibling to
  `Personal/`/`Work/`) as pure vault-content authoring — no
  `src/backend`/`src/frontend` change. Each matches
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`'s resolved
  schema field-for-field; Customer is structurally parallel to
  `REQ-SB-14-US-01-T01`'s `create_customer_hub_note_baseline` output; the
  other three carry the inline `**Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]`
  wikilink line established by `REQ-SB-14-US-01`. Verified by reading all
  four files back from the real vault and YAML-parsing each frontmatter
  block in isolation (all 5 tagged ACs — AC-01 through AC-04, AC-06 —
  passed)
- docs: authored the in-vault Manual Entry Guide note
  (`REQ-SB-15-US-01-T02`) — `Work/Guides/Manual-Entry-Guide.md`, written
  vault-relative at `VAULT_PATH` (deliberately outside `Templates/` per
  ADR-006, so it never appears in Obsidian's "Insert Template" picker).
  Explains all four manual-entry note types (Customer, Opportunity,
  Agreement, Consumption-Snapshot) — what each is for, its target folder,
  and its matching template — plus a shared "How to insert a template"
  walkthrough; folder/template names cross-checked against T01's actual
  written files, no drift. This closes `REQ-SB-15-US-01` — all six ACs now
  verified (AC-01 through AC-04, AC-06 in T01; AC-05 here). Verified by
  reading the file back from the real vault
- chore: **SPRINT-003 Done** (2026-08-11) — REQ-SB-15 closed. Sizing
  estimate (~2 tasks, XS) matched actual exactly, third sprint in a row.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- refactor: `vault_writer._tag_slug` promoted to public `tag_slug`
  (`REQ-SB-10-US-01-T01`) — pure rename, no behavior change; `build_tags`'s
  two internal call sites updated. Frees the normalization function for
  reuse by `app/business/people_extraction.py` (T02) without duplicating
  slug logic outside `data_access`
- feat: five new Person-note file-I/O primitives added to `vault_writer.py`
  (`REQ-SB-10-US-01-T01`) — `person_note_path`/`person_note_exists` (dedup
  key: sender email, lowercased before slugifying), `build_person_tags`
  (separate `company/<slug>` tag namespace, `kind/person` always present),
  `create_person_note_baseline` (first-write baseline: type/name/email/
  phone/linkedin/tags + empty body), `ensure_person_note_baseline_frontmatter`
  (surgical top-up of missing baseline keys only, never resets a
  user-filled value, never touches the body) — mirrors the
  `REQ-SB-14-US-01` hub-note primitives for the People schema. Additive
  only; no other existing function's behavior changed. Verified via three
  non-AC smoke checks against the real backend `.venv` and real configured
  vault (this task's own locked-AC verification runs later, live, in
  T02/T03/T04): `tag_slug`/`build_tags` behavior-preserved after rename;
  `create_person_note_baseline` created a throwaway Person note with
  correct frontmatter/dedup-by-lowercased-email behavior;
  `ensure_person_note_baseline_frontmatter` topped up a removed `linkedin`
  key exactly once and was a true no-op on a second run. Throwaway test
  note and the `Work/People/` directory it created were deleted afterward,
  restoring the vault to its exact pre-task state
- feat: new `app/business/people_extraction.py` orchestration module
  (`REQ-SB-10-US-01-T02`) — `derive_company_from_email` (email-domain ->
  display-name company, `None` for a fixed set of personal/free email
  providers or a blank/malformed address), `find_matching_customer`
  (company vs. `list_known_customers()` by `tag_slug` equality, not exact
  string match), `ensure_person_note` (the shared create-or-top-up
  operation: baseline note on first sight, surgical baseline top-up on
  repeat, company tag always when derivable, hub-note link only after a
  confirmed customer match — calling `customer_hub_linking`'s two
  granular primitives directly, never `ensure_hub_note_and_link`),
  `ensure_person_note_for_captured_email` (per-write hook wrapper, skips
  cleanly on a blank `sender_email`), and `retrofit_people_from_emails`
  (one-time batch over every captured Email note, deduped by lowercased
  `sender_email`, skips notes with none). First business module that
  composes another business module (`customer_hub_linking.py`) rather
  than only `data_access` — an intentional, ADR-003-permitted shape
  recorded in `architecture.md`. This task's own functions carry no
  locked story AC directly (this story's 9 locked ACs are exercised
  live by T03/T04); verified via three non-AC smoke checks against the
  real backend `.venv` and real configured vault:
  `derive_company_from_email` correctly resolved `"core42.ai"` ->
  `"Core42"`, a personal Gmail domain -> `None`, and a blank address ->
  `None`; `find_matching_customer("Adnoc")` matched the real vault's
  `"ADNOC"` known customer despite mixed casing, and a made-up company
  name matched nothing; `ensure_person_note` created a throwaway Person
  note (`created: True`, correct company/no-match/no-link outcome) and a
  second identical call was a true no-op (`created: False`, no duplicate).
  Throwaway test note deleted afterward, restoring the vault to its
  exact pre-task state
- feat: going-forward per-write Person-note hook wired into
  `email_classification.py` (`REQ-SB-10-US-01-T03`) — immediately after the
  existing `customer_hub_linking.ensure_hub_note_and_link(note_path,
  customer)` call in `classify_recent_emails`, one additional call,
  `people_extraction.ensure_person_note_for_captured_email(email
  ["sender_name"], email["sender_email"])`, ensures every newly captured
  email's sender gets a Person note created or topped up as part of the
  same write — no separate manual step, going forward (Scenario 7). Only
  the import line and this one call site changed; `classify_recent_emails`'s
  return shape, `run_capture_and_record_completion`, and the manual
  `POST /poc/classify-emails` endpoint are untouched. Verified live
  (`REQ-SB-10-US-01-AC-07`, both creation and update halves) against the
  real Outlook desktop client and the real configured vault: called
  `classify_recent_emails(limit=10)` against two genuinely unprocessed
  emails, confirming `Work/People/ahmad.hamzeh@core42.ai.md` and
  `Work/People/shadi.shaat@core42.ai.md` were created in the same call
  with no prior manual step (creation half: PASS); immediately calling
  `ensure_person_note_for_captured_email` again for the same sender
  returned `created: False` with no duplicate note (update half: PASS)
- feat: new `POST /poc/retrofit-people-from-emails` endpoint
  (`REQ-SB-10-US-01-T04`) — thin wrapper around T02's
  `retrofit_people_from_emails`, matching the existing `/poc/backfill-tags`/
  `/poc/flatten-customer-folders`/`/poc/retrofit-customer-hub-links`
  one-off-migration-endpoint shape exactly; tallies `created`/`linked`
  counts from the results list. This closes `REQ-SB-10-US-01` — all nine
  ACs now verified (AC-07 live in T03; AC-01 through AC-06, AC-08, AC-09
  verified live here). Verified live against the real configured vault
  using real, naturally-occurring senders wherever the vault already had
  one, falling back to a single throwaway Email note only for AC-09's
  blank-`sender_email` case: `mohamed.eltanany@core42.ai` (7 Email notes,
  no Person note yet) produced exactly one Person note with `kind/person`
  and, since Core42 is an existing known customer, both the `company/core42`
  tag and a `[[Core42]]` wikilink, no duplicate hub note (AC-01, AC-03);
  `karimlouis@microsoft.com` (Microsoft, a derivable but not-a-known-
  customer company) got the `company/microsoft` tag only, no wikilink, no
  new hub note (AC-04); `mahmoud.m.moussa@live.com` (a personal email
  domain already in `people_extraction.py`'s known-provider set) got
  neither tag nor wikilink (AC-05); a throwaway blank-`sender_email` Email
  note was skipped without erroring the run (AC-09); a manually-added
  `## Notes` line on the Microsoft-company Person note survived an
  idempotent second call byte-for-byte (matching SHA-256 hashes,
  confirming AC-02's no-duplicate-Person-note guarantee too) (AC-02,
  AC-06); creating a `Work/Customers/Microsoft.md` hub note (via
  `customer_hub_linking.ensure_customer_hub_note`, then deleted afterward
  as test-only) and re-running retroactively added the `[[Microsoft]]`
  wikilink to that same Person note without disturbing the manual content
  (AC-08). Real production Person notes created by this real retrofit run
  against the real vault (18 distinct senders) were deliberately kept, not
  cleaned up — only the throwaway Email note, the throwaway
  `Microsoft.md` hub note, and the wikilink line it caused were removed
  afterward
- chore: **SPRINT-004 Done** (2026-08-11) — REQ-SB-10 closed. Sizing
  estimate (~4 tasks, S) matched actual exactly, third sprint in a row for
  this task shape. Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- fix: `BUG-001` — Email notes now wikilink to their sender's Person note
  (`BUGFIX-01-US-01-T01`) — new `people_extraction.link_email_to_person
  (email_note_path, person_note_path) -> bool`, mirroring
  `customer_hub_linking.link_note_to_customer_hub`'s exact shape: inserts
  an inline `**Sender:** [[PersonStem]]` wikilink into the Email note's
  body via the existing `vault_writer.insert_body_line_if_missing`
  primitive, only if not already present. Wired into
  `email_classification.classify_recent_emails`'s existing
  `ensure_person_note_for_captured_email` call site — its previously-
  discarded return value is now captured, and `link_email_to_person` is
  called whenever it isn't `None`. Closes the inbound (Email→Person)
  direction of `MEMORY.md`'s 2026-08-11 standing constraint (a
  referencing note must link out, not just cause the referenced note to
  be created), which the original `REQ-SB-10` pass only checked outbound
  (Person→Company). Verified live: a genuine newly-captured email
  (`Rudra.Potturu@tadweer.ae`, captured by the real app-start capture
  trigger) had `**Sender:** [[rudra.potturu@tadweer.ae]]` in its body
  immediately after capture, with no separate manual step
  (`BUGFIX-01-US-01-AC-01`, going-forward half)
- feat: one-time `retrofit_email_sender_links()` batch + new
  `POST /poc/retrofit-email-sender-links` endpoint (`BUGFIX-01-US-01-T02`)
  — backfills the same `**Sender:** [[PersonStem]]` wikilink onto every
  already-captured Email note with a real `sender_email`, mirroring
  `retrofit_customer_hub_links`'s/`retrofit_people_from_emails`'s exact
  batch shape and the existing `/poc/retrofit-*` endpoint pattern. Unlike
  `retrofit_people_from_emails`, deliberately does not dedup by sender —
  every Email note from a given sender needs its own body link. Verified
  live against the real configured vault (`VAULT_PATH`): one run linked
  249 already-captured Email notes (`BUGFIX-01-US-01-AC-01`, retrofit
  half), 84 notes correctly skipped for having no `sender_email` (Person/
  Customer-hub notes plus one Guide note), and a real newly-captured email
  already linked by the forward hook read `already_linked`; a second,
  identical run produced zero new links and no duplicate wikilink lines
  (`BUGFIX-01-US-01-AC-02`); a naturally-occurring blank-`sender_email`
  note (`Work/Guides/Manual-Entry-Guide.md`) was skipped, left
  byte-for-byte unchanged, with no error on either run
  (`BUGFIX-01-US-01-AC-03`)
- chore: **SPRINT-005 Done** (2026-08-11) — `BUGFIX-01-US-01` closed,
  `BUG-001` flipped `In Sprint → Closed` in both `BUGS.md` and
  `BACKLOG.md`. Sizing estimate (~2 tasks, XS) matched actual exactly.
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- feat: Partner hub-note baseline primitives + four generic rename/remove/
  swap/replace primitives (`REQ-SB-16-US-01-T01`) — ten new functions
  appended to `app/data_access/vault_writer.py`: `partner_hub_note_path`/
  `_exists`, `build_partner_tags`, `create_partner_hub_note_baseline`,
  `ensure_partner_hub_note_baseline_frontmatter`, `list_known_partners`
  (mirroring the Customer hub-note family exactly, `ADR-009`'s shorter
  Partner baseline-key set, no `affiliate_of`), plus `rename_frontmatter_key`,
  `remove_frontmatter_key_if_present`, `swap_tag`, `replace_body_line` —
  four generic, idempotent-by-construction primitives (no-op once the old
  key/tag/line is already absent) any future rename/retag migration can
  reuse. No existing function's behavior changed. Verified live against the
  real vault (AC-01 plus five non-AC smoke checks, all throwaway data
  deleted afterward)
- feat: new `app/business/partner_hub_linking.py` module
  (`REQ-SB-16-US-01-T02`) — `ensure_partner_hub_note`,
  `link_note_to_partner_hub` (mirroring `customer_hub_linking.py`'s two
  granular primitives exactly), and `migrate_customer_to_partner(
  customer_name)` — the one-time Customer→Partner migration: moves
  `Work/Customers/<name>.md` to `Work/Partners/<name>.md`
  (`vault_writer.move_note_and_attachments`), then a single generic
  vault-wide scan retags every note whose `customer` frontmatter equals
  `customer_name` (frontmatter key, `type` value, tags, and — where
  present — the inline `**Customer:**` body line), idempotent by
  construction. A parallel sibling to `customer_hub_linking.py`, per
  `ADR-009` — the `Done` REQ-SB-14 module and its
  `email_classification.py` call site are untouched. Verified live against
  a small faithfully-reproduced Microsoft-shaped fixture (throwaway data
  only — see `REQ-SB-16-US-01-T04` below for why this was **not** run
  against the real Microsoft data yet)
- feat: `people_extraction.py` gains a Partner-matching branch
  (`REQ-SB-16-US-01-T03`) — new `find_matching_partner` (mirrors
  `find_matching_customer` exactly, against a new vault-derived
  `list_known_partners()`); `ensure_person_note` now checks Customer first
  (unchanged) and Partner second, only when no Customer match was found
  (`ADR-009`'s mutual-exclusivity rule); return dict gains `partner_matched`
  (additive). Verified live end-to-end against throwaway partner/customer
  names (`REQ-SB-16-US-01-AC-01/02/03/04/08` Person-note half, all PASS) —
  real Microsoft/ADNOC data untouched by this task
- fix: `MEMORY.md` gains a new standing constraint — a "generic scan"
  migration keyed on frontmatter-field equality silently misses notes that
  reference the same entity by tag plus inline wikilink alone (found live
  verifying `REQ-SB-16-US-01-T04`, below)
- fix: `partner_hub_linking.migrate_customer_to_partner`'s retag-scan match
  predicate (`REQ-SB-16-US-01-T04`, corrected scope per `ADR-012`) —
  broadened from frontmatter-equality alone to a union of that signal and
  a new inline-body-wikilink-presence signal, both read from the loop's
  existing single `read_note()` call (no second scan, no new
  `vault_writer.py` primitive). Resolves `ESCALATIONS.md` → `ESC-001`: the
  original predicate structurally could never reach Person notes, which
  never carry a `customer` frontmatter field, only a `company/<slug>` tag
  plus a separately-written inline `**Customer:** [[Hub]]` wikilink
- feat: new `POST /poc/migrate-customer-to-partner` endpoint
  (`REQ-SB-16-US-01-T04`) — thin wrapper over the corrected
  `migrate_customer_to_partner`, matching the existing `/poc/retrofit-*`
  one-off-migration-endpoint shape. Ran live against the real vault: moved
  `Work/Customers/Microsoft.md` → `Work/Partners/Microsoft.md` (correct
  schema, no `affiliate_of`, existing `[[Microsoft]]` wikilinks still
  resolve — exactly one `Microsoft.md` file exists anywhere in the vault);
  a full vault-wide sweep confirmed all 15 real Microsoft-related notes the
  generic scan found (1 hub note, 2 Email, 1 Meeting, 1 Newsletter, 4
  Notification, 6 Person — one more Person note than the story's original
  count of 5, correctly picked up by the generic, not-hardcoded design)
  are fully retagged with zero stale Customer references remaining
  anywhere; a rerun is a true no-op; manually-added hub-note content
  survives reruns. This closes `REQ-SB-16-US-01` — all 8 locked ACs now
  verified live
- fix: two real vault notes manually repaired as due diligence during this
  live verification, both documented in `ESCALATIONS.md`: a harmless
  duplicate wikilink line on `nabeehquaroout@microsoft.com.md` (a real,
  newly-found 6th Microsoft Person note), and a genuine structural
  corruption on `karimlouis@microsoft.com.md` (pre-existing since an old
  `REQ-SB-10-US-01-T04` verification pass — `insert_body_line_if_missing`'s
  fixed body-start byte offset assumption, `ESC-003`, new finding, `Open`,
  primitive itself not yet fixed — see `MEMORY.md`)
- feat: `Templates/Research.md` (`REQ-SB-17-US-01-T01`) — the fifth
  Obsidian core-Templates file, authored directly into the real vault
  (`VAULT_PATH`), matching the resolved Research schema field-for-field
  (`type: Research`, `title`/`author` `REPLACE_WITH_...` placeholders,
  `tags: [kind/research]`), free-form body, deliberately no customer/
  company link anywhere. Verified live: real YAML parse confirms valid
  frontmatter with both placeholders unfilled; raw-text scan confirms no
  `customer`/`company` substring anywhere in the file
- docs: `Work/Guides/Manual-Entry-Guide.md` gains a fifth `## Research`
  section (`REQ-SB-17-US-01-T02`) — additive only: the opening paragraph
  now names five note types (Research added), and a new section matches
  the existing four sections' exact `**Folder:** ... · **Template:** ...`
  shape, citing `Work/Researches/`/`Templates/Research.md` by exact name.
  The four pre-existing sections and the "How to insert a template" steps
  are byte-for-byte unchanged. This closes `REQ-SB-17-US-01` — all 4 ACs
  verified live
- chore: **SPRINT-007 Done** (2026-08-11) — both `REQ-SB-16-US-01` and
  `REQ-SB-17-US-01` closed, every locked AC verified live against the real
  vault. Sizing estimate (~6 tasks, M) matched actual task count exactly,
  though `REQ-SB-16-US-01-T04`'s own live-migration verification needed a
  mid-flight architecture correction (`ADR-012`) and surfaced one
  unrelated, real primitive-level bug (`ESC-003`, still `Open`).
  Retrospective drafted, flagged for human harvest into
  `Implementation/Learnings.md` (see `REVIEW-QUEUE.md`)
- feat: **first real frontend page** (`REQ-SB-12-US-01-T01`, app shell +
  routing scaffold) — `react-router` (pinned `^7.18.2` per ADR-010's `v7.x`
  decision) wires `App.tsx`'s `<BrowserRouter>` to three routes (`/`,
  `/my-day`, `/settings`) behind a persistent `AppShell`/`Sidebar` layout;
  the collapsible burger-menu sidebar reproduces `html-prototype`'s
  `.app-shell`/`.sidebar-collapsed` behavior exactly (`aria-expanded`
  flips on toggle), `NavLink`'s `isActive` drives the `.active` nav-item
  class. `styles/tokens.css`/`shell.css`/`settings.css` ported near-
  verbatim from `html-prototype/styles.css`; the old Vite-template
  `App.css`/`index.css` counter-demo content removed. `api/client.ts`
  (thin `fetch` wrapper convention, unused this pass) established per
  ADR-010. Verified live in a real browser: burger toggle (`AC-04`) and
  nav round-trip across all 3 placeholder pages (`AC-05`) both PASS, zero
  console errors
- feat: **Agents Map polar-grid visualization** (`REQ-SB-12-US-01-T02`) —
  `features/agents-map/` (`mockAgents.ts` — the prototype's exact 5-agent/
  3-section populated dataset plus an empty first-run dataset;
  `polarLayout.ts` — a pure `polarToCartesian(radius, angleDeg)` geometry
  function, replacing the prototype's hand-derived per-node coordinates;
  `KnowledgeBaseNode`/`SectionHub`/`AgentNode`/`AgentsMapCanvas`) renders
  a central Knowledge Base "brain" SVG with 3 Section Hubs and 5 type-
  classed agent nodes (`.agent-node--worker/--producer/--expert`) on a
  3-ring polar grid, plus the ambient radar/ring/section-boundary/spoke-
  line/cluster-line SVG chrome. `styles/agents-map.css` ported near-
  verbatim. Verified live: populated state (1 KB element + 5 correctly-
  typed agent nodes, `AC-02`) and first-run empty state (KB element +
  "No agents connected yet" message, zero agent/hub nodes, `AC-03`) both
  PASS; every node's computed position matches the approved prototype's
  literal coordinates to within rounding
- feat: **Settings page reachability** (`REQ-SB-12-US-01-T03`) — minimal
  placeholder (`<h1>Settings</h1>` + an explanatory paragraph) replacing
  `T01`'s bare placeholder; no Vault/Connections card content (explicitly
  deferred per story scope). Verified live: URL reaches `/settings`, no
  thrown error, Settings `NavLink` carries `aria-current="page"` +
  `.active` while the other two nav items do not (`AC-06` PASS)
- chore: **`REQ-SB-12-US-01` (`SPRINT-008`) Done** (2026-08-11) — `T04`
  end-to-end verification found zero integration defects across `T01`–
  `T03`; all 6 locked ACs (`AC-01`–`AC-06`) re-verified together in one
  continuous, fresh-browser-session pass (headless Chrome via the Chrome
  DevTools Protocol — no test-stack ADR exists yet, so this is this
  sprint's "browser preview tool"), zero console errors/warnings
  throughout. This is the first-ever frontend build in this project and
  the foundation `REQ-SB-12-US-02` (My Day) and `REQ-SB-13-US-01` (agent
  chat panel) both build on next. Sprint `status: Done`, `gate: flagged`
  (retro drafted, awaiting human `Learnings.md` harvest — see
  `REVIEW-QUEUE.md`)
  (deferred until the blocked task resolves)
- feat: **new Outlook Calendar read primitive** (`REQ-SB-08-US-01-T01`) —
  `app/data_access/outlook_com.py::list_calendar_events(days_back,
  days_ahead, limit)`, this codebase's first calendar-read capability
  (ported from agentic-map's `list_upcoming_events`/`list_calendar_since`
  COM mechanics per ADR-008), plus `_resolve_attendees` (merges required/
  optional recipients into one flat `{"name", "email"}` list, excluding
  organizer/resource recipients). Verified live: 38 real events returned,
  correct schema, real Outlook calendar-view data matched
- feat: **Meeting-note vault-writer primitives** (`REQ-SB-08-US-01-T02`) —
  `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`/
  `ensure_meeting_note_baseline_frontmatter` (mirroring the Person/Customer-
  hub baseline-preservation contract), `load_processed_meeting_ids`/
  `mark_meeting_processed` (mirroring the email dedup-state-file shape),
  and a genuinely new `upsert_attendee_links` primitive — a per-attendee-
  wikilink upsert for the growable `**Attendees:** [[P1]], [[P2]], ...]`
  body line (distinct from the single-target `insert_body_line_if_missing`
  reused as-is for `**Customer:** [[Hub]]`). Verified live via a throwaway
  note, then cleaned up
- feat: **`app/business/meeting_classification.py`** (`REQ-SB-08-US-01-T03`,
  new) — the Meetings-capture orchestration: fetch calendar events →
  exclude the vault owner's own email (new required `Settings.self_email`
  config field, `.env`-sourced) → derive a customer via majority vote among
  attendee companies (tie-broken by first-encountered order) → write/top-up
  the Meeting note → link the matched customer hub and every attendee's
  Person note (reusing `people_extraction.ensure_person_note`/
  `customer_hub_linking`'s granular primitives as-is, per REQ-SB-10/14's
  established carve-out). Verified live: correct customer derivation
  (majority vote confirmed against real Core42-domain attendees), and the
  vault owner's own email confirmed excluded from both Person-note creation
  and customer derivation on a real self-organized meeting
- feat: **Meetings capture rides the existing hourly scheduler**
  (`REQ-SB-08-US-01-T04`) — `email_classification.
  run_capture_and_record_completion` gains one additional call,
  `meeting_classification.classify_recent_meetings()`, alongside its
  existing email-capture call; zero changes to `app/scheduling/
  capture_scheduler.py` (confirmed by diff — extends ADR-005 without
  rewriting it, per ADR-008). Verified live: a fresh dev-server app-start
  produced 38 real Meeting notes with no separate manual trigger
- feat: **`POST /poc/classify-meetings`** (`REQ-SB-08-US-01-T05`) — manual
  on-demand trigger mirroring `/poc/classify-emails`'s thin-wrapper shape.
  All 10 of this task's tagged ACs (`AC-01`–`AC-09`, `AC-11`) verified live
  against the real Outlook calendar/vault: idempotent reruns (no
  duplicates, manually-added Meeting-note and Person-note content
  preserved), no-customer-match handling, same-subject/same-date
  disambiguation, no-attendee events handled without error, recurring-
  occurrence handling, and — the story's most important AC — the vault
  owner's own email confirmed excluded from both Person-note creation and
  customer derivation on real production data, not just a throwaway
  construction
- chore: **`REQ-SB-08-US-01` (`SPRINT-006`) Done** (2026-08-11) — all 5
  tasks built and verified live; all 11 locked ACs pass against the real
  Outlook calendar and vault (38 real Meeting notes correctly captured,
  classified, and linked). One genuine architectural finding surfaced
  during Scenario 9 verification and escalated per ADR-008's own
  pre-authorized path, not silently patched: 3 real occurrences of a
  recurring meeting were found to share one identical, full Outlook
  `EntryID` (not just a coincidental filename-suffix match), falsifying
  ADR-008's stated per-occurrence-EntryID-uniqueness assumption — today's
  notes are all correct only because the filename also incorporates the
  event's date, and a future same-date recurring collision could silently
  merge two distinct meetings into one note. Does not block this sprint's
  `Done` status (every locked AC passed against real data available
  today). Full detail: `ESCALATIONS.md` → `ESC-002`; `REVIEW-QUEUE.md`
  pointer added for a human decision (superseding ADR vs. accepted known
  limitation). Sprint `status: Done`, `gate: flagged` (retro drafted,
  awaiting human `Learnings.md` harvest, plus the `ESC-002` decision — see
  `REVIEW-QUEUE.md`)
- feat: **`vault_writer.list_notes_in_kind_folder(kind)`**
  (`REQ-SB-12-US-02-T01`) — same-shape sibling of `list_all_note_paths()`
  scoped to one `Work/<kind>/` folder, returning `[]` if that kind folder
  doesn't exist yet. Verified live against the real vault (178 sorted
  paths under `Work/Emails/`; `[]` for a nonexistent kind)
- feat: **`app/business/my_day.py`** (`REQ-SB-12-US-02-T02`, new) —
  read-only My Day aggregation: `list_email_items()`/`list_calendar_items()`
  project `subject`/`sender`(or `start`)/`customer` from captured Email/
  Meeting notes (`customer` normalized to `null` for `"Unsorted"`/absent,
  reusing `list_known_customers()`'s existing convention); `summary()`
  returns per-section counts (`todo` hardcoded `0` — REQ-SB-09 has no
  resolved task source yet). Verified live against the real vault
- feat: **`GET /my-day/summary|emails|calendar|todo`**
  (`REQ-SB-12-US-02-T03`, new `app/api/my_day_router.py`) — the first
  router outside the `/poc` migration-endpoint family, registered in
  `app/main.py` alongside the existing routers. Also added
  `fastapi.middleware.cors.CORSMiddleware` to `app/main.py` — the first
  real browser-to-backend fetch call in this codebase, which fails
  outright without it; scoped to the Vite dev server's own default
  origins. Verified live against the real vault (178 emails, 39 meetings,
  0 to-do items)
- feat: **My Day dashboard page** (`REQ-SB-12-US-02-T04`) — three
  clickable `.day-section-card`s (Emails/Calendar/To-Do) with live counts
  from `/my-day/summary`, or "Nothing captured yet" per section; drill-down
  routes (`/my-day/emails|calendar|todo`) registered in `App.tsx`;
  `features/my-day/client.ts` and `styles/my-day.css` (ported from
  `html-prototype/styles.css`) added. Verified live in a real browser via
  headless-Chrome CDP: exactly 3 cards render, correct counts/empty-state
  per section, all-zero first-run state (temporary stub), and all 3
  card-click navigations land on the right drill-down route
- feat: **Emails drill-down page** (`REQ-SB-12-US-02-T05`,
  `MyDayEmailsPage.tsx`) — populated `.item-list` (subject/sender/customer,
  `null` renders "Unclassified") sourced from `/my-day/emails`, or an
  `.empty-state`. Verified live: 178 real captured emails rendered
  correctly (5 "Unclassified"); empty state confirmed via a temporary
  client-side stub, then reverted
- feat: **Calendar drill-down page** (`REQ-SB-12-US-02-T06`,
  `MyDayCalendarPage.tsx`) — populated `.item-list`
  (subject/start/customer, `null` renders "No customer") sourced from
  `/my-day/calendar`, or an `.empty-state`. Verified live: 39 real
  captured meetings rendered correctly (3 "No customer") — SPRINT-006
  landed concurrently mid-sprint, so this is real production data, not the
  synthetic test note the task originally planned; empty state confirmed
  via a temporary client-side stub instead (the real vault can no longer
  produce it naturally), then reverted
- feat: **To-Do drill-down page** (`REQ-SB-12-US-02-T07`,
  `MyDayTodoPage.tsx`) — always renders `.empty-state` ("To-Do Capture
  (REQ-SB-09) has not been built yet"), deliberately no populated-state
  code path pending REQ-SB-09's own future task-source resolution.
  Verified live
- chore: **`REQ-SB-12-US-02` (`SPRINT-009`) Done** (2026-08-11) — all 7
  tasks built and verified live; all 8 locked ACs pass (backend
  smoke-checked against the real vault; frontend verified in a real
  browser via headless-Chrome CDP, `npm run build` clean). Zero blocked
  tasks, zero `ESCALATIONS.md` entries. One genuine architectural gap
  (missing CORS middleware — see the `T03` entry above) was found and
  fixed within scope, flagged for human spot-check of the allowed-origins
  policy. Sprint `status: Done`, `gate: flagged` (retro drafted, awaiting
  human `Learnings.md` harvest, plus the CORS spot-check — see
  `REVIEW-QUEUE.md`)
- feat: **agent-history vault_writer primitives** (`REQ-SB-13-US-01-T01`,
  `ADR-011`) — new `.second-brain/agent_communication_history.json`,
  `append_agent_history_entry(agent_id, kind, text)` /
  `load_agent_history(agent_id)`, mirroring the existing
  `record_capture_run_completed`/`load_last_capture_run` shape. Additive
  only — no existing `vault_writer.py` function changed
- feat: **static agent/settings/actions/trigger-phrases registry**
  (`REQ-SB-13-US-01-T02`, new `app/business/agent_registry.py`) — five
  known agents (`email-capture`/`meeting-capture`/`todo-capture`/
  `people-producer`/`vault-qa`), each with `settings`/`actions`/
  `trigger_phrases`, deliberately hardcoded per `ADR-011` (not
  vault-derived — which agents exist is deployment configuration, not
  open-ended vault content)
- feat: **agent chat trigger-phrase matching** (`REQ-SB-13-US-01-T03`, new
  `app/business/agent_chat.py`) — `handle_chat_message(agent_id, message)`,
  lowercase substring match against the agent's declared trigger phrases,
  registry order, first match wins; deliberately not an NLU/LLM pipeline
  (`ADR-007`/`ADR-011`)
- feat: **`run_capture_and_record_completion` history hook**
  (`REQ-SB-13-US-01-T04`) — one additional
  `vault_writer.append_agent_history_entry("email-capture", "run_event",
  ...)` call, alongside the existing `record_capture_run_completed()`
  call, so every trigger source (scheduler, app-start,
  `/poc/classify-emails`, the new agent-panel action/chat triggers)
  produces the same Communication History entry through one shared entry
  point. The only change to already-`Done` code this story makes
- feat: **`GET /agents/{id}`, `POST /agents/{id}/actions/{action_id}`,
  `POST /agents/{id}/chat`, `GET /agents/{id}/history`**
  (`REQ-SB-13-US-01-T05`, new `app/api/agents_router.py`, registered in
  `app/main.py`) — the shared `_invoke_action`/`_ACTION_HANDLERS` call
  site used by both the direct action-trigger endpoint and the chat
  endpoint, so a button click and a matching chat message invoke the
  identical handler. Only `email-capture`'s `run_capture_now` has a real
  handler this pass; every other action returns an honest "not yet
  available" result. Verified live: `GET /agents/email-capture` returns
  settings/actions with no `trigger_phrases` leaked, `404` for an unknown
  agent, chat matching and fallback confirmed, the real action-trigger
  path confirmed via `T07`'s UI-driven check (see below)
- feat: **agent detail panel — settings, available actions, open/close**
  (`REQ-SB-13-US-01-T06`, new `AgentDetailPanel.tsx`/
  `agentsApiClient.ts`/`styles/agent-panel.css`; `AgentNode.tsx`/
  `AgentsMapCanvas.tsx` gained `onSelect`/`onSelectAgent` click wiring;
  `AgentsMapPage.tsx` gained selection state) — clicking an `.agent-node`
  opens a `.side-panel` overlay showing that agent's real settings/
  actions; closes via its close control or an outside click. Verified
  live in a real browser via headless-Chrome CDP
- feat: **embedded chat thread** (`REQ-SB-13-US-01-T07`) — send/receive
  against the real `POST /agents/{id}/chat` endpoint, no canned/demo
  reply. Verified live: a non-matching message gets a real fallback
  reply; "please run capture now" triggered one real Outlook/Compass/
  vault-write capture run through the actual UI, with a reply confirming
  what was done — no external navigation at any point
- feat: **communication history + full agent-switching refresh**
  (`REQ-SB-13-US-01-T08`) — unified chronological `.log-list` (chat +
  run events together, not two separate lists) or an `.empty-state`,
  re-fetched on agent switch and after every chat send. Verified live:
  populated history renders correctly ordered, an untouched agent
  (`meeting-capture`) shows the empty state, and switching agents mid-panel
  fully replaces every section's content with no leftover from the
  previously selected agent
- chore: **`REQ-SB-13-US-01` (`SPRINT-010`) Done** (2026-08-11) — all 8
  tasks built and verified live; all 8 locked ACs pass, including both
  trust-surface-defining scenarios (a chat message triggering a real
  backend action; chat + run events unified in one chronological
  history), confirmed with a single real capture run triggered through
  the actual chat UI. `npm run build` clean. Zero blocked tasks, zero
  `ESCALATIONS.md` entries; small additive CORS-origin extension in the
  shared `app/main.py` (Vite landed on port 5174, already flagged by a
  concurrent session's own `REVIEW-QUEUE.md` entry, not duplicated).
  Sprint `status: Done`, `gate: flagged` (retro drafted, awaiting human
  `Learnings.md` harvest — see `REVIEW-QUEUE.md`)
- feat: **Agents Map wired to real backend data, replacing `mockAgents.ts`'s
  static example** (operator-directed, 2026-08-11, outside the formal
  pipeline — small, well-bounded wiring task, not new product scope). New
  `agent_registry.list_agents()` + `GET /agents` (`app/api/agents_router.py`)
  return the real 5-agent registry (id/name/type) already built by
  `REQ-SB-13-US-01`/ADR-011. New frontend `fetchAgentList()`
  (`agentsApiClient.ts`) + `layoutAgents()` (`features/agents-map/
  layoutAgents.ts`) derive section membership and evenly-spaced ring angles
  from the real list instead of hardcoded per-agent coordinates —
  `AgentsMapPage` now fetches on mount instead of importing static
  `POPULATED_SECTIONS`/`POPULATED_AGENTS`, which were removed from
  `mockAgents.ts` (shared type definitions kept). Verified live: `GET
  /agents` returns the real registry, the rendered map matches it exactly
  (5 agents, correct sections/rings), zero console errors on a fresh load.
- design: `/design` run retroactively against REQ-SB-18 (Dynamic Agent
  Sections & Agent-to-Section Assignment) and REQ-SB-19 (Per-Agent LLM
  Provider Selection), still pre-approval — both stories already went
  through `/spec` and had their Gherkin locked (including the operator-
  resolved block-until-empty/unused deletion policy, Scenario 4b in both),
  and their analyst flagged the missing prototype coverage for `/design`
  to supply before `/plan-tasks`. `html-prototype/settings.html` gains two
  new cards: **Sections** (list/create/rename/delete, REQ-SB-18) and
  **Providers** (list/add/edit/remove, Compass pre-seeded and marked
  "Default", REQ-SB-19); the existing Vault/Connections cards (REQ-SB-12)
  are untouched. Both new cards demonstrate the block-until-empty/unused
  policy two ways at once — a disabled Delete/Remove button with a `title`
  tooltip, plus an always-visible danger-colored explanation naming which
  agent(s) block it — and an isolated "blocked deletion/removal attempt"
  state-switcher panel. Credential fields are always `type="password"`
  (masked). `html-prototype/agents-map.html`'s side panel `kv-list` gains
  its first genuinely *editable* rows — a Section picker and a Provider
  picker (native `<select>`, zero JS) — on all 5 existing agents; People
  Notes is deliberately set to a non-Compass Provider with no real client
  yet, surfaced with a `badge-warning` "Not yet available" + explanatory
  text, directly demonstrating REQ-SB-19 Scenario 7's honesty requirement
  at the exact surface where the user picks a Provider. A new third Agents
  Map state, "5 sections (REQ-SB-18 N-section reference)", proves the
  existing polar-grid Hub mechanism (ring=Type, angle=Section, Hub on the
  inner band, radar/ring background, KB brain — all otherwise UNCHANGED)
  generalizes past the approved design's hardcoded 3 hubs to an arbitrary
  N: 5 evenly-spaced Sections (72° apart, same angle x radius trigonometry
  every prior agents-map.html round used, re-derived from round 6's own
  committed coordinates rather than eyeballed), 2 of them genuinely
  zero-agent Hubs (Scenario 7) rendering with no cluster lines — a visual
  reference for `/plan-tasks`'s real `layoutAgents.ts`/`polarLayout.ts`
  computation, not the final production geometry (explicitly out of this
  batch's scope). Reused: My Day's `.item-list`/`.item-row` family for
  both new Settings lists; native `<details>/<summary>` for every create/
  rename/edit/add affordance instead of new JS wiring. New (added to
  `styles.css`): `.item-row-actions`, `.btn-danger` (symmetric with
  `.btn-primary`, built from the existing `--color-danger` token, no new
  hex), `.kv-select` (compact inline `<select>` for the side panel), and a
  `summary.btn` marker reset. Hub color in the new 5-section state is
  neutral (`--color-accent`) instead of the old per-Type modifier classes
  — a Section can now hold agents of any Type (Scenario 6), so a single
  Type color on its Hub would misrepresent it; the existing 3-hub
  "Populated" state's Type-colored hubs are left exactly as approved
  (minimal-change scope), flagged in `REVIEW-QUEUE.md` for a human call on
  whether that older state should eventually be relabeled to the new
  Section names. As always, flagged for mandatory human browser sign-off
  before `/plan-tasks` proceeds — never marked "clear"
- feat: `REQ-SB-18-US-01` (User-editable agent Sections, decoupled from
  agent Type, with per-agent section reassignment, `SPRINT-011`) shipped
  end-to-end and verified live, per `ADR-014`. Backend: `app/data_access/
  vault_writer.py` gained `load_sections_state`/`save_sections_state`
  (new `.second-brain/agent_sections.json`); new `app/business/
  section_registry.py` (seeds the starting 5 sections — Technical, Sales,
  Productivity, Customers, Products — on first read, self-heals any known
  agent absent from `assignments` to the first section, and owns
  create/rename/delete with a block-until-empty result dict); new `app/
  api/sections_router.py` (`GET/POST /sections`, `PATCH/DELETE
  /sections/{id}`, `409` with a name-resolved message when a delete is
  blocked), registered in `app/main.py`; `app/api/agents_router.py`
  gained `PATCH /agents/{agent_id}` (`section_id`) and merged
  `section_id`/`section_name` fields onto `GET /agents`/`GET
  /agents/{agent_id}`, composed at the router layer without modifying
  `agent_registry.py` (`ADR-011` point 2 untouched). Frontend:
  `layoutAgents.ts` rewritten to a genuinely N-section-generic computation
  (hub angles evenly spaced around the full circle from the real `GET
  /sections` list; section membership from each agent's own `section_id`,
  no longer from `type`); `mockAgents.ts`'s `AgentSection` dropped `type`,
  `SectionId` widened to `string`; `AgentsMapCanvas.tsx`'s
  `section-boundary` dividers generalized from 3 fixed lines to N
  adjacent-hub-angle-midpoint lines, and Hub/spoke-line/cluster-line
  coloring moved to one neutral `var(--color-accent)` (a Section can now
  hold agents of any Type); `SectionHub.tsx` dropped its per-Type modifier
  class; new `src/frontend/src/features/settings/SectionsCard.tsx` +
  `settingsApiClient.ts` (Settings' new Sections area — list/create/
  rename/delete, a disabled+tooltipped Delete button when blocked, and a
  blocked-message region rendering the server's exact `409` text);
  `AgentDetailPanel.tsx` gained a Section `<select>` kv-row wired to the
  new `updateAgentAssignment` (`agentsApiClient.ts`). Verified live (real
  `.second-brain/agent_sections.json`, real backend on `:8001`, real
  frontend via headless-Chrome-via-CDP on `:5173`): all 9 locked ACs pass,
  including both trust-defining scenarios — `AC-05` (blocked deletion:
  confirmed the exact `409` message renders in the UI, section/assignments
  unchanged) and `AC-09` (the Agents Map reflects a just-changed
  assignment with no code change/restart, confirmed via cluster-line
  topology counts matching the reassignment exactly). `npx tsc --noEmit`
  and `npm run build` both clean. Full verification detail: each task's
  own `## Implementation Log`,
  `Implementation/Tasks/REQ-SB-18-US-01-T01`…`T08`.
- design: `/design` run against `REQ-SB-20-US-01` (Section Hub Intelligence
  & Cross-Section Routing), `REQ-SB-21-US-01` (Agent Working Modes), and
  `REQ-SB-23-US-01` (My Day Intake Agent), still pre-approval — all three
  already had their Gherkin locked (including the operator-resolved
  decisions in each story's own `## Notes`: free-text keywords/keyword-
  match routing/cross-Section-only for REQ-SB-20; default mode Autonomous/
  a real Pending Approvals surface built now for REQ-SB-21) and were
  flagged for missing prototype coverage. Four changes: (1)
  `html-prototype/agents-map.html`'s side panel Settings `kv-list` gains
  Keywords (free-text, following the Section/Provider picker-row pattern —
  empty on To-Do Capture to demonstrate REQ-SB-20 Scenario 4's "no
  keywords, never a routing target") and Working mode
  (Autonomous/Supervised/Manual, defaulting Autonomous; Meeting Capture and
  People Notes set Supervised, To-Do Capture set Manual) rows on all 5
  agents; (2) Meeting Capture's Chat block gains a pending-approval
  proposal card (new `.chat-proposal` pattern in `styles.css` — dashed-
  warning while pending, solid-success/solid-danger once resolved, all via
  the existing `color-mix(...)`-over-token technique, no new hex), its
  pending/approved/declined outcomes demonstrated via a small
  `.state-switcher` nested inside the chat thread itself; (3) a new
  Pending Approvals surface — a 5th card on `html-prototype/my-day.html`'s
  dashboard grid plus a new drill-down page,
  `html-prototype/my-day-approvals.html` (reusing the same `.item-list`
  pattern the other four My Day drill-downs already use), listing each
  Supervised agent's background-pipeline proposal with Approve/Decline
  actions, plus an empty "queue caught up" state — placed on My Day (not
  Settings, not a new nav item) since My Day is this project's existing
  "things needing my attention today" surface; (4) a new "Quick Capture"
  card at the top of `my-day.html` (the My Day Intake Agent, REQ-SB-23) — a
  free-text input + Capture button plus an `.item-list` submission history
  demonstrating all 4 of that story's locked scenarios (a
  customer-classified filing using the exact tags-and-wikilinks copy from
  `MEMORY.md`'s standing schema, an unclassified filing, a second same-day
  filing proving no filename collision, and a classification-FAILED
  submission with its original text visibly preserved plus a Retry
  affordance) and a first-run empty state. `html-prototype/index.html`'s
  catalog updated to list the new drill-down and the three additions. As
  always, flagged for mandatory human browser sign-off before `/plan-tasks`
  proceeds — never marked "clear". Full breadcrumb: the top-of-file
  comments in `agents-map.html`/`my-day.html`/`my-day-approvals.html`;
  review entry: `REVIEW-QUEUE.md`.
- feat: `REQ-SB-22-US-01` (My Day drill-downs and dashboard counts scoped
  to a rolling 7-day window, `SPRINT-013`) shipped end-to-end and verified
  live. `app/business/my_day.py` gained the first date-range filtering
  ever added to My Day's read path — new `_compute_window()` (3 days
  before through 3 days after `datetime.now()`, recomputed on every call,
  never cached) and `_within_window()` (ISO-date-string-prefix compare,
  no `datetime.fromisoformat()`/timezone logic) helpers; both
  `list_email_items()` and `list_calendar_items()` now narrow to the
  window, and `list_email_items()` gains a `received` field it previously
  omitted entirely. `app/api/my_day_router.py` is unchanged — endpoint
  contracts are unaffected (additive field + narrower result set only).
  Frontend: `features/my-day/client.ts`'s `MyDayEmailItem` gains
  `received: string`; `MyDayEmailsPage.tsx`'s existing `.item-row-meta`
  line renders it. `MyDayCalendarPage.tsx`/`MyDayPage.tsx` needed no code
  change — verified live as already-correct consumers of the now-narrower
  backend response. Verified against the real vault (179 Email notes, 39
  Meeting notes): windowed counts 21 emails / 17 meetings; a real
  out-of-window email and a real out-of-window meeting were each confirmed
  genuinely absent from the returned lists (not flagged, not
  de-emphasized); a monkeypatched `datetime` simulating 10 days later
  produced a correctly-shifted window and result set, then reverted to
  restore the exact original result — confirming the window advances
  automatically with zero caching. Both drill-downs' empty states verified
  via a temporary client-stub-and-revert (`Promise.resolve([])`), real
  populated states restored exactly afterward. `npm run build` clean, zero
  console errors. Full verification detail: `Implementation/Tasks/
  REQ-SB-22-US-01-T01-backend-rolling-window-filtering.md`,
  `Implementation/Tasks/REQ-SB-22-US-01-T02-drilldowns-consume-windowed-
  response.md`.
- feat: `REQ-SB-19-US-01` (Global LLM Provider CRUD in Settings, with a
  per-agent Provider picker defaulting to Compass, `SPRINT-012`) shipped
  end-to-end and verified live, per `ADR-014`, built as a diff on top of
  `REQ-SB-18-US-01`/`SPRINT-011`'s already-landed shared surface. Backend:
  `app/data_access/vault_writer.py` gained `load_providers_state`/
  `save_providers_state` (new `.second-brain/agent_providers.json`); new
  `app/business/provider_registry.py` (seeds a "Compass" Provider entry
  from `app.config.settings.compass_*` on first read, self-heals any known
  agent absent from `assignments` to `"compass"`, owns create/update/
  remove with a block-until-unused result dict, and `has_real_client()` —
  a small hardcoded real-client set, mirroring `ADR-011` point 3's
  "declared but unbuilt" pattern one layer up); new `app/api/
  providers_router.py` (`GET/POST /providers`, `PATCH/DELETE
  /providers/{id}`, `409` with a name-resolved message when a removal is
  blocked, never a `credential` field in any response), registered in
  `app/main.py`; `app/api/agents_router.py` gained the `provider_id`
  portion of `PATCH /agents/{agent_id}`, merged `provider_id`/
  `provider_name`/`provider_available` fields onto `GET /agents`/`GET
  /agents/{agent_id}`, and a Provider-availability gate inside
  `_invoke_action` (returns an honest "not available yet" result before
  ever calling a real handler, when the agent's selected Provider has no
  real client — no silent fallback to Compass, no fabricated response).
  `agent_registry.py`, `app/data_access/compass_client.py`, and
  `app/config.py` were not modified — the pre-seeded "Compass" Provider
  entry is a CRUD-editable *representation* only; the real Compass call
  path keeps reading `.env`/`Settings.compass_*` directly, unaffected by
  any edit made to it from Settings. Frontend: new
  `src/frontend/src/features/settings/ProvidersCard.tsx` +
  `settingsApiClient.ts`'s `/providers` calls (Settings' new Providers
  area — list/add/edit/remove, a masked credential field, a disabled+
  tooltipped Remove button when blocked, and a blocked-message region
  rendering the server's exact `409` text), composed into
  `SettingsPage.tsx` alongside `REQ-SB-18-US-01`'s `<SectionsCard>`;
  `AgentDetailPanel.tsx` gained a Provider `<select>` kv-row (wired to the
  existing `updateAgentAssignment`, `agentsApiClient.ts`'s `AgentDetail`
  widened with `provider_id`/`provider_name`/`provider_available`) plus a
  conditional honesty note when the selected Provider has no real client.
  Verified live (real `.second-brain/agent_providers.json`, real backend
  on `:8001`, real frontend via headless-Chrome-via-CDP on `:5173`): all 8
  locked ACs pass, including both trust-surface-defining scenarios —
  `AC-07` (an agent using Compass behaves identically even after editing
  the Compass Provider entry's own representation, confirmed with one real
  Outlook/Compass/vault-write capture run) and `AC-08` (an agent pointed
  at a non-Compass Provider honestly reports unavailability, confirmed via
  its own history log that no real Outlook/Compass call occurred). `npm
  run build` (`tsc -b && vite build`) clean. Full verification detail:
  each task's own `## Implementation Log`,
  `Implementation/Tasks/REQ-SB-19-US-01-T01`…`T06`.
