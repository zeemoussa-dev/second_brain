---
id: SPRINT-057
title: Project & Customer Status Synthesizer Agents
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "drafted retrospective awaiting human skim/harvest into Implementation/Learnings.md"                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-18"                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-057 — Project & Customer Status Synthesizer Agents

## Sprint Goal

Build the Project/Customer Synthesizer mechanism (`REQ-SB-57`) so a Project's
Glimpse regenerates automatically on every real evidence change (Thread update,
Meeting link-in), a Customer's rollup Glimpse cascades from it, History grows only
on a genuine `status` conclusion, and a new durable Customer fact routes through a
Pending Approval instead of a silent Background rewrite.

---

## Grouping Rationale & Sizing

- **Why grouped — single-story sprint.** `REQ-SB-57-US-01` is the only `Ready`,
  ungrouped (`sprint: ""`) story in scope for this pass. All 4 tasks (`T01`-`T04`)
  belong to this one story, share one architecture scope
  (`architecture.md` → "Project & Customer Synthesizer — the 'genuinely concludes'
  History-line bar", extending `ADR-042`), and the decomposer's own recorded
  `depends_on` graph — read directly from each task file's own frontmatter, not
  inferred from the story's own summary table:
  - `T01` (`depends_on: []`) — Project Synthesizer core (Glimpse regeneration +
    History-line conclusion trigger) + Thread-pipeline trigger wiring + the new
    `project-customer-synthesizer` Agent identity. The one shared root every other
    task builds on.
  - `T02` (`depends_on: [T01]`) — Customer Synthesizer core (rollup Glimpse +
    History-line cascade + drop-from-rollup) + Route-to-Project-approval trigger
    wiring.
  - `T03` (`depends_on: [T01]`) — Meeting-link-in trigger wiring, independent of
    `T02` (touches a different module, `meeting_classification.py`, and only needs
    `T01`'s shared `resync_project_from_thread` helper).
  - `T04` (`depends_on: [T02]`) — Background-amendment durable-fact detection +
    Pending Approval proposal/finalize. The last task in the chain; nothing depends
    on it.
  - Two independent build lanes converge on one shared root: `T01` → `T03` on one
    lane, `T01` → `T02` → `T04` on the other. `T02`/`T03` may build in either order
    relative to each other once `T01` lands. The graph is acyclic — confirmed
    directly against each task file's own `depends_on:` frontmatter, not the
    story's own non-authoritative summary table.
  - All four tasks are `phase: P1` — no phase mix.
- **Sizing estimate:** ~4 tasks, S — matches this project's own established
  4-task/S precedent (`SPRINT-025`, `SPRINT-037`, `SPRINT-042`), one notch below
  the 6-task/M precedent (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, `SPRINT-045`,
  `SPRINT-048`) and the 3-task/S precedent (`SPRINT-023`, `SPRINT-024`,
  `SPRINT-050`, `SPRINT-054`) this project has already confirmed accurate at
  retro. One shared root plus a two-lane fan-out converging through one final
  task is a small, single-working-context shape — no task in the chain exceeds
  one working session per the decomposer's own sizing note in the story.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-057 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-57-US-01](../UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md) | Project & Customer Status Synthesizer Agents — regenerate Glimpse on evidence change, append History on conclusion, propose Background amendments via Pending Approvals | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's own `## Dependencies` names
  `REQ-SB-54-US-01` (`SPRINT-048`, Done), `REQ-SB-55-US-01` (`SPRINT-049`, Done),
  and `REQ-SB-56-US-01` (`SPRINT-053`, Done) as blockers — all three are already
  shipped, so no `depends_on_sprints` edge is needed; this sprint is immediately
  buildable.
- Unblocks `REQ-SB-58-US-01` (Customer/Project-Aware Expert, `Draft`, blocked on
  this story shipping) and `REQ-SB-59-US-01` (Full Vault Migration, `Draft`,
  blocked on `REQ-SB-54` through `REQ-SB-58` all shipping) — per the operator's
  own explicit direction to properly unblock `REQ-SB-59` through the full
  pipeline. This sprint is the first of the two remaining blockers; `REQ-SB-58` is
  the second, already specced and waiting on this one.

---

## Out of Scope

- Producing the evidence itself (Thread updates, Meeting links, manual Captures)
  — already shipped, `REQ-SB-54`/`55`/`56`'s own scope.
- Glimpse-first chat answering — `REQ-SB-58`'s own scope.
- Backfilling historical evidence — `REQ-SB-59`'s own scope.
- Deciding whether Project Synthesizer and Customer Synthesizer are one or two
  Agent identities — already resolved by the decomposer (one identity,
  `project-customer-synthesizer`) and recorded in the story's own `## Notes`.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no change beyond the already-recorded, operator-confirmed proposal from `/plan-tasks`
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR this sprint
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  No task was split, dropped, or merged; the recorded `depends_on` graph
  (`T01` independent root → `T02`/`T03` fan-out → `T04` convergence) built
  in exactly that order with zero reordering. `T01` (the shared root,
  Glimpse regeneration + the operator-confirmed History-line trigger) was
  correctly the heaviest by real design surface; `T04` (this session) was
  the lightest in build friction — `guess_project_for_thread`'s already-
  proven Compass-call shape and `vault_filing_expert._create_cross_
  cutting_proposal`'s already-proven Pending-Approval shape both
  generalized cleanly with zero surprises on first run.

### What worked

- **Reusing two already-proven shapes verbatim for a brand-new mechanism**
  — `T04`'s `detect_customer_durable_fact` is a direct, byte-for-byte-shape
  copy of `guess_project_for_thread`'s own Compass-call construction, and
  `_propose_background_amendment`/`finalize_background_amendment_proposal`
  is a direct copy of `vault_filing_expert._create_cross_cutting_proposal`/
  `finalize_cross_cutting_update`. Zero design iteration needed; the live
  verification passed on the very first attempt.
- **Grounding a dedup decision in the entity's OWN current state instead of
  building a second dedup mechanism** — `T04`'s detection prompt reads the
  Customer's own current `## Background` and asks "is this NEW," so a
  repeat observation of an already-approved fact honestly returns
  `has_durable_fact: false` with no separate idempotency check anywhere.
  Verified live, not just by prompt inspection: the exact same
  `evidence_text` re-run after approval produced zero new proposals.
- **A wholly-disposable, never-before-seen fixture entity name** (`T04`'s
  own `ZZZ-T04-Verify-Co`, vs. `T01`-`T03`'s shared use of the real
  `Core42` customer) **avoided the concurrent-session collision class of
  finding `T03` hit entirely** — no drift, no self-heal step needed, cheap
  independent re-confirmation that cleanup left zero residue.
- **`Implementation Log` + `REVIEW-QUEUE.md` "flag scope-internal judgement
  calls without blocking"** carried through consistently across all four
  tasks (`T01`/`T03`/`T04` all logged real, disclosed judgement calls with
  zero MUST-FLAG triggers) — the story shipped end-to-end in one
  continuous sprint with no human intervention required mid-build.

### What didn't work

- **`T03`'s own live verification against the real, shared `Core42`
  customer collided with a concurrent sibling coder session's own
  independent `REQ-SB-57` verification pass against the SAME real
  customer** — real content/mtime drift on `Core42`'s own `log.md`/
  `index.md`, self-healed live via the already-`Done`
  `synthesize_customer("Core42")` call, not a defect in `T03`'s own code.
  Root cause: sizing this sprint's live verification around a real,
  already-populated shared entity when a synthetic one would have served
  equally well for the mechanism under test.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **"Propose in the owning module, finalize via `_APPROVAL_HANDLERS`" is
  now a 4x-confirmed canonical shape** (`SPRINT-050`'s original 3x-confirm,
  now reconfirmed a fourth time by `T04`'s `propose_background_amendment`)
  — default to this shape for any future new Pending-Approval kind without
  re-deriving it; the whole mechanism (Compass-call prompt shape included)
  ported with zero design iteration.
- **Ground a dedup/repeat-observation decision in the entity's own CURRENT
  recorded state, not a separate idempotency table** — when a detection
  prompt is explicitly grounded in "what's already true about X," an
  already-recorded fact naturally yields a negative result with no second
  dedup mechanism to build or keep in sync. Verify this live via a literal
  repeat-observation regression check, not just by inspecting the prompt.
- **Prefer a wholly-disposable, never-before-used fixture entity name over
  a real, already-populated shared one whenever a mutation-heavy live
  mechanism (Pending Approvals, `## Background`/`## Glimpse` writes) is
  under test and the AC doesn't specifically require a pre-existing real
  entity** — sidesteps concurrent-session collision risk entirely, and
  makes independent post-cleanup reconfirmation trivial (a directory-
  existence check plus a pending-approval-list filter, both unambiguous).

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Defaulting to a real, shared, already-populated fixture entity for
  live verification of a mutation-heavy mechanism just because it's
  already there and convenient** — `T03`'s use of the real `Core42`
  customer collided with a genuinely concurrent sibling session's own live
  verification against the same entity. Not catastrophic here (self-healed
  live, real root cause independently traced and disclosed), but entirely
  avoidable by defaulting to a synthetic, never-before-seen fixture name
  whenever the AC itself doesn't require a real, pre-existing entity.

### Open follow-ups

- Three linked `REVIEW-QUEUE.md` spot-check items (`T01`, `T03`, `T04`'s
  own scope-internal judgement calls) remain open for human spot-check —
  none block anything downstream (no locked-AC impact either way).
- `REQ-SB-57-US-01` shipping unblocks `REQ-SB-58-US-01` (Customer/
  Project-Aware Expert) to proceed through `/plan-tasks` next, per the
  operator's own explicit direction to properly unblock `REQ-SB-59`
  through the full pipeline.

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single-story, single-sprint
grouping — the only `Ready`, ungrouped story in scope. Dependency graph confirmed
by direct read of each task file's own `depends_on:` frontmatter (`T01`
independent root; `T02`→`T01`; `T03`→`T01`; `T04`→`T02`), acyclic, no cross-sprint
edge needed since all three of the story's own blocking stories are already
`Done`. Not oversized against this project's own confirmed sizing precedent for
4-task sprints. No ambiguity in the partition (one story, obviously one sprint).
No MUST-FLAG trigger fired — no new material assumption, no ADR created or
changed, no `ESCALATIONS.md` entry, no cross-sprint dependency introduced, no
blocked story, no oversized grouping, no equally-valid alternative partition.

gate: clear 2026-08-18 (product-owner) — no trigger fired; see itemized reasoning
above. Sprint `status: Draft → Ready`. Eligible for `/implement-sprint`.

---

**Coder pass (2026-08-18) — sprint closes.** `T01`-`T04` all `Done`;
`REQ-SB-57-US-01` (this sprint's only story) `status: In Progress → Done`.
Sprint `status: In Progress → Done`, `completed: 2026-08-18`. `## Retrospective`
drafted above per the Pipeline's own "coder drafts, human harvests" contract.

gate: flagged 2026-08-18 (coder) — sprint-retro human-skim trigger (not a
MUST-FLAG failure): the drafted retrospective awaits human skim and
propagation of "Patterns to carry forward"/"Antipatterns to avoid" into
`Implementation/Learnings.md`. A `REVIEW-QUEUE.md` entry has been added,
alongside the three linked task-level scope-internal-judgement-call
spot-check items (`T01`/`T03`/`T04`) and the story-level closing entry.
