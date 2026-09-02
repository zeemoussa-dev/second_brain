---
id: SPRINT-083
title: Migrate email-thread-capture and summarize-and-tag-threads write mechanics onto vault_manager.py
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint retro drafted for human skim + Learnings.md harvest; both stories individually carry their own already-disclosed scope-internal judgement calls, see REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-082]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-09-01
started: "2026-09-01"              # YYYY-MM-DD when status → In Progress
completed: "2026-09-02"            # YYYY-MM-DD when status → Done
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

# SPRINT-083 — Migrate email-thread-capture and summarize-and-tag-threads Write Mechanics onto vault_manager.py

## Sprint Goal

Migrate both Capture-side (`email-thread-capture`) and Enrich-side
(`summarize-and-tag-threads`) write mechanics onto the resynced
`vault_manager.py` engine — two independent, parallel migrations of two
different live production Skills, built on the same `SPRINT-082` foundation.

---

## Grouping Rationale & Sizing

- **Why grouped together:** `REQ-SB-87-US-02` and `REQ-SB-87-US-04` are a
  real, confirmed **diamond**, not a chain — both `US-02-T01` and
  `US-04-T01` `depends_on: [REQ-SB-87-US-01-T05]` directly (the same single
  upstream task, `SPRINT-082`'s own output), but neither depends on the
  other at all: read directly from each task file's own frontmatter, `US-02`
  is a straight 5-task chain (`T01→T02→T03→T04→T05`) migrating
  `email-thread-capture`'s five scripts, and `US-04` is a straight 4-task
  chain (`T01→T02→T03→T04`) migrating `apply_thread_review.py` — two
  different Skills, two different script files, zero shared files, zero
  cross edges between them. Per hard rule 7 ("dependency-linked stories go
  in the same sprint or in ordered sprints"), two stories that fan out from
  the SAME single prerequisite with no dependency on each other are the
  textbook case for building together in parallel within one sprint, once
  that shared prerequisite (`SPRINT-082`) is `Done` — mirroring this
  project's own already-established "a diamond stays one sprint" precedent
  (`SPRINT-049`'s `REQ-SB-55-US-01`), generalized here one level up from a
  single story's own task graph to two sibling stories sharing one
  upstream task.
  - Both stories also share the identical rollout-risk posture (the
    operator's own locked 100-email scratch-vault proving-phase rollout,
    both stories' own Constraints), the identical production-risk profile
    (each migrates a live, cron-backed pipeline — `email-delta-capture` and
    `job4-summarize-tag-threads` respectively), and the identical
    "mechanics migration, not a bugfix" framing — real cohesion beyond just
    the shared dependency edge.
- **Sizing:** 5 + 4 = 9 tasks, sized `L`. This sits exactly at this
  project's own largest confirmed-accurate sizing ceiling (`SPRINT-021`
  `REQ-SB-21-US-01`, `SPRINT-030` `REQ-SB-39-US-01`, both 9 tasks/L matched
  exactly at retro) — not exceeding it. Combining a third story here (e.g.
  folding in `US-03` or `US-05`) would push past that ceiling into
  genuinely oversized territory with no real precedent of an exact match;
  keeping this sprint at exactly `US-02` + `US-04` is the correct sizing
  call, not an arbitrary round number.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-083 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-87-US-02](../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md) | Migrate email-thread-capture's write mechanics onto vault_manager.py | P1 | Done (gate: flagged) — all 6 tasks Done (T01 2026-09-01, `ESC-061` resolved same-day; T02-T04 2026-09-02; T06 2026-09-02; T05 2026-09-02, real-vault retrofit + live cron cutover), all 9 locked ACs verified live; 3 disclosed scope-internal judgement calls at T05 (2 real bugs found+fixed live, see T05's own Implementation Log) |
| [REQ-SB-87-US-04](../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md) | Migrate summarize-and-tag-threads' write mechanics onto vault_manager.py | P1 | Done (gate: flagged) — all 4 tasks Done 2026-09-01, all 7 locked ACs verified live incl. real-vault retrofit-safety + cutover; 2 disclosed scope-internal judgment calls, see T04's own Implementation Log |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-082` (must be `Done` before
  `/implement-sprint` may start this sprint — `US-02-T01` and `US-04-T01`
  each `depends_on: [REQ-SB-87-US-01-T05]`, the Thread/RawMessage
  templates `SPRINT-082` authors).
- Internal task order (per the decomposer's own `depends_on`; the two
  stories' own chains are independent of each other and may build in
  either order or in parallel):
  - `US-02`: `T01` → `T02` → `T03` → `T04` → `T05` (the real-vault
    retrofit check + live cron cutover).
  - `US-04`: `T01` → `T02` → `T03` → `T04` (the real-vault retrofit check
    + live cron cutover).

---

## Out of Scope

- `REQ-SB-87-US-01` — built in `SPRINT-082`, this sprint's own
  prerequisite.
- `REQ-SB-87-US-03`/`US-05` — each reaches back into a specific task
  inside this sprint (`US-03-T03` → `US-02-T01`; `US-05-T01` →
  `US-04-T03`) and is sequenced after this sprint via `SPRINT-084`'s own
  `depends_on_sprints: [SPRINT-083]` edge, not folded in here (would push
  this sprint past its own 9-task sizing ceiling).
- Any change to either Skill's own real business-logic/judgment (Person-
  note dedup, company resolution, the section-ownership guard's real
  per-caller rules) — both stories' own Constraints keep this a mechanics
  migration only.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no new architectural fact this sprint (confirmed by both stories' own architect passes)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR this sprint
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-09-01)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made pairing `US-02` and `US-04` (the real `depends_on` edges, both
  the shared upstream edge into `SPRINT-082` and the absence of any edge
  between the two stories themselves, were read directly from the
  decomposer's own task frontmatter, never re-derived or guessed);
  `REQ-SB-87` is not `Draft`/unfinalised in the PRD; no ADR was created or
  changed by this pass; no `ESCALATIONS.md` entry was written by this
  pass; the sprint is not oversized (9 tasks sits exactly at, not past,
  this project's own confirmed ceiling); the `depends_on_sprints:
  [SPRINT-082]` edge this pass introduces is a **disclosed, honoured**
  edge matching two independent real task-level `depends_on` edges
  reaching back into that sprint, not a contradiction of the graph; the
  partition is unambiguous — given the real dependency fault line (both
  stories fan out from the same single upstream task, neither depends on
  the other, and no other pairing keeps every sprint within this
  project's own confirmed 6-9 task sizing band while also honouring every
  real edge), there is no equally-valid alternative grouping.
- Both stories in scope already carry `gate: clear` at the story level
  (both production-risk MUST-FLAG triggers were resolved directly by the
  analyst/architect before this pass — see each story's own Notes) — no
  flag to carry forward here, unlike `SPRINT-082`/`SPRINT-084`.
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 10 tasks, L (9 originally
  planned `T01`-`T05` x2 stories, plus one late-added `US-02-T06` for the
  real `direction`/recipient-type fields, decomposed mid-sprint once the
  requirement's own scope expanded 2026-09-02). Task count grew by
  exactly one task and stayed within the `L` sizing band — the extra
  task didn't push this sprint past this project's own previously-
  confirmed 9-task ceiling by a meaningful margin. Both stories' own
  real-vault retrofit + live cron cutover tasks (`US-02-T05`,
  `US-04-T04`) were, as anticipated by the sizing rationale, the heaviest
  by verification effort, not code volume.

### What worked

- **Diamond-shaped sprint grouping (two independent stories sharing one
  upstream prerequisite, zero edge between them) built cleanly in
  parallel with zero reordering** — `US-02` and `US-04` never touched a
  shared file, confirmed at close: the whole sprint closed with zero
  cross-story rework.
- **Reusing an already-established "mint-and-backfill on first touch"
  pattern a second time, across two DIFFERENT scripts in the SAME
  sprint** — `US-04-T01` (`apply_thread_review.py`) established it first
  for a Thread with no `id` field; `US-02-T05` reused the exact same
  shape (a real, live-confirmed second instance of the identical
  no-id-on-pre-migration-content problem) for `ingest_email.py`, closing
  a genuine live-found retrofit-duplication risk with zero new design.
- **Verifying a retrofit-safety assumption statically, in isolation,
  BEFORE running anything against real data** — a direct, scratch-copy
  `find_by_id`/`_find_by_title` check surfaced the Thread-duplication
  risk with zero real-vault exposure, before a single real write was
  attempted. This is what turned a potential real-data-corruption
  incident into a same-session, fully-controlled fix.
- **A real ~100-message retrofit against the live vault, with an
  explicit pre/post Thread-count and `.md`-count reconciliation**, gave
  a strong, independently-verifiable positive result (Thread count +5,
  exactly matching the 5 genuinely-new non-noise captures) rather than
  trusting each individual script's own reported JSON alone.

### What didn't work

- **A second real, pre-existing bug (`ingest_email.py`'s own missing
  `sys.stdout.reconfigure(encoding="utf-8")`) was only found by actually
  running the real ~100-message retrofit, not by any earlier task's own
  scratch-vault verification** — every prior task's own scratch samples
  happened not to include a subject with a character outside cp1252.
  This is the SAME bug class `list_recent_emails.py` had already fixed
  for itself weeks earlier in this same Skill; it should have been
  checked for explicitly (a quick grep for `sys.stdout.reconfigure` across
  every script in a Skill, once one script needs it) rather than
  rediscovered live during the final, real-data-touching task.
- **My own verification driver script hit this exact same
  Windows-cp1252-redirected-stdout class of bug on itself**, twice
  (once crashing mid-batch, requiring a resume-from-index re-run) —
  should have applied `sys.stdout.reconfigure(encoding="utf-8")` to any
  throwaway verification script from the start, not just the scripts
  under test, given this project's own already-documented
  `SPRINT-038` Antipattern on exactly this failure mode.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Before a retrofit/cutover task runs ANY write against real,
  pre-existing production data, statically verify the migrated code's
  own resolution mechanism (`find_by_id`-equivalent) actually recognizes
  that pre-existing data — in isolation, on a throwaway scratch copy,
  before the first real write** — this is what caught a genuine
  duplicate-creation risk with zero real-vault exposure in
  `REQ-SB-87-US-02-T05`, and should be a standing pre-flight step for
  any future "migrate a script from a hand-rolled identity scheme onto
  `vault_manager.py`'s id-based lookup" retrofit task, not something
  discovered by accident.
- **Once one script in a Skill needs `sys.stdout.reconfigure(encoding=
  "utf-8")` for real Unicode content, grep every OTHER script in that
  same Skill for the same gap immediately, rather than waiting for each
  one to independently crash on real data** — `list_recent_emails.py`
  fixed this for itself 2026-08-24; `ingest_email.py` carried the
  identical gap, undiscovered, for over a week until real retrofit data
  happened to trigger it.
- **A pre/post structural count (Thread-directory count, total `.md`
  count) reconciled against the exact expected delta is a strong,
  cheap, independent cross-check for any real-vault write task** —
  catches a duplication defect a script's own self-reported JSON summary
  alone could not.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a migrated script's own scratch-vault verification (built
  from a FRESH sample every time) has exercised the "resolve an
  ALREADY-EXISTING, pre-migration record" code path just because the
  script LOOKS idempotent** — every prior scratch-vault check in this
  exact sprint used freshly-pulled, never-before-seen email samples, so
  the "does this find a real record with no `id` field" path was never
  actually exercised until the real retrofit task ran. A migrated
  script's idempotency against ITS OWN prior output is not the same
  claim as its retrofit-safety against PRE-migration output.

### Open follow-ups

- `ADR-017` still awaits human review (standing flag, carried forward
  from `SPRINT-082`, not resolved by this sprint's own closure) — see
  `REVIEW-QUEUE.md`.
- Several disclosed scope-internal judgement calls from `US-02-T01`/
  `T02`/`T03`/`T06`/`T05` and `US-04-T04` still await human spot-check —
  see `REVIEW-QUEUE.md` for the full list, not repeated here.
- `email-capture-classifier`'s own deployed `SOUL.md` still documents
  `direction` as `"inbound"`/`"sent"` instead of the real
  `"received"`/`"sent"` values (`US-02-T06`'s own disclosed, non-blocking
  finding) — a future small fix, filed to `REVIEW-QUEUE.md`, not done by
  this sprint (out of every task's own `## Files to Modify`).
