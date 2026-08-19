---
id: REQ-SB-38-US-01
title: Agents Map Density Clustering — collapse a crowded Section+Type-ring's overflow agents into a clickable cluster marker
requirement_ids: [REQ-SB-38]
requirement_section: "REQ-SB-38: Agents Map Density Clustering"
phase: P1
status: Done
gate: flagged
gate_reason: "coder T04 scope-internal judgement call — src/frontend/src/pages/AgentsMapPage.tsx required a minimal, mechanical edit outside any task's declared Files to Modify; see REQ-SB-38-US-01-T04's Implementation Log"
sprint: SPRINT-037
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-38-US-01 — Agents Map Density Clustering — collapse a crowded Section+Type-ring's overflow agents into a clickable cluster marker

## Story

**As a** Second Brain user
**I want** the Agents Map overview to collapse a Section's overcrowded agents
into a single "+N" cluster marker instead of rendering every agent at a fixed
position regardless of how many share that Section
**So that** the overview stays readable as the number of agents grows, and I
can still see exactly which agents are inside a cluster by clicking it

## Context

- PRD: `Documentation/PRD.md` -> *REQ-SB-38: Agents Map Density Clustering* —
  "As the number of agents within a Section grows, the Agents Map overview
  groups agents that would otherwise crowd/overlap into a single cluster
  marker — a circle showing a count and a '+' — instead of rendering every
  individual agent node at a fixed position regardless of how many share the
  same Section. Clicking a cluster marker shows the agents inside it."

- **Operator's own words, verbatim (2026-08-13, raised the same day
  `BUG-009`/`BUG-010` were fixed live):** "This is a problem and will always
  appear as the number of Agents grow, we will have them on top of each
  other... We need to be able to cluster some agents together to limit the
  overlapping in future — a circle with a number and '+' so we can click on
  it to view the agents inside." `BUG-009`'s own fix corrected
  `layoutAgents.ts`'s fan-out angle to stay within a Section's own wedge
  boundary (`SECTION_ARC_SPAN_DEG_CAP`), but that only prevents cross-Section
  spillover — it does nothing about same-Section, same-ring crowding as
  agent count grows within that now-correctly-bounded wedge. This story is
  the next layer: a real density/scale problem, distinct from that boundary
  fix, and distinct from `layoutSectionDrilldown`'s own full-360-degree
  drill-down spread (out of scope here — see Non-Goals).

- **`/design` ran and produced a demonstrated prototype
  (`html-prototype/agents-map.html`'s "Density clustering (REQ-SB-38 demo)"
  state), but sign-off was lukewarm and non-specific — this materially
  bounds this story.** `REVIEW-QUEUE.md`'s own entry records the operator's
  response as "It's okay kinda," and that the operator declined to specify
  what's off when asked directly. Per that entry's own explicit instruction,
  **this analyst pass does not treat that lukewarm approval as confirming
  the prototype's own two most load-bearing numbers.** Everything else the
  prototype demonstrates is treated as an approved design reference, same as
  any other `/design` output.

- **Resolved here, from direct precedent already established elsewhere in
  this codebase (not a new assumption):**
  1. **Click-to-view mechanic.** A cluster marker's click reuses the exact
     click-to-zoom mechanic `BUG-002`'s Option D already established for
     Section Hubs (`AgentsMapCanvas.tsx`'s existing zoom-then-mount-drilldown
     flow) — applied one level deeper, opening a drill-down scoped to only
     the clustered subset, not the whole Section. This is not new
     interaction design; it is the same mechanism the operator's own words
     ask for ("click on it to view the agents inside").
  2. **A cluster marker never represents agents of more than one Type.**
     `layoutAgents.ts` already keys an agent's radius to its own Type's ring
     (Worker/Expert/Producer) and its angle to its Section — a single
     cluster marker occupies one fixed position on one ring, so it can only
     ever stand in for agents that would otherwise render on that same ring.
     This holds regardless of how the two flagged questions below are
     ultimately resolved.
  3. **The Section Hub's own full drill-down is out of scope for this
     story.** Clicking a Section's Hub (not a cluster marker) still opens
     `layoutSectionDrilldown`'s existing full, unclustered spread of every
     agent in that Section — including the ones a cluster marker represents
     on the overview. The approved prototype demonstrates this deliberately
     (its own inline callout says so), matching the PRD's own framing of
     this as a separate, still-open question (see Non-Goals).

- **Genuinely NOT resolved here — left open, per this task's explicit
  direction not to treat the lukewarm approval as confirming them:**
  1. **The exact clustering threshold.** The prototype's own top-of-file
     breadcrumb proposes `VISIBLE_SLOT_CAP = 6` agents, hand-sized by
     checking chord spacing at today's real 5-Section geometry — explicitly
     labeled there as "the designer's own proposal, flagged for confirm/
     adjust," not a settled number. This story does not adopt `6` as final.
  2. **The clustering scope granularity.** The prototype scopes clustering
     per (Section x Type-ring) — i.e., a Section's Worker agents, Expert
     agents, and Producer agents are each checked against the threshold
     independently, rather than checking the Section's total agent count as
     one pool. This is presented in the prototype's own breadcrumb as the
     designer's own reasoning from how `layoutAgents.ts` already renders
     (real crowding only happens within one ring), not a confirmed product
     decision. This story does not adopt per-(Section x Type-ring) as the
     final, locked scoping rule — see the Acceptance Criteria's own framing
     below, which describes the demonstrated behavior for grounding without
     asserting it as settled.
  3. Whether a cluster's own count needs to update live as agents are
     added/removed (PRD's own open question 5, tied to `REQ-SB-37` Agent
     Creation, itself still `Draft`) — out of scope for this pass (see
     Non-Goals).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks, once the two flagged open questions in Context are confirmed and
these scenarios' generic "clustering threshold"/"clustering scope" language
can be tightened to a real, confirmed number and granularity. -->

### Scenario 1: A crowded Section+ring collapses its overflow agents into one cluster marker

```gherkin
Given a Section has more agents on the same Type-ring — grouped by
    (sectionId, agentType) — than the app's VISIBLE_SLOT_CAP of 6 allows to
    render as individual nodes (e.g. 15 same-ring agents in one Section)
When the user views the Agents Map overview
Then the first 5 agents in that (Section x Type-ring) group render as
    individual compact dots, exactly as they do today
  And the remaining agents in that group's overflow (10, for the 15-agent
    example) are represented by a single cluster marker in the group's last
    fan slot, instead of additional, overlapping dots
  And the cluster marker is a circle showing a count of how many agents it
    represents and a "+"
```
<!-- AC-ID: REQ-SB-38-US-01-AC-01 -->

### Scenario 2: Clicking a cluster marker shows exactly the agents it represents

```gherkin
Given the Agents Map overview shows a cluster marker representing a specific
    set of overflow agents in one Section
When the user clicks the cluster marker
Then a drill-down view opens showing only the agents that marker represents
  And no other agent from that Section — including the ones already visible
    as individual dots on the overview — appears in that drill-down
```
<!-- AC-ID: REQ-SB-38-US-01-AC-02 -->

### Scenario 3: Returning from a cluster's drill-down restores the overview unchanged

```gherkin
Given the user has opened a cluster marker's own drill-down
When the user clicks "Back to Agents Map"
Then the overview reappears with the same individual dots and the same
    cluster marker(s) it showed before, unchanged
```
<!-- AC-ID: REQ-SB-38-US-01-AC-03 -->

### Scenario 4: A cluster marker never mixes agents of different Types

```gherkin
Given a Section has agents of more than one Type, and at least one
    (Section x Type-ring) group in it — e.g. that Section's Worker-ring
    agents — has more than 6 agents, triggering clustering for that group
    only
When the user views the Agents Map overview
Then each cluster marker represents agents of exactly one Type, scoped to
    its own (Section x Type-ring) group
  And no cluster marker's drill-down mixes agents from more than one
    Type-ring
```
<!-- AC-ID: REQ-SB-38-US-01-AC-04 -->

### Scenario 5: A Section under the clustering threshold shows every agent individually

```gherkin
Given every (Section x Type-ring) group in a Section has 6 or fewer agents
    (at or under VISIBLE_SLOT_CAP)
When the user views the Agents Map overview
Then every agent in that Section renders as its own individual node
  And no cluster marker appears anywhere in that Section
```
<!-- AC-ID: REQ-SB-38-US-01-AC-05 -->

### Scenario 6: The Section Hub's own full drill-down remains unclustered

```gherkin
Given a Section's overview shows one or more cluster markers
When the user clicks that Section's own Hub, not a cluster marker
Then the drill-down shows every agent in the Section, including the ones a
    cluster marker represents on the overview
  And none of those agents are collapsed or hidden behind a marker in this
    view
```
<!-- AC-ID: REQ-SB-38-US-01-AC-06 -->

## Affected Screens

- `html-prototype/agents-map.html` — the approved "Density clustering
  (REQ-SB-38 demo)" state demonstrates every scenario above (see Notes'
  Prototype parity breakdown). The real screen this story builds against is
  the existing Agents Map overview (`REQ-SB-12-US-01`'s own delivered
  screen) — this story extends it, it does not replace it.

## Dependencies

- **Blocked by:** [[REQ-SB-12-US-01]] — Done; this story extends the Agents
  Map overview that story delivered (`AgentsMapCanvas.tsx`, `layoutAgents.ts`,
  `SectionHub.tsx`, `AgentNode.tsx`).
- **Related to:** [[REQ-SB-37-US-01]] — Draft, flagged; Agent Creation is the
  main way a Section's agent count actually grows over time, which is what
  makes clustering necessary in practice. This story does not depend on
  Agent Creation shipping first — it clusters whatever agents already exist.
- **Related to:** `BUG-009` (Resolved) — the fan-out wedge-boundary fix that
  directly prompted this requirement; that fix prevents cross-Section
  spillover, this story addresses the same-Section, same-ring crowding it
  left unaddressed.
- **External:** none.

## Constraints

- A cluster marker must never represent agents of more than one Type — see
  Scenario 4. This holds regardless of how the flagged threshold/scope
  questions are ultimately resolved.
- Clicking a cluster marker must open a drill-down scoped to only the agents
  it represents, reusing the existing click-to-zoom mechanism
  (`BUG-002` Option D) rather than a new interaction pattern.
- Clicking a Section's own Hub must continue to show every agent in that
  Section, unclustered — this story must not narrow or otherwise change that
  existing full drill-down.
- This story does not invent a new numeric threshold or scoping rule on its
  own authority — both remain open until a human confirms them (see Notes);
  `/plan-tasks` should not proceed on this story until that confirmation
  happens.

## Implementation Tasks

| Task | Title | Depends on | Status |
|---|---|---|---|
| [[REQ-SB-38-US-01-T01]] | `layoutAgents.ts` — `VISIBLE_SLOT_CAP` + per-(Section x Type-ring) clustering grouping | — | Done |
| [[REQ-SB-38-US-01-T02]] | `agents-map.css` — port clickable `.map-overflow-marker` (count/label spans, hover/focus) | — | Done |
| [[REQ-SB-38-US-01-T03]] | Cluster-scoped drill-down component (reuses `layoutSectionDrilldown()`) | T01 | Done |
| [[REQ-SB-38-US-01-T04]] | `AgentsMapCanvas.tsx` — render cluster markers, widen click-to-zoom state, wire cluster drill-down | T01, T02, T03 | Done |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — `n/a`, test tooling still pending across this codebase; all ACs verified manually per Pipeline.md's manual-mode default (real code execution / real CDP-driven headless browser against real running dev server + backend + created-then-cleaned-up real agents, per each task's own Implementation Log)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Applying clustering to `layoutSectionDrilldown`'s own full-360-degree
  Section Hub drill-down.** The approved prototype deliberately shows that
  view still dense/unclustered at 15 agents, with its own inline callout
  naming this as a genuinely open follow-up question (PRD open question 2),
  not resolved by this pass.
- **Live/dynamic recount of a cluster's own count as agents are added or
  removed.** Tied to `REQ-SB-37` (Agent Creation), itself still `Draft` — out
  of scope until that story is further along (PRD open question 5).
- **A computed node-size-vs-available-arc-length dynamic threshold check.**
  The PRD's own text names this as the more robust, more work, long-term
  alternative to a fixed numeric cap. Not built here regardless of which
  fixed-threshold approach the human confirms — a reasonable future
  follow-up once real agent counts approach the threshold in practice.
- **Locking the exact clustering threshold number or the clustering scope
  granularity.** Both are explicitly left open by this story (see Context
  and the flag below) — a human must confirm or adjust the prototype's own
  proposed values before `/plan-tasks` can lock precise, numeric ACs.

## Notes

**Prototype parity (`html-prototype/agents-map.html`, "Density clustering
(REQ-SB-38 demo)" state):**

- Overview's 5-slot individual-dot + 1-slot cluster-marker fan for Technical
  — **Specced**, Scenario 1, grounded directly in what the prototype
  demonstrates, with the specific `6`/`(Section x Type-ring)` parameters
  explicitly flagged, not adopted, per the framing above.
- `.map-overflow-marker`'s "+N" click opening a narrower, cluster-scoped
  drill-down — **Specced**, Scenario 2.
- Cluster drill-down's "Back to Agents Map" button — **Specced**, Scenario 3.
- All-Worker-type synthetic dataset (no mixed-Type demonstration in the
  prototype's own dataset) — **Specced conceptually** via Scenario 4, though
  the prototype itself does not visually demonstrate a multi-Type Section
  reaching threshold on more than one ring simultaneously; this scenario is
  grounded in `layoutAgents.ts`'s existing ring-per-Type geometry (Context
  point 2 above), not in a prototype screenshot.
- Sections at or under threshold (Sales/Productivity/Customers/Products,
  all empty in this demo state; every other existing state — Populated,
  5 sections, Dense section — shows real agents below any plausible
  threshold) rendering individually, unchanged — **Specced**, Scenario 5,
  confirmed by every pre-existing Agents Map state.
- Technical Hub's own full, unclustered 15-agent drill-down with its inline
  open-question callout — **Specced**, Scenario 6; the callout itself
  documents that this view's own clustering is a separate, deferred
  question (see Non-Goals), not silently resolved here.
- Live count updates as agents are created — **Deferred**, tied to
  `REQ-SB-37` (Agent Creation), itself still `Draft` — see Non-Goals.
- The full-360-degree drill-down's own clustering treatment — **Deferred**,
  named explicitly as a follow-up in both the PRD and the prototype's own
  inline callout — see Non-Goals.

**Why this is flagged, not cleared:**

Per `REVIEW-QUEUE.md`'s own entry for this prototype pass, the operator's
sign-off was lukewarm ("It's okay kinda") and non-specific (declined to say
what's off when asked directly). The orchestrating session that produced
that entry explicitly instructed that the prototype's two most load-bearing
numbers — the `VISIBLE_SLOT_CAP = 6` threshold and the per-(Section x
Type-ring) clustering scope — stay flagged as open/tentative rather than
being treated as locked-in by that approval. This analyst pass honors that
instruction: the Acceptance Criteria above describe the *behavior* the
prototype demonstrates (a real, useful grounding — happy-path clustering,
click-to-view-subset, Type-purity, the Hub's own unclustered full view) using
generic "clustering threshold"/"same Type-ring overflow" language rather than
hardcoding `6` or asserting per-(Section x Type-ring) as the final, confirmed
scoping rule. A human needs to explicitly confirm or adjust both values (and
confirm whether `layoutSectionDrilldown`'s own view is in scope for a future
follow-up story) before `/plan-tasks` can tighten these scenarios into
locked, numeric ACs.

gate: flagged 2026-08-13, gate_reason: unclear-requirement — clustering
threshold value and clustering scope granularity both left open by the
lukewarm, non-specific `/design` sign-off recorded in `REVIEW-QUEUE.md`;
`REQ-SB-38` itself is finalised PRD text (no `<!-- Draft -->` marker) — the
flag is about the two unconfirmed parameters, not about the requirement's
own finalization state.

**Architect pass, 2026-08-13 (`/plan-tasks` step 1) — both flagged
parameters now confirmed and locked by direct operator decision, relayed to
this pass.** The operator confirmed the prototype's own two proposed
values as final, exactly as the prototype's own breadcrumb reasoning laid
them out — this pass does not re-derive them, it records why they're now
locked (operator decision) rather than tentative:

- **`VISIBLE_SLOT_CAP = 6`** — confirmed, verbatim from
  `html-prototype/agents-map.html`'s top-of-file breadcrumb (2026-08-13
  revision) and its "Density clustering (REQ-38 demo)" state (Technical
  Section: 5 individual dots + 1 cluster marker showing "+10" for 15
  synthetic same-ring agents).
  Grounded in `layoutAgents.ts`'s current
  `SECTION_ARC_SPAN_DEG_CAP=80`/`SECTION_ARC_SPAN_FRACTION=0.8`
  hand-sizing precedent (`BUG-009`) — same class of numeric constant as
  those two, which also never required an ADR.
- **Clustering scope: per-(Section × Type-ring)** — confirmed. Direct code
  read of `src/frontend/src/features/agents-map/layoutAgents.ts` and
  `polarLayout.ts` confirms the prototype's own reasoning is exactly how
  the real code already works today: an agent's angle comes from its index
  among its Section's agents, but its radius comes from its own Type's
  `RING_RADIUS` (`polarLayout.ts`) — so real visual crowding only ever
  happens among agents sharing both a Section AND a Type-ring. Grouping by
  `(sectionId, agentType)` before applying the cap is therefore not an
  arbitrary choice but the axis crowding actually happens on — and it
  structurally guarantees Scenario 4 (a cluster never mixes Types) by
  construction.

**No new ADR.** Locking these two numbers, and extending the existing
click-to-zoom mechanism (`BUG-002` Option D,
`AgentsMapCanvas.tsx`'s `zoomTargetSectionId`/`activeSectionId`) one level
deeper to a cluster-scoped drill-down that reuses `layoutSectionDrilldown()`
unmodified, introduces no new tool, framework, or structural boundary — it
is the same class of "additive composition of already-Accepted structure"
`BUGFIX-02-US-01`'s own architecture pass used for the original semantic-
zoom/drill-down mechanism. See `architecture.md` → "Agents Map — Density
Clustering (REQ-SB-38-US-01)" for the full reasoning (constant placement,
grouping key, overflow-slot rendering, drill-down reuse, and the widened
click-to-zoom state).

**Both flagged Acceptance Criteria placeholders are now resolved — for the
decomposer to tighten, not for this pass to rewrite.** Per Hard Rule 3, the
decomposer alone authors/tightens final AC wording. Scenarios 1, 4, and 5's
generic "clustering threshold"/"same Type-ring overflow" language may now
be replaced with the real locked values: threshold = `6`; scope =
per-(Section × Type-ring). The `## Acceptance Criteria` header comment's
own "once confirmed" condition is satisfied as of this pass.

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Agents Map — Density Clustering (REQ-SB-38-US-01)" (this pass) and
"Agents Map — semantic zoom / drill-down containment fix (BUGFIX-02-US-01,
BUG-002)" (the click-to-zoom mechanism this story extends). The coder is
bounded to:
- `src/frontend/src/features/agents-map/layoutAgents.ts` — new
  `VISIBLE_SLOT_CAP = 6` constant; new per-(Section × Type-ring) grouping
  logic ahead of the existing fan-out math, producing which agents render
  individually vs. which single slot becomes a cluster marker (and which
  agent ids that marker represents).
- `src/frontend/src/features/agents-map/polarLayout.ts` — read-only
  reference (`RING_RADIUS`); no change expected.
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — new
  cluster-marker rendering alongside existing `AgentNode`/`SectionHub`
  children; widened click-to-zoom state to also address a cluster's
  subset, reusing the existing `zoomTargetSectionId`/`activeSectionId`
  mechanism rather than a new interaction pattern.
- `src/frontend/src/features/agents-map/AgentNode.tsx`,
  `SectionHub.tsx` — reused unchanged (no new props expected beyond what
  `BUGFIX-02-US-01` already added).
- `src/frontend/src/features/agents-map/SectionDrilldown.tsx` — reference
  shape for a new sibling component (or a generalization of this one) that
  renders a cluster-scoped drill-down via `layoutSectionDrilldown()`,
  unmodified, fed the clustered subset instead of a whole Section.
- `src/frontend/src/styles/agents-map.css` (or equivalent ported
  stylesheet) — `.map-overflow-marker` port, verbatim class names, per
  `BUGFIX-02-US-01`'s own CSS-port convention.

gate: clear 2026-08-13 — no ADR triggered (confirming two previously-
tentative constants via direct operator decision, extending only
already-Accepted mechanisms — `BUG-002` Option D, `layoutAgents.ts`'s
ring-per-Type geometry — is not a new architectural decision); no
contradiction with any Accepted ADR, the PRD, or a `MEMORY.md` constraint
found. Handing off to the decomposer to lock ACs and author tasks.

**Decomposer pass, 2026-08-13 (`/plan-tasks` step 2).** All 6 Gherkin
scenarios authored/tightened and locked as `REQ-SB-38-US-01-AC-01`..`-06`
(sequential, all `locked: true`). Per Hard Rule 3 and the architect's
explicit instruction above, Scenarios 1, 4, and 5's generic "clustering
threshold"/"clustering scope" placeholder language was replaced with the
real locked values — `VISIBLE_SLOT_CAP = 6` and grouping by
`(sectionId, agentType)` — including the concrete 15-agent/5-individual/
+10-marker worked example from the architect's own confirmed prototype
parity note. Scenarios 2, 3, 6 needed no wording change (no placeholder
language) — AC-IDs only.

Four flat-root tasks created (`REQ-SB-38-US-01-T01`..`T04`), mirroring
`BUGFIX-02-US-01`'s own layout-logic / CSS / new-component / canvas-wiring
split for this same feature area:
- `T01` — `layoutAgents.ts`: new `VISIBLE_SLOT_CAP` constant + grouping by
  `(sectionId, agentType)` ahead of the existing fan-out math, producing
  which agents render individually vs. one cluster-marker descriptor per
  overflowing group (count + represented agent ids). No dependencies.
- `T02` — `agents-map.css`: port the prototype's now-clickable
  `.map-overflow-marker` shape (border/shadow/hover-focus states plus the
  new `.map-overflow-marker-count`/`-label` inner spans) verbatim, replacing
  the currently-ported static-chip version. Independent of `T01`, mirrors
  `BUGFIX-02-US-01-T02`'s precedent (non-AC smoke checks only — a CSS-only
  change has no independent DOM signature until a component actually
  renders the class).
- `T03` — new cluster-scoped drill-down component, a sibling to/
  generalization of `SectionDrilldown.tsx`, reusing `layoutSectionDrilldown()`
  unmodified against the clustered subset only. Depends on `T01` (needs the
  cluster descriptor's agent-id list).
- `T04` — `AgentsMapCanvas.tsx`: renders one cluster-marker button per `T01`
  descriptor (styled via `T02`), widens the existing
  `zoomTargetSectionId`/`activeSectionId` click-to-zoom state to also
  address a cluster's own distinct id, and mounts `T03`'s component on
  click. Also carries the regression check that Section Hub clicks still
  open the full, unclustered drill-down unchanged (Scenario 6). Depends on
  `T01`, `T02`, `T03`.

`depends_on` graph is acyclic (`T01`/`T02` -> `T03` -> `T04`, with `T02`
also feeding `T04` directly). Every locked AC has at least one AC-tagged
manual verification step across these four tasks (several are tagged twice,
once at the logic layer and once at the DOM layer, for stronger coverage —
see each task's own `## Tests`). All four tasks written at `status: Ready`
in lockstep with the story.

No MUST-FLAG trigger fired during this pass: both numbers were confirmed by
the architect from a direct operator decision (not a decomposer assumption),
no new ADR, no `ESCALATIONS.md` entry, no oversized task, every locked AC is
DOM- or logic-verifiable, no contradictory inputs, and the task breakdown
follows established precedent (`BUGFIX-02-US-01`) rather than being a
genuinely unclear/multi-valid-option call.

gate: clear 2026-08-13 — story advances `Draft -> Ready`; all 6 ACs locked,
every locked AC has a tagged verification step, `depends_on` acyclic.

**Coder pass, 2026-08-14 (`/implement-sprint SPRINT-037`).** All four tasks
built and verified live, in dependency order (`T01`/`T02` → `T03` → `T04`).
All 6 locked ACs verified for real (not simulated): `AC-01`/`AC-04`/`AC-05`
against the real `layoutAgents()` function (Node's own TS type-stripping,
no transpile step); `AC-02`/`AC-04` against the real `ClusterDrilldown`
component rendered by the real dev server + React runtime in a real
CDP-driven headless browser; `AC-01`/`AC-03`/`AC-06` against the real,
fully-wired `AgentsMapCanvas` with 8 real `worker`-type agents created via
the live `POST /agents` endpoint (bringing the real `technical/worker`
group to 8, over `VISIBLE_SLOT_CAP`) — genuinely observed 5 dots + 1 "+3"
marker, a cluster-scoped drill-down showing exactly the 3 overflow agents,
an unchanged overview on Back, and the Section Hub's own full 9-agent
unclustered drill-down. Test agents removed from the persisted registry
immediately after (`.second-brain/agents_registry.json`/
`agent_sections.json` restored to their pre-run state) — confirmed via a
fresh `GET /agents` back to the original 7 real agents.

`T04` surfaced one scope-internal judgement call, logged in its own
Implementation Log and flagged there (`gate: flagged`) for human spot-
check: `src/frontend/src/pages/AgentsMapPage.tsx` — not in any task's
declared `## Files to Modify` — needed a minimal, mechanical extension of
its own already-established state-then-pass-through pattern (one new
`clusters` state, one new derived `fullAgents` state, both passed to
`AgentsMapCanvas` as new props) because (a) `AgentsMapCanvas` cannot
compute `clusters` itself — `AgentsMapPage.tsx` is the sole caller of
`layoutAgents()` — and (b) `T01`'s own locked `mapAgents` reduction, if
also fed unmodified into `SectionDrilldown`/`ClusterDrilldown`, silently
drops the very agents a cluster represents, a live-confirmed violation of
`T04`'s own Constraint/Scenario 6 ("must not narrow ... the full
drill-down"). No new external dependency, no shared interface with any
consumer outside this one caller, no ADR deviation — this story's own
gate above is set to `flagged` (not a hard `ESCALATIONS.md` entry) to
route this specific file-scope deviation to a human for spot-check,
mirroring `SPRINT-021`'s own established "mechanical, zero-judgement
port of already-approved design" precedent
(`Implementation/Learnings.md`).

All Constraints respected: a cluster marker never mixes Types (structural,
`(sectionId, agentType)` grouping in `T01`); cluster clicks reuse the
existing `BUG-002` Option D zoom-then-mount mechanism, widened not
duplicated (`T04`); the Section Hub's own full drill-down is unaffected
(`AC-06`, verified live). Story `Done`.
