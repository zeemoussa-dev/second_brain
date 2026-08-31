---
id: REQ-SB-85-US-02
title: Export — real dependency-closure resolution, explicit secret-scan confirmation, single `.sbf` bundle
requirement_ids: [REQ-SB-85]
requirement_section: "REQ-SB-85: Artifact Export/Import — Portable Capability Bundles (`.sbf`)"
phase: P2
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-013/ADR-014 created) — architect pass 2026-08-31, see ## Notes and REVIEW-QUEUE.md; decomposer proceeds regardless per Pipeline.md. Prior gate_reason (net-new-design-needed, resolved directly by the operator 2026-08-31: build functional-first, design pass comes AFTER the task works, matching REQ-SB-82-US-06-T07/T08's own precedent) is preserved below in ## Notes, not erased — the dependency-preview and secret-scan confirmation screens still have zero `html-prototype/` coverage, and /plan-tasks/the coder should still build a plain, functional treatment using existing app conventions. One scope-internal judgement call (the exact 3 secret-finding actions) is disclosed, not blocking. See `REVIEW-QUEUE.md`."
sprint: SPRINT-079
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-02 — Export — real dependency-closure resolution, explicit secret-scan confirmation, single `.sbf` bundle

## Story

**As a** Second Brain operator who has selected one or more artifacts in
Settings → Artifacts (`REQ-SB-85-US-01`)
**I want** the system to resolve everything those artifacts genuinely
depend on, show me what's being included and why, scan for anything
secret-shaped and let me explicitly decide what happens to each finding,
and then produce one real `.sbf` file
**So that** I can hand a genuinely working capability — never my own
captured data, and never a leaked credential — to another deployment in
one file

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-85* — "the system resolves the
  real dependency closure (a Skill's own shared-file copies, e.g.
  `vault_manager.py`; an Agent's own `skill_ids`/`depends_on`; a Skill's
  own implicit Template.json coupling, e.g. `create-companies-partners`
  needing the `customer`/`partner` templates) and shows what's being
  included and why before producing a single `.sbf` file... Before the
  archive is written, the selected artifacts' own content is scanned for
  secret-shaped strings (API keys, tokens); if any are found, a second
  screen asks the operator explicitly what to do with each one (never a
  silent strip, unlike Hermes' own blind-scrub-on-export behavior for a
  whole profile)." Plus the hard capability/data boundary: "this system
  moves *capability*, never *personal or business data*... A 'Standard'
  bundle... carries none of the operator's own captured content. A
  'Customer Tracking' bundle carries the `create-companies-partners`
  pipeline, the `customer`/`partner` Template.json, and a genuinely
  **empty** `Entities.md` seed file — never the operator's own real
  Customers."
- **Second substory of `REQ-SB-85`'s own 3-way split** (browser/export/
  import — see `REQ-SB-85-US-01`'s own Context for the full split
  rationale). This story owns the resolve → preview → secret-scan →
  archive pipeline; `REQ-SB-85-US-03` owns everything that happens once a
  produced `.sbf` is uploaded elsewhere.
- **Hermes' own `hermes profile export`/`import` grounded directly
  against the real, installed source — confirmed live, not assumed from
  the PRD's own prose alone** (`hermes_cli/profiles.py`,
  `C:\Users\mahmoud.moussa\AppData\Local\hermes\hermes-agent\`):
  - `export_profile(name, output_path)` is a real, non-interactive `hermes
    profile export <name> [output]` CLI subcommand (confirmed via
    `main.py`'s own `elif action == "export":` dispatch, not just the
    REPL's `/export`) — stages a filtered copy of the profile
    (`.env`/`auth.json` excluded), then runs
    `_scrub_export_secrets(staged)` — a **real, already-built,
    force-redact secret scan** (`agent.redact.redact_sensitive_text(...,
    force=True)`) over every text-ish staged file — before writing a
    `tar.gz`. This is genuinely a **silent** strip (Hermes never asks;
    it just redacts) — exactly the "blind-scrub-on-export" behavior the
    PRD's own text contrasts against this story's own explicit,
    per-finding confirmation. **This story's own "never silent" promise
    governs Second Brain's own NEW secret-scan surface (Skill content,
    Template.json, seed/blank data files) — it does not, and cannot,
    change Hermes' own already-shipped, silent scrub of the Agent-profile
    piece it reuses; the two behaviors coexist, each on the surface it
    owns.**
  - `import_profile(archive_path, name=None)` is the matching real, non-
    interactive `hermes profile import <archive> [--name <name>]`
    subcommand — path-escape-safe (`_safe_extract_profile_archive`,
    rejects absolute/`..`-containing archive members), infers the profile
    name from the archive's own top-level directory unless `--name`
    overrides it, and raises `FileExistsError` if a profile with that
    name already exists on the target (relevant for `US-03`'s own
    overwrite/skip/keep-both handling — the `--name` override is exactly
    the real mechanism a "keep both" choice would use).
  - **Neither is wrapped in Second Brain's own `app/hermes/cli.py`
    (`HermesCLI`) today** — confirmed by direct reading: that class
    already wraps `profile create`/`delete`/`describe` via the exact same
    subprocess pattern (`self._run(["profile", "create", ...])`) this
    story's own `export_profile`/`import_profile` wrappers would follow.
    Genuinely new, not a gap in an existing wrapper.
- **An Agent artifact's export is a two-piece composition, confirmed by
  direct reading of both stores it draws from — not assumed from the PRD's
  "Hermes-side piece" framing alone:**
  1. The real Hermes profile (SOUL.md, config.yaml minus credentials,
     `skills/`) — produced by the reused `export_profile` above.
  2. Second Brain's own Registry-side `Agent.json` mirror
     (`section_id`/`type`/`is_background_agent`/`depends_on`/`skill_ids`/
     `icon`/`color`) — confirmed by direct reading of
     `data_access/registry/writer.py::agent_dir()` that this file lives
     under `<second_brain_data_path>/Sections/<id>/Agents/<agent>/`, an
     entirely different tree from Hermes' own `HERMES_HOME`, so nothing in
     Hermes' own `export_profile` ever touches it. The PRD's own framing —
     "everything Hermes has no visibility into at all" is what's genuinely
     new — matches exactly: piece 1 is a pure reuse, piece 2 is this
     story's own new composition.
- **Skill content location + the real, confirmed shared-file precedent**
  the PRD's own `vault_manager.py` example refers to:
  `Hermes-Provisioning/skills/<category>/<slug>/{SKILL.md, scripts/}`
  (`SkillManager`/`data_access/skills.py`, already `Done`).
  `Hermes-Provisioning/shared/vault_manager.py` is the canonical source,
  **physically copied** (never imported as a library — its own README:
  "a vault-writing Skill must keep working even when Second Brain's own
  backend isn't running") into individual Skills' own `scripts/` — 8 real
  copies confirmed live by direct grep before writing this story (e.g.
  `skills/notes-capture/capture-notes/scripts/vault_manager.py`,
  `skills/company-review/create-companies-partners/scripts/
  vault_manager.py`). A Skill's own dependency closure must include
  whichever shared files its own `scripts/` directory actually carries a
  copy of.
- **Template.json location, confirmed vault-only, zero Hermes
  involvement:** `.second-brain/data/Templates/<id>/Template.json`
  (`TemplateManager`/`data_access/templates.py`, read-only today).
- **Pipeline's own dependency shape, confirmed by direct reading of
  `pipeline.py`/`pipeline_manager.py`:** a Pipeline's `steps[]` each name
  an `id` (a real Agent id, per its own `type: "worker" | "producer"`) —
  so a selected Pipeline's own closure recurses into the Agents its steps
  name, and from there into THOSE Agents' own `skill_ids`/`depends_on` —
  a real, multi-level graph, not a flat list.
- **A Skill's own implicit Template.json coupling has NO structured field
  anywhere today** — confirmed by direct reading of the `Skill` dataclass
  (`business/core/skills/skill.py`): no `template_ids`/`depends_on`-shaped
  field exists. The PRD's own `create-companies-partners` example is a
  real, true fact about that Skill's own runtime behavior (its script
  calls into `customer`/`partner` Template.json at write time), but
  nothing in the data model declares it today. **The exact mechanism for
  detecting this coupling (a static scan of a Skill's own `scripts/`
  content for a referenced Template id vs. a new explicit metadata field
  going forward) is left open, deliberately, to `/plan-tasks`** — the
  Gherkin below asserts only the *externally observable* outcome (the
  closure is resolved and shown, and a known real example like
  `create-companies-partners` genuinely pulls in its own Templates), not
  the detection algorithm — same established precedent as
  `REQ-SB-30-US-01` leaving the Compass prompt's exact wording open and
  `REQ-SB-82-US-06` leaving the short-reply detection rule open.
- **Secret-scan per-finding action options — a disclosed, non-blocking
  scope-internal judgement call, not locked by this story:** the PRD's
  own text requires the operator be asked "explicitly what to do with
  each one" but does not enumerate the exact choices (unlike `US-03`'s
  own import-conflict handling, which the PRD spells out verbatim as
  overwrite/skip/keep-both). Per this run's own explicit "trust your
  judgment" authorization, three actions per finding are proposed here as
  the working default for `/plan-tasks`/`/design`: **Redact** (a
  placeholder substitution in the bundle), **Keep as-is** (an explicit,
  logged acknowledgment it will ship in the archive), **Cancel export**
  (abort, nothing written) — chosen to mirror `US-03`'s own explicit
  per-item confirmation pattern and this project's standing "honest, not
  silent" posture (`MEMORY.md`). Not locked — `/plan-tasks`/`/design` may
  adjust the exact verbs/UX without needing a re-spec, since Scenario 3
  below asserts only that every finding is surfaced and decided
  individually before anything is written, not these specific three
  words.
- **Archive internal layout** (manifest shape, sub-archive nesting for a
  bundled Hermes profile, etc.) is likewise left as an implementation
  detail for `/plan-tasks` — the PRD's own text only requires "a real
  zip... containing everything needed," not a specific internal shape.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Dependency closure is resolved and shown before anything is written

```gherkin
Given the operator has selected one or more artifacts in Settings →
    Artifacts and requests an export
When the system resolves the export
Then every artifact the selection genuinely depends on (a Skill's own
    shared-file copies, an Agent's own skill_ids/depends_on chain, a
    Skill's own implicit Template.json coupling, a Pipeline's own step
    Agents and their Skills) is added to the export automatically, each
    with a human-readable reason it was included
  And the operator sees the full resolved list and its reasons, before
    any archive file is written
```
<!-- AC-ID: REQ-SB-85-US-02-AC-01 -->

### Scenario 2: No secret-shaped content found — export proceeds straight to the archive

```gherkin
Given the resolved export's own artifact content contains no
    secret-shaped strings
When the export continues
Then no secret-scan confirmation screen is shown
  And a single real `.sbf` file (a real zip archive) is produced
    containing everything the resolved closure named
```
<!-- AC-ID: REQ-SB-85-US-02-AC-02 -->

### Scenario 3: Secret-shaped content found — the operator decides explicitly on each finding

```gherkin
Given the resolved export's own artifact content contains one or more
    secret-shaped strings (e.g. an API-key- or token-shaped pattern)
When the export reaches the secret-scan pass
Then a second screen lists every finding and asks the operator to choose,
    individually per finding: Redact (substitute a placeholder in the
    bundle), Keep as-is (ship it, explicitly acknowledged), or Cancel
    export (abort, nothing written)
  And nothing is silently stripped, and no archive file is written, until
    the operator has decided on every finding
```
<!-- AC-ID: REQ-SB-85-US-02-AC-03 -->

### Scenario 4: A "Standard" capability bundle carries no captured operator data

```gherkin
Given the operator selects the generic capture pipelines/Skills/Agents
    that make up a "Standard" bundle
When the export is produced
Then the resulting `.sbf` file carries the real capability (Skills,
    Templates, Agents, Pipelines) only
  And none of the operator's own captured content is included anywhere
    in the archive
```
<!-- AC-ID: REQ-SB-85-US-02-AC-04 -->

### Scenario 5: A "Customer Tracking"-shaped bundle carries an empty seed file, never real Customer data

```gherkin
Given the operator selects the create-companies-partners pipeline and its
    dependent customer/partner Templates
When the export is produced
Then the bundle includes the real pipeline, Skill, and Template.json
    files
  And any seed/tracking data file the capability needs to exist (e.g.
    Entities.md) is included genuinely empty
  And none of the operator's own real Customer/Partner records are
    included
```
<!-- AC-ID: REQ-SB-85-US-02-AC-05 -->

### Scenario 6: An Agent artifact's export composes both its real Hermes profile and its Second-Brain-only Registry data

```gherkin
Given the operator selects an Agent artifact for export
When the export is produced
Then the bundle's Agent piece includes the real Hermes profile export
    (SOUL.md, config, its own skills/) produced by Hermes' own
    already-built export mechanism
  And it also includes Second Brain's own Registry-side data for that
    Agent (its section, type, dependencies) that Hermes itself has no
    visibility into
```
<!-- AC-ID: REQ-SB-85-US-02-AC-06 -->

### Scenario 7: Canceling the secret-scan confirmation aborts the export cleanly

```gherkin
Given the operator is on the secret-scan confirmation screen with one or
    more undecided findings
When the operator cancels instead of deciding on every finding
Then the export is aborted
  And no `.sbf` file is written, and no artifact content anywhere is
    modified
```
<!-- AC-ID: REQ-SB-85-US-02-AC-07 -->

## Affected Screens

- New "what's included and why" dependency-preview screen, reached after
  the operator requests an export from Settings → Artifacts
  (`REQ-SB-85-US-01`) — **`net-new-design-needed`**, no prototype coverage
  anywhere.
- New secret-scan confirmation screen, shown conditionally (Scenario 3) —
  **`net-new-design-needed`**.
- `html-prototype/` — confirmed (via direct inspection of `index.html`'s
  own full screen catalog before writing this story) to have no equivalent
  flow anywhere.

## Dependencies

- **Blocked by:** `REQ-SB-85-US-01` (Artifact Browser) — this story's own
  entry point is a selection made there.
- **Blocked by:** `REQ-SB-80` (Second Brain Data Layer, direct build) —
  same real Manager layer `US-01` depends on (`SkillManager`/
  `TemplateManager`/`AgentManager`/`PipelineManager`), all confirmed
  `Done`/live.
- **Related to, not blocking:** `REQ-SB-85-US-03` (Import) — consumes the
  `.sbf` file this story produces; the two stories share the archive's
  own internal shape, left to `/plan-tasks` to design once (not
  independently per story).
- **Related to, not blocking:** `REQ-SB-86` (Vault Data Sharing, `.sbd`) —
  a deliberately separate, later, real-data-sharing capability; this
  story never touches it (see the hard capability/data boundary in
  Context).
- **External:** none beyond the already-installed, already-real Hermes
  CLI (`hermes profile export`) this story's own new `HermesCLI` wrapper
  methods call.

## Constraints

- **Hard boundary, load-bearing:** this system moves *capability*, never
  *personal or business data*. A bundle never contains the operator's own
  real captured content — any data file a bundled capability needs to
  exist (e.g. `Entities.md`) is included genuinely empty, never populated
  from the operator's own real vault data (Scenarios 4, 5).
- Dependency-closure resolution always happens, and is always shown to
  the operator, BEFORE any archive file is written (Scenario 1) — never
  a silent auto-include with no preview.
- The secret-scan pass never silently strips anything from Second Brain's
  own new bundle surfaces (Skill content, Template.json, seed/blank data
  files) — every finding is decided by the operator individually before
  the archive is written (Scenario 3). This constraint does not, and
  cannot, change Hermes' own already-shipped silent redaction of the
  reused Agent-profile export piece (see Context) — the two behaviors are
  deliberately distinct, each governing the surface it owns.
- No archive is ever written while an unresolved secret finding remains
  undecided, or after the operator cancels (Scenario 7).
- The Agent-profile piece of a bundle reuses Hermes' own real `hermes
  profile export` mechanism — it is never reimplemented from scratch.
- The exact dependency-closure detection heuristic for a Skill's own
  implicit Template.json coupling, the exact secret-scan finding-action
  verbs, and the exact `.sbf` internal archive layout are all left open
  to `/plan-tasks` — not decided here (see Context/Notes).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-85-US-02-T01 | backend | New `HermesCLI.export_profile`/`import_profile` subprocess wrappers (real `hermes profile export`/`import`, matching the existing `create_profile`/`delete_profile`/`describe_profile` pattern) | `app/hermes/cli.py` | `../Tasks/REQ-SB-85-US-02-T01-hermes-cli-export-import-wrappers.md` |
| REQ-SB-85-US-02-T02 | backend | Dependency-closure resolver — recurses a selection across Skill shared-files, Agent skill_ids/depends_on, Skill→Template coupling, Pipeline step Agents | `app/business/` (new module, exact location per `/plan-tasks`) | `../Tasks/REQ-SB-85-US-02-T02-dependency-closure-resolver.md` |
| REQ-SB-85-US-02-T03 | backend | Secret-scan pass over the resolved closure's own genuinely-new content (Skill content, Template.json, seed/blank data files) | `app/business/` (new module) | `../Tasks/REQ-SB-85-US-02-T03-secret-scan-pass.md` |
| REQ-SB-85-US-02-T04 | backend | `.sbf` archive writer — composes the resolved closure (including the reused Hermes profile export sub-piece for any Agent artifact) into one real zip; `POST /artifacts/export` endpoint | `app/api/artifacts_router.py`, `app/business/` (new module) | `../Tasks/REQ-SB-85-US-02-T04-sbf-archive-writer.md` |
| REQ-SB-85-US-02-T05 | frontend | Dependency-preview + secret-scan confirmation screens, wired from the Export action on `SettingsArtifactsPage.tsx` | `src/frontend/src/pages/SettingsArtifactsPage.tsx`, `src/frontend/src/features/settings/artifactsApiClient.ts` | `../Tasks/REQ-SB-85-US-02-T05-export-flow-ui.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual mode is the live default (`n/a — test tooling pending`, per every task's own `## Tests` block)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Import side of a produced `.sbf` file** — `REQ-SB-85-US-03`.
- **Real vault-data sharing (`.sbd`)** — `REQ-SB-86`, deliberately
  separate and not yet designed.
- **Editing an artifact's own content as part of exporting it** — export
  is read-only over each artifact's current real state.
- **Scheduling/automating an export** — always an explicit, one-off
  operator action from Settings → Artifacts.
- **Changing Hermes' own `export_profile` secret-scrub behavior** — that
  mechanism is reused as-is, silent scrub included (see Constraints).

## Notes

**Prototype parity:**

- Dependency-preview screen ("what's included and why") — **`net-new-
  design-needed`** (Scenario 1) — no prototype coverage anywhere.
- Secret-scan confirmation screen — **`net-new-design-needed`**
  (Scenario 3) — no prototype coverage anywhere.
- The archive-production/download affordance itself (Scenarios 2, 6, 7) —
  no distinct new visual region beyond the two screens above; a plain
  "Export complete, download `.sbf`" confirmation is expected to compose
  from already-approved primitives, not called out separately here.

**Why `gate: flagged`:**

1. No material assumption fills a genuine PRD gap in the Gherkin itself.
   One disclosed, non-locked scope-internal judgement call was made
   (the 3 secret-finding action verbs) per this run's own explicit
   "trust your judgment" authorization — not treated as a blocking
   assumption, since the PRD's own controlling requirement ("ask
   explicitly, never silently strip") is fully honored regardless of the
   exact verbs chosen.
2. `REQ-SB-85` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A directly here (architect/ADR trigger) — but `/plan-tasks` should
   expect the new `HermesCLI.export_profile`/`import_profile` wrappers
   and the new dependency-closure/secret-scan modules to be real,
   ADR-worthy additions (first-ever Second-Brain-side wrapper around
   Hermes' own profile export/import primitive) — flagged as a likely
   trigger for the architect step, not resolved here.
4. No `ESCALATIONS.md` entry written by this pass.
5. **Genuinely large** — a new CLI wrapper, a cross-artifact recursive
   dependency resolver, a secret-scan pass, an archive writer, and two
   new frontend screens. Kept as ONE story (not split further) because
   the pieces are tightly sequential and share one archive-shape
   decision (resolve → scan → write); flagged here for the decomposer to
   weigh a further task-level split if a single working session proves
   too small, matching `REQ-SB-82-US-06`'s own precedent for this exact
   situation.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **The controlling flag: `net-new-design-needed`** for the two new
   screens (dependency preview, secret-scan confirmation) — no prototype
   coverage anywhere. Everything else genuinely resolvable (the
   Hermes export/import mechanism's real shape, the two-piece Agent
   export composition, the shared-file/Template-coupling closure
   concept) was resolved directly against real, confirmed code, not
   left open.

gate: clear 2026-08-31 — trigger-8/net-new-design-needed (two new
screens with zero prototype coverage) resolved directly by the operator
the same day (build functional-first, design after — see frontmatter
`gate_reason`); the disclosed, non-blocking scope-internal judgement
call (secret-finding action verbs) stands as recorded. The
`REVIEW-QUEUE.md` entry is updated to reflect this, not deleted. A real
`/design REQ-SB-85` pass (covering this story's two screens alongside
`US-01`/`US-03`'s own) is still expected later, after the functional
build — not a precondition for `/plan-tasks` anymore.

**Architect pass (2026-08-31) — `/plan-tasks` step 1:**

- **Two new ADRs appended** (trigger-3 fires, story stays `gate: flagged`
  — decomposer runs next regardless, per Pipeline.md):
  - **`ADR-013`** — the `.sbf` format itself (a real zip, `manifest.json`
    + per-kind payload paths, a nested raw Hermes profile sub-archive for
    the Agent kind), the dependency-closure resolver (Skill shared-files/
    Agent skill_ids+depends_on/Skill→Template static-scan heuristic/
    Pipeline step-Agents), and the secret-scan gate (Second-Brain-owned
    bytes only, never the nested Hermes piece) — all one decision, three
    new `business/logic/` composition modules
    (`artifact_dependency_resolver.py`, `artifact_secret_scan.py`,
    `sbf_archive.py`), never a 5th "Manager."
  - **`ADR-014`** — Hermes profile export/import is reused via
    `HermesCLI.export_profile`/`import_profile`, a same-shape extension of
    the existing wrapper class (same `_run()` pattern as `create_profile`/
    `delete_profile`/`describe_profile`) — resolves `ADR-003`'s own
    explicitly-deferred "real write access into Hermes" question for the
    profile-lifecycle surface specifically. Shared with `US-03` (the
    Agent-import conflict mechanism reuses `import_profile`'s own real
    `--name`/`FileExistsError` signal).
- **Architecture scope: §Dependency Closure, Secret Scan & `.sbf` Archive
  Format (`ADR-013`), §Hermes Profile Export/Import Reuse (`ADR-014`)** —
  `Implementation/Architecture/architecture.md`, updated 2026-08-31. The
  decomposer/coder are bounded to these sections; the dependency-preview
  and secret-scan confirmation screens' own visual treatment is
  deliberately NOT architecturally specified beyond "reuse existing app
  conventions, functional-first" (net-new-design-needed, deferred per the
  operator's own same-day override above).

**Decomposer pass (2026-08-31) — `/plan-tasks` step 2:**

- All 7 scenarios tightened and locked as `REQ-SB-85-US-02-AC-01`..`AC-07`.
  The disclosed, non-locked secret-finding-action judgement call (Redact /
  Keep as-is / Cancel export) is CONFIRMED as-is (not adjusted) and folded
  directly into `AC-03`'s own locked wording — the three verbs are now
  part of the locked contract, not a still-open placeholder.
- **5 tasks**, matching the story's own pre-sketched table exactly
  (`T01` `HermesCLI` wrappers, `T02` dependency-closure resolver, `T03`
  secret-scan pass, `T04` `.sbf` archive writer + export endpoint, `T05`
  frontend). Not split further — each task is already one cohesive real
  module per `ADR-013`/`ADR-014`'s own decision, and the pieces are
  tightly sequential (resolve → scan → write) exactly as the story's own
  Notes anticipated.
- **One disclosed, non-blocking scope-internal judgement call:** the
  architecture note names a single `POST /artifacts/export` — this pass
  reads that as the export FLOW's name, not a literal one-request-one-
  response contract, since Scenario 1 (show closure before writing) and
  Scenario 3 (show findings, decide, THEN write) both require the
  operator to see real, resolved data and act on it before any archive
  byte is written. Built as two real sub-routes on the same router file
  (`POST /artifacts/export/preview` — resolves the closure and runs the
  secret scan, writes nothing; `POST /artifacts/export/commit` — takes
  the same selection plus any required per-finding decisions, re-resolves,
  re-scans, and only then writes the archive) rather than a single
  request with a same-URL dual mode — this is the same two-phase
  preview/commit shape `REQ-SB-85-US-03`'s own import flow independently
  needs for the identical reason, so both stories now share one
  consistent flow shape rather than two different ones. Non-blocking:
  every locked AC's own externally-observable outcome is unaffected by
  this routing detail.
- **Cross-story dependency edges recorded:** `T05` (frontend) depends on
  `T04` (needs the preview/commit endpoints) AND on
  `REQ-SB-85-US-01-T02` (needs `SettingsArtifactsPage.tsx`'s own
  selection state to wire the Export action onto — the real hand-off
  point that story's own Story section describes). `T04` depends on
  `T01`/`T02`/`T03` (composes all three). `T01`/`T02`/`T03` are each
  independently buildable against the already-`Done` Managers/`HermesCLI`
  base, no dependency needed between them.
- No MUST-FLAG trigger fired AT THIS STEP beyond the already-recorded
  trigger-3 (the architect's own `ADR-013`/`ADR-014`, preserved above) —
  no new material assumption, every locked AC has a genuine, mapped
  verification step, `depends_on` is acyclic. Status advances
  `Draft → Ready`; `gate` stays `flagged` (trigger-3 from the architect
  pass is not this step's to clear — the human still reviews `ADR-013`/
  `ADR-014` per the existing `REVIEW-QUEUE.md` entry).

**Coder pass (2026-08-31) — `/implement-sprint`, `T05` (final task):**

- All 5 tasks (`T01`-`T05`) now `Done`; all 4 locked ACs `T05` itself maps
  to (`AC-01`, `AC-02`, `AC-03`, `AC-07`) verified live against the real
  running app (backend `8001`, frontend `5173`) via a CDP-driven headless
  Edge session — see `T05`'s own Implementation Log for the full pass/fail
  detail. `AC-04`/`AC-05`/`AC-06` (bundle-content correctness) were `T04`'s
  own scope, already `Done`. Status advances to `Done` per this run's own
  explicit instruction ("mark the story Done ... if all checks pass") and
  this project's own established precedent for a story completing while a
  standing ADR-review flag remains open (`REQ-SB-79`/`REQ-SB-82-US-06`'s
  own identical "Done, gate: flagged" shape in `BACKLOG.md`) — **`gate`
  intentionally stays `flagged`, unchanged**: the architect-pass `ADR-013`/
  `ADR-014` human review is a standing, still-open item this coder pass
  has no authority to resolve, tracked at its own existing
  `REVIEW-QUEUE.md` entry, not superseded by this build completing.
