---
id: REQ-SB-95-US-02
title: Action as the sixth artifact kind — one catalogue of what this app can actually do
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: In Progress
gate: clear
gate_reason: "RESOLVED operator confirmed ADR-033's catalogue fields, 2026-10-17 — was: trigger-3 (ADR-033 created — it decides the Action fields this story stores: allowed_callers as agent ids, and the confirmation flag's meaning)"
sprint: SPRINT-087
created: 2026-10-16
updated: 2026-10-17  # coder: T03 Done 2026-10-17 (Actions CRUD API, suite 457 passing) — gate: flagged for a scope-internal spot-check only (409-not-422 for Manager refusals, 200-not-201 on create, TestClient instead of the ASGITransport the task named — no test here uses ASGITransport and twelve use TestClient, POST-onto-an-existing-id overwrites and was left to the Manager). T05 and T06 outstanding; T06 must map `implementation` between its nested write shape and its flat read shape, see that task's Implementation Log. Previously — coder: T01, T02, T04 and T07 Done (suite 436 passing). ESC-065 is Resolved by T07 — `index` and `action` are registered in artifact_import_conflicts._MANAGER_BY_KIND, so a mixed-kind bundle previews and commits through the real import route; T04's gate, flagged on ESC-065 alone, is cleared (status unchanged, Done). T03, T05, T06 outstanding
---

# REQ-SB-95-US-02 — Action as the sixth artifact kind — one catalogue of what this app can actually do

## Story

**As a** Second Brain operator
**I want** every invocable operation this app offers to be a catalogued Action —
with typed inputs, permitted callers, a confirmation flag, and exactly one
working implementation
**So that** there is one list of what the app can do, instead of a Skills list
and a separate set of features that only exist inside a screen

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95* — Finding 2 ("the agent cannot see
  what the app can do": "Make Adobe a Strategic Entity" is a real feature
  implemented in a screen, Skills are a separate list, so the app has
  capabilities the agent cannot reach) and the second **What is wanted** bullet
  ("Actions, as a first-class artifact kind. One invocable operation: id,
  description, typed inputs with required flags, who may run it, whether it needs
  confirmation, and exactly one implementation (a Skill, an HTTP route, or an
  in-app feature). The UI renders from the same catalogue... Plugins contribute
  actions the way they already contribute Cockpit tabs").
- **Architecture is already settled — `ADR-032`** (Accepted 2026-10-16, pending a
  human look): `Action` becomes the **sixth artifact kind**, stored at
  `<DATA_PATH>/data/Actions/<id>/Action.json` beside the kinds that already live
  in the data path; exactly ONE `implementation` of `skill` | `http` | `ui`; and
  **the implementation is resolved when the Action is SAVED, not when it is
  called**, "so a broken action cannot sit in the catalogue waiting to fail in
  front of the operator".
- **Sibling stories.** This is the second of `REQ-SB-95`'s five stories and the
  **spine the rest hang off**: `US-03` publishes and enforces this catalogue,
  `US-04`'s Workflow steps reference Action ids, and `US-05`'s entity read is
  reachable by an agent only once it can be catalogued as an Action. `US-01`
  (Operator Profile) is independent of it. This story deliberately stops at the
  catalogue — a stored, validated, browsable, portable Action — because adding
  agent-side publication and call validation to it would not fit one working
  context.
- **Grounded against the real code, not guessed.** `artifacts_inventory.py` today
  composes exactly five Managers and its own header states `kind` is "always
  exactly one of skill/template/agent/pipeline/index — no 6th value is ever
  produced, since these are the only 5 Managers composed" (confirmed by direct
  reading). The **Index precedent** is the template for the work: `Index` joined
  that set on 2026-09-06, which is the measured cost `ADR-032` points at. Export,
  import, the secret scan and the dependency resolver (`artifact_export.py`,
  `artifact_import.py`, `artifact_secret_scan.py`) all key off that same kind set.
- **Plugins already have a facade.** `app/plugin_api.py` is the single surface a
  plugin may import (`ADR-022`), and route/screen/nav registration already goes
  through it — so "plugins contribute actions" is an addition to an existing
  registration mechanism, not a new one.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The operator catalogues an invocable operation as an Action

```gherkin
Given the operator wants an operation this app can perform to be invocable
When the operator saves an Action with an id, a description, typed inputs each
    flagged required or optional, allowed_callers (agent ids, or ["*"]), a
    needs_confirmation flag, and exactly one resolvable implementation
Then the Action is stored for this install at
    <DATA_PATH>/data/Actions/<id>/Action.json
  And the Actions catalogue lists it with its id, description and implementation
    kind
  And reopening it returns exactly the inputs, required flags, allowed_callers
    and confirmation flag that were saved
```
<!-- AC-ID: REQ-SB-95-US-02-AC-01 -->

### Scenario 2: An Action whose implementation does not resolve cannot be saved

```gherkin
Given the operator is creating or editing an Action
When the named implementation does not resolve on this install — a Skill that is
    not deployed, an HTTP route the running app does not expose, or a UI feature
    key that is not registered
Then the save is refused with a message naming the implementation that did not
    resolve
  And no Action.json is created or changed on disk
  And re-saving the same Action with a resolvable implementation succeeds
```
<!-- AC-ID: REQ-SB-95-US-02-AC-02 -->

### Scenario 3: Exactly one implementation, never zero and never two

```gherkin
Given the operator is saving an Action
When the payload carries no implementation, or more than one of skill / http / ui
Then the save is refused and the message states that an Action has exactly one
    implementation
  And nothing is written
  And a payload naming exactly one of the three is saved normally
```
<!-- AC-ID: REQ-SB-95-US-02-AC-03 -->

### Scenario 4: Actions appear in the artifact inventory as a sixth kind

```gherkin
Given this install has real Actions in its catalogue
When the artifact inventory is read and the operator opens Settings → Artifacts
Then the Actions are listed under their own "action" kind alongside the existing
    skill, template, agent, pipeline and index entries
  And a kind with no artifacts renders its honest empty state rather than being
    hidden
  And every pre-existing kind returns exactly the entries it returned before the
    sixth kind existed
```
<!-- AC-ID: REQ-SB-95-US-02-AC-04 -->

### Scenario 5: An exported Action carries the thing it runs

```gherkin
Given an Action whose implementation is a deployed Skill
When the operator exports that Action as part of a portable bundle
Then the dependency closure that already pulls an Agent's Skills in resolves that
    Skill into the bundle, and the Action travels under its own
    actions/<id>/Action.json payload folder
  And importing that bundle onto another install produces an Action whose
    implementation resolves there too
  And importing an Action whose id already exists is handled by the existing
    conflict resolution — skip, overwrite or keep-both — never silently
    overwritten
```
<!-- AC-ID: REQ-SB-95-US-02-AC-05 -->

### Scenario 6: A plugin contributes Actions into the same catalogue

```gherkin
Given an installed plugin registers its own Actions through the app.plugin_api
    facade
When the operator opens the Actions catalogue
Then the plugin's Actions appear in the same one catalogue as the install's own
  And each plugin-contributed Action is attributed to the plugin id that
    registered it
  And no plugin Action is written into <DATA_PATH>/data/Actions/, so
    uninstalling that plugin removes its Actions and leaves the install's own
    untouched
```
<!-- AC-ID: REQ-SB-95-US-02-AC-06 -->

### Scenario 7: An Action whose implementation stops resolving is visible, not silent

```gherkin
Given a catalogued Action whose implementation resolved when it was saved
When the thing it points at is no longer present on this install
Then reading the catalogue reports that Action with a broken status naming what
    no longer resolves
  And the Actions catalogue screen shows that broken state to the operator
    without anything having had to call the Action first
```
<!-- AC-ID: REQ-SB-95-US-02-AC-07 -->

## Affected Screens

- **New** `src/frontend/src/pages/SettingsActionsPage.tsx` (name indicative) —
  the Actions catalogue: a list of Actions and an editor for one Action (id,
  description, typed inputs with required flags, permitted callers, confirmation
  flag, implementation picker). Reuses the live approved `.item-list`/`.item-row`
  list shape and `.input`/`Save changes` form conventions.
- `src/frontend/src/pages/SettingsPage.tsx` — one more card in the live
  `SETTINGS_SECTIONS` grid.
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` — the cross-kind inventory
  gains a sixth kind (Scenario 4); no new visual pattern.
- `html-prototype/settings.html` — **not** the design authority (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:** none within `REQ-SB-95`.
- **Related to:** `REQ-SB-95-US-03` (publishes and enforces this catalogue) and
  `REQ-SB-95-US-04` (Workflow steps reference Action ids) both depend on this
  story; `REQ-SB-85-US-01`/`US-02`/`US-03` (artifact browser, export, import) are
  the machinery Scenarios 4 and 5 extend; `ADR-022` plugin facade is what
  Scenario 6 extends.
- **External:** none new.

## Constraints

- **`<DATA_PATH>/data/Actions/<id>/Action.json`** — instance data in the data
  path, edited in the app, never the repository (`ADR-032`). The framework may
  ship starter Actions the way it ships Master Templates.
- **One Manager is the sole gateway** onto Action data, raw I/O in
  `data_access/` only — the standing backend layering rule.
- **Resolution happens at save, not at call** (`ADR-032`). A call-time-only check
  is explicitly not what this story asks for.
- **Core must not name a plugin.** Plugin-contributed Actions arrive through the
  `app.plugin_api` facade (`ADR-022`), not through core knowing any plugin id.
- **No pre-existing artifact kind changes behaviour.** Adding the sixth kind must
  leave Skills, Templates, Agents, Pipelines and Indexes exactly as they are.
- **`Pipeline` is untouched** (`ADR-032`) — an Action is not a Pipeline step and
  no Pipeline is reclassified.

## Implementation Tasks

Final split, owned by the decomposer (2026-10-16). `depends_on` holds task ids.

| ID | Type | Task | ACs covered | depends_on | Task File |
|---|---|---|---|---|---|
| REQ-SB-95-US-02-T01 | backend | `Action` entity + `ActionManager` + data access over `<DATA_PATH>/data/Actions/<id>/Action.json`, incl. exactly-one-implementation | AC-01, AC-03 | — | `../Tasks/REQ-SB-95-US-02-T01-action-entity-manager-data-access.md` |
| REQ-SB-95-US-02-T02 | backend | Save-time implementation resolution for `skill` / `http` / `ui`, plus the read-side broken-entry status | AC-02, AC-07 | T01 | `../Tasks/REQ-SB-95-US-02-T02-save-time-resolution-and-broken-report.md` |
| REQ-SB-95-US-02-T03 | backend | Actions CRUD API (`app/api/actions_router.py`) | AC-01, AC-02, AC-03, AC-07 | T02 | `../Tasks/REQ-SB-95-US-02-T03-actions-crud-api.md` |
| REQ-SB-95-US-02-T04 | backend | Sixth kind in inventory, dependency resolver, export, import, secret scan | AC-04, AC-05 | T01 | `../Tasks/REQ-SB-95-US-02-T04-sixth-kind-inventory-export-import-resolver.md` |
| REQ-SB-95-US-02-T05 | backend | Plugin-contributed Actions through the `app.plugin_api` facade, composed at read time | AC-06 | T02 | `../Tasks/REQ-SB-95-US-02-T05-plugin-contributed-actions.md` |
| REQ-SB-95-US-02-T06 | frontend | Actions catalogue + Action editor page, Settings card, route, sixth Artifacts tab | AC-01, AC-02, AC-03, AC-04, AC-06, AC-07 | T03, T04, T05 | `../Tasks/REQ-SB-95-US-02-T06-actions-catalogue-screen.md` |
| REQ-SB-95-US-02-T07 | backend | The import conflict gate knows every artifact kind, not four — `index` + `action` in `artifact_import_conflicts._MANAGER_BY_KIND` (added 2026-10-16, resolving `ESC-065`) | AC-05 | T04 | `../Tasks/REQ-SB-95-US-02-T07-import-conflict-gate-knows-every-kind.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Publishing the catalogue into agent context, and validating an agent's call
  against it** — `REQ-SB-95-US-03`. This story's Actions are real, stored and
  portable; no agent behaviour changes because of it.
- **Workflows** — `REQ-SB-95-US-04`.
- **Entity resolution and its starter Action** — `REQ-SB-95-US-05`.
- **Retro-cataloguing every existing in-app feature as an Action.** This story
  delivers the kind and its catalogue; which existing features become Actions is
  separate, incremental work.
- **Changing how Skills are deployed, or merging Skills into Actions.** An Action
  may point at a Skill; it does not replace one.
- **Converting any Pipeline into an Action or Workflow** (`ADR-032` leaves
  Pipeline alone).

## Notes

**Prototype parity (`html-prototype/settings.html` is the only prototype screen
in scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27; the new
  Actions card reuses the live approved grid.
- Actions list rows — **Specced** (Scenarios 1, 4, 7) on the already-approved
  `.item-list`/`.item-row`/`.item-row-meta` family live on
  `SettingsArtifactsPage.tsx` and `SettingsSectionsPage.tsx`.
- The Action editor (typed-input rows with required flags, permitted callers,
  implementation picker) — **Specced functional-first** (Scenarios 1, 2, 3). It
  is a composition of already-approved `.input`/`.btn`/`Save changes` controls
  rather than a new visual system, and this follows the operator's own 2026-08-31
  precedent (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied again on
  `REQ-SB-78`): build functional-first with existing app conventions, take the
  visual pass afterwards. If the human disagrees, `/design REQ-SB-95` before
  `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- *How* "who may run it" is represented is deliberately left open — every AC here
  asserts behaviour only. The nearest existing precedents are per-agent
  `skill_ids` grants and Section ownership.
- *How* "needs confirmation" is honoured is likewise open; the obvious candidate
  is the already-live Working Modes / Pending Approvals machinery
  (`REQ-SB-21`, `REQ-SB-78`) rather than a second confirmation mechanism.
- `artifacts_inventory.py`'s header comment hard-states "the only 5" and will
  need correcting as part of the change, not around it.

**Architecture scope (bounds the decomposer/coder):**
`Implementation/Architecture/architecture.md` → §An Agent Acts From a Published
Catalogue (`REQ-SB-95`) → **§Action Catalogue — the Sixth Artifact Kind**,
**§Adding a Kind — the Measured Touch Points**, **§Plugin-Contributed Actions**.
Read-only context (this story builds none of it): §Catalogue Publication Into
Agent Context and §The Action Call Gate, which define the meaning of the two
fields this story stores. ADRs in force: `ADR-032` (kind, store, cardinality,
save-time resolution), `ADR-033` (field shapes below), `ADR-019` (the `Index`
precedent and the payload/application-code boundary), `ADR-022` (plugin facade),
`ADR-013`/`ADR-015` (export/import machinery being extended).

**Architect pass 2026-10-16 — what was decided for this story:**

- **"Who may run it" is `allowed_callers`: a list of agent ids, or `["*"]`**
  (`ADR-033`). The Registry agent id IS the Hermes profile id everywhere in this
  codebase, so it is the one identifier both sides already share. Not a Section
  (an agent's `section_id` is legitimately `None` when unplaced), not agent type.
- **"Needs confirmation" is a per-Action boolean whose honouring is `US-03`'s
  work**, through a new Action-call ledger — NOT `Agent.working_mode` and NOT the
  archived pending-approvals subsystem (`pending_approvals_router.py` is not in
  the repo; `GET /agents/{id}/history` returns `[]` and says why). This story
  stores the flag and nothing more.
- **Plugin Actions are composed at read time, never written to
  `<DATA_PATH>/data/Actions/`** — `plugin_api.register_action(...)` follows the
  existing per-plugin registration shape, so uninstall removes them by
  construction (Scenario 6).
- **Scenario 7's broken-action view is a read-side status**, shaped like
  `SkillManager`'s existing deployment report, computed on read with no cache.
- No decision was taken here about retro-cataloguing existing features; that
  remains out of scope as the story states.

**Decomposer pass 2026-10-16 — AC locking and the task split:**

- Seven ACs locked, `REQ-SB-95-US-02-AC-01` … `AC-07`, one per analyst
  scenario, tightened to name the real store path, the real field names
  (`allowed_callers`, `needs_confirmation`) and the real payload folder, so each
  is verifiable without re-deriving `ADR-032`/`ADR-033`.
- Six tasks, `T01`–`T06`, dependency chain
  `T01 → T02 → {T03, T05}` and `T01 → T04`, converging on the frontend `T06`.
  The split follows the architecture's own seams (entity/manager/data access,
  resolution, API, the measured touch points, the plugin facade, the screen) —
  no judgement call was needed beyond them.
- **Verification is automated for every backend task.** This project has a real
  backend pytest stack (`src/backend/tests/`), and `tests/test_index_artifact_kind.py`
  is the direct precedent for adding a kind, so backend ACs get AC-tagged tests
  with `pytest tests/<file>.py` from `src/backend`. The **frontend declares no
  test runner** (CLAUDE.md), so `T06`'s AC-tagged steps are structural DOM
  checks in a real browser; pure visual polish is deliberately not a locked AC.
- Gate left as the architect set it (trigger 3, `ADR-033`) — the decomposer pass
  fired no additional trigger. No `ESCALATIONS.md` entry; no new
  `REVIEW-QUEUE.md` item (the existing `REQ-SB-95-US-02` entry already asks for
  exactly the `ADR-033` review these tasks now depend on).

**Audit breadcrumb:**

gate: flagged 2026-10-16 (architect) — trigger 3: `ADR-033` was created in this
pass and decides two fields this story persists. The prior analyst breadcrumb
below remains accurate for everything else; no `ESCALATIONS.md` entry, no
contradiction with `ADR-032`, the PRD or `MEMORY.md`.

gate: clear 2026-10-16 — no triggers fired. No material assumption (every AC
asserts observable behaviour the PRD or `ADR-032` already states; representation
choices are left to the architect by design); `REQ-SB-95` is finalised in the PRD
with a complete Acceptance paragraph and carries no `<!-- Draft -->` marker; no
ADR created or changed by this pass (`ADR-032` is pre-existing and already took
these decisions); no `ESCALATIONS.md` entry; not oversized (~6 tasks, M — the
five-way requirement split exists to keep it that way); no contradictory inputs;
no second equally-valid scoping — `ADR-032` settles kind, store, cardinality and
resolution timing.
