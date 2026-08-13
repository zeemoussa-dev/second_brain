---
id: SPRINT-006
title: Meeting notes captured from calendar sync
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "other — ESC-002 (live-confirmed EntryID-stability risk, ADR-008's own pre-flagged risk) + standard retro-harvest flag"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"            # YYYY-MM-DD when status → Done
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

# SPRINT-006 — Meeting notes captured from calendar sync

## Sprint Goal

Stand up REQ-SB-08's calendar-capture pipeline end to end — a new Outlook
Calendar read primitive, Meeting-note file-I/O, customer derivation from
attendees, attendee Person-note linking (reusing REQ-SB-10's mechanism),
and scheduler wiring — so every calendar meeting shows up in the vault the
same automatic, no-duplicate way email already does.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-08-US-01` is the only
  `Ready`, ungrouped story whose scope is this pipeline; none of the other
  three stories eligible this pass (`REQ-SB-16-US-01`, `REQ-SB-17-US-01`,
  `REQ-SB-12-US-01`) share a dependency edge or a code surface with it —
  it touches `app/data_access/outlook_com.py` (new calendar-read
  function), a new `app/business/meeting_classification.py`, and the
  scheduler wiring, none of which any other Ready story touches. Its five
  tasks form one acyclic chain (`T01`/`T02` independent → `T03` depends on
  both → `T04`/`T05` both depend on `T03` only) implementing one cohesive
  capability (fetch → derive customer → write note → link customer hub +
  attendee Person notes → dedup) — not splittable across sprints without
  inventing an artificial cross-sprint edge through the middle of a single
  dependency chain (would contradict hard rule 7).
- **Why NOT combined with REQ-SB-16-US-01/REQ-SB-17-US-01:** this story is
  explicitly larger and more novel than either of them — its own
  decomposer note calls out "5 tasks, larger than REQ-SB-10/14's 4-task
  shape... driven by the new calendar-fetch layer," and it is the only
  story this pass introducing a genuinely new external-integration
  surface (Outlook Calendar COM read, not yet built anywhere in this
  codebase) plus its own live-Outlook, live-vault verification surface
  (T05's manual-trigger endpoint exercises 10 of 11 locked ACs against the
  real calendar). Pairing it with either of the other two reuse-only
  extension stories would push a single sprint past every prior sprint's
  task count (would be 7–9 tasks vs. this session's established ~4-task
  precedent) while mixing a brand-new-integration risk profile with two
  low-risk, direct-extension stories — kept separate for a cleaner,
  lower-risk working context per story.
- **Sizing estimate:** ~5 tasks, M (medium) — one size step up from the
  ~4 tasks/S shape `Implementation/Learnings.md`'s calibration precedent
  (SPRINT-001/002/004) established for "data-access primitives → business
  orchestration → downstream wire-ups" sprints, matching this story's own
  extra task (a wholly new calendar-read primitive layer that those
  precedents didn't need). No prior sprint this session has built a new
  external-integration read primitive from scratch, so this is treated as
  a fresh calibration point, not assumed identical to the S-sized
  precedents.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-006 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-08-US-01](../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md) | Meeting notes captured from calendar sync, classified by customer via attendees, and linked to Person notes | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` section confirms it is not hard-blocked:
  the recurring-schedule infrastructure (`REQ-SB-07-US-01`, Done), the
  attendee Person-note mechanism (`REQ-SB-10-US-01`, Done), and the
  customer-hub-linking primitives (`REQ-SB-14-US-01`, Done) all already
  exist and work. The one genuinely new dependency (a calendar-read
  function in `app/data_access/outlook_com.py`) is built as this story's
  own `T01`, not a separate blocking story.
- `T05` (the manual-trigger endpoint used for the bulk of this story's live
  verification) runs against the user's real, live Outlook calendar and
  Obsidian vault (`VAULT_PATH`) — no fixture/mock environment, same
  precedent as SPRINT-001/002/004/005. Not a sprint-blocking dependency,
  noted here for the coder's awareness going into `/implement-sprint`.
- `ADR-008` (the architect's calendar-read/dedup-key/customer-tie-break/
  scheduler-wiring/self-email decisions this story's tasks build against)
  was reviewed and approved by the operator 2026-08-11 — not an open
  blocker for this sprint.

---

## Out of Scope

- **REQ-SB-09** (To-Do Task Capture Pipeline) — a separate, not-yet-specced
  sibling story, per the story's own Non-Goals.
- **Any Second Brain UI surfacing of Meetings data** — REQ-SB-11
  (Observability) is the future story that would surface capture-run
  history/status; REQ-SB-12-US-02's Calendar drill-down (a separate,
  not-yet-grouped story) is what will eventually render this pipeline's
  output in the app, not built here.
- **Collapsing a recurring meeting series into one note**, or a
  `Meeting`-type manual-entry Obsidian template — both explicitly rejected/
  deferred per the story's own Non-Goals.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no change beyond what the architect pass already recorded
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-008` already recorded and `Accepted`; confirmed. No superseding ADR was authored this pass for `ESC-002` — that decision is left to the human (see `REVIEW-QUEUE.md`)
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

- **Estimated:** ~5 tasks, M — **Actual:** 5 tasks, M (matched exactly) —
  **Takeaway:** the sprint's own pre-build calibration note (one size step
  up from the ~4-task/S precedent, justified by the genuinely new
  calendar-fetch layer) held precisely. This is the first sprint to build
  a brand-new external-integration read primitive from scratch, and it
  still landed exactly at the estimated size — worth trusting the "new
  integration layer = +1 task" heuristic for future similar work (e.g.
  REQ-SB-09's To-Do capture, which will add its own new read primitive).

### What worked

- **Porting a working precedent instead of designing fresh** —
  `list_calendar_events` (T01) ported agentic-map's COM mechanics
  (`GetDefaultFolder(9)`, `IncludeRecurrences = True`) near-verbatim per
  ADR-008/`MEMORY.md`'s integration-sourcing precedence; it worked
  correctly against the real live Outlook client on the first live smoke
  check, no COM-syntax trial-and-error needed.
  Extended into confirming a config value the same way: rather than guess
  or ask blind, a one-time **read-only** Outlook COM probe
  (`Namespace.CurrentUser`) determined the real `self_email` value
  empirically before it was ever written to `.env` — turned a "no safe
  default, must ask the human" situation into a self-verifying one,
  without violating ADR-008's own rejection of a *dynamic runtime* lookup
  (the distinction: one-time COM-assisted determination of a static
  config value vs. sourcing the value dynamically at every call).
- **Concentrating live verification into one endpoint task (T05), per
  REQ-SB-10-US-01-T04's own established shape** — 10 of 11 locked ACs were
  exercised end-to-end against real production data (38 real Meeting notes
  correctly captured, classified, and linked) in one coherent verification
  pass, with throwaway calendar events created only for the two scenarios
  (AC-03, AC-07) the real calendar genuinely had no natural example of —
  same fallback discipline `REQ-SB-10-US-01-T04` established, confirmed to
  generalize cleanly to a second capture pipeline.
- **Honestly-flagged risks in an ADR paying off when they materialize** —
  ADR-008's own Consequences section pre-named the EntryID-stability risk
  and pre-authorized exactly the right response ("superseding ADR, not a
  silent workaround") *before* it was ever observed live. When it did
  materialize during Scenario 9 verification, there was no ambiguity about
  what to do — write it up, don't patch it, point to the pre-existing
  Alternatives Considered section for the two remediation options. Writing
  known-unverified risks into an ADR's Consequences section up front is
  worth doing deliberately for any future new-integration ADR.

### What didn't work

- **A stray, orphaned dev-server process from an earlier session** was
  found already bound to port 8001 running stale (pre-this-sprint) code —
  had to be identified and stopped before a clean, code-accurate AC-10
  verification restart could happen. Not a sprint-specific problem, but a
  reminder that this project's dev-server processes don't get cleaned up
  automatically between sessions/sprints.
- **A smoke-test-script bug (not a `vault_writer.py` bug), logged in T02's
  own Implementation Log:** manually mangling a note's frontmatter for a
  "remove one key" smoke check via naive `splitlines()`/`"\n".join()`
  silently drops the trailing blank-line body separator `write_note()`
  relies on — the actual primitive was fine; the first manual-editing
  approach corrupted the fixture. Worth remembering for any future manual
  smoke-test editing of a generated note: use a surgical regex/string
  substitution that preserves exact structure, not a
  parse-lines/rejoin round-trip.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **COM-assisted, one-time determination of a "no safe default" config
  value** — when a required config value (like `self_email`) has no safe
  default and the ADR has already rejected sourcing it *dynamically* at
  runtime, a one-time, read-only probe of the same external system (here,
  Outlook's `Namespace.CurrentUser`) to determine *what static value to
  configure* is a legitimate middle path between guessing and blocking on
  a human question — as long as it's read-only, logged, and clearly
  distinguished from the rejected dynamic-lookup alternative.
- **Write down unverified integration risks in the ADR's Consequences
  section, with the exact required response pre-authorized** — this
  turned a potentially ambiguous "did I just find a bug, or is this
  expected?" moment during live verification into a clear, fast
  escalate-don't-patch decision (`ESC-002`). Apply to every future ADR
  that ports an external-system integration with any behavior the team
  hasn't personally stress-tested yet.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Naive `splitlines()`/`"\n".join()` round-tripping of a generated
  note's text during manual smoke-test editing** — silently drops
  structural whitespace (here, the blank-line body separator) that a
  targeted regex substitution would have preserved. Produces a false
  signal that a primitive is broken when the actual bug is in the test
  fixture setup.

### Open follow-ups

- **`ESC-002` — EntryID-stability-across-recurring-occurrences risk,
  confirmed live, needs a human decision** (superseding ADR vs. accepted
  known limitation) — filed in `ESCALATIONS.md` and `REVIEW-QUEUE.md`, not
  resolved by this sprint. Does not block this sprint's own `Done` status
  since every locked AC passed against real data available today.
- **REQ-SB-09 (To-Do Task Capture Pipeline)** inherits this sprint's
  "add one more call inside `run_capture_and_record_completion`" scheduler
  pattern (ADR-008 point 4, extending ADR-005) as its own established
  precedent — no new scheduled job, no new concurrency guard, when it is
  eventually specced.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for this grouping decision:
`REQ-SB-08-US-01`'s own dependency graph (five tasks, one acyclic chain,
`T01`/`T02` → `T03` → `{T04, T05}`) is honoured intact, not split across
sprints. Not oversized — five tasks is one step above this session's
~4-task precedent, directly justified by the story's own decomposer note
about the added calendar-fetch layer, and comparable in kind to
`REQ-SB-10-US-01`/`REQ-SB-14-US-01`'s already-Done single-story-sprint
precedents (SPRINT-002, folded into SPRINT-004). Not blocked — all five
tasks are `status: Ready`, the story itself is `status: Ready`, and its own
`## Dependencies` section confirms every upstream mechanism it reuses
(`REQ-SB-07-US-01`, `REQ-SB-10-US-01`, `REQ-SB-14-US-01`) is already `Done`.
No cross-sprint dependency was introduced (`depends_on_sprints: []`).
Single phase (P1) throughout. The story's `gate: flagged` (trigger-3,
ADR-008 creation) does not block this stage — the operator reviewed and
approved ADR-008 2026-08-11, per the pipeline's own ADR-flag-doesn't-halt
rule; resetting the story's `gate:` value is not this role's job. Advanced
`Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 5 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (`/implement-sprint`), 2026-08-11 — `status: Ready → Done`.**
All 5 tasks built and verified live against the real Outlook calendar and
Obsidian vault, in dependency order. All 11 of `REQ-SB-08-US-01`'s locked
ACs verified live. One genuine architectural finding (`ESC-002`) surfaced
during Scenario 9 verification and was escalated per ADR-008's own
pre-authorized path, not silently patched — full detail in
`ESCALATIONS.md` and the story's own Notes. `gate: flagged` set (this new
`ESC-002` finding, plus the standard retro-harvest flag) — does not block
this sprint's `Done` status, since every locked AC passed against real
data available today. `BACKLOG.md` updated (`REQ-SB-08` row and Sprint
Status table).
