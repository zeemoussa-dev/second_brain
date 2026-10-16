---
id: SPRINT-086
title: Operator Profile — the singleton record, published into every agent's context
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
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

# SPRINT-086 — Operator Profile — the Singleton Record, Published Into Every Agent's Context

## Sprint Goal

Give this install one record of who the agent acts for — the operator's identity,
their other mail addresses, and their team as email+role entries — and publish it
into every agent's own SOUL.md as an auto-generated marker block, in one republish
pass that reloads the Registry exactly once.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-01` is the one story of
  `REQ-SB-95`'s five that is **fully independent** in the decomposer's recorded
  graph — read task by task, every `depends_on` edge in `T01`–`T05` points inside
  this story (`T01 → T02 → T04`, `T01 → T03 → T05`), and **no task in `US-02`,
  `US-03`, `US-04` or `US-05` reaches back into it**. It therefore needs no
  `depends_on_sprints` edge and can be built immediately, in parallel with or
  ahead of the Action spine. The story itself states the intent directly: it
  "deliberately lands first" because it builds the agent-context publication seam
  `US-03` reuses.
- **Why it was not merged with another story.** The only merge candidate that
  would not import a dependency it does not have is `US-02` (6 tasks, also
  edge-free at the sprint level) — 5 + 6 = 11 tasks, well past this project's own
  confirmed 8–9-task `L` ceiling (`SPRINT-021`, `SPRINT-030`, `SPRINT-049`,
  `SPRINT-083`). Merging with `US-05` (the other 5-task story) would be worse: it
  would drag this independent story behind `SPRINT-087`/`SPRINT-088`, since
  `US-05-T05` depends on `US-02-T02`, `US-03-T02` and `US-03-T03`. Standing alone
  is the only grouping that honours the graph without delaying buildable work.
- **Sizing:** 5 tasks, sized `M`. Four backend plus one frontend, in line with
  this project's own 5-task precedents (`SPRINT-032`, `SPRINT-034`, `SPRINT-038`
  at `S`; `SPRINT-081` at `M`). Sized `M` rather than `S` because `T02` is a
  genuinely new mechanism in the most actively-extended backend file
  (`agent_manager.py`) — a fourth marker-block pair plus a new one-pass republish
  method — and its ACs need real agent-context verification, which this project's
  Learnings repeatedly show dominates cost over code volume.
- **Sizing risk to watch:** if the operator answers the open export-privacy
  question (below) with *strip on export*, this story gains **one further task**
  and `AC-08` becomes locked. That takes the sprint to ~6 tasks, still inside the
  band — it does not re-open this grouping.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-086 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-01](../UserStories/REQ-SB-95-US-01-operator-profile.md) | Operator Profile — one record of who the agent acts for, published into every agent's context | P2 | Ready |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → (T02, T03)`, `T02 → T04`, `T03 → T05`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- **Shared file with `SPRINT-088`, with no dependency edge between them.** Both
  `REQ-SB-95-US-01-T02` (here) and `REQ-SB-95-US-03-T01` (`SPRINT-088`) add their
  own independent auto-generated marker pair to
  `src/backend/app/business/core/agents/agent_manager.py`. The decomposer recorded
  **no edge between them**, and neither reads the other's block — but their titles
  disagree about who lands first (`US-01-T02` calls its pair "the fourth",
  `US-03-T01` calls its own "the third", and both describe the same **two**
  existing pairs, `_SPECIALISTS_*` and `_INDEX_GUIDANCE_*`). The ordinal is
  cosmetic naming; no AC and no behaviour depends on it. Under this plan `US-01`'s
  pair lands first and is in fact the third. Whichever lands second composes around
  the **real current file**, per this project's standing pattern — do not apply
  either task's illustrative code block to a remembered version of that file.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-01` is flagged under trigger 8 — publication writes
  colleague names into every agent's SOUL.md, and an exported Agent bundle copies
  both that `soul.md` and Hermes' own `profile.tar.gz` (opaque bytes, `ADR-014`),
  so a second copy rides along. `AC-08` is deliberately **`locked: false`**, no
  task implements either answer, and `T04` only *discloses* what a real bundle
  contains. The sprint can be built and closed without that decision: the other
  seven ACs are locked and complete. See `REVIEW-QUEUE.md`.
- **ADRs awaiting a human look:** `ADR-032`, `ADR-035`, `ADR-036` (its marker-block
  decision only) and `ADR-038` (binding; it supersedes `ADR-036`'s `SELF_EMAIL`
  retirement). All are `Accepted`; the operator has reviewed the `ADR-036` item
  (marker block approved, retirement rejected). Nothing here waits on them.

---

## Out of Scope

- Actions, Workflows, enforcement and entity resolution — `SPRINT-087` …
  `SPRINT-090`.
- **`SELF_EMAIL` stays exactly as it is** (`ADR-038`): `system_settings._FIELDS`,
  `config.REQUIRED_FOR_STARTUP`, `setup_wizard.py`, `setup_router.py`,
  `SettingsSystemPage.tsx` and the deployed payload capture scripts are all
  untouched. The Profile mirrors the setting and never writes it.
- Implementing either answer to the export-privacy question (`AC-08`).
- Org-chart modelling, Person-note editing, multi-operator installs.

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

**gate: clear 2026-10-16 — no product-owner trigger fired.** Checked trigger by
trigger: no assumption (the partition is read from the recorded `depends_on`
edges, not from story order); requirement finalised; no ADR created or changed by
this pass; no `ESCALATIONS.md` entry; **not oversized** (5 tasks, inside the
confirmed band); **no `Blocked` story** (`REQ-SB-95-US-01` is `Ready`); **no
cross-sprint dependency** — this sprint has none at all; no contradictory inputs
(the marker-block ordinal mismatch above is cosmetic and is recorded, not
guessed at); and **no ambiguity** — there is exactly one grouping that keeps this
independent story buildable now without exceeding the sizing band. The story's own
upstream `gate: flagged` is carried forward above rather than cleared here;
`/plan-sprints` does not resolve another stage's flag.

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
