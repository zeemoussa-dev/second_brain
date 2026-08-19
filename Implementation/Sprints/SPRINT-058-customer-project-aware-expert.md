---
id: SPRINT-058
title: Customer/Project-Aware Expert (Glimpse-First Answers)
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint complete — drafted retrospective awaiting human skim/harvest into Implementation/Learnings.md. Two real, disclosed, out-of-scope findings (ESC-046, ESC-047) surfaced during live verification, neither blocking."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-18"                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-058 — Customer/Project-Aware Expert (Glimpse-First Answers)

## Sprint Goal

Extend `vault-qa` so a Customer/Project status question is answered from that
entity's own Glimpse (and Background, for durable questions) first, falling
back to its existing full-search/tool-based behavior only when no entity
resolves or the operator asks for evidence/detail.

---

## Grouping Rationale & Sizing

- **Why grouped — single-story sprint.** `REQ-SB-58-US-01` is the only
  `Ready`, ungrouped (`sprint: ""`) story in scope for this pass. Both tasks
  belong to this one story, share one architecture scope (`architecture.md`
  → "Glimpse-First `vault-qa` Answers — entity resolution + Glimpse/
  Background context injection, evidence drill-down unchanged"), and form a
  straight, acyclic 2-node dependency chain — read directly from each task
  file's own `depends_on:` frontmatter, not inferred from the story's own
  summary table:
  - `T01` (`depends_on: []`) — new, standalone `app/business/glimpse_
    first_qa.py` module (rank-1 entity resolution reusing `vault_search.
    search()` verbatim + Glimpse/Background read via `read_body_section`).
    Directly testable in isolation; the shared root the second task builds
    on.
  - `T02` (`depends_on: [T01]`) — the new `graph.py` node (`retrieve_memory
    -> glimpse_first_context -> call_model`, gated to `agent_id ==
    "vault-qa"` only), `state.py`'s additive grounding-text clause, and the
    live verification of all 6 of the story's locked ACs (every Scenario
    names an actual `vault-qa` reply that does not exist until the graph
    node is wired in — including evidence drill-down, `AC-03`, which needed
    no task of its own since it reuses `vault-qa`'s already-`Done`
    `retrieve_notes_in_agent_scope` tool unchanged).
  - Both tasks are `phase: P1` — no phase mix.
- **Why not split into two sprints:** the two tasks are a tight,
  single-chain build over one existing agent's reply path — splitting them
  would produce two single-task sprints for a story the analyst/decomposer
  themselves already framed as "the smallest, most-separable requirement in
  the batch." No dependency, complexity, or amount-of-work driver favors a
  split.
- **Sizing estimate:** ~2 tasks, S — matches this project's own established
  2-task/S precedent (`SPRINT-029`, `SPRINT-036`), the smallest recurring
  sizing bucket this project uses.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-058 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-58-US-01](../UserStories/REQ-SB-58-US-01-customer-project-aware-expert.md) | Customer/Project-Aware Expert — vault-qa answers status questions from Glimpse (and Background) first, falling back to raw evidence search on request | P1 | Done |

**Tasks in scope** (dependency order): `T01` (new `glimpse_first_qa.py`
entity-resolution module, `depends_on: []`) → `T02` (graph-node wiring +
`state.py` grounding clause + live verification of all 6 locked ACs,
`depends_on: [T01]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's own `## Dependencies` names
  `REQ-SB-54-US-01` (`SPRINT-048`, Done) and `REQ-SB-57-US-01` (`SPRINT-057`,
  Done) as blockers — both are already shipped, so no `depends_on_sprints`
  edge is needed; this sprint is immediately buildable.
- Unblocks `REQ-SB-59-US-01` (Full Vault Migration to the New Knowledge
  Model, `Draft`, blocked on `REQ-SB-54` through `REQ-SB-58` all shipping) —
  per the operator's own explicit direction to properly unblock `REQ-SB-59`
  through the full pipeline. This sprint is the second and final blocker;
  `REQ-SB-57` (`SPRINT-057`) already shipped.

---

## Out of Scope

- Writing or maintaining Glimpse/Background/History content — exclusively
  `REQ-SB-57`'s own scope; this story is read-only.
- A new Agent — this is an extension of the existing `vault-qa` Expert.
- New entity-resolution/name-matching logic — reuses `REQ-SB-02`'s existing
  mechanism as-is.
- Backfilling historical evidence — `REQ-SB-59`'s own scope.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already appended at `/plan-tasks`, unchanged this pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created this sprint
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

- **Estimated:** ~2 tasks, S — **Actual:** 2 tasks, S — matched exactly.
  Both tasks built cleanly on the first pass with zero rework; `T02`'s
  real cost was entirely in live-verification effort (root-causing two
  real, out-of-scope findings), not in code volume — its own diff was
  ~60 lines across two files.

### What worked

- Reading the REAL current `graph.py`/`state.py` before applying any
  diff (this project's own repeated Learnings finding on `graph.py`
  specifically) confirmed zero drift from the task's own literal
  samples — the diff applied cleanly on the first attempt.
- Disposable-fixture, fully-cleaned-up-after live verification (the
  `REQ-SB-57-US-01-T01` fixture technique, reused directly: a real
  `thread_match_merge` call pair, then `synthesize_project`) produced a
  genuinely checkable, deliberately-marked `## Glimpse`/`## Background`
  without touching any real, non-disposable vault content.
- In-process monkeypatch + `object.__setattr__` on a loaded LangChain
  `StructuredTool` instance's own `ainvoke` (needed because pydantic's
  `__setattr__` rejects a plain attribute assignment for a non-field
  attribute) is a real, reusable technique for counting/capturing a
  specific tool's real invocation without touching any source file.
- Instrumenting a diagnostic retry to capture the EXACT tool-call
  arguments a model sent (not just whether a call happened) turned an
  ambiguous "sometimes it works, sometimes it doesn't" observation into
  a fully root-caused, reproducible, disclosed finding (`ESC-047`) in
  under 10 minutes of additional real-Provider time.

### What didn't work

- Assuming the story/architecture's own framing of "the existing
  full-search baseline" (i.e., the model reliably calls `retrieve_
  notes_in_agent_scope` for a plain status question once Glimpse-first
  is disabled) would hold organically on the first live attempt — it
  took several real retries, and the underlying reason (`ESC-047`) was
  a pre-existing `REQ-SB-29` tool-contract gap, not a flaw in this
  story's own design.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **`object.__setattr__(tool, "ainvoke", wrapper)` to monkeypatch a
  loaded LangChain `StructuredTool` instance's own method for call
  counting/argument capture** — a plain instance attribute assignment
  raises (`"StructuredTool" object has no field "ainvoke"`, pydantic's
  own `__setattr__` rejecting a non-field attribute); `object.
  __setattr__` bypasses that cleanly, reverted immediately after. Found
  live, `REQ-SB-58-US-01-T02`.
- **When a live AC verification step fails organically 2+ times,
  instrument a diagnostic retry that captures the EXACT arguments/data
  a real model call produced, not just pass/fail** — turned a vague
  "sometimes fails" into a fully root-caused, reproducible finding
  (`ESC-047`) far faster than guessing at causes from reply text alone.
  Found live, `REQ-SB-58-US-01-T02`.
- **Before assuming a new node caused a live verification failure,
  reproduce the SAME failure with the new node's own effect fully
  monkeypatched to a no-op** — definitively separated "pre-existing
  behavior, unaffected by this task" from "a regression this task
  introduced" in one extra, cheap check. Found live, `REQ-SB-58-US-01-T02`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting an architecture/story's own assumed baseline agent
  behavior (e.g. "the model reliably calls tool X for question Y")
  without live-testing it independently of the new feature under
  build** — the assumed "existing full-search baseline" trigger
  condition for `AC-02`/`AC-03` turned out to depend on a real,
  pre-existing, unrelated tool-contract gap (`ESC-047`) the architecture
  pass had no way to know about without a live probe. Found live,
  `REQ-SB-58-US-01-T02`.

### Open follow-ups

- `ESC-046` (`T01`) — legacy-flat-vs-OKF-directory filename-stem
  collision in `vault_indexing`, recommend `/bug` capture (Area: Logic).
- `ESC-047` (`T02`) — `retrieve_notes_in_agent_scope`'s own MCP tool
  requires the calling model to self-report an internal `agent_id` it is
  never told, recommend `/bug` capture (Area: Logic).

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Single-story, single-sprint
grouping — the only `Ready`, ungrouped story in scope this pass (scoped
explicitly to `REQ-SB-58-US-01`). Dependency graph confirmed by direct read of
each task file's own `depends_on:` frontmatter (`T01` independent root, `T02`
→ `T01`), acyclic, single phase (`P1`). No cross-sprint edge needed since both
of the story's own blocking stories (`REQ-SB-54-US-01`/`REQ-SB-57-US-01`) are
already `Done`. Sizing calibrated against this project's own confirmed
2-task/S precedent (`SPRINT-029`, `SPRINT-036`) — not oversized. No ambiguity
in the partition (one story, two tightly-coupled tasks, obviously one sprint;
no equally-valid alternative grouping exists since there is no other
ungrouped story to fold with or split against). No blocked story — both
external blockers already shipped. No MUST-FLAG trigger fired: no material
assumption (both tasks' `depends_on` were read directly from their own
frontmatter, not inferred), no ADR created or changed (product-owner does not
write ADRs), no `ESCALATIONS.md` entry, no cross-sprint dependency introduced,
no oversized grouping, no genuinely unclear/multiple-equally-valid partition.

gate: clear 2026-08-18 (product-owner) — no trigger fired; see itemized
reasoning above. Sprint `status: Draft → Ready`. Eligible for
`/implement-sprint`.
