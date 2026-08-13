---
id: SPRINT-014
title: Real, Provider-backed conversational replies for embedded agent chat (LangGraph + shared MCP server foundation)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "All 5 flagged technical corrections spot-checked and accepted 2026-08-12 (see each task's own updated gate_reason) — no longer a factor. Retrospective drafted below, awaiting human skim/harvest into Learnings.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
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

# SPRINT-014 — Real, Provider-backed conversational replies for embedded agent chat (LangGraph + shared MCP server foundation)

## Sprint Goal

Give an agent's embedded chat a real, Provider-backed conversational reply
(via a new `langgraph`-based `agent_orchestration/` package and a shared
`FastMCP` server) for any message that isn't a recognized trigger phrase,
while leaving the existing keyword-match action fast path untouched — and
in doing so, land the shared orchestration/MCP scaffolding `REQ-SB-26`
(Agent Memory) and `REQ-SB-27` (Skills Repository) both build on next.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `REQ-SB-25-US-01` is the only
  story in this batch with no unresolved cross-story `depends_on` edge
  pointing *into* another not-yet-built story in this batch; its 8 tasks
  form one acyclic dependency graph (`T01 → {T02, T03}`; `T04` independent;
  `T05` depends on `{T01, T04}`; `T06` depends on `{T01, T05}`; `T07`
  depends on `{T02, T03, T06}`; `T08` depends on `{T07}`), delivering one
  coherent, independently valuable capability (real conversational replies,
  fast path preserved) with a superseding ADR (`ADR-015`) already
  `Accepted` and unchanged since. Not splittable across sprints without
  cutting through the middle of this single dependency graph, which would
  contradict hard rule 7.
- **Why NOT combined with `REQ-SB-26-US-01`/`REQ-SB-27-US-01` in one
  sprint:** all three stories are `phase: P1` and extend the same
  `ADR-015` LangGraph/shared-MCP-server surface, so a single combined
  sprint was genuinely considered. Rejected on sizing grounds: combined,
  the three stories total 16 tasks (8 + 4 + 4) — double this session's
  established single-sprint ceiling (`SPRINT-010`'s 8 tasks is the largest
  single-story sprint to date; a comparably large combination was
  explicitly rejected for `SPRINT-009`/`SPRINT-010` on the same grounds).
  Separately, `REQ-SB-26-US-01-T02`/`T03`/`T04` carry real cross-story
  `depends_on` edges onto `REQ-SB-25-US-01-T02`/`T07`/`T08`, and
  `REQ-SB-27-US-01-T02` carries one onto `REQ-SB-25-US-01-T05` — both
  sibling stories genuinely cannot make meaningful progress until this
  story's own near-terminal tasks (`T02`/`T05`/`T07`/`T08`) exist, a real
  sprint boundary, not an invented one. `REQ-SB-26-US-01` and
  `REQ-SB-27-US-01` are grouped together instead, in `SPRINT-015`, with
  `depends_on_sprints: [SPRINT-014]` — see that sprint's own Grouping
  Rationale. Not a genuinely ambiguous partition — not flagged.
- **Sizing estimate:** ~8 tasks, L — matches `SPRINT-010`'s own 8-task L
  precedent (the largest single-story sprint to date), consistent here
  too: net-new package (`langgraph`/`langchain-openai`/`mcp`/
  `langchain-mcp-adapters`), a new `agent_orchestration/` package
  (`state.py`, `model_factory.py`, `mcp_client.py`, `graph.py`), a new
  shared MCP server (`mcp_server.py`), and one integration task
  (`agents_router.py::chat`) — genuinely new-from-scratch scaffolding, not
  a diff on already-landed code, matching `SPRINT-010`'s own comparable
  from-scratch shape.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-014 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-25-US-01](../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md) | Real, Provider-backed conversational replies for embedded agent chat, with the keyword-match action fast-path preserved | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` confirm both hard blockers are already
  satisfied: `REQ-SB-13-US-01` (embedded chat surface, `Done`) and
  `REQ-SB-19-US-01` (per-agent Provider selection, `Done`).
- `ADR-015` (LangGraph + shared MCP server, `Accepted` 2026-08-11) is the
  settled architectural home for this story's full scope — already
  confirmed sufficient by the architect's own `/plan-tasks` pass
  (2026-08-12); no open ADR review blocks this sprint.
- `T01`'s own real `pip install` verification carries an honestly-flagged
  Windows `cp314` wheel-availability risk for the new packages
  (`langgraph`/`langchain-openai`/`mcp`/`langchain-mcp-adapters`) — not
  assumed clean; the coder confirms live at build time, per the task's own
  Notes. Not a sprint-blocking dependency, flagged here for the coder's
  awareness going into `/implement-sprint`.
- No new external-integration surface beyond what `REQ-SB-19-US-01`
  already established (Compass is the only Provider with a real client).

---

## Out of Scope

- **`REQ-SB-26`'s persistent, cross-conversation agent memory** — a
  separate, dependent story (`SPRINT-015`), not built here; this sprint's
  own multi-turn continuity is bounded to the current conversation only.
- **`REQ-SB-27`'s skill registration/invocation** — a separate story
  (`SPRINT-015`) that depends on this sprint's `mcp_server.py` existing,
  not built here.
- **`REQ-SB-20`'s Hub-to-Hub routing mechanism** — a structurally separate,
  not-yet-built concern; unaffected by this sprint.
- **`REQ-SB-23`'s own conversational intake-agent flow** — a separate,
  dependent story; not built here.
- **Building real LLM clients for non-Compass Providers** — unchanged from
  `REQ-SB-19-US-01`'s own Non-Goal.
- **Function-calling / the real LLM deciding to trigger an action** —
  action-triggering stays exclusively the existing keyword-match fast path.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (N/A — no architectural fact changed this pass; `ADR-015` already covered this story in full, per the architect's own 2026-08-12 pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (N/A — no new/changed ADR this pass)
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

- **Estimated:** `~8 tasks, L` — **Actual:** 8 tasks, L, all `Done`, but with five real, live-discovered technical corrections layered across `T05`/`T06`/`T07`/`T08` beyond their own literal code samples (see `## Notes`/`REVIEW-QUEUE.md` for the full list). **Takeaway:** the *task count* estimate held exactly, but "L" undersold the actual verification effort — this was the first story in the project to compose a brand-new framework (LangGraph), a brand-new protocol server (MCP/`FastMCP`), and a brand-new third-party model-client library (`langchain_openai.ChatOpenAI`) all in one sprint, with zero prior live-verification precedent for any of the three. Future sprints introducing a genuinely new framework/protocol/library for the first time should budget real integration-debugging time as its own line item, not assume "the code sample compiles" implies "the code sample works end-to-end."

### What worked

- **Manual, live, real-service verification caught every one of the five corrections** — none of the five (MCP mount double-nesting, MCP mount lifespan composition, `ChatOpenAI` `base_url` suffix mismatch, the unexecuted-tool-call empty reply, the per-turn round-count history-conflation bug) would have been caught by a unit test against mocked dependencies; each is a real integration behavior of a real third-party library/service that only manifests against the genuine `mcp` SDK / real OpenAI-SDK-shaped HTTP semantics / real Compass model behavior. This is exactly the case for this project's own standing "no test-stack ADR yet, verify live" discipline (`Implementation/Pipeline.md`'s Coder Verification Mode) paying off as intended.
- **Self-managing the backend process directly (not relying on `--reload`) once file-watching proved unreliable in this sandboxed environment** — switching to explicit kill-and-restart after every code change, with output redirected to a scratch log file the coder could `tail`, gave deterministic, inspectable control over exactly which code version was live for each verification step. Discovering and adapting to this early (`T05`) avoided a much larger class of "did my last edit actually take effect?" confusion for the remaining tasks.
- **Reusing the existing honest-unavailability funnel-gate pattern one layer over** (`model_factory.resolve_agent_model` mirroring `_invoke_action`'s exact phrasing/short-circuit shape) meant `AC-04` passed on the first real attempt with zero corrections needed — a genuinely reusable pattern paying off exactly as designed.
- **Recovering mid-task from an interrupted session cleanly** — re-reading each task file and the actual on-disk code fresh (not trusting prior-session memory) before resuming let this session pick up exactly where the interruption left off (T05/T06 code present but unverified) without re-doing already-correct work or silently skipping verification.

### What didn't work

- **The task files' own literal code samples for a brand-new library/framework integration (LangGraph, `FastMCP`, `ChatOpenAI`) were each individually plausible but did not compose correctly end-to-end** — every one of the five corrections was a real, load-bearing gap between "this line of code is syntactically what the library's docs suggest" and "this actually works against the real service once every other piece is wired together." Root cause: the story's own architecture pass (`ADR-015`) was explicit that it had "no live network/package-index access" and could not verify these integration details directly — entirely reasonable at that stage, but it means the decomposer's task-level code samples inherited that same unverified-until-real-build status, and this sprint is where that bill came due. Not a process failure — this is exactly what live coder verification exists to catch — but worth naming plainly rather than filing five separate "found a bug" notes with no unifying root cause.
- **Environment port/process visibility friction cost real time** — port `8000` (known `agentic-map` conflict) and port `8001` (this project's own usual convention) were both occupied, and the `8001` process could not be identified or killed by any available process-management tool from within this coder session's own sandbox (`Get-Process`/`Get-CimInstance`/`tasklist` all reported "not found" for a PID `netstat` itself attributed the port to). This is either a real, recurring sandbox-boundary limitation worth a permanent adaptation, or a one-off anomaly — genuinely unclear from inside this session, which is exactly why it's flagged in `REVIEW-QUEUE.md` rather than silently worked around a second time.
- **The task-authored round-limit guard for the tool-execution loop wasn't tested against a real, already-populated conversation history before being called "done"** — the bug (counting every `AIMessage` in the full replayed history, not just the current turn) only surfaces once an agent already has real prior chat history, which the very first smoke check (an agent with no prior history) could not have caught. A second, more adversarial self-check ("what if this agent already has history?") before moving on would have caught it one step earlier.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Self-manage the dev server process directly (explicit kill/restart, redirected logs) instead of trusting `--reload`, once file-watching is found unreliable in a given environment** — deterministic, inspectable control over exactly which code version is live beats an automatic-but-unverified reload, especially mid-debugging a real integration issue.
- **When a story composes a genuinely new framework/protocol/library for the first time (no prior live-verification precedent in this codebase), budget real end-to-end integration-debugging time explicitly, separate from "coding" time** — a task's own literal code sample for a new library is a best-effort starting point, not a guarantee; the task-count/size estimate can still be accurate while still needing meaningfully more live-debugging effort than a same-sized story extending an already-proven pattern.
- **A per-turn/per-request round or step guard computed over a full replayed-history message list must be scoped to the current turn only** (e.g. a backward walk stopping at the turn's own boundary marker), never a naive count over the entire list — the same shape of bug (a growing, unrelated denominator silently degrading a per-call guard) could recur anywhere else this codebase replays accumulating history into a bounded operation.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Treating a task's own literal `## Files to Modify` code sample for a brand-new third-party library/framework as verified-correct rather than as a best-effort starting point** — for genuinely new integrations with no prior live-verification precedent in this codebase, always run the real end-to-end smoke check before trusting the sample compiles-and-works; budget for at least one real correction.
- **Verifying a stateful/accumulating-context code path (e.g. a per-turn guard, a history-replay loop) only against a fresh/empty starting state** — the bug this sprint found in the round-limit guard was invisible against an agent with no prior history and only surfaced on a second real turn against an agent that already had real accumulated history from earlier verification steps in the *same* sprint. Prefer testing at least one such path against a non-trivial pre-existing state before calling it done.

### Open follow-ups

- **Port 8001 was live-occupied by an unidentifiable/unmanageable process during this sprint's own verification** — filed in `REVIEW-QUEUE.md` (SPRINT-014 / REQ-SB-25-US-01 entry) for a human check on whether this is expected sandbox behavior or worth its own investigation.
- **`provider_registry.has_real_client`'s hardcoded-`"compass"`-only gate means no newly created Provider can ever be used to test a genuine real-Provider-call-failure path** — not a defect in this story's own scope (the gate is `REQ-SB-19-US-01`'s already-`Done`, unmodified design), but worth a note for any future story that needs to test multiple real-client Providers' own failure modes independently — today's design structurally cannot support that without repointing the one real `"compass"` entry each time.
- **`SPRINT-015`** (`REQ-SB-26-US-01`, Agent Memory; `REQ-SB-27-US-01`, Skills Repository) is now unblocked (`depends_on_sprints: [SPRINT-014]` satisfied) — both extend this same compiled graph (`agent_orchestration/graph.py`) with additional nodes, per `ADR-015`'s own extensibility design; the graph now has two nodes (`call_model`, `execute_tools`) and one conditional edge instead of the single node `ADR-015`'s own Context assumed, worth a quick read of `graph.py`'s current shape before extending it.

---

## Notes

**gate: clear 2026-08-12** — no MUST-FLAG trigger fired for this grouping
decision: (1) no material assumption — the split from `REQ-SB-26`/
`REQ-SB-27` is grounded directly in the decomposer's own real cross-story
`depends_on` edges (`REQ-SB-26-US-01-T02`/`T03`/`T04` → `REQ-SB-25-US-01-
T02`/`T07`/`T08`; `REQ-SB-27-US-01-T02` → `REQ-SB-25-US-01-T05`), not
guessed; (2) `REQ-SB-25` is not `<!-- Draft -->` in the PRD; (3) N/A
(product-owner does not touch ADRs); (4) no `ESCALATIONS.md` entry
written; (5) not oversized (8 tasks matches the established `SPRINT-010`
L-precedent exactly), not `Blocked`, and no cross-sprint dependency was
introduced *by this sprint* (this sprint itself has `depends_on_sprints:
[]` — it is the upstream sprint the other two stories depend on, not the
downstream one); (6) N/A (coder trigger); (7) no contradictory inputs;
(8) not a genuinely ambiguous partition — the 8-task combined-vs-split
question has one clearly-better answer given the established sizing
ceiling and the real dependency-graph shape, not multiple equally-valid
options. Advances `Draft → Ready`.

**Sprint assembled (2026-08-12):** 1 story, 8 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`. `SPRINT-015`
(`REQ-SB-26-US-01` + `REQ-SB-27-US-01`) depends on this sprint reaching
`Done` before it can start (`depends_on_sprints: [SPRINT-014]`), per hard
rule 9.

**Coder pass (`/implement-sprint`, 2026-08-12):** all 8 tasks built and
`Done`, in dependency order (`T01`→`T02`/`T03`→`T04`→`T05`→`T06`→`T07`→
`T08`, with `T04` built in parallel per its own no-dependency status).
`REQ-SB-25-US-01`'s all 5 locked ACs verified live against the real
backend, real Compass Provider, and real vault — full evidence in
`T08`'s own Implementation Log. Story and sprint both advance to `status:
Done`. Five real, live-discovered technical corrections were needed
across `T05`/`T06`/`T07`/`T08` beyond their own literal code samples/
Tests instructions — none weakened a locked AC, none touched a file
outside the correcting task's own declared scope, and every one was
re-verified live afterward; full detail in each task's own Implementation
Log, summarized in `MEMORY.md`'s Constraints and in this sprint's own
Retrospective below. `gate: flagged` (not `clear`) so a human can
spot-check these corrections — this is a manual-verification-mode coder
pass finding real integration gaps live, exactly as intended, not a sign
anything is broken or left undone. `SPRINT-015` is now unblocked
(`depends_on_sprints: [SPRINT-014]` satisfied).
