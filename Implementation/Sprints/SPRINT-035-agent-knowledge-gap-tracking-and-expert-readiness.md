---
id: SPRINT-035
title: Agent knowledge-gap tracking and Expert readiness
status: Done
gate: flagged
gate_reason: "Coder retro drafted 2026-08-14 (Sprint wrap) — human skims the retro and propagates patterns into Implementation/Learnings.md. Also carries the parent story's own trigger-3 flag (ADR-032 created at /plan-tasks) — the human reviews ADR-032 alongside the built code."
phase: P1
depends_on_sprints: []
sizing_estimate: "~8 tasks, L"
created: 2026-08-13
started: "2026-08-14"
completed: "2026-08-14"
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-035 — Agent knowledge-gap tracking and Expert readiness

## Sprint Goal

Record every honest "I don't know" an agent surfaces as a knowledge gap, let
the user close it (human answer or delegated research), and surface a
declining open-gap count as an Expert-readiness signal.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-40-US-01` is the only story
  here. Its 8 tasks form a mostly-linear internal chain (`T01 → T02 → {T04,
  T05, T07} → T06 → T08`, `T03` independent); verified directly against
  every task file's real frontmatter that none carries a cross-story
  `depends_on` edge — it composes entirely with already-`Done` work
  (`REQ-SB-33`/`35`/`36`), not with any sibling story in this batch.
- **Why NOT bundled with `REQ-SB-41-US-01` (its one real downstream
  consumer):** would produce a 10-task sprint, past this project's own `L`
  ceiling (9 tasks). Kept standalone; `REQ-SB-41-US-01` is scheduled in its
  own small sprint instead (`SPRINT-036`), ordered after this one.
- **Sizing estimate:** ~8 tasks, L.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-40-US-01](../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md) | Agent knowledge-gap tracking — record every honest "I don't know", let the user close it, surface a declining open-gap count as Expert readiness | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (vault_writer.py primitives,
`depends_on: []`) → `T02` (knowledge_gap_tracking.py business module,
`depends_on: [T01]`); `T03` (state.py gap_recorded field + system prompt,
`depends_on: []`) → `T04` (graph.py record_knowledge_gap tool + node,
`depends_on: [T02, T03]`) → `T05` (human-answer closing path, `depends_on:
[T02]`) → `T06` (delegated-research closing path, `depends_on: [T02, T05]`),
`T07` (agents_router.py knowledge-gaps list endpoint, `depends_on: [T02]`)
→ `T08` (AgentDetailPanel.tsx Knowledge gaps tab, `depends_on: [T05, T06,
T07]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.

---

## Out of Scope

- Agent Overview surface (`REQ-SB-41-US-01` → `SPRINT-036`), which consumes
  this story's `T08` output.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (already landed at `/plan-tasks`, `ADR-032`'s own architect pass — no further change needed at build time)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-032`, already `Accepted` from `/plan-tasks`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — matched exactly. No
  task was split, dropped, or merged. `T04` (the graph tool/node) and `T06`
  (the delegated-research closing path) were correctly the heaviest by
  verification effort, not code volume — extending an already-proven
  interception pattern (`ADR-017`) took little code, but genuinely proving
  it live, plus proving the shared graph's ordinary-chat behavior was
  unaffected on 2 separate agents, was the real cost.

### What worked

- **Extending `ADR-017`'s already-proven tool-interception pattern a second
  time** (`request_cross_section_help` → `record_knowledge_gap`) was a
  same-shape, low-risk extension exactly as designed — the new node/branch/
  loop-back-edge composed cleanly with zero changes to any pre-existing
  node.
- **Reading the turn's real `HumanMessage` instead of trusting the model's
  own `topic` tool argument** (`ADR-032` point 1) was directly, live-
  confirmed correct: the recorded gap's `question` field was the full,
  real question text, not the model's short paraphrase.
- **Composing already-`Done` chains as black boxes** (`vault_filing_expert`
  for `T05`, `knowledge_bootstrap` for `T06`) meant zero reimplementation
  and zero regressions in either — both were confirmed byte-for-byte
  unmodified after this sprint.

### What didn't work

- **The real vault's current agent configuration could not, as-is, reach a
  genuine `"written"` research outcome (`T06` `AC-04`)** — no agent has
  both real `web-research` skill access and a Hub-routing keyword match,
  and the two natural Section-Hub candidates (`vault-qa`/`vault-filing-
  expert`) started in the same Section, which the two-hop relay's own
  design requires them not to be. Reaching a genuinely real (not mocked)
  `"written"` outcome needed 3 temporary, real, fully-reverted state
  changes through the app's own existing APIs (a skill grant, a Provider
  swap, a Section reassignment) rather than a single clean call.

### Patterns to carry forward

- **When a locked AC needs a real positive outcome from a multi-hop
  composed chain, and the real vault's current configuration cannot reach
  it as-is, temporarily reconfigure real state through the app's own
  already-`Done` APIs (skill grant / Provider assignment / Section
  assignment), verify, then revert and independently reconfirm the
  revert** — stronger evidence than a mock, and bounded/reversible since
  it goes through real, already-trusted endpoints, not direct file/state
  surgery. Extends this project's own established "closest-to-real
  substitute" precedent (`SPRINT-025`/`SPRINT-027`) to a multi-step Hub-
  routing scenario specifically.
- **`uvicorn --reload`'s WatchFiles-triggered restart can silently keep
  serving the OLD worker process's routes for an extended period** when a
  long-running background asyncio task (this project's own
  `run_capture_if_idle` scheduler tick) is in flight at the moment of
  reload — a route added in the most recent edit returned a bare `404`
  against the still-old worker for several real interleaved requests
  before this was caught. The fix (kill both the reloader parent and its
  child worker PID, then start a single fresh non-`--reload` instance for
  the remainder of the session) is a variant of this project's own
  already-documented specific-PID-kill-and-restart protocol, worth naming
  explicitly for the `--reload` + long-background-task combination.
- **Edge's own CDP `/json/new` endpoint requires `PUT`, not `GET`, on this
  installed browser version** (`Edg/151`) — a real, version-specific
  behavior change from the `GET`-based examples this project's own prior
  CDP-driving sessions used; worth checking directly (`curl -X PUT`) rather
  than assuming GET still works, next time a fresh CDP driver script is
  written against a possibly-updated local Edge install.

### Antipatterns to avoid

- **Assuming a task's own illustrative "obscure/nonsensical subject"
  no-results test technique (established `SPRINT-036`/`REQ-SB-36-US-01`)
  still reliably produces an honest `"no_results"` once a real web-search
  Provider is genuinely reachable** — a privacy-refusal reply from the
  real model was itself treated by the composed chain as a "found" result
  and filed as a guide note, a real, disclosed finding about the already-
  `Done` chain's own behavior, not a defect in this sprint's own code. The
  AC was still satisfiable and was satisfied via an earlier, independently
  real `"no_results"` induction (before the real web-search access was
  granted) — worth remembering that "genuinely no relevant content exists"
  and "the model declines to answer" are two different real conditions a
  single obscure-subject prompt can hit.

### Open follow-ups

- **`REQ-SB-41-US-01` (Agent Overview, `SPRINT-036`)** is this story's one
  real downstream consumer (`count_open_gaps()`/the Knowledge gaps tab as
  a possible Overview-surfaced signal) — scheduled next, already ordered
  after this sprint per the product-owner's own grouping rationale.
- **Human review still owed:** `ADR-032` itself (trigger-3, carried on both
  the story and this sprint), plus the two scope-internal judgement calls
  logged in `T06`'s and `T08`'s own Implementation Logs.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).**

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption — zero cross-story deps confirmed directly off real task
frontmatter; (2) `REQ-SB-40` is finalized PRD text; (3) product-owner does
not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (8
tasks sits just under this project's own 9-task `L` ceiling); not a blocked
story; no cross-sprint dependency needed for this sprint itself; (6) N/A;
(7) no contradictory inputs; (8) not ambiguous — no genuine alternative
grouping exists once the 10-task-oversized bundle with `REQ-SB-41-US-01` is
ruled out on sizing grounds. Advances `Draft → Ready`.

**Coder pass (`/implement-sprint`, 2026-08-14) — sprint `Done`.** All 8
tasks under `REQ-SB-40-US-01` built and verified live in dependency order
(`T01 → T02 → {T04(+T03), T05, T06, T07} → T08`); all 7 locked ACs verified
against the real running app. `gate` stays `flagged` — carries the parent
story's own `trigger-3` (`ADR-032` created) plus this sprint's own retro
draft, per the "coder drafts the retro, sets `gate: flagged`, human
propagates learnings" rule. Nothing blocked; no `ESCALATIONS.md`/
`REVIEW-QUEUE.md` entry written by this pass. `BACKLOG.md`'s Sprint Status
table and `REQ-SB-40` row both updated to `Done`.
