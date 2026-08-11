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
