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
| BUG-008 | App-start Outlook-COM capture in `main.py`'s lifespan has no timeout, can hang the whole server's startup indefinitely | Logic | Major | Open | 2026-08-12 | — |
| BUG-009 | Agents Map overview: agents fan out past their own Section's wedge boundary into a neighboring Section | UI | Major | Open | 2026-08-13 | — |
| BUG-010 | Agents Map overview: on hover, an agent's Type and Name labels render at the identical position, directly overlapping | UI | Major | Open | 2026-08-13 | — |
| BUG-011 | `_slugify`'s 80-char truncation can silently eat a filename's disambiguating id-suffix, causing two distinct real notes to collide on the same filename stem — in `Work/Tasks/`'s flat folder this causes a real same-path overwrite (content loss), not just index-invisibility | Logic | Blocker | Open | 2026-08-13 | — |

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
- **Status:** Open
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
- **Fixed by:** —
- **Screenshot:** N/A
- **Fixed by:** —

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
