---
id: REQ-SB-85-US-03-T05
title: artifact_import.py orchestrator + POST /artifacts/import/{preview,commit} — real per-artifact deployment
parent_story: REQ-SB-85-US-03
requirement_id: REQ-SB-85
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption: a fresh Skill's name/description are parsed from its own bundled SKILL.md frontmatter, since the frozen ADR-013 manifest shape never carries Skill metadata) + a real, pre-existing SkillManager.delete() bug found live during verification, disclosed but out of this task's own scope to fix. See ## Implementation Log and MEMORY.md. Parent story REQ-SB-85-US-03 stays In Progress — T06 (frontend) is still open."
phase: P2
depends_on: [REQ-SB-85-US-03-T01, REQ-SB-85-US-03-T02, REQ-SB-85-US-03-T03, REQ-SB-85-US-03-T04, REQ-SB-85-US-02-T01]
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03-T05 — artifact_import.py orchestrator + POST /artifacts/import/{preview,commit}: real per-artifact deployment

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Compose `T01`/`T02`/`T03`/`T04`/`REQ-SB-85-US-02-T01` into the real
import flow: parse + detect conflicts (preview), then deploy every
artifact per its resolved decision — Skill via `SkillManager.deploy`,
Agent via `HermesCLI.import_profile` + Registry write, Template/Pipeline
via `T03`/`T04` — reporting every artifact's own real outcome
independently.

---

## Starting State → End State

**Before / Inputs:**
- `T01` (`read_archive`), `T02` (`detect_conflicts`), `T03`
  (`TemplateManager.import_template`), `T04`
  (`PipelineManager.import_pipeline`), `REQ-SB-85-US-02-T01`
  (`HermesCLI.export_profile`/`import_profile`) all exist. `SkillManager.
  deploy(skill_id, profile_id)`/`.create(...)`/`.update(...)`,
  `AgentManager.delete(agent_id)`, `data_access.registry.writer.
  agent_dir`/`write_agent_files`, `data_access.registry.loader.boot()`
  all already exist and are real, `Done`.

**After / Outputs:**
- `app/business/logic/artifact_import.py` (new) exposes:
  - `preview_import(archive_path: str) -> dict` — `read_archive(...)`
    (`T01`, `MalformedBundleError` propagated uncaught — the router turns
    it into a clean `4xx`), `detect_conflicts(manifest["artifacts"])`
    (`T02`), plus `"available_profiles": [p.id for p in
    get_client().profiles.get_all()]` (the target machine's own real
    profile list, for the Skill target-profile-selection UI — see
    Context). Returns `{"manifest": ..., "artifacts": <conflict-annotated
    list>, "available_profiles": [...]}`. Writes/deploys nothing.
  - `commit_import(archive_path: str, decisions: dict[str, str],
    skill_target_profiles: dict[str, list[str]]) -> list[dict]` —
    `decisions` keys `f"{kind}:{id}"` to `"overwrite" | "skip" |
    "keep_both"` (only meaningful/required for an artifact `T02` flagged
    `conflicts: True`; a non-conflicting artifact always deploys
    directly, any decision entry for it is ignored). `re-parses AND
    re-detects conflicts fresh` (never trusts a cached preview — same
    staleness-safety principle as `REQ-SB-85-US-02`'s own `commit_export`).
    For EVERY artifact in the manifest, deploys per the per-kind mechanics
    below inside its own `try/except Exception`, appending one outcome
    dict regardless of success/failure — **never lets one artifact's
    real failure stop the loop or silently drop/mis-report another**
    (Scenario 9): `{"kind": str, "id": str, "status": "deployed" |
    "skipped" | "failed", "deployed_as": str | None, "detail": str}`.

**Per-kind deployment mechanics:**

- **Skill:** content = the payload's own `skills/<id>/SKILL.md` text +
  every `skills/<id>/scripts/**` entry; `category` = the manifest
  artifact entry's own `category` field (`REQ-SB-85-US-02-T04`).
  Target profile(s) = `skill_target_profiles.get(id) or ["default"]`
  (the documented default — see Context). No conflict → `SkillManager
  ().create(category, id, name=..., description=..., skill_md_content=
  content, tool_id="jarvis", scripts=scripts, deploy_to=targets)`.
  Conflict + `"skip"` → no-op, `status: "skipped"`. Conflict +
  `"overwrite"` → `SkillManager().update(id, skill_md_content=content,
  scripts=scripts)` (content-only replace — the existing Tool
  grouping/name/description on the target are deliberately left
  untouched by an overwrite, a disclosed scope-internal judgement call:
  "overwrite" replaces the artifact's own CAPABILITY, not its target-
  machine-local organisation), then `.deploy(id, profile_id)` for every
  requested target not already in `deployed_to`. Conflict +
  `"keep_both"` → generate an alternate id (`f"{id}-imported"`,
  `f"{id}-imported-2"`, ... — first one `SkillManager().get_by_id(...)`
  returns `None` for), `SkillManager().create(category, alt_id,
  name=f"{name} (imported)", description=..., skill_md_content=content,
  tool_id="jarvis", scripts=scripts, deploy_to=targets)`, `deployed_as:
  alt_id`.
- **Template:** No conflict → `TemplateManager().import_template(id,
  data)`. Conflict + `"skip"` → no-op. Conflict + `"overwrite"` →
  `import_template(id, data)` (same call — it already replaces the file
  unconditionally). Conflict + `"keep_both"` → alternate id via the same
  suffix scheme, `import_template(alt_id, {**data, "id": alt_id})`,
  `deployed_as: alt_id`.
- **Pipeline:** Same shape as Template, via `PipelineManager().
  import_pipeline`.
- **Agent:** payload's own `agents/<id>/profile.tar.gz` bytes are written
  to a scratch temp file first (deleted after use, every path). No
  conflict → `HermesCLI.import_profile(temp_path)` (no `--name` — the
  archive's own top-level directory already names `id`, so the restored
  profile lands under the same real id). Conflict + `"skip"` → no-op.
  Conflict + `"overwrite"` → `AgentManager().delete(id)` (mirrors
  `AgentManager.update()`'s own delete-then-recreate shape, per
  `ADR-014`), THEN the same no-conflict import path. Conflict +
  `"keep_both"` → `HermesCLI.import_profile(temp_path, name=
  f"{id}-imported")` (the real `--name` override, `ADR-014`),
  `deployed_as: f"{id}-imported"`. In every deploy/overwrite/keep-both
  case, after the Hermes-side profile call succeeds, the Registry-side
  piece is written via `registry_writer.write_agent_files(registry_writer.
  agent_dir(<real deployed id>, section_id=<resolved, see Context>,
  is_background_agent=<from the bundled Agent.json>), config=<the
  bundled Agent.json content, with `id` rewritten to the real deployed
  id when keep-both used an alternate one>, soul_text=<the bundled
  soul.md text>)`, then `asyncio.run(registry_loader.boot())` to make it
  visible immediately (same reload discipline `AgentManager.
  _reload_registry()` already applies).
- **Seed/blank data files:** for every payload path under `seed_data/`
  the manifest's own closure implies is needed (i.e. every `seed_data/`
  member actually present in the archive — the writer only ever included
  ones it detected were needed), write it VERBATIM (the archive's own
  copy is already guaranteed empty, `REQ-SB-85-US-02`'s own Scenario 4/5)
  to its real target-relative path — e.g. `seed_data/Settings/
  Entities.md` → `data_access.entities.write_raw("")`. No conflict/
  decision concept applies to a seed file on its own (it isn't a
  manifest `artifacts` entry) — always written when its owning
  capability was deployed, silently no-op'd when that capability was
  skipped entirely.

---

## Files to Modify

- `src/backend/app/business/logic/artifact_import.py` (new file).
- `src/backend/app/api/artifacts_router.py` — two new routes.

---

## Constraints

- Inherits from parent story.
- **Every artifact's own deployment is wrapped in its own `try/except`**
  — one real failure (e.g. `HermesCLI.import_profile` returning
  `(False, ...)`) is recorded as `status: "failed"` with the real
  `detail` text and the loop CONTINUES to the next artifact, never
  aborts the whole commit (Scenario 9).
- **Re-parses and re-detects conflicts fresh in `commit_import`** — never
  trusts a cached preview response (same staleness-safety principle as
  the export side).
- **A seed/blank data file is always written genuinely empty** — this
  task never introduces real operator data on import, matching
  `REQ-SB-85-US-02`'s own hard boundary.
- **Target-profile-selection UX (Skill kind only):** default to the
  target's own `"default"` (root) profile when `skill_target_profiles`
  omits an entry for a given Skill — `T06`'s own UI is expected to
  pre-check this same default and let the operator add more; this task's
  own backend code must NOT require an explicit selection to succeed
  (Scenario 2's "ends in a genuinely working state" must hold with zero
  required operator action beyond committing).
- **Agent Section resolution:** a bundled Agent's own `section_id` is
  used as-is only if `SectionManager().get_by_id(section_id)` confirms it
  exists on the target; otherwise falls back to the target's own
  "Data Gatherer" section (the same `_FALLBACK_SECTION_NAME` convention
  `AgentManager`/`PipelineManager` already use for a not-yet-resolved
  section) — an imported Agent must never land under a section folder
  that doesn't exist on the target machine.
- Scratch temp files (any `profile.tar.gz` written for `HermesCLI.
  import_profile`) are always cleaned up, success or failure.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-03-AC-01]` Produce a real `.sbf` (via
   `REQ-SB-85-US-02`'s own `commit_export`) covering at least one
   artifact per kind; call `preview_import(...)`; confirm the returned
   `artifacts` list names every real bundled artifact with a correct
   `conflicts` flag per artifact, and `available_profiles` lists real
   Hermes profiles on this machine.
2. `[REQ-SB-85-US-03-AC-02]` Using a bundle whose artifact ids are
   guaranteed not to exist on this machine (fresh, scratch ids), call
   `commit_import(...)` with `decisions={}`; confirm every artifact comes
   back `status: "deployed"`, and independently confirm each one is now
   genuinely working: `SkillManager().get_by_id(...)` finds the Skill
   deployed to the default profile; `AgentManager().get_by_id(...)` finds
   the real Agent; `TemplateManager().get_by_id(...)`/`PipelineManager().
   get_by_id(...)` find the real Template/Pipeline — never merely
   unpacked files with no live entity behind them.
3. `[REQ-SB-85-US-03-AC-03]` Re-run `commit_import(...)` on the SAME
   bundle a second time (every artifact now conflicts) with `decisions=
   {}` (no decisions supplied); confirm every conflicting artifact comes
   back `status: "failed"` (or an equivalent explicit "undecided
   conflict" outcome) rather than silently defaulting to any of
   overwrite/skip/keep-both — no conflict is EVER resolved without an
   explicit decision.
4. `[REQ-SB-85-US-03-AC-04]` Re-run with `decisions` mapping one
   conflicting Skill to `"keep_both"`; confirm the outcome's
   `deployed_as` names a real alternate id, that
   `SkillManager().get_by_id(<alt id>)` finds it deployed, AND that the
   original Skill's own real content/metadata is byte-for-byte unchanged
   (re-read it before and after to confirm).
5. `[REQ-SB-85-US-03-AC-05]` Re-run with `decisions` mapping one
   conflicting Template to `"overwrite"`; confirm
   `TemplateManager().get_by_id(id)` now returns the IMPORTED content
   (not the pre-existing one).
6. `[REQ-SB-85-US-03-AC-06]` Re-run with `decisions` mapping one
   conflicting Pipeline to `"skip"` and every OTHER conflicting artifact
   to `"overwrite"`; confirm the skipped Pipeline's real, on-disk JSON is
   byte-for-byte unchanged AND `status: "skipped"` for it, while every
   other artifact's own outcome is independently `"deployed"`.
7. `[REQ-SB-85-US-03-AC-07]` Using a bundle that carries a
   `seed_data/Settings/Entities.md` entry, commit it; confirm
   `data_access.entities.read_raw()` on the target returns `""` (or
   `None`, if never written before) — genuinely empty, never populated
   with any real content.
8. `[REQ-SB-85-US-03-AC-09]` Engineer one real failure (e.g. in-process
   monkeypatch `HermesCLI.import_profile` for exactly one Agent artifact
   in a multi-artifact commit to return `(False, "engineered failure")`,
   leaving every other real call untouched); confirm that ONE artifact's
   outcome is `status: "failed"`, `detail` contains the real engineered
   message, and every OTHER artifact in the same commit still reports its
   own real, independent `"deployed"`/`"skipped"` outcome — never a
   whole-batch abort, never a false "succeeded."
9. Clean up every scratch artifact created across steps 2-8 (real
   Skills/Templates/Pipelines/Agents, both original and any `keep_both`
   alternates) via each entity's own already-real `delete` — no leftover
   test state (no AC tag).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `preview_import` parses + flags conflicts without deploying anything
- [x] `commit_import` deploys every non-conflicting artifact directly to
      a genuinely working state, defaulting Skills to the target's own
      root profile with zero required operator action
- [x] Every conflicting artifact requires an explicit decision — no
      silent default resolution
- [x] `"keep_both"`/`"overwrite"`/`"skip"` each behave exactly per their
      locked Scenario, independently verified for at least one kind each
- [x] A seed/blank data file always lands genuinely empty
- [x] One artifact's real failure never aborts the batch or corrupts
      another artifact's own independently-reported outcome
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The upload/preview/conflict-resolution UI — `T06`.
- Any general Templates/Pipelines authoring UI beyond import provisioning.
- Real Hermes cron job re-provisioning for an imported Pipeline (`T04`'s
  own disclosed Out of Scope).

---

## Context / Notes

`ADR-013`/`ADR-014`/`ADR-015` (`Implementation/Architecture/ADR.md`),
architecture `§Template/Pipeline Write-Path Additions & Import
Orchestration`, are the authoritative design for this task.

**Target-profile-selection UX (this story's own explicit open decision,
resolved by the decomposer — see the parent story's own Notes):** the
operator is shown the target machine's own real profile list
(`available_profiles`) and may check which one(s) each bundled Skill
deploys to, defaulting to the root `"default"` profile — chosen
specifically to avoid reopening `ADR-013`'s own already-Accepted,
frozen manifest shape for a cosmetic UX improvement. This task's own
backend code is the one place that default is actually enforced
(`skill_target_profiles.get(id) or ["default"]`) — `T06`'s own UI only
needs to pre-check the same default, not re-derive the fallback logic.

---

## Implementation Log

**Build.** New `src/backend/app/business/logic/artifact_import.py` — composes
`sbf_archive.read_archive` (`T01`), `artifact_import_conflicts.detect_conflicts`
(`T02`), `TemplateManager.import_template`/`PipelineManager.import_pipeline`
(`T03`/`T04`), `SkillManager.create/update/deploy`, `HermesCLI.import_profile`
+ `AgentManager.delete` + `registry_writer.write_agent_files` +
`registry_loader.boot()` (`REQ-SB-85-US-02-T01`, `ADR-014`), per the task's
own Per-kind deployment mechanics, exactly. Two new routes added to
`src/backend/app/api/artifacts_router.py`: `POST /artifacts/import/preview`
(`UploadFile` → scratch temp `.sbf` → `preview_import`, `MalformedBundleError`
→ `400`) and `POST /artifacts/import/commit` (`UploadFile` + `decisions`/
`skill_target_profiles` JSON-string `Form` fields → `commit_import`).

**Scope-internal judgement calls (log per Pipeline.md; task `gate: flagged`
for human spot-check):**
1. A fresh Skill's `name`/`description` (required by `SkillManager.create()`)
   are parsed from the bundled `SKILL.md`'s own real YAML frontmatter (same
   convention `app/hermes/skills.py::_skill_from_md` already uses) — the
   frozen `ADR-013` manifest shape never carries Skill metadata at all.
2. An Agent's Section-fallback resolution (`_resolve_section_id`) always
   takes the "target's own Data Gatherer" branch in practice, since a
   bundled `Agent.json` never carries `section_id` (confirmed by reading
   `AgentManager._write_registry_agent` — section placement is derived
   from the folder path, never a stored field). Confirmed safe live (see
   AC-06 note below) via `SectionManager.create()`'s own pre-existing
   `tag_slug`-based idempotent-collapse-on-collision behavior.
3. Template/Pipeline cleanup for the live-verification's own scratch state
   used direct file removal (no Manager-level `delete()` exists for either
   kind — a real, pre-existing, disclosed gap per the story's own
   Non-Goals, not something this task adds).

**Real, pre-existing bug found live (NOT fixed — out of this task's own
`## Files to Modify`, logged to `MEMORY.md` for a future `/bug`):**
`SkillManager.delete()`/`.undeploy()` pass our bare-slug `skill_id` straight
to `HermesSkills.delete(profile_id, skill_id)`, which expects Hermes' own
`"category/slug"` id form — the real per-profile deployed skill folder is
silently never removed (`delete()` still reports `{"deleted": True}`). Hit
directly during this task's own AC-04 cleanup; worked around by calling
`get_client().skills.delete(profile_id, "<category>/<slug>")` directly with
the correct id form for cleanup purposes only.

**Verification (manual mode — real, disposable scratch artifacts against
this machine's own real, live Hermes install + vault; every id prefixed
`zz-import-test-*`; all scratch state confirmed fully deleted afterward,
including the orphaned-skill-folder cleanup above).** Built one real `.sbf`
covering all 4 kinds via `REQ-SB-85-US-02`'s own real `commit_export`
(scratch Skill/Template/Pipeline/Agent created first, then deleted from this
machine to simulate "ids guaranteed not to exist on target").

- `[REQ-SB-85-US-03-AC-01]` **PASS.** `preview_import` on the real bundle
  returned all 4 real artifacts with `"conflicts": false` (fresh machine)
  and a real `available_profiles` list (40 real Hermes profiles on this
  machine), writing nothing.
- `[REQ-SB-85-US-03-AC-02]` **PASS.** `commit_import(decisions={})` on the
  fresh bundle: all 4 artifacts `"status": "deployed"`. Independently
  confirmed genuinely live: `SkillManager().get_by_id` found the Skill
  deployed to `["default"]`; `AgentManager().get_by_id` found the real
  Agent; `TemplateManager().get_by_id`/`PipelineManager().get_by_id` found
  the real Template/Pipeline.
- `[REQ-SB-85-US-03-AC-03]` **PASS.** Re-running the SAME bundle with
  `decisions={}` (now all 4 conflict): all 4 came back `"status": "failed"`
  with an explicit "no explicit decision supplied" detail — never a silent
  default resolution.
- `[REQ-SB-85-US-03-AC-04]` **PASS.** Re-run with the Skill mapped to
  `"keep_both"`: outcome named `deployed_as: "zz-import-test-skill-imported"`,
  confirmed real and deployed via `SkillManager().get_by_id`. The original
  Skill's own metadata AND real `SKILL.md` bytes confirmed byte-for-byte
  unchanged (read before/after).
- `[REQ-SB-85-US-03-AC-05]` **PASS.** The live Template was mutated
  in-place first (`note_name` changed locally), then re-run with
  `"overwrite"` for it: `TemplateManager().get_by_id` afterward showed the
  bundle's own original content restored, not the local mutation.
- `[REQ-SB-85-US-03-AC-06]` **PASS.** Re-run mapping the Pipeline to
  `"skip"` and every other conflicting artifact (Skill/Template/Agent) to
  `"overwrite"`: the Pipeline's real on-disk JSON confirmed byte-for-byte
  unchanged (read before/after) and `"status": "skipped"`; the other 3
  artifacts each independently `"deployed"` — including a real Agent
  overwrite (`AgentManager().delete()` then a fresh `import_profile`).
- `[REQ-SB-85-US-03-AC-07]` **PASS.** The real, live `Entities.md` (backed
  up first) had a genuine 46-byte placeholder injected, then the bundle's
  Skill was deployed again (`"overwrite"`, others `"skip"`):
  `entities_data.read_raw()` came back empty afterward, confirming a real
  write-to-empty (not a vacuous already-empty check). The true original
  real content was restored immediately after and confirmed byte-identical.
- `[REQ-SB-85-US-03-AC-09]` **PASS.** `HermesCLI.import_profile` was
  in-process monkeypatched to return `(False, "engineered failure...")` for
  every call, then all 4 artifacts re-run with `"overwrite"`: the Agent
  came back `"status": "failed"` with the real engineered detail text; the
  other 3 (Skill/Template/Pipeline — none of which route through
  `HermesCLI.import_profile`) each independently came back `"deployed"` in
  the SAME commit call.
- Step 9 (cleanup, no AC tag): all scratch state (original + `keep_both`
  alternate Skill, Agent, Template, Pipeline, the real orphaned Hermes-side
  skill folders from the `SkillManager.delete()` bug above, the stray
  `Hermes-Provisioning/skills/zz-import-test-cat` category folder) confirmed
  fully removed; `SectionManager().get_all()` confirmed unchanged (6 real
  sections, no stray "Data Gatherer" section created).

`REQ-SB-85-US-03-AC-08` (`MalformedBundleError` → clean 4xx) is `T01`'s own
scope — not tagged in this task's Tests block, not re-verified here (the
router's `except MalformedBundleError` mapping is a direct, untested-here
pass-through of `T01`'s own already-verified behavior).

gate: flagged 2026-08-31 — trigger-1 (material assumption: Skill name/
description derivation) + a real, disclosed, out-of-scope pre-existing bug
found live (`SkillManager.delete`, see `MEMORY.md`). Every locked AC mapped
to this task was independently verified live with a real positive result.
