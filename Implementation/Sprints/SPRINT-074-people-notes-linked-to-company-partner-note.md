---
id: SPRINT-074
title: People Notes Retroactively Linked to Their Real Company/Partner Note
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-073]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: ""                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-074 — People Notes Retroactively Linked to Their Real Company/Partner Note

## Sprint Goal

Make the already-shipped, already-working retroactive Person↔Company/Partner
linking mechanism reliably reachable via two real, durable trigger points —
instant on a company's status changing, and self-healing on
`SPRINT-073`'s own scheduled Company and Partner Building pass.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 4 tasks belong to
  `REQ-SB-77-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "People Notes Retroactively Linked to Company/
  Partner"). Graph read directly from each of the 4 task files' own
  `depends_on:` frontmatter:
  - `T01` (`relink_people_for_thread_paths` new function) — `depends_on:
    []`, root.
  - `T02` (instant hook — `finalize_company_review` retarget) —
    `depends_on: [T01]`.
  - `T03` (scheduled self-heal, verification-only) — `depends_on: [T01,
    REQ-SB-79-US-01-T02]`.
  - `T04` (live verification, Scenarios 1-5/7) — `depends_on: [T01]`.
  - **Acyclic** — `T01` is the one shared root; `T02`/`T03`/`T04` each
    depend on it, no back-reference. All 4 tasks carry `phase: P2`
    (matching the parent story) — no phase mixing.
- **Why sequenced behind `SPRINT-073`, not combined with it:** confirmed by
  direct reading of `T03`'s own `depends_on` frontmatter that this story
  carries one REAL, decomposer-recorded cross-story edge into
  `REQ-SB-79-US-01` — `T03` depends on `REQ-SB-79-US-01-T02` (the task that
  creates `run_company_partner_building_pass()`). `T03`'s own task file is
  explicit this is not a soft ordering preference: "This task cannot start
  before `REQ-SB-79-US-01-T02` is `Done` — `run_company_partner_building_
  pass()` does not exist before then. This is a real, disclosed cross-story
  dependency... not a soft sequencing preference." Per `Implementation/
  Pipeline.md` hard rule 7, this dependency must be honoured — either same
  sprint or ordered sprints with a recorded `depends_on_sprints` edge.
  Choosing ordered sprints over combining, for two real, disclosed reasons:
  1. **A genuine, not artificial, live-verification boundary.** `T03`'s own
     Tests block requires a real, direct call to `run_company_partner_
     building_pass()` to prove Scenario 6b's own self-healing outcome — that
     function's own body is `SPRINT-073`'s own `T02` deliverable. Mirrors
     this project's own established `SPRINT-011`→`SPRINT-012`,
     `SPRINT-025`→`SPRINT-026`, and `SPRINT-049`→`SPRINT-050` precedent
     (`Implementation/Learnings.md`, `SPRINT-049`: "sequence a downstream
     story strictly behind its upstream one via `depends_on_sprints`,
     rather than combining into one oversized sprint, when the downstream
     story's own Tests block requires the REAL, running output of the
     upstream story").
  2. **Sizing ceiling.** Combined, the two stories would total 10 tasks —
     past this project's own largest-ever confirmed-accurate single-sprint
     ceiling (`SPRINT-021`/`SPRINT-030`/`SPRINT-063`, 9 tasks/L, all three
     exact matches at retro), with no sizing precedent to calibrate a
     10-task working context against — a real, avoidable risk to "fits in a
     single working context," not a hypothetical one.
  Kept as two ordered sprints, not two flagged-ambiguous options — the
  live-verification boundary plus the sizing ceiling make this a reasoned
  sizing + dependency-shape call, not a genuinely ambiguous partition
  (mirroring `SPRINT-049`'s/`SPRINT-050`'s own identical framing). `T01`,
  `T02`, and `T04` have NO dependency on `SPRINT-073` at all and could in
  principle build ahead of it — but a story is not split across sprints;
  the whole story sequences behind the one task (`T03`) that genuinely needs
  `SPRINT-073`'s own output, consistent with this project's own "a sprint's
  scope is a whole story, not a partial one" convention.
- **Sizing estimate: ~4 tasks, S.** Matches this project's own repeatedly-
  confirmed 4-task/S shape (`SPRINT-019`, `SPRINT-025` — both exact matches
  at retro per `Implementation/Learnings.md`), consistent with the story's
  own Notes ("2 starting tasks, smaller than any comparable Librarian-family
  story to date — the mechanism this story exercises already exists; the
  new work is a reach/trigger promotion plus verification, not a new
  mechanism build").

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-77-US-01's own
frontmatter now carries sprint: "SPRINT-074". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-77-US-01](../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md) | People Notes Retroactively Linked to Their Real Company/Partner Note | P2 | Ready |

**Tasks in scope** (dependency order): `T01` (root) → `T02`/`T04` (need
`T01`) → `T03` (needs `T01` AND `SPRINT-073`'s own `T02`, so it necessarily
builds last within this sprint, after `SPRINT-073` reaches `Done`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-073` (`REQ-SB-79-US-01`) — must be `Done`
  before this sprint can start (hard rule 9; `/implement-sprint` refuses
  otherwise). `T03` cannot be built OR verified until `SPRINT-073`'s `T02`
  is real, shipped code — its own Tests block requires the actual, running
  `run_company_partner_building_pass()`.
- **Related, non-blocking:** `REQ-SB-76-US-01` (Company Review,
  `SPRINT-072`, `In Progress`) — `T02`'s own instant hook retargets
  `finalize_company_review`, which already exists in the codebase today
  regardless of `REQ-SB-76-US-01`'s own story status (confirmed directly in
  `T02`'s own Context/Notes) — no hard dependency on `SPRINT-072`.
- **External:** none new.

---

## Out of Scope

- The Librarian's own two-sub-pipeline split — `REQ-SB-79`, `SPRINT-073`,
  sequenced ahead of this sprint.
- Grouping/color-coding the Pending Approvals list by proposal type —
  `REQ-SB-78`, `SPRINT-075` (fully independent).
- Rebuilding or changing the matched-company linking mechanism itself
  (`ensure_person_note`, `find_matching_customer`/`find_matching_partner`,
  `build_person_tags`) — the story's own disclosed Non-Goal.

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact (no change expected — already updated at `/plan-tasks` under "People Notes Retroactively Linked to Company/Partner")
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` (none expected — no new ADR created for this story)
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

- **Estimated:** ~4 tasks, S — **Actual:** _(tasks / effort)_ — **Takeaway:** _(over/under, why)_

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

---

## Notes

**Sprint assembled 2026-08-19 (`/plan-sprints`).** `REQ-SB-77-US-01` enters
`/plan-sprints` `status: Ready`, `gate: clear` (the operator's own live
resolution of the analyst's earlier trigger-8 flag, recorded in the story's
own frontmatter `gate_reason`).

**Gate: `gate: clear` 2026-08-19.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone, single-story
grouping and the sequencing behind `SPRINT-073` are both read directly off
the decomposer's own recorded `depends_on` edge on `T03` (confirmed by direct
reading, not guessed); (2) `REQ-SB-77` is not `<!-- Draft -->`/unfinalised;
(3) product-owner does not write ADRs — none created or changed by this pass;
(4) no new `ESCALATIONS.md` entry — `ESC-057` is a pre-existing, standing
entry this pass does not reopen or duplicate; (5) not oversized (4 tasks, S,
matching two prior confirmed-accurate 4-task/S precedents,
`SPRINT-019`/`SPRINT-025`); not a blocked story — every task is `status:
Ready`, the real upstream need is recorded as a genuine `depends_on_sprints:
[SPRINT-073]` edge, directly reflecting the decomposer's own recorded
`REQ-SB-79-US-01-T02` cross-story edge on `T03` — not an artificial edge
this role invented, so this does NOT trip the "cross-sprint dependency you
had to introduce" trigger (the same pattern already established, `gate:
clear`, by `SPRINT-012`'s own `depends_on_sprints: [SPRINT-011]` edge and
`SPRINT-050`'s own `depends_on_sprints: [SPRINT-049]` edge); (6) N/A
(coder-only trigger); (7) no contradictory inputs; (8) not genuinely
ambiguous — the sizing-ceiling plus the one-directional, live-verification-
gated dependency shape make two ordered sprints the reasoned call, not an
equally-valid toss-up with one combined 10-task sprint (full reasoning in
`## Grouping Rationale & Sizing` above). Advances `Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-77` row's Sprint column set to
`SPRINT-074`.
