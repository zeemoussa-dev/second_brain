---
id: SPRINT-073
title: The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest — coder drafted the Retrospective below; human skims and propagates Patterns/Antipatterns into Implementation/Learnings.md. The story's own standing ADR-058 human-review flag (REVIEW-QUEUE.md) is separate and unaffected by this sprint closing."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-073 — The Librarian — Two Sub-Pipelines

## Sprint Goal

Split the single shared `librarian-housekeeping` identity into two real,
independently-scheduled Agents — Threads Cleaning and Company and Partner
Building — via `ADR-058`'s "retire without delete" primitive, with zero
orphaned historical records.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 6 tasks belong to
  `REQ-SB-79-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "The Librarian — Two Sub-Pipelines", `ADR-058`). Graph
  read directly from each of the 6 task files' own `depends_on:`
  frontmatter (not from the story's own prose summary):
  - `T01` (`agent_registry.py` retire-without-delete primitive) —
    `depends_on: []`, root.
  - `T02` (two new agents + orchestrator split + 5-call-site rewire) —
    `depends_on: []`, root.
  - `T03` (Skill/grant catalog split) — `depends_on: [T02]`.
  - `T04` (`email_poc_router.py` route split) — `depends_on: [T02]`.
  - `T05` (`main.py` bootstrap wiring) — `depends_on: [T01, T02, T03]`.
  - `T06` (real end-to-end verification) — `depends_on: [T04, T05]`.
  - **Acyclic** — a valid topological order exists (`T01`/`T02` → `T03`/`T04`
    → `T05` → `T06`); confirmed by walking every edge above, no
    back-reference found. All 6 tasks carry `phase: P2` (matching the parent
    story) — no phase mixing.
- **Single sprint, not split.** No fault line decouples cleanly: `T05`
  (bootstrap wiring) alone needs `T01`, `T02`, AND `T03` simultaneously
  before `create_or_update_schedule` will even succeed, and `T06`
  transitively needs every other task's own output for a real full-system
  verification pass. Splitting along any plausible seam would still require
  the earlier group(s) fully `Done` before the next could start — no
  different in outcome from one sprint building all 6 in dependency order,
  just with extra sprint files and `depends_on_sprints` edges adding zero
  real decoupling value. Directly analogous to `SPRINT-072`'s own identical
  reasoning for the prior story in this same module (`REQ-SB-76-US-01`).
- **Sizing estimate: ~6 tasks, M.** Matches this project's own
  repeatedly-confirmed 6-task/M shape (`SPRINT-020`, `SPRINT-022`,
  `SPRINT-028`, `SPRINT-048` — all four exact matches at retro per
  `Implementation/Learnings.md`), and sits well under this project's own
  9-task/L ceiling — consistent with the PRD's and decomposer's own "smaller
  than `REQ-SB-72-US-01`'s 9-task/L build" sizing note. Every task is real,
  distinct, non-duplicative work (a new registry primitive, an orchestrator
  split + 5-call-site rewire, a skill/grant split, a route split, bootstrap
  wiring, and a real end-to-end verification pass) — no MUST-FLAG oversized
  trigger fired for this grouping decision.
- **Standing story-level flag, not a grouping ambiguity.** The story itself
  carries `gate: flagged` / `gate_reason: trigger-3 (ADR-058 created)` from
  the architect pass — a standing human-review item, already logged in
  `REVIEW-QUEUE.md` (`REQ-SB-79-US-01` entry, 2026-08-19). Per
  `Implementation/Pipeline.md`, this does not halt `/plan-sprints` — the
  product-owner does not clear an architect's own ADR flag, and the grouping
  decision above is itself unambiguous (single story, well-calibrated
  6-task/M shape, acyclic graph, all hard prerequisites already `Done`). This
  sprint's own `gate: clear` covers ONLY the grouping/partition decision; the
  story's own standing `ADR-058` review remains open in `REVIEW-QUEUE.md` and
  is unaffected by this sprint reaching `Ready`. Mirrors `SPRINT-072`'s own
  identical `ADR-057`/`REQ-SB-76-US-01` precedent and `SPRINT-049`'s own
  `ADR-043`/`REQ-SB-55-US-01` precedent.
- **Real, downstream cross-story dependency this sprint UNBLOCKS (not one it
  depends on):** `REQ-SB-77-US-01-T03` (a sibling story's own
  verification-only task) carries a real, decomposer-recorded `depends_on`
  edge directly onto THIS sprint's own `T02` — `run_company_partner_
  building_pass()` does not exist before `T02` lands. Recorded as
  `SPRINT-074`'s own `depends_on_sprints: [SPRINT-073]` edge, not duplicated
  here (mirrors `SPRINT-049`'s own "Unblocks: `SPRINT-050`" note).

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-79-US-01's own
frontmatter now carries sprint: "SPRINT-073". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-79-US-01](../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md) | The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building) | P2 | Done |

**Tasks in scope** (dependency order): `T01`/`T02` (independent roots) →
`T03`/`T04` (need `T02`) → `T05` (needs `T01`, `T02`, `T03`) → `T06` (needs
`T04`, `T05`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's three hard-blocking prerequisite
  stories are all already `Done` — `REQ-SB-72-US-01` (`SPRINT-063`),
  `REQ-SB-73-US-01` (`SPRINT-067`), `REQ-SB-74-US-01` (`SPRINT-068`) —
  confirmed directly: every one of this story's 6 tasks' `depends_on` edges
  resolves to another task WITHIN this same story/sprint; none names a task
  ID from any other sprint.
- **Soft, non-blocking sequencing note:** `REQ-SB-76-US-01` (Company Review,
  `SPRINT-072`, `In Progress`) — Scenario 5 of this story explicitly handles
  either ordering (`propose_company_review` joins Company and Partner
  Building whenever it ships, before or after this sprint). Not a hard
  blocker; no `depends_on_sprints` edge needed.
- **Unblocks:** `SPRINT-074` (`REQ-SB-77-US-01`) — recorded as that sprint's
  own `depends_on_sprints: [SPRINT-073]` edge, not duplicated here.
- **External:** none new — the real, already-configured vault this pipeline
  extends. The story's own standing `ADR-058` human-review item
  (`REVIEW-QUEUE.md`, 2026-08-19) does not block `/implement-sprint` per
  `Implementation/Pipeline.md`'s "flagged doesn't halt the stage" rule, but
  remains open for the human's own sign-off independent of this sprint's own
  readiness.

---

## Out of Scope

- People notes linking to their real Company/Partner note — `REQ-SB-77`,
  sequenced into `SPRINT-074`, behind this sprint.
- Grouping/color-coding the Pending Approvals list by proposal type —
  `REQ-SB-78`, sequenced into `SPRINT-075` (fully independent).
- Extending `REQ-SB-65`'s Job Tree visualization to either new sub-agent —
  the story's own disclosed Non-Goal.
- Any change to any individual Job's own internal mechanism, ordering logic,
  or output shape — pure re-registration/re-wiring of agent ownership.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed — already updated at `/plan-tasks` under "The Librarian — Two Sub-Pipelines"; confirmed the build matched it exactly, zero deviation)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-058`, recorded at `/plan-tasks`; standing human-review item remains open in `REVIEW-QUEUE.md`, unaffected by task/sprint completion)
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

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly,
  extending this project's own repeatedly-confirmed 6-task/M precedent
  (`SPRINT-020`/`022`/`028`/`048`, all four exact matches). Task count and
  code volume were both correctly predicted; the real cost driver was NOT
  code volume (the whole diff across all 6 tasks is well under 200 lines)
  but real-Compass-call latency during live verification — consistent
  with this project's own established pattern (`SPRINT-020`/`023`/`028`)
  of the estimate holding for build effort while live-verification cost
  needed its own separate reasoning.

### What worked

- **Bounding live verification to a small, real, dynamically-tracked
  Thread subset (via `vault_writer.list_thread_notes` monkeypatch, keyed
  by real `conversation_id` re-resolved fresh on every call — never a
  frozen path list) instead of paying for a full 141-Thread real-Compass
  sweep (~25.6s/call measured, ~2 hours per full orchestrator run)** —
  reused across `T02`/`T03`/`T04`/`T06`, each time producing genuinely
  real evidence (real files, real Compass calls, real Pending Approval
  writes, real HTTP round trips) at a small fraction of the unbounded
  cost. Directly extends `Implementation/Learnings.md`'s own `SPRINT-028`
  precedent one further time.
- **A dedicated, disposable, worktree-owned backend instance on its own
  port (`8010`), separate from the operator's own main-checkout processes
  (`8000`/`8001`)** — let `T04`/`T05`/`T06`'s own "start the real backend"
  test steps run genuinely, including a real kill-and-restart idempotency
  proof, with zero risk to the operator's already-running processes
  (confirmed reachable/undisturbed throughout, checked before AND after).
- **A temporary, monkeypatch-bounded SEPARATE server process (port
  `8011`), launched purely to real-HTTP-verify the two new POC routes**
  — proved genuine HTTP-level plumbing (not just function-level
  correctness) without extending the main verification instance's own
  scope or waiting out an unbounded real run.
- **Building `T04` (POC routes) and `T05` (`main.py` bootstrap) together
  before running either task's own HTTP-level Tests**, since `T04`'s own
  "start the real backend" step could not literally succeed until `T05`'s
  `main.py` fix also landed (both tasks only depend on `T02`, so the
  decomposer's own graph allowed either build order, but not either
  VERIFY order) — avoided a wasted, doomed-to-`ImportError` verification
  attempt.

### What didn't work

- **A first, unbounded real dispatch call (`T03`'s own Skill-delegation
  check) was started before the ~25.6s/real-Compass-call latency had been
  measured** — it made ~10 real Compass calls against the full 141-Thread
  corpus before being recognized as needlessly expensive for what the
  check actually needed proven, then deliberately killed by specific PID
  and re-run bounded. No real harm (each per-Thread write is
  independently idempotent-safe), but measuring one real Compass call's
  own latency FIRST (as ultimately done, and as should have been done
  before `T03`, not after) would have avoided the wasted partial run
  entirely.
- **A git worktree's own branch was several real commits behind
  `master`, even though the main checkout's `git status` was fully
  clean** — this session's very first `Read` calls against task/story/
  sprint files (via the main-checkout path, before any worktree
  awareness) succeeded, creating a false sense that the worktree already
  had everything; the worktree's OWN copy of those same files did not
  exist at all until a `git merge master --ff-only` was run. Root cause
  and fix now recorded in `MEMORY.md` (a new failure mode distinct from
  the already-documented `M`/`??` uncommitted-file staleness). Also
  surfaced a second, related gap: this same worktree's `SPRINT-073` file
  was still `status: Ready`/`started: ""` despite the launching agent's
  own instruction that it was "already flipped to `In Progress`" — that
  edit existed only as an UNCOMMITTED change in the main checkout, so it
  never reached this worktree at all (a real instance of the
  ALREADY-documented `M`/`??` staleness class, not the new one above);
  reconciled by applying the start/complete transition together in this
  same pass, since the sprint was in practice built start-to-finish in
  one continuous session.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Measure one real, representative external-call's own latency FIRST,
  before deciding a live-verification technique** (bounded-subset vs.
  full-corpus) — a single 25.6s real Compass call, timed up front, made
  the ~2-hour full-corpus cost immediately obvious and directly justified
  reusing the bounded-subset monkeypatch technique for the rest of the
  sprint's own live verification, rather than discovering the cost mid-
  run (as happened once, `T03`, before this was internalized).
- **When two sibling tasks both depend on the same third task but their
  own live-verification Tests blocks implicitly depend on EACH OTHER
  (e.g. both need "start the real backend" to actually succeed), build
  both tasks' CODE per the decomposer's own recorded dependency order,
  but defer VERIFICATION until both are on disk** — avoids a doomed,
  wasted verification attempt against a still-half-wired app.
- **A dedicated, disposable, worktree-owned backend instance on its own
  port is the correct default for any coder run needing to prove a real
  app-boot/restart-idempotency AC**, kept strictly separate from (and
  independently reconfirmed not to disturb) any already-running
  operator-facing process on the project's own usual ports.
- **Before trusting a git worktree's own copy of ANY pipeline artefact
  (task/story/sprint file), check whether the worktree's branch itself is
  simply behind `master`** (`git log --oneline HEAD..master`), not just
  whether the main checkout has uncommitted `M`/`??` drift — two distinct
  root causes for the same "worktree is missing something the main
  checkout has" symptom, both now documented in `MEMORY.md`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a real, unbounded orchestrator call is cheap to verify
  directly just because its own code diff is small** — `T03`'s Skill-
  wrapper change was a literal one-line delegate, but verifying it via an
  unbounded real dispatch call still cost real, multi-minute-and-counting
  Compass latency before being caught and bounded. Reconfirms this
  project's own standing "code volume does not predict live-verification
  cost" pattern (`SPRINT-020`/`023`/`028`/`031`) one further time,
  specifically for a case where the code change itself was trivial.
- **Trusting that a worktree "already has" a file just because reading
  the SAME logical path via the main-checkout's own filesystem path
  succeeded** — the two paths are genuinely different files on disk; a
  successful `Read` against the main checkout says nothing about the
  worktree's own copy until independently checked.

### Open follow-ups

- None blocking. The story's own standing `ADR-058` human-review item
  (`REVIEW-QUEUE.md`, logged 2026-08-19 at `/plan-tasks`) remains open,
  unaffected by this sprint's own completion — the human still owes it a
  look before/alongside reviewing this retro.

---

## Notes

**Grouping decision (product-owner, 2026-08-19):** Single sprint, no split.
Verified the 6 task files' own `depends_on:` frontmatter directly — matches
exactly, acyclic, all `phase: P2`. This sprint's grouping is unambiguous: one
story, one well-calibrated 6-task/M shape, all hard prerequisite stories
already `Done`, no cross-sprint dependency needed for THIS sprint to start.

**Real, disclosed downstream edge (not a grouping ambiguity):**
`REQ-SB-77-US-01-T03` carries a real, decomposer-recorded `depends_on` edge
onto this sprint's own `T02` (`run_company_partner_building_pass()`) — see
`REQ-SB-77-US-01`'s own `## Notes` (Decomposer pass) for the full reasoning.
Honoured here by sequencing `SPRINT-074` (`REQ-SB-77-US-01`) strictly behind
this sprint via a `depends_on_sprints: [SPRINT-073]` edge on `SPRINT-074`,
rather than combining the two stories into one sprint — mirrors this
project's own established `SPRINT-011`→`SPRINT-012`, `SPRINT-025`→
`SPRINT-026`, and `SPRINT-049`→`SPRINT-050` precedent (`Implementation/
Learnings.md`, `SPRINT-049`: "sequence a downstream story strictly behind
its upstream one via `depends_on_sprints`... when the downstream story's own
Tests block requires the REAL, running output of the upstream story"). Two
additional, real reasons beyond that precedent: (1) `REQ-SB-77-US-01-T03`'s
own Tests block requires a real, direct call to `run_company_partner_
building_pass()` — that function's own body does not exist until this
sprint's `T02` lands, so building the downstream sprint only after this one
closes means that task never has to stub or improvise the composition; (2) a
sizing-ceiling check — combined, the two stories would total 10 tasks, past
this project's own largest-ever confirmed-accurate single-sprint ceiling
(`SPRINT-021`/`SPRINT-030`/`SPRINT-063`, 9 tasks/L, all three exact matches),
with no sizing precedent to calibrate a 10-task working context against. This
is a reasoned sizing + dependency-shape call, not a genuinely ambiguous
partition — not flagged.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this role's own
grouping decision: not oversized (well under the proven 9-task/L ceiling); no
blocked story (all hard prerequisites `Done`); no cross-sprint dependency
this role had to introduce for THIS sprint to start (it has none); the
single-sprint-vs-split question was actively checked against the real task
graph, not left ambiguous. The story's own standing `gate: flagged`
(`ADR-058`, architect trigger-3) is a separate, already-logged
`REVIEW-QUEUE.md` item this role does not clear and which does not block
this sprint reaching `Ready`. Advanced `Draft → Ready` — eligible for
`/implement-sprint SPRINT-073`.

**BACKLOG.md updated:** `REQ-SB-79` row's Sprint column set to
`SPRINT-073`.

---

**Coder close-out (2026-08-19):** All 6 tasks built and independently
live-verified in dependency order (`T01`/`T02` → `T03`/`T04` → `T05` →
`T06`) against the real, configured vault. Every locked AC re-confirmed
live by `T06`'s own final integration pass. No genuine defect found. This
worktree's own copy of this sprint file had not yet received the launching
agent's own `status: In Progress`/`started: "2026-08-19"` edit (that edit
existed only as an uncommitted change in the main checkout at session
start — see this retro's own "What didn't work" and the new `MEMORY.md`
entry) — both the start and completion transitions are applied together
in this same pass, reflecting the sprint's real single-session build.
Sprint advances **`Ready` → `Done`**. `BACKLOG.md`'s Sprint Status table
row updated to `Done`.
