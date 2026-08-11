---
id: SPRINT-003
title: Obsidian manual-entry templates and in-vault guide note
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, XS"    # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-003 — Obsidian manual-entry templates and in-vault guide note

## Sprint Goal

Author the four Obsidian core-Templates note-type templates (Customer,
Opportunity, Agreement, Consumption-Snapshot) and the in-vault Manual Entry
Guide note, so manual entries are structurally consistent with the
automated capture pipeline's output without leaving Obsidian.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `REQ-SB-15-US-01` is the only
  story in scope. Its two tasks form a strict linear `depends_on` chain
  (`T02 → [T01]` — the guide note is written after, and cites, the four
  template files T01 authors, to stay accurate) implementing one cohesive
  deliverable (templates + the guide explaining them), so there is no
  partition question inside this story.
- **Sibling story `REQ-SB-14-US-01` deliberately excluded, not merged in:**
  both stories were born in the same `/plan-tasks` batch and reference the
  same `ADR-006`, but neither story's tasks `depends_on` the other's (both
  stories' own `## Dependencies` sections confirm this explicitly), and
  they are different *kinds* of work: this story is pure vault-content
  authoring (four template files + one guide note, explicitly zero
  `src/backend`/`src/frontend` changes per its own Constraints), verified
  by direct file inspection against the resolved schema; `REQ-SB-14-US-01`
  is real backend Python across three architecture layers, verified live
  against the running Outlook/vault integration. Each story is also
  independently shippable — this story alone delivers the full manual-entry
  path — and folding a 2-task, XS story into a 4-task, S story would not
  reduce total work, only sprint count, at the cost of mixing two
  materially different verification styles into one working context.
  Shared batch timing and a shared ADR are not, on their own, grouping
  drivers under this role's mandate (dependencies, complexity, amount of
  work). See SPRINT-002 for `REQ-SB-14-US-01`.
- **Sizing estimate:** ~2 tasks, XS (extra-small). Both tasks are pure
  markdown/content authoring with no code, no live-integration
  verification, and no automated-test tooling applicable (per both tasks'
  own `## Tests` sections) — the smallest-effort sprint in the project so
  far, smaller even than the SPRINT-001/SPRINT-002 precedent (~4 tasks,
  S). No calibration history exists yet for a content-only sprint
  specifically (`Implementation/Learnings.md` has no harvested retro data
  at all yet); this estimate is a first-principles judgement based on task
  count and the near-total absence of implementation complexity (content
  authoring against an already-fully-resolved schema), not a calibrated
  one.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-003 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-15-US-01](../UserStories/REQ-SB-15-US-01-manual-entry-templates-and-guide.md) | Obsidian templates and in-vault guide for manual Customer/Pipeline/Agreement/Consumption entries | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None. Not ordered relative to `SPRINT-002`
  either — the two sprints are independent siblings (see Grouping
  Rationale), so `/implement-sprint` may run them in either order.
- The story itself carried `gate: flagged` for ADR-006 (new `Templates/`
  vault root, guide-note placement), already resolved: "Operator review
  (2026-08-11): ADR-006 approved as written — no changes requested.
  `gate: flagged → clear`." No open blocker remains.
- The templates and guide note are authored directly into the real,
  configured Obsidian vault (`VAULT_PATH`), not a fixture/test vault — no
  new external dependency, same live-vault posture as SPRINT-002 and
  SPRINT-001.

---

## Out of Scope

- `REQ-SB-14-US-01` (Vault Graph Connectivity) — sibling story from the
  same `/plan-tasks` batch, deliberately placed in its own sprint,
  `SPRINT-002` — see Grouping Rationale above.
- Any capture/ingestion pipeline for Opportunity, Agreement, or
  Consumption-Snapshot data — no such pipeline exists or is scoped by this
  story, per its own Non-Goals.
- A community plugin (e.g. Templater) — explicitly excluded; only
  Obsidian's core Templates plugin is used.
- Any Second Brain application UI for creating these notes — Obsidian-
  native authoring only.
- Frontmatter schema validation/enforcement tooling — not built.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — Data Model §Vault Content Conventions (architect pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — ADR-006 (shared with sibling story)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new decision emerged
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

- **Estimated:** ~2 tasks, XS — **Actual:** 2 tasks, XS, zero rework —
  **Takeaway:** matched exactly. Third sprint in a row hitting its
  estimate; this one is the first data point specifically for a
  content-only (no code, no live integration) sprint shape — smaller
  effort correlates cleanly with smaller task count here, worth reusing
  this size class for future pure-vault-content sprints.

### What worked

- **Literal content in decomposer-authored tasks**, same payoff pattern as
  SPRINT-001/002 but for markdown instead of Python — both tasks specified
  the exact file content verbatim, so the coder's job was write-and-verify,
  not design.
- **Sequencing the guide note after the templates it describes** (T02
  `depends_on` T01) meant the guide's cited paths/names were verified
  against real, already-written files rather than the plan document —
  caught nothing wrong here, but the ordering removed the risk of the
  guide drifting from what T01 actually produced.
- **Verification-by-file-inspection for non-code deliverables** worked
  cleanly: both tasks' `## Tests` sections explicitly named "read the file
  back and check field-for-field" as the verification method up front
  (acknowledging Obsidian's own UI is a human action outside a coder
  subagent's reach), so there was no ambiguity about what "verified" meant
  for content work.

### What didn't work

- No friction this sprint.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Content-only sprints are their own size class** — XS, not S: this
  sprint (2 tasks, pure markdown, no live-integration verification) took
  meaningfully less coder effort than SPRINT-001/002's S-sized backend
  sprints despite a similar task count ratio. When sizing a future
  vault-content-authoring sprint, don't default to the backend-sprint
  calibration — use this sprint as the XS reference point instead.
- **Name the verification method explicitly when a task has no automated
  test path** — both tasks stated up front that "read the file back,
  check field-for-field" was the verification proxy for a human-driven
  Obsidian UI action. Worth doing this for any future non-code
  deliverable task, not just when it happens to come up.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- (None new this sprint.)

### Open follow-ups

- Obsidian's Settings → Templates → "Template folder location" still needs
  a one-time manual step from the operator (point it at `Templates/`) —
  not something this project's code can automate or verify; flagged in
  both this sprint's tasks' Out of Scope, repeated here so it isn't lost.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for the grouping decision
itself: only one story is in scope (`REQ-SB-15-US-01`), its own two tasks
form one strict linear `depends_on` chain implementing one cohesive
deliverable, it is not oversized (2 small content-only tasks), it is not
blocked (both tasks are `status: Ready`, the story's own `gate: flagged`
for ADR-006 was already resolved by the operator before this pass), and no
cross-sprint dependency was introduced (`depends_on_sprints: []`). The
decision to keep sibling story `REQ-SB-14-US-01` in a separate sprint
(`SPRINT-002`) rather than merging it in was a judgement call, not a
genuinely ambiguous multiple-equally-valid-options case — see
`SPRINT-002`'s own Notes for the mirrored rationale. Advanced
`Draft → Ready`.

---

**Sprint wrap (2026-08-11):** Both tasks Done, all 6 locked ACs verified,
nothing blocked. `status: Done`, `completed: 2026-08-11`. `gate: flagged`
per this role's sprint-wrap contract — the Retrospective above is a
**draft**; a human should skim it and propagate "Patterns to carry
forward" into `Implementation/Learnings.md`.
