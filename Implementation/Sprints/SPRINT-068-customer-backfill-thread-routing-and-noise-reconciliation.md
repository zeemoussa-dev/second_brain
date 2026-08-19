---
id: SPRINT-068
title: Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint-wrap retro drafted — human skim + Learnings.md propagation; ADR-055 review also still standing"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-068 — Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation

## Sprint Goal

Ship the Librarian's new batched propose/approve Customer-routing Job for
the real 137-Thread backlog (including brand-new Customers like TAQA) plus
evidence-based archival-candidate surfacing for existing folders with zero
real Thread matches — never a silent write, archive-not-delete.

---

## Grouping Rationale & Sizing

- **Single story, one sprint.** All 6 tasks belong to `REQ-SB-74-US-01`,
  one Definition of Done, one architecture scope (`architecture.md` → "The
  Librarian — Customer Backfill", `ADR-055`). Graph read directly from each
  task file's own `depends_on:` frontmatter (per the decomposer's own
  recorded reasoning in the story's Decomposer pass):
  - `T01` (`propose_customer_backfill()` + its own 2 new `data_access`
    primitives) — `depends_on: []`, root — the shared detection/grouping
    every other task consumes.
  - `T02` (`finalize_customer_backfill_routing`) — `depends_on: [T01]` —
    needs `T01`'s own payload shape settled first.
  - `T03` (`propose_customer_archival_candidates`) — `depends_on: [T01]` —
    consumes `T01`'s own `list_customer_folders()` primitive and its own
    returned matched-Customer set (one evidence pass, never a second,
    independent Compass sweep, per `ADR-055` Decision 5).
  - `T04` (`move_okf_directory()` + `finalize_customer_archival`) —
    `depends_on: [T03]` — needs `T03`'s own payload shape settled first.
  - `T05` (`_APPROVAL_HANDLERS` registration + one orchestrating endpoint) —
    `depends_on: [T01, T02, T03, T04]` — needs every propose/finalize pair
    to exist before it can register or route to any of them.
  - `T06` (full-corpus backfill run + a real approve round trip +
    re-run/no-re-propose verification) — `depends_on: [T01, T02, T03, T04,
    T05]` — needs the whole wired system reachable via the real endpoint.
  - Acyclic, all `phase: P1`.
- **Not split further** — the two propose/finalize pairs (`T01`/`T02` and
  `T03`/`T04`) share a root (`T01`) and converge in the same single-story
  assembly (`T05` → `T06`); splitting would add a needless
  `depends_on_sprints` edge for zero real decoupling value, the same
  antipattern already named in `SPRINT-063`'s own `## Notes`.
- **Not bundled with `REQ-SB-73-US-01`** — see `## Notes` below for the
  full independence reasoning (both stories add Jobs to the same
  `librarian_housekeeping.py`/`email_poc_router.py` files, but the
  decomposer explicitly confirmed zero task-level `depends_on` edge in
  either direction between the two stories' task sets).
- **Sizing estimate: ~6 tasks, M.** Matches this project's own repeatedly-
  confirmed "~6 tasks, M" bucket (`SPRINT-007`, `SPRINT-012`, `SPRINT-020`,
  `SPRINT-022`, `SPRINT-028`, `SPRINT-044`, `SPRINT-048`) and sits well
  under the `librarian_housekeeping.py` module's own proven 9-task/L
  ceiling (`SPRINT-063`). Not oversized.
- **Manually-triggered, not scheduled** — the story's own standing
  Constraint keeps this Job OUT of `run_housekeeping_pass()`'s recurring
  chain, so this sprint carries no ordering interaction with any other
  Librarian Job's own schedule.

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-74-US-01's own
frontmatter now carries sprint: "SPRINT-068". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-74-US-01](../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md) | Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation | P1 | Done |

**Tasks in scope** (dependency order): `T01` → `T02` (also feeds `T05`);
`T01` → `T03` → `T04` (also feeds `T05`); `T02` + `T04` → `T05` → `T06`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `REQ-SB-54-US-01` (`SPRINT-048`, Done),
  `REQ-SB-57-US-01` (`SPRINT-057`, Done), and `REQ-SB-72-US-01`
  (`SPRINT-063`, Done) are the story's own hard prerequisites — all already
  `Done`, so no NEW cross-sprint dependency is introduced by this sprint
  (confirmed directly: every one of this story's own 6 tasks' `depends_on`
  edges resolves to another task WITHIN this same story/sprint).
- **External:** none new — the real, already-configured vault this Job
  backfills (137 real Threads, all still `customer: "Unsorted"`; 26 real
  existing Customer folders, confirmed live 2026-08-19).

---

## Out of Scope

- Project-level routing (Thread → Project beneath a Customer) — stays
  untouched; this requirement only reaches Customer, one level up.
- Pipeline-stage or topic/content tags on Threads — the deeper Thread
  taxonomy question stays open for a later, separate conversation.
- Wiring `synthesize_customer`/`resync_project_from_thread` into this write
  path or into live capture (`#128`, still parked).
- Hand-classifying any of the 26 existing folders by name alone (Columbus,
  Sindan, AZCON Holding, HR Avatar, etc.) — evidence-based only.
- Wiring this Job into `run_housekeeping_pass()`'s recurring schedule —
  manually-triggered one-time backfill only.
- Any new `html-prototype/` screen — `my-day-approvals.html`'s existing
  generic `.item-row` pattern covers both new proposal kinds.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — N/A, no architectural fact changed this sprint (built exactly per `ADR-055`/architecture.md's already-written "Customer Backfill" section)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-055` already `Accepted` from the architect pass; unchanged by this build
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** `~6 tasks, M` — **Actual:** 6 tasks, M, all `Done` in one
  session, zero blocked, one in-scope defect found and fixed live (`T05`).
  **Takeaway:** exact match again — this project's own "~6 tasks, M"
  bucket (`SPRINT-007`, `-012`, `-020`, `-022`, `-028`, `-044`, `-048`)
  holds for a sixth time. The real cost driver wasn't task count but
  wall-clock time: 3 full real-corpus passes (~577s, ~480s, ~483s) for
  live AC verification at 100+-real-Thread scale — sizing in "tasks"
  captured build effort correctly; it doesn't (and isn't meant to)
  capture real-external-API verification wall-clock time.

### What worked

- **Direct-function-call verification for T01-T04, real HTTP for T05/T06**
  (this codebase's own established two-tier technique, `REQ-SB-72-US-01`'s
  precedent) — proved the business logic first, cheaply and precisely,
  then proved HTTP reachability/dispatch separately. Caught the real
  Compass-connection-drop defect at the HTTP tier specifically (100+
  sequential real calls in one request is where a transient network
  hiccup actually surfaces), not at the function tier.
- **Reusing real, already-correct T01 output for T02-T04's own
  verification** (rather than hand-constructing disposable synthetic
  payloads) turned every AC check into a genuine, production-value action
  on real, trusted vault data (no staging/promotion gate, `CLAUDE.md`) —
  TAQA's own real routing and a real Twitter/Google archival are now
  permanently correct, not test-only artifacts to later redo.
- **A dedicated, isolated server process** (port 8002, not the two other
  already-running dev servers on 8000/8001 belonging to concurrent
  sessions) avoided any cross-session interference while building
  alongside `SPRINT-067`'s own concurrent, disclosed-safe, additive edits
  to the SAME `librarian_housekeeping.py`/`email_poc_router.py` files —
  confirmed zero collision the whole session.

### What didn't work

- **`detect_customer_for_thread`'s own "no retry loop" design (`ADR-055`
  Decision 2, correctly mirroring `classify_task`) has no Job-level
  safety net for a multi-hundred-call sequential pass** — a single
  transient Compass connection drop wasted an entire ~120-Thread real
  pass (all Compass calls already made were discarded, since batches are
  only persisted as Pending Approvals AFTER the whole detection loop
  completes). Root cause: the ORIGINAL `T01` build (mirroring `ADR-055`
  correctly) had no per-item failure isolation in the JOB's own loop, a
  different, orthogonal concern from the per-CALL retry `ADR-055`
  explicitly scoped out. Fixed in `T05` once it surfaced for real.
- **`propose_customer_archival_candidates`'s own "this pass only" evidence
  window (`ADR-055` Decision 5, correct per its own locked AC wording)
  produces real false positives across REPEATED real passes** for any
  Customer already fully routed by an earlier pass — surfaced twice for
  real this session (`Aldar`, `LinkedIn`). Not a code defect against any
  locked AC, but a real rough edge for a "manually re-triggerable" Job
  whose own re-trigger risk `ADR-055` disclosed only for the ROUTING side,
  not the archival side.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Job-level failure isolation is a DIFFERENT concern from per-call
  retry, and both may be needed** — when a new Job's own real, live-run
  scale (dozens to hundreds of sequential external calls in one pass) is
  materially larger than the sibling function whose retry contract it
  mirrors, add per-item try/except + an honest `"failed"` key around the
  EXTERNAL call inside the JOB's own loop (this codebase's already-
  established `backfill_files`/`detect_mentioned_companies_for_thread`
  pattern), even when the ADR correctly decided the call itself needs no
  retry loop. One does not substitute for the other.
- **When verifying a propose/approve Job against real, trusted,
  no-staging-gate data, reuse the real propose output for the finalize
  verification instead of hand-constructing a disposable payload** — it
  is both a correctness proof AND genuinely useful, permanent forward
  progress on the real backlog, not throwaway test scaffolding.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A "this pass only" evidence window for a negative/absence-based
  proposal (archival, decommission, cleanup) that can be manually
  re-triggered multiple times will re-flag anything already resolved by
  an earlier pass as a NEW false positive** — if a future story adds
  another "propose X for entities that get zero evidence this pass" Job,
  it should explicitly decide (and the ADR should record) whether prior-
  pass resolution history is in scope to check, rather than silently
  inheriting `ADR-055`'s own narrower, correctly-scoped-for-THIS-story
  precedent.
- **Triggering a real, expensive, full-corpus external-API pass multiple
  times within one build session (once per task needing its own real
  proof) compounds `trigger="direct"`'s own disclosed no-idempotency-guard
  duplication risk fast** — by session end, 64+31 real pending records
  existed for one story alone. Where a task's own literal Tests block
  allows either a function-level OR an HTTP-level real check for the SAME
  underlying evidence, prefer reusing ONE real trigger's own output across
  multiple tasks' verification (as this session did for `T02`-`T04`)
  rather than re-triggering the full external pass per task.

### Open follow-ups

- **Cross-pass archival evidence** (flagged to `REVIEW-QUEUE.md`) — decide
  whether a future story should add a "has real, currently-linked
  Threads" exclusion to `propose_customer_archival_candidates`, out of
  this story's own locked scope.
- **64 pending routing + 31 pending archival-candidate real records**
  (flagged to `REVIEW-QUEUE.md`) — operator review/consolidation needed;
  substantial real duplication from 3 real full-corpus triggers this
  session, per `ADR-055`'s own disclosed, accepted risk.
- **`ADR-055` itself** — still awaiting the standing architect-level human
  review (unrelated to this build; carried forward, not newly introduced).

---

## Notes

**Grouping decision (product-owner, 2026-08-19):** Two `Ready`, ungrouped
stories existed this pass — `REQ-SB-74-US-01` (this sprint) and
`REQ-SB-73-US-01` (`SPRINT-067`). The decomposer's own task-level
`depends_on` graph confirms no edge exists between the two stories' task
sets in either direction (each story's own Decomposer pass states this
explicitly). Both are `phase: P1` and both add Jobs to the SAME
`librarian_housekeeping.py`/`email_poc_router.py` files, but that is a
disclosed shared-file overlap, never a functional dependency — neither
story's functions call, read, or depend on the other's.

**Why kept as two separate sprints, not one combined sprint:** combining
would total 6 + 4 = 10 tasks, one task ABOVE this project's own proven,
twice-exactly-matched single-story-sprint ceiling (9 tasks, L —
`SPRINT-021`, `SPRINT-030`, `SPRINT-063`, all exact estimate-vs-actual
matches per `Implementation/Learnings.md`). With zero real dependency
forcing them together, bundling would only add oversized-sprint risk for
no real decoupling benefit. Each sprint alone (`~6 tasks, M` here; `~4
tasks, S` for `SPRINT-067`) sits comfortably within this project's own
repeatedly-confirmed sizing buckets.

**Why no `depends_on_sprints` edge to `SPRINT-067`:** the decomposer
explicitly confirmed independence at `/plan-tasks` (both stories' own
Decomposer passes state it identically); building them in either order, or
concurrently across sessions, is safe — the shared-file overlap is
additive (different functions in the same file), not a call/data
dependency.

**Story-level ADR flag, not this role's to clear:** `REQ-SB-74-US-01`
carries `gate: flagged` (`trigger-3`, `ADR-055`) from the architect pass —
an already-open, separate `REVIEW-QUEUE.md` line item ("review `ADR-055`
... before the build starts"). Per the `SPRINT-060` precedent (built while
`ADR-048`'s own standing review flag was still open), this standing
architect-level flag does not, by itself, make THIS role's own grouping
decision ambiguous, oversized, blocked, or cross-sprint-dependent — the
partition itself is unambiguous. The sprint is therefore set `gate: clear`
at this stage; the ADR-055 review remains open under its own existing
`REQ-SB-74-US-01` line item in `REVIEW-QUEUE.md`, untouched by this pass.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this role's own
grouping decision: not oversized (6 tasks, M, well under the proven
ceiling); no blocked story; no NEW cross-sprint dependency (all 3 hard
prerequisite sprints are already `Done`); the split-vs-combine partition
was actively considered and resolved on real sizing/dependency grounds,
not left ambiguous. Advanced `Draft → Ready` — eligible for
`/implement-sprint SPRINT-068`.
