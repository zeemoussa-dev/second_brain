---
id: SPRINT-059
title: Full Vault Migration to the New Knowledge Model
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: ""                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-059 — Full Vault Migration to the New Knowledge Model

## Sprint Goal

One-time backfill: wipe the legacy `Work/Emails/` notes/dedup stores, fully
re-run capture over Outlook history through the new Thread/Meeting pipelines,
and regenerate every legacy flat Customer note onto the new OKF shape — so the
whole vault reflects the new knowledge model consistently from day one.

---

## Grouping Rationale & Sizing

- **Why grouped — single-story sprint.** `REQ-SB-59-US-01` is the only
  `Ready`, ungrouped (`sprint: ""`) story in scope this pass (verified by
  scanning every `Implementation/UserStories/*.md` for `status: Ready` +
  `sprint: ""` — no other story matched). All 3 of its tasks belong to this
  one story, share one architecture scope (`architecture.md` → "Vault
  Migration — One-Time Full Vault Migration to the New Knowledge Model
  (REQ-SB-59, see ADR-047)"), and form a graph read directly from each task
  file's own `depends_on:` frontmatter, not re-derived from the story's own
  summary table:
  - `T01` — `wipe_legacy_email_notes()`. `depends_on: []`. Independent root:
    archives `Work/Emails/` notes plus the two `.second-brain/` dedup stores.
  - `T02` — `recapture_outlook_history(email_limit, meeting_days_back)`.
    `depends_on: [REQ-SB-59-US-01-T01]` — hard, load-bearing edge: `T01`
    archiving `processed_email_ids.json` is what resets the email dedup gate;
    without it `T02`'s recapture silently no-ops. Must run strictly after
    `T01`.
  - `T03` — `regenerate_customer_notes()`. `depends_on: []` — the
    decomposer's own directly-verified finding (not an assumed straight
    chain): its evidence is each legacy flat Customer note's own
    pre-migration body, fully disjoint from what `T01` archives and what
    `T02` recaptures. No code-level dependency either direction.
  - Acyclic (`T01 -> T02`, `T03` independent). All 3 tasks are `phase: P1` —
    no phase mix. No cross-sprint edge is needed for `T03`'s independence —
    it stays in this same sprint regardless, per the decomposer's own note
    ("all three land in one story/sprint regardless").
- **Why not split into two sprints:** all 3 tasks belong to one story with
  one Definition of Done and one architecture scope (`ADR-047`); splitting
  `T03` out into its own sprint would introduce a needless cross-sprint edge
  for zero dependency, complexity, or amount-of-work benefit — the same
  "don't split a tightly-scoped single story" reasoning `SPRINT-057` and
  `SPRINT-058` (both single-story sprints from this same batch) already
  established as this project's norm.
- **Sizing estimate:** ~3 tasks, S — matches this project's own repeatedly
  confirmed "~3 tasks, S" sizing bucket (e.g. `SPRINT-023`, `SPRINT-024`,
  `SPRINT-050`, `SPRINT-053`), not oversized. The real cost here is live
  wall-clock time against a real mailbox/vault (per the decomposer's own
  note), not task count or code volume.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-059 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-59-US-01](../UserStories/REQ-SB-59-US-01-full-vault-migration-to-new-knowledge-model.md) | Full Vault Migration to the New Knowledge Model — wipe Work/Emails/, re-run capture over Outlook history through the new pipelines | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (`wipe_legacy_email_notes()`,
`depends_on: []`) → `T02` (`recapture_outlook_history(...)`,
`depends_on: [T01]`); `T03` (`regenerate_customer_notes()`, `depends_on: []`)
runs independently of both.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's own `## Dependencies` names all
  five hard-blocking sibling stories — `REQ-SB-54-US-01` (`SPRINT-048`),
  `REQ-SB-55-US-01` (`SPRINT-049`), `REQ-SB-56-US-01` (`SPRINT-053`),
  `REQ-SB-57-US-01` (`SPRINT-057`), `REQ-SB-58-US-01` (`SPRINT-058`) — all
  five are already `Done` per `BACKLOG.md`, so no `depends_on_sprints` edge
  is needed; this sprint is immediately buildable.
- **External:** the real, live Outlook mailbox/calendar this migration
  re-captures from (read-only from Outlook's own perspective, per the
  story's own Scenario 4/AC-04).

---

## Out of Scope

- A parallel-run/diff-then-cutover mechanism — explicitly declined by the
  operator in favor of wipe-then-recapture (story's own `## Constraints`).
- Any change to the capture pipelines themselves — only re-runs the
  already-`Done` `REQ-SB-55`/`REQ-SB-56` pipelines over historical data.
- A recurring/scheduled version of this migration — genuinely one-time.
- Modifying Outlook's own source data.
- Resolving the Pending Approvals `regenerate_customer_notes()` produces —
  ordinary, ongoing operator review, decoupled from "migration complete."

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact — already appended at `/plan-tasks` (`ADR-047`), unchanged this pass
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created this sprint (product-owner does not write ADRs; `ADR-047` already exists from `/plan-tasks`)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
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

- **Estimated:** ~3 tasks, S — **Actual:** _(filled in by coder at Done)_

### What worked

- _(filled in by coder at Done)_

### What didn't work

- _(filled in by coder at Done)_

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(filled in by coder at Done)_

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(filled in by coder at Done)_

### Open follow-ups

- _(filled in by coder at Done)_

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single-story, single-sprint
grouping — `REQ-SB-59-US-01` confirmed the only `Ready`, ungrouped
(`sprint: ""`) story in scope this pass. Dependency graph read directly from
each of the 3 task files' own `depends_on:` frontmatter (`T01` independent
root → `T02` hard-depends on `T01`; `T03` independent), acyclic, single phase
(`P1`) — no phase mix. No `depends_on_sprints` edge needed: all 5 stories the
story's own `## Dependencies` names as hard blockers
(`REQ-SB-54-US-01`/`REQ-SB-55-US-01`/`REQ-SB-56-US-01`/`REQ-SB-57-US-01`/
`REQ-SB-58-US-01`) are already `Done`. Sizing calibrated against this
project's own repeatedly confirmed "~3 tasks, S" bucket — not oversized. No
ambiguity in the partition (one story, three tasks with one real dependency
edge and one confirmed-independent task; no other ungrouped story exists to
fold with or split against). No blocked story. The story's own `gate: clear`
(set 2026-08-18 when the human reviewed and approved `ADR-047` directly in
chat, clearing the architect/decomposer's prior flag) carries forward
unchanged — this pass introduces no new ADR, no new assumption, no new
`ESCALATIONS.md` entry, and no cross-sprint dependency. No MUST-FLAG trigger
fired from this grouping pass.

gate: clear 2026-08-18 (product-owner) — no trigger fired; see itemized
reasoning above. Sprint `status: Draft → Ready`. Eligible for
`/implement-sprint`.
