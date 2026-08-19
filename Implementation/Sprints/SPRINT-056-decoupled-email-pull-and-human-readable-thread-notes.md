---
id: SPRINT-056
title: Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest + standing REQ-SB-69-US-01 ADR-046 human-review flag, see REVIEW-QUEUE.md"                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-17
started: "2026-08-17"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-17"                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-056 — Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes

## Sprint Goal

Decouple the Outlook email pull into its own durable, vault-local staging step
(`pull_email`) so a stall inside it can never again block or be blocked by
Classify/Thread-Match-Merge/Route-to-Project (`process_staged_email`), and make
Thread notes read like a human wrote them — a human-readable filename, human-readable
dates, and real `[[wikilinks]]` into the Customer/Person/Project notes a Thread is
actually about.

---

## Grouping Rationale & Sizing

- **Why grouped — single-story sprint.** `REQ-SB-69-US-01` is the only `Ready`,
  ungrouped (`sprint: ""`) story in scope for this pass (operator-directed,
  end-to-end autonomy grant for this one requirement tonight, following a real
  production incident — see `## Notes`). All 8 tasks (`T01`-`T08`) belong to this
  one story, one architecture scope (`ADR-046`), and the decomposer's own recorded
  `depends_on` graph — read directly from each task file's frontmatter, not
  inferred from the story's own summary table:
  - `T01` (`depends_on: []`) and `T05` (`depends_on: []`) are two independent
    roots — the pull/staging half and the Thread content-quality half share no
    edge between them anywhere in the graph.
  - Pull/staging chain: `T01` → `T02` (`depends_on: [T01]`), `T03`
    (`depends_on: [T01]`) — a real diamond, `T02`/`T03` mutually independent —
    → `T04` (`depends_on: [T02, T03]`), converging both.
  - Thread content-quality chain: `T05` → `T06` (`depends_on: [T05]`) → `T07`
    (`depends_on: [T06]`) → `T08` (`depends_on: [T06, T07]`).
  - Confirmed acyclic by direct construction (two roots, two short converging
    chains, no back-edges) — a DAG, matching the decomposer's own "diamond plus
    two short chains" description exactly.
  No reason to split a single story's own internal, acyclic graph across sprints
  — every edge stays inside `REQ-SB-69-US-01`, so there is no cross-story
  dependency to reconcile this pass (unlike `SPRINT-049`→`050`, which had a real
  one-directional cross-story edge to sequence).
- **Why not split into two sprints along the two independent-root halves.**
  Genuinely possible in principle (the two chains never touch each other's
  tasks), but not warranted here: both halves are P1, touch overlapping real
  files (`email_capture_pipeline.py`, `email_classification.py::
  thread_match_merge`, `vault_writer.py`'s Thread primitives — the analyst's own
  `## Context` "why one story, not two" reasoning, reused here at the sprint
  level), and the story's own decomposer pass explicitly reasoned the two halves
  as one coherent build ("content quality is only worth doing once the pull-
  decoupling half stops the pipeline from randomly wedging mid-work," the PRD's
  own sequencing framing). Splitting would produce two ordered-but-not-really-
  dependent sprints for no isolation benefit, and 8 tasks sits exactly at this
  project's own well-calibrated single-sprint L ceiling (below), not past it —
  unlike `SPRINT-049`/`050`'s split, which was driven by a REAL cross-story
  `depends_on` edge plus a live-verification-gated boundary, neither of which
  exists here.
- **Never mixes phases** — `REQ-SB-69-US-01` is `P1` throughout; no `BUGFIX-NN`
  or other-phase story is bundled in.
- **Sizing estimate:** ~8 tasks, L — directly matches this project's own
  repeatedly-confirmed-accurate 8-task/L precedent (`SPRINT-010`, `SPRINT-039`,
  `SPRINT-035`, `SPRINT-049`, all matched their estimate exactly at retro per
  `Implementation/Learnings.md`), and sits at, not past, this project's own
  largest confirmed-accurate ceiling (`SPRINT-021`/`SPRINT-030`, 9 tasks/L).
  `T04` (independent-dispatch + lock separation — the mechanism making
  Scenarios 2/3 true by construction, per the decomposer's own framing) and `T06`
  (wiring the new filename/lookup/rename mechanism into `thread_match_merge`,
  plus the stale-payload fix) are expected to be the heaviest tasks, by
  live-verification/induced-stall-concurrency effort rather than code volume —
  consistent with this project's own repeated sizing-calibration finding
  (`Implementation/Learnings.md`, most sprints) that the heaviest task is the one
  carrying the real correctness/concurrency proof, not the largest diff.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-056 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-69-US-01](../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md) | Decouple the Outlook pull out of Classify/Thread-Match-Merge/Route-to-Project into a durable vault-local staging step, and make Thread notes read like a human wrote them | P1 | Done (8/8 tasks, all 11 locked ACs verified live) |

**Tasks in scope** (dependency order, two independent roots, two mostly-independent
chains — verified directly against each task file's own `depends_on:` frontmatter):

- Pull/staging half: `T01` (staging primitives, `depends_on: []`) → `T02` (Pull
  step / `on_item_fetched` callback, `depends_on: [T01]`), `T03` (pipeline reads
  from staging, `depends_on: [T01]`) → `T04` (independent pull_email/
  process_staged_email dispatch, lock separation, `depends_on: [T02, T03]`).
- Thread content-quality half: `T05` (filename/lookup/rename primitives,
  `depends_on: []`) → `T06` (wire `thread_match_merge` + stale-payload fix,
  `depends_on: [T05]`) → `T07` (human-readable dates, `depends_on: [T06]`) →
  `T08` (Related-section wikilinks, `depends_on: [T06, T07]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. Every real upstream dependency this story's own
  `## Dependencies` names is already `Done`: `REQ-SB-55-US-01`
  (`SPRINT-049`), `REQ-SB-56-US-01` (`SPRINT-053`), `REQ-SB-63-US-01`
  (`SPRINT-050`), `REQ-SB-67-US-01` (`SPRINT-054`), `REQ-SB-68-US-01`
  (`SPRINT-055`) — no sprint-level edge is needed for already-completed work.
- **Standing story-level flag, not a build blocker.** `REQ-SB-69-US-01` carries
  `gate: flagged`, `gate_reason: "trigger-3 (ADR-046 created)"` from the
  architect's pass — a standing breadcrumb awaiting a human look at `ADR-046`,
  independent of delivery progress, per this project's own established
  `REQ-SB-54-US-01`/`SPRINT-048` and `REQ-SB-55-US-01`/`SPRINT-049` precedent
  ("a flagged story is fully eligible for `/plan-sprints` and
  `/implement-sprint`"). Not duplicated as a new `REVIEW-QUEUE.md` entry by this
  pass — the architect's own pointer (`REVIEW-QUEUE.md`, filed 2026-08-17)
  already covers it.
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`) and
  real Outlook/Compass — the story's own `## Constraints`/task `## Tests` blocks
  name real, live-triggered pulls and induced-stall concurrency checks; no
  fixture/test vault substitutes for the mandatory live verification.

---

## Out of Scope

- **Giving `Pull` its own Agent-tier identity** — `ADR-046` Decision 5 resolves
  against this; the story's own Non-Goals.
- **`REQ-SB-53`'s original Puller/Tagger/Linker/Storer 4-agent split** — stays
  `Parked`, not revived.
- **Reconciling multiple `ConversationID`s into one real Conversation** —
  `REQ-SB-60`'s own separate, deferred scope.
- **A Scheduling-view row for the new, decoupled Pull step** — open question,
  not designed or built here; `T04` explicitly does not touch `GET
  /system-health`'s response shape or `SystemHealthPage.tsx`.
- **Backfilling already-captured Thread notes onto the new filename/date/
  wikilink shape** — going-forward capture only, per the story's own Non-Goals.
- **Real-time push/WebSocket-based live staging-queue depth display** — no new
  observability UI beyond what the story's `## Affected Screens` already scopes
  as open.
- **Any change to Classify/Thread-Match/Merge/Route-to-Project's own internal
  decision logic** (customer/kind classification, tag accumulation,
  project-routing guess, recurring-pattern detection) — only Pull's timing and
  the Thread note's filename/dates/links change.
- This pass was scoped specifically to `REQ-SB-69-US-01` per the launching
  agent's explicit instruction (the only `Ready`, ungrouped story flagged for
  tonight's autonomous run) — it did not re-survey the rest of the backlog for
  other `Ready`/ungrouped stories; any such story remains available for a future
  `/plan-sprints` pass.

---

## Definition of Done

- [x] Every story in scope has status `Done` — `REQ-SB-69-US-01`, all 8 tasks Done
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      — already done at the architect's own `/plan-tasks` pass (confirmed
      present, unchanged by this coder pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-046`
      confirmed `Status: Accepted`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — exact match. The
  sprint's own sizing note (`T04` and `T06` expected to be the heaviest,
  "by live-verification/induced-stall-concurrency effort rather than code
  volume") held precisely: `T04` (this task) needed a real, controlled,
  induced-stall concurrency proof (two independent live dispatch tests)
  and surfaced/fixed a genuine transitive circular import; `T06` found and
  fixed a real live regression (`BUG-019`) in an out-of-scope module
  (`meeting_classification.py`) via a `grep`-before-assuming discipline.
  Both diffs were small; both took real verification effort well beyond
  their line count.

### What worked

- **Two independent roots, two short converging chains (the diamond
  shape) let concurrent coder sessions build `T02`/`T03` (and separately
  discover each other's progress mid-session) and `T05` in parallel with
  zero file-level conflicts** — confirmed directly: `T02`'s own
  Implementation Log records finding `T03` already `Done` mid-session, no
  collision, no rework.
- **Controlled/deterministic monkeypatching beat relying on real
  Outlook/Compass latency for a timing-comparison proof.** `T04`'s first,
  fully-real `AC-02` attempt was genuinely ambiguous (both a stalled Pull
  and a real 4-email Compass run finished within ~1s of each other at
  ~210s, for two entirely unrelated real reasons) — re-run with a
  controlled sleep on one side and a fast, deterministic stub on the
  other produced an unambiguous ms-precision proof in both directions
  (`0.53s`/`0.01s` vs. a known `15s` stall).
- **`grep`-before-assuming a retired function is dead code.** `T06`
  grepped for `thread_note_exists`/`thread_note_path` before treating
  them as superseded-but-harmless, and found a real, live second caller
  outside its own scope (`meeting_classification.py`) — escalated
  (`ESC-044`) and fixed same-pass (`BUG-019`) rather than shipping a
  silent regression.
- **The story's own analyst/architect passes writing every Scenario at
  the observable-outcome level, deliberately leaving mechanism-level
  latitude to the coder, worked as intended** — every task's own
  disclosed scope-internal judgement calls (`T02`'s callback-filtering
  reconciliation, `T04`'s `run_capture_for_agent`/`run_capture_and_
  record_completion` split, `T06`'s `date` parameter, `T08`'s helper
  signature) were resolvable from the task's own text plus the already-
  `Accepted` `ADR-046`, with zero need to stop and ask.

### What didn't work

- **Checking only the DIRECT one-hop import edges is not enough to rule
  out a circular import.** `T04`'s own initial top-level `skill_tools.py
  -> email_capture_pipeline` import compiled and even ran successfully
  under one real import order (triggered via `agent_schedule_registry`
  first) before a DIFFERENT, equally-real order (`import
  email_capture_pipeline` first) hit a genuine `ImportError`. Root cause:
  a TRANSITIVE cycle through `email_classification.py`'s own OTHER
  imports (`vault_filing_expert -> agent_orchestration -> ... ->
  knowledge_bootstrap -> skill_registry -> skill_tools`), not the direct
  edge either task's own docstring precedent described. `T06`
  independently hit and worked around the SAME underlying cycle from a
  different entry point the same night — this is a real, recurring
  hazard in this codebase's own current module graph, not a one-off.
- **A real, external Compass API degradation (`CompassError: couldn't
  parse Compass response`) during `T04`'s own live verification made one
  regression check (full E2E filing via `run_capture_now`) unable to show
  a literal successful outcome for its 4 real test emails, even though
  the STRUCTURAL claim `T04` owns (Pull+Process compose in one call) was
  independently, conclusively proven via call-count instrumentation.**
  Root cause is plausibly this sprint's own repeated, heavy, same-session
  real-API test traffic (rate limiting) rather than a code defect —
  disclosed in `T04`'s own Implementation Log, not silently worked
  around.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Dual independent `asyncio.Lock`s for two capabilities of one Agent
  that must never block each other** — when a single Agent-tier identity
  gains a second, independently-dispatched capability that must survive a
  stall in the first (or vice versa), give it its OWN dedicated
  `asyncio.Lock` and a sibling dispatch function mirroring the existing
  one's exact shape (skip-not-queue on contention, `asyncio.to_thread`,
  run-state marking, outcome recording) — never a flag/parameter on the
  existing shared-lock dispatcher. This makes the "never blocks the
  other" property true BY CONSTRUCTION (no lock is ever shared), not by
  convention/discipline. `agent_schedule_registry.py`'s `dispatch_with_
  shared_lock`/`dispatch_with_dedicated_processing_lock` pair is the
  concrete precedent; `_RUN_STATE_TRACKED_CAPABILITY_ID` (singular)
  widening to a plain tuple of tracked ids is the matching pattern for
  extending shared observability state to a new capability without a new
  hardcoded list.
- **Verify a "no circular import" claim by actually importing the new
  edge from more than one real entry point, not just tracing direct
  one-hop imports on paper.** At minimum: import the new module directly
  first, AND import the real app entry point (`app.main`) first — the
  second is what matters for production correctness (real `uvicorn`
  startup order), the first is what actually exercises the worst-case
  order. A deferred (inside-function) import is the fix once a real cycle
  is confirmed — never assumed pre-emptively without confirming the risk
  is real first (over-deferring costs nothing structurally but obscures
  intent).
- **When a real, live-triggered timing comparison between two dispatch
  paths would otherwise depend on unpredictable real network/COM
  latency, stub the deepest LEAF call on both sides to a controlled,
  deterministic duration/outcome while keeping every dispatch/lock layer
  above it 100% real.** This isolates the property actually under test
  (lock independence) from environmental variability, without weakening
  the proof — the induced-stall side still uses a real, observable sleep;
  the comparison side's own internal correctness is not what's being
  proven by this specific test.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a shared dispatch function's "Autonomous mode does X" branch
  can be split by trigger value without checking every OTHER real caller
  of the function it delegates to.** `run_capture_for_agent`'s own email
  branch is called by THREE real, independent paths (the scheduled
  composite tick, `run_capture_now`'s manual/chat dispatch, and a
  Supervised background-approval's Approve dispatch) — a naive "just make
  the scheduled path Pull-only" change without also fixing what `run_
  capture_for_agent` itself composes would have silently broken the OTHER
  two callers' own "fully captured end-to-end" contract, since an earlier
  task in the same story (`T03`) had already retired Fetch from the
  function `run_capture_for_agent` delegates to.

### Open follow-ups

- **`agent_schedules_router.py::run_now` hardcodes the shared Outlook-COM
  dispatch lock for every `capability_id`, unconditionally** — a manual
  `POST .../schedules/process_staged_email/run-now` would incorrectly
  route through the shared lock instead of the new dedicated processing
  lock, reintroducing lock-sharing for that one specific manual trigger
  path. Disclosed by `T04` (outside its own `## Files to Modify`); the fix
  is a one-line conditional mirroring the two fixes `T04` already made in
  `agent_schedule_registry.py`/`capture_scheduler.py`. Not filed as a
  `BUGS.md` entry — no locked AC or Constraint is violated (the hard
  Constraint binds the hourly/app-start scheduled tick specifically, which
  IS correctly lock-separated) — but worth a small follow-up task.
- **A genuinely pre-existing, task-independent circular-import fragility**
  (`skill_registry.py`'s own top-level `_SKILL_HANDLERS` dict literal
  reading `skill_tools.diagram_understanding` at module-load time, hit
  only when `app.business.skill_tools` is imported standalone-first,
  bypassing `app.main`) was confirmed real but is never reached by actual
  `uvicorn` startup — not fixed (out of every task's own scope this
  sprint), disclosed here in case a future refactor of `skill_registry.py`
  wants to close it structurally (e.g. building `_SKILL_HANDLERS` lazily
  instead of as a module-level literal).
- **`ADR-046`'s own standing `trigger-3` human-review flag remains
  unresolved** — a human should read `ADR-046` in full before this
  sprint's own work is considered fully signed off, per the architect's
  own original flag (unrelated to build completeness; every task's own
  ACs are independently verified).

---

## Notes

**Sprint assembled 2026-08-17 (`/plan-sprints`), scoped to `REQ-SB-69-US-01`.**
Per the launching agent's explicit instruction, this pass targeted the one
requirement raised tonight following a real Outlook-COM production incident,
under the operator's own full-autonomy grant — not a full backlog survey for
other `Ready`/ungrouped stories. `REQ-SB-69-US-01` enters `/plan-sprints`
`status: Ready`, `gate: flagged` (trigger-3, `ADR-046` — a standing breadcrumb,
not a blocker, per the established `REQ-SB-54-US-01`/`SPRINT-048` and
`REQ-SB-55-US-01`/`SPRINT-049` precedent, reconfirmed here).

**Dependency graph read directly from each of the 8 task files' own
`depends_on:` frontmatter** (not just the story's own summary table) —
confirmed: `T01: []`, `T02: [T01]`, `T03: [T01]`, `T04: [T02, T03]`, `T05: []`,
`T06: [T05]`, `T07: [T06]`, `T08: [T06, T07]`. Two independent roots (`T01`,
`T05`), two short converging chains, no edge between the two halves, no cycle —
a clean DAG. This exactly mirrors `REQ-SB-55-US-01`'s own 8-task diamond shape
(`SPRINT-049`), reconfirming "8 tasks, two-root diamond/chain shape" as this
project's own well-calibrated single-sprint L ceiling.

**Gate: `gate: clear` 2026-08-17.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the single-story, single-sprint
grouping is read directly off the decomposer's own recorded `depends_on` graph
(confirmed by reading all 8 task files directly, not inferred), and no
cross-story dependency exists to reconcile (this pass's scope is one story);
(2) `REQ-SB-69` is not `<!-- Draft -->`/unfinalised in the PRD; (3) product-owner
does not write ADRs — `ADR-046` was already authored at the architect's own pass,
unedited here; (4) no new `ESCALATIONS.md` entry; (5) not oversized (8 tasks, L,
matching four prior confirmed-accurate 8-task/L precedents — `SPRINT-010`,
`SPRINT-035`, `SPRINT-039`, `SPRINT-049` — and at, not past, this project's own
largest confirmed-accurate ceiling, `SPRINT-021`/`SPRINT-030`, 9 tasks/L); not a
`Blocked` story (all 8 tasks are `status: Ready`); no cross-sprint dependency had
to be introduced (`depends_on_sprints: []` — every real prerequisite is already
`Done`); (6) N/A (coder-only trigger); (7) no contradictory inputs for this
pass's own grouping act; (8) not genuinely ambiguous — a single-story,
single-sprint grouping is the only reasoned partition here (no real cross-story
edge, no phase split, no sizing-ceiling breach that would force a split), not a
toss-up among equally-valid alternatives. Advances `Draft → Ready`.

**`BACKLOG.md` updated:** `REQ-SB-69` row's Story Status left as the story's own
live `status:`/`gate:` string, Sprint column set to `SPRINT-056`, Sprint Status
set to `Ready`; a new `SPRINT-056` row appended to the Sprint Status table.

**REVIEW-QUEUE.md:** no new entry written by this pass — `REQ-SB-69-US-01`'s own
standing `ADR-046`/trigger-3 flag (filed by the architect, 2026-08-17) already
covers the one open human-review item; this pass's own grouping decision is
unambiguous and introduces no new flag.

**Eligible for `/implement-sprint`** — `status: Ready`, `gate: clear`,
`depends_on_sprints: []` (nothing to wait on).
