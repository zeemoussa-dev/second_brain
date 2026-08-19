---
id: SPRINT-065
title: process_staged_email retires legacy thread_match_merge — flat-shape migration + directory-shape orphan fix (BUG-026 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "All 5 tasks (T01-T05) Done. Both locked ACs (AC-01, AC-02) genuinely verified PASS live, with real evidence in each task's own Implementation Log. email-capture-pipeline's working mode flipped supervised -> autonomous, confirmed permanent via a fresh GET -- the final undo of ESC-048's protective measure. BUG-026 flipped In Sprint -> Closed. gate: flagged for the human to skim the drafted Retrospective below and harvest Learnings.md -- this sprint's own real journey (two genuine, live-found content-integrity bugs, both caught and fully repaired before any permanent damage) is a real pattern worth capturing. Not blocking -- nothing remains open."
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-065 — process_staged_email retires legacy thread_match_merge — flat-shape migration + directory-shape orphan fix (BUG-026 fix)

## Sprint Goal

Ship `BUGFIX-05-US-01` end to end: `process_staged_email` composes
`capture_raw_thread_messages`/`synthesize_thread` instead of the legacy
`thread_match_merge` path, a legacy flat-shape Thread note is lazily
migrated and threaded in place instead of duplicated, and an
already-migrated directory-shaped Thread's own `messages/`/`files/`
content is never orphaned — then `email-capture-pipeline`'s working mode
is flipped back to `autonomous` once both facets are verified live.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-05-US-01` is the only
  `Ready`, ungrouped story this pass (confirmed by scanning every
  `Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`;
  the other two `Ready` stories found — `REQ-SB-59-US-01`,
  `REQ-SB-42-US-01` — already carry a `sprint:` value (`SPRINT-059`,
  `SPRINT-039` respectively) and are excluded as "not ungrouped"). Its 4
  tasks form two dependency shapes exactly as recorded by the decomposer's
  final re-lock pass: `T01` (`[]`) → `T02` (`[T01]`) is the composing-
  function rewire (`AC-02`, orphaning facet) then its own live
  verification; `T03` (`[]`) is the independent `vault_writer.py`-only
  migration primitive (`AC-01`, duplication facet, `ADR-052`) — no edge to
  `T01`/`T02`, different files entirely; `T04` (`[T01, T02, T03]`) is the
  converging live verification of `AC-01` AND the working-mode flip, which
  correctly needs all three of the others `Done` first. One story, one
  small dependency graph, one working context — there is no real partition
  question here to flag as ambiguous.
- **No phase-mixing question:** `BUGFIX-05-US-01` carries no `phase:` —
  per `Pipeline.md` hard rule 8's bugfix exception, this sprint is exempt
  from phase homogeneity and is built standalone (`phase: ""` above,
  mirroring `SPRINT-005`/`SPRINT-016`/`SPRINT-064`'s own precedent for a
  single-bugfix-story sprint).
- **Sizing estimate:** ~4 tasks, S. Matches this project's own recurring
  "~4 tasks, S" precedent for a small, well-scoped batch shaped as two
  code tasks (`T01`, `T03` — disjoint files, no coordination overhead)
  plus two real-vault live-verification tasks (`T02`, `T04`) — the same
  shape `SPRINT-064` itself sized identically. `Implementation/
  Learnings.md`'s own recurring calibration note for this exact shape
  (`SPRINT-055`, `SPRINT-064`) is that live-verification-against-the-real-
  vault cost, not code volume, is this batch's real risk dimension — both
  `T02` and `T04` require identifying real flat/directory-shaped Thread
  candidates in the live vault and a careful backup/verify/(selective)
  cleanup discipline, same posture as `BUGFIX-03-US-01-T02`'s own
  precedent this story's own tasks explicitly cite. No task needs its own
  sprint or a cross-sprint `depends_on_sprints` edge — the whole batch fits
  comfortably in one working session together.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-065 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-05-US-01](../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md) | process_staged_email retires legacy thread_match_merge so Threads no longer duplicate or orphan on new messages (BUG-026 fix) | — (bugfix) | Done |

---

## Dependencies / External Blockers

- **Resolved (2026-08-19):** `BUGFIX-05-US-01-T04`'s own first attempt
  found, via live end-to-end verification, that `AC-01` genuinely failed
  as originally designed — `ADR-052`'s migration mechanism alone did not
  preserve a freshly-migrated flat Thread's own real, pre-migration
  `## Summary` content once the SAME composed pipeline tick immediately
  called `synthesize_thread` next. The architect resolved this with
  `ADR-053` (a one-time, self-consuming `pre_migration_summary.md`
  sidecar), implemented by the new `T05` and re-verified by a second `T04`
  attempt — both `AC-01` and `AC-02`'s flip clause now genuinely PASS live.
  Full detail: `ESCALATIONS.md` → `ESC-056` (now `Resolved`);
  `REVIEW-QUEUE.md`.
- **Depends on sprints:** None.
- No external blocker — `REQ-SB-71-US-02` (`Done`) already built the
  `capture_raw_thread_messages`/`synthesize_thread` functions this story
  composes; `ADR-051` and `ADR-052` (both `Accepted`) already resolve the
  architecture-level questions this story's tasks build against.
- **Note carried from the story:** this work runs against the user's real,
  live Obsidian vault and real Outlook mailbox, not a fixture/test vault —
  no-data-loss is load-bearing per `BUG-026`'s severity (Major). `T04`
  must not choose `conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A` (the
  already-diverged Azure conversation) as its verification target — see
  the story's own Notes and `ESCALATIONS.md` → `ESC-055`.

---

## Out of Scope

- Fixing, merging, or otherwise reconciling the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` duplicate — deferred to a future
  Librarian-housekeeping backlog item per the architect's own explicit
  Decision 2 (`ADR-052`); a dedicated `REVIEW-QUEUE.md` entry already asks
  the human to accept that deferral or request a one-off reconciliation
  instead.
- Retiring `thread_match_merge`'s function body, `_build_graph()`,
  `_GRAPH`, or `get_job_tree()` — deprecated, not deleted (`ADR-051`
  Decision 6).
- Any change to `pull_email`/`email_pull.pull_and_stage_emails` — confirmed
  out of this bug's own call chain.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted`
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

- **Estimated:** ~4 tasks, S — **Actual:** 5 tasks, M (one task, `T05`,
  and one architect re-pass, `ADR-053`, were added mid-sprint) —
  **Takeaway:** under-sized by one task/ADR. Not a planning failure —
  `T05`/`ADR-053` exist because `T04`'s own FIRST live end-to-end
  verification attempt found a genuine, previously-undiscovered
  interaction gap between two already-`Accepted` ADRs (`ADR-051`,
  `ADR-052`) that neither `T01`'s nor `T03`'s own narrower smoke tests
  happened to chain together. This is the SAME calibration note
  `Implementation/Learnings.md` already carries forward from `SPRINT-055`/
  `SPRINT-064` — for this recurring "code task + real-vault live-
  verification task" shape, the live-verification task is the real risk
  surface, and its own genuine live findings can (and, twice now in this
  one story, did) legitimately grow the task count after the sprint
  starts.

### What worked

- **Live, end-to-end verification against the REAL capability endpoint —
  not a raw script — is what caught both real bugs.** `T02`'s own first
  attempt and `T04`'s own first attempt each independently found a real,
  live defect (an orphaning incident from a stale server process; a
  genuine content-loss gap between two composed ADRs) specifically
  BECAUSE they drove the real `process_staged_email` endpoint end-to-end
  against real vault data, rather than calling `synthesize_thread`/
  `resolve_thread_directory` directly. A narrower unit-style check would
  have missed both.
- **"No-data-loss is load-bearing, not a convenience" held under real
  pressure, twice.** Every incident this sprint (T02's stale-server
  orphaning; T04's own two incidents — a side-effect-triggered migration
  outside the endpoint, and a second stale-server repeat of the pre-
  `ADR-053` content-loss bug) was caught immediately, diagnosed by direct
  evidence (not assumed), and the real vault was restored byte-identical
  before any further action, confirmed via direct comparison rather than
  visual inspection alone. Zero permanent data loss across the whole
  sprint despite four distinct real-vault incidents.
- **"Resolve directly when the fix only adds safety, never removes it"**
  (the operator's own standing judgment this whole session) let `ADR-053`
  ship and unblock `T05`/`T04` without a human round-trip mid-session,
  because the fix's own shape (a durable, archived, additive sidecar) was
  unambiguously safety-adding by construction — the same judgment already
  used for `ADR-047`–`ADR-052` this same story.
- **Disclosing incidents in the task's own Implementation Log, not
  silently repairing and moving on**, gave this retro (and the human) a
  complete, honest record of exactly what went live-wrong and how it was
  fixed — the `REVIEW-QUEUE.md` FYI-entry pattern this story now has three
  instances of (`T02`, and two new ones this session for `T04`) turned
  each incident into a visible, spot-checkable breadcrumb rather than an
  invisible recovery.

### What didn't work

- **A "just re-confirm the candidate is clean" diagnostic call
  accidentally triggered a real, permanent side effect.** `resolve_
  thread_note_path`/`resolve_thread_directory` are DOCUMENTED as
  side-effecting for a flat-shape Thread (a deliberate, disclosed
  exception, `ADR-052` Decision 5) — but that side effect is easy to
  forget mid-session when the immediate intent is "just look," not
  "migrate." Root cause: no structural guard distinguishes a read-only
  intent from a write-triggering one at the call site; the caller must
  remember the function's own prose contract every time.
- **A stale, no-`--reload` backend server silently serving pre-edit code
  is a repeat failure class — this is the THIRD time this exact shape has
  bitten a live-verification task in this project** (`T02` this story;
  now `T04` twice in a row, once as a genuine repeat of the SAME failure
  class within one task). Root cause: nothing in this project's own dev
  workflow currently forces a fresh server process before a live-
  verification task's tracked run, and a stale process gives no visible
  signal (it responds to `GET` requests fine) that it is running old code.
- **No backup/version-control layer exists for the vault itself.** When
  the diagnostic-call incident required reconstructing a file's exact
  original content, the only source of truth was two prior `Read` tool
  outputs already in the conversation transcript — sufficient this time,
  but a near-miss: had those two reads not existed or not agreed, there
  would have been no way to prove byte-identical restoration at all.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Restart the backend server (confirm via a fresh, correct-code smoke
  check) immediately before ANY live-verification task's own tracked
  run, every time, without exception** — do not trust that "it's already
  running" means "it's running today's code." This is now a THREE-time
  repeat finding in this one project (`T02`, `T04` x2) and should become a
  standing pre-flight step for every future live-verification task, not
  something each coder pass has to rediscover.
- **When a function has a documented side effect on read (e.g. `resolve_
  thread_directory`'s legacy-migration exception), treat EVERY call to it
  during verification — including "just checking" diagnostic calls — as a
  potential real write.** Prefer reading a file directly (`Read`
  tool / plain `path.read_text`) over calling a domain function with a
  known side-effecting exception when the intent is genuinely read-only.
- **When a live-verification task's own first attempt finds a genuine
  defect (not a process/script mistake), expect it to grow the task
  graph** — a new task plus possibly a new ADR, not a same-task fix. This
  story hit this pattern twice (`ESC-055`→`ADR-052`→`T03`; `ESC-056`→
  `ADR-053`→`T05`) and both times the "sizing was too small" outcome was
  actually the process working correctly — a real gap being found and
  closed properly, not a planning failure to avoid.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Calling a side-effecting lookup primitive "just to check state" during
  verification.** A function whose own docstring discloses a write side
  effect (however narrow/deliberate) should never be called from a
  diagnostic aside — only from the tracked verification step itself, so
  every real mutation is intentional and accounted for in the task's own
  Implementation Log.
- **Trusting `GET`-style read endpoints as proof a server is "fresh."** A
  running process answers reads fine regardless of whether it has picked
  up recent code edits — only a check that actually exercises the CHANGED
  code path (or an explicit process-age/edit-time comparison, as used to
  diagnose this sprint's own second `T04` incident) can tell the
  difference.

### Open follow-ups

- Two still-open, non-blocking `REVIEW-QUEUE.md` items from this sprint
  remain for a human decision, unrelated to this sprint's own `Done`
  status: (1) `ESC-055`'s own already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A`
  Thread duplicate — accept deferral to a future Librarian-housekeeping
  backlog item, or request a one-off manual reconciliation now; (2)
  optional human spot-check of `T02`'s and `T04`'s own disclosed real-
  vault incidents (informational, no action required to unblock
  anything).
- Filed as a candidate future backlog item, not yet created: a project-
  wide "restart the backend server before every live-verification task"
  pre-flight convention, per the "Patterns to carry forward" note above —
  worth promoting from a Learnings pattern to an actual checklist step in
  `Implementation/Pipeline.md`'s own coder contract if it recurs a fourth
  time.
