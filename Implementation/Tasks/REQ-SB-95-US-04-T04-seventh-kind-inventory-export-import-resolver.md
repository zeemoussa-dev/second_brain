---
id: REQ-SB-95-US-04-T04
title: Workflow as the seventh kind across inventory, dependency resolver, export and import
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "RESOLVED 2026-10-18 (ESC-077 authorised, fixed in ab68176) — was: the unknown-kind guard test used `workflow` as its stand-in for an unsupported kind. Remains flagged for an optional skim of the scope-internal judgement calls in the Implementation Log, and for two MEMORY.md candidates deliberately not appended (budget rule): a negative test must pick an example nothing plans to build, and a throwaway probe is a test too. Nothing is blocked; T07 is unblocked."
phase: P2
depends_on: [REQ-SB-95-US-04-T01, REQ-SB-95-US-02-T04]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-04-T04 — The Seventh Kind's Measured Touch Points

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Land `workflow` as a real artifact kind in the inventory, the dependency
closure, export and import — including the new Workflow → Action → Skill edge —
so a Workflow can travel in a bundle and arrive runnable.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-02-T04` has already added the sixth kind to
  `artifacts_inventory.py`, `artifact_dependency_resolver.py`,
  `artifact_export.py`, `artifact_import.py` and `artifact_secret_scan.py`, and
  corrected the "only 5" header. **Re-read each real current file** — this task
  extends that change, it does not repeat it.
- `ActionCalls/` and `WorkflowRuns/` are instance data and are excluded from
  export (`ADR-033`/`ADR-034`).

**After / Outputs:**

- `artifacts_inventory.py` composes `WorkflowManager` as a seventh entry, header
  accurate.
- `artifact_export.py` gains `_PAYLOAD_FOLDER["workflow"] = "workflows"` and the
  payload branch writing `workflows/<id>/Workflow.json`.
- `artifact_dependency_resolver.py` gains an `elif kind == "workflow"` branch
  pulling in every Action its steps name, **recursing into those Actions' own
  implementation Skills**.
- `artifact_import.py` gains `_deploy_workflow` in the dispatch with conflict
  detection and the `_next_alternate_id` keep-both path.
- `artifact_secret_scan.py` covers the new `Workflow.json` bytes.
- Nothing under `ActionCalls/` or `WorkflowRuns/` is exportable.

---

## Files to Modify

- `src/backend/app/business/logic/artifacts_inventory.py`
- `src/backend/app/business/logic/artifact_dependency_resolver.py`
- `src/backend/app/business/logic/artifact_export.py`
- `src/backend/app/business/logic/artifact_import.py`
- `src/backend/app/business/logic/artifact_secret_scan.py`
- `src/backend/tests/test_workflow_artifact_kind.py` (extend — created by `T01`)

---

## Constraints

- Inherits from parent story.
- **No pre-existing artifact kind changes behaviour** — including `action`,
  which landed one task-chain earlier.
- `_PAYLOAD_FOLDER["workflow"] = "workflows"` stated explicitly, never
  `kind + "s"`.
- `ActionCalls/` and `WorkflowRuns/` stay out of export — a run is not a
  capability.
- **`Pipeline` untouched**: no Pipeline entry, behaviour, schedule or label
  changes as a side effect of adding the seventh kind.

---

## Tests

**Automated tests** — extend `src/backend/tests/test_workflow_artifact_kind.py`,
run with `pytest tests/test_workflow_artifact_kind.py` from `src/backend`.

1. `[REQ-SB-95-US-04-AC-04]` With Workflows present, assert
   `artifacts_inventory.list_all_artifacts()` returns entries with
   `kind == "workflow"` alongside all six pre-existing kinds.
2. `[REQ-SB-95-US-04-AC-04]` Snapshot the entries for the six pre-existing kinds
   with zero Workflows and again with Workflows present; assert they are
   identical.
3. `[REQ-SB-95-US-04-AC-05]` Assert
   `artifact_export._PAYLOAD_FOLDER["workflow"] == "workflows"`.
4. `[REQ-SB-95-US-04-AC-05]` Run `resolve_closure` on a selection of one
   Workflow whose steps name two Actions, one of them `skill`-implemented;
   assert the closure contains both Actions **and** that Skill, each with a
   `depends_via` naming what pulled it in.
5. `[REQ-SB-95-US-04-AC-05]` Export that Workflow, assert the payload carries
   `workflows/<id>/Workflow.json` plus both Actions and the Skill; import onto a
   clean monkeypatched store and assert every step of the imported Workflow
   resolves there.
6. `[REQ-SB-95-US-04-AC-07]` Assert a Pipeline's inventory entry, stored JSON
   and schedule fields are byte-identical before and after Workflows exist, and
   that no Pipeline appears under any `workflow` kind.
7. `[REQ-SB-95-US-04-AC-07]` Assert nothing from `ActionCalls/` or
   `WorkflowRuns/` is included in an export of everything.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-04]` With the backend running and a real Workflow saved,
   `GET /artifacts` and confirm the `workflow` rows appear beside the six
   existing kinds, every pre-existing row unchanged.
2. `[REQ-SB-95-US-04-AC-07]` Confirm the install's real Pipelines still list
   with their own steps and schedules, and that their Hermes cron jobs are
   untouched.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Seventh kind present in inventory, resolver, export, import and secret scan
- [x] Workflow → Action → Skill closure, recursing correctly
- [x] `_PAYLOAD_FOLDER["workflow"] == "workflows"`, stated explicitly
- [x] Import conflict handling works for Workflows
- [x] No pre-existing kind changed; Pipelines provably untouched
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — deliberately **not** updated; two candidates recorded in `ESC-077` and the
      `REVIEW-QUEUE.md` entry instead. See the Implementation Log.
- [x] `CHANGELOG.md` entry appended
- [x] `ESC-077` resolved under the authorised scope extension (`ab68176`) — the
      unknown-kind guard now picks an example nobody plans to build and derives
      its accepted-kinds assertion from the live map. Suite green.

---

## Out of Scope

- The `SettingsArtifactsPage` tab for the seventh kind — `T07`.
- Workflow runs — `T05`.

---

## Context / Notes

`architecture.md` → **§Adding a Kind — the Measured Touch Points** names the
exact edit per file and the genuinely new edges ("Workflow → every Action its
steps name (recursing into those Actions' own Skills)"). Compose every edit
around the real current file — these five modules will have just been changed
by `REQ-SB-95-US-02-T04`.

---

## Implementation Log

**2026-10-18 — Done.** Commits `2f91bb4` (six modules + 12 tests), `ab68176`
(the `ESC-077` scoped test fix). All three locked ACs verified; suite green.

Briefly `Blocked` on `ESC-077` between the two commits — see *The two scope
extensions* below. Nothing about the verification changed; the block was one
stale assertion in a `Done` task's test file, not an unverified AC.

### Baseline, and how to read the final numbers

| Point | Suite | Note |
|---|---|---|
| Session baseline, tree at `6724db8` | **634 passed, 0 failed, 1 warning** (37.7s) | The one warning is the pre-existing `starlette/testclient.py` `anyio.abc.BlockingPortal` deprecation. **All three known order-dependent tests passed** — `test_health_check.py::test_health_reports_the_commit_the_running_code_was_loaded_from`, `test_marketplace_source.py`, `test_marketplace.py::test_install_repairs_a_plugin_left_with_only_its_bytecode_cache`. |
| After `2f91bb4` (`ESC-077` open) | **654 passed, 1 failed, 1 warning** (36.8s) | The one failure was `ESC-077`. |
| **Final, after `ab68176`** | **655 passed, 0 failed, 1 warning** (44.5s) | Same single pre-existing warning; no new ones. |

The arithmetic is 634 + 9 + 12 = 655 collected. The **9** are not mine: the
concurrent `REQ-SB-95-US-01-T01` landed `tests/test_operator_profile.py`
(commit `b4a4343`) between the baseline and the final run — verified by
`git diff --stat 6724db8..HEAD` and by counting that file's test functions. The
**12** are this task's. `ab68176` changed an existing test rather than adding
one, so the collected count is unchanged by it.

**One flake observed and run down, not mine.** The first full run after
`ab68176` reported `test_marketplace.py::test_uninstall_never_deletes_outside_the_plugin_folders`
failing on a `PermissionError` out of `pathlib.py:1188`. It passes alone (that
file: 28/28) and the immediately following full run was clean at 655/0, so it is
the same Windows file-locking/ordering family as the three known flakes the
sprint already tracks — plausibly aggravated by the concurrent session writing
into the untracked `src/marketplace/entities/1.3.0/` and `src/marketplace/my-day/1.7.1/`.
Recorded rather than ignored, since it is a *fourth* member of that family and
the three known ones are named per-task on the assumption the list is complete.

### Verification — automated mode, `cd src/backend && .venv/Scripts/python.exe -m pytest tests/test_workflow_artifact_kind.py`

All 12 new tests sit under the `-- The seventh kind across the artifact
machinery --` banner, extending the file `T01` created. File total 9 → 21, all
21 passing (0.98s).

| Tests step | AC | Test | Observed |
|---|---|---|---|
| 1 | `AC-04` | `test_the_inventory_lists_workflows_as_a_seventh_kind` | **Pass.** The `workflow` rows are exactly `[{kind, id, name, description}]` with `name == id`, and the kind set is all seven. |
| 2 | `AC-04` | `test_the_seventh_kind_changes_nothing_about_the_other_six` | **Pass.** The six pre-existing entries are equal as a **full entry list**, not a count, with zero Workflows and with two present. |
| — | `AC-04` | `test_a_kind_with_no_workflows_is_an_absence_not_an_omission_or_an_error` | **Pass.** An install with no Workflows reads the inventory successfully, has no `workflow` rows, and still returns all six others. (Extra — the Action precedent's third inventory test, which the decomposer's steps did not name but which is where an "absence vs error" regression would land.) |
| 3 | `AC-05` | `test_the_payload_folder_is_stated_not_naively_pluralised` | **Pass.** `artifact_export._PAYLOAD_FOLDER["workflow"] == "workflows"`, stated outright in the literal. |
| 4 | `AC-05` | `test_a_workflow_pulls_every_action_its_steps_name_and_their_skills` | **Pass.** Closure over one Workflow with two steps = `{workflow, action:list-team-actions, action:send-mail, skill:vault-search}`. `depends_via` one hop at a time: `"workflow:mail-me-the-team-list (step collect)"`, `"...(step send)"`, and `"action:list-team-actions (skill implementation)"` for the Skill. The `ui`-implemented Action adds nothing further. |
| 5 | `AC-05` | `test_an_exported_workflow_travels_with_its_actions_and_arrives_runnable` | **Pass.** A real `.sbf` carries `workflows/<id>/Workflow.json`, both `actions/<id>/Action.json` and `skills/vault-search/SKILL.md`; manifest names all four. Imported onto a cleared store, step order, ids, confirmation flags, inputs and the report's `include_step_ids` all survive, and **every step's `action_id` is in the receiving catalogue** — "arrives runnable" asserted as resolution against the catalogue, not as the presence of files. |
| — | `AC-05` | `test_the_secret_scan_covers_a_workflow_steps_inputs` | **Pass.** An `sk-`-shaped token in a step's `inputs` is found at `workflows/call-the-provider/Workflow.json`, and `apply_decisions` redacts it through the export's own `_text_content_for_scan` output — so scanner and export agree on `file_path:line`. The step's other input is untouched. |
| — | `AC-05` | `test_importing_a_workflow_whose_id_exists_never_silently_overwrites` | **Pass.** All four conflict branches: undecided → `failed` naming the missing decision, store unchanged; `skip` → unchanged; `keep_both` → `mail-me-the-team-list-imported` beside the original, both intact; `overwrite` → replaced. |
| — | `AC-05` | `test_an_imported_workflow_naming_an_unknown_action_is_refused_at_the_first_save` | **Pass.** Lands with its definition intact, and the first `update()` raises `WorkflowStepActionNotFoundError` naming `step 2` and `'an-action-this-install-never-had'` with `nothing was saved` — `T02`'s own sentence, unreworded. |
| 6 | `AC-07` | `test_a_pipeline_is_byte_identical_before_and_after_workflows_exist` | **Pass.** The stored `pipelines/morning-sweep.json` **bytes** are identical before and after Workflows are created and deleted; `list_pipeline_ids()` unchanged; `cron_job_id`/`cron_profile_id`/`schedule` unchanged; the whole re-read dict equals the original. A Workflow deliberately created under the Pipeline's own id `morning-sweep`, then deleted, converted nothing and removed nothing. |
| 6 | `AC-07` | `test_no_pipeline_is_relabelled_as_a_workflow` | **Pass.** The inventory half: `pipeline` ids and `workflow` ids are disjoint, and the Pipeline's own row is byte-equal to what it always was. |
| 7 | `AC-07` | `test_no_action_call_or_workflow_run_can_travel_in_a_bundle` | **Pass.** Real `data/ActionCalls/call-001.json` and `data/WorkflowRuns/run-001.json` written to disk first, so this is an absence from a bundle rather than of a folder. An export of everything the inventory lists carries the Workflow (positive control) and **no** payload path mentioning either store, no such manifest kind, and neither record id anywhere in the payload. Structural: no kind maps to either folder. |

### Manual steps

Both of the task's manual steps are subsumed by automated coverage and were not
re-run against the live install, deliberately — step 1 (`GET /artifacts` shows
`workflow` rows beside six unchanged kinds) is tests 1–2 plus `T03`'s already-
verified router, and step 2 (real Pipelines keep their steps and schedules, Hermes
cron untouched) is tests 6a/6b asserted on real stored bytes. The stronger reason
is that running either against the live install means writing a real Workflow
into the operator's own store, and nothing in this task needs that — see the
scratch-probe note below for what happened the one time this session touched it.

### What was decided, and why

- **Export pulls a Workflow's Actions in — as a dependency, not as disclosure.**
  `ADR-032` makes a step naming an uncatalogued Action invalid by construction and
  `T02` refuses exactly that save, so a bundle carrying the Workflow alone would
  deliver, to the receiving install, the one state this install refuses to create.
  The branch therefore `visit()`s every step's `action_id` as a real `"dependency"`
  and lets the existing `action` branch recurse into its implementation Skill and
  the `skill` branch into its Templates. Workflow → Action → Skill → Template falls
  out of three branches that already existed; nothing about finding an Action's
  Skill is duplicated here. Two steps naming the same Action resolve it once, via
  `visit()`'s own cycle-safety, keeping the first step's `depends_via` — one true
  reason, which is what that field is for.
- **Import does not re-run `T02`'s catalogue check, and that is a deferral, not a
  hole.** `_deploy_workflow` calls `WorkflowManager.import_workflow` and builds no
  second opinion. Re-running the rule here would be wrong twice: a bundle carries
  the Workflow *and* its Actions with no fixed deploy order between them, so the
  check would reject **complete** bundles; and it would need its own wording for a
  refusal that already has one, which is how two sentences for one rule drift
  apart. The gate fires at the door it belongs to — the first save — with `T02`'s
  sentence verbatim, and that is asserted rather than asserted-about. Exactly the
  line `import_action` and `import_workflow` already draw in their own docstrings:
  shape yes, resolution no.
- **The secret scan reads the whole `Workflow.json`, not a field allowlist.** The
  task said not to assume which fields carry a secret. Read directly,
  `WorkflowStep.inputs` is an unconstrained `dict[str, Any]` holding *either* the
  literal values an Action is called with *or* a mapping saying where each value
  comes from — stored verbatim, validated only at dispatch (`ADR-033`). A literal
  value is where a pasted token lands, so `inputs` is the real carrier. But
  `description`, `request_kind` and the report description are operator-authored
  free text in the same file, so an allowlist would buy nothing and would silently
  stop covering any field a later task adds.

### Scope-internal judgement calls

- **`request_kind` is not folded into the inventory row.** A Workflow has a real
  `description` and no `name`, so its id names it (Template/Action precedent).
  `request_kind` is a third, different fact — what an agent recognises an incoming
  intent as — and substituting it for a description the operator left blank would
  make the inventory say something they never wrote.
- **Fixtures write Action definitions straight into the in-memory store rather than
  calling `ActionManager.create()`.** `create()` resolves a `skill` implementation
  against this machine's really-deployed Skills and a `ui` one against registered
  feature keys, so going through it would make these tests pass or fail by accident
  of what the machine running them has installed — the instance-state dependency
  `ESC-064`/`ESC-075` were both about.
- **`T01`'s autouse `the_fixtures_action_ids_are_catalogued` was read first and left
  untouched.** It was extended by *reuse*, not by edit: every new fixture names only
  ids that tuple already catalogues (`list-team-actions`, `send-mail`,
  `append-capture`), so no new invented id exists to catalogue and the operator's
  real `<DATA_PATH>/data/Actions/` stays out of reach. Proven rather than asserted,
  per `T03`'s method: `SECOND_BRAIN_DATA_PATH` pointed at a freshly-created empty
  directory, the file re-run, **21 passed** — and that directory was then counted
  recursively and held **0 items**, so the run neither read nor wrote the
  configured data path at all, which is the stronger claim.
- **One extra test beyond the decomposer's seven steps per kind of risk** (the
  empty-install inventory case, the secret scan, the four conflict branches, and the
  import-then-save refusal). The last of these exists because the task text asked
  what import does about the gate; a decision recorded only in prose is not verified.

### The scratch probe that touched the real store — recorded, not hidden

`MEMORY.md` requires a new kind's import test to drive `commit_import`, not
`_deploy_one`. The pytest suite cannot call `commit_import` against the real
install, so that claim was measured with a one-off script instead. It ran against
**live settings**, and `commit_import` therefore wrote a real
`<DATA_PATH>/data/Workflows/mail-me-the-team-list/Workflow.json`. Caught
immediately, confirmed from its contents to be the scratch payload and not
operator data (empty `steps`, no `request_kind`, no `created_at`), and deleted
through `WorkflowManager.delete()`; `list_workflow_ids()` is `[]` again. The now-
empty `data/Workflows/` directory remains and is harmless — the store's own root,
which the kind creates on first save anyway. **The suite itself never touches the
real store.** The rule this earns — *a throwaway probe is a test too, and
`commit_import` against live settings is a write* — is a `MEMORY.md` candidate
recorded in `ESC-077`'s neighbourhood rather than appended (budget rule, below).

Measured before and after the `_MANAGER_BY_KIND` entry, reproducing `ESC-065`'s
own output shape:

```
before:  kinds known to detect_conflicts: ['action','agent','index','pipeline','skill','template']
         kinds artifact_export can emit:  [... same six ..., 'workflow']
         preview_import -> ValueError: unrecognized artifact kind 'workflow'
         commit_import  -> ValueError: unrecognized artifact kind 'workflow'
after:   both sets equal, seven kinds
         preview_import -> OK      detect_conflicts(workflow) -> OK      commit_import -> OK
```

### The two scope extensions, and what the pair of them cost

Both were found by reading before writing, reported rather than reached for, and
taken up only once authorised. Together they are one story: this task's file list
was written from `architecture.md` §*Adding a Kind*, which still names five
modules, and the sixth plus its tripwire were discovered by the work.

**`ESC-076` — `artifact_import_conflicts.py`.** The sixth
`business/logic/artifact_*.py` module that enumerates kinds; `_MANAGER_BY_KIND`
**raises** for an unlisted kind and both `preview_import()` and `commit_import()`
run it over the whole manifest, so omitting it fails the entire bundle rather
than one entry. Found by enumerating that directory before writing any code — the
rule `ESC-076` then landed in `.claude/agents/decomposer.md`. The change was held
to the authorised single entry: `"workflow": WorkflowManager`, its import, and the
map's comment date. `detect_conflicts()`'s contract is unchanged.

**`ESC-077` — one test in `test_action_artifact_kind.py`.** Taking up `ESC-076`
turned its first gate test green and its second one red:
`test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name` needed an example
of a kind the gate rejects and had picked `workflow` — which `_MANAGER_BY_KIND`'s
own comment described as "next" at the time it was written. The guard was never
broken; the example stopped being unknown. `ESC-076`'s authorisation had named
that file out of scope and said to escalate rather than reach, so the task
stopped there with the replacement written out, and resumed on authorisation.
Three changes, scoped to that one test (`ab68176`):

1. the manifest kind and its bundle member path moved to `hologram`, with a
   precondition asserting it really is absent from `_MANAGER_BY_KIND` — so the
   example cannot silently go stale again without the test saying so;
2. the message assertion followed it;
3. **the accepted-kinds assertion now iterates `_MANAGER_BY_KIND`** instead of a
   frozen six-kind tuple.

Point 3 is the part worth more than the unblock, and was treated as required
rather than as polish. A hand-maintained tuple must be extended for every future
kind, and the eighth kind's author who forgot would see this test fail for a
reason unrelated to the guard — rediscovering this entire sequence. Derived from
the live map, it extends itself. The test's meaning is unchanged and its green
sibling was not touched.

**What the pair cost and bought:** one round trip each, versus two silent edits
to a `Done` task's frozen artefacts. The second escalation existed only because
the first was honoured.

### `MEMORY.md` — deliberately not appended

`MEMORY.md` is 86 KB against the 40 KB budget its own rule 1 sets, and that rule
forbids appending while over budget. Two genuine candidates are recorded in
`ESC-077` and the `REVIEW-QUEUE.md` entry for a compaction pass to pick up:

1. **A negative test must pick an example nothing plans to build, or derive it from
   the live set** — never name the next roadmap item as its "unsupported" case.
   This is `ESC-077` exactly, and the code's own comment said `workflow` was next
   when that test was written.
2. **A throwaway probe script is a test too** — the no-real-data rule covers
   anything that runs against live settings, and `commit_import` is a write.

### Done

Every locked AC — `AC-04`, `AC-05`, `AC-07` — has an AC-tagged automated test and
a recorded observed outcome above. `ESC-076` and `ESC-077` are both Resolved, and
the suite is **655 passed, 0 failed**. `T07` (the Workflows screen), which waited
on this task, is unblocked; `T05` was never affected. `SPRINT-089` stays
`In Progress` — `T05`, `T06` and `T07` remain.

Left `gate: flagged` deliberately: nothing is blocked, but the two `MEMORY.md`
candidates above need a human to place them, and the scope-internal judgement
calls are worth a two-minute skim.

---

## Scope extension — 2026-10-18 (unblocks `ESC-076`)

**Added to `## Files to Modify`:** `src/backend/app/business/logic/artifact_import_conflicts.py`
— the `_MANAGER_BY_KIND` entry only.

That module is the **sixth** `business/logic/artifact_*.py` file that enumerates
artifact kinds; this task's list named the other five. Adding `workflow` to the
export side without it makes
`test_action_artifact_kind.py::test_the_gate_accepts_every_kind_the_export_can_emit`
fail — that test exists to catch exactly this drift, and it is doing its job. Add
`"workflow": WorkflowManager` to the map and that test goes green again; **do not edit
the test**, and do not touch anything else in the conflicts module.

`test_action_artifact_kind.py` itself stays out of scope. If it needs a change beyond
going green on its own, stop and escalate.

---

## Scope extension — 2026-10-18 (unblocks `ESC-077`)

**Added to `## Files to Modify`:** `src/backend/tests/test_action_artifact_kind.py`,
scoped to **`test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name` alone**
(lines ~746–767). Nothing else in that file, and no other test in it.

`ESC-076` named this file out of scope and said to escalate rather than touch it if it
did not go green. It did not, you escalated, and this is the answer: the guard is intact
and its chosen example stopped being unknown. Make the three changes your escalation
spells out —

1. the bundle's `kind` and its member path move from `workflow` to a kind nothing plans
   to build (`hologram` is fine),
2. the message assertion follows it,
3. **the accepted-kinds assertion iterates `artifact_import_conflicts._MANAGER_BY_KIND`
   instead of a frozen tuple.**

Point 3 is the part that matters beyond this task: the hard-coded tuple is what would
make the eighth kind's author rediscover all of this. Derive it from the live map.

Do not weaken the test, do not change what it means, and do not touch its sibling
`test_the_gate_accepts_every_kind_the_export_can_emit`, which is green.

Then mark `T04` `Done` with the suite green, and propagate status as normal.
