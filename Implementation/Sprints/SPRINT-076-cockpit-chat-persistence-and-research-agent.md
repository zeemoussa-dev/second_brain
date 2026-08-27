---
id: SPRINT-076
title: Cockpit Chat Persistence + Research Agent — the two independent foundations REQ-SB-82's remaining substories build on
status: Done
gate: flagged
gate_reason: "sprint-retro-harvest — both stories Done, every locked AC verified live; retro drafted below for human skim + Learnings.md propagation, per the pipeline's own sprint-wrap protocol"
phase: P2
depends_on_sprints: []
sizing_estimate: "~5 tasks, M"
created: 2026-08-25
started: "2026-08-25"
completed: "2026-08-25"
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

# SPRINT-076 — Cockpit Chat Persistence + Research Agent

## Sprint Goal

Build the two independent foundational mechanisms `REQ-SB-82`'s remaining
substories (`US-03`, `US-05`) need to exist first: a real, persisted
Cockpit chat store (`US-01`) and a Librarian-Section Research Agent
(`US-02`).

---

## Grouping Rationale & Sizing

- **Why grouped:** `REQ-SB-82-US-01` and `REQ-SB-82-US-02` have **no
  dependency on each other** (confirmed directly from the decomposer's own
  task frontmatter — `REQ-SB-82-US-01-T01`/`REQ-SB-82-US-02-T01`/`T02` all
  carry `depends_on: []`), but each is a **hard foundation** another
  `REQ-SB-82` substory needs before it can build: `US-03`'s `T02`/`T03`
  depend on `US-01`'s `T01`/`T02`/`T03`; `US-05`'s `T02` depends on
  `US-02`'s `T02`. Grouping the two independent foundations into one
  sprint, ahead of a second sprint for their two dependents, honours the
  real dependency graph (hard rule 7) while keeping each sprint's own
  internal task count inside this project's own confirmed-accurate sizing
  ceiling.
- **Why NOT one sprint of all four stories:** this project's own
  `Learnings.md` sizing-calibration history caps out at 9 tasks/L as the
  largest sprint that matched its own estimate exactly (`SPRINT-021`,
  `SPRINT-030`); all four `REQ-SB-82` substories together total 10 tasks
  across four stories touching materially different subsystems (a new
  JSON persistence store + REST endpoints + frontend wiring; a brand-new
  Hermes Skill + live profile provisioning; deterministic backend matching
  logic + new frontend UI; a second Hermes Skill + cron declaration) — each
  with its own real, non-trivial live-verification cost (`SPRINT-027`/
  `SPRINT-029`'s own repeated finding: verification effort, not code
  volume, is what actually drives a sprint's real cost). Splitting along
  the graph's own natural fault line — the two independent foundations
  first, their two dependents second — keeps both sprints inside the
  proven ~5-6-task/M envelope instead of pushing past the largest
  confirmed-accurate precedent. This is a disclosed product-owner sizing
  judgement call, not a PRD- or dependency-graph-dictated split (either
  shape is dependency-graph-legal); reasoned here rather than silently
  picked, per this project's own "disclose real judgement calls, don't
  hide them" convention. Not flagged as `ambiguous-partition`, since the
  sizing evidence above gives a clear, non-arbitrary basis for the choice.
- **Sizing estimate:** ~5 tasks, M (`US-01`: 3 tasks; `US-02`: 2 tasks).
  `US-02-T02` carries a real, disclosed live-provisioning cost beyond its
  own code volume (a live Hermes profile + Skill installation, per the
  decomposer's own note on that task) — expect that to be the heavier of
  the five.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-076 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-82-US-01](../UserStories/REQ-SB-82-US-01-persisted-cockpit-chat.md) | Persisted Cockpit Chat — real roster + message-history storage | P2 | Done |
| [REQ-SB-82-US-02](../UserStories/REQ-SB-82-US-02-research-agent-librarian-section.md) | Research Agent — Librarian-Section capability, no approval needed | P2 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- Internal task order (within this sprint, per the decomposer's own
  `depends_on`): `REQ-SB-82-US-01-T01` → `T02` → `T03` (linear chain);
  `REQ-SB-82-US-02-T01` and `T02` are both independent (`depends_on: []`
  each) and may build in either order.
- `REQ-SB-82-US-03`/`REQ-SB-82-US-05` (this sprint's downstream consumers)
  are deliberately NOT in this sprint — see `SPRINT-077`, which records
  `depends_on_sprints: [SPRINT-076]` for exactly this reason.

---

## Out of Scope

- `REQ-SB-82-US-03` (Meeting Moderator roster pre-assembly) and
  `REQ-SB-82-US-05` (Meeting Preparation Agent) — both depend on this
  sprint's own output and are sequenced into `SPRINT-077` instead.
- `REQ-SB-82-US-04` (Meeting Moderator live routing + async research) —
  still `Draft`/`gate: flagged` (unresolved routing-mechanism/threaded-UI/
  Hermes-back-channel risk, see its own `## Notes`); not `Ready`, so not
  eligible for any sprint yet.
- Enabling the Chat composer to send/receive a real message —
  `REQ-SB-82-US-01`'s own Non-Goals (deferred to `US-04`).
- Growing the Research Agent into a full Expert, or any merge/dedup logic
  across repeated research requests — `REQ-SB-82-US-02`'s own Non-Goals.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed beyond what `ADR-008` (already Accepted, pre-existing) already documents
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-008`, already `Accepted` before this sprint started
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

- **Estimated:** ~5 tasks, M — **Actual:** 5 tasks, M (`US-01`: 3 tasks;
  `US-02`: 2 tasks) — matched exactly. `US-02-T02`, correctly predicted
  as the heaviest, carried a real, disclosed live-provisioning cost (a
  brand-new Hermes profile plus Skill installation and 3 separate real
  agent-turn round trips for live verification) well beyond its own
  code volume — reconfirms this project's own repeated "verification
  effort, not code volume, drives real sprint cost" finding.

### What worked

- **Mirroring an already-proven, real precedent file-for-file
  (`azure-kb-writer`'s `write_azure_doc.py`/`SKILL.md`) instead of
  designing a new Skill contract from scratch** — the CLI shape
  (`--vault-path`/`--input-file`, scratch JSON payload, frontmatter +
  `## Summary`/`## Details`), the plain-`terminal`-invocation calling
  convention, and even a second real precedent's own collision-avoidance
  primitive (`capture_note.py`'s `_unique_note_path`) all transferred
  directly with zero rework — the ONE deliberate divergence (never
  update in place) was exactly, and only, what `ADR-008` called for.
- **Verifying the real `hermes profile create --clone` shape against an
  already-Done sibling profile (`azure-expert`) before assuming any
  pruning/customization step was needed** — confirmed live that a fresh
  clone's bundled `skills/` tree is byte-for-byte the same set
  `azure-expert` itself still carries (no removal ever happened for that
  family), which correctly ruled out an unnecessary "trim Primary-style
  skills" step that would have been unrequested scope for this task.
- **A three-call live verification ladder (direct chat → cross-profile
  relay → deliberately-unanswerable request) proved all three
  caller-behavior/honesty-related ACs (`AC-01`/`AC-04`/`AC-05`) with real,
  independently-inspectable evidence** (2 real distinct notes in
  `Work/Research/`, one real "found nothing, wrote nothing" reply) rather
  than reasoning about any of them from the SOUL.md/Skill text alone.

### What didn't work

- No real friction this sprint — `US-01`'s 3 tasks and `US-02`'s 2 tasks
  both built and verified on the first pass, no rework, no reordering.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **When a task explicitly authorizes real, live, out-of-repo
  infrastructure provisioning (a new Hermes profile via `--clone`), verify
  the CLI's own real cloning behavior against an already-Done sibling
  profile before assuming any customization/pruning step is needed** —
  the closest-to-real ground truth for "what does a fresh clone actually
  contain" is a real, already-working sibling profile, not the CLI's own
  `--help` text or a guess. Found live, `REQ-SB-82-US-02-T02`.
- **A 3-step live-verification ladder (direct call → cross-caller relay →
  deliberately-unanswerable request) is a reusable shape for any new
  agent whose locked ACs cover both "does real work" and "behaves
  consistently/honestly regardless of caller or outcome"** — each rung
  produces its own independently-inspectable real artefact (a note, or
  the explicit absence of one), rather than inferring caller-agnostic or
  honest-failure behavior from static prompt text alone. Found live,
  `REQ-SB-82-US-02-T02`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- No new antipattern this sprint.

### Open follow-ups

- `REQ-SB-82-US-04` (Meeting Moderator live routing + async research)
  remains `Draft`/`gate: flagged` — unresolved design/routing questions,
  tracked in `REVIEW-QUEUE.md`, not a consequence of this sprint's own
  work.
- `SPRINT-077` (`REQ-SB-82-US-03`/`US-05`) is now unblocked —
  `depends_on_sprints: [SPRINT-076]` is satisfied.
