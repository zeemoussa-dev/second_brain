---
id: SPRINT-034
title: Agent Creation Wizard — Worker-type and Producer-type flows
status: Done
gate: flagged
gate_reason: "retro-harvest — human skims the drafted retro below and propagates patterns into Implementation/Learnings.md; also carries forward REQ-SB-37-US-03's own ADR-031 review flag (unchanged by this coder pass)"
phase: P1
depends_on_sprints: [SPRINT-030, SPRINT-031, SPRINT-032, SPRINT-033]
sizing_estimate: "~5 tasks, S"
created: 2026-08-13
started: 2026-08-14
completed: 2026-08-14
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-034 — Agent Creation Wizard — Worker-type and Producer-type flows

## Sprint Goal

Complete the Agent Creation Wizard's remaining two type flows: Worker
(Skills multi-select + Vault Scope + Section) and Producer (Purpose + a
single-select output Skill + Section).

---

## Grouping Rationale & Sizing

- **Why grouped:** `REQ-SB-37-US-02` and `REQ-SB-37-US-03` have a real,
  same-sprint-appropriate dependency chain between them, verified directly
  against real task frontmatter: `37-US-03-T02` `depends_on:
  [REQ-SB-37-US-02-T01, REQ-SB-37-US-03-T01]` and `37-US-03-T03`
  `depends_on: [REQ-SB-37-US-03-T02, REQ-SB-37-US-02-T02, ...]`. Per rule 1,
  dependency-linked stories belong in the same sprint or ordered sprints —
  here the tight, two-way interleaving (Producer's `T02`/`T03` each depend on
  a specific Worker task) makes the same sprint the cleaner choice over a
  further split, and combined they total only 5 tasks (S), well under this
  project's own `L` ceiling.
- **Why NOT combined with `SPRINT-033` (`REQ-SB-37-US-01`):** see
  `SPRINT-033`'s own Grouping Rationale — `US-01` has zero cross-story deps
  and can build/ship independently in parallel with the Skills-foundation
  chain, while `US-02`/`US-03` are hard-blocked on that same chain
  (`SPRINT-030`/`031`) plus `SPRINT-032`. Bundling all three into one sprint
  would needlessly delay `US-01`'s own start and push the same file
  (`agents_router.py`'s `POST /agents` endpoint) through three edits inside
  one working context instead of two spread across ordered sprints.
- **Sizing estimate:** ~5 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-37-US-02](../UserStories/REQ-SB-37-US-02-agent-creation-worker-flow.md) | Agent Creation Wizard — the Worker-type flow (Skills, Vault Scope, Section) | P1 | Ready |
| [REQ-SB-37-US-03](../UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md) | Agent Creation Wizard — the Producer-type flow (Purpose + output action) | P1 | Ready |

**Tasks in scope** (dependency order): `37-US-02-T01` (agents_router.py
POST /agents worker type, `depends_on: [37-US-01-T03, 39-US-02-T03]`) →
`37-US-03-T01` (write-to-vault-draft placeholder output Skill, `depends_on:
[39-US-01-T01, 39-US-01-T02, 39-US-02-T01]`) → `37-US-03-T02`
(agents_router.py POST /agents producer type, `depends_on: [37-US-02-T01,
37-US-03-T01]`) → `37-US-02-T02` (CreateAgentWizard.tsx Worker step,
`depends_on: [37-US-02-T01, 37-US-01-T04, 39-US-01-T09, 39-US-02-T03,
29-US-01-T05]`) → `37-US-03-T03` (CreateAgentWizard.tsx Producer step,
`depends_on: [37-US-03-T02, 37-US-02-T02, 39-US-01-T09]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-030` (`REQ-SB-39-US-01`), `SPRINT-031`
  (`REQ-SB-39-US-02`), `SPRINT-032` (`REQ-SB-29-US-01`), `SPRINT-033`
  (`REQ-SB-37-US-01`) — every one of these edges mirrors a real task-level
  `depends_on` recorded by the decomposer, not an invented dependency.

---

## Out of Scope

- Wizard entry point + Expert-type flow (`REQ-SB-37-US-01` → `SPRINT-033`).

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  No task was split, dropped, or merged. Build order held to the
  dependency chain the sprint's own Grouping Rationale predicted
  (`37-US-02-T01` → `37-US-03-T01` → `37-US-03-T02` → `37-US-02-T02` →
  `37-US-03-T03`), and every task's own code sample matched the real
  current state of its target files almost verbatim — the composition
  work this sprint's own "no new ADR" (Worker) / "one new ADR" (Producer,
  `ADR-031`, already reviewed at `/plan-tasks`) reasoning predicted held
  up exactly at build time, with zero mid-build reconciliation surprises
  beyond ordinary file-drift checks.

### What worked

- **Backend-layer-first verification, reconfirmed a further time** — six
  of this sprint's own twelve locked ACs (`37-US-02-AC-03/05/06`,
  `37-US-03-AC-02/03/06`) were verified directly against `POST /agents`
  before either wizard step existed, against every already-`Done`
  downstream surface (Agents Map, Skills grant/gate, chat, history) —
  zero rework needed once the frontend steps landed; the backend proof
  and the frontend proof were genuinely independent, not one masking a
  gap in the other.
- **CDP-driven headless-Edge verification with a `window.fetch` spy**,
  combined with the native-setter React-controlled-input technique, gave
  byte-exact confirmation of the wizard's own multi-call sequencing
  contracts (Worker's *combined* `PATCH` vs. Producer's *alone*
  `section_id` `PATCH`) that a screenshot or a passing-unit-test claim
  alone could not have proven — the Network-panel-equivalent evidence
  (call count, method, URL, body) was the actual load-bearing proof for
  `AC-02` in both stories.
- **Cross-checking a freshly-created agent's behavior against an
  existing, already-shipped agent's own identical call**, live, in the
  same session (Supervised-mode deferral for `ops-helper` vs.
  `email-capture`; honest-unavailable shape for `ops-helper` vs.
  `meeting-capture`) turned "the gate probably behaves the same for a
  new agent" into a directly-observed, byte-identical confirmation —
  reused this project's own established cross-check pattern
  (`SPRINT-018`) one layer up, at the agent-creation layer.

### What didn't work

- **A rapid two-file edit sequence (`skill_tools.py` then
  `agents_router.py`, ~1 minute apart) caused `uvicorn --reload`'s
  `WatchFiles` watcher to miss the second file's change** — a request
  issued right after the edit still returned pre-edit behavior, with no
  corresponding `Reloading...` log line ever appearing for the second
  file. Root-caused via this project's own established
  `Get-CimInstance Win32_Process` orphaned-fork-child inspection (the
  actual serving process's parent PID had already vanished); resolved by
  killing the specific orphaned PID and starting one fresh,
  explicitly-controlled instance, then re-running every affected Test
  step against confirmed-fresh code before recording any result.

### Patterns to carry forward

- **Backend-layer-first verification for any locked AC whose own Given
  clause names "an agent has just been created," not specifically "via
  the wizard"** — this is now the third story in the `REQ-SB-37` family
  to use this split cleanly (`US-01`, `US-02`, `US-03` alike), and it
  keeps each task's own live-verification cost bounded to what that
  task's own file changes can actually prove.
- **A `window.fetch` spy + the native-setter input technique, used
  together in one CDP script**, is now a proven, repeatable combination
  for verifying "validate everything client-side before any call fires,
  then fire an exact N-call sequence in a specific order with a specific
  body shape" ACs — worth reaching for by default whenever a locked AC's
  own wording specifies call *sequencing* or *cardinality*, not just an
  eventual outcome.
- **After ANY edit to a file a running `--reload` server is watching,
  re-confirm the new behavior with one cheap real request BEFORE running
  a task's full Tests sequence against it** — this sprint's own stale-
  reload finding was caught early specifically because a smoke check ran
  first; generalizes the existing orphaned-multiprocessing-fork-child
  Learnings entry (`SPRINT-019`/`021`/`022`/`029`) to a new trigger
  (rapid successive edits to sibling files), not just single-hang
  detection.

### Antipatterns to avoid

- **`taskkill /IM msedge.exe /T` for CDP-launched-browser cleanup** —
  this project's own `Implementation/Learnings.md` (`SPRINT-026`) already
  names the specific-PID form as the required technique; used the `/IM`
  form once early in this sprint out of habit before correcting to the
  specific-PID form for the rest of the sprint. No observed harm this
  time (verified via process-tree inspection afterward), but the risk
  the Learnings entry names (killing an unrelated session's own Edge
  instance) is real and this sprint should have followed its own
  project's documented guidance from the first CDP launch, not the
  second.
- **Checking `.second-brain/` state-file cleanliness at
  `src/backend/.second-brain` instead of the real, `.env`-configured
  `VAULT_PATH`** — cost one avoidable round of "why does a freshly
  created agent already have a Skill granted" investigation before
  finding the real, external vault directory holds the actual state
  files, not a path relative to the backend source tree. Worth naming
  explicitly: this project's own vault is *always* external to `src/`;
  any task's own "delete leftover state files first" instruction means
  the real `VAULT_PATH`, never a guessed in-repo path.

### Open follow-ups

- **`CreateAgentCard.tsx`'s own static copy is stale** ("Worker and
  Producer types are coming soon — Expert is available today") now that
  both flows are real — a single-line, zero-ambiguity copy fix, correctly
  left out of both `T02`'s and `T03`'s own `## Files to Modify` scope;
  worth a trivial follow-up edit (not a full story) the next time that
  file is touched for any reason.
- **The output-Skill this sprint seeded, `write-to-vault-draft`, is
  still an honest-unavailable stub** (`ADR-031` point 2, by design) — a
  real write-to-vault handler remains explicitly out of scope here and
  is real, unbuilt follow-on work whenever a future story picks it up.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** Four `depends_on_sprints`
edges recorded — all four are direct mirrors of real cross-story task
`depends_on` edges already present in the decomposer's own task files, not
inventions of this pass.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption; (2) `REQ-SB-37` is finalized PRD text; (3) product-owner
does not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (5
tasks, S); not a blocked story; the 4 cross-sprint dependencies recorded are
real, pre-existing task edges surfaced across a sizing-driven sprint split —
not a dependency "introduced" by this pass's own choice, so this does not
trip the cross-sprint-dependency MUST-FLAG sub-trigger; (6) N/A; (7) no
contradictory inputs; (8) the US-02+US-03-together vs. further-split choice
is resolved on a concrete basis (their own direct interleaving dependency),
not left ambiguous. Advances `Draft → Ready`.

**Coder pass, 2026-08-14 (`/implement-sprint SPRINT-034`).** Both stories
(`REQ-SB-37-US-02`, `REQ-SB-37-US-03`) built in the sprint's own
dependency order and marked `Done` — all 5 tasks `Done`, all 12 locked
ACs (6 per story) verified live, nothing `Blocked`. A real Worker agent
(`ops-helper`) and a real Producer agent (`vault-scribe`) were each
created end-to-end through the actual wizard UI and independently
confirmed via direct `GET` calls to match the UI's own claimed outcome.
Nothing new written to `REVIEW-QUEUE.md`/`ESCALATIONS.md` this pass — the
existing `ADR-031` review entry already covers `REQ-SB-37-US-03`'s own
carried-forward flag. `status: Ready → Done`, `completed: 2026-08-14`,
`gate: flagged` for retro-harvest (see Retrospective below) — the human
skims it and propagates patterns into `Implementation/Learnings.md`.
