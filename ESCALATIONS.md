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

**Resolution (2026-10-18, `REQ-SB-95-US-03-T05`):** option (b), and it arrived on
its own. `T05` ships the starter `report-unmet-request` Action, whose whole
meaning is "the app performs nothing about this, a human decides" — so it is a
`ui` implementation, and the one screen it can honestly name is the Actions page.
`action.py` IS inside `T05`'s own `## Files to Modify` (the whole of
`app/business/core/actions/`), so the one-line addition was made here rather than
left for a dedicated task: `af54a4c`.

**The deeper question is NOT resolved by that line** and is deliberately not
claimed to be: `UI_FEATURE_KEYS` is still a hand-maintained mirror of another
build's route table, and it will drift again the next time a screen is added.
`http` resolves against the live route table; `ui` is the only kind reading a
frozen list. Carried into `SPRINT-088`'s retro as an open follow-up.

**Resolving artefact:** `af54a4c` (the drifted key), `REQ-SB-95-US-03-T05`
**Status:** Resolved — the one stale key only; the drift mechanism stays open

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
**Resolution (2026-10-18):** both halves settled. (1) The orchestrator authorises `src/backend/tests/conftest.py` (new) into `REQ-SB-95-US-03-T01`'s `## Files to Modify` — a suite-wide autouse sandbox so no test can write a real `SOUL.md`. The four existing Action test files are NOT edited; the fixture is what makes them safe. (2) The operator decided the publish cost: **background publication, returning immediately**, following the vault index rebuild's existing pattern, accepting that an agent's SOUL may name the old catalogue for a few seconds. Publication still goes through `AgentManager` — the waiting moves, not the ownership. The measurement that forced the question (~2.7s per agent, so ~110s for an `allowed_callers: ["*"]` Action across 41 profiles) stands as recorded.

**Resolving artefact:** `REQ-SB-95-US-03-T01` scope extension + operator decision, 2026-10-18

**Status:** Resolved

---
## ESC-073: wiring `http` dispatch makes two tests in `test_action_invocation_gate.py` stop telling the truth — the file is outside `REQ-SB-95-US-03-T03`'s scope — 2026-10-18

**Category:** unanticipated-file

**Trigger:** `REQ-SB-95-US-03-T03` fills `dispatch_validated_action_call()` with
dispatch by implementation kind. Two of its three paths perform nothing by
definition (`ui` is pointed at, `skill` is authorised) and shipped without
incident. The third, `http`, is the one the app really performs — and the moment
it is wired, two tests written by `T02` the same day stop being true:

1. `test_a_valid_call_passes_the_gate_records_it_and_enters_dispatch_exactly_once`
   asserts `outcome == "not_dispatched"` and `"not implemented yet" in detail`.
   `T02`'s own Implementation Log calls that outcome **transitional** and assigns
   dispatch to `T03`, so this is the assertion `T03` was always going to replace —
   measured: it is the single failure, `assert 'performed' == 'not_dispatched'`.
2. `test_a_caller_outside_allowed_callers_is_refused_and_the_wildcard_admits_it`
   points its test Action at the **real** `POST /vault-index/refresh`. With
   dispatch live it still passes, silently, by really re-reading the operator's
   whole vault on every run of the suite — measured at **1.09s → 8.60s** for that
   one file. Several sessions run `pytest` here constantly.

`src/backend/tests/test_action_invocation_gate.py` is **not** in `T03`'s
`## Files to Modify` (written 2026-10-16, before that file existed).

**Resolution:** Not improvised, and nothing was damaged — the breakage was
measured behind the write/outbound interceptor before the suite was ever run with
it live, and the `http` branch was then left unwired rather than the out-of-scope
file being edited. So:

- the `ui` and `skill` paths, the single-use grant, `consume_single_use_grant()`
  and the ledger's `claim_call_once()` primitive are **built, tested and
  committed** (`e16013c`, `ab0ed44`) — 7 new AC-tagged tests, suite 490 → 497,
  0 failed;
- `_perform_http_implementation()` is **complete and proved by three of those
  tests driving it directly** — it performs the route in process over
  `httpx.ASGITransport` (no socket, so it cannot reach a backend on :8001), binds
  path parameters, treats only 2xx as `performed`, reports an honest failure
  otherwise, and refuses to dispatch at the call gate's own route rather than
  recursing endlessly;
- the seam's `http` branch keeps reporting `not_dispatched` — exactly what `T02`
  already shipped for every kind, so nothing regresses and nothing claims to have
  run — with the reason in the function's own docstring;
- `REQ-SB-95-US-03-T03` is therefore `Blocked`, not `Done`: `AC-02`'s
  "an http implementation is performed by the app" is proved at the unit the task
  owns and unproved end to end through `POST /actions/{action_id}/call`.

**What is needed:** authorise `src/backend/tests/test_action_invocation_gate.py`
into `T03`'s `## Files to Modify`. The change is small and is already specified:
(a) in the valid-call test, replace the two transitional assertions with
`performed` and the real result; (b) in the wildcard test, stop pointing a test
Action at the real `/vault-index/refresh` — `tests/test_action_dispatch.py`
already registers a harmless test-only target route that can be reused. Then one
line routes the seam's `http` branch to `_perform_http_implementation()`, and the
task's remaining two automated steps plus its manual loopback step can be run.

Worth deciding at the same time, because it is the one genuinely new design
choice here: **`http` is dispatched in process through `httpx.ASGITransport`
rather than over a loopback socket to `127.0.0.1:8001`.** That is deliberate —
"performed by the app" then means by THIS app, not by whatever is listening on
that port, and no test can reach the operator's running backend — but it is a new
technique in this codebase and is recorded as a judgement call in the task log.

**Resolving artefact:** — (Open)

**Resolution (2026-10-18):** authorised by the orchestrator. `src/backend/tests/test_action_invocation_gate.py` is added to `REQ-SB-95-US-03-T03`s `## Files to Modify`, scoped to the three changes this escalation names: two stale `not_dispatched` assertions T02 marked transitional and handed to T03, repointing the wildcard test off the real `POST /vault-index/refresh`, and the one line routing http to `_perform_http_implementation()`. The repointing matters beyond the task: with dispatch live that test made every suite run re-read the operator entire vault, 1.09s to 8.60s for one file. Fourth escalation in two sprints from a file joining two tasks and owned by neither (ESC-064, 069, 072, 073).

**Resolving artefact:** `REQ-SB-95-US-03-T03` scope extension, 2026-10-18

**Status:** Resolved

---

## ESC-074: the shipped starter Action is built and never seeded — `app/main.py` is the one place that would run it, and it is outside `REQ-SB-95-US-03-T05`'s scope — 2026-10-18

**Category:** unanticipated-file

**Trigger:** `REQ-SB-95-US-03-T05`'s `## Files to Modify` names
`src/backend/app/business/core/actions/` for "the shipped-starter mechanism,
**mirroring how Master Templates ship**". That mechanism has two halves, and only
one of them lives in that directory:

1. the shipped source plus the Manager method — built here:
   `business/core/actions/starters/report-unmet-request/Action.json`,
   `shipped_starters.py`, `ActionManager.seed_shipped_starters()` (`ce38963`);
2. the boot call that actually runs it. For Master Templates that is five lines
   in `app/main.py`'s lifespan, immediately above where this one would sit. That
   file is in no task's `## Files to Modify`.

Without (2) a fresh install never gets `report-unmet-request`, so `AC-05`'s
"the unmet request is recorded in the Action-call ledger" is true of the
mechanism and not of the product.

**Three in-scope alternatives were tried on paper and rejected, with reasons —
nothing was improvised:**

- **Compose the starter on read**, the shape a plugin's Action already uses
  (`_plugin_contributed()`). It needs no boot call at all, and it breaks a
  `Done` task's test: the starter is `allowed_callers: ["*"]`, so
  `test_an_agent_permitted_to_call_nothing_carries_no_block_at_all`
  (`T01`, `AC-01`) would find a block on the agent that must have none. That
  test replaces the Action **store**, which a composed entry bypasses by
  definition. Editing it is forbidden twice over — a `Done` task, and a file
  outside this scope.
- **Seed from `ActionManager.__init__()` or from `get_all()`.** Same failure for
  the same reason, plus it makes a read path write.
- **Compose into `get_by_id()` only**, so the gate finds it and publication does
  not. The gate would then accept an Action no agent was ever told about and no
  screen lists — the exact "the screen and the agent cannot disagree about what
  exists" property `ADR-033` ships this route for.

**Resolution:** the seed is built, tested and committed; the boot call is not
made. Everything else in `T05` is complete:

- the runner Skill (`catalog/actions/call-action/`) and 12 AC-tagged tests, suite
  525 → 538, 0 failed (`199d2dc`);
- `AC-02`, `AC-03`, `AC-04` and `AC-05` all verified end to end, including the
  live manual run of the shipped script over a real loopback socket against a
  disposable install on `127.0.0.1:8015` (never the operator's `:8001`), where
  the starter was seeded by calling its own shipped mechanism once;
- `REQ-SB-95-US-03-T05` is therefore `Blocked`, not `Done`.

**What is needed:** authorise `src/backend/app/main.py` into `T05`'s
`## Files to Modify` for exactly one addition, beside the Master Template seed it
mirrors:

```python
    try:
        starters = ActionManager().seed_shipped_starters()
        if starters["seeded"]:
            print(f"[startup] seeded starter Actions: {', '.join(starters['seeded'])}")
    except Exception as exc:
        print(f"[startup] ERROR: could not seed starter Actions: {exc!r}")
```

Two consequences to accept with it, neither hidden: the first boot after this
lands will publish the new Action into **every** agent's `SOUL.md` (it is
`["*"]`, and that is the point — an agent that is not told it exists cannot use
it), in the background, the way any catalogue change already does; and an
operator who deletes the starter gets it back on the next restart, which is the
same property `seed_shipped_masters()` has had since 2026-09-06.

**Resolving artefact:** — (Open)
**Resolution (2026-10-18):** authorised. `src/backend/app/main.py` is added to `REQ-SB-95-US-03-T05`'s `## Files to Modify`, scoped to the seed call beside the Master Template seed and nothing else. The three in-scope alternatives the coder worked through were correctly rejected -- composing on read breaks a `Done` task's test, and `get_by_id`-only composition hides an Action from every surface that should list it.

**This is the fifth escalation of one shape in two sprints** (`ESC-069`, `ESC-071`, `ESC-072`, `ESC-073`, `ESC-074`): `## Files to Modify` names where new code lives and not the one line that makes it run. Rather than authorise a sixth, the generator is fixed -- `.claude/agents/decomposer.md` now carries a standing rule to name the switch-on site, with these five as the evidence, and framework `MEMORY.md` records it.

**Resolving artefact:** `REQ-SB-95-US-03-T05` scope extension + decomposer rule, 2026-10-18

**Status:** Resolved

---

## ESC-075: save-time step validation makes six tests in `test_workflow_artifact_kind.py` fail — the file is outside `REQ-SB-95-US-04-T02`'s scope — 2026-10-18

**Category:** unanticipated-file

**Trigger:** `REQ-SB-95-US-04-T02` adds `ADR-034`'s save-time referential check to
`WorkflowManager.create()`/`update()`: a step naming an action id the catalogue
does not have is refused, naming the step and the id, before anything is written.
`T01` (Done, `4393124`) wrote `src/backend/tests/test_workflow_artifact_kind.py`
before that check existed, and every one of its step fixtures names an invented
action id — `list-team-actions`, `send-mail`, `append-capture` — which this
install has never catalogued. Six of its nine tests now fail, all on one cause:

```
FAILED tests/test_workflow_artifact_kind.py::test_a_saved_workflow_round_trips_its_ordered_steps_and_report
WorkflowStepActionNotFoundError: step 1 of this Workflow names action
'list-team-actions', which is not in this install's Action catalogue; nothing was saved
```

`T02`'s `## Files to Modify` names `workflow_manager.py`, `action_manager.py`,
`actions_router.py` and the new `tests/test_workflow_action_integrity.py`.
`test_workflow_artifact_kind.py` is not in it, so fixing it is an out-of-scope
edit (`Pipeline.md` hard rule 5), and the coder committed the correct code
(`d71630f`) and stopped rather than editing a `Done` task's test file.

**This is `ESC-064` again, one story later and one kind along.** There, `T02`'s
new save-time *resolution* gate refused `T01`'s own Action fixture; here `T02`'s
new save-time *referential* check refuses `T01`'s own Workflow fixtures. Same
cause, same shape, same five-line fix — the generator rule added on 2026-10-18
covers the missing **switch-on** site, and this is its mirror image: the
**fixture** site, the place a `Done` sibling test stops being true the moment a
new save-time gate lands. The file-list check for a missing switch-on site was
performed before any code was written here and correctly found none
(`actions_router.py` was already named; `ActionManager.delete()` has exactly one
caller and it is that router).

**There is no in-scope alternative, and the constraints are jointly
unsatisfiable without a human.** `AC-02` is locked as a refusal at save, in the
Manager, with nothing written — the decomposer's own test step asserts
`write_workflow_json` was never called — so the check cannot move to the router
or to a later audit without weakening it. The six failing tests assert order,
minting and cost; none of them asserts anything about the catalogue, so their
meaning is untouched by the fix.

**A second reason the fix is needed even if those ids existed:** that file
monkeypatches the *Workflow* store only, so with this gate live its saves now
consult the operator's **real** `<DATA_PATH>/data/Actions/` store. A test about
step order would pass or fail by accident of what the machine running the suite
has catalogued — the exact instance-state dependency `ESC-064`'s resolution
called out, and the reason that file's Action equivalent has carried an autouse
`_implementations_resolve` fixture since 2026-10-16.

**What the fix is:** one autouse fixture in
`src/backend/tests/test_workflow_artifact_kind.py`, mirroring the one
`tests/test_action_artifact_kind.py` already has, so the three invented ids are
catalogued for that file and for no other — roughly six lines, nothing else in
the file touched:

```python
@pytest.fixture(autouse=True)
def the_fixtures_action_ids_are_catalogued(monkeypatch) -> None:
    """T02's save-time referential check (ADR-034) refuses a step naming an
    uncatalogued Action. These tests are about order, step identity and cost,
    not about what this install has catalogued -- and without this they would
    consult the operator's real Actions store."""
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.ActionManager.get_all",
        lambda self: [SimpleNamespace(id=action_id) for action_id in
                      ("list-team-actions", "send-mail", "append-capture")],
    )
```

Whoever authorises it should add that file to `T02`'s `## Files to Modify` (or
mint a `T02a`) rather than letting a coder reach outside its scope by precedent,
which is what `ESC-064` decided for the identical case.

**State of the task:** everything `T02` owns is built, committed and green — 10
AC-tagged tests in `tests/test_workflow_action_integrity.py` covering both locked
ACs. Suite: 617 passed / 1 failed at baseline (`78fb600`, the
`test_marketplace.py` ordering flake, which passes alone), **622 passed / 6
failed** after, the six being exactly the ones above. `T02` is `Blocked` until
this is settled; `T03` depends on it.

**Resolving artefact:** — (Open)

**Resolution (2026-10-18):** authorised. `src/backend/tests/test_workflow_artifact_kind.py` is added to `REQ-SB-95-US-04-T02`'s `## Files to Modify`, scoped to the one autouse fixture. `T01`'s step fixtures invented Action ids before a save-time gate existed; the gate refusing them is the locked `AC-02` behaviour, not a regression, and `ESC-064` was the identical case one story earlier.

Two things make this worth more than an unblock. First, the fixture is needed **independently**: without it those tests read the operator's real `<DATA_PATH>/data/Actions/` store, so their result depends on what happens to exist on the machine. Second, this is the **mirror** of the switch-on rule added this morning after five escalations — that rule asks which file makes your code run; this asks which existing fixtures your new rule makes invalid. The decomposer rule and framework `MEMORY.md` now carry both halves.

**Resolving artefact:** `REQ-SB-95-US-04-T02` scope extension + decomposer rule extension, 2026-10-18

**Status:** Resolved

---

## ESC-076: adding the seventh artifact kind needs a sixth `artifact_*.py` module that `REQ-SB-95-US-04-T04`'s scope does not name — 2026-10-18

**Raised by:** the orchestrator, from a failure another session's task reported mid-flight.

**What happened:** `REQ-SB-95-US-04-T04` adds `workflow` to the five
`business/logic/artifact_*.py` modules its `## Files to Modify` names. A sixth module in
the same family, `artifact_import_conflicts.py`, carries `_MANAGER_BY_KIND` and is not in
the list. With `workflow` in the export's `_PAYLOAD_FOLDER` and absent from that map,
`test_action_artifact_kind.py::test_the_gate_accepts_every_kind_the_export_can_emit` fails
— the test that exists to catch precisely this drift. `REQ-SB-95-US-01-T01`, running
concurrently in the shared checkout, hit the failure in its own suite run, correctly
identified it as not its own, and left it alone.

**Resolution (2026-10-18):** authorised. `src/backend/app/business/logic/artifact_import_conflicts.py`
is added to `REQ-SB-95-US-04-T04`'s `## Files to Modify`, scoped to the one
`_MANAGER_BY_KIND` entry. `test_action_artifact_kind.py` stays out of scope and is not to
be edited — it should go green on its own, and if it does not, that is a new escalation.

**This is the third variant of one rule in two days.** `ESC-069`/`071`/`072`/`073`/`074`
gave "name the switch-on site"; `ESC-075` gave its mirror, "name the fixtures your change
invalidates"; this one gives the cheapest of the three — *enumerate a family of sibling
modules from the directory, not from memory.* Five of six were listed, and a one-line glob
would have found the sixth. `.claude/agents/decomposer.md` now carries all three.

**Two things worth recording beyond the unblock.** The drift was caught by an existing
test within the hour rather than at review, which is the `test_*_artifact_kind.py` guard
family working as designed. And it surfaced through a *concurrent* task's suite run, which
is the first time the shared checkout's multi-session traffic has produced useful
cross-checking rather than interference.

**MEMORY.md candidate, deliberately not appended:** `MEMORY.md` is 86 KB against the 40 KB
budget its own rule 1 sets, and that rule forbids appending while over budget. The rule
lives in `.claude/agents/decomposer.md`, which is where it is actually read. Recorded here
so the compaction pass can pick it up.

**Resolving artefact:** `REQ-SB-95-US-04-T04` scope extension + decomposer rule, 2026-10-18

**Status:** Resolved

---

## ESC-077: registering the seventh kind makes `test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name` fail — it used `workflow` as its stand-in for a kind that does not exist — 2026-10-18

**Category:** unanticipated-file

**Trigger:** `ESC-076` authorised `REQ-SB-95-US-04-T04` to add
`"workflow": WorkflowManager` to `artifact_import_conflicts._MANAGER_BY_KIND`,
scoped to that one entry, with
`src/backend/tests/test_action_artifact_kind.py` explicitly out of scope and the
instruction that it "should go green on its own. If it does not, stop and
escalate rather than touching it."

It did not go green on its own. One of its two gate tests flipped the other way:

```
FAILED tests/test_action_artifact_kind.py::test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name
    with pytest.raises(ValueError) as refusal:
        artifact_import.preview_import(bundle_path)
E   Failed: DID NOT RAISE ValueError
```

`test_the_gate_accepts_every_kind_the_export_can_emit` — the test `ESC-076` was
raised from — **is now green**, as predicted. The failure is its sibling, written
by `REQ-SB-95-US-02-T07` thirty lines below it (`test_action_artifact_kind.py`
lines 746–767). It needed a kind the gate would reject, and reached for the kind
that was coming next:

```python
            "artifacts": [{"kind": "workflow", "id": "monday-sweep"}],
...
    assert "unrecognized artifact kind 'workflow'" in str(refusal.value)
    for accepted_kind in ("skill", "template", "agent", "pipeline", "index", "action"):
        assert accepted_kind in str(refusal.value)
```

**This is not the guard breaking — the guard is intact and still refuses an
unknown kind.** The test's chosen example simply stopped being unknown. Verified
directly: `detect_conflicts` now answers `workflow` and raises for anything
genuinely absent, with the accepted kinds still named in the message.

**Why it was not fixed here.** `test_action_artifact_kind.py` belongs to
`REQ-SB-95-US-02-T07` (`Done`, `b2b09fe`) and is named out of scope twice over —
by that task's own Constraints and by `ESC-076`'s authorisation. `Pipeline.md`
hard rule 1 freezes a `Done` task's artefacts. This is `ESC-073`/`ESC-075` again:
a new capability makes an existing sibling test's *premise* stale while leaving
its *meaning* intact.

**What the fix is:** two lines in that one test, nothing else in the file —
re-point it at a kind that genuinely does not exist, and let the accepted-kinds
assertion read the map rather than a frozen tuple, so the next kind's author does
not rediscover this:

```python
            "artifacts": [{"kind": "hologram", "id": "monday-sweep"}],
...
        {"holograms/monday-sweep/Hologram.json": b"{}"},
...
    assert "unrecognized artifact kind 'hologram'" in str(refusal.value)
    for accepted_kind in artifact_import_conflicts._MANAGER_BY_KIND:
        assert accepted_kind in str(refusal.value)
```

Reading the map instead of a hard-coded tuple is what stops this recurring: the
tuple would have to be hand-extended for every future kind, and the bundle member
path is the other hard-coded half. Whoever authorises it should add the file to
`T04`'s `## Files to Modify` scoped to this one test (or mint a `T04a`), rather
than letting a coder reach outside scope by precedent — which is what `ESC-064`,
`ESC-073` and `ESC-075` each decided for the identical shape.

**A rule worth more than the unblock, and the reason this is the fourth of its
shape.** `ESC-076` added "enumerate a family of sibling modules from the
directory, not from memory". Its mirror is now due for *test fixtures that name a
thing by its absence*: a test asserting "X is not supported" dates itself the day
X ships, and a roadmap that already names X — `artifact_import_conflicts.py`'s own
comment said "`workflow` is next" when that test was written — makes it a
scheduled failure, not a surprise. **A negative test should pick an example
nothing plans to build, or derive it from the live set.**

**State of the task:** everything `T04` owns is built and committed (`2f91bb4`),
with 12 AC-tagged tests green covering `AC-04`, `AC-05` and `AC-07`, including the
real `preview_import`/`commit_import` route now taking a `workflow` bundle.
Suite: **634 passed / 0 failed** at this session's baseline (`6724db8`, before the
concurrent `REQ-SB-95-US-01-T01` landed its 9 tests), **654 passed / 1 failed**
now — the one being the test above. `T04` is `Blocked` until this is settled;
`T07` depends on it.

**Resolution (2026-10-18):** authorised. `src/backend/tests/test_action_artifact_kind.py` is added to `REQ-SB-95-US-04-T04`'s `## Files to Modify`, scoped to `test_a_genuinely_unknown_kind_still_fails_the_bundle_by_name` alone, with all three changes the escalation specifies — including deriving the accepted-kinds assertion from `artifact_import_conflicts._MANAGER_BY_KIND` rather than a frozen tuple. That third change is the one worth more than the unblock: the tuple is precisely what would make the eighth kind's author rediscover this.

**The coder was right not to fix it itself.** `ESC-076`'s authorisation named that file out of scope and said to escalate rather than reach; it escalated, with the exact replacement written out. That is the behaviour the preceding six escalations were meant to produce, and it cost one round trip instead of a silent edit to a `Done` task's test.

**Fourth variant of one rule in two days**, now all four in `.claude/agents/decomposer.md`: name the switch-on site (`ESC-069`/`071`/`072`/`073`/`074`); name the fixtures your change invalidates (`ESC-075`); enumerate a family of sibling modules from the directory, not from memory (`ESC-076`); and a negative test must pick an example nothing plans to build, or derive it from the live set (this one).

**Separately, and recorded because it nearly went unnoticed:** the coder's throwaway probe of `commit_import` ran against live settings and planted a Workflow in the operator's real `<DATA_PATH>/data/Workflows/`. It caught this itself, confirmed the artefact was its own, removed it through the app's own path, and reported it unprompted. Independently verified by the orchestrator afterwards: the directory exists and holds zero entries. The suite itself never touches the real store — re-run against an empty data path, 21/21 passed with that directory still empty. The second `MEMORY.md` candidate below comes from this.

**Two `MEMORY.md` candidates, deliberately not appended** (86 KB against the 40 KB budget its own rule 1 sets, which forbids appending while over): *a negative test must pick an example nothing plans to build*, and *a throwaway probe is a test too — it needs the same sandbox discipline as the suite*. Both are held here for the compaction pass; the first also lives in `.claude/agents/decomposer.md`, where it is actually read.

**Resolving artefact:** `REQ-SB-95-US-04-T04` scope extension + decomposer rule, 2026-10-18

**Status:** Resolved

## ESC-078: the seventh Artifacts tab needs the `ArtifactKind` union and the export modal's map, and `REQ-SB-95-US-04-T07`'s scope names neither — 2026-10-18

**Category:** unanticipated-file

**Trigger:** Building `REQ-SB-95-US-04-T07`. Its `## Files to Modify` reads
`src/frontend/src/pages/SettingsArtifactsPage.tsx (seventh KIND_NAV entry + the
ArtifactKind union)` — but the union is **not** declared in that file. It lives in
`src/frontend/src/features/settings/artifactsApiClient.ts:8`, which this task's list
does not name at all, and `KIND_NAV` is typed `{ kind: ArtifactKind; … }[]`, so the
seventh tab does not compile until the union grows. Widening it then breaks a
second, unlisted file: `src/frontend/src/features/settings/ArtifactExportModal.tsx:12`
declares its own `KIND_LABELS: Record<ArtifactKind, string>`, and a `Record` keyed by
a union is exhaustive — it fails `TS2741` the moment the union has a member it does
not map. A red `tsc -b` is not local here: it blocks every plugin publish and install
across the shared checkout.

This is **`ESC-070` repeating one kind later**, for the reason `ESC-070` itself
recorded: *"a task that widens a shared union owns every exhaustive map over it, and a
`## Files to Modify` written from the union's declaration site will miss them."* The
sixth kind's task (`REQ-SB-95-US-02-T06`) did list `artifactsApiClient.ts`; the
seventh kind's does not, so the gap is wider this time, not narrower.

**What is needed — the exact changes, neither of them taken:**

1. `src/frontend/src/features/settings/artifactsApiClient.ts`, line 8 — one member:

   ```ts
   export type ArtifactKind = 'skill' | 'template' | 'agent' | 'pipeline' | 'index' | 'action' | 'workflow';
   ```

   The comment directly above it already says *"Must list every kind GET /artifacts
   returns"*, and since `REQ-SB-95-US-04-T04` that endpoint returns `workflow`.
   Confirmed live against a disposable backend: `GET /artifacts` answered
   `skill 11 / template 6 / agent 1 / action 4 / workflow 1`. The page drops those
   workflow rows silently today — `groupedByKind[artifact.kind]?.push(…)` is
   `?.`-guarded by design, so there is no crash, no tab, and the kind is invisible.

2. `src/frontend/src/features/settings/ArtifactExportModal.tsx`, lines 12-15 — one
   entry, so the exhaustive map compiles and a selected Workflow is labelled rather
   than rendered as its raw kind:

   ```ts
   const KIND_LABELS: Record<ArtifactKind, string> = {
     skill: 'Skill', template: 'Template', agent: 'Agent', pipeline: 'Pipeline', index: 'Index',
     action: 'Action', workflow: 'Workflow',
   };
   ```

With those two authorised, the in-list change to `SettingsArtifactsPage.tsx` is
`KIND_ORDER` + `'workflow'`, one `KIND_NAV` entry
(`{ kind: 'workflow', icon: 'account_tree', label: 'Workflows' }`), one `KIND_LABELS`
entry, and the intro sentence's list of kinds. `KIND_ORDER` is the load-bearing one:
`byKind()`, `SelectionState` and the `useUrlState` `valid:` list all derive from it,
and `ESC-070` already recorded that adding only the `KIND_NAV` entry compiles and then
silently drops every row of the new kind.

**Impact of leaving it:** `REQ-SB-95-US-04-AC-04` (the seventh kind listed on
Settings → Artifacts) cannot be verified, so `T07` is `Blocked`. The task's other three
locked ACs — `AC-01`, `AC-02`, `AC-06` — were built and verified live in a real browser
before this was raised, and none of them touches either file.

**Resolution (2026-10-18):** authorised. Both files are added to `REQ-SB-95-US-04-T07`'s `## Files to Modify` — `artifactsApiClient.ts` (one union member) and `ArtifactExportModal.tsx` (one `KIND_LABELS` entry) — exactly as the escalation wrote them out, and nothing else in either.

**The coder is right that this is `ESC-070` repeating one kind later, and the reason is worth more than the unblock.** `ESC-070` recorded the rule correctly and in full — *a task that widens a shared union owns every exhaustive map over it, and a `## Files to Modify` written from the union's declaration site will miss them* — and recorded it **only in `ESCALATIONS.md`**. That file is an append-only log of what happened; nobody opens it when writing a file list. The four rules landed in `.claude/agents/decomposer.md` earlier today have all held so far; this one, logged and not landed, recurred verbatim one story later.

So two rules go into the decomposer rather than one: the union rule itself, and the meta-rule — **a rule recorded only in `ESCALATIONS.md` is not recorded.** A lesson lands where the work is done: decomposer rules in `.claude/agents/decomposer.md`, constraints in `MEMORY.md`, sprint heuristics in `Implementation/Learnings.md`.

**A live defect, not only a compile gate.** `GET /artifacts` has returned `workflow` since `REQ-SB-95-US-04-T04`, and Settings → Artifacts drops those rows silently through its `?.` guard — measured against a disposable backend as `skill 11 / template 6 / agent 1 / action 4 / workflow 1`. There is no crash and no tab, so the kind is simply invisible on the operator's install today. `AC-04` closes an existing gap, not a hypothetical one.

**`MEMORY.md` candidates, deliberately not appended** (86 KB against the 40 KB budget its own rule 1 sets, which forbids appending while over): the union rule above, and the two the coder raised — *a `<select>` must carry an unknown stored value as its own labelled option*, and *a refused save is evidence the picker's list is stale, so re-read it*. Held here for the compaction pass; the first two also live in `.claude/agents/decomposer.md`, where they are actually read.

**Resolving artefact:** `REQ-SB-95-US-04-T07` scope extension + two decomposer rules, 2026-10-18

**Status:** Resolved
