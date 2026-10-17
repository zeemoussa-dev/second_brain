---
id: SPRINT-088
title: The catalogue published into agent context and enforced at the call — "I cannot do that" becomes a real answer
status: In Progress                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-088 — Published Catalogue and Call Enforcement

## Sprint Goal

Tell every agent exactly what this app can do, from the live catalogue, and
validate every action call against that same catalogue before it runs — so an
unknown id is refused by the framework rather than by the prompt, and "I cannot
do that" becomes a real answer with a recorded unmet-request.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-03` is the behavioural half of
  the Action spine and sits one wave behind `US-02`. Its two inbound edges are
  recorded in the task files: `US-03-T01 → US-02-T01` (the catalogue entity it
  publishes from) and `US-03-T02 → US-02-T03` (the CRUD API the call gate
  validates against). Everything else is internal: `T02 → T03`, `T02 → T04`,
  `(T01, T03, T04) → T05`.
- **Why it is not merged back into `SPRINT-087`.** 6 + 5 = 11 tasks, past the
  confirmed 8–9-task `L` ceiling — and this project has a repeatedly-confirmed
  precedent (`SPRINT-011`→`012`, `025`→`026`, `049`→`050`) that a downstream
  story whose own Tests need the **real, running** output of the upstream one is
  better sequenced behind it than improvised against an imagined interface.
  That is exactly this case: the call gate's ACs need a real, stored, resolvable
  Action to refuse and to accept.
- **Why `US-04` and `US-05` are not folded in here.** Both depend on *this*
  story as well as on `US-02` (`US-04-T05 → US-03-T04`, `US-04-T06 → US-03-T01`,
  `US-05-T05 → US-03-T02`/`US-03-T03`), so neither can be built alongside it;
  they go one wave later.
- **Sizing:** 5 tasks, sized `L` — deliberately a notch above this project's
  5-task norm (`SPRINT-032`/`034`/`038` at `S`, `SPRINT-081` at `M`). Code volume
  is not the driver: this is the sprint where agent answers actually change, so
  every locked AC needs real, live agent-call verification across a loopback call
  path, a single-use confirmation grant and a ledger. This project's Learnings
  name that cost explicitly and repeatedly ("verification cost, not code volume,
  drove the real effort" — `SPRINT-031`, `SPRINT-036`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-088 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-03](../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md) | The catalogue is published into agent context and enforced at the call — "I cannot do that" becomes a real answer | P2 | Ready |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01` (needs `US-02-T01`), `T02` (needs `US-02-T03`) `→ T03`, `T02 → T04`,
`(T01, T03, T04) → T05`.

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-087` (`REQ-SB-95-US-02` — the Action entity,
  its Manager and its CRUD API). `/implement-sprint` refuses this sprint until
  `SPRINT-087` is `Done` (hard rule 9).
- **Two sprints depend on this one:** `SPRINT-089` (`US-04`) and `SPRINT-090`
  (`US-05`).
- **Shared file with `SPRINT-086`, with no dependency edge between them.**
  `US-03-T01` (here) and `US-01-T02` (`SPRINT-086`) each add their own
  independent auto-generated marker pair to
  `src/backend/app/business/core/agents/agent_manager.py`. No edge was recorded
  between them and neither reads the other's block, but their titles disagree
  about who lands first (`US-03-T01` calls its pair "the third", `US-01-T02`
  calls its own "the fourth"; both describe the same **two** existing pairs).
  The ordinal is cosmetic — no AC depends on it. Under this plan `SPRINT-086`
  lands first, so this story's pair is in fact the fourth. Compose around the
  **real current file**, not the task's remembered version of it.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-03` is flagged under trigger 3 — `ADR-033` decides
  how an agent actually invokes an action (one loopback route on this app's own
  API, reached by a shipped runner Skill; confirmation as an app-owned
  single-use grant) and awaits the operator's look. That call path is what this
  whole sprint builds, so it is worth reading before the build starts. See
  `REVIEW-QUEUE.md`.

---

## Out of Scope

- The Action catalogue itself — `SPRINT-087`.
- Workflows (`SPRINT-089`) and entity resolution (`SPRINT-090`).
- The Operator Profile's own marker block (`SPRINT-086`).

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

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (both
inbound edges are quoted from the task files); requirement finalised; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; **not oversized**
(5 tasks); **no `Blocked` story**. On trigger 5's cross-sprint clause: the
`depends_on_sprints: [SPRINT-087]` edge is **not a dependency this pass
introduced** — it is the decomposer's own `US-03-T01 → US-02-T01` /
`US-03-T02 → US-02-T03` edges expressed at sprint level, forced by the fact that
28 tasks cannot be one sprint. Recording it, rather than inventing a merge that
breaks the sizing ceiling, is what hard rule 7 asks for, and it matches this
repo's own precedent for the same situation (`SPRINT-080` ← `079`,
`SPRINT-083` ← `082`, `SPRINT-084` ← `083`, all `gate: clear`). No contradictory
inputs (the marker-block ordinal mismatch above is cosmetic and recorded), and no
ambiguity about the partition.

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
