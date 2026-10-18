---
id: SPRINT-089
title: Workflow as the seventh artifact kind — the operator documents how a kind of request is handled
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint closed 2026-10-18 — the drafted ## Retrospective awaits a human skim so its patterns and antipatterns can be harvested into Implementation/Learnings.md (the coder never writes that file)."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087, SPRINT-088]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: 2026-10-18                        # YYYY-MM-DD when status → In Progress
completed: 2026-10-18              # YYYY-MM-DD when status → Done
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

# SPRINT-089 — Workflow as the Seventh Artifact Kind

## Sprint Goal

Let the operator document, as a real artifact, the ordered steps for a kind of
request — each step referencing a catalogued Action id so a workflow is invalid
by construction rather than by review — and have the framework run it step by
step against a run record.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-04` is the most dependent of
  the five. Its six inbound cross-story edges are recorded in the task files —
  four into `US-02` (`T01 → US-02-T01`, `T02 → US-02-T03`, `T04 → US-02-T04`,
  `T07 → US-02-T06`) and two into `US-03` (`T05 → US-03-T04`,
  `T06 → US-03-T01`) — so it cannot start until both `SPRINT-087` and
  `SPRINT-088` are `Done`. At 7 tasks it also fills a sprint on its own.
- **Why not merged with `SPRINT-090` (`US-05`).** They share the same two
  upstream sprints and have **zero edges between them** (checked task by task in
  both directions), which is normally this project's textbook case for one
  shared sprint (`SPRINT-083`, `SPRINT-084`, `SPRINT-085` all did exactly that).
  It was rejected here on size alone: 7 + 5 = 12 tasks, far past the confirmed
  8–9-task `L` ceiling. Being independent of each other, they may be built in
  either order once their two upstream sprints are `Done` — the sprint numbering
  carries no ordering claim between `SPRINT-089` and `SPRINT-090`.
- **Sizing:** 7 tasks, sized `L`. Precedent for 7 tasks is split between `M`
  (`SPRINT-052`, `SPRINT-085`) and `L` (`SPRINT-079`); this one sits with the
  `L` case because, like `SPRINT-079`, it adds a whole **kind** across
  inventory, export, import and the dependency resolver (`T04`), plus a run
  record with its own routes (`T05`), publication into agent context (`T06`) and
  a new Settings screen (`T07`). `T04` additionally depends on `US-02-T04`, so
  it extends a six-kind set that will itself be freshly written.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-089 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-04](../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md) | Workflow as the seventh artifact kind — the operator documents how a kind of request is handled | P2 | **Done 2026-10-18** — all seven tasks complete, all seven locked ACs verified. **T06 Done 2026-10-18** — `AC-03`: a fourth marker block in each agent's SOUL.md names the Workflows that agent could really run, the kind of request each handles and what it reports, and deliberately **not** their steps (`ADR-034` — the run engine owns the order, and a recital in the prompt would be a second, unenforced copy of it); `WorkflowManager.create/update/delete` republish automatically on a background thread, so editing the catalogue IS the whole operation; `run_workflow.py` joins `call_action.py` in the shipped runner Skill and drives a real run one step at a time, relaying the app's own composed report verbatim. Proved byte-for-byte on a real SOUL.md in a scratch Hermes home (190 → 1680 bytes, exactly the 1488-byte block plus its separator; no CRLF, final newline kept, one marker pair, a no-op pass leaving even the mtime alone) and end to end on a disposable install over a real socket, including a confirmation pause at exactly the marked step and `--resume` finishing the SAME run without re-running step 1. Two defects found by running it rather than reading it, both fixed here: the Action and Workflow publication passes were silently losing each other's block, and a confirmation pause had no way to resume. Suite 672 → **686 passed, 0 failed**. Task `gate: flagged` for six judgement calls; no `ESCALATIONS.md` entry. (T01 Done 2026-10-18 — `AC-01`, `AC-07`; T02 Done 2026-10-18 — `AC-02`/`AC-06`; `ESC-075` Resolved, the authorised one-fixture scope extension landed and also stopped `T01`'s tests reading the operator's real Actions store; suite 627 passed. T03 Done 2026-10-18 — `AC-01`/`AC-02` verified over the new `app/api/workflows_router.py`, registered in `app/main.py`; refusals reach the client as a 409 carrying the Manager's own sentence; suite 628 → 634 passed, 0 failed, plus a real-socket round trip on a disposable install. `T05` and `T07` unblocked. **T04 Done 2026-10-18** — `AC-04`/`AC-05`/`AC-07` verified on 12 AC-tagged tests: the seventh kind is live across all six `business/logic/artifact_*.py` modules including the import conflict gate, an exported Workflow carries every Action its steps name and recurses into their implementation Skills, import reuses `WorkflowManager.import_workflow` so `T02`'s refusal fires at the first save rather than as a second divergent check, Pipelines are byte-identical on their real stored bytes/cron ids/schedules, and nothing from `ActionCalls/`/`WorkflowRuns/` is exportable. Two authorised scope extensions, both escalated rather than reached for: `ESC-076` (the sixth `artifact_*.py` module) and `ESC-077` (the unknown-kind guard test, which had used `workflow` as its unsupported-kind example and now derives its accepted-kinds assertion from the live map). Suite 634 → **655 passed, 0 failed**. `T07` unblocked. **T05 Done 2026-10-18** — `AC-03` verified on 11 AC-tagged tests plus the manual loopback run: a run is now a record at `<DATA_PATH>/data/WorkflowRuns/<run_id>.json` holding every documented step in the documented order, each with a literal status word (`not_reached`/`running`/`awaiting_confirmation`/`done`/`failed`/`refused`) written from the first byte, so a step that has not run is never a step that succeeded with no output; `next-step` hands back exactly one step dispatched through the unchanged `ADR-033` gate and returns the same step — dispatching nothing twice, measured around the real seam — until its outcome is recorded; a confirmation-marked step pauses at an ordinary `awaiting_confirmation` ledger row on the existing pending/confirm/decline surface and a decline leaves the run `blocked`, never complete; and the report is composed from the recorded outcomes on demand, never stored. Three run routes and no fourth. Suite 655 → **666 passed, 0 failed**, the new file proved to leave an empty install empty. Task `gate: flagged` for one judgement call (a step marked for confirmation whose Action is not confirmation-required is refused rather than performed — the gate accepts no override; the one-parameter change that would close the gap is written out in `REVIEW-QUEUE.md`), nothing blocked, no `ESCALATIONS.md` entry. `T06` unblocked; `T06`/`T07` remain) |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → T02 → T03`, `T01 → T04`, `T03 → T05 → T06`, `(T03, T04) → T07`.

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-087` (`US-02` — the Action entity, CRUD API,
  kind registration and the Actions screen) **and** `SPRINT-088` (`US-03` — the
  publication seam and the confirmation/single-use grant). `/implement-sprint`
  refuses this sprint until **both** are `Done` (hard rule 9).
- **No dependency either way with `SPRINT-090`.** Either may be built first once
  the two upstream sprints are `Done`.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-04` is flagged under trigger 3 — `ADR-034` decides
  that the framework *runs* a workflow step by step against a run record rather
  than reciting it into the agent's context, and awaits the operator's look.
  That decision shapes `T05`/`T06` directly. See `REVIEW-QUEUE.md`.
- **`ADR-032`'s "`Pipeline` is left exactly as it is"** stands: a Workflow is
  intent-triggered, a Pipeline is time-triggered, and convergence is explicitly
  deferred.

---

## Out of Scope

- The Action catalogue (`SPRINT-087`) and enforcement at the call
  (`SPRINT-088`).
- Entity resolution (`SPRINT-090`).
- Any change to the existing `Pipeline` artifact kind (`ADR-032`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact —
      no change needed: the sprint built exactly what §Workflow — the Seventh
      Artifact Kind, §Workflow Runs — Ordered by the Framework and §Catalogue
      Publication Into Agent Context already describe
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-032` and
      `ADR-034`, both written before the build and both confirmed by it
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints —
      **not appended.** `MEMORY.md` is 86 KB against the 40 KB budget its own
      rule 1 sets, which forbids appending while over, so every candidate this
      sprint produced is parked in `REVIEW-QUEUE.md` instead. See
      *Open follow-ups* — this is now the sprint's largest single piece of
      unfiled knowledge.
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (all
six inbound edges are quoted from the task files); requirement finalised; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; **not oversized**
(7 tasks, inside the confirmed band — this is also why `US-05` was not folded in
here); **no `Blocked` story**. On trigger 5's cross-sprint clause: both
`depends_on_sprints` edges are the decomposer's own task edges expressed at
sprint level, not dependencies this pass introduced; hard rule 7's "ordered
sprints with a recorded edge" is exactly the sanctioned shape, and the repo
precedent for it is `SPRINT-080`/`083`/`084`, all `gate: clear`. No contradictory
inputs. On trigger 8: the `SPRINT-089`/`SPRINT-090` build order is genuinely free
(no edge either way), but that is not an ambiguous *partition* — both sprints are
legal in either order and the sprint files say so, so there is nothing for a
human to decide.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~7 tasks, `L` — **Actual:** 7 tasks, `L`, none split, dropped
  or merged — **Takeaway:** accurate on both axes, and the grouping rationale's
  own reasoning held: `T04` (the kind across six shared modules) and `T07` (the
  screen) were the heaviest, exactly as predicted, and for the predicted
  reason — they cross other people's files. What the estimate did **not**
  capture is that four of the seven tasks raised an escalation
  (`ESC-075`–`ESC-078`), three of them the same family, and each one cost a
  `Blocked` task and a human round trip. On this evidence, "adds a kind across
  an existing family" should carry an explicit escalation-likelihood note at
  sizing time, separately from task count.

### What worked

- **Writing the ADRs before the build and letting them decide.** `ADR-032`
  (seventh kind, step-references-Action, `Pipeline` untouched) and `ADR-034`
  (the framework runs a Workflow against a run record; publication only says
  which exist) were both settled before `T01`. Every task then had an answer to
  "what is this text allowed to be load-bearing for", and `T06` in particular
  was able to assert the steps are **absent** from the published block rather
  than argue about how much to recite. Zero mid-build architectural rework.
- **Turning prose promises into properties of a stored file.** `AC-03`'s "in
  order", "no skipped step", "no invented step" and "reports what the Workflow
  says" were rewritten by the decomposer against the run record. That is the
  single reason `AC-03` was verifiable at all — the final check is a `.json` on
  disk, not a judgement about a model's behaviour.
- **The suite-wide Hermes sandbox (`tests/conftest.py`, from `US-03-T01`) paid
  for itself twice over.** Written because publication was measured attempting
  123 real `SOUL.md` writes, it then silently protected every Workflow test in
  this sprint — including `T06`'s, which adds a *second* publication trigger
  that nobody would have remembered to isolate.
- **Running the thing on a disposable install found what reading it could
  not.** `T06`'s two defects — two publication passes losing each other's
  block, and a confirmation pause with no way to resume the same run — were
  both invisible to a green test suite and both obvious within one real run.
  Neither would have been found by more unit tests, because both are about two
  real things happening near each other in time.
- **Escalating rather than reaching, four times, cost less than the
  alternative.** Every one of `ESC-075`–`ESC-078` was authorised essentially as
  written. The discipline also produced the sprint's most useful artefact: six
  file-list rules now live in `.claude/agents/decomposer.md`, where the work is
  done.

### What didn't work

- **A `## Files to Modify` list written from the layer the task is about keeps
  missing the crossing point.** Four escalations, three of them this exact
  shape: the sixth `artifact_*.py` module (`ESC-076`), the fixture file whose
  test data predated a new save-time rule (`ESC-075`), the shared union's
  declaration site and every exhaustive map over it (`ESC-078`, a verbatim
  repeat of `ESC-070` one story later). Root cause, now named: the list is
  written from where the code will be *typed*, not from where it will be
  *switched on* or *invalidated*.
- **A rule recorded only in `ESCALATIONS.md` is not recorded.** `ESC-070` wrote
  the union rule correctly and in full, and it recurred one story later anyway.
  `ESCALATIONS.md` is a log of what happened; nobody opens it while writing a
  file list.
- **`MEMORY.md` is 86 KB against its own 40 KB budget, and rule 1 forbids
  appending while over — so this sprint filed none of its constraints.** Four
  separate tasks hit this and parked candidates in `REVIEW-QUEUE.md` instead.
  That is now a real cost, not a tidiness issue: the budget rule is doing the
  opposite of what it exists for, because the knowledge it blocks is exactly
  the hard-rule kind `MEMORY.md` is *for*. The compaction pass should be
  treated as blocking work, not background work.
- **A throwaway probe is a test, and `T04`'s was not treated as one** — a
  one-off measurement script planted a real artefact in the operator's real
  store. The rule that came out of it ("point `HERMES_HOME_PATH` and
  `SECOND_BRAIN_DATA_PATH` at scratch directories *before* running anything
  that writes") held for the rest of the sprint.
- **`git worktree` is not usable in this shared checkout.** `T07` tried one to
  establish a real before-render and got `fatal: Could not reset index file to
  revision 'HEAD'` — concurrent sessions are writing the index. Rolled back
  cleanly, but it cost a cycle.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Publication says what exists; the framework does it** — when a feature's
  correctness depends on an agent behaving in a particular order, put the order
  in a record the framework steps through and let the published text say only
  that the thing exists. Then "in order", "nothing skipped", "nothing invented"
  are assertions about bytes on disk. `ADR-034`, built in `T05`/`T06`.
- **Prove a file-preserving write by comparing bytes, on a real file, in a
  scratch install** — not by reading the splice logic. `T06`'s check is
  `after.replace(b"\n\n" + block, b"") == before` plus "a no-op pass leaves the
  mtime alone"; it catches CRLF drift, a lost final newline and a reordered
  section in one line. `BUG-093`/`BUG-092` are what happens when the same claim
  is argued from the code instead.
- **Two writers of one derived block must be serialised, and the guard must
  fail without the lock** — `T06` added a second publication pass over the same
  `SOUL.md` and the two silently dropped each other's block. The regression
  test was confirmed to fail with the lock replaced by a `nullcontext`; a
  concurrency guard nobody has watched fail is not a guard.
- **Bind a background pass to the install it was started for** — anything that
  writes an install's files from a thread nobody waits for should capture which
  install that was and abandon itself if it changed. The setup wizard can
  reconfigure the Hermes home at runtime, and a test sandbox is torn down the
  same way.
- **Run it on a disposable install before calling a task done** — a real
  `uvicorn` on a spare port with every path pointed at scratch, the real
  scripts deployed into a real profile, a real socket. Both of `T06`'s defects,
  and `T03`'s and `T05`'s confirmations, came from exactly this.
- **A runner that pauses must name what to come back to** — `--resume <run_id>`
  rather than "run it again". Restarting a multi-step operation to get past a
  pause re-performs everything before the pause.
- **When the obvious fix is in someone else's file, look for the in-scope
  reordering first** — `T06`'s publication pass reads the roster before the
  catalogues ("who am I publishing to?" before "what am I publishing?"), which
  is defensible on its own merits and also happened to keep two `Done` tasks'
  cost-pinning tests passing untouched. Disclose both reasons; do not let the
  second one be the hidden one.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Reciting an ordered procedure into a prompt and trusting it** — the
  rejected alternative in `ADR-034`, and the same prompt-only grounding
  `ADR-032` rejected one level up. If the text is load-bearing for ordering,
  the ordering is not enforced.
- **Writing a `## Files to Modify` list from where the code will be typed** —
  it will miss the switch-on site, the shared union's declaration, the
  exhaustive maps over it, and the fixtures a new save-time rule invalidates.
  Four escalations this sprint, three of them this.
- **Filing a durable rule in `ESCALATIONS.md` and nowhere else** — it recurred
  verbatim one story later. A decomposer rule belongs in
  `.claude/agents/decomposer.md`, a constraint in `MEMORY.md`, a sprint
  heuristic here.
- **Treating a one-off measurement script as exempt from the sandbox** — it
  writes to the operator's real store exactly as a test would.
- **Reaching for `git worktree` in this checkout** — concurrent sessions are
  writing the index and the reset fails.

### Open follow-ups

- **`MEMORY.md` compaction is now blocking real constraints from being filed.**
  Candidates parked in `REVIEW-QUEUE.md` across this sprint, including `T06`'s
  three (serialise two writers of one derived block; bind a background pass to
  its install; a paused runner names its resume handle) and the ones `ESC-078`
  recorded. Filed as `REVIEW-QUEUE.md` entries; nothing is in `MEMORY.md`.
- **`AgentManager.update()` writes the SOUL.md and then raises on an agent with
  no Section** (`TypeError` in `registry_writer.agent_dir()` for
  `section_id is None`). The block is published but reported as failed and the
  Registry mirror is skipped. Pre-existing since `REQ-SB-95-US-03-T01`, found
  by `T06`'s disposable install, out of scope to fix there. Filed as a `/bug`
  candidate in `REVIEW-QUEUE.md`.
- **`T05`'s confirmation-override question is still open and still
  unauthorised** — a step marked `needs_confirmation` over an Action that is
  not confirmation-required is refused. The one-parameter additive fix is
  written out in `REVIEW-QUEUE.md`; `T06` deliberately did not take it.
- **The two publication triggers now solve the same hazard two different
  ways** — `ActionManager` remembers its threads so a caller can join them;
  `WorkflowManager` does that *and* binds the pass to its install. Worth
  converging, in whichever direction the operator prefers. Noted in
  `REVIEW-QUEUE.md`.
- **`REQ-SB-95` has one story left** — `US-05` (entity resolution) in
  `SPRINT-090`, which has no edge in either direction with this sprint and is
  unblocked.
