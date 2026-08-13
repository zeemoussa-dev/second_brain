---
id: SPRINT-004
title: Person notes auto-created and updated from email capture
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

# SPRINT-004 — Person notes auto-created and updated from email capture

## Sprint Goal

Stand up REQ-SB-10's shared "ensure this email sender's Person note exists
and is up to date, linking it to their company's Customer hub note when
that company is a known customer" mechanism, wired into both a one-time
retrofit endpoint over already-captured Email notes and the going-forward
email-capture pipeline, so every person the user has emailed with gets a
living Person note that builds itself without manual entry.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `REQ-SB-10-US-01` is the only
  Ready, ungrouped story this pass. Its four tasks form the exact same
  shape as `REQ-SB-14-US-01`/SPRINT-002's precedent: a branching
  `depends_on` chain (`T02→[T01]`, `T03→[T02]`, `T04→[T02]` — file-I/O
  primitives, then the shared business-orchestration module, then two
  independent consumers of it: the per-write capture hook and the retrofit
  endpoint) implementing one cohesive capability against one shared
  mechanism (`ensure_person_note`). There is no partition question inside
  this story — splitting T01–T04 across sprints would force an artificial
  cross-sprint edge through the middle of a single acyclic dependency
  chain, which hard rule 7 exists precisely to prevent. No sibling story is
  in scope to weigh against (unlike SPRINT-002, which had `REQ-SB-15-US-01`
  born in the same batch); `REQ-SB-10-US-01` is the only story currently
  `Ready` with `sprint: ""`, so there is no partition ambiguity to resolve.
- **Sizing estimate:** ~4 tasks, S (small) — directly matching the
  SPRINT-002 (`REQ-SB-14-US-01`) precedent's shape (data-access primitives
  → business orchestration → two downstream wire-ups) and its recorded
  estimate. Two real calibration points now exist for this exact shape:
  SPRINT-001 (estimated ~4 tasks/S, actual 4 tasks/S, zero rework) and
  SPRINT-002 (same estimate, same actual, zero rework) — per
  `Implementation/Learnings.md`'s harvested pattern, "trust sizing
  calibration a little more once two same-shaped sprints agree." This
  story's own task files make the resemblance concrete, not just
  structural: T01 explicitly mirrors REQ-SB-14-US-01-T01's baseline/
  top-up primitives shape; T02 explicitly reuses `customer_hub_linking.py`
  as its composed dependency and mirrors its module shape
  (`retrofit_*` batch function over smaller reusable functions); T03 and
  T04 are each a small, single-purpose wire-up (a two-line hook call and a
  thin ~15-line HTTP wrapper respectively), same as SPRINT-002's T03/T04.
  No task here is larger or more novel in kind than its SPRINT-002
  counterpart, so the same estimate is reused with high confidence.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-004 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-10-US-01](../UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md) | Person notes auto-created and updated from email capture, preserving manual edits | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` section confirms it is not blocked: the
  capture pipeline (`app/business/email_classification.py`, REQ-SB-07-US-01,
  Done) and the hub-note primitives it reuses (`app/business/
  customer_hub_linking.py`, `app/data_access/vault_writer.py`,
  REQ-SB-14-US-01, Done) both already exist and work. No open blocker.
- T03 (the per-write hook) and T04 (the retrofit endpoint) both run live
  against the real, configured Obsidian vault (`VAULT_PATH`) and, for T03,
  the real Outlook/Compass integration — no fixture/mock environment, per
  the story's own Constraints. Not a sprint-blocking dependency (the same
  integration already worked for SPRINT-001 and SPRINT-002), noted here for
  the coder's awareness going into `/implement-sprint`.

---

## Out of Scope

- **Meeting-attendee-based Person backfill/capture** — blocked on
  REQ-SB-08 (Meetings Capture Pipeline), which does not exist yet, per the
  story's own Non-Goals. A follow-on story will replicate this sprint's
  mechanism for meeting attendees once REQ-SB-08 exists.
- REQ-SB-08 (Meetings) / REQ-SB-09 (To-Do) capture pipelines themselves —
  not built yet.
- Any Second Brain application UI surfacing People data — Obsidian's own
  note/graph views are the presentation surface, unchanged by this sprint.
- A `Person` Obsidian manual-entry template — belongs with REQ-SB-15's
  pattern if/when wanted; not part of this story's automated-capture scope.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — Data Model §Person Notes & Email-Sender Extraction (architect pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none needed, extends ADR-003/004
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
  **Takeaway:** matched exactly. Third sprint in a row hitting this
  estimate for this exact shape (data-access primitives → business
  orchestration → two downstream wire-ups), following SPRINT-001 and
  SPRINT-002. This shape's calibration is now well-trusted — worth reusing
  with high confidence the next time the same pattern appears, without
  re-deriving the estimate from scratch.

### What worked

- **Reusing an existing business module's granular primitives, not its
  combined convenience function** — the story's own carve-out (never call
  `customer_hub_linking.ensure_hub_note_and_link` blindly; call
  `ensure_customer_hub_note`/`link_note_to_customer_hub` separately, only
  after `find_matching_customer` confirms a real match) was designed in
  at architecture time and worked exactly as intended live: derivable-but-
  unknown companies (Microsoft, and Core42 itself for internal colleagues)
  correctly got a tag with no spurious Customer hub note.
- **A fixed, hardcoded blocklist for a genuinely stable external set**
  (personal email providers) rather than forcing everything into the
  vault-derived-list pattern that fits customer/kind names — the
  architect's explicit reasoning for treating this one list differently
  held up with no friction.
- **Business-module composition, made explicit** — this is the first
  module that calls into another business module rather than only
  `data_access`; architecture.md recorded this as an intentional,
  permitted shape ahead of time rather than leaving it to be
  second-guessed during implementation.
- **A transient agent-session interruption cost nothing** — T03's first
  attempt was cut off by an unrelated API error before any file was
  touched; confirmed via git diff/grep that nothing had changed, then
  retried clean. Worth normalizing: always verify actual on-disk/task
  state before assuming a retry needs to reconcile a partial edit.

### What didn't work

- **Environment collision, not a code problem:** T04's dev server couldn't
  bind port 8000 because an unrelated project (`agentic-map`) already had
  it open on this shared dev machine. Cost a few minutes of diagnosis
  before falling back to port 8001. Not this project's bug, but worth
  knowing about ahead of time next time multiple projects' dev servers
  might run on the same host.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Call a composed module's granular primitives, not its convenience
  wrapper, when the wrapper's assumptions don't hold for the new caller**
  — `ensure_hub_note_and_link` assumes "this is definitely a customer";
  `people_extraction.py` isn't always calling about a customer, so it
  calls the two granular steps directly instead, after its own check.
  Apply this whenever a new caller wants only part of an existing
  function's unconditional behavior.
- **Verify actual repo/task state before treating an interrupted agent run
  as a partial edit needing reconciliation** — an early API-error
  termination may mean nothing was written yet; check before assuming
  cleanup work is needed.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- (None new this sprint.)

### Open follow-ups

- **Meeting-attendee-based Person capture** remains blocked on REQ-SB-08
  (Meetings Capture Pipeline), which doesn't exist yet — a follow-on story
  should replicate this sprint's `ensure_person_note` mechanism for
  meeting attendees once REQ-SB-08 is built, per this story's own
  Non-Goals.
- A `Person` Obsidian manual-entry template (mirroring REQ-SB-15's four
  templates) isn't built — not part of this story's automated-capture
  scope; worth adding to REQ-SB-15's template set if/when wanted.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for the grouping decision itself:
`REQ-SB-10-US-01` is the only story `Ready` with `sprint: ""` this pass, so
there is no partition question at all (not even a judgement call like
SPRINT-002's sibling-story exclusion). Its own four tasks form one acyclic
branching `depends_on` chain (`T02→[T01]`, `T03→[T02]`, `T04→[T02]`)
implementing one shared mechanism (`ensure_person_note`), not splittable
without inventing an artificial cross-sprint edge (would contradict hard
rule 7). Not oversized — same task count and shape as the already-Done
SPRINT-002 precedent, and `Implementation/Learnings.md` records two prior
same-shaped sprints (SPRINT-001, SPRINT-002) both landing exactly at their
~4 tasks/S estimate with zero rework. Not blocked — all four tasks are
`status: Ready`, the story itself is `status: Ready, gate: clear`, and its
own `## Dependencies` section confirms both upstream mechanisms it reuses
(REQ-SB-07-US-01, REQ-SB-14-US-01) are already `Done`. No cross-sprint
dependency was introduced (`depends_on_sprints: []`). Single phase (P1)
throughout — no phase-mixing. Advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 4 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Sprint wrap (2026-08-11):** All 4 tasks Done, all 9 locked ACs verified
live, nothing blocked. `status: Done`, `completed: 2026-08-11`.
`gate: flagged` per this role's sprint-wrap contract — the Retrospective
above is a **draft**; a human should skim it and propagate "Patterns to
carry forward" into `Implementation/Learnings.md`.
