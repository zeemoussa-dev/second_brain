---
id: SPRINT-019
title: System Health View — read-only status aggregation + chat-path crash-gap fix
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retrospective drafted, awaiting human skim + Learnings.md harvest; T02's live-discovered follow_redirects correction also awaits spot-check."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"            # YYYY-MM-DD when status → Done
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

# SPRINT-019 — System Health View

## Sprint Goal

Build and verify `REQ-SB-31-US-01` end to end: a new, read-only System
Health page (MCP/agent-orchestration reachability, per-Provider
availability, disabled agents as Health Issues, last capture run status)
backed by a new aggregation module and router, plus the one concretely-
identified `run_agent_conversation` crash-gap fix (Scenario 8) — all 8
locked ACs verified.

---

## Grouping Rationale & Sizing

- **Why grouped:** all 4 tasks belong to the same story
  (`REQ-SB-31-US-01`) and the same PRD requirement (`REQ-SB-31`). This is
  a single-story sprint, not a multi-story bundle — the story itself
  already spans backend aggregation, a new router, and a new frontend
  page, which is enough work for one sprint on its own (mirrors this
  project's own precedent for single-story, multi-layer sprints, e.g.
  `SPRINT-009`/`SPRINT-010`).
- **Dependency graph honoured, not contradicted:** `T02 → T03 → T04`
  (aggregation module → router → page) is a straight in-sprint chain, all
  four tasks land together, no ordering edge needs to cross a sprint
  boundary. `T01` (the `run_agent_conversation` crash-gap fix) has
  `depends_on: []` and stands alone — backend-only, unrelated file, can be
  built first or in parallel within this sprint. `T04`'s task-level edge
  on `REQ-SB-12-US-01-T01` (it literally edits the already-`Done`
  `App.tsx`/`Sidebar.tsx`) needs **no** `depends_on_sprints` edge: that
  task is already `Done` (`SPRINT-008`, itself `Done`) — the dependency is
  already satisfied, not an open ordering constraint on another Draft/
  in-flight sprint.
- **Considered and rejected: bundling with `REQ-SB-20-US-01`** — the only
  other `Ready`, ungrouped, `gate: clear`, P1 story this pass
  (phase-compatible on paper). Re-confirmed, not re-decided from scratch:
  `SPRINT-018`'s own Grouping Rationale (created the same day, immediately
  prior to this pass) already considered and rejected this exact pairing
  for the same reason that still holds unchanged here — `REQ-SB-20-US-01`
  is a 6-task story (`T01`…`T06`: agent-keyword vault-writer primitives, a
  new business module, the agents router, orchestration state, `graph.py`'s
  routing node, and a frontend agent-detail-panel row) touching an
  entirely different concern and file set than this story's health-
  aggregation/page/crash-gap work. Nothing material changed between
  `SPRINT-018`'s pass and this one — `REQ-SB-20-US-01` is still `status:
  Draft` (not even `Ready`), still ungrouped, still a different
  concern/file set. Forcing them together would bloat a well-scoped,
  cohesive 4-task sprint into a mixed-concern one for no dependency or
  shared-surface reason. `REQ-SB-20-US-01` remains ungrouped and, being
  `Draft`, is not even eligible for `/plan-sprints` yet regardless.
- **Sizing estimate:** ~4 tasks, S — two backend-only tasks (`T01`, the
  crash-gap fix; `T02`, the aggregation module), one thin router (`T03`),
  and one frontend page + nav wiring (`T04`). Smaller than the project's
  `M`/`L` precedents (`SPRINT-009` ~7 tasks M, `SPRINT-010` ~8 tasks L)
  since three of the four tasks are single-file, no-new-external-
  dependency additions (`T02`/`T03` write no new persisted state; `T01`
  is a two-call try/except addition to already-`Done` code) and only
  `T04` carries real UI surface — but sized `S`, not `XS`, given it spans
  backend + router + a genuinely new page with 7 of the story's 8 ACs
  concentrated there.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-019 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-31-US-01](../UserStories/REQ-SB-31-US-01-system-health-view.md) | System Health View | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-31-US-01-T01]] (crash-gap
fix, `depends_on: []`, independent), [[REQ-SB-31-US-01-T02]] (aggregation
module, `depends_on: []`), [[REQ-SB-31-US-01-T03]] (router, `depends_on:
[T02]`), [[REQ-SB-31-US-01-T04]] (page + nav wiring, `depends_on: [T03,
REQ-SB-12-US-01-T01]` — the latter already `Done`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `T04`'s task-level dependency on
  `REQ-SB-12-US-01-T01` is already satisfied — that task shipped `Done` in
  `SPRINT-008` (also `Done`), so no cross-sprint ordering edge is needed;
  it is recorded here for traceability only.
- No new external-integration surface; no ADR created or changed
  (per the story's own Architect pass: `ADR-003`'s read-only-aggregation
  shape, `ADR-010`'s frontend conventions, and `ADR-015`'s honest-failure-
  funnel pattern are all extended, not reopened).

---

## Out of Scope

- `REQ-SB-20-US-01` (Section Hub Intelligence & Cross-Section Routing) —
  considered for bundling, rejected; see Grouping Rationale. Also still
  `status: Draft`, not `Ready`, this pass.
- Any other `Draft` or already-`Done`/in-flight story — not touched by
  this sprint.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no update needed; the architect's own "no new ADR" pass already fully described the new module/router/page shape before build, and the build matched it exactly (one in-scope bugfix, `follow_redirects=True`, doesn't change the architectural shape)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR this sprint
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S (as estimated;
  `T02`/`T03` were genuinely single-sitting units, `T01` was a two-call
  try/except, `T04` was the one task carrying real build+verification
  weight) — **Takeaway:** accurate. The estimate's own explicit reasoning
  ("only `T04` carries real UI surface... but sized `S`, not `XS`, given
  it spans backend + router + a genuinely new page with 7 of the story's
  8 ACs concentrated there") held up exactly — `T04`'s verification
  (4 real state inductions, 4 screenshots, one live bug found and fixed)
  was the real cost center, matching the sizing rationale's own
  prediction almost exactly.

### What worked

- **Consolidating the "issues present" verification into one real state
  change** covering two ACs at once (`AC-02` MCP-unreachable + `AC-03`
  disabled-agent) via one combined temporary edit (`_MCP_MOUNT_URL`
  pointed at an unreachable port) + one combined API call (throwaway
  Provider + reassignment), then one combined revert — mirrored the
  approved prototype's own "issues" panel showing both conditions
  together, and cut the number of real backend-reload cycles roughly in
  half versus verifying each AC as a fully separate induced state.
- **Backend-layer-first live verification held again** — `T02`/`T03`'s
  own non-AC smoke checks (direct `GET /system-health` calls) caught the
  `follow_redirects` bug *before* any frontend code was written against
  it, so `T04` never had to debug "why does the healthy state show a
  failure" as a frontend-layer mystery — the root cause was already
  known and fixed by the time `T04`'s own verification ran.
- **The specific-PID-kill-and-restart protocol worked exactly as
  documented** on a second, slightly different symptom shape (this time
  the reloader/worker/fork-child tree was fully alive, not literally
  orphaned — yet still served stale code). Confirms the protocol's value
  isn't limited to the one literal failure mode it was first found under;
  "kill the specific PIDs, restart clean" is a safe general recovery step
  whenever a `--reload` server's own edits stop reflecting, regardless of
  whether the process tree looks orphaned or not.

### What didn't work

- **The task's own literal `httpx.get()` code sample silently assumed
  redirect-following behavior it doesn't have by default** — `T02`'s
  spec'd `mcp_mount_reachable()` would have shipped a real, live,
  AC-01-breaking false-negative (MCP reported unreachable when genuinely
  healthy) had the backend-layer-first smoke check not caught it before
  any frontend code was written against it. Root cause: the story's own
  "confirmed live 2026-08-12" `406` finding was almost certainly observed
  through a redirect-following client (browser/PowerShell), and that
  detail — which specific client, and whether it followed the mount's own
  `307` — was never captured alongside the finding itself.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **When a task's own code sample is later found to disagree with a real
  live HTTP call, treat the live call as ground truth and correct the
  code in-scope, not the other way around** — `T02`'s `httpx.get()` (no
  `follow_redirects`) vs. the real `/mcp` mount's `307`→`406` redirect
  chain. The fix stayed entirely inside the task's own file, required no
  new dependency/interface/ADR, and was caught early specifically because
  the non-AC backend smoke check ran *before* the frontend task started —
  reinforcing the existing "backend-layer-first" pattern's own value.
- **When a locked AC's own wording implies "the exact same underlying
  condition, shown two different ways on the same page" (e.g. this
  story's MCP-unreachable + Provider-disabled both feeding one combined
  Health Issues list), induce both real conditions together in one
  combined edit/revert cycle** rather than as two fully separate live
  passes — halves the number of real backend-reload/API-round-trip
  cycles needed and produces a screenshot that directly matches what the
  approved prototype's own combined "issues" state shows.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Recording a live-observed HTTP status-code finding ("confirmed
  live") without also recording which client/method produced it** — a
  `307`-redirecting endpoint can genuinely answer `200`/`406`/whatever the
  final destination returns through a redirect-following client while a
  literal `httpx.get()` (redirect-following off by default) sees only the
  `307` — the same "ground truth" claim can be simultaneously true and
  misleading to a later reader depending on tooling defaults never
  written down. Record the client/method alongside any live HTTP-status
  finding meant to ground a future code sample.

### Open follow-ups

- **`BUG-007`** (`graph.py::_call_model`'s synchronous blocking
  `model.invoke()` call, still `Open`, unconfirmed root cause) — this
  sprint's own `T01` verification made its one real Compass call from an
  isolated throwaway script's own event loop, not through the shared dev
  backend's own concurrent-request event loop, so it provides no new
  confirming/disconfirming evidence either way. Still open, still worth a
  dedicated fix pass (make `_call_model` genuinely async, per this
  project's own standing async-graph-node Constraint) independent of any
  future story that happens to touch `graph.py` again.
- **The Agents-Map-consistency tension the story's own Notes already
  flagged** (the same `provider_available: false` state now reads
  "Disabled/Health Issue" on System Health but stays neutral "not
  configured" on Agents Map/Settings) remains open, not decided or built
  here — a separate product question for whoever picks up next.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired: (1) no material
assumption — the grouping (single-story sprint, `REQ-SB-20-US-01` left
out) is read directly off the task/story files' own already-resolved
scope, dependency edges, and size, and the `REQ-SB-20-US-01` exclusion
re-confirms `SPRINT-018`'s own already-recorded reasoning rather than
re-deciding it from scratch; (2) `REQ-SB-31` is not `<!-- Draft -->` in
the PRD; (3) no ADR touched (product-owner does not write ADRs; the
story's own Architect pass already found no new ADR needed); (4) no new
`ESCALATIONS.md` entry written by this pass; (5) not oversized (4 tasks,
`S`, matches this project's own established mid-range precedent), not
`Blocked`, no cross-sprint dependency introduced (`depends_on_sprints:
[]` — `T04`'s task-level edge resolves against already-`Done` work, not
an open sprint); (6) N/A (coder-only trigger); (7) no contradictory
inputs; (8) not genuinely ambiguous — one story, one natural partition
(all 4 of its own tasks), the one considered alternative (bundling with
`REQ-SB-20-US-01`) documented and rejected above rather than left
implicit. Advances `Draft → Ready`.

**Sprint assembled (2026-08-12):** 1 story, 4 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

---

**Coder pass (2026-08-12, `/implement-sprint`).** All 4 tasks built and
verified live in dependency order (`T01`/`T02` independently, then `T03`,
then `T04`). All 8 locked ACs pass against real running systems — see
`REQ-SB-31-US-01`'s own Coder-pass Notes and each task's `##
Implementation Log` for full transcripts. One real, live-discovered bug
found and fixed in-scope (`T02`'s `mcp_mount_reachable()` needed
`follow_redirects=True`) — `T02` is `gate: flagged` for human spot-check,
`REVIEW-QUEUE.md` pointer added. `status: Done`, `completed: 2026-08-12`.
`gate: flagged` so the human skims this Retrospective and the `T02`
correction together, then harvests Patterns/Antipatterns into
`Implementation/Learnings.md`.
