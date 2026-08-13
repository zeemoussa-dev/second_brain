---
id: SPRINT-020
title: Section Hub Intelligence & Cross-Section Routing — per-agent keywords, Hub-to-Hub routing node
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Built and verified live 2026-08-12 — all 6 tasks Done, all 4 locked ACs verified live; flagged for the human's spot-check pass on scope-internal judgement calls (see story's own Notes / REVIEW-QUEUE.md) and to harvest this Retrospective into Implementation/Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"                        # YYYY-MM-DD when status → Done
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

# SPRINT-020 — Section Hub Intelligence & Cross-Section Routing

## Sprint Goal

Build and verify `REQ-SB-20-US-01` end to end: free-text keyword assignment
per agent on the Agent Settings surface, and a `route_hub_request`
LangGraph node (`ADR-017`) that relays a cross-Section help request through
the requesting agent's own Hub, then the target Section's Hub, by keyword
match only — never a direct agent-to-agent call across Sections.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — all 6 tasks belong to
  `REQ-SB-20-US-01`/`REQ-SB-20`, the only story assigned here. Mirrors this
  project's own established precedent for a single, decently-sized story
  filling its own sprint (`SPRINT-012`, `SPRINT-019`, etc.) rather than
  being force-bundled with an unrelated story just to fill space.
- **Foundation of a larger dependency chain, not a standalone build.** This
  story is the first "layer" of a 5-story, ~28-task business-use-case chain
  (today's "Compass Expert" pilot): `REQ-SB-35-US-01` (Vault Filing Expert)
  and `REQ-SB-36-US-01` (Web Research Skill) both carry real, decomposer-
  confirmed cross-story `depends_on` edges onto this story's own tasks
  (`T02`, `T05`), and `REQ-SB-36-US-02` (the Compass Expert pilot) composes
  this story's routing mechanism as its own first hop. This sprint is
  sequenced first for that reason — see `SPRINT-023`/`SPRINT-022`/
  `SPRINT-024`'s own `depends_on_sprints` edges.
- **Why NOT bundled with `REQ-SB-21-US-01` (Agent Working Modes), despite
  both being `Ready`, `gate: clear`, `P1`, and part of the same overall
  business chain:** the two stories' own task graphs have **zero**
  `depends_on` edge onto each other in either direction — confirmed by
  direct reading of both story files' task tables. Nothing downstream
  needs them built in the same sprint or even in a particular order
  relative to each other; only later stories (`REQ-SB-35-US-01`,
  `REQ-SB-36-US-02`) need *both* done, which is captured correctly via
  those sprints' own `depends_on_sprints: [SPRINT-020, SPRINT-021]` edges,
  not by artificially coupling `SPRINT-020`/`SPRINT-021` together.
  Bundling them would double this sprint's size (6 → 15 tasks, well past
  every prior sprint's own size) for no dependency-graph or shared-file
  reason (`REQ-SB-20-US-01` touches `agent_keywords.py`/`graph.py`'s
  routing node/`AgentDetailPanel.tsx`'s keyword row; `REQ-SB-21-US-01`
  touches `working_mode_registry.py`/`pending_approval_registry.py`/
  `agents_router.py`'s gate/a new Pending-Approvals page — no shared file
  between the two task sets) and would remove real, legitimate parallelism
  (`REQ-SB-36-US-01` can start the moment this sprint alone is `Done`,
  without waiting on `REQ-SB-21-US-01` too). Kept as two separate,
  independently-sequenced sprints instead — mirrors `SPRINT-019`'s own
  precedent of documenting and rejecting a considered bundling rather than
  leaving it implicit.
- **Sizing estimate:** ~6 tasks, M — `T01 → T02` (vault-writer primitives →
  business module) is the load-bearing chain; `T03`/`T06` (router field,
  frontend keyword row) and `T04`/`T05` (orchestration state field, the
  routing node itself) each branch off `T02`. Comparable to `SPRINT-007`/
  `SPRINT-012`'s own 6-task M precedent.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-020 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-20-US-01](../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md) | Per-agent keyword assignment and Hub-mediated routing for cross-Section help requests | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-20-US-01-T01]]
(`agent_keywords.json` vault-writer primitives, `depends_on: []`),
[[REQ-SB-20-US-01-T02]] (`agent_keywords.py` business module, `depends_on:
[T01]`), [[REQ-SB-20-US-01-T03]] (agents router `keywords` field,
`depends_on: [T02]`), [[REQ-SB-20-US-01-T04]] (orchestration state
`hub_routing_result` field, `depends_on: [REQ-SB-25-US-01-T02]`, already
`Done`), [[REQ-SB-20-US-01-T05]] (`route_hub_request` node +
`request_cross_section_help` tool, `depends_on: [T02, T04,
REQ-SB-25-US-01-T07]`, already `Done`), [[REQ-SB-20-US-01-T06]] (frontend
keyword row, `depends_on: [T02, T03]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `T04`/`T05`'s task-level edges onto
  `REQ-SB-25-US-01-T02`/`T07` are already satisfied — that story shipped
  `Done` in `SPRINT-014` (also `Done`) — recorded here for traceability
  only, no open ordering edge.
- `ADR-017` (Hub-routing keyword storage + routing-node mechanism) is
  `Accepted` but still carries its own open human-review flag on the story
  (`gate: clear` per the story's most recent note, but the ADR itself
  still awaits a human skim per `REVIEW-QUEUE.md`) — not a blocker for
  `/implement-sprint`, since the story's own `status: Ready`/`gate: clear`
  already reflects that review path having been reconciled; recorded here
  for visibility only.

---

## Out of Scope

- `REQ-SB-21-US-01` (Agent Working Modes) — considered for bundling,
  rejected; see Grouping Rationale. Built in its own sprint, `SPRINT-021`.
- `REQ-SB-35-US-01`, `REQ-SB-36-US-01`, `REQ-SB-36-US-02` — the three
  downstream stories that depend on this one; each has its own sprint
  (`SPRINT-023`, `SPRINT-022`, `SPRINT-024` respectively), sequenced after
  this one via `depends_on_sprints`.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (N/A — `ADR-017`/`architecture.md`'s own "Section-Hub cross-Section routing" subsection were already written at `/plan-tasks`; this build pass composed around the real current files, no further architectural-fact change)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-017`, already `Accepted` at `/plan-tasks`; unchanged by this build pass)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M. Sizing held exactly;
  no task needed splitting or turned out oversized. `T05` (the graph node)
  was the heaviest by a wide margin — not in task count, but in the amount
  of real-file reconciliation needed against three sibling stories'
  intervening changes (see below).

### What worked

- Building strictly in dependency order (`T01 → T02 → {T03 → T06, T05}`,
  `T04` independent) meant every downstream task's own live smoke check
  used real, already-verified state from its upstream — no task had to
  guess at an unverified assumption from an earlier task.
- `ADR-017` point 5's own directly-callable `route_cross_section_request`
  (built specifically so this story's own ACs could be verified without
  first wiring a live, model-driven tool-call trigger end-to-end) worked
  exactly as designed — `AC-02`/`AC-03`/`AC-04` were all verified as real,
  deterministic Python-shell calls against the real backend, with zero
  dependency on `REQ-SB-25-US-01-T08`'s live chat-wiring being reachable.
- This project's own established Learnings pattern ("compose the new
  change around the REAL current file, never overwrite it with the stale
  sample") generalized cleanly a second time (first found at
  `REQ-SB-26-US-01-T03`) — `graph.py`/`state.py`/`agents_router.py` had
  each grown materially since this task breakdown was authored
  (`REQ-SB-26-US-01`/`ADR-016` memory nodes; `REQ-SB-25-US-01-T08`/
  `REQ-SB-31-US-01`'s live tool-execution-loop and async corrections), and
  reading the real current file before applying any diff caught the one
  genuinely load-bearing divergence (the routing tool-call interception
  had to happen before the graph's own generic tool-execution node, not
  after — see below).
- The React-Fiber-props-direct-invoke pattern (`MEMORY.md` Patterns, first
  found `REQ-SB-18-US-01-T07`) generalized cleanly to a third distinct
  scenario (`onBlur` on a free-text commit-on-blur input, vs. the original
  `onClick` on a `disabled`-gated button) — confirmed a real, unmodified
  production code path fires exactly the same whether triggered by a real
  user interaction or this direct-invoke technique, by observing the real
  `PATCH` request over the CDP `Network` domain both times.

### What didn't work

- Two task files' own illustrative example need-descriptions
  (`T02`/`T05`) did not actually contain their own example keywords as a
  literal substring under the exact deterministic algorithm the task
  itself specifies — a wording slip in the test data (not the algorithm,
  not the code), only caught by actually running the example live rather
  than trusting it by inspection. Cheap to catch and correct once run for
  real; would have silently "passed" a purely code-review-based
  verification pass without ever noticing the algorithm and the example
  disagreed.
- A plain synthetic `blur` `Event` dispatch, and even a real
  `input.focus()`/`input.blur()` DOM-API call pair, did not reliably
  deliver React's delegated `onBlur` handler in this specific
  headless-Chrome-via-CDP session — confirmed via the CDP `Network` domain
  that no `PATCH` request ever fired, despite `document.activeElement`
  genuinely changing. Resolved by falling back to the already-documented
  Fiber-props-direct-invoke technique, but cost real debugging time before
  landing on it — see Patterns, below, for a way to shortcut that next
  time.

### Patterns to carry forward

- **Verify `onChange`/`onBlur`-driven React commit handlers via
  Fiber-props direct-invoke by default in a headless-Chrome-via-CDP
  session, not native DOM `focus()`/`blur()` calls** — this session found
  live that even real `.focus()`/`.blur()` DOM-API calls (which do
  genuinely change `document.activeElement`) did not reliably deliver the
  native `focusout` bubbling event React's `onBlur` prop depends on, in
  this specific headless environment. Going straight to reading the real
  handler off `element[Object.keys(element).find(k =>
  k.startsWith('__reactProps$'))].onBlur` and invoking it with `{ target:
  element }` — confirming a real network request as evidence the identical
  production code path fired — is faster and more reliable than debugging
  synthetic-event delivery first. Extends the existing
  `onClick`-on-`disabled`-button precedent (`REQ-SB-18-US-01-T07`) to
  `onBlur`-on-commit-input; likely generalizes to any React synthetic
  event type in this same harness.
- **Run a task's own illustrative example test data live before trusting
  it, even when it looks obviously correct on inspection** — a
  deterministic keyword-substring-match algorithm is simple enough that an
  example string can *look* like it should match while not actually being
  a literal substring (singular vs. plural, an apostrophe-s changing the
  character sequence). The fix is cheap (correct the example, log the
  finding) but only surfaces by actually running it.

### Antipatterns to avoid

- Do not assume a task file's own "Before" code sample still matches the
  real current file's shape once 2+ sibling stories may have landed
  additive changes to the same shared file in between — this is now the
  **second** time this exact class of drift caused a task sample to
  require reconciliation against reality (`REQ-SB-26-US-01-T03`, this
  sprint's `T05`), both times on `graph.py` specifically, this project's
  most actively-extended shared file. Always re-read the real current file
  immediately before applying any task's own literal code block to it.

### Open follow-ups

- `ADR-017`'s own human-review item remains open in `REVIEW-QUEUE.md`
  (unresolved since 2026-08-12, predating this build pass) — not a blocker
  for this sprint's own `Done` status (an ADR-creation flag does not halt
  `/implement-sprint`, mirroring the same posture already established for
  `/plan-tasks`), but still awaiting a human decision independent of this
  sprint's own completion.
- `SPRINT-022`/`SPRINT-023` (both `depends_on_sprints: [SPRINT-020, ...]`)
  are now unblocked on this sprint's own side — `SPRINT-022`/`SPRINT-023`
  specifically need `T02`'s `agent_keywords` module and `T05`'s
  `graph.route_cross_section_request`, both `Done` and live-verified.

---

## Notes

**Sprint assembled 2026-08-12 (`/plan-sprints`, operator-directed batch —
the "Compass Expert" business chain).** Part of a 5-sprint sequence
(`SPRINT-020`…`SPRINT-024`) partitioning a real, ~28-task, 5-story
dependency chain that is larger than any single sprint built so far this
session. Each story kept as its own single-story sprint (this project's
own well-established default shape) rather than one giant multi-story
sprint, specifically so `/implement-sprint` never has to hold this much
cross-story context in one working session, and so real parallelism
(`REQ-SB-20-US-01`/`REQ-SB-21-US-01` have no dependency on each other) is
not artificially removed by bundling. Full cross-story `depends_on` graph
verified by direct reading of all 5 story files' own task tables before
partitioning — not re-derived from scratch, confirmed against the
decomposer's own already-recorded edges.

**Gate: `gate: clear` 2026-08-12.** No MUST-FLAG trigger fires: (1) no
material assumption — the partition is read directly off the already-
recorded task `depends_on` graph, not guessed; (2) `REQ-SB-20` is not
`<!-- Draft -->`/unfinalised; (3) product-owner does not write ADRs — none
touched; (4) no new `ESCALATIONS.md` entry written by this pass; (5) not
oversized (6 tasks, M, well inside precedent) and no cross-sprint
dependency was introduced for *this* sprint specifically
(`depends_on_sprints: []` — this is the first sprint in the chain); (6)
N/A (coder-only trigger); (7) no contradictory inputs; (8) not genuinely
ambiguous — one story, one natural partition, the one considered
alternative (bundling with `REQ-SB-21-US-01`) documented and rejected
above rather than left implicit. Advances `Draft → Ready`.
