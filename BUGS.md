# BUGS.md

The append-only **source of truth** for bugs found through manual testing — UI
issues and logic issues alike. Detail lives here; `BACKLOG.md`'s `## Bugs` section
is a thin status mirror of the index table below.

- **Capture:** `/bug` (interactive — asks clarifying questions, then writes a row
  here at `Open`).
- **Fix:** `/triage` batches chosen `Open` bugs into one `BUGFIX-NN-US-01` story;
  that story then flows through `/plan-tasks → /plan-sprints → /implement-sprint`.
- **Full contract:** `Implementation/Pipeline.md` → "Bug tracking".

## Rules

- **Append-only.** Never delete a row or a detail subsection.
- `BUG-NNN` ids are **sequential and never reused** (even for `Won't Fix` bugs).
- This file is the source of truth; the `BACKLOG.md` `## Bugs` mirror is derived.
  Whoever changes a bug's status updates **both** in the same touch.
- **Area:** `UI | Logic`. **Severity:** `Blocker | Major | Minor | Cosmetic`.
- **Status:** `Open` (logged, no fix story) → `In Sprint` (a `BUGFIX-NN` story
  covers it, set at `/triage`) → `Closed` (covering story `Done`). Terminal:
  `Won't Fix` (with a reason in the detail subsection; never auto-set).
- A bug against already-`Done` work becomes **new forward work** (a `BUGFIX-NN`
  story), never a reopening of the original story.

---

## Index

| ID | Title | Area | Severity | Status | Found | Fixed by |
|---|---|---|---|---|---|---|
| BUG-001 | Email notes don't wikilink to their sender's Person note | Logic | Major | Closed | 2026-08-11 | BUGFIX-01-US-01 |
| BUG-002 | Agents Map: sections with 4+ agents visually spill into neighboring sections | UI | Major | Closed | 2026-08-11 | BUGFIX-02-US-01 |
| BUG-003 | `insert_body_line_if_missing` corrupts notes whose body lacks the blank line after frontmatter | Logic | Major | Open | 2026-08-11 | — |
| BUG-004 | Agents Map: an agent node renders directly on top of a neighboring Section's Hub | UI | Major | Open | 2026-08-12 | — |
| BUG-005 | Agents Map: top Section title renders off-screen above the viewport | UI | Minor | Open | 2026-08-12 | — |
| BUG-006 | Agents Map: Worker and Expert rings have zero gap, agents visually read as the same ring | UI | Minor | Open | 2026-08-12 | — |
| BUG-007 | `graph.py::_call_model` is a synchronous node with a blocking Provider call, suspected cause of a real dev-backend hang | Logic | Major | Open | 2026-08-12 | — |
| BUG-008 | App-start Outlook-COM capture in `main.py`'s lifespan has no timeout, can hang the whole server's startup indefinitely | Logic | Major | Closed | 2026-08-12 | Direct fix, 2026-08-14 |
| BUG-009 | Agents Map overview: agents fan out past their own Section's wedge boundary into a neighboring Section | UI | Major | Open | 2026-08-13 | — |
| BUG-010 | Agents Map overview: on hover, an agent's Type and Name labels render at the identical position, directly overlapping | UI | Major | Open | 2026-08-13 | — |
| BUG-011 | `_slugify`'s 80-char truncation can silently eat a filename's disambiguating id-suffix, causing two distinct real notes to collide on the same filename stem — in `Work/Tasks/`'s flat folder this causes a real same-path overwrite (content loss), not just index-invisibility | Logic | Blocker | Open | 2026-08-13 | — |
| BUG-012 | Mid-conversation model tool-calls bypass the working-mode approval gate for mutating Skills | Logic | Minor | Open | 2026-08-14 | — |
| BUG-013 | `skill_registry._load_state` re-applies `_MIGRATION_GRANT_SEED` on every read, silently un-revoking a migration-seeded Skill from a migration-seeded agent immediately after a real revoke call | Logic | Major | Open | 2026-08-14 | — |
| BUG-014 | Thread email attachments are never captured (Outlook fetch never reads them), and `write_attachments` has no filename-collision protection for when they are | Logic | Major | Closed | 2026-08-17 | BUGFIX-03-US-01 |
| BUG-015 | `compass_client.classify_email` consistently fails (timeout / empty response) for 3 specific real "Weekly/Net New Forecast"-style emails, even after retries — those emails never get captured, silently retried forever | Logic | Major | Open | 2026-08-17 | — |
| BUG-016 | An attendee resolving to a legacyExchangeDN address crashes `classify_recent_meetings`, aborting the whole meeting-capture run | Logic | Major | Open | 2026-08-17 | — |
| BUG-017 | `_is_inline_attachment` false-positives on real, standalone attachments that happen to carry a MIME Content-ID, silently dropping them from capture entirely | Logic | Major | Closed | 2026-08-17 | Direct fix, 2026-08-17 |
| BUG-018 | `BUGFIX-03-US-01-T02`'s per-message attachment nesting silently broke Inbox Cockpit's flat-path attachment lookup (`list_attachments`/`hand_off_attachment_to_chat` returned empty/not-found, no error) | Logic | Major | Closed | 2026-08-17 | Direct fix, 2026-08-17 |
| BUG-019 | `REQ-SB-69-US-01-T06`'s human-readable Thread filenames silently broke `meeting_classification.py`'s Link-to-Thread PRIMARY strategy — `thread_note_exists(conversation_id)` always returns `False` for a genuinely-existing post-`ADR-046` Thread | Logic | Major | Closed | 2026-08-17 | Direct fix, 2026-08-17 |
| BUG-020 | `skill_tools.process_staged_email`'s new `run_email_capture_pipeline()` handler counted `len(results)` as "filed" without filtering out per-item `{"error": ...}` entries, silently reporting real Compass classification failures as successes | Logic | Major | Closed | 2026-08-17 | Direct fix, 2026-08-17 |
| BUG-021 | `thread_match_merge`'s update path reads `frontmatter.get("thread_name")` for the rename check, which is `None` for any Thread created before `ADR-046`/`T06` shipped (no `thread_name` key existed yet) — produced a real, literal `"None-<date>-<hash>.md"` filename | Logic | Major | Closed | 2026-08-17 | Direct fix, 2026-08-17 |
| BUG-022 | Meeting/Inbox Cockpit: every agent responds to a message, not just the addressed one | Logic | Major | Closed | 2026-08-19 | BUGFIX-04-US-01 |
| BUG-023 | Meeting/Inbox Cockpit: pressing Enter in the chat input does nothing, must click Send | UI | Major | Closed | 2026-08-19 | BUGFIX-04-US-01 |
| BUG-024 | Meeting/Inbox Cockpit: sent message/replies don't appear until manual page refresh | UI | Major | Closed | 2026-08-19 | BUGFIX-04-US-01 |
| BUG-025 | Chat messages render as plain text instead of rich text (Meeting Cockpit, Inbox Cockpit, Agents Map chat panel) | UI | Major | Closed | 2026-08-19 | BUGFIX-04-US-01 |
| BUG-026 | `thread_match_merge`'s legacy rename logic duplicates old-shape Threads and orphans `messages/`/`files/` on new-shape Threads (`ESC-048`/`ESC-050`) | Logic | Major | Closed | 2026-08-19 | BUGFIX-05-US-01 |
| BUG-027 | `resolve_people_chips` 500s on a real Meeting note whose `attendees` frontmatter is a plain list of wikilink strings, not dicts | Logic | Minor | Closed | 2026-08-19 | BUGFIX-06-US-01 |
| BUG-028 | `create_okf_directory_baseline`/`ensure_okf_directory_baseline` create `log.md`/`captures.md` completely empty — no header naming the owning Customer/Project, unlike `index.md`'s own `# {name}` convention | Logic | Minor | In Sprint | 2026-08-19 | BUGFIX-07-US-01 |
| BUG-029 | `meeting-capture`'s `run_capture_now` fired via both a scheduled tick and a direct dispatch 6ms apart, creating two real Pending Approval records for the same real action, neither ever resolved | Logic | Major | Closed | 2026-08-19 | BUGFIX-08-US-01 |
| BUG-030 | A staged email that generates a Compass-classification-failure or Route-to-Project Pending Approval is never marked/removed from the staging queue, so the next capture tick reprocesses it and creates ANOTHER duplicate Pending Approval — same root cause pattern seen in `librarian-housekeeping`'s repeated Customer-backfill proposals | Logic | Major | Closed | 2026-08-19 | BUGFIX-08-US-01 |

---

## Bug Details

<!-- One subsection per bug, added by /bug. Template:

### BUG-NNN — <title>
- **Area:** UI | Logic
- **Severity:** Blocker | Major | Minor | Cosmetic
- **Status:** Open
- **Found:** YYYY-MM-DD
- **Screen / route:** <where it occurs>
- **Repro steps:**
  1. <step>
  2. <step>
- **Expected:** <what should happen>
- **Actual:** <what happens instead>
- **Screenshot:** <path, optional>
- **Fixed by:** <BUGFIX-NN-US-01, once triaged>
-->

### BUG-001 — Email notes don't wikilink to their sender's Person note
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-11
- **Screen / route:** N/A (backend/vault content, not a UI screen) —
  `Work/<Kind>/*.md` Email notes (and, prospectively, `Work/Meetings/*.md`
  once `REQ-SB-08` builds).
- **Repro steps:**
  1. Open any already-captured Email note under `Work/<Kind>/` in Obsidian
     (e.g. `Work/Emails/`).
  2. Note its frontmatter carries `sender` / `sender_email` as plain string
     fields, and a matching Person note already exists at
     `Work/People/<sender_email>.md` (created by `REQ-SB-10`'s per-write
     hook, `people_extraction.ensure_person_note_for_captured_email`).
  3. Open Obsidian's Graph view, or check the Person note's backlinks
     ("Linked mentions") panel.
- **Expected:** The Email note's body contains an actual `[[PersonName]]`
  wikilink to the sender's Person note, per `MEMORY.md`'s standing
  "tags AND wikilinks, always, wherever a real link target exists" rule
  (2026-08-11) — the same convention already applied to Person→Company
  (`**Company:** [[ADNOC]]`) and already specified for the not-yet-built
  Meeting→Attendees link (`**Attendees:** [[Person1]], [[Person2]]`,
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`'s Meetings
  section — which explicitly (and, it turns out, incorrectly) assumed
  Email notes already followed "the same inline-wikilink convention").
- **Actual:** `app/business/email_classification.py`'s
  `classify_recent_emails` writes the sender only as plain frontmatter
  (`sender`, `sender_email` strings) and separately calls
  `people_extraction.ensure_person_note_for_captured_email` to create/
  update the Person note as a side effect — the Email note's body never
  gets a wikilink back to it. Every already-captured Email note (49+
  before this session's in-progress full-inbox pull) has this gap; the
  corresponding Person notes render as disconnected nodes in Obsidian's
  graph relative to every Email that actually mentions them.
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-01-US-01

### BUG-002 — Agents Map: sections with 4+ agents visually spill into neighboring sections
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-11
- **Screen / route:** Agents Map (`/`), `AgentsMapCanvas.tsx` / `layoutAgents.ts`
- **Repro steps:**
  1. Have (or move) 4+ agents into the same Section via Settings' Sections
     area or the Agent Settings surface's Section picker.
  2. View the Agents Map.
  3. Observe agent nodes and their labels rendered outside their own
     section's angular wedge, overlapping neighboring sections' nodes,
     Hub labels, and section-title text.
- **Expected:** An agent always renders within its own section's visual
  territory, regardless of how many agents share that section or how many
  sections currently exist; labels never overlap another section's nodes
  or text.
- **Actual:** `layoutAgents.ts`'s `SECTION_ARC_SPAN_DEG` is a fixed 80°
  arc that every section's agents fan out across, regardless of how many
  sections actually exist. With `N` sections evenly spaced around 360°,
  each section only owns `360/N` degrees (72° at `N=5`) — a fixed 80° span
  already exceeds that at `N=5` before even accounting for agent count,
  and gets worse as more sections are added or more agents pile into one
  section (real repro: all 5 seeded agents currently sit in "Technical",
  confirmed visually spilling into "Customers"/"Products" territory with
  heavy label collision).
- **Screenshot:** N/A (confirmed via live browser screenshot against the
  real running app, 2026-08-11)
- **Fixed by:** BUGFIX-02-US-01

### BUG-003 — `insert_body_line_if_missing` corrupts notes whose body lacks the blank line after frontmatter
- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-08-11
- **Screen / route:** N/A (backend/vault content) — `app/data_access/
  vault_writer.py::insert_body_line_if_missing`, used by
  `customer_hub_linking.link_note_to_customer_hub`,
  `partner_hub_linking.link_note_to_partner_hub`, and any other caller
  that inserts a line into an existing note's body.
- **Repro steps:**
  1. Have a note whose body does not have a blank line immediately after
     the frontmatter's closing `---` (i.e. it does not follow
     `write_note()`'s own `"---\n\n<body>"` convention — e.g. a note
     hand-edited outside that convention).
  2. Call any code path that invokes `insert_body_line_if_missing` against
     that note (e.g. `link_note_to_customer_hub`/`link_note_to_partner_hub`,
     triggered by a real capture run).
  3. Repeat step 2 (a second capture run, or any other caller hitting the
     same note again).
- **Expected:** The inserted line lands at the true start of the note's
  existing body content, regardless of whether a blank line follows the
  frontmatter; repeated calls never corrupt previously-written content.
- **Actual:** `insert_body_line_if_missing` computes the insertion point
  as a **fixed offset** from the frontmatter's closing `---`
  (`body_start = end + 6`), assuming the blank-line convention always
  holds. On a note that lacks it, every insertion lands at the same fixed
  byte offset regardless of what's actually there — landing mid-word or
  mid-line rather than at the true body start. Each subsequent call
  compounds the corruption further rather than being a one-off. One real
  note (`Work/People/karimlouis@microsoft.com.md`) was found in this
  corrupted state during `REQ-SB-16-US-01-T04`'s live verification
  (2026-08-11) — a stray character glued onto a wikilink, plus a separate
  orphaned text fragment — and was manually, byte-exact repaired as part
  of that task's own due diligence (not a code fix). A vault-wide sweep
  at the time found no other note in this state, but the underlying
  primitive defect remains and could resurface on any future
  manually-edited note.
- **Screenshot:** N/A
- **Fixed by:** —

### BUG-004 — Agents Map: an agent node renders directly on top of a neighboring Section's Hub
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-12
- **Screen / route:** Agents Map (`/`), real running app (`src/frontend`,
  not the prototype) — `AgentsMapCanvas.tsx`/`layoutAgents.ts`/
  `polarLayout.ts`. Found on the real app after `BUGFIX-02-US-01`
  (`SPRINT-016`) already shipped and was live-verified against a
  4-agent-in-one-Section case — this is a different, not-yet-covered
  repro shape: a 5-agent Section including a Producer-type agent.
- **Repro steps:**
  1. Have a Section with 5 agents assigned, including at least one
     Producer-type agent (today's real data: "Productivity" section — 3
     Worker, 1 Expert, 1 Producer).
  2. View the Agents Map overview (not the drill-down).
  3. Inspect the Producer-type agent's rendered position relative to a
     neighboring Section's Hub.
- **Expected:** Every agent renders within its own Section's angular
  territory and never overlaps a different Section's Hub or any other
  node.
- **Actual:** Confirmed via direct DOM measurement in a real browser
  session (not just visual inspection): `People Notes` (Productivity,
  Producer-type) renders at `{x:703-738, y:223-258}`, which is entirely
  contained within `Customers Hub`'s own bounding box
  (`{x:682-759, y:188-265}`) — the two nodes fully overlap. `BUGFIX-02-US-01`'s
  own fix and live verification only exercised same-Section spillover
  among same/adjacent nodes at one ring (all-Worker), not this
  Producer-ring-into-neighboring-Hub case.
- **Root cause, confirmed on investigation:** `polarLayout.ts`'s
  `HUB_RADIUS` (32) was almost the same radial distance as
  `RING_RADIUS.producer` (30) — only 2 units apart — while the Hub's own
  visual size (`.hub-node`, 11% width ⇒ ~5.5-unit radius) meant its disk
  physically overlapped the entire Producer ring band, regardless of
  angular position. Any Producer-type agent could render inside a
  neighboring Section's Hub.
- **Screenshot:** N/A (confirmed via `getBoundingClientRect()` measurement,
  2026-08-12)
- **Fixed by:** direct fix, 2026-08-12 (operator-directed Hub resize/
  reposition — see `CHANGELOG.md`; not routed through `/triage` since it
  was requested and fixed live in the same pass). Re-verified: 0 overlaps
  between any agent node and any Hub across all 5 real seeded agents
  after the fix.

### BUG-005 — Agents Map: top Section title renders off-screen above the viewport
- **Area:** UI
- **Severity:** Minor
- **Status:** Open
- **Found:** 2026-08-12
- **Screen / route:** Agents Map (`/`), real running app —
  `AgentsMapCanvas.tsx`/`layoutAgents.ts` (Section title positioning).
- **Repro steps:**
  1. View the Agents Map overview in a browser at default/typical window
     size.
  2. Look for the Section title positioned at the top of the polar
     layout (12 o'clock position — today's real data: "Customers").
- **Expected:** Every Section's title is visible within the normal page
  viewport without needing to scroll above the page's own top (which is
  not possible in a standard browser).
- **Actual:** Confirmed via `getBoundingClientRect()`: the "Customers"
  title's `top` value is `-26.25px` — genuinely positioned above the
  visible viewport, unreachable by any scroll action. The canvas's own
  top-padding/margin doesn't account for a title rendered above the
  12 o'clock ring position.
- **Screenshot:** N/A (confirmed via direct DOM measurement, 2026-08-12)
- **Fixed by:** —

### BUG-006 — Agents Map: Worker and Expert rings have zero gap, agents visually read as the same ring
- **Area:** UI
- **Severity:** Minor
- **Status:** Open
- **Found:** 2026-08-12
- **Screen / route:** Agents Map (`/`), real running app —
  `polarLayout.ts`'s `RING_RADIUS` constants.
- **Repro steps:**
  1. View the Agents Map overview with a Section containing both a
     Worker-type and an Expert-type agent (today's real data:
     "Productivity" — 3 Worker, 1 Expert).
  2. Visually compare the Expert agent's radial position against the
     Worker agents'.
- **Expected:** The three rings (Worker outermost, Expert middle,
  Producer innermost) read as visually distinct bands, per the design's
  own "Worker ring (outermost)... Expert ring (middle)... Producer ring
  (innermost)" legend.
- **Actual:** Confirmed via measurement: the Worker ring's radius is
  ~350px, the Expert ring's is ~315px; each node is ~35px in diameter
  (17.5px radius). The Worker ring's own inner edge (350 - 17.5 = 332.5)
  and the Expert ring's outer edge (315 + 17.5 = 332.5) land at the exact
  same distance from center — zero gap between the two rings' node
  bounding circles, so an Expert-ring agent (`Vault Q&A`) can visually
  read as sitting on the same line as the Worker-ring agents depending on
  angular position.
- **Screenshot:** N/A (confirmed via direct DOM measurement, 2026-08-12)
- **Fixed by:** —

### BUG-007 — `graph.py::_call_model` is a synchronous node with a blocking Provider call, suspected cause of a real dev-backend hang
- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-08-12
- **Screen / route:** N/A (backend) — `app/business/agent_orchestration/
  graph.py::_call_model`, invoked from `_GRAPH.ainvoke()` during
  `POST /agents/{agent_id}/chat`.
- **Repro steps:**
  1. Send a real chat message that triggers a live Provider (Compass) call
     via `_call_model`.
  2. While that call is in flight, send any other request to the same
     backend process (e.g. a plain `GET /agents`).
  3. Observed live during `REQ-SB-33-US-01-T01`'s verification
     (`SPRINT-018`, 2026-08-12): the second request also hung, and the
     first call did not resolve even after several minutes — well past
     this project's own documented Compass-latency precedent. The server
     was not crashed, just fully unresponsive; recovered only via the
     standing `MEMORY.md` specific-PID-kill-and-restart protocol.
- **Expected:** `_call_model` runs inside `_GRAPH.ainvoke()`'s otherwise
  fully-async graph; per this project's own standing `MEMORY.md`
  Constraint (established after the `REQ-SB-25`/`SPRINT-014` nested-event-
  loop chat outage), every node that makes its own real I/O call must be
  `async def` so it can't block the single asyncio event loop other
  requests share.
- **Actual:** `_call_model` is a plain, synchronous `def` node that calls
  `model.invoke(...)` — a blocking call — directly inside the async graph,
  in apparent tension with that same standing Constraint. This is the
  **plausible root cause** of the hang above, not yet conclusively
  confirmed: `graph.py` was out of `REQ-SB-33-US-01-T01`'s own file scope
  (`state.py` only) to fix or definitively prove, so this is a strong live
  correlation (one incident, one plausible mechanism), not a proven
  root-cause. See `SPRINT-018`'s own Retrospective → "What didn't work" /
  "Open follow-ups" for the full write-up, and `MEMORY.md` → Decisions for
  the unconfirmed-flag entry.
- **Update, 2026-08-12 (`SPRINT-019`/`REQ-SB-31-US-01-T01`):** still
  unconfirmed, neither strengthened nor ruled out. `T01`'s own AC-08
  verification made its one real Compass call from an isolated throwaway
  script's own event loop, not through the shared dev backend's own
  concurrent-request event loop, so it could not have reproduced or
  disproved this bug's mechanism either way — no new evidence. Still
  worth a dedicated fix pass (make `_call_model` genuinely `async def`,
  per this project's own standing async-graph-node Constraint)
  independent of any future story that happens to touch `graph.py`
  again.

### BUG-008 — App-start Outlook-COM capture in `main.py`'s lifespan has no timeout, can hang the whole server's startup indefinitely
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-12
- **Screen / route:** N/A (backend) — `app/main.py`'s FastAPI `lifespan`
  → `app/scheduling/capture_scheduler.py`'s app-start Outlook-COM capture
  pass, run unconditionally before the server accepts any HTTP request.
- **Repro steps:**
  1. Start the backend (`uvicorn app.main:app`) in an environment with no
     interactive Outlook desktop session available (e.g. this session's
     own headless build/verification environment).
  2. Observe that the server never becomes reachable — the app-start
     Outlook-COM capture call blocks the lifespan's own startup
     indefinitely, with no timeout.
  3. Confirmed live during `SPRINT-023`'s (`REQ-SB-35-US-01`) own build —
     verification had to fall back to direct Python-shell calls against
     the real `.venv`/vault instead of a live HTTP round trip, since no
     sprint ACs required the HTTP layer.
- **Expected:** The app-start capture pass should not block the server
  from becoming reachable — either a startup timeout, or making the
  app-start trigger best-effort/non-blocking (e.g. scheduled to run
  shortly after startup rather than gating it).
- **Actual:** No timeout exists; a real capture failure/hang (e.g.
  Outlook not interactively available) hangs the entire server's startup
  indefinitely, with no user-facing signal.
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-14 (not routed through `/triage` —
  same urgency-based direct-fix precedent as the `REQ-SB-25` chat bug in
  `MEMORY.md`, since it was actively blocking live verification for the
  8 sprints then in flight). Root cause confirmed live, independent of
  and broader than the original "no interactive Outlook session" repro:
  `capture_scheduler.py`'s `lifespan()` did `await
  run_capture_if_idle()` before `yield` — even when Outlook and Compass
  are fully reachable and the run eventually succeeds, the entire
  capture pass (bounded but real: ~10 items, multiple real API calls
  each) still had to finish before FastAPI considered startup complete
  and began accepting ANY HTTP request. Observed live 2026-08-14: over
  100 sequential real Compass calls before `Application startup
  complete.` fired. Fixed exactly per this bug's own "Expected" text —
  changed to `asyncio.create_task(run_capture_if_idle())`, making the
  trigger non-blocking/best-effort; capture still fires unconditionally
  on every start, per `REQ-SB-07`'s spec, it just no longer gates the
  API on finishing first. Verified live: server now answers
  `GET /agents` with `200` within ~2 seconds of start, both with and
  without `--reload`, while capture continues in the background.

### BUG-009 — Agents Map overview: agents fan out past their own Section's wedge boundary into a neighboring Section
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-13
- **Screen / route:** Agents Map overview (`/`) — `src/frontend/src/
  features/agents-map/layoutAgents.ts::layoutAgents`.
- **Repro steps:**
  1. Open the Agents Map overview (not a Section drill-down).
  2. Look at the Productivity section (5 sections exist today, evenly
     spaced at 72° apart; Productivity currently has 6 agents).
  3. Confirmed live via direct DOM measurement (agent-node/section-title
     bounding rects, angle computed from the shared Knowledge Base
     center): `Email Capture` (Section: Productivity, hub angle -18°)
     renders at -58°, inside the Customers section's own wedge
     (-126° to -54°), not Productivity's own wedge (-54° to 18°).
- **Expected:** An agent never renders outside its own Section's wedge on
  the overview.
- **Actual:** `layoutAgents.ts`'s `SECTION_ARC_SPAN_DEG` is a fixed 80°
  fan-out per section, applied regardless of how many sections exist.
  With `n` sections evenly spaced, each section's own wedge is only
  `360/n` degrees wide — 72° for the current 5 sections — narrower than
  the fixed 80° fan-out. Any section whose agents fan out near the
  extremes (first/last agent when `count` is large enough) overflows the
  wedge by `(80 - 360/n) / 2` degrees per side (4° per side at `n=5`,
  worse as `n` grows or more sections are added).
- **Screenshot:** N/A (confirmed via direct DOM angle computation,
  2026-08-13)
- **Fixed by:** Direct fix, 2026-08-13 (operator-directed live fix, not
  routed through `/triage`) — `SECTION_ARC_SPAN_DEG` replaced with a
  span computed as `min(80deg, (360/n) * 0.8)`, capping the per-section
  fan-out at 80% of that section's own wedge width regardless of how
  many sections exist. Re-verified live: `Email Capture` now renders at
  -47° (within Productivity's -54°..18° wedge, was -58°); `Vault Filing
  Expert` now at 11° (was 22°, past the wedge's own +18° edge).

### BUG-010 — Agents Map overview: on hover, an agent's Type and Name labels render at the identical position, directly overlapping
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-13
- **Screen / route:** Agents Map overview (`/`) — `src/frontend/src/
  styles/agents-map.css`, the `.agent-node--compact:hover` reveal rule.
- **Repro steps:**
  1. Open the Agents Map overview (agents render as small `.agent-node
     --compact` dots at this zoom level).
  2. Hover over (or focus) any agent dot.
  3. Observe the revealed Name and Type labels.
- **Expected:** The agent's Name and Type labels are both legible,
  stacked vertically, on hover.
- **Actual:** `.agent-node--compact:hover .agent-node-label` and
  `.agent-node--compact:hover .agent-node-type` share the identical
  positioning rule (`top: 100%; left: 50%; transform:
  translateX(-50%);`), with no vertical offset differentiating the two
  — both render at the exact same position below the node, directly on
  top of each other, illegible.
- **Screenshot:** N/A (confirmed via direct CSS source inspection,
  2026-08-13)
- **Fixed by:** Direct fix, 2026-08-13 (operator-directed live fix, not
  routed through `/triage`) — the label rule kept its `top: 100%;
  margin-top: 4px`; the type rule changed to `top: calc(100% + 1.9em);
  margin-top: 4px`, offsetting it below the label's own reveal box.
  Re-verified live with real rendered text ("Email Capture" /
  "worker"): label renders top 214.4–bottom 236.0, type renders top
  239.0–bottom 260.6 — a clean 3px gap, zero overlap.

### BUG-011 — `_slugify`'s 80-char truncation can silently eat a filename's disambiguating id-suffix, causing two distinct real notes to collide on the same filename stem
- **Area:** Logic
- **Severity:** Blocker (raised from Major, 2026-08-13 — see Update below: confirmed to cause real content loss, not just index-invisibility)
- **Status:** Open
- **Found:** 2026-08-13
- **Screen / route:** N/A (backend/vault content) — `app/data_access/
  vault_writer.py::_slugify` (the 80-char truncation), combined with
  `app/business/email_classification.py::classify_recent_emails`'s
  filename-stem construction (`f"{date}-{subject}-{entry_id[-8:]}"`,
  subject placed *before* the disambiguating id-suffix).
- **Repro steps:**
  1. Two distinct real Outlook items (e.g. an email and a Google
     Calendar notification forwarded as email) share an identical,
     sufficiently long subject line — long enough that the subject
     alone consumes `_slugify`'s full 80-character budget.
  2. Both get captured via `email_classification.classify_recent_emails`,
     each building a `filename_stem` as `f"{date}-{subject}-
     {entry_id[-8:]}"`.
  3. `vault_writer.write_note` passes that full string through
     `_slugify(text, max_len=80)`, which truncates to the first 80
     characters — silently cutting off the trailing `-{entry_id[-8:]}`
     disambiguating suffix entirely.
  4. Confirmed live in the real vault (2026-08-13, during
     `REQ-SB-01-US-01-T02`'s own mandated `AC-01` verification): 503
     real note files under `Work/`, but only 502 unique filename stems.
     Root-caused to exactly this pair — `Work/Emails/2026-07-30-RE- [
     Core42 @UAE ] SimplAI Agentic AI Operating System - Demo (deep
     .md` and `Work/Notifications/2026-07-30-RE- [ Core42 @UAE ]
     SimplAI Agentic AI Operating System - Demo (deep .md` — two
     genuinely distinct, correctly-captured real items (different
     `outlook_entry_id`, different sender, different
     `conversation_id`, received one second apart).
- **Expected:** Every real note has a unique filename stem; a
  disambiguating id-suffix a caller explicitly appends to avoid
  collisions must survive truncation, not be silently discarded by it.
- **Actual:** Both files exist intact on disk (no file was ever
  overwritten — they land in different kind-subfolders), but their
  **filename stems** are byte-identical, since the subject text alone
  fills `_slugify`'s entire 80-character budget before the
  `-{entry_id[-8:]}` suffix is even reached. Any stem-keyed consumer
  (confirmed live: `REQ-SB-01-US-01`'s new `vault_indexing.
  rebuild_index()`, a plain `stem`-keyed dict) silently drops one of
  the two notes on every rebuild, with no error raised — `REQ-SB-02`
  (Browse & Search, built directly on this index) would silently omit
  one of these two colliding notes from browse/search results.
- **Screenshot:** N/A (confirmed via direct vault inspection and stem
  count cross-check, 2026-08-13)
- **Fixed by:** — (recommended fix, not yet applied: compute/truncate
  the disambiguating suffix *before* the human-readable subject text,
  or hash the whole candidate string before any truncation — mirroring
  `meeting_note_filename_stem`'s own already-correct "hash before
  truncate" precedent — in either `_slugify` itself or
  `classify_recent_emails`'s own stem-construction; a real design
  choice for whichever fix story picks this up, not decided here. See
  `ESCALATIONS.md` → `ESC-027` for the full write-up.)
- **Update, 2026-08-13 (`SPRINT-028`/`REQ-SB-09-US-01-T04`, `ESC-028`) —
  severity raised, real content loss confirmed, not just index-
  invisibility.** The identical defect also affects Task notes, and
  there it's materially worse: Email/Notification's own collision
  (original finding above) landed in two *different* kind-subfolders, so
  both files survived intact on disk and only the vault-wide index
  silently dropped one. Task notes all share one flat `Work/Tasks/`
  subfolder (no Compass-classified `kind` split, per `ADR-027`), so the
  identical collision causes a literal same-path file **overwrite** — a
  real, live capture run (3 real Outlook Tasks sharing one 72-character
  subject) confirmed only the LAST of three writes survived on disk; the
  other two notes' content is genuinely gone, not just absent from the
  index. The disambiguation mechanism itself (`task_note_index.json`,
  `EntryID`-keyed) is confirmed correct in isolation — a controlled
  real short-subject pair produced two distinct, correctly-disambiguated
  notes, neither overwritten — the defect is entirely inside the shared,
  pre-existing `_slugify` function. Real production data also confirmed
  the mechanism only fails once the combined stem exceeds 80 characters
  (three distinct real 57-character-subject tasks correctly produced
  three distinct files, no truncation). See `ESCALATIONS.md` → `ESC-028`
  for the full write-up.

### BUG-012 — Mid-conversation model tool-calls bypass the working-mode approval gate for mutating Skills
- **Area:** Logic
- **Severity:** Minor
- **Status:** Open
- **Found:** 2026-08-14
- **Screen / route:** N/A (backend logic, not a UI screen) — any agent's
  embedded chat (`POST /agents/{agent_id}/chat`), specifically the
  model's own mid-conversation tool-calling path inside
  `app/business/agent_orchestration`'s conversational graph (`ADR-015`).
- **Repro steps:**
  1. Set an agent that has a mutating Skill granted (e.g. a migrated
     `run_capture_now`-equivalent, once `REQ-SB-39-US-02` ships) to
     Supervised or Manual working mode (`REQ-SB-21`).
  2. Chat with the agent in a way that causes the model itself to decide,
     on its own initiative, to tool-call that mutating Skill mid-
     conversation — not via a matched chat trigger phrase and not via the
     direct `/skills/{skill_id}/invoke` endpoint.
  3. Observe whether the Skill executes immediately.
- **Expected:** Per `REQ-SB-21`/`ADR-020`'s working-mode gate, a
  Supervised-mode mutating capability should create a pending-approval
  record instead of executing immediately; a Manual-mode agent should
  refuse outright unless the user's own chat/direct request explicitly
  asked for it.
- **Actual:** Confirmed by direct code investigation (`ADR-036`,
  2026-08-14, while scoping `REQ-SB-43`/`REQ-SB-44`'s Cockpit work — the
  same gap was already named, unresolved, in `architecture.md`'s own
  "What this pass does not decide" note under `ADR-015` when `REQ-SB-25`
  shipped): `run_agent_conversation`'s tool-execution path
  (`_execute_tools`) calls the bound MCP tool directly via
  `tool.ainvoke(...)`. This path never calls
  `skill_registry.invoke_skill` — only `mcp_client.load_agent_tools`'s
  access-grant filter (`has_skill_access`) applies. A Supervised or
  Manual agent's mutating Skill therefore executes immediately and
  ungated when the model itself chooses to tool-call it — no
  pending-approval record, no Manual-mode refusal — even though the
  identical Skill invoked via the direct/chat-keyword-match dispatch
  path (`agents_router.py`'s `_invoke_capability` /
  `skills_router.py`'s invoke endpoint) IS correctly gated.
- **Screenshot:** N/A
- **Fixed by:** — (operator decision, 2026-08-14: log now, do not fix as
  part of `REQ-SB-42`/`REQ-SB-43`/`REQ-SB-44` — out of scope for that
  batch; `ADR-036` deliberately declines to close this for ordinary chat,
  calling it "separate future work." A future fix would need to route
  the graph's own tool-execution path for any `skill_tools.SKILLS`-member
  id through `skill_registry.invoke_skill`'s gate instead of calling
  `tool.ainvoke(...)` directly — a real design/mechanism decision for
  whichever fix story picks this up, not decided here.)


### BUG-013 — `skill_registry._load_state` re-applies the migration seed on every read, silently un-revoking a migration-seeded Skill right after a real revoke
- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-08-14
- **Screen / route:** N/A (backend logic, not a UI screen) — `DELETE
  /agents/{agent_id}/skills/{skill_id}` (`skills_router.py`), and
  equally the AgentDetailPanel Capabilities section's per-row/multi-
  select Revoke affordances that call it (`REQ-SB-48-US-01-T02`).
- **Repro steps:**
  1. Pick any agent + Skill id pair from `skill_registry._MIGRATION_GRANT_SEED`
     (e.g. `email-capture` / `view_last_run`, currently granted).
  2. Call `skill_registry.revoke_skill_access('email-capture',
     'view_last_run')` directly (or click Revoke on that row in the real
     UI) — the call returns `True`/`{"revoked": true}`.
  3. Immediately re-read the agent's capabilities (`list_agent_skills`/
     `list_agent_capabilities`, or refetch `GET /agents/email-capture`).
- **Expected:** The revoked Skill (`view_last_run`) no longer appears in
  the agent's granted Skills, exactly as it would for any non-migration-
  seeded Skill/agent pair (confirmed working correctly for those — e.g.
  `ask_question`/`view_channel_status` revoke from `email-capture` behaves
  correctly and durably).
- **Actual:** Confirmed live, twice independently (a direct Python-shell
  call with zero UI/frontend involvement, and a real CDP-driven browser
  round trip against the actual running app) — the Skill reappears as
  granted on the very next state read, with no further user action.
  Root cause: `_load_state()` unconditionally re-applies EVERY entry in
  `_MIGRATION_GRANT_SEED` (via `grant_skill_access`'s own idempotent
  "only append if not already granted" logic) on every single call, not
  just once, ever, the first time `agent_skills.json` is created. This
  was already a latent risk in `_load_state()`'s own docstring ("runs on
  every read") but its real behavioral consequence — that an EXPLICIT
  revoke of one of the 7 migration-seeded ids
  (`view_last_run`/`ask_question`/`view_channel_status`/
  `run_capture_now`/`pause_schedule`/`rebuild_person_note`/
  `build_knowledge`) against one of its own named seed agents can never
  actually stick — was not caught until this sprint's own live
  multi-select-revoke verification (`REQ-SB-48-US-01-T02`, `AC-06`)
  needed a genuine, durable revoke to check against.
- **Screenshot:** N/A
- **Fixed by:** — (found live during `REQ-SB-48-US-01-T02`'s own AC-06
  verification, 2026-08-14; out of scope for that task — the defect is
  entirely inside `_load_state`/`_MIGRATION_GRANT_SEED`, a function
  neither `REQ-SB-48-US-01-T01` nor `-T02` touches or is allowed to touch
  per their own `## Files to Modify`. AC-06 was instead verified live
  using a Skill/agent pair NOT in `_MIGRATION_GRANT_SEED` (durable,
  correct revoke confirmed). A future fix should make the seed apply-once
  — e.g. gated on a persisted `"migration_seed_applied": true` flag in
  `agent_skills.json`, mirroring how a one-time migration is usually
  guarded elsewhere in this codebase — not decided here.)

### BUG-014 — Thread email attachments are never captured, and the underlying save path has no filename-collision protection
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend logic) —
  `src/backend/app/data_access/outlook_com.py` (email fetch),
  `src/backend/app/business/pipelines/email_capture_pipeline.py`
  (`_summarize_attachment_node`), `src/backend/app/data_access/
  vault_writer.py::write_attachments`.
- **Repro steps:**
  1. Send/receive a real email with a genuine file attachment into an
     Outlook conversation that the email-capture pipeline will process.
  2. Let the pipeline capture it (scheduled tick or manual
     `run_capture_now`).
  3. Open the resulting Thread note (`Work/Threads/<conversation-id>.md`)
     and check for a `## Attachments` section; check
     `Work/Threads/attachments/` on disk.
- **Expected:** The attachment is saved under
  `Work/Threads/attachments/<thread-slug>/...`, summarized, and appears
  as a dated sub-entry under a `## Attachments` section in the Thread
  note (per `REQ-SB-55-US-01`'s own `Summarize-Attachment` Job design).
- **Actual:** Confirmed live against real vault data, 2026-08-17: a real
  captured Thread (`01D26A7530444A23803A002210620160.md`) whose own
  source email body literally reads "Please find attached a short
  presentation..." has NO `## Attachments` section at all, and
  `Work/Threads/attachments/` does not exist anywhere in the vault.
  **Root cause:** `outlook_com.py` never reads a `MailItem`'s
  `Attachments` COM collection — the word "attachment" does not appear
  anywhere in that file. `email_capture_pipeline.py::
  _summarize_attachment_node` loops `for attachment in email.get(
  "attachments") or []:` — since `list_recent_mail` never populates an
  `"attachments"` key, this is always `None or []`, an empty loop, on
  every real email regardless of whether it actually has attachments.
  The entire `Summarize-Attachment` Job has been a structural no-op
  since it shipped (`SPRINT-049`).
  **Second, downstream defect** (confirmed by direct code reading, not
  yet live-triggered since nothing reaches this path today):
  `vault_writer.py::write_attachments` (line ~484) writes
  `attachments_dir / filename` and calls `file_path.write_bytes(...)`
  unconditionally — no existence check, no collision handling of any
  kind, silently overwriting on a same-filename collision. This is a
  real, likely-frequent risk specifically for Threads once fixed:
  corporate emails routinely carry generically-named inline
  signature/logo images (`image001.png`, `image002.png`, ...) that would
  recur across nearly every message in a multi-message thread, silently
  clobbering each other under today's flat `attachments/<thread-slug>/
  <filename>` layout. This directly contradicts the collision-handling
  convention this SAME file already established one function below
  (`move_note_and_attachments`: "Refuses to silently overwrite an
  existing file at the destination — a genuine collision should surface,
  not disappear one of the two notes").
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-03-US-01 (`Done`, `SPRINT-055`, 2026-08-17).
  Gap 1's originally-stated root cause ("`outlook_com.py` never reads
  `Attachments`") was directly contradicted by live code re-reading at
  triage time — see `ESCALATIONS.md` → `ESC-041` (`Resolved`). The REAL
  gap-1 mechanism, confirmed by direct reading of the live pipeline chain:
  `_summarize_attachment_node` only ever appended an entry into
  `attachment_entries` when `summarize_attachment` returned a real
  `dated_entry` — every other real outcome (oversized/unsaved, saved but
  unsummarizable) silently vanished with no fallback, no log. **Fixed,
  `BUGFIX-03-US-01-T01`:** `_summarize_attachment_node` now synthesizes a
  visibly-distinct fallback `## Attachments` entry (via new
  `_fallback_attachment_entry`) whenever no real `dated_entry` was
  produced, restoring the honest-signal convention
  `classify_recent_emails` already established. Gap 2 (no filename-
  collision protection) confirmed exactly as originally described.
  **Fixed, `BUGFIX-03-US-01-T02`:** `write_attachments` now requires a
  `message_segment: str` parameter and nests its save path/`relative_link`
  one level deeper by `_slugify(message_segment)` —
  `Work/Threads/attachments/<thread-slug>/<slug-of-received>/<filename>`
  instead of the old flat `attachments/<thread-slug>/<filename>` — so two
  different messages in the same Thread sharing an attachment filename
  (e.g. recurring `image001.png` signature images) can never silently
  overwrite each other. Both live call sites
  (`summarize_attachment`/`classify_recent_emails`) updated. Live-verified
  end-to-end against the real configured vault: two same-filename,
  genuinely-different-content attachments across two messages in the same
  real Thread both survived intact on disk under distinct nested paths,
  and the Thread note gained two separate dated `## Attachments`
  sub-entries; a third, non-colliding attachment confirmed no regression.
  Full evidence: `Implementation/Tasks/BUGFIX-03-US-01-T02-per-message-attachment-nesting.md`
  → `## Implementation Log`. **Known follow-up (non-blocking, tracked
  separately):** verifying this fix surfaced a real, previously
  unconsidered consequence for `app/business/cockpit/attachments.py`
  (Inbox Cockpit) — see `ESCALATIONS.md` → `ESC-043` and
  `REVIEW-QUEUE.md` (recommends a new `/bug` capture).

### BUG-015 — `compass_client.classify_email` consistently fails for 3 specific real emails, even after retries
- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend logic) —
  `src/backend/app/data_access/compass_client.py::classify_email`,
  called from `email_capture_pipeline.py`'s per-email loop.
- **Repro steps:**
  1. Run the real email-capture pipeline against the live inbox
     (`POST /agents/email-capture-pipeline/actions/run_capture_now`, or
     directly call `email_capture_pipeline.run_email_capture_pipeline()`).
  2. Observe the per-item results list.
- **Expected:** Every fetched, not-yet-processed email is classified and
  filed (or fails once and clearly recovers on a later retry).
- **Actual:** Confirmed live, three independent runs in direct succession
  (including one with a new 3-attempt retry-with-backoff added to
  `classify_email` specifically to rule out transience) — the EXACT same
  3 real emails fail every single time, with varying but consistently
  Compass-side errors:
  - "RE: Azure-Net New Revenue Forecast for H2 for AM Updates" —
    `httpx` read timeout (30s) on every attempt.
  - "RE: Weekly Forecast l Major Clients" — Compass returns a genuinely
    empty response body (`Expecting value: line 1 column 1 (char 0)`) on
    most attempts, a forcibly-closed connection on others.
  - "RE: Weekly Forecast l Strategic Clients" — same failure family.
  All three are large, densely-structured recurring "Forecast" reports
  (per the vault's own real content — dozens of accounts, per-segment
  metrics, tabular data). Other real emails in the same batch classify
  successfully every time (confirmed via real `200 OK` Compass responses
  in the same runs). Retrying does NOT help — ruled out as transient
  network/rate-limit flakiness; something about these 3 specific
  messages' real content reliably defeats Compass. Since a failed email
  is never marked processed (by design), these 3 are silently re-fetched
  and re-failed on every single capture tick, forever, with no operator
  visibility beyond the (now-fixed, see below) history count.
  **Not yet found:** the exact content mechanism (encoding artifact from
  HTML-table extraction, body length/structure past what the 4000-char
  cap alone would suggest, or something Compass-side) — deeper
  investigation would need to inspect the exact raw body bytes being
  sent for these 3 messages specifically.
- **Screenshot:** N/A
- **Fixed by:** — two partial mitigations already shipped as DIRECT fixes
  (not through a BUGFIX story, applied live 2026-08-17 while
  investigating): (1) `email_classification.py::run_capture_and_record_
  completion` no longer mislabels a failed email as "filed" in its own
  history text — now honestly reports `"N email(s) filed, M failed (will
  retry next run)"`; (2) `classify_email` gained a 3-attempt retry with
  backoff (confirmed live NOT to fix these 3 specific emails, but a
  reasonable general resilience improvement for genuinely transient
  failures). The underlying root cause for these 3 specific messages
  remains unresolved and open for a future investigation session (needs
  raw body inspection).

  **Update, 2026-08-17 — raw body inspected directly, no client-side
  smoking gun found.** Pulled all 3 real message bodies via
  `outlook_com.list_recent_mail` and inspected them directly (length,
  non-ASCII/control-character scan, raw repr of the first 300 chars).
  All three are ordinary, well-formed real corporate email text —
  properly UTF-8-decoded Python strings, zero control characters, one
  wholly unremarkable non-ASCII character (a curly apostrophe, U+2019,
  in "today's meeting" — not a plausible failure cause, every JSON/HTTP
  stack handles this trivially). The one real structural outlier: "RE:
  Azure-Net New Revenue Forecast for H2 for AM Updates" is 33,845 chars
  built around a dense, highly repetitive table (Account Name/
  Engagement/Account Manager × monthly columns, many accounts) — even
  truncated to the existing 4000-char cap, this remains a plausible
  (though unproven from the client side) explanation for why THAT one
  specifically times out. The two "Weekly Forecast l
  Major/Strategic Clients" emails are short (6.2-6.4KB) and structurally
  unremarkable meeting notices — no explanation found for their empty-
  response failures from content inspection alone. **Conclusion:** this
  does not look like a client-side data/encoding defect we can fix by
  sanitizing the request further; it looks like Compass-side behavior
  (moderation/rate-limit/backend quirk) that would need investigation
  from the Compass API side to resolve. No further code fix attempted
  this session — closing out this round of investigation here.

### BUG-016 — An attendee resolving to a legacyExchangeDN address crashes `classify_recent_meetings`, aborting the whole meeting-capture run
- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend logic) — `src/backend/app/data_access/
  outlook_com.py::_resolve_attendees`, `src/backend/app/business/
  people_extraction.py::ensure_person_note`, `src/backend/app/
  data_access/vault_writer.py::create_person_note_baseline`, all invoked
  from `src/backend/app/business/meeting_classification.py::
  classify_recent_meetings`.
- **Repro steps:**
  1. Have a real calendar meeting whose attendee list includes at least
     one recipient whose Exchange identity cannot be resolved to a real
     SMTP address via `recipient.AddressEntry.GetExchangeUser()` (e.g. a
     mail-enabled security group, a stale/migrated internal recipient, or
     any other case where that COM call fails or returns nothing) — its
     raw `recipient.Address` is a legacyExchangeDN-style string (e.g.
     `/o=ExchangeLabs/ou=Exchange Administrative Group (...)/cn=
     Recipients/cn=...`), not a normal `name@domain` address.
  2. Run the real meeting-capture pipeline against the live Outlook
     calendar (`classify_recent_meetings`, e.g. via
     `run_capture_now`/scheduled tick).
  3. Observe the run for that meeting (and every other meeting in the
     same batch, processed after it).
- **Expected:** A single attendee whose address can't be resolved to a
  normal SMTP-style email should not stop the rest of the run — either
  the Person note falls back to a usable identity (e.g. the attendee's
  display name) or is honestly skipped for that one attendee with a
  clear skip reason, and every other meeting in the batch still
  processes normally.
- **Actual:** Confirmed live during `REQ-SB-56-US-01-T01`'s own
  end-to-end verification against real, live Outlook data (2026-08-17,
  see that task's own Implementation Log): `_resolve_attendees` defaults
  `address = recipient.Address` and only overwrites it with
  `exch_user.PrimarySmtpAddress` when `GetExchangeUser()` both succeeds
  and returns a truthy object — when it doesn't, the raw
  legacyExchangeDN string passes straight through as the attendee's
  `"email"`, with no display-name fallback anywhere in that function.
  That value reaches `people_extraction.ensure_person_note(name, email)`,
  which calls `vault_writer.create_person_note_baseline(name, email,
  tags)` with `filename_stem=email.lower()`. After `_slugify` (which
  replaces `\/:*?"<>|` with `-`), the resulting path looked like
  `Work/People/-o=exchangelabs-ou=...-cn=recipients.md` — writing to it
  raised `FileNotFoundError` inside `ensure_person_note`. That exception
  is uncaught anywhere between there and `classify_recent_meetings`, so
  it propagates all the way up and aborts the entire batch run — every
  other meeting queued in that same pass also fails to process, not just
  the one meeting with the unresolvable attendee. Root-caused live but
  worked around (not fixed) by mocking the calendar-event source for that
  task's own regression check, since fixing it was out of that task's
  declared file scope.
- **Screenshot:** N/A
- **Fixed by:** — (recommended fix, not yet applied: give
  `_resolve_attendees` a display-name fallback for the Person note's own
  identity/filename when `GetExchangeUser()` doesn't yield a real SMTP
  address, or have `ensure_person_note`/`classify_recent_meetings` catch
  a per-attendee note-creation failure and skip just that attendee with
  an honest skip reason instead of letting it crash the whole run — a
  real design choice for whichever fix story picks this up, not decided
  here.)

### BUG-017 — `_is_inline_attachment` false-positives on real, standalone attachments carrying a MIME Content-ID
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend logic) —
  `src/backend/app/data_access/outlook_com.py::_is_inline_attachment`
  (and its caller `_extract_attachments`).
- **Repro steps:**
  1. Receive a real email whose attachment was sent by a mail system
     that stamps a MIME Content-ID on real, standalone attachments (not
     just genuinely-inline signature/logo images) — confirmed live with
     a real 4.96MB PDF, "260816 Agentic academy v06_shared.pdf".
  2. Run the real email-capture pipeline against it.
  3. Check the resulting Thread note for a `## Attachments` entry, or
     `Work/Threads/attachments/` for the saved file.
- **Expected:** The real attachment is saved and summarized.
- **Actual:** Confirmed live during `BUGFIX-03-US-01-T01`'s own
  investigation (2026-08-17): `_is_inline_attachment` treated ANY
  non-empty `PR_ATTACH_CONTENT_ID` value as sufficient proof an
  attachment is inline, filtering it out before the pipeline ever saw
  it — no fallback entry, no log, completely silent. This directly
  explained why the historical "Presight Agent Academy Demo" Thread
  never captured its own real attachment despite the source email
  literally saying "Please find attached a short presentation..."
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-17. `_is_inline_attachment` now
  requires the Content-ID to be genuinely REFERENCED inline in the
  message's own HTML body (`item.HTMLBody`) via a `cid:` URL (e.g.
  `<img src="cid:...">`) — not just present as a property. A
  Content-ID that exists but isn't referenced now falls through to the
  existing filename-based heuristics, same as an attachment with no
  Content-ID at all. Verified live against the real mailbox both
  directions: the previously-dropped real PDF now correctly resolves
  `is_inline=False`; a sample of genuinely-inline images
  (`image001.png`, `image001.jpg`, `image002.png`, `image003.png`,
  multiple `thumbnail_emailsignature_*`/`logo_*` files) all still
  correctly resolve `is_inline=True` — no regression to the existing
  filter. Full-inbox scan: 81 real attachments now correctly
  recognized, 1747 genuinely-inline images still correctly filtered.

### BUG-018 — Inbox Cockpit's attachment lookup broke silently after BUGFIX-03-US-01-T02's per-message nesting
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** Inbox Cockpit — `app/business/cockpit/attachments.py`
  (`list_attachments`/`hand_off_attachment_to_chat`), reachable via
  `cockpit_router.py`'s `GET .../attachments` and
  `POST .../attachments/{filename}/hand-off`.
- **Repro steps:**
  1. Capture a real email with an attachment via the still-live
     `classify_recent_emails` path (`/poc/classify-emails`) after
     `BUGFIX-03-US-01-T02` shipped (which made `vault_writer.
     write_attachments` require a `message_segment`, nesting saves one
     level deeper: `.../attachments/<stem>/<slug-of-segment>/<filename>`
     instead of the old flat `.../attachments/<stem>/<filename>`).
  2. Open that email in Inbox Cockpit, try to view/hand off its
     attachment.
- **Expected:** The attachment is listed and can be handed off, same as
  before.
- **Actual:** Confirmed via `ESC-043` (found live during
  `BUGFIX-03-US-01-T02`'s own verification, before this fix):
  `cockpit/attachments.py::_attachments_dir` still assumed the OLD flat
  layout — `list_attachments` silently returned `[]`,
  `hand_off_attachment_to_chat` silently returned
  `{"status": "not_found"}`. No exception, no log — a genuine,
  currently-reachable functional loss for any email captured after the
  nesting change. Already-saved historical attachments (real, on disk,
  still flat) were unaffected by this specific bug — only future
  captures would have silently lost Cockpit visibility.
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-17. New
  `_iter_attachment_files(email_note_stem)` generator supports BOTH
  shapes: yields files sitting directly in the attachments directory
  (the real, already-saved historical flat shape — untouched, never
  migrated) AND files one level deeper inside any per-message-segment
  subdirectory (the new nested shape). `list_attachments`/
  `hand_off_attachment_to_chat` both now compose this generator instead
  of assuming a flat directory. Chosen over threading the exact
  `message_segment` value through Cockpit's own path resolution (the
  other candidate from `ESC-043`) since it needs no new coupling and
  `classify_recent_emails` only ever writes exactly one segment per
  email note, so the glob is unambiguous. Verified live against the
  real vault: a real historical flat attachment
  ("Product Exhibit 2 - Compass Core42 210726.docx") still found
  correctly; a scratch nested attachment (mirroring the new shape)
  also found correctly, both list and hand-off paths confirmed, scratch
  data cleaned up afterward.

### BUG-019 — `REQ-SB-69-US-01-T06`'s human-readable Thread filenames silently broke Link-to-Thread's PRIMARY strategy in `meeting_classification.py`
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend/vault content) —
  `app/business/meeting_classification.py::_link_to_thread_by_conversation_id`
  (`REQ-SB-56-US-01`'s Link-to-Thread Job, PRIMARY strategy), invoked
  from `classify_recent_meetings`.
- **Repro steps:**
  1. Capture a brand-new email Thread AFTER `REQ-SB-69-US-01-T06`
     shipped (`ADR-046` Decision 7 — Thread filenames become
     `<thread_name>-<date>-<hash8>.md` instead of the old
     `<slug-of-conversation_id>.md`).
  2. Capture a real Meeting whose own `conversation_id` matches that
     Thread's.
  3. Observe `_link_to_thread_by_conversation_id`'s own
     `vault_writer.thread_note_exists(conversation_id)` check.
- **Expected:** The Meeting's `thread` frontmatter field is set to the
  matching Thread's `conversation_id` via the PRIMARY (exact-match)
  strategy, same as before `ADR-046`.
- **Actual:** Found live during `REQ-SB-69-US-01-T06`'s own
  verification (grep across `src/backend` for other real callers of the
  soon-to-be-superseded `thread_note_exists`/`thread_note_path`, not just
  the one call site `ADR-046`/`T06` named). `ADR-046`'s own Consequences
  section characterizes those two functions as "becoming dead code" —
  factually wrong: `meeting_classification.py` is a real, live, unnamed
  second caller. `thread_note_exists(conversation_id)` checks the OLD
  deterministic `Work/Threads/<slug-of-conversation_id>.md` path, which a
  brand-new, post-`ADR-046` Thread never lives at (confirmed live:
  `thread_note_exists(conv)` returns `False` for a genuinely-existing
  Thread whose `resolve_thread_note_path(conv)` correctly resolves it) —
  so this primary strategy silently fails for every future new Thread,
  permanently falling through to `T02`'s own weaker date-proximity
  fallback heuristic. No exception, no log. Meetings linked to Threads
  captured BEFORE `ADR-046` (still at their old filename) are unaffected.
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-17. `_link_to_thread_by_conversation_id`'s
  existence check changed from `vault_writer.thread_note_exists(
  conversation_id)` to `vault_writer.resolve_thread_note_path(
  conversation_id) is not None` — the same real, current-path lookup
  `T05`/`T06` already built and live-verified for `thread_match_merge`
  itself, applied here as a one-line, surgical fix (this function never
  used the OLD helper's own returned path, only its boolean existence
  signal, so no other change was needed). Verified live: created a real
  disposable post-`ADR-046` Thread, confirmed
  `_link_to_thread_by_conversation_id` now returns `True` and correctly
  writes the Meeting's own `thread` frontmatter field; scratch data
  cleaned up afterward. See `ESCALATIONS.md` → `ESC-044`.

### BUG-020 — `process_staged_email`'s handler mislabeled every failed staged email as "filed"
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend) — `app/business/skill_tools.py::
  process_staged_email`, the new capability `REQ-SB-69-US-01-T04` built
  tonight, dispatched via `POST /agents/email-capture-pipeline/actions/
  process_staged_email` (or the scheduled tick).
- **Repro steps:**
  1. Stage a real email whose Compass classification call fails (e.g.
     one of `BUG-015`'s known 3 "Forecast"-style emails).
  2. Trigger `process_staged_email`.
  3. Read the returned `message` / the recorded history entry.
- **Expected:** A failed staged email is honestly reported as failed —
  mirroring `email_classification.run_capture_and_record_completion`'s
  own already-fixed `history_text` split (`filed`/`failed`, see that
  function's own comment, dated earlier the same day).
- **Actual:** `process_staged_email`'s handler did
  `f"Done — {len(results)} email(s) filed."` on the raw `results` list
  from `run_email_capture_pipeline()`, which includes one
  `{"subject": ..., "error": ...}` entry per failed item (`T03`'s own
  honest per-item failure funnel, never an exception escaping the
  loop) — every failed item was counted as filed. Found live tonight
  while investigating why 4 real, genuinely-staged emails (3 of them
  `BUG-015`'s own known failures, confirmed by inspecting the staged
  `email.json` subjects directly) kept being reported "Done — 4
  email(s) filed" across 5 separate real runs while `Work/Threads/`
  and the staging directory both stayed completely unchanged — the
  exact same silent-mislabeling bug class `email_classification.py`'s
  own comment already names as a previously-fixed regression, freshly
  reintroduced in the new capability built earlier tonight.
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-17. `process_staged_email` now
  splits `results` into `filed`/`failed` (same `"error" not in r`/
  `"error" in r` filter as the already-fixed sibling function) before
  building its message, and reports both counts honestly. Verified
  live: re-ran against the same 4 real staged emails after the fix —
  correctly reported `"Done — 0 email(s) filed. 4 failed (will retry
  next run)."`, matching `BUG-015`'s own known, still-open failure
  pattern exactly, and all 4 items correctly remained staged for
  retry (no data loss).

### BUG-021 — `thread_match_merge`'s rename check produced a literal "None" filename for any pre-`ADR-046` Thread
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-17
- **Screen / route:** N/A (backend/vault content) —
  `app/business/email_classification.py::thread_match_merge`'s update
  path (`REQ-SB-69-US-01-T06`, `ADR-046` Decision 7).
- **Repro steps:**
  1. Have a real Thread note created BEFORE `T06` shipped tonight (no
     `thread_name` frontmatter key — that field didn't exist until
     `T05`/`T06`).
  2. Capture a new message that belongs to that same `conversation_id`
     (an update, not a new Thread).
  3. Observe the resulting filename after `thread_match_merge`'s own
     end-of-call rename check.
- **Expected:** The Thread keeps (or gains) a real, human-readable
  filename derived from its actual subject.
- **Actual:** `frontmatter.get("thread_name")` returns `None` for a
  legacy Thread that never had the key — that `None` flows straight
  into `thread_note_path_for`, producing a real, literal
  `"None-2026-08-17-2990e9ad.md"` filename. Found live tonight
  processing the real "Weekly Forecast l Strategic Clients" Thread's
  own second message (`0C41DC9411479C4BAC82EBDDDCA753E7.md`, one of
  this vault's 2 pre-existing real Threads) — content and frontmatter
  were correct, only the filename was broken.
- **Screenshot:** N/A
- **Fixed by:** Direct fix, 2026-08-17. When `thread_name` is missing
  from frontmatter, `thread_match_merge` now backfills it once using
  the current message's own subject (`upsert_frontmatter_key`) — the
  same top-up-only-if-missing convention `T05`'s own baseline-key
  helpers already use — so every later update reuses the real
  persisted value instead of re-deriving `None`. The one already-broken
  file was corrected directly (backfilled `thread_name`, renamed via
  the real `vault_writer.thread_note_path_for`/`rename_thread_note`
  functions) to
  `"RE- Weekly Forecast l Strategic Clients-2026-08-17-2990e9ad.md"`.
  Verified live: content/frontmatter unchanged, only the filename
  corrected; the vault's other pre-existing legacy Thread (Presight)
  is unaffected until its own next update, at which point this same
  fix now backfills it correctly instead of reproducing the bug.

### BUG-022 — Meeting/Inbox Cockpit: every agent responds to a message, not just the addressed one
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-19
- **Screen / route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro steps:**
  1. Open either Cockpit with more than one agent available in the
     conversation context.
  2. Send a message intended for one specific agent.
  3. Observe which agent(s) reply.
- **Expected:** Only the addressed/relevant agent responds — the
  Cockpit should route the message and dispatch it to the correct
  single agent, mirroring how a real conversation would only involve
  the person actually being spoken to.
- **Actual:** Every agent in the conversation responds with a message,
  regardless of who the message was actually addressed to.
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-04-US-01

### BUG-023 — Meeting/Inbox Cockpit: pressing Enter in the chat input does nothing, must click Send
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-19
- **Screen / route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro steps:**
  1. Open either Cockpit's chat input.
  2. Type a message.
  3. Press Enter.
- **Expected:** Pressing Enter sends the message, matching standard
  chat-UI convention.
- **Actual:** Pressing Enter does nothing — the message is not sent.
  The Send button must be clicked explicitly instead.
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-04-US-01

### BUG-024 — Meeting/Inbox Cockpit: sent message/replies don't appear until manual page refresh
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-19
- **Screen / route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro steps:**
  1. Open either Cockpit's chat.
  2. Send a message using the Send button (the working path, distinct
     from `BUG-023`).
  3. Observe the chat UI without refreshing the page.
- **Expected:** The sent message appears immediately (optimistic
  update), and any agent reply streams/appears in the UI as it
  arrives, with no manual action required.
- **Actual:** Nothing visibly changes after clicking Send — no
  confirmation the message was sent or delivered, no new messages
  shown — until the page is manually refreshed, at which point the
  sent message and any replies appear.
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-04-US-01

### BUG-025 — Chat messages render as plain text instead of rich text (Meeting Cockpit, Inbox Cockpit, Agents Map chat panel)
- **Area:** UI
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-19
- **Screen / route:** Meeting Cockpit, Inbox Cockpit, and the Agents
  Map embedded agent chat panel (all three).
- **Repro steps:**
  1. Open chat in any of the three surfaces above.
  2. Send or receive a message containing rich-text formatting (bold,
     lists, links, etc.).
  3. Observe how the message renders.
- **Expected:** Rich text renders as formatted content — this already
  shipped once (`REQ-SB-32`, "Rich Text Rendering in Agent Chat") and
  should hold across all three chat surfaces.
- **Actual:** Messages render as plain, unformatted text in all three
  surfaces — formatting is lost.
- **Screenshot:** N/A
- **Fixed by:** BUGFIX-04-US-01

### BUG-026 — `thread_match_merge`'s legacy rename logic duplicates old-shape Threads and orphans `messages/`/`files/` on new-shape Threads
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed
- **Found:** 2026-08-18/19 (originally disclosed as `ESC-048`/`ESC-050`
  during `REQ-SB-71`/`REQ-SB-72` planning and build)
- **Screen / route:** N/A (backend/vault content) —
  `app/business/pipelines/email_capture_pipeline.py`'s still-live graph,
  specifically `email_classification.thread_match_merge`, the
  implementation still behind the scheduled `email-capture-pipeline`
  Agent's `process_staged_email` capability. This is the OLD pipeline
  `REQ-SB-71` was meant to fully replace — it was never actually retired,
  only left `supervised` as a stopgap.
- **Repro steps (two distinct failure modes, same root cause — a legacy
  rename check incompatible with the new Thread directory shape):**
  1. **Duplication (old-shape Thread):** have a real, pre-redesign, FLAT
     `Work/Threads/<name>.md` Thread note. Capture a new message
     belonging to that same `conversation_id`. `resolve_thread_note_path`
     (post-`ADR-049`, frontmatter-scan-based) does not find the flat file
     at its expected location → `thread_match_merge` treats it as a brand
     new conversation and creates a SECOND, duplicate Thread under the OLD
     naming scheme.
  2. **Orphaning (new-shape Thread):** have a real, already-existing,
     NEW-shape (directory-based, `ADR-048`) Thread with real `messages/`
     and/or `files/` content. Capture a new message for that same
     `conversation_id`. `resolve_thread_note_path` correctly finds it, but
     `thread_match_merge` then computes a rename target via its own
     still-live legacy `thread_note_path_for(...)` (a flat, hash-suffixed
     filename) and calls `rename_thread_note(path, new_path)`, physically
     moving ONLY the concept file out of its own directory — its sibling
     `messages/`/`files/` subfolders are left behind, disconnected from the
     concept file that now sits elsewhere.
- **Expected:** `process_staged_email` correctly threads a new message
  into its existing Thread — old-shape or new-shape — without creating a
  duplicate note or orphaning any of that Thread's own content.
- **Actual:** either a real duplicate Thread is created (old-shape case)
  or a real Thread's own `messages:`/`files/` content is silently
  disconnected from its concept file (new-shape case), depending on which
  shape the target Thread is in.
- **Screenshot:** N/A
- **Note:** currently contained, not actively firing — `email-capture-
  pipeline`'s working mode has been kept `supervised` since `ESC-048` was
  found (a scheduled tick creates a Pending Approval instead of executing
  `thread_match_merge`), but a manual "Run Capture Now" or approving that
  Pending Approval would still trigger it. The real fix — already named in
  `architecture.md`'s own stated intent — is rewiring
  `process_staged_email`'s own implementation to compose
  `capture_raw_thread_messages`/`synthesize_thread` (the new `REQ-SB-71`
  pipeline) instead of `pull_and_stage_emails`/
  `run_email_capture_pipeline`/`thread_match_merge`, formally retiring the
  old path's live call site and allowing `email-capture-pipeline` to
  return to `autonomous` once shipped.
- **Fixed by:** BUGFIX-05-US-01
- **Closed 2026-08-19:** `BUGFIX-05-US-01` shipped `Done` — `process_
  staged_email` now composes `capture_raw_thread_messages`/`synthesize_
  thread` instead of the legacy `thread_match_merge` path (`T01`,
  `ADR-051`); a legacy flat-shape Thread is lazily migrated to the
  standard directory shape and its real pre-migration content preserved
  via a one-time, self-consuming `pre_migration_summary.md` sidecar
  (`T03`/`T05`, `ADR-052`/`ADR-053`), rather than duplicated; an
  already-migrated directory-shaped Thread's `messages/`/`files/` content
  is never orphaned (`T01`). Both failure modes verified live against the
  real `process_staged_email` capability endpoint and real vault data
  (`T02` → `AC-02` PASS; `T04` → `AC-01` PASS, including the sidecar
  fold-in/archive). `email-capture-pipeline`'s working mode flipped
  `supervised → autonomous`, confirmed permanent — the final undo of
  `ESC-048`'s protective measure.

### BUG-027 — `resolve_people_chips` 500s on a real Meeting note whose `attendees` frontmatter is a plain list of wikilink strings, not dicts
- **Area:** Logic
- **Severity:** Minor
- **Status:** Closed
- **Fixed by:** BUGFIX-06-US-01 (`Done`, 2026-08-19 — `cockpit/people.py`
  gains `_normalize_person_item`, wired into `_coerce_people_list`, via a
  promoted public `vault_writer.WIKILINK_PATTERN`; live-verified against
  both real repro meetings named below, both now `200` with real,
  cross-checked attendee data; `AC-01`/`AC-02` both PASS. See
  `BUGFIX-06-US-01-T01`'s own `## Implementation Log` for the full
  verification record.)
- **Found:** 2026-08-19 (found incidentally during `SPRINT-064`'s own live
  verification, disclosed via `REVIEW-QUEUE.md`, formally captured here)
- **Screen / route:** Meeting Cockpit — `GET /cockpit/meeting/<id>`.
- **Repro steps:**
  1. Have a real Meeting note whose `attendees` frontmatter is a plain
     list of wikilink strings (e.g. `["[[sandeep.penumadu@core42.ai]]",
     ...]` — the actual, real shape Meeting Capture currently writes for
     at least some meetings), not `list[dict]`.
  2. Open that Meeting in the Meeting Cockpit (`GET /cockpit/meeting/<id>`).
- **Expected:** The Cockpit loads normally, showing the meeting's real
  attendees.
- **Actual:** `500 Internal Server Error`. Root cause confirmed by direct
  code reading: `app/business/cockpit/people.py::_coerce_people_list`
  only JSON-decodes a STRING `attendees` value or passes a real `list`
  through as-is; `resolve_people_chips`'s own `for person in people:
  person.get("email", "")` then crashes with `AttributeError: 'str'
  object has no attribute 'get'` on a plain wikilink-string list,
  surfaced as a bare `500`. Confirmed on 2 real meetings ("Alignment
  Mubadala-2026-08-17-a4737bc4", "PSS Team Weekly Meeting-2026-08-18-
  47a72b70").
- **Screenshot:** N/A
- **Note:** likely fix shape (not yet decided/built): either normalize a
  plain wikilink-string `attendees` entry into a display name/email
  (reusing the same extraction pattern `people_extraction.py` already
  uses elsewhere) inside `_coerce_people_list`, or add a defensive
  per-item type check inside `resolve_people_chips`'s own loop.
  `→ src/backend/app/business/cockpit/people.py`

### BUG-028 — Customer/Project `log.md`/`captures.md` are created with zero identifying content
- **Area:** Logic
- **Severity:** Minor
- **Status:** Closed
- **Fixed by:** BUGFIX-07-US-01 (`Done`, 2026-08-19 — `SPRINT-070`)
- **Found:** 2026-08-19 (operator, live Obsidian browsing: "I noticed
  Something, The Customer is a folder so if we updated the log file
  inside the Customer we will have Multiple Log files Connect but no
  place to see the customer name")
- **Screen \ route:** N/A — vault data layer, not a UI screen. Confirmed
  these files are deliberately excluded from `vault_indexing`
  (`list_all_note_paths()`), so this does NOT affect search/backlinks/the
  new Vault graph (`REQ-SB-75`) — it's purely an Obsidian-native
  file-browsing problem (tab bar, quick switcher, file explorer).
- **Repro steps:**
  1. Create (or ensure) any Customer or Project OKF directory via
     `vault_writer.create_okf_directory_baseline` /
     `ensure_okf_directory_baseline` (shared primitive, `ADR-042` — same
     shape for both kinds).
  2. Open the resulting `log.md` or `captures.md` directly.
- **Expected:** Some stable, identifying header naming the owning
  Customer/Project, mirroring `index.md`'s own already-correct
  `# {name}\n\n...` convention (`index_listing_body` param, already
  written correctly today).
- **Actual:** Confirmed by direct code reading
  (`src/backend/app/data_access/vault_writer.py`,
  `create_okf_directory_baseline`/`ensure_okf_directory_baseline`):
  `log.md`/`captures.md` are written as a literal empty string
  (`paths["log"].write_text("", encoding="utf-8")`) and only topped up
  with `write_text("")` again if missing — never given a header at
  creation OR retrofitted onto already-existing empty ones. With 26+ real
  Customer folders already in the vault (more once `REQ-SB-74`'s backfill
  runs, plus every Project nested under a Customer, same shape), every one
  of these files is identically named and, once opened alone, completely
  anonymous.
- **Screenshot:** N/A
- **Note:** fix shape confirmed with the operator before capture — add a
  header line at creation (mirroring `index.md`'s own working pattern),
  and backfill it onto already-existing headerless files WITHOUT
  disturbing any real already-appended content (`append_person_note_
  update_line`'s own raw-append writes must stay intact).
  `→ src/backend/app/data_access/vault_writer.py`

### BUG-029 — `meeting-capture`'s `run_capture_now` fires twice concurrently, creating a permanent duplicate Pending Approval
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed — fixed by `BUGFIX-08-US-01` (`ADR-056`'s target-aware `dedupe_key`,
  `Implementation/Tasks/BUGFIX-08-US-01-T01-dedupe-key-registry-and-invoke-skill.md`),
  verified live 2026-08-19: a real scheduled-vs-direct race through
  `skill_registry.invoke_skill` for `meeting-capture`/`run_capture_now` now collapses to one
  live Pending Approval.
- **Found:** 2026-08-19 (operator, live Pending Approvals review: "The
  Pending Approval I can See it Keeps Repeating (Meeting Capture appear
  Multiple time)")
- **Screen \ route:** N/A — backend dispatch/gating layer. Surfaces in the
  Pending Approvals list.
- **Repro steps:**
  1. Confirmed live against real, current data (`GET /pending-approvals`):
     two real records exist for `agent_id: "meeting-capture"`,
     `action_id: "run_capture_now"`, both `status: "pending"`:
     `4e5ef1403765` (`trigger: "scheduled"`, created
     `2026-08-14T11:38:31.199941Z`) and `424ad11f9f8f` (`trigger:
     "direct"`, created `2026-08-14T11:38:31.205701Z`) — **5.76
     milliseconds apart**, identical description
     (`"Run Capture Now (Meeting Capture)"`).
  2. Neither has ever been resolved — both sat `pending` for 5 real days
     until this session's cleanup pass declined the `direct` one.
- **Expected:** One real "Meeting Capture wants to run" decision point per
  real trigger event, regardless of which code path (scheduler tick vs.
  manual dispatch) happened to fire it.
- **Actual:** Confirmed by direct code reading
  (`src/backend/app/business/pending_approval_registry.py::
  create_pending_approval`): the idempotency guard is scoped to
  `trigger == "background"` ONLY (`ADR-018` point 2) — `"scheduled"` and
  `"direct"` are both deliberately exempted, on the documented reasoning
  that "each is a distinct, deliberate user request." That assumption
  breaks here: a scheduled interval tick
  (`agent_schedule_registry.dispatch_with_shared_lock`, called via
  `capture_scheduler._build_scheduled_tick`) and a manual "Run Capture Now"
  dispatch (`agent_schedules_router.py` line 110, `trigger="direct"`)
  landed within the same real 6ms window and both reached
  `skill_registry.invoke_skill` — neither trigger source knows about the
  other, and the shared dispatch lock only serializes actual EXECUTION,
  not the act of asking for approval before execution starts.
- **Screenshot:** N/A
- **Note:** root cause is architectural (the "direct"/"scheduled"
  exemption from dedup, correct for most real call sites, is wrong for
  two independent trigger sources racing for the SAME logical action) —
  needs an architect pass, not a one-line patch.
  `→ src/backend/app/business/pending_approval_registry.py`,
  `→ src/backend/app/business/agent_schedule_registry.py`,
  `→ src/backend/app/api/agent_schedules_router.py`

### BUG-030 — A staged email that generates a classification/routing Pending Approval is reprocessed on every later capture tick, creating a fresh duplicate each time
- **Area:** Logic
- **Severity:** Major
- **Status:** Closed — fixed by `BUGFIX-08-US-01` (`ADR-056`'s target-aware `dedupe_key`,
  `Implementation/Tasks/BUGFIX-08-US-01-T02-dedupe-key-email-and-librarian-call-sites.md`),
  verified live 2026-08-19 across all four named call sites (`route_to_project`,
  `_create_classification_failure_pending_approval`, `propose_customer_backfill`,
  `propose_customer_archival_candidates`): a later reprocessing pass no longer creates a
  duplicate Pending Approval for the same real target while the first is unresolved.
- **Found:** 2026-08-19 (operator's own report investigated; root cause
  traced during the same session as `BUG-029`)
- **Screen \ route:** N/A — `email-capture-pipeline`'s `process_staged_
  email` capability.
- **Repro steps:**
  1. Confirmed live against real, current data (`GET /pending-approvals`):
     301 real `"Compass couldn't classify ..."` proposals and 50 real
     `"Route-to-Project guesses ..."` proposals for `agent_id:
     "email-capture-pipeline"`, `trigger: "direct"` — with real,
     confirmed EXACT-duplicate description groups within them (same
     email subject + sender repeated 2×, 3×, up to 6× across different
     `created_at` timestamps spanning hours/days), plus 15 real, generic
     `"Process Staged Email (Email Capture Pipeline)"` records with
     identical description text.
  2. Same real pattern independently confirmed in
     `librarian-housekeeping`'s Customer-backfill proposals (13 real
     duplicate groups, one repeated 17×) during `SPRINT-068`'s own build.
- **Expected:** A staged email/Thread that already has an unresolved
  Pending Approval covering it should not generate a second, identical
  one on the next capture tick.
- **Actual:** Confirmed by direct code reading
  (`src/backend/app/business/email_classification.py::route_to_project`):
  each proposal call site uses `trigger="direct"`, deliberately exempted
  from `create_pending_approval`'s own idempotency guard (`ADR-018`
  point 2 — "a single pipeline tick can legitimately produce multiple
  distinct routing proposals across different new Threads," which is
  true and correct BETWEEN different Threads). `route_to_project` itself
  already guards against re-proposing on an Thread UPDATE
  (`if not thread_result["created"]: return None`) — but nothing prevents
  the SAME staged email being treated as a brand-new Thread again on a
  LATER capture tick if it was never actually consumed/marked-resolved
  after its first pass generated a Pending Approval. The existing
  `"background"`-only, per-agent-scoped guard can't fix this even if
  reused as-is — it would incorrectly collapse proposals for genuinely
  DIFFERENT real emails/Threads into one, which `ADR-018` correctly
  avoided; what's actually missing is a PER-TARGET check ("does a pending
  approval already exist for this exact email/Thread"), not a per-agent
  one.
- **Screenshot:** N/A
- **Note:** same underlying gap as `BUG-029` — `create_pending_approval`
  has no way to dedupe two proposals that are targeting the same real
  thing when trigger isn't `"background"`. Also affects
  `librarian_housekeeping.propose_customer_backfill`/`propose_customer_
  archival_candidates` (confirmed live during `SPRINT-068`) — likely the
  SAME fix (a target-aware idempotency check, not just agent-scoped)
  closes all three real call sites at once. Needs an architect pass to
  decide the right shape (e.g. a caller-supplied `dedupe_key` parameter
  on `create_pending_approval`, checked regardless of `trigger`).
  `→ src/backend/app/business/pending_approval_registry.py`,
  `→ src/backend/app/business/email_classification.py`,
  `→ src/backend/app/business/pipelines/librarian_housekeeping.py`
