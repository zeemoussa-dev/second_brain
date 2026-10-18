---
id: SPRINT-091
title: A Hermes profile as it really is — the read-only debug view
status: In Progress                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-17
started: 2026-10-18                        # YYYY-MM-DD when status → In Progress
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

# SPRINT-091 — A Hermes Profile As It Really Is — the Read-Only Debug View

## Sprint Goal

Give the operator one read-only page that answers, for a single Hermes profile,
the five questions this week's incidents were answered by hand: what its soul
actually says, which skills it carries at which versions and whether each
matches the framework, what its config really is, which cron jobs are bound to
it, and which toolsets are enabled — reporting each failed read honestly rather
than papering over it.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-99-US-01` is the **only** story that
  is both `status: Ready` and `sprint: ""` at this pass. Of the 17 ungrouped
  story files, the other 16 are all `Draft`; of the 8 `Ready` stories, the other
  7 already carry a sprint (`SPRINT-086`–`SPRINT-090`, plus older sprints). The
  partition is therefore **forced, not chosen** — there is exactly one story to
  place, and it fills a sprint on its own at 6 tasks.
- **Why not appended to an existing sprint.** No sprint is in `Draft` — the only
  status a story may be added to freely. `SPRINT-086`, `SPRINT-088`, `SPRINT-089`
  and `SPRINT-090` are all `Ready`, and appending to a `Ready` sprint
  auto-reverts it to `Draft` and re-gates it; those four became human-unblocked
  only today (the operator cleared every open review-queue item on 2026-10-17)
  and there is no dependency reason to disturb them. `SPRINT-087` is
  `In Progress` and must not be touched at all. On size alone the merges fail
  too: 6 + 5 = 11 and 6 + 7 = 13, both well past the confirmed 8–9-task ceiling.
- **Sizing:** 6 tasks, `M` — the decomposer's own estimate, and squarely on this
  project's 6-task precedent (`SPRINT-073` at `M`; two further 6-task sprints in
  `Learnings.md` estimated `~6 tasks, M` and came in at exactly that). Four
  independent backend roots are each small and local; `T05` is a five-region
  composition over readers that already exist; `T06` is the cost centre, as every
  frontend task in `Learnings.md` has been — by verification effort, not code
  volume. Not `L`: this story adds **no** new access path, writes nothing, and
  touches no shared spine.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-091 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-99-US-01](../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md) | See a Hermes profile as it really is — the full soul, skills with versions, config, jobs and toolsets | P2 | In Progress |

Build order inside the sprint, read from the task files' own `depends_on`:
`(T01, T02, T03, T04) → T05 → T06`. The four roots carry `depends_on: []` and
may be built in any order; `T05` needs all four; `T06` needs `T05`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. Every one of the six `depends_on` edges is
  internal to `REQ-SB-99-US-01` — verified by reading all six task files'
  frontmatter, not taken from the story's prose: `T01`/`T02`/`T03`/`T04` are
  `depends_on: []`, `T05` is
  `[REQ-SB-99-US-01-T01, …-T02, …-T03, …-T04]`, `T06` is `[REQ-SB-99-US-01-T05]`.
  **No edge leaves this story**, so there is no `depends_on_sprints` edge to
  record and hard rule 9 does not hold this sprint behind anything. It is
  startable now, in parallel with `SPRINT-087`'s remaining work.
- **In particular, no edge into `REQ-SB-96`.** `REQ-SB-96-US-01` (deployment
  drift) is still `Draft`, ungrouped and itself `gate: flagged` (`ESC-066`).
  Had this story depended on it, this sprint could not have been planned at all.
  It does not, by construction: `ADR-043` settles that `deployed_to` is not
  consulted on this read path, and the profile's own `skills/` tree is the
  enumeration source.
- **The skills-verdict overlap is a sequencing fact, not a dependency.** The
  story records that the skills-with-versions comparison is the same fact
  `REQ-SB-96-US-01` needs from the artifact's side, and that *whichever story
  lands first owns it*. This sprint lands first, so `T01`'s shared four-status
  verdict rule becomes the one implementation; when `REQ-SB-96-US-01` is specced
  into a sprint it consumes `T01`'s rule rather than writing a second one. That
  is a note for the later sprint, and imposes nothing on this one.
- **External:** a real Hermes install to read — the same standing precondition
  every Hermes-touching sprint in this repo has had. `AC-07` makes an absent or
  unreadable `<HERMES_HOME>` an asserted, verifiable outcome rather than a
  blocker.
- **Story-level gate — already resolved, carried forward as context only:**
  `REQ-SB-99-US-01` was flagged under trigger 3 for `ADR-043`. The operator
  approved `ADR-043` on 2026-10-17 and the story now reads `status: Ready`,
  `gate: clear`. Nothing about it is re-flagged here.

---

## Out of Scope

- **Editing anything from this view** — soul, config, skills or jobs. This is a
  debugger; `AgentDetailPanel.tsx` already owns what is editable.
- **Deploying or repairing a mismatched skill** — `REQ-SB-96-US-02`.
- **The cross-profile drift table** — `REQ-SB-96-US-01`, the same fact from the
  artifact's side.
- **Session transcripts** — `REQ-SB-100-US-01` (`Draft`, ungrouped).
- **Cron job authoring or scheduling** — jobs are listed, never managed.
- **Reworking the Agents Map** or retiring `agents_map_adapter.py`.
- Everything in the `REQ-SB-95` spine — `SPRINT-086` through `SPRINT-090`.

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

**gate: clear 2026-10-17 — no product-owner trigger fired.** No material
assumption: the partition is forced (one eligible story) and every dependency
claim above was read from the six task files' own frontmatter rather than from
the story's prose. The requirement is finalised in the PRD. No ADR created or
changed by this pass — `ADR-043` was the architect's, and the operator approved
it today, which is why the story arrives `gate: clear`. No `ESCALATIONS.md`
entry. **Not oversized:** 6 tasks against a confirmed 8–9-task ceiling. **No
`Blocked` story.** **No cross-sprint dependency introduced** — `depends_on_sprints`
is empty because no task edge leaves the story; there was nothing to record.
No contradictory inputs. On trigger 8: with exactly one eligible story and no
`Draft` sprint to append to, there is no second equally-valid partition to
choose between.

**Why this sprint can start immediately, unlike its neighbours.** Every other
planned-but-unstarted sprint in the repo sits behind `SPRINT-087`
(`SPRINT-088`, and `SPRINT-089`/`SPRINT-090` behind both `087` and `088`), or is
independent-but-already-planned (`SPRINT-086`). `SPRINT-091` joins `SPRINT-086`
as free of any `depends_on_sprints` edge, so it may be built now or at any point
alongside the `REQ-SB-95` spine. The numbering carries no ordering claim over
`SPRINT-086`, `SPRINT-089` or `SPRINT-090`.

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
