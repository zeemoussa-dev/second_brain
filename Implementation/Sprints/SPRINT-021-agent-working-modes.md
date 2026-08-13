---
id: SPRINT-021
title: Agent Working Modes — Autonomous/Supervised/Manual gating + Pending Approvals surface
status: Done                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Built and verified live 2026-08-12 — all 9 tasks Done, all 8 locked ACs verified live; flagged for the human's spot-check pass on scope-internal judgement calls (T07's CSS port + console-error fix, see REVIEW-QUEUE.md) and to harvest this Retrospective into Implementation/Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-12"                        # YYYY-MM-DD when status → Done
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

# SPRINT-021 — Agent Working Modes

## Sprint Goal

Build and verify `REQ-SB-21-US-01` end to end: a per-agent working-mode
setting (Autonomous / Supervised / Manual), the corrected two-axis gate on
`agents_router.py::_invoke_action` (`ADR-020` — Supervised gates on an
action's own `mutates` classification, Manual gates on trigger source
including a new `hub_routed` refusal), the matching background-pipeline
gate, and a real Pending Approvals surface (list/approve/decline).

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — all 9 tasks belong to
  `REQ-SB-21-US-01`/`REQ-SB-21`, the only story assigned here.
- **Foundation of a larger dependency chain, not a standalone build.** Two
  downstream stories in the same "Compass Expert" business chain carry
  real, decomposer-confirmed cross-story `depends_on` edges onto this
  story's own tasks: `REQ-SB-35-US-01` (Vault Filing Expert, Tier-2
  approval) needs `T03`/`T06`; `REQ-SB-36-US-02` (the Compass Expert
  pilot) needs `T02`/`T09` (the Autonomous-mode check and the `mutates`
  classification). This sprint is sequenced before both — see
  `SPRINT-023`/`SPRINT-024`'s own `depends_on_sprints` edges.
- **Why NOT bundled with `REQ-SB-20-US-01` (Section Hub Intelligence),
  despite both being `Ready`, `gate: clear`, `P1`, and part of the same
  overall chain:** see `SPRINT-020`'s own Grouping Rationale — the two
  stories' task graphs have zero `depends_on` edge onto each other, touch
  disjoint file sets, and bundling would remove real parallelism and
  roughly double this sprint's own size for no dependency-graph benefit.
  Kept as two separate, independently-sequenced sprints.
- **Sizing estimate and a real size note, not silently absorbed:** ~9
  tasks, L — one task larger than this project's own established 8-task L
  ceiling (`SPRINT-010`, `SPRINT-011`, `SPRINT-014`, `SPRINT-015`).
  **Splitting this story's own tasks across two sprints was considered and
  rejected**, not overlooked: `REQ-SB-21-US-01`'s 9-task graph
  (`T01: []`, `T02: [T01]`, `T03: [T01]`, `T09: []`, `T04: [T02, T03,
  T09]`, `T05: [T02, T03]`, `T06: [T03, T04, T05]`, `T07: [T04, T06]`,
  `T08: [T06, T07]`) is one single, already-decomposed story's own
  dependency graph with no natural, independently-valuable seam — every
  task chains toward the same locked ACs (`AC-01`…`AC-08`), and this
  project's own `SPRINT-012` precedent already established that splitting
  a single story's task graph across a sprint boundary "would contradict
  hard rule 7" (never contradict the decomposer's own `depends_on` edges,
  which describe one continuous build, not two independently-shippable
  halves). One task over the prior ceiling is a marginal, natural
  consequence of this already-locked story's own task count, not an
  ambiguous grouping call — not flagged as oversized.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-021 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-21-US-01](../UserStories/REQ-SB-21-US-01-agent-working-modes.md) | Per-agent working mode (Autonomous / Supervised / Manual) | P1 | Done |

**Tasks in scope** (dependency order): [[REQ-SB-21-US-01-T01]]
(`agent_working_modes.json`/`agent_pending_approvals.json` vault-writer
primitives, `depends_on: []`), [[REQ-SB-21-US-01-T09]] (`agent_registry.py`
`mutates` classification + `get_action` helper, `depends_on: []`),
[[REQ-SB-21-US-01-T02]] (`working_mode_registry.py`, `depends_on: [T01]`),
[[REQ-SB-21-US-01-T03]] (`pending_approval_registry.py`, `depends_on:
[T01]`), [[REQ-SB-21-US-01-T04]] (`_invoke_action`/`_execute_action`
two-axis gate, `depends_on: [T02, T03, T09]`), [[REQ-SB-21-US-01-T05]]
(background-pipeline gate, `depends_on: [T02, T03]`),
[[REQ-SB-21-US-01-T06]] (`pending_approvals_router.py`, `depends_on: [T03,
T04, T05]`), [[REQ-SB-21-US-01-T07]] (frontend working-mode picker +
`.chat-proposal` card, `depends_on: [T04, T06]`), [[REQ-SB-21-US-01-T08]]
(`MyDayApprovalsPage.tsx`, `depends_on: [T06, T07]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This sprint is a root of the dependency
  chain (`SPRINT-023`/`SPRINT-024` depend on it, not the reverse).
- `ADR-018`/`ADR-020` are both `Accepted` (`ADR-020` supersedes `ADR-018`
  points 3/5 only) but still carry their own open human-review flag on the
  story; not a blocker for `/implement-sprint`, recorded here for
  visibility only.

---

## Out of Scope

- `REQ-SB-20-US-01` (Section Hub Intelligence & Cross-Section Routing) —
  considered for bundling, rejected; see Grouping Rationale. Built in its
  own sprint, `SPRINT-020`.
- `REQ-SB-35-US-01`, `REQ-SB-36-US-02` — the two downstream stories that
  depend on this one's Pending-Approvals/`mutates`/working-mode machinery;
  each has its own sprint (`SPRINT-023`, `SPRINT-024`), sequenced after
  this one via `depends_on_sprints`.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no update needed this pass — the prior `/plan-tasks` architecture pass already described `ADR-020`'s corrected mechanism in full; confirmed unchanged by direct re-check)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-020`, already `Accepted` from the prior `/plan-tasks` pass; no new ADR needed at build time — the build matched the design with no deviation)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — matched exactly.
  No task was split, dropped, or merged during the build. `T04`'s own
  scope grew slightly beyond its written sample (composing around a
  second, un-anticipated file drift — `SPRINT-020`'s `keywords`
  support, on top of the already-known async chat/memory drift) but
  this was absorbed within the same task, not a re-estimate.

### What worked

- **Composing every backend task around the REAL current file, every
  time, without exception** — `T04` (`agents_router.py`, two
  independent drifts stacked: `REQ-SB-25`/`26`'s async chat/memory
  *and* `SPRINT-020`'s keywords support), `T05`
  (`email_classification.py`, confirmed byte-identical to its own
  "Before" narrative — a useful negative-drift confirmation), `T06`
  (`main.py`, `skills_router`/`system_health_router`/`mcp_server`
  registrations the sample never knew about), `T08` (`MyDayPage.tsx`,
  `REQ-SB-22-US-01`'s rolling-7-day-window navigator). Reading the real
  file first, every time, before writing a line, caught every drift
  before it became a silent regression.
- **Backend-layer-first live verification, deepest task first** — `T01`
  smoke-checked before `T02`/`T03`, both smoke-checked before `T04`/`T05`
  ever ran against them, `T04`/`T05` fully verified before `T06`, `T06`
  before `T07`/`T08`. Every layer's own real behaviour was confirmed
  independently before the next layer composed on top of it, so a
  defect at any layer would have been caught at its own source, not
  discovered three layers later as a confusing symptom.
- **Real, deliberate live-side-effect verification, not simulated
  states** — every "Autonomous executes" / "Supervised proposes" /
  "Manual refuses" claim was proven with a genuine Outlook/Compass
  capture run (or the deliberate absence of one, confirmed via the
  history audit trail and, for the background/meeting case, a real
  filesystem `LastWriteTime` spot-check), not a mocked or stubbed
  response.
- **Headless-Chrome-via-CDP for the frontend, including a real click
  round trip** — the working-mode picker, the `.chat-proposal` card's
  live Approve/Decline, and the standalone `/my-day/approvals` page
  were all driven via real DOM clicks (React-Fiber-props `onChange` for
  the controlled `<select>`, per this project's own established
  Learnings technique) against the real running Vite dev server, not
  asserted from source code alone.

### What didn't work

- **A background/scheduled real capture call (`run_capture_and_record_
  completion`, especially the full 39-meeting sweep) can take
  1.5–5 minutes end to end**, well past this shell's own 2-minute
  default command timeout — several verification steps needed
  `run_in_background` + `flush=True` output + explicit polling loops
  rather than a single blocking call. One first attempt at the
  `AC-07` Manual+`hub_routed` check was killed mid-flight by this
  timeout, silently leaving `email-capture`'s mode already flipped to
  `autonomous` before a naively-labelled "manual" re-run reported a
  false-shaped pass — caught before being recorded, corrected with an
  explicit `set_agent_working_mode` at the top of the retry script.
- **A stray, already-running dev process from before this session**
  (port 8001, `--reload`) produced a genuine OS-level stale-listener
  condition — `Get-Process`/`taskkill` both reported the PID as gone,
  yet the socket stayed bound to it. Worked around with a second
  instance on port 8002 rather than losing time fighting an unkillable
  handle; not fully root-caused (see Open follow-ups).
- **A prior task's own explicitly-authorized "harmless, no cleanup
  needed" throwaway test data (`T01`'s smoke-check `pending_approval_id
  ="abc123"` entry) became a real, live-reproducible defect once a
  *later* task (`T07`) started rendering every `"proposal"`-kind entry
  and resolving its live status** — an assumption that held at the time
  it was made stopped holding once new code was layered on top of it.
  Caught by the console/network check `T07`'s own Tests block already
  mandates, not by inspection.

### Patterns to carry forward

- **A "harmless, no cleanup needed" throwaway test artefact is only
  harmless relative to the code that exists *at the time the smoke
  check runs* — re-check that assumption whenever a later task adds
  new code that iterates/renders the same store unconditionally**, and
  either prune the artefact or make the new code degrade gracefully
  (ideally both, as done here: `.catch(() => {})` for defense-in-depth,
  plus pruning the one stale entry).
- **When a real background/scheduled pipeline call is part of a task's
  own mandated live verification, assume multi-minute latency up front
  and background the shell call with unbuffered (`flush=True`/`-u`)
  output from the start**, rather than discovering the timeout
  mid-verification and having to re-run.
- **A task's own `## Files to Modify` list is a strong default, not an
  absolute ceiling, when the missing piece is a mechanical, zero-
  judgement port of already-approved design (e.g. copying CSS rules
  verbatim from the signed-off prototype) that the task's own written
  Constraints already assumed existed** — log it as a scope-internal
  judgement call for human spot-check (flag the task, not the sprint),
  rather than either silently improvising outside the documented rule
  or blocking the whole build on a trivial, zero-ambiguity gap.

### Antipatterns to avoid

- Do not trust a stray already-running dev-server process on the
  project's usual port without first confirming what code it is
  actually serving — in this session it happened to have picked up the
  same edits via its own `--reload` watcher, but that is luck, not a
  property that can be assumed next time. Prefer starting a fresh,
  explicitly-controlled instance on a different port when a port
  conflict's root cause cannot be quickly confirmed.
- Do not label a verification step's output based on the *intended*
  precondition (e.g. "should be manual") without an explicit, in-script
  assertion/set of that precondition immediately beforehand — a
  disturbed prior state (here, from a killed-mid-flight earlier attempt)
  can silently invalidate the label.

### Open follow-ups

- The port-8001 stale-listener condition (a PID neither `Get-Process`
  nor `taskkill` could find, yet still shown as the owning process of a
  live `Listen` socket) was worked around, not root-caused. If it
  recurs, worth a deeper OS-level investigation (`netsh` reset, or
  checking for a WSL/Windows PID-namespace interaction) rather than
  routing around it again.
- `T07`'s two scope-internal judgement calls (the CSS port into
  `agent-panel.css`; the `.catch(() => {})` robustness fix) are logged
  for human spot-check per this sprint's own `gate: flagged` — no
  further build action needed, just a human skim.

---

## Notes

**Sprint assembled 2026-08-12 (`/plan-sprints`, operator-directed batch —
the "Compass Expert" business chain).** Part of a 5-sprint sequence
(`SPRINT-020`…`SPRINT-024`); see `SPRINT-020`'s own Notes for the full
chain-partitioning rationale, applied identically here.

**Gate: `gate: clear` 2026-08-12.** No MUST-FLAG trigger fires: (1) no
material assumption — the partition is read directly off the already-
recorded task `depends_on` graph; (2) `REQ-SB-21` is not `<!--
Draft -->`/unfinalised; (3) product-owner does not write ADRs — none
touched; (4) no new `ESCALATIONS.md` entry written by this pass; (5) not
oversized — re-checked explicitly given the 9-task count (one above the
prior 8-task L ceiling), reasoned through above and found to be a natural,
non-splittable consequence of one already-locked story's own task count,
not an ambiguous or forced grouping; no cross-sprint dependency introduced
for *this* sprint specifically (`depends_on_sprints: []`); (6) N/A
(coder-only trigger); (7) no contradictory inputs; (8) not genuinely
ambiguous — one story, one natural partition, the one considered
alternative (bundling with `REQ-SB-20-US-01`) documented and rejected
above. Advances `Draft → Ready`.

**Coder pass (2026-08-12, `/implement-sprint`) — built and verified
live, `status: Ready → Done`.** All 9 tasks built in dependency order
and marked `Done`; all 8 locked ACs on `REQ-SB-21-US-01` verified live
against the real backend/frontend/vault/Outlook/Compass. Full detail:
the story's own Notes (coder pass) and each task's own Implementation
Log. `gate: flagged` — two scope-internal judgement calls from `T07`
logged for human spot-check (not escalations), and this Retrospective
itself needs a human skim to harvest into `Implementation/Learnings.md`.
`REVIEW-QUEUE.md` and `ESCALATIONS.md` → `ESC-013` updated accordingly.
This sprint is now a satisfied `depends_on_sprints` prerequisite for
`SPRINT-023`/`SPRINT-024`.
