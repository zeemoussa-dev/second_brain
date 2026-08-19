---
id: BUGFIX-08-US-01-T01
title: Add target-aware dedupe_key to create_pending_approval and wire it into invoke_skill's central Supervised gate (BUG-029 fix)
parent_story: BUGFIX-08-US-01
requirement_id: BUG-029
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-08-US-01-T01 — Add target-aware `dedupe_key` to `create_pending_approval` and wire it into `invoke_skill`'s central Supervised gate

## Parent Story

- Story: [[BUGFIX-08-US-01]] — `../UserStories/BUGFIX-08-US-01-pending-approval-target-aware-dedup.md`
- Requirement: `BUGS.md` → `BUG-029` (bugfix story; no PRD requirement anchor). Mechanism: [ADR-056](../Architecture/ADR.md).

---

## Objective

Give `pending_approval_registry.create_pending_approval` a new, additive, optional
`dedupe_key: str | None = None` parameter that — when supplied — matches an existing
`status == "pending"` record sharing the same `agent_id` AND `dedupe_key`, regardless of
`trigger`, and returns it instead of creating a duplicate; wire `skill_registry.py::invoke_skill`'s
central Supervised+mutates gate to compute and pass `dedupe_key = f"{agent_id}:{skill_id}"`
internally, closing `BUG-029`'s race for every Supervised mutating Skill, not just
`meeting-capture`/`run_capture_now`.

---

## Starting State → End State

**Before / Inputs:**
- `create_pending_approval(agent_id, trigger, action_id, description, payload=None)`
  (`src/backend/app/business/pending_approval_registry.py`, lines 40-84) has exactly one
  idempotency check, scoped to `trigger == "background"` (`ADR-018` point 2) — matches on
  `agent_id` + `trigger == "background"` + `status == "pending"` alone, no target/payload
  comparison. `"scheduled"`, `"direct"`, `"chat"` all skip this check entirely.
- Stored records have no `dedupe_key` field at all today.
- `skill_registry.py::invoke_skill`'s Supervised+mutates gate (lines ~225-240) calls
  `create_pending_approval(agent_id=agent_id, trigger=trigger, action_id=skill_id,
  description=..., payload=args)` with no dedup protection beyond the `"background"`-only
  guard above — a `trigger="scheduled"` call and a `trigger="direct"` call for the SAME
  `(agent_id, skill_id)` pair can each independently create their own live Pending
  Approval (`BUG-029`'s own live evidence: two real records, `meeting-capture`/
  `run_capture_now`, 5.76ms apart, `trigger: "scheduled"` and `trigger: "direct"`).

**After / Outputs:**
- `create_pending_approval(agent_id, trigger, action_id, description, payload=None,
  dedupe_key: str | None = None)` — every existing zero-argument caller is unaffected by
  construction (default `None` skips the new check entirely, behaving exactly as before).
- When `dedupe_key` is not `None`: a SECOND, independent check runs alongside (never
  replacing) the existing `trigger == "background"` guard — if an existing record shares
  the same `agent_id` AND `dedupe_key` AND `status == "pending"` (regardless of that
  record's own `trigger` value), that existing record is returned unchanged; no new record
  is created.
- The stored record schema gains one new additive field, `"dedupe_key": str | None`,
  defaulting to `None` on every newly-created record where the caller didn't supply one —
  and implicitly absent/`None` on every pre-existing record in
  `.second-brain/agent_pending_approvals.json` (no migration needed; an absent key behaves
  identically to "no `dedupe_key` supplied").
- `skill_registry.py::invoke_skill`'s Supervised+mutates gate computes
  `dedupe_key = f"{agent_id}:{skill_id}"` internally, right before its existing
  `create_pending_approval` call, and passes it through — zero change to `invoke_skill`'s
  own external signature or to any of its real callers
  (`dispatch_with_shared_lock`, `skills_router.py`, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`).

---

## Files to Modify

- `src/backend/app/business/pending_approval_registry.py`:
  1. Add `dedupe_key: str | None = None` as a new keyword parameter to
     `create_pending_approval`, positioned after the existing `payload` parameter.
  2. Add the new dedupe check: when `dedupe_key is not None`, look for an existing
     `state["pending"]` record with matching `agent_id`, matching `dedupe_key`, and
     `status == "pending"` (no `trigger` filter) — return it immediately if found, exactly
     mirroring the existing `trigger == "background"` early-return shape immediately above
     it. This check must run independently of, and in addition to, the existing
     `trigger == "background"` check — do not merge the two into one combined condition.
  3. Add `"dedupe_key": dedupe_key` to the new record dict this function builds.
  4. Update the function's own docstring to describe the new parameter and its additive,
     opt-in nature — mirroring `payload`'s own docstring precedent (`ADR-021` point 4).
- `src/backend/app/business/skill_registry.py`:
  1. Inside `invoke_skill`'s Supervised+mutates branch (the block that calls
     `create_pending_approval` today, lines ~225-240), compute
     `dedupe_key = f"{agent_id}:{skill_id}"` and pass it as the new keyword argument on
     that call. No other line in this function changes.

No other file is in scope for this task — `email_classification.py` and
`librarian_housekeeping.py`'s call sites are `BUGFIX-08-US-01-T02`'s scope, not this one.

---

## Constraints

- Inherits from parent story — must not weaken or remove `ADR-018` point 2's existing
  `trigger == "background"` guard; it stays exactly as documented, unmodified, and runs
  independently of the new check.
- `dedupe_key` is additive and opt-in — every caller that does not pass it (every call
  site outside this task's own scope, until `BUGFIX-08-US-01-T02` lands) is behaviourally
  unaffected; do not give it a non-`None` default.
- The registry performs no parsing/derivation of `dedupe_key`'s value — it is opaque to
  the registry, meaningful only to the caller, mirroring `payload`'s own established shape
  (`ADR-021` point 4, restated by `ADR-056` point 2). Do not add any registry-side
  namespacing/validation logic.
- `skill_registry.py::invoke_skill`'s own external signature (`agent_id, skill_id, args,
  trigger`) does not change — `dedupe_key` is computed and consumed entirely inside the
  function; zero change required in any of its callers.
- Do not touch `agent_schedule_registry.py`'s shared-lock mechanism
  (`dispatch_with_shared_lock`/`dispatch_with_dedicated_processing_lock`/
  `run_capture_if_idle`) — `ADR-056` Decision 3 keeps it unmodified; this fix is
  deliberately independent of its timing guarantees.
- A `dedupe_key` match must return the EXISTING record's own stale `payload`/`description`
  unchanged — do not refresh it with the new, suppressed call's own arguments
  (`ADR-056`'s own accepted Consequence).

---

## Tests

**Manual verification steps (direct Python-shell calls against the real
`app.business.pending_approval_registry`/`app.business.skill_registry`/
`app.business.working_mode_registry` functions, run via the backend's own `.venv` against
the real, configured vault):**

1. [BUGFIX-08-US-01-AC-01] **Registry-level mechanism, isolated.** Call
   `create_pending_approval(agent_id="zz-verify", trigger="scheduled", action_id="run_capture_now",
   description="verify dedupe A", dedupe_key="run_capture_now:zz-verify")`, then immediately call
   `create_pending_approval(agent_id="zz-verify", trigger="direct", action_id="run_capture_now",
   description="verify dedupe B", dedupe_key="run_capture_now:zz-verify")` — two DIFFERENT
   `trigger` values, same `agent_id`+`dedupe_key`. Confirm the second call returns a dict with
   the identical `"id"` as the first call's return value (not a new id), and confirm its
   `"description"` is still `"verify dedupe A"` (the first call's, never overwritten). Confirm
   `list_pending_approvals(status="pending", agent_id="zz-verify")` returns exactly one record.
   Then call `resolve_pending_approval(<that id>, "declined")` to clean up this throwaway record
   and confirm it flips to `status: "declined"`.
2. [BUGFIX-08-US-01-AC-01] **Real end-to-end race, through `invoke_skill`.** Pick a real agent
   already granted a real `mutates: True` Skill (e.g. `agent_id="meeting-capture"`,
   `skill_id="run_capture_now"`, per `skill_registry._MIGRATION_GRANT_SEED`). Read and save its
   current working mode (`working_mode_registry.get_agent_working_mode`); if not already
   `"supervised"`, set it to `"supervised"` for the duration of this check. Call
   `skill_registry.invoke_skill(agent_id, "run_capture_now", args=None, trigger="scheduled")`
   immediately followed by `skill_registry.invoke_skill(agent_id, "run_capture_now", args=None,
   trigger="direct")` — mirroring `BUG-029`'s own real scheduled-vs-direct race. Confirm BOTH
   calls return `status: "pending"` with the IDENTICAL `pending_approval_id`. Confirm
   `pending_approval_registry.list_pending_approvals(status="pending", agent_id=agent_id)` shows
   exactly ONE record with `action_id == "run_capture_now"` (not two), and that record's own
   `dedupe_key == f"{agent_id}:run_capture_now"`. Restore the agent's original working mode
   afterward (skip the restore if it was already `"supervised"` beforehand) and resolve/decline
   the throwaway record so it doesn't linger as a real, unresolved Pending Approval.
3. [BUGFIX-08-US-01-AC-01] **Surviving record stays normally resolvable.** Using the single
   surviving record's id from step 2 (before declining it in that step's own cleanup, or as a
   fresh repeat of step 2 if step 2's record was already cleaned up), call
   `resolve_pending_approval(id, "approved")` — confirm it returns the record with
   `status: "approved"` and a non-null `resolved_at`, exactly as any ordinary Pending Approval
   resolves today. Proves the dedup mechanism affects only creation, never a surviving record's
   own resolvability.
4. Regression check (not itself a locked-AC step, but confirms `## Constraints` is respected):
   call `create_pending_approval` twice with the SAME `agent_id` and `trigger="background"` but
   NO `dedupe_key` — confirm the existing `ADR-018` point 2 background guard still fires exactly
   as before (second call returns the first's record). Then call it twice with the same
   `agent_id` but two DIFFERENT `dedupe_key` values — confirm two DISTINCT records are created
   (proves the new check never collapses genuinely different targets sharing one agent).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `create_pending_approval` gains an additive, optional `dedupe_key: str | None = None`
      parameter; every existing zero-argument caller is unaffected
- [x] When `dedupe_key` is supplied, a second, independent idempotency check matches on
      `agent_id` + `dedupe_key` + `status == "pending"`, regardless of `trigger`, and returns
      the existing record instead of creating a duplicate
- [x] The existing `trigger == "background"` guard (`ADR-018` point 2) stays unmodified and
      runs independently of the new check
- [x] Stored records gain the additive `"dedupe_key"` field
- [x] `skill_registry.py::invoke_skill`'s Supervised+mutates gate computes
      `dedupe_key = f"{agent_id}:{skill_id}"` internally and passes it through — zero change to
      `invoke_skill`'s own external signature or any of its callers
- [x] `BUGFIX-08-US-01-AC-01` (Scenario 1 / `BUG-029`) verified live: two near-simultaneous,
      different-trigger requests for the same agent/action produce exactly one live Pending
      Approval, still normally resolvable
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `email_classification.py::route_to_project`/`_create_classification_failure_pending_approval`
  and `librarian_housekeeping.py::propose_customer_backfill`/
  `propose_customer_archival_candidates` — `BUGFIX-08-US-01-T02`'s scope.
- Any change to `agent_schedule_registry.py`'s shared-lock mechanism.
- Cleaning up the already-existing real duplicate Pending Approval records in
  `.second-brain/agent_pending_approvals.json` — explicit story Non-Goal.
- Any UI/Pending Approvals list rendering change — confirmed no screen change needed.

---

## Context / Notes

Full reasoning, alternatives considered, and consequences: [ADR-056](../Architecture/ADR.md).
Architecture scope: `Implementation/Architecture/architecture.md` → §"Agent Working Modes &
Pending Approvals" (`REQ-SB-21-US-01`, see `ADR-018` + `ADR-020` + `ADR-056`) — the coder is
bounded to this section plus the shared-lock section already documented under "Per-Agent
Scheduler" (`ADR-037`, read-only reference — no change made there).

`BUGFIX-08-US-01-T02` (the remaining three call sites for `BUG-030`) `depends_on` this task —
it calls `create_pending_approval` with its own new `dedupe_key` argument, which only exists
once this task lands.

---

## Implementation Log

**Changes made (exactly as scoped, no deviation):**
- `pending_approval_registry.py::create_pending_approval` gained the additive
  `dedupe_key: str | None = None` keyword parameter, positioned after `payload`. A second,
  independent early-return check runs when `dedupe_key is not None`, matching `agent_id` +
  `dedupe_key` + `status == "pending"` (no `trigger` filter), mirroring the existing
  `trigger == "background"` check's shape without merging into it. New records now carry an
  additive `"dedupe_key"` field (`None` when the caller didn't supply one). Docstring updated
  to describe the new parameter, mirroring `payload`'s own precedent.
- `skill_registry.py::invoke_skill`'s Supervised+mutates branch now computes
  `dedupe_key = f"{agent_id}:{skill_id}"` immediately before its existing
  `create_pending_approval` call and passes it through. No other line changed; `invoke_skill`'s
  external signature and every real caller are untouched.

**Live verification — run via `.venv` against the real, configured vault/store**
(throwaway script `src/backend/.scratch/verify_dedupe_key_t01.py`, not part of `## Files to
Modify`, discarded after this run — mirrors this project's established throwaway-script
verification pattern):

- **[BUGFIX-08-US-01-AC-01] Step 1 — registry-level mechanism, isolated.** PASS. Two calls with
  the same `agent_id`/`dedupe_key` but different `trigger` ("scheduled" then "direct") returned
  the identical record id; the second call's `description` remained the first call's own
  ("verify dedupe A", never overwritten); `list_pending_approvals` showed exactly one pending
  `zz-verify` record. Cleaned up (declined).
- **[BUGFIX-08-US-01-AC-01] Step 2 — real end-to-end race through `invoke_skill`.** PASS on the
  load-bearing assertion: `invoke_skill("meeting-capture", "run_capture_now", trigger=
  "scheduled")` immediately followed by `invoke_skill(..., trigger="direct")` both returned
  `status: "pending"` with the IDENTICAL `pending_approval_id`, and the new record's own
  `dedupe_key == "meeting-capture:run_capture_now"` — confirming the fix collapses a real
  scheduled-vs-direct race for the same `(agent_id, skill_id)` into one record, closing
  `BUG-029`'s own class of problem. **Judgement call disclosed (not a MUST-FLAG trigger, scope-
  internal):** the live `agent_pending_approvals.json` store still has ONE pre-existing, real,
  unresolved legacy record for `meeting-capture`/`run_capture_now`
  (`4e5ef1403765`, `trigger: "scheduled"`, created `2026-08-14`, `dedupe_key` absent/`None` —
  the ORIGINAL `BUG-029` repro's `"scheduled"` half; its `"direct"` sibling was already declined
  during this session's earlier queue cleanup). Because that legacy record predates this fix and
  carries no `dedupe_key`, it correctly does NOT collapse with the new race's shared record (a
  pre-fix record with `dedupe_key: None` can never match a post-fix `dedupe_key` — by design, per
  `## Constraints`). This made the raw `list_pending_approvals(..., agent_id=...)` count read `2`
  momentarily during the race step, not `1` — but the count includes that untouched pre-existing
  legacy duplicate, not a second NEW duplicate created by this fix. Per the story's own explicit
  Non-Goal ("cleaning up already-existing duplicate records... is a separate, explicit operator
  action, not part of this fix's acceptance criteria"), the legacy record was deliberately left
  untouched by this task — cleaning it up was out of scope, not a fix failure. The agent's working
  mode was `"autonomous"` beforehand and was restored to `"autonomous"` after the check.
- **[BUGFIX-08-US-01-AC-01] Step 3 — surviving record stays normally resolvable.** PASS. The
  step-2 surviving record (`pending_approval_id` shared by both calls) was resolved via
  `resolve_pending_approval(id, "approved")`, returning `status: "approved"` with a non-null
  `resolved_at` — ordinary resolution, unaffected by the dedup mechanism.
- **Step 4 — regression (Constraints, not itself a locked AC).** PASS. Two `trigger=
  "background"` calls with no `dedupe_key` still collapsed to the same record (existing
  `ADR-018` point 2 guard unmodified). Two calls sharing one `agent_id` with two DIFFERENT
  `dedupe_key` values produced two DISTINCT records (no false collapse across genuinely
  different targets). All throwaway `zz-verify*` records cleaned up (declined); confirmed zero
  leftover.

**No pollution left in the real queue** beyond the one pre-existing, disclosed, out-of-scope
legacy `meeting-capture` record noted above (present before this task ran, untouched by it).

`gate: clear` 2026-08-19 — no MUST-FLAG trigger fired. No new dependency, no shared-interface
change beyond the task's own additive parameter (already the task's explicit scope), no ADR
deviation (matches `ADR-056` exactly), no unanticipated file, and the one judgement call above
(leaving the pre-existing legacy record untouched) is a scope-internal call already directed by
the story's own Non-Goals, logged here for spot-check, not an escalation.
