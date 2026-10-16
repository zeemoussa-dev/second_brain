---
id: SPRINT-087
title: Action as the sixth artifact kind — the catalogue, its CRUD API, plugin contributions and its screen
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-087 — Action as the Sixth Artifact Kind

## Sprint Goal

Make `Action` a real, stored, validated, browsable and portable sixth artifact
kind — one catalogue of what this app can actually do, resolved at save time so a
broken action cannot sit waiting to fail, contributable by plugins, and rendered
in its own Settings screen.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-02` is the **root of
  `REQ-SB-95`'s dependency spine** — read from the task files' own frontmatter,
  eight cross-story edges point *into* it and none point out of it:
  `US-03-T01 → US-02-T01`, `US-03-T02 → US-02-T03`, `US-04-T01 → US-02-T01`,
  `US-04-T02 → US-02-T03`, `US-04-T04 → US-02-T04`, `US-04-T07 → US-02-T06`,
  `US-05-T05 → US-02-T02`. It therefore needs no `depends_on_sprints` edge of its
  own and must land before `SPRINT-088`, `SPRINT-089` and `SPRINT-090`.
- **Why nothing was folded in with it.** `US-03` (5 tasks) is the obvious
  candidate — it depends only on this story — but 6 + 5 = 11 tasks is well past
  this project's confirmed 8–9-task `L` ceiling, and `US-03`'s own story text
  states the split reason directly: "adding agent-side publication and call
  validation to it would not fit one working context." The only other edge-free
  story at this point is `US-01` (`SPRINT-086`); merging it here would make an
  11-task sprint out of two stories that share no file and no edge.
- **Sizing:** 6 tasks, sized `L`. Six tasks has repeatedly landed at `M` on this
  project (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, `SPRINT-048`), but this one
  is sized a notch up because adding an artifact **kind** is cross-cutting by
  nature: `T04` alone reaches `artifacts_inventory.py`, export, import, the
  secret scan and the dependency resolver — every one of which today hard-codes
  the five-kind set ("no 6th value is ever produced"). The `Index` precedent
  (2026-09-06) is the measured template, and `T06` adds a new Settings screen on
  top of it.
- **Deliberate ordering consequence — it closes an open plan gap.** `ADR-037`
  takes the `FRAMEWORK_API` 7 → 8 bump **once**, in whichever of the two
  plugin-contract stories lands last. `REQ-SB-95-US-05-T02` reads the real
  `plugin_api.py` first and bumps only if `register_action` is already there;
  `REQ-SB-95-US-02-T05` (here) carries no equivalent instruction, so if `US-02`
  landed last nobody would move the constant. **Sequencing `US-05`
  (`SPRINT-090`) strictly behind this sprint makes that moot** — the
  `depends_on_sprints` edge guarantees `register_action` exists before
  `US-05-T02` runs, so its conditional read takes the bump. This is the exact
  resolution option named in the `REVIEW-QUEUE.md` item, and no task file was
  edited to achieve it.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-087 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-02](../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md) | Action as the sixth artifact kind — one catalogue of what this app can actually do | P2 | Ready |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → T02 → T03`, `T01 → T04`, `T02 → T05`, `(T03, T04, T05) → T06`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This is the spine's root and can start
  immediately (as can `SPRINT-086`, which is independent of it).
- **Three sprints depend on this one:** `SPRINT-088` (`US-03`), `SPRINT-089`
  (`US-04`) and `SPRINT-090` (`US-05`). Per hard rule 9, `/implement-sprint`
  refuses each of them until this sprint is `Done`.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-02` is flagged under trigger 3 — `ADR-033` fixes two
  fields this story stores (`allowed_callers` as agent ids, and the confirmation
  flag's meaning) and awaits the operator's look. If `ADR-033` changes, the
  catalogue's stored shape changes with it, so this is the cheapest moment to
  read it. See `REVIEW-QUEUE.md`.
- **`ADR-032` is `Accepted` but has never had a human review entry.** Noted, not
  blocking.

---

## Out of Scope

- **Publication into agent context and enforcement at the call** — `SPRINT-088`.
  This story stops at a stored, validated, browsable, portable Action and changes
  no agent behaviour.
- Workflows (`SPRINT-089`) and entity resolution (`SPRINT-090`).
- The `FRAMEWORK_API` 7 → 8 bump — owed by `SPRINT-090` under this ordering
  (see Grouping Rationale).

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
eight cross-story edges above are quoted from the task files, not inferred from
story order); requirement finalised; no ADR created or changed by this pass; no
`ESCALATIONS.md` entry; **not oversized** (6 tasks, inside the confirmed band);
**no `Blocked` story**; **no cross-sprint dependency on this sprint's side** — it
has none; no contradictory inputs; **no ambiguity** — as the root of the spine
with three dependants, this story's placement first is forced by the graph, and
the only merge candidate that would not import a dependency breaks the sizing
ceiling. The story's own upstream `ADR-033` flag is carried forward above rather
than cleared here.

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
