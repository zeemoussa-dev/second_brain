---
id: REQ-SB-85-US-01
title: Settings → Artifacts — cross-type browsable, multi-selectable inventory of Skills/Templates/Agents/Pipelines
requirement_ids: [REQ-SB-85]
requirement_section: "REQ-SB-85: Artifact Export/Import — Portable Capability Bundles (`.sbf`)"
phase: P2
status: Done
gate: clear
gate_reason: "clear 2026-08-31 — operator directly resolved the net-new-design-needed flag this same day: build functional-first, design pass comes AFTER the task works, matching this exact session's own established precedent (REQ-SB-82-US-06-T07/T08 shipped functional-but-unstyled UI, styled separately once proven). Original analyst finding preserved below for context, not erased: no `html-prototype/` screen anywhere covers a cross-type artifact browser with multi-select (confirmed by direct inspection of `html-prototype/index.html`'s own screen catalog before writing this story: zero mention of Artifacts/bundles anywhere). The underlying per-row rendering reuses an already-approved pattern (`.item-list`/`.item-row`, live on `SettingsVaultTemplatesPage.tsx`/`SettingsSectionsPage.tsx`), but the cross-type grouping + multi-select selection UI itself has no prior approved precedent — /plan-tasks and the coder should build a plain, functional treatment using existing app conventions, not invent a bespoke visual system; a real `/design` pass for polish is expected later, tracked separately. See `REVIEW-QUEUE.md`."
sprint: SPRINT-079
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-01 — Settings → Artifacts — cross-type browsable, multi-selectable inventory of Skills/Templates/Agents/Pipelines

## Story

**As a** Second Brain operator
**I want** a new Settings → Artifacts section that lists every real Skill,
Template, Agent, and Pipeline my deployment has, browsable and
multi-selectable across all four kinds
**So that** I have one place to see everything I could move to another
deployment, and a real selection to hand to the Export flow
(`REQ-SB-85-US-02`) or to review against an imported bundle's own contents
(`REQ-SB-85-US-03`)

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-85: Artifact Export/Import —
  Portable Capability Bundles (`.sbf`)* — "A new **Settings → Artifacts**
  section lists every real artifact the operator's own deployment has —
  Skills, Templates, Agents, Pipelines — browsable and multi-selectable
  across types." This story is the first of three substories this
  requirement splits into, matching this project's own established
  large-requirement precedent (`REQ-SB-82`'s six-way split,
  `REQ-SB-71`'s three-way split) — the requirement is genuinely too large
  for one working context: a new cross-type browser UI, a dependency-
  resolution + secret-scan export flow, and a real target-machine
  provisioning + conflict-resolution import flow are each independently
  substantial. This story is the **foundational** piece both `US-02`
  (Export) and `US-03` (Import's own "preview what will be deployed"
  screen) build on.
- **PRD breadcrumb (2026-08-31, operator, verbatim):** "This can be a new
  Section under Settings (Artifcates)... Click Export it Generates the
  Exported Entities it can SHow me a message that those Items will be
  exported with the Package as they depend on it." The browsing/selection
  surface itself (this story) is the entry point the breadcrumb describes,
  distinct from the resolve-and-confirm step that follows it (`US-02`).
- **Grounded directly against the real, already-`Done` Manager layer, not
  guessed** — all four kinds this browser composes already exist as real
  `business/core/<entity>/<entity>_manager.py` gateways, each with a
  working `get_all()` (confirmed by direct reading, not assumed):
  `SkillManager` (`Hermes-Provisioning/skills/<category>/<slug>/` content +
  Registry `Tools/<tool>/Skills/<slug>/Skill.json` metadata),
  `TemplateManager` (read-only, `.second-brain/data/Templates/<id>/
  Template.json`, vault-only — confirmed zero Hermes involvement),
  `AgentManager` (composes a real Hermes profile + the Registry's own
  `Agent.json` — two genuinely separate stores, see `US-02`'s own Context
  for why that matters for export), and `PipelineManager` (read-only,
  `<second_brain_data_path>/pipelines/<id>.json`, cron-linked). All four
  are the product of `REQ-SB-80` (Second Brain Data Layer) — "Locked
  design, direct build (no `/spec`... reverses `ADR-003`'s
  read-only-mirror stance)" per `BACKLOG.md`'s own row — and are confirmed
  `Done`/live per `MEMORY.md`'s 2026-08-28 entries (`AgentManager`
  built/verified live; `SkillManager`/`ToolManager` built; `PipelineManager`
  built). This story adds **zero new entity or write path** — it is a
  pure read/compose/select surface over four Managers that already exist.
- **Exactly the 4 kinds the PRD names, no more.** The PRD's own literal
  text lists Skills/Templates/Agents/Pipelines — it does not name
  Providers, Sections, or the Vault Index as browsable/exportable
  artifact kinds, and no PRD text asks for them here. Adding one would be
  inventing scope this requirement doesn't ask for.
- **The real, current Settings landing page is a card grid
  (`SettingsPage.tsx`), NOT `html-prototype/settings.html`** — same "real
  code supersedes a stale prototype" situation `REQ-SB-82-US-06` already
  established for `Cockpit.tsx`. `SettingsPage.tsx`'s own header comment
  confirms it replaced the prototype's flat card stack with an icon-card
  grid (2026-08-27) and that Providers already lost its own Settings UI
  entirely (dead router) — `html-prototype/settings.html` is stale on both
  points and is not the design authority for where a new "Artifacts" card
  goes.
- **Closest visual precedent, confirmed live:** `SettingsVaultTemplatesPage.tsx`
  and `SettingsSectionsPage.tsx` both already render a real, approved
  `.item-list`/`.item-row`/`.item-row-main`/`.item-row-title`/
  `.item-row-meta` list of named entities with metadata — the natural
  per-row shape for this story's own list. Neither page has a multi-select/
  checkbox affordance anywhere, and no other real screen in this app does
  either (confirmed by scanning the frontend's own `features/`/`pages/`
  tree) — the selection mechanism itself is genuinely new interaction,
  not a restyle of something already approved.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Settings → Artifacts lists every real artifact across all 4 kinds

```gherkin
Given the operator's own Second Brain deployment has real Skills,
    Templates, Agents, and Pipelines
When the operator opens Settings → Artifacts
Then every real artifact across all 4 kinds (Skill, Template, Agent,
    Pipeline) is listed, each row clearly labeled with its own kind and
    its own name/id
  And the list reflects the real, current state of the deployment — never
    a fabricated or stale sample
```
<!-- AC-ID: REQ-SB-85-US-01-AC-01 -->

### Scenario 2: Multi-selecting artifacts across different kinds builds one combined selection

```gherkin
Given the Artifacts list is showing real Skills, Templates, Agents, and
    Pipelines
When the operator selects one or more artifacts, including artifacts of
    different kinds in the same selection
Then the selection accumulates across kinds into one combined set
  And the operator can see, at a glance, a per-kind count of how many
    artifacts of each kind are currently selected
```
<!-- AC-ID: REQ-SB-85-US-01-AC-02 -->

### Scenario 3: A kind with zero real artifacts is shown honestly, not hidden or fabricated

```gherkin
Given the deployment genuinely has zero real artifacts of one particular
    kind (e.g. no Pipelines exist yet)
When the operator opens Settings → Artifacts
Then that kind's own section renders an honest empty state (e.g. "No
    Pipelines yet") rather than being hidden or showing a fabricated row
  And the other kinds' real artifacts are still listed normally
```
<!-- AC-ID: REQ-SB-85-US-01-AC-03 -->

### Scenario 4: Clearing a selection

```gherkin
Given the operator has selected one or more artifacts across one or more
    kinds
When the operator activates the clear-selection control
Then no artifact remains selected, and every per-kind selection count
    reads zero
  And the underlying artifact list itself is unchanged
```
<!-- AC-ID: REQ-SB-85-US-01-AC-04 -->

### Scenario 5: Reachable from the Settings landing page

```gherkin
Given the operator is on the Settings landing page
When the operator looks for a way to manage capability bundles
Then a new "Artifacts" card is present alongside the existing Settings
    cards (System/Sections/Vault/Config/UI)
  And selecting it navigates to Settings → Artifacts
```
<!-- AC-ID: REQ-SB-85-US-01-AC-05 -->

## Affected Screens

- `src/frontend/src/pages/SettingsPage.tsx` — the REAL, current Settings
  landing page (see Context for why this, not `html-prototype/
  settings.html`, is the design authority). `SETTINGS_SECTIONS` gains one
  more entry ("Artifacts") — reuses the exact `.card.settings-card` grid
  pattern already live, no new component.
- New `src/frontend/src/pages/SettingsArtifactsPage.tsx` — genuinely new
  screen. Per-row rendering reuses the already-approved `.item-list`/
  `.item-row` family (`SettingsVaultTemplatesPage.tsx`/
  `SettingsSectionsPage.tsx`); the cross-type grouping + multi-select
  selection UI + selection-count summary has no approved precedent
  anywhere — **`net-new-design-needed`**.
- `html-prototype/settings.html` — **not** the design authority for this
  story (see Context); not touched.

## Dependencies

- **Blocked by:** `REQ-SB-80` (Second Brain Data Layer, direct build, no
  `/spec`) — the four real Managers this browser composes
  (`SkillManager`/`TemplateManager`/`AgentManager`/`PipelineManager`) are
  its product; all four confirmed `Done`/live per `MEMORY.md`'s
  2026-08-28 entries.
- **Related to:** `REQ-SB-85-US-02` (Export) and `REQ-SB-85-US-03`
  (Import) — sibling substories of the same requirement; this story is
  the entry point/selection surface both build on.
- **External:** none new — this story adds zero new backend write paths
  (list/read composition only over already-real Managers).

## Constraints

- Exactly the 4 artifact kinds the PRD names — Skill, Template, Agent,
  Pipeline. No Provider/Section/Vault-Index kind is added (out of
  `REQ-SB-85`'s literal scope — see Context).
- Read-only browsing/selection only — no create/edit/delete of any
  artifact happens from this screen. Each kind's own existing (or future)
  CRUD surface is untouched by this story.
- The multi-select selection itself is ephemeral, client-side state, not
  persisted anywhere — it exists only to be handed to the Export flow
  (`REQ-SB-85-US-02`).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-85-US-01-T01 | backend | New cross-type listing endpoint composing `SkillManager`/`TemplateManager`/`AgentManager`/`PipelineManager`.`get_all()` into one tagged (`kind`, `id`, `name`/`description`) response | `app/api/artifacts_router.py` (new) | `../Tasks/REQ-SB-85-US-01-T01-artifacts-list-endpoint.md` |
| REQ-SB-85-US-01-T02 | frontend | `SettingsArtifactsPage.tsx` — cross-type list/browse + multi-select UI; new "Artifacts" card on `SettingsPage.tsx`; new route | `src/frontend/src/pages/SettingsArtifactsPage.tsx` (new), `src/frontend/src/pages/SettingsPage.tsx`, `src/frontend/src/features/settings/artifactsApiClient.ts` (new), `src/frontend/src/App.tsx` | `../Tasks/REQ-SB-85-US-01-T02-settings-artifacts-page.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual verification mode still the live default project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new one emerged
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Export/Import actions themselves** — `REQ-SB-85-US-02`/`REQ-SB-85-US-03`.
- **Any create/edit/delete of a Skill/Template/Agent/Pipeline** from this
  screen — untouched, existing (or future) surfaces own that.
- **Provider, Section, or Vault Index as a browsable artifact kind** — not
  named by the PRD's literal text (see Context).
- **Persisting a selection across sessions/reloads.**

## Notes

**Prototype parity:**

- Settings landing page card grid — **Specced** (Scenario 5); the new
  "Artifacts" card reuses the exact live `.card.settings-card` pattern,
  no new component.
- Per-artifact row rendering (name/kind/metadata) — **Specced**
  (Scenarios 1, 3); reuses the already-approved `.item-list`/`.item-row`
  family live on `SettingsVaultTemplatesPage.tsx`/`SettingsSectionsPage.tsx`.
- Cross-type grouping + multi-select selection UI (checkboxes, per-kind
  selection counts, clear-selection control) — **`net-new-design-needed`**
  (Scenarios 2, 4) — no approved screen anywhere shows this pattern.

**Why `gate: flagged`:**

1. No material assumption fills a genuine PRD gap in the Gherkin itself —
   every scenario asserts only what the PRD's own text and the operator's
   own breadcrumb already describe (a browsable, multi-selectable,
   cross-type list), grounded against the real, already-`Done` Manager
   layer.
2. `REQ-SB-85` is not marked `<!-- Draft -->`/unfinalised in the PRD — its
   body text and operator breadcrumb are both fully resolved (confirmed
   by direct reading, `Documentation/PRD.md` line 4410 onward).
3. N/A directly (architect/ADR trigger) — this story adds no new entity,
   no new write path, and composes only already-real Managers; not
   expected to need a new ADR on its own.
4. No `ESCALATIONS.md` entry written by this pass.
5. Not oversized — 2 tasks, a pure read/compose backend endpoint plus one
   new frontend page.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **The controlling flag: `net-new-design-needed`** — the cross-type
   multi-select browser has no prior approved screen anywhere in
   `html-prototype/` (confirmed directly against the catalog's own full
   screen list before writing this story). Recommend a single
   `/design REQ-SB-85` pass covering this story's browser alongside its
   two siblings' own net-new screens (`US-02`'s dependency-preview/
   secret-scan confirmation screens, `US-03`'s upload/conflict-resolution
   screen) as one related flow, before `/plan-tasks` cuts any frontend
   task.

gate: clear 2026-08-31 — trigger-8/net-new-design-needed was the only
trigger, resolved directly by the operator the same day (build
functional-first, design after — see frontmatter `gate_reason`). The
`REVIEW-QUEUE.md` entry is updated to reflect this, not deleted.

**Architect pass (2026-08-31) — `/plan-tasks` step 1:** No new/changed
ADR — this story composes only already-Accepted Manager gateways
(`SkillManager`/`TemplateManager`/`AgentManager`/`PipelineManager`, all
`REQ-SB-80`, `Done`) via the existing `business/logic/` cross-entity
composition pattern (`section_agents.py`/`cockpit_view.py`/
`system_health.py` precedent) — no new store, no write path, no new
structural boundary. `REQ-SB-85-US-02`/`US-03` (siblings) needed real new
ADRs (`ADR-013`/`ADR-014`/`ADR-015`) for the export/import machinery this
story's own browser feeds into.

**Architecture scope: §Artifact Inventory Composition** —
`Implementation/Architecture/architecture.md`, updated 2026-08-31. The
decomposer/coder are bounded to this section; the cross-type multi-select
selection UI's own visual treatment is deliberately NOT architecturally
specified beyond "reuse `.item-list`/`.item-row`/`.card.settings-card`,
functional-first" (net-new-design-needed, deferred to a later `/design`
pass per the operator's own same-day override — see frontmatter).

gate: clear 2026-08-31 — architect pass, no trigger fired (no ADR
created/changed, no material assumption, requirement finalised).

**Decomposer pass (2026-08-31) — `/plan-tasks` step 2:** All 5 scenarios
tightened and locked as `REQ-SB-85-US-01-AC-01`..`AC-05` (wording
tightened for buildability, intent unchanged from the analyst's own
untagged Gherkin). Two tasks created (`T01` backend list-composition
endpoint, `T02` frontend browser/multi-select page), matching the
story's own pre-sketched Implementation Tasks table exactly — no further
split needed, this is genuinely the smallest of the three `REQ-SB-85`
substories (a pure read/compose endpoint plus one new page). `T02`
depends on `T01` (needs `GET /artifacts` to exist to wire the page
against); `T01` has no dependency (composes only already-`Done`
Managers). No cross-story dependency FROM this story (it is the
foundational entry point `US-02`/`US-03`'s own frontend tasks depend on,
not the other way around). No MUST-FLAG trigger fired at this step (no
new assumption, no AC left unverifiable, `depends_on` acyclic) — status
advances `Draft → Ready`, `gate` stays `clear`.

**Coder pass (2026-08-31) — `T01` `Done`:** `app/business/logic/
artifacts_inventory.py` + `GET /artifacts` (`app/api/artifacts_router.py`)
built and registered in `main.py`. `AC-01`/`AC-03` both verified live
against the real deployment (70 real artifacts across the 4 kinds,
id-set/count cross-checked directly against each real Manager's own
`get_all()`); `AC-03`'s own zero-artifact condition and the malformed-
Template DoD checkbox were both induced honestly via a scoped, reverted
in-process monkeypatch of the real Manager functions (no kind is
naturally empty and no Template is naturally malformed on this real
deployment today) — see `T01`'s own `## Implementation Log` for the full
detail. No MUST-FLAG trigger fired. Story status moves `Ready → In
Progress` (`T02`, the frontend browser page, is still outstanding).
`gate: clear 2026-08-31`.

**Coder pass (2026-08-31) — `T02` `Done`, story `Done`:** `SettingsArtifactsPage.tsx`
+ `artifactsApiClient.ts` (both new), one new `SettingsPage.tsx` card, one
new `App.tsx` route, built and verified live via a headless-Edge CDP
session against the real running app (real backend on `127.0.0.1:8001`,
real vault-backed 70 real artifacts across all 4 kinds). All 5 locked ACs
(`AC-01`..`AC-05`) verified with a real positive result — `AC-03`'s
zero-real-artifact condition used the task's own explicitly-permitted
mocked-filtered-response technique (an in-page `fetch` override in front
of the real endpoint, no backend file touched) since no kind is naturally
empty on this deployment today. See `T02`'s own `## Implementation Log`
for the full detail. No MUST-FLAG trigger fired. Both story tasks are now
`Done` — story status moves `In Progress → Done`. `gate: clear 2026-08-31`.
