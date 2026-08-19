---
id: SPRINT-055
title: Non-Blocking Manual Capture Dispatch + Scheduling Monitor, bundled with the Thread-Attachment Capture Fix (BUG-014)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retro-harvest (standard on every Done sprint) AND two standing, non-blocking items carried in from this sprint's own two stories: REQ-SB-68-US-01's own ADR-045/trigger-3 human-review flag (unresolved by build completion, unrelated to BUGFIX-03-US-01), and ESC-043 (shared-interface-change, opened during BUGFIX-03-US-01-T02's own verification — a real, previously-unconsidered consequence for app/business/cockpit/attachments.py, out of both stories' own scope, a /bug capture recommended). Neither item blocks either story's own Done status or this sprint's own DoD."
phase: P1                          # single phase only — a sprint never mixes phases; BUGFIX-03-US-01 carries no phase: (hard rule 8's bugfix exception), rides alongside REQ-SB-68-US-01's own P1 phase without contradiction
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-17
started: "2026-08-17"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-17"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-055 — Non-Blocking Manual Capture Dispatch + Scheduling Monitor, bundled with the Thread-Attachment Capture Fix (BUG-014)

## Sprint Goal

Fix `run_capture_now`'s manual-dispatch blocking bug and give the operator a real
per-job running/duration/outcome Scheduling monitor on System Health, and — bundled
into this same sprint per explicit operator instruction — close `BUG-014` so a real
Thread email attachment is actually captured, saved, and linked, with two
same-named attachments across different messages in one Thread never colliding.

---

## Grouping Rationale & Sizing

- **Why grouped — operator directive, not this pass's own dependency/complexity
  partitioning.** `REQ-SB-68-US-01` and `BUGFIX-03-US-01` are the only two
  `Ready`, ungrouped stories found this pass (confirmed by reading every story
  file's `status:`/`sprint:` frontmatter — see `## Notes`). Left to this pass's
  own default drivers (dependencies, complexity, amount-of-work-per-context),
  these two would normally land in **separate** sprints: no `depends_on` edge
  connects either story's tasks to the other's, and they touch disjoint files
  (`REQ-SB-68-US-01`: `agents_router.py`, `agent_schedule_registry.py`,
  `vault_writer.py`'s run-state primitives, `system_health.py`,
  `SystemHealthPage.tsx`; `BUGFIX-03-US-01`:
  `email_capture_pipeline.py`, `vault_writer.py`'s `write_attachments`,
  `email_classification.py`). **This is an explicit operator instruction
  (2026-08-17): "bundle the bugfix into REQ-SB-68's own sprint rather than
  spinning up a separate one for it."** `BUGFIX-03-US-01`'s own `## Non-Goals`
  already anticipated and named this exact bundling as a `/plan-sprints`
  decision deferred to this pass, not decided by the triage pass itself — so
  this is a directive being followed, not a partition being second-guessed or
  split back apart.
- **No false `depends_on` edge invented.** The two stories' task chains are
  recorded, verbatim, as two independent linear chains within this one sprint
  — no cross-story `depends_on` edge is added anywhere, since none exists in
  the decomposer's own recorded graph for either story.
- **Task ordering within the sprint (a judgment call, since neither chain
  depends on the other — either order is valid):** `REQ-SB-68-US-01`'s own
  four tasks (`T01`→`T02`→`T03`→`T04`) are ordered **first**, followed by
  `BUGFIX-03-US-01`'s own two tasks (`T01`→`T02`). Rationale: the operator's
  own instruction frames this as "bundle the bugfix into `REQ-SB-68`'s own
  sprint" — `REQ-SB-68-US-01` is the anchor story this sprint is built around
  (larger, 4 tasks, carries the sprint's own `ADR-045` architecture pass and
  its still-open human-review flag), with `BUGFIX-03-US-01` appended after it,
  matching the operator's own framing rather than an arbitrary
  alphabetical/numeric tie-break. Within each story, its own decomposer-
  recorded linear chain is preserved exactly (`REQ-SB-68-US-01-T01→T02→T03→T04`;
  `BUGFIX-03-US-01-T01→T02`) — this pass does not reorder either chain's own
  internal sequencing.
- **No cross-sprint dependency needed.** Every real upstream dependency named
  by either story is already `Done`: `REQ-SB-68-US-01` extends
  `REQ-SB-31-US-01` (`Done`, `SPRINT-019`, System Health page) and routes
  through `REQ-SB-47-US-01`/`ADR-037`'s already-`Accepted` shared dispatch
  lock (`Done`, `SPRINT-045`); `BUGFIX-03-US-01` extends `REQ-SB-55-US-01`
  (`Done`, `SPRINT-049`, the `write_attachments`/`summarize_attachment`
  mechanism it fixes). `depends_on_sprints: []`.
- **Sizing estimate:** ~6 tasks, M — the combined 4+2 task count matches this
  project's own repeated "~6 tasks, M" precedent (`SPRINT-020`, `SPRINT-022`,
  `SPRINT-028`, `SPRINT-048`, all matched exactly at retro per
  `Implementation/Learnings.md`). `REQ-SB-68-US-01-T04` (the new frontend
  Scheduling section, carrying most of that story's locked ACs) and
  `BUGFIX-03-US-01-T02` (the live end-to-end verification of both of that
  story's locked ACs in one continuous capture session) are each expected to
  be the heaviest task within their own story, by live-verification
  complexity rather than code volume, per this project's own consistent
  finding across prior sprints.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-055 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-68-US-01](../UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md) | Non-blocking manual capture dispatch + a real Job/Scheduling monitor on System Health | P1 | Done |
| [BUGFIX-03-US-01](../UserStories/BUGFIX-03-US-01-thread-attachment-capture-and-collision-safety.md) | Thread email attachments are actually captured, saved, and collision-safe (BUG-014 fix) | — (bugfix, no phase) | Done |

**Tasks in scope** (dependency order, two independent chains, no edge between
them):

- `REQ-SB-68-US-01-T01` (backend, `_invoke_capability` becomes `async def`,
  routes `run_capture_now` through `dispatch_with_shared_lock`, `depends_on: []`)
  → `REQ-SB-68-US-01-T02` (backend, `job_run_state.json` persistence,
  `depends_on: [T01]`) → `REQ-SB-68-US-01-T03` (backend, `GET /system-health`'s
  new `"scheduling"` key, `depends_on: [T02]`) → `REQ-SB-68-US-01-T04`
  (frontend, the new Scheduling section, `depends_on: [T03]`).
- `BUGFIX-03-US-01-T01` (backend, restore the honest attachment-fallback
  signal — gap 1, `depends_on: []`) → `BUGFIX-03-US-01-T02` (backend,
  per-message attachment nesting — gap 2, plus the live end-to-end
  verification of both locked ACs, `depends_on: [T01]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. Every real upstream dependency for both
  stories (`REQ-SB-31-US-01`/`SPRINT-019`, `REQ-SB-47-US-01`/`SPRINT-045`,
  `REQ-SB-55-US-01`/`SPRINT-049`) is already `Done`.
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`)
  and real Outlook/Compass — both stories' own Dependencies sections name
  this; no fixture/test vault substitutes for the live verification either
  story requires.

---

## Out of Scope

- **Closing the separate race-condition risk** `REQ-SB-68-US-01`'s own
  Non-Goals left open is resolved IN scope by `ADR-045` (the manual path now
  joins the shared dispatch lock) — not a leftover Non-Goal for this sprint.
- **Real-time push/WebSocket-based live-updating duration display** — deferred
  per `REQ-SB-68-US-01`'s own Non-Goals; recompute-on-refresh only.
- **`BUG-011`** (a different, already-`Open` `_slugify`-truncation collision
  in `Work/Tasks/`'s flat folder) — not the same defect as `BUG-014`'s gap 2;
  not addressed by this sprint.
- **Retroactively backfilling attachments** for already-captured Thread notes
  processed while `BUG-014`'s gap 1 was live — out of scope per
  `BUGFIX-03-US-01`'s own Non-Goals.
- Every other `Ready` story found this pass already carries a sprint and is
  out of scope: `REQ-SB-42-US-01` (`SPRINT-039`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status,
      including `BUG-014` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once `BUGFIX-03-US-01` is `Done`
- [x] `architecture.md` updated if the sprint changed an architectural fact
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-045`
      already exists from the architect's `/plan-tasks` pass; confirm it is
      `Accepted` (or reconciled) by the time this sprint closes
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints,
      including the wording correction to the 2026-08-17 "scheduled runs also
      block" Constraint entry `REQ-SB-68-US-01`'s own `## Context` flagged
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

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks (`REQ-SB-68-US-01`
  `T01`→`T04`, `BUGFIX-03-US-01` `T01`→`T02`), M — matched exactly, the
  fifth consecutive "~6 tasks, M" precedent to land exactly on estimate
  (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, `SPRINT-048`, now
  `SPRINT-055`). **Takeaway:** the estimate held even under a genuine
  mid-sprint interruption (`REQ-SB-68-US-01-T03`'s own real
  `ESC-042` blocker, resolved same-day) and a genuine architecture-pass
  contradiction (`BUGFIX-03-US-01`'s `ESC-041`, also resolved same-day)
  — neither turned into extra tasks, both were absorbed as escalation
  write-ups + fixes within the already-scoped task boundaries. The "~6
  tasks, M" heuristic continues to hold specifically for sprints combining
  one larger (3-4 task) feature story with one smaller (2-task) bugfix
  story bundled by explicit operator directive.

### What worked

- **Root-causing a bug's OWN stated mechanism against live code, not
  trusting the ledger entry, before building anything** —
  `BUGFIX-03-US-01`'s architect pass re-read `outlook_com.py` directly and
  found `BUG-014`'s own stated gap-1 cause ("never reads Attachments")
  was flatly false against the current code (`ESC-041`). Building the
  originally-described fix would have been redundant, non-closing work;
  the real mechanism (a pipeline NODE silently discarding an honest
  `summary_error` signal) was a completely different, correct target.
  This is the second time this project has found a bug ledger's own
  stated root cause was stale/wrong by the time it reached `/plan-tasks`
  — worth treating "confirmed via code reading" claims in a bug entry as
  a hypothesis to re-verify, not a given, especially for bugs triaged
  same-day as a fast-moving live investigation.
- **Disclosed test substitution, applied consistently across both
  tasks** — neither `T01` (a throwaway monkeypatch) nor `T02` (calling
  `summarize_attachment` directly against a real Thread, plus reusing
  `thread_match_merge`'s own real `append_body_section_line` primitive to
  observe the note-body effect) needed a fixture/mock vault; both stayed
  inside the real `VAULT_PATH` vault and real production code paths,
  with every throwaway write fully reverted and diffed back to
  byte-identical afterward. This kept "live, real, no fixture vault"
  (this story's own hard Constraint) intact even where a real
  two-message email collision didn't naturally occur in-session.
- **Recording, not fixing, a found-but-out-of-scope defect —
  applied twice in one story, one already resolved by the time of
  writing.** `T01` found and disclosed the real `_is_inline_attachment`
  false-positive (outside its own `## Files to Modify`) instead of
  silently patching `outlook_com.py`; it was independently captured and
  directly fixed the same day (`BUG-017`, `Closed`) by a separate,
  faster-moving track. `T02` found and disclosed a second, different
  out-of-scope consequence (`cockpit/attachments.py`'s stale flat-path
  assumption, `ESC-043`) the same way. Neither discovery blocked its own
  task from reaching `Done`.

### What didn't work

- **Neither this sprint's own architecture pass (`BUGFIX-03-US-01`) nor
  `BUG-014`'s own original ledger entry considered DOWNSTREAM readers of
  `write_attachments`'s save-path convention — only its own two writers.**
  `grep write_attachments` correctly found the two functions that CALL
  it, but a third file (`cockpit/attachments.py`) depends on the exact
  same path convention without calling the function itself, and was
  invisible to that grep. This is the second time in this sprint alone a
  file outside a task's own declared scope turned out to be a real,
  live-reachable consequence of an in-scope change (`ESC-042`'s
  `provider_registry.py`/`system_health.py` coupling was the first,
  discovered by `REQ-SB-68-US-01-T03`). Root cause both times: a shared
  on-disk/data CONVENTION (a JSON key shape; a directory-path shape) has
  more real consumers than its own defining function's direct callers —
  grepping for calls to the primitive undercounts consumers of its
  CONTRACT.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Before changing a shared save-path/data-shape convention, grep for
  the CONVENTION'S OWN literal shape (a path prefix, a JSON key name),
  not just calls to the function that produces it** — a downstream
  reader can depend on the same convention without ever calling the
  producing function, and will silently miss a `grep <function_name>`
  scan (`ESC-042`, `ESC-043`, both `SPRINT-055`).
- **A bug ledger's own stated root cause is a hypothesis to re-verify by
  direct code reading at `/plan-tasks`, not a given, especially for a
  same-day-triaged live investigation** — `BUG-014`'s own gap-1 mechanism
  was confirmed false by the very next pipeline stage (`ESC-041`); do not
  build a fix against an unread bug-ledger claim.
- **Disclosed, real-vault throwaway verification with a full
  revert-and-diff-back-to-byte-identical close-out** stays viable even
  when a manual step's own "wait for a real event" precondition
  (a second same-filename email arriving naturally) doesn't occur inside
  the session window — call the real, unmodified function(s) directly
  with synthetic-but-realistic inputs, and, where a downstream effect the
  AC also names isn't reachable without the full pipeline, reuse the
  SAME real primitive the pipeline itself would call (not a hand-rolled
  substitute) to observe it.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Treating "no other function calls this" as proof a save-path/data-
  shape CHANGE has no other consumers** — it only proves no other
  function calls the PRODUCER; a reader that independently recomputes
  the same path/shape (rather than composing the producer's own return
  value) is a real, silent consumer a call-site grep will never surface.

### Open follow-ups

- **`ESC-043`** (`cockpit/attachments.py`'s stale flat-path assumption,
  opened this sprint, `BUGFIX-03-US-01-T02`) — recommend a `/bug` capture
  and eventual `BUGFIX-NN-US-01` fix story; tracked in `REVIEW-QUEUE.md`
  and `ESCALATIONS.md`.
- **`REQ-SB-68-US-01`'s own standing `ADR-045`/trigger-3 human-review
  flag** (opened this sprint, still unresolved by build completion) —
  tracked in `REVIEW-QUEUE.md`, independent of this retro.
- Adjacent, NOT this sprint's own scope, surfaced the same overnight
  session and worth the human's attention alongside this retro: (1)
  `ESC-040` (`SPRINT-053`) — the operator's own provisional overnight
  "Option (a)" resolution of the recurring-meeting `ConversationID`
  finding still has its own spot-check open in `REVIEW-QUEUE.md`; (2)
  `BUG-015` — the 3-message Compass `classify_email` failure investigation
  remains genuinely open (2 partial direct fixes shipped, root cause for
  those specific messages still unconfirmed); (3) `BUG-017`
  (`_is_inline_attachment` false-positive, found by this sprint's own
  `BUGFIX-03-US-01-T01`) was independently captured and directly fixed
  the same day, outside this sprint's own task-tracked flow — already
  `Closed`, noted here only for continuity since it surfaced during this
  sprint's own work.

---

## Notes

**Sprint assembled 2026-08-17 (`/plan-sprints`).** Full pass over every story
file's `status:`/`sprint:` frontmatter confirmed exactly two `Ready`, ungrouped
stories: `REQ-SB-68-US-01` (`sprint: ""`, four `Ready` tasks, `T01`→`T02`→`T03`
→`T04`) and `BUGFIX-03-US-01` (`sprint: ""`, two `Ready` tasks, `T01`→`T02`).
One other `Ready` story exists but is already grouped and out of scope:
`REQ-SB-42-US-01` (`sprint: SPRINT-039`). Every other story is `Draft`,
`In Progress`, or `Done`.

**Grouped together per explicit operator instruction, 2026-08-17** — "bundle
the bugfix into REQ-SB-68's own sprint rather than spinning up a separate one
for it" — not this pass's own default dependency/complexity/effort
partitioning, which would otherwise have kept these two stories in separate
sprints (no `depends_on` edge connects either story's tasks to the other's,
disjoint files, unrelated fixes — one async-dispatch + monitoring UI, one
silent attachment-capture bug). The instruction does not contradict any
dependency edge or the phase rule (`BUGFIX-03-US-01` carries no `phase:`,
riding alongside `REQ-SB-68-US-01`'s own `P1` per hard rule 8's bugfix
exception), so it is followed, not pushed back on. No false `depends_on`
edge was invented between the two stories' task chains — see
`## Grouping Rationale & Sizing` for the task-ordering judgment call (`REQ-SB-68`'s
own chain first, `BUGFIX-03`'s own chain second — a placement choice, not a
dependency claim).

**Gate: `gate: clear` 2026-08-17.** No MUST-FLAG trigger fires for THIS
pass's own grouping decision: (1) no material assumption — the operator's own
instruction directly resolves what would otherwise have been this pass's own
partition choice, and no `depends_on` edge was invented or contradicted;
(2) neither `REQ-SB-68` nor `BUG-014` is `<!-- Draft -->`/unfinalised;
(3) product-owner does not write ADRs — none created or changed by this pass
(`ADR-045` already existed from the architect's own `/plan-tasks` pass);
(4) no new `ESCALATIONS.md` entry; (5) not oversized (6 tasks total, M,
matching four prior confirmed-accurate "~6 tasks, M" precedents) — neither
story is `Blocked` (all six tasks are `status: Ready`) — no cross-sprint
dependency had to be introduced; (6) N/A (coder-only trigger); (7) no
contradictory inputs for this pass's own grouping act (the two stories' own
prior contradictory-input flags — `REQ-SB-68-US-01`'s `ADR-045`/trigger-3 and
`BUGFIX-03-US-01`'s now-resolved `ESC-041`/trigger-7 — are standing story-level
breadcrumbs from earlier passes, not reopened or newly triggered here, matching
this project's own established `SPRINT-051`/`REQ-SB-65-US-01` precedent for
"a flagged story is fully eligible for `/plan-sprints`; the flag stays a
standing breadcrumb, independent of delivery progress"); (8) not genuinely
ambiguous FOR THIS PASS — the grouping itself is operator-directed, not a
choice among equally-valid alternatives this pass had to resolve on its own.
Advances `Draft → Ready`.

**`BACKLOG.md` updated:** `REQ-SB-68` row's Sprint column set to
`SPRINT-055`, Sprint Status set to `Ready`; `BUG-014`'s `Fixed by` note
updated to point at `SPRINT-055`; a new `SPRINT-055` row appended to the
Sprint Status table.

**REVIEW-QUEUE.md:** no new entry written by this pass — `REQ-SB-68-US-01`'s
own standing `ADR-045`/trigger-3 flag and `BUGFIX-03-US-01`'s own resolved
`ESC-041` history already have their own `REVIEW-QUEUE.md` entries, unchanged
and unresolved (where still open) by this pass.
