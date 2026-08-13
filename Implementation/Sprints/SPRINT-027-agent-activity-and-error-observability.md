---
id: SPRINT-027
title: Agent Activity & Error Observability — honest-failure-recording fix, chronological run log, channel status
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint retro drafted — human to skim and propagate patterns into Implementation/Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-13
started: "2026-08-13"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-027 — Agent Activity & Error Observability

## Sprint Goal

Build `REQ-SB-11-US-01`'s new top-level Agent Activity page: close the
honest-failure-recording gaps in the capture pipeline's own history
entries, then aggregate/show a chronological cross-agent run log plus
Outlook communication-channel reachability.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-11-US-01` is the only
  story assigned here. All 4 tasks share one architecture scope ("Agent
  Activity & Error Observability" in `architecture.md`) and mirror
  `REQ-SB-31-US-01`'s (System Health) own already-`Done` shape (one fix
  task, one read-only aggregation module, one router, one frontend page).
- **Why NOT combined with `REQ-SB-04-US-01` (Agent Vault Write Access) in
  this same sprint**, despite both being small, independent, same-phase
  (P1) stories with no dependency between them: the two share no
  architecture scope, no file surface, and no product cohesion (a
  write-access trust surface vs. a run-observability view) — combining
  them would only be for raw task-count convenience, not a real grouping
  reason, and this project's own sprint history consistently keeps
  same-phase-but-unrelated stories in separate sprints rather than
  padding sprint size for its own sake.
- **Why sequenced ahead of `REQ-SB-09-US-01` (To-Do Task Capture):** this
  story's `T01` (the honest-failure-recording fix to
  `email_classification.py::run_capture_and_record_completion`) is a real,
  decomposer-recorded prerequisite for `REQ-SB-09-US-01-T04`
  (`depends_on: [REQ-SB-09-US-01-T03, REQ-SB-11-US-01-T01]`, confirmed by
  direct reading of `Implementation/Tasks/
  REQ-SB-09-US-01-T04-scheduler-working-mode-wiring.md`) — a genuine
  structural build-order dependency (`REQ-SB-09-US-01`'s own third gated
  capture block must be written directly against this story's post-fix
  function shape, not the pre-fix one). See `SPRINT-028`'s own
  `depends_on_sprints: [SPRINT-027]`.
- **Sizing estimate:** ~4 tasks, S. `T01` (the failure-recording fix,
  `email_classification.py` only) and `T02` (the `agent_activity.py`
  aggregation module + `outlook_com.py::check_reachable()`) are both
  independent, `depends_on: []` — can build in either order. `T03`
  (router, depends on `T02`) → `T04` (frontend page + nav wiring, depends
  on `T03` and the already-`Done` `REQ-SB-12-US-01-T01`). Matches this
  project's own precedent for this exact shape (`SPRINT-019`, System
  Health's identical one-fix/one-aggregation/one-router/one-page
  breakdown, ~4 tasks, S).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-027 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-11-US-01](../UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md) | Chronological background-agent-run activity log, per-communication-channel status, and the honest-failure-recording fix | P1 | Ready |

**Tasks in scope** (dependency order): [[REQ-SB-11-US-01-T01]]
(honest-failure-recording fix — meeting-capture success-entry parity +
per-step honest-failure-funnel, `email_classification.py` only,
`depends_on: []`), [[REQ-SB-11-US-01-T02]] (`app/business/agent_activity.py`
read-only aggregation module + `outlook_com.py::check_reachable()`,
`depends_on: []`), [[REQ-SB-11-US-01-T03]] (`app/api/
agent_activity_router.py`, `GET /agent-activity`, `depends_on: [T02]`),
[[REQ-SB-11-US-01-T04]] (`AgentActivityPage.tsx` + nav wiring,
`depends_on: [T03, REQ-SB-12-US-01-T01]` — the latter already `Done`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- **Downstream, not a blocker for this sprint:** `SPRINT-028`
  (`REQ-SB-09-US-01`, To-Do Task Capture) records
  `depends_on_sprints: [SPRINT-027]` — this sprint must be `Done` before
  `SPRINT-028` may start.
- No external blocker — `/design REQ-SB-11` already produced and got
  browser sign-off on the approved prototype
  (`html-prototype/agent-activity.html`); the architect pass found no new
  ADR needed.

---

## Out of Scope

- `REQ-SB-31-US-01`'s own three existing System Health checks (MCP mount,
  per-agent Provider availability, last capture run) — not duplicated or
  rebuilt here.
- A real Hermes-wrapped channel status — this sprint reports direct
  Outlook COM reachability only, honestly described as such.
- Alerting/notifications on a detected failure, auto-refresh/polling, and
  general exception-catching/logging middleware for the ASGI application
  as a whole — all explicitly out of this story's own scope.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural change this sprint (architect pass at `/plan-tasks` already confirmed no new ADR needed)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  No task was split, dropped, or merged. `T04` (the frontend page) was
  correctly the heaviest by verification effort, not code volume — all 7
  locked ACs plus the nav-item structural check needed real, screen-level
  proof, which took real tool-improvisation (see Patterns below) rather
  than being the code-writing itself.

### What worked

- Composing `T01`'s fix, `T03`'s router registration, and `T04`'s route
  registration each directly around the REAL current file (not the
  task's own "Before" sample) caught two independent, real,
  concurrent-session drifts (SPRINT-025's `vault_indexing.rebuild_index()`
  addition to `email_classification.py`; a concurrent sibling session's
  own `vault_search_router`/`VaultBrowserPage` additions to
  `main.py`/`App.tsx`) — this project's own established pattern held up a
  third time this session alone.
- Real, live, end-to-end verification of the entire honest-failure-
  recording fix in one pass: the real app-start scheduler tick alone
  produced the first-ever `meeting-capture` success entry (proving `T01`
  before any manual test was even written), then a real in-process
  monkeypatch proved the failure path, `Scenario 3` independence, and the
  `record_capture_run_completed()` gating — all against the real vault
  and real Outlook, no mocks.

### What didn't work

- The task's own literal `T02`/`T04` Tests-block technique ("temporarily
  close Outlook desktop") does not actually produce a genuine unreachable
  state on this machine — Windows COM's `Dispatch("Outlook.Application")`
  silently auto-relaunches Outlook.exe on the very next connection
  attempt, confirmed live by the process's own `StartTime` advancing
  immediately after a forced kill. Had to substitute the already-
  established in-process-monkeypatch technique instead (see Patterns).

### Patterns to carry forward

- **When a task's own named induction technique for a real external
  system's "unreachable" state doesn't actually stick (auto-recovery
  behaviour of the real dependency itself, not a test-authoring
  mistake), fall back to this project's own established in-process-
  monkeypatch technique rather than accepting a weaker, backend-only
  proof** — and when the locked AC is specifically screen-level (a real
  rendered badge, not just a JSON field), monkeypatch the dependency
  *before importing the real app*, temporarily swap it in on the SAME
  port the frontend is already wired to, screenshot, then revert —
  keeping the verification genuinely end-to-end instead of quietly
  dropping to a backend-only substitute. Found live, `REQ-SB-11-US-01-T04`
  (`AC-05`).
- **When no visual-harness/CDP/screenshot tool is available to a Coder
  session, the OS-installed Edge browser's own headless screenshot mode
  (`msedge.exe --headless=new --screenshot=... URL`) is a real,
  legitimate, zero-new-dependency substitute** — it renders the actual
  app through a real browser engine against the real dev server, not a
  mock, and produces a real PNG the Read tool can view directly. Cheaper
  and more honest than either skipping the "LOOK before Done" step
  entirely or claiming a pass from API responses/code-reading alone. When
  a page's own content grows past one viewport (a long `.log-list` with
  no max-height), a large `--window-size` height plus a
  `System.Drawing`-based crop (via PowerShell) reaches content below the
  fold without needing a real scroll interaction. Found live,
  `REQ-SB-11-US-01-T04`.
- **A real background/scheduled real-Provider capture tick's own latency
  is genuinely variable run-to-run** (this session: ~90s on the first
  app-start tick, ~6-7 minutes on a later restart of the same
  unmodified code with a larger history file and a just-relaunched
  Outlook) — reconfirms `SPRINT-021`'s own "assume multi-minute latency,
  background the call, don't assume a hang" Learnings entry; checking the
  waiting process's own accumulating CPU time (not just wall-clock
  elapsed) is a cheap, decisive way to distinguish "still genuinely
  working" from a true `BUG-008`-style hang before concluding the latter.
  Found live, `SPRINT-027`.

### Antipatterns to avoid

- **Assuming `npx`/`tsc` are resolvable on PATH in every session/shell**
  — neither Bash nor PowerShell in this session could resolve `npx`,
  even though the project's own already-running Vite dev server proved
  Node/npm were installed somewhere on the machine. A live Vite-transform
  fetch of the changed module (confirms no syntax error, real esbuild
  output) is a reasonable fallback when a full type-check genuinely can't
  be run, but should be named explicitly as a narrower check than `tsc
  -b`, not conflated with one. Found live, `REQ-SB-11-US-01-T04`.

### Open follow-ups

- None blocking. `BUG-008` (app-start capture has no startup timeout) was
  reconfirmed as a real, live risk shape this session (a ~6-7 minute
  real startup, though not an actual indefinite hang) — still `Open`,
  unchanged, out of this sprint's own scope (no task named it).

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** First of a two-sprint,
P1-phase pair (`SPRINT-027` → `SPRINT-028`) — this story's `T01` is a real
prerequisite for `REQ-SB-09-US-01`'s own scheduler-wiring task.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the task breakdown is read
directly off the decomposer's own recorded graph; (2) `REQ-SB-11` is
finalized PRD text; (3) product-owner does not write ADRs — this story's
own architect pass found no new ADR needed; (4) no new `ESCALATIONS.md`
entry needed; (5) not oversized (4 tasks, S) and not a blocked story (all 4
tasks are `Ready`); (6) N/A (coder-only trigger); (7) no contradictory
inputs; (8) not ambiguous — a single-story sprint with a straight
dependency shape (two independent leaves feeding a router then a page) has
exactly one reasonable grouping; explicitly considered and rejected
combining with `REQ-SB-04-US-01` for lack of any real cohesion reason (see
Grouping Rationale). Advances `Draft → Ready`.
