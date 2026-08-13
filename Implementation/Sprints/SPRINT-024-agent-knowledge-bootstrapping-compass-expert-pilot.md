---
id: SPRINT-024
title: Agent Knowledge Bootstrapping — end-to-end delegated-research chain, Compass Expert pilot
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint wrap — human should skim the retro below and propagate patterns to Implementation/Learnings.md. Also carries two scope-internal reconciliations logged in T02/T03's own Implementation Logs, plus the still-Open ESC-018 (T04 remains outside every sprint)."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-020, SPRINT-021, SPRINT-022, SPRINT-023]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S (buildable — T04 excluded, see Notes)"      # effort estimate; checked vs actual in retro
created: 2026-08-12
started: "2026-08-12"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"             # YYYY-MM-DD when status → Done
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

# SPRINT-024 — Agent Knowledge Bootstrapping (Compass Expert Pilot)

## Sprint Goal

Build and verify `REQ-SB-36-US-02`'s buildable scope end to end: a new
pilot `"compass-expert"` Expert agent with a `"build_knowledge"` action,
and `knowledge_bootstrap.py::bootstrap_agent_knowledge` — deterministically
composing Hub routing (`SPRINT-020`), the Autonomous-mode check
(`SPRINT-021`), the web-research skill (`SPRINT-022`), and the Vault Filing
Expert's Tier-1/Tier-2 placement (`SPRINT-023`) into one real, end-to-end,
approval-free (except the one Tier-2 exception) delegation chain, dispatched
through the existing chat/direct-action funnel.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — the 3 buildable tasks
  (`T01`–`T03`) belong to `REQ-SB-36-US-02`, the only story assigned here.
  This is the final, composing layer of the 5-sprint "Compass Expert"
  chain: it builds no new mechanism of its own, only the orchestration
  that calls the four prior sprints' own real functions
  (`route_cross_section_request`, `working_mode_registry`, `invoke_skill`,
  `determine_placement_and_file`) deterministically, per `ADR-023`.
- **Why sequenced after all four prior sprints:** confirmed by direct
  reading of this story's own task table — `T01: [REQ-SB-21-US-01-T09]`;
  `T02: [T01, REQ-SB-20-US-01-T05, REQ-SB-21-US-01-T02,
  REQ-SB-36-US-01-T05, REQ-SB-35-US-01-T02, REQ-SB-35-US-01-T03]`;
  `T03: [T01, T02]`. Every prior sprint's own composed function is a real,
  named prerequisite — `depends_on_sprints: [SPRINT-020, SPRINT-021,
  SPRINT-022, SPRINT-023]` records all four, none fabricated or omitted.
- **`REQ-SB-36-US-02-T04` is deliberately EXCLUDED from this sprint's own
  scope — not scheduled as buildable work.** The decomposer's own pass
  individually held `T04` at `status: Draft`, `depends_on: []`, with an
  explicit "⚠️ BLOCKED — do not start" note (`ESC-018`, `Open`): `T04`
  covers `AC-03` ("the newly-expert agent can draw on the filed content
  afterward"), which composes entirely with `REQ-SB-29-US-01`'s own
  vault-scope-assignment/retrieval mechanism — and `REQ-SB-29-US-01` has
  not been decomposed at all (zero task files exist), so there is no real
  task id anywhere to sequence `T04` against. This is a confirmed,
  operator-acceptable judgement call, not this product-owner pass's own
  decision to make or unmake — per this project's own established
  precedent (`ESC-011`), a task with no real prerequisite to wire a
  `depends_on` edge onto stays individually blocked rather than being
  given a fabricated dependency or silently scheduled anyway. **This
  sprint schedules only `T01`–`T03`.** `T04` remains outside every sprint
  until `REQ-SB-29-US-01` is itself decomposed and a real task id exists to
  sequence it against — at that point a future `/plan-sprints` pass gives
  it its own sprint (most likely depending on this one plus whichever
  sprint eventually carries `REQ-SB-29-US-01`'s own tasks), not this one.
- **Why NOT held back entirely pending `T04` (the `ESC-011`-style
  "hold the whole story back" alternative):** the decomposer's own pass
  already considered and explicitly rejected full-story-lockstep here
  (see the story's own Notes, "a genuine judgement call, flagged rather
  than silently resolved either way") — advancing the story to `Ready`
  while holding only `T04` individually `Draft`/blocked, since `T01`–`T03`
  have zero blocking issue of their own and every one of their real
  cross-story prerequisites already has a real, `Ready` (soon `Done`) task
  id. This product-owner pass honours that already-made, human-flagged
  judgement call rather than re-litigating it — scheduling the three
  genuinely buildable tasks is the correct, non-speculative action; holding
  the entire sprint back for one requirement-composition task with no code
  of its own to write yet would leave real, valuable, unblocked work
  unscheduled for no dependency-graph reason.
- **Sizing estimate:** ~3 tasks, S (buildable scope only) — `T01` (pilot
  agent + action definition, data only) → `T02` (the orchestration module
  itself, the real cost center — composes 4 prior sprints' own real
  functions, covers `AC-02`/`AC-04`/`AC-05`/`AC-06`) → `T03` (the real
  chat/direct-trigger dispatch, `AC-01`). `T04` excluded, see above.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-024 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-36-US-02](../UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md) | Agent knowledge bootstrapping via delegated research — Compass Expert pilot | P1 | In Progress (T01–T03 Done; T04 blocked, ESC-018) |

**Tasks in scope** (dependency order, buildable only): [[REQ-SB-36-US-02-T01]]
(new `"compass-expert"` pilot agent + `"build_knowledge"` action,
`depends_on: [REQ-SB-21-US-01-T09]` — cross-sprint), [[REQ-SB-36-US-02-T02]]
(`knowledge_bootstrap.py` orchestration, `depends_on: [T01,
REQ-SB-20-US-01-T05, REQ-SB-21-US-01-T02, REQ-SB-36-US-01-T05,
REQ-SB-35-US-01-T02, REQ-SB-35-US-01-T03]` — cross-sprint),
[[REQ-SB-36-US-02-T03]] (`build_knowledge` action dispatch, `depends_on:
[T01, T02]`).

**Excluded from this sprint (not scheduled, not buildable):**
[[REQ-SB-36-US-02-T04]] — `status: Draft`, `depends_on: []`, individually
blocked pending `REQ-SB-29-US-01`'s own decomposition (`ESC-018`, `Open`).
See Grouping Rationale.

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-020` (Section Hub Intelligence — Hub
  routing), `SPRINT-021` (Agent Working Modes — Autonomous-mode check,
  `mutates` classification), `SPRINT-022` (Web Research Skill — the
  research invocation), `SPRINT-023` (Vault Filing Expert — Tier-1/Tier-2
  filing). All four must be `Done` before `/implement-sprint` may start
  this sprint.
- **Not a blocker for this sprint, but recorded for the human:**
  `REQ-SB-36-US-02-T04` stays outside every sprint until `REQ-SB-29-US-01`
  is decomposed (`ESC-018`, `Open` — see `REVIEW-QUEUE.md`). This sprint's
  own Definition of Done does not require `T04` or `AC-03` to be verified —
  the story's own `Done` status, once all locked ACs this sprint's tasks
  cover are verified, still leaves `AC-03` open pending that future task;
  this is the same shape `ESC-011`'s own precedent already established for
  an individually-blocked task inside an otherwise-`Ready`/buildable story.
- `ADR-023` (already `Accepted`, written at `/plan-tasks`) still carries its
  own open human-review flag on the story, alongside the still-`Open`
  `ESC-018` and the decomposer's own judgement-call confirmation request;
  none of these block `/implement-sprint` from running `T01`–`T03` once the
  four prerequisite sprints are `Done` — recorded here for visibility only.

---

## Out of Scope

- `REQ-SB-36-US-02-T04` — individually blocked, excluded from this sprint's
  own scope; see Grouping Rationale and Dependencies above.
- `REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) — not yet decomposed, not
  eligible for `/plan-sprints`; not built here.
- `REQ-SB-28-US-01` (File Upload for Agents) — the later, additive
  file-upload research path; explicitly out of scope for this story's own
  initial-bootstrap scenario.

---

## Definition of Done

- [x] `REQ-SB-36-US-02-T01`, `T02`, `T03` are all `Done` and their covered
      ACs (`AC-01`, `AC-02`, `AC-04`, `AC-05`, `AC-06`) verified
- [x] All story-level Definition-of-Done items satisfied for the buildable
      scope; `AC-03`/`T04` remain explicitly open, tracked via `ESC-018`,
      not silently marked complete
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change needed; `ADR-023`/architecture.md's own "Delegated knowledge-bootstrap orchestration" section already correctly described what was built, unmodified by this build pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none new this pass (`ADR-023` already `Accepted` at `/plan-tasks`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~3 tasks, S (buildable) — **Actual:** 3 tasks, S,
  matched exactly. `T02` (the orchestration module) was correctly
  identified up front as the real cost center — not in code volume (the
  module itself is ~110 lines), but in live-verification complexity: two
  independent honest-failure paths for `AC-05`, a real Tier-2-forcing
  content-engineering iteration (the vault's own `"Notes"` catch-all had
  materialized since `REQ-SB-35-US-01-T03`'s own precedent, requiring a
  reframed test), and a genuinely load-bearing `try/except` finding only
  surfaced by actually invoking the real, composed dependency chain.

### What worked

- **This was the culmination of a genuine 5-sprint chain
  (`SPRINT-020`→`024`), and every one of its composed real functions held
  up exactly as documented** — `route_cross_section_request`,
  `get_agent_working_mode`, `invoke_skill`, `determine_placement_and_file`
  all composed cleanly with zero surprises in their own contracts; the
  only real friction was at this sprint's own dispatch-layer seams
  (below), not in the four prior sprints' own work.
- **Real, end-to-end, live proof of the whole business use case**,
  achieved honestly despite the known credential gap: real Hub routing
  (both hops), a real Autonomous-mode check, a real (unmocked) attempted
  Anthropic web-search call that genuinely hit a real `401` and was
  correctly, honestly handled — and, via the established, disclosed
  in-process-monkeypatch-and-revert technique isolating ONLY the
  externally-credential-gated research step, a real Vault Filing Expert
  invocation (a real Compass LLM placement call) that genuinely wrote a
  real note to the real vault (Tier 1) and genuinely created a real
  pending-approval record for a genuinely new top-level area (Tier 2).
  Splitting verification this way (real for everything reachable; a
  clearly-disclosed, reverted substitution for the one piece genuinely
  blocked on an unprovisioned external credential) — the same shape
  `SPRINT-022` already established — continues to be the right call
  rather than either claiming a full pass or blocking the whole task on
  an environment gap outside this sprint's own control.
- **Reading the REAL current file before applying a task's own sample
  caught two genuinely load-bearing gaps**, not just cosmetic drift:
  `anthropic_client.web_search`'s own real exception-raising behavior
  (not returning a result dict) and `_execute_action`'s own real,
  narrow handler-calling convention (hardcoded to one existing action's
  shape). Both were invisible from the task files' own samples alone and
  only surfaced by tracing the real, current dependency code — this
  project's most consistently load-bearing habit, reconfirmed a further
  time.

### What didn't work

- **A locked task's own illustrative code sample assumed a shared
  dispatch function (`_execute_action`) was more generic than it
  actually was.** `_execute_action`'s real body is tightly coupled to
  `run_capture_now`'s own zero-arg/list-returning shape (`len(results)`
  inline); nothing in the task file itself flagged this as a risk beyond
  the general "read the real file" instruction. Consider having a future
  decomposer pass explicitly name a shared dispatch function's own real
  contract (arg shape, return shape) as a named risk when a new task adds
  a second entry to an existing single-entry dispatch table, rather than
  leaving it to the coder to discover by tracing the real call chain.

### Patterns to carry forward

- **When a locked task Constraint says "no step may fabricate a result"
  and a composed real dependency can raise rather than return, add the
  `try/except` — this is satisfying the AC's own honest intent, not
  scope creep** — confirmed genuinely necessary this pass (the real,
  unmocked Anthropic call really did raise, and really was caught
  correctly). Extends `graph.py::_call_model`'s own precedent to a
  second, non-graph call path.
- **When a task's own sample proposes reusing an existing shared
  dispatch function for a new, differently-shaped handler, verify the
  existing function's own real handler-calling convention before wiring
  the new entry in** — a shape mismatch here is silent at import time and
  only surfaces at first real invocation. Add a NEW sibling function
  alongside the existing one (rather than generalizing/branching inside
  it) whenever the existing function is also relied on synchronously by
  a caller outside the current task's own `## Files to Modify` — safer
  than touching a shared function another out-of-scope file imports
  directly.
- **A generic, non-action-specific flag on a shared response envelope
  (e.g. `"history_recorded"`) resolves a "the generic post-processing
  double-records a self-recording handler's own outcome" tension without
  special-casing by action/agent id** — reusable by any future handler
  with the same self-recording shape, not a one-off hack.
- **When an established Tier-2-forcing test-content technique from an
  earlier sprint stops working because the vault's own real taxonomy has
  since materialized the exact catch-all kind that content used to force
  a new area under, don't fight the model — reframe the content to
  genuinely warrant a dedicated area** (explicit, structured, recurring
  content type, not just "doesn't fit elsewhere"). The methodology-
  grounded model was behaving correctly against the real, current vault
  state; the test technique needed to catch up to reality, not the
  reverse.
- **Clean up fabricated/junk vault content and orphaned `.second-brain`
  state-file residue created purely for live verification (in-process
  `AGENTS` mutations, monkeypatched research content), while deliberately
  keeping the one real-information Tier-1 test note** — mirrors this
  project's own general "leave real, meaningful verification residue;
  remove fabricated placeholder content" judgement, applied explicitly
  to a case where a live monkeypatch's own synthetic content had no
  standalone informational value.

### Antipatterns to avoid

- None new beyond the ones already carried forward above — no
  environment/tooling surprise this pass beyond the already-known,
  already-disclosed missing `ANTHROPIC_API_KEY` credential.

### Open follow-ups

- `REQ-SB-36-US-02-T04`/`AC-03` remain `Draft`/blocked on
  `REQ-SB-29-US-01`'s own decomposition (`ESC-018`, still `Open`) — no
  change this pass; tracked in `REVIEW-QUEUE.md` as before.
- The real `ANTHROPIC_API_KEY` credential gap (`ESC-019`,
  `SPRINT-022`'s own finding) remains open — this sprint's own live
  verification further confirms it (a real `401` from a real Anthropic
  call). Provisioning a real key remains an operator action, not
  something any sprint's own code can resolve.
- Real, live-verification-only vault/config changes this sprint made
  that should be reviewed as PERMANENT, intentional configuration (not
  test residue): `vault-qa` now carries real keywords
  (`["research", "web research"]`) and real `"web-research"` skill
  access, serving as this pilot's real Research-Expert candidate;
  `vault-filing-expert` gained one additional real keyword (`"vault"`)
  so Hop 2's fixed `need_description` genuinely matches it. Both are
  real, load-bearing configuration for `compass-expert`'s own chain to
  route correctly going forward, not throwaway test setup — worth a
  human glance to confirm `vault-qa` (originally the read-only Vault Q&A
  expert) is an acceptable long-term home for this Research-Expert role,
  or whether a future, purpose-built Research Expert agent should take
  over instead.

---

## Notes

**Sprint assembled 2026-08-12 (`/plan-sprints`, operator-directed batch —
the "Compass Expert" business chain).** Final sprint of the 5-sprint
sequence (`SPRINT-020`…`SPRINT-024`); see `SPRINT-020`'s own Notes for the
full chain-partitioning rationale.

**`REQ-SB-36-US-02-T04` explicitly confirmed excluded/blocked, not
scheduled into this or any other sprint as buildable work** — per the
task-issuing operator's own direction and the decomposer's own already-
recorded, confirmed-acceptable judgement call (`ESC-018`). No attempt was
made to unblock it, fabricate a `depends_on` edge for it, or silently
schedule it. It remains outside every sprint until `REQ-SB-29-US-01` is
decomposed.

**Gate: `gate: clear` 2026-08-12.** No MUST-FLAG trigger fires for this
product-owner pass itself: (1) no material assumption — all four
cross-sprint edges and the `T04` exclusion are read directly off the
decomposer's own recorded `depends_on` graph and its own already-flagged,
human-facing judgement call, not guessed or re-decided; (2) `REQ-SB-36` is
not `<!-- Draft -->`/unfinalised; (3) product-owner does not write ADRs —
none touched; (4) **no new `ESCALATIONS.md` entry written by this pass** —
`ESC-018` was already opened by the decomposer, this pass does not
duplicate it; (5) **re-checked explicitly against both the "oversized" and
"blocked story" MUST-FLAG sub-triggers, not skipped:** not oversized (3
buildable tasks, S); this is not a "blocked story" in the MUST-FLAG sense
requiring a fresh flag — the *story* is `status: Ready` with 3 of 4 tasks
genuinely buildable and zero blocking issue of their own, and the one
blocked task (`T04`) was already individually flagged, with its own
options presented, by the decomposer's prior pass; this pass's own
contribution is scheduling the confirmed-buildable subset, not making a
fresh blocked-story judgement call. The four `depends_on_sprints` edges
introduced mirror real, already-recorded task-level edges exactly, the
same reasoning `SPRINT-012`/`SPRINT-022`/`SPRINT-023` already established;
(6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous for this pass — the decomposer's own prior pass already
named the two options (full-story-lockstep vs. granular per-task
scheduling) and made the granular choice, itself flagged for human
confirmation (`REVIEW-QUEUE.md`); this pass applies that already-made
choice rather than re-opening it. Advances `Draft → Ready`.
