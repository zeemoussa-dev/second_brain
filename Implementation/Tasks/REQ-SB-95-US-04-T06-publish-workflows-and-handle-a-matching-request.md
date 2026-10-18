---
id: REQ-SB-95-US-04-T06
title: Publish Workflows into agent context and handle a matching request end-to-end
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger 1 — six scope-internal judgement calls are written up in the Implementation Log for a skim, two of them fixing defects found live rather than reasoned about (a lost update between the two publication passes, and a confirmation pause with no way to resume). AC-03 is verified; nothing is blocked and no ESCALATIONS.md entry was needed."
phase: P2
depends_on: [REQ-SB-95-US-04-T05, REQ-SB-95-US-03-T01]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-04-T06 — Publication + a Matching Request, End to End

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Tell the agent which Workflows exist and when each applies, so that a real
request of that kind starts a real framework-driven run — the agent recognises
the intent, it does not drive the order.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-03-T01` publishes the Action catalogue as a marker-delimited
  auto-generated block in each agent's SOUL.md, republished by `ActionManager`
  on every change.
- The run engine and its routes exist (`T05`) but nothing tells an agent a
  Workflow exists.

**After / Outputs:**

- The same published block (or a sibling block in the identical idempotent
  marker shape) lists the Workflows available to that agent: the kind of
  request each handles, and that the way to act on one is to start a run.
- `WorkflowManager.create()` / `update()` / `delete()` trigger republication,
  exactly as `ActionManager` does.
- The agent's runner path can start a run and step through it, receiving one
  step at a time.
- A request of a published kind is handled by the documented Workflow: the
  steps run in order, confirmation is asked at exactly the marked steps, and
  the report back is the one the Workflow defines.

---

## Files to Modify

- `src/backend/app/business/core/agents/agent_manager.py`
- `src/backend/app/business/core/workflows/workflow_manager.py` (the republish trigger)
- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/scripts/` (the runner Skill gains the start-run / next-step / report-outcome calls — same script family `REQ-SB-95-US-03-T05` created)
- `src/backend/tests/test_workflow_publication.py` (new)

---

## Constraints

- Inherits from parent story.
- **Publication says which Workflows exist and when each applies; the framework
  runs them** (`ADR-034`). Do not recite the steps into context and trust the
  model — that is the rejected alternative.
- Idempotent, marker-delimited, derived, never hand-edited — same discipline as
  the Action block; no duplicate blocks, no mutation of hand-authored text.
- The run engine remains the only thing that decides order. Nothing in the
  published text may be load-bearing for ordering, skipping or reporting.
- Existing agent behaviour is otherwise unchanged.

---

## Tests

**Automated tests** — `src/backend/tests/test_workflow_publication.py`, run
with `pytest tests/test_workflow_publication.py` from `src/backend`.

1. `[REQ-SB-95-US-04-AC-03]` Compose an agent's SOUL text with two Workflows
   published; assert each is listed with the kind of request it handles and the
   start-a-run instruction, between markers, with nothing outside the markers
   changed.
2. `[REQ-SB-95-US-04-AC-03]` Change the Workflow catalogue and assert
   republication happened automatically and idempotently (one marker pair, new
   content, surrounding text byte-identical).
3. `[REQ-SB-95-US-04-AC-03]` Drive the runner script through a published
   Workflow against the real app transport: assert it starts a run, receives
   step 1, reports its outcome, receives step 2, and that the final report it
   relays is the run engine's composed report — not text the script assembled
   itself.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-03]` With the backend running and the runner Skill
   deployed to a real Hermes profile, make a real request of the published kind
   in a real chat. Confirm, against the real `WorkflowRuns/<run_id>.json` on
   disk: the documented steps ran in the documented order, confirmation was
   asked at exactly the marked steps, the report back matches what the Workflow
   defines, and no extra step was invented or documented step skipped. Record
   the run file's step list verbatim in the Implementation Log.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Workflows published per agent in the idempotent marker shape
- [x] Republished automatically on every Workflow catalogue change
- [x] A real matching request runs the documented Workflow through the run engine
- [x] The report back comes from recorded outcomes, not from the model
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not appended**: `MEMORY.md` is 86 KB against the 40 KB budget its own
      rule 1 sets, which forbids appending while over. Three candidates are
      written out in `REVIEW-QUEUE.md` for the compaction pass.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Workflows screen — `T07`.
- Inferring or suggesting Workflows from history (story Non-Goals).

---

## Context / Notes

`architecture.md` → **§Workflow Runs — Ordered by the Framework** and
**§Catalogue Publication Into Agent Context**. `ADR-034`'s first decision bullet
("Publication says which Workflows exist and when each applies; the framework
runs them. The agent recognises the intent and starts a run; it does not drive
the order") is the exact contract.

---

## Implementation Log

**2026-10-18 — Done. `REQ-SB-95-US-04-AC-03` verified**, on 14 AC-tagged
automated tests plus a full manual run against a disposable install.

### What was built

- **A fourth auto-generated marker block in SOUL.md**
  (`agent_manager.py`): `<!-- BEGIN WORKFLOW CATALOGUE … -->` beside the
  specialists, index-guidance and Action blocks, with
  `publish_workflow_catalogue()`, `regenerate_workflow_catalogue_section()` and
  the same idempotent marker-replace shape. It names each Workflow, the kind of
  request it handles, its description and what it reports, and the three run
  routes. **It does not list the steps** — `ADR-034` puts the order, the
  confirmation points and the report in the run record, and a recital here
  would be a second, unenforced copy of them.
- **The republish trigger** (`workflow_manager.py`): `create()`, `update()` and
  `delete()` each fire `publish_workflow_catalogue_in_background()`, the same
  shape `ActionManager` uses, so editing the catalogue IS the whole operation.
  A refused save and a delete of an id this install never had fire nothing.
- **`run_workflow.py`**, beside `call_action.py` in the same shipped Skill. It
  knows a workflow id and nothing else: start a run, take ONE step, do what the
  step says, report what really happened, ask for the next, and finally relay
  the app's own composed report verbatim. It reuses `call_action.py`'s
  `caller_agent_id_of_this_profile()` and `perform_granted_skill()` rather than
  carrying a second copy of the honest-reporting rules.

### Verification

**Automated** — `pytest tests/test_workflow_publication.py` from `src/backend`,
14 tests, all tagged `[REQ-SB-95-US-04-AC-03]`.

1. **Tests block step 1 — the block itself.** Two Workflows published into one
   agent's SOUL.md: each listed with its `request_kind`, its description and
   its report definition, inside exactly one marker pair, with the three run
   routes and `caller_agent_id`; the two Action ids its steps name asserted
   **absent**; and `soul.replace("\n\n" + block, "") == HAND_AUTHORED_SOUL` —
   every other character identical. **PASS.** Also covered here: an agent that
   could not finish a Workflow is never told about it, an agent with no runnable
   Workflow carries no block at all (not an empty shell), and one profile Hermes
   refuses to write leaves the rest published.
2. **Tests block step 2 — automatic and idempotent republication.** Add, edit
   and delete a Workflow, each followed by a pass: one marker pair throughout,
   the block tracks every change, a pass with nothing to change returns `[]` and
   writes nothing, and the surrounding hand-authored text (including the final
   newline, `BUG-092`) is byte-identical from first publication to last.
   `create()`/`update()`/`delete()` each fire the trigger; a refused save and an
   unknown-id delete fire nothing; a save really reaches the agents through the
   real background thread with no explicit publish; and the save returns while
   the pass is still running. **PASS.**
3. **Tests block step 3 — the runner against the real app transport.** The
   shipped scripts are copied into a throwaway Hermes profile under `tmp_path`
   in the flat shape a deploy really writes, `run_workflow.py` is loaded from
   there (so it names itself from its own path) and driven through its real
   `main()`; `urllib.request.urlopen` is replaced by `TestClient`
   (`httpx.ASGITransport`, in process), so the routes, the run engine, the
   `ADR-033` gate and the ledger are the real ones and no socket is opened. The
   call sequence is asserted exactly: `run → next-step → outcome → next-step →
   outcome → next-step`. Step 1 is a `ui` Action (`pointed_at`), step 2 a
   `skill` Action the app AUTHORISES and the runner really performs in its own
   profile ("mailed the list to the operator" is the Skill's own stdout). The
   relayed report is parsed back out of the script's stdout and compared with
   the report the engine composes when asked again — **equal**. **PASS.**

**Manual step — a real matching request, against a disposable install.** A real
`uvicorn` on port **8019** with `VAULT_PATH`/`SECOND_BRAIN_DATA_PATH`/
`HERMES_HOME_PATH` pointed at a scratch directory; a real Hermes profile
(`cbo-agent`) with a hand-authored SOUL.md; the Actions and the Workflow created
over real HTTP; the two scripts copied into that profile; `python
run_workflow.py team-actions-by-mail` run as a real subprocess over a real
socket. **PASS**, exit 0. The published block appeared in the real profile's
SOUL.md on the save, with the Action block intact beside it (2996 bytes, one
marker pair each). The run record on disk, verbatim:

```
run 9934c8c710c94c75968e32a925781c06, workflow 'team-actions-by-mail', status: complete
  step_id=gather  position=1 action_id=list-the-teams-actions needs_confirmation=False status=done dispatch_outcome=pointed_at calls=1
  step_id=refresh position=2 action_id=refresh-the-index      needs_confirmation=False status=done dispatch_outcome=performed calls=1
```

Step 2 really ran the app's own `POST /vault-index/refresh` (HTTP 200,
`notes_indexed: 0` against the scratch vault). The report the script printed is
the engine's `compose_report()` output, `every_documented_step_done: true`.

**Manual step, confirmation half.** A second Workflow `tidy-then-archive` whose
step 2 is marked `needs_confirmation` over a confirmation-required Action:

```
run 4799e4bd775846909676ffd7dcd7b4d7, workflow 'tidy-then-archive', status: complete
  step_id=gather  position=1 action_id=list-the-teams-actions needs_confirmation=False status=done dispatch_outcome=pointed_at calls=1
  step_id=archive position=2 action_id=archive-the-mailbox    needs_confirmation=True  status=done dispatch_outcome=pointed_at calls=2
```

The first pass stopped at **exactly** the marked step (exit 2, "WAITING FOR THE
OPERATOR at step 'archive' (position 2)"), step 1 having run and nothing beyond
step 2 touched. `POST /actions/calls/<id>/confirm` then `--resume <run_id>`
finished the SAME run: step 1 was not re-run (one call id, not two), step 2
carries `ADR-033`'s two rows (the decision and the re-call that spends it), no
second run file was created, no step was invented and none skipped.

**Byte-for-byte proof, on a real file, measured not argued.** A scratch Hermes
home with a real SOUL.md carrying prose this app cannot read (`## Scope
boundary`, prose inside `## Scope`, a final newline), published into through the
real `AgentManager.update()` → `HermesProfiles.write_soul()`:

```
before : 190 bytes      after : 1680 bytes      block : 1488 bytes (+2 for the blank line)
after.replace(b"\n\n" + block, b"") == before : True
CRLF introduced : False      final newline kept : True      marker pairs : 1
second pass : []  -> file bytes identical AND st_mtime_ns identical
```

The same assertion is pinned in `test_publishing_into_a_real_profile_changes_only_the_block`.

**Suite.** Baseline before this task, same tree, its own file excluded:
**672 passed / 0 failed**. After: **686 passed / 0 failed** (+14, all mine). None
of the four known order-dependent tests failed in any of the four full runs. The
new file leaves an empty install empty: every store it touches (Actions,
Workflows, WorkflowRuns, the Action-call ledger, the Registry data path, the
Hermes home) is redirected into memory or onto `tmp_path` first, and the
operator's real `<DATA_PATH>/data/` has no `WorkflowRuns/` and no `SOUL.md`
written in the whole session (checked before and after).

### Two defects found live, and fixed here

Both were found by running the thing, not by reading it.

1. **Two publication passes over one SOUL.md lost each other's block.** On the
   disposable install, an Action save and a Workflow save seconds apart left the
   profile carrying the Action block and **no** Workflow block: each pass
   composes its new text from the agent it read when it started, so the second
   writer silently drops the first's work, and nothing restores it until the
   next change *of that kind*. Fixed with `_publication_lock` in
   `agent_manager.py`, taken by both passes — in scope (the file is in this
   task's list) and required by this task, which is what introduced the second
   writer. The regression guard
   (`test_an_action_pass_and_a_workflow_pass_never_drop_each_others_block`) was
   confirmed to **fail** with the lock replaced by a `nullcontext`.
2. **A confirmation pause had no way to resume.** The runner's first message
   told the agent to "run this script's run again", which opens a NEW run and
   performs every earlier step a second time — harmless for the `ui` step it was
   tested with, a duplicated operation for an `http` one. `--resume <run_id>`
   was added and the pause message now names it. Verified live, above.

### Scope-internal judgement calls (for a skim — none is an escalation)

1. **A Workflow is published to an agent only if that agent could run it end to
   end** — every step names a catalogued Action the agent may call, asked
   through the same `ActionManager.is_callable_by` the gate and the Action block
   use. The task's End State says "the Workflows **available to that agent**",
   and a Workflow has no `allowed_callers` of its own, so availability had to be
   derived from somewhere; deriving it from the steps' own Actions is the only
   source that cannot disagree with what the run would actually do. A Workflow
   with no steps is also excluded — `start_run()` refuses it.
2. **A `pointed_at` step is reported `done` by the runner**, with the app's own
   "RECORDED, NOT PERFORMED … tell the operator to go there" relayed verbatim.
   The run record keeps `dispatch_outcome: pointed_at` whatever is reported over
   it — `workflow_run._snapshot_step`'s own docstring anticipates exactly this —
   so the operator reading the record still sees that they are the one who does
   it. The alternative, stopping the run, would block every Workflow containing
   a `ui` step at that step forever.
3. **`publish_workflow_catalogue()` reads the roster FIRST and the two
   catalogues only if it is not empty.** An install with no reachable Hermes has
   nobody to publish to. Disclosed because it has a second effect: it is also
   what keeps two cost-pinning tests owned by `Done` tasks
   (`test_reading_a_workflow_costs_exactly_one_read`,
   `test_validating_a_save_reads_the_catalogue_once_…`) passing unchanged. With
   the catalogues read first, a Workflow save adds a deterministic 1 list + N
   reads and both tests go red — and the only fixes available then were editing
   two other tasks' test files or editing `tests/conftest.py`, i.e. an
   escalation either way. The reordering is defensible on its own merits and was
   taken for that reason, but the reader should know it also avoided that.
4. **`_publication_lock` was added to `publish_action_catalogue()`**, which is
   `REQ-SB-95-US-03-T01`'s code. The file is in this task's `## Files to
   Modify`; the defect is this task's own doing; and serialising only one side
   would not serialise anything.
5. **`_publish_into()` binds a pass to the install it was started for.**
   `hermes_home_path` is reconfigurable at runtime (`REQ-SB-89`'s setup wizard)
   and nothing waits for a publication pass, so a pass in flight across a
   reconfiguration would write one install's catalogue into another's profiles.
   It abandons itself and says so in the log instead.
6. **`SKILL.md` was not touched** — it is not under the `scripts/` folder this
   task's file list names. The new script is therefore documented to the agent
   by the published block itself ("`run_workflow.py`, beside the `call-action`
   runner in your own skills"), which is in scope and is where the agent reads.
   `test_skill_command_paths.py` is unaffected: it pins documented commands
   against deployed scripts, not the reverse.

### One pre-existing defect, reported and NOT fixed

`AgentManager.update()` writes the real SOUL.md and **then** raises
`TypeError: unsupported operand type(s) for /: 'WindowsPath' and 'NoneType'` in
`registry_writer.agent_dir()` whenever the agent has no Section
(`section_id is None`). The file write has already happened, so publication
reports the agent as *failed* and logs a stale-block warning while the block is
in fact published, and the Registry mirror is left behind. Observed on the
disposable install before its Registry was seeded; it affects the Action
catalogue identically and has since `REQ-SB-95-US-03-T01`. Out of scope here
(the crash is in `data_access/registry/writer.py`, the caller is `update()`'s
registry half) — logged in `REVIEW-QUEUE.md` as a `/bug` candidate.

gate: flagged 2026-10-18 — trigger 1 (six judgement calls above). Trigger 6 does
not apply: `AC-03` is verified. No `ESCALATIONS.md` entry: nothing outside this
task's `## Files to Modify` was changed, and the one place that nearly forced it
is written up as judgement call 3.
