# BACKLOG

Index of all PRD requirements and the user stories that implement them. Updated by
the analyst at `/spec` and by the product-owner at `/plan-sprints`.

## How to read this

- **No story link** = not yet started (run `/spec REQ-SB-XX` to begin)
- **Story link** = story exists; check its status
- **Sprint** = which sprint this requirement is being built in

---

## MVP

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-01 | Vault Indexing | [REQ-SB-01-US-01](Implementation/UserStories/REQ-SB-01-US-01-vault-indexing.md) | Done (gate: flagged — ESC-027, Open, non-blocking) | [SPRINT-025](Implementation/Sprints/SPRINT-025-vault-indexing.md) | Done |
| REQ-SB-02 | Browse & Search | [REQ-SB-02-US-01](Implementation/UserStories/REQ-SB-02-US-01-browse-and-search.md) | Done (gate: clear) | [SPRINT-026](Implementation/Sprints/SPRINT-026-browse-and-search.md) | Done (gate: flagged — retro-harvest) |

## P1

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-03 | Conversational Agent Access via Hermes | [REQ-SB-03-US-01](Implementation/UserStories/REQ-SB-03-US-01-conversational-agent-access-via-hermes.md) | Draft (gate: clear — blocked on REQ-SB-01/REQ-SB-02 shipping) | — | — |
| REQ-SB-04 | Agent Vault Write Access | [REQ-SB-04-US-01](Implementation/UserStories/REQ-SB-04-US-01-agent-vault-write-access.md) | In Progress (gate: clear — T01/T02 Done, AC-03/AC-04 verified; T03/AC-01/AC-02 individually blocked, see ESC-026) | [SPRINT-029](Implementation/Sprints/SPRINT-029-agent-vault-write-access.md) | Done |
| REQ-SB-05 | Content Ingestion Path | [REQ-SB-05-US-01](Implementation/UserStories/REQ-SB-05-US-01-content-ingestion-path.md) | Draft (flagged — transport mechanism still open, see REVIEW-QUEUE.md) | — | — |
| REQ-SB-07 | Scheduled Recurring Agent Capture | [REQ-SB-07-US-01](Implementation/UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md) | Done | [SPRINT-001](Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md) | Done |
| REQ-SB-08 | Meetings Capture Pipeline | [REQ-SB-08-US-01](Implementation/UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md) | Done (flagged — one honestly-flagged, non-blocking live discovery from T06's final build; ESC-002/ESC-012 both Resolved; see REVIEW-QUEUE.md) | [SPRINT-006](Implementation/Sprints/SPRINT-006-meeting-notes-from-calendar-capture.md); T06 → [SPRINT-017](Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md) | Done; SPRINT-017 Done |
| REQ-SB-09 | To-Do Task Capture Pipeline | [REQ-SB-09-US-01](Implementation/UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md) | Done (gate: clear — one disclosed, non-blocking finding, ESC-028, Open) | [SPRINT-028](Implementation/Sprints/SPRINT-028-todo-notes-from-outlook-tasks-capture.md) | Done (gate: flagged — retro-harvest) |
| REQ-SB-10 | People Living Documents | [REQ-SB-10-US-01](Implementation/UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md) | Done | [SPRINT-004](Implementation/Sprints/SPRINT-004-person-notes-from-email-capture.md) | Done |
| REQ-SB-11 | Agent Activity & Error Observability | [REQ-SB-11-US-01](Implementation/UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md) | Done | [SPRINT-027](Implementation/Sprints/SPRINT-027-agent-activity-and-error-observability.md) | Done |
| REQ-SB-12 | Primary Application UI Shell — Agents Map & My Day | [REQ-SB-12-US-01](Implementation/UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md), [REQ-SB-12-US-02](Implementation/UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md) | Done, Done (flagged — CORS spot-check, see REVIEW-QUEUE.md) | [SPRINT-008](Implementation/Sprints/SPRINT-008-app-shell-agents-map-and-settings.md), [SPRINT-009](Implementation/Sprints/SPRINT-009-my-day-dashboard-and-drilldowns.md) | Done, Done |
| REQ-SB-13 | Embedded Agent Chat & Communication History | [REQ-SB-13-US-01](Implementation/UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md) | Done | [SPRINT-010](Implementation/Sprints/SPRINT-010-embedded-agent-chat-and-communication-history.md) | Done |
| REQ-SB-14 | Vault Graph Connectivity | [REQ-SB-14-US-01](Implementation/UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md) | Done | [SPRINT-002](Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md) | Done |
| REQ-SB-15 | Manual-Entry Templates & Guidelines | [REQ-SB-15-US-01](Implementation/UserStories/REQ-SB-15-US-01-manual-entry-templates-and-guide.md) | Done | [SPRINT-003](Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md) | Done |
| REQ-SB-16 | Partner Hub Notes & Graph Connectivity | [REQ-SB-16-US-01](Implementation/UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md) | Done | [SPRINT-007](Implementation/Sprints/SPRINT-007-partner-hub-notes-and-research-notes.md) | Done |
| REQ-SB-17 | Research Notes (Books & Reads) | [REQ-SB-17-US-01](Implementation/UserStories/REQ-SB-17-US-01-research-notes-template-and-guide.md) | Done | [SPRINT-007](Implementation/Sprints/SPRINT-007-partner-hub-notes-and-research-notes.md) | Done |
| REQ-SB-18 | Dynamic Agent Sections & Agent-to-Section Assignment | [REQ-SB-18-US-01](Implementation/UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md) | Done (flagged — ADR-014 review, see REVIEW-QUEUE.md) | [SPRINT-011](Implementation/Sprints/SPRINT-011-dynamic-agent-sections-and-assignment.md) | Done |
| REQ-SB-19 | Per-Agent LLM Provider Selection | [REQ-SB-19-US-01](Implementation/UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md) | Done (flagged — ADR-014 review, see REVIEW-QUEUE.md) | [SPRINT-012](Implementation/Sprints/SPRINT-012-per-agent-llm-provider-selection.md) | Done |
| REQ-SB-20 | Section Hub Intelligence & Cross-Section Routing | [REQ-SB-20-US-01](Implementation/UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md) | Done (flagged — scope-internal judgement calls awaiting spot-check, retro pending harvest, see REVIEW-QUEUE.md) | [SPRINT-020](Implementation/Sprints/SPRINT-020-section-hub-intelligence-and-cross-section-routing.md) | Done |
| REQ-SB-21 | Agent Working Modes | [REQ-SB-21-US-01](Implementation/UserStories/REQ-SB-21-US-01-agent-working-modes.md) | Done (flagged — scope-internal judgement calls awaiting spot-check, retro pending harvest, see REVIEW-QUEUE.md) | [SPRINT-021](Implementation/Sprints/SPRINT-021-agent-working-modes.md) | Done |
| REQ-SB-22 | My Day Rolling 7-Day Window | [REQ-SB-22-US-01](Implementation/UserStories/REQ-SB-22-US-01-my-day-rolling-7-day-window.md) | Done (flagged — retro pending harvest, see REVIEW-QUEUE.md) | [SPRINT-013](Implementation/Sprints/SPRINT-013-my-day-rolling-7-day-window.md) | Done |
| REQ-SB-23 | My Day Intake Agent (Conversational) | [REQ-SB-23-US-01](Implementation/UserStories/REQ-SB-23-US-01-my-day-intake-agent.md) | Draft (re-specced for the conversational revision, flagged — blocked on REQ-SB-25-US-01, net-new-design-needed; see REVIEW-QUEUE.md) | — | — |
| REQ-SB-24 | Per-Agent Token Consumption & Cost Tracking | [REQ-SB-24-US-01](Implementation/UserStories/REQ-SB-24-US-01-per-agent-token-consumption-and-cost-tracking.md) | Draft (flagged — see REVIEW-QUEUE.md) | — | — |
| REQ-SB-25 | Real Conversational Agent Chat | [REQ-SB-25-US-01](Implementation/UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md) | Done (flagged — live-discovered technical corrections, see REVIEW-QUEUE.md) | [SPRINT-014](Implementation/Sprints/SPRINT-014-real-conversational-agent-chat.md) | Done |
| REQ-SB-26 | Agent Memory | [REQ-SB-26-US-01](Implementation/UserStories/REQ-SB-26-US-01-agent-memory.md) | Done (flagged — live-discovered technical correction in T03, see REVIEW-QUEUE.md) | [SPRINT-015](Implementation/Sprints/SPRINT-015-agent-memory-and-skills-repository.md) | Done |
| REQ-SB-27 | Skills Repository | [REQ-SB-27-US-01](Implementation/UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md) | Done (plumbing only — first real skill deferred, see story's own Non-Goals) | [SPRINT-015](Implementation/Sprints/SPRINT-015-agent-memory-and-skills-repository.md) | Done |
| REQ-SB-28 | File Upload for Agents | [REQ-SB-28-US-01](Implementation/UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md) | Draft (flagged — see REVIEW-QUEUE.md) | — | — |
| REQ-SB-29 | Agent-to-Tag/Folder Scoping | [REQ-SB-29-US-01](Implementation/UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md) | Draft (flagged — see REVIEW-QUEUE.md) | — | — |
| REQ-SB-30 | Email Importance Filtering via Compass Reasoning | [REQ-SB-30-US-01](Implementation/UserStories/REQ-SB-30-US-01-email-importance-filtering-via-compass.md) | Draft | — | — |
| REQ-SB-31 | System Health View | [REQ-SB-31-US-01](Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md) | Done | [SPRINT-019](Implementation/Sprints/SPRINT-019-system-health-view.md) | Done |
| REQ-SB-32 | Rich Text Rendering in Agent Chat | — | — | — | — |
| REQ-SB-33 | Agent Grounding & Honest-Uncertainty Guardrail | [REQ-SB-33-US-01](Implementation/UserStories/REQ-SB-33-US-01-agent-grounding-and-honest-uncertainty-guardrail.md) | Done | [SPRINT-018](Implementation/Sprints/SPRINT-018-agent-grounding-and-honest-uncertainty-guardrail.md) | Done |
| REQ-SB-34 | ~~Tech Knowledge Area~~ — Withdrawn, merged into REQ-SB-35 | — | Withdrawn | — | — |
| REQ-SB-35 | Vault Filing Expert | [REQ-SB-35-US-01](Implementation/UserStories/REQ-SB-35-US-01-vault-filing-expert.md) | Done | [SPRINT-023](Implementation/Sprints/SPRINT-023-vault-filing-expert.md) | Done |
| REQ-SB-36 | Agent Knowledge Bootstrapping via Delegated Research | [REQ-SB-36-US-01](Implementation/UserStories/REQ-SB-36-US-01-web-research-skill.md), [REQ-SB-36-US-02](Implementation/UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md) | Done (flagged — see REVIEW-QUEUE.md), In Progress (T01–T03 Done; T04 blocked — see ESC-018) | [SPRINT-022](Implementation/Sprints/SPRINT-022-web-research-skill.md), [SPRINT-024](Implementation/Sprints/SPRINT-024-agent-knowledge-bootstrapping-compass-expert-pilot.md) | Done, Done |
| REQ-SB-37 | Agent Creation | [REQ-SB-37-US-01](Implementation/UserStories/REQ-SB-37-US-01-agent-creation.md) | Draft (flagged — see REVIEW-QUEUE.md) | — | — |
| REQ-SB-38 | Agents Map Density Clustering | [REQ-SB-38-US-01](Implementation/UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md) | Draft (flagged — see REVIEW-QUEUE.md) | — | — |

## P2

| Req ID | Description | Story | Story Status | Sprint | Sprint Status |
|---|---|---|---|---|---|
| REQ-SB-06 | Search Quality Enhancements | — | — | — | — |

---

## Sprint Status

| Sprint | Title | Phase | Status | Depends On | Sizing |
|---|---|---|---|---|---|
| [SPRINT-001](Implementation/Sprints/SPRINT-001-scheduled-recurring-capture.md) | Scheduled recurring email capture (hourly + app-start + catch-up) | P1 | Done | None | ~4 tasks, S |
| [SPRINT-002](Implementation/Sprints/SPRINT-002-vault-graph-connectivity.md) | Automated Customer hub notes and wikilinking for vault graph connectivity | P1 | Done | None | ~4 tasks, S |
| [SPRINT-003](Implementation/Sprints/SPRINT-003-manual-entry-templates-and-guide.md) | Obsidian manual-entry templates and in-vault guide note | P1 | Done | None | ~2 tasks, XS |
| [SPRINT-004](Implementation/Sprints/SPRINT-004-person-notes-from-email-capture.md) | Person notes auto-created and updated from email capture | P1 | Done | None | ~4 tasks, S |
| [SPRINT-005](Implementation/Sprints/SPRINT-005-email-notes-wikilink-to-sender-person-note.md) | Email notes wikilink to their sender's Person note (BUG-001 fix) | — (bugfix) | Done | None | ~2 tasks, XS |
| [SPRINT-006](Implementation/Sprints/SPRINT-006-meeting-notes-from-calendar-capture.md) | Meeting notes captured from calendar sync, classified by customer, linked to Person notes | P1 | Done (flagged — ESC-002, see REVIEW-QUEUE.md) | None | ~5 tasks, M |
| [SPRINT-007](Implementation/Sprints/SPRINT-007-partner-hub-notes-and-research-notes.md) | Partner hub notes + Microsoft migration, and Research notes template + guide | P1 | Done | None | ~6 tasks, M |
| [SPRINT-008](Implementation/Sprints/SPRINT-008-app-shell-agents-map-and-settings.md) | App shell, Agents Map, and Settings reachability (first frontend build) | P1 | Done | None | ~4 tasks, S |
| [SPRINT-009](Implementation/Sprints/SPRINT-009-my-day-dashboard-and-drilldowns.md) | My Day dashboard and its Emails/Calendar/To-Do drill-down pages | P1 | Done | SPRINT-008 | ~7 tasks, M |
| [SPRINT-010](Implementation/Sprints/SPRINT-010-embedded-agent-chat-and-communication-history.md) | Embedded agent detail panel — settings, actions, chat, and communication history | P1 | Done | SPRINT-008 | ~8 tasks, L |
| [SPRINT-011](Implementation/Sprints/SPRINT-011-dynamic-agent-sections-and-assignment.md) | Dynamic agent Sections — CRUD, per-agent assignment, N-generic Agents Map layout | P1 | Done (flagged — retro pending harvest; ADR-014 review, see REVIEW-QUEUE.md) | None | ~8 tasks, L |
| [SPRINT-012](Implementation/Sprints/SPRINT-012-per-agent-llm-provider-selection.md) | Global LLM Provider CRUD, per-agent Provider picker defaulting to Compass | P1 | Done (flagged — retro pending harvest; ADR-014 review, see REVIEW-QUEUE.md) | SPRINT-011 | ~6 tasks, M |
| [SPRINT-013](Implementation/Sprints/SPRINT-013-my-day-rolling-7-day-window.md) | My Day drill-downs and dashboard counts scoped to a rolling 7-day window | P1 | Done (flagged — retro pending harvest, see REVIEW-QUEUE.md) | None | ~2 tasks, XS |
| [SPRINT-014](Implementation/Sprints/SPRINT-014-real-conversational-agent-chat.md) | Real, Provider-backed conversational replies for embedded agent chat (LangGraph + shared MCP server foundation) | P1 | Done (flagged — retro pending harvest; live-discovered technical corrections, see REVIEW-QUEUE.md) | None | ~8 tasks, L |
| [SPRINT-015](Implementation/Sprints/SPRINT-015-agent-memory-and-skills-repository.md) | Agent memory (persistent, per-agent fact recall) and skills repository (registration + per-agent access plumbing) | P1 | Ready | SPRINT-014 | ~8 tasks, L |
| [SPRINT-016](Implementation/Sprints/SPRINT-016-agents-map-semantic-zoom-drilldown-fix.md) | Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix) | — (bugfix) | Done | None | ~6 tasks, M |
| [SPRINT-017](Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md) | Replace EntryID with GlobalAppointmentID as the Meeting-occurrence dedup/filename key (ADR-013 hardening fix, resolves ESC-002) — rebuilt against ADR-019's structural precise-start-timestamp key after ADR-013's own GlobalAppointmentID premise was live-falsified (ESC-012) | P1 | Done | None | ~1 task, XS |
| [SPRINT-018](Implementation/Sprints/SPRINT-018-agent-grounding-and-honest-uncertainty-guardrail.md) | Agent grounding & honest-uncertainty guardrail — global system-prompt instruction on every agent's real conversational reply path | P1 | Done | None | ~1 task, XS |
| [SPRINT-019](Implementation/Sprints/SPRINT-019-system-health-view.md) | System Health View — read-only status aggregation + chat-path crash-gap fix | P1 | Done | None | ~4 tasks, S |
| [SPRINT-020](Implementation/Sprints/SPRINT-020-section-hub-intelligence-and-cross-section-routing.md) | Section Hub Intelligence & Cross-Section Routing — per-agent keywords, Hub-to-Hub routing node | P1 | Done | None | ~6 tasks, M |
| [SPRINT-021](Implementation/Sprints/SPRINT-021-agent-working-modes.md) | Agent Working Modes — Autonomous/Supervised/Manual gating + Pending Approvals surface | P1 | Done | None | ~9 tasks, L |
| [SPRINT-022](Implementation/Sprints/SPRINT-022-web-research-skill.md) | Real Anthropic Provider integration & web-research skill for Research Expert agents | P1 | Done (flagged — ADR-022 Correction + open credential-verification gap, see REVIEW-QUEUE.md) | SPRINT-020 | ~6 tasks, M |
| [SPRINT-023](Implementation/Sprints/SPRINT-023-vault-filing-expert.md) | Vault Filing Expert — methodology-grounded placement/tag decision and write, two-tier approval | P1 | Done | SPRINT-020, SPRINT-021 | ~3 tasks, S |
| [SPRINT-024](Implementation/Sprints/SPRINT-024-agent-knowledge-bootstrapping-compass-expert-pilot.md) | Agent Knowledge Bootstrapping — end-to-end delegated-research chain, Compass Expert pilot (T04 excluded, blocked on REQ-SB-29-US-01, see ESC-018) | P1 | Done | SPRINT-020, SPRINT-021, SPRINT-022, SPRINT-023 | ~3 tasks, S (buildable) |
| [SPRINT-025](Implementation/Sprints/SPRINT-025-vault-indexing.md) | Vault Indexing — core index, on-demand re-index endpoint, hourly-schedule wiring | MVP | Done | None | ~4 tasks, S |
| [SPRINT-026](Implementation/Sprints/SPRINT-026-browse-and-search.md) | Browse & Search — tag filter, wikilink navigation, ranked keyword search | MVP | Done (flagged — retro-harvest, see REVIEW-QUEUE.md) | SPRINT-025 | ~4 tasks, M |
| [SPRINT-027](Implementation/Sprints/SPRINT-027-agent-activity-and-error-observability.md) | Agent Activity & Error Observability — honest-failure-recording fix, chronological run log, channel status | P1 | Done | None | ~4 tasks, S |
| [SPRINT-028](Implementation/Sprints/SPRINT-028-todo-notes-from-outlook-tasks-capture.md) | To-Do Task Capture Pipeline — Outlook Tasks capture, customer classification, My Day To-Do drill-down | P1 | Done (flagged — retro-harvest, see REVIEW-QUEUE.md) | SPRINT-027 | ~6 tasks, M |
| [SPRINT-029](Implementation/Sprints/SPRINT-029-agent-vault-write-access.md) | Agent Vault Write Access — /mcp shared-secret auth, write-capable MCP tool, Pending Approvals plumbing (T03 excluded, blocked on REQ-SB-29-US-01, see ESC-026) | P1 | Done | None | ~2 tasks, S (buildable) |

---

## Bugs

Thin status **mirror** of [`BUGS.md`](BUGS.md) (the source of truth — repro steps,
expected/actual, and screenshots live there, not here). Never edit by hand: `/bug`
adds rows at `Open`, the analyst flips them to `In Sprint` at `/triage` (writing the
fix-story link), and the coder flips them to `Closed` when the `BUGFIX-NN` story is
`Done`. The actor that changes a bug's status updates `BUGS.md` and this table in the
same touch. Status: `Open | In Sprint | Closed | Won't Fix`.

| ID | Title | Area | Status | Fixed by |
|---|---|---|---|---|
| BUG-001 | Email notes don't wikilink to their sender's Person note | Logic | Closed | BUGFIX-01-US-01 |
| BUG-002 | Agents Map: sections with 4+ agents visually spill into neighboring sections | UI | Closed | BUGFIX-02-US-01 |
| BUG-003 | `insert_body_line_if_missing` corrupts notes whose body lacks the blank line after frontmatter | Logic | Open | — |
| BUG-004 | Agents Map: an agent node renders directly on top of a neighboring Section's Hub | UI | Closed | direct fix, 2026-08-12 |
| BUG-005 | Agents Map: top Section title renders off-screen above the viewport | UI | Open | — |
| BUG-006 | Agents Map: Worker and Expert rings have zero gap, agents visually read as the same ring | UI | Open | — |
| BUG-007 | `graph.py::_call_model` is a synchronous node with a blocking Provider call, suspected cause of a real dev-backend hang | Logic | Open | — |
| BUG-008 | App-start Outlook-COM capture in `main.py`'s lifespan has no timeout, can hang the whole server's startup indefinitely | Logic | Open | — |
| BUG-009 | Agents Map overview: agents fan out past their own Section's wedge boundary into a neighboring Section | UI | Closed | Direct fix, 2026-08-13 |
| BUG-010 | Agents Map overview: on hover, an agent's Type and Name labels render at the identical position, directly overlapping | UI | Closed | Direct fix, 2026-08-13 |
| BUG-011 | `_slugify`'s 80-char truncation can silently eat a filename's disambiguating id-suffix — causes a real same-path overwrite (content loss) in `Work/Tasks/`'s flat folder | Logic | Open | — |
