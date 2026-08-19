---
id: SPRINT-074
title: People Notes Retroactively Linked to Their Real Company/Partner Note
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest — the coder drafts the Retrospective below; the human skims it and propagates Patterns/Antipatterns into Implementation/Learnings.md. No blocking trigger fired during the build itself (no new ADR, no unresolved assumption, nothing blocked, every locked AC verified live)."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-073]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
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
| [REQ-SB-77-US-01](../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md) | People Notes Retroactively Linked to Their Real Company/Partner Note | P2 | Done |

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

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change made — already updated at `/plan-tasks` under "People Notes Retroactively Linked to Company/Partner"; confirmed still accurate against the real, shipped code)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (none — no new ADR needed for this story)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints (n/a — none emerged; every task's own Implementation Log confirms this explicitly)
- [x] `CHANGELOG.md` entry appended (one entry per task, four total)
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly, extending
  this project's own repeatedly-confirmed 4-task/S precedent (`SPRINT-019`,
  `SPRINT-025`). No task was split, dropped, or merged. The estimate's own
  reasoning ("the mechanism this story exercises already exists; the new work is
  a reach/trigger promotion plus verification, not a new mechanism build") held
  up exactly — `T01` was the only task that wrote genuinely new code (one
  function, ~30 lines); `T02` was a rename + a 2-line wrapper; `T03`/`T04` were
  verification-only, as scoped. The real cost center across all four tasks was
  live-verification technique (finding real Threads/Persons in the exact right
  precondition state, disposable-test setup/teardown discipline), not code
  volume — consistent with this project's own long-running pattern.

### What worked

- **Reading `T01`'s own `depends_on: []` root task first, in full, before
  touching any other file** made `T02`/`T03`/`T04` straightforward compositions
  — each task's own "After/Outputs" code sample matched the real, already-shipped
  neighboring code almost exactly, with only one real discrepancy found (the
  `people_extraction` import `T02`'s Constraints named as new was already present
  — `SPRINT-073`'s own sibling work had added it first).
- **The worktree-sync check at the very start of the run caught a real, load-
  bearing gap before any code was written** — this worktree was 8 real commits
  behind `master` (including `SPRINT-073`'s own landing commit,
  `run_company_partner_building_pass()` itself), not just individually-modified
  files. A `git log --oneline HEAD..master` + a safe `git merge master --ff-only`
  (confirmed a pure-ancestor branch first) resolved it in one step, per
  `MEMORY.md`'s own already-documented technique from `SPRINT-073`'s own coder
  run the same day. Without this check, `T03` would have wrongly concluded
  `run_company_partner_building_pass()` didn't exist and escalated a false
  blocker.
- **Disposable-test Customer/Partner/Affiliate classifications, snapshotted and
  reverted via byte-for-byte `Compare-Object` diffs, proved a genuinely real
  instant-trigger and self-heal call end-to-end** without leaving any permanent
  mark on the operator's real vault — reused across `T02`/`T03`/`T04` with zero
  cleanup failures. Picking a fresh real Thread/Person candidate each time (via a
  small scan script checking `find_matching_customer`/`find_matching_partner`
  both return `None` and the Thread's own primary `customer`/`partner` field is
  genuinely unset) avoided the false-negative trap described below.
- **Bounding an expensive, already-independently-verified real dependency
  (`backfill_company_folders()`'s own real, whole-vault Compass sweep) via a
  scoped, reverted in-process stub**, while leaving the actually-under-test
  dependency (`retrofit_people_from_emails()`) fully real and unbounded, proved
  `T03`'s locked AC with a real positive result without a multi-minute,
  wide-blast-radius, real-Compass-backed full-vault re-run. Directly reused this
  project's own `SPRINT-028` Learnings pattern.

### What didn't work

- **The first `T02` verification attempt picked a real Thread (`2026-07-28 MIC`,
  company "Microsoft") that already had a Partner (`Core42`) set as its own
  primary field** — applying a NEW Customer classification correctly took the
  pre-existing `_apply_company_to_threads` additive-tag branch (adds
  `customer/microsoft` to `tags`, but never sets the primary `customer:` field,
  since a Thread's primary is single-value by design), which meant
  `list_known_customers()` (a primary-field-only scan) never picked up
  "Microsoft" as known, so the relink correctly found no match and wrote no
  wikilink. Not a defect — a real, disclosed property of already-`Done`,
  out-of-scope code (`REQ-SB-76-US-01-T06`) — but it cost one real write/revert
  cycle before switching to a genuinely primary-unset Thread. Root cause: picked
  the first Thread found for the right SENDER without first checking the
  Thread's own current `customer`/`partner` primary state.
- **Assuming `customer_hub_linking.ensure_customer_hub_note` alone would make a
  company "known"** for `T03`'s own precondition setup — it does not; only a real
  Thread's own `customer`/`partner` frontmatter FIELD (not the hub note's mere
  existence) is what `list_known_customers()`/`list_known_partners()` scan. Cost
  one real create/verify/revert cycle on a throwaway "Ewec" hub note with zero
  actual effect before switching to the correct technique (calling
  `_finalize_company_review_outcome` directly, which both creates the hub note
  AND sets the Thread's own primary field).

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Before picking a real Thread for any Company-classification live-verification
  step, explicitly check its OWN current `customer`/`partner` primary-field state
  first (not just which sender it references)** — `_apply_company_to_threads`'s
  own primary-vs-additive branch (`REQ-SB-76-US-01-T06`) means the SAME
  classification call produces materially different real, observable effects
  (a `list_known_customers()`-visible primary write vs. an additive tag-only
  write invisible to that same scan) depending purely on the Thread's own
  pre-existing state — verify this precondition explicitly before relying on the
  outcome. Found live, `SPRINT-074`/`T02`.
- **"A company becomes known" for this codebase's own `find_matching_customer`/
  `find_matching_partner` mechanism means a real Thread's own primary
  `customer`/`partner` frontmatter FIELD is set — never the mere existence of a
  Customer/Partner hub note/OKF directory.** `ensure_customer_hub_note`/
  `ensure_partner_hub_note` alone are necessary but not sufficient; use
  `_finalize_company_review_outcome` (or the real `finalize_company_review`
  wrapper) to set up a genuine "this company just became known" precondition for
  any future live-verification of this same mechanism family. Found live,
  `SPRINT-074`/`T03`.
- **Re-syncing a worktree to `master` via `git log --oneline HEAD..master` + a
  safe `git merge master --ff-only` (after confirming zero unique commits via
  `master..HEAD`) generalizes cleanly a second time** — `SPRINT-073`'s own coder
  run found and documented this technique the same day; this sprint's own coder
  run independently hit the identical symptom (a worktree created "fresh from
  master" that was actually 8 commits behind) and the documented fix worked
  immediately, with zero improvisation needed. Worth treating as a standard
  FIRST step for any coder run, not just something to reach for after a
  suspicious "file doesn't exist" finding.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a plain, non-worktree-prefixed file path's `Read` result as
  authoritative for "what does MY worktree currently contain"** — this session's
  own `Read` calls against the short `C:\myWorx\Projects\Second Brain\...` path
  returned content that did NOT match this worktree's own actual, literal
  git-tracked file state for at least one file (`SPRINT-074`'s own frontmatter
  showed `status: In Progress`/`started: "2026-08-19"` via the short-path read,
  but the worktree's own real file — confirmed via the explicit
  `.claude\worktrees\...` path — still had `status: Ready`/`started: ""`).
  `Edit`/`Write` tool calls correctly refuse a non-worktree path outright (a
  hard guard), but `Read` did not, silently returning a DIFFERENT copy's
  content. Always use the explicit worktree-prefixed path for BOTH Read and
  Edit/Write once a worktree-isolation error has fired even once in a session —
  don't assume the short path is safe for reads just because it "worked" for
  earlier files that happened not to have diverged. Found live, `SPRINT-074`.
- **Picking the first real Thread that merely references the target sender,
  without checking whether that Thread's own primary `customer`/`partner` field
  is already occupied by a DIFFERENT real company** — costs a real write/revert
  cycle discovering the additive-branch/primary-branch distinction the hard way.
  See the matching Pattern above.

### Open follow-ups

- The disclosed, non-blocking finding from `T02`'s own log (a Thread with an
  already-set Partner primary silently loses a SECOND company's own
  `list_known_customers()`-visibility when classified via the additive-tag
  branch) is a property of already-`Done`, out-of-scope code
  (`_apply_company_to_threads`, `REQ-SB-76-US-01-T06`) — not filed as a new bug,
  since it is not this story's own defect and no locked AC of this story depends
  on the additive branch's own visibility. Worth a human judgement call on
  whether it is worth a future `BUG-NNN`/`REQ` if a real multi-company Thread
  scenario turns out to matter more than currently assumed.

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

---

## Coder pass, 2026-08-19 (`/implement-sprint`)

Before starting, confirmed this worktree needed re-syncing to `master`
(`git log --oneline HEAD..master` showed 8 real commits missing, including
`SPRINT-073`'s own `run_company_partner_building_pass()` landing commit,
`8ec8f49`) — resolved via a safe `git merge master --ff-only` after confirming
this worktree's branch was a pure ancestor of `master` (zero unique commits).
All 4 tasks (`T01`→`T02`/`T03`/`T04`) built and verified in dependency order;
`T03` built last, only after re-confirming `run_company_partner_building_pass()`
was real, shipped code. Every locked AC verified live against the real vault
with a real positive result — see `REQ-SB-77-US-01`'s own `## Coder pass` note
and each task file's own `## Implementation Log` for the full evidence. Nothing
blocked; nothing escalated to `ESCALATIONS.md`/`REVIEW-QUEUE.md` during the
build itself.

Sprint advances **`Ready` → `Done`**, `completed: 2026-08-19`. `gate: flagged`
— retro-harvest only (see `gate_reason` above); no MUST-FLAG trigger fired
during the build. `BACKLOG.md`'s `REQ-SB-77` row and `SPRINT-074`'s own Sprint
Status row both updated to `Done`.
