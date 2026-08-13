---
id: SPRINT-010
title: Embedded agent detail panel — settings, actions, chat, and communication history
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted — human to skim and harvest Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-008]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"             # YYYY-MM-DD when status → Done
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

# SPRINT-010 — Embedded agent detail panel — settings, actions, chat, and communication history

## Sprint Goal

Build the Agents Map's agent detail side panel end to end — settings,
available actions, an embedded chat backed by a real backend (with
natural-language action-triggering per `ADR-011`), and a unified
chronological communication-history timeline — so a user can understand,
configure, and talk to any agent without leaving Second Brain.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-13-US-01` is the only story
  in this batch whose tasks it covers; its 8 tasks form one acyclic
  dependency graph (`T01→T03→T05`, `T02→T03`, `T02→T05`, `T04→T05`,
  `T01→T04`, `T05→T06→T07→T08`) delivering one coherent, independently
  valuable capability — the full detail panel (settings/actions/chat/
  history) — per the story's own reasoning that it is a distinct PRD
  requirement with its own acceptance text, not splittable across sprints
  without cutting through the middle of a single dependency graph, which
  would contradict hard rule 7.
- **Why NOT combined with `REQ-SB-12-US-02`:** both are `Ready`, ungrouped,
  P1, frontend+backend stories that depend only on SPRINT-008, and no
  `depends_on` edge exists between them (different files: `agent_registry.
  py`/`agent_chat.py`/`agents_router.py`/`AgentDetailPanel.tsx` vs.
  `my_day.py`/`my_day_router.py`/`MyDayPage.tsx` — no shared module, no
  cross-story task edge), so a combined sprint is graph-legal. It was
  rejected purely on **size**: 8 + 7 = 15 tasks, more than double this
  session's established ceiling (SPRINT-007's 6 tasks is the largest
  multi-story sprint to date; SPRINT-006's 5 tasks is the largest
  single-story sprint to date) and clearly outside "fits in a single
  working context." This story is also the materially higher-risk of the
  two — it introduced a new `ADR-011` (action-triggering mechanism, agent
  registry source, history persistence) — the same "isolate the
  higher-risk/first-of-kind story in its own sprint" call `SPRINT-006` made
  against `SPRINT-007`'s two lower-risk, direct-extension stories. Not a
  genuinely ambiguous partition (rejected on sizing + risk-isolation
  grounds, not graph ambiguity) — recorded as a reasoned cohesion decision,
  not flagged.
- **Sizing estimate:** ~8 tasks, L (large) — two steps up from
  `Implementation/Learnings.md`'s calibrated ~4-6 task precedent
  (SPRINT-001/002/004 at 4/S, SPRINT-006 at 5/M, SPRINT-007 at 6/M
  combined), matching this story's own larger backend surface (5 backend
  tasks — history primitives, registry, chat matching, a capture-hook, and
  the router — versus 2-3 in prior precedents) plus 3 frontend tasks (panel
  shell, chat thread, history). No prior sprint this session has built a
  natural-language action-triggering surface or a unified chat+run-event
  history timeline, so this is treated as a fresh calibration point, not
  assumed identical to smaller prior precedents.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-010 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-13-US-01](../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md) | Embedded agent detail panel — settings, actions, chat, and communication history from the Agents Map | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-008` — `REQ-SB-13-US-01-T06` carries a
  task-level `depends_on: [REQ-SB-12-US-01-T02]` (it edits `AgentNode.tsx`
  built there), so this sprint cannot start until SPRINT-008 is `Done`.
  `/implement-sprint` will refuse this sprint otherwise, per hard rule 9.
- **`ADR-011`** (action-triggering mechanism, agent registry source, history
  persistence) was reviewed and approved by the operator 2026-08-11 — not
  an open blocker. The story's own `gate: flagged`
  (`gate_reason: trigger-3, ADR-011 created`) does not block this stage —
  resetting the story's `gate:` value is not this role's job, per the same
  precedent `SPRINT-006`/`SPRINT-007`/`SPRINT-008` already established for
  operator-approved ADRs.
- `T05`/`T07`'s Tests explicitly flag that triggering `email-capture`'s
  `run_capture_now` (via the direct endpoint or a matching chat message)
  fires a **real** Outlook/Compass/vault-write capture run — not a
  sprint-blocking dependency, noted here for the coder's awareness per the
  story's own Notes.

---

## Out of Scope

- **The Agents Map itself and its shell/navigation** — `REQ-SB-12-US-01`/
  `SPRINT-008`, a dependency, not rebuilt here.
- **The My Day dashboard** — `REQ-SB-12-US-02`/`SPRINT-009`, a separate,
  independent sprint.
- **Whether the chat can read/write the vault per REQ-SB-04's own carve-out**
  — a separate, not-yet-resolved question, per the story's own Non-Goals.
- **Persisting communication history in a real backend data store beyond the
  new flat-JSON-file convention** — per `ADR-011`, not decided differently
  here.
- **The exact final set of actions the chat can trigger** beyond
  `email-capture`'s `run_capture_now` — future, additive work per
  `ADR-011`'s own Consequences.
- **Hermes-channel chat (REQ-SB-03)** — this sprint is the in-app embedded
  surface only.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change needed; the architect's `/plan-tasks` step 1 pass already recorded the "Agent detail panel" API/module shape this sprint built against
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-011` confirmed `Accepted`
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

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L, landed exactly at
  estimate, zero rework, zero blocked tasks — **Takeaway:** the sizing
  note's own calibration ("two steps up from the ~4-6 task precedent,
  matching this story's larger backend+action-triggering+history surface")
  held up. The 5-backend/3-frontend split (history primitives → registry →
  chat-matching → completion hook → router, then panel shell → chat →
  history) is a reusable template for a future "new capability surface +
  its own panel" sprint, distinct from both the pure-backend
  primitives→orchestration→wire-up shape and the pure-frontend
  scaffold→visualization→placeholder shape earlier sprints established.

### What worked

- **Keyword-substring matching (ADR-011) was exactly proportionate to
  what this pass needed.** No NLU/LLM call was required anywhere — a
  small per-agent `trigger_phrases` list plus first-match-wins substring
  matching correctly handled every real message tried, including a
  message where a longer typed phrase ("please run capture now")
  contained a shorter declared phrase ("run capture now") as a substring.
  Confirms ADR-011's own reasoning that building real NLU for a
  one-real-action universe would have been speculative machinery.
- **Reusing SPRINT-008's CDP-based verification pattern for a much more
  interactive flow (multi-step chat send + real backend action + async
  history refresh) scaled cleanly.** The driver script's `eval` steps
  could express an async polling loop directly in the injected JS (`await`
  inside a `Runtime.evaluate` expression) to wait out a real ~80-second
  Outlook/Compass/vault-write run without any new tooling — the same
  zero-dependency approach handles both simple DOM assertions and
  long-running real-side-effect waits.
- **Deliberately reserving one agent (`meeting-capture`) as an
  untouched fixture for the empty-state AC, decided up front once the
  concurrency risk was spotted**, avoided a self-inflicted test collision
  — a non-AC smoke check in one task (`T05`) would otherwise have
  populated the exact agent a later locked AC (`T08`'s `AC-05`) needed to
  observe as empty. Substituting a different, equally-valid no-handler
  agent (`todo-capture`) for the earlier smoke check cost nothing and
  avoided the collision entirely, rather than working around it after the
  fact.
- **Consolidating a "verify this real-side-effect endpoint" step across
  two tasks (T05's own direct-HTTP check, T07's UI-driven AC-08 check)
  into a single live invocation**, rather than triggering the same real
  Outlook/Compass/vault-write capture run twice in immediate succession,
  matched both tasks' own "be deliberate" instruction while still giving
  each task genuine, real, first-hand verification evidence (the raw HTTP
  shape from the shared history endpoint, the actual UI interaction from
  the browser).

### What didn't work

- **The task files' assumed "Before" state for shared files
  (`email_classification.py`, `main.py`) had already drifted from reality
  by the time this sprint ran**, because SPRINT-006/007/009 were
  genuinely running concurrently against the same working tree (not a
  hypothetical risk — confirmed live: `run_capture_and_record_completion`
  already called `meeting_classification.classify_recent_meetings()`
  before this sprint touched it, and `main.py` already had
  `my_day_router` plus a `CORSMiddleware` block neither T05 nor any
  earlier artefact anticipated). Every edit in this sprint stayed
  additive and no real conflict occurred, but this was closer to genuine
  concurrent-write risk than any prior sprint this session — re-reading
  every shared file immediately before each edit (as instructed) is what
  kept it safe, not luck.
- **Every dev-server port from 8000 through 8002 was already occupied**
  by the known `agentic-map` process plus two other concurrent Second
  Brain verification sessions — MEMORY.md's existing single-alternate-port
  guidance (8000 → 8001) wasn't enough this pass; had to scan a range and
  land on 8003. The frontend's default port (5173) was similarly already
  taken, requiring a second, less-anticipated fix (extending `main.py`'s
  CORS `allow_origins` to cover Vite's auto-incremented 5174) before any
  browser-based verification could reach the backend at all.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Scan a small port range, don't assume one alternate is enough** —
  when multiple concurrent sessions are live against the same project,
  check several candidate ports (`Get-NetTCPConnection` over a small
  range) rather than hardcoding a single fallback (e.g. 8000 → 8001);
  this pass needed 8003 before finding a free port, and the frontend
  needed the same treatment (Vite auto-increments, but the CORS allow-list
  it lands on needs to follow it).
- **Reserve one untouched fixture agent/entity up front when a locked AC
  needs to observe "genuinely empty" state, and route every non-AC smoke
  check for that same category away from it** — decided before writing
  any smoke-check code this pass, not discovered as a collision after the
  fact. Generalizes beyond agents: any locked AC asserting "nothing here
  yet" needs its fixture identified and protected at build-planning time,
  not verification time.
- **Consolidate repeated real-side-effect triggers across sibling tasks
  into one live invocation when the same endpoint/action is exercised by
  more than one task's own verification script** — matches the "real
  side effect, be deliberate" instruction better than mechanically running
  every task's own literal script in isolation, while still producing
  first-hand evidence for each task's own AC/contract.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a task file's own "Before" narrative for a shared file
  without re-reading it fresh** — this sprint's own task files (authored
  before SPRINT-006/007/009 ran) described `email_classification.py`/
  `main.py` states that had already changed by build time. No defect
  resulted only because every edit in this sprint was re-verified against
  the real file immediately before writing — treat every shared-file
  "Before" description in a task file as provisional, not authoritative,
  once multiple sprints can be in flight concurrently.

### Open follow-ups

- **CORS allowed-origins policy** — already flagged by a concurrent
  session's own `REVIEW-QUEUE.md` entry (`REQ-SB-12-US-02-T03`), which
  this sprint's own port-5174 extension is referenced from; worth a
  proper ADR (env-var-driven origins, or a dev-only wildcard) before a
  fourth frontend-calling-backend story repeats the same ad hoc
  hardcoded-port pattern.
- **The double `run_event` history entry for `email-capture`'s
  `run_capture_now`** (one from `T04`'s hook inside the invoked handler
  itself, one from the router's own generic post-`_invoke_action` append)
  is a real, observed consequence of this pass's exact architecture —
  harmless against every locked AC (Scenario 3b only requires entries to
  appear together, not exactly-once), but worth a note for whoever wires
  the next real action handler (REQ-SB-08/09/03) that already
  self-reports via its own completion hook: expect the same doubling
  unless the router's own generic `run_event` append is made conditional
  on the handler not already having appended one itself.
- **The exact final action set beyond `email-capture`'s
  `run_capture_now`** — per `ADR-011`'s own Consequences, this is expected
  additive work once REQ-SB-08/09/03 ship real, callable pipelines; not a
  defect of this pass.

---

## Notes

gate: clear 2026-08-11 — no new MUST-FLAG trigger fired **at this
`/plan-sprints` stage**. `REQ-SB-13-US-01`'s own dependency graph
(`T01→T03→T05`, `T02→T03`, `T02→T05`, `T04→T05`, `T01→T04`,
`T05→T06→T07→T08`) is honoured intact, not split across sprints. Not
oversized on its own (8 tasks, two steps above this session's established
~4-6 task range, matching this story's larger backend+frontend surface and
its status as the first agent-chat/action-triggering build). Not blocked —
all 8 tasks and the story itself are `status: Ready`; the one real upstream
need (`REQ-SB-12-US-01-T02`) is recorded as a real
`depends_on_sprints: [SPRINT-008]` edge, not contradicted. Single phase
(P1) throughout. The story's own `gate: flagged` (trigger-3, `ADR-011`
creation, set at the architect's `/plan-tasks` step 1 pass) does **not**
block this stage — the operator reviewed and approved `ADR-011` 2026-08-11,
and resetting a story's own `gate:` value is not this role's job, per the
identical precedent already established for `REQ-SB-16-US-01`/`SPRINT-007`
and `REQ-SB-12-US-01`/`SPRINT-008`. The decision to split
`REQ-SB-13-US-01` and `REQ-SB-12-US-02` into two sprints rather than one
combined sprint is a reasoned sizing-and-risk-isolation call (15 combined
tasks vs. this session's ~4-6 task precedent, plus this story's materially
higher architectural-novelty profile), not a genuinely ambiguous partition
— recorded above, not flagged. Advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 8 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint` once `SPRINT-008` is `Done`.

---

**Coder pass (`/implement-sprint`), 2026-08-11.** `REQ-SB-13-US-01` built
end-to-end: `T01` (agent-history vault_writer primitives) → `{T02` (agent
registry), `T03` (chat matching)`} → T04` (capture-completion history
hook) → `T05` (agents router) → `T06` (panel shell) → `T07` (chat thread)
→ `T08` (communication history + agent switching), all 8 tasks `Done`,
all 8 locked ACs verified live — backend against a real `uvicorn` server
(port 8003; ports 8000-8002 were all already occupied by the known
`agentic-map` process and concurrent Second Brain sessions), frontend via
headless-Chrome CDP browser automation against a real `npm run dev`
server (port 5174; 5173 already occupied). Both trust-surface-defining
ACs — `Scenario 7`/`AC-08` (chat-triggered real action) and
`Scenario 3b`/`AC-04` (unified chat+run-event history) — confirmed with a
single real Outlook/Compass/vault-write capture run triggered via the
actual chat UI, not a direct endpoint call, matching this story's own
"real, live system" framing. `npm run build` passed clean. Zero blocked
tasks, zero `ESCALATIONS.md` entries; two scope-internal judgment calls
(agent substitution to protect an empty-state fixture; consolidating a
repeated real-side-effect verification step across two tasks) logged in
the relevant tasks' own Implementation Logs, plus one small additive CORS
extension in the shared `main.py` (already covered by a concurrent
session's own `REVIEW-QUEUE.md` entry, not duplicated here). Sprint
`status: Ready → Done`, `completed: 2026-08-11`. Story `status: Ready →
Done`; its `gate: flagged` (from the architect's ADR-011-creation flag)
reset to `clear` — the ADR-011 review it recorded is resolved (operator
confirmation already noted in this story's own Notes), same precedent as
`REQ-SB-12-US-01`/`SPRINT-008`. `BACKLOG.md` updated (`REQ-SB-13`/
`SPRINT-010` rows → `Done`). This sprint's own `gate` set to `flagged`
(`gate_reason`: retro drafted, awaiting human `Learnings.md` harvest) per
this role's own mandatory sprint-wrap behaviour — a `REVIEW-QUEUE.md`
entry has been added.
