---
id: SPRINT-063
title: The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, ## Related Ownership Transfer, Company Folder Backfill)
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Coder pass, 2026-08-19: all 9 tasks Done, all 11 locked ACs verified against real, live evidence — see the story's own Coder pass and ESC-054. Flagged solely for the sprint retro (standard human-harvest gate) and for T09/AC-11's disclosed partial-evidence gap (2 of 5 /poc/librarian-* endpoints have a captured live 200 in this session; the other 3 have strong real execution evidence but no captured 200, due to a reproducible coding-session background-process reclaim, not believed to indicate a real defect). Prior gate_reason (product-owner, 2026-08-18, grouping rationale) preserved below in ## Notes."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-063 — The Librarian Section — First Housekeeping Pipeline

## Sprint Goal

Ship the Librarian's first scheduled/autonomous housekeeping pipeline —
Thread rename, Files/OKF backfill, `## Related` ownership transfer, and
company-folder backfill — as one new "Librarian" Section/Agent, reachable
via 5 real endpoints and a real recurring schedule.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 9 tasks belong to
  `REQ-SB-72-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "The Librarian Section — First Housekeeping
  Pipeline", `ADR-049`). Graph read directly from each task file's own
  `depends_on:` frontmatter:
  - `T01` (Thread-lookup primitives + rename primitive) — `depends_on: []`, root.
  - `T03` (Rename Job) — `depends_on: [T01]`.
  - `T02` (migrate 3 real callers off `thread_directory_paths`) —
    `depends_on: [T01, T03]` — sequenced after `T03` specifically because
    `T02`'s own `AC-02` verification needs a real, already-renamed Thread
    as its test fixture, a genuine verification-order dependency, not
    merely both sharing `T01`.
  - `T04` (Files/OKF backfill Job) — `depends_on: [T01]`.
  - `T05` (company-mention detection) — `depends_on: []`, independent,
    shared building block feeding `T06` and `T07`.
  - `T06` (`## Related` ownership transfer) — `depends_on: [T02, T05]`.
  - `T07` (company folder backfill + ambiguous-finding Pending Approval) —
    `depends_on: [T05]`.
  - `T08` (Librarian Section/Agent + orchestration + 5 endpoints) —
    `depends_on: [T03, T04, T06, T07]`.
  - `T09` (scheduled wiring) — `depends_on: [T08]`.
  - Acyclic, all `phase: P1`.
- **Single sprint, not split — a split was actively considered and
  rejected, not a default.** The one plausible fault line is "lookup/
  rename infra" (`T01`/`T03`/`T02`) vs. "housekeeping content Jobs"
  (`T04`/`T05`/`T06`/`T07`) vs. "Section/scheduling bootstrap"
  (`T08`/`T09`). This does NOT hold up as a real ordered-sprint partition:
  - `T08` — the assembly/bootstrap task — depends on `T03` (infra group),
    `T04`, `T06`, `T07` (content group) SIMULTANEOUSLY. There is no way to
    finish "infra" and "content" as two cleanly sequenceable sprints feeding
    a clean third — `T08` needs BOTH groups' own outputs at once, so a
    3-sprint split would still require the first two sprints to both
    complete before the third starts, which is no different in outcome
    from one sprint building all 9 tasks in the SAME dependency order,
    just with 2 extra sprint files and 2 recorded `depends_on_sprints`
    edges adding zero real decoupling value.
  - `T06` (nominally "content") has a hard edge back into `T02` (nominally
    "infra"), so even the two-way split isn't clean — the groups aren't
    actually independent, they're two intermingled strands of the SAME
    directory-rename/lookup concern feeding into the SAME `## Related`
    write.
  - Per `Implementation/Pipeline.md` hard rule 7, dependency-linked stories
    (or here, tasks within one story) go in the same sprint OR ordered
    sprints with a `depends_on_sprints` edge — but that rule exists to
    honor a REAL dependency graph, not to force a split where none of the
    graph's own shape actually decouples cleanly. Introducing 2 new
    cross-sprint edges among sibling sprints of the SAME single-DoD story,
    for zero real complexity reduction, would itself be the kind of
    needless-fragmentation call `SPRINT-062`'s own `## Notes` explicitly
    warns against ("Splitting it into a separate sprint would not reduce
    this sprint's real dependency floor... while adding a needless extra
    sprint file").
  - Directly distinguishable from `SPRINT-060`/`061`/`062`'s own 3-way
    split (`REQ-SB-71`'s own batch): THAT split was across 3 SEPARATE
    stories, each with its OWN Definition of Done, where `SPRINT-061`'s
    own `## Notes` explicitly rejected a single combined 12-13-task sprint
    as oversized. This sprint is ONE story with ONE Definition of Done —
    there is no analogous "avoid oversized combined sprint" pressure,
    because 9 tasks is not oversized on its own (see below), and there are
    no separate stories to keep apart in the first place.
- **Sizing estimate: ~9 tasks, L.** Sits exactly at this project's own
  established, twice-already-matched-exactly single-session ceiling for a
  single-story sprint (`SPRINT-021`, 9 tasks/L; `SPRINT-030`, 9 tasks/L —
  both estimated-vs-actual exact matches per `Implementation/Learnings.md`),
  and one task above `SPRINT-049`'s own 8-task/L precedent (also an exact
  match, also a single story with a diamond-shaped dependency graph that
  "built cleanly end-to-end with zero reordering once the graph was
  correctly recorded at `/plan-tasks`" — directly analogous to this
  sprint's own shape). Not oversized: every task is real, cited, non-
  duplicative work (a 3-real-caller lookup migration, 2 backfill Jobs, a
  shared detection building block, an ownership transfer, a Pending
  Approval, and a new Agent/Section/schedule identity), and the decomposer's
  own pass already cross-checked this same "not oversized" conclusion
  against the identical precedent (see the story's own `## Notes`).

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-72-US-01's own
frontmatter now carries sprint: "SPRINT-063". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-72-US-01](../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md) | The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, ## Related Ownership Transfer, Company Folder Backfill) | P1 | Done |

**Tasks in scope** (dependency order): `T01` → `T03` → `T02` (also needs
`T03`, sequenced after it for its own verification fixture) → `T06` (also
needs `T05`); `T01` → `T04`; `T05` independent, feeds `T06`/`T07`; `T03` +
`T04` + `T06` + `T07` → `T08` → `T09`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `REQ-SB-71-US-02` (`SPRINT-061`, Done) and
  `REQ-SB-71-US-01` (`SPRINT-060`, Done) are the story's own hard
  prerequisites — both already `Done`, so no NEW cross-sprint dependency is
  introduced by this sprint (confirmed directly: every one of this story's
  own 9 tasks' `depends_on` edges resolves to another task WITHIN this same
  story/sprint; none names a task ID from `SPRINT-060`/`061`/`062`).
- **External:** none new — the real, already-configured vault this
  pipeline retrofits/extends.

---

## Out of Scope

- Meaningful/topic tags and cross-Thread linking of recurring file
  artifacts — the story's own explicit PRD deferrals.
- Reassigning the already-shipped `vault-filing-expert` Agent into the new
  "Librarian" Section — the story's own explicit non-goal.
- Any change to `email_capture_pipeline.py`/`thread_match_merge` — out of
  this story's `## Files to Modify`; `ESC-050`'s own second, more severe
  finding stays a separate, disclosed follow-up, not this sprint's scope.
- Backfilling any pre-`REQ-SB-71-US-02` flat-shape Thread notes, if any
  remain — `ESC-048`'s own separate, disclosed concern.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed this sprint — `ADR-049`/architecture.md were already updated at `/plan-tasks`, not touched further by this build)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-049`, recorded at `/plan-tasks`, unchanged by this build)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — exact match again
  (third time this project has hit its own single-story/single-sprint
  ceiling exactly: `SPRINT-021`, `SPRINT-030`, now `SPRINT-063`). Task
  *shape* held; task *duration* did not — see "What didn't work" below.
  Real elapsed wall-clock time to close this sprint was far higher than 9
  tasks/L would normally imply, entirely because of `T06`/`T07`/`T09`'s own
  long-running real-vault Jobs, not because any task's own code was
  underestimated.

### What worked

- **Building forward from a genuinely-interrupted prior session's own
  partial code, after verifying it by direct reading first, rather than
  redoing it.** `T06`/`T07`'s business logic was already correct and
  complete on disk when this session resumed; re-reading it end-to-end
  before writing anything new (rather than trusting the resume brief's
  claim blindly, or distrusting it and rewriting from scratch) was the
  right amount of skepticism — confirmed correct, saved real rebuild time,
  and caught nothing wrong.
- **The manual-mode verification technique this codebase has used since
  `SPRINT-021`** (real endpoint call → real before/after disk-state
  comparison, byte-for-byte where the AC demands it) scaled cleanly to
  this sprint's much larger real corpus (126 real Threads) without any
  new verification machinery — `AC-06`/`AC-07`/`AC-08`'s single-Thread,
  targeted checks gave strong, fast, unambiguous evidence without needing
  a full corpus run to complete first.
- **Never issuing a second concurrent call to the same mutating function,
  confirmed via live log tailing before every retry** — held throughout a
  genuinely stressful, repeatedly-interrupted session; zero orphaned or
  duplicate-running processes at any point, unlike the two prior sessions
  on this exact task.
- **The Pending-Approval propose/finalize shape (`T07`), reused unchanged
  from `REQ-SB-63-US-01`'s own precedent**, verified cleanly both ways
  (approve → real folder created; decline → real nothing created) on the
  first real attempt — no rework needed.

### What didn't work

- **Bulk Jobs with no per-call scope/limit (`populate_thread_related_
  links`, `backfill_company_folders`) are structurally 30-90+ minute
  single HTTP calls against this vault's real size (126 Threads, one real
  Compass call per Thread apiece).** This is not itself a defect — it is
  an honest, correct design per `T06`/`T07`'s own task files — but it
  collided head-on with this specific coding session's own tool
  infrastructure: the backgrounded backend process was reclaimed by the
  session's own harness 3 separate times (at roughly 35, 40, and 55
  minutes of that process's own age), every time while the Job itself was
  still genuinely, successfully progressing (confirmed via live log
  tailing — real Compass 200s, real file mutations — right up to each
  kill). This is the SAME failure class disclosed as having stopped the
  two PRIOR coder sessions that attempted `T06` before this one — now
  reproduced a third time within a single session, and for the first time
  root-caused specifically to the coding session's own background-process
  lifecycle, not the application, not the Compass API (every logged call
  succeeded), and not a concurrency bug (verified clean throughout). See
  `ESC-054`.
- **A real, live client was concurrently using the app during part of
  this session** (`GET /vault-search/...`, `GET /cockpit/meeting/...`
  traffic observed in the backend's own logs, not originating from this
  session) — surfaced a pre-existing, already-known `500` bug in `/cockpit/
  meeting/{stem}` (already tracked in `REVIEW-QUEUE.md` from `SPRINT-064`'s
  own verification, `people.py::resolve_people_chips`), unrelated to this
  sprint, not fixed here, not double-logged.
- **As a direct result of the above, one locked AC (`AC-11`, `T09`)
  carries a disclosed, itemized partial-evidence gap** (2 of 5 endpoints
  have a captured live `200`; the other 3 have strong real execution
  evidence but no captured `200` within this session) rather than a
  completely clean pass — the first time this project's own "every locked
  AC gets a real, captured verification" bar was met with strong-but-not-
  literal-100% evidence, disclosed rather than silently accepted or used
  to block an otherwise-correct, well-evidenced sprint.

### Patterns to carry forward

- **Verify a long-running bulk Job's own correctness via a single,
  targeted, real-but-small-scope call (one real Thread) FIRST, before
  attempting to drive the full corpus to completion** — this is what let
  `AC-06`/`AC-07`/`AC-08` close cleanly and fast, independent of whether
  the full-corpus run itself ever finished within the session.
- **When a background mutating call outlives a client-side timeout, poll
  read-only (log tailing / disk-state re-scans) rather than retrying** —
  confirmed safe and correct 4 separate times this session; never issue a
  second call to the same mutating function until process-absence + log
  evidence together confirm the prior one has actually ended.
- **Disclose a genuine, reproducible infrastructure limitation as exactly
  that — infrastructure, not application defect, not scope failure —**
  with itemized real evidence for what WAS proven, rather than either (a)
  silently accepting a weaker verification standard, or (b) blocking an
  otherwise-correct, extensively-evidenced sprint over a formality the
  next session (or the operator running the app normally) can close in
  minutes.

### Antipatterns to avoid

- **Do not design a future bulk housekeeping Job (this Section will grow
  more of them) without a per-call scope/limit or resumability knob** —
  this sprint's own `populate_thread_related_links`/`backfill_company_
  folders` have none, which is what turned a correct design into a
  session-infrastructure collision. Recommend the NEXT Librarian-Section
  story give bulk Jobs an optional `limit`/cursor parameter so both a
  coding session and the operator's own UI can drive them to completion
  in smaller, interruption-safe slices.
- **Do not treat "the client-side HTTP call timed out" as evidence of
  failure without first checking whether the server-side work is still
  genuinely progressing** — 3 of 4 long-running calls this session looked
  like failures at first glance (`curl` exit 28) and were in fact
  succeeding correctly server-side; the correct diagnostic is live log
  tailing before any retry decision.

### Open follow-ups

- `ESC-050` (`ESCALATIONS.md`, disclosed by the architect pass) —
  `thread_match_merge`'s own still-live legacy rename logic orphans
  `messages/`/`files/` for an already-existing new-shape Thread, confirmed
  to already fire today, independent of this sprint shipping. Out of this
  sprint's own `## Files to Modify`; carried forward unresolved.
- `ESC-054` (`ESCALATIONS.md`, this sprint) — long-running bulk housekeeping
  Jobs collide with this coding session's own background-process reclaim
  policy; recommend a `limit`/chunking knob on future bulk Jobs. `AC-11`'s
  own disclosed partial-evidence gap (`T09`) awaits human spot-check —
  trivially closeable by running the app normally and calling `POST /poc/
  librarian-run-housekeeping-pass` once.
- The real `## Related`/company-folder backfill is genuinely incomplete
  across the full 126-Thread corpus as of this sprint's own close (`##
  Related`: 87/126; several real ambiguous Pending Approvals still
  `pending` real operator review) — will complete autonomously via `T09`'s
  own real, persisted 6-hour schedule once the app runs normally, or can be
  driven to completion immediately via the endpoint above.
- The story's own architect-set `gate: flagged` (`ADR-049`, `trigger-3`)
  was already cleared directly by the operator, 2026-08-18, per the
  story's own frontmatter `gate_reason` — not reopened by this sprint (the
  story's own gate was re-flagged by the coder pass for the separate,
  unrelated `AC-11` reason above).

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single sprint, no split,
no `depends_on_sprints` edge. Full split-vs-single reasoning recorded above
under `## Grouping Rationale & Sizing` — the one plausible fault line
("lookup/rename infra" vs. "housekeeping content Jobs" vs. "Section/
scheduling bootstrap") does not actually decouple: `T08` needs outputs from
all three groups at once, and `T06` (nominally "content") has a hard edge
back into `T02` (nominally "infra"). Splitting would introduce 2 needless
cross-sprint `depends_on_sprints` edges within one single-DoD story for zero
real complexity reduction — the antipattern `SPRINT-062`'s own `## Notes`
already named. Distinguished directly from `SPRINT-060`/`061`/`062`'s own
3-way split: that split was across 3 separate stories, each with its own
DoD, specifically to avoid a disclosed 12-13-task oversized-sprint risk
(`SPRINT-061`'s own `## Notes`); this sprint is one story, one DoD, and 9
tasks is not oversized on its own (established precedent: `SPRINT-021`/
`SPRINT-030`, both 9 tasks/L, both exact matches at retro).

gate: clear 2026-08-18 — no MUST-FLAG trigger fired: not oversized (at,
not beyond, an already-twice-proven ceiling); no blocked story; no NEW
cross-sprint dependency (both real prerequisite sprints, `SPRINT-060`/
`SPRINT-061`, are already `Done`); the split-vs-single partition was
actively considered and rejected on real dependency-graph grounds, not left
ambiguous. Advanced `Draft → Ready` — eligible for `/implement-sprint
SPRINT-063`.
