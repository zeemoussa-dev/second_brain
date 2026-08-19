---
id: SPRINT-075
title: Pending Approvals — Grouped, Color-Coded Review
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest (standard sprint-close gate) + standing ESC-058 review — a real, out-of-scope vault_writer.py concurrent-write-locking gap was found live during T03's own AC-06 verification; this story's own locked ACs all pass (fixed in-scope via a sequential bulk-approve loop), the flag is for the human to route the underlying primitive gap toward a /bug capture, see REVIEW-QUEUE.md"
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-075 — Pending Approvals — Grouped, Color-Coded Review

## Sprint Goal

Group the Pending Approvals list by `action_id` with a distinct color
treatment per group, plus a bulk-approve control for groups whose items
share a simple, uniform approve/decline action.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 4 tasks belong to
  `REQ-SB-78-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "Pending Approvals — Grouped, Color-Coded Review").
  Graph read directly from each of the 4 task files' own `depends_on:`
  frontmatter:
  - `T01` (`pendingApprovalGroups.ts` + CSS) — `depends_on: []`, root.
  - `T02` (grouped rendering) — `depends_on: [T01]`.
  - `T03` (bulk-approve control) — `depends_on: [T01, T02]`.
  - `T04` (real-browser live verification, all 7 ACs) — `depends_on: [T02,
    T03]`.
  - **Acyclic** — a strict linear chain (`T01` → `T02` → `T03` → `T04`); no
    back-reference found. All 4 tasks carry `phase: P2` (matching the parent
    story) — no phase mixing.
- **Why NOT combined with `SPRINT-073`/`SPRINT-074` (this same batch's other
  two stories):** confirmed by direct reading of this story's own
  `## Dependencies` and all 4 task files' own `depends_on` frontmatter —
  zero edges, in either direction, connect `REQ-SB-78-US-01` to
  `REQ-SB-77-US-01` or `REQ-SB-79-US-01`. The two areas share no file, no
  module, and no architecture section (`MyDayApprovalsPage.tsx`/
  `pendingApprovalGroups.ts`, frontend-only, vs.
  `librarian_housekeeping.py`/`agent_registry.py`, backend-only). The
  story's own `## Dependencies` names `REQ-SB-76-US-01` (shares the same
  screen, `SPRINT-072`, `In Progress`) as a soft, non-blocking sequencing
  note only — "Not required to be `Done` first — this story's own grouping
  wrapper is generically keyed off `agent_id`/`action_id`, not specific to
  any one proposal type." Keeping this story in its own sprint, rather than
  folding it into `SPRINT-074` (which itself must wait on `SPRINT-073`),
  means this fully independent, unblocked frontend work is never
  artificially gated behind an unrelated backend dependency chain it does
  not need — a real decoupling benefit, not merely "the third story needs
  somewhere to go."
- **Sizing estimate: ~4 tasks, S.** Matches this project's own repeatedly-
  confirmed 4-task/S shape (`SPRINT-019`, `SPRINT-025` — both exact matches
  at retro per `Implementation/Learnings.md`), consistent with the story's
  own Notes comparing its scope to `REQ-SB-52-US-01`'s own single-screen
  restyle. `T04` (real-browser CDP verification of all 7 locked ACs) is
  expected to be the heaviest by live-verification effort, not code volume —
  mirrors this project's own established screen-level-AC-verification
  precedent (`Implementation/Learnings.md`, `SPRINT-026`/`036`/`038`).

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-78-US-01's own
frontmatter now carries sprint: "SPRINT-075". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-78-US-01](../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md) | Pending Approvals — Grouped, Color-Coded Review | P2 | Done |

**Tasks in scope** (dependency order): `T01` (root) → `T02` (needs `T01`) →
`T03` (needs `T01`, `T02`) → `T04` (needs `T02`, `T03`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This story has zero task-level `depends_on`
  edge onto any other story, in either this batch or any prior sprint —
  confirmed directly by reading all 4 task files.
- **Related, non-blocking:** `REQ-SB-76-US-01` (Company Review,
  `SPRINT-072`, `In Progress`) — shares this exact screen; this story's own
  grouping/color scheme accounts for the Company Review proposal type as one
  of its groups (Scenario 5), but is not required to be `Done` first (see
  story's own `## Dependencies`).
- **External:** none new.

---

## Out of Scope

- The Librarian's own two-sub-pipeline split — `REQ-SB-79`, `SPRINT-073`
  (unrelated screen/module).
- People notes linking to their real Company/Partner note — `REQ-SB-77`,
  `SPRINT-074` (unrelated screen/module).
- Any change to any individual proposal type's own approve/decline mechanism
  or decision-control shape (including the Company Review 5-way control) —
  the story's own disclosed Non-Goal.
- Reconciling `SPRINT-072`'s own in-flight UI changes beyond reading its
  current live shape for grounding — the story's own disclosed Non-Goal.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change expected — already updated at `/plan-tasks` under "Pending Approvals — Grouped, Color-Coded Review") — confirmed unchanged, no architectural drift found during the build
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (none expected — no new ADR created for this story) — confirmed, no new ADR
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — one new standing Constraint added (`vault_writer.py` concurrent-write-locking gap, `T03`)
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly,
  extending this project's own repeatedly-confirmed 4-task/S precedent
  (`SPRINT-019`/`SPRINT-025`, both noted in the sprint's own Grouping
  Rationale). `T04` (real-browser CDP verification of all 7 locked ACs)
  was, as predicted at sizing time, the heaviest by live-verification
  effort, not code volume — the actual frontend diff across all 3 code
  tasks stayed well under 150 lines total.

### What worked

- **Structural grouping-by-construction (only iterate real `items`, never
  a fixed `KNOWN_GROUPS`-key loop)** made empty-group suppression
  (Scenario 3) true by design, needing zero extra defensive code — the
  same "design for the AC, don't add a runtime check" pattern this
  project has used before (`SPRINT-037`).
- **Reusing this project's own established real-vault-data-first
  verification discipline** — every AC was checked against real, live
  pending-approval data first, with disposable test records seeded via the
  real `create_pending_approval()` function only for the 2 conditions
  (unmapped `action_id`, a 2+-item non-branching group) the real queue
  didn't happen to contain at verification time — meant every finding
  (including the concurrency race below) surfaced against genuinely real
  code paths, not a mock.
- **An in-page `window.fetch` monkeypatch stub for the empty-state check**
  (established `SPRINT-026` precedent) avoided ever needing to touch any
  of the 80+ real, operator-owned pending records to prove the empty-state
  branch — zero real-data risk for a scenario that would otherwise require
  destroying real state to observe.

### What didn't work

- **Assuming a `KNOWN_GROUPS` action_id chosen for synthetic test data is
  automatically "safe" (no real handler) just because the task's own
  Context text described the Approve endpoint as unchanged.** The first
  bulk-approve test used `route_thread_to_project` — a real
  `_APPROVAL_HANDLERS` entry (`finalize_thread_project_routing`) now
  exists for it (shipped by an unrelated, concurrently-in-flight sprint)
  and 500s on a synthetic/`None` payload. Root cause: the task file's own
  prose ("already exists — a plain POST call with no decision body") was
  accurate about the endpoint's OWN interface but silently stale about
  which `action_id`s now have real handler side effects behind that same
  endpoint. Recovered by switching to a wholly-unmapped `action_id` for
  synthetic bulk-approve test data instead (safe by construction — always
  falls through to the honest "not yet available" no-op path).

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **When synthesizing a disposable test Pending Approval for a live
  verification step, prefer a wholly-unmapped/novel `action_id` over a
  real, already-`KNOWN_GROUPS`/registry-listed one, unless the test
  specifically needs that real action's own handler behavior.** A
  `KNOWN_GROUPS`-listed `action_id` may have gained a real
  `_APPROVAL_HANDLERS` entry since the task was written (this project's
  approval-handler dispatch table has grown continuously across many
  concurrent sprints) that expects a real, populated `payload` — an
  unmapped `action_id` always safely no-ops via `_execute_action`'s honest
  "not yet available" path regardless of payload shape, making it the
  lower-risk default for synthetic test data. Found live,
  `REQ-SB-78-US-01-T03`.
- **Root-cause an unexplained partial-success result (e.g. "only 1 of 2
  concurrent writes survived") by reproducing it a second time with a
  DIFFERENT, unrelated input before attributing it to that specific input**
  — reproducing the concurrent-write loss with a second, wholly different
  `action_id` is what confirmed the cause was a genuine backend
  concurrency gap, not something specific to the first `action_id` tried.
  Extends this project's own `SPRINT-028` "independently confirm a
  mechanism is correct via a controlled case before attributing a failure
  to it" pattern to the inverse direction (isolating a failure's true
  scope). Found live, `REQ-SB-78-US-01-T03`.
- **When a task's own Tests/Constraints text explicitly offers 2 equally-
  valid implementation choices (here: "sequential or `Promise.all` — the
  coder's own choice") and live verification reveals one choice trips a
  real, out-of-scope backend defect, picking the other explicitly-allowed
  choice is an in-scope fix, not a scope deviation** — no escalation
  needed for the AC itself; only the underlying out-of-scope defect gets
  logged (`ESC-058`). Worth naming explicitly since it's a cheap, fully
  in-bounds way to route around an unrelated found defect without
  blocking the task.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a task/story file's own prose description of an existing
  endpoint's behavior ("already exists — a plain POST call with no
  decision body") as still-complete, rather than re-reading the REAL,
  current router file for every handler branch that endpoint might now
  dispatch to** — the endpoint's own outer interface (URL, method, no
  request body) was accurately described and unchanged; what the prose
  didn't (and couldn't, at spec time) anticipate was that a fully
  unrelated, concurrently-in-flight sprint would add new real dispatch
  branches (`_APPROVAL_HANDLERS` entries) behind that same stable
  interface between spec time and build time. Re-confirms this project's
  own "compose around the REAL current file, every time" precedent
  (`SPRINT-020`/`SPRINT-021`/`SPRINT-027`) one layer deeper: it's not
  enough to re-read the ONE file you're modifying — a shared endpoint's
  full real dispatch surface (every file it imports/branches into) can
  also have grown since a task was written, especially in a codebase with
  multiple concurrently-building sprints. Found live, `REQ-SB-78-US-01-T03`.

### Open follow-ups

- `ESC-058` / `REVIEW-QUEUE.md` — `vault_writer.py`'s JSON state-file
  writers have no concurrent-write locking (confirmed for the
  pending-approvals state file; the same `path.write_text(json.
  dumps(state))`-with-no-lock shape appears across most of its other state
  files too). Recommend a `/bug` capture and eventual `BUGFIX-NN-US-01`
  fix story — likely shape: a file lock or atomic read-modify-write helper
  shared across `vault_writer.py`'s state-file writers.
- This story's own grouping/color treatment was built directly against
  the app's existing token/component vocabulary, with no `/design` pass
  (operator-resolved by precedent, see the story's own frontmatter
  `gate_reason`) — a future design pass may still want to restyle the
  `.pending-approval-group` wrapper/heading for closer visual parity with
  a from-scratch design, per that same resolution's own "coder builds
  directly... a later design pass may restyle it" wording.

---

## Notes

**Sprint assembled 2026-08-19 (`/plan-sprints`).** `REQ-SB-78-US-01` enters
`/plan-sprints` `status: Ready`, `gate: clear` (the operator's own prior
resolution of the architect's earlier `/design`-pass question, recorded in
the story's own frontmatter `gate_reason`).

**Gate: `gate: clear` 2026-08-19.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone, single-story
grouping is read directly off all 4 task files' own `depends_on` frontmatter
(fully internal to this story, confirmed zero cross-story edges either
direction); (2) `REQ-SB-78` is not `<!-- Draft -->`/unfinalised; (3)
product-owner does not write ADRs — none created or changed by this pass;
(4) no new `ESCALATIONS.md` entry; (5) not oversized (4 tasks, S, matching
two prior confirmed-accurate 4-task/S precedents, `SPRINT-019`/`SPRINT-025`);
not a blocked story — every task is `status: Ready`, no unmet prerequisite;
no cross-sprint dependency introduced (none exists); (6) N/A (coder-only
trigger); (7) no contradictory inputs; (8) not genuinely ambiguous — the
absence of any real dependency edge onto `REQ-SB-77-US-01`/`REQ-SB-79-US-01`
(this same batch's other two stories) makes "its own independent sprint" the
unambiguous, reasoned call over folding it into either — not an
equally-valid toss-up (full reasoning in `## Grouping Rationale & Sizing`
above). Advances `Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-78` row's Sprint column set to
`SPRINT-075`.
