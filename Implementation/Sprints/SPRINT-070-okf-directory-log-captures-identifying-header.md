---
id: SPRINT-070
title: Customer/Project log.md and captures.md carry an identifying header (BUG-028 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint close — retro drafted, awaiting human skim/harvest into Implementation/Learnings.md (normal at sprint close)."
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~1 task, XS"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
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

# SPRINT-070 — Customer/Project log.md and captures.md carry an identifying header (BUG-028 fix)

## Sprint Goal

Ship `BUGFIX-07-US-01` end to end: `create_okf_directory_baseline`/
`ensure_okf_directory_baseline` (`src/backend/app/data_access/vault_writer.py`)
write/backfill an identifying `# {name}` header onto Customer/Project
`log.md`/`captures.md`, mirroring `index.md`'s own already-`Accepted` header
convention, without disturbing any real content already appended to an
existing file.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-07-US-01` is the only
  `Ready`, ungrouped story this pass (confirmed by scanning every
  `Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`).
  The other `Ready` stories found this pass — `REQ-SB-42-US-01`,
  `REQ-SB-59-US-01`, `REQ-SB-75-US-01` — already carry a `sprint:` value
  (`SPRINT-039`, `SPRINT-059`, `SPRINT-069` respectively) and are excluded
  as "not ungrouped." The story has exactly
  one task, `BUGFIX-07-US-01-T01`, with `depends_on: []` — no dependency
  graph to honour, no ordering question, nothing to split.
- **No phase-mixing question:** `BUGFIX-07-US-01` carries no `phase:` — per
  `Pipeline.md` hard rule 8's bugfix exception, this sprint is exempt from
  phase homogeneity and is built standalone (`phase: ""` above, mirroring
  `SPRINT-005`/`SPRINT-016`/`SPRINT-064`/`SPRINT-065`/`SPRINT-066`'s own
  precedent for a single-bugfix-story sprint).
- **Sizing estimate:** ~1 task, XS. One small, shared-primitive-scoped fix
  (`vault_writer.py`'s `create_okf_directory_baseline`/`ensure_okf_
  directory_baseline`, plus four mechanical wrapper call-site updates in the
  same file); the decomposer's own task file already confirms this fits one
  working session easily (mirrors `SPRINT-018`/`SPRINT-047`/`SPRINT-066`'s
  own "~1 task, XS" precedent for a small, well-scoped single-task batch).
  No task needs its own sprint or a cross-sprint `depends_on_sprints` edge.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-070 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-07-US-01](../UserStories/BUGFIX-07-US-01-okf-directory-log-captures-identifying-header.md) | Customer/Project `log.md`/`captures.md` carry an identifying header, mirroring `index.md`'s own convention (BUG-028 fix) | — (bugfix) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- No external blocker — `create_okf_directory_baseline`/`ensure_okf_
  directory_baseline` and all four Customer/Project wrapper functions
  (`REQ-SB-54-US-01`, `ADR-042`) are already `Done` and already live; this
  fix only adds a header write to two already-existing code paths inside
  them.
- **Note carried from the story:** verification should run against at
  least one genuinely new Customer or Project (fresh-creation facet) and at
  least one already-existing real Customer folder from the live vault whose
  `log.md` already carries real appended content, if one exists, to
  exercise the backfill/content-preservation facet against real data rather
  than a synthetic fixture alone.

---

## Out of Scope

- Adding `log.md`/`captures.md` to `vault_indexing`/search/backlinks/the
  Vault graph — they stay deliberately excluded, per `BUG-028`'s own note.
- Changing `index.md`'s own already-correct header/listing behavior.
- Changing `append_person_note_update_line`'s own append contract.
- Retrofitting `move_okf_directory`, `okf_directory_paths`, or any other
  OKF-directory primitive not named in `BUGFIX-07-US-01-T01`.
- Any UI change — confirmed no screen is affected (`BUG-028`'s own
  "Screen \ route: N/A").

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      — n/a, no architectural fact changed (the architect's own
      `BUGFIX-07-US-01` correction bullet was already recorded at
      `/plan-tasks`, before this build)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no
      new ADR (confirmed by both the architect and analyst passes)
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

- **Estimated:** ~1 task, XS — **Actual:** 1 task, XS — **Takeaway:** on
  the money. A single shared-primitive fix with four mechanical wrapper
  call-site updates and a docstring correction really was one small,
  single-file, single-session change; the story/task's own pre-confirmed
  fix shape (agreed with the operator before capture) meant zero
  discovery cost during the build itself.

### What worked

- Reusing an already-`Accepted` convention (`index.md`'s own bare
  `# {name}` header half) instead of inventing a new header shape kept
  the fix unambiguous end to end — analyst, architect, decomposer, and
  coder all converged on the exact same header string with zero
  back-and-forth.
- One shared helper (`_write_or_backfill_identifying_header`) covering
  both the fresh-creation and backfill cases, called identically from
  both `create_okf_directory_baseline` and `ensure_okf_directory_baseline`,
  meant the "never duplicate the header-writing logic" constraint was
  satisfied by construction rather than by discipline.
- Reading `append_person_note_update_line`'s three real call sites before
  writing the backfill-detection rule (`first line doesn't start with
  "# "`) turned what could have been a risky heuristic into a
  structurally-confirmed one — real production line shapes were checked,
  not assumed.

### What didn't work

- The live vault turned out to have zero real Customer/Project `log.md`/
  `captures.md` files with any actual appended content — every one of the
  26+ real Customer folders' `log.md`/`captures.md` is still genuinely
  empty. The story's own `## Dependencies` → External note anticipated
  wanting to verify against real pre-existing content, but that facet
  could only be exercised against the synthetic throwaway directory this
  pass. Not a build failure, just a verification-coverage gap the story
  couldn't have known about until this pass ran the real check.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Grep-confirm real call sites before writing a detection heuristic** —
  when a fix's correctness depends on "no existing real content looks
  like X," directly grep/read every real writer of that content first
  (as this task did for `append_person_note_update_line`'s three call
  sites) rather than reasoning about it in the abstract; turns an assumed
  heuristic into a structurally-confirmed one.
- **One shared helper for symmetric create/ensure paths** — when a
  `create_*`/`ensure_*` pair must apply the identical fix on both the
  fresh-creation and top-up code paths, write one small helper the
  create_* path also calls (not just ensure_*), since a partial/
  interrupted prior create_* run can leave the same already-exists-but-
  unfixed state ensure_* is meant to repair.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Don't mutate real production data "just to exercise a real-data
  facet" when there's nothing real to preserve** — this task deliberately
  declined to run the fix against a real, content-free Customer folder
  once it confirmed (by reading, not writing) that no real candidate
  actually carried content worth protecting; touching production data
  for zero marginal verification signal is a bad trade even when the
  task's own Tests block would technically allow it.

### Open follow-ups

- None filed. `REQ-SB-74`'s own already-planned backfill pass will
  naturally apply this header to every real Customer/Project directory's
  `log.md`/`captures.md` the next time its `ensure_*` path runs, per the
  story's own `## Dependencies` note — no separate one-off backfill
  script was created or is needed.

---

## Gate breadcrumb

`gate: clear` 2026-08-19 — no MUST-FLAG trigger fired during grouping: exactly
one `Ready`, ungrouped story in scope (confirmed by scanning all
`Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`; the
three other `Ready` stories found — `REQ-SB-42-US-01`, `REQ-SB-59-US-01`,
`REQ-SB-75-US-01` — all already carry a `sprint:` value and were excluded as
not ungrouped), its single task has `depends_on: []` (no
graph edge to honour or contradict), the story carries no `phase:` per the
bugfix exception (hard rule 8) so no phase-mixing question arises, the story
is not oversized (decomposer's own gate already confirmed single-file-scoped),
it is not blocked, and no cross-sprint dependency was introduced (this sprint
has no `depends_on_sprints`). Partition is unambiguous — one story, one
sprint. Advanced `Draft → Ready`.

`gate: flagged` 2026-08-19 (coder pass, sprint close) — `BUGFIX-07-US-01`
and its single task `BUGFIX-07-US-01-T01` are both `Done`; both locked ACs
(`AC-01`, `AC-02`) verified via manual mode against the real
`vault_writer` functions and the real, configured vault (full detail in
the task's own `## Implementation Log`); `BUG-028` flipped
`In Sprint → Closed` in both `BUGS.md` and `BACKLOG.md`'s `## Bugs`
mirror. Flagged per the standing sprint-close convention — not a
MUST-FLAG failure — so the human can skim `## Retrospective` above and
propagate "Patterns to carry forward"/"Antipatterns to avoid" into
`Implementation/Learnings.md`. Advanced `In Progress → Done`.
