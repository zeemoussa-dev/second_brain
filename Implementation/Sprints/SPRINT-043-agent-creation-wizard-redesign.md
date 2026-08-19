---
id: SPRINT-043
title: Agent Creation Wizard Redesign — Agents Map FAB, popup modal, visual step bar, reorganized 4-step flow
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "coder drafted retro below — human to skim and propagate Learnings; REQ-SB-46-US-01 also carries its own flagged scope-internal judgement calls in REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-042]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-043 — Agent Creation Wizard Redesign

## Sprint Goal

Build `REQ-SB-46-US-01` end to end per `ADR-039`: relocate agent creation
from Settings to a new Agents Map FAB opening a popup modal with a visual
4-step progress bar, reorganize the existing per-type field set into the
new step groupings, and add the additive Trigger (User/Agent/Schedule)
metadata choice — reusing the already-`Done` `create_agent`/grant/assign
call sequence unchanged.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-46-US-01` is the only
  story here. Its 5 tasks form one linear, tightly-coupled chain
  (`T01 → T02 → T03 → T04 → T05`, all editing the same single-file wizard
  component's own step state) plus one real, external leaf edge
  (`T04 depends_on REQ-SB-48-US-01-T02`) — confirmed acyclic by direct
  read of all 5 task files.
- **Why NOT combined with `REQ-SB-48-US-01`** (the story its own `T04`
  depends on): combining would still fit under this project's own sizing
  ceiling (5 + 2 = 7 tasks), but per this project's own established
  `SPRINT-040`/`SPRINT-041` precedent for an identical real cross-story
  task-dependency shape, an **ordered pair of smaller sprints** — via a
  recorded `depends_on_sprints` edge — is preferred over one merged sprint
  when the dependency graph gives a genuine choice, keeping each sprint's
  own risk profile (this one carries an outstanding `ADR-039` human-review
  item; `SPRINT-042` does not) cleanly separated rather than conflated.
  `REQ-SB-48-US-01` is sequenced into `SPRINT-042`, ordered before this
  sprint — satisfying `REQ-SB-46-US-01-T04`'s own real `depends_on` edge
  onto `REQ-SB-48-US-01-T02` exactly as that task's own Context/Notes
  direct ("no later than the same sprint as, and ordered before, this
  task").
- **Grouping is unambiguous, not a MUST-FLAG trigger of its own:** the
  cross-sprint `depends_on_sprints` edge recorded here is not newly
  discovered by this pass — it is the decomposer's own already-locked
  `REQ-SB-46-US-01-T04.depends_on` edge, already named in
  `REVIEW-QUEUE.md`'s own `REQ-SB-46-US-01` entry as a "confirm the
  sequencing at `/plan-sprints`" action item for this exact role. Honouring
  an already-known, already-documented dependency via the mechanism
  `Implementation/Pipeline.md` hard rule 7 itself names ("ordered sprints
  with a recorded `depends_on_sprints` edge") is the single, sensible
  resolution here — not an ambiguous partition, and not a dependency this
  pass introduced from scratch. Mirrors `SPRINT-040`/`041`'s own
  precedent, neither of which was flagged for this reason at creation.
- **Sizing estimate:** ~5 tasks, S.
- **Story-level `gate: flagged` carried, not re-flagged by this sprint:**
  `REQ-SB-46-US-01` itself stays `gate: flagged` (its own `ADR-039` human
  review is still outstanding, plus a decomposer-surfaced `SkillsTree.tsx`
  shape-gap finding, now resolved at the task-artefact level per
  `SPRINT-042`'s own Dependencies note). Per `.claude/agents/product-
  owner.md`'s own closed list of 4 sprint-level flag triggers (oversized
  story; blocked story; cross-sprint dependency *introduced by this pass*;
  ambiguous partition), none fired for THIS grouping decision — the
  partition itself is the one clearly correct sequencing. This sprint
  therefore advances `Draft → Ready` with `gate: clear` — the unmet
  `depends_on_sprints: [SPRINT-042]` edge does not block this status
  advancement; it only blocks `/implement-sprint` from actually starting
  this sprint until `SPRINT-042` is `Done` (Pipeline.md hard rule 9),
  exactly as `SPRINT-041`'s own real precedent (`depends_on_sprints:
  [SPRINT-040, SPRINT-038]`) was itself sequenced.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-46-US-01](../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md) | Agent Creation Wizard Redesign — popup modal, visual step bar, reorganized steps | P1 | Done (gate: flagged) |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-042` (must be `Done` — supplies the real,
  standalone, mode-parameterized `SkillsTree.tsx` component this sprint's
  `T04` consumes in `mode="select"`, per `ADR-039` point 2 / the real
  `depends_on: REQ-SB-48-US-01-T02` edge on `REQ-SB-46-US-01-T04`).
- **Outstanding, human-owned, not resolved by this pass:** `ADR-039`
  itself still needs human review before the coder builds — see the
  existing `REQ-SB-46-US-01` entry in `REVIEW-QUEUE.md` (2026-08-14,
  architect pass). This sprint does not duplicate that flag; it is already
  tracked at the story level and will surface again when a human reviews
  the queue before running `/implement-sprint SPRINT-043`.

---

## Out of Scope

- `REQ-SB-47`'s own Schedule tab / schedule-configuration UI — the Step 4
  Trigger choice only records intent (story's own Non-Goals).
- `REQ-SB-48`'s own collapsible Tool-grouped Skills tree presentation
  details — this sprint's `T04` only *consumes* `SkillsTree.tsx` in
  `mode="select"`; originating it is `SPRINT-042`'s own scope.
- `REQ-SB-51`'s `is_background_agent` toggle — explicitly declined for
  fold-in by the architect pass; left for a future story.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (none needed — `ADR-039` was already recorded by the architect pass; the coder made no further architectural change)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-039`, already `Accepted` before this sprint started)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  Task count and split held with zero re-scoping. All 5 tasks share one
  single, tightly-coupled file (`CreateAgentWizardModal.tsx`); the coder
  built Steps 1-4 in one coherent pass rather than 5 separate
  non-compiling checkpoints (disclosed in each task's own Implementation
  Log), but still verified and marked each task `Done` independently,
  strictly against its own locked ACs only, in dependency order. Real
  effort was dominated by live verification breadth (11 locked ACs, 3 full
  agent-type regression walkthroughs with real backend cross-checks), not
  code volume — matches this project's own repeatedly-confirmed "verification
  cost, not code volume, drives real effort" pattern.

### What worked

- **Reconciling `T04` against `SkillsTree.tsx`'s REAL shipped shape before
  writing any Step 3 code, per the task's own explicit "Before / Inputs"
  directive** — the real component's `mode="select"` props
  (`skills`/`selectedIds`/`onChange`, each skill object needing a
  `granted: boolean` field even though unused by the Select view) differed
  from `ADR-039`'s own illustrative `tools={...} skills={...}` guess; using
  the real shape caught this before any code was written, not after a
  compile error.
- **Filtering a `window.fetch` spy's captured calls to non-`GET` only**
  cleanly isolated each type's own submit-sequence call count/order/shape
  from `T01`'s own legitimate, newly-added map-refresh `GET` calls that
  fire immediately afterward via `onCreated` — without this the AC-07
  regression guard's literal "exactly N calls" wording would have looked
  like a false failure against a real, intended, in-scope behavior change
  (the Map now refreshes itself instead of requiring a page reload).
- **Cross-checking the wizard-created Expert agent against an
  independent, parallel direct `POST /agents` + `PATCH` call with the same
  inputs** turned "the resulting agent looks right" into a byte-for-byte
  confirmed match — reusing this project's own established cross-check
  pattern one more time, now at the agent-creation-wizard-redesign layer.
- **Picking Step 3's "extra" Skill by real `data-testid` (skill id), not
  checkbox index** for the Producer regression case — the Tool-grouped
  tree's own row order differs from the flat Step-2 output-Skill radio
  order, so an index-based pick risked accidentally re-selecting the same
  skill as the mandatory output Skill (silently reducing the intended
  4-call sequence to 3 via the code's own correct de-dup logic, which
  would have looked like a false failure rather than the real bug it would
  have been in the *test*, not the app).

### What didn't work

- **A multi-statement `Runtime.evaluate` string reusing `const`/`let`
  identifiers across separate `evaluate()` calls in the same CDP session**
  — Chrome's per-session global execution context persists top-level
  `const`/`let` bindings between otherwise-independent `Runtime.evaluate`
  calls, so a second script reusing the same `const boxes = ...` name hit
  a real `SyntaxError: Identifier already declared`. Fixed immediately by
  wrapping every multi-statement evaluate string in an IIFE.

### Patterns to carry forward

- **Wrap every multi-statement CDP `Runtime.evaluate` expression in an
  IIFE `(() => { ... })()`** — never rely on top-level `const`/`let` being
  safely reusable across separate `evaluate()` calls in the same browser
  session; a single shared global execution context persists them.
- **When a task's own literal "exactly N calls" regression-guard wording
  predates a sibling task's own legitimate, in-scope behavior addition
  (here, `T01`'s new post-create map refresh), filter the spy to the
  semantically relevant call subset (non-`GET`/mutating calls) rather than
  either loosening the assertion or treating the new behavior as a bug** —
  the AC's own intent (submit-sequence parity) and the new feature's own
  intent (immediate map refresh) are both real and both satisfiable
  without contradiction once correctly scoped.
- **Select a specific target element by its own real, unique identifying
  `data-testid`/id, not by DOM/render-order index, whenever two different
  UI regions independently iterate the same underlying data set in
  potentially different orders** (a Tool-grouped tree vs. a flat radio
  list over the same Skill catalog here) — reconfirms this project's own
  general "don't trust incidental ordering" caution one layer up from
  prior sprints' own CDP-interaction findings.

### Antipatterns to avoid

- **Assuming a task's own Starting-State call-count description is
  exhaustive of every legitimate call the final, fully-composed feature
  will make**, when an earlier sibling task in the same story already
  added new, real, in-scope behavior (a map refresh) that also uses
  `fetch` — filter deliberately by call semantics (mutating vs. read),
  don't just count total calls.

### Open follow-ups

- Two scope-internal judgement calls (all-4-steps-built-together
  sequencing; Expert's own optional Step-3 Skills grants) parked in
  `REVIEW-QUEUE.md` for human spot-check — neither blocks anything, both
  are disclosed and verified live.
- The ADR-039 human-review REVIEW-QUEUE item that was open before this
  sprint started is now effectively superseded by this sprint's own
  completion (the ADR was already `Accepted` by the time `/implement-
  sprint` ran) — left as-is for the human to close explicitly, not
  auto-resolved by the coder.
