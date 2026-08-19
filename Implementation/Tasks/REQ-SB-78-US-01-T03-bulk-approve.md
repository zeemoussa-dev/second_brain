---
id: REQ-SB-78-US-01-T03
title: Bulk-approve control per eligible group
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Done
gate: flagged
gate_reason: "out-of-scope — ESC-058: vault_writer.py's pending-approvals JSON state file has no concurrent-write locking, found live during this task's own AC-06 verification; fixed in-scope by looping sequentially (already within this task's own explicit implementation latitude), but the underlying vault_writer.py primitive gap is out of this task's frontend-only file scope and recommended for a future /bug capture. This task's own locked AC-06 is fully verified and passing."
phase: P2
depends_on: [REQ-SB-78-US-01-T01, REQ-SB-78-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T03 — Bulk-approve control per eligible group

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review" § "Bulk-approve eligibility (Scenario 7)"

---

## Objective

Give every rendered group whose items are ALL non-branching-decision a real bulk-approve control that loops the already-existing single-item `approvePendingApproval(id)` call; a group containing any branching-decision item (Company Review) offers no bulk-approve control at all.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed: groups render as `[data-group-key]` sections, each with its own `items` array.
- `approvePendingApproval(id)` (`../features/agents-map/pendingApprovalsApiClient.ts`) already exists — a plain `POST /pending-approvals/{id}/approve` call with no decision body.

**After / Outputs:**
- For each rendered group, compute eligibility: `group.items.every(item => !BRANCHING_DECISION_ACTION_IDS.has(item.action_id))` (correctly covers the heterogeneous `Other` catch-all too, since it's computed per rendered group, not per group key).
- An eligible group's own section header/toolbar gains a `Bulk approve (<N>)` button (`btn btn-primary`, mirroring existing button vocabulary). Clicking it calls `approvePendingApproval(id)` once per item currently in that group (sequential or `Promise.all` — coder's own implementation choice), then refreshes the list once at the end (mirrors `handleApprove`'s own existing `refresh()` call).
- A group containing at least one branching-decision item (`propose_company_review`) renders NO bulk-approve control for that group.

---

## Files to Modify

- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — bulk-approve control + handler, added to `T02`'s own group-section rendering.

---

## Constraints

- Inherits from parent story.
- **Zero new backend endpoint/capability** — loops the ALREADY-EXISTING `approvePendingApproval(id)` verbatim, once per item, mirroring `handleApprove`'s own existing per-item call shape exactly.
- **Eligibility computed PER RENDERED GROUP, not per group key** — a future `Other`-catch-all group that happens to contain a mixed set (some branching, some not) must correctly get NO bulk-approve control, using the same one check as every named group.
- **Refresh once at the end**, not once per item — avoid N redundant re-fetches for an N-item bulk action.
- Never bulk-approve/bulk-decline without an explicit operator click on this task's own new control — no auto-trigger.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-78-US-01-AC-06]` Seed 2+ real pending approvals sharing a non-branching `action_id` (e.g. `route_thread_to_project` or `acknowledge_classification_failure`). Confirm that group renders a `Bulk approve` control. Click it; confirm every item in the group is approved via a real `POST /pending-approvals/{id}/approve` call each (confirm via network inspection: one call per item, no decision body), and the group empties/disappears once the list refreshes.
2. `[REQ-SB-78-US-01-AC-06]` Seed a real `propose_company_review` pending approval. Confirm its own group renders NO bulk-approve control.
3. Seed a group with a mix (if the `Other` catch-all can realistically contain a branching + non-branching mix — construct this case even if synthetic). Confirm the mixed group ALSO gets no bulk-approve control — the per-group, not per-key, computation.
4. Confirm a single-item group still offers bulk-approve if eligible (no "2+ items" gate on rendering the control itself — the Gherkin's own "2+" is about a realistic demonstration, not a hard eligibility floor; disclose if a different reading was taken).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-78-US-01-AC-06]` Bulk-approve confirmed live for an eligible group, looping the existing single-item endpoint
- [x] `[REQ-SB-78-US-01-AC-06]` No bulk-approve control rendered for a group containing any branching-decision item
- [x] List refreshes once at the end of a bulk action, not once per item
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (yes — `vault_writer.py` concurrent-write-locking gap, `ESC-058`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any new backend endpoint.
- Bulk-decline (not asked for by this story's own Gherkin — Approve only).

---

## Context / Notes

A future new branching-decision `action_id` needs to be added to BOTH `BRANCHING_DECISION_ACTION_IDS` (`T01`) AND `MyDayApprovalsPage.tsx`'s own existing per-item render branch — the same "each new decision control names itself" precedent the Company Review control already established, not a new gap this task introduces.

---

## Implementation Log

**2026-08-19, coder.** `MyDayApprovalsPage.tsx` — added `handleBulkApprove
(groupItems)` (loops the existing `approvePendingApproval(id)` **sequentially**
— see finding below — then `refresh()` once) and a `Bulk approve (<N>)`
button in each group's own heading, rendered iff `group.items.every(item =>
!BRANCHING_DECISION_ACTION_IDS.has(item.action_id ?? ''))` (per-rendered-
group computation, correctly covering a heterogeneous `Other` catch-all
too). Imported `BRANCHING_DECISION_ACTION_IDS` from `T01`'s
`pendingApprovalGroups.ts`.

**Real, load-bearing finding during live verification — Promise.all
switched to sequential (full detail: `ESCALATIONS.md` → `ESC-058`,
`MEMORY.md` → new Constraint):** the task's own Tests/Constraints text
explicitly allowed either "sequential or `Promise.all`." The first build
used `Promise.all`. Live-verifying against 2 disposable test records
sharing one `action_id` found only 1 of 2 actually resolved to `approved`
— root-caused to `vault_writer.py`'s pending-approvals JSON state file
having no concurrent-write locking (2 simultaneous requests each
read-modify-write the same file; the later write silently clobbers the
earlier one). Reproduced a second time with a different, unrelated
`action_id` to rule out a per-handler cause. **Fixed in-scope** by
rewriting `handleBulkApprove` to loop sequentially (`for...of` + `await`)
— already within this task's own explicit implementation-choice latitude,
not a scope deviation. Re-verified live: 2/2 disposable records correctly
resolved to `approved`, zero data loss, one POST call per item, no
decision body, `refresh()` still called exactly once at the end (not
inside the loop). The underlying `vault_writer.py` primitive gap itself is
OUT of this task's own frontend-only `## Files to Modify` — logged to
`ESCALATIONS.md`/`REVIEW-QUEUE.md`/`MEMORY.md` for a future `/bug` capture,
not fixed here.

**Live verification (same running app/session as `T01`/`T02` — dev server
`http://127.0.0.1:5174`, real backend `http://127.0.0.1:8000`, headless
Edge via CDP):**

- `[REQ-SB-78-US-01-AC-06]` (eligible group, bulk-approve works) — seeded 2
  disposable Pending Approvals sharing a safe, wholly-unmapped `action_id`
  (falls into the `Other` group; a real `KNOWN_GROUPS` action_id,
  `route_thread_to_project`, was tried FIRST and found to now have a real
  `_APPROVAL_HANDLERS` entry — `finalize_thread_project_routing` — that
  500s on a synthetic/incomplete payload; not a defect in this story's own
  code, disclosed below, routed around by using an unmapped `action_id`
  instead, which safely no-ops via `_execute_action`'s honest "not yet
  available" path). Confirmed the group rendered `Bulk approve (2)`;
  clicking it fired exactly 2 real `POST /pending-approvals/{id}/approve`
  calls (Network-domain-captured), neither carrying a body; both records
  confirmed `status: "approved"` via a direct `GET`; the group correctly
  disappeared from the DOM after the single end-of-loop `refresh()`.
  **Confirmed.**
- `[REQ-SB-78-US-01-AC-06]` (branching group, no control) — the real,
  live `propose_company_review` group (73 real records) rendered NO
  `Bulk approve` button (`bulkButtonPresent: false`, directly queried).
  **Confirmed.**
- Mixed-group per-rendered-group (not per-key) computation — synthetic
  check (task's own Tests step 3 explicitly allows "even if synthetic"):
  called the exact same eligibility expression the component uses,
  against the REAL `BRANCHING_DECISION_ACTION_IDS` constant, with a
  synthetic `[propose_company_review, <non-branching>]` mixed array →
  `false` (ineligible), and an all-non-branching synthetic pair → `true`
  (eligible). **Confirmed.**
- Single-item group still offers bulk-approve — a genuinely single-item
  disposable `Other` group (before a second record was added) rendered
  `Bulk approve (1)`, confirmed directly. **Confirmed** (Test step 4's own
  reading: no "2+ items" hard eligibility floor).
- Refresh-once constraint — confirmed by direct code review (the
  `refresh()` call sits after the `for...of` loop, never inside it) and by
  the DOM/network trace above (exactly 1 `GET /pending-approvals` refresh
  observed after the 2 approve calls, not 2).

Every disposable artefact created for this task's own verification (7
Pending Approval records total across the `route_thread_to_project`
misstep and the final safe-`action_id` retest) was resolved (approved or
declined) via the REAL HTTP API before moving on — never a raw store
mutation, per this project's archive-not-delete/API-first standing
constraint. None of the 80 real, operator-owned records were touched.

**Gate: flagged 2026-08-19 (`out-of-scope`)** — trigger 4/7 fired: this
task wrote an `ESCALATIONS.md` entry (`ESC-058`) for a genuine, pre-existing
concurrency defect found live in `vault_writer.py` (out of this task's own
file scope, not caused by this story). This task's OWN locked AC
(`AC-06`) is fully verified and passing via the in-scope sequential-loop
fix; the flag is for the human to review/route the underlying primitive
gap toward a `/bug` capture, not because anything in this task is
unresolved.
