---
id: SPRINT-002
title: Automated Customer hub notes and wikilinking for vault graph connectivity
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"             # YYYY-MM-DD when status → Done
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

# SPRINT-002 — Automated Customer hub notes and wikilinking for vault graph connectivity

## Sprint Goal

Stand up REQ-SB-14's shared "ensure this customer's hub note exists, then
link this note to it" mechanism, wired into both a one-time retrofit
endpoint and the going-forward email-capture pipeline, so Obsidian's graph
view shows connected customer clusters instead of isolated dots.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `REQ-SB-14-US-01` is the only
  story in scope. Its four tasks form a branching `depends_on` chain
  (`T02→[T01]`, `T03→[T02]`, `T04→[T02]` — file-I/O primitives, then the
  shared orchestration module, then two independent consumers of it: the
  per-write hook and the retrofit endpoint) implementing one cohesive
  capability against one shared mechanism, so there is no partition
  question inside this story — matching the `REQ-SB-07-US-01`/SPRINT-001
  precedent's reasoning exactly (a strict/branching dependency chain
  implementing one capability is not splittable across sprints without
  inventing an artificial cross-sprint edge).
- **Sibling story `REQ-SB-15-US-01` deliberately excluded, not merged in:**
  both stories were born in the same `/plan-tasks` batch and reference the
  same `ADR-006`, but neither story's tasks `depends_on` the other's (both
  stories' own `## Dependencies` sections confirm this explicitly — "not
  overlapping... neither story's implementation blocks the other"), and
  they are different *kinds* of work: this story is real backend Python
  across three architecture layers (`data_access` → `business` →
  `api`/hook wiring) verified live against the running Outlook/vault
  integration, per `REQ-SB-14-US-01-T03`/`T04`'s manual-verification
  steps; `REQ-SB-15-US-01` is pure vault-content authoring (four template
  files + one guide note, zero `src/backend`/`src/frontend` changes, per
  its own Constraints), verified by direct file inspection, not a live
  integration run. Each story is also independently shippable value on its
  own — REQ-SB-14 alone delivers a fully connected graph for
  pipeline-captured data; REQ-SB-15 alone delivers the manual-entry path —
  neither needs the other to be "done" the way SPRINT-001's four tasks
  needed each other (one shared mechanism, no independent value split
  across them). Shared batch timing and a shared ADR are not, on their
  own, grouping drivers under this role's mandate (dependencies,
  complexity, amount of work); they don't override the absence of a real
  `depends_on` edge or a shared build mechanism. See SPRINT-003 for
  `REQ-SB-15-US-01`.
- **Sizing estimate:** ~4 tasks, S (small). Same shape as SPRINT-001's
  precedent (data-access primitives → business orchestration → two
  downstream wire-ups), each task a single-file-or-single-new-module
  backend change already scoped tightly by the decomposer. One real
  calibration point exists now (SPRINT-001: estimated ~4 tasks/S, actual
  4 tasks/S, zero rework) — this sprint's shape and task count match that
  precedent closely enough to reuse the same estimate with reasonable
  confidence, though still only one prior data point per
  `Implementation/Learnings.md` (whose only entry is an explicitly
  provisional book-reference note, not yet a harvested sprint retro).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-002 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-14-US-01](../UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md) | Customer hub notes and automatic wikilinking for vault graph connectivity | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story itself carried `gate: flagged` for ADR-006 (new `Templates/`
  vault root — see sibling story below), already resolved: "Operator
  review (2026-08-11): ADR-006 approved as written — no changes
  requested. `gate: flagged → clear`." No open blocker remains.
- The retrofit endpoint (T04) and the per-write hook (T03) both run
  live against the real, configured Obsidian vault (`VAULT_PATH`) and the
  real Outlook/Compass integration — no fixture/mock environment, per the
  story's own Constraints. Not a sprint-blocking dependency (the same
  integration already worked for SPRINT-001), noted here for the coder's
  awareness going into `/implement-sprint`.

---

## Out of Scope

- `REQ-SB-15-US-01` (Manual-Entry Templates & Guidelines) — sibling story
  from the same `/plan-tasks` batch, deliberately placed in its own
  sprint, `SPRINT-003` — see Grouping Rationale above.
- REQ-SB-10 (People Living Documents) — this story replicates its
  auto-baseline + preserve-manual-edits pattern for Customer notes only;
  building out People notes themselves is not in scope.
- REQ-SB-08 (Meetings) / REQ-SB-09 (To-Do) capture pipelines — not built
  yet; wiring them into this same hub-linking hook is future work for
  those stories' own `/plan-tasks` passes.
- Any Second Brain application UI surfacing graph connectivity — Obsidian's
  own graph view is the presentation surface, unchanged by this sprint.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — Data Model §Customer Hub Notes & Graph Linking (architect pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — ADR-006 (shared with sibling story)
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S, zero rework —
  **Takeaway:** matched exactly, second sprint in a row (SPRINT-001 also
  matched). The "reuse SPRINT-001's calibration for a similarly-shaped
  sprint" reasoning in this sprint's own Grouping Rationale held up —
  worth trusting a bit more next time a sprint has this same shape
  (data-access primitives → business orchestration → downstream wire-ups).

### What worked

- **Literal code in decomposer-authored tasks**, again — same payoff as
  SPRINT-001. All 4 tasks specified exact functions/code; coders implemented
  and verified with near-zero ambiguity.
- **Live verification surfaced a real interaction the plan didn't
  anticipate, and the fallback handled it cleanly**: T04's test plan
  suggested ADNOC as the "missing hub note" example, but T03's own
  newly-wired hook had already created `Work/Customers/ADNOC.md` via the
  dev-server startup capture run by the time T04 ran — a direct, correct
  consequence of the story's own earlier task, not a bug. The coder
  substituted TAQA per the task's own pre-written fallback ("if every
  customer already has a hub note, pick any existing...") rather than
  stalling. Worth naming as a pattern: when a task's manual-verification
  walkthrough names a specific example, write the "if that example no
  longer fits, do X instead" fallback into the task up front — it paid off
  directly here.
- **Orchestrator-level review of small scope-internal assumptions** (the
  `limit=10` and ADNOC→TAQA substitutions) kept the human queue clean —
  both were exactly the fallback the task briefs had already pre-authorized,
  so clearing them didn't need to wait for the operator, only genuinely
  novel judgement calls should reach `REVIEW-QUEUE.md` for a human.

### What didn't work

- No real friction this sprint — smoother than SPRINT-001 (which had the
  filename-collision bug and a stale-server code-reload miss). Nothing to
  flag here.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Pre-write the fallback for a task's example-based verification step** —
  when a task's manual-test walkthrough names a specific example (a
  customer, a record, a file), write the "if that example's state has
  changed, do X instead" fallback directly into the task, the way T04's did.
  Live, sequential task execution means an earlier task in the same story
  can legitimately change the state a later task's example assumed.
- **Trust sizing calibration a little more once two same-shaped sprints
  agree** — SPRINT-001 and SPRINT-002 both estimated ~4 tasks/S and landed
  exactly there. Not yet a large sample, but real signal for sprints with
  this same "primitives → orchestration → wire-ups" shape.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- (None new this sprint — SPRINT-001's `BACKLOG.md`-status-drift antipattern
  remains the standing one; it didn't recur here because it was actively
  watched for.)

### Open follow-ups

- `REQ-SB-08` (Meetings) / `REQ-SB-09` (To-Do) will need their own capture
  pipelines wired into `customer_hub_linking.ensure_hub_note_and_link`,
  replicating T03's per-write hook pattern — not built here, per this
  sprint's own Out of Scope.
- `SPRINT-003` (`REQ-SB-15-US-01`, the sibling story) is still open —
  separate sprint, not part of this retro.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for the grouping decision
itself: only one story is in scope (`REQ-SB-14-US-01`), its own four tasks
form one acyclic branching `depends_on` chain implementing one shared
mechanism (not splittable without an artificial cross-sprint edge), it is
not oversized (4 tasks, same shape/size as the SPRINT-001 precedent), it is
not blocked (all four tasks are `status: Ready`, the story's own
`gate: flagged` for ADR-006 was already resolved by the operator before
this pass), and no cross-sprint dependency was introduced
(`depends_on_sprints: []`). The decision to keep sibling story
`REQ-SB-15-US-01` in a separate sprint (`SPRINT-003`) rather than merging
it in was a judgement call, not a genuinely ambiguous multiple-equally-
valid-options case — both stories' own `## Dependencies` sections
independently confirm neither blocks the other, and the two are materially
different kinds of work (live backend integration vs. pure vault-content
authoring), so the grouping call is defensible and not flagged.
Advanced `Draft → Ready`.

---

**Sprint wrap (2026-08-11):** All 4 tasks Done, all 5 locked ACs verified
live, nothing blocked. `status: Done`, `completed: 2026-08-11`.
`gate: flagged` per this role's sprint-wrap contract — the Retrospective
above is a **draft**; a human should skim it and propagate "Patterns to
carry forward" into `Implementation/Learnings.md`.
