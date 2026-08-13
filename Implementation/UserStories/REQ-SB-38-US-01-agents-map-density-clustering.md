---
id: REQ-SB-38-US-01
title: Agents Map Density Clustering — collapse a crowded Section+Type-ring's overflow agents into a clickable cluster marker
requirement_ids: [REQ-SB-38]
requirement_section: "REQ-SB-38: Agents Map Density Clustering"
phase: P1
status: Draft
gate: flagged
gate_reason: "unclear-requirement — the clustering threshold (prototype's own proposed VISIBLE_SLOT_CAP=6) and the clustering scope granularity (per-(Section x Type-ring), the prototype's own proposal, vs. an alternative) are both left genuinely open per REVIEW-QUEUE.md's own framing of the lukewarm ('It's okay kinda') prototype approval; net-new-decision-needed before the decomposer can lock precise ACs."
sprint: ""
created: 2026-08-13
updated: 2026-08-13
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
Given a Section has more agents sharing the same Type-ring than the app's
    configured clustering threshold allows to render as individual nodes
    (the approved prototype illustrates this with 15 same-ring agents
    against its own proposed cap of 6, pending confirmation of both numbers)
When the user views the Agents Map overview
Then the agents up to the clustering threshold render as individual compact
    dots, exactly as they do today
  And the remaining agents in that Section's same-ring overflow are
    represented by a single cluster marker instead of additional, overlapping
    dots
  And the cluster marker is a circle showing a count of how many agents it
    represents and a "+"
```

### Scenario 2: Clicking a cluster marker shows exactly the agents it represents

```gherkin
Given the Agents Map overview shows a cluster marker representing a specific
    set of overflow agents in one Section
When the user clicks the cluster marker
Then a drill-down view opens showing only the agents that marker represents
  And no other agent from that Section — including the ones already visible
    as individual dots on the overview — appears in that drill-down
```

### Scenario 3: Returning from a cluster's drill-down restores the overview unchanged

```gherkin
Given the user has opened a cluster marker's own drill-down
When the user clicks "Back to Agents Map"
Then the overview reappears with the same individual dots and the same
    cluster marker(s) it showed before, unchanged
```

### Scenario 4: A cluster marker never mixes agents of different Types

```gherkin
Given a Section has agents of more than one Type, and at least one of those
    Types has enough agents on its own ring to trigger clustering
When the user views the Agents Map overview
Then each cluster marker represents agents of exactly one Type
  And no cluster marker's drill-down mixes agents from more than one ring
```

### Scenario 5: A Section under the clustering threshold shows every agent individually

```gherkin
Given a Section's agents on every Type-ring each stay at or under the app's
    configured clustering threshold
When the user views the Agents Map overview
Then every agent in that Section renders as its own individual node
  And no cluster marker appears anywhere in that Section
```

### Scenario 6: The Section Hub's own full drill-down remains unclustered

```gherkin
Given a Section's overview shows one or more cluster markers
When the user clicks that Section's own Hub, not a cluster marker
Then the drill-down shows every agent in the Section, including the ones a
    cluster marker represents on the overview
  And none of those agents are collapsed or hidden behind a marker in this
    view
```

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

<!-- Left for the architect/decomposer at /plan-tasks, once the clustering
threshold and clustering-scope-granularity flags below are resolved by a
human. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

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
