---
id: SPRINT-084
title: Capture-time noise/classification + Enrich-stage pending-action extraction
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-083]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-084 — Capture-time Noise/Classification + Enrich-stage Pending-action Extraction

## Sprint Goal

Layer the two genuinely new REQ-SB-87 judgment capabilities — Capture-time
classify-or-skip (noise definition + Internal/Partner/Customer stamping) and
Enrich-stage pending-action extraction into `## Actions` — onto the two
already-migrated Skills `SPRINT-083` delivers.

---

## Grouping Rationale & Sizing

- **Why grouped together:** `REQ-SB-87-US-03` and `REQ-SB-87-US-05` are the
  second real diamond in this requirement's dependency graph, mirroring
  `SPRINT-083`'s own `US-02`/`US-04` pairing one wave later. Read directly
  from each task file's own frontmatter: `US-03-T03`
  `depends_on: [REQ-SB-87-US-03-T02, REQ-SB-87-US-02-T01]` — it reaches
  back specifically into `US-02` (now in `SPRINT-083`), not `US-04`.
  `US-05-T01` `depends_on: [REQ-SB-87-US-04-T03]` — it reaches back
  specifically into `US-04` (also `SPRINT-083`), not `US-02`. Neither
  `US-03` nor `US-05` has any dependency on the other at all — one is a
  5-task Capture-side chain (`T01→T02→T03→T04→T05`), the other a 3-task
  Enrich-side chain (`T01→T02→T03`), touching entirely different scripts
  (`ingest_email.py`/orchestrators vs. `apply_thread_review.py`/`SKILL.md`).
  Since both stories' own real prerequisite tasks live inside the SAME
  upstream sprint (`SPRINT-083`), and neither depends on the other, they
  are the textbook case for one shared `depends_on_sprints: [SPRINT-083]`
  edge rather than two further, unnecessarily-split sprints — the same
  "diamond stays one sprint" reasoning `SPRINT-083`'s own Grouping
  Rationale already applies one wave earlier in this same requirement.
  - Both stories also share the identical rollout posture (the same
    100-email scratch-vault proving phase, both stories' own Constraints)
    and both are genuinely NEW judgment capabilities (not mechanics
    migrations) building directly on `SPRINT-083`'s freshly-migrated
    engine calls — real cohesion beyond the shared dependency edge alone.
- **Sizing:** 5 + 3 = 8 tasks, sized `L`. Inside this project's own
  reliable 6-9 task band, matching the `8 tasks/L` precedent confirmed
  multiple times (`SPRINT-010`, `SPRINT-039`, `SPRINT-049`, `SPRINT-056`).
  Folding a third story in here was not possible without contradicting the
  graph (there is no third `REQ-SB-87` story left ungrouped); splitting
  `US-03`/`US-05` apart into two further sequential sprints was considered
  and rejected — both already stand alone comfortably inside the band (5
  and 3 tasks respectively), so an additional sprint boundary between them
  would add pure process overhead without honouring any real dependency
  edge that requires it (neither depends on the other).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-084 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-87-US-03](../UserStories/REQ-SB-87-US-03-capture-time-noise-definition-and-classification.md) | Capture-time noise definition, skip, and Internal/Partner/Customer classification | P1 | Ready (gate: flagged — `ADR-018` human review pending, see REVIEW-QUEUE.md) |
| [REQ-SB-87-US-05](../UserStories/REQ-SB-87-US-05-enrich-pending-action-extraction.md) | Enrich-stage pending-action extraction into Thread `## Actions` | P1 | Ready (gate: clear) |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-083` (must be `Done` before
  `/implement-sprint` may start this sprint — `US-03-T03` needs the real,
  migrated `ingest_email.py` `US-02-T01` delivers; `US-05-T01` needs the
  real, migrated, template-access-converged `apply_thread_review.py`
  `US-04-T03` delivers).
- Internal task order (per the decomposer's own `depends_on`; the two
  stories' own chains are independent of each other and may build in
  either order or in parallel, subject to the cross-sprint edges above):
  - `US-03`: `T01` → `T02` → `T03` (also needs `SPRINT-083`'s `US-02-T01`)
    → `T04` → `T05` (the scratch-proving pass + real-vault cutover).
  - `US-05`: `T01` (needs `SPRINT-083`'s `US-04-T03`) → `T02` → `T03` (the
    real, live scratch-vault agent-pass verification).

---

## Out of Scope

- `REQ-SB-87-US-01`/`US-02`/`US-04` — built in `SPRINT-082`/`SPRINT-083`,
  this sprint's own prerequisites.
- Retrofitting/reclassifying already-captured Threads with the new coarse
  classification, or backfilling `## Actions` for already-processed
  Threads — both stories' own Non-Goals; each governs new
  captures/re-processing going forward only.
- `BUG-042` (existing fine-grained company-name resolution mis-tagging) —
  a separate, already-tracked Open bug, not absorbed into either story
  here.

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
  was made pairing `US-03` and `US-05` (the real `depends_on` edges — each
  reaching back into a specific, different task inside `SPRINT-083`, and
  the absence of any edge between the two stories themselves — were read
  directly from the decomposer's own task frontmatter, never re-derived or
  guessed); `REQ-SB-87` is not `Draft`/unfinalised in the PRD; no ADR was
  created or changed by this pass (`ADR-018` was appended at
  `/plan-tasks`, not here); no `ESCALATIONS.md` entry was written by this
  pass; the sprint is not oversized (8 tasks, inside the confirmed band);
  the `depends_on_sprints: [SPRINT-083]` edge this pass introduces is a
  **disclosed, honoured** edge matching two independent real task-level
  `depends_on` edges reaching back into that sprint, not a contradiction
  of the graph; the partition is unambiguous — this is the only grouping
  of the two remaining stories that honours both cross-sprint edges while
  keeping the sprint inside this project's own confirmed sizing band.
- **What this does NOT mean:** `REQ-SB-87-US-03` itself still carries
  `gate: flagged` at the story level (`ADR-018`, trigger-3) with its own
  open `REVIEW-QUEUE.md` entry. That flag is carried forward here for
  visibility, not silently dropped — see the `Stories in Scope` status
  column above. Per `Pipeline.md`, a flagged story gate does not block
  `/plan-sprints` or `/implement-sprint` from proceeding; the human
  resolves the story's own flag independently, on its own timeline — the
  same carry-forward shape already established for `SPRINT-078`,
  `SPRINT-080`, and `SPRINT-082` (this same requirement's own foundation
  sprint).
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-87-US-03`/`ADR-018` entry already covers the
  open review; duplicating it here would only fragment the same open item
  across two places.
- With this sprint's own creation, `REQ-SB-87`'s full, real dependency
  graph (foundation → two parallel migrations → two parallel new
  capabilities) is now expressed as three ordered sprints
  (`SPRINT-082` → `SPRINT-083` → `SPRINT-084`), 6 + 9 + 8 = 23 tasks total,
  matching the decomposer's own reported task count exactly.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** _(filled in by coder at close)_

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
