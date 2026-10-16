---
id: SPRINT-090
title: Entity resolution instead of search — one tag-keyed index, synthesis first then evidence
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087, SPRINT-088]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: ""                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
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

# SPRINT-090 — Entity Resolution Instead of Search — One Tag-Keyed Index

## Sprint Goal

Make a named entity in a question resolve to a real kind, tag and hub note, and
have the answer read from that entity's own scoped synthesis and then its
evidence — one tag-keyed index serving every entity, reachable by an agent as a
catalogued Action rather than only as a route.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-05` is the retrieval half of
  the requirement and is almost entirely self-contained — `T01` and `T02` are
  independent roots, `T03` joins them, `T04` follows. Its **only** reach into
  the Action spine is its last task: `US-05-T05`
  `depends_on: [US-05-T04, US-02-T02, US-03-T02, US-03-T03]` — the scenario where
  the scoped read becomes reachable *through the catalogue*. That single edge is
  what puts this sprint behind `SPRINT-087` and `SPRINT-088`; the story's own
  text says the same ("its only dependency on the spine is Scenario 6").
- **Why not merged with `SPRINT-088` or `SPRINT-089`.** With `US-03`: 5 + 5 = 10
  tasks, past the confirmed 8–9-task `L` ceiling. With `US-04`: 5 + 7 = 12 —
  further past it, even though the two share identical upstream sprints and have
  **zero edges between them**. Being mutually independent, `SPRINT-089` and
  `SPRINT-090` may be built in either order once their two upstream sprints are
  `Done`; the numbering carries no ordering claim between them.
- **Sizing:** 5 tasks, sized `M`, matching this project's 5-task precedents
  (`SPRINT-081` at `M`; `SPRINT-032`/`034`/`038` at `S`). Sized `M` rather than
  `S` because `T01` rebinds a projection inside `VaultManager.rebuild_index()`
  against a real, large vault, and `T05` is a four-way integration task whose
  verification needs the real catalogue and the real call gate from two earlier
  sprints.
- **This ordering closes an open plan gap, by design.** `ADR-037` takes the
  `FRAMEWORK_API` 7 → 8 bump **once**, in whichever plugin-contract story lands
  last. `US-05-T02` reads the real `app/plugin_api.py` first and bumps only if
  `register_action` is already present; the sibling `US-02-T05` carries **no**
  equivalent instruction, so if `US-02` landed last nobody would move the
  constant and no plugin could ever use either capability. The
  `depends_on_sprints: [SPRINT-087, …]` edge makes `US-02` land first with
  certainty (hard rule 9), so `US-05-T02`'s conditional read takes the bump.
  This is the second of the two resolution options the `REVIEW-QUEUE.md` item
  itself offered ("tell the product-owner to sequence `US-05` after `US-02`"),
  and it required **no edit to any task file**.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-090 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-05](../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md) | Entity resolution instead of search — one tag-keyed index, synthesis first then evidence | P2 | Ready |

Build order inside the sprint, read from the task files' own `depends_on`:
`(T01, T02) → T03 → T04 → T05` (`T05` also needs `US-02-T02`, `US-03-T02`,
`US-03-T03`, all delivered by `SPRINT-087`/`SPRINT-088`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-087` (`US-02-T02`'s save-time resolution) and
  `SPRINT-088` (`US-03-T02`'s call gate and `US-03-T03`'s dispatch) — all three
  required by `T05` alone. `/implement-sprint` refuses this sprint until **both**
  are `Done` (hard rule 9).
- **`T01`–`T04` carry no cross-story dependency at all.** If the upstream
  sprints slip and the human wants value sooner, the honest option is to re-cut
  this story — not to start the sprint early; `T05` is the only task that needs
  them. Raise it as a re-plan rather than building out of order.
- **No dependency either way with `SPRINT-089`.**
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-05` is flagged under trigger 3 (`ADR-037` — the
  tag-keyed index as a projection rebound inside `VaultManager.rebuild_index()`
  rather than a new Index artifact with its own cron job, a plugin registering a
  namespace as a callable, and the single `FRAMEWORK_API` bump) and under
  trigger 7 (the bump gap above — **structurally closed by this sprint's
  ordering**, see Grouping Rationale). `ESC-063` (who owns Customer/Partner
  entity knowledge across the `ADR-022` boundary) is **Resolved**: the resolver
  is framework, Customer stays the plugin (`ADR-035`). See `REVIEW-QUEUE.md`.
- **`ADR-032`'s own recorded consequence applies:** the answer depends on the
  Entities registry being current, and discovery was once paused for 41 days
  before anyone noticed. The freshness surface proposed under `BUG-085` is
  related, separate work and is not in this sprint.

---

## Out of Scope

- The Action catalogue (`SPRINT-087`), enforcement at the call (`SPRINT-088`),
  Workflows (`SPRINT-089`), the Operator Profile (`SPRINT-086`).
- Replacing the existing per-entity Index artifacts — `ADR-032` keeps them
  available for accounts that deserve a custom scope.
- The pipeline-freshness surface (`BUG-085`).

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (the
single inbound edge is quoted from `US-05-T05`'s own frontmatter); requirement
finalised; no ADR created or changed by this pass; no `ESCALATIONS.md` entry;
**not oversized** (5 tasks); **no `Blocked` story**. On trigger 5's cross-sprint
clause: the two `depends_on_sprints` edges are the decomposer's own `T05` edges
expressed at sprint level, not dependencies this pass introduced — recording
them is what hard rule 7 prescribes, and the repo precedent for a recorded edge
at `gate: clear` is `SPRINT-080`/`083`/`084`. No contradictory inputs. On
trigger 8: this sprint's own story is unambiguous, and the free
`SPRINT-089`/`SPRINT-090` build order is a non-decision (no edge either way,
both legal, stated in both files). The story's upstream `ADR-037` flag is carried
forward; its trigger-7 half is structurally closed by this sprint's ordering and
the `REVIEW-QUEUE.md` item is marked resolved on that basis.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** _(from `sizing_estimate:`)_ — **Actual:** _(tasks / effort)_ — **Takeaway:** _(over/under, why)_

### What worked

- _(specific behaviour, decision, or technique that paid off)_

### What didn't work

- _(specific friction, dead end, or mistake — name the root cause if known)_

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(pattern — short title — when to apply)_

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(antipattern — short title — why to avoid)_

### Open follow-ups

- _(follow-up — filed as what and where?)_
