---
id: REQ-SB-85-US-03-T06
title: Import flow UI — upload/preview + per-artifact conflict-resolution screens
parent_story: REQ-SB-85-US-03
requirement_id: REQ-SB-85
type: frontend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls logged for human spot-check (extractErrorDetail fallback-string generalization; Import card placement/layout, net-new-design-needed with no prototype coverage). Every locked AC mapped to this task verified live with a real positive result. See ## Implementation Log."
phase: P2
depends_on: [REQ-SB-85-US-03-T05, REQ-SB-85-US-01-T02]
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03-T06 — Import flow UI: upload/preview + per-artifact conflict-resolution screens

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Add an "Import" trigger on `SettingsArtifactsPage.tsx` that lets the
operator upload a `.sbf` file, previews its real contents + conflicts,
collects an explicit per-conflict decision, and commits the import,
reporting every artifact's own real outcome.

---

## Starting State → End State

**Before / Inputs:**
- `SettingsArtifactsPage.tsx` (`REQ-SB-85-US-01-T02`) has no Import
  entry point yet. `POST /artifacts/import/preview` and `POST
  /artifacts/import/commit` (`T05`) exist, both multipart form endpoints
  (`file: UploadFile`, plus `decisions`/`skill_target_profiles` as
  JSON-encoded form fields on `/commit`).

**After / Outputs:**
- `src/frontend/src/features/settings/artifactsApiClient.ts` gains:
  - `interface ImportArtifactPreview { kind: string; id: string;
    conflicts: boolean; category: string | null }`
  - `interface ImportOutcome { kind: string; id: string; status:
    'deployed' | 'skipped' | 'failed'; deployed_as: string | null;
    detail: string }`
  - `previewImport(file: File): Promise<{ manifest: unknown; artifacts:
    ImportArtifactPreview[]; available_profiles: string[] }>` — real
    `multipart/form-data` POST.
  - `commitImport(file: File, decisions: Record<string, 'overwrite' |
    'skip' | 'keep_both'>, skillTargetProfiles: Record<string,
    string[]>): Promise<ImportOutcome[]>`.
- `SettingsArtifactsPage.tsx` gains a `data-testid="import-trigger"`
  button (independent of the multi-select selection — import doesn't
  need a prior selection, it operates on the uploaded file's own
  contents) that opens an upload control
  (`data-testid="import-file-input"`, a real `<input type="file"
  accept=".sbf">`). On file selection:
  1. The client keeps the real `File` object in state (needed again at
     commit — `T05`'s own two-phase design re-parses fresh rather than
     trusting a cached preview, so the same file is re-submitted, never
     just its parsed preview data).
  2. Calls `previewImport(file)`; on a clean rejection (a `400`-class
     response for a malformed archive), renders an honest inline error
     (`data-role="import-error"`) and does NOT render any contents/
     conflict UI (Scenario 8).
  3. On success, renders a contents-preview panel
     (`data-role="import-contents-preview"`) listing every real bundled
     artifact (kind/id), each row showing whether it `conflicts`.
  4. For every artifact whose `conflicts` is `true`, a per-artifact
     3-way control renders (`data-testid="conflict-overwrite-<kind>-<id>"`,
     `data-testid="conflict-skip-<kind>-<id>"`,
     `data-testid="conflict-keep-both-<kind>-<id>"`) — never a single
     whole-bundle control.
  5. For every `kind: "skill"` artifact, a checkbox list of
     `available_profiles` renders (`data-testid="skill-target-profile-
     <id>-<profile>"`), with `"default"` PRE-CHECKED (the documented
     backend default — `T05`'s own Context) — the operator may check
     additional/different real profiles.
  6. `data-testid="import-commit"` is enabled only once every conflicting
     artifact has a chosen resolution; calls `commitImport(file,
     decisions, skillTargetProfiles)`.
  7. On a successful commit, renders a per-artifact outcome list
     (`data-role="import-outcome-<kind>-<id>"`) showing each real
     `status`/`detail` independently — a `"failed"` entry renders its own
     real `detail` text, never a generic/blanked error, and never blocks
     the other entries from rendering their own real outcomes.

---

## Files to Modify

- `src/frontend/src/pages/SettingsArtifactsPage.tsx`.
- `src/frontend/src/features/settings/artifactsApiClient.ts`.

---

## Constraints

- Inherits from parent story.
- **DOM-structural ACs only** — lock only that the preview renders before
  commit, that every conflict requires its own explicit decision before
  Commit is enabled, and that outcomes render independently per artifact
  — never pixel-level/colour/hover assertions. Both screens are
  `net-new-design-needed` (functional-first per the story's own
  frontmatter override) — a non-blocking design spot-check is expected
  later.
- **Never calls `/commit` before the preview has rendered** — no
  "one-click import skipping the preview" shortcut.
- **Never fabricates a resolution for an undecided conflict** — Commit is
  genuinely disabled, not just visually deprioritized, until every
  conflicting artifact has one of the 3 real choices selected.
- Reuse `.item-list`/`.item-row` for both new lists (contents-preview,
  outcome report) — no new list primitive.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-03-AC-01]` Upload a real `.sbf` (from
   `REQ-SB-85-US-02`'s own already-`Done` export flow) via
   `[data-testid="import-file-input"]`; confirm
   `[data-role="import-contents-preview"]` renders every real bundled
   artifact BEFORE any `/commit` call is made (verify via a
   `window.fetch` spy: only `/preview` has been called at this point).
2. `[REQ-SB-85-US-03-AC-03]` Using a `.sbf` whose artifact ids already
   exist on this deployment (re-upload the same file a second time after
   a first successful import, or use a bundle exported from this same
   machine), confirm each conflicting artifact renders its own 3 real
   controls (`overwrite`/`skip`/`keep_both`) independently — not one
   shared control for the whole bundle — and that
   `[data-testid="import-commit"]` starts disabled.
3. `[REQ-SB-85-US-03-AC-04]`/`[REQ-SB-85-US-03-AC-05]`/`[REQ-SB-85-US-03-AC-06]`
   Select `keep_both` on one conflicting artifact, `overwrite` on
   another, `skip` on a third (requires at least 3 real conflicting
   artifacts, or simulate via a mocked preview response); confirm
   `[data-testid="import-commit"]` becomes enabled once all are decided,
   and that the outgoing `/commit` request body's `decisions` map
   contains exactly those 3 real choices keyed correctly.
4. `[REQ-SB-85-US-03-AC-08]` Upload a plain, non-`.sbf` file (e.g. a
   `.txt`); confirm `[data-role="import-error"]` renders an honest error
   and neither the contents-preview panel nor any conflict control ever
   renders.
5. `[REQ-SB-85-US-03-AC-09]` Commit an import where the backend reports a
   mix of `"deployed"`/`"failed"` outcomes (engineer this via a mocked
   `/commit` response, or a real induced failure if `T05`'s own Test
   step 8 setup is still available); confirm every artifact's own
   `[data-role="import-outcome-<kind>-<id>"]` renders independently, the
   failed one showing its own real `detail` text, with no outcome
   silently missing from the list.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The contents-preview panel renders every real bundled artifact
      before any commit call, and honestly rejects a malformed upload
- [x] Every conflicting artifact gets its own independent 3-way control;
      Commit stays disabled until all are decided
- [x] The Skill target-profile checklist defaults to `"default"`
      pre-checked
- [x] Every artifact's own real deployment outcome renders independently,
      including a failed one's own real detail text
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `SettingsArtifactsPage.tsx`'s own multi-select mechanism
  — `REQ-SB-85-US-01-T02`, reused unchanged (Import doesn't consume the
  selection at all).
- The Export side — `REQ-SB-85-US-02-T05`.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

The parent story's own frontmatter `gate_reason` records the operator's
direct override: build functional-first, a real `/design REQ-SB-85` pass
covering this screen (alongside `US-01`/`US-02`'s own new screens)
happens later. The Skill target-profile default (`"default"` pre-checked)
is `T05`'s own documented backend default — this task only needs to
mirror it in the initial checkbox state, not re-derive it.

---

## Implementation Log

**Environment note.** The running backend dev-server (port 8001, `--reload`)
was confirmed stale before this task started — its own `/openapi.json` was
still missing `T05`'s own `/artifacts/import/{preview,commit}` routes, even
though `T05` was already `Done`. Reconfirms this project's own repeated
finding (`SPRINT-019`/`022`/`035`) that `--reload` can silently keep serving
old routes. Root cause here was slightly different: the reloader parent PID
had already exited, but its real multiprocessing-fork worker child was still
alive and holding the listening socket (found via `Get-CimInstance
Win32_Process`'s `ParentProcessId` chain after `Get-Process` on the parent
PID came back empty). Killed the real child PID, started one fresh,
non-`--reload` instance; `/openapi.json` then correctly listed both new
import routes.

**Build.** `artifactsApiClient.ts` gains `ImportArtifactPreview`/
`ImportPreviewResult`/`ImportOutcome`, `previewImport(file)`/
`commitImport(file, decisions, skillTargetProfiles)` — both real
`multipart/form-data` POSTs via the existing `apiFetch` helper (already
FormData-aware, no change needed there). `SettingsArtifactsPage.tsx` gains
an independent "Import" card (own `data-role="import-flow"`) alongside the
existing selection/Export cards: `import-trigger` reveals a real
`<input type="file" accept=".sbf" data-testid="import-file-input">`; on
selection the real `File` is kept in state and re-submitted at commit time
(never just the cached preview), `previewImport` renders
`data-role="import-contents-preview"` (every bundled artifact, `.item-list`/
`.item-row` reused per the Constraint) with an independent 3-way
overwrite/skip/keep-both control per conflicting artifact
(`conflict-{overwrite,skip,keep-both}-<kind>-<id>`) and a
`skill-target-profile-<id>-<profile>` checkbox list (defaulting to
`"default"` pre-checked) for every `kind: "skill"` artifact regardless of
conflict status (a fresh, non-conflicting Skill deploy also needs a target
profile — `T05`'s own documented default). `import-commit` stays disabled
until every conflicting artifact has a decision, then calls `commitImport`
and renders each real outcome independently
(`data-role="import-outcome-<kind>-<id>"`).

**Scope-internal judgement calls (log per Pipeline.md; task `gate: flagged`
for human spot-check):**
1. Generalized the shared `extractErrorDetail()` helper's non-`ApiError`
   fallback string from `"Export failed."` to `"Request failed."`, since
   it is now called by both the Export and Import flows on the same page —
   a mechanical, same-file correctness fix (the old string would have been
   misleading on an Import-flow non-`ApiError` throw), not a behavior
   change for the real path (every real backend rejection is an `ApiError`,
   so this fallback is essentially unreachable in practice).
2. Placement/layout not specified by the task (net-new-design-needed,
   functional-first per the story's own frontmatter override): the Import
   card sits between the selection-summary card and the Export-preview
   card; the skill target-profile checklist renders inline inside the
   conflicting/non-conflicting artifact's own `item-row-main`, and the
   3-way conflict control renders in that row's `item-row-actions` (mirrors
   the existing secret-finding redact/keep row shape from the Export flow
   this same page already has). `import-trigger` only ever reveals the file
   input (no toggle-back) — the simplest shape satisfying the Objective's
   "opens an upload control."
3. Cleared the real file input's value after every selection
   (`event.target.value = ''`) so the SAME file can be re-selected a second
   time (needed for Scenario 3's own "re-upload the same file" verification
   technique) — otherwise a browser's file input never fires `onChange`
   again for an identical path. Mechanical, not a business-logic choice.

**Verification (manual mode — real browser, real backend, real disposable
scratch artifacts; a minimal native `fetch`+`WebSocket` CDP driver against a
dedicated headless Edge instance, `--remote-debugging-port` + isolated
`--user-data-dir`, matching this project's own established `SPRINT-036`/
`038` technique; `DOM.setFileInputFiles` for the real file upload, per
`SPRINT-038`'s own confirmed-required primitive).** Prepared a real `.sbf`
bundle (via a direct, in-venv Python script driving `SkillManager().create`/
`TemplateManager().import_template`/`PipelineManager().import_pipeline`
then `artifact_export.commit_export` — the same already-`Done` real export
path `US-02` built) covering 3 kinds (Skill/Template/Pipeline, ids prefixed
`zz-t06-import-test-*`), which — since these 3 artifacts already exist on
this machine at upload time — also directly exercises the real conflict
path for every one of them.

- `[REQ-SB-85-US-03-AC-01]` **PASS.** Uploaded the real bundle via
  `[data-testid="import-file-input"]` (`DOM.setFileInputFiles`); confirmed
  `[data-role="import-contents-preview"]` rendered all 3 real bundled
  artifacts. A `window.fetch` spy installed before upload confirmed only
  `POST /artifacts/import/preview` had fired at that point — zero calls to
  `/commit`.
- `[REQ-SB-85-US-03-AC-03]` **PASS.** All 3 artifacts (uploaded a second
  time onto a machine where they already exist) rendered their own
  independent 3-way control set (9 distinct `conflict-*` testids for 3
  artifacts, confirmed by direct DOM query) — never one shared control.
  `[data-testid="import-commit"]` confirmed `disabled: true` before any
  decision was made.
- `[REQ-SB-85-US-03-AC-04]`/`[REQ-SB-85-US-03-AC-05]`/
  `[REQ-SB-85-US-03-AC-06]` **PASS.** Selected `keep_both` on the Skill,
  `overwrite` on the Template, `skip` on the Pipeline;
  `[data-testid="import-commit"]` became enabled (`disabled: false`)
  exactly once all 3 were decided. Confirmed the real outgoing `/commit`
  request's own `decisions` `Form` field (read via a body spy) was exactly
  `{"skill:zz-t06-import-test-skill":"keep_both",
  "template:zz-t06-import-test-template":"overwrite",
  "pipeline:zz-t06-import-test-pipeline":"skip"}` — correctly keyed. The
  real commit then genuinely deployed per `T05`'s own already-verified
  mechanics: Skill outcome named `deployed_as:
  "zz-t06-import-test-skill-imported"` (real `keep_both` alternate),
  Template outcome `"deployed"` (real overwrite), Pipeline outcome
  `"skipped"` — all rendered independently via their own
  `[data-role="import-outcome-<kind>-<id>"]`.
- `[REQ-SB-85-US-03-AC-08]` **PASS.** Uploaded a plain `.txt` file;
  `[data-role="import-error"]` rendered the real backend's own honest 400
  detail (`"... is not a valid zip archive"`); confirmed via DOM query that
  neither the contents-preview panel nor any conflict control ever
  rendered.
- `[REQ-SB-85-US-03-AC-09]` **PASS.** Per the task's own Tests block
  ("engineer this via a mocked `/commit` response"): re-uploaded the real
  bundle (fresh page load, fresh conflicts against the artifacts the prior
  AC-04/05/06 pass had just deployed), decided all 3 conflicts, then
  installed a `window.fetch` override intercepting only the `/commit` URL
  to return an engineered 3-artifact response (`"deployed"`/`"failed"`/
  `"skipped"`, the `"failed"` one carrying a real, distinct detail string
  `"engineered failure: disk full"`) — every other real call untouched.
  Confirmed all 3 outcomes rendered independently, the failed one showing
  its own real (engineered) detail text, none silently missing, no
  whole-batch abort visible in the UI.
- Cleanup (no AC tag): all real scratch state removed via a direct in-venv
  Python script — `SkillManager().delete()` for both the original and the
  `keep_both` `-imported` alternate (working around the SAME real,
  pre-existing `SkillManager.delete()`/Hermes-id-form bug `T05` already
  found and logged to `MEMORY.md`, by calling `get_client().skills.delete()`
  directly with the correct `"category/slug"` form first), direct file
  removal for Template/Pipeline (no Manager-level `delete()` exists for
  either — the same disclosed gap `T05` already logged). Independently
  confirmed afterward: all 3 `get_by_id()` calls return `None`, the real
  Hermes `default` profile's own skill list has zero `zz-t06-*` entries
  left, and `SectionManager().get_all()` is unchanged (6 real sections, no
  stray section created). The headless Edge instance's own specific PID
  tree (`taskkill /PID <root> /T /F`, never `/IM`) was also cleaned up.

`REQ-SB-85-US-03-AC-02`/`AC-07` are not tagged to this task's own Tests
block (`T05`'s own scope, already independently verified there) — not
re-verified here.

gate: flagged 2026-09-01 — trigger-1-adjacent scope-internal judgement calls
above (logged for human spot-check, not a MUST-FLAG assumption about
product behavior); every locked AC mapped to this task was independently
verified live with a real positive result against the real running
frontend + backend.
