---
id: SPRINT-054
title: Real Per-Thread Summary Synthesis (live capture) + One-Shot Backfill for Already-Captured Threads
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Retro-harvest — coder-drafted Retrospective below awaits human propagation into Implementation/Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-17
started: "2026-08-17"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-17"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-054 — Real Per-Thread Summary Synthesis + Existing-Thread Backfill

## Sprint Goal

Give `thread_match_merge` a real Compass-synthesized `## Summary` and opening-line
"current state at a glance" sentence for live-captured Threads, plus a one-shot
admin backfill that regenerates both for the Thread notes already sitting in the
vault today.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-67-US-01` is the only `Ready`,
  ungrouped story this pass (confirmed by reading every story file's
  `status:`/`sprint:` frontmatter). The two other `Ready` stories found,
  `REQ-SB-42-US-01` (`sprint: SPRINT-039`) and `REQ-SB-56-US-01`
  (`sprint: SPRINT-053`, `In Progress` — not touched), already carry a sprint and
  are out of scope for this pass. Its 3 tasks (`T01` → `T02` → `T03`) form one
  strict linear chain, acyclic, all within one architecture section ("Real Thread
  Summary Synthesis + Opening-Line + One-Shot Backfill") — no reason to split a
  single story's own 3-task chain across sprints.
- **Dependency graph honoured, not contradicted:** `T01` (standalone
  `vault_writer.py` opening-line primitive, `depends_on: []`) → `T02` (wires the
  real Compass synthesis call into `thread_match_merge`, `depends_on: [T01]`) →
  `T03` (one-shot backfill, reuses `T02`'s own shared synthesis helper,
  `depends_on: [T02]`) — read directly off the decomposer's own recorded
  `depends_on` edges, not reinterpreted.
- **No cross-sprint dependency needed.** The story's own upstream dependencies —
  `REQ-SB-55-US-01` (`SPRINT-049`, the `Thread-Match/Merge` Job this story
  extends), `REQ-SB-54-US-01` (`SPRINT-048`, the `replace_body_section`/opening-
  line convention this story builds on), and `REQ-SB-66-US-01` (`SPRINT-052`, the
  `prompt_override`/`agent_prompts.py` wiring this story's new call reuses) — are
  all already `Done`, fully satisfied before this sprint starts, not merely
  ordered against an in-flight sprint. No `depends_on_sprints` edge is required.
- **Sizing estimate:** ~3 tasks, S — matches this project's now-repeated
  "~3 tasks, S" precedent for a single, bounded story extending one already-`Done`
  mechanism in place with one new call/endpoint (`SPRINT-023`, `SPRINT-024`,
  `SPRINT-050`, `SPRINT-053`, all matched exactly or closely at retro). `T02`
  (the integration task wiring the new Compass call, config, and the
  `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` follow-on) is expected to be the
  heaviest — it owns the largest share of locked ACs (`AC-01`, `AC-02`, `AC-04`
  live-capture half, `AC-05`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-054 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-67-US-01](../UserStories/REQ-SB-67-US-01-real-thread-summary-synthesis-and-backfill.md) | Real Per-Thread Summary Synthesis (live capture) + One-Shot Backfill for Already-Captured Threads | P1 | Done |

**Tasks in scope** (dependency order): `T01` (standalone `vault_writer.py`
opening-line primitive `replace_body_opening_line`, `depends_on: []`) → `T02`
(`thread_match_merge` gains the real Compass synthesis call, config-wired, honest
failure posture, `depends_on: [REQ-SB-67-US-01-T01]`) → `T03` (one-shot
`POST /poc/backfill-thread-summaries`, `depends_on: [REQ-SB-67-US-01-T02]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None — `REQ-SB-55-US-01` (`SPRINT-049`),
  `REQ-SB-54-US-01` (`SPRINT-048`), and `REQ-SB-66-US-01` (`SPRINT-052`) — the
  three stories this story's new call site and config wiring build on — are all
  already `Done`.
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`) and
  the real, configured Compass Provider — Scenario 3's backfill and every other
  scenario's live-capture verification are not satisfiable via a
  mocked/simulated vault or a mocked Compass response (parent story's own
  Dependencies).

---

## Out of Scope

- `REQ-SB-57`'s Project/Customer Glimpse synthesis — confirmed to never touch a
  Thread's own `## Summary`; not reduced or replaced by this sprint.
- `REQ-SB-59`'s future full vault migration/wipe-and-recapture — this sprint's
  backfill is deliberately narrow (Summary + opening line only, in place).
- Point 11's ("current state at a glance" opening line) rollout to
  Meeting/Project/Customer concept files — this sprint implements it for Thread
  notes only.
- A persisted/scheduled background catch-up mechanism for the backfill —
  resolved by the parent story to a one-shot admin endpoint instead.
- `REQ-SB-42-US-01` (Real-time Agent Activity Pulses) and `REQ-SB-56-US-01`
  (Meeting Capture & Thread Linking) — already grouped into their own
  `SPRINT-039`/`SPRINT-053`, out of scope for this pass.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR this sprint (architect's own confirmed finding)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S, no blockers, no
  mid-flight scope change — **Takeaway:** the "~3 tasks, S" estimate for a
  single bounded story extending one already-`Done` mechanism in place
  continues to hold exactly (now confirmed a fifth time — `SPRINT-023`,
  `SPRINT-024`, `SPRINT-050`, `SPRINT-053`, and this sprint).

### What worked

- **Designing the live-capture call site's own shared helper
  (`T02`'s `_synthesize_thread_summary`) with an explicit
  optional-delta parameter up front paid off directly for the backfill
  (`T03`).** `T03` composed `T02`'s helper with `new_message_body=None`
  with zero new synthesis logic, zero fork risk, and zero
  `email_classification.py` edits — `T03`'s own `## Files to Modify`
  never touched the file its own dependency lives in. This is the third
  sprint in a row where a deliberately-generalized primitive from an
  earlier task in the same story paid off for a later one without a
  second implementation (`SPRINT-053`'s own `T02` composing an existing
  more-general primitive is the most recent prior instance).
- **Reversing a `Done` story's own documented Constraint via a new story,
  confirmed by the architect to not require a new ADR, worked cleanly in
  practice.** `REQ-SB-55-US-01`'s "no second Compass call" Constraint was
  reopened by this story exactly as the architect pass predicted — no ADR
  touched, `REQ-SB-55-US-01` itself untouched, `Pipeline.md` hard rule 1
  (specs are append-only) respected throughout.
- **The scratch-vault-for-controlled-checks / real-vault-for-the-actual-
  operator-request split, reused from `T01`/`T02`'s own established
  precedent, gave clean byte-for-byte AC evidence AND satisfied the
  operator's real "backfill existing Threads" ask in the same task** — no
  tension between the two once the split was applied consistently.

### What didn't work

- **Spinning up a second `uvicorn app.main:app` instance against a
  `VAULT_PATH`-overridden scratch vault to test the new endpoint over
  real HTTP had an unintended side effect: `app/main.py`'s own `lifespan`
  unconditionally starts `capture_scheduler`, which polls the REAL
  configured Outlook mailbox regardless of which `VAULT_PATH` the
  process was started with.** Left running for several minutes, it pulled
  real Outlook conversations into the scratch vault in the background,
  producing confusing stray files that had to be identified and cleaned
  up before the controlled AC checks could be trusted. No real vault or
  real backend data was affected, but real Compass calls were wasted and
  verification time was lost diagnosing the stray files' own origin.
  Recorded as a new `MEMORY.md` Constraint.

### Patterns to carry forward

- **A one-shot backfill/maintenance task that reuses a live-capture
  call site's own synthesis logic should compose that call site's own
  shared helper with its delta parameter set to `None`/absent, never
  fork a second implementation** — this is now the established shape
  for this exact "regenerate what's already persisted, no new delta"
  class of operation.
- **For any future scratch-`VAULT_PATH` manual verification, call the
  target function directly in-process (a throwaway script/`python -c`
  importing the module) — never start a second full `uvicorn` instance**
  unless the scheduler itself is under test, in which case explicitly
  disable/mock its tick first. `T01`/`T02` already used the safe
  in-process pattern; this sprint is the first time the unsafe
  alternative was tried and its cost was observed directly.

### Antipatterns to avoid

- **Don't assume a `VAULT_PATH` environment override fully isolates a
  scratch verification run from the real, live external systems (Outlook,
  Compass) this codebase's own background scheduler polls unconditionally
  on process start** — the override only isolates the WRITE target, not
  whether background polling happens at all. Check whether the process
  you're about to start has its own `lifespan`/background-scheduler
  side effects before assuming "different `VAULT_PATH` = fully isolated."

### Open follow-ups

- None outstanding for this story — all 6 locked ACs verified, the real
  one-time backfill the operator asked for tonight was run and confirmed
  against the actual live vault's 2 real Thread notes.

---

## Notes

**Sprint assembled 2026-08-17 (`/plan-sprints`).** Full pass over every story
file's `status:`/`sprint:` frontmatter confirmed exactly one `Ready`, ungrouped
story: `REQ-SB-67-US-01` (`sprint: ""`, just decomposed into 3 `Ready` tasks —
this sprint). Two other `Ready` stories exist but are already grouped and out of
scope: `REQ-SB-42-US-01` (`sprint: SPRINT-039`) and `REQ-SB-56-US-01`
(`sprint: SPRINT-053`, `status: In Progress` — untouched, per hard rule "never
edit an `In Progress` sprint"). Every other story is `Draft`, `In Progress`, or
`Done`.

`REQ-SB-67-US-01` enters `/plan-sprints` at `status: Ready`, `gate: clear`
(decomposer pass, 2026-08-17 — 6 ACs locked and AC-tagged, 3 tasks created,
acyclic linear `depends_on` chain: `T01` → `T02` → `T03`). No standing
story-level flag to carry forward — both PRD-flagged open scope questions
(backfill trigger mechanism, cost/rate-limiting posture) were resolved by the
analyst via direct existing-code precedent before the story reached `Ready`, and
no ADR was touched at any upstream pass.

**Gate: `gate: clear` 2026-08-17.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the single-story grouping and
the "no `depends_on_sprints` needed" conclusion are both read directly off the
decomposer's own recorded `depends_on` edges and `BACKLOG.md`'s own confirmed
`Done` status for `REQ-SB-54-US-01`/`REQ-SB-55-US-01`/`REQ-SB-66-US-01`, not
guessed; (2) `REQ-SB-67` is not `<!-- Draft -->`/unfinalised; (3) product-owner
does not write ADRs — none created or changed by this pass; (4) no new
`ESCALATIONS.md` entry; (5) not oversized (3 tasks, S, matching four prior
confirmed-accurate "~3 tasks, S" precedents — `SPRINT-023`, `SPRINT-024`,
`SPRINT-050`, `SPRINT-053`); not a blocked story — every task is `status: Ready`;
no cross-sprint dependency had to be introduced (the story's three real upstream
dependencies are already `Done`, not merely ordered); (6) N/A (coder-only
trigger); (7) no contradictory inputs; (8) not genuinely ambiguous — one story,
one sprint, no equally-valid alternative partition exists. Advances
`Draft → Ready`.

**BACKLOG.md updated:** `REQ-SB-67` row's Sprint column set to `SPRINT-054`,
Sprint Status set to `Ready`; new `SPRINT-054` row appended to the Sprint Status
table.

---

**Coder pass, 2026-08-17 — `REQ-SB-67-US-01-T01` `Done`.** Sprint status flipped
`Ready` → `In Progress` (`started: 2026-08-17`) — the first task of this sprint's
only story is built and verified; `T02`/`T03` remain `Ready`, so the story itself
stays `status: Ready` until all three tasks are `Done` (mirrors `SPRINT-053`'s own
same "story stays `Ready` while its own tasks progress" precedent). `BACKLOG.md`'s
`SPRINT-054` Sprint Status row updated `Ready` → `In Progress`. `gate: clear` — no
MUST-FLAG trigger fired.

---

**Coder pass, 2026-08-17 — `REQ-SB-67-US-01-T03` `Done` (the sprint's last
task).** All 3 tasks now `Done`, all 6 locked ACs verified (`T02`:
`AC-01`/`AC-02`/`AC-04` live-capture half/`AC-05`; `T03`: `AC-03`/`AC-04`
backfill half/`AC-06`). Story `REQ-SB-67-US-01` set to `status: Done`.
Sprint status flipped `In Progress` → `Done` (`completed: 2026-08-17`),
`gate: flagged` (retro-harvest — see `## Retrospective` above) —
`REVIEW-QUEUE.md` entry written for the human harvest step.
`BACKLOG.md`'s `REQ-SB-67` row and `SPRINT-054` Sprint Status row both
updated to `Done`. Full verification evidence in `T03`'s own
`## Implementation Log`
(`Implementation/Tasks/REQ-SB-67-US-01-T03-thread-summary-backfill.md`),
including the real, live one-time backfill run against the operator's
actual `VAULT_PATH` vault's 2 real pre-existing Thread notes.
