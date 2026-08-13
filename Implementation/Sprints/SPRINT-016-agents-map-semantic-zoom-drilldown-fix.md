---
id: SPRINT-016
title: Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retrospective drafted, awaiting human skim/harvest into Learnings.md. (T06's scope-internal judgement call spot-checked and accepted 2026-08-12 — no longer a factor.)"
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"            # YYYY-MM-DD when status → Done
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

# SPRINT-016 — Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix)

## Sprint Goal

Close `BUG-002`: make every agent always render within its own Section's
visual territory at the Agents Map overview (small, unlabeled compact dots
regardless of density), with a click-to-drill-down per-Section "Agents
Tree" view — porting the already-approved, live-browser-verified Option D
design from the prototype into the real React app.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-02-US-01` is the only
  `Ready`, ungrouped bugfix story this pass. Its 6 tasks form one acyclic
  dependency graph (`T01`/`T02`/`T03`/`T04` independent roots → `T05`
  depends on all four → `T06` depends on `{T02, T03, T04, T05}`),
  implementing one cohesive fix (containment math + rendering/interaction
  port). There is no partition question: one story, one dependency chain,
  nothing to split without inventing an artificial cross-sprint edge
  through the middle of it (would contradict hard rule 7).
- **Why not combined with `REQ-SB-08-US-01-T06`** (the other ungrouped item
  this pass, a small hardening fix on an already-`Done` story): no shared
  file, shared module, or shared verification surface exists between the
  two — this story is a frontend-only Agents Map layout/rendering fix
  (`layoutAgents.ts`, `AgentNode.tsx`, `SectionHub.tsx`,
  `AgentsMapCanvas.tsx`, `SectionDrilldown.tsx`, `agents-map.css`);
  `REQ-SB-08-US-01-T06` is a backend-only Outlook calendar/vault-writer
  dedup-key fix (`outlook_com.py`, `vault_writer.py`,
  `meeting_classification.py`). Pipeline.md hard rule 8's bugfix-sprint
  phase exemption applies to *this* story regardless of pairing, but
  pairing two technically unrelated items purely because both are
  "hardening, not new-feature work" would be a cohesion-free grouping —
  unlike `SPRINT-007`'s own precedent for combining independent stories
  (which shared one taxonomy-resolution origin and a matched combined
  size), there is no real shared origin, shared file, or shared
  verification pass here to justify combining. Kept separate — see
  `SPRINT-017`.
- **Sizing estimate:** ~6 tasks, M — matches `SPRINT-007`'s own 6-task M
  combined precedent; comparable in shape/risk to
  `REQ-SB-18-US-01-T05`/`T06`'s own frontend-task precedent this story's
  own decomposer pass cited directly, and smaller than `SPRINT-011`'s own
  8-task L (this fix reuses `ADR-010`'s already-`Accepted` component shape
  and `ADR-014` point 6's already-ported N-section-generic layout math — no
  new architectural pattern, a fully worked reference implementation
  already approved in the prototype).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-016 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-02-US-01](../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md) | Agents Map — semantic-zoom overview + per-Section Agents Tree drill-down (BUG-002 fix, ported to the real app) | — (bugfix, phase-agnostic) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` confirm it is not blocked:
  `REQ-SB-18-US-01` (Dynamic Agent Sections, `Done` — `SPRINT-011`) already
  delivers the dynamic N-section hub-angle math this fix's containment
  math scales with. No other blocker.
- The approved Option D design (+ both refinements) is already
  live-browser-verified in the canonical `html-prototype/agents-map.html`/
  `.js` (`REVIEW-QUEUE.md`'s "BUG-002 layout exploration" entry,
  2026-08-12 final update) — no further `/design` pass needed before this
  sprint starts.
- Frontend-only change — no backend/API contract change, no new external
  dependency.

---

## Out of Scope

- Option C's communication-affinity clustering or cross-Section affinity
  lines — not the accepted direction.
- Any change to `REQ-SB-20`'s Hub routing logic — purely visual/layout.
- Re-theming Hub coloring or any other visual convention beyond what the
  approved prototype already settled.
- Replaying the overview entrance animation from the drill-down's own
  "Back to Agents Map" button — explicit follow-on extension, not built
  here.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      — N/A, no architectural fact changed by the build (component/prop/
      function decomposition within already-`Accepted` `ADR-010`/`ADR-014`
      shapes, per the architect's own pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — N/A, no
      new ADR
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)
- [x] `BUG-002` flipped `In Sprint → Closed` in both `BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror once this sprint is `Done`

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M, all `Done` in one
  pass with zero rework — **Takeaway:** accurate. Every task's own `##
  Files to Modify` code block was fully specified by the decomposer (down
  to literal diffs), which made this sprint closer to careful transcription
  + live verification than open-ended implementation — worth noting for
  future sizing that a decomposer pass this thorough measurably de-risks
  the coder pass's own effort, not just the planning pass's.

### What worked

- Building strictly in dependency order (`T01`-`T04` independent roots →
  `T05` → `T06`) with a `tsc --noEmit` smoke check after every task caught
  zero integration surprises by the time `T06` wired everything together —
  the whole chain type-checked clean on the first attempt at every step.
- Reusing the already-running backend (port 8001) and frontend (port 5173)
  dev servers instead of restarting them, per this run's own instruction —
  avoided both `MEMORY.md`'s known "dev-server restart fires a real
  capture run" side effect and any port-conflict churn with the
  concurrently-running `SPRINT-014` session in the same real directory.
- headless-Chrome-via-CDP (this project's own standing zero-dependency
  frontend-verification pattern) scaled cleanly to a genuinely interactive
  multi-step scenario (click Hub → wait for CSS `transitionend` → assert
  drill-down DOM → click Back → assert restored state) — no new tooling
  needed, `Page.captureScreenshot` with `captureBeyondViewport` also
  produced a full-page screenshot of content that had scrolled off the
  initial 1000px-tall viewport, which was the key piece of evidence for
  confirming the "drill-down renders below the fold" finding below was
  the approved design, not a rendering defect.

### What didn't work

- The headless Chrome instance became unreachable over CDP partway through
  verification (likely resource pressure from several successive
  `json/new` tab creations without closing prior tabs) — required
  detecting the failure (`ECONNREFUSED` on `/json/version`) and relaunching
  a fresh instance with a new `--user-data-dir` profile. Cost a few minutes
  of re-diagnosis, no data loss (each verification script was independently
  re-runnable against the still-live dev servers).
- `T06`'s own manual-test wording (a "nearest-hub-center-distance"
  heuristic operationalizing "stays within its own angular wedge") turned
  out not to be logically equivalent to the locked AC's own literal text
  ("no agent node or label visually overlaps..."), and the two diverged in
  practice: 2 of 4 real dense-Section agents were geometrically nearer a
  neighboring Hub's center than their own, while zero actual visual
  (bounding-box) overlap existed anywhere. Root cause: the overview's ring
  radii are global across every Section (pre-existing, explicitly frozen
  by this story's own `T01` Constraints), so the heuristic was never a
  sound proxy for "no visual overlap" to begin with — this was a decomposer-
  time wording gap, not a build defect, and didn't block `Done` since the
  locked AC's own literal criterion was independently verified true. See
  the Open follow-up below.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Verify visual-containment ACs via real DOM `getBoundingClientRect()`
  intersection, not a distance-to-center proxy** — when a locked AC's own
  wording is about visual overlap ("no node overlaps X"), the load-bearing
  check is literal bounding-box intersection between the real rendered
  elements; a "nearest center distance" heuristic can diverge from it
  whenever elements sit at different radii/sizes from their reference
  point (found live this sprint: `SECTION_ARC_SPAN_DEG`'s pre-existing,
  out-of-scope, global-not-per-Section ring radii made the distance
  heuristic fail for real agents that had zero actual visual collision).
  Prefer the literal geometric check the AC text itself asserts over any
  task-authored proxy, and cross-check with a full-page screenshot when
  in doubt.
- **Relaunch headless Chrome with a fresh `--user-data-dir` the moment
  `/json/version` stops responding, rather than debugging the stale
  instance** — cheap (a few seconds), avoids sunk-cost time on a process
  that's already gone; every verification script in this sprint's session
  was written to be idempotent/re-runnable against the still-live app
  servers, which made this a zero-cost recovery.
- **Full-page (`captureBeyondViewport`) screenshots settle "is this really
  rendering correctly?" for content that scrolls out of the default
  viewport** — this sprint's drill-down view genuinely renders below the
  fold in normal document flow (confirmed as the approved design's own
  real behavior, not a defect, by cross-checking the prototype's own markup
  comment and JS for an absent auto-scroll) — a viewport-only screenshot
  alone would have looked like a blank-page failure.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a task's own manual-test wording as automatically equivalent
  to its parent locked AC's literal text** — a decomposer-authored
  verification step is an operationalization, not the AC itself; when the
  two diverge (as they did here), the coder must resolve in favor of the
  AC's own literal wording and re-verify against that directly, logging
  the divergence rather than silently picking whichever is easier to pass
  or silently failing the task over a proxy that was never load-bearing.

### Open follow-ups

- Consider a future task to scope `layoutAgents()`'s ring radii per-Section
  (rather than global) so an outer-ring agent can never sit geometrically
  nearer a neighboring Section's Hub than its own — purely a tightening of
  an already-non-overlapping visual result, not a defect fix; filed here
  for decomposer attention if a future bug report ever shows a *real*
  visual collision at higher agent density than today's real data
  (currently 4 in one Section) exercises. Not filed as a new `BUG-NNN` —
  no observed defect, just a geometric margin worth widening proactively.
- `MEMORY.md`'s "all 5 agents in Technical" framing (from `BUG-002`'s
  original filing) is now stale — the real seed/assignment data has
  drifted to 4-in-Productivity/1-in-Customers over the course of this
  session's other concurrent work. Worth a human note if `BUG-002`'s
  history is ever referenced again expecting the original "Technical"
  grouping specifically.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired: (1) no material
assumption — grouping and sizing both trace directly to the story's own
already-locked task breakdown and dependency graph, not guessed; (2)
`BUG-002` is a finalised, non-`Draft` ledger entry; (3) N/A (product-owner
does not touch ADRs); (4) no `ESCALATIONS.md` entry written; (5) not
oversized (6 tasks matches the `SPRINT-007` M-precedent), not `Blocked`,
no cross-sprint dependency introduced (`depends_on_sprints: []`); (6) N/A
(coder trigger); (7) no contradictory inputs; (8) not genuinely ambiguous
— single-story sprint, no real alternative partition. Per Pipeline.md hard
rule 8's bugfix-sprint exception, `phase: ""` — `BUGFIX-02-US-01` itself
carries no `phase:` field. Advances `Draft → Ready`.

**Sprint assembled (2026-08-12):** 1 story, 6 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (`/implement-sprint SPRINT-016`), 2026-08-12:** All 6 tasks
built and verified in dependency order; `BUGFIX-02-US-01` and `SPRINT-016`
both advance to `status: Done`. `BUG-002` flipped `In Sprint -> Closed` in
both `BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror. `BACKLOG.md`'s Sprint
Status table row updated to `Done`. Full build/verification evidence lives
in each task's own Implementation Log (`T06`'s is the most detailed — it
carries the story's one locked-AC live-browser verification pass).

`gate: flagged 2026-08-12` on sprint close — two reasons, both per
Pipeline.md's standard sprint-wrap protocol and MUST-FLAG trigger 8: (1)
the Retrospective above is drafted, not yet human-skimmed/harvested into
`Implementation/Learnings.md` (standard for every sprint close, not
specific to this one); (2) `T06`'s own scope-internal judgement call
(verifying `AC-01`'s containment clause via literal DOM rect-intersection
rather than its own draft "nearest-hub-center" heuristic, fully reasoned
in `T06`'s Implementation Log) is carried up to this sprint's own gate for
visibility, per Pipeline.md's "scope-internal judgement calls... make the
task gate: flagged" rule. Neither is a blocker — every locked AC is
verified `Done`, nothing in this sprint is `Blocked`.
