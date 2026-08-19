---
id: SPRINT-062
title: Meeting Capture Redesign — One-Time/Recurring Split, People Auto-Extraction Nested Under Customer
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint complete, all ACs verified live. gate: flagged so the human skims this Retrospective and propagates patterns into Implementation/Learnings.md (coder drafts, does not write Learnings.md itself), and spot-checks the disclosed scope-internal judgement calls + ESC-049 (my_day.py regression, non-blocking, disclosed) recorded across T01/T02/T03's own Implementation Logs. The pre-existing ADR-048 trigger-3 human-review flag (shared across this whole 4-story batch) also remains open, tracked in REVIEW-QUEUE.md's existing entry."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: ["SPRINT-060", "SPRINT-061"]  # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-18"                        # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-062 — Meeting Capture Redesign — One-Time/Recurring Split, People Auto-Extraction Nested Under Customer

## Sprint Goal

Split Meeting capture into a one-time-note vs. one-ongoing-note-per-series
shape (a new dated `## History` entry per recurring occurrence, synthesized
from both calendar logistics and the linked Thread), drop raw calendar
boilerplate entirely, and close the silent no-email-attendee gap by
auto-creating a real Person note — nested under the attendee's primary
Customer — for every real attendee.

---

## Grouping Rationale & Sizing

- **Why a single-story sprint.** All 3 tasks belong to one story
  (`REQ-SB-71-US-03`) with one Definition of Done and one architecture
  scope (`architecture.md` → "Meeting Capture Redesign — One-Time/Recurring
  Split" + "People — Nested Under Primary Customer"). Graph read directly
  from each task file's own `depends_on:` frontmatter:
  - `T01` (one-time vs. recurring split) — `depends_on:
    [REQ-SB-71-US-01-T01, REQ-SB-71-US-02-T02]` — two real, hard
    cross-story edges into this batch's other two sibling stories.
  - `T02` (`## History` synthesis) — `depends_on: [T01,
    REQ-SB-71-US-02-T05]` — a further real, hard cross-story edge.
  - `T03` (People nested under Customer) — `depends_on: [T01]` only — no
    edge into `REQ-SB-71-US-02` (confirmed by the decomposer's own direct
    repo-wide search: `ensure_person_note`'s public signature is
    unchanged, so `email_classification.py`'s existing calls need zero
    modification).
  - Acyclic, all `phase: P1`.
- **Why sequenced strictly BEHIND both `SPRINT-060` AND `SPRINT-061`, not
  merged into either:** this is the clearest-cut sequencing case in the
  whole batch — `T01` depends directly on BOTH
  `REQ-SB-71-US-01-T01` (the section-ownership guard, `SPRINT-060`) AND
  `REQ-SB-71-US-02-T02` (the Thread note-discovery generalization,
  `SPRINT-061`) at once, and `T02` additionally depends on
  `REQ-SB-71-US-02-T05` (`synthesize_thread` — this story's own `##
  History` entry literally reads that function's real, regenerated `##
  Summary` output via `read_body_section`). Per `Implementation/
  Pipeline.md` hard rule 7, a story with hard `depends_on` edges into TWO
  other stories must either share a sprint with BOTH of them, or be
  ordered strictly after both — sharing one sprint with both would
  recreate the oversized (12-13-task) single-sprint risk `SPRINT-061`'s
  own `## Notes` already rejected, so ordering is the correct call here,
  not a coin-flip.
- **Why `T03` (People) isn't split into its own, earlier, less-blocked
  sprint** even though it only needs `T01`, not `REQ-SB-71-US-02`: it
  shares `classify_recent_meetings` — the SAME function `T01` rewrites —
  with `T01` itself (the decomposer's own explicit reasoning: sequencing
  `T03` after `T01` "avoids two tasks editing the same function's own body
  concurrently in conflicting ways"). Splitting it into a separate sprint
  would not reduce this sprint's real dependency floor (still gated on
  `SPRINT-061` via `T01`/`T02`) while adding a needless extra sprint file
  for one task with no independent value once separated from `T01`'s own
  rewritten function body.
- **Sizing estimate:** ~3 tasks, S — matches this project's own repeatedly
  confirmed "~3 tasks, S" bucket (`SPRINT-023`, `SPRINT-024`, `SPRINT-050`,
  `SPRINT-053`, `SPRINT-059`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-062 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-71-US-03](../UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md) | Meeting Capture Redesign — one-time/recurring split, frontmatter-only logistics, People auto-extraction from attendees (nested under Customer) | P1 | Done |

**Tasks in scope** (dependency order): `T01` (depends on
`REQ-SB-71-US-01-T01` and `REQ-SB-71-US-02-T02`, both from earlier sprints)
→ `T02` (depends on `T01` and `REQ-SB-71-US-02-T05`) and `T03` (depends on
`T01` only) may build in either order once `T01` is `Done`.

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-060` AND `SPRINT-061` — both must be
  `Done` before this sprint starts (`T01` hard-depends on
  `REQ-SB-71-US-01-T01` from `SPRINT-060` and `REQ-SB-71-US-02-T02` from
  `SPRINT-061`; `T02` additionally hard-depends on `REQ-SB-71-US-02-T05`
  from `SPRINT-061`), per `Implementation/Pipeline.md` hard rule 9.
- **External:** the real, live Outlook calendar this pipeline captures
  from.

---

## Out of Scope

- Email capture, the Thread raw/distilled split, and the Files/OKF
  companion convention — `SPRINT-061`'s own scope entirely; this sprint
  only READS that sprint's new Thread shape for `## History` synthesis.
- Section-ownership enforcement itself and vault base provisioning —
  `SPRINT-060`'s own scope.
- Scheduler wiring (explicitly excluded per the story's own `##
  Non-Goals`).
- Backfilling already-captured Meeting/People notes onto the new shapes.
- Archiving the dropped raw calendar-invite boilerplate anywhere —
  deliberate, operator-authorized deletion, not an oversight.
- Fixing Meeting Cockpit's own pre-existing series/`## History` regression
  risk — disclosed, deliberately left as a separate follow-up (story's own
  `## Non-Goals`).
- Person's own `## Glimpse`/`## Personal Notes` body redesign — explicitly
  out of scope for this batch per the architect's own addendum.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already appended at `/plan-tasks` (`ADR-048`), unchanged this pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created this pass (`ADR-048` already exists from `/plan-tasks`, still awaiting the human review recorded in `REVIEW-QUEUE.md`)
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

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S — exact match, the
  FOURTH consecutive time this "~3 tasks, S" shape has landed precisely
  on estimate (`SPRINT-023`, `SPRINT-024`, `SPRINT-050`, now `SPRINT-062`)
  — even though this sprint's own real verification effort (live Outlook
  data exhaustively scanned for edge cases, two disclosed monkeypatch
  fixtures engineered and fully cleaned up) was noticeably heavier than a
  typical 3-task/S sprint, task COUNT stayed exactly as sized.

### What worked

- Reading the task's own more precise End-State text as the tie-breaker
  when it disagreed with the story's own broader Scenario prose on a
  narrow mechanical point (which frontmatter fields survive) — the
  `SPRINT-049` Learnings precedent held up cleanly a further time.
- Live-probing the real Outlook COM body content directly (a small,
  disposable diagnostic script) BEFORE writing the `teams_link`/`dial_in`
  regex extraction — this caught the real invite-footer shape (a "Join:
  <url> <safelinks-redirect>" line, a `<tel:...>` machine-readable phone
  reference) precisely on the first attempt, verified against 15+ real,
  varied real invites before committing to the pattern.
- A single real recurring series with 3-4 already-scheduled occurrences
  landing inside the default capture window turned out to be an
  extremely strong, single-call proof of `AC-02`'s own "same note,
  multiple entries, file count unchanged" claim — no artificial waiting
  or engineering needed for that half of the AC.
- Scoped, disclosed, real-endpoint monkeypatching of ONLY the external
  Outlook-COM boundary (never the capability under test itself) — via
  Starlette's `TestClient`, a genuine HTTP call through the real FastAPI
  route — proved to be the right tool a SECOND time this batch
  (`SPRINT-050`'s own Compass-model-factory-stub precedent) for a
  DIFFERENT external dependency (live calendar data) that genuinely
  couldn't be arranged to produce a specific real-world condition
  (a no-email attendee; a not-yet-real future occurrence) on demand.
  Always paired with full, verified cleanup of every fixture artifact.

### What didn't work

- The first full server run (triggered by `ADR-005`'s own unconditional
  app-start capture job, MEMORY.md's already-known behavior) hung for
  several minutes on a LATER, unrelated pipeline leg (not this sprint's
  own meeting-capture code, which had already completed correctly and
  produced real, verified output) — CPU usage flatlining was the
  reliable signal that distinguished a genuine hang from real, ongoing
  Compass/Outlook work; killed cleanly, no orphaned processes, restarted
  for controlled testing. Worth watching for on any future session that
  restarts this app against the real, live mailbox.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **When a real-world precondition an AC's own Test step describes
  (a specific attendee/customer/date shape) genuinely does not exist in
  the current live data — confirmed by an exhaustive, disclosed direct
  scan, not assumed — verify via a scoped, disclosed monkeypatch of ONLY
  the external, uncontrollable data-source boundary, called through the
  REAL endpoint (e.g. Starlette's `TestClient` against the real FastAPI
  route), never a raw internal-function bypass of the capability itself.
  Always fully clean up every fixture/engineered artifact afterward and
  confirm the cleanup (e.g. a vault-wide `*fixture*` scan returning zero
  matches) before considering the task done.** Extends `SPRINT-050`'s own
  "scoped monkeypatch of an external dependency" precedent to a SECOND
  external boundary (live Outlook calendar data, not just the Compass
  model factory).
- **A single batched capture call against real, already-scheduled
  recurring occurrences can independently prove BOTH halves of a
  "second occurrence appends, doesn't duplicate" AC in one pass** — no
  need to force two separate calls when the real calendar already has
  multiple in-window occurrences of the same series.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Don't assume every field named in a sibling AC's own prose (e.g.
  Scenario 1's "frontmatter carries only X, Y, Z") is a literal,
  exhaustive enumeration of every frontmatter key a note will ever
  carry** — cross-check against the task's own more precise End-State
  text and this app's own established cross-cutting dependencies (here,
  `customer`/`type`/`tags` are relied on by several other, unrelated
  modules) before treating a Scenario's own illustrative list as a
  literal contract to strip everything else.

### Open follow-ups

- `ESC-049` (`ESCALATIONS.md`, `Open`) — `my_day.py::list_calendar_
  items` silently excludes every new-shape Meeting note from its own
  7-day window (reads `subject`/`start`, both now dropped) — a real,
  disclosed, non-blocking regression, left as a follow-up.
- `ESC-048` (`ESCALATIONS.md`, `Open`, inherited from `SPRINT-061`) —
  `email-capture-pipeline` remains deliberately `supervised`; unrelated
  to this sprint's own scope, left exactly as `SPRINT-061` left it.
- Fixing `meeting-cockpit.html`'s own pre-existing series/`## History`
  regression risk (disclosed in this story's own `## Non-Goals`,
  unchanged by this pass) — a separate, deliberate follow-up.
- The `ADR-048` human-review flag (shared across `SPRINT-060`/`061`/
  `062`) remains open regardless of this sprint's own completion.

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single-story sprint,
sequenced strictly behind BOTH `SPRINT-060` and `SPRINT-061` via recorded
`depends_on_sprints` edges, per three real, hard task-level dependencies
(`T01` → `REQ-SB-71-US-01-T01` and `REQ-SB-71-US-02-T02`; `T02` →
`REQ-SB-71-US-02-T05`) confirmed by direct reading of the task files. This
is the tightest-constrained story in the batch — it is the only one with
hard edges into BOTH sibling stories at once — which makes "ordered
sprints, strictly sequenced" the only reading consistent with
`Implementation/Pipeline.md` hard rule 7 once the batch was split at all
(the alternative, one 12-13-task sprint, is rejected in `SPRINT-061`'s own
`## Notes` as a real, disclosed oversized-sprint risk). See `SPRINT-060`'s
own `## Notes` for the full single-vs-multi-sprint reasoning across the
whole 4-story `ADR-048` batch.

**Why `gate: flagged` (MUST-FLAG trigger 5 — cross-sprint dependency
introduced):** this sprint's own `depends_on_sprints: ["SPRINT-060",
"SPRINT-061"]` is a cross-sprint dependency this pass had to introduce.
Flagged for human visibility per this role's own MUST-FLAG list, even
though the sequencing is the only reading the real task graph supports
once the batch is split into more than one sprint — not a genuinely
ambiguous call. No other MUST-FLAG trigger fired: not oversized on its own
(3 tasks, S); no blocked story; the partition is unambiguous given
`SPRINT-060`/`SPRINT-061`'s own already-decided split. The story's own
`gate: flagged` (architect's `ADR-048` flag) stays on the STORY, unchanged
— tracked in `REVIEW-QUEUE.md`'s existing 4-story `ADR-048` entry, not
duplicated here.

gate: flagged 2026-08-18 (product-owner) — trigger 5 (cross-sprint
dependency introduced). See `REVIEW-QUEUE.md` for the human-facing entry.
Sprint stays `status: Draft` until the human reviews the sequencing (and,
separately, `ADR-048` itself).

---

**Coder closing note (2026-08-18, `/implement-sprint SPRINT-062`):** the
cross-sprint-dependency flag above is satisfied — both `SPRINT-060` and
`SPRINT-061` are `Done` — and the operator's own directive to proceed
with this sprint is recorded in this sprint's own frontmatter `gate_
reason` history. All 3 tasks built and all 7 locked ACs verified live;
`status: Done`, `completed: 2026-08-18`. `gate` stays `flagged` — see the
`## Retrospective` above and the frontmatter `gate_reason` for what the
human should skim/harvest/spot-check on this pass (the Retrospective
itself; each task's own disclosed scope-internal judgement calls;
`ESC-049`). The pre-existing `ADR-048` human-review flag (shared across
this whole 4-story batch) remains separately open, unaffected by this
sprint's own completion — see `REVIEW-QUEUE.md`.
