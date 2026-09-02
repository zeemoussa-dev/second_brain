---
id: SPRINT-085
title: Migrate summarize-and-tag-files and track-opportunities write mechanics onto vault_manager.py
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Coder-drafted retrospective awaits human skim + Learnings.md harvest; T04's own disclosed cron skip-rule finding (REQ-SB-88-US-01-T04, ESC-062's own concurrency near-miss) also await human review, see REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-09-02
started: 2026-09-02                # YYYY-MM-DD when status → In Progress
completed: 2026-09-02              # YYYY-MM-DD when status → Done
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

# SPRINT-085 — Migrate summarize-and-tag-files and track-opportunities Write Mechanics onto vault_manager.py

## Sprint Goal

Close out `REQ-SB-88`'s two remaining `vault_manager.py` migration gaps —
`summarize-and-tag-files` (new deploy + a real cron job) and
`track-opportunities` (an already-deployed but unused engine copy) — two
independent, parallel migrations of two different Skills.

---

## Grouping Rationale & Sizing

- **Why grouped together:** `REQ-SB-88-US-01` and `REQ-SB-88-US-02` are the
  ONLY two `Ready`, ungrouped stories, both anchored on the same requirement
  (`REQ-SB-88`), both `phase: P1`, and both genuinely independent of each
  other — read directly from each story's own task table and `depends_on`
  edges: `US-01` is a straight 4-task chain (`T01→T02→T03→T04`) migrating
  `apply_file_review.py` + provisioning a new cron job; `US-02` is a
  straight 3-task chain (`T01→T02→T03`) migrating `link_opportunity.py`
  against its own already-deployed engine copy. Different Skills
  (`summarize-and-tag-files` vs. `track-opportunities`), different script
  files, zero shared files, and — per each story's own `Non-Goals`
  section — each explicitly calls the other out as "a genuinely independent
  Skill ... its own story," confirming there is no hidden coupling. Both
  also depend only on `REQ-SB-87-US-01` (`Done`), which is not a live
  in-progress sprint here, so no `depends_on_sprints` edge is needed. This
  mirrors this project's own already-established "two independent stories
  sharing one already-satisfied upstream prerequisite build together in one
  sprint" precedent (`SPRINT-083`'s `REQ-SB-87-US-02`/`US-04` pairing,
  itself generalizing `SPRINT-049`'s single-story diamond precedent one
  level up to sibling stories).
- **Sizing:** 4 + 3 = 7 tasks, sized `M`. Comfortably under this project's
  own confirmed `L` ceiling (8-9 tasks: `SPRINT-035`, `SPRINT-049`,
  `SPRINT-083`) and consistent with prior 7-task sprints sized `M`
  (`SPRINT-052`). No third story exists to fold in or split out — this is
  the entire ungrouped-and-Ready backlog at the time of this pass.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-085 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-88-US-01](../UserStories/REQ-SB-88-US-01-summarize-and-tag-files-vault-manager-migration.md) | Migrate summarize-and-tag-files' write mechanics onto vault_manager.py + give it a real cron job | P1 | Done (gate: flagged) |
| [REQ-SB-88-US-02](../UserStories/REQ-SB-88-US-02-track-opportunities-vault-manager-migration.md) | Migrate track-opportunities' Link write mechanics onto its own already-deployed vault_manager.py | P1 | Done (gate: clear) |

---

## Dependencies / External Blockers

- **Depends on sprints:** None — both stories' sole upstream prerequisite,
  `REQ-SB-87-US-01` (the canonical `vault_manager.py` convergence), is
  already `Done` (`SPRINT-082`), not a still-in-progress sprint this one
  needs to wait behind.
- Internal task order (per the decomposer's own `depends_on`; the two
  stories' own chains are independent of each other and may build in
  either order or in parallel):
  - `US-01`: `T01` → `T02` → `T03` → `T04` (the real-vault retrofit check +
    new cron job provisioning).
  - `US-02`: `T01` → `T02` → `T03` (the real-vault retrofit check +
    deployment).

---

## Out of Scope

- `REQ-SB-87-US-02`/`US-03`/`US-05` — still-`In Progress`/`Ready` sibling
  work under `REQ-SB-87`, tracked in `SPRINT-083`/`SPRINT-084`, genuinely
  unrelated Skills/scripts to this sprint's own two stories.
- Any change to either Skill's own real business/judgment logic (per-file
  summarization content, company resolution, Opportunity resolution) — both
  stories' own Constraints keep this a mechanics migration only.
- `files-manager`'s own separate, live-triggered Agent flow for ad-hoc
  uploaded files — explicitly out of scope per `US-01`'s own Non-Goals.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied — `US-01`'s own DoD
      carries one disclosed partial (AC-06's skip-rule sub-clause), see
      its own file and `REQ-SB-88-US-01-T04`'s Implementation Log
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed by this sprint (purely additive/consumptive of `ADR-017`, per the architect's own pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-09-02)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made pairing `US-01` and `US-02` (both stories' own task-level
  `depends_on` graphs were read directly, confirming two straight chains
  with zero cross edges and zero shared files); `REQ-SB-88` is not
  `Draft`/unfinalised in the PRD; no ADR was created or changed by this
  pass; no `ESCALATIONS.md` entry was written by this pass; the sprint is
  not oversized (7 tasks sits well under this project's own confirmed `L`
  ceiling); no cross-sprint dependency had to be introduced (both stories'
  sole upstream prerequisite is already `Done`); the partition is
  unambiguous — these are the only two `Ready`, ungrouped stories in the
  backlog at this pass, both same-phase and independent, so there is no
  equally-valid alternative grouping (e.g. splitting them into two separate
  sprints would create two undersized `S` sprints with no dependency or
  sizing reason to do so).
- Both stories in scope already carry `gate: clear` at the story level (both
  disclosed open scoping questions were resolved directly by the
  analyst/architect before this pass — see each story's own Notes) — no
  flag to carry forward here.
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

- **Estimated:** ~7 tasks, M — **Actual:** 7 tasks, M — matched exactly,
  extending this project's own already-confirmed 7-task/M precedent
  (`SPRINT-052`). Task COUNT held with zero reordering/splitting/merging.
  The real cost, as usual, was not in code volume (both migrations were
  small, mechanical, closely mirroring `REQ-SB-87-US-04`'s own already-
  proven precedent) but in live-verification wall-clock time: two real
  cron-job ticks for `US-01-T04` (~6 min and ~40 min respectively,
  reconfirming this project's own documented "assume multi-minute,
  highly variable real-pipeline latency" Learnings entries a further
  time) dominated this sprint's actual duration far more than either
  story's own build effort.

### What worked

- **Reading the real, current `apply_file_review.py`/`link_opportunity.py`
  directly before editing, every time, caught zero drift** — both files
  matched their own task files' "Starting State" descriptions exactly,
  so every migration edit applied cleanly on the first pass with no
  reconciliation needed, unlike several prior sprints' own documented
  file-drift antipatterns.
- **Mirroring `REQ-SB-87-US-04`'s own already-proven migration shape
  (id-mint-if-missing → `vm.modify_section`, `vm.merge_tags`, one
  additive `Template.json` `allowed_callers` edit per new caller)
  verbatim, twice, for two independent Skills** — zero design iteration
  needed either time; both migrations built and verified correctly on
  the first attempt.
- **Independently reconfirming a real deployed dependency's own
  freshness before building against it (`US-02-T01`'s own direct `diff`
  against the canonical source), rather than trusting a prior story's
  own resync claim** — cheap, and turned "should still be current" into
  a directly-confirmed fact.
- **Snapshot-before/diff-after real-vault verification, reused a third
  time (`REQ-SB-87-US-04-T04` → now `US-01-T03`/`US-02-T03`)** — caught
  the exact, already-accepted "only a new `id` line differs" shape
  cleanly, with zero ambiguity about what changed.
- **Deploying an additional scratch Opportunity specifically to force a
  genuinely NEW write through a migrated path, beyond what the task's own
  named fixture alone would exercise (`US-02-T02`)** — proved the
  migrated `vm.modify_section` call actually executed and was accepted
  against the widened `allowed_callers`, not just that an already-correct
  pre-existing line stayed unchanged.
- **Pausing a real, live, actively-firing cron job the moment its own
  mandated live verification surfaced a genuine reliability gap,
  rather than letting it keep firing unattended or silently downgrading
  the finding** — reversible, zero data loss, gives the human a clean
  decision point without burning further real API cost on a known issue.

### What didn't work

- **This sprint's own two real-vault touches (`US-01-T03`, `US-02-T03`)
  were correctly re-checked for cron/process concurrency immediately
  before each one fired — but `US-01-T04`'s own cron-job creation/
  trigger (also a real-vault-writing action) was NOT given the same
  fresh pre-check**, only the dispatch's own two explicitly-named tasks
  were. A concurrent session's own `REQ-SB-87-US-02-T05` cutover went
  live in the gap between checks — no actual file collision resulted
  (confirmed via a full forensic mtime cross-check across every real-
  vault-writing action's own window), but this was closer to a real
  near-miss than this sprint's own process should have allowed. See
  `ESC-062`.
- **`summarize-and-tag-files`' own documented `## Summary`-non-empty skip
  rule has zero code-level enforcement, unlike `job4`/Threads' own
  timestamp-based safety net** — this was knowable from reading SKILL.md
  ahead of time (it says outright "this has to be YOUR OWN judgment
  every time"), but its real reliability at scale (4/15 = ~27% failure
  in one real batch) was only discoverable by actually running the real,
  scheduled job twice, which is exactly what `T04`'s own Tests block
  mandated. Worth treating "purely agent-judgment-enforced skip rule" as
  a real risk signal earlier in future decomposition passes, not just a
  design note to carry forward.
- **The live Hermes gateway itself showed a real, environment-level
  "fire claim lost, execution was not started" retry pattern** on one
  early trigger attempt (likely related to two simultaneous "gateway
  run" processes observed on this host) — not this sprint's own defect,
  but it added real wall-clock uncertainty distinguishing "still
  working" from "actually stuck," resolved via this project's own
  established CPU-accumulation-check technique.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A new Hermes cron job's `--skill` only resolves against the
  PRIMARY/default profile's own enabled skill catalog, never the
  specialized per-Skill profile the script actually lives under (that
  profile's own gateway is typically `stopped`, not the one that fires
  cron ticks)** — before provisioning any first-time cron job for a
  Skill that currently lives only under a specialized profile, confirm
  and (if needed) enable it under the primary/default profile too, per
  `MEMORY.md`'s own new entry.
- **`hermes cron create SCHEDULE ...`'s schedule-string syntax is a real,
  silent trap** — a bare duration (`"20m"`) creates a ONE-TIME job; only
  the `"every "`-prefixed form (`"every 20m"`) creates a real recurring
  interval job. Always read the newly-created job's own raw JSON entry
  (`schedule.kind`) before trusting it, not just the CLI's own success
  text, which looks nearly identical either way.
- **When a mandated live-verification step for a cron/batch job surfaces
  a genuine reliability gap mid-execution, pause the job (not remove it,
  not silently let it keep running) and disclose exactly what was
  observed** — a reversible, human-respecting default for exactly this
  situation, extending this project's own "archive/pause over delete"
  value one layer up to a live scheduled job.
- **When a sprint's dispatch names specific sibling tasks as live
  concurrent-writer risks, treat the check as needing to cover EVERY
  real-vault-writing action the sprint's own later decomposition
  produces — not just the tasks the dispatch happened to enumerate in
  advance** — a decomposer/product-owner drafting ahead of time cannot
  always foresee every real-vault-touching task a later pass adds (here,
  cron provisioning).

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Treating "the dispatch named these two specific tasks as needing a
  concurrency pre-check" as the complete list, rather than "every real-
  vault-writing action in this sprint needs one"** — see `ESC-062`; no
  actual damage resulted this time, purely by timing luck, not by
  design.
- **Assuming a purely agent-judgment-enforced "skip if already done"
  rule (no mechanical timestamp/flag check) will hold reliably across
  multiple real runs of the SAME job, just because the prompt states the
  rule clearly** — it does not, at a materially non-trivial failure rate
  (~1 in 4, observed live); prefer a real, mechanical skip-guard for any
  future cron-driven batch Skill with this shape.

### Open follow-ups

- **`REQ-SB-88-US-01-T04`'s own disclosed cron skip-rule finding** —
  human decision needed on resume-as-is / add a mechanical guard first /
  strengthen the prompt first, per its own `REVIEW-QUEUE.md` entry.
- **`ESC-062`'s own concurrency near-miss** — human decision needed on
  whether a structural real-vault write-lock safeguard is warranted now
  that concurrent sessions against the same real vault are a
  demonstrated occurrence, per its own `REVIEW-QUEUE.md` entry.
- **`link_opportunity.py`'s own pre-existing CLI stdout-`UnicodeEncodeError`
  crash** (found live, `US-02-T03`) — candidate for a small, standalone
  `BUG-NNN` via `/bug`, per its own `REVIEW-QUEUE.md` entry; the
  established one-line `sys.stdout.reconfigure(encoding="utf-8")` fix
  already proven twice elsewhere in this codebase.
