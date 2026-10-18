---
id: SPRINT-089
title: Workflow as the seventh artifact kind — the operator documents how a kind of request is handled
status: In Progress                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087, SPRINT-088]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
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

# SPRINT-089 — Workflow as the Seventh Artifact Kind

## Sprint Goal

Let the operator document, as a real artifact, the ordered steps for a kind of
request — each step referencing a catalogued Action id so a workflow is invalid
by construction rather than by review — and have the framework run it step by
step against a run record.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-04` is the most dependent of
  the five. Its six inbound cross-story edges are recorded in the task files —
  four into `US-02` (`T01 → US-02-T01`, `T02 → US-02-T03`, `T04 → US-02-T04`,
  `T07 → US-02-T06`) and two into `US-03` (`T05 → US-03-T04`,
  `T06 → US-03-T01`) — so it cannot start until both `SPRINT-087` and
  `SPRINT-088` are `Done`. At 7 tasks it also fills a sprint on its own.
- **Why not merged with `SPRINT-090` (`US-05`).** They share the same two
  upstream sprints and have **zero edges between them** (checked task by task in
  both directions), which is normally this project's textbook case for one
  shared sprint (`SPRINT-083`, `SPRINT-084`, `SPRINT-085` all did exactly that).
  It was rejected here on size alone: 7 + 5 = 12 tasks, far past the confirmed
  8–9-task `L` ceiling. Being independent of each other, they may be built in
  either order once their two upstream sprints are `Done` — the sprint numbering
  carries no ordering claim between `SPRINT-089` and `SPRINT-090`.
- **Sizing:** 7 tasks, sized `L`. Precedent for 7 tasks is split between `M`
  (`SPRINT-052`, `SPRINT-085`) and `L` (`SPRINT-079`); this one sits with the
  `L` case because, like `SPRINT-079`, it adds a whole **kind** across
  inventory, export, import and the dependency resolver (`T04`), plus a run
  record with its own routes (`T05`), publication into agent context (`T06`) and
  a new Settings screen (`T07`). `T04` additionally depends on `US-02-T04`, so
  it extends a six-kind set that will itself be freshly written.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-089 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-04](../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md) | Workflow as the seventh artifact kind — the operator documents how a kind of request is handled | P2 | In Progress (T01 Done 2026-10-18 — `AC-01`, `AC-07`; T02 Done 2026-10-18 — `AC-02`/`AC-06`; `ESC-075` Resolved, the authorised one-fixture scope extension landed and also stopped `T01`'s tests reading the operator's real Actions store; suite 627 passed. T03 Done 2026-10-18 — `AC-01`/`AC-02` verified over the new `app/api/workflows_router.py`, registered in `app/main.py`; refusals reach the client as a 409 carrying the Manager's own sentence; suite 628 → 634 passed, 0 failed, plus a real-socket round trip on a disposable install. `T05` and `T07` unblocked. **T04 Done 2026-10-18** — `AC-04`/`AC-05`/`AC-07` verified on 12 AC-tagged tests: the seventh kind is live across all six `business/logic/artifact_*.py` modules including the import conflict gate, an exported Workflow carries every Action its steps name and recurses into their implementation Skills, import reuses `WorkflowManager.import_workflow` so `T02`'s refusal fires at the first save rather than as a second divergent check, Pipelines are byte-identical on their real stored bytes/cron ids/schedules, and nothing from `ActionCalls/`/`WorkflowRuns/` is exportable. Two authorised scope extensions, both escalated rather than reached for: `ESC-076` (the sixth `artifact_*.py` module) and `ESC-077` (the unknown-kind guard test, which had used `workflow` as its unsupported-kind example and now derives its accepted-kinds assertion from the live map). Suite 634 → **655 passed, 0 failed**. `T07` unblocked; `T05`/`T06` remain) |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → T02 → T03`, `T01 → T04`, `T03 → T05 → T06`, `(T03, T04) → T07`.

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-087` (`US-02` — the Action entity, CRUD API,
  kind registration and the Actions screen) **and** `SPRINT-088` (`US-03` — the
  publication seam and the confirmation/single-use grant). `/implement-sprint`
  refuses this sprint until **both** are `Done` (hard rule 9).
- **No dependency either way with `SPRINT-090`.** Either may be built first once
  the two upstream sprints are `Done`.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-04` is flagged under trigger 3 — `ADR-034` decides
  that the framework *runs* a workflow step by step against a run record rather
  than reciting it into the agent's context, and awaits the operator's look.
  That decision shapes `T05`/`T06` directly. See `REVIEW-QUEUE.md`.
- **`ADR-032`'s "`Pipeline` is left exactly as it is"** stands: a Workflow is
  intent-triggered, a Pipeline is time-triggered, and convergence is explicitly
  deferred.

---

## Out of Scope

- The Action catalogue (`SPRINT-087`) and enforcement at the call
  (`SPRINT-088`).
- Entity resolution (`SPRINT-090`).
- Any change to the existing `Pipeline` artifact kind (`ADR-032`).

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

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (all
six inbound edges are quoted from the task files); requirement finalised; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; **not oversized**
(7 tasks, inside the confirmed band — this is also why `US-05` was not folded in
here); **no `Blocked` story**. On trigger 5's cross-sprint clause: both
`depends_on_sprints` edges are the decomposer's own task edges expressed at
sprint level, not dependencies this pass introduced; hard rule 7's "ordered
sprints with a recorded edge" is exactly the sanctioned shape, and the repo
precedent for it is `SPRINT-080`/`083`/`084`, all `gate: clear`. No contradictory
inputs. On trigger 8: the `SPRINT-089`/`SPRINT-090` build order is genuinely free
(no edge either way), but that is not an ambiguous *partition* — both sprints are
legal in either order and the sprint files say so, so there is nothing for a
human to decide.

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
