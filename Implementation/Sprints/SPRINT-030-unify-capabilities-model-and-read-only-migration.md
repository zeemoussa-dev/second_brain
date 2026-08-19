---
id: SPRINT-030
title: Unify agent capabilities under Skills — capability model + read-only migration
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint Done — retrospective drafted below, awaiting human skim + Learnings.md harvest. Also carries forward REQ-SB-39-US-01's own inherited ADR-028-review flag plus 3 coder-level scope-internal spot-check items (T05, T07, T09) — see REVIEW-QUEUE.md for all pointers."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-13
started: "2026-08-13"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"            # YYYY-MM-DD when status → Done
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

# SPRINT-030 — Unify agent capabilities under Skills — capability model + read-only migration

## Sprint Goal

Establish the unified Skills capability model (`mutates`/`trigger` fields,
`invoke_skill` trigger param, the `list_agent_capabilities` aggregator, the
migration-grant retrofit seed) and migrate every existing read-only Action
(`view_last_run`, `ask_question`, `view_channel_status`) onto it — the single
foundation every other story in this `/plan-sprints` batch composes with.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-39-US-01` is the only story
  here. All 9 tasks share one architecture scope (`ADR-028`) and one mostly-
  linear internal dependency chain (`T01 → T02 → {T03, T04, T05, T06} → T07 →
  T08 → T09`); no cross-story `depends_on` edges exist for this story at all
  (verified directly against every task file's real frontmatter).
- **Why NOT combined with `REQ-SB-39-US-02`, despite the direct dependency:**
  9 tasks already sits at this project's own established `L` ceiling
  (`SPRINT-021` precedent, 9 tasks). Adding `US-02`'s 4 tasks would produce a
  13-task sprint, past every prior sprint's own size, and both stories touch
  the same files (`skill_registry.py`, `skill_tools.py`) — stacking both
  passes in one working context raises exactly the file-collision risk this
  pass was asked to actively minimize. Kept as its own dependency-ordered
  sprint instead (`SPRINT-031`, `depends_on_sprints: [SPRINT-030]`).
- **Sizing estimate:** ~9 tasks, L.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-030 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-39-US-01](../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md) | Unify agent capabilities under Skills — the capability model, plus migrating every existing read-only Action to a Skill | P1 | Done |

**Tasks in scope** (dependency order): `T01` (skill_tools.py mutates field +
3 stub handlers, `depends_on: []`) → `T02` (skill_registry.py trigger param
+ handlers, `depends_on: [T01]`) → `T03` (skills_router.py trigger="direct"),
`T04` (knowledge_bootstrap.py trigger="hub_routed"), `T05` (migration-grant
retrofit seed), `T06` (list_agent_capabilities aggregator) — all
`depends_on: [T01, T02]` (T05/T06) or `[T02]` (T03/T04) → `T07`
(agents_router.py dispatch fork, `depends_on: [T01, T02, T05]`) → `T08`
(get_agent() capabilities response, `depends_on: [T06, T07]`) → `T09`
(AgentDetailPanel.tsx unified capability list, `depends_on: [T08]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- No external blockers; `ADR-028` is already `Accepted`.

---

## Out of Scope

- Working-mode approval gate extension + mutating-Action migration
  (`REQ-SB-39-US-02` → `SPRINT-031`).
- Every story that composes with this one (`REQ-SB-37-US-01/02/03`,
  `REQ-SB-28-US-01`) — scheduled in their own sprints, ordered after this one
  via `depends_on_sprints`.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, `ADR-028` was already `Accepted` before this sprint built against it; no further architectural fact changed
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR written by the coder this sprint (`ADR-028` pre-existed, `Accepted`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — matched exactly.
  No task was split, dropped, or merged. `T05` (migration seed) and `T07`
  (dispatch fork) were correctly the heaviest by real verification cost —
  not code volume — each surfacing a genuine correctness bug in the
  task's own illustrative sample code (an infinite-recursion risk in
  `T05`, a `KeyError`-on-success bug in `T07`) that only a real live run
  found, not a code-review pass alone.

### What worked

- **Live, end-to-end verification of every locked AC, including the
  operator's own explicitly-named highest-risk regression check
  (`AC-04`/`T07`)** — confirmed via three independent layers (direct
  unmodified-function call for the true pre-migration baseline, FastAPI
  `TestClient` for a real HTTP round-trip, and finally a genuine `curl`
  against a fully-started real `uvicorn` server once its real Outlook/
  Compass app-start capture finished) rather than trusting code review.
- **`T05`'s own migration-grant retrofit seed genuinely ran and genuinely
  wrote real state** — confirmed by a real clean-slate deletion +
  reconstruction of `.second-brain/agent_skills.json`, not just a
  function-return-value check; the 4 real, already-shipped agents named
  in `ADR-028` show the equivalent Skill grant.
- **Composing every backend edit around the REAL current file, every
  time** (this project's own long-established pattern) caught two real
  bugs the task samples' own illustrative code would have shipped broken:
  `_load_state()` calling `grant_skill_access()`, which itself calls
  `_load_state()` (infinite recursion), and `_invoke_capability`'s sample
  using `result["status"]` against a real result shape that has no
  `"status"` key at all on its success path (`KeyError` on first real
  use). Both fixed in-scope, same file, same task, disclosed as
  scope-internal judgement calls rather than escalated or silently
  patched.
- **Backend-layer-first, HTTP-layer-second, curl-layer-third** verification
  sequencing (reconfirmed once more this sprint) let each layer's own
  evidence stand on its own, and let the slowest layer (a real multi-
  minute app-start capture) run in the background while other, cheaper
  verification proceeded in parallel rather than blocking on it serially.

### What didn't work

- **This specific worktree/session had two real environment gaps beyond
  what any task file anticipated:** (1) `.env`/`.venv` were both
  gitignored and missing, plus every currently-uncommitted tracked file
  in the main checkout (ADRs, `MEMORY.md`, task/story/sprint files
  themselves) was also absent from the worktree's git-checked-out state —
  both had to be synced in before any work could start. (2) Node.js is
  not installed anywhere on this host at all (a step beyond the
  already-documented off-PATH antipattern), which fully blocked `T09`'s
  own build/browser verification — handled via disclosure, not silence,
  and did not block the task since both locked ACs `T09` touches were
  already independently proven at the API layer.

### Patterns to carry forward

- **When a task's own illustrative sample code composes two real,
  already-existing functions in a new way, trace the actual call graph
  before running it, not just after a crash** — the `_load_state()` →
  `grant_skill_access()` recursion would have been a real, immediate
  stack-overflow in production; reasoning through the call chain caught
  it before ever executing the naive version.
- **`FastAPI TestClient` without triggering `lifespan`, then a real
  `curl` against a fully-started server once it's ready, is not either/
  or — do both when a real app-start side effect (a real capture pass)
  makes the full server slow to bring up** — the `TestClient` result gave
  fast, real evidence immediately; the later `curl` confirmation was free
  bonus rigor once the background capture finished on its own.
- **When a task's own named test agent turns out to be one of a sibling
  task's own seeded/self-healing agents, and the test's own premise
  (e.g. "revoke, then confirm refusal") silently doesn't hold, don't
  force the original agent — use the task's own named alternative and
  document why**, rather than treating the seed's own already-documented
  behavior as a surprise defect.

### Antipatterns to avoid

- **Assuming a worktree's git-checked-out state matches the main
  checkout's real, current working-tree content** — true only for files
  the main checkout's own `git status` reports clean; every `M`/`??` file
  there (a large, easy-to-miss set on an actively-developed repo) needs
  an explicit sync before the worktree's copy can be trusted for reading
  OR appending.
- **Triggering a real real-Outlook/Compass app-start capture pass just to
  get a live HTTP-routing confirmation, when a lighter established
  technique (`TestClient`) already gives equivalent real evidence** — the
  full server start was still valuable as bonus confirmation, but should
  not be the *first* or *only* attempted route when time is scarce.

### Open follow-ups

- Human review of the 3 coder-level flagged spot-check items (`T05`,
  `T07`, `T09` — see `REVIEW-QUEUE.md`) plus the story's own
  inherited `ADR-028` review.
- `T09`'s own real browser/build verification is still owed once Node.js
  is provisioned on this host (or from a session that has it) —
  `REVIEW-QUEUE.md` entry names the exact steps.
- `SPRINT-031` (`REQ-SB-39-US-02`) is now unblocked — its own
  `depends_on_sprints: [SPRINT-030]` is satisfied.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** Verified directly against
every real task file's `depends_on:` frontmatter (not the batch summary) that
none of `REQ-SB-39-US-01`'s 9 tasks carry a cross-story edge — it is a true
foundation story with zero external inputs.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the dependency graph was
read directly off real task frontmatter; (2) `REQ-SB-39` is finalized PRD
text; (3) product-owner does not write ADRs; (4) no new `ESCALATIONS.md`
entry; (5) not oversized (9 tasks matches this project's own `L` ceiling,
not past it); not a blocked story; no cross-sprint dependency was needed for
this sprint itself (it has none); (6) N/A (coder-only trigger); (7) no
contradictory inputs; (8) not ambiguous — the story has no cross-story deps
and stands alone at the graph's own root. Advances `Draft → Ready`.
