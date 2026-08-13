---
id: SPRINT-023
title: Vault Filing Expert — methodology-grounded placement/tag decision and write, two-tier approval
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint wrap — retrospective drafted by the coder; human skims it and propagates patterns/antipatterns into Implementation/Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-020, SPRINT-021]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"             # YYYY-MM-DD when status → Done
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

# SPRINT-023 — Vault Filing Expert

## Sprint Goal

Build and verify `REQ-SB-35-US-01` end to end: a new `"vault-filing-expert"`
registry agent, reachable via Hub routing, that decides vault placement/tags
grounded in the vault's own design methodology — writing Tier-1 placements
(existing category, or a new tag/subfolder within an existing top-level
area) autonomously, and pausing for explicit operator approval only when it
proposes a genuinely new top-level vault area (Tier 2, reusing the Pending
Approvals workflow).

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — all 3 tasks belong to
  `REQ-SB-35-US-01`, the only story assigned here.
- **Why sequenced after BOTH `SPRINT-020` and `SPRINT-021`:** this story's
  own `depends_on` graph carries two distinct, real cross-story edges —
  `T01`/`T02` need `REQ-SB-20-US-01-T02`/`T05` (`agent_keywords.py`,
  `route_cross_section_request` — Hub-routing composition, `SPRINT-020`),
  and `T03` needs `REQ-SB-21-US-01-T03`/`T06` (`pending_approval_
  registry.py`, `pending_approvals_router.py` — Tier-2's own approval
  workflow, `SPRINT-021`). Both are ground truth from the decomposer's own
  pass (`ADR-021`), not re-derived here. `depends_on_sprints: [SPRINT-020,
  SPRINT-021]` records both.
- **Why NOT bundled with `REQ-SB-36-US-01` (Web Research Skill), despite
  both being downstream of `SPRINT-020` and both feeding the same
  "Compass Expert" chain:** the two stories' task graphs have zero
  `depends_on` edge onto each other, and `REQ-SB-36-US-01` has no
  dependency on `SPRINT-021` at all (see `SPRINT-022`'s own Grouping
  Rationale). Bundling would force `REQ-SB-36-US-01`'s otherwise-
  independent build to wait on `SPRINT-021` too, an artificial coupling
  with no dependency-graph justification. Kept as two separate,
  independently-sequenced sprints — this one gated on both `SPRINT-020`
  and `SPRINT-021`, `SPRINT-022` gated only on `SPRINT-020`.
- **Sizing estimate:** ~3 tasks, S — small by task count (comparable to
  `SPRINT-003`/`SPRINT-005`'s own 2-task XS precedent, sized S rather than
  XS given `T02` alone covers 6 of the story's 8 locked ACs, including a
  real LLM-backed placement decision grounded in the methodology document
  plus live vault inspection — not a trivial single-file edit).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-023 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-35-US-01](../UserStories/REQ-SB-35-US-01-vault-filing-expert.md) | Vault Filing Expert — methodology-grounded placement/tag decision and write | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-35-US-01-T01]] (new
`"vault-filing-expert"` registry agent entry + keyword assignment,
`depends_on: [REQ-SB-20-US-01-T02]` — cross-sprint), [[REQ-SB-35-US-01-T02]]
(`determine_placement_and_file`, Tier-1 write path, `depends_on: [T01,
REQ-SB-20-US-01-T05]` — cross-sprint), [[REQ-SB-35-US-01-T03]] (Tier-2
resolution — `finalize_new_top_level_area`, `depends_on: [T02,
REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T06]` — cross-sprint).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-020` (must be `Done`) — `T01`/`T02`'s
  real edges onto `REQ-SB-20-US-01-T02`/`T05` (Hub-routing composition).
  `SPRINT-021` (must be `Done`) — `T03`'s real edges onto
  `REQ-SB-21-US-01-T03`/`T06` (Tier-2's Pending-Approvals store + HTTP
  surface).
- `ADR-021` (already `Accepted`, written at `/plan-tasks`) still carries its
  own open human-review flag on the story; not a blocker for
  `/implement-sprint`, recorded here for visibility only.

---

## Out of Scope

- `REQ-SB-36-US-01` (Web Research Skill) — no dependency edge from this
  story onto it, and it has no dependency on `SPRINT-021`; not bundled.
  Built in its own sprint, `SPRINT-022`.
- `REQ-SB-36-US-02` (Compass Expert pilot) — depends on this story's `T02`/
  `T03`; built in its own sprint, `SPRINT-024`, sequenced after this one.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — not needed; `ADR-021`/its `architecture.md` section were already written at `/plan-tasks`, no new architectural fact emerged during the build
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none new; `ADR-021` was already `Accepted` at `/plan-tasks`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S, matching the
  estimate closely. `T02` was correctly identified up front as the heavy
  task (6 of 8 locked ACs, a real grounded LLM placement decision) — it
  took the majority of build time, including two real prompt-iteration
  cycles to satisfy `AC-02`'s own "discoverable via `list_known_
  customers()`" wording (see below). `T01`/`T03` were both genuinely
  small, as sized.

### What worked

- **Direct, before-writing-anything reading of all 4 cross-story
  dependencies' own real, current code** (`agent_keywords.py`,
  `route_cross_section_request`, `pending_approval_registry.py`,
  `pending_approvals_router.py`) — confirmed every task's own literal
  code sample matched the real, `Done` shape closely enough to build
  directly against it, with zero silent regression of a sibling story's
  own mechanism (the exact failure mode `REQ-SB-20-US-01-T05`/
  `REQ-SB-21-US-01`'s own prior Implementation Logs flagged as a
  recurring risk).
- **Deterministic re-check of the Tier boundary in Python
  (`kind not in known_kinds`), never trusting the model's own boolean** —
  worked exactly as designed; live-verified that `_create_tier_2_proposal`
  never even references `working_mode_registry` (zero `grep` matches),
  making the "bypass by construction, not a conditional" design point a
  literal, inspectable, and live-tested property rather than a documented
  intention.
- **Building `T02` with a `NotImplementedError` Tier-2 stub first,
  verifying Tier 1 fully, then applying `T03`'s real replacement** — even
  though both cross-story Tier-2 dependencies were already `Done` and
  building the final version directly was possible, doing it in the
  task-defined order kept each task's own live verification cleanly
  scoped to its own locked ACs, and made the diff per task easy to reason
  about.

### What didn't work

- **A first-pass prompt/schema design (`referenced_customer`: "the exact
  KNOWN customer name... or null") silently excluded the single most
  common real case — a genuinely NEW customer/partner — from getting a
  frontmatter field and a hub-note wikilink at all**, even though the
  `tags` list correctly carried `customer/<slug>` both times. Caught
  live only because `AC-02`'s own locked wording explicitly demanded
  `list_known_customers()` reflect the new value — a less specific AC
  might have let this pass unnoticed. Two real Compass calls were needed
  before the fix (schema wording made "REQUIRED whenever a customer/
  <slug> tag is set, known or new alike") produced the correct field
  reliably.
- **The FastAPI app's own `lifespan` (`app/main.py` → `capture_scheduler.
  lifespan`) unconditionally runs a real Outlook-COM capture pass on
  startup, before the server accepts any HTTP request** — in this
  headless build/verification session (no interactive Outlook desktop
  session available), that startup call hung indefinitely, blocking a
  live `uvicorn` server from ever becoming reachable. Not this story's
  own scope to fix (`capture_scheduler.py` is untouched by any of
  `T01`–`T03`'s own `## Files to Modify`) — worked around by verifying
  every locked AC via direct Python-shell calls against the real
  `.venv`/vault instead (exactly what every task's own `## Tests` block
  already specified), never through a live HTTP round trip. No sprint
  ACs required the HTTP layer at all, so this was a pure environment
  friction point, not a blocker.

### Patterns to carry forward

- **When a locked AC names a specific downstream read function (e.g.
  "discoverable via `list_known_customers()`"), read that function's own
  real implementation FIRST, before trusting a task's own illustrative
  code sample to satisfy it** — `list_known_customers()` scans a
  `customer:` FRONTMATTER field, never the `tags` list; a plausible-
  looking `{"tags": [...]}`-only write would have silently failed this
  AC if verification hadn't specifically re-checked the AC's own exact
  read path after the first write.
- **When prompting a model for a conditional field ("X, only if the
  content is about a KNOWN Y"), make the "known-or-new" scope explicit
  and test with content about a definitely-new entity, not just an
  already-known one** — a prompt instruction that reads correctly for
  the already-known case can silently mean "existing entities only" to
  the model for the exact case (a brand-new customer/partner) a
  taxonomy-extensibility feature most needs to get right.
- **Prefer direct Python-shell verification over spinning up the full
  HTTP server whenever a task's own `## Tests` block already specifies
  it that way** — this sprint's own experience (a real, unrelated
  app-startup side effect blocking the whole server) is a second, live
  confirmation of this project's own standing "backend-layer-first live
  verification" pattern (`MEMORY.md`) generalizing to "skip the HTTP
  layer entirely when it isn't load-bearing for the locked ACs."

### Antipatterns to avoid

- Do not assume a model-returned field will be populated symmetrically
  for both an "already known" and a "genuinely new" case just because the
  prompt technically allows both — verify both cases live, independently,
  before treating either as passing.

### Open follow-ups

- **`app/scheduling/capture_scheduler.py`'s unconditional app-start
  Outlook-COM capture run has no timeout and can hang the whole server's
  own startup indefinitely in an environment where Outlook is not
  interactively available** — out of this story's own scope to fix (not
  in any of `T01`–`T03`'s `## Files to Modify`), but worth a dedicated
  look (e.g. a startup timeout, or making the app-start trigger
  best-effort/non-blocking) since it also affects any future coder pass
  needing a live HTTP server in a similar headless session.
- The two synthetic, monkeypatch-driven test notes left in the real vault
  from `AC-06`/`AC-08` (`Work/Notifications/TEST-AC06-low-confidence-
  placement.md`, `Work/Notifications/TEST-AC08-collision-stem[-2].md`)
  are clearly fixture content (not real captured data), left in place
  rather than deleted per this project's own "real writes are permanent,
  no staging gate" standing decision and to preserve an honest audit
  trail of what was verified — flagged here for visibility, not
  auto-cleaned.

---

## Notes

**Sprint assembled 2026-08-12 (`/plan-sprints`, operator-directed batch —
the "Compass Expert" business chain).** Part of a 5-sprint sequence
(`SPRINT-020`…`SPRINT-024`); see `SPRINT-020`'s own Notes for the full
chain-partitioning rationale. This is the first sprint in the chain gated
on two upstream sprints simultaneously — a real, ground-truth consequence
of `T01`/`T02` needing `SPRINT-020` and `T03` needing `SPRINT-021`, not an
artificial coupling.

**Gate: `gate: clear` 2026-08-12.** No MUST-FLAG trigger fires: (1) no
material assumption — both cross-sprint edges are read directly off the
decomposer's own recorded `depends_on` graph, not guessed; (2) `REQ-SB-35`
is not `<!-- Draft -->`/unfinalised; (3) product-owner does not write
ADRs — none touched; (4) no new `ESCALATIONS.md` entry written by this
pass; (5) not oversized (3 tasks, S); the two `depends_on_sprints` edges
introduced (`[SPRINT-020, SPRINT-021]`) mirror real, already-recorded
task-level edges exactly — not a MUST-FLAG "cross-sprint dependency you
had to introduce" in the problematic/ambiguous sense, the same reasoning
`SPRINT-012`'s own precedent already established; (6) N/A (coder-only
trigger); (7) no contradictory inputs; (8) not genuinely ambiguous — one
story, one natural partition, the one considered alternative (bundling
with `REQ-SB-36-US-01`) documented and rejected above. Advances
`Draft → Ready`.
