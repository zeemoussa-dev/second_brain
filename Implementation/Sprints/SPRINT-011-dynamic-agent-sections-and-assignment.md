---
id: SPRINT-011
title: Dynamic agent Sections — CRUD, per-agent assignment, N-generic Agents Map layout
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted, pending human skim/harvest into Learnings.md; ADR-014's own human review (REVIEW-QUEUE.md) also still open, independent of this sprint's own completion"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"                      # YYYY-MM-DD when status → Done
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

# SPRINT-011 — Dynamic agent Sections — CRUD, per-agent assignment, N-generic Agents Map layout

## Sprint Goal

Let the user create/rename/delete their own business-domain Sections from
Settings and reassign any agent to a different Section (independent of its
Worker/Producer/Expert Type), with the Agents Map rendering the current,
arbitrary-N section set live — landing `ADR-014`'s shared persistence
mechanism and the `PATCH /agents/{agent_id}` surface that `SPRINT-012`
(`REQ-SB-19-US-01`) builds its Provider-picker diff on top of afterward.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-18-US-01` is the only story
  in this batch whose tasks it covers; its 8 tasks form one acyclic
  dependency graph (`T01 → T02 → {T03, T04} → T05 → T06 → {T07, T08}`, `T07`
  also depending on `T03`/`T05`, `T08` on `T04`/`T06`/`T07`) delivering one
  coherent, independently valuable capability — Section CRUD + per-agent
  reassignment + the N-generic map layout — per the story's own "no
  independent value alone" reasoning (Section CRUD with no way to assign
  agents has no value; per-agent reassignment among a fixed set has little
  value either). Not splittable across sprints without cutting through the
  middle of a single dependency graph, which would contradict hard rule 7.
- **Why NOT combined with `REQ-SB-19-US-01` into one sprint:** the two
  stories are graph-legal to combine (rule 7 allows same-sprint *or* ordered
  sprints for dependency-linked stories), but the decomposer's own
  cross-story `depends_on` edges make the ordering, not the grouping, the
  load-bearing fact here: `REQ-SB-19-US-01-T04` depends on this story's
  `T04`, `T05` depends on this story's `T07`, `T06` depends on this story's
  `T08` — i.e. half of `REQ-SB-19-US-01`'s tasks are explicitly gated on
  this story's *later, near-terminal* tasks, not just its first one. That
  means `REQ-SB-19-US-01` cannot meaningfully start its shared-surface work
  until this story is almost entirely built, which is a natural sprint
  boundary, not an artificial one. Combining would also push the pair to 14
  tasks total (8 + 6) — clearly past this session's established ceiling
  (`SPRINT-010`'s 8 tasks is the largest single-story sprint to date;
  `SPRINT-007`'s 6 tasks is the largest multi-story sprint to date; a 15-task
  combination was explicitly rejected on sizing grounds when `SPRINT-009`/
  `SPRINT-010` were split). Two sequenced sprints — this one, then
  `SPRINT-012` with `depends_on_sprints: [SPRINT-011]` — keeps each sprint
  inside a single working context and makes the build order for the coder
  completely unambiguous: `SPRINT-012` cannot start until every task here is
  `Done` (hard rule 9 enforces this mechanically), which mirrors the
  decomposer's own framing exactly ("`REQ-SB-18` lands the shared surface
  first, `REQ-SB-19` builds its diff on top"). This is a reasoned sizing +
  dependency-shape call, not a genuinely ambiguous partition — not flagged.
- **Sizing estimate:** ~8 tasks, L (large) — directly matches the already-
  Done `REQ-SB-13-US-01`/`SPRINT-010` precedent (8 tasks, L: 4 backend +
  4 frontend, a new persisted-state mechanism plus a new ADR), the largest
  well-calibrated single-story precedent to date. This story's own shape is
  comparable: 4 backend tasks (vault-writer primitives, registry, router,
  agents-router extension) + 4 frontend tasks (layout generalization, canvas
  dividers, Settings card, detail-panel picker).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-011 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-18-US-01](../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md) | User-editable agent Sections, decoupled from agent Type, with per-agent section reassignment | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` confirm no hard blocker: `REQ-SB-12-US-01`
  and `REQ-SB-13-US-01` (both `Done`) provide the Settings page shell and
  Agent Settings detail panel this story extends.
- `ADR-014` (new — Sections/Providers persistence mechanism, shared with
  `REQ-SB-19-US-01`) was written by the architect 2026-08-11 and is still
  under human review — see `REVIEW-QUEUE.md`'s `REQ-SB-18-US-01 /
  REQ-SB-19-US-01` entry. Per `Implementation/Pipeline.md`'s "an ADR-creation
  flag does not halt downstream stages" rule, the decomposer already locked
  ACs and wrote tasks against it, and this sprint is assembled on the same
  basis. If the human's review of `ADR-014` changes it, the affected
  task/story `status:` should be reset and `/plan-tasks` re-run before this
  sprint starts building.
- `REQ-SB-19-US-01`'s `T04`/`T05`/`T06` each carry a cross-story `depends_on`
  edge naming a task in this sprint (`T04`, `T07`, `T08` respectively) —
  `SPRINT-012` cannot start until this sprint is fully `Done`.

---

## Out of Scope

- **Redesigning the Worker/Producer/Expert Type taxonomy or the ring layout
  it drives** — per the story's own Non-Goals; unchanged from
  `REQ-SB-12-US-01`.
- **Multi-section membership per agent** — every agent belongs to exactly
  one section, per the story's own Non-Goals.
- **Automatic reassignment or cascading deletion when a section is deleted**
  — deletion of an in-use section is blocked, not auto-resolved.
- **The Provider concept, Provider CRUD, or the Provider picker** —
  `REQ-SB-19-US-01`/`SPRINT-012`'s scope; this sprint lands only the
  Section-side portion of the shared `PATCH /agents/{agent_id}` surface and
  shared frontend files.
- **A full visual redesign of the Agents Map's polar-grid aesthetic** — the
  layout *mechanism* becomes N-section-generic; the existing visual language
  (rings, hubs, spokes, radar background) is extended, not replaced.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already landed at the architect pass (2026-08-11); unchanged by this build pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-014` already `Accepted` at the architect pass
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

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L, built in one
  uninterrupted pass (4 backend + 4 frontend, exactly as scoped; no task
  dropped, split, or added). **Takeaway:** the `REQ-SB-13-US-01`/
  `SPRINT-010` precedent this sizing was calibrated against continues to
  hold for an 8-task single-story sprint that pairs a new persisted
  `.second-brain/` state file with a matching frontend surface — this
  shape (new state file → business registry → router → shared-endpoint
  extension → frontend layout/rendering → two composed UI surfaces) is now
  twice-confirmed as an accurately-estimable unit at this size.

### What worked

- **Decomposer-provided literal code blocks let the coder focus verification
  time on real behaviour, not code authorship** — every one of the 8 tasks
  gave a complete, ready-to-paste implementation; the coder's own judgement
  was needed only twice (see Antipatterns/assumptions below), both small
  and same-file. Freed the entire build pass for live verification depth
  instead of design decisions already made upstream.
- **Consolidating a real-side-effect check across two ACs in one live
  interaction** — `AC-06`/`AC-07`/`AC-09` were all confirmed from a single
  reassignment sequence (Section change → reopen panel → reload map),
  rather than three separate repro sequences, mirroring the
  `SPRINT-010`-established "consolidate repeated real-side-effect
  verification" pattern (`MEMORY.md`).
- **Topology-count verification for map rendering** — rather than
  asserting pixel positions, counting `.cluster-line`/`.section-boundary`/
  `.hub-node` elements against the exact combinatorial math a section
  reassignment predicts (`C(n,2)+n` per section) gave a precise,
  deterministic live check for `AC-08`/`AC-09` without needing exact
  coordinate assertions.

### What didn't work

- **React suppresses a native `.click()` dispatched at a DOM node it still
  believes is `disabled` via its own Fiber props, even after the raw DOM
  `disabled` attribute is removed** — the natural "force-enable via
  DevTools" technique this project's own `T07` task text suggested for
  exercising a disabled button's blocked-click path silently no-ops
  (confirmed via a control test: an identical click on a genuinely-enabled
  button worked immediately). Root cause: React's SimpleEventPlugin checks
  the component's own `disabled` *prop* state, not the DOM attribute, for
  click/mouseover-family events on form controls. Worked around by
  invoking the button's `onClick` handler directly via the DOM node's
  React Fiber props (`Object.keys(el).find(k =>
  k.startsWith('__reactProps$'))`) — the same handler a real click would
  call, exercising identical code, just bypassing React's own disabled-
  click short-circuit rather than fighting it.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **React Fiber-props direct-invoke for verifying a `disabled`-gated
  click handler** — when a locked AC needs to exercise the handler behind
  a `disabled` button (e.g. confirming a blocked-delete error path
  renders correctly), removing the DOM `disabled` attribute alone does not
  let a dispatched click reach React's handler (React checks its own Fiber
  props, not the DOM attribute). Instead, read the handler directly off
  the element's React Fiber props (`el[Object.keys(el).find(k =>
  k.startsWith('__reactProps$'))].onClick`) and invoke it — the identical
  code path a real click would take once unblocked, without needing to
  fake full component re-render state. Verify the technique first against
  a known-*enabled* control element in the same session, to rule out a
  harness bug before concluding it's React's own disabled-click
  suppression.
- **Topology-count assertions for computed polar-layout rendering** — when
  a layout is computed (not hand-placed), asserting element *counts*
  against the exact formula the computation predicts (e.g.
  `cluster-line` count `= Σ over sections of (C(agents_in_section, 2) +
  agents_in_section)`) is a precise, deterministic live-verification
  technique for confirming a reassignment or an N-generic layout change
  actually took effect, without needing brittle pixel-coordinate
  assertions.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A decomposer's literal per-file diff can miss a same-pattern reference
  elsewhere in a file it doesn't otherwise touch** — `T06`'s own `Files to
  Modify` named two `section.type`-referencing spots in
  `AgentsMapCanvas.tsx` to neutralize, but a third occurrence
  (`section-title-accent`'s background color) used the identical
  now-dropped field and would have been a TypeScript compile error left
  unaddressed, since no task's own diff named it. Caught by running `npx
  tsc --noEmit` immediately after the type-dropping task (`T05`) rather
  than waiting until the final whole-story build check — worth continuing
  to run the type-check incrementally per task, not just once at the end,
  specifically whenever a task narrows/drops a shared type other
  untouched files might still reference.
- **A task's own inline "ported verbatim" CSS snippet can drift from the
  actual prototype file it claims to port from** — `T07`'s inline
  `.item-row`/`.btn-danger` code block used different layout/color-mix
  values than `html-prototype/styles.css`'s real, current rules for the
  same selectors. The task's own constraint text ("match it exactly rather
  than approximating") already anticipated this and named the real file as
  the tiebreaker — worth remembering that "ported verbatim" code blocks in
  task files are a convenience copy, not necessarily current; re-read the
  actual design-authority file before trusting an inline snippet at face
  value when a literal verbatim-match constraint is also stated.

### Open follow-ups

- **`ADR-014`'s own human review** (`REVIEW-QUEUE.md` pointer, since the
  architect pass 2026-08-11) remains open — independent of this sprint
  reaching `Done` (all 9 ACs pass against the ADR as currently written).
  If the human's review changes `ADR-014`, the affected task(s)' `status:`
  should be reset and rebuilt.
- **`SPRINT-012` (`REQ-SB-19-US-01`)** is now unblocked —
  `depends_on_sprints: [SPRINT-011]` is satisfied. Its `T04`/`T05`/`T06`
  land the Provider-portion diff strictly on top of this sprint's own
  already-`Done` `T04`/`T07`/`T08` (shared `PATCH /agents/{agent_id}`,
  `AgentDetailPanel.tsx`, `agentsApiClient.ts`, `settingsApiClient.ts`,
  `SettingsPage.tsx`) — re-read each of those 4 files fresh before editing
  (not from this sprint's own stale in-context knowledge), per this
  session's own established "re-read shared files fresh" antipattern
  guard (`SPRINT-010`'s retro).

---

## Notes

gate: clear 2026-08-11 — no MUST-FLAG trigger fired for this grouping
decision. This story's own dependency graph
(`T01→T02→{T03,T04}→T05→T06→{T07,T08}`) is honoured intact, not split
across sprints. Not oversized on its own (8 tasks matches the already-Done
`REQ-SB-13-US-01`/`SPRINT-010` precedent exactly). Not blocked — all 8 tasks
and the story itself are `status: Ready`; the one open item
(`ADR-014` human review) is a pre-existing flag on the story/architecture
pass, not something this stage introduced, and per Pipeline.md does not
halt `/plan-sprints`. Single phase (P1). No cross-sprint dependency was
introduced for *this* sprint (`depends_on_sprints: []`) — the real
cross-story dependency runs the other direction, recorded on `SPRINT-012`
instead, exactly mirroring the decomposer's own `depends_on` edges (not an
artificial edge this role invented). The choice to give this story its own
sprint rather than merge with `REQ-SB-19-US-01` is a reasoned sizing +
dependency-shape call (14 combined tasks past this session's established
ceiling, plus half of `REQ-SB-19-US-01`'s tasks gated on this story's own
near-terminal tasks), not a genuinely ambiguous partition — recorded above,
not flagged. Advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 8 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`. `SPRINT-012`
(`REQ-SB-19-US-01`) is sequenced to build immediately after this sprint
reaches `Done`.

**Sprint built (2026-08-11, `/implement-sprint` — coder):** All 8 tasks
built and verified live in dependency order
(`T01→T02→{T03,T04}→T05→T06→{T07,T08}`), all 9 locked ACs
(`REQ-SB-18-US-01-AC-01`…`AC-09`) confirmed passing against the real
backend and browser — see the story's own Notes and each task's
Implementation Log for full detail. `npx tsc --noEmit` and `npm run build`
both clean. Zero `ESCALATIONS.md` entries this pass; two scope-internal
judgement calls logged (`T06`, `T07` — see the Retrospective above). Story
advances `Ready → Done`; sprint advances `Ready → Done`,
`completed: 2026-08-11`. `gate: flagged` — the retro above is drafted, not
yet human-skimmed/harvested into `Learnings.md`; `ADR-014`'s own human
review (`REVIEW-QUEUE.md`) is a separate, still-open item unaffected by
this sprint reaching `Done`. `SPRINT-012` (`REQ-SB-19-US-01`) is now
eligible to start — `depends_on_sprints: [SPRINT-011]` satisfied.
