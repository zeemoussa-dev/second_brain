---
id: SPRINT-025
title: Vault Indexing — core index, on-demand re-index endpoint, hourly-schedule wiring
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "trigger-7 (real, live-discovered filename-stem collision — ESC-027, Open, non-blocking)"
phase: MVP                         # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-13
started: "2026-08-13"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"            # YYYY-MM-DD when status → Done
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

# SPRINT-025 — Vault Indexing

## Sprint Goal

Build `REQ-SB-01-US-01`'s real, re-runnable structural index of the vault's
frontmatter/tags/wikilinks (per `ADR-024`), reachable both via an explicit
on-demand endpoint and automatically on `REQ-SB-07`'s existing hourly
scheduled run.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-01-US-01` is the only story
  assigned here, all 4 of its tasks form one straight dependency chain
  (`T01 → T02 → {T03, T04}`), and it is the foundational, never-before-built
  work every other MVP-phase story in this batch (`REQ-SB-02-US-01`) depends
  on. Nothing else in this batch shares its architecture scope
  (`ADR-024`, "Vault Indexing Layer"), so there is no cohesion reason to
  combine it with anything else.
- **Why NOT combined with `REQ-SB-02-US-01` (Browse & Search) in one
  sprint:** the real, decomposer-recorded cross-story edge
  (`REQ-SB-02-US-01-T01` → `REQ-SB-01-US-01-T02`) is honoured via
  `SPRINT-026`'s own `depends_on_sprints: [SPRINT-025]` instead of same-
  sprint sequencing. `REQ-SB-02-US-01` adds a genuinely different, larger
  surface on top (ranked search algorithm, a new API router, and two full
  frontend pages) — combining both stories' 8 tasks into one sprint would
  push well past this project's own `~8-9 tasks, L` sizing ceiling
  (`SPRINT-010`/`SPRINT-021`) while mixing a pure-backend indexing layer
  with a heavy frontend build in the same working context. Two ordered,
  right-sized sprints is the cleaner fit — an ordinary application of hard
  rule 7's "same sprint **or** ordered sprints" choice, not a forced
  single-story-per-sprint pattern for its own sake.
- **Sizing estimate:** ~4 tasks, S. `T01` (a `vault_writer.py` parsing fix +
  a public wikilink-extraction primitive) → `T02` (the real cost center —
  the core index build/rebuild/backlink module itself, covers `AC-01`–
  `AC-07`) → `T03`/`T04` (the two independent trigger surfaces — an
  on-demand endpoint, and one unconditional call wired into the existing
  scheduler tick — both depend only on `T02`, not on each other). Matches
  this project's own precedent for a first-pass, backend-only foundational
  story of this shape (`SPRINT-001`, `SPRINT-008`, `SPRINT-019`, all
  ~4 tasks, S).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-025 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-01-US-01](../UserStories/REQ-SB-01-US-01-vault-indexing.md) | Vault Indexing — a real, re-runnable index of frontmatter, tags, and wikilinks | MVP | Done |

**Tasks in scope** (dependency order): [[REQ-SB-01-US-01-T01]]
(`vault_writer.py` frontmatter list-value round-trip fix + public
wikilink-extraction primitive, `depends_on: []`), [[REQ-SB-01-US-01-T02]]
(core index build/rebuild/backlink logic — `app/business/vault_indexing.py`,
`depends_on: [T01]`), [[REQ-SB-01-US-01-T03]] (on-demand re-index endpoint —
`app/api/vault_index_router.py`, `depends_on: [T02]`), [[REQ-SB-01-US-01-T04]]
(scheduler-tick wiring — `email_classification.py` unconditional call,
`depends_on: [T02]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- No external blocker — this story's own dependencies (`REQ-SB-07-US-01`,
  the existing hourly-scheduler infrastructure this story's `T04` wires
  into) are already `Done`.

---

## Out of Scope

- `REQ-SB-02-US-01` (Browse & Search) — the natural next sprint,
  `SPRINT-026`, sequenced behind this one via `depends_on_sprints`.
- Embeddings/semantic search/chunking (`REQ-SB-06`, P2) — out of this
  story's own scope entirely, not just this sprint's.
- Live filesystem watching — resolved out of scope for this story (see
  the story's own Constraints); on-demand + hourly-scheduled re-indexing is
  the full trigger-mechanism scope this sprint builds.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed — built exactly per the architect's already-recorded `ADR-024`/"Vault Indexing Layer" section)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (none new this pass — `ADR-024` already `Accepted`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  No task was split, dropped, or merged. `T02` (the core index module)
  was correctly identified up front as the real cost center and took the
  bulk of build/verification time, largely due to the real-vault
  filename-stem collision investigation (`ESC-027`), not the index logic
  itself, which built clean on the first pass exactly per `ADR-024`'s own
  code block.

### What worked

- **Reading the real, current file before every edit — twice caught real
  drift mid-sprint.** `app/config.py` gained a `hermes_mcp_shared_secret`
  field and `app/main.py` gained the `/mcp` shared-secret auth wrap
  (both `REQ-SB-04`/`ADR-025` landing concurrently) between this sprint's
  own planning and its build — both non-issues because every file was
  re-read fresh immediately before editing, exactly per this project's
  own repeatedly-documented "never trust a task's stale code sample"
  pattern, restated explicitly for this sprint by the launching agent.
- **Treating a real, live-discovered, out-of-scope defect as "escalate,
  don't block"** — `ESC-027`'s filename-stem collision (2 of 503 real
  notes) was found via `T02`'s own mandated `AC-01` live verification,
  root-caused precisely (which two files, why, which already-`Done` code
  is responsible), escalated formally (`ESCALATIONS.md` + `REVIEW-QUEUE.md`
  + a recommended `/bug` capture), and did not block `T02`/`T03`/`T04`/the
  sprint — mirroring this project's own established `ESC-002`/`ESC-003`/
  `ESC-012` precedent exactly. Avoided two worse outcomes: silently
  accepting a broken AC, or freezing this whole foundational sprint (and
  everything downstream, e.g. `SPRINT-026`) over a narrow, pre-existing,
  unrelated defect in already-shipped code.
- **Skipping the HTTP layer, twice, for two different real reasons, both
  disclosed** — `T03` (`TestClient` without the `with` lifespan context)
  and `T04` (calling `capture_scheduler.run_capture_if_idle()` directly
  via `asyncio.run`) both avoided a real, confirmed-live app-start hang
  (`BUG-008`) while still exercising the *real* code path each AC actually
  needed proven (real FastAPI routing for `T03`; the literal real
  app-start trigger function, including a real live Outlook/Compass
  capture run, for `T04`) — not a weaker substitute, and not a blind
  retry-until-it-works loop against a process already confirmed to hang.
  Before assuming `BUG-008` applied wholesale, a quick, bounded, isolated
  check confirmed Outlook COM itself was actually fine in this
  environment right now — avoiding an unnecessary escalation/blocker for
  a risk that, on closer inspection, wasn't this task's actual obstacle
  (the real, slow, per-email Compass LLM classification calls almost
  certainly were).
- **Killing a hung background process by its own specific, timestamp-
  verified PID, leaving an unrelated concurrent process pair alone** —
  this session's own repo has genuine concurrent work landing in
  real time (confirmed twice, `config.py`/`main.py` drift above); a
  blanket `taskkill` here would have risked killing another session's
  own in-flight work, the exact antipattern `SPRINT-009`'s own retro
  already flagged.

### What didn't work

- Nothing structural. The one real friction point (`BUG-008`'s hang) was
  already a known, logged, pre-existing issue with an established
  workaround pattern from `Implementation/Learnings.md` (`SPRINT-023`) —
  applying and slightly extending that pattern (real `TestClient` HTTP
  routing instead of a raw function call; calling the literal real
  trigger function instead of the underlying business function) cost
  investigation time but no rework.

### Patterns to carry forward

- **When a "start the real server" verification step is blocked by a
  known, already-logged app-startup issue (`BUG-008`), don't default to
  the weakest possible substitute (a raw function call) — find the
  closest-to-real substitute that still exercises what the AC actually
  needs proven** (`TestClient` without lifespan for a real HTTP-routing
  AC; the literal real trigger function via `asyncio.run` for a real
  "does the wiring fire automatically" AC) — both are disclosed
  verification-method deviations, not silent AC weakenings.
- **Before assuming a known, logged issue (`BUG-008`) explains a new
  hang, isolate and test its actual named cause in isolation first** — a
  bounded, standalone Outlook-COM check (20s timeout) proved COM itself
  was fine, redirecting the investigation toward the real, more likely
  cause (multiple real per-email Compass LLM classification calls) rather
  than mis-attributing a slow-but-working pipeline to `BUG-008`'s own
  named "no interactive Outlook session" failure mode.
- **A locked AC's own exact-match verification step (`len(index) ==
  len(real_paths)`) is itself a real correctness assertion, not just
  illustrative prose — when it genuinely fails against live data, root-
  cause it fully before deciding whether it's a build defect or an
  environmental/out-of-scope finding**, then escalate the latter formally
  rather than loosening the check to make it pass.

### Antipatterns to avoid

- None new this sprint beyond what's already documented (blanket process
  kills, trusting a task's stale code sample) — both were actively
  avoided here, not repeated.

### Open follow-ups

- `ESC-027` (Open) — real filename-stem collision, needs a `/bug` capture
  and eventual `BUGFIX-NN-US-01` fix in `email_classification.py`'s
  stem-construction or `vault_writer._slugify`. Non-blocking for this
  sprint or `SPRINT-026` (Browse & Search), but `SPRINT-026`'s own build
  should be aware one real vault note can currently be silently absent
  from `vault_indexing.get_index()`'s result when two subjects collide
  after 80-char truncation.
- `BUGS.md` → `BUG-008` (Open, pre-existing, not this sprint's own
  finding) — this sprint's own experience reinforces its real operational
  cost: two of four tasks needed a documented workaround because of it.
  Worth prioritizing now that a second, independent sprint has hit it.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** First of a two-sprint,
MVP-phase pair (`SPRINT-025` → `SPRINT-026`) covering `REQ-SB-01`/`REQ-SB-02`
— the vault's first-ever real index, and the browse/search surface built on
top of it.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the task breakdown and its
`depends_on` chain are read directly off the decomposer's own recorded
graph, not guessed; (2) `REQ-SB-01` is finalized PRD text; (3) product-owner
does not write ADRs — `ADR-024` was already reviewed and approved
(`REVIEW-QUEUE.md`, 2026-08-13) before this pass; (4) no new
`ESCALATIONS.md` entry needed; (5) not oversized (4 tasks, S) and not a
blocked story (all 4 tasks are `Ready`, zero blocking issue); (6) N/A
(coder-only trigger); (7) no contradictory inputs; (8) not ambiguous — a
single-story sprint with a straight dependency chain has exactly one
reasonable grouping. Advances `Draft → Ready`.
