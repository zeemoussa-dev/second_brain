---
id: REQ-SB-85-US-03
title: Import — upload a `.sbf` bundle, per-artifact conflict resolution, real target-machine provisioning
requirement_ids: [REQ-SB-85]
requirement_section: "REQ-SB-85: Artifact Export/Import — Portable Capability Bundles (`.sbf`)"
phase: P2
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-015 created; ADR-014 also newly created this same architect pass and shared with US-02) — architect pass 2026-08-31, see ## Notes and REVIEW-QUEUE.md; decomposer proceeds regardless per Pipeline.md. Prior gate_reason (net-new-design-needed, resolved directly by the operator 2026-08-31: build functional-first, design pass comes AFTER the task works, matching REQ-SB-82-US-06-T07/T08's own precedent) is preserved below in ## Notes, not erased — the upload/preview and per-artifact conflict-resolution screens still have zero `html-prototype/` coverage, and /plan-tasks/the coder should still build a plain, functional treatment using existing app conventions. See `REVIEW-QUEUE.md`."
sprint: SPRINT-080
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03 — Import — upload a `.sbf` bundle, per-artifact conflict resolution, real target-machine provisioning

## Story

**As a** Second Brain operator on a target deployment
**I want** to upload a `.sbf` bundle, see what it genuinely contains, be
asked explicitly what to do with every artifact that already exists on
this machine, and have every artifact actually, fully deployed — not just
unpacked
**So that** a capability someone shared with me (or I built on another
machine) ends in a genuinely working deployment here, with no data loss
and no half-wired files left behind

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-85* — "upload a `.sbf` file
  through the same Settings surface: the system deploys the real skill
  folders into the right Hermes profile location(s), creates/clones the
  real Agent profile(s) (via Hermes' own import where a whole profile was
  bundled), writes the Template.json file(s) into the target vault, and
  drops any seed/blank data files — ending in a genuinely working
  deployment, not a pile of unwired files. Any artifact id that already
  exists on the target machine is a real, per-artifact conflict, never
  resolved silently: the operator is asked overwrite / skip / keep both
  for each one." Import-conflict handling is directly confirmed by the
  operator, verbatim (breadcrumb below), unlike `US-02`'s own secret-scan
  action verbs, which the PRD leaves unenumerated.
- **Third substory of `REQ-SB-85`'s own 3-way split** — see
  `REQ-SB-85-US-01`'s own Context for the full split rationale. This
  story owns everything that happens once a real `.sbf` (produced by
  `REQ-SB-85-US-02`, or received from elsewhere) is uploaded.
- **PRD breadcrumb (2026-08-31, operator, verbatim):** "in import we do
  the same import --> upload a file *.sbf." Confirmed further via
  follow-up (per the PRD body's own text) that overwrite/skip/keep-both
  is asked for EVERY conflicting artifact individually, never once for
  the whole bundle.
- **Per-kind provisioning mechanism, grounded directly against real,
  already-`Done` code — not assumed:**
  - **Skill:** `SkillManager.deploy(skill_id, profile_id)` already exists
    and does exactly the "push this Skill's current content to one more
    real Hermes profile" operation a fresh deploy needs (confirmed by
    direct reading, `business/core/skills/skill_manager.py`) — this
    story's own new work is choosing WHICH profile(s) to deploy to on the
    target machine and wiring the conflict/no-conflict decision into it,
    not reimplementing the deploy mechanism itself.
  - **Agent:** two real, confirmed paths depending on what the bundle
    carries (see `US-02`'s own Scenario 6 — every Agent artifact's export
    always carries BOTH pieces): (1) the bundled Hermes profile
    sub-archive is restored via Hermes' own real `import_profile`
    (`hermes profile import <archive> [--name <name>]`, confirmed
    path-escape-safe and already raising `FileExistsError` on a genuine
    name collision — exactly the real signal a conflict decision needs);
    (2) the bundled Registry-side `Agent.json` data is written via the
    SAME real writer `AgentManager` already uses
    (`data_access/registry/writer.py::write_agent_files`) once the
    profile itself exists. **A confirmed real mechanism for "keep both":**
    `import_profile`'s own `name` parameter lets the imported profile
    land under a different id than the archive's own top-level directory
    name — this is the exact, already-real primitive a "keep both" choice
    would use, not new Hermes-side work. **A confirmed real mechanism for
    "overwrite":** `AgentManager.delete(agent_id)` (already exists, real
    Hermes profile deletion + Registry folder cleanup) run first, then a
    fresh import — matching the same "delete then recreate" shape
    `AgentManager.update()`'s own section-move logic already uses
    internally for a relocated agent.
  - **Template:** **a real, confirmed gap, not assumed away** —
    `TemplateManager` (`business/core/templates/template_manager.py`) is
    explicitly documented as read-only today (`get_by_id`/`get_all`
    only); `data_access/templates.py` likewise has no
    `write_template_json` function. Writing a `Template.json` into the
    target vault on import is genuinely new write capability this story
    must add — a direct, same-shape extension of the existing
    `read_template_json` primitive (mirrors how `AgentManager`'s own
    `_write_registry_agent` was called out as "the ONE genuinely new
    writer" against an otherwise read-only Registry), not a design fork.
  - **Pipeline:** **the same class of real, confirmed gap** —
    `PipelineManager`/`data_access/pipelines.py` has zero write path of
    any kind today (confirmed by direct reading — `pipeline_manager.py`'s
    own module docstring: "Read-only for now... no create/update/delete
    existed before this and none is built here either"). Writing a new
    `<second_brain_data_path>/pipelines/<id>.json` on import is likewise
    new write capability this story must add.
  - **Seed/blank data files:** e.g. `Entities.md` (confirmed real,
    `data_access/entities.py`) — dropped into the target vault at the
    location the capability expects, genuinely empty, per `US-02`'s own
    Scenario 5 guarantee that the bundle never carried real data in the
    first place.
- **The exact target-profile-selection UX** (which real Hermes profile(s)
  a Skill/Agent gets deployed to on the target machine — e.g. "every
  profile," "a profile the operator picks," or "the profile named inside
  the bundle if it exists, else prompt") is **left open to `/plan-tasks`**
  — the PRD's own text says "deploys... into the right Hermes profile
  location(s)" without specifying the selection mechanism, and this is a
  genuine target-machine-specific decision (a fresh machine may have
  entirely different profile names than the source). The Gherkin below
  asserts only that the deployment ends up genuinely working, not the
  exact profile-selection UI.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Uploading a valid `.sbf` file previews its real contents before anything is deployed

```gherkin
Given the operator has a real `.sbf` file (produced by REQ-SB-85-US-02, or
    received from another deployment)
When the operator uploads it through Settings → Artifacts
Then the system shows what the bundle genuinely contains — every Skill,
    Template, Agent, and Pipeline it carries, and whether each one already
    conflicts with something on this machine — before anything is
    deployed
```
<!-- AC-ID: REQ-SB-85-US-03-AC-01 -->

### Scenario 2: An artifact with no id conflict on the target deploys directly, ending in a genuinely working state

```gherkin
Given the bundle contains an artifact whose id does not already exist on
    the target machine
When the operator commits the import
Then that artifact is fully deployed — a Skill's real folder lands in the
    right Hermes profile location(s), an Agent's real profile is
    created/cloned, a Template's Template.json is written into the target
    vault, and any seed/blank data file it needs is dropped — not merely
    unpacked into a holding area
```
<!-- AC-ID: REQ-SB-85-US-03-AC-02 -->

### Scenario 3: An artifact whose id already exists on the target always triggers an explicit, per-artifact conflict prompt

```gherkin
Given the bundle contains an artifact whose id already exists on the
    target machine
When the operator commits the import
Then the operator is asked, for that specific artifact, to choose
    overwrite, skip, or keep both — never resolved silently, and asked
    independently for every conflicting artifact in the bundle, not once
    for the whole import
```
<!-- AC-ID: REQ-SB-85-US-03-AC-03 -->

### Scenario 4: Choosing "keep both" imports the conflicting artifact alongside the existing one, untouched

```gherkin
Given the operator is asked to resolve a conflict for one artifact
    (Scenario 3)
When the operator chooses "keep both"
Then the imported artifact is deployed under an alternate id/name
  And the existing artifact on the target machine is completely
    unchanged
```
<!-- AC-ID: REQ-SB-85-US-03-AC-04 -->

### Scenario 5: Choosing "overwrite" replaces the existing artifact with the imported one

```gherkin
Given the operator is asked to resolve a conflict for one artifact
    (Scenario 3)
When the operator chooses "overwrite"
Then the existing artifact on the target machine is replaced by the
    imported one
```
<!-- AC-ID: REQ-SB-85-US-03-AC-05 -->

### Scenario 6: Choosing "skip" leaves the existing artifact untouched and does not import that piece

```gherkin
Given the operator is asked to resolve a conflict for one artifact
    (Scenario 3)
When the operator chooses "skip"
Then the existing artifact on the target machine is completely unchanged
  And that one artifact from the bundle is not imported
  And every other, non-conflicting artifact in the same bundle is still
    imported normally
```
<!-- AC-ID: REQ-SB-85-US-03-AC-06 -->

### Scenario 7: A seed/blank data file always imports genuinely empty, never carrying real data

```gherkin
Given the bundle carries a seed/blank data file for a capability that
    needs one to exist (e.g. Entities.md)
When that artifact is deployed (directly, or via an overwrite/keep-both
    resolution)
Then the resulting file on the target machine is genuinely empty
  And no real captured data is ever introduced by an import, matching the
    same capability/data boundary the bundle was produced under
    (REQ-SB-85-US-02)
```
<!-- AC-ID: REQ-SB-85-US-03-AC-07 -->

### Scenario 8: An invalid or corrupted `.sbf` file is rejected cleanly, nothing is deployed

```gherkin
Given the operator uploads a file that is not a genuine, well-formed
    `.sbf` archive
When the system attempts to read it
Then the upload is rejected with a clear, honest error
  And no artifact is deployed and no existing artifact on the target
    machine is touched
```
<!-- AC-ID: REQ-SB-85-US-03-AC-08 -->

### Scenario 9: A failure partway through a multi-artifact import is surfaced honestly, not silently absorbed

```gherkin
Given a bundle with multiple artifacts is being imported and one
    artifact's own deployment step genuinely fails (e.g. the underlying
    Hermes profile import fails)
When the import continues processing the remaining artifacts
Then the failed artifact is reported honestly as failed, not silently
    dropped or falsely reported as succeeded
  And every other artifact's own real deployment outcome (succeeded or
    failed) is reported independently, per artifact
```
<!-- AC-ID: REQ-SB-85-US-03-AC-09 -->

## Affected Screens

- New upload + contents-preview screen, reached from Settings → Artifacts
  (`REQ-SB-85-US-01`) — **`net-new-design-needed`**, no prototype coverage
  anywhere.
- New per-artifact conflict-resolution screen (overwrite/skip/keep-both),
  shown conditionally (Scenario 3) — **`net-new-design-needed`**.
- `html-prototype/` — confirmed (via direct inspection of `index.html`'s
  own full screen catalog before writing this story) to have no
  equivalent flow anywhere.

## Dependencies

- **Blocked by:** `REQ-SB-85-US-01` (Artifact Browser) — shares the same
  Settings → Artifacts entry point.
- **Blocked by:** `REQ-SB-85-US-02` (Export) — this story consumes the
  `.sbf` archive shape that story defines; the two stories must agree on
  one internal archive layout (left to `/plan-tasks` to design once).
- **Blocked by:** `REQ-SB-80` (Second Brain Data Layer, direct build) —
  same real Manager layer (`SkillManager`/`AgentManager`/
  `TemplateManager`/`PipelineManager`), all confirmed `Done`/live, though
  `TemplateManager`/`PipelineManager` both need a genuinely new write path
  added by this story (see Context/Constraints — a confirmed, real gap,
  not assumed).
- **Related to, not blocking:** `REQ-SB-86` (Vault Data Sharing, `.sbd`) —
  a deliberately separate, later, real-data-sharing capability; this
  story never imports real operator data (Scenario 7).
- **External:** the already-installed, already-real Hermes CLI (`hermes
  profile import`), reused via `REQ-SB-85-US-02`'s own new
  `HermesCLI.import_profile` wrapper (built once, shared by both
  stories — not duplicated).

## Constraints

- **Hard boundary, load-bearing:** import never introduces real
  operator/business data — a seed/blank data file always lands empty
  (Scenario 7), matching the same capability/data boundary
  `REQ-SB-85-US-02`'s own export guarantees.
- Every artifact-id conflict is resolved explicitly, per artifact, never
  silently and never batched into one whole-bundle decision (Scenario 3).
- An import always ends in a genuinely working deployment for every
  successfully-deployed artifact — a Skill actually lands in a real
  Hermes profile's own `skills/`, an Agent's real profile actually exists
  and its Registry data is actually written, a Template.json actually
  lands in the target vault — never a partially-unpacked archive left for
  the operator to wire up by hand (Scenario 2).
- A failed artifact's own deployment is always reported honestly,
  independently of every other artifact in the same bundle (Scenario 9) —
  matches this project's standing "honest, not silent" posture
  (`MEMORY.md`).
- Writing `Template.json`/Pipeline JSON on import is new write capability
  this story adds to otherwise-read-only Managers — a same-shape
  extension of the existing read primitive in each case, not a design
  fork (see Context).
- The exact target-profile-selection mechanism for Skill/Agent deployment,
  and the exact conflict-resolution screen's visual treatment, are left
  open to `/plan-tasks`/`/design` (see Context/Notes).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-85-US-03-T01 | backend | `.sbf` archive reader/validator — parses an uploaded bundle into its real per-artifact contents for preview; rejects a malformed archive cleanly | `app/business/` (new module, shares shape with `REQ-SB-85-US-02`'s writer) | `../Tasks/REQ-SB-85-US-03-T01-sbf-archive-reader.md` |
| REQ-SB-85-US-03-T02 | backend | Per-artifact conflict detection against the target machine's own real current state, across all 4 kinds | `app/business/` (new module) | `../Tasks/REQ-SB-85-US-03-T02-conflict-detection.md` |
| REQ-SB-85-US-03-T03 | backend | Template.json write path (new — extends `data_access/templates.py`/`TemplateManager`) | `app/data_access/templates.py`, `app/business/core/templates/template_manager.py` | `../Tasks/REQ-SB-85-US-03-T03-template-write-path.md` |
| REQ-SB-85-US-03-T04 | backend | Pipeline JSON write path (new — extends `data_access/pipelines.py`/`PipelineManager`) | `app/data_access/pipelines.py`, `app/business/core/pipelines/pipeline_manager.py` | `../Tasks/REQ-SB-85-US-03-T04-pipeline-write-path.md` |
| REQ-SB-85-US-03-T05 | backend | Import orchestrator — deploys each artifact per its resolved conflict decision (Skill via `SkillManager.deploy`, Agent via `HermesCLI.import_profile` + Registry write, Template/Pipeline via T03/T04, seed files empty); `POST /artifacts/import` endpoint | `app/api/artifacts_router.py`, `app/business/` (new module) | `../Tasks/REQ-SB-85-US-03-T05-import-orchestrator.md` |
| REQ-SB-85-US-03-T06 | frontend | Upload + contents-preview + per-artifact conflict-resolution screens, wired from the Import action on `SettingsArtifactsPage.tsx` | `src/frontend/src/pages/SettingsArtifactsPage.tsx`, `src/frontend/src/features/settings/artifactsApiClient.ts` | `../Tasks/REQ-SB-85-US-03-T06-import-flow-ui.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Producing a `.sbf` file** — `REQ-SB-85-US-02`.
- **Real vault-data import (`.sbd`)** — `REQ-SB-86`, deliberately separate
  and not yet designed.
- **Undo/rollback of a completed import** — not requested by the PRD;
  overwrite/keep-both/skip are the only resolution mechanisms this story
  builds.
- **Automatic conflict resolution of any kind** (e.g. "always overwrite")
  — every conflict is always asked explicitly (Constraints).
- **Cross-machine transport of the `.sbf` file itself** (e.g. email, a
  file-share integration) — the PRD's own text describes a plain
  upload-through-Settings mechanism; how the file physically reaches the
  target machine is the operator's own business, not this story's.

## Notes

**Prototype parity:**

- Upload + contents-preview screen — **`net-new-design-needed`**
  (Scenario 1) — no prototype coverage anywhere.
- Per-artifact conflict-resolution screen — **`net-new-design-needed`**
  (Scenarios 3-6) — no prototype coverage anywhere.
- Per-artifact deployment outcome reporting (Scenarios 2, 8, 9) — no
  distinct new visual region beyond the two screens above; expected to
  compose from already-approved primitives (e.g. the existing honest-
  error-detail pattern `Agent Activity`/`System Health` already use), not
  called out separately here.

**Why `gate: flagged`:**

1. No material assumption fills a genuine PRD gap in the Gherkin itself —
   every scenario asserts only what the PRD's own text (including its
   directly-confirmed overwrite/skip/keep-both mechanism) already
   describes. Two real, confirmed technical gaps (Template/Pipeline write
   paths) are disclosed in Context/Constraints as buildable, same-shape
   extensions, not guessed around.
2. `REQ-SB-85` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A directly here (architect/ADR trigger) — but `/plan-tasks` should
   expect the new Template/Pipeline write paths and the import
   orchestrator's own overwrite/keep-both mechanics to be real,
   ADR-worthy additions — flagged as a likely trigger for the architect
   step, not resolved here.
4. No `ESCALATIONS.md` entry written by this pass.
5. **Genuinely large** — an archive reader, per-artifact conflict
   detection across 4 kinds, two brand-new write paths (Template,
   Pipeline), a multi-mechanism deployment orchestrator (Skill/Agent/
   Template/Pipeline each provisioned differently), and two new frontend
   screens. Kept as ONE story here for the same reason as `US-02`
   (tightly sequential, one shared archive-shape decision) — flagged for
   the decomposer to weigh a further task-level split.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **The controlling flag: `net-new-design-needed`** for the two new
   screens (upload/preview, conflict resolution) — no prototype coverage
   anywhere. The exact target-profile-selection UX for Skill/Agent
   deployment is also left open (not a blocking ambiguity — the Gherkin
   only asserts the deployment ends up genuinely working, not the
   selection mechanism).

gate: clear 2026-08-31 — trigger-8/net-new-design-needed (two new
screens with zero prototype coverage) resolved directly by the operator
the same day (build functional-first, design after — see frontmatter
`gate_reason`); two disclosed, non-blocking real technical gaps
(Template/Pipeline write paths, both buildable same-shape extensions)
stand as recorded. The `REVIEW-QUEUE.md` entry is updated to reflect
this, not deleted. A real `/design REQ-SB-85` pass (covering this
story's screens alongside `US-01`/`US-02`'s own) is still expected
later, after the functional build — not a precondition for
`/plan-tasks` anymore.

**Architect pass (2026-08-31) — `/plan-tasks` step 1:**

- **One new ADR appended, one shared ADR cited** (trigger-3 fires, story
  stays `gate: flagged` — decomposer runs next regardless, per
  Pipeline.md):
  - **`ADR-015`** (new) — `TemplateManager`/`PipelineManager` gain a
    real, narrowly-scoped write path (`write_template_json`/
    `write_pipeline_json` in each's `data_access` sibling, plus a matching
    create/import method on each Manager) — a disclosed, scoped reversal
    of each module's own documented "read-only for now" stance, built
    ONLY to support this story's own import provisioning (no general
    Templates/Pipelines authoring UI). Both modules' own header
    docstrings must be updated by the coder as part of Definition of Done
    (see `ADR-015`'s own Decision).
  - **`ADR-014`** (cited, created this same pass alongside `US-02`) —
    `HermesCLI.export_profile`/`import_profile` is this story's own real
    mechanism for the Agent kind's conflict detection/"keep both"
    (`import_profile`'s own `--name` override) and "overwrite"
    (`AgentManager.delete()` then a fresh import).
- **Architecture scope: §Template/Pipeline Write-Path Additions & Import
  Orchestration (`ADR-015`), §Hermes Profile Export/Import Reuse
  (`ADR-014`), §Dependency Closure, Secret Scan & `.sbf` Archive Format
  (`ADR-013`, read-side/format only — this story is a consumer, not an
  author, of the format)** — `Implementation/Architecture/architecture.md`,
  updated 2026-08-31. The decomposer/coder are bounded to these sections;
  the upload/preview and per-artifact conflict-resolution screens' own
  visual treatment is deliberately NOT architecturally specified beyond
  "reuse existing app conventions, functional-first" (net-new-design-
  needed, deferred per the operator's own same-day override above).

**Decomposer pass (2026-08-31) — `/plan-tasks` step 2:**

- All 9 scenarios tightened and locked as `REQ-SB-85-US-03-AC-01`..`AC-09`
  (`AC-01`'s own Then clause tightened to also cover "whether each
  artifact already conflicts" — the same preview screen Scenario 3 relies
  on to show the operator a conflict before asking them to resolve it;
  intent unchanged from the analyst's own untagged Gherkin, wording made
  concrete for buildability).
- **The target-profile-selection UX (left explicitly open by the
  story/PRD) is resolved here, as authorized:** on import, the operator
  is shown the target machine's own real, current Hermes profile list
  (`get_client().profiles.get_all()`) as a checkbox list per bundled
  Skill artifact, **defaulting to the target's own root/"default"
  profile pre-checked** (every real Hermes install has this one, so the
  default always yields a genuinely working deployment per `AC-02` with
  zero required operator action) — the operator may check additional/
  different real profiles before committing. Chosen specifically to avoid
  extending `ADR-013`'s own already-Accepted, frozen manifest shape (no
  new `deployed_to`-on-manifest field needed) — a source-machine
  "which profiles was this deployed to" hint would have required
  reopening that ADR for a cosmetic UX improvement, not a genuine
  correctness need. Documented in `T05`/`T06`'s own task files; not a
  blocking ambiguity (`AC-02` only requires the deployment ends up
  genuinely working, which the always-available root-profile default
  guarantees).
- **6 tasks**, matching the story's own pre-sketched table exactly
  (`T01` archive reader, `T02` conflict detection, `T03` Template write
  path, `T04` Pipeline write path, `T05` import orchestrator + endpoint,
  `T06` frontend). Not split further — `ADR-015`'s own narrow, disclosed
  write-path scope keeps `T03`/`T04` each a small, same-shape sibling
  addition; `T05` is the one genuinely large task (a real 4-kind
  multi-mechanism deployment orchestrator) but stays cohesive since every
  kind's own deploy step shares the same per-artifact conflict-decision
  loop.
- **Cross-story dependency edges recorded:** `T01` depends on
  `REQ-SB-85-US-02-T04` (shares the `sbf_archive.py` module the writer
  creates — reader is its real counterpart in the same file, per
  `ADR-013`'s own "writer and reader share this one module" Decision).
  `T02` depends on `T01` (needs the parsed bundle's own per-artifact ids
  to check for conflicts). `T05` depends on `T01`/`T02`/`T03`/`T04` (
  composes all four) AND on `REQ-SB-85-US-02-T01` (the SAME `HermesCLI`
  edit already adds both `export_profile` AND `import_profile` — `T05` is
  the real first caller of the import half). `T06` (frontend) depends on
  `T05` (needs the preview/commit import endpoints) AND on
  `REQ-SB-85-US-01-T02` (needs `SettingsArtifactsPage.tsx`'s own Import
  entry point). `T03`/`T04` have no dependency on one another or on
  `T01`/`T02` — each is an independent, same-shape write-path addition
  buildable directly against its own already-`Done` read-side Manager.
- No MUST-FLAG trigger fired AT THIS STEP beyond the already-recorded
  trigger-3 (the architect's own `ADR-015`, `ADR-014` cited, preserved
  above) — no new material assumption beyond the disclosed, non-blocking
  target-profile-selection UX call above, every locked AC has a genuine,
  mapped verification step, `depends_on` is acyclic (a 6-node DAG:
  `T01→T02`, `T01/T02/T03/T04→T05`, `T05→T06`, plus the two cross-story
  edges above — no cycle). Status advances `Draft → Ready`; `gate` stays
  `flagged` (trigger-3 from the architect pass is not this step's to
  clear — the human still reviews `ADR-015`/`ADR-014` per the existing
  `REVIEW-QUEUE.md` entry).

**Coder pass (2026-09-01) — `/implement-sprint`, `T06` (final task):**

- All 6 tasks now `Done`: `T01`-`T04` (archive reader, conflict detection,
  Template/Pipeline write paths), `T05` (import orchestrator +
  `/artifacts/import/{preview,commit}`, 8 of 9 locked ACs independently
  verified live, `AC-08` deferred to `T01`'s own already-verified scope),
  `T06` (upload/preview + per-artifact conflict-resolution UI — the
  remaining 5 tagged ACs, `AC-01`/`AC-03`/`AC-04`/`AC-05`/`AC-06`/`AC-08`/
  `AC-09`, all independently verified live via a real headless-browser CDP
  session against the real running frontend + backend). Every one of this
  story's 9 locked ACs (`AC-01`-`AC-09`) is now independently verified live
  across `T05`/`T06` — `AC-02`/`AC-07` at `T05`, the rest split as recorded
  in each task's own Implementation Log.
- **Story `status` → `Done`.** `gate` stays `flagged` — carried forward,
  not silently cleared: the architect-pass trigger-3 (`ADR-015` new,
  `ADR-014` cited) still awaits human review per the open
  `REVIEW-QUEUE.md` entry, and `T05`'s own two disclosed findings (a
  scope-internal Skill-metadata-parsing assumption; a real, pre-existing
  `SkillManager.delete()` Hermes-id-form bug, not fixed here) also remain
  open. `T06` added its own two scope-internal judgement calls (a shared
  error-message helper's fallback string generalized for correctness
  across both Export/Import flows; Import card placement/layout, since the
  screen is `net-new-design-needed` with zero prototype coverage) — logged
  in `T06`'s own Implementation Log, not blocking.
- No new `ESCALATIONS.md` entry — no out-of-scope event, no new
  dependency, no shared-interface change beyond what `T05` already
  disclosed. The stale `--reload` backend dev-server found at the start of
  `T06` (missing `T05`'s own already-`Done` routes) was an environment
  hygiene issue, not a code defect — resolved by restarting a fresh,
  non-`--reload` instance, logged in `T06`'s own Implementation Log.
