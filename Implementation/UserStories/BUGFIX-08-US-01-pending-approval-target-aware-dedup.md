---
id: BUGFIX-08-US-01
title: Pending Approvals gain a target-aware dedup check — closes the concurrent-trigger race (BUG-029) and same-target reprocessing duplication (BUG-030)
requirement_ids: [BUG-029, BUG-030]
requirement_section: "BUGS.md → BUG-029, BUG-030"
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-056 created — architect pass, /plan-tasks step 1). Decomposer pass complete (both ACs locked, both mapped to AC-tagged verification steps, depends_on acyclic) — status advanced to Ready per pipeline convention (gate stays flagged for the ADR review; forward progress is not blocked on it)."
sprint: "SPRINT-071"
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-08-US-01 — Pending Approvals gain a target-aware dedup check

## Story

**As a** Second Brain operator relying on the Pending Approvals list as an
accurate, once-per-real-decision-point queue
**I want** a Pending Approval to be deduplicated against any other
already-unresolved Pending Approval that targets the same real thing —
regardless of which trigger source (`scheduled`, `direct`, `background`)
asked for it, and regardless of how many capture ticks reprocess the same
target before it's resolved
**So that** I see exactly one live decision point per real event/target,
instead of the same meeting-capture run, the same staged email, or the
same Customer-backfill batch piling up 2–17 duplicate, never-resolved
records I have to manually sort through and decline one-by-one

## Context

Triage batch: `BUG-029` and `BUG-030` — both logged `2026-08-19`, both
`Open` at triage time, both root-caused during the same investigation
session, both explicitly disclosed by their own `BUGS.md` notes as
"likely the same fix."

### BUG-029 — `meeting-capture`'s `run_capture_now` fires twice concurrently, creating a permanent duplicate Pending Approval (Logic, Major)

- **Repro, confirmed live against real, current data** (`GET
  /pending-approvals`): two real records for `agent_id:
  "meeting-capture"`, `action_id: "run_capture_now"`, both `status:
  "pending"` — `4e5ef1403765` (`trigger: "scheduled"`, created
  `2026-08-14T11:38:31.199941Z`) and `424ad11f9f8f` (`trigger: "direct"`,
  created `2026-08-14T11:38:31.205701Z`) — **5.76 milliseconds apart**,
  identical description (`"Run Capture Now (Meeting Capture)"`). Neither
  was ever resolved — both sat `pending` for 5 real days until this
  session's cleanup pass declined the `direct` one.
- **Expected:** one real "Meeting Capture wants to run" decision point
  per real trigger event, regardless of which code path (scheduler tick
  vs. manual dispatch) fired it.
- **Actual, confirmed by direct code reading** (`pending_approval_
  registry.py::create_pending_approval`): the idempotency guard is scoped
  to `trigger == "background"` ONLY (`ADR-018` point 2) — `"scheduled"`
  and `"direct"` are both deliberately exempted, on the documented
  reasoning that "each is a distinct, deliberate user request." That
  assumption breaks here: a scheduled interval tick
  (`agent_schedule_registry.dispatch_with_shared_lock`, called via
  `capture_scheduler._build_scheduled_tick`) and a manual "Run Capture
  Now" dispatch (`agent_schedules_router.py`, `trigger="direct"`, line
  ~110) landed within the same real 6ms window and both reached
  `skill_registry.invoke_skill` — neither trigger source knows about the
  other, and `dispatch_with_shared_lock`'s own shared lock only
  serializes actual EXECUTION, not the act of asking for approval before
  execution starts.
- **Note (BUG-029's own):** root cause is architectural (the
  `"direct"`/`"scheduled"` exemption from dedup, correct for most real
  call sites, is wrong for two independent trigger sources racing for the
  SAME logical action) — needs an architect pass, not a one-line patch.

### BUG-030 — A staged email that generates a classification/routing Pending Approval is reprocessed on every later capture tick, creating a fresh duplicate each time (Logic, Major)

- **Repro, confirmed live against real, current data** (`GET
  /pending-approvals`): 301 real `"Compass couldn't classify ..."`
  proposals and 50 real `"Route-to-Project guesses ..."` proposals for
  `agent_id: "email-capture-pipeline"`, `trigger: "direct"` — with real,
  confirmed EXACT-duplicate description groups (same email subject +
  sender repeated 2×–6× across different `created_at` timestamps spanning
  hours/days), plus 15 real, generic `"Process Staged Email (Email
  Capture Pipeline)"` records with identical description text. The same
  real pattern was independently confirmed in `librarian-housekeeping`'s
  Customer-backfill proposals (13 real duplicate groups, one repeated
  17×) during `SPRINT-068`'s own build.
- **Expected:** a staged email/Thread that already has an unresolved
  Pending Approval covering it should not generate a second, identical
  one on the next capture tick.
- **Actual, confirmed by direct code reading**
  (`email_classification.py::route_to_project`): each proposal call site
  uses `trigger="direct"`, deliberately exempted from `create_pending_
  approval`'s own idempotency guard (`ADR-018` point 2 — "a single
  pipeline tick can legitimately produce multiple distinct routing
  proposals across different new Threads," true and correct BETWEEN
  different Threads). `route_to_project` itself already guards against
  re-proposing on a Thread UPDATE (`if not thread_result["created"]:
  return None`) — but nothing prevents the SAME staged email being
  treated as a brand-new Thread again on a LATER capture tick if it was
  never actually consumed/marked-resolved after its first pass generated
  a Pending Approval. The existing `"background"`-only, per-agent-scoped
  guard can't fix this even if reused as-is — it would incorrectly
  collapse proposals for genuinely DIFFERENT real emails/Threads into
  one, which `ADR-018` correctly avoided; what's actually missing is a
  PER-TARGET check ("does a pending approval already exist for this
  exact email/Thread"), not a per-agent one.
- **Note (BUG-030's own):** same underlying gap as `BUG-029` —
  `create_pending_approval` has no way to dedupe two proposals that are
  targeting the same real thing when trigger isn't `"background"`. Also
  affects `librarian_housekeeping.propose_customer_backfill`/`propose_
  customer_archival_candidates` (confirmed live during `SPRINT-068`) —
  likely the SAME fix (a target-aware idempotency check, not just
  agent-scoped) closes all three real call sites at once. Needs an
  architect pass to decide the right shape (e.g. a caller-supplied
  `dedupe_key` parameter on `create_pending_approval`, checked regardless
  of `trigger`).

### Code read this pass (confirms both notes' claims, does not pre-decide a fix)

- `src/backend/app/business/pending_approval_registry.py::
  create_pending_approval` — idempotency guard fires only when `trigger
  == "background"`, matching a record on `agent_id` + `trigger ==
  "background"` + `status == "pending"` alone (no target/payload
  comparison at all). `"scheduled"`, `"direct"`, and `"chat"` all skip
  this check entirely today.
- `src/backend/app/business/email_classification.py::route_to_project` —
  every real proposal call site passes `trigger="direct"`, by design, so
  it never reaches the guard above.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` —
  `propose_customer_backfill` and `propose_customer_archival_candidates`
  both call `create_pending_approval(..., trigger="direct", ...)` at
  their own proposal sites; `propose_customer_backfill`'s own docstring
  claims its Unsorted-Thread filtering "gives Scenario 9's own
  idempotency for free," but `BUG-030`'s own live evidence (13 real
  duplicate groups, one repeated 17×, confirmed during `SPRINT-068`)
  shows that claim does not hold once a batch has an unresolved
  approval sitting pending across more than one capture tick — flagged
  here for the architect's attention, not resolved by this pass.
- `src/backend/app/business/agent_schedule_registry.py::dispatch_with_
  shared_lock` — the ONE function every real scheduled/on-demand trigger
  passes through; its `asyncio.Lock` serializes actual dispatch/execution
  only (`async with lock: ... invoke_skill(...)`), never the
  approval-creation step that can happen inside that dispatch for a
  Supervised, mutating action — confirming BUG-029's own claim that the
  shared lock does not protect against two trigger sources both reaching
  `create_pending_approval` in the same narrow window.
- `src/backend/app/api/agent_schedules_router.py` — the `trigger="direct"`
  call site (`dispatch(agent_id, capability_id, trigger="direct")`) that
  races against a `trigger="scheduled"` call into the same `dispatch_
  with_shared_lock`/`dispatch_with_dedicated_processing_lock` functions.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs this at /plan-tasks. Per the triage-mode
contract: one scenario per bug, each scenario IS that bug's regression
criterion. Both scenarios describe OUTCOMES only — the dedup mechanism
itself (e.g. a dedupe_key parameter) is explicitly left to the architect,
per both bugs' own disclosed notes; see ## Notes. -->

### Scenario 1: Two near-simultaneous trigger sources for the same real action never produce two live Pending Approvals (BUG-029)

```gherkin
Given a Supervised agent's mutating action (e.g. meeting-capture's
    `run_capture_now`) is about to require approval
  And a scheduled trigger and a direct/manual trigger both independently
    request approval for that same agent/action within the same narrow
    real-world window, neither trigger source aware of the other
When both requests reach the Pending Approval creation path
Then exactly one Pending Approval record exists in `status: "pending"`
    for that action afterward — the second trigger source's request is
    recognized as covering the same already-pending decision point and
    does not create a second, duplicate record
  And the one surviving record is still resolvable (approve/decline)
    exactly as any other Pending Approval is today
```
<!-- AC-ID: BUGFIX-08-US-01-AC-01 -->


### Scenario 2: A staged email/Thread with an unresolved Pending Approval is not reprocessed into a duplicate on a later capture tick (BUG-030)

```gherkin
Given a staged email/Thread already has an unresolved (`status:
    "pending"`) Pending Approval covering it — e.g. a Compass
    classification-failure proposal or a Route-to-Project routing guess
When a later capture tick processes staged email/Thread data and would,
    without this fix, treat that same staged email/Thread as new again
Then no second, duplicate Pending Approval is created for that same
    email/Thread
  And the existing unresolved Pending Approval remains the only live
    record covering that target, until it is actually resolved
    (approved or declined)
```
<!-- AC-ID: BUGFIX-08-US-01-AC-02 -->


## Affected Screens

- None — backend only. Both bugs surface indirectly in the Pending
  Approvals list (`html-prototype/my-day-approvals.html`'s drill-down
  list, per `ADR-018`'s own approved surface) as duplicate rows, but the
  fix is entirely dedup logic inside `pending_approval_registry.py` and
  its callers — no prototype markup/behaviour changes. The existing list
  rendering is correct today; it simply has fewer, non-duplicate records
  to render once this fix ships.

## Dependencies

- **Blocked by:** none — `create_pending_approval`, `route_to_project`,
  `propose_customer_backfill`/`propose_customer_archival_candidates`,
  `dispatch_with_shared_lock`, and `agent_schedules_router.py`'s dispatch
  call site are all already `Done` and already live; this fix only adds a
  target-aware dedup check to already-existing call paths.
- **Related to:** `ADR-018` point 2 (the existing `trigger ==
  "background"`-only idempotency guard this fix must extend/correct
  without breaking the legitimate cross-target case it protects — e.g. a
  single pipeline tick producing several proposals for genuinely
  DIFFERENT real emails/Threads/Customers must remain unaffected).
- **Related to:** `src/backend/app/business/pending_approval_registry.py`,
  `src/backend/app/business/email_classification.py`,
  `src/backend/app/business/pipelines/librarian_housekeeping.py`,
  `src/backend/app/business/agent_schedule_registry.py`,
  `src/backend/app/api/agent_schedules_router.py` — the real call sites
  named by both bugs' own root-cause notes.
- **External:** none new.

## Constraints

- **Must not weaken or remove `ADR-018` point 2's existing, correct
  `trigger == "background"` per-agent dedup behaviour** — that guard
  stays valid for the case it was built for.
- **Must not collapse proposals for genuinely different real targets
  into one** — e.g. two different staged emails, two different Threads,
  or two different Customer-backfill batches must each still get their
  own Pending Approval. The dedup this story asks for is target-scoped
  ("does an unresolved approval already exist for THIS specific
  email/Thread/action"), never agent-scoped alone.
- **The exact dedup mechanism is explicitly NOT decided by this story** —
  both `BUG-029` and `BUG-030` disclose this needs a real architect pass
  (e.g. a caller-supplied `dedupe_key` parameter on `create_pending_
  approval`, checked regardless of `trigger`). Per this pipeline's
  "Gherkin specifies outcome, not mechanism" convention, the mechanism
  decision belongs to `/plan-tasks`'s architect step — recorded as an
  open question in `## Notes` below, not pre-decided here.
- **Covers all three real call sites named across both bugs' notes** —
  `pending_approval_registry.create_pending_approval` (the shared
  primitive), `email_classification.route_to_project`, and
  `librarian_housekeeping.propose_customer_backfill`/`propose_customer_
  archival_candidates` — plus the `agent_schedule_registry.dispatch_
  with_shared_lock`/`agent_schedules_router.py` race path BUG-029 traces
  through. Whether this becomes one shared-primitive change plus
  call-site updates, or something else, is the architect's/decomposer's
  own scoping call.

## Implementation Tasks

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-08-US-01-T01 | backend | Add the additive, optional `dedupe_key` parameter to `create_pending_approval` (second, independent idempotency check alongside the existing `trigger == "background"` guard) and wire `skill_registry.py::invoke_skill`'s central Supervised+mutates gate to compute `dedupe_key = f"{agent_id}:{skill_id}"` internally | `src/backend/app/business/pending_approval_registry.py`, `src/backend/app/business/skill_registry.py` | `../Tasks/BUGFIX-08-US-01-T01-dedupe-key-registry-and-invoke-skill.md` |
| BUGFIX-08-US-01-T02 | backend | Pass a per-target `dedupe_key` into `create_pending_approval` at the four remaining named call sites: `route_to_project`, `_create_classification_failure_pending_approval`, `propose_customer_backfill`, `propose_customer_archival_candidates` | `src/backend/app/business/email_classification.py`, `src/backend/app/business/pipelines/librarian_housekeeping.py` | `../Tasks/BUGFIX-08-US-01-T02-dedupe-key-email-and-librarian-call-sites.md` |

**Dependency-graph summary:** `BUGFIX-08-US-01-T01` has `depends_on: []` (the shared
primitive — must land first). `BUGFIX-08-US-01-T02` has
`depends_on: [BUGFIX-08-US-01-T01]` — its four call sites all pass the new `dedupe_key`
keyword argument, which only exists once `T01` lands. Linear chain, acyclic, two tasks.

## Definition of Done

- [x] Both acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected — including that `ADR-018` point 2's
      existing background-trigger dedup stays intact and no genuinely
      different real target is ever incorrectly collapsed into another
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test
      tooling still pending; both ACs verified live via manual mode per `Pipeline.md`'s
      default, see both tasks' own `## Implementation Log`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-029` and `BUG-030` flipped `In Sprint → Closed` in both
      `BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror once this story is
      `Done`

---

### Coder pass (`/implement-sprint SPRINT-071`, 2026-08-19) — both tasks `Done`, story `Done`

Both `BUGFIX-08-US-01-T01` and `BUGFIX-08-US-01-T02` are `Done`; both locked ACs
(`BUGFIX-08-US-01-AC-01`, `BUGFIX-08-US-01-AC-02`) verified live against the real, running
backend and the real, configured vault/store, per each task's own `## Implementation Log`.
`BUG-029` and `BUG-030` flipped `In Sprint → Closed` in `BUGS.md` and `BACKLOG.md`'s `## Bugs`
mirror. `gate` stays `flagged` — the standing `ADR-056` review (trigger 3, architect pass) is
carried forward unchanged for the human to skim alongside this closure; no new MUST-FLAG trigger
fired during the coder pass itself (both tasks' own scope-internal judgement calls — the T01
pre-existing-legacy-record disclosure, and T02's bounded-Job-run plus its own self-corrected
archival-candidate cleanup — are logged in each task's `## Implementation Log` for spot-check,
not escalations).

## Non-Goals / Out of Scope

- **Deciding the dedup mechanism's exact shape** (parameter name,
  matching-key derivation, storage change if any) — explicitly deferred
  to the architect at `/plan-tasks`.
- **A general-purpose dedup/idempotency framework** beyond what's needed
  to close these three real call sites — no speculative extension to
  call sites neither bug names.
- **Cleaning up the already-existing duplicate records** in the live
  `.second-brain/agent_pending_approvals.json` store (the 2 real
  meeting-capture records, 301+50+15 real email-capture-pipeline
  records, 13 real librarian-housekeeping records) — this story fixes
  the creation path going forward; a one-time data cleanup, if wanted, is
  a separate, explicit operator action, not part of this fix's
  acceptance criteria.
- **Changing the Pending Approvals list UI/rendering** — confirmed no
  screen change is needed (see `## Affected Screens`).
- **Re-litigating `ADR-018` point 2's own reasoning for the cross-target
  case** — it remains correct and unmodified; this story only closes the
  same-target gap both bugs found.

## Notes

**Why one story for two bugs:** both `BUG-029`'s and `BUG-030`'s own
`BUGS.md` notes independently name the exact same underlying gap
(`create_pending_approval` has no way to dedupe two proposals targeting
the same real thing once `trigger` isn't `"background"`) and explicitly
predict "likely the SAME fix" closes both. Batching them into one story
avoids the architect making the same target-aware-dedup design decision
twice.

**Why the mechanism is left open (per the task's own instruction and
this pipeline's convention):** Gherkin specifies outcome, not mechanism.
Both scenarios above describe the observable outcome ("exactly one live
Pending Approval per real target/event") without naming HOW that's
achieved. The architect's own candidate direction, already sketched in
`BUG-030`'s note and restated here for continuity (not decided, subject
to revision at `/plan-tasks`): a caller-supplied `dedupe_key: str | None`
parameter on `create_pending_approval`, checked against any other
`status: "pending"` record sharing the same `dedupe_key` regardless of
`trigger` value, additive alongside the existing `trigger ==
"background"` per-agent guard (`ADR-018` point 2, unmodified). Each of
the three call-site families would then supply its own natural key (e.g.
`f"{agent_id}:{action_id}"` for BUG-029's race; the staged email's own
stable identifier, or the Thread's own path/id, for BUG-030's routing
and classification-failure proposals; the Customer-backfill batch's own
identity for `librarian_housekeeping`). This is a starting point for the
architect, not a locked decision.

**Discrepancy flagged for the architect's attention (not a MUST-FLAG
trigger for this pass):** `propose_customer_backfill`'s own docstring
claims its Unsorted-Thread filtering already gives idempotency "for
free," but `BUG-030`'s own live evidence (13 real duplicate groups, one
repeated 17×, `SPRINT-068`) shows that claim doesn't hold once a batch
has an unresolved approval spanning more than one capture tick — the
filtering-based reasoning and the live observed behaviour disagree. This
doesn't block writing a clear regression scenario (the live evidence is
authoritative), but the architect should account for it when scoping the
`librarian_housekeeping` call sites' fix.

**Why `gate: clear` — trigger-by-trigger:**
- Trigger 1 (material assumption): none beyond what both bugs' own notes
  already disclose. This pass re-confirmed every claim by direct reading
  of the real, current `pending_approval_registry.py::create_pending_
  approval`, `email_classification.py::route_to_project`,
  `librarian_housekeeping.py`'s two propose functions, `agent_schedule_
  registry.py::dispatch_with_shared_lock`, and `agent_schedules_
  router.py`'s dispatch call site — not assumed from the bug text alone.
  The dedup mechanism itself is deliberately left undecided (see above),
  which is this pipeline's normal deferral pattern, not a filled gap.
- Trigger 2 (Draft/unfinalised requirement relied on): not applicable —
  `BUG-029`/`BUG-030` are finalised `Open` bug-ledger entries, not PRD
  requirements, and carry no unresolved ambiguity about what "Open"
  means here.
- Trigger 3 (ADR created/changed): not applicable to the analyst — no ADR
  authored or implicated by this pass; whether the architect's eventual
  mechanism needs a new/amended ADR is that role's own call at
  `/plan-tasks`.
- Trigger 4 (wrote an `ESCALATIONS.md` entry): not applicable — none
  written.
- Trigger 5 (oversized): no — two scenarios, one shared root cause,
  touching one primitive plus a small, named set of call sites (all
  already enumerated by the bugs' own notes); fits one working context.
  Whether the decomposer later splits the fix into more than one task
  (shared primitive vs. per-call-site wiring) is a scoping call for
  `/plan-tasks`, not a reason to split this story now.
- Trigger 7 (contradictory inputs): the `propose_customer_backfill`
  docstring-vs.-live-evidence discrepancy noted above was considered —
  it is not a contradiction that blocks writing a clear regression
  scenario (BUG-030's live evidence resolves it: duplicates are
  observed regardless of the docstring's claim), so it's flagged in
  `## Notes` for the architect rather than escalated.
- Trigger 8 (multiple equally-valid interpretations / genuinely
  unclear): none for the OUTCOME each scenario specifies — "one live
  Pending Approval per real target/event, across trigger sources and
  across capture ticks" is unambiguous in both bugs' own "Expected"
  text. The mechanism has multiple equally-valid shapes, which is
  exactly why it's deferred to the architect rather than guessed here —
  this is the pipeline's designed division of labour, not an
  unclear-requirement flag.

`gate: clear` 2026-08-19 (analyst pass) — no triggers fired (both bugs' own
notes pre-disclose the architect-deferred mechanism, no ADR/escalation
implicated by this pass, single shared-root-cause scope, both scenarios
independently verifiable, no requirement-level contradiction, one
unambiguous outcome per scenario with the mechanism intentionally left
open).

---

### Architect pass (`/plan-tasks` step 1, 2026-08-19) — mechanism decided, `gate: flagged` (trigger 3)

**Mechanism decided:** `pending_approval_registry.create_pending_approval`
gains one new optional, additive parameter, `dedupe_key: str | None =
None`. When supplied, a SECOND idempotency check runs — alongside, never
replacing, `ADR-018` point 2's existing `trigger == "background"` guard —
matching an existing `status == "pending"` record on the same `agent_id` +
`dedupe_key`, regardless of `trigger`, and returning it instead of
creating a duplicate. Full reasoning, alternatives considered, and
consequences: [ADR-056](../Architecture/ADR.md).

**`dedupe_key` shape per real call site** (each namespaced
`"{action_id}:{stable_target_identifier}"` so two different action kinds
sharing one `agent_id` never collide):
- `skill_registry.py::invoke_skill`'s own Supervised+mutates gate —
  `f"{agent_id}:{skill_id}"`, computed INSIDE `invoke_skill` itself. Zero
  change needed to any of its own callers (`dispatch_with_shared_lock`,
  `skills_router.py`, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`) — this is the generalized, permanent fix for
  BUG-029's own class of problem (any Supervised mutating Skill racing
  across trigger sources for the same decision point), not scoped to
  `meeting-capture`/`run_capture_now` alone.
- `email_classification.py::route_to_project` —
  `f"route_thread_to_project:{thread_result['conversation_id']}"`.
- `email_classification.py::_create_classification_failure_pending_
  approval` — `f"acknowledge_classification_failure:{email['conversation_id']}"`.
- `librarian_housekeeping.py::propose_customer_backfill` —
  `f"propose_customer_backfill_routing:{customer}"`, per batch.
- `librarian_housekeeping.py::propose_customer_archival_candidates` —
  `f"propose_customer_archival_candidate:{customer}"`, per candidate.

**BUG-029 race resolution — `dedupe_key` alone, no lock restructuring
needed.** Direct reading of `agent_schedule_registry.dispatch_with_shared_
lock` confirms its `asyncio.Lock` already wraps the entire `skill_
registry.invoke_skill` call (via `asyncio.to_thread`) inside its critical
section, for both `"scheduled"` and `"direct"` dispatch of the same
`(agent_id, capability_id)` pair — a single-threaded `asyncio.Lock`'s own
check-then-acquire has no yield point when uncontended, so the LITERAL
race the live evidence measured is not structurally reproducible against
this already lock-consolidated path as it stands today. The live evidence
most likely either predates `ADR-037`'s shared-lock consolidation, or
crossed the separate, also-real gap between the bundled-hourly
`run_capture_if_idle` path and a standalone per-agent-schedule `dispatch_
with_shared_lock` call — two different code paths that both reach
`create_pending_approval` for the same agent without being the literal
same function call. Either way, the `dedupe_key` check at the point of
persistence is the correct, deterministic, caller-independent guarantee —
not a re-derivation of, or reliance on, precise lock-timing behaviour,
which is real today but fragile to depend on alone and not independently
unit-testable. No change to `agent_schedule_registry.py`'s lock mechanism
is made or needed; see `ADR-056`'s Alternatives Considered for the full
reasoning against restructuring the lock instead.

**`propose_customer_backfill` docstring discrepancy — resolved, not a
wrong claim, an incomplete one.** The docstring's "this filtering alone
gives Scenario 9's own idempotency for free" claim IS correct — but only
for a Thread that has been ALREADY APPROVED AND WRITTEN (its `customer`
frontmatter is no longer `"Unsorted"` once `finalize_customer_backfill_
routing` has actually run). It does NOT hold for a Thread with an
UNRESOLVED, still-`"pending"` proposal — that Thread's frontmatter is
deliberately left `"Unsorted"` until approval (the function's own
"proposal only, never a silent write" contract), so a repeated Job run
before that first proposal resolves re-scans the SAME still-`"Unsorted"`
Threads and re-batches them into a brand-new duplicate. This is exactly
the case `ADR-055`'s own Consequences already named ("a second manual
trigger... will re-propose the SAME still-Unsorted Threads into a NEW,
separate pending batch") without closing, and exactly what BUG-030's live
evidence (13 real duplicate groups, one repeated 17×, `SPRINT-068`) hit.

**Architecture scope:** §Agent Working Modes & Pending Approvals
(`architecture.md`, `REQ-SB-21-US-01`, see `ADR-018` + `ADR-020` +
`ADR-056`) — the decomposer/coder are bounded to this section (the
`dedupe_key` addition to `create_pending_approval` and its named real
call sites) plus the shared-lock section already documented under "Per-
Agent Scheduler" (`ADR-037`, read-only reference — no change made there).

**Why `gate: flagged` (trigger 3):** this pass created a new ADR
(`ADR-056`) extending `ADR-018` point 2 — a structural change to
`create_pending_approval`, the shared primitive used by every Pending-
Approval-creating call site in the codebase. Per the MUST-FLAG list,
creating/changing an ADR always flags the story for a human look,
regardless of how confident the reasoning is — the pipeline does not halt
here; the decomposer still runs so the human reviews the ADR and the
resulting tasks together in one pass, per `Pipeline.md`.

---

### Decomposer pass (`/plan-tasks` step 2, 2026-08-19)

**ACs locked, wording tightened only (no scope change):**
- `BUGFIX-08-US-01-AC-01` (Scenario 1 — `BUG-029`: two near-simultaneous,
  different-trigger requests for the same agent/action produce exactly
  one live Pending Approval, still normally resolvable).
- `BUGFIX-08-US-01-AC-02` (Scenario 2 — `BUG-030`: a staged email/Thread
  already covered by an unresolved Pending Approval is never reprocessed
  into a duplicate on a later capture tick).

Both are real, directly-observable outcomes (a `pending_approval_registry`
record count/id comparison), verifiable without any UI/HTTP layer —
neither was marked `locked: false`.

**Task split — two tasks, matching the architect's own named scoping
call:**

- `BUGFIX-08-US-01-T01` — the shared-primitive change
  (`create_pending_approval` gains `dedupe_key`) plus
  `skill_registry.py::invoke_skill`'s central Supervised+mutates gate,
  which computes its own `dedupe_key` internally with zero caller
  changes. This one task fully closes `BUG-029`'s own class of problem
  (any Supervised mutating Skill racing across trigger sources) and is the
  one atomic unit every other call site depends on. `depends_on: []`.
- `BUGFIX-08-US-01-T02` — the four remaining named call sites
  (`route_to_project`, `_create_classification_failure_pending_approval`,
  `propose_customer_backfill`, `propose_customer_archival_candidates`),
  each a thin, mechanical addition of one `dedupe_key=` keyword argument
  to an already-existing `create_pending_approval` call, using a target
  identifier each function already has in local scope. Grouped as one
  task (not four) since none of the four additions is independently
  buildable/verifiable in a way that benefits from separate task
  boundaries — same shape, same file family, same mechanism, and all four
  together close `BUG-030`. `depends_on: [BUGFIX-08-US-01-T01]` — the new
  `dedupe_key` parameter must exist before any of these four calls can
  pass it.

No lock restructuring, no ADR of the decomposer's own, no third task —
`ADR-056`'s own Decision 3 (no change to `agent_schedule_registry.py`)
left nothing further to decompose there.

**AC → verification mapping:** `BUGFIX-08-US-01-AC-01` is tagged with
three real, live manual verification steps in `BUGFIX-08-US-01-T01`'s
`## Tests` (an isolated registry-level dedupe check, a real
`invoke_skill` scheduled-vs-direct race reproducing `BUG-029`'s own
repro shape, and a surviving-record-stays-resolvable check).
`BUGFIX-08-US-01-AC-02` is tagged with four real, live manual verification
steps in `BUGFIX-08-US-01-T02`'s `## Tests`, one per named call site,
including an actual double-run of the real `propose_customer_backfill`/
`propose_customer_archival_candidates` Jobs against the real, current
vault (the literal `BUG-030` repro shape) — with an explicit fallback to
a direct registry-level two-call check if the live vault currently has no
real Unsorted Thread to exercise the full Job path against, disclosed
either way. Every locked AC has at least one AC-tagged step — no hard
failure.

**Status transition:** `Draft → Ready`. All three status-transition
conditions are met: (a) both ACs are locked, (b) both locked ACs have at
least one AC-tagged verification step, (c) `depends_on`
(`T02 → T01`) is a simple two-node chain, acyclic. `status:` advances to
`Ready`; both task files are written at `status: Ready` in lockstep, per
this pipeline's own "status moves in lockstep with the story" rule.

**Gate stays `flagged` (trigger 3, unchanged from the architect's own
pass):** per `/plan-tasks`'s own convention — when the architect flags a
story for an ADR change, the decomposer still runs and advances `status:`
normally, but does NOT flip `gate:` to `clear`; the human reviews
`ADR-056` and this pass's resulting tasks together in one sitting, via
the architect's own already-filed `REVIEW-QUEUE.md` entry (no second,
duplicate entry added by this pass — same trigger, same review, one
pointer). No new MUST-FLAG trigger fired during this decomposer pass
itself: no material assumption beyond direct reading of the real current
`invoke_skill`/`route_to_project`/`_create_classification_failure_
pending_approval`/`propose_customer_backfill`/`propose_customer_
archival_candidates` bodies (confirming each one's exact existing
`create_pending_approval` call shape and each target identifier's real
local-scope availability before writing the tasks); no Draft/unfinalised
requirement relied on beyond `ADR-056` itself (already accounted for by
trigger 3); no new ADR authored by this pass; no `ESCALATIONS.md` entry;
not oversized (two small, mechanically-scoped tasks); no locked AC left
unverifiable; no contradictory inputs; and no genuinely unclear or
multiple-equally-valid task-boundary choice (the architect's own
call-site list and the "shared primitive first, thin call-site wiring
second" split are unambiguous).

---

### Product-owner pass (`/plan-sprints`, 2026-08-19)

Checked every `Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`.
This was the only `Ready`, ungrouped story found this pass — `REQ-SB-42-US-01`,
`REQ-SB-59-US-01` already carry a `sprint:` value (`SPRINT-039`, `SPRINT-059`
respectively) and were excluded as "not ungrouped." No existing `Draft` sprint to
append to (none found). Assigned its own new sprint, `SPRINT-071` — a single story
with a two-task linear `depends_on` chain (`T02 → T01`), nothing to partition or
sequence against any other sprint. Bugfix sprint, exempt from phase homogeneity per
`Pipeline.md` hard rule 8. The story's own standing `gate: flagged` (`ADR-056`
review) is disclosed and carried forward unchanged — it does not block sprint
grouping or block `/implement-sprint`; the human reviews `ADR-056` and this story's
tasks together via the architect's own already-filed `REVIEW-QUEUE.md` entry.

`gate: clear` 2026-08-19 (product-owner pass) — grouping unambiguous: one story, one
dependency chain, one sprint; no dependency graph contradicted; no phase mixed; no
cross-sprint dependency introduced; nothing blocked. Sprint advanced `Draft → Ready`.
