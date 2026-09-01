---
id: SPRINT-083
title: Migrate email-thread-capture and summarize-and-tag-threads write mechanics onto vault_manager.py
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-082]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-09-01
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

# SPRINT-083 — Migrate email-thread-capture and summarize-and-tag-threads Write Mechanics onto vault_manager.py

## Sprint Goal

Migrate both Capture-side (`email-thread-capture`) and Enrich-side
(`summarize-and-tag-threads`) write mechanics onto the resynced
`vault_manager.py` engine — two independent, parallel migrations of two
different live production Skills, built on the same `SPRINT-082` foundation.

---

## Grouping Rationale & Sizing

- **Why grouped together:** `REQ-SB-87-US-02` and `REQ-SB-87-US-04` are a
  real, confirmed **diamond**, not a chain — both `US-02-T01` and
  `US-04-T01` `depends_on: [REQ-SB-87-US-01-T05]` directly (the same single
  upstream task, `SPRINT-082`'s own output), but neither depends on the
  other at all: read directly from each task file's own frontmatter, `US-02`
  is a straight 5-task chain (`T01→T02→T03→T04→T05`) migrating
  `email-thread-capture`'s five scripts, and `US-04` is a straight 4-task
  chain (`T01→T02→T03→T04`) migrating `apply_thread_review.py` — two
  different Skills, two different script files, zero shared files, zero
  cross edges between them. Per hard rule 7 ("dependency-linked stories go
  in the same sprint or in ordered sprints"), two stories that fan out from
  the SAME single prerequisite with no dependency on each other are the
  textbook case for building together in parallel within one sprint, once
  that shared prerequisite (`SPRINT-082`) is `Done` — mirroring this
  project's own already-established "a diamond stays one sprint" precedent
  (`SPRINT-049`'s `REQ-SB-55-US-01`), generalized here one level up from a
  single story's own task graph to two sibling stories sharing one
  upstream task.
  - Both stories also share the identical rollout-risk posture (the
    operator's own locked 100-email scratch-vault proving-phase rollout,
    both stories' own Constraints), the identical production-risk profile
    (each migrates a live, cron-backed pipeline — `email-delta-capture` and
    `job4-summarize-tag-threads` respectively), and the identical
    "mechanics migration, not a bugfix" framing — real cohesion beyond just
    the shared dependency edge.
- **Sizing:** 5 + 4 = 9 tasks, sized `L`. This sits exactly at this
  project's own largest confirmed-accurate sizing ceiling (`SPRINT-021`
  `REQ-SB-21-US-01`, `SPRINT-030` `REQ-SB-39-US-01`, both 9 tasks/L matched
  exactly at retro) — not exceeding it. Combining a third story here (e.g.
  folding in `US-03` or `US-05`) would push past that ceiling into
  genuinely oversized territory with no real precedent of an exact match;
  keeping this sprint at exactly `US-02` + `US-04` is the correct sizing
  call, not an arbitrary round number.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-083 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-87-US-02](../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md) | Migrate email-thread-capture's write mechanics onto vault_manager.py | P1 | Ready (gate: clear) |
| [REQ-SB-87-US-04](../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md) | Migrate summarize-and-tag-threads' write mechanics onto vault_manager.py | P1 | Ready (gate: clear) |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-082` (must be `Done` before
  `/implement-sprint` may start this sprint — `US-02-T01` and `US-04-T01`
  each `depends_on: [REQ-SB-87-US-01-T05]`, the Thread/RawMessage
  templates `SPRINT-082` authors).
- Internal task order (per the decomposer's own `depends_on`; the two
  stories' own chains are independent of each other and may build in
  either order or in parallel):
  - `US-02`: `T01` → `T02` → `T03` → `T04` → `T05` (the real-vault
    retrofit check + live cron cutover).
  - `US-04`: `T01` → `T02` → `T03` → `T04` (the real-vault retrofit check
    + live cron cutover).

---

## Out of Scope

- `REQ-SB-87-US-01` — built in `SPRINT-082`, this sprint's own
  prerequisite.
- `REQ-SB-87-US-03`/`US-05` — each reaches back into a specific task
  inside this sprint (`US-03-T03` → `US-02-T01`; `US-05-T01` →
  `US-04-T03`) and is sequenced after this sprint via `SPRINT-084`'s own
  `depends_on_sprints: [SPRINT-083]` edge, not folded in here (would push
  this sprint past its own 9-task sizing ceiling).
- Any change to either Skill's own real business-logic/judgment (Person-
  note dedup, company resolution, the section-ownership guard's real
  per-caller rules) — both stories' own Constraints keep this a mechanics
  migration only.

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

## Notes (product-owner, `/plan-sprints`, 2026-09-01)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made pairing `US-02` and `US-04` (the real `depends_on` edges, both
  the shared upstream edge into `SPRINT-082` and the absence of any edge
  between the two stories themselves, were read directly from the
  decomposer's own task frontmatter, never re-derived or guessed);
  `REQ-SB-87` is not `Draft`/unfinalised in the PRD; no ADR was created or
  changed by this pass; no `ESCALATIONS.md` entry was written by this
  pass; the sprint is not oversized (9 tasks sits exactly at, not past,
  this project's own confirmed ceiling); the `depends_on_sprints:
  [SPRINT-082]` edge this pass introduces is a **disclosed, honoured**
  edge matching two independent real task-level `depends_on` edges
  reaching back into that sprint, not a contradiction of the graph; the
  partition is unambiguous — given the real dependency fault line (both
  stories fan out from the same single upstream task, neither depends on
  the other, and no other pairing keeps every sprint within this
  project's own confirmed 6-9 task sizing band while also honouring every
  real edge), there is no equally-valid alternative grouping.
- Both stories in scope already carry `gate: clear` at the story level
  (both production-risk MUST-FLAG triggers were resolved directly by the
  analyst/architect before this pass — see each story's own Notes) — no
  flag to carry forward here, unlike `SPRINT-082`/`SPRINT-084`.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** _(filled in by coder at close)_

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
