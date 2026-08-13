---
id: SPRINT-007
title: Partner hub notes + Microsoft migration, and Research notes template
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Done — human retro skim + Learnings.md harvest pending; see ESCALATIONS.md ESC-003 (Open, unrelated primitive-level bug found during verification)"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"             # YYYY-MM-DD when status → Done
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

# SPRINT-007 — Partner hub notes + Microsoft migration, and Research notes template

## Sprint Goal

Close out this batch of the 2026-08-10 vault-taxonomy resolution's two
remaining direct-extension items: give Partner companies their own hub
note and Person-note linking (with Microsoft's existing mis-tagged
Customer data migrated cleanly), and give the user an Obsidian-native
Research (books & reads) template plus guide-note entry — neither of which
requires any new external integration, both built entirely on already-Done
mechanisms.

---

## Grouping Rationale & Sizing

- **Why grouped:** Both stories are direct, reuse-only extensions of
  already-`Done` work (`REQ-SB-16-US-01` extends `REQ-SB-14-US-01`'s
  hub-note mechanism and `REQ-SB-10-US-01`'s Person-note linking;
  `REQ-SB-17-US-01` extends `REQ-SB-15-US-01`'s Templates/guide-note
  mechanism) — neither introduces a new external-integration surface or a
  new architectural risk the way `REQ-SB-08-US-01` does, and both trace
  back to the same 2026-08-10 taxonomy-resolution plan (Partners and
  Researches were resolved in the same pass as Meetings). There is no
  dependency edge between them (different modules: `partner_hub_linking.py`
  / `people_extraction.py` vs. `Templates/Research.md` / the guide note —
  no shared file, no `depends_on` edge across their task sets), so they run
  as two independent chains inside one sprint, not a single merged
  dependency graph: `REQ-SB-16-US-01`'s `T01 → T02 → {T03, T04}` and
  `REQ-SB-17-US-01`'s `T01 → T02`, both acyclic, neither referencing the
  other's tasks.
- **Why grouped together rather than each standalone:** combined they total
  6 tasks (4 + 2), matching this session's established ~4–6 task single-
  working-context precedent (SPRINT-001/002/004 at ~4 tasks S; SPRINT-003
  at ~2 tasks XS) without exceeding it meaningfully. `REQ-SB-17-US-01` alone
  (2 tasks, vault-content-only, no backend code) is smaller than any prior
  standalone sprint except SPRINT-003 and would under-use a full sprint
  cycle on its own; pairing it with the other similarly low-risk,
  no-new-integration story (`REQ-SB-16-US-01`) keeps the sprint count
  reasonable while keeping `REQ-SB-08-US-01`'s materially higher-risk,
  new-integration profile isolated in its own sprint (SPRINT-006) rather
  than diluting this lower-risk batch's verification story. This is a
  clear, defensible cohesion call (shared taxonomy-plan origin + matched
  risk/complexity profile + combined size fitting one working context), not
  a genuinely ambiguous partition — the alternative of three
  single-story sprints was considered and rejected only because it would
  leave `REQ-SB-17-US-01` needlessly fragmented from a comparably-sized,
  comparably-low-risk sibling.
- **Sizing estimate:** ~6 tasks, M (medium) — `REQ-SB-16-US-01`'s own 4
  tasks are directly comparable in shape to the already-Done
  `REQ-SB-14-US-01`/SPRINT-002 precedent (vault-writer primitives →
  business orchestration → matching-branch extension → HTTP endpoint,
  ~4 tasks/S); `REQ-SB-17-US-01`'s 2 tasks directly mirror the already-Done
  `REQ-SB-15-US-01`/SPRINT-003 precedent (template file → guide-note
  addition, ~2 tasks/XS). Summing two well-calibrated precedents (S + XS)
  gives a combined M estimate with higher-than-usual confidence, since both
  halves individually match a "landed exactly as estimated" prior sprint.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-007 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-16-US-01](../UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md) | Partner hub notes, Person-note linking, and Microsoft customer-to-partner migration | P1 | Done |
| [REQ-SB-17-US-01](../UserStories/REQ-SB-17-US-01-research-notes-template-and-guide.md) | Obsidian template and guide-note entry for manual Research (books & reads) entries | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- `REQ-SB-16-US-01`'s own `## Dependencies` confirms no hard blocker:
  `REQ-SB-14-US-01` and `REQ-SB-10-US-01` (both Done) provide the exact hub-
  note and Person-note-linking mechanisms it extends.
- `REQ-SB-17-US-01`'s own `## Dependencies` confirms no hard blocker:
  `REQ-SB-15-US-01` (Done) already established the `Templates/` vault root
  and the guide note it extends.
- `REQ-SB-16-US-01`'s `T04` (the migration endpoint) runs live against the
  real Microsoft data already present in the configured vault (`VAULT_PATH`)
  — no fixture/mock environment, same precedent as prior sprints. Not a
  sprint-blocking dependency, noted here for the coder's awareness.
- `REQ-SB-17-US-01`'s tasks author directly into the real vault
  (`Templates/Research.md`, `Work/Guides/Manual-Entry-Guide.md`) — vault
  content, not application code; no fixture environment either.
- `ADR-009` (Partner primitive layering + generic-scan migration design)
  was reviewed and approved by the operator 2026-08-11 — not an open
  blocker.

---

## Out of Scope

- **A general per-write capture-pipeline hook for Partner** — per
  `REQ-SB-16-US-01`'s own Non-Goals; Partner linking is scoped to Person
  notes only.
- **Pipeline/Agreement/Consumption-Snapshot-equivalent sub-entities for
  Partner** — operator's explicit scoping, per the story's own Non-Goals.
- **Any AI-assisted capture/summarization pipeline for Research notes** —
  per `REQ-SB-17-US-01`'s own Non-Goals; manual entry only.
- **Any Second Brain application UI for either Partner or Research data** —
  Obsidian's own graph/tag/template surfaces are the presentation layer for
  both stories; no application screen is added or changed by this sprint.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (unchanged this pass — `ADR-012`'s own architecture-scope addendum was the architect's pass, not this coder pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-009` and `ADR-012` both `Accepted`
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

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M, but with one
  mid-flight architecture correction (`ADR-012`, a 7th artefact beyond the
  original 6 tasks — a one-`if`-condition fix routed through the
  not-yet-`Done` `T04` rather than reopening the frozen `T02`) and one
  unplanned, out-of-scope live-data repair (2 real vault notes manually
  fixed as due diligence, `ESC-003`). **Takeaway:** the task-count estimate
  itself landed exactly right, but "M" undersold the actual verification
  effort for `REQ-SB-16-US-01-T04` specifically — a live-data migration
  task whose own mandatory pre-migration sanity check is genuinely
  open-ended work (it can surface a real architecture gap, as it did here),
  not a fixed-size verification step. Future sizing for any "generic scan
  against real, live, concurrently-modified data" task should budget for
  at least one round of "the scan found something the story didn't
  anticipate" as a normal, not exceptional, outcome — this is now the
  second sprint in a row (after `SPRINT-006`'s `ESC-002`) where a live
  verification pass on real data surfaced a genuine architecture/design
  gap the story text alone couldn't have caught.

### What worked

- **The pre-migration sanity check caught a real bug before it touched
  live data.** Per this task's own explicit instruction ("verify the
  generic scan finds exactly what you expect first... before actually
  executing the mutating migration call"), the coder inspected the real
  vault and found the scan's match predicate structurally could never
  reach 5 real, already-identified Person notes — and stopped, rather than
  running the migration and silently leaving those notes stranded. This is
  exactly the discipline the story's own gating language asks for, and it
  worked: zero data loss, a clean escalation, a fast, narrow architect
  correction (`ADR-012`), and a fully-correct final migration once resumed.
- **Routing a narrow, single-`if`-condition fix through the still-open task
  (`T04`) rather than reopening a `Done`, frozen task (`T02`) kept the
  append-only-specs rule intact** while still landing the fix exactly
  where the locked AC it unblocks lives — a clean precedent for "small
  correction discovered late in a dependency chain" that avoids both
  reopening frozen work and minting a disproportionate new task for a
  one-line change.
- **Idempotent-by-construction primitives (no-op-if-absent) meant the
  corrected migration could simply be re-run to completion** rather than
  needing careful manual reconciliation of partial state, even after a
  genuinely confusing concurrent-process complication (see below) left the
  real vault in a partially-migrated, partially-untouched state mid-flight.
- **Direct-vault inspection before AND after every mutating live-data call**
  (not just trusting the endpoint's own JSON response) caught a real
  correctness gap between "what the endpoint reported" and "what the vault
  actually contains," in both this sprint's incident and the one that
  triggered `ESC-001` in the first place.

### What didn't work

- **A leftover server process from an earlier, superseded attempt in the
  same session silently served live HTTP requests using stale (pre-fix)
  code**, because the coder's own earlier belief that it had exited (based
  on one `curl` connection-refused check) was wrong — the process had
  simply not yet been checked again after outliving that one probe. This
  meant the first "corrected" migration call actually ran with the *old*
  single-signal predicate, and a second, genuinely new server process
  (which *did* have the fix) failed to bind the same port and silently
  exited after completing its own real-capture side effect. Root cause:
  no positive, minimal confirmation ("this exact PID is bound to this exact
  port, right now") was done before trusting an HTTP call's success:
  a 200 response was taken as proof the intended process handled it,
  when in a environment with multiple concurrent dev-server instances (a
  now-repeated pattern across sessions) that assumption is unsafe.
- **The same dev-server-start side effect that's already a known
  constraint (`MEMORY.md`'s "every backend dev-server start fires a real
  capture run") had a second-order consequence this session hadn't
  considered: that capture run can itself call the exact business logic
  under test** (here, `T03`'s own `ensure_person_note` Partner-matching),
  independently of and concurrently with whatever HTTP call the coder is
  making — producing real, live side effects on the very data being
  verified, mid-verification. This collided with a genuinely pre-existing,
  unrelated data-quality defect in one real note
  (`insert_body_line_if_missing`'s fixed-offset assumption, `ESC-003`),
  compounding a small corruption into a more visible one.
- **A second, independent concurrent session's own capture pipeline
  (`SPRINT-006`, meeting classification) was actively writing new
  Microsoft-related notes into the same real vault during this sprint's
  own live verification window**, changing the "expected" note count
  between the coordinator's message and the coder's own re-check (14
  anticipated, 15 actually found). The generic-scan design absorbed this
  correctly (by construction), but it's worth naming explicitly: this
  project's real vault is not a static fixture even within a single
  verification session — concurrent sessions are a standing operating
  condition now, not a one-off.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Positive process/port confirmation before trusting an HTTP call
  against a live-mutating endpoint** — when multiple dev-server attempts
  may exist in the same session (or concurrently with other sessions),
  don't infer "which process handled my request" from the HTTP response
  alone; confirm the exact PID bound to the exact port immediately before
  the mutating call, and prefer a **direct in-process function call**
  (bypassing HTTP entirely) for the actual mutating verification step once
  any ambiguity is suspected — this sprint's recovery used exactly that,
  and it resolved the ambiguity completely.
- **A pre-mutation sanity scan is not a formality — treat "the scan found
  something different than expected" as a normal, not exceptional,
  outcome for any generic-scan-based migration against real, live,
  concurrently-modified data**, and budget verification time accordingly
  (this is the second sprint running where this happened: `SPRINT-006`'s
  `ESC-002`, now `SPRINT-007`'s `ESC-001`/finding-of-15-not-14).
  Re-running the sanity scan immediately before the mutating call (not
  just once, hours earlier) is worth the extra step when other concurrent
  work is known to be touching the same vault.
- **Route a narrow, single-locus correction discovered late in a
  dependency chain through the still-open blocked task, not by reopening
  an already-`Done`, frozen upstream task** — keeps the append-only-specs
  rule intact while still landing the fix exactly where its own locked AC
  verification lives. Confirmed working precedent from `ADR-012`/`T04`.
- **When a live-data defect is found that's genuinely out of the current
  task's scope to fix at the primitive level, repair the specific affected
  real data directly (byte-exact, not retyped) as due diligence, and
  separately escalate the underlying primitive bug for proper fixing** —
  don't leave known-corrupted real user data sitting broken just because
  the root-cause fix is out of scope, but also don't quietly expand scope
  to fix the primitive itself without a proper task/story for it.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a background dev-server process has exited based on a single
  connection-refused check, without re-verifying immediately before the
  next mutating action** — a process can outlive that one probe (e.g. a
  long-running lifespan startup), and a second server start can then
  silently fail to bind while the "dead" one keeps serving stale code.
  Always re-check port/process state immediately before, not just once,
  hours earlier.
- **Trusting a primitive's documented structural assumption
  (`insert_body_line_if_missing`'s "body always starts with a blank line
  after frontmatter") without a live spot-check against real, possibly
  hand-edited data** — this assumption silently breaks on any note that
  was ever manually edited outside `write_note()`'s own convention, and
  the failure mode (silent mid-word insertion) gives no error, no
  exception, nothing to notice except by direct inspection.

### Open follow-ups

- **`ESC-003`** (`ESCALATIONS.md`, `Open`) — `vault_writer.
  insert_body_line_if_missing`'s fixed body-start byte offset corrupts any
  note whose body lacks the standard blank line after frontmatter; one real
  note found and manually repaired, underlying primitive not yet fixed.
  Recommended next step: `/bug` capture → `BUGFIX-NN-US-01`.
- **`ESC-002`** (`ESCALATIONS.md`, `Open`, from `SPRINT-006`, unrelated to
  this sprint but still awaiting a human decision) — ADR-008's own
  EntryID-stability risk, confirmed real on the live calendar.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for this grouping decision. Both
stories' own dependency graphs are honoured intact and are independent of
each other (no shared file, no cross-story `depends_on` edge), so grouping
them in one sprint does not contradict hard rule 7. Not oversized — 6
combined tasks is within this session's established range, and each
story's task count individually matches an already-Done, well-calibrated
precedent (`REQ-SB-14-US-01`/SPRINT-002 for the 4-task half,
`REQ-SB-15-US-01`/SPRINT-003 for the 2-task half). Not blocked — all six
tasks across both stories are `status: Ready`, both stories are
`status: Ready`, and each story's own `## Dependencies` section confirms
every upstream mechanism it reuses is already `Done`. No cross-sprint
dependency was introduced (`depends_on_sprints: []`). Single phase (P1)
throughout for both stories. `REQ-SB-16-US-01`'s `gate: flagged`
(trigger-3, ADR-009 creation) does not block this stage — the operator
reviewed and approved ADR-009 2026-08-11; resetting the story's `gate:`
value is not this role's job. `REQ-SB-17-US-01` was already `gate: clear`.
The grouping choice itself (pair these two rather than give each its own
sprint) is a reasoned cohesion call, not a genuinely ambiguous partition —
recorded above, not flagged. Both stories advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 2 stories, 6 tasks total, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (`/implement-sprint`), 2026-08-11 — status set to `In
Progress`; `gate` set to `flagged`.** `REQ-SB-17-US-01` (both tasks) is
`Done` — `Templates/Research.md` and the guide note's Research entry both
built and verified live against the real vault, all 4 locked ACs `PASS`.
`REQ-SB-16-US-01`'s `T01`/`T02`/`T03` are `Done` (AC-01/02/03/04/08
Person-note-half all verified live against throwaway data, real
Microsoft/ADNOC data untouched by these three tasks). `REQ-SB-16-US-01-T04`
is **`Blocked`**: the coder's own pre-migration sanity scan (performed
before calling the mutating endpoint, as instructed) found the migration's
generic scan structurally cannot reach the 5 real Microsoft Person notes
`AC-06` names — a data-shape gap in the generic-scan design (`ADR-009`
point 4/5), not the already-resolved Newsletter/Notification undercount.
The mutating `POST /poc/migrate-customer-to-partner` endpoint was **never
called**; the real vault's Microsoft data (hub note + every
`customer/microsoft`-tagged note) is fully untouched, exactly in its
pre-migration state — no data loss, no partial/inconsistent write. Full
detail: `ESCALATIONS.md` → `ESC-001`; `REVIEW-QUEUE.md` entry added.

Since `REQ-SB-16-US-01` cannot reach `Done` (a locked AC — `AC-06`, and
transitively `AC-05`/`AC-07`/`AC-08`'s migration half — cannot be verified
as passing with the implementation exactly as specified), this sprint
cannot close: `status: In Progress` (not `Done`), `completed:` left blank,
no Retrospective drafted yet — per this role's own rule ("if anything is
blocked, leave the sprint In Progress and flag the blocked list"), a
sprint-level retro is deferred until `REQ-SB-16-US-01-T04`'s blocker is
resolved and the migration actually runs against the real vault. The
`BACKLOG.md` Sprint Status row and both requirement rows were updated to
reflect this (`REQ-SB-16` → `Blocked`, `REQ-SB-17` → `Done`, `SPRINT-007` →
`In Progress`).

**Explicitly listing what was written to the human surfaces this pass:**
- `ESCALATIONS.md` → `ESC-001` (new, `Status: Open`) — the data-shape gap
  in the migration's generic scan relative to real Person notes.
- `REVIEW-QUEUE.md` → new entry for `REQ-SB-16-US-01-T04`, pointing at
  `ESC-001` and this task's own `## Implementation Log`, with a concrete
  "what to do" (decide the Person-note-inclusion design, then reset the
  task's `status:` to resume).
- Auto-advanced (`gate: clear`) without a new flag: `REQ-SB-16-US-01-T01`,
  `T02`, `T03`, and both of `REQ-SB-17-US-01`'s tasks — all fully verified
  live, no trigger fired by any of them individually.

---

**Coder pass (`/implement-sprint`, resumption after `ADR-012`), 2026-08-11
— status set to `Done`; `gate` set to `flagged` (retro-harvest pending).**
The architect resolved `ESC-001` with `ADR-012`, correcting
`REQ-SB-16-US-01-T04`'s scope to include the migration's match-predicate
fix. Implemented the fix exactly as specified, re-ran the pre-migration
sanity scan (found 15 real matches, not 14 — 2 more legitimate notes had
appeared from `SPRINT-006`'s own concurrent capture work; both confirmed
genuine), and ran the real, mutating migration against the live vault.

A genuine complication surfaced and was fully investigated and resolved
before completing verification: a leftover server process from an earlier
attempt in this same session (which the coder had incorrectly believed had
exited) actually served the first migration HTTP call using stale,
pre-fix code, while a second, correctly-fixed process failed to bind the
same port and exited after its own real-capture side effect legitimately
linked two live Microsoft contacts via `T03`'s own mechanism — one of
which collided with a pre-existing, unrelated structural defect in that
one real note, compounding a corruption (`ESC-003`, new, `Open`). Both
affected notes were repaired directly (byte-exact) before completing the
migration via a direct, unambiguous Python call (bypassing HTTP entirely).

Every locked AC across both stories is now verified `PASS` live against
the real vault: `REQ-SB-16-US-01`'s `AC-01` through `AC-08` (T01/T02/T03
already verified; `AC-05`/`AC-06`/`AC-07`/`AC-08`-migration-half verified
in this pass) and `REQ-SB-17-US-01`'s `AC-01` through `AC-04` (verified
earlier this sprint). Both stories `Done`. `BACKLOG.md`'s `REQ-SB-16`,
`REQ-SB-17`, and `SPRINT-007` rows all updated to `Done`. `MEMORY.md` and
`CHANGELOG.md` updated. Retrospective drafted above.

**Explicitly listing what was written to the human surfaces this pass:**
- `ESCALATIONS.md` → `ESC-001` marked **Resolved** (by the architect's
  `ADR-012` pass, confirmed and closed out by this coder pass's successful
  live verification).
- `ESCALATIONS.md` → `ESC-003` (new, `Status: Open`) — the
  `insert_body_line_if_missing` fixed-offset primitive bug found live,
  with one real note manually repaired as due diligence; underlying
  primitive not fixed (out of `T04`'s scope).
- `REVIEW-QUEUE.md` → the `REQ-SB-16-US-01`/`ADR-012` review pointer
  removed (resolved); a new `ESC-003` entry added recommending a `/bug`
  capture; a new `SPRINT-007` retro-harvest entry added (this sprint).
- Auto-advanced (`gate: clear`): `REQ-SB-16-US-01-T04`, the
  `REQ-SB-16-US-01` story itself — all locked ACs verified, `ADR-012`
  already reviewed/approved per the architect's own pass; the `ESC-003`
  finding is logged and flagged separately, orthogonal to this story's own
  scope.
- Sprint `gate: flagged` — standard end-of-sprint pattern, for the human to
  skim this retrospective and harvest `Implementation/Learnings.md`; also
  carries forward visibility of the still-`Open` `ESC-003`.
