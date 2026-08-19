---
id: SPRINT-069
title: The Vault — Real-Data Knowledge Graph Screen
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint close — retro drafted for human skim/harvest, plus the standing REQ-SB-75-US-01-T03 scope-internal judgement call, see REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
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

# SPRINT-069 — The Vault — Real-Data Knowledge Graph Screen

## Sprint Goal

Ship a new "The Vault" screen at `/vault` that reshapes the existing
`vault_indexing.get_index()` data into a real, interactive force-directed
knowledge graph (nodes = notes, edges = resolved wikilinks), with kind
filters, name search, and click-through into the existing `/browse/:stem`
note detail route.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single story, `REQ-SB-75-US-01`, with exactly one strict,
  acyclic task dependency chain (`T01 → T02 → T03` — backend reshape/
  endpoint, then rendering engine, then page assembly/route/nav). Per hard
  rule 7 / Pipeline.md, a strict dependency chain belongs in one sprint, not
  split across ordered sprints — none of the tasks is independently
  buildable or verifiable ahead of its predecessor (`T02` composes `T01`'s
  real endpoint; `T03` composes `T02`'s real rendering engine). No other
  `Ready`, ungrouped story exists to combine or contend with — confirmed via
  `grep '^status: Ready'` across `Implementation/UserStories/`: the only 4
  hits are this story plus `REQ-SB-74`/`REQ-SB-59`/`REQ-SB-42`, each of
  which already carries a non-empty `sprint:` (`SPRINT-068`/`SPRINT-059`/
  `SPRINT-039` respectively) and is therefore excluded from this sweep.
- **Sizing estimate:** ~3 tasks, S — matches this project's own repeated
  "3 tasks, S, one additive backend reshape + endpoint plus a small frontend
  chain" precedent (`SPRINT-023`, `SPRINT-024`, `SPRINT-050`, all landed
  exactly on this estimate per `Implementation/Learnings.md`). No new ADR,
  no new npm dependency, no new indexing/caching mechanism — the decomposer
  already confirmed this is a composition of already-`Accepted` `ADR-003`/
  `ADR-010`.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-069 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-75-US-01](../UserStories/REQ-SB-75-US-01-the-vault-knowledge-graph-screen.md) | The Vault — Real-Data Knowledge Graph Screen | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None — `REQ-SB-01` (Vault Indexing) and `REQ-SB-02`
  (Browse & Search) are the story's hard PRD-level blockers, but both are
  already `Done` (shipped `SPRINT-025`/`SPRINT-026`); this story only reuses
  their already-shipped, unmodified code (`vault_indexing.get_index()`,
  `/browse/:stem`/`NoteDetailPage`), so no `depends_on_sprints` edge is
  needed — nothing here is still in flight.
- No other external dependency.

---

## Out of Scope

- Any new note-detail rendering/editing beyond the existing `/browse/:stem`.
- Resolving the "Vault Browser" vs. "The Vault" naming overlap (non-blocking,
  per the story's own `## Notes`).
- Large-corpus performance work (neighborhood scoping/clustering) — out of
  scope at the vault's current real scale (~680 notes).
- A new `html-prototype/` screen file — design sign-off already happened
  against a live Artifact this same session; not required.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (n/a — the architect's `/plan-tasks` pass already recorded the full mechanism; no further architectural fact changed during build)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (n/a — no new ADR, confirmed pure composition of `ADR-003`/`ADR-010`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints (n/a — no new decision/pattern/constraint emerged during build beyond what the decomposer already recorded)
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

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S — matched exactly,
  extending this project's own repeated "3 tasks, S, one additive backend
  reshape + endpoint plus a small frontend chain" precedent
  (`SPRINT-023`/`SPRINT-024`/`SPRINT-050`) a fourth time. `T03` (the
  integration task carrying all 6 locked ACs) was correctly identified up
  front as the real cost center — not in code volume (the page itself is
  ~110 lines), but in live-verification complexity: a real force-directed
  canvas has no stable DOM per-node/per-edge representation to query, so
  proving click-through/filter/search behavior needed several
  React-internals techniques (Fiber `memoizedProps`, Fiber hook-chain
  reads for `VaultGraphCanvas`'s own internal simulation-position refs)
  layered on top of the more ordinary DOM-text/screenshot checks.

### What worked

- **Layer-by-layer live verification, cheapest layer first** (backend
  HTTP call at `T01`, real browser at `T03`) — reconfirmed once more;
  caught nothing wrong at the cheap layer, so `T02`/`T03` could build
  against a fully-trusted real endpoint with zero backend surprises.
- **Deriving exact click coordinates from the component's own real
  internal simulation state (via a React Fiber hook-chain read), rather
  than assuming where force-directed physics "should" settle** — an
  initial assumption ("an isolated single node settles to dead canvas
  center") was directly falsified by a screenshot showing the node well
  off-center (alpha decay bounds how far the centering force can pull a
  node before forces vanish, it does not guarantee full convergence to
  center). Reading `simulationNodesRef`/`panRef`/`scaleRef` directly off
  the owning fiber's hook list, then computing the real screen coordinate
  from that, turned an unreliable assumption into 5/5 exact real clicks
  landing on 5/5 real nodes across all 5 named kinds, first try after the
  fix.
- **A real, dedicated headless-Edge CDP instance (own
  `--user-data-dir`/`--remote-debugging-port`), driven by a minimal native
  `fetch`+`WebSocket` Node script** — zero new dependency, reused this
  project's own established Learnings precedent
  (`SPRINT-032`/`033`/`035`/`036`/`038`) directly, with zero adaptation
  needed for a canvas-only (no stable per-node DOM) screen.

### What didn't work

- **A React-Fiber `memoizedProps` read via `canvasEl[fiberKey]` +
  walking `.return` intermittently returned a STALE snapshot after a
  rapid second state toggle** (confirmed via a side-by-side
  `fiber.alternate` read showing the correct, current value at the exact
  same instant the "current" pointer's own reads did not) — while the
  real, ground-truth DOM (count text, chip class, screenshots) was
  correct and consistent across every single toggle. Root cause not
  fully isolated (a `current`/work-in-progress fiber-swap timing subtlety
  specific to this exact double-toggle-in-quick-succession shape); the
  practical fix was trusting ground-truth DOM/pixel evidence over the
  Fiber introspection for a fast state-flip check, and reserving the
  Fiber-read technique for slower, single-state-read verifications
  (`AC-02`, `AC-05`) where it worked perfectly every time.
- **Assuming a force-directed simulation's own centering force would
  reliably pull a lone, unconnected node to exact canvas center within a
  few seconds** — false; `ALPHA_DECAY` bounds the total impulse applied
  before forces vanish entirely, so a node can settle well short of
  center depending on its pre-existing position. Cost one investigation
  cycle (a first `AC-05` click attempt, aimed at assumed canvas center,
  silently missed every node) before switching to reading the real
  simulation position directly.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Read a canvas-rendered (non-DOM) component's own real internal
  simulation/position state directly via a React Fiber hook-chain walk,
  rather than assuming a physics simulation converges to a predictable
  layout** — when a screen has no stable per-element DOM node to query
  (a hand-rolled `<canvas>` force-directed graph), this is the only way
  to get exact, real click-target coordinates for a genuine
  `PointerEvent` dispatch. Confirm the real hook index order live first
  (a hook consumed by an upstream call like `useNavigate()` shifts every
  subsequent index) rather than assuming declaration order maps 1:1 to
  hook-list position.
- **When a React-Fiber `memoizedProps`/hook read disagrees with the real,
  ground-truth DOM text/screenshot for the SAME state, trust the DOM** —
  the DOM is what the user (and every locked AC's own "the operator
  sees/clicks X" wording) actually cares about; treat a Fiber-introspection
  disagreement as a testing-technique finding to investigate/disclose, not
  as evidence the app itself is broken.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a hand-rolled force-directed simulation's centering force
  converges a lone node to exact canvas center within a short, fixed
  wait** — an alpha-decay-bounded simulation applies only a FINITE total
  impulse before forces vanish; verify the real settled position
  directly (component's own internal state) rather than clicking a
  computed "should be here" coordinate.
- **Relying on a single React-Fiber `memoizedProps` read as the SOLE
  evidence for a state check performed twice in quick succession** (e.g.
  uncheck-then-recheck the same toggle within ~1-2 seconds) — cross-check
  against ground-truth DOM text/screenshots when the two disagree, rather
  than trusting the Fiber read by default.

### Open follow-ups

- The `T02`→`T03` Fiber-introspection staleness finding (see "What
  didn't work," above) is worth a small, standalone investigation if this
  verification technique is reused heavily in a future sprint — not
  filed as a story (no product-facing gap, testing-technique-only).
- `REQ-SB-75-US-01-T03`'s own disclosed scope-internal judgement call
  (`main.tsx` touch) is open in `REVIEW-QUEUE.md` for human spot-check.
