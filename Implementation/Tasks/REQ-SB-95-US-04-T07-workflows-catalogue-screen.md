---
id: REQ-SB-95-US-04-T07
title: Workflows catalogue screen + ordered-step editor, Settings card, route, and the seventh Artifacts tab
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: frontend
status: Blocked
gate: flagged
gate_reason: "triggers 4, 6 and 7 — ESC-078 written (unanticipated-file): the seventh KIND_NAV tab needs the ArtifactKind union in features/settings/artifactsApiClient.ts and the exhaustive Record in ArtifactExportModal.tsx, neither of which this task's ## Files to Modify names, so AC-04 could not be verified. AC-01, AC-02 and AC-06 are verified live."
phase: P2
depends_on: [REQ-SB-95-US-04-T03, REQ-SB-95-US-04-T04, REQ-SB-95-US-02-T06]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-04-T07 — Workflows Catalogue Screen + Ordered-Step Editor

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Let the operator actually document a Workflow: a catalogue list, an ordered-step
editor whose step picker offers only real catalogued Actions, the Settings card
and route, and the seventh kind tab on the Artifacts page.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-02-T06` has added the Actions page, its Settings card, its route
  and the sixth `KIND_NAV` tab — re-read those real files; this task extends the
  same three shared files.
- The frontend declares no test runner, so verification is structural, in a real
  browser.

**After / Outputs:**

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` — the Workflows catalogue
  (`.item-list`/`.item-row` family) and the one-Workflow editor: the kind of
  request it handles, an ordered list of step rows each picking a real
  catalogued Action from a fetched list, a per-step confirmation toggle, plain
  move-up/move-down reordering controls (no bespoke drag-and-drop), and the
  report-back definition.
- `src/frontend/src/features/settings/workflowsApiClient.ts`.
- One more `SETTINGS_SECTIONS` entry and one more `<Route>`.
- `SettingsArtifactsPage.tsx` gains the seventh `KIND_NAV` entry (`workflow`).
- A refused save renders the backend's own message naming the step and the
  unknown action id; a blocked Action delete renders the referencing Workflows.

---

## Files to Modify

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` (new)
- `src/frontend/src/features/settings/workflowsApiClient.ts` (new)
- `src/frontend/src/pages/SettingsPage.tsx` (one `SETTINGS_SECTIONS` entry)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` (seventh `KIND_NAV` entry + the `ArtifactKind` union)
- `src/frontend/src/pages/SettingsActionsPage.tsx` (render the blocked-delete message naming referencing Workflows)

---

## Constraints

- Inherits from parent story.
- **Functional-first on already-approved conventions** (story Notes → Prototype
  parity): reordering is built plainly with existing controls, not a bespoke
  drag-and-drop system. Visual polish is an out-of-band spot-check, never a
  locked AC.
- Every assertion below is on **DOM structure**, not computed CSS or layout.
- The step picker is populated from the live Actions API — never a hardcoded
  list — so the invalid state is hard to reach; the backend refusal is still
  rendered when it fires.
- No change to how Pipelines render anywhere.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP, reading the DOM back at least ~500ms after any dispatched
state change):

1. `[REQ-SB-95-US-04-AC-01]` Open `/settings`, confirm a Workflows card is
   present in the `settings-grid` and routes to the Workflows page. Create a
   Workflow with a request kind and three steps (the second marked as needing
   confirmation); save; confirm the row renders, and that reopening it shows the
   same three steps in the same order with the same confirmation flags and the
   same report definition.
2. `[REQ-SB-95-US-04-AC-01]` Reorder two steps with the move controls, save,
   reopen; confirm the new order persisted and no step was dropped or
   duplicated.
3. `[REQ-SB-95-US-04-AC-02]` Confirm the step picker's options are exactly the
   real catalogued Actions fetched from the API (assert the option values
   against `GET /actions`), so an unknown action id is not reachable through the
   screen. Then force a refusal (e.g. delete an Action in another tab and save a
   stale step) and confirm the backend's message naming the step and the unknown
   id renders.
4. `[REQ-SB-95-US-04-AC-04]` Open `/settings/artifacts`; confirm an
   `[data-testid="artifacts-tab-workflow"]` nav item is present beside the six
   existing tabs, that selecting it lists the real Workflows as `.item-row`
   entries, and that every pre-existing tab still lists exactly what it listed
   before.
5. `[REQ-SB-95-US-04-AC-06]` On the Actions page, attempt to delete an Action a
   Workflow references; confirm the screen renders the refusal naming the
   referencing Workflow(s) and that the Action row is still present afterwards.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Workflows catalogue page + ordered-step editor on existing approved conventions
- [ ] Settings card and route added; seventh `KIND_NAV` tab on the Artifacts page
      — card and route **done**; the seventh tab is **blocked** on `ESC-078`
- [x] Step picker populated from the live Actions API
- [x] Backend refusals (bad step, blocked Action delete) rendered verbatim
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — two candidates recorded in `REVIEW-QUEUE.md` instead; the file is 86 KB
      against the 40 KB budget its own rule 1 sets, which forbids appending while over
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- A screen over workflow runs — not in this story.
- Drag-and-drop reordering, visual polish (out-of-band spot-check).

---

## Context / Notes

The story's Affected Screens and its Prototype-parity Notes are authoritative,
including the operator's own 2026-08-31 functional-first precedent that makes
plain move controls the right first build for reordering.

---

## Implementation Log

### 2026-10-18 — built, three of four locked ACs verified, `AC-04` blocked on `ESC-078`

**What was built** (four files mine outright, two one-edit touches, nothing else):

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` (new) — the catalogue on the
  approved `.item-list`/`.item-row` family, and the one-Workflow editor: request
  kind, description, an ordered list of step rows (a `<select>` of real catalogued
  Actions, a description, the step's own stable id, its stored `inputs` read-only, a
  per-step **Needs confirmation** toggle, **Move up** / **Move down** / **Remove**),
  and the report definition (free text + optional per-step tick list).
- `src/frontend/src/features/settings/workflowsApiClient.ts` (new) — thin client over
  the real `GET/POST/PUT/DELETE /workflows`.
- `src/frontend/src/pages/SettingsPage.tsx` — one `SETTINGS_SECTIONS` entry.
- `src/frontend/src/App.tsx` — one import, one `<Route path="/settings/workflows">`.
- `src/frontend/src/pages/SettingsActionsPage.tsx` — the blocked-delete contract
  written into the file's own header comment. **No rendering change was needed and
  none was made:** `handleDelete` already renders `extractErrorDetail(error)` verbatim
  in `[data-testid="action-list-error"]` and deliberately does not reload the
  catalogue on a refusal, so the backend's sentence naming the referencing Workflows
  is what the operator reads and the Action's row is still there afterwards. Verified
  live rather than assumed (`AC-06` below).
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` — **not touched.** See `ESC-078`.

**Where it was verified.** A **disposable** backend on `127.0.0.1:8042` over a
scratch `SECOND_BRAIN_DATA_PATH` / `VAULT_PATH` / `HERMES_HOME_PATH` under this
session's scratchpad, plus a second Vite on `:5174` with `VITE_API_BASE_URL`
overridden (the `:5174` origin is already in the backend's default CORS list).
Headless Edge driven over CDP, the DOM read back ≥500 ms after every dispatched
change, every screenshot opened and looked at. The operator's own `:8001` and real
data path were never written to — confirmed after the run: the real
`<DATA_PATH>/data/Workflows/` holds **zero** entries and the real `Actions/` still
holds exactly the operator's own two, while every artefact this task created is under
the scratch path. `:8001` answered `200` afterwards.

| AC-ID | Observed | Verdict |
|---|---|---|
| `REQ-SB-95-US-04-AC-01` (step 1) | `/settings` renders 15 `.settings-card`s, one of them **Workflows** → `/settings/workflows`; clicking it routed there (`location.pathname` `/settings/workflows`, `h1` `Workflows`). Created `team-actions-by-mail`, request kind *"send my team's assigned actions by mail"*, three steps (`list-team-actions` → `format-as-a-table` → `mail-the-result`), **step 2 ticked** as needing confirmation, report *"the table that was sent and who it went to"*. Saved with no error; the row rendered as `workflow-row-team-actions-by-mail` with badges `3 steps` and `list-team-actions → format-as-a-table → mail-the-result`. Reopened: same three steps, same order, same descriptions, **`confirm` true on step 2 only**, same report text, and the report scope line reading *"Reports on every step, in order — the default while nothing is picked below."* Steps came back carrying minted ids `step-6f8bfdc9` / `step-3b5089ff` / `step-af83f33e`. | **Pass** |
| `REQ-SB-95-US-04-AC-01` (step 2) | **Move up** on step 3 swapped it with step 2 in the editor; saved; the catalogue badge read `list-team-actions → mail-the-result → format-as-a-table`. Reopened and re-read `GET /workflows` directly: steps are `[step-6f8bfdc9 list-team-actions]`, `[step-af83f33e mail-the-result]`, `[step-3b5089ff format-as-a-table, needs_confirmation true]` — **the same three step ids as before the move, in the new order**, none dropped, none duplicated, and the confirmation flag travelled with its own step rather than with position 2. | **Pass** |
| `REQ-SB-95-US-04-AC-02` | The step picker's `option` values were `["doomed-action","format-as-a-table","list-team-actions","mail-the-result","report-unmet-request"]` — **byte-identical to the ids `GET /actions` returned in the same run**, asserted by fetching both from the page. No free-text action field exists, so an uncatalogued id is not reachable by typing. Then forced a refusal: added a 4th step naming `doomed-action`, deleted that Action out from under the open editor (`DELETE /actions/doomed-action` → `{"deleted":true}`, allowed because no *saved* Workflow named it yet), and saved. The editor rendered, verbatim: **"step 4 of this Workflow names action 'doomed-action', which is not in this install's Action catalogue; nothing was saved"** under a `Save refused` badge. `GET /workflows` still held the three original steps — nothing written. The re-read Action catalogue then relabelled the stale option **"doomed-action — not in this install's Action catalogue"** rather than leaving it looking catalogued. | **Pass** |
| `REQ-SB-95-US-04-AC-04` | **Not verified — blocked.** `GET /artifacts` on the same install really does return the seventh kind (`skill 11 / template 6 / agent 1 / action 4 / workflow 1`), but the page's `ArtifactKind` union lives in `features/settings/artifactsApiClient.ts` and widening it breaks the exhaustive `Record<ArtifactKind, string>` in `ArtifactExportModal.tsx`. Neither file is in this task's `## Files to Modify`, so neither was touched. `ESC-078` carries both exact edits. | **Blocked** |
| `REQ-SB-95-US-04-AC-06` | On `/settings/actions`, deleted `mail-the-result` (step 2 of the saved Workflow). The screen rendered, verbatim: **"action 'mail-the-result' was not deleted: it is a step of workflow 'team-actions-by-mail'. Remove the step from each first, so no documented handling is left pointing at nothing"**. `action-row-mail-the-result` was **still present** afterwards and `GET /actions` still listed it. An Action nothing references (`nobody-references-me`, seeded for the check) deleted normally with no error. | **Pass** |

**Gates.** `npx tsc --noEmit` from `src/frontend`: **clean, exit 0** — no shared union
was widened, which is exactly why `AC-04` is blocked rather than shipped half-done.
`npx oxlint src`: **12 warnings, all pre-existing, none in any file this task
touched**, 0 errors. `pytest -q` in `src/backend`: **655 passed / 0 failed** before,
**666 passed / 0 failed** after — this task is frontend-only and moved the backend
suite by **zero**; the +11 are `REQ-SB-95-US-04-T05`'s `tests/test_workflow_runs.py`
landing in the shared checkout mid-session (11 `def test_` in that file). All four
known order-dependent tests passed in both full runs.

**Judgement calls made inside scope (spot-check these):**

1. **A step whose Action is no longer catalogued is carried as its own labelled
   `<option>`.** A `<select>` with no matching option renders its *first* option, so
   simply listing the catalogue would silently rewrite a stored step into a different
   Action just by opening the editor. The unknown id is kept, labelled *"— not in this
   install's Action catalogue"*, and the backend is left to refuse the save. This is
   also what makes `AC-02`'s forced-refusal step reachable at all.
2. **The Action catalogue is re-read after a refused save**, while the Workflow
   catalogue deliberately is not. A refusal is proof the option list is stale; leaving
   it unlabelled would have the screen presenting a dead id as catalogued directly
   under a message saying it is not.
3. **`inputs` are shown read-only and carried through verbatim.** The task does not ask
   for an inputs editor, and a save *replaces* the stored step list wholesale — so
   anything this editor dropped would be dropped on disk.
4. **The report's step picker only offers steps that already have an id**, with a
   plain sentence for a step that does not yet; an id whose step has since been
   removed is dropped at save, because the run engine composes the report from
   recorded step outcomes and a step that no longer exists records none.
5. **A new-Workflow save onto an existing id announces itself as a replacement** — a
   `Replaces` badge, and the button reads `Replace <id>` instead of `Save changes`.
   `POST /workflows` overwrites, same as `POST /actions`; calling that "New workflow"
   would be the screen's own word for overwriting something.
6. **Three different renderings for three different states** (`SPRINT-091`'s rule):
   `workflow-catalogue-error` names `GET /workflows` and carries the real message, and
   is never the empty wording; `workflow-actions-error` names `GET /actions` and
   suppresses the picker entirely rather than showing an empty one;
   `workflow-catalogue-empty` / `workflow-actions-empty` are used only for a read that
   genuinely returned nothing.

**Not touched:** `app/api/workflows_router.py`, `app/data_access/workflow_runs.py`,
`app/business/logic/workflow_run.py`, `tests/test_workflow_runs.py` (all `T05`'s, live
in this checkout), `src/marketplace/entities/1.3.0/`, `src/marketplace/my-day/1.7.1/`.

gate: flagged 2026-10-18 — trigger 4 (`ESC-078` written), trigger 6 (`AC-04`
unverifiable inside scope), trigger 7 (unanticipated file). No ADR created or
deviated from; no new dependency; no backend file touched.
