---
id: REQ-SB-74-US-01-T06
title: One-time backfill run against the real 137-Thread corpus + idempotency-after-approval verification
parent_story: REQ-SB-74-US-01
requirement_id: REQ-SB-74
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-74-US-01-T01, REQ-SB-74-US-01-T02, REQ-SB-74-US-01-T03, REQ-SB-74-US-01-T04, REQ-SB-74-US-01-T05]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01-T06 — Backfill run + idempotency-after-approval verification

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill"

---

## Objective

Run the full Customer backfill for real against the real 137-Thread corpus (re-confirm the live count before running) via the real endpoint, resolve at least one real batch by approving it, then re-run the backfill and prove an already-routed Thread is never re-proposed.

---

## Starting State → End State

**Before / Inputs:**
- Everything from `T01`-`T05` is deployed: detection, both propose Jobs, both finalize handlers, `_APPROVAL_HANDLERS` registration, and the real `POST /poc/librarian-propose-customer-backfill` endpoint.
- Zero of the real 137 Threads have ever been routed — all still `customer: "Unsorted"`.

**After / Outputs:**
- A real first run of `POST /poc/librarian-propose-customer-backfill` against the full real corpus produces real, batched Pending Approval records (both routing batches and archival candidates).
- At least one real routing batch is approved for real via `POST /pending-approvals/{id}/approve` — its Threads' `customer`/`tags` genuinely updated on disk.
- A real second run of the SAME endpoint never re-proposes any Thread that was part of the already-approved batch — only Threads still `customer: "Unsorted"` are considered.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — no code change expected in this task (verification-only); if a genuine defect surfaces during the real run, fix it here, in scope.

---

## Constraints

- Inherits from parent story.
- This IS the backfill vehicle — no separate, standalone script (`MEMORY.md` — API-first, no script workarounds). The real, already-built Jobs, invoked via the real endpoint, are the entire mechanism.
- A second manual trigger before an already-created batch is approved/declined re-proposes the SAME still-`"Unsorted"` Threads into a NEW batch (`ADR-055`'s own disclosed, accepted operational risk for `"direct"`-triggered proposals) — this task's own re-run must happen AFTER resolving (approving) at least one real batch first, not merely re-triggering blindly, so this AC is tested honestly against its own real precondition ("some batches are already approved").
- Archive-not-delete — if any real archival-candidate approval is exercised in this task, confirm the folder is moved, never deleted.

---

## Tests

**Manual verification steps:**
1. `POST /poc/librarian-propose-customer-backfill` for real against the full real corpus; confirm a real `200` and record the real counts (routing batches created, archival candidates created, Threads left Unsorted).
2. `[REQ-SB-74-US-01-AC-09]` Pick one real, pending routing batch naming one or more real Threads. `POST /pending-approvals/{id}/approve` against the real running server; confirm the named Threads' `customer`/`tags` are genuinely updated on disk. Re-run `POST /poc/librarian-propose-customer-backfill` a second time; confirm NONE of the just-approved Threads appear in any new batch's own `payload["thread_paths"]` this second time — re-read each one's `customer` frontmatter directly to confirm it is still the routed value, not reverted or re-proposed. Confirm only Threads still genuinely `customer: "Unsorted"` are considered by this second run.
3. Spot-check at least one real archival-candidate approval end-to-end (approve, confirm the real folder moved to `Work/Archive/Customers/`, content unchanged) as bonus integration confidence beyond `T04`'s own direct-function-call verification.
4. Record the real, final backfill counts observed at run time (Threads routed, new Customers created, archival candidates raised, Threads left Unsorted) in this task's own Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A real first backfill run against the full real corpus produces real, batched Pending Approval records
- [x] At least one real batch approved for real, Threads genuinely routed on disk
- [x] A real second run never re-proposes an already-approved Thread — only still-`"Unsorted"` Threads are considered
- [x] Real, final backfill counts recorded in the Implementation Log
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change beyond a genuine defect fix discovered live during this run.
- Hand-classifying any of the 26 existing folders by name alone — evidence-based only, unaffected here.
- Wiring this Job into `run_housekeeping_pass()`'s recurring schedule — stays manually-triggered, per the story's own Constraint.

---

## Context / Notes

Mirrors `REQ-SB-73-US-01-T04`'s own sibling shape (the heaviest task by real-verification cost, not code volume) — a real, on-demand, full-corpus pipeline invocation can take meaningfully longer wall-clock time than its code volume suggests; background the real endpoint call with unbuffered output if it runs long, per this project's own established technique.

---

## Implementation Log

**Real vault, whole-sprint timeline (2026-08-19, this session):**
1. `T01`'s own real, direct `propose_customer_backfill()` call = the real
   FIRST backfill run against the full corpus (132 real Threads at that
   time; 577.9s): 26 batches, 106 Threads matched, 26 left `Unsorted`.
2. `T02`'s own direct verification calls routed 2 real batches (`"Aldar"`,
   3 Threads; `"TAQA"`, 7 Threads, new Customer) — real writes.
3. `T05`'s own component check re-triggered the real orchestrating
   endpoint (`T05`'s own Implementation Log has the full defect-fix
   story: a real `500` from a transient Compass connection drop, fixed
   in scope by adding per-Thread failure isolation to `propose_customer_
   backfill()`, then a clean real `200`, 480.0s, 123 Threads — 23 new
   batches, 29 left `Unsorted`, 0 failed). `T05` also exercised one real
   approve round trip each for routing (`"LinkedIn"`) and archival
   (`"Google"`) via the real HTTP surface.

**`[REQ-SB-74-US-01-AC-09]` PASS — real, this task's own second real
endpoint call (2026-08-19).** With `"LinkedIn"`'s one real Thread already
approved/routed (`T05`), re-ran `POST /poc/librarian-propose-customer-
backfill` again for real (483.4s, 122 still-`Unsorted` Threads at start):
20 new batches, 30 left `Unsorted`, 0 failed. Programmatically confirmed:
the just-approved LinkedIn Thread's own path does NOT appear in ANY
batch's own `thread_paths` this run; its `customer` frontmatter is still
`"LinkedIn"` (not reverted); every single Thread path named across every
batch in this run is genuinely, currently `customer: "Unsorted"` (set-
difference check, real result: empty — zero false inclusions).

**Real, final backfill counts (as of this session's own last real run,
2026-08-19):** 133 real Threads total in the corpus by the end of this
session (grew from 132 mid-session — a new real message arrived; a real,
disclosed operational fact, not a defect). 10 real Threads genuinely
routed on disk this session (`"Aldar"` × 3, `"TAQA"` × 7). 1 real Customer
folder genuinely archived (`"Google"` → `Work/Archive/Customers/Google/`,
plus `"Twitter"` from `T04`'s own direct verification — 2 real archivals
total this session). 1 brand-new real Customer folder created
(`"TAQA"`).

**Real Pending Approvals outstanding at session end (never auto-approved
— flagged for operator review, see `REVIEW-QUEUE.md`):** 64 pending
`propose_customer_backfill_routing` records, 31 pending `propose_
customer_archival_candidate` records — real, but with SUBSTANTIAL
duplication across this session's 3 real full-corpus trigger points
(`T01`, `T05`'s component check, `T06`'s own AC-09 re-run), each an
unavoidable real, disclosed cost of `ADR-055`'s own accepted "no
idempotency guard on `trigger="direct"`" operational risk, restated
explicitly by the launching agent's own instructions ("propose against
real data,... do NOT auto-approve/mass-process unattended"). This coder
session deliberately did NOT bulk-decline the stale duplicate rounds —
that is itself a form of unattended mass-processing of real records the
operator has not reviewed, even in the declining direction — beyond the
handful of individually-verified/protected records named above (`AC-06`/
`AC-07`'s own decline tests; `T05`'s own real approve round trip; and 2
declines of a real, discovered false-positive nuance below). Left for
the operator's own real review and consolidation, per `ADR-055`'s own
explicit posture.

**A real, disclosed nuance encountered live, not a defect (extends `T03`'s
own abstract finding with real, concrete evidence):** across `T05`'s
component check and this task's own re-run, `"Aldar"` and `"LinkedIn"` —
BOTH already real-approved with real routed Threads earlier in THIS same
session — were each proposed AGAIN as `zero-match-this-pass` archival
candidates, since their own real Thread-match evidence was already fully
consumed (routed away from `"Unsorted"`) by an earlier pass, and no
customer-history check exists across passes (`propose_customer_archival_
candidates` deliberately consumes only THIS SAME pass's own evidence, per
`ADR-055` Decision 5 — literally correct per Scenario 4's own "this pass"
wording, not a code defect). Both real, live instances were explicitly
DECLINED by this session (never approved) to protect real, actively-used
Customer data from being wrongly archived. **Flagged to `REVIEW-QUEUE.md`**
as a real, disclosed operational finding for a human decision on whether a
future story should add a "has real, currently-linked Threads" cross-pass
exclusion to `propose_customer_archival_candidates` — out of THIS story's
own locked ACs, which this build satisfies exactly as specced.

**Also observed, not a defect:** the SAME real Thread was classified
slightly differently by Compass across repeated real passes for a small
number of customers (e.g. `"TAQA"`'s one real remaining Unsorted-thread
match, `"SimplAI"`) — ordinary LLM non-determinism across independent
calls, not a parsing or logic defect; `detect_customer_for_thread` itself
is unchanged from `T01`'s own build.

gate: clear 2026-08-19 — no locked AC left unverified; the archival
false-positive-across-passes nuance and the real pending-approval
duplication are both real, disclosed operational findings (not code
defects against any locked AC), written to `REVIEW-QUEUE.md` for the
operator's own review per `Implementation/Pipeline.md`'s "scope-internal
judgement call" logging convention.
