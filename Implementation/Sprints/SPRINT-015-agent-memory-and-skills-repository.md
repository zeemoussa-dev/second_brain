---
id: SPRINT-015
title: Agent memory (persistent, per-agent fact recall) and skills repository (registration + per-agent access plumbing)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "T03's correction spot-checked and accepted 2026-08-12 — no longer a factor. Retrospective drafted below, awaiting human skim/harvest into Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-014]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
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

# SPRINT-015 — Agent memory (persistent, per-agent fact recall) and skills repository (registration + per-agent access plumbing)

## Sprint Goal

Extend `SPRINT-014`'s new LangGraph conversation graph and shared MCP
server with two independent capabilities: persistent, per-agent memory an
agent's replies can draw on across separate conversations (`REQ-SB-26`),
and a code-level skill catalog with persisted, per-agent access grants
(`REQ-SB-27`, plumbing only — no first real skill built yet).

---

## Grouping Rationale & Sizing

- **Why grouped:** Both stories are `phase: P1` extensions of the exact
  same architectural surface `SPRINT-014` lands — `ADR-015`'s single
  compiled `langgraph.graph.StateGraph`
  (`app/business/agent_orchestration/graph.py`) and shared `FastMCP`
  server (`app/api/mcp_server.py`) — and both carry a real, decomposer-
  authored cross-story `depends_on` edge into `REQ-SB-25-US-01`'s own
  tasks (`REQ-SB-26-US-01-T02`/`T03`/`T04` → `REQ-SB-25-US-01-T02`/`T07`/
  `T08`; `REQ-SB-27-US-01-T02` → `REQ-SB-25-US-01-T05`), so neither can
  start before `SPRINT-014` is `Done` — a real, shared sprint boundary,
  not two unrelated stories forced together. There is no dependency edge
  *between* the two stories themselves (`REQ-SB-26-US-01` touches
  `state.py`/`graph.py`/`vault_writer.py`'s memory primitives/
  `agents_router.py::chat`'s memory wiring; `REQ-SB-27-US-01` touches
  `skill_tools.py`/`skill_registry.py`/`skills_router.py`/
  `vault_writer.py`'s skills-state primitives/`main.py` — no shared file
  between the two stories' own task sets, and neither story's own
  `depends_on` graph references the other), so they run as two
  independent chains inside one sprint, exactly the same shape
  `SPRINT-007` already established for two independent, similarly-scoped
  stories sharing one origin.
- **Why grouped together rather than each standalone:** combined they
  total 8 tasks (4 + 4), matching `SPRINT-010`'s own 8-task L precedent —
  the established single-sprint ceiling — without exceeding it. Neither
  story alone (4 tasks each) would meaningfully under-use a sprint cycle
  on its own the way `REQ-SB-17-US-01`'s 2-task shape did in `SPRINT-007`,
  but pairing them still keeps the sprint count reasonable while both
  share one upstream dependency (`SPRINT-014`) and one architectural
  origin (`ADR-015`'s shared graph/MCP-server surface, extended one layer
  further by `ADR-016` for `REQ-SB-26` specifically). This is a clear,
  defensible cohesion call (shared upstream dependency + shared
  architectural surface + matched combined size against precedent), not a
  genuinely ambiguous partition — not flagged. An alternative partition
  (three sprints: `REQ-SB-25` alone, `REQ-SB-26` alone, `REQ-SB-27` alone)
  was considered and rejected as unnecessarily fragmenting two
  same-sized, independently-shippable, same-dependency-boundary stories
  into two separate sprint cycles for no sizing or dependency-graph
  benefit.
- **Sizing estimate:** ~8 tasks, L — 4 tasks per story, each story's own
  chain small and linear (`REQ-SB-26-US-01`: `T01`/`T02` roots → `T03` →
  `T04`; `REQ-SB-27-US-01`: `T01` root, `T02` → `REQ-SB-25-US-01-T05`
  (external) → `T03` depends on `{T01, T02}` → `T04`), comparable in
  per-story shape to `SPRINT-012`'s own 6-task M (this sprint runs two
  such chains rather than one, hence the larger L total).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-015 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-26-US-01](../UserStories/REQ-SB-26-US-01-agent-memory.md) | Persistent, per-agent memory an agent's real conversational replies can draw on across separate conversations | P1 | Done |
| [REQ-SB-27-US-01](../UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md) | Skill repository — registration and per-agent access (plumbing only; first real skill deferred) | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-014` — `REQ-SB-26-US-01-T02`/`T03`/`T04`
  each carry a task-level `depends_on` naming `REQ-SB-25-US-01-T02`/`T07`/
  `T08` respectively (the `agent_orchestration/state.py`/`graph.py`
  scaffolding and `agents_router.py::chat`'s no-trigger-phrase-match
  branch); `REQ-SB-27-US-01-T02` carries a task-level `depends_on` naming
  `REQ-SB-25-US-01-T05` (the shared `mcp_server.py` `FastMCP` instance).
  This sprint cannot start until `SPRINT-014` is `Done`. `/implement-sprint`
  will refuse this sprint otherwise, per hard rule 9.
- `ADR-015` (shared with `SPRINT-014`) and `ADR-016` (Agent Memory's own
  extraction-mechanism ADR, extending `ADR-015` point 13) are both
  `Accepted` — operator-approved 2026-08-12 (`REVIEW-QUEUE.md`). No open
  ADR review blocks this sprint.
- `REQ-SB-27-US-01`'s own prior `ESC-006`/`ESC-011` blockers are both
  resolved (`ADR-015` settled "what is a skill"; the follow-up decomposer
  pass wired the real `depends_on` edge onto `REQ-SB-25-US-01-T05`) — no
  open blocker remains for this story.
- No new external-integration surface — `REQ-SB-26-US-01`'s memory
  extraction reuses the already-resolved model from the same graph call
  (no second Provider resolution); `REQ-SB-27-US-01` registers exactly one
  illustrative stub skill with an honest "not yet available" body, no real
  external capability.

---

## Out of Scope

- **The first real skill's actual implementation** (e.g. image/diagram
  understanding) — explicit follow-on work, per `REQ-SB-27-US-01`'s own
  Non-Goals; no multimodal-capable Provider exists yet.
- **Cross-agent or Section-wide shared memory** — explicitly resolved as
  per-agent only, per `REQ-SB-26-US-01`'s own Non-Goals.
- **A user-facing surface to view/edit/clear agent memory, or a Skills
  card/access-picker UI** — neither story ships any UI this pass.
- **`REQ-SB-28`'s file-upload mechanism as a skill's input** — not assumed
  or designed here.
- **Which agent(s) get default access to a newly registered skill** — not
  decided here; `REQ-SB-27-US-01`'s Scenario 2 explicit-grant model only.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (N/A — no architectural fact changed this pass; `ADR-015`/`ADR-016` already covered both stories in full, per the architect's own prior `/plan-tasks` passes)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (N/A — no new/changed ADR this pass; `ADR-016` was created at `/plan-tasks` time, already `Accepted` before this coder pass began)
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

- **Estimated:** `~8 tasks, L` — **Actual:** 8 tasks (4 + 4), L, all
  `Done`, with exactly one real, live-discovered technical correction
  (`REQ-SB-26-US-01-T03`) beyond its own literal code sample, plus two
  minor scope-internal reconciliations both tasks' own text explicitly
  anticipated (`REQ-SB-27-US-01-T02`'s tool-registration mechanism,
  `T03`'s dispatch-table shape). **Takeaway:** the task-count estimate
  held exactly, and unlike `SPRINT-014` (which needed five real
  corrections composing three genuinely new third-party
  frameworks/protocols for the first time), this sprint needed only one —
  because both stories extended an already-`Done`, already-live-verified
  foundation (`ADR-014`'s registry-composition pattern, `ADR-015`'s
  shared graph/MCP-server) rather than introducing anything genuinely new
  to this codebase. The one correction that *was* needed came from a
  different, narrower risk: a task file authored slightly ahead of a
  sibling story's own final shape (`REQ-SB-25-US-01-T08`'s tool-loop
  landed after this story's own decomposer pass wrote `T03`'s sample).
  Confirms `SPRINT-014`'s own retro takeaway in a positive direction:
  extending an already-proven pattern is genuinely lower-risk than
  composing a new one, even within the same sprint cycle.

### What worked

- **Extending the REAL current file instead of trusting a stale "full
  replacement" sample** — `REQ-SB-26-US-01-T03`'s own code sample would
  have silently regressed `REQ-SB-25-US-01`'s own already-`Done`
  tool-calling loop had it been applied verbatim. Reading the actual
  current `graph.py` first, diffing the task's own *intent* (two new
  nodes) against the file's real current shape, and composing around it
  instead of overwriting caught this before it ever became a live defect.
- **Isolating a memory-recall AC from a sibling story's own already-tested
  mechanism by temporarily clearing the confounding state** —
  `REQ-SB-26-US-01-T04`'s own `AC-01` step (backing up and clearing
  `agent_communication_history.json`'s relevant entry before the second
  chat call) proved the reply's recall genuinely came from
  `agent_memory.json`/`retrieve_memory`, not `REQ-25`'s own already-
  verified history replay — a real, deliberate verification design, not
  an accidental byproduct.
- **Reusing `ADR-014`'s registry-composition pattern a second time
  (`skill_registry.py` mirroring `section_registry.py`/
  `provider_registry.py` almost line-for-line)** — the one deliberate
  divergence (no self-healing default assignment) was easy to keep
  correct precisely because everything else matched a proven shape
  exactly; zero surprises in `T03`'s own smoke checks.
- **Self-managed backend process (explicit kill-and-restart, real PIDs via
  `Get-CimInstance`, never by image name) with the port already known
  from `SPRINT-014`'s own precedent (`8002`)** — no time spent
  rediscovering the port-conflict situation this sprint; it was simply
  applied from the start.

### What didn't work

- **A decomposer-authored task's own literal code sample can drift out of
  sync with a sibling story's own in-flight evolution when both are
  planned close together in time** — `REQ-SB-26-US-01-T03` was authored
  against `graph.py`'s shape as it existed at that story's own
  `/plan-tasks` pass, which predated `REQ-SB-25-US-01-T08`'s own later
  live correction (the tool-execution loop). Root cause: task samples are
  a snapshot of the codebase at authoring time, not a live reference —
  worth naming plainly again, since `SPRINT-014`'s own retro already
  flagged "a task's own literal code sample is a best-effort starting
  point, not a guarantee" for *new-library* integration risk; this sprint
  shows the same principle also applies to *cross-story sequencing* risk
  within one batch of closely-planned stories, not just new-framework
  risk.
- **Every backend restart still costs 60-90 real seconds** (the
  unconditional app-start capture run, `ADR-005`) — expected, documented
  behavior, not a defect, but genuinely added real wall-clock time across
  the 4 restarts this sprint needed (once per task in `REQ-SB-26-US-01`'s
  chain, once more for `REQ-SB-27-US-01-T04`'s router registration).

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Diff a task's own literal "full replacement" code sample against the
  file's REAL current contents before applying it, especially for a file
  a sibling story's own later-completed task may have already extended**
  — never trust "this is what the file should look like" over "this is
  what the file actually contains right now" once more than one story is
  touching the same file/module across a sprint boundary. Re-derive any
  logic that implicitly assumes the file's old shape (e.g., whether an
  earlier node already appended something onto shared state) rather than
  copying the sample verbatim.
- **Isolate a new state-recall mechanism from an already-tested sibling
  mechanism by temporarily neutralizing the sibling's own confounding
  state, not just by trusting the new mechanism "must be" the source** —
  when two independent state sources could both explain the same
  observed correct behavior (here: conversation history replay vs. the
  new long-term memory store), deliberately knock out the already-proven
  one for one verification call to prove the new one is genuinely doing
  the work.
- **`FastMCP` tool registration via a sibling module's own decorator
  import needs zero edits to the server's own defining file** — confirmed
  a second time this sprint; worth treating as the default expectation
  for any future skill/tool addition, not something to re-verify from
  scratch each time.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Treating a decomposer-authored task's own literal code sample as
  necessarily still accurate once a sibling story's own task has shipped
  in the meantime** — even without introducing any new third-party
  library (this sprint's own risk profile, unlike `SPRINT-014`'s), a
  same-file sample can still silently go stale purely from ordinary
  cross-story sequencing inside one active sprint cycle. Always re-read
  the real file immediately before writing to it, never rely on what the
  task file's own snapshot describes.

### Open follow-ups

- **`REQ-SB-26-US-01-T03`'s live-discovered `graph.py` correction is
  parked in `REVIEW-QUEUE.md` for a human spot-check** — not a blocker,
  same pattern `SPRINT-014` established for its own five corrections; see
  the `SPRINT-015 / REQ-SB-26-US-01` entry there.
- **`REQ-SB-27-US-01`'s own explicit Non-Goals remain fully open follow-on
  work** — the first real skill's implementation (e.g. image/diagram
  understanding, needs a multimodal-capable Provider that does not exist
  yet), any Skills-card/access-picker UI (needs its own `/design` pass
  first), and the default-vs-explicit future-skill-access question
  (`ESCALATIONS.md` → `ESC-006`, still `Open`, tracks this).
- **`REQ-SB-20` (Hub Intelligence & Cross-Section Routing)** is the next
  requirement `ADR-015`'s own shared graph/MCP-server surface is expected
  to extend, per that ADR's own text — worth a quick read of `graph.py`'s
  now-four-node shape (`retrieve_memory`/`call_model`/`execute_tools`/
  `extract_memory`) before adding a fifth.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired: (1) no material
assumption — the grouping is grounded directly in the decomposer's own
real cross-story `depends_on` edges (into `SPRINT-014`) and the two
stories' own confirmed independence from each other (no shared file, no
`depends_on` edge between them), not guessed; (2) neither `REQ-SB-26` nor
`REQ-SB-27` is `<!-- Draft -->` in the PRD; (3) N/A (product-owner does
not touch ADRs — `ADR-015`/`ADR-016` were already `Accepted` before this
pass); (4) no new `ESCALATIONS.md` entry written by this pass (`ESC-006`/
`ESC-011` were already resolved by the decomposer's own prior passes);
(5) not oversized (8 tasks matches the `SPRINT-010` L-precedent), not
`Blocked`, and the one cross-sprint dependency
(`depends_on_sprints: [SPRINT-014]`) is not an artificial edge this role
invented — it directly reflects the decomposer's own cross-story
`depends_on` edges, the same non-flagged pattern already established by
`SPRINT-009`/`SPRINT-010` → `SPRINT-008` and `SPRINT-012` → `SPRINT-011`;
(6) N/A (coder trigger); (7) no contradictory inputs; (8) the
combine-vs-split choice (one 8-task sprint vs. two 4-task sprints) has a
clear, reasoned answer given the shared upstream boundary and matched
sizing precedent, not multiple genuinely equally-valid options. Advances
`Draft → Ready`.

**Sprint assembled (2026-08-12):** 2 stories, 8 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint` once `SPRINT-014` is
`Done`.

**Coder pass (`/implement-sprint`, 2026-08-12):** confirmed `SPRINT-014`
`Done` before starting, per hard rule 9. All 8 tasks built and `Done`,
built in dependency order across both independent chains (interleaved:
`REQ-SB-26-US-01-T01` → `REQ-SB-27-US-01-T01` → `REQ-SB-26-US-01-T02` →
`REQ-SB-27-US-01-T02` → `REQ-SB-26-US-01-T03` → `REQ-SB-27-US-01-T03` →
`REQ-SB-26-US-01-T04` → `REQ-SB-27-US-01-T04`). `REQ-SB-26-US-01`'s all 4
locked ACs and `REQ-SB-27-US-01`'s all 5 locked ACs verified live against
the real backend (port `8002` — ports `8000`/`8001` both live-occupied by
unrelated processes on this host, same established `SPRINT-014` pattern,
self-managed via explicit kill-and-restart on real PIDs, never by image
name), the real vault, and the real Compass Provider; full evidence in
each task's own Implementation Log. One real, live-discovered technical
correction was needed, in `REQ-SB-26-US-01-T03` (`graph.py`) — the real
current file had already grown a tool-execution loop
(`REQ-SB-25-US-01-T08`'s own live correction) beyond what this task's own
literal code sample assumed; corrected by composing the two new memory
nodes around the real current graph rather than overwriting it, and by
fixing `_extract_memory`'s own completion-context construction to avoid
duplicating the model's final reply message. No locked AC was weakened,
omitted, or touched a file outside the correcting task's own declared
scope; re-verified live afterward. Both stories and this sprint advance
to `status: Done`. `gate: flagged` (not `clear`) so a human can
spot-check this one correction and skim the retrospective — a
manual-verification-mode coder pass finding a real integration gap live,
exactly as intended, not a sign anything is broken or left undone.
