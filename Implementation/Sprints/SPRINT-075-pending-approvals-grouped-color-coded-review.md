---
id: SPRINT-075
title: Pending Approvals — Grouped, Color-Coded Review
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: ""                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-075 — Pending Approvals — Grouped, Color-Coded Review

## Sprint Goal

Group the Pending Approvals list by `action_id` with a distinct color
treatment per group, plus a bulk-approve control for groups whose items
share a simple, uniform approve/decline action.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 4 tasks belong to
  `REQ-SB-78-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "Pending Approvals — Grouped, Color-Coded Review").
  Graph read directly from each of the 4 task files' own `depends_on:`
  frontmatter:
  - `T01` (`pendingApprovalGroups.ts` + CSS) — `depends_on: []`, root.
  - `T02` (grouped rendering) — `depends_on: [T01]`.
  - `T03` (bulk-approve control) — `depends_on: [T01, T02]`.
  - `T04` (real-browser live verification, all 7 ACs) — `depends_on: [T02,
    T03]`.
  - **Acyclic** — a strict linear chain (`T01` → `T02` → `T03` → `T04`); no
    back-reference found. All 4 tasks carry `phase: P2` (matching the parent
    story) — no phase mixing.
- **Why NOT combined with `SPRINT-073`/`SPRINT-074` (this same batch's other
  two stories):** confirmed by direct reading of this story's own
  `## Dependencies` and all 4 task files' own `depends_on` frontmatter —
  zero edges, in either direction, connect `REQ-SB-78-US-01` to
  `REQ-SB-77-US-01` or `REQ-SB-79-US-01`. The two areas share no file, no
  module, and no architecture section (`MyDayApprovalsPage.tsx`/
  `pendingApprovalGroups.ts`, frontend-only, vs.
  `librarian_housekeeping.py`/`agent_registry.py`, backend-only). The
  story's own `## Dependencies` names `REQ-SB-76-US-01` (shares the same
  screen, `SPRINT-072`, `In Progress`) as a soft, non-blocking sequencing
  note only — "Not required to be `Done` first — this story's own grouping
  wrapper is generically keyed off `agent_id`/`action_id`, not specific to
  any one proposal type." Keeping this story in its own sprint, rather than
  folding it into `SPRINT-074` (which itself must wait on `SPRINT-073`),
  means this fully independent, unblocked frontend work is never
  artificially gated behind an unrelated backend dependency chain it does
  not need — a real decoupling benefit, not merely "the third story needs
  somewhere to go."
- **Sizing estimate: ~4 tasks, S.** Matches this project's own repeatedly-
  confirmed 4-task/S shape (`SPRINT-019`, `SPRINT-025` — both exact matches
  at retro per `Implementation/Learnings.md`), consistent with the story's
  own Notes comparing its scope to `REQ-SB-52-US-01`'s own single-screen
  restyle. `T04` (real-browser CDP verification of all 7 locked ACs) is
  expected to be the heaviest by live-verification effort, not code volume —
  mirrors this project's own established screen-level-AC-verification
  precedent (`Implementation/Learnings.md`, `SPRINT-026`/`036`/`038`).

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-78-US-01's own
frontmatter now carries sprint: "SPRINT-075". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-78-US-01](../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md) | Pending Approvals — Grouped, Color-Coded Review | P2 | Ready |

**Tasks in scope** (dependency order): `T01` (root) → `T02` (needs `T01`) →
`T03` (needs `T01`, `T02`) → `T04` (needs `T02`, `T03`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This story has zero task-level `depends_on`
  edge onto any other story, in either this batch or any prior sprint —
  confirmed directly by reading all 4 task files.
- **Related, non-blocking:** `REQ-SB-76-US-01` (Company Review,
  `SPRINT-072`, `In Progress`) — shares this exact screen; this story's own
  grouping/color scheme accounts for the Company Review proposal type as one
  of its groups (Scenario 5), but is not required to be `Done` first (see
  story's own `## Dependencies`).
- **External:** none new.

---

## Out of Scope

- The Librarian's own two-sub-pipeline split — `REQ-SB-79`, `SPRINT-073`
  (unrelated screen/module).
- People notes linking to their real Company/Partner note — `REQ-SB-77`,
  `SPRINT-074` (unrelated screen/module).
- Any change to any individual proposal type's own approve/decline mechanism
  or decision-control shape (including the Company Review 5-way control) —
  the story's own disclosed Non-Goal.
- Reconciling `SPRINT-072`'s own in-flight UI changes beyond reading its
  current live shape for grounding — the story's own disclosed Non-Goal.

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact (no change expected — already updated at `/plan-tasks` under "Pending Approvals — Grouped, Color-Coded Review")
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` (none expected — no new ADR created for this story)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
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

- **Estimated:** ~4 tasks, S — **Actual:** _(tasks / effort)_ — **Takeaway:** _(over/under, why)_

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

---

## Notes

**Sprint assembled 2026-08-19 (`/plan-sprints`).** `REQ-SB-78-US-01` enters
`/plan-sprints` `status: Ready`, `gate: clear` (the operator's own prior
resolution of the architect's earlier `/design`-pass question, recorded in
the story's own frontmatter `gate_reason`).

**Gate: `gate: clear` 2026-08-19.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone, single-story
grouping is read directly off all 4 task files' own `depends_on` frontmatter
(fully internal to this story, confirmed zero cross-story edges either
direction); (2) `REQ-SB-78` is not `<!-- Draft -->`/unfinalised; (3)
product-owner does not write ADRs — none created or changed by this pass;
(4) no new `ESCALATIONS.md` entry; (5) not oversized (4 tasks, S, matching
two prior confirmed-accurate 4-task/S precedents, `SPRINT-019`/`SPRINT-025`);
not a blocked story — every task is `status: Ready`, no unmet prerequisite;
no cross-sprint dependency introduced (none exists); (6) N/A (coder-only
trigger); (7) no contradictory inputs; (8) not genuinely ambiguous — the
absence of any real dependency edge onto `REQ-SB-77-US-01`/`REQ-SB-79-US-01`
(this same batch's other two stories) makes "its own independent sprint" the
unambiguous, reasoned call over folding it into either — not an
equally-valid toss-up (full reasoning in `## Grouping Rationale & Sizing`
above). Advances `Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-78` row's Sprint column set to
`SPRINT-075`.
