---
id: SPRINT-028
title: To-Do Task Capture Pipeline — Outlook Tasks capture, customer classification, My Day To-Do drill-down
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint Done — human skim + retro-harvest into Implementation/Learnings.md. One disclosed, non-blocking finding along the way (ESC-028, extends BUG-011 to Task notes) — see REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-027]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-028 — To-Do Task Capture Pipeline

## Sprint Goal

Build `REQ-SB-09-US-01` end to end: capture Outlook's Tasks folder into
Task-type vault notes, classified by customer where possible, on the same
recurring schedule email/meeting capture already runs on, and surface the
real result in My Day's To-Do drill-down.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-09-US-01` is the only
  story assigned here. Its 6 tasks form one dependency graph
  (`{T01, T02} → T03 → {T04, T05} → T06`) covering one cohesive pipeline
  (fetch → classify → write/dedup → schedule → surface in My Day) sharing
  one "Task Notes & Outlook-Tasks Capture" architecture scope (`ADR-027`).
- **Why sequenced behind `SPRINT-027`, not combined with it:** this story's
  `T04` carries a real, decomposer-recorded cross-story edge —
  `depends_on: [REQ-SB-09-US-01-T03, REQ-SB-11-US-01-T01]`, confirmed by
  direct reading of `Implementation/Tasks/
  REQ-SB-09-US-01-T04-scheduler-working-mode-wiring.md`. This is not an
  incidental edge: `REQ-SB-11-US-01-T01` rewrites the exact same function
  (`email_classification.py::run_capture_and_record_completion`) this
  story's `T04` also edits, wrapping each Autonomous branch's call in its
  own `try/except` and adding a new `_failed`-boolean gate on the trailing
  completion call — `T04`'s own `## Files to Modify` code is written
  directly against that already-known post-fix shape. Building `T04`
  before `REQ-SB-11-US-01-T01` lands would either look inconsistent with
  its sibling branches or silently omit the new `todo_capture_failed`
  boolean from the trailing gate once `REQ-SB-11-US-01-T01` later lands.
  Per hard rule 7, this is honoured via `depends_on_sprints: [SPRINT-027]`
  (ordered sprints) rather than same-sprint sequencing — the two stories
  otherwise share no architecture scope (Agent Activity's aggregation
  module vs. Task-note capture), so folding them into one 10-task sprint
  would mix two unrelated feature surfaces for no dependency-graph reason
  beyond this one shared-file edit.
- **Sizing estimate:** ~6 tasks, M. `T01` (`list_outlook_tasks` COM-read
  primitive) and `T02` (Task-note vault-writer primitives, incl. the
  load-bearing `task_note_index.json` dedup index) are independent,
  `depends_on: []` — can build in either order. `T03` (orchestration
  module + `compass_client.classify_task`, depends on `T01`/`T02`, carries
  the end-to-end live dedup/top-up verification for `AC-06`) → `T04`
  (scheduler/working-mode wiring, depends on `T03` and the cross-sprint
  `REQ-SB-11-US-01-T01`) and `T05` (real `GET /my-day/todo`, depends on
  `T02`/`T03`) both follow `T03` independently → `T06` (To-Do drill-down
  populated state, depends on `T05`). Matches this project's own precedent
  for a capture-pipeline-plus-My-Day-wiring story of this shape
  (`REQ-SB-08-US-01`/`SPRINT-006`, ~5 tasks, M, plus one extra task here
  from splitting scheduler wiring out of the orchestration module, mirroring
  that same story's own `T03`/`T04` split).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-028 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-09-US-01](../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md) | Task notes captured from Outlook's Tasks folder, classified by customer, and surfaced in My Day's To-Do drill-down | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-09-US-01-T01]]
(`list_outlook_tasks` Tasks-folder COM-read primitive, incl. the isolated
live EntryID-stability check — `app/data_access/outlook_com.py`,
`depends_on: []`), [[REQ-SB-09-US-01-T02]] (Task-note vault-writer
primitives — baseline create/top-up, `upsert_frontmatter_key`,
`task_note_index.json` dedup index — `app/data_access/vault_writer.py`,
`depends_on: []`), [[REQ-SB-09-US-01-T03]] (`todo_classification.py`
orchestration module + `compass_client.classify_task`,
`depends_on: [T01, T02]`), [[REQ-SB-09-US-01-T04]] (third gated capture
block + `run_capture_for_agent` branch wired into the shared scheduler tick,
`depends_on: [T03, REQ-SB-11-US-01-T01]` — **cross-sprint**),
[[REQ-SB-09-US-01-T05]] (real `GET /my-day/todo` + dashboard count,
`depends_on: [T02, T03]`), [[REQ-SB-09-US-01-T06]] (To-Do drill-down
populated state — item-list + Due today/Upcoming badge,
`depends_on: [T05]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-027` (Agent Activity & Error
  Observability) — must be `Done` before `/implement-sprint` may start this
  sprint; `REQ-SB-09-US-01-T04`'s own `depends_on: [..., REQ-SB-11-US-01-T01]`
  is the real, task-level ground truth for this edge.
- No other external blocker — `ADR-027` was already reviewed and approved
  (`REVIEW-QUEUE.md`, 2026-08-13); this pipeline runs against the user's
  real, live Outlook desktop and Obsidian vault, not a fixture — no-data-
  loss/idempotency verification is load-bearing per the story's own
  Constraints.

---

## Out of Scope

- Agent-created follow-ups and manually-flagged emails as task sources —
  confirmed out of scope for this story's own pass (`ESC-024`, Resolved).
- An "Overdue" badge/visual state — not sketched in the approved
  `my-day-todo.html` prototype, not specced.
- Marking a task complete/checking it off from within Second Brain's own
  UI, or manual task creation from Second Brain's UI — both explicitly
  out of this story's own scope.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed this sprint — already updated at `/plan-tasks` step 1, per `ADR-027`)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-027`, already `Accepted` before this sprint started)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly.
  No task was split, dropped, or merged. `T03` and `T04` were correctly
  the heaviest by verification effort (real, multi-minute Compass-backed
  capture runs and the induced-failure/Supervised-mode/recovery cycle),
  not by code volume — the estimate's own reasoning held up.

### What worked

- **Empirically closing an architect-disclosed gap, not just building
  around it.** `ADR-027` honestly disclosed that `EntryID`-stability was
  reasoned structurally, not live-verified, and explicitly assigned the
  coder a live-verification step. That step was run for real (`T01`'s
  isolated check + `T03`'s end-to-end capture→edit→rerun→confirm-topup
  cycle) and PASSED — the architect's own structural reasoning ("no
  `IncludeRecurrences`-equivalent exists for Tasks") is now an
  empirically confirmed fact, not a standing risk. Closing a disclosed
  gap this cleanly is worth naming as a repeatable pattern for future
  ADRs that carry the same kind of honestly-disclosed-but-unverified
  claim.
- **Bounding a live verification to a real, filtered subset via
  in-process monkeypatch of the real data-fetch function** (reused
  repeatedly this sprint: `AC-07`'s short-subject control pair, `AC-06`'s
  body-preservation/EntryID-reinforcement check, the recovery-from-
  induced-failure check, the badge-rendering screenshots) kept every
  check genuinely real — real Outlook items, real Compass calls, real
  vault writes — while avoiding repeating a ~100-item/~5-minute full-folder
  sweep for every single check. Extends `SPRINT-022`'s/`SPRINT-024`'s own
  "in-process monkeypatch of a real dependency" pattern from failure
  induction to scope-bounding.
- **A locked AC's own live verification surfaced a real, disclosed,
  non-blocking defect in shared, out-of-scope infrastructure — treated
  exactly per the established `ESC-027`/`BUG-011` precedent, not as a
  blocker.** `AC-07`'s own mechanism was independently confirmed correct
  before concluding the real long-subject collision was someone else's
  defect, not this story's own — the same discipline `ESC-027` itself
  used.

### What didn't work

- **The default shell environment could not resolve `node`/`npm`/`npx`
  on `PATH`, a second time** (first found `SPRINT-027`) — resolved by
  locating the real install via `HKLM:\SOFTWARE\Node.js`'s own registry
  pointer rather than assuming Node wasn't installed at all. Worth
  fixing at the environment level rather than re-discovering per sprint.
- **Two genuinely stray prior-session dev-server processes (Vite, ports
  5173/5174) had to be identified and killed** before a screen-level
  check could pass CORS at all (`main.py`'s `allow_origins` is scoped
  to exactly those two ports, not a wildcard, and is out of any
  frontend task's own file scope to widen) — cost one extra debug cycle
  before the root cause (CORS-origin mismatch, not a broken fetch) was
  identified.

### Patterns to carry forward

- **When an ADR discloses a claim it could not empirically verify and
  assigns the coder a live-verification step, treat that step as
  load-bearing, not a formality** — run it for real, record the result
  explicitly (confirmed or superseding-ADR-worthy), and close the loop
  in the story's own gate reasoning. Found live, `REQ-SB-09-US-01-T01`/`T03`.
- **Bound a live-data verification to a real, filtered subset via
  in-process monkeypatch of the real fetch function, rather than
  re-running a full real capture for every single check** — real data,
  real dependencies, bounded cost. Reconfirmed and generalized this
  sprint (`SPRINT-022`/`SPRINT-024`'s own precedent), now applied to
  scope-bounding as well as failure induction.
- **Independently confirm a new mechanism is correct via a controlled
  case BEFORE attributing a real-data failure to that mechanism** — the
  short-subject control pair proved `T02`/`T03`'s own disambiguation
  logic was sound, which is what made it possible to confidently
  root-cause the long-subject collision to pre-existing, out-of-scope
  infrastructure (`BUG-011`) instead of second-guessing the new code.

### Antipatterns to avoid

- **Assuming a stray dev-server process on the project's own usual
  ports is safe to build against without confirming what it's serving,
  or that the currently-bound port is actually the one CORS/config
  expects** — reconfirmed a further time (`SPRINT-021`/`SPRINT-022`/
  `SPRINT-029` → `SPRINT-028`); killed and restarted explicitly-controlled
  instances both times this sprint (backend port 8010, frontend
  port 5173).
- **Assuming `npx`/`node`/`npm` are resolvable on `PATH` in every
  session/shell** — a second confirmed instance of `SPRINT-027`'s own
  antipattern; worth fixing at the environment/session level so future
  sprints don't need to rediscover the same registry-lookup workaround.

### Open follow-ups

- **`ESC-028` / extend `BUG-011`** — the pre-existing `_slugify` 80-char
  truncation defect is now confirmed to affect Task notes too, with a
  worse (same-subfolder literal overwrite) consequence than its own
  documented case. Recommend extending `BUG-011`'s `BUGS.md` entry
  (not a new bug) and re-reviewing its `Severity`, then batching into a
  `BUGFIX-NN-US-01` fix story via `/triage`. The real vault still carries
  this exposure today (100 `task_note_index.json` entries vs. 82 real
  files under `Work/Tasks/`).
- **`BUG-003`/`BUG-007`/`BUG-008`** (pre-existing, unrelated to this
  sprint) remain `Open` — not touched or worsened by this sprint's own
  work, noted only because `BUG-008`'s own app-start-hang shape is
  structurally adjacent to this sprint's own real, multi-minute
  app-start capture runs (no new instance of it was hit this sprint).

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** Second of a two-sprint,
P1-phase pair (`SPRINT-027` → `SPRINT-028`); see `SPRINT-027`'s own Notes
for the full pair-partitioning rationale. This pair is independent of the
`SPRINT-029` (`REQ-SB-04-US-01`) sprint assembled in this same
`/plan-sprints` pass — no shared file surface, no dependency either way.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the `depends_on_sprints`
edge mirrors `REQ-SB-09-US-01-T04`'s own real, decomposer-recorded
cross-story task edge exactly (itself already surfaced by the decomposer
as a within-normal-bounds finding, not an escalation — see that story's
own `## Notes`), not guessed or invented; (2) `REQ-SB-09` is finalized PRD
text (the task-source/schema open questions were resolved before this
pass, `ESC-024`, Resolved); (3) product-owner does not write ADRs —
`ADR-027` was already reviewed and approved (`REVIEW-QUEUE.md`,
2026-08-13) before this pass; (4) no new `ESCALATIONS.md` entry needed;
(5) not oversized (6 tasks, M) and not a blocked story (all 6 tasks are
`Ready`, zero blocking issue); re-checked explicitly against the
"cross-sprint dependency" MUST-FLAG sub-trigger — this is the ordinary,
expected mechanical translation of an already-recorded task-level edge
into a sprint-level one, the same shape `SPRINT-009`/`SPRINT-012`/
`SPRINT-015`/`SPRINT-022`/`SPRINT-023`/`SPRINT-024` already used without a
flag; (6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
ambiguous — a single-story sprint with one dependency chain, sequenced
behind its one real cross-story prerequisite, has exactly one reasonable
grouping. Advances `Draft → Ready`.
