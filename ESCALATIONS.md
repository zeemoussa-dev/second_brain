# ESCALATIONS

Append-only log of every backward pipeline step (re-spec, re-architect, re-plan)
and out-of-scope event. Never edit a resolved entry. Every resolved entry names a
concrete resolving artefact (story ID, ADR number, or commit hash).

Categories: `unclear-requirement | out-of-scope | new-dependency |
shared-interface-change | adr-deviation | unanticipated-file | oversized-story |
other`

<!-- Entry format:
## ESC-NNN: [Short description] — YYYY-MM-DD
**Category:** [category from list above]
**Trigger:** What caused the escalation
**Resolution:** What was decided
**Resolving artefact:** story-id / ADR-NNN / commit abc123
**Status:** Resolved | Open
-->

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 63 entries / 5,035 lines, 36 still `Open`, the oldest from
> 2026-08-11.
>
> **This one is a deliberate exception to the file's own rule.** It is designed
> append-only precisely so the record of backward steps survives; emptying it is
> the operator's call for a fresh build phase, not a change to that rule. The
> rule still stands for everything logged from here on.
>
> **Nothing is lost** — the full log is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:ESCALATIONS.md
> ```
>
> **The next id is `ESC-063`.** Ids are never reused; the historical ones are
> still referenced from stories, tasks and ADRs.

---

## ESC-063: `ADR-032`'s entity resolver and `ADR-022`'s Entities-plugin boundary disagree — 2026-10-16

**Category:** adr-deviation
**Trigger:** Specing `REQ-SB-95` (analyst, `/spec`) produced
`REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`, which cannot say which
repository it builds in. `ADR-032` (Accepted 2026-10-16) specifies entity
resolution as "ONE tag-keyed index, not one index per entity. A single artifact
groups every `customer/*` and `partner/*` tag" — written as framework work, and
spelt out nowhere as anything else. `ADR-022` (Accepted 2026-09-14) decides the
opposite boundary for exactly those concepts: "the Customer, Partner and
Opportunity code moves into a Entities plugin (`sb-plugins-entities`) together
with `Entities.md`, its Settings page, the company Skills and `company_index`",
and "Core never imports, names or knows a plugin", under the operator's own test
that *a second brain built for a CFO cares nothing about Partners and Customers*.
The contradiction is not theoretical: `Settings/Entities.md` is already reached
through `app/plugin_api.py`'s `register_seed_data_file()`, i.e. it is already
being handled as plugin-owned seed data, while `ADR-032` assumes a resolver that
reads it. The two readings land the work in different repositories, under
different `CLAUDE.md`/`MEMORY.md` contexts (`ADR-023`), with different answers to
whether a non-Customer/Partner install gets the feature at all.
**Resolution:** Operator, 2026-10-16: "Resolver is framework, Customer stays the
plugin." The framework ships a tag-keyed resolver generic over any `<namespace>/<slug>`
tag, naming no plugin and knowing nothing of Customers; a plugin registers its namespace
through the Plugin API, and the entities plugin registers `customer/` and `partner/`.
`REQ-SB-95-US-05` therefore builds in this repository as mechanism, with the namespace
registration belonging to `sb-plugins-entities`. `ADR-022` stands unamended -- core offers
a seam, the plugin fills it.
**Resolving artefact:** `ADR-035`
**Status:** Resolved

---

## ESC-064: `REQ-SB-95-US-02-T02` needs a file `T01` owns — save-time resolution makes one of `T01`'s own tests fail — 2026-10-16

**Category:** out-of-scope-file
**Trigger:** `REQ-SB-95-US-02-T02` adds `ADR-032`'s save-time implementation
resolution to `ActionManager.create()`/`update()`. `T01` (Done, commits
`4ecd43c`/`8fd50bb`) wrote `src/backend/tests/test_action_artifact_kind.py`
before that gate existed, and its `AC-01` round-trip test saves an Action
against `implementation={"skill": {"skill_id": "vault-search"}}`. `vault-search`
is catalogued in this repo and deployed to **no** Hermes profile
(`SkillManager().get_by_id("vault-search").deployed_to == []`, measured), so the
new gate correctly refuses that save and the `T01` test fails:

```
FAILED tests/test_action_artifact_kind.py::test_a_saved_action_round_trips_everything_the_operator_authored
ActionImplementationUnresolvedError: this Action's skill implementation does not
resolve on this install: skill 'vault-search' is not deployed on this install
```

`T02`'s `## Files to Modify` names only `action_manager.py`, `action.py` and the
new `tests/test_action_resolution.py`. `test_action_artifact_kind.py` is not in
it, so fixing the failure is an out-of-scope edit (Pipeline.md hard rule 5), and
the coder stopped rather than improvising a change to a `Done` task's test.

**The two constraints are jointly unsatisfiable without a human**: "`AC-02`
refuses a catalogued-but-undeployed Skill" (locked, verified green) and "the
suite stays green" cannot both hold while that `T01` test stands. This is a
decomposition gap, not a disagreement about behaviour — nothing in `ADR-032`,
`ADR-033` or the story is contradicted, and `T02`'s own locked ACs (`AC-02`,
`AC-07`) pass on nine new AC-tagged tests.

**What the fix is:** `test_a_saved_action_round_trips_everything_the_operator_authored`
needs the same resolution-source monkeypatch the new `tests/test_action_resolution.py`
already uses (`deployed_skill_ids` / `app_route_table` / `UI_FEATURE_KEYS` on
`app.business.core.actions.action_manager`), or its `"vault-search"` swapped for
a really-deployed slug. Roughly five lines; it asserts nothing about resolution,
so `AC-01`'s meaning is untouched either way. Whoever authorises it should add
that file to `T02`'s `## Files to Modify` (or mint a `T02a`) rather than letting
a coder reach outside its scope by precedent.

**Resolving artefact:** `REQ-SB-95-US-02-T02` (2026-10-16)
**Status:** Resolved

---

## ESC-065: `artifact_import_conflicts.py` knows four kinds, so neither `index` nor `action` can be imported end to end — 2026-10-16

**Category:** out-of-scope

**Trigger:** Building `REQ-SB-95-US-02-T04` (Action as the sixth kind across the
inventory, resolver, export, import and secret scan). The task's `## Files to
Modify` names `artifact_import.py` — where `_deploy_action` now lives — but not
`artifact_import_conflicts.py`, which sits upstream of it and is the gate every
real import passes through first.

Measured directly on this install, 2026-10-16:

```
kinds known to detect_conflicts: ['agent', 'pipeline', 'skill', 'template']
index  -> ValueError: unrecognized artifact kind 'index' -- expected one of
          ['agent', 'pipeline', 'skill', 'template']
action -> ValueError: unrecognized artifact kind 'action' -- expected one of
          ['agent', 'pipeline', 'skill', 'template']
```

`_MANAGER_BY_KIND` in that module raises for any kind outside its four, and both
`preview_import()` and `commit_import()` call `detect_conflicts()` on the WHOLE
manifest before deploying anything. So a bundle containing a single `action`
entry — or a single `index` entry — fails as a whole, and no other artifact in
it is imported either.

**This is pre-existing, not introduced here.** `index` joined the kind set on
2026-09-06 (`ADR-019`) and the same file was never extended then; the
`tests/test_index_artifact_kind.py` precedent verifies the import side by calling
`artifact_import._deploy_one` directly, which is exactly the call that bypasses
this gate, so the gap has never shown up in the suite. `T04` followed that same
precedent (`Learnings.md` 2026-09-05, "Fixing an out-of-scope bug in the task
that found it" — finding a bug is not authority to fix it inside someone else's
scope), so `T04`'s own locked ACs (`AC-04`, `AC-05`) are verified and green and
nothing was improvised into a file it does not own.

**Consequence if left:** `Action` and `Index` are exportable and deployable but
not importable through the real `/artifacts/import/{preview,commit}` routes. The
operator sees a failed import of the whole bundle, not a skipped kind.

**What the fix is:** add `"index": IndexManager` and `"action": ActionManager` to
`_MANAGER_BY_KIND` in `src/backend/app/business/logic/artifact_import_conflicts.py`
— two lines plus two imports; both Managers already expose the `get_by_id(id)`
that module calls, and `ActionManager.get_by_id` already answers `None` for an
unknown id. It needs a task that owns that file (a small `T04a`, or adding the
file to `REQ-SB-95-US-04-T04`, which extends these same files for `Workflow`),
plus an AC-tagged test driving `commit_import` rather than `_deploy_one`.

**Resolution (2026-10-16):** A new task was minted to own the file —
`REQ-SB-95-US-02-T07`, "The import conflict gate knows every artifact kind, not
four", in `SPRINT-087`. `_MANAGER_BY_KIND` now maps `index → IndexManager` and
`action → ActionManager` (both already exposed the `get_by_id` the gate calls),
and the stale "matching `sbf_archive`/`artifact_export`'s own 4-kind vocabulary"
comment above the map — the assumption that caused this — was corrected in the
same change. The guard is unchanged: an unknown kind still raises, still naming
the accepted kinds. Four AC-tagged tests were added to
`src/backend/tests/test_action_artifact_kind.py`, all four driving
`preview_import`/`commit_import` on a real mixed-kind `.sbf` rather than
`_deploy_one`, as this entry asked. Verified both ways: the four fail against the
pre-fix map and pass against the fix; backend suite 432 → 436 passing.
`REQ-SB-95-US-02-T04`'s `gate: flagged`, which existed solely for this entry, is
cleared (its `status` was and remains `Done`).

**Still true, not fixed here:** `Implementation/Architecture/architecture.md`
§*Adding a Kind — the Measured Touch Points* still lists five files and folds
conflict detection into its `artifact_import.py` bullet, so it does not name
`artifact_import_conflicts.py` as a touch point of its own. `MEMORY.md`
(2026-10-16, "Adding an artifact kind means six files, not five") carries the
rule in stronger form, so `REQ-SB-95-US-04`'s `Workflow` author has it; the
architecture file is outside `T07`'s `## Files to Modify` and was left untouched.

**Resolving artefact:** `REQ-SB-95-US-02-T07`, commit `b2b09fe`
**Status:** Resolved

---

## ESC-066: `REQ-SB-96` is written on a premise the code contradicts — the framework already writes into the Hermes install, and already computes Skill drift — 2026-10-17

**Category:** unclear-requirement

**Trigger:** Specing `REQ-SB-96` (analyst, `/spec`, 2026-10-17). The requirement's
Finding 4 states "**the framework cannot deploy at all**… The framework's Hermes
surface (`hermes_router.py`, `hermes_agents_router.py`, `skills_router.py`) is
**entirely read-only**", and its *Worth knowing before choosing* states "this is
the **first time** the framework would *write* into the Hermes install; everything
it does there today is read-only. That boundary is worth crossing deliberately,
with an ADR."

Read directly from the repository on 2026-10-17, both statements are inaccurate as
statements of fact:

- `app/hermes/skills.py::HermesSkills.create/update/delete` write and delete under
  `<HERMES_HOME>/profiles/<profile>/skills/<category>/<slug>/`.
- `app/hermes/profiles.py::HermesProfiles.write_soul` writes `SOUL.md` into a
  profile; `business/core/agents/agent_manager.py` calls it on create and update.
- `app/hermes/cli.py::create_profile` / `create_cron_job` create profiles and cron
  jobs on the install.
- `business/core/skills/skill_manager.py::deploy/undeploy/delete` already push and
  remove a Skill's real content to and from a real profile, refreshing the
  install's shared managers first (`data_access/skills.py::deploy_shared_managers`
  writes into `<HERMES_HOME>` too).
- `SkillManager.check_deployment_drift()` **already computes a drift report** with
  `missing | stale | modified | current` per skill/profile pair.
- The opposite direction also exists: `reconcile_deployed_to(dry_run=…)` and
  `sync_from_hermes()` pull the install's reality back into the framework.

What is genuinely true is narrower, and is what the two stories were written
against: **none of it is exposed** — nothing under `app/api/` mentions deploy or
drift, `check_deployment_drift`'s only caller in the repository is
`tests/test_versioning.py`, and there is no screen. And the drift it does compute
is Skills-only, iterates the untrustworthy `deployed_to` claim rather than the
install's real profiles, and never reads the install's own
`<HERMES_HOME>/skills/<tool>/<slug>/` tree — which is exactly the PRD's own
Finding 2.

**Why this is escalated rather than quietly corrected:** it changes what the work
is. "Build the first write path, behind an ADR about crossing the boundary" and
"surface, widen and correct write paths that already exist" produce different task
splits, different risk, and a differently-scoped ADR. It also means the write
boundary this ADR is supposed to guard was crossed some time ago without one, which
the operator should know independently of this requirement.

**Consequence if left:** the architect at `/plan-tasks` writes an ADR about
crossing a boundary already crossed, and a second deployment implementation is
built beside `SkillManager.deploy()` — the duplicated-copies failure mode
`REQ-SB-96` exists to end.

**Resolution:** Open. The two stories
(`REQ-SB-96-US-01`, `REQ-SB-96-US-02`) are written against the code as measured, not
against the premise, and both record this entry.

**Resolving artefact:** —
**Resolution (2026-10-17):** the premise was corrected in `Documentation/PRD.md` (commit `671b4bd`) -- Finding 4 now states that `SkillManager.deploy/undeploy` and `check_deployment_drift()` already exist and already write into `<HERMES_HOME>`, and names the four real gaps: nothing exposes them, they are Skills-only, they iterate the untrustworthy `deployed_to`, and they never read the install's own `skills/` tree. The operator confirmed the smaller job ("surface and correct what exists") and settled the open default in the same pass: the framework wins for `missing` and `stale`, and a `modified` copy is refused rather than overwritten.

**Resolving artefact:** `REQ-SB-96` PRD correction (`671b4bd`) + operator decision, 2026-10-17

**Status:** Resolved

---

## ESC-067: `REQ-SB-97`'s mail-sending bullet asks for the reversal of a hard `MEMORY.md` constraint — left unspecced rather than specced around — 2026-10-17

**Category:** unclear-requirement

**Trigger:** Specing `REQ-SB-97` (analyst, `/spec`, 2026-10-17). Its fourth
**What is wanted** bullet asks for "an explicit capability the operator grants,
scoped to internal recipients", and its Acceptance paragraph requires that "an
Action the operator has granted mail to can be performed by a named agent against
an internal address".

`MEMORY.md` (2026-09-07) records the opposite as a framework hard rule: *"The email
capture pipeline is READ-ONLY, and stays read-only even when the token would permit
more… capture reads mail and writes only to the vault, never back to the mailbox.
Concretely, no `sendMail`, no flag/move/delete, no draft creation — every Graph
call stays a GET… an agent that can send mail as the operator is a different risk
class from one that files notes, and nothing in this product needs it."* The PRD
itself acknowledges this, citing the Action Center plugin's README: "every pipeline
on this install is deliberately read-only against the mailbox. That is an explicit
operator decision, not a feature to add quietly."

The analyst may not edit `MEMORY.md` and will not write acceptance criteria that
presume a reversal the operator has not made. The bullet is therefore **not
specced**: `REQ-SB-97-US-01` covers the requirement's per-agent performability and
deploy-state bullets, and records the mail grant in its `## Non-Goals` pointing
here.

**Consequence if left:** `REQ-SB-97` is partially covered. The operator's literal
example ("Hermes understands it can send an email for internals") remains
undeliverable until the decision is taken — which is the correct outcome for a
deliberate read-only posture, but it must be a decision rather than an omission.

**Resolution:** Open — awaiting an explicit operator decision, logged in
`REVIEW-QUEUE.md`. If granted, it needs `MEMORY.md` amended by its owner (not by an
agent), the grant's scope written down where the read-only decision is recorded, and
a new story (`REQ-SB-97-US-02`); it is not an edit to `REQ-SB-97-US-01`.

**Resolving artefact:** —
**Resolution (2026-10-17):** granted, scoped to internal recipients. Asked as a direct question rather than taken from the batch approval, because reversing a hard rule inside a blanket "approve all" is not a decision. `MEMORY.md` now carries the exception beside the 2026-09-07 rule it narrows (commit `4a427c9`): the capture pipeline stays read-only and every Graph call in it stays a GET; a single operator-granted Action may send to internal addresses, with the grant visible on its own screen. Builds as `REQ-SB-97-US-02`.

**Resolving artefact:** `MEMORY.md` amendment (`4a427c9`) + operator decision, 2026-10-17

**Status:** Resolved

## ESC-068: Everything planned before the Hermes pivot is cancelled — 2026-10-17

**Category:** out-of-scope

**Trigger:** Asked whether all sprint tasks were done, the real answer was 46 not
Done — and two of the open sprints turned out to predate the Hermes pivot by two
months. The operator's decision: "Anything Before Hermes is Cancelled".

**What was cancelled.** Everything created before 2026-08-20 that never reached
`Done`: **2 sprints** (`SPRINT-039` real-time agent activity pulses, `SPRINT-059`
full vault migration), **7 stories** (`REQ-SB-23-US-01`, `REQ-SB-24-US-01`,
`REQ-SB-30-US-01`, `REQ-SB-36-US-02`, `REQ-SB-42-US-01`, `REQ-SB-59-US-01`,
`REQ-SB-64-US-01`) and **11 tasks**. Nothing `Done` was touched; each artefact
keeps its previous status and the reason in its own body.

**Why it is right rather than tidy.** All of it assumed the retired model: Hub-routed
pipelines, the old agent model's pulses and per-agent token accounting, and capture
run by the framework. `SPRINT-059`'s two survivors are the clearest case —
`recapture_outlook_history()` re-runs Email/Meeting capture from
`app/business/vault_migration.py`, which is Hermes' job now, and
`regenerate_customer_notes()` targets the old OKF shape rather than today's hub
notes.

**`Cancelled` is a new terminal status**, added to `Implementation/Pipeline.md` and
`CLAUDE.md` in the same change. Prose alone would not have held: commands act on
`status:`, so a cancelled sprint left at `Ready` is one argument-less
`/implement-sprint` away from being built by a command doing exactly what it was
told.

**Also found, not cancelled:** `SPRINT-024` is marked `Done` while
`REQ-SB-36-US-02-T04` sat at `Draft` inside it — the sprint was closed over an
unfinished task. That task is pre-Hermes and is cancelled here, which settles the
inconsistency without rewriting a `Done` sprint's history.

**Resolving artefact:** operator decision, 2026-10-17
**Status:** Resolved

## ESC-069: `app/api/actions_router.py` carries the Action catalogue onto the screen but belongs to no remaining task — plugin attribution stops at the Manager — 2026-10-18

**Category:** unanticipated-file

**Trigger:** Building `REQ-SB-95-US-02-T05` (plugin-contributed Actions). The task
delivers `AC-06` at the layer it owns — `ActionManager.get_all()` returns the
install's stored Actions plus the loaded plugins', each plugin entry carrying its
`plugin_id`, and both write paths refuse a contributed one. Measured against the
real HTTP surface afterwards, two things do not reach a client:

- **`GET /actions` drops the attribution.** The list route builds an explicit dict
  (`id`, `description`, `implementation_kind`, `status`, `reason`) and the detail
  route's response model is the `Action` entity, so `plugin_id` — carried by the
  `PluginContributedAction` the Manager composes — is serialised by neither.
  Observed: the plugin's Action *is* listed, resolves, and disappears on uninstall;
  it just cannot be told apart from the operator's own.
- **`PUT`/`DELETE` on a plugin Action raises out of the router.** The new
  `PluginContributedActionIsReadOnlyError` has no `409` mapping beside the two
  refusals `T03` already maps, so a refusal the Manager words carefully reaches the
  client as a 500.

`app/api/actions_router.py` is in **neither `T05`'s nor `T06`'s** `## Files to
Modify`. `T05`'s Out of Scope explicitly hands "showing the plugin attribution on a
screen" to `T06`, and `T06`'s own file list is frontend-only — so the one file that
joins them is unassigned. `T06`'s AC-tagged manual step 5 ("confirm its row renders
… shows the contributing plugin id, and exposes no edit/delete control") cannot pass
as written until it is.

**Resolution:** Not improvised. `T05` stopped at its own boundary, shipped `AC-06` at
the Manager and facade, and recorded the gap here. The fix is small and belongs to
one owner: add `plugin_id` to the `GET /actions` list payload (absent or `null` for a
stored Action) and map `PluginContributedActionIsReadOnlyError` to `409` alongside
the cardinality and resolution refusals.

**What is needed:** a human adds `src/backend/app/api/actions_router.py` to
`REQ-SB-95-US-02-T06`'s `## Files to Modify` (the cheapest route — `T06` is `Ready`,
not started, and already owns the screen that needs it), or mints a `T08` for it.

**Resolving artefact:** — (Open)
**Resolution (2026-10-18):** authorised by the orchestrator rather than re-planned. `src/backend/app/api/actions_router.py` is added to `REQ-SB-95-US-02-T06`'s `## Files to Modify`, scoped to exactly the two changes named in the escalation: carry `plugin_id` on the list response, and map `PluginContributedActionIsReadOnlyError` to 409. T06 is the last task in `SPRINT-087`, so there is no later owner to hand it to, and its own AC-tagged step cannot pass without it. Same shape as `ESC-064` on 2026-10-16 — the task's boundary is widened explicitly instead of a coder reaching past it by precedent.

**Resolving artefact:** `REQ-SB-95-US-02-T06` scope extension, 2026-10-18

**Status:** Resolved

## ESC-070: widening `ArtifactKind` breaks every exhaustive `Record` over it, and one of them belongs to no task — 2026-10-18

**Category:** unanticipated-file

**Trigger:** Building `REQ-SB-95-US-02-T06`. Its `## Files to Modify` authorises the
`ArtifactKind` union gaining `'action'` ("the `ArtifactKind` type, if the union lives
there") and names `SettingsArtifactsPage.tsx` as the other consumer. There is a
third: `src/frontend/src/features/settings/ArtifactExportModal.tsx` declares its own
`KIND_LABELS: Record<ArtifactKind, string>`, and a `Record` keyed by a union is
exhaustive — the moment the union grew, that file failed `TS2741` and `tsc -b` with
it. A broken `tsc -b` is not a local inconvenience in this repo: it blocks every
plugin publish and install, which is the same failure a `CHANGELOG` entry already
records ("the frontend compiles again, which had blocked every plugin publish and
install").

**Resolution:** The one-line `action: 'Action'` entry was already in the working tree
when this task reached the commit — authored by a parallel session unblocking its own
build, not by this task. It is committed together with the union that requires it
(`b590b1a`), because committing either alone leaves a clean checkout broken in one
direction or the other. The orchestrator confirmed this placement explicitly. No
other change was made to that file.

All five `Record<ArtifactKind, …>` / `ArtifactKind[]` sites were then audited rather
than assumed: the export modal, and `SettingsArtifactsPage.tsx`'s `KIND_LABELS`,
`KIND_ORDER`, `byKind<T>()` and `SelectionState`. The last three derive from
`KIND_ORDER`, so adding the kind to `KIND_NAV` alone would have compiled and then
silently dropped every Action from the page — the same shape as the 2026-09-06 Index
regression that `byKind()`'s own comment exists to prevent.

**What is needed:** nothing to unblock the build. Worth a human's note only as a
decomposition lesson: a task that widens a shared union owns every exhaustive map
over it, and a `## Files to Modify` written from the union's declaration site will
miss them.

**Resolving artefact:** commit `b590b1a`
**Status:** Resolved

## ESC-071: the backend's `UI_FEATURE_KEYS` is now one route stale — the Actions screen cannot be named as a `ui` implementation — 2026-10-18

**Category:** out-of-scope

**Trigger:** `REQ-SB-95-US-02-T06` adds a real front-end route, `/settings/actions`.
A `ui` implementation resolves against `UI_FEATURE_KEYS` in
`app/business/core/actions/action.py`, a tuple whose own comment states it is "the
front end's own route paths, **verbatim** from `src/frontend/src/App.tsx`". It no
longer is: saving an Action whose `ui` implementation names `/settings/actions` is
refused with "ui feature key '/settings/actions' is not registered in this app's
front end", for a screen that demonstrably exists.

**Resolution:** Not improvised. `action.py` is in no task's `## Files to Modify`
(`T01` owns it and is `Done`, and specs are append-only), and no locked AC in this
story needs that key — `AC-01`/`AC-02` were verified against other, already-listed
keys. The one-line addition was therefore deliberately not made.

Worth deciding rather than patching: the deeper issue is that a hand-maintained
mirror of another build's route table drifts by construction, and this is the first
measured drift. `http` implementations already resolve against the **live** route
table (`app_route_table()`), including plugin routes — the `ui` kind is the only one
reading a frozen list.

**What is needed:** a human either (a) mints a one-line task to add
`"/settings/actions"` to `UI_FEATURE_KEYS`, or (b) folds the wider question — how
the front end's registered feature keys stay true without a hand-edited tuple —
into `REQ-SB-95-US-03`, which is the story that gives a `ui` implementation its
meaning at the call.

**Resolving artefact:** — (Open)
**Status:** Open

---

## ESC-072: publication rewrites every agent's real SOUL.md, and the backend suite has no Hermes sandbox — the `REQ-SB-95-US-03-T01` trigger is built but not wired — 2026-10-18

**Category:** unanticipated-file

**Trigger:** `REQ-SB-95-US-03-T01` requires `ActionManager.create()/update()/delete()`
to republish the catalogue into every affected agent's context (`ADR-033`, the
`SkillManager.publish_section_access_map()` precedent). Publication writes a real
`SOUL.md` through Hermes for every agent whose block changes — and `["*"]` means
every agent on the install.

Nothing in `src/backend/tests/` sandboxes Hermes. The four existing Action test
files isolate the Action *store* and nothing else (`test_actions_api.py`'s own
docstring: "the Action store, so no test writes into this install's real
`<DATA_PATH>/data/Actions/`"), while the agent roster they publish to is the live
one — 41 real profiles on the machine this was built on.

Measured, not estimated. With the three write paths wired and a pytest plugin
intercepting the writes, `tests/test_actions_api.py`, `test_action_resolution.py`,
`test_action_artifact_kind.py` and `test_plugin_actions.py` attempted **123 real
`SOUL.md` writes across all 41 profiles**, plus 40 `Agent.json` writes, and took
**5m36s instead of ~2s**. Every one of those blocks would have named this install's
agents after fabricated test Actions (`capture-the-thread`, `refresh-the-index`),
and nothing would ever have removed them: the fake catalogue is gone when the run
ends, so no later republication can correct them. `pytest` is run constantly here
by several concurrent sessions.

**Resolution:** Not improvised, and the damage was never done — the blast radius was
measured behind an interceptor before the suite was ever run for real. Isolating
those four test files (or adding a suite-wide `tests/conftest.py` Hermes sandbox) is
outside this task's `## Files to Modify`, so:

- the publication block, the per-agent `allowed_callers` filtering, the idempotent
  replace-own-block behaviour and the roster-wide `publish_action_catalogue()` pass
  are **built, tested and committed** (`4af306a`) — `REQ-SB-95-US-03-AC-01` verified;
- the three call sites in `ActionManager` are **deliberately left unwired**, with the
  reason recorded in the function's own docstring, so the suite stays safe for every
  session sharing this checkout;
- `REQ-SB-95-US-03-T01` is therefore `Blocked`, not `Done`: `AC-08`'s "republished by
  `ActionManager` on every catalogue change" half is unverified.

This is also a real design signal for whoever answers it: those 123 writes took 5m36s
(~2.7s each), because `AgentManager.update()` does a full registry reload per agent.
Saving one `["*"]` Action in the UI would, as specified, cost ~110s and rewrite 41
profiles. A cheaper publication write may be worth deciding at the same time.

**What is needed:** a human decides (a) how the backend suite sandboxes Hermes writes
— a `tests/conftest.py` autouse fixture pointing `hermes_home_path` at `tmp_path`
would cover every present and future test, versus per-file agent isolation in the four
Action test files — and (b) whether publication keeps going through
`AgentManager.update()` or gets a narrower SOUL-only write. Then mint the follow-up
task that wires the three call sites and adds the trigger test (the spy test is
written and was removed from the committed file; it asserts one call each on create,
update and a real delete, and none on a no-op delete).

**Resolving artefact:** — (Open)
**Status:** Open

---
