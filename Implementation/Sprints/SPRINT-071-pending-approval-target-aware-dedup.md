---
id: SPRINT-071
title: Pending Approvals gain a target-aware dedup check (BUG-029/BUG-030 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint retro drafted — human skim + Learnings.md harvest; standing ADR-056 review on BUGFIX-08-US-01 also still open"
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, S"      # effort estimate; checked vs actual in retro
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

# SPRINT-071 — Pending Approvals gain a target-aware dedup check

## Sprint Goal

Add a target-aware `dedupe_key` idempotency check to `create_pending_approval` and
wire it through the five real call sites named by `BUG-029`/`BUG-030`, so exactly one
live Pending Approval exists per real target/event regardless of trigger source or
how many capture ticks reprocess it.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single story, `BUGFIX-08-US-01`, batching both bugs (their own
  `BUGS.md` notes independently predicted "likely the same fix"). Its two tasks form
  a strict linear dependency chain (`T02 depends_on: [T01]` — the four call-site
  updates in `T02` cannot pass the new `dedupe_key` keyword argument until `T01` adds
  the parameter to `create_pending_approval` and wires `skill_registry.py::
  invoke_skill`'s own internal computation). One story, one dependency chain — no
  partition question. Per `Pipeline.md` hard rule 8, a bugfix sprint is exempt from
  phase homogeneity; the story itself carries no `phase:` field.
- **Sizing estimate:** ~2 tasks, S — matches this project's own `SPRINT-029`
  precedent (2 tasks, S buildable) for a small, mechanically-scoped shared-primitive-
  plus-call-sites shape. Both tasks are backend-only, touching a small, already-
  enumerated set of files; no UI change (see the story's own `## Affected Screens`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-071 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-08-US-01](../UserStories/BUGFIX-08-US-01-pending-approval-target-aware-dedup.md) | Pending Approvals gain a target-aware dedup check (BUG-029/BUG-030) | — (bugfix) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- Story-level `gate: flagged` (standing `ADR-056` review) is disclosed but explicitly
  non-blocking for this stage per the story's own architect-pass note — the human
  reviews `ADR-056` and the story's tasks together in one sitting via the existing
  `REVIEW-QUEUE.md` entry; `/implement-sprint` is not gated on it.

---

## Out of Scope

- Deciding the dedup mechanism's exact shape — already decided by the architect
  (`ADR-056`), not a product-owner decision.
- Cleaning up already-existing duplicate Pending Approval records in the live store —
  explicitly out of scope per the story's own `## Non-Goals`.
- Any UI/rendering change — confirmed none needed.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already landed at
      the architect pass (`/plan-tasks` step 1); no further change needed at build time
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-056`, already `Accepted` at
      the architect pass; code now matches it exactly, no deviation
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

- **Estimated:** ~2 tasks, S — **Actual:** 2 tasks, S (matches) — **Takeaway:** the sizing
  precedent this sprint cited (`SPRINT-029`'s own "shared-primitive-plus-call-sites" shape)
  held exactly: a linear `T02 depends_on: [T01]` chain, one shared-primitive task then one
  thin-wiring task across four call sites, built and verified in one working session with no
  scope surprises. The pre-decided `ADR-056` mechanism (additive `dedupe_key`, no lock
  restructuring) meant the coder pass itself needed zero design judgement — pure, mechanical
  build-and-verify, which is exactly what kept it at S.

### What worked

- **Architect pre-deciding the mechanism made the build genuinely mechanical.** `ADR-056`
  already named the exact parameter shape, the exact per-call-site `dedupe_key` convention,
  and explicitly rejected the lock-restructuring alternative with reasoning — the coder pass
  had nothing left to design, only to type. Zero mid-build judgement calls about the fix
  itself; both disclosed judgement calls (see below) were about HOW to verify safely, not
  about the fix's own shape.
- **Live verification via a throwaway `.scratch/` script, run against the real backend
  functions directly (not the HTTP layer), reused a pattern already established in this
  project** (`verify_section_ownership.py` precedent) — fast, precise, and left a clear,
  reviewable trail of exactly what was called and what was observed, without needing the
  uvicorn server itself to be restarted mid-task.
- **Checking real data volume before firing a "real Job re-run" verification step paid off.**
  Before running `propose_customer_backfill()` twice, a quick real count (123 real `"Unsorted"`
  Threads) revealed the unbounded version would have fired ~246 real Compass calls and flooded
  the just-cleaned live queue with dozens of new proposals purely for verification. The task's
  own pre-authorized monkeypatch-bounding escape hatch was used instead — same real function,
  same real Compass calls, same real dedup mechanism under test, just a smaller real input set.

### What didn't work

- **Bounding one real Job's input set without also accounting for its downstream sibling Job's
  own signal dependency created a real, if caught-and-corrected, side effect.**
  `propose_customer_archival_candidates` takes `propose_customer_backfill`'s own
  `matched_existing_customer_names` as its ONLY signal for "this Customer folder has zero real
  matches" — bounding the backfill pass to 3 real Threads (to control Compass call volume)
  starved that signal down to 3 matched customers, so the archival step then proposed 24 OTHER
  real Customer folders as "archival candidates," which is not just verification noise but
  actively wrong business data (those folders likely DO have real matches across the full
  123-Thread corpus; bounding just didn't compute them this pass). Root cause: the two Jobs'
  data dependency (`propose_customer_backfill`'s output feeds `propose_customer_archival_
  candidates`'s only input) wasn't accounted for when choosing where to bound scope — bounding
  the FIRST Job's input silently degrades the SECOND Job's own correctness, not just its
  runtime. Caught immediately by inspecting real record counts before/after (not assumed
  correct from the two calls returning identical ids to each other, which they did — the
  mechanism itself was never wrong, only the artificially-narrowed evidence was), and corrected
  by explicitly declining all 24 records this pass created before finishing the task.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Check real record/data counts BEFORE firing a "real end-to-end" verification step against
  live external-API-backed pipelines** — a quick, cheap enumeration (e.g. `len(list_thread_
  notes())` filtered to the relevant state) before calling the real function tells you whether
  an unbounded run is proportionate or whether the task's own authorized bounding escape hatch
  should be used, and by how much.
- **When bounding one Job's input for a live verification pass, trace what OTHER real function
  consumes that Job's own output as its ONLY evidence signal, and bound/verify that downstream
  consumer's real record counts too** — a Job pipeline's "propose A, then propose whatever A
  didn't match" shape (seen here between `propose_customer_backfill` and `propose_customer_
  archival_candidates`) silently degrades the SECOND function's correctness when the FIRST
  one's input is narrowed, even though neither function is individually "wrong."

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting "two calls returned identical results" as sufficient proof a live-data
  verification step is clean, without also checking whether the ABSOLUTE record counts/values
  it produced are themselves correct.** The archival-candidate dedup mechanism passed its own
  narrow test (both calls returned the same 24 ids) while the 24 ids themselves were an
  artifact of insufficiently-scoped bounding, not a real Job result — the mechanism check and
  the input-correctness check are two different things and both are needed.

### Open follow-ups

- **Pre-existing real duplicate records this story's own Non-Goals left uncleaned** — 1 real
  `meeting-capture`/`run_capture_now` legacy record (`4e5ef1403765`, pending since
  `2026-08-14`), plus the pre-existing 38 `propose_customer_backfill_routing` and 13
  `propose_customer_archival_candidate` real records already in the live queue before this
  sprint — a one-time data cleanup pass, if wanted, is a separate, explicit operator action per
  the story's own Non-Goals, not filed as a new bug (the creation path is now fixed; these are
  historical residue only).
