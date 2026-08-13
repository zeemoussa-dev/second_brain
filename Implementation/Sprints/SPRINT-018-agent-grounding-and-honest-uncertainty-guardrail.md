---
id: SPRINT-018
title: Agent grounding & honest-uncertainty guardrail — global system-prompt instruction on every agent's real conversational reply path
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retro drafted, awaiting human harvest into Learnings.md; T01 itself also carries a separate scope-internal-judgement-call flag (AC-03 verification technique) — see REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~1 task, XS"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-018 — Agent grounding & honest-uncertainty guardrail

## Sprint Goal

Build and verify `REQ-SB-33-US-01-T01`: extend `history_entries_to_messages`'s
existing identity `SystemMessage` with a grounding/honest-uncertainty
instruction so every agent's real conversational reply (`REQ-SB-25`) stays
grounded in its own tool results and honestly says "I don't know" instead
of fabricating an answer, verified against all 4 locked ACs.

---

## Grouping Rationale & Sizing

- **Why standalone:** `REQ-SB-33-US-01` is the only `Ready`, ungrouped,
  `gate: clear` story with no outstanding blocker this pass. It has exactly
  one task (`REQ-SB-33-US-01-T01`, `depends_on: []`), scoped to a single
  function in a single file (`app/business/agent_orchestration/
  state.py::history_entries_to_messages`) — a self-contained prompt-content
  change with no dependency on any other in-flight work. `REQ-SB-25-US-01`,
  the story it extends, is already `Done` (`SPRINT-014`), so no
  `depends_on_sprints` edge is needed.
- **Considered and rejected: bundling with `REQ-SB-20-US-01`** (the other
  `Ready`, ungrouped, `gate: clear`, P1 story this pass — phase-compatible
  on paper). Rejected because it would be a cohesion-free grouping, not a
  genuine dependency/shared-surface reason: `REQ-SB-20-US-01` is a 6-task
  story (`REQ-SB-20-US-01-T01`…`T06`, agent-keyword routing/hub-request
  plumbing across `vault_writer.py`, a new business module, the agents
  router, orchestration state, `graph.py`'s routing node, and a frontend
  panel row) touching an entirely different concern and file set than this
  story's single prompt-content edit. Forcing them into one sprint would
  bloat a naturally XS-sized, self-contained change into a mixed-concern
  sprint for no dependency or shared-surface reason — the same "don't
  force an artificial pairing to avoid a small sprint" reasoning
  `SPRINT-017`'s own Grouping Rationale already established for this
  project. `REQ-SB-20-US-01` remains ungrouped, eligible for its own
  `/plan-sprints` pass (or a future batch with other Section-Hub-adjacent
  work).
- **`REQ-SB-31-US-01` deliberately excluded** — still `Draft`/mid-`/design`
  in a separate, parallel agent run per this pass's own instruction; not
  `Ready`, not eligible for `/plan-sprints` regardless.
- **Sizing estimate:** ~1 task, XS — matches this project's smallest
  precedent sprints (`SPRINT-003`, `SPRINT-005`, `SPRINT-017`): one
  self-contained task, one function edited, verified via real prompting
  against 4 locked ACs (no new UI, no ADR, no new file).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-018 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-33-US-01](../UserStories/REQ-SB-33-US-01-agent-grounding-and-honest-uncertainty-guardrail.md) | Agent grounding & honest-uncertainty guardrail | P1 | Done |

**Task in scope:** [[REQ-SB-33-US-01-T01]] — Extend
`history_entries_to_messages`'s existing identity `SystemMessage` with a
grounding/honest-uncertainty instruction
(`Implementation/Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- `REQ-SB-25-US-01` (the real conversational reply path this story guards)
  is already `Done` (`SPRINT-014`) — no cross-sprint ordering needed.
- No new external-integration surface; no ADR created or changed
  (`ADR-015` already covers `history_entries_to_messages` and is
  `Accepted`).

---

## Out of Scope

- `REQ-SB-20-US-01` (Section Hub Intelligence & Cross-Section Routing) —
  considered for bundling, rejected; see Grouping Rationale.
- `REQ-SB-31-US-01` (System Health View) — still `Draft`/mid-`/design` in a
  parallel run; not touched by this sprint.
- A reply-verification/citation mechanism, per-agent configurability, or
  any new Agent Settings UI surface — all explicitly out of this story's
  own scope (see story's Non-Goals/Constraints).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (already done at `/plan-tasks` — architect's own Addendum; no further change needed here)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (N/A — no new ADR this sprint, per the architect's own already-recorded finding)
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

- **Estimated:** ~1 task, XS — **Actual:** 1 task, XS (one prompt-content
  edit to one function; verification, not code volume, was the real cost)
  — **Takeaway:** the sizing estimate was accurate for build effort; what
  the estimate doesn't capture is real-provider-call latency variance
  during live verification (see "What didn't work" below) — worth naming
  explicitly in future XS-sized prompt-only stories that still require
  several real Provider round-trips to verify.

### What worked

- **Real, unmodified production code path for the "hard" AC (AC-03)
  without touching any out-of-scope file** — rather than editing
  `mcp_client.py` (named as an example technique in the task's own Tests,
  but outside this task's `## Files to Modify`) to point at an
  unreachable target, a throwaway script (kept only in the session
  scratchpad, never in `src/`) loaded the real MCP tools from the real
  running server and monkeypatched one tool's `.coroutine` in-process to
  raise, then called the real `run_agent_conversation` directly. This
  exercised the genuine, unmodified `_call_model`/`_execute_tools` code
  path end-to-end (real model, real prompt, real exception handling) with
  zero file edits and zero revert step needed — a reusable technique for
  any future "induce a real failure in a specific dependency" AC where
  the obvious approach would touch a file outside the task's own scope.
- **Asking a question about a real, existing vault entity (ADNOC) framed
  around a plausible general-knowledge fact** was a sharper AC-04 test
  than a wholly fictitious question — it puts the model in the exact
  tempting position the AC describes (an in-scope, real entity the model
  may "know" real-world facts about) rather than a case so obviously
  out-of-vault the model would decline regardless of the new instruction.
- **Cross-checking the model's AC-01 answer against an independent,
  direct call to the same tool function** (`vault_query_tools.
  list_known_customers()`, called directly, not through the agent) turned
  "the reply sounds plausible" into "the reply is byte-for-byte the real
  tool's own output" — a stronger regression-guard confirmation than
  eyeballing the reply alone.

### What didn't work

- **The shared dev backend became fully unresponsive (not just slow)
  mid-verification** — a plain `GET /agents` timed out while the first
  AC-01 chat call was still in flight, and this did not resolve after
  several minutes (well past this project's own documented "Compass calls
  take a while" precedent). Root cause not fully diagnosed within this
  task's own scope (`graph.py`'s `_call_model` node is a plain, synchronous
  `def`, not `async def` — plausible enough to block the single asyncio
  event loop for the duration of a real Compass HTTP call, but `graph.py`
  is out of this task's file scope to fix or even conclusively confirm).
  Recovered via the standing MEMORY.md protocol (specific-PID kill, never
  by image name; documented `run-backend.cmd` relaunch) — cost real time,
  not a build blocker, but the underlying `_call_model` sync-node question
  is worth a dedicated look before it recurs on a busier verification day.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **In-process monkeypatch of a real, already-loaded dependency to induce
  a failure condition, instead of editing a file outside the task's own
  scope** — when a task's own Tests section names an out-of-scope-file
  technique as one *example* way to induce a real failure condition (not
  as a locked-AC requirement of that specific mechanism), a throwaway
  script that loads the real dependency, monkeypatches just the failing
  call in-process, and invokes the real, unmodified production function
  directly achieves the same genuine verification with zero file edits
  and zero revert step. Found live 2026-08-12, `REQ-SB-33-US-01-T01`.
- **Frame a "does the model fabricate from general training knowledge"
  test (AC-04-style) around a real, in-vault entity, not a wholly
  fictitious one** — asking about real-world facts of an entity that
  genuinely exists in the vault (but whose specific fact was never
  actually retrieved by any tool call) is a sharper test of "does the
  system prompt actually stop the model from answering from training
  knowledge" than an obviously-irrelevant question, which a model might
  decline for unrelated scope reasons regardless of any grounding
  instruction. Found live 2026-08-12, `REQ-SB-33-US-01-T01`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a long-running real-Provider chat call is "just slow" without
  a control check** — the first AC-01 attempt was left running past the
  point where this project's own documented Compass-latency precedent
  would predict completion, without independently confirming the server
  was still alive via a trivial, unrelated `GET`. A quick `GET /agents`
  probe against the same server, in parallel with any single real-Provider
  call expected to take more than ~30-60s, would have caught the genuine
  hang sooner instead of waiting on an indefinitely stuck background call.
  Found live 2026-08-12, `REQ-SB-33-US-01-T01`.

### Open follow-ups

- **`graph.py`'s `_call_model` node is a synchronous `def`, invoking a
  blocking `model.invoke(...)` call inside `_GRAPH.ainvoke()`'s otherwise
  async graph** — plausible root cause of the real dev-backend hang this
  task hit live (see "What didn't work"), but `graph.py` is out of this
  task's own file scope to confirm or fix. Worth a dedicated look (make
  `_call_model` genuinely `async def`, matching this project's own
  standing `MEMORY.md` Constraint on every graph node/its own call chain)
  before it recurs during a busier concurrent-verification session. Not
  filed as a `/bug` yet — no confirmed root cause, only a strong
  correlation observed live once.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired: (1) no material
assumption — the grouping decision (standalone sprint, `REQ-SB-20-US-01`
left out) is read directly off the task/story files' own already-resolved
scope and size, not guessed; (2) `REQ-SB-33` is not `<!-- Draft -->` in the
PRD; (3) no ADR touched (product-owner does not write ADRs; `ADR-015`
already `Accepted` and unchanged); (4) no new `ESCALATIONS.md` entry
written by this pass; (5) not oversized (the smallest possible unit — one
task), not `Blocked`, no cross-sprint dependency introduced
(`depends_on_sprints: []`); (6) N/A (coder-only trigger); (7) no
contradictory inputs; (8) not genuinely ambiguous — one story, one
plausible partition, considered-and-rejected alternative documented above
rather than left implicit. Advances `Draft → Ready`.

**Sprint assembled (2026-08-12):** 1 story, 1 task, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.
